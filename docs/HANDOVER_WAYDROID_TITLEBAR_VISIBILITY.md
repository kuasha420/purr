# 🐾 Waydroid Titlebar Button Visibility: Architecture & Resolution

**Target Branch**: `feat/waydroid-titlebar-visibility`  
**Date**: 2026-09-02  
**Status**: **RESOLVED & VERIFIED**  
**Author**: Purr Development Team / Project Tuki

---

## 1. Executive Summary & Root Cause Analysis

In Android freeform multi-window mode, window caption controls (`<`, `—`, `🗗`, `✕`) were previously invisible on dark-themed apps (such as Google Play Store) and solid-purple apps (such as Gamepad Tester).

Extensive binary and runtime investigation uncovered **two distinct architectural layers and bugs**:

### Layer 1: Google Material Components `<Button>` Tag Interception (`framework-res.apk`)
- In stock AOSP `framework-res.apk`, `res/layout/decor_caption.xml` declared caption buttons using the generic tag `<Button>`.
- In any modern Android app utilizing Google Material Components (`Theme.MaterialComponents`, such as Gamepad Tester `ru.elron.gamepadtester`), Android's `MaterialComponentsViewInflater` automatically intercepts and replaces every `<Button>` tag with `com.google.android.material.button.MaterialButton`.
- `MaterialButton` enforces a `MaterialShapeDrawable` background and applies `backgroundTint` defaulting to `?attr/colorPrimary` (which in Gamepad Tester is `#9147ff` purple).
- When `DecorView` or `DecorCaptionView` attempted to set the vector drawable icon, `MaterialButton` tinted the entire drawable with solid `#9147ff` purple, obliterating the vector glyph and rendering purple-on-purple (100% invisible).
- **The Fix**: In `framework-res.apk`'s `res/layout/decor_caption.xml`, the StringPool element name is changed from `'Button'` to `'View'`. Since `DecorCaptionView`'s internal fields (`mBack`, `mMinimize`, `mMaximize`, `mClose`) are generic `android.view.View` references, declaring `<View>` completely bypasses `MaterialComponentsViewInflater`. The view remains a clean, standard Android view that renders the vector drawables with crisp white icons.

### Layer 2: SystemUI Window Decor & Unfocused Alpha 20% Bug (`SystemUI.apk`)
- In Android 13, WMShell freeform window captions are also rendered by `com.android.wm.shell.windowdecor.CaptionWindowDecoration` inside `SystemUI.apk`.
- In stock `SystemUI.apk`:
  - `decor_button_dark_color.xml` and `decor_button_light_color.xml` define an unfocused fallback color with `alpha="0x33"` (20% opacity). When windows lose focus or are rendered without active focus state resolution, icons become almost invisible.
  - `res/drawable/decor_close_button_dark.xml` and `decor_back_button_dark.xml` hardcode `fillColor="@android:color/black"`.
- **The Fix**: In `SystemUI.apk`:
  - Color selectors `decor_button_dark_color.xml` and `decor_button_light_color.xml` are patched so that focused states use `#ffffffff` (solid bright white) and unfocused states use `#80ffffff` (50% dimmed white), maintaining active window hierarchy while remaining completely legible.
  - Vector fill colors in `decor_close_button_dark.xml` and `decor_back_button_dark.xml` are updated from `@android:color/black` (`0x0106000c`) to `@android:color/white` (`0x0106000b`).

### Layer 3: PackageManager APK Signature Scheme Verification
- In Android 13, `system_server`'s `PackageManagerService` strictly verifies that any modified `framework-res.apk` possesses a valid APK Signature Scheme v2/v3 signature using the platform key.
- Both `framework-res.apk` and `SystemUI.apk` are signed with the standard publicly available AOSP platform test-keys (`platform.pk8` and `platform.x509.pem`) using `apksigner`.

---

## 2. Implementation & Automation Pipeline

The fix is completely automated in [`recipes/waydroid_native/titlebar_patch.py`](../recipes/waydroid_native/titlebar_patch.py):

1. **Mounts Base System Image**: Mounts `/var/lib/waydroid/images/system.img` read-only via loop device.
2. **Patches `framework-res.apk`**:
   - Replaces `'Button'` with `'View'` in `res/layout/decor_caption.xml` StringPool.
   - Enforces solid white `#ffffffff` in `res/color/decor_button_dark_color.xml` and `res/color/decor_button_light_color.xml`.
   - 4-byte `zipalign`.
   - Signs with platform keys (v1/v2/v3 enabled).
   - Deploys to `/var/lib/waydroid/overlay/system/framework/framework-res.apk`.
3. **Patches `SystemUI.apk`**:
   - Enforces solid white `#ffffffff` (focused) and `#80ffffff` (unfocused) in `res/color/decor_button_dark_color.xml` and `res/color/decor_button_light_color.xml`.
   - Replaces vector fill colors with `@android:color/white`.
   - 4-byte `zipalign`.
   - Signs with platform keys (v1/v2/v3 enabled).
   - Deploys to `/var/lib/waydroid/overlay/system/system_ext/priv-app/SystemUI/SystemUI.apk`.
4. **Clears Caches**: Flushes `resource-cache` and `package_cache` in OverlayFS and user directories.
5. **Idempotency**: Embeds asset markers (`purr-decor-dark-white-v2` and `purr-decor-sysui-white-v2`) to skip re-patching if already installed.

---

## 3. Visual Verification

Verified on live desktop with active foreground windows:
- **Google Play Store (`com.android.vending`)**: Caption controls `< — 🗗 ✕` are crisp, solid white.
- **Gamepad Tester (`ru.elron.gamepadtester`)**: Caption controls `< — 🗗 ✕` are crisp, solid white on the purple header with zero purple tinting or clipping.
