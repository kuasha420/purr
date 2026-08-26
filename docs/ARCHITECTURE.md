# Smart App Installer Architecture & Discovery Engine

This document details the internal design, multi-source resolution logic, and scoring heuristics of `smart-install`.

---

## 1. Resolution Hierarchy

When discovering and installing software on Arch Linux, `smart-install` enforces the following priority:

```text
[1] System Repositories (core, extra, multilib, endeavouros, archlinuxcn)
        │ (Native binary packages, fastest, best system integration)
        ▼
[2] Arch User Repository (AUR / yay)
        │ (Community PKGBUILDs built for Arch)
        ▼
[3] Flatpak (Flathub)
        │ (Sandboxed runtime container applications)
        ▼
[4] AppImage (AUR / AppImageHub / Gear Lever)
        │ (Portable standalone bundle)
        ▼
[5] Git / Direct Source Build
          (Fallback repository cloning and build)
```

---

## 2. Multi-Strategy Query Expansion

Naive text search breaks on multi-word queries (e.g. `"google chrome"` vs `google-chrome`) and aliases (`vscode` vs `visual-studio-code-bin`).

`smart-install` applies:
* **Canonical Tokenization**: Splits input into clean alphanumeric tokens.
* **Slug Generation**: Generates hypenated slugs (`"google chrome"` $\rightarrow$ `google-chrome`).
* **Alias Mapping**: Expands common brand names to their distribution package names.
* **Concurrent Multi-Backend Retrieval**: Queries Pacman, AUR RPC, and Flatpak simultaneously.

---

## 3. Heuristic Scoring Formula

For any package $P$ and query $Q$, the composite score $S(P, Q)$ is computed as:

$$S(P, Q) = S_{\text{match}}(P, Q) + S_{\text{type}}(P) + S_{\text{pop}}(P) + S_{\text{channel}}(P) - P_{\text{aux}}(P)$$

### Component Weights:
1. **$S_{\text{match}}$ (Name & Slug Matching)**:
   * Exact slug / display name match: $+100$ pts
   * Binary / Desktop suffix (`-bin`, `-desktop`): $+95$ pts
   * Prefix match: $+75 - \Delta\text{len}$ pts
   * Token subset overlap: $+70$ pts
   * Description match: $+25$ pts
   * Fuzzy string similarity: $\text{ratio} \times 30$ pts

2. **$S_{\text{type}}$ (Desktop Application Verification)**:
   * Verified Desktop Application in AppStream / Flathub: $+25$ pts

3. **$S_{\text{pop}}$ (Community Trust & Popularity)**:
   * For AUR packages: $\min(30, \; 6 \times \log_{10}(\text{Votes} + 1))$
   * For System repository packages: $+15$ pts baseline

4. **$P_{\text{aux}}$ (Auxiliary Package & Plugin Penalty)**:
   * Extensions, plugins, themes, skins, bindings, drivers (`-plugin`, `-extension`, `-theme`, `-languageserver`, `krunner-`, `uget-integrator-`, `python-`, `chromedriver`): $-60$ pts penalty unless explicitly searched.

5. **Noise Suppression**:
   * When any package scores $\ge 80.0$ (high confidence), all results with score $< 50.0$ are suppressed.
