# Hướng dẫn cho AI khác làm việc trên dự án OneOS-S26U

> Tài liệu này là điểm vào duy nhất cho một AI mới (ví dụ Notion AI worker) tiếp quản dự án.
> Đọc hết tài liệu này TRƯỚC khi sửa bất kỳ file nào. Nếu tài liệu này mâu thuẫn với
> một ghi chú cũ, tài liệu này thắng — trừ khi user nói ngược lại bằng miệng/chat.

## 1. Repo và nhánh — chốt, không tự đổi

- Repo làm việc: **`Smarthome-Hume/OneOS`** (fork thật của `fahadalijaved23/OneOS`).
- Nhánh làm việc: **`s26u`**.
- Nhánh `main` của fork: **chỉ là mirror của upstream, KHÔNG sửa gì trực tiếp vào `main`**.
- Commit nền upstream hiện tại: **OneOS 0.4.23, `a83b559b528b103a6c0c550b1898081fe3832fe1`**.
- Commit `s26u` hiện tại: **`67936667c65e438eece3d8e34a2760508ae25e82`** —
  "OneOS-S26U: S26 Ultra only (rebased onto upstream 0.4.23)".
- Repo cũ `Smarthome-Hume/OneOS-S26U` (nền 0.4.13, main `282aa807…`) chỉ là bản lưu,
  KHÔNG phải gốc làm việc nữa. Đừng push code mới vào đó, đừng lấy nó làm base.
- Lấy code về:
  ```sh
  git clone https://github.com/Smarthome-Hume/OneOS.git
  cd OneOS
  git checkout s26u
  ```

## 2. Mục đích dự án — user đã chốt

- Build riêng OneOS tối ưu cho **Galaxy S26 Ultra**, không phụ thuộc tác giả gốc.
- Tiêu chí nghiệm thu, theo thứ tự này:
  1. **Tất cả chức năng port sang phải hoạt động được** trên S26U thật.
  2. **Độ phân giải, hiển thị nội dung phải điều chỉnh cho phù hợp nhất với panel S26U**
     (kích thước, density, status bar, cutout — không phải cứ chạy được là xong).
  3. Không regression: thứ đã chạy được trên S26U không được hỏng sau mỗi lần sửa/sync.
- User là người duy nhất tuyên bố "đạt" trên thiết bị thật. AI không tự tuyên bố.

## 3. Thiết bị thật — số đo đã có, không đoán lại

- Máy: **Galaxy S26 Ultra, SM-S948B, codename m3q, chip SM8850 (Snapdragon 8 Elite Gen 5)**,
  One UI 9.0, Android 17, SDK 37.
- Màn: **1440×3120, xdpi 501,0411 / ydpi 498,4151, density bucket 600**.
- Cutout (lỗ camera): `M 0,0 H -10.666… V 37.066… H 10.666… V 0 H 0 Z @dp`
  (21,333×37,067 dp); lỗ camera Rect(680,0–760,139) px máy thật.
- `status_bar_height_portrait = 7.539978mm`, `status_bar_height_default = 30dp`.
- Ảnh chụp màn hình user gửi là 1320×2860 (hệ số quy đổi sang máy thật 1,0909);
  tâm dọc lỗ camera = **69,5 px máy thật = 63,7 px trên ảnh 1320×2860**.
- Profile trong code: `S_ULTRA_8850` (id `s-ultra-8850`), form `phone`, KHÔNG phải fold.

## 4. Trạng thái thật từng chức năng (27/10/2026 — đừng viết lại thành "đã xong")

### 4.1. Image / Profile / PackageSet — ĐÃ CẮT, ĐÃ LÊN NHÁNH s26u
- `Images.ALL` chỉ còn **2 image đã chạy thật trên S26U**:
  - `FIND_X9U` — ColorOS Find X9 Ultra CN, gz `OneOS_ColorOS17_FindX9Ultra_S26U.img.gz`
    (5.290.346.735 byte, sha256 `9796d276…e919fe`, raw 10.385.141.760 byte).
  - `PIXEL_KODIAK` — Pixel 11 Pro, gz `OneOS_Pixel11Pro_Full_S26U.img.gz`
    (3.266.985.222 byte, sha256 `ee9b6005…d727c`, raw 6.529.871.872 byte).
    Upstream ghi "untested", nhưng nó **đã chạy thật trên S26U ngày 27/10** nên
    `testedOn = "Galaxy S26 Ultra"`, `tested = true`.
