## Ghi chú nhánh s26u (2026-10-27, rebase lên upstream 0.4.23)

- Repo gốc cho S26U là fork `Smarthome-Hume/OneOS`, nhánh `s26u`, nền upstream `0.4.23` (`a83b559…`).
- `main` của fork này là mirror upstream, KHÔNG sửa gì vào `main`; mọi patch S26U nằm trên `s26u` và rebase lên `main` mới mỗi lần tác giả update.
- Repo `Smarthome-Hume/OneOS-S26U` cũ (nền 0.4.13, main `282aa807…`) chỉ còn là bản lưu, không phải gốc làm việc nữa.
- Merge 0.4.13 → 0.4.23: upstream thêm image Pixel 9 Pro XL komodo, set Pixel Fold8 / Pixel9, profile S26+ Exynos / Flip7; các object mới này được GIỮ NGUYÊN trong code (định nghĩa, test object), chỉ `Images.ALL` vẫn là 2 image S26U, `PackageSets.ALL` vẫn là 2 set S26U, `Profiles.BUILT_IN` vẫn chỉ `S_ULTRA_8850` — nên test kỳ vọng S26U vẫn giữ nguyên, test object upstream mới giữ nguyên.


# OneOS-S26U — OneOS tối ưu riêng cho Galaxy S26 Ultra

Fork riêng, không phụ thuộc tác giả gốc. `main` của repo này **là bản S26U**,
không phải một nhánh phụ. Upstream: https://github.com/fahadalijaved23/OneOS
(Apache 2.0, xem `LICENSE`/`NOTICE`/`CREDITS.md` của upstream).

## 1. Mục đích — tại sao phải tự làm

Mục đích của fork này là: **mọi chức năng port sang phải hoạt động được
trên S26U, và độ phân giải / hiển thị nội dung phải được điều chỉnh lại
cho phù hợp nhất với S26U** — chứ không phải chỉ chạy được cho có, rồi
chờ tác giả gốc sửa từng chỗ một.

Tiêu chí nghiệm thu cho mỗi chức năng (không đạt = chưa xong, không được
ghi là "xong" trong commit message hay README):

1. Chức năng đó chạy được trên máy thật S26U, có bằng chứng đo được
   (log, ảnh chụp, `dumpsys`, hash file) — không phải "chạy trên lý thuyết".
2. Hiển thị đúng panel S26U (xem §2): kích thước chữ/icon, chiều rộng dp,
   status bar cân với lỗ camera, không bị to quá / bé quá / lệch so với One UI.
3. Không làm hỏng chức năng khác đã chạy được (regression check bằng ảnh
   home + khóa sau mỗi lần switch).

## 2. Máy đích — Galaxy S26 Ultra (SM-S948, m3q, SM8850)

Số đo từ Probe ngày 2026-10-27 (`findings-SM-S948B-2026-10-27`, không commit
lên repo này — file probe chứa thông tin máy, giữ ở local):

- Màn hình: 1440 × 3120 px, xdpi 501,0411 / ydpi 498,4151, density bucket 600 (3,75).
- `ro.sf.lcd_density` Samsung chia sẻ cho guest: **480** → guest ở 480 sẽ là
  1440 × 160 / 480 = **480 dp** chiều rộng.
- Lỗ camera: Rect(680,0–760,139) px, tâm dọc y = 69,5 px máy thật.
  Trong ảnh screenshot 1320 × 2860, tâm lỗ = 63,7 px (hệ số 3120/2860 = 1,0909).
- One UI: `status_bar_height_portrait = 7,539978 mm`, `status_bar_height_default = 30 dp`.
- Cutout path (dp): `M 0,0 H -10.66666666666667 V 37.06666666666667 H 10.66666666666667 V 0 H 0 Z`
  (21,333 dp × 37,067 dp, rect approximation chép nguyên path này).
- One UI 9.0, Android 17, SDK 37, build CP2A.260605.016.

## 3. Image chỉ còn 2 — đã chạy thật trên S26U

`Images.ALL` trong fork này chỉ có 2 image. Cắt ở
`app-android/core/model/src/main/kotlin/com/fahadali/oneos/core/model/Images.kt`,
`Profiles.BUILT_IN` chỉ còn `S_ULTRA_8850`, `PackageSets.ALL` chỉ còn 2 set
tương ứng. Các image khác của upstream chưa bị xóa khỏi code: object của
chúng vẫn nằm trong file (để các call site / test của máy khác còn biên dịch),
nhưng chúng **không nằm trong `ALL` / `BUILT_IN` / `PackageSets.ALL` nên app
không bao giờ offer chúng**, và chúng nằm trong `Images.RETIRED` để stage cũ /
file đã tải vẫn được nhận diện là "không còn hỗ trợ", không phải "không phải
image OneOS". Xóa hẳn object của chúng là việc dọn dẹp Phase 2 cho worker
tiếp theo, sau khi các call site đó đã được gỡ.

