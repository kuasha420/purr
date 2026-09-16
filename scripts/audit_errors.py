#!/usr/bin/env python3
"""
🐾 Purr Error Swallowing & Silent Failures Auditor
Project Tuki / Purr Ecosystem

Enforces Step 7 of the In-Lockstep Maintainability Invariant:
"No error swallowing in committed code" & Zero Silent Failures Doctrine.

Scans Python files and shell scripts across the repository using AST analysis
and structural heuristics to detect:
  1. Bare 'except:' clauses
  2. Swallowed exceptions ('except ...: pass' or '...' without logging/surfacing)
  3. Unlogged broad catches ('except Exception:' without logging, raise, or honest error return)
  4. Subprocess stderr blackholing ('stderr=subprocess.DEVNULL')
  5. Operational shell stderr blackholing and blind '|| true' masking
"""

import ast
import os
import re
import sys
import argparse
from typing import List, Dict, Any, Tuple, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class Colors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


class AuditViolation:
    def __init__(self, file_path: str, line_no: int, rule_id: str, message: str, snippet: str = ""):
        self.file_path = file_path
        self.line_no = line_no
        self.rule_id = rule_id
        self.message = message
        self.snippet = snippet

    def __str__(self) -> str:
        rel_path = os.path.relpath(self.file_path, REPO_ROOT)
        out = f"  {Colors.RED}✘ [{self.rule_id}]{Colors.RESET} {Colors.BOLD}{rel_path}:{self.line_no}{Colors.RESET}\n"
        out += f"    {self.message}\n"
        if self.snippet:
            out += f"    {Colors.DIM}Snippet: {self.snippet.strip()}{Colors.RESET}\n"
        return out


def is_diagnostic_call(call_node: ast.Call) -> bool:
    """
    Checks if an AST Call represents a logging, stderr output, or diagnostic notification.
    """
    func_name = ast.unparse(call_node.func).lower()

    # Recognized diagnostic / telemetry targets
    diagnostic_keywords = [
        "log", "logger", "debug", "warn", "warning", "error", "critical",
        "stderr", "write", "log_error", "log_warning", "log_step",
        "showmessage", "emit", "fail", "exit"
    ]
    for kw in diagnostic_keywords:
        if kw in func_name:
            return True

    # Check for print(...) with stderr or error/warning/debug content
    if func_name == "print":
        for kw in call_node.keywords:
            if kw.arg == "file" and ("stderr" in ast.unparse(kw.value).lower()):
                return True
        # Check if printing message containing error/warning/debug
        if call_node.args:
            first_arg = ast.unparse(call_node.args[0]).lower()
            if any(k in first_arg for k in ["error", "warn", "fail", "debug", "[!]", "[✘]"]):
                return True

    return False


def surfaces_error_in_return(body_node: ast.AST, exc_var_name: Optional[str]) -> bool:
    """
    Determines if an exception handler surfaces an honest error status or passes the exception upstream.
    """
    for sub in ast.walk(body_node):
        # 1. Direct re-raise
        if isinstance(sub, ast.Raise):
            return True

        # 2. Honest return values
        if isinstance(sub, ast.Return) and sub.value:
            ret_str = ast.unparse(sub.value)
            # Tuple returns like (False, f"Error: {e}") or RecipeResult(False, ...)
            if any(term in ret_str for term in ["RecipeResult(False", "False,", "(False", "False)"]):
                return True
            if exc_var_name and exc_var_name in ret_str:
                return True

    return False


