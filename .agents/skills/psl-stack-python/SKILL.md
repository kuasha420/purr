---
name: psl-stack-python
description: >-
  Hermetic Python development standards and runtime execution hygiene for Agyis Harness.
  Use when writing, testing, or executing Python scripts, lifecycle hooks, CLI commands,
  or harness components.
---
<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2026 Arafat Zahan (@kuasha420) -->
<!-- Corporate Stewardship & Infrastructure: Purrfect Software Limited (PSL) -->
<!-- Governed by: ICARO-42/b Ordinance (Company-Supported Personal IP Framework) -->

# PSL Stack Skill: Python Runtime Hygiene & Test Invariants

This skill codifies empirical Python development standards, hermetic execution rules, and sub-second testing invariants for Agyis Harness.

---

## 1. Runtime Environment Invariants

### 1.1 Hermetic CPython >= 3.12 Enforcement
- All scripts and harness lifecycle hooks must target CPython >= 3.12.
- The harness dynamically discovers and prefers hermetic, isolated Python runtimes (e.g. from the `uv` python cache or isolated venvs) via `pipeline.psl_doctor.find_hermetic_uv_python()` or `sys.executable`.
- Never rely on mutating global system Python packages or running unpinned user-space dependencies.

### 1.2 Exception Hygiene & Strict Failure Transparency (Rule 1)
- **Absolute ban on bare `except:`** and `except Exception: pass`.
- Every handled exception must either:
  1. Recover deterministically with an explicit fallback or retry, OR
  2. Log the exact error context (`sys.stderr.write(f"Error: {e}\n")`) and exit with a non-zero exit code, OR
  3. Re-raise with causal context (`raise HarnessError("Failed to parse config") from err`).
- Never conceal runtime failures behind empty except blocks:
  ```python
  # BAD: Silent failure hides runtime defects
  try:
      config = json.loads(payload)
  except:
      pass

  # GOOD: Strict error handling with explicit failure reporting
  try:
      config = json.loads(payload)
  except json.JSONDecodeError as err:
      sys.stderr.write(f"Fatal: Invalid payload JSON at line {err.lineno}: {err}\n")
      sys.exit(1)
  ```

---

## 2. Testing & Isolation Invariants

### 2.1 Clean-Room Temporary Directory Isolation
- Tests and transient harness operations must never pollute the repository workspace with temporary files, state databases, or cache directories.
- Always use `tempfile.TemporaryDirectory()` (or redirect via `PSL_HARNESS_STATE_DIR` environment override) in test fixtures and tear them down in `tearDown()`:
  ```python
  import tempfile
  from pathlib import Path
  import unittest

  class TestIsolatedComponent(unittest.TestCase):
      def setUp(self):
          self.temp_dir = tempfile.TemporaryDirectory()
          self.state_path = Path(self.temp_dir.name)

      def tearDown(self):
          self.temp_dir.cleanup()
  ```

### 2.2 Sub-Second Test Invariant (ADR-015)
- The entire automated test suite (`agyis test`) must execute in strictly **under 1.0 second**.
- Unit tests must be hermetic and in-memory:
  - Do not make external network requests.
  - Do not introduce `time.sleep()` delays; mock time or use deterministic event loops.
  - Avoid unnecessary disk thrashing; use memory buffers (`io.StringIO`, `io.BytesIO`) or compact temporary directories.

### 2.3 Script Invocation & Syntax Hygiene
- For complex logic or multi-line automation, write standalone script modules instead of executing deeply nested inline `python3 -c "..."` commands that suffer from quote-escaping and f-string corruption in bash shells.
- In Python 3.12+, leverage modern type annotations (`list[T]`, `dict[K, V]`, `X | Y`) without deprecated `typing` imports where appropriate, maintaining backward compatibility when needed.

---

## 3. Python Verification Checklist

1. [ ] Code targets CPython >= 3.12.
2. [ ] Zero bare `except:` or `except Exception: pass` blocks.
3. [ ] All test state isolated in `tempfile.TemporaryDirectory()` or in-memory fixtures.
4. [ ] `agyis test` completes in <1.0s.
5. [ ] Explicit error logging and non-zero exit status on fatal paths.