| Image | File .gz | Trạng thái trên S26U |
|---|---|---|
| ColorOS 17, Find X9 Ultra build (CN) | `OneOS_ColorOS17_FindX9Ultra_S26U.img.gz` (5.290.346.735 B, sha `9796d276…8708e919fe`) | Đã test upstream trên S26U, `tested = true` |
| Pixel 11 Pro, kodiak build | `OneOS_Pixel11Pro_Full_S26U.img.gz` (3.266.985.222 B, sha `ee9b6005…9dea8d727c`) | **Đã chạy thật trên S26U 2026-10-27**: guest boot, `Bound guest /oem`, đo status bar V3–V6. Upstream ghi "untested"; fork này đã sửa `testedOn = "Galaxy S26 Ultra"` và `tested = true` theo bằng chứng đó |

**Không có trong fork này, và tại sao:**

- ColorOS 17 Find X9 Ultra **IN** (global, có Google Play): upstream ghi
  `testedOn = null`, profile `tested = false`, và ngày 2026-10-27 nó mới
  đang được tải về để phân tích, chưa chạy lần nào trên S26U. Đưa nó vào
  `ALL` lúc này là nói dối về "đã test". Chỉ thêm lại khi đã chạy thật
  trên S26U, kèm cập nhật `testedOn`/`tested` và bằng chứng.
- ColorOS Find N6, Pixel 11 Fold (yogi): image của máy gập, chưa chạy trên S26U.

## 4. Tối ưu S26U đã làm — có bằng chứng

### 4.1 Status bar + cutout (Pixel guest) — đã build, V6 chưa test

- Overlay mới `switcher/overlays/pixel_cutout_s26u/` (target `android`,
  static, priority 10): cutout path của One UI + chiều cao status bar.
  `scripts/make-overlays.sh` đã vá để build nó (`OneOSPixelS26UCutout.apk`)
  khi framework-res có đủ 4 resource và không khai overlayable.
  `guest_prepare.sh` copy nó vào `$STAGE/oem/overlay`.
- Overlay SystemUI `switcher/overlays/pixel_statusbar/`: priority 1 → 10,
  pin `status_bar_header_height_keyguard = 7,539978 mm`.
  **Cảnh báo thật:** pin này đã KHÔNG giữ được khóa ở V3 — khóa vẫn dịch
  theo framework (+19 px ảnh). Đừng tin pin này mà không đo lại khóa.
- Số đo (ảnh 1320 × 2860, cụm phải 5G/sóng/pin là chuẩn sạch nhất):
  trước V3 home 47,5 / khóa 67; V3 (9,68 mm) home 87 / khóa 86;
  V4 (8,40 mm) home 74–75 (khớp One UI cùng thang là 76,1, lệch 1–2 px);
  V5 (7,20 mm) home 63–64 / khóa 67.
  Đích cuối do user chốt: **tâm camera đi qua chính giữa icon/chữ status bar**,
  không phải khớp One UI.
- **V6 hiện tại: 7,60 mm** (7,20 + 0,39 mm để home xuống tới khóa ~67).
  APK đã build, apksigner verify OK, dump 7,599976 mm,
  sha256 `8a992ed8a5d8a5523e5b24aba353ece2b397c6d55bd1c146cb518d19bde811c4`.
  **Chưa test trên máy** (tính đến lúc push fork này). Home = khóa không
  đảm bảo chỉ bằng chiều cao framework vì khóa cũng chạy theo; sau switch
  V6 phải chụp lại cả home + khóa để đo, không được kết luận bằng suy luận.

### 4.2 Độ sáng guest (Pixel) — map đã vào, auto vẫn chưa ổn

- `guest_prepare.sh` có nhánh S26U (chỉ khi `ONEOS_PROFILE=s-ultra-8850`
  và `ONEOS_GUEST_FORM=phone`): tạo
  `product/etc/displayconfig/display_port_147.xml` từ 52 điểm vendor S26U
  (nits 0,2289 → 782,4283, interpolation linear) + cảm biến tiệm cận Samsung.
  Switch gộp bắt buộc `ONEOS_GUEST_DISPLAY_CONFIG=1` (để 0 là bỏ qua map).
