# 🐾 Purr Project Coding Standards & Engineering Principles

> **Status**: Mandatory across all codebases, recipes, scripts, and AI-assisted contributions.  
> **Core Doctrine**: **Zero Silent Failures (Fail Loudly & Surface Diagnostics)**.

---

## 1. The Zero Silent Failures Doctrine

In systems programming (managing Linux cgroups, BinderFS, OverlayFS, APK signing, KWin DBus, systemd, and pacman/yay), silent errors are catastrophic. Masking an error causes downstream systems to fail in bizarre, untraceable ways, turning a 30-second fix into hours of debugging.

### Rule 1: No Blind Stderr Redirection (`DEVNULL` Blackholing Banned)
- **Banned**:
  - `2>/dev/null` or `>/dev/null 2>&1` in shell scripts.
  - `stderr=subprocess.DEVNULL` in Python subprocess calls.
- **Exceptions**:
  - Only allowed in tight polling loops (e.g. `lxc-info` querying status every 200ms) *provided* that if the loop times out, the final error state and command output are captured and logged or returned.
- **Required Pattern**:
  - Capture stderr via `capture_output=True` (or `stderr=subprocess.PIPE`) and check `returncode`.
  - When background services or daemons are spawned, redirect their output to a persistent log file (e.g. `~/.local/share/purr/daemon.log` or `~/.local/share/waydroid/session.log`) or syslog via `systemd-cat` / `logger`, never to `/dev/null`.

```python
# ❌ UNACCEPTABLE: Silent blackholing
subprocess.Popen(["sudo", "tee", path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ✅ REQUIRED: Transparent error propagation
p = subprocess.Popen(["sudo", "tee", path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
_, err = p.communicate(input=content)
if p.returncode != 0:
    logger.error(f"Failed to write to {path}: {err.strip()}")
    raise RuntimeError(f"Failed to write to {path}: {err.strip()}")
```

---

### Rule 2: No Blind Exception Swallowing (No Pokémon Exception Handling)
- **Banned**:
  - Bare `except:` without an exception type.
  - `except Exception: pass` without logging or telemetry.
- **Required Pattern**:
  - Catch specific exceptions whenever possible (`FileNotFoundError`, `subprocess.CalledProcessError`, `KeyError`).
  - If a broad `except Exception:` is necessary as a top-level safety net, the exception MUST be logged at least with `logger.debug("...", exc_info=True)` or `logger.warning("...")`.
  - Never let an exception evaporate into thin air.

```python
# ❌ UNACCEPTABLE: Swallowing everything blindly
try:
    clear_caches()
except Exception:
    pass

# ✅ REQUIRED: Traceable logging
try:
    clear_caches()
except Exception as e:
    logger.warning(f"Cache cleanup encountered a non-fatal error: {e}", exc_info=True)
```

---

### Rule 3: No False Success ("Lethal Optimism" Banned)
- **Banned**:
  - Returning `(True, "Skipped ...")` or `(True, "... pattern not found")` when an operation failed, was skipped due to missing prerequisites, or did not perform its promised work.
  - Returning exit code 0 when a core operation did not run.
- **Required Pattern**:
  - If an operation cannot complete because a prerequisite tool is missing (e.g. `zipalign`, `apksigner`, `kwriteconfig6`), it MUST return `(False, "Missing prerequisite: ...")`.
  - If a patch helper cannot find its target pattern in an upstream file, it MUST return `(False, "Pattern mismatch in <file>: upstream structure may have changed")` unless the file is already verified to be patched.
  - Never tell the caller that an operation succeeded when it did not.

```python
# ❌ UNACCEPTABLE: Masquerading failure as success
try:
    zipalign = _find_sdk_tool("zipalign")
except FileNotFoundError as e:
    return True, f"Titlebar patch skipped: {e}"  # Caller assumes framework was patched!

# ✅ REQUIRED: Honest status reporting
try:
    zipalign = _find_sdk_tool("zipalign")
except FileNotFoundError as e:
    logger.error(f"Required build tool missing: {e}")
    return False, f"Missing required Android SDK build tool: {e}. Install android-sdk-build-tools."
```

---

### Rule 4: Forensic Subprocess Error Transparency
- When using `subprocess.run(..., check=True)`, catch `subprocess.CalledProcessError` and unpack `e.stderr`. Python's default `str(e)` only outputs `Command '...' returned non-zero exit status 1.`, leaving out the actual stderr text.
- Inspect `res.returncode` when `check=False` is used, and log or return `res.stderr.strip()`.

```python
# ✅ REQUIRED: Extracting real stderr diagnostics
try:
    res = subprocess.run(cmd, check=True, capture_output=True, text=True)
except subprocess.CalledProcessError as e:
    err_msg = (e.stderr or "").strip() or (e.stdout or "").strip() or str(e)
    logger.error(f"Command {' '.join(cmd)} failed (code {e.returncode}): {err_msg}")
    return False, f"Command failed: {err_msg}"
```

---

### Rule 5: No Blind `|| true` Masking in Shell Scripts
- **Banned**:
  - Appending `|| true` to critical commands in Makefiles, installation scripts, or ecosystem setups to artificially force a zero exit status.
- **Required Pattern**:
  - Test for command availability first (`if command -v foo >/dev/null 2>&1; then ... fi`).
  - If a step is non-fatal, log an explicit warning rather than swallowing the exit status (`cmd || echo "==> [!] Warning: non-fatal step failed"`).

---

## 2. In-Lockstep Maintainability Step 7: Automated Static Audit & Enforcement

To prevent silent failures and error swallowing from entering committed code, the Purr ecosystem enforces **Step 7 of the In-Lockstep Maintainability Invariant** through an automated AST and structural auditor (`scripts/audit_errors.py`).

### Verification & CI Integration
- **Local Developer Target**:
  ```bash
  make audit-errors
  ```
- **Test Suite Requirement**: `make test` executes `audit-errors` before running py_compile, CLI tests, or recipe diagnostics. Any violation immediately aborts the test suite.
- **Release Gate**: `scripts/release.py` executes `audit_errors.py` during pre-flight checks. Releases cannot be tagged or pushed if any swallowed error exists in the working directory.
- **GitHub Actions CI**: `.github/workflows/ci.yml` validates `python3 scripts/audit_errors.py` on all pull requests and pushes to `main`.

### Automated Checks Performed
1. **`RULE-1-STDERR-DEVNULL`**: Flags any `subprocess` invocation with `stderr=subprocess.DEVNULL`.
2. **`RULE-2-BARE-EXCEPT`**: Flags any bare `except:` clause (catches `BaseException` / system interrupts blindly).
3. **`RULE-2-PASS-SWALLOWED`**: Flags any `except` handler whose body contains `pass` or `...` without diagnostic handling or logging.
4. **`RULE-2-UNLOGGED-BROAD-EXCEPT`**: Flags any `except Exception:` block that neither logs forensic diagnostics (`logger.debug/error`, `sys.stderr.write`, `log_error`), nor re-raises, nor returns an explicit failure state (`RecipeResult(False, ...)`, `return False, ...`).
5. **`RULE-1-SHELL-STDERR-BLACKHOLE` & `RULE-5-SHELL-MASKED-EXIT`**: Flags operational `2>/dev/null` blackholing and unhandled `|| true` error masking in shell scripts.
