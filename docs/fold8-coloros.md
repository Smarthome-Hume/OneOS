# Fold8 ColorOS port

This ports the fixes tested on SM-F971B / h8q / SM8850 with the Find N6
ColorOS 17 image (`coloros17-findn6`, PLP120_17.0.0.109(CN01)). OneOS 0.4.13 supplies the `f8` profile; its Find N6 choice uses the
separate `n6-f8` package set while its Pixel choice stays unchanged. It does not widen the Ultra's hardware match, enable a
new image, or change the screen-lock or OneLineage startup requirements.

## Included

- Cover camera bounds centered on its 1248 px panel, restoring status-bar width.
- Larger cover Quick Settings tiles with stock spacing for two swipeable rows.
  Crossing sw600 refreshes the QS view and text-density cache, including the
  existing font scale. The inner screen retains its original sizing.
- Samsung sensor 65686 read as degrees despite its maxRange metadata of 1.
  When SystemUI cannot register it, a guest system-UID helper relays timestamped
  angles. A single reader per provider rejects stale frames and stops with
  the provider; the producer exits when the guest zygote disappears. Android
  sensor 36 remains the fallback.
- The experimental Android unfold gates previously tested on this phone.
  These are not a complete implementation of OPPO's home/lock-screen and
  closing animations. The wallpaper callback reports merged window geometry
  only after Canvas posts a frame, fixing the observed multi-second blank
  display during panel changes.
- Original donor AOD, UMS and Instant APKs. UMS and Instant supply the home and
  lock-screen widget catalogues; their CN category names remain Chinese.
  CardService is already in this image and is not duplicated.
- Native lock-screen-linked Workshop AOD on either panel and a 0.12 doze
  brightness fallback. Native libraries are repaired only for the exact stock
  AOD APK. A later user-updated AOD is preserved.
- Stock Find N6 Pocket Studio and flexible-freeform feature declarations,
  scoped to Fold8 / Find N6. The container does not scan the stock
  `my_stock/etc/extension/com.oplus.oplus-feature.xml` that enables them.
  Restoring them selects the native multitasking path for the split-screen
  gesture and taskbar integration.
- Launcher taskbar feature-provider row and one-time taskbar/AOD defaults.
  Later user choices are retained. Live Alerts, fold animation, separate
  wallpapers and haptic-channel feature declarations are restored in the
  guest's feature configuration. A haptic flag does not provide OPPO hardware.
- Missing Play services and Play Store binaries copied from One UI before
  shutdown, with arm64 library directories derived from the same APK splits.
  These are guest-only mounts; host app/account data is not copied. Local
  network permission is left to the user rather than granted automatically.

The 0.4.13 N6 baseline's jars, guarded guest vold and in-guest return app
are preserved byte for byte. Its guard manifest already includes biometric,
gatekeeper, FRP, APEX-install, app-id and user-creation protection. An existing stage
with guest app ids 10000–14999 retains its apps/data and skips Google binary
injection. The display repairs remain available; injection only runs when
the guarded app-ID layout is already present.

The Fold8 SystemUI bind is installed after the system_ext overlay so that
overlay cannot hide it. Split-permission cleanup removes only mounts sourced
from this stage's `oneos_split_<number>.xml`, preserving the foldable feature
configuration and other permissions overrides. `scripts/test-permission-cleanup.py`
checks full and /data-relative mount roots and unrelated/foreign XML mounts.

## Build

OEM APKs and generated package files stay outside Git, like the other OneOS
sets. Required inputs:

1. The base files matching `app-android/packages/n6-f8u.sha256` exactly.
2. Unmodified Find N6 `SystemUI.apk`, SHA-256
   `e6bf0e49649dc82117e7b9584c13dbcf737183d17c461cd6edcedcc127165f7e`.
3. A donor directory containing `Aod.apk`, `UMS.apk` and `Instant.apk` from
   the firmware above. The builder checks their full hashes before use.

```sh
ANDROID_HOME=/path/to/android-sdk \
ONEOS_ANDROID_PLATFORM=android-37 \
APKTOOL=/path/to/apktool.jar \
python3 scripts/make-fold8-coloros.py \
    --base /path/to/pinned-n6-overlays \
    --systemui /path/to/original/SystemUI.apk \
    --donor /path/to/extracted-donor-apks
```