def audit_python_file(file_path: str) -> List[AuditViolation]:
    """
    Audits a single Python file using AST inspection.
    """
    violations = []
    with open(file_path, "r", encoding="utf-8") as f:
        src = f.read()

    try:
        tree = ast.parse(src, filename=file_path)
    except SyntaxError as e:
        violations.append(AuditViolation(file_path, e.lineno or 1, "PY-SYNTAX", f"Syntax error parsing Python file: {e}"))
        return violations

    lines = src.splitlines()

    for node in ast.walk(tree):
        # --- Check 1: Exception Handlers ---
        if isinstance(node, ast.ExceptHandler):
            exc_str = ast.unparse(node.type) if node.type else "<bare>"
            name = node.name
            line_no = node.lineno
            snippet = lines[line_no - 1].strip() if 0 < line_no <= len(lines) else ""

            # 1. Bare except:
            if node.type is None:
                violations.append(AuditViolation(
                    file_path, line_no, "RULE-2-BARE-EXCEPT",
                    "Bare 'except:' caught without specifying an exception type. Banned under Zero Silent Failures.",
                    snippet
                ))
                continue

            # 2. Contains pass or ellipsis (...)
            has_pass = any(isinstance(stmt, ast.Pass) for stmt in node.body)
            has_ellipsis = any(isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis for stmt in node.body)

            if has_pass or has_ellipsis:
                violations.append(AuditViolation(
                    file_path, line_no, "RULE-2-PASS-SWALLOWED",
                    f"Swallowed exception: 'except {exc_str}:' contains 'pass' or '...' with no diagnostic handling or logging.",
                    snippet
                ))
                continue

            # 3. Broad exception without logging, raise, or honest error return
            is_broad = (exc_str in ["Exception", "BaseException"] or exc_str.startswith("Exception,") or exc_str.endswith(", Exception)"))
            if is_broad:
                has_logging = any(is_diagnostic_call(c) for c in ast.walk(node) if isinstance(c, ast.Call))
                has_surface = surfaces_error_in_return(node, name)

                if not has_logging and not has_surface:
                    violations.append(AuditViolation(
                        file_path, line_no, "RULE-2-UNLOGGED-BROAD-EXCEPT",
                        f"Unlogged broad exception: 'except {exc_str}:' must log diagnostics (logger.debug/error, sys.stderr.write), re-raise, or return an explicit failure state.",
                        snippet
                    ))

        # --- Check 2: Subprocess stderr Blackholing ---
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id

            if func_name in ["run", "Popen", "call", "check_call", "check_output"]:
                for kw in node.keywords:
                    if kw.arg == "stderr":
                        val_str = ast.unparse(kw.value)
                        if "DEVNULL" in val_str:
                            line_no = node.lineno
                            snippet = lines[line_no - 1].strip() if 0 < line_no <= len(lines) else ""
                            violations.append(AuditViolation(
                                file_path, line_no, "RULE-1-STDERR-DEVNULL",
                                f"Banned subprocess stderr blackholing ('stderr={val_str}'). Capture stderr or redirect to log file.",
                                snippet
                            ))

    return violations


def audit_shell_file(file_path: str) -> List[AuditViolation]:
    """
    Audits shell script files for operational error swallowing.
    """
    violations = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        # Skip pure comments
        if line.startswith("#"):
            continue

        # Allowed presence check patterns
        is_presence_check = any(pattern in line for pattern in [
            "command -v", "type -p", "which ", "grep -q", "is-active", "if ! ", "if [", "if [["
        ])

        # Check for 2>/dev/null on non-presence-check commands
        if "2>/dev/null" in line and not is_presence_check:
            # Check if this is an explicitly documented safe uninstaller/teardown line
            if "uninstall.sh" in file_path and any(k in line for k in ["pkill", "rm -f"]):
                # Legacy process killing or cache deletion during complete teardown
                continue
            violations.append(AuditViolation(
                file_path, idx, "RULE-1-SHELL-STDERR-BLACKHOLE",
                "Operational command redirects stderr to /dev/null ('2>/dev/null'). Banned under Zero Silent Failures.",
                line
            ))

        # Check for || true masking non-cleanup commands
        if "|| true" in line and not is_presence_check:
            if "uninstall.sh" in file_path:
                # In uninstaller, allow clean teardown fallback only if documented
                continue
            violations.append(AuditViolation(
                file_path, idx, "RULE-5-SHELL-MASKED-EXIT",
                "Blind '|| true' suppresses command failure without testing availability or logging warning.",
                line
            ))

    return violations


