---
name: purr-release
description: >-
  Release orchestration and intelligent changelog compaction skill for the Purr ecosystem.
  Synthesizes development commits into Debian-style Feline-named releases, crafts Two-Tier product
  stories (Tier 1: Human outcomes; Tier 2: Engineering specs), updates CHANGELOG.md in lockstep,
  and executes automated release cycles.
---

# 🐾 Purr Release Orchestration & Intelligent Changelog Skill

This skill guides AI agents in cutting releases for Purr (Project Tuki). It bridges the gap between chaotic development commits and delightful, structured product releases.

---

## 1. Debian-Style Feline Taxonomy Convention

Every Purr release receives a dual name: a scientific feline codename and a descriptive release subtitle.

### Major Releases (`X.0.0`) — Big Cats (*Pantherinae*)
* `v1.0.0`: *Panthera leo* (Universal App Discovery & Priority Engine)
* `v2.0.0`: *Panthera tigris* (Next-Gen Subsystem Orchestration)
* `v3.0.0`: *Panthera pardus* (Cloud & Mesh Federation)
* `v4.0.0`: *Panthera onca* (Jaguar)
* `v5.0.0`: *Panthera uncia* (Snow Leopard)
* `v6.0.0`: *Neofelis nebulosa* (Clouded Leopard)

### Minor Releases (`X.Y.0`) — Small Cats (*Felinae*)
* `v1.1.0`: *Prionailurus bengalensis* (Purr Recipes & Android Native Subsystem) — *The agile, resilient Leopard Cat of Bengal*
* `v1.2.0`: *Otocolobus manul* (Pallas's Cat — serene, cold-hardened, calm wildcat)
* `v1.3.0`: *Caracal caracal* (Caracal — high-jumping precision)
* `v1.4.0`: *Leopardus wiedii* (Margay — acrobatic balance)
* `v1.5.0`: *Felis chaus* (Jungle Cat)
* `v1.6.0`: *Felis catus* (Domestic Cat — dedicated to Tuki's legacy)
* `v1.7.0`: *Acinonyx jubatus* (Cheetah — maximum throughput)
* `v1.8.0`: *Puma concolor* (Cougar / Mountain Lion)
* `v1.9.0`: *Lynx lynx* (Eurasian Lynx)

### Patch Releases (`X.Y.Z`)
Patch releases retain the parent minor codename with a maintenance descriptor:
* `v1.1.1`: *Prionailurus bengalensis* (Hotfix & Hardware Parity)

### Official Header Syntax in `CHANGELOG.md`
```markdown
## [X.Y.Z] - YYYY-MM-DD — *Scientific name* (Descriptive Release Name)
```

---

## 2. Two-Tier Changelog Architecture

Changelogs must serve both everyday desktop users and core systems engineers. Never dump raw git commits or PR reviews into the release notes.

### Tier 1: 🌟 What's New For You (Human-First Outcomes)
* **Audience**: Everyday Linux and KDE Plasma users (including the author's wife).
* **Voice**: Warm, empowering, clear, outcomes-driven. Free of jargon like "RRO", "APEX", or "cgroup2".
* **Focus**: What can the user now do that they couldn't do before? How is their life calmer and more delightful?
* **Formatting**: Clean bullet points with bold feature headlines, user-oriented explanations, and visual tips:
  ```markdown
  ### 🌟 What's New For You
  * **Android Apps on Your Desktop, Made Simple**: Run Android apps as normal desktop windows alongside your Linux tools. They remember where you left them, resize smoothly, and let you copy-paste text effortlessly.
  * **One-Click Healing for Crashing Apps**: If a chat app like Messenger turns black, Purr diagnoses and fixes the problem instantly in the background without losing your login or messages.
  * **Controller & Webcam Plug-and-Play**: Plug in a PlayStation DualSense or Xbox controller or plug in a webcam, and it works immediately in your Android apps.
  ```

### Tier 2: 🔧 Under the Hood (Technical Mechanics & Engineering Specs)
* **Audience**: Systems engineers, Arch packagers, DevOps agents, and security auditors.
* **Voice**: Forensic, authoritative, technically precise.
* **Focus**: Architectural boundaries, subsystem IPC, kernel interfaces, overlay mechanisms, database sanitization, and Zero Silent Failures compliance.
* **Formatting**: Structured categorized sections:
  ```markdown
  ### 🔧 Under the Hood
  * **Synchronous Two-Way Android IPC (`PurrBridgeHelper`)**:
    * Built-in system companion APK deployed to `/system/priv-app/PurrBridgeHelper/` enabling synchronous IPC via `am broadcast -W`.
  * **Window Geometry & Dynamic Normalization**:
    * Dynamic resolution and scaling factor auto-detection via `kscreen-doctor` (`window_memory.py`).
  * **Subsystem State Convergence (`is_deployed()` & `sync()`)**:
    * Non-destructive state convergence engine updating companions and KWin rules during `purr upgrade`.
  ```

---

## 3. The Release Execution Playbook

When cutting a release:

1. **Analyze Commits & Diff**:
   ```bash
   git log $(git describe --tags --abbrev=0)..HEAD --oneline
   ```
2. **Synthesize Changelog**:
   - Write the Tier 1 and Tier 2 sections according to the Two-Tier architecture.
   - Select the next Feline Codename from the taxonomy table.
   - Update `CHANGELOG.md` by turning `[n.e.x.t]` into `[X.Y.Z] - YYYY-MM-DD — *Codename* (Subtitle)`.
   - Prepend an empty `## [n.e.x.t] - YYYY-MM-DD` section at the top of `CHANGELOG.md`.
3. **Run Release Automation Engine**:
   ```bash
   python3 scripts/release.py --version X.Y.Z --codename "Scientific name" --descriptive-name "Subtitle" --auto-push
   ```
4. **Verify & Sync Mesh Nodes**:
   - Check local test suite and AUR package integrity:
     ```bash
     make test && make aur
     ```
   - Synchronize mesh partner nodes (e.g. laptop via `knot exec laptop "cd ~/purr && git pull --ff-only && make test"`).
