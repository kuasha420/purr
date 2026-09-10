#!/usr/bin/python3
"""
🐾 Purr Release Automation Engine
Project Tuki / Purr Ecosystem

Automates atomic version propagation in lockstep across all codebase locations,
regenerates packaging definitions, executes verification suites, cuts git commits
and annotated tags, and publishes releases to origin.
"""

import sys
import os
import re
import subprocess
import datetime
import argparse
from typing import Dict, List, Tuple, Optional


class Colors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def log_step(msg: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}==> {msg}{Colors.RESET}")


def log_success(msg: str):
    print(f"{Colors.BOLD}{Colors.GREEN}[✔] {msg}{Colors.RESET}")


def log_error(msg: str):
    print(f"{Colors.BOLD}{Colors.RED}[✘] Error: {msg}{Colors.RESET}", file=sys.stderr)


def log_warning(msg: str):
    print(f"{Colors.BOLD}{Colors.YELLOW}[!] Warning: {msg}{Colors.RESET}")


def check_git_status(dry_run: bool = False) -> None:
    """
    Ensures git repository is clean and on main branch.
    """
    if dry_run:
        return

    # Check branch
    res_branch = subprocess.run(["git", "-C", REPO_ROOT, "branch", "--show-current"], capture_output=True, text=True)
    branch = res_branch.stdout.strip()
    if branch != "main":
        log_warning(f"Current git branch is '{branch}', not 'main'.")

    # Check for uncommitted changes
    res_diff = subprocess.run(["git", "-C", REPO_ROOT, "status", "--porcelain"], capture_output=True, text=True)
    uncommitted = [l for l in res_diff.stdout.splitlines() if not l.startswith("??")]
    if uncommitted:
        log_error("Git working directory has uncommitted changes:")
        for line in uncommitted:
            print(f"    {line}", file=sys.stderr)
        log_error("Please commit or stash your changes before cutting a release.")
        sys.exit(1)


def check_tag_exists(version: str) -> None:
    tag = f"v{version}"
    res = subprocess.run(["git", "-C", REPO_ROOT, "tag", "-l", tag], capture_output=True, text=True)
    if tag in res.stdout.split():
        log_error(f"Git tag '{tag}' already exists! Cannot re-release existing version.")
        sys.exit(1)