def get_target_files(custom_paths: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
    """
    Resolves Python and Shell files to audit.
    """
    if custom_paths:
        py_files = []
        sh_files = []
        for p in custom_paths:
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        fp = os.path.join(root, f)
                        if fp.endswith(".py") or f in ["purr", "purr-tray", "purr-integrate"]:
                            py_files.append(fp)
                        elif fp.endswith(".sh"):
                            sh_files.append(fp)
            elif os.path.isfile(p):
                if p.endswith(".sh"):
                    sh_files.append(p)
                else:
                    py_files.append(p)
        return py_files, sh_files

    py_files = [
        os.path.join(REPO_ROOT, "bin", "purr"),
        os.path.join(REPO_ROOT, "bin", "purr-integrate"),
        os.path.join(REPO_ROOT, "bin", "purr-tray"),
        os.path.join(REPO_ROOT, "scripts", "compact_changelog.py"),
        os.path.join(REPO_ROOT, "scripts", "release.py"),
        os.path.join(REPO_ROOT, "scripts", "audit_errors.py"),
    ]

    # Add recipes
    recipes_dir = os.path.join(REPO_ROOT, "recipes")
    if os.path.exists(recipes_dir):
        for root, _, files in os.walk(recipes_dir):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))

    sh_files = [
        os.path.join(REPO_ROOT, "install.sh"),
        os.path.join(REPO_ROOT, "uninstall.sh"),
        os.path.join(REPO_ROOT, "setup-ecosystem.sh"),
    ]

    return py_files, sh_files


def main():
    parser = argparse.ArgumentParser(
        prog="audit_errors.py",
        description="🐾 Purr Zero Silent Failures & Error Swallowing Auditor"
    )
    parser.add_argument("paths", nargs="*", help="Specific files or directories to audit (defaults to entire repository)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only output on violation")
    args = parser.parse_args()

    py_files, sh_files = get_target_files(args.paths if args.paths else None)

    if not args.quiet:
        print(f"{Colors.BOLD}{Colors.CYAN}===================================================================================={Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}    🐾 Purr Maintainability Invariant Step 7: Zero Error Swallowing Audit          {Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}===================================================================================={Colors.RESET}\n")
        print(f"  • Auditing {len(py_files)} Python files and {len(sh_files)} Shell scripts...")

    total_violations = []

    for pf in py_files:
        if os.path.exists(pf):
            violations = audit_python_file(pf)
            total_violations.extend(violations)

    for sf in sh_files:
        if os.path.exists(sf):
            violations = audit_shell_file(sf)
            total_violations.extend(violations)

    if total_violations:
        print(f"\n{Colors.BOLD}{Colors.RED}[✘] FAILED: Found {len(total_violations)} error swallowing / silent failure violation(s):{Colors.RESET}\n")
        for v in total_violations:
            print(str(v))
        print(f"{Colors.YELLOW}Remediation guidance:{Colors.RESET}")
        print("  1. Replace 'except ...: pass' with explicit logging ('logger.debug(...)', 'logger.error(...)', or 'sys.stderr.write(...)').")
        print("  2. Replace bare 'except:' with explicit exception types ('except Exception as e:').")
        print("  3. Never blackhole subprocess stderr via 'stderr=subprocess.DEVNULL'; redirect to log or capture.")
        print("  4. Comply with docs/CODING_STANDARDS.md before committing code.\n")
        sys.exit(1)
    else:
        if not args.quiet:
            print(f"\n{Colors.BOLD}{Colors.GREEN}[✔] SUCCESS: 0 error swallowing or silent failure violations detected.{Colors.RESET}")
            print(f"{Colors.GREEN}    Codebase strictly complies with Step 7 In-Lockstep Maintainability & CODING_STANDARDS.md.{Colors.RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
