---
name: psl-stack-shell
description: >-
  Strict bash shell scripting standards and operational command patterns for Google Antigravity.
  Use when writing, debugging, or executing shell scripts, bash pipelines, system automation commands,
  or pattern-probing commands (grep, diff).
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2026 Arafat Zahan (@kuasha420) -->
<!-- Corporate Stewardship & Infrastructure: Purrfect Software Limited (PSL) -->
<!-- Governed by: ICARO-42/b Ordinance (Company-Supported Personal IP Framework) -->

# PSL Stack Skill: Shell Scripting & Terminal Command Hygiene

This skill codifies empirical shell scripting invariants and safe command execution patterns for Google Antigravity harnesses across Linux and POSIX environments.

---

## 1. Core Script Invariants

### 1.1 Mandatory Script Header
Every shell script or embedded execution block must enforce strict POSIX error handling:
```bash
#!/usr/bin/env bash
set -euo pipefail
```
- `-e`: Exit immediately on unhandled command failure.
- `-u`: Treat unset variables as errors and exit immediately.
- `-o pipefail`: Return the exit status of the first failing command in a pipeline.

### 1.2 ADR-013 Pattern Probing Exit Exception
Under `set -e` and `pipefail`, commands like `grep`, `diff`, or `pgrep` exit with return code `1` when no matches are found. This is a benign condition during inspection or validation, not a runtime failure.

- **INVARIANT**: Never allow unhandled `grep` or `diff` to abruptly crash under `set -e`.
- **INVARIANT**: Standalone probing commands must explicitly handle exit code 1:
  ```bash
  # Pattern probing with safe exit 1 handling
  grep "PATTERN" file.txt || [ $? -eq 1 ]
  
  # Or within a pipeline:
  diff -u old.txt new.txt || [ $? -eq 1 ]
  ```
- **ANTI-PATTERN**: Never use naked `|| true` on probing commands. Naked `|| true` swallows exit code `2` (syntax error) and exit code `127` (missing binary), concealing genuine system defects.

---

## 2. Command Safety & Environment Invariants

### 2.1 Exit 127 Mitigation (Binary Pre-flight)
Before invoking non-standard binaries, CLI tools, or external utilities, verify binary presence using `command -v`:
```bash
command -v rg >/dev/null 2>&1 || {
    echo "Error: ripgrep (rg) not found in PATH" >&2
    exit 127
}
```

### 2.2 Context Flood Prevention
Commands that generate unbounded output (e.g. `find`, large logs, test traces, or database dumps) must be bounded to protect the token budget and prevent attention saturation:
```bash
# Good: Constrained output preview
find . -type f -name "*.py" | head -n 50
git log -n 10 --oneline
cat output.log | tail -n 100

# For counting matches without flooding:
grep -c "pattern" file.txt || [ $? -eq 1 ]
```

### 2.3 Multi-Line Script Hygiene
Avoid escaping long, complex multi-line bash `-c` strings containing nested quotes, f-strings, or subshells. Escaped one-liners frequently corrupt whitespace, quote nesting, and variable interpolation.
- Write multi-line scripts to an isolated file in `scratch/`:
  ```bash
  cat <<'EOF' > scratch/verify_step.sh
  #!/usr/bin/env bash
  set -euo pipefail
  python3 -c "import harness; print(harness.__version__)"
  EOF
  chmod +x scratch/verify_step.sh
  ./scratch/verify_step.sh
  ```
- Always use single-quoted `<<'EOF'` heredocs when variable expansion is not desired at generation time.

---

## 3. Remote Execution Invariants (ADR-027)

### 3.1 OpenSSH Multiplexing & Socket Directory Invariant
- Always enable OpenSSH multiplexing for programmatic/agentic SSH commands:
  ```bash
  -o ControlMaster=auto -o ControlPath=~/.cache/psl/ssh/cm_%C -o ControlPersist=10m -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=15
  ```
- **Socket Path Security**: Keep ControlPath within user space (`~/.cache/psl/ssh/`) with strict `0700` permissions. Use `%C` (hash) to prevent socket path length exhaustion against the 108-byte UNIX socket limit.

### 3.2 Non-Login `$PATH` Elimination (Login-Shell Promotion)
- Non-interactive SSH commands bypass `.bashrc` and NVM PATH shims, causing false `Exit Code 127` failures when invoking toolchain binaries (`pm2`, `node`, `pnpm`, `cargo`, `nvm`, `uv`).
- **INVARIANT**: Wrap remote toolchain invocations in a login shell (`bash -l -c '...'`) unless explicit `PATH=` is defined:
  ```bash
  ssh host "bash -l -c 'pm2 status'"
  ```

### 3.3 Remote ADR-013 Pattern Probing Sanitization
- Remote grep/diff commands must have `|| [ $? -eq 1 ]` placed **inside** the remote execution payload, preventing false exits from zero matches:
  ```bash
  ssh host "grep ERROR /var/log/app.log || [ \$? -eq 1 ]"
  ```
- Never leave `|| [ $? -eq 1 ]` unquoted outside the SSH argument; doing so evaluates `$?` locally rather than on the remote host.

### 3.4 Zero-Disk-Footprint Stdin Script Streaming
- Favor streaming local scripts into remote interpreters over `scp` + remote file creation:
  ```bash
  # Python stdin streaming
  ssh host "python3 -s -" < local_script.py
  # Bash stdin streaming
  ssh host "bash -l -s -- arg1 arg2" < local_script.sh
  ```
- When file staging is required (`--stage`), always enclose the staging directory in an EXIT trap:
  ```bash
  ssh host "mkdir -p /tmp/.psl_remote_xyz && trap 'rm -rf /tmp/.psl_remote_xyz' EXIT; ..."
  ```

---

## 4. Operational Command Verification Checklist

1. [ ] Does the script begin with `set -euo pipefail`?
2. [ ] Do pattern-probing commands (`grep`, `diff`, `pgrep`) append `|| [ $? -eq 1 ]`?
3. [ ] Are external dependencies checked with `command -v` before execution?
4. [ ] Are high-volume command outputs constrained with `head -n`, `tail -n`, or `--limit`?
5. [ ] Are complex scripts stored in `scratch/` rather than passed as unwieldy inline `-c` strings?
6. [ ] Are remote commands executed with OpenSSH multiplexing and selective `bash -l -c`?
7. [ ] Are remote pattern probes sanitized inside quotes?
8. [ ] Do staged remote scripts include an automatic `trap 'rm -rf ...' EXIT` cleanup handler?
