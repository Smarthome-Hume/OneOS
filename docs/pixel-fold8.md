# Pixel on Galaxy Z Fold8

These changes apply to profile `f8` with Pixel SystemUIGoogle present. The
ColorOS path, Fold8 Ultra and bar-phone profiles keep their current resources.
They use the guest OEM overlay directory, with no flash operation or root module.

## Status bar and always-on display

Pixel uses a 24dp bar on the Samsung vendor configuration. The verified Fold8
geometry is 48dp for the default, portrait and landscape bar heights, with 0dp
extra top padding. The clock and icons retain Pixel's own dimensions and font
scaling; no `status_bar_clock_size` or `status_bar_icon_size` is overridden.

The image also leaves `config_dozeComponent` empty and AOD availability false.
Runtime fabricated overlays expose the Settings entry and update SystemUI,
but system_server's system resources still have no doze component. Immutable
boot overlays provide the existing `com.android.systemui/.doze.DozeService` and
declare AOD availability. SystemUI uses the supported DOZE state; DOZE_SUSPEND
is left disabled. No secure AOD preference is written during startup, so later
user choices remain intact.

The two small configuration APKs are built from
`switcher/overlays/pixel_fold8_framework` and `pixel_fold8_systemui`. The
compressed payloads live in the existing integrity-checked preparation script,
so this does not add files to OneOS's app/model/package-set staging schema.
The script verifies their SHA-256 hashes before including them in guest `/oem`.
They contain resources only, with no executable dex or OEM donor content.

Regenerate them after editing the XML:

```sh
python3 scripts/make-pixel-fold8-overlays.py --sdk /path/to/android-sdk \
  --build-tools 36.0.0 --platform android-37.0 \
  --keystore /path/to/debug.keystore
```

The keystore uses the standard `androiddebugkey` alias and public `android`
password. Java must be available to Android's signing tools. App builds then
include the updated script through their existing content-addressed assets and
BuildConfig script hashes.

## Wallpaper reset between sessions

This Pixel image's `WallpaperDataParser.parseWallpaperDescription()` calls
`next()` once and expects the saved description's start tag. Its serializer
writes a newline there, so `next()` returns TEXT and the saved live wallpaper
component is skipped. On the device, a saved Pine selection became the static
ImageWallpaper after re-entry. A read-only probe of the actual guest parser
returned event 4 (TEXT) for the original file, and event 2 (START_TAG) with the
correct Pine component after removing whitespace between elements.

Before the guest starts, normalize only whitespace between XML elements in
`data/system/users/0/wallpaper_info.xml`. Component names, crop values, colours,
content values and wallpaper imagery remain intact. The original formatting is
backed up beside the file. Source and temporary paths are checked for symlinks;
failed copies or normalization retain the original. Compact files are unchanged.
This does not repeatedly force a particular wallpaper or replace user choices.

## Validation

- Fold8 SM-F971B / h8q, Pixel 11 Fold yogi, staged through installed OneOS
  0.4.15 (version code 28) receive/finish integrity checks.
- AOD component resolved in DreamManager after boot, and AOD was visually
  confirmed by the owner.
- Pine live wallpaper survived a complete return to One UI and Pixel re-entry.
- After another guest exit/re-entry, all three status-bar heights resolved to
  48dp with 0dp top padding, native 14sp clock / 22dp icon resources and no
  fabricated PixelBar overlays. Pine remained selected and DreamManager still
  resolved the AOD component.
- Seven dedicated Python regressions cover resource scope, native sizing,
  wallpaper content preservation, idempotence, failed normalization and symlink
  refusal. Existing Google snapshot and permission-cleanup regressions also pass.

Run `python3 scripts/test-pixel-fold8.py` and the existing Fold8 regressions.
The complete host APK has not been rebuilt here. An upstream app update or a
new Prepare operation can replace locally staged scripts until the changes are
included in that build.
