#!/system/bin/sh
# Fold8 / Find N6 only. Called by the checked session scripts; never in One UI
# for runtime. Binaries come through the normal pinned n6-f8 package set.
set -e
STAGE=${STAGE:-/data/local/tmp/oneos}
BB=${BB:-/data/oneos_bin/busybox}
fail() { echo "Fold8 ColorOS: $*" >&2; exit 3; }
selected() {
    [ "${ONEOS_PROFILE:-}" = f8 ] &&
        grep -q '^  "image": "coloros17-findn6",$' "$STAGE/.oneos_stage" &&
        grep -q '^  "set": "n6-f8",$' "$STAGE/.oneos_stage"
}
# Reject links anywhere below these new caches, including a guest-planted
# link to host data. Existing stage/namespace checks run before this script.
plain_tree() {
    [ ! -L "$1" ] || fail "$1 is a symlink"
    [ ! -d "$1" ] || [ -z "$(find "$1" -type l -print -quit)" ] || fail "symlink below $1"
}
verify_google() {
    for name in GmsCore Phonesky; do
        dir="$STAGE/fold8_google/$name"
        plain_tree "$dir"
        (cd "$dir" && sha256sum -c apk.sha256 && sha256sum -c native.sha256) >/dev/null || fail "invalid $name snapshot"
    done
}
case "$1" in
snapshot)
    selected || exit 0
    # Run before One UI stops: copy signed application binaries only, never
    # app/account data. A later prepare pass verifies and mounts the snapshot.
    for guard in gatekeeper pdb apexd appid15000; do
        grep '^#' "$STAGE/guards.txt" | grep -qw "$guard" || fail "missing $guard guard"
    done
    if awk '$2 >= 10000 && $2 <= 14999 {f=1} END {exit !f}' "$STAGE/data/system/packages.list" 2>/dev/null; then
        fail 'old guest app ids; prepare fresh guest data before enabling Google services'
    fi
    plain_tree "$STAGE/fold8_google"
    [ ! -e "$STAGE/fold8_google" ] || [ -d "$STAGE/fold8_google" ] || fail 'Google cache is not a directory'
    mkdir -p "$STAGE/fold8_google"
    for spec in com.google.android.gms:GmsCore com.android.vending:Phonesky; do
        pkg=${spec%:*}; name=${spec#*:}
        dir="$STAGE/fold8_google/$name"; plain_tree "$dir"
        new="$STAGE/fold8_google/.${name}-$$"
        mkdir "$new" || fail 'snapshot temporary directory already exists'
        pm path "$pkg" | sed -n 's/^package://p' > "$new/source.paths"
        [ -s "$new/source.paths" ] || fail "$pkg is not installed in One UI"
        mkdir -p "$new/lib/arm64"
        while IFS= read -r source; do
            case "$source" in /data/app/*/*.apk|/product/*/*.apk|/system/*/*.apk|/system_ext/*/*.apk) ;; *) fail 'unexpected APK path';; esac
            [ -f "$source" ] && [ ! -L "$source" ] || fail 'APK missing or linked'
            cp "$source" "$new/${source##*/}"
        done < "$new/source.paths"
        for apk in "$new"/*.apk; do
            for entry in $("$BB" unzip -l "$apk" | "$BB" awk '$4 ~ /^lib\/arm64-v8a\/lib[^/]*\.so$/ {print $4}'); do
                lib=${entry##*/}
                "$BB" unzip -p "$apk" "$entry" > "$new/lib/$lib"
                [ -s "$new/lib/$lib" ] || fail 'empty native library'
                rm -f "$new/lib/arm64/$lib"
                ln "$new/lib/$lib" "$new/lib/arm64/$lib"
            done
        done
        (cd "$new" && sha256sum ./*.apk > apk.sha256 && sha256sum lib/*.so lib/arm64/*.so > native.sha256)
        chown -R 0:0 "$new"; find "$new" -type d -exec chmod 755 {} \;
        find "$new" -type f -exec chmod 644 {} \;
        if [ -e "$dir" ]; then
            mv "$dir" "$STAGE/fold8_google/.${name}-previous-$$"
        fi
        mv "$new" "$dir"
        # Only our own immediately replaced binary snapshot; no guest data.
        rm -rf "$STAGE/fold8_google/.${name}-previous-$$"
    done
    verify_google
    ;;
prepare)
    selected || exit 0
    ROOTFS="$STAGE/rootfs"
    verify_google
    target="$ROOTFS/system/system_ext/priv-app/SystemUI/SystemUI.apk"
    "$BB" umount -l "$target" 2>/dev/null || true
    [ -f "$target" ] && [ ! -L "$target" ] || fail 'unexpected SystemUI path'
    [ "$(sha256sum "$target" | cut -d' ' -f1)" = e6bf0e49649dc82117e7b9584c13dbcf737183d17c461cd6edcedcc127165f7e ] || fail 'SystemUI donor differs'
    "$BB" mount --bind "$STAGE/Fold8SystemUI.apk" "$target"
    "$BB" mount --make-private "$target"
    "$BB" mount -o remount,bind,ro "$STAGE/Fold8SystemUI.apk" "$target"
    for spec in GmsCore:GmsCore Phonesky:GooglePlayServicesUpdater; do
        name=${spec%:*}; slot=${spec#*:}
        target="$ROOTFS/my_product/priv-app/$slot"
        [ -d "$target" ] && [ ! -L "$target" ] || fail "missing Google slot $slot"
        if [ "$name" = GmsCore ] && [ -d "$target/m" ]; then
            # Keep the image's own signed Dynamite module files.
            cp -a "$target/m" "$STAGE/fold8_google/GmsCore/"
        fi
        chcon -R u:object_r:system_file:s0 "$STAGE/fold8_google/$name"
        "$BB" mount --bind "$STAGE/fold8_google/$name" "$target"
        "$BB" mount --make-private "$target"
        "$BB" mount -o remount,bind,ro "$STAGE/fold8_google/$name" "$target"
    done
    dest="$STAGE/data/oneos_fold8"
    plain_tree "$dest"
    mkdir -p "$dest"
    for f in Fold8Aod.apk Fold8UMS.apk Fold8Instant.apk Fold8AngleRelay.dex; do
        cp -f "$STAGE/$f" "$dest/$f"
        chmod 644 "$dest/$f"
    done
    cp -f "$STAGE/fold8_coloros.sh" "$dest/runtime.sh"
    chmod 755 "$dest"; chmod 644 "$dest/runtime.sh"
    chown -R 0:0 "$dest"
    chcon -R u:object_r:system_data_file:s0 "$dest"
    ;;
runtime)
    # This file is copied only into an n6-f8 guest data tree and invoked via
    # the UI activator's guest namespace + environment. No host pm/settings.
    D=/data/oneos_fold8
    [ -f "$D/Fold8AngleRelay.dex" ] || exit 0
    reload=0
    for spec in com.oplus.aod:Fold8Aod.apk com.oplus.pantanal.ums:Fold8UMS.apk com.nearme.instant.platform:Fold8Instant.apk; do
        pkg=${spec%:*}; apk="$D/${spec#*:}"
        if [ -z "$(pm path "$pkg" 2>/dev/null)" ]; then
            pm install -r --abi arm64-v8a --user 0 "$apk"
        fi
    done
    # This stock AOD declares extractNativeLibs=false. Repair its on-disk
    # arm64 path only while it is still our exact donor, never a user update.
    aod=$(pm path com.oplus.aod | sed -n 's/^package://p' | head -1)
    case "$aod" in /data/app/*/base.apk)
        if [ "$(sha256sum "$aod" | cut -d' ' -f1)" = 87bfba25e06a5081f5feef73aef15a90dbc9b9f39b1fe756c68fd9975ac38638 ]; then
            libdir=${aod%/base.apk}/lib/arm64
            mkdir -p "$libdir"
            for entry in $("$BB" unzip -l "$aod" | "$BB" awk '$4 ~ /^lib\/arm64-v8a\/lib[^/]*\.so$/ {print $4}'); do
                "$BB" unzip -p "$aod" "$entry" > "$libdir/${entry##*/}"
                chmod 644 "$libdir/${entry##*/}"
            done
            chmod 755 "${libdir%/arm64}" "$libdir"
            restorecon -RF "${libdir%/arm64}"
        fi
    ;; esac
    settings put global fluid_cloud_not_support 0
    uri=content://com.oplus.customize.coreapp.configmanager.configprovider.AppFeatureProvider/app_feature
    if ! content query --uri "$uri" --where 'featurename="com.android.launcher.TASKBAR_ENABLE"' 2>/dev/null | grep -q 'featurename=com.android.launcher.TASKBAR_ENABLE'; then
        content insert --uri "$uri" --bind featurename:s:com.android.launcher.TASKBAR_ENABLE --bind parameters:s:
        reload=1
    fi
    if [ ! -f "$D/defaults-v1" ]; then
        settings put system enable_launcher_taskbar 1
        settings put secure oplus_keyguard_workshop_aod_support 1
        settings put secure Setting_AodState 1
        settings put secure Setting_AodState_Local 1
        touch "$D/defaults-v1"
    fi
    ui=$(pidof com.android.systemui | cut -d' ' -f1)
    if [ -n "$ui" ]; then
        uid=$(stat -c %u /proc/$ui)
        mkdir -p /data/oneos_hinge
        chown 1000:"$uid" /data/oneos_hinge; chmod 2750 /data/oneos_hinge
        chcon u:object_r:system_data_file:s0 /data/oneos_hinge
        if ! ps -A -o ARGS | grep -q '[a]pp_process /system/bin OneOSAngleRelay '; then
            z=$(pidof zygote64 | cut -d' ' -f1)
            (umask 027; CLASSPATH="$D/Fold8AngleRelay.dex" "$BB" nohup "$BB" setuidgid system /system/bin/app_process /system/bin OneOSAngleRelay /data/oneos_hinge/angle.bin "$z" >/data/local/tmp/oneos-angle.log 2>&1 </dev/null &)
            # Let the fresh relay frame exist before SystemUI reselects its provider.
            for n in 1 2 3 4 5; do [ ! -s /data/oneos_hinge/angle.bin ] || break; sleep 1; done
            [ ! -s /data/oneos_hinge/angle.bin ] || reload=1
        fi
    fi
    if [ "$reload" = 1 ]; then
        for pkg in com.android.launcher com.android.systemui; do
            p=$(pidof "$pkg"); [ -z "$p" ] || kill -TERM $p
        done
    fi
    ;;
*) fail 'expected snapshot, prepare or runtime' ;;
esac