- Bản có ramp vendor (Fast 0,06 / Slow 0,04 / MaxMillis 3000), sha guest_prepare
  `c8e644fd48033b2bf5883f32d7b7b85d7a2e9a6b44e2d25e494179f60c6b24eb`.
- **Trạng thái thật, không giấu:** sau switch gộp, auto vẫn bất định
  (lúc lên lúc không, test đèn flash chỉ lên 2/10 rồi tụt rất nhanh, giữ sáng
  ổn định 5–10 s cũng không về cùng mức). Map chỉ là bước cuối (nits → backlight);
  chuỗi auto là lux → mức auto → map, và bộ điều khiển Pixel dùng trung bình
  ngắn/dài hạn + ngưỡng nên test flash liên tiếp không độc lập. Chưa có
  xác nhận dòng `Display config: product/etc/displayconfig/display_port_147.xml`
  trong switch.log, chưa có so lux guest vs One UI cùng phòng.
  Cách đơn giản nhất lúc này (không cần switch lại): tắt Adaptive brightness
  trong guest, kéo tay.

### 4.3 Độ phân giải / hiển thị — workstream chính còn mở

Đây là lý do fork tồn tại, và là phần **chưa xong**, ghi rõ để worker tiếp
theo (Notion AI, xem §7) không tưởng đã xong:

- Hiện trạng: guest phone **không có logic forced density riêng cho S26U**.
  UI Activator trong `oneos_switch.sh` chỉ chỉnh density cho fold
  (`GUEST_FOLD_FORM=1` + layout); phone form thì "no fold layout, left alone",
  guest lấy base Samsung 480 → 480 dp.
- Vấn đề đã thấy ở ColorOS (2026-10-27): "để lớn thì hơi lớn quá, để tiêu
  chuẩn thì lại quá bé" — ColorOS chỉ có vài mức rời rạc, không có mức trung
  gian rơi đúng vị trí Samsung. Bảng quy đổi panel S26U (chắc chắn, không
  phụ thuộc ROM): 400 → 576 dp, 420 → 549 dp, 440 → 524 dp, 460 → 501 dp,
  480 → 480 dp, 520 → 443 dp, 560 → 411 dp, 600 → 384 dp.
  Mức trung gian nhiều khả năng ở **440–460 density (501–524 dp)** nếu
  Standard ~400–420 và Large ~480–520 — đây là suy ra từ bảng, **chưa phải
  số đo thực tế trên guest**, cần đo mới chốt.
- Việc cần làm (theo thứ tự, không đoán số):
  1. Đo trong guest đang chạy: `wm density`, `wm size`, smallest width,
     và `settings get secure display_density_forced`.
  2. Đo One UI: Samsung đang để Display size nấc nào, Font size nấc nào
     (Samsung tách 2 thứ riêng; ColorOS gộp — đừng lẫn).
  3. Chụp cùng 1 app ở cùng 1 nội dung trên One UI và guest, so kích thước
     chữ/icon thực tế, rồi mới chọn density trung gian cho phone form
     (qua `ONEOS_GUEST_DENSITY` hoặc forced density cho display 0 của S26U,
     không copy logic fold sang phone một cách mù).
  4. Lặp lại cho cả 2 guest (Pixel + ColorOS CN): chúng không dùng cùng
     cơ chế display size, không được chốt 1 số cho cả 2 nếu chưa đo cả 2.

## 5. Chức năng khác — trạng thái thật

| Chức năng | Trạng thái |
|---|---|
| Switch bằng script (không qua app UI) | Chạy được, với export bắt buộc: `ONEOS_PROFILE=s-ultra-8850`, `ONEOS_GUEST_FORM=phone`, `ONEOS_GUEST_FOLD=off`, `ONEOS_COVER_TSP=0`, `ONEOS_GUEST_FOLD_CONTINUE=0`, `ONEOS_GUEST_UNFOLD_PORTRAIT=0`, `ONEOS_GUEST_COMPACT_WINDOW=0`, `ONEOS_GUEST_WALLPAPER_GRID=0`, `ONEOS_GUEST_DISPLAY_CONFIG` theo ngữ cảnh. Thiếu export → lấy mặc định Fold (`f8u`) → crash system_server (đã chứng minh 2026-10-27). |
| Switch bằng app UI sau khi copy patch tay | **Không chạy được:** app báo Repair "Some of its files changed since setup" vì patch ngoài pinned set. Muốn qua app UI thật phải build lại app có patch trong pinned set — chính là fork này, chưa hoàn thành phần này. |
| Camera trong guest Pixel | **Chưa chạy.** Đứt ở HAL trước cả app (Samsung UniHAL, VINTF guest không khai camera provider, OneOS cố ý hide `PersistentBackgroundCameraServices` vì crash-loop). Port Pixel Camera APK một mình không khả thi. Test chẩn đoán đầu tiên: `dumpsys media.camera` (số camera = 0 hay >0) + cài Open Camera. |
| HyperOS (Xiaomi) làm guest | **Chưa bắt đầu.** Là 1 dự án port mới (firmware Xiaomi + MysticGSI + patch set + guest_prepare riêng), không phải cài APK. Xem §8. |