Use Python 3.11+, apktool 3.0.3, Android build-tools 36.1.0 and a JDK capable
of `--release 8`. The builder creates `out/overlays_n6_fold8`, refuses an
existing output, and verifies every output against `n6-f8.sha256`. Changes in
compiler/tool output require an explicit reviewed pin update. It never
silently regenerates trusted hashes. Normal Gradle packaging then includes
this set, with the usual root/script/list pins and receive limits.

`fold8_coloros_systemui.py` applies `fold8-coloros/systemui.patch` only to
known class hashes. All classes are checked before any write; a complete
rerun is idempotent. New helper smali and their Java sources are beside the
patch. Only the affected dex entries are replaced; manifest, resources and
all other entries retain their original bytes. The original APK signer block
is retained as system-partition certificate metadata, **not as a valid OEM
signature for changed content**. This APK is a root-mounted system overlay,
not an APK for normal installation.

## Validation and remaining device check

```sh
python3 scripts/test-fold8-coloros.py /path/to/pristine/apktool/SystemUI
python3 scripts/test-fold8-google-snapshot.py
python3 scripts/test-permission-cleanup.py
python3 scripts/check-dex.py out/overlays_n6_fold8/Fold8SystemUI.apk \
    out/overlays_n6_fold8/services_patched.jar
cd app-android
./gradlew :core:model:test :core:root:testDebugUnitTest
```

The Python tests cover image/profile isolation, missing safety guards,
invalid Google snapshots, exact patch application, idempotence and atomic
refusal on class drift. The Kotlin tests cover the Fold8 model, set and root
staging agreement, and retain the screen-lock BLOCK test. Root script tests
expect GNU command semantics (not macOS's BSD `stat` and `find`).

The individual UI fixes were tested in the earlier modified ColorOS session;
this integrated source build still needs a fresh launch and fold/unfold/AOD/
widget/Play Store check on the device. The repair APK can be installed and
staged while the phone remains in One UI; this does not verify a guest boot. Runtime installation failures are recorded in
`$STAGE/fold8_runtime.log`, and hinge producer errors in the guest's
`/data/local/tmp/oneos-angle.log`.

Verification for the 0.4.13 refresh: 196 model tests passed. The full root
suite ran 113 tests with one absent-log skip; three package-set expectations
were corrected and passed an 18-case targeted rerun. Five Fold8 Python checks
(including pristine donor patching) and two permissions/mount-order regressions
passed. The Android private-mount test retained a real foldable feature bind
while removing the split-permission bind, without changing the host namespace.
SystemUI and the current baseline services.jar passed the DEX checks.

The APK was packaged with all six package sets. Its 118 content-addressed
payloads, every set manifest, the root script and generated BuildConfig pins
were checked after packaging. Limited Mac disk space required reusing the
verified compressed assets and removing recoverable unpacked build copies;
this did not change the shipped file contents or checks. A full clean rebuild
and fresh ColorOS launch of this refresh remain separate device/build checks.

On-device launch check against OneOS 0.4.14: the original Fold8 snapshot
stopped before host shutdown because BusyBox awk rejected its escaped-slash
regular expression. APK library paths are now matched by components; archive
errors stop the snapshot, and APKs without native libraries have a verified
empty native manifest. The same path matcher is used for AOD library repair.
Four ZIP/manifest regressions cover split APKs, no native libraries, malformed
archives and modified native libraries. A real Android BusyBox fixture and
snapshots of the installed Google apps passed too.

With these scripts staged into 0.4.14, ColorOS reached its launcher and
SystemUI without a kernel reboot. Moving the Fold8 hook after system_ext
construction and retaining the feature XML bind restored the inner display's
foldable layout, confirmed on the device. This validates the staged script
repairs; the complete APK for this latest script revision has not been rebuilt,
and this run did not repeat every AOD, widget or fold-transition test.

Pocket Studio was staged into installed OneOS version code 28 using its normal
receive/finish integrity checks. On-device testing confirmed that the
split-screen gesture opens the chooser and the taskbar works in split screen.
The original Fold8 SystemUI payload was retained; experimental legacy
split-helper bytecode changes are not included.

Pixel guest AOD, persistent status-bar geometry and wallpaper restoration on
the same Fold8 profile are covered in [pixel-fold8.md](pixel-fold8.md).
