---
name: psl-stack-systems
description: >-
  Systems engineering, Linux/Wayland automation, and workstation configuration standards.
  Use when managing system configurations, background services, network probes, or Wayland/desktop automation.
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2026 Arafat Zahan (@kuasha420) -->
<!-- Corporate Stewardship & Infrastructure: Purrfect Software Limited (PSL) -->
<!-- Governed by: ICARO-42/b Ordinance (Company-Supported Personal IP Framework) -->

# PSL Stack Skill: Systems Engineering, Linux Automation & Configuration

This skill codifies systems engineering best practices, Linux/Wayland desktop automation protocols, and workstation configuration invariants.

---

## 1. Linux & Wayland Desktop Automation

### 1.1 Non-Destructive Automation & Safe Fallbacks
- Automation scripts targeting Wayland, X11, KDE, or window managers must operate non-destructively.
- Never issue ungraceful kill commands (`kill -9`, `killall -9`) against display server processes, compositor daemons (e.g. `kwin_wayland`, `sway`, `hyprland`), or system session managers.
- Always use standard freedesktop / D-Bus interfaces or safe IPC commands when querying or steering desktop components.

### 1.2 User-Space Isolation (Zero-Sudo Invariant)
- Harness automation and developer tooling must run strictly in unprivileged user space.
- **NEVER** propose or execute `sudo` commands or attempt root privilege escalation in automated scripts.
- Store configuration, logs, and binaries in standardized user directories:
  - Config: `~/.config/` or `XDG_CONFIG_HOME`
  - Data: `~/.local/share/` or `XDG_DATA_HOME`
  - Binaries: `~/.local/bin/`

---

## 2. Configuration File Management

### 2.1 Atomic INI Parsing with Case Preservation
Standard Python `configparser.ConfigParser` automatically converts all keys to lowercase by default (`optionxform = str.lower`), corrupting case-sensitive configuration files (such as KDE config files, systemd unit files, or Git configs).

- **INVARIANT**: Always preserve case sensitivity when reading and writing INI configurations:
  ```python
  import configparser
  from pathlib import Path

  config = configparser.RawConfigParser(strict=False)
  config.optionxform = str  # Preserve exact case
  config.read(config_path, encoding="utf-8")
  ```

### 2.2 Atomic File Replacement
- Never write directly to live configuration files or database files in-place to avoid corruption during crashes or interruptions.
- Write to a sibling temporary file and atomically rename:
  ```python
  import os
  import tempfile
  from pathlib import Path

  target = Path("~/.config/app/settings.ini").expanduser()
  temp_file = target.with_suffix(".tmp")
  with open(temp_file, "w", encoding="utf-8") as f:
      config.write(f)
  os.replace(temp_file, target)
  ```

---

## 3. Network & Remote Probing Guards

### 3.1 Mandatory Network Probing Timeouts
- Unbounded network probes can block agent execution threads indefinitely when remote hosts or interfaces are unreachable.
- Any SSH probe, health check, or remote sync must include strict connection and batch timeouts:
  ```bash
  # SSH probe with strict connection timeout and non-interactive batch mode
  ssh -o ConnectTimeout=3 -o BatchMode=yes -o StrictHostKeyChecking=accept-new user@host "echo ok"

  # Curl probes with maximum time limits
  curl --connect-timeout 3 --max-time 10 -fsSL https://api.service.internal/health
  ```

---

## 4. Systems Verification Checklist

1. [ ] No `sudo` or root escalation commands used.
2. [ ] INI parser configures `optionxform = str` to preserve case.
3. [ ] Configuration updates committed via atomic temporary file replacement.
4. [ ] Network probes and SSH commands specify explicit connection timeouts.
5. [ ] Desktop automation handles Wayland/session fallbacks gracefully.
