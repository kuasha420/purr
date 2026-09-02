# 🐾 Handover: Waydroid Titlebar Button Visibility Fix

**Target Branch**: `feat/waydroid-titlebar-visibility` (branched off `feat/multiwindow-and-keyboard-qol` / PR #3)  
**Date**: 2026-09-02  
**Author**: Purr Development Team / Project Tuki

---

## 1. Problem Statement & Verified Root Cause

### The Problem
In freeform multi-window mode, Android windows (such as Gamepad Tester `ru.elron.gamepadtester` or Play Store) display standard window caption controls:
- `<` (`R.id.back_window`)
- `—` (`R.id.minimize_window`)
- `🗗` (`R.id.maximize_window`)
- `✕` (`R.id.close_window`)

**These buttons ARE physically present, rendered by `DecorCaptionView` across the top of the window, and 100% interactive**.
However, on dark/purple app headers (like Gamepad Tester's `#673AB7` bar), the buttons appear **completely invisible** because their color blends into the dark background.

### The AOSP Mechanism
In [`com.android.internal.widget.DecorCaptionView.java`](https://cs.android.com/android/platform/superproject/+/master:frameworks/base/core/java/com/android/internal/widget/DecorCaptionView.java):
```java
private void updateShade() {
    int shade = mOwner.getContext().getResources().getColor(
            mOwner.isLightNavBar() ? R.color.decor_button_light_color : R.color.decor_button_dark_color);
    mClose.setColorFilter(shade, PorterDuff.Mode.SRC_IN);
    mMaximize.setColorFilter(shade, PorterDuff.Mode.SRC_IN);
    mMinimize.setColorFilter(shade, PorterDuff.Mode.SRC_IN);
    mBack.setColorFilter(shade, PorterDuff.Mode.SRC_IN);
}
```
1. When the app header is dark, `mOwner.isLightNavBar()` returns `false`.
2. AOSP applies `R.color.decor_button_dark_color` from `framework-res.apk`.
3. In stock AOSP `framework-res.apk`, `decor_button_dark_color` is **`#ff000000` (solid black)**.
4. Solid black vector icons on dark purple background have zero contrast, rendering them invisible to the eye while retaining full clickability.

---

## 2. Lessons Learned from Previous Attempts

| Attempt | Root Cause of Failure | Lesson for Next Agent |
| :--- | :--- | :--- |
| **Hex Editing `resources.arsc`** | Offset mismatch in string pool caused `libandroidfw.so` (`LoadedPackage::GetEntryOffset`) to segfault during view inflation. | **Never hex edit binary resource tables**. Use proper tooling (`apktool` / `aapt2`). |
| **AAPT2 Standalone Compilation** | `aapt2 link` stripped the `android:color` attribute when compiled without resource namespace mapping, making `ColorStateList` return `0x00000000` (transparent). | Must include full namespace and resource mapping if building RROs. |
| **Static RRO (`isStatic="true"`) with Debug Key** | In Android 13, `idmap2` silently drops static framework overlays that are not signed with the platform certificate. | Use direct OverlayFS framework replacement OR sign with public LineageOS platform test keys. |

---

## 3. Recommended Action Plan & Implementation Pathways

The incoming agent should investigate and implement one of the following tested approaches:

### Pathway 1: Direct OverlayFS `framework-res.apk` Resource Patching (Recommended)
Waydroid supports `/var/lib/waydroid/overlay/system/framework/framework-res.apk` via OverlayFS.
1. Decompile stock `/var/lib/waydroid/rootfs/system/framework/framework-res.apk` using `apktool d framework-res.apk`.
2. In `res/values/colors.xml` (or `res/color/decor_button_dark_color.xml`), change `decor_button_dark_color` from `#ff000000` to `#ffffffff` (pure solid white).
3. Rebuild with `apktool b` or `aapt2`, zipalign (4-byte), and copy to `/var/lib/waydroid/overlay/system/framework/framework-res.apk`.
4. *Advantage*: Bypasses all `idmap2` and RRO signature checks; Android loads it directly as the native platform framework on boot!

### Pathway 2: Public LineageOS Platform Key RRO Signing
Waydroid's build fingerprint is `waydroid/lineage_waydroid_x86_64/waydroid_x86_64:13/TQ3A.230901.001/eng.aleast.20260403.113748:userdebug/test-keys`.
1. It uses standard AOSP / LineageOS public test-keys (`platform.pk8` and `platform.x509.pem`).
2. Sign the RRO overlay with the platform test-key so `idmap2` treats it as a first-party platform overlay.

---

## 4. Key Subsystem & In-Lockstep Invariants

Whenever code changes are made:
1. **Never break `system_server` stability**: Verify `logcat -d -b crash` is 100% clean.
2. **Never wipe user pattern locks**: Keep `sp-handle` checks guarded in `recipe.py`.
3. **In-Lockstep Maintainability**: Run `make test && make aur` to update `.SRCINFO`, `PKGBUILD`, and `CHANGELOG.md` (`## [n.e.x.t] - YYYY-MM-DD`).
