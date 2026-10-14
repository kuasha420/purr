# 🐾 Purr Project & Architecture Invariants

## 1. System Python & Runtime Environment
- **System Python Shebangs**: All executable scripts in `bin/` (`purr`, `purr-tray`, `purr-integrate`) and subprocess launchers MUST target `/usr/bin/python3` to ensure system Qt bindings (`python-pyqt6`) and desktop libraries are loaded rather than user-level pyenv/virtualenv shims.
- **Dependency Guarding**: Always import PyQt6 and other desktop libraries inside `try/except ImportError` blocks with user-friendly remediation instructions.

## 2. Non-Destructive KDE Plasma 6 Desktop Integrations
- **Zero-Crash Task Manager Updates**: Never invoke destructive DBus methods like `refreshCurrentShell` or restart `plasmashell`.
- **In-Memory Configuration Reloads**: When modifying Task Manager pinned launchers (`org.kde.plasma.icontasks` / `taskmanager`), use `qdbus6 org.kde.plasmashell /PlasmaShell evaluateScript` to update the `launchers` configuration array and invoke `w.reloadConfig()`.

## 3. Package Management & Conflict Resolution
- **Pacman Automation**: Always pass `--needed --noconfirm --ask 4` (to auto-confirm package replacements) and use `--overwrite "*"` when resolving unowned file conflicts.
- **AUR (yay) Automation**: Always pass `--noconfirm --answerclean All --answerdiff None --answeredit None --answerupgrade None --removemake --cleanafter --overwrite "*"`.
- **Flatpak Maintenance**: Always pass `-y --noninteractive` and prune unreferenced/EOL runtimes via `flatpak uninstall --unused -y --noninteractive`.
- **Stale Locks**: Check and remove abandoned `/var/lib/pacman/db.lck` locks before starting package transactions.