- Các image khác (FIND_N6, FIND_X9U_IN, PIXEL_YOGI, và image mới của upstream 0.4.23
  như PIXEL_KOMODO Pixel 9 Pro XL) **vẫn định nghĩa trong code, nhưng KHÔNG nằm trong `ALL`**.
  Image cũ đã từng dùng được đưa vào `Images.RETIRED` để stage cũ còn nhận diện.
  - `FIND_X9U_IN` cố ý CHƯA vào `ALL`: chưa chạy lần nào trên S26U, đang tải để phân tích
    (xem §7), không được đưa vào `ALL` khi chưa có bằng chứng chạy thật.
- `Profiles.BUILT_IN` chỉ còn **`S_ULTRA_8850`**, choices của nó chỉ 2 image trên, cả 2 `tested = true`.
- `PackageSets.ALL` chỉ còn **`X9U_SULTRA` + `PIXEL_SULTRA`**.
- Các profile/set khác vẫn định nghĩa (để tham chiếu/test object), không nằm trong
  `BUILT_IN`/`ALL`. Xóa hẳn chúng là Phase 2, chỉ làm sau khi test S26U xanh.
- **Lưu ý build:** `app/build.gradle.kts` vẫn còn liệt kê đủ các set (kể cả set máy gập / IN),
  trong khi model đã cắt còn 2 set. Đây là việc Phase 2: cắt `packageSets` trong
  `build.gradle.kts` về đúng 2 set S26U rồi mới build full sạch được (xem §6).

### 4.2. Status bar / cutout — V6, CHƯA TEST
- V6 hiện tại: **framework 7,60mm**, dump 7,599976mm, overlay `pixel_cutout_s26u`
  (dimens trong `switcher/overlays/pixel_cutout_s26u/res/values/dimens.xml`),
  cutout sha `8a992ed8a5d8a5523e5b24aba353ece2b397c6d55bd1c146cb518d19bde811c4`.
- Đích user chốt: **cân với tâm camera, không phải cân với OneUI**.
  Mô hình đã hiệu chuẩn: tâm icon/chữ status bar = chiều cao framework / 2.
- Lịch sử đo (ảnh 1320×2860, tâm camera 63,7):
  V3 home 87,5/khóa 86 — thẳng hàng nhưng thấp hơn camera ~22–25 px;
  V4 home 74–75 — khớp OneUI nhưng user vẫn phán thấp;
  V5 home 63,0/64,0 (đúng camera), khóa 67,0 (thấp hơn camera 3,3 px);
  V6 chọn home = khóa (home xuống tới ~67).
- **Cảnh báo đã chứng minh:** chỉ đổi chiều cao framework KHÔNG đảm bảo home = khóa,
  vì màn khóa cũng chạy theo (pin keyguard không giữ được ở V3).
  Sau mỗi lần switch V6 phải chụp **cả home + khóa** và đo lại, không báo "đã sửa"
  khi chưa có 2 ảnh đó.
- Overlay statusbar trong `switcher/overlays/pixel_statusbar/`: priority 1→10, có keyguard pin.
  File statusbar trong stage luôn giữ sha `07a72e1f00ecb62eb6b58f9cdced278b2c1c69df4c80999cbe6162d4eb212a03`
  trong `files.sha256` khi kiểm tra.

### 4.3. Độ sáng guest — map đã có, auto CHƯA ỔN ĐỊNH
- `switcher/assets/guest_prepare.sh` (nhánh S26U, chỉ khi profile `s-ultra-8850` AND form `phone`)
  tạo `product/etc/displayconfig/display_port_147.xml` từ **52 điểm vendor S26U**
  (float 0,0→1,0, nits 0,2289→782,4283) + proxSensor Samsung, qua overlay tmpfs product/etc.
  Bật bằng `ONEOS_GUEST_DISPLAY_CONFIG=1` khi switch.