def get_current_version() -> str:
    bin_purr = os.path.join(REPO_ROOT, "bin", "purr")
    with open(bin_purr, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not m:
        raise ValueError("Could not determine current version from bin/purr")
    return m.group(1).strip()


def update_file_regex(file_path: str, pattern: str, replacement: str, dry_run: bool = False) -> bool:
    """
    Atomically updates pattern in file_path.
    """
    abs_path = os.path.join(REPO_ROOT, file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.exists(abs_path):
        log_error(f"Target file not found: {abs_path}")
        return False

    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count == 0:
        log_warning(f"No match found for pattern in {file_path}")
        return False

    if not dry_run:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    return True


def propagate_version(old_ver: str, new_ver: str, codename: str, descriptive_name: str, dry_run: bool = False) -> List[str]:
    """
    Propagates version in lockstep across all 10+ codebase locations.
    """
    now = datetime.datetime.now()
    month_year = now.strftime("%B %Y")
    date_str = now.strftime("%Y-%m-%d")
    updated_files = []

    # 1. bin/purr
    if update_file_regex("bin/purr", r'__version__\s*=\s*["\'][^"\']+["\']', f'__version__ = "{new_ver}"', dry_run):
        update_file_regex("bin/purr", r'🐾 purr \(Project Tuki\) — Version [0-9A-Za-z\.-]+', f'🐾 purr (Project Tuki) — Version {new_ver}', dry_run)
        updated_files.append("bin/purr")

    # 2. bin/purr-tray
    if update_file_regex("bin/purr-tray", r'__version__\s*=\s*["\'][^"\']+["\']', f'__version__ = "{new_ver}"', dry_run):
        updated_files.append("bin/purr-tray")

    # 3. bin/purr-integrate
    if update_file_regex("bin/purr-integrate", r'__version__\s*=\s*["\'][^"\']+["\']', f'__version__ = "{new_ver}"', dry_run):
        updated_files.append("bin/purr-integrate")

    # 4. install.sh
    if update_file_regex("install.sh", r'PURR_VERSION\s*=\s*["\'][^"\']+["\']', f'PURR_VERSION="{new_ver}"', dry_run):
        updated_files.append("install.sh")

    # 5. PKGBUILD
    if update_file_regex("PKGBUILD", r'^pkgver=.*$', f'pkgver={new_ver}', dry_run):
        update_file_regex("PKGBUILD", r'^pkgrel=.*$', 'pkgrel=1', dry_run)
        updated_files.append("PKGBUILD")

    # 6. recipes/base.py
    if update_file_regex("recipes/base.py", r'version:\s*str\s*=\s*["\'][^"\']+["\']', f'version: str = "{new_ver}"', dry_run):
        updated_files.append("recipes/base.py")

    # 7. recipes/waydroid_native/recipe.json
    if update_file_regex("recipes/waydroid_native/recipe.json", r'"version":\s*["\'][^"\']+["\']', f'"version": "{new_ver}"', dry_run):
        updated_files.append("recipes/waydroid_native/recipe.json")

    # 8. recipes/waydroid_native/recipe.py
    if update_file_regex("recipes/waydroid_native/recipe.py", r'version\s*=\s*["\'][^"\']+["\']', f'version = "{new_ver}"', dry_run):
        updated_files.append("recipes/waydroid_native/recipe.py")

    # 9. Manpages (.TH macro)
    man_files = ["man/man1/purr.1", "man/man1/purr-tray.1", "man/man1/purr-integrate.1", "man/man1/tuki.1"]
    for mf in man_files:
        th_pattern = r'(\.TH\s+\S+\s+1\s+")[^"]*("\s+")purr\s+[^"]*(")'
        th_repl = rf'\g<1>{month_year}\g<2>purr {new_ver}\g<3>'
        if update_file_regex(mf, th_pattern, th_repl, dry_run):
            updated_files.append(mf)

    # 10. docs/ROADMAP.md
    if codename:
        roadmap_pattern = r'### Phase 2: Purr Recipes, Android Native Subsystem & Interactive Curation \([^\)]+\)'
        roadmap_repl = f'### Phase 2: Purr Recipes, Android Native Subsystem & Interactive Curation (v{new_ver} — *{codename}*) — *Completed*'
        if update_file_regex("docs/ROADMAP.md", roadmap_pattern, roadmap_repl, dry_run):
            updated_files.append("docs/ROADMAP.md")

    # 11. CHANGELOG.md
    changelog_path = os.path.join(REPO_ROOT, "CHANGELOG.md")
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            cl_content = f.read()

        # Check if version already exists as a header
        if f"## [{new_ver}]" not in cl_content:
            # Transform ## [n.e.x.t] into ## [n.e.x.t]\n\n## [<new_ver>] ...
            header_desc = f" — *{codename}* ({descriptive_name})" if codename and descriptive_name else (f" — {descriptive_name}" if descriptive_name else "")
            new_header = f"## [{new_ver}] - {date_str}{header_desc}"
            
            # Pattern matching ## [n.e.x.t] line
            next_header_pattern = r'##\s+\[n\.e\.x\.t\][^\n]*\n'
            m = re.search(next_header_pattern, cl_content)
            if m:
                # Replace n.e.x.t with new release header and prepend fresh empty n.e.x.t template
                template_next = "## [n.e.x.t] - YYYY-MM-DD\n\n"
                replacement = f"{template_next}{new_header}\n"
                new_cl = cl_content[:m.start()] + replacement + cl_content[m.end():]
                if not dry_run:
                    with open(changelog_path, "w", encoding="utf-8") as f:
                        f.write(new_cl)
                updated_files.append("CHANGELOG.md")
            else:
                log_warning("Could not locate '## [n.e.x.t]' header in CHANGELOG.md to convert.")
        else:
            updated_files.append("CHANGELOG.md")

    return updated_files


def regenerate_srcinfo(dry_run: bool = False) -> None:
    """
    Executes makepkg --printsrcinfo > .SRCINFO.
    """
    log_step("Regenerating .SRCINFO packaging definitions...")
    if dry_run:
        print("  [dry-run] Would execute: makepkg --printsrcinfo > .SRCINFO")
        return

    res = subprocess.run(["makepkg", "--printsrcinfo"], cwd=REPO_ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        log_error(f"Failed to generate .SRCINFO: {res.stderr}")
        sys.exit(1)

    with open(os.path.join(REPO_ROOT, ".SRCINFO"), "w", encoding="utf-8") as f:
        f.write(res.stdout)
    log_success(".SRCINFO successfully updated.")


def run_tests(dry_run: bool = False) -> None:
    """
    Runs make test and make aur.
    """
    log_step("Executing verification test suites (make test & make aur)...")
    res_test = subprocess.run(["make", "test"], cwd=REPO_ROOT)
    if res_test.returncode != 0:
        log_error("make test failed! Aborting release.")
        sys.exit(1)

    res_aur = subprocess.run(["make", "aur"], cwd=REPO_ROOT)
    if res_aur.returncode != 0:
        log_error("make aur validation failed! Aborting release.")
        sys.exit(1)

    log_success("All test suites and AUR validations passed cleanly.")


def commit_and_tag(version: str, codename: str, descriptive_name: str, auto_push: bool, dry_run: bool = False) -> None:
    """
    Creates release commit, annotated tag, and pushes to origin.
    """
    tag = f"v{version}"
    commit_msg = f"chore(release): {tag} ({codename})" if codename else f"chore(release): {tag}"
    tag_msg = f"Release {tag}: {codename} ({descriptive_name})" if codename and descriptive_name else f"Release {tag}"

    log_step(f"Creating git release commit and annotated tag {tag}...")

    if dry_run:
        print(f"  [dry-run] git add -A")
        print(f"  [dry-run] git commit -m '{commit_msg}'")
        print(f"  [dry-run] git tag -a {tag} -m '{tag_msg}'")
        if auto_push:
            print(f"  [dry-run] git push --follow-tags origin main")
        return

    # Add all modified files
    subprocess.run(["git", "-C", REPO_ROOT, "add", "-A"], check=True)

    # Commit
    res_commit = subprocess.run(["git", "-C", REPO_ROOT, "commit", "-m", commit_msg], capture_output=True, text=True)
    if res_commit.returncode != 0:
        log_error(f"git commit failed: {res_commit.stderr}")
        sys.exit(1)
    log_success(f"Release commit created: '{commit_msg}'")

    # Tag
    res_tag = subprocess.run(["git", "-C", REPO_ROOT, "tag", "-a", tag, "-m", tag_msg], capture_output=True, text=True)
    if res_tag.returncode != 0:
        log_error(f"git tag failed: {res_tag.stderr}")
        sys.exit(1)
    log_success(f"Annotated tag '{tag}' created successfully.")

    # Auto push
    if auto_push:
        log_step(f"Pushing release {tag} and branch to origin...")
        res_push = subprocess.run(["git", "-C", REPO_ROOT, "push", "--follow-tags", "origin", "main"], capture_output=True, text=True)
        if res_push.returncode != 0:
            log_error(f"git push failed: {res_push.stderr}")
            sys.exit(1)
        log_success(f"Successfully pushed {tag} and commits to origin/main!")


def main():
    parser = argparse.ArgumentParser(
        prog="release.py",
        description="🐾 Purr Automated Lockstep Release Engine (Project Tuki)"
    )
    parser.add_argument("--version", "-v", required=True, help="Target release version (e.g. 1.1.0)")
    parser.add_argument("--codename", "-c", default="", help="Feline scientific codename (e.g. 'Prionailurus bengalensis')")
    parser.add_argument("--descriptive-name", "-d", default="", help="Descriptive release name (e.g. 'Purr Recipes & Android Native Subsystem')")
    parser.add_argument("--dry-run", action="store_true", help="Simulate release workflow without modifying git state")
    parser.add_argument("--no-push", action="store_true", help="Do not push tags and commits to origin")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running make test and make aur (for testing only)")

    args = parser.parse_args()

    version = args.version.lstrip("v").strip()
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        log_error(f"Invalid semantic version: '{version}'. Must follow format X.Y.Z.")
        sys.exit(1)

    print(f"{Colors.BOLD}{Colors.CYAN}===================================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}             🐾 Purr Release Engine — Cutting v{version} (Project Tuki)             {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}===================================================================================={Colors.RESET}\n")

    current_ver = get_current_version()
    print(f"  • Current codebase version : {Colors.BOLD}{current_ver}{Colors.RESET}")
    print(f"  • Target release version   : {Colors.BOLD}{version}{Colors.RESET}")
    print(f"  • Codename                 : {Colors.BOLD}{args.codename or 'None'}{Colors.RESET}")
    print(f"  • Descriptive Name         : {Colors.BOLD}{args.descriptive_name or 'None'}{Colors.RESET}")
    print(f"  • Dry-Run Mode             : {Colors.BOLD}{args.dry_run}{Colors.RESET}")
    print(f"  • Automated Push           : {Colors.BOLD}{not args.no_push}{Colors.RESET}")

    # 1. Pre-flight checks
    log_step("Executing pre-flight checks...")
    check_git_status(dry_run=args.dry_run)
    check_tag_exists(version)
    log_success("Pre-flight checks passed.")

    # 2. Lockstep Version Propagation
    log_step(f"Propagating version {current_ver} -> {version} across 10+ codebase locations...")
    updated_files = propagate_version(
        old_ver=current_ver,
        new_ver=version,
        codename=args.codename,
        descriptive_name=args.descriptive_name,
        dry_run=args.dry_run
    )
    for uf in updated_files:
        print(f"  ✔ Updated: {uf}")
    log_success(f"Updated {len(updated_files)} files in lockstep.")

    # 3. Regenerate .SRCINFO
    regenerate_srcinfo(dry_run=args.dry_run)

    # 4. Verify test suite
    if not args.skip_tests:
        run_tests(dry_run=args.dry_run)

    # 5. Commit, tag, and push
    commit_and_tag(
        version=version,
        codename=args.codename,
        descriptive_name=args.descriptive_name,
        auto_push=(not args.no_push),
        dry_run=args.dry_run
    )

    print(f"\n{Colors.BOLD}{Colors.GREEN}===================================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}       🐾 Release v{version} Completed Successfully! System is Purring.             {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}===================================================================================={Colors.RESET}\n")


if __name__ == "__main__":
    main()