## 4. In-Lockstep Maintainability Invariant
Whenever any new CLI flag, subcommand, cache file, or desktop integration is added or modified, the following MUST be updated in lockstep:
1. Built-in CLI help (`parser.epilog` / `parser.description` in `bin/purr`)
2. UNIX manual pages in `man/man1/` (`purr.1`, `purr-tray.1`, `purr-integrate.1`, `tuki.1`)
3. Shell completions (`completions/purr.bash`, `completions/_purr.zsh`)
4. Installer (`install.sh`) and complete uninstaller (`uninstall.sh`)
5. Packaging definitions (`PKGBUILD`, `.SRCINFO`) via `make aur`
6. Project documentation (`README.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `CHANGELOG.md`)
7. **Zero Error Swallowing & Silent Failure Audit**: No error swallowing in committed code. Every `try/except` block must catch explicit exception types, log forensic diagnostics (`logger.debug(..., exc_info=True)`, `sys.stderr.write`, or `print(..., file=sys.stderr)`), or surface honest failure states upstream. Blind `except: pass`, unlogged broad catches, and subprocess stderr blackholing (`stderr=subprocess.DEVNULL`) are strictly prohibited and mechanically enforced via automated static AST audit (`make audit-errors` / `make test` / `python3 scripts/audit_errors.py`).

## 5. Versioning & Changelog Convention (`n.e.x.t`)
- **No Premature Version Bumping in PRs**: No pull request or feature branch may hardcode or reference a specific future release version (e.g. `1.1.0`, `1.2.0`).
- **Unreleased Heading Standard**: All unreleased features and changes in `CHANGELOG.md` and roadmap/feature documentation MUST be noted as `## [n.e.x.t] - YYYY-MM-DD`.
- **Release Workflow Finalization**: Concrete semantic version tags (`vX.Y.Z`) and actual release dates are strictly finalized in a separate release workflow where placeholders are replaced.

## 6. Debian-Style Feline Codename Taxonomy & Two-Tier Changelogs
- **Taxonomy Convention**: Major releases (`X.0.0`) use Big Cats (subfamily *Pantherinae*, e.g., *Panthera leo*). Minor releases (`X.Y.0`) use Small Cats (subfamily *Felinae*, e.g., *Prionailurus bengalensis*, *Otocolobus manul*). Scientific names are italicized in headers.
- **Two-Tier Changelog Structure**: All releases must feature:
  - **Tier 1**: `### 🌟 What's New For You` — Human-first outcomes written with warmth and empathy for everyday users.
  - **Tier 2**: `### 🔧 Under the Hood` — Forensic engineering specs, IPC mechanisms, and Zero Silent Failures compliance for systems engineers.
- **Automated Execution**: Once cut and marked for release, `scripts/release.py` executes atomically and deterministically without human interruption loops.

## 7. Subsystem State Convergence Invariant
- **Zero Container Wiping**: Routine package updates or recipe changes MUST NEVER invoke destructive re-provisioning (`waydroid init -f`) or erase user app databases, chats, or logins.
- **Convergence Lifecycle**: All recipes implement `is_deployed() -> bool` and `sync(options) -> RecipeResult`.
- **Automatic Host Upgrade Sync**: `purr upgrade` executes `sync_all_deployed()` in Step 4, converging all active subsystem overlays, companions, framework patches, and KWin rules whenever the host system updates.

<!-- Added by AGYIS-HARNESS -->
<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2026 Arafat Zahan (@kuasha420) -->
<!-- Corporate Stewardship & Infrastructure: Purrfect Software Limited (PSL) -->
<!-- Governed by: ICARO-42/b Ordinance (Company-Supported Personal IP Framework) -->

# Universal Empirical Agent Rules: Agyis Harness Guidelines

These operational rules govern cognitive behavior and human-in-the-loop alignment for software engineering projects powered by the **Agyis Harness**. All deterministic environment guarantees (runtime injection, pager normalization, surgical grep exit sanitization, output compaction) are enforced transparently by harness hooks.

---

## 1. Explicit Project Command Dictionary (The Victory Pattern)
*Explicit CLI palettes yield 10x lower human intervention rates:*

```bash
# 🧪 Project Verification & Native Toolchain
make test                                      # Run complete project test suite
make clean                                     # Clean build artifacts & caches
make install                                   # Install production copy to system
make dev                                       # Link repository live to /usr/local/bin for instant development
make help                                      # Execute help
make reload-tray                               # Execute reload-tray
make uninstall                                 # Execute uninstall
make integrate                                 # Execute integrate
make audit-errors                              # Execute audit-errors
make release                                   # Execute release
make release-check                             # Execute release-check
make changelog-compact                         # Execute changelog-compact

# 🩺 Environment Diagnostics & Auto-Healing
agyis doctor                                   # Audit workstation runtimes & auto-heal
agyis status                                   # Print harness health, active hooks & telemetry

# 🧩 Skills & Subagents Discovery
agyis skills                                   # List installed modular skills & triggers
agyis agents                                   # List registered specialist subagents & tools

# 🌐 Remote Operations & Cloud/Mesh Triage (ADR-027)
agyis remote exec <target> "<cmd>"             # Multiplexed SSH with login-shell promotion
agyis remote script <target> <file>            # Stdin script streaming (zero disk footprint)
agyis remote triage <target>                   # Compact (<2KB) multi-component health report

# 📊 Empirical Telemetry Laboratory
agyis sync                                     # Audit & synchronize active session telemetry
```

---

## 2. Mandatory Project-Native Automated Verification Contract
1. **Mandatory Automated Verification**:
   - Never declare a task "complete", "fixed", or "verified" without executing the active project's native test runner (e.g. `pnpm test`, `pytest`, `cargo test`, `go test`) and asserting exit code 0.
2. **Sub-Second to Fast Benchmark Invariant**:
   - Unit and integration tests must run as fast and hermetically as possible. Avoid slow network calls, unbounded sleeps, or unneeded whole-filesystem sweeps in verification loops.
3. **Hermetic Isolation**:
   - Tests must never access untracked external services without hermetic mocks or local temporary environments. All state-persisting operations should use temporary directories.

---

## 3. Terminal Invariants & Grep Probing Exception (ADR-013)
1. **Pre-flight Tool Availability (Mitigate Exit Code 127)**:
   - Verify tool availability (`command -v <bin>`) or handle fallback paths gracefully.
2. **Context Flood Prevention (The 200+ Step Cliff)**:
   - Never execute unfiltered commands that dump thousands of lines. Pipe large outputs through `head -n <N>`, `tail -n <N>`, or `wc -l`.
3. **Pattern Probing Exception**:
   - Error swallowing is banned in production code, but standalone terminal pattern probes (`grep`, `diff`) without conditionals must use `|| [ $? -eq 1 ]` to avoid panicking on benign empty matches.
4. **Multi-line Script Hygiene**:
   - Write multi-line scripts to temporary scratch files (`scratch/script.sh` or `scratch/script.py`) rather than escaping fragile multi-line bash `-c` one-liners.

---

## 4. Surgical Contiguous Edits Invariant (99.9% Tool Success)
*Audit revealed single contiguous block replacements achieve 99.9% tool success:*
1. Always make single contiguous block replacements for targeted edits (`replace_file_content`).
2. Do NOT overwrite whole files when modifying specific functions, classes, or blocks.
3. Preserve surrounding comments, docstrings, imports, and formatting.

---

## 5. Context Preservation & Subagent Ladder
*Trajectories <50 steps / <50k tokens maintain 0.8 errors/session; >200 steps suffer a 20x error spike:*
1. **Keep Primary Context in the Healthy Zone (<50k tokens)**.
2. **Anti-Loop Heuristics**:
   - Do NOT repeatedly call `view_file` on the same file within consecutive steps.
   - Evolve search queries; do not repeat identical `grep_search` patterns.
   - Never poll task status in a loop (`manage_task(Action='status')`); await reactive wakeups.
3. **Subagent Delegation Protocol**:
   - Decompose multi-phase refactoring, test debugging, or massive build sweeps, delegating to specialist subagents (`@harness_builder`, `@harness_reviewer`, `@harness_auditor`, `@planner`, `@harness_custodian`, `@coordinator`) in isolated worktrees (`Workspace: "share"` or `"branch"`).
   - Follow the 6-stage Ladder lifecycle: Plan -> Implement (Executioner) -> Review (Hammer) -> Commit Gate (Custodian) -> Verification (Auditor) -> Archival (Coordinator).

---

## 6. The Artifact-First Planning Invariant (ADR-012) & Dynamic Aperture
1. **Anti-Chatbot Seduction**:
   - Never propose multi-component architectural changes or execution plans in raw conversational chat turns.
   - All non-trivial proposals must immediately crystallize into an interactive `implementation_plan.md` artifact before requesting operator confirmation.
2. **Dynamic Sliding Aperture**:
   - High resolution for current task execution.
   - Medium resolution for near-future milestones (macro boundaries; no speculative code).
   - Low resolution for far-future vision.
3. **Retroactive Horizon Compaction**:
   - When completing a phase or milestone, compact findings into the project ledger under 50 lines, update the project roadmap, commit clean code to git, and instruct the operator to reset session.

---

## 7. The 5 Ground Rules
1. **Rule 1 (Zero Error Swallowing)**: Never hide or swallow errors. Zero bare `except:`, no unhandled pipe errors (`set -euo pipefail`).
2. **Rule 2 (No Product Homework in Tests)**: Never redefine product logic or duplicate production calculations in test asserts.
3. **Rule 3 (Complete Deliveries)**: Deliver complete packages (code + types + tests + docs). No partial drafts or broken stubs.
4. **Rule 4 (Zero Verification Homework)**: Self-verify all changes using the project's native test runner before declaring completion.
5. **Rule 5 (Stop & Inquire)**: Stop and ask the operator if an unforeseen blocker, architectural conflict, or ambiguity arises.

---

## 8. Human-in-the-Loop & Steering Alignment
1. **Anti-Drift Commitment**: Anchor all implementation decisions to the agreed plan. If novel obstacles arise, pause and present options.
2. **Proactive Confirmation Gates**: When encountering destructive operations (file deletion, git branch force-push, node reboots), pause for explicit review.
3. **Clear Error Reporting**: If a command fails twice, stop thrashing. State the error concisely and propose a concrete path forward.
<!-- End AGYIS-HARNESS -->