- Có thêm ramp vendor: FastDecrease/Increase 0,06, Slow 0,04, MaxMillis 3000.
- Kết quả trên máy sau switch gộp (user báo 27/10): kéo tay lên được, **auto lên bất định,
  không ổn định, không mượt**; test đèn flash chỉ lên 2/10 rồi tụt rất nhanh; cùng 1 nguồn
  sáng giữ 5–10 giây không về cùng mức; có delay cả hiển thị lẫn thanh bar.
- Đừng đề xuất đo lux→nits kiểu OneUI nữa — user đã từ chối ("đơn giản hơn đi, chứ tao
  ko có đo được"). Hướng đơn giản đã giao: (1) tắt Adaptive brightness trong guest, kéo tay;
  (2) switch bản ramp gộp với V6. Chưa rõ user đã làm cách nào.
- Kiểm chứng còn thiếu: dòng `Display config: product/etc/displayconfig/display_port_147.xml
  (S26 Ultra nits curve…)` trong switch.log, và so lux guest vs OneUI cùng phòng.
- Rollback độ sáng: switch lại với `ONEOS_GUEST_DISPLAY_CONFIG=0`.
- **Biến môi trường quan trọng (đã đổi ở upstream 0.4.23):** `PETC="$GUEST_PRODUCT/etc"`
  (bản cũ là `$ROOTFS/system/product/etc`). Khi sửa guest_prepare.sh, giữ biến mới này.

### 4.4. Switch bằng script — lệnh chuẩn, pitfall đã chứng minh
- Lệnh switch chuẩn (ở OneUI): copy file vào `$STAGE=/data/local/tmp/oneos`, chmod 644,
  cập nhật `files.sha256`, **kiểm sha trong stage khớp bản mới trước khi switch**, rồi export bắt buộc:
  ```sh
  export ONEOS_PROFILE=s-ultra-8850
  export ONEOS_GUEST_FORM=phone
  export ONEOS_GUEST_FOLD=off
  export ONEOS_COVER_TSP=0
  export ONEOS_GUEST_FOLD_CONTINUE=0
  export ONEOS_GUEST_UNFOLD_PORTRAIT=0
  export ONEOS_GUEST_COMPACT_WINDOW=0
  export ONEOS_GUEST_WALLPAPER_GRID=0
  export ONEOS_GUEST_DISPLAY_CONFIG=1   # khi muốn dùng map sáng S26U; =0 để rollback
  sh oneos_switch.sh > /data/local/tmp/switch.log 2>&1
  ```
  Giữ `ONEOS_APP` mặc định 0. **Thiếu export → script lấy mặc định Fold `f8u`** → bản đồ sáng
  Fold8 Ultra áp lên panel S26U → guest system_server crash
  (`DisplayDeviceConfig.constrainNitsAndBacklightArrays: Min or max values are invalid;
  raw min=0.0026; raw max=0.196299`) — đã xảy ra thật 27/10, đừng lặp lại.
- App OneOS chính chủ báo Repair nếu ghi patch vào `files.sha256` ngoài pinned set
  (`StageStatus.verify()` coi file ngoài pinned set là lỗi). Đừng cố patch tay qua app UI
  cho V6/cutout; dùng đường switch script như trên.
- Pitfall copy file: file tải về trong Download có thể bị thêm đuôi có dấu cách
  (`OneOSPixelS26UCutout v5.apk`…); copy theo tên gốc là copy nhầm bản cũ.
  Phải dùng tên thật + kiểm sha ngay sau copy.

### 4.5. Display size / density — CHƯA CÓ SỐ ĐO THẬT, ĐỪNG ĐOÁN
- Cơ chế: chiều rộng dp = 1440×160/density. Bảng panel S26U: 400→576dp, 420→549dp,
  440→524dp, 460→501dp, 480→480dp, 520→443dp, 560→411dp, 600→384dp.
- Mức trung gian nhiều khả năng 440–460 density (501–524dp) nếu Standard ~400–420 và
  Large ~480–520 — **đây là suy ra từ bảng, chưa phải số đo thực tế**.
- Code hiện tại: guest phone **không có logic forced density riêng cho S26U**
  (UI Activator trong `oneos_switch.sh` chỉ chỉnh density cho fold; phone lấy base Samsung 480 → 480dp).
- Còn cần từ user (chưa có): ảnh Settings Display size trong guest, nấc Display size +
  Font size của Samsung, và density hiện tại trong guest
  (`wm density` / `settings get secure display_density_forced`).
- User nêu 27/10: ColorOS "để lớn thì hơi lớn quá, để tiêu chuẩn thì lại quá bé" —
  đó là vấn đề density/display size của guest, chưa giải quyết.

### 4.6. Camera guest — ĐÃ ĐIỀU TRA, KẾT LUẬN LÀ KHÔNG KHẢ THI BẰNG APK
- Đứt ở HAL trước cả app: host Samsung UniHAL `sec-camera-provider`, guest VINTF không khai
  camera provider, OneOS cố ý hide `system_ext/app/PersistentBackgroundCameraServices` /
  `com.google.pixel.camera.services` vì crash-loop do VINTF declaration error;
  `oneos_switch.sh` để nguyên cameraserver host.
- Port Pixel Camera APK một mình **không khả thi**.
- Test chẩn đoán đã giao, user chưa báo chạy: trong guest (1) `dumpsys media.camera`
  xem số camera = 0 hay >0 và có provider `internal/0` không; (2) cài Open Camera xem
  liệt kê được camera nào. Đừng làm patch camera mới khi chưa có 2 kết quả này.

### 4.7. ColorOS IN vs CN, Google, HyperOS — trạng thái
- ColorOS CN (`FIND_X9U`, googleServices=false) đưa Google vào: cài mỗi Play Store APK không đủ;
  cần GMS đầy đủ (PrebuiltGmsCore, Google Services Framework, gmssystem APEX payload,
  allowlist quyền privileged). Xếp hạng: (1) đổi sang bản IN (có Google sẵn, nhưng chưa test
  trên S26U), (2) cấy GMS từ IN vào CN là việc tầng dự án, rủi ro bootloop, (3) microG +
  Aurora là thay thế tạm, app cần Play Integrity sẽ không chạy.
- HyperOS làm guest: **chưa bắt đầu**. Là dự án port mới: firmware Xiaomi ưu tiên cùng chip
  SM8850 → MysticGSI → patch set + overlay + guest_prepare riêng cho service Xiaomi →
  ImageRef/profile/package set mới → test boot sửa crash-loop từng service.
  Hướng chi tiết ở `README-S26U.md` §8 (trong repo).
- File ColorOS IN đang tải (gofile.io, folder `ColorOS-17_Gsi`, file
  `OneOS_ColorOS17_FindX9Ultra_IN.img.gz`): gz kỳ vọng 5.882.128.321 byte,
  sha256 `413380426cdff8b5e760f1424895fc5b43e7a6ffe5f889e0406e437590c0d04e`;
  raw 12.069.945.344 byte, sha256 `a36ef550f4b2530fb9c7c6d363180d9eb4437e0497ebc87292697e4bf2a580b0`.
  **Tải xong phải verify size + sha gz trước, khớp mới giải nén + verify raw sha rồi mới
  phân tích IN vs CN; không khớp thì báo ngay, không phân tích file lỗi.**

## 5. Thứ tự ưu tiên làm việc (đừng làm ngược)

1. **Display** (status bar V6 test + density/display size theo số đo thật).
2. **App UI hết Repair** (pinned set — app chính chủ chấp nhận set S26U).
3. **Brightness auto** (ổn định, mượt, theo test chuẩn: sáng ổn định 60–90 giây, ghi mức cuối,
   từ slider thấp và cao — không test flash liên tiếp vì bộ điều khiển Pixel dùng trung bình
   ngắn/dài hạn + ngưỡng nên các lần test đó không độc lập).
4. **Camera chẩn đoán** (chỉ làm bước chẩn đoán ở §4.6 trước, không patch mù).
5. **HyperOS** (chỉ bắt đầu khi 4 việc trên đã có kết quả đo trên máy thật).

## 6. Build APK — làm đúng, không đoán

- Yêu cầu: **JDK 21** (Gradle dùng toolchain JDK 21, không tự tải), Android SDK có platform
  **`android-37`** (`ANDROID_HOME` hoặc `sdk.dir` trong `local.properties`), internet tới
  Google Maven + Maven Central. VM push trước đây chỉ có android-34 và sdkmanager bị proxy
  chặn nên **chưa build được APK** — đừng báo "build xong" khi chưa có file APK thật.
- Vào thư mục app:
  ```sh
  cd app-android
  # Chỉ Probe (không cần file overlay trong ../out):
  ./gradlew --max-workers=3 assembleProbeDebug
  # OneOS full (cần set overlay trong ../out, xem dưới):
  ./gradlew --max-workers=3 assembleFullDebug
  ```
- Output:
  - Probe: `app/build/outputs/apk/probe/debug/app-probe-debug.apk` — chỉ làm device report +
    test chỉ đọc, **không switch guest**.
  - Full: `app/build/outputs/apk/full/debug/app-full-debug.apk` — bản debug, ký bằng debug key
    của máy build, cài được ngay. Bản full này mới là app để chạy guest.
- Release: `./gradlew assembleFullRelease` sẽ **từ chối** nếu không có
  `~/.oneos-release/keystore.properties` (storeFile / storePassword / keyAlias / keyPassword).
  Nó không cho ra APK unsigned. Mọi bản update sau phải ký cùng 1 key mới cài đè được.
- Full build cần các set overlay trong `../out/` (ví dụ `out/overlays_x9u_r50`,
  `out/overlays_pixel_kodiak`) — `out/` bị gitignore, **không có trong repo**.
  Build bằng `scripts/make-overlays.sh <system.img> out/overlays` (cần apktool + extract.erofs),
  và mọi file phải khớp `app-android/packages/<set>.sha256`.
- Cài lên S26U: gỡ app OneOS chính chủ trước nếu cùng applicationId `com.fahadali.oneos`
  mà khác chữ ký (debug key vs key release của tác giả) — không gỡ thì Android báo lỗi cài đè.
  Verify trước khi cài: `apksigner verify <apk>` và kiểm tra versionCode/versionName trong APK
  (hiện là 0.4.13/26 ở base cũ, 0.4.23 ở base mới — khi build bản S26U riêng nên tăng version
  để khỏi lẫn với bản gốc).
- Test model: `./gradlew test` (core/model). Test đã sửa về kỳ vọng S26U-only;
  khi sync upstream, test object mới của upstream phải giữ nguyên, test kỳ vọng
  `ALL`/`BUILT_IN` phải giữ nguyên bản S26U (xem §8).

## 7. Quy tắc làm việc bắt buộc — vi phạm là làm lại

- **Cấm nói "xong / fix rồi / được rồi".** Chỉ báo "đã làm X" kèm bằng chứng thật:
  hash, output lệnh, ảnh + phép đo. User phán trên thiết bị thật mới tính đạt.
- **Không ước lượng giờ hoàn thành.** Chỉ báo trạng thái đo được.
- **Không hỏi lại thứ đã chốt / đã khoanh.** Ảnh user khoanh + đính chính bằng miệng
  thắng bản vẽ, thắng suy luận từ code.
- **Kiểm chứng phải ở view mặc định user mở.** Đừng chụp render ở chế độ khác rồi báo đã sửa.
- **Ảnh user khoanh đã định nghĩa lỗi thì mở lại ảnh đó trước khi hỏi thêm.**
  Chỉ hỏi thêm khi ảnh khoanh không đủ định nghĩa lỗi.
- **Không tự build IPA/APK sau fix khi không có lệnh explicit** (đối với các dự án khác của user;
  riêng OneOS, build APK chỉ khi user/nhiệm vụ yêu cầu rõ).
- **Không force-push lên `main`, không force-push đè lịch sử của người khác.**
  Chỉ được `git push --force-with-lease` trên nhánh của riêng mình sau rebase.
- **Không commit:** `probe-findings-*/`, `firmware/`, `out/`, file APK, key/keystore,
  token/password/PAT. Bí mật cấp qua Secure Vault hoặc biến môi trường thoáng qua, không vào git,
  không vào chat, không vào memory/file.
- **Không tự gửi tin thay user.** Draft là để user gửi.
- **Khi giả định sai, tự nhận lỗi công khai** (ví dụ: vụ files.sha256/app UI, vụ mặc định Fold,
  vụ copy nhầm file cũ, vụ token/repo) rồi sửa bằng bằng chứng, không biện hộ.
- **Bước có thể fail sau khi framework dừng thì lưu log ra file sống sót qua reboot trước.**
- **Không build đoán mò khi chưa có ảnh/đo rõ của user** (đặc biệt density, status bar, camera).

## 8. Sync upstream — quy trình duy nhất được phép

Upstream đang ra bản liên tục (0.4.13 → 0.4.23 chỉ trong vài ngày, có cả merge Fold8).
Sync theo mốc version, không sync mù mọi commit.

```sh
git checkout main
git pull upstream main          # upstream = https://github.com/fahadalijaved23/OneOS.git
# hoặc bấm Sync fork trên web GitHub (chỉ sync được main, không sync được s26u)
git checkout s26u
git rebase main                 # S26U commit nằm gọn trên đầu main mới
./gradlew test                  # rồi mới build full / test máy thật
git push --force-with-lease origin s26u
```

Khi rebase, conflict gần như chắc chắn rơi vào đúng các file S26U đã sửa:
`Images.kt`, `Profiles.kt`, `PackageSets.kt` (+ 3 test), `make-overlays.sh`,
`guest_prepare.sh`, overlay statusbar. Nguyên tắc giải conflict (đã áp dụng cho 0.4.23):

- **Giữ object mới của upstream** (định nghĩa image/profile/set mới, test object mới,
  code chung như root script, wallpaper Pixel, unfold RRO Fold8).
- **Giữ kỳ vọng S26U** cho `Images.ALL` (chỉ 2 image), `PackageSets.ALL` (chỉ 2 set),
  `Profiles.BUILT_IN` (chỉ `S_ULTRA_8850`), và các test kỳ vọng tương ứng.
- Đừng lấy bừa 1 phía, đừng đè file S26U cũ lên code upstream mới, đừng đè file upstream
  mới lên patch S26U.
- Sau rebase: chạy test, build Probe trước, rồi mới build full; sync code mà không rebuild
  overlay với image mới (nếu upstream đổi image) là chưa xong — image guest (`system.img`,
  overlay set trong `out/`) không nằm trong repo.
- Đọc message commit upstream xem có đụng tới S26U không: status bar, display, brightness,
  camera, package set — nếu đụng thì test kỹ, nếu không đụng thì merge an toàn hơn.

## 9. Việc còn mở ngay lúc bàn giao (27/10/2026)

1. Test V6 status bar trên S26U thật: copy/switch theo §4.4, chụp **cả home + khóa**, đo lại.
2. Test ramp độ sáng gộp với V6, hoặc xác nhận user đã tắt Adaptive brightness trong guest.
3. Lấy số đo display size/density thật từ user (§4.5) rồi mới chỉnh density S26U.
4. Chạy 2 test chẩn đoán camera (§4.6) và báo kết quả, chưa patch camera.
5. Khi file IN tải xong: verify sha (§4.7) rồi phân tích IN vs CN.
6. Phase 2 (sau khi test S26U xanh): cắt `packageSets` trong `build.gradle.kts` về 2 set S26U;
   xóa hẳn các profile/set/image không còn trong `BUILT_IN`/`ALL` nếu user duyệt.
7. HyperOS: chỉ bắt đầu sau khi 1–4 có kết quả đo.

## 10. Định nghĩa "bàn giao xong" cho AI mới

Một nhiệm vụ chỉ được coi là xong khi có đủ, trong cùng một lần báo cáo:

- Link commit/nhánh trên GitHub (sha đầy đủ, đã verify qua API, không phải sha local).
- Diff tóm tắt: file nào đổi, vì sao, conflict nào đã giải và giải theo nguyên tắc nào.
- Bằng chứng kiểm chứng: output test / `sh -n` / `apksigner verify` / ảnh + số đo trên máy thật
  (ghi rõ góc chụp, chế độ mặc định, home + khóa nếu là status bar).
- Việc còn mở + việc cần user làm tiếp (nếu có), viết riêng, không gộp vào phần "đã làm".
- Nếu chưa có đủ 4 điểm trên, báo cáo phải ghi rõ "chưa xong, còn kẹt ở …" và cần gì để tiếp tục.