## 6. Build

Yêu cầu (upstream README): **JDK 21**, Android SDK platform `android-37`
(`ANDROID_HOME` hoặc `sdk.dir` trong `local.properties`), internet tới
Google Maven + Maven Central. Chi tiết ở `app-android/README.md`.

```sh
git clone https://github.com/Smarthome-Hume/OneOS.git (nhánh s26u)
cd OneOS-S26U/app-android
./gradlew assembleProbeDebug   # Probe: không cần gì ngoài repo này
./gradlew test                # unit tests
```

**Lưu ý build ở VM ngày 2026-10-27:** máy ảo dùng để push fork này chỉ có
SDK platform `android-34`, và `sdkmanager` tải `android-37` bị proxy chặn,
nên **APK của fork này chưa được build/verify trên VM đó**. APK phải được
build ở máy có đủ android-37 (Android Studio của user, hoặc máy của worker
tiếp theo), rồi mới verify bằng `apksigner verify` + `aapt2 dump` trước khi
gửi cho user. Đừng ghi "đã build APK" nếu chưa có file APK + hash đó.

App full (`assembleFullDebug`/`assembleFullRelease`) cần package set từ
`../out/overlays*` — không có trong repo (gitignore). Release ký bằng key ở
`~/.oneos-release/keystore.properties`; không có thì release packaging dừng.

## 7. Cho worker tiếp theo (Notion AI)

Repo này được giao cho Notion AI quản lý như một công nhân code, chịu trách
nhiệm code tiếp cho fork này. Quy tắc giao việc, để worker không làm hỏng
những gì đã đo:

1. **Đọc README-S26U.md này trước, rồi mới đọc code.** Số đo ở §2–§4 là
   bằng chứng, không phải gợi ý. Thay đổi nào mâu thuẫn với số đo phải có
   số đo mới thay thế, không được sửa README cho khớp code mới một cách mù.
2. **Không nói "xong / fix rồi / được rồi".** Chỉ báo "đã làm X" kèm bằng
   chứng (hash, log, ảnh + phép đo). User là người duy nhất phán "đạt" trên
   thiết bị thật.
3. **Không hỏi lại thứ đã chốt:** S26U-only, main là bản S26U, IN chưa test
   thì chưa vào `ALL`, V6 chưa test thì vẫn là chưa test.
4. **Thứ tự ưu tiên:** (a) display/resolution phone form (§4.3),
   (b) app UI chấp nhận patch trong pinned set (hết Repair),
   (c) brightness auto ổn định, (d) camera chẩn đoán, (e) HyperOS (§8).
   Không tự ý đổi thứ tự mà không báo user.
5. **Không commit lên repo này:** file probe, `firmware/`, `out/`,
   APK debug, keystore, token, password, private key. Xem `.gitignore`.
6. **Không force-push.** Lịch sử diverged thì tái dựng commit byte-identical
   hoặc tạo commit mới, không ghi đè lịch sử của người khác.

## 8. Hướng HyperOS (chưa làm, chỉ ghi hướng)

Muốn HyperOS chạy làm guest trong OneOS-S26U, cần: firmware Xiaomi flagship
(ưu tiên cùng chip SM8850 để tránh lỗi CPU SVE/SME như vụ Pixel) → build GSI
bằng MysticGSI (ngoài repo này, giống cách build image ColorOS/Pixel) →
patch set mới trong `switcher/patches/` + overlay mới + xử lý riêng trong
`guest_prepare.sh`/`guest_start.sh` cho service của Xiaomi (khác oplus-services
của ColorOS và SystemUIGoogle của Pixel) → thêm `ImageRef` mới trong
`Images.kt` + profile + package set → test boot, sửa crash-loop từng service
một. Đây là công việc tầng dự án, không phải "cài APK HyperOS là xong".
