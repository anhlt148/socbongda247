# NHẬT KÝ THAY ĐỔI — hệ Sóc
> Mỗi lần sửa: một dòng. **Ngày · sửa gì · vì sao · đụng những đâu · đã kiểm gì.**
> Sổ này để lần sau truy được "cái này ai đổi, đổi vì cái gì".

## 14/08/2026
- **PHÍM TẮT GẮP ẢNH cho extension (v1.3 → 1.4)** · anh đặt: "chuột phải + phím tắt là tải về
  trạm luôn, các tính năng khác giữ nguyên" · **VÌ SAO**: chuột phải → rê xuống → bấm mục là
  ba nhịp; gắp một loạt ảnh thì ba nhịp nhân mấy chục tấm rất mỏi tay
  · **CÁCH LÀM**: `chrome.commands` hai phím — **Alt+S** về kho VIỆC, **Alt+A** về KHO CHUNG
  (menu có hai đích thì phím tắt phải có đủ hai — luật chính-phụ). Biết "ảnh nào đang trỏ"
  bằng cách **mượn trạng thái `:hover` trình duyệt vốn tự giữ**, bơm một mẩu mã vào trang lúc
  bấm phím rồi rút ra ngay — KHÔNG cắm content script chạy thường trực trên mọi trang anh mở
  · **DÙNG LẠI** `guiAnh`/`guiAnhKho` của menu chuột phải: cùng cổng watermark, cùng chống
  trùng vân tay, không viết luồng song song · lời nhắn hiện NGAY TRÊN TRANG (không dùng thông
  báo góc màn hình vì gắp liên tục thì dồn đống)
  · **ĐỤNG**: `tram/extension/manifest.json` (thêm khối `commands`, lên v1.4) ·
  `tram/extension/nen.js` (+3 hàm, +1 listener; KHÔNG sửa hàm cũ nào) · `kiem_tram.py`
  (thêm tầng ⑧) · `KIEN-TRUC.md` (bản đồ trước nay THIẾU HẲN extension — đã bổ sung)
  · **LỖI TỰ BẮT ĐƯỢC KHI THỬ**: lớp dự phòng dò ảnh duyệt cả `body`, nên trang chỉ có MỘT
  tấm ảnh mà trỏ vào vùng trống vẫn gửi tấm đó đi — im lặng. Vá: bỏ `html`/`body`, chỉ soi 3
  cấp sát con trỏ, và khối phải ≤60% màn hình. Đo thật: cùng vị trí chuột, bản cũ vơ nhầm ảnh,
  bản mới trả rỗng
  · **ĐÃ KIỂM**: cú pháp JS + JSON ✅ · 5 ca dò ảnh trên trình duyệt thật (img thường ·
  background-image · img bị lớp phủ che · ô không phải ảnh · khối to 64% màn chứa 1 ảnh) —
  đúng cả 5 · **thử ngược** cổng ⑧ bằng cách cắm một luồng song song giả: cổng bắt được, gỡ ra
  thì im · `kiem_tram.py --sau` ✅ ĐẠT HẾT
  · ⏳ **CÒN CHỜ ANH**: vào `chrome://extensions` bấm ↻ nạp lại tiện ích thì phím tắt mới ăn

## 12/08/2026
- **SỬA MẶC ĐỊNH FADE — em đặt sai, anh bắt đúng** · anh hỏi "đầu video cần âm lượng cao để
  thu hút, set 0,3s tăng dần thì lúc đầu bé à?" → **anh đúng, mặc định của em sai**. ĐO THẬT
  trên `giong.mp3` của bài video-2 ngày 11/08: fade vào 0,3s làm 0,3 giây đầu tụt **-14,2 dB**
  (0,5s đầu tụt -6,6 dB); tốc độ kênh 4,4 tiếng/giây nên 0,3s ≈ **1,3 tiếng bị hạ âm lượng** —
  mà câu đầu của kênh chính là ĐỌC LẠI TIÊU ĐỀ. Mục đích thật của fade vào chỉ là chống tiếng
  "bụp" lúc mở file, việc đó cần 10–50ms: 0,05s chỉ tụt 2,9 dB, tai không nghe ra
  · **SỬA**: giọng vào 0,3 → **0,05** · nhạc vào 1,5 → **0,4** · giọng ra 0,8 → **0,4**;
  bước nhập đổi 0,1 → 0,01–0,05 cho chỉnh được mức nhỏ
  · **ĐO THÊM**: nhạc vào 0s / 0,4s / 1,5s / 3,0s cho độ to mở đầu bản trộn chênh **0,1 dB** —
  vì nhạc chạy ở 11% dưới giọng 130%. Núm nhạc-vào chỉ đổi CẢM GIÁC, không đổi độ to. Đã ghi
  thẳng lên chú thích để anh khỏi vặn nhầm chỗ
  · **CỔNG CẢNH BÁO** trên trang: `giong_vao > 0,15` là kêu ngay, kèm lý do
  · sửa nốt docstring `phong_cach.py` còn tả thiết kế DẢI đã bỏ (bài học #16)
  · **ĐÃ KIỂM**: cảnh báo kêu đúng ở 0,3 và im ở 0,05; `kiem_tram.py --sau` ✅ ĐẠT HẾT
- **BỎ DẢI → MỘT CHỈ SỐ + 4 núm âm lượng vào/ra** · anh chốt: "set 1 chỉ số là được, không
  cần khoảng; bỏ luôn đa dạng hoá và giải thích" · `NUM` trong `phong_cach.py` đổi từ
  `(dải, lo, hi, lẻ)` → `(mặc_định, lo, hi, lẻ)`; bỏ cờ `bat`; `cho_video()` lấy thẳng, không
  rút ngẫu nhiên nữa (chỉ còn CHỌN GIỌNG là xoay theo video khi anh bật nhiều giọng) · tốc độ
  mỗi giọng cũng về một số · **DI CƯ ÊM**: sổ bản cũ lưu dải thì `chuan()` tự quy về một số
  (giọng lấy giữa dải), không nổ, không mất giọng anh đã thêm (giữ nguyên "Minh quân pro")
  · **THÊM 4 NÚM**: nhạc to dần ở đầu · nhạc nhỏ dần ở cuối · giọng to dần ở đầu · giọng nhỏ
  dần ở cuối. Nối vào `fc` của ffmpeg qua hàm `_fade()`; núm để **0 thì BỎ HẲN** bộ lọc vì
  `afade d=0` là lỗi ffmpeg — đã thử thật cả 3 ca (mức đang đặt · tất cả 0 · chỉ vào không ra)
  · trang bỏ khối giải thích + ô đa dạng hoá, lưới 4 cột → 2 cột, bảng xem trước rút còn
  "6 video kế tiếp ai đọc" · sửa cả chữ mô tả đã thành mâu thuẫn (mục Chuyển động cũ nói
  "cùng mức phóng là dấu vân tay" trong khi nay mọi video CÙNG mức phóng)
  · **CỔNG ⑦ VIẾT LẠI** cho khớp thiết kế mới — cổng cũ kiểm "khác video khác thông số" nay
  sẽ báo sai; nay canh: mọi núm là một chỉ số · kẹp biên · sổ cũ tự quy đổi · mọi video dùng
  đúng chỉ số anh đặt · xưởng dùng đủ 4 núm mới · núm 0 thì bỏ afade
  · **ĐÃ KIỂM**: ffmpeg chạy 3/3 ca, trang mở bằng trình duyệt thật, `kiem_tram.py --sau`
  ✅ ĐẠT HẾT (tầng ⑦ nay 21 mục)
- **NHIỀU GIỌNG ĐỌC + làm rõ "2 ô số"** · anh hỏi "sao lại có 2 dải giá trị?" → **lỗi giao
  diện của em**: khái niệm DẢI chỉ có trong lời em nói, trang không tự nói ra. Sửa: thêm khối
  vàng đầu trang giải thích TỪ–ĐẾN + tiêu đề cột TỪ/ĐẾN trên mỗi bảng + chỉ cách "gõ hai ô
  bằng nhau" nếu muốn cố định · anh đặt thêm: cấu hình NHIỀU giọng VBee kèm tốc độ riêng
  · **THÊM** `giong_ds` vào `phong_cach.py` (mã · tên gợi nhớ · dải tốc độ riêng · bật/tắt),
  mỗi video rút một giọng đang bật; danh sách KHÔNG BAO GIỜ rỗng (xoá hết → tự trả giọng đang
  chạy, không thì xưởng mất giọng câm) · bỏ núm "tốc độ đọc" chung vì tốc độ nay thuộc từng giọng
  · **CỬA THỬ GIỌNG** `/api/thu-giong` + `/thu-giong.mp3` — DÙNG LẠI `xuong.doc_giong` chứ không
  viết luồng song song; gõ sai mã là hỏng cả mẻ nên phải thử + NGHE được trước khi lưu
  · ⚠️ **BẪY TỰ BẮT ĐƯỢC**: xưởng đệm giọng theo LỜI (`giong.mp3.loi`) — đổi giọng mà lời không
  đổi thì dùng lại file giọng CŨ, đúng họ lỗi anh bắt 07/08. Vá: dấu vân tay nay gồm
  `mã giọng | tốc độ | lời` · **CỔNG** tầng ⑦ thêm 5 mục canh giọng
  · **ĐÃ KIỂM**: gọi VBee THẬT — mã đúng trả ok 3,3s audio; mã bịa trả lỗi rõ ràng (không im
  lặng); route nghe thử trả 27KB audio/mpeg (không để link hứa suông); `kiem_tram.py --sau`
  ✅ ĐẠT HẾT
- **TRANG PHONG CÁCH VIDEO** (`/phong-cach`) — núm vặn chống dập khuôn · anh đặt: cấu hình
  các thông số làm video đa dạng để nền tảng không đọc ra "máy làm hàng loạt" · **cách làm:
  anh đặt DẢI, mỗi video rút một giá trị trong dải, gieo theo mã việc** → video nào cũng khác
  nhau mà dựng lại vẫn ra y hệt (tất định, truy lỗi được), và luôn nằm trong khoảng anh duyệt
  · **THÊM MỚI** `phong_cach.py` (rà tên trước: phong_cach/PHONG_CACH/api đều 0 trùng) — não
  một nguồn, cấu hình ở `kho-tai-nguyen/phong-cach.json`, ghi nguyên tử (os.replace), kẹp biên
  cứng nên gõ nhầm không phá được video · trang `tram/phong-cach.html` có BẢNG THỬ 6 video
  tính bằng đúng công thức xưởng + dòng đánh giá "dải có đủ rộng không" · route `/phong-cach`,
  `/api/phong-cach` (GET+POST), `/api/phong-cach-thu` (0 trùng) · **7 điểm nối vào xuong.py**:
  rút thông số đầu `dung()`, áp lên chuyen_dong, giọng đọc, trần một kiểu (truyền TAY vì là
  tham số mặc định chốt lúc def), nhóm nhạc, âm lượng + fade nhạc · import ĐẦU FILE cả hai
  bên (luật cứng) · thêm trang vào `menu.js` (luật menu chung 10/08) · **CỔNG MỚI** tầng ⑦:
  kẹp biên · tất định · khác video khác thông số · xưởng thật sự dùng · route sống · có trong
  menu · **ĐÃ KIỂM**: lưu→đọc lại từ đĩa đúng giá trị đặc trưng, kẹp biên chặn zoom [99,-5]→
  [1.02,1.20], trang mở bằng trình duyệt thật (bảng thử 6 dòng, menu 5 nút), `kiem_tram.py
  --sau` ✅ ĐẠT HẾT
- **TIẾP NHẬN KHO NHẠC 12 NHÓM + NỐI CẦU CHỌN THEO CẢM XÚC** · anh giao đưa kho nhạc mới
  vào hệ, dùng được không lỗi link, gọi đúng cảm xúc nội dung.
  · **CHẨN ĐOÁN GỐC (nặng hơn việc anh giao)**: `xuong.py` chọn nhạc bằng `kb["cung_nhac"]`
    nhưng KHÔNG AI sinh trường đó — kiểm 5/5 blueprint thật đều `None`, và dict `CUNG_NHAC`
    trong xuong.py là code chết (không ai sinh `giong_tin`). ⇒ **MỌI video kênh Sóc từ trước
    tới nay đều dùng đúng MỘT cung `cang_thang` với 3 file.** Hỏng âm thầm nhiều tuần.
  · **THÊM MỚI** `chon_nhac.py` (rà tên trước: `chon_nhac`/`CUNG_12`/`map_cung` đều 0 trùng):
    dò cảm xúc bằng luật cứng, 12 nhóm, 4 tầng dự phòng (đúng nhóm → hàng xóm gần nghĩa →
    bất kỳ bài nào kho mới → kho cũ 7 cung), KHÔNG BAO GIỜ trả rỗng.
  · **SỬA** `xuong.py`: import `chon_nhac as CN` ở ĐẦU FILE (không import trong thân hàm —
    luật cứng), thay 4 dòng glob bằng `CN.chon(kb, viec)` + in log nói rõ vì sao chọn nhóm đó.
  · **HAI BẪY TỰ BẮT ĐƯỢC KHI TEST, đã sửa gốc**: ① khớp chuỗi trần → "lay" lọt trong
    "ma-LAY-sia" khiến tin đại chiến ra nhạc HÀI ⇒ đổi sang khớp ranh giới từ; ② từ khoá đặt
    theo CHỦ ĐỀ ("tuyển Việt Nam") khiến nhóm PATRIOTIC nuốt gần hết video ⇒ từ khoá phải là
    CẢM XÚC, và viết CÓ DẤU (bỏ dấu thì "khẩn"↔"khán giả" đụng nhau).
  · **CỔNG MỚI** `kiem_tram.py` tầng ⑥: kho đủ 12 nhóm · xưởng phải đi qua cầu · canh lại
    đúng hai bẫy trên · `chon()` luôn ra file thật · blueprint cung CŨ vẫn quy đúng nhóm.
  · **KHÔNG ĐỤNG**: kho `nhac/` cũ và `fetch_nhac.py` (giữ làm lưới đỡ tầng 4).
  · **ĐÃ KIỂM**: cú pháp py ✅ · import xuong.py không vòng ✅ · giải mã THẬT 88/88 file ✅ ·
    trộn `amix` giọng+nhạc đúng lệnh xưởng dùng, 12/12 nhóm ✅ · `kiem_tram.py --sau` ✅ ĐẠT HẾT.

## 11/08/2026
- **CHUÔNG "trạm đã nâng cấp"** (`/api/phien-ban` + dải đỏ trong `menu.js`) · anh báo "kho ảnh
  chờ ghép + ảnh đã ghép trong cảnh không phóng to được" · TÁI HIỆN bằng trình duyệt thật trên
  bản mới: cả 3 đường soi (🔍 kho ứng viên · 🔍 dải kho nhà · 🔍 ô cảnh) đều CHẠY TỐT, log chỉ có
  BrokenPipe vô hại của video.mp4 → kết luận: tab của anh mở từ TRƯỚC các đợt restart trạm hôm
  qua (WM + cụm vàng), JS cũ chạy với sổ mới (trường `goi_y` khung đôi) nên chết câm — LỚP LỖI
  sẽ tái phát vì anh để tab sống nhiều ngày · SỬA GỐC: server đóng dấu mốc khởi động
  `PHIEN_BAN_TRAM` + route `/api/phien-ban` (rà tên: 0 trùng); `menu.js` so mốc mỗi 60s, lệch
  thì giăng dải đỏ "bấm để tải lại" — đặt ở menu.js nên phủ CẢ 3 trang một nguồn · đụng:
  tram_tai_nguyen.py (hằng số + route đầu do_GET), menu.js (khối IIFE cuối file) · đã kiểm:
  cú pháp py+js, restart kickstart, /api/phien-ban trả mốc mới sau restart, 3 đường soi vẫn mở
  trên bản mới, `kiem_tram.py --sau` ✅ ĐẠT HẾT

## 10/08/2026
- **Lập skill `soc-kien-truc-su`** · anh giao vai kiến trúc sư kỹ thuật trưởng sau một
  đêm gãy 3 chỗ · thêm mới, không đụng code cũ · đã chạy `kiem_tram.py --sau` ✅
- **Đổi tên route** `/api/xep-kho` → `/api/xep-kho-nghia` (+ `-gan`) · route mới trùng
  tên route đóng gói kho, nuốt mất chức năng cũ · đụng: server + trang trạm · đã kiểm:
  xếp kho chạy lại được, video vào Drive hộp 03
- **Thêm cổng ②d** quét route trùng tên vào `kiem_tram.py` · chống tái phát · chỉ báo
  khi trùng trong cùng do_GET/do_POST
- **Nút Mở nói rõ đích**: "📦 Kho" (Drive) / "📂 Việc" (DATA) · rút gọn trước đó làm mất
  thông tin trạng thái
- **Dải kho: thêm 🔍 xem to + đường ghép đôi** · gộp về dùng chung `ganAnh()` thay vì
  luồng riêng · đụng: trang trạm
- **Hồ sơ bài** (`_trich_ho_so_bai`) + học lúc chốt · anh chốt: tin paste từ GPT nên
  phải đọc hiểu lúc duyệt lời · đụng: chuỗi sau duyệt lời, `_kho_nha_bai`, `_duyet`
- **Kho não**: `luat-ghep-anh.md` · `tu-dien-thuc-the.json` · `ho-so-cau-thu.json` ·
  `kien-thuc-tuyen-qg.json` — nạp vào prompt máy xếp + máy gắn nhãn
- **Gộp khối công cụ dưới mỗi cảnh** · anh: "tối ưu diện tích khu vực này" · GỐC: `.hang-o`
  khai grid 2 cột `1fr auto` mà hàng đầu có 3 phần tử → nút 🏠 rớt hàng riêng, ăn 66px thay
  vì 29px · sửa: grid → **flex** + gộp ghi chú vào cùng hàng Thẻ/Card · **làm cả cảnh phụ**
  (op-gc) theo luật chính-phụ · đụng: `tram-tai-nguyen.html` (CSS + 2 template) · ĐO: khối
  công cụ 204→172px, cảnh 224→192px, hàng 1 66→31px, danh sách 3056→3027px · đã kiểm: 6/6
  chức năng còn đủ, cảnh phụ đủ 5/5, gõ ghi chú vẫn lưu, `kiem_tram.py --sau` ✅
- **Nút Mở đổi nhãn** "📦 Kho" → "📂 Mở kho"/"📂 Mở việc" · anh bắt: nhãn cũ TRÙNG nút xếp
  kho ngay cạnh, hai nút giống hệt nhau là nhầm · đụng: `veVideo()` · đã kiểm: thanh trên
  không còn hai nút trùng nhãn
- **Vá thẻ TỶ SỐ rơi mất trường** · anh hỏi "sao không thấy đề xuất thẻ nữa" · KIỂM: đường
  dây UI+server còn nguyên (tối ưu UI KHÔNG làm gãy), nguyên nhân thật là bài CHƯA duyệt lời
  nên chuỗi sau-duyệt chưa chạy · LỘ THÊM lỗi có sẵn: `goi_y_the.py` chép cứng 5 trường thẻ
  SỐ THƯỜNG khi ghi sổ → thẻ TỶ SỐ vào sổ thành rỗng, nút hiện "◌" trống · sửa: ghi theo
  ĐÚNG LOẠI · đụng: skill soc-tai-nguyen/cong-cu/goi_y_the.py · đã kiểm: gợi lại ra thẻ tỷ số
  4-0 đủ tên đội/cờ/người ghi bàn, `kiem_tram.py --sau` ✅
- **Thêm `/api/goi-y-the`** + nút "✨ Máy gợi cả bài" trong hộp thẻ · máy gợi vốn chỉ chạy
  trong chuỗi sau duyệt lời, bài chưa duyệt hoặc sửa lời sau khi duyệt thì không có đường
  gợi lại · đặt nút TRONG hộp thẻ (nút theo ngữ cảnh, không ăn chỗ thanh trên) · rà tên
  route trước khi đặt: 0 trùng
- **#58 MÁY TỰ ĐỀ XUẤT KHUNG ĐÔI** · anh cho ba kiểu content cần hai ảnh (hai chủ thể ·
  chủ thể kèm dẫn chứng/số liệu · so sánh) · kiến trúc HAI TẦNG theo luật rẻ-trước-model-sau:
  `_do_khung_doi()` dò cấu trúc bằng CODE (0 token, bài thật dò 4/11 câu) rồi nhét vào ĐÚNG
  lượt model `_xep_kho_nghia` đang có — KHÔNG đẻ lượt model mới · `_gan_khung_doi()` lấy nửa
  dưới về qua cửa `gap_anh.lay_theo_url` như mọi đường khác, ghi `ghep_canh[câu][ô]` cờ
  `goi_y` · UI: viền cam + nhãn kiểu + nút ✓ trên nửa thứ hai, nút "⿻ gợi khung đôi" ·
  route mới `/api/goi-y-doi` (rà tên trước: 0 trùng) · XƯỞNG KHÔNG ĐỤNG (render khung đôi đã
  nghiệm thu #33/#34; trường mới `goi_y/kieu/vi_sao` xưởng không đọc nên vô hại) · đã kiểm:
  ca test ô CHÍNH + ô PHỤ đều ghép được (dat 2/2), khung đôi anh gán tay không bị đụng, dọn
  sạch ca test, `kiem_tram.py --sau` ✅
- **Vá họ lỗi `int()` trên MÃ Ô** (lộ ra khi làm #58, có sẵn từ hôm thêm ô phụ vào máy xếp) ·
  ô phụ mang mã `"3:0"`, `int()` thẳng là nổ · gãy 3 chỗ: `_kho_nha_bai` (DẢI KHO NHÀ CHẾT
  CÂM 500 mỗi khi kho-xep có ô phụ), `_xep_kho_nghia` cuối hàm (mất trắng cả lượt model),
  route gán hàng loạt (nổ khi gán ô phụ) · thêm hàm dùng chung `_ten_ma_o()` py + `tenMaO()`
  js · thêm cổng ②⑤ vào `kiem_tram.py` canh `int()` trên khoá xep — cổng này BẮT ĐƯỢC lỗi
  ngay lần chạy đầu
- **Giữ bản thô của model** (`anh/kho-xep-tho.txt`) + trường `doi_bo` · máy báo "không đề
  xuất gì" thì đây là bằng chứng duy nhất phân biệt "đã cân nhắc rồi từ chối" với "prompt
  hỏng" — nhờ nó biết bài U20 bị từ chối vì kho thiếu ảnh đội Nhật/Triều Tiên/Palestine/Iran
- **Tít video TRẮNG TRƠN — vá cửa cuối cụm tô vàng** · anh báo video lên sáng nay không còn
  chữ vàng điểm nhấn · truy: bài `2026-08-11/video-1-bai-tay-ee0cab` có `cum_to_vang: []`, và
  việc CHỌN cụm vàng vốn chỉ chạy trong chuỗi SAU DUYỆT LỜI — bài anh paste tin từ GPT rồi
  dựng thẳng thì không ai chọn, xưởng nhận rỗng và vẽ trắng IM LẶNG · sửa GỐC: tách module
  dùng chung `cum_vang.py` (chon + bao_dam), trạm gọi lúc duyệt lời, XƯỞNG GỌI LẠI ở cửa cuối
  trước khi vẽ tít + in rõ ra log · bỏ bản sao logic trong trạm (một logic một bản) · đụng:
  cum_vang.py (mới), xuong.py (import + ④ lớp phủ), tram_tai_nguyen.py (②b) · đã kiểm: chạy
  thật ra ['THAY TOÀN BỘ ĐỘI HÌNH', 'THẮNG 4-0'], render đếm được 22.092 điểm ảnh màu nhấn
  (bản cũ: 0), `kiem_tram.py --sau` ✅
- **🧽 XOÁ WATERMARK trong cửa soi của TRẠM** (ảnh ứng viên của bài) · trước đây chỉ kho chung
  xoá được, ảnh gắp về bài dính watermark là phải bỏ hoặc crop cụt mất người · DÙNG LẠI hết
  những gì đã có: cơ chế khoanh vùng của crop (kể cả luật soi gương khi ảnh đang lật), khoá
  `WM_KHOA` một-LaMa-một-lúc, và **bản gốc cất chung `anh/_goc-crop/`** nên nút "↩ Hoàn (U)"
  sẵn có lo được cả cắt lẫn xoá WM — không đẻ nút hoàn tác thứ hai · route mới `/api/wm-bai`
  + `/api/wm-bai-chot` (rà tên trước: 0 trùng), hoàn tác đi bằng `/api/crop-undo` cũ · UI:
  🧽 Xoá WM (W) · 🔁 Vá đặc · ✔ Thay · ✕ Giữ gốc, phím W/Enter/Esc · đã kiểm bằng CDP 10 mục
  + đường ống server 3 nhịp (thử → chốt → hoàn về ĐÚNG md5 gốc), `kiem_tram.py --sau` ✅
  · **CDP BẮT ĐƯỢC LỖI THẬT**: `batCrop()` không tắt chế độ WM → cả hai cùng bật, Enter rơi
  vào nhánh crop và CẮT MẤT ẢNH trong khi anh tưởng đang xoá watermark. Đã cho hai chiều
  tắt lẫn nhau + dọn cờ ở `moSoi`/`dongSoi`.
- **⏪⏩ UNDO/REDO bước chọn ảnh** (anh đặt 11/08: "ghép ảnh bị lỗi không quay lại được") ·
  chụp toàn cảnh 4 sổ (ban_do · anh_phu · ghep_canh · lat_anh) mỗi lần veCau() — điểm mọi
  đường sửa ảnh đều đi qua nên không sót đường mới thêm sau này · ⌘Z/⌘⇧Z + 2 nút cạnh thanh
  tiến độ · áp snapshot là LƯU SERVER NGAY kèm anh_phu · ĐỔI BÀI XOÁ SẠCH lịch sử (không thì
  ⌘Z áp bản đồ bài cũ đè bài mới — họ tai nạn f04608) · CDP 6 mục ✅
- **🖐 KÉO THẢ ảnh giữa cảnh** · kéo ô cảnh A thả lên cảnh B (chính/phụ đều được, kho → cảnh
  cũng được): mặc định CHUYỂN (đích bị đè, nguồn trống — một tấm một cảnh), giữ Alt = ĐỔI
  CHỖ · chip "câu N" trong kho tự đúng vì veKho() tính lại từ bản đồ · cảnh đang CLIP thì
  chặn kèm lời nhắc · thao tác đi qua veCau nên ⌘Z hoàn được cú thả · CDP 7 mục ✅
- **Nối MÁY XẾP KHO + KHUNG ĐÔI vào chuỗi sau Duyệt lời** · anh hỏi "sao bài Bukit Jalil
  (sân 90k vs 18k) không thấy đề xuất khung đôi" — vì _xep_kho_nghia chỉ chạy khi bấm 🧠 tay,
  bài đó chưa ai bấm · họ bệnh "một việc một đường chạy" lần THỨ BA trong ngày · chèn bước
  ⑤b vào _sau_duyet_loi TRƯỚC gán nháp (gán nháp vốn đọc kho-xep làm nguồn ①a) · thêm cổng
  ②⑥ vào kiem_tram.py: chuỗi sau duyệt phải gọi đủ 3 máy · chạy lại bài Bukit Jalil: máy đề
  xuất 1 khung đôi so_sanh hai sân đúng kiểu anh nói; gắn nháp bo_qua vì Ô ĐÓ ANH ĐÃ TỰ GHÉP
  TAY — tay người thắng máy, đúng thiết kế · kiem_tram --sau ✅
- **Crop/Xoá WM mọi nơi = LƯU LÀ THAY LUÔN** (anh đổi 11/08: "lưu/enter thì tự động thay
  luôn ảnh cũ") · TRẠM CHÍNH + TRANG KHO: LaMa xong tự gọi chốt luôn, bỏ bước ✔ Thay thủ
  công — an toàn vì bản gốc vẫn cất (_goc-crop / .goc-wm), ↩ Hoàn lúc nào cũng được; 🔁 Vá
  đặc chạy tiếp trên bản đã thay (vùng nhớ wmVungCuoi) · TRANG CHỌN: thêm 🧽 ghi VÙNG XOÁ
  WM (phím W) như ✂ crop — ảnh còn ở web, lúc LẤY VỀ server tự vá LaMa rồi mới nhập bài;
  vùng quy đổi toạ độ khi ảnh đồng thời bị crop, vùng nằm ngoài phần giữ thì bỏ (watermark
  đã bị cắt) · route lay-chon nhận thêm `wms` · đã kiểm: md5 đổi + gốc cất đúng chỗ + hoàn
  về đúng gốc, CDP 7 mục, kiem_tram --sau ✅
- **📥📦 Chip nhắc luồng nhập kho** (vá 2 lỗ hổng im lặng anh duyệt) · route `/api/nhac-nho`:
  đếm ảnh cho_nhan trong sổ chủ thể + quét bài video.mp4 >24h chưa cờ `da_xep_kho` (chỉ bài
  từ 11/08 — bài cũ không cờ, nhắc là oan) · buoc3_xepkho.py ghi cờ khi xếp xong · trạm
  chính hiện chip cạnh nút undo, tự tươi 2 phút/lần
- **Bấm đề xuất ≈N thì cột trái nhảy về cảnh 1** (anh bắt 11/08 chiều) · gốc: `kbLay` gán
  theo `o.dataset.cau` nhưng không cập nhật `dangChon`, `veCau()` cuộn theo cảnh đang chọn
  cũ · vá 1 dòng: gán ô chính xong thì `dangChon = cau` — focus + viền vàng về đúng cảnh
  vừa gán · đường ô phụ (dangPhu) và đường xem-to-rồi-gán vốn đã đúng, không đụng · CDP:
  bấm tấm ≈3 → dangChon=2, viền cảnh 3 ✅ · kiem_tram --sau ✅
- **Ảnh KHO NHÀ xem to giờ ✂ cắt + 🧽 xoá WM được** (anh bắt 11/08: "có nút mà bấm không
  phản ứng") · gốc: cửa soi phục vụ HAI loại ảnh — ảnh BÀI (dl.anh[soiK]) và ảnh KHO
  (kbXemTo, soiK=null) — mà catCrop/xoaWmThuBai/batCrop/batWm đều chặn im `soiK == null` ·
  vá: rẽ nhánh theo `_kbToO`, ảnh kho đi route sẵn của trang kho (kho-nha-crop · xoa-wm +
  tự chốt · *-hoan theo thao tác cuối `_kbSuaCuoi`), LƯU ĐÈ ảnh kho đúng luật "lưu là thay",
  gốc vẫn cất thùng rác · kbXemTo gỡ class latx (ảnh kho luôn chiều gốc, không thì vùng
  khoanh bị soi gương oan) · LỘ THÊM 2 lỗi có sẵn nhờ test chuỗi: ① kbXemTo ghi textContent
  đè nút Gán làm MẤT span #soiCau → mở ảnh bài kế là moSoi nổ null (vá: moSoi tự dựng lại
  cả nút); ② Enter khi soi ảnh kho nổ dl.anh[null].duong (vá guard) · CDP 12 mục ✅ ·
  kiem_tram --sau ✅ · ảnh kho test đã hoàn nguyên đúng md5
- **Dải kho ứng viên thành 2 TAB 🖼 Ảnh / 🎬 Video** (anh đặt 11/08: "không thấy đề xuất
  video có sẵn trong kho") · route mới `/api/kho-video-bai` (rà tên: 0 trùng) chấm đoạn
  video CÙNG THƯỚC với ảnh — q tay đi _diem_khop nghiêm, không q đi _diem_mem theo chữ bài
  (tiêu đề + từ khoá + hồ sơ) + phạt đội lạ ×0.4 y như ảnh · ô tìm DÙNG CHUNG hai tab
  (veKhoBai rẽ nhánh theo _kbTab nên #kbTim khỏi sửa) · bấm đoạn = lấy về dải 🎬 CLIP của
  bài qua route kho-video-lay SẴN CÓ (ffmpeg cắt + khung né logo tự theo) rồi cắt & gán
  cảnh bằng đồ nghề clip đang dùng — KHÔNG mở luồng gán song song (bài học kbLay) · nút
  chỉ-có-nghĩa-cho-ảnh (🧠 xếp · ⚡ gán hết · thêm ↓ · ⓘ) ẩn ở tab video · 🔍 xem thử đoạn
  mở tab mới · đã kiểm CDP 8 mục: đổi tab xuôi ngược, tìm chung, lấy đoạn thật về clip/tay,
  thẻ ▶ hiện trên dải clip, tab ảnh khôi phục nguyên; clip test đã dọn · kiem_tram --sau ✅
- **Tab 🎬: CẮT TẠI CHỖ từ video gốc** (anh đổi 11/08: "đoạn cắt sẵn chỉ 4s, không lấy
  được đoạn ưng ý") · bấm ô đoạn giờ KHÔNG lấy đoạn cắt sẵn nữa mà HARDLINK video GỐC kho
  về clip/tay của bài (cùng volume DATA — 0 byte thêm, os.link, fallback copy) rồi mở cửa
  cắt quen `moClip` với thanh cắt ĐẶT SẴN quanh đoạn máy đề xuất — nới rộng tuỳ ý, gán
  chính/phụ, ✂ cắt lưu kho nhiều đoạn thành thẻ ▶ kho ứng viên · route mới
  `/api/kho-video-goc` · KHÔNG viết modal mới — dùng nguyên bộ đồ nghề clip (luật dùng lại)
- **KIỂM TRÙNG KHO VIDEO (anh hỏi "sao lắm video thế")** · đáp: 114 đoạn không phải 114
  video — là 8 FILE gốc tách cảnh · phát hiện v01.mp4 ≡ v09.mp4 TRÙNG HỆT TỪNG BYTE (md5 +
  size khớp, một video highlight tải 2 lần) → dọn v09 + 25 đoạn + 25 thumb vào thùng rác
  (hoàn được), sổ còn 89 đoạn · 12 đoạn QUẢNG CÁO (Samsung, đăng-ký-kênh) lọt đề xuất →
  route kho-video-bai lọc đoạn có mô tả MỞ ĐẦU "Quảng cáo/Khung quảng cáo" (chỉ mở đầu —
  cảnh thật có biển quảng cáo sau lưng không bị lọc oan) → đề xuất còn 87 đoạn sạch ·
  VIỆC CHỜ đề xuất: cổng chống trùng md5 ngay khi TẢI video vào kho (nhap_kho_video) để
  bệnh không tái · CDP 8 mục ✅ · kiem_tram --sau ✅
- **Cổng MD5 chống nhập trùng kho video** (anh gật 11/08 sau vụ v01≡v09) · đặt tại CỬA
  NHẬP DUY NHẤT `_nhap_tep_video` — mọi đường (tải link · hồi tố bài cũ · nhập tay) đều
  qua · hai lớp: lớp rẻ cũ (nguon_tep/co_goc) giữ nguyên, lớp mới md5 NỘI DUNG so với mọi
  file kho, đặt TRƯỚC khâu tách cảnh + nhãn mắt máy (đắt) · md5 ghi vào sổ (md5_kho),
  bản cũ tính bù một lần — đã bù đủ 89/89 dòng · test thật: nhập lại chính v09 từ thùng
  rác → "BỎ QUA — TRÙNG TỪNG BYTE với v01.mp4", kho không đẻ file · thêm bẫy ②⑦ vào
  kiem_tram canh cổng không bị gỡ · kiem_tram --sau ✅
- **Cửa cắt video: TUA LÀ CHỌN LUÔN** (anh đặt 11/08: "chọn thanh timeline ở đâu thì lấy
  luôn mốc đó xuống ô Từ, khỏi tự tính gõ lại — Đến tự tính theo") · listener `seeked`
  trên #mcVideo: tua tay → Từ = mốc tua, Đến = Từ + ĐỘ DÀI ĐANG CHỌN (mcSpan — nhớ qua
  capNhatMc, thay luật +4s cứng 07/08: tua giờ là DỊCH cả cửa sổ cắt) · cú seek do nút
  "▶ Xem đoạn" tự đặt mang cờ mcSeekMay, bỏ qua — không thì bấm xem thử là mốc bị đè ·
  sửa MỘT chỗ (modal mClip là cửa cắt duy nhất) phủ mọi nguồn: clip bài, video kho, đoạn ·
  CDP 4 mục ✅ (tua nhận mốc · span giữ khi đổi độ dài · Xem đoạn không đè) · kiem_tram ✅
- **Trang kho: GỢI Ý NHÃN ĐÃ CÓ, khớp KHÔNG DẤU** (anh đặt 11/08) · route mới
  `/api/kho-nhan-goiy` gom nhãn + chủ thể của CẢ sổ ảnh lẫn sổ video kèm tần suất (3.308
  nhãn duy nhất), cache theo mtime hai sổ, trả MỘT lần — client lọc không dấu tức thì ·
  hộp sửa sâu (#suaHop dùng CHUNG ảnh + video): gõ ở ô CHỦ THỂ hay ô NHÃN đều ra dropdown,
  "dinh bac" → "Nguyễn Đình Bắc", xếp khớp-đầu-chuỗi > tần suất, ↑↓ + Enter hoặc bấm chuột,
  nhãn đã đeo trên tấm không gợi lại · Enter chữ TỰ DO vẫn thêm nhãn mới như cũ (goiVt<0
  thì nhường handler cũ; handler gợi ý bắt capture để ưu tiên khi đang chọn) · SỬA KÈM:
  chip 📥 chờ nhãn ở trạm chính link nhầm /kho-nha (404) → /kho-nha-duyet · CDP 8 mục ✅
  (cả tab VIDEO cùng hộp sửa) · kiem_tram --sau ✅
- **Trang kho: Enter nhãn = LƯU LUÔN + gợi ý cho GÁN LOẠT + XOÁ MỘT khi zoom** (3 yêu cầu
  11/08 chiều) · shLuuNgam(): thêm/xoá chip nhãn là ghi sổ ngay, hộp vẫn mở gõ tiếp; chủ
  thể + mô tả vẫn chốt bằng 💾 (gõ dở mà tự lưu = lưu rác) · gợi ý nhãn mở rộng cho ô
  thanh LOẠT (#ctLoatGoi treo absolute, không đẩy thanh) — một bộ veGoi/chonGoi rẽ theo
  `cho` · cửa soi thêm 🗑 Xoá + phím Delete/Backspace (guard không bắt khi đang gõ input),
  đi đúng route xoá của loạt, ảnh có hoàn tác, video theo route video · LỘ LỖI CÓ SẴN nhờ
  test: route kho-nha-sua CẮT nhãn [:8] lúc nhận nhưng giữ [:12] sau khử trùng — tấm sẵn
  8 nhãn máy thì nhãn anh VỪA THÊM rụng IM LẶNG; vá [:12] nhất quán + server trả bộ nhãn
  thật khi sửa 1 tấm, client đồng bộ chip + kịch trần thì NÓI RA · CDP ✅ (tấm 8 nhãn —
  chính ca từng trượt) · kiem_tram --sau ✅
- **KHO VIDEO: bỏ tách cảnh tự động — 1 video = 1 dòng, nhãn GỐC/CẮT** (anh bắt 11/08:
  "a chỉ cắt 1-2 đoạn 4-5s mà kho thấy quá nhiều video cắt") · CHẨN: không phải lỗi luồng
  cắt — `_tach_canh` scene-detect băm MỌI video lúc nhập kho thành 13–26 dòng (thiết kế cũ
  #40), 7 file thành 80 dòng · SỬA GỐC `_nhap_tep_video`: bỏ tách cảnh, mỗi video vào kho
  = MỘT dòng có `loai` ("goc" tải link · "cat" hồi tố clip tay đã cắt), nhãn mắt máy vẫn
  giàu (3 khung đầu-giữa-cuối gộp về một dòng; video <12s chỉ 1 khung) · DỌN SỔ một lần:
  80 → 10 dòng (5 gốc + 5 đoạn cắt/đã-lên-hình), nhãn gộp top-12 theo tần suất, sổ cũ
  backup thùng rác · UI badge cả hai trang: 🎞 GỐC xanh dương (phút) vs ✂ cắt xanh lá
  (giây) · bấm ô GỐC vẫn mở cửa cắt-tại-chỗ · bẫy ②⑧ vào kiem_tram canh không ai bật lại
  tách cảnh · test: nhập video mới ra ĐÚNG 1 dòng, nhập lại bị md5 chặn, badge hiện đúng
  cả 2 trang · kiem_tram --sau ✅
- **Tách rõ CHỦ THỂ vs NHÃN ở thanh loạt + thêm GẮN NHÃN HÀNG LOẠT** (anh hỏi 11/08:
  "tưởng nút Gán cả loạt là gắn nhãn") · chữ "👤 Gán cả loạt" mơ hồ — nó đặt CHỦ THỂ (một
  giá trị, đè cũ), còn thêm NHÃN (nhiều giá trị, cộng dồn) thì CHƯA CÓ · đổi nhãn nút thành
  "👤 Đặt CHỦ THỂ" + thêm "🏷 Thêm NHÃN", dùng CHUNG một ô nhập (đã có gợi ý không dấu) ·
  server: cả kho-nha-sua lẫn kho-video-sua nhận trường mới `nhan_them` cộng dồn — KHÔNG
  dùng `nhan` vì trường đó ghi đè cả bộ, gắn loạt là xoá sạch nhãn riêng từng tấm; route
  video bổ sung luôn khâu khử nhãn trùng (bỏ dấu) vốn chỉ kho ảnh có · CDP ✅ (2 tấm 8+7
  nhãn: nhãn mới vào đủ, nhãn cũ nguyên vẹn, ô tự trống) · kiem_tram --sau ✅
- **Vá NameError 'cung' làm báo "dựng hỏng" oan** (anh báo 12/08 00:40, bài
  2026-08-11/video-5-bai-tay-5b70c3) · `xuong.py:1060` in kết quả bằng biến `cung` — tên
  CŨ, sau đổi thành `nhom_nhac` (dòng 970) mà quên dòng in · lỗi nằm SAU khi ffmpeg xong:
  video 59,7s/15,2MB đã nằm trên đĩa, chỉ dòng in cuối nổ → anh nhận báo hỏng cho một
  video LÀNH · sửa `cung` → `nhom_nhac`, dựng lại bài đó chạy trọn ✅ · lỗi có từ 07/08
  (bản .bak_clip đã dính) — sống sót 5 ngày vì `ast.parse` không bắt được tên sai
- **Cổng ① mọc thêm răng: soi BIẾN CHƯA KHAI** · `_bien_chua_khai()` trong kiem_tram —
  quét theo phạm vi hàm, gom tên từ tham số/gán/import/except/global/lambda + cả cây hàm
  con, CHỈ soi hàm cấp ngoài cùng (hàm lồng dùng biến hàm cha là hợp lệ) · vặn hai vòng
  cho hết BÁO GIẢ: vòng 1 báo giả 4 mục (closure), vòng 2 báo giả 2 mục (tham số lambda)
  — cổng báo giả nhiều lần là cổng bị bỏ qua · thử ngược: cắm lại đúng lỗi 'cung' → bắt;
  cắm biến lạ → bắt · toàn bộ 11 file .py của hệ giờ sạch · kiem_tram --sau ✅
- **Nhạc nền: chống LẶP BÀI giữa các video** (anh báo 12/08 vừa tải kho nhạc mới) · KIỂM:
  bộ chọn-theo-cảm-xúc + ngẫu nhiên ĐÃ chạy đúng — kho 12 nhóm/88 bài đủ, thử 14 bài thật
  ra 6 nhóm khác nhau, đoán cảm xúc chuẩn ("cái dớp đáng sợ"→TENSION, "tin vui"→COMEBACK,
  "siêu sân 60%"→ANALYSIS) · NHƯNG đo 30 video gần nhất thấy 10/08 có 2 video ăn CÙNG một
  bài TENSION — ngẫu nhiên thuần vẫn đụng, kênh 10 video/ngày là người xem nghe lại ngay ·
  thêm sổ `nhac-da-dung.jsonl` cạnh kho + `_chon_it_lap()`: ① bài đã dựng rồi thì TRẢ LẠI
  đúng nhạc cũ (dựng lại sửa một cảnh mà nhạc đổi là hỏng cảm giác đã duyệt) ② chưa dựng
  thì ưu tiên bài CHƯA DÙNG, hết mới lấy trong nửa lâu-chưa-dùng-nhất · cùng họ luật "ảnh
  ít dùng gần đây" của kho ảnh · đo lại: 20 video → 20 bài KHÁC NHAU, lặp 0 (trước 3 video
  cùng nhóm chung 1 bài); dựng lại bài cũ giữ đúng nhạc ✅ · dựng thật ✅ · kiem_tram --sau ✅
- **Nút Kho: 31–106 giây → 0,2 giây** (anh đặt 12/08: "bấm Kho chậm, trong khi a xem video
  1 phút thì hệ thống ngồi chơi") · ĐO TỪNG KHÂU trước khi sửa: pgrep 0,01s · ffprobe 0,35s ·
  chép video+giọng 0,02s · ghi 3 tệp text ~0,01s · ffprobe lại 0,3s · kiem_hop 0,05s → cơ
  khí CHỈ 0,8s; thủ phạm DUY NHẤT là sinh SEO gọi haiku 30–105s (5/25 bài gần nhất thiếu
  SEO nên phải gọi tại chỗ) · SEO chỉ cần TIÊU ĐỀ + LỜI BÌNH — có đủ ngay lúc dựng xong →
  xưởng bắn `buoc3_xepkho.py --seo <việc>` chạy NỀN detach cuối hàm dung() · cờ `.dang-seo`
  chống gọi model hai lần: bấm Kho sớm thì CHỜ bản nền thay vì gọi lại (hai lượt cùng ghi
  kich-ban.json là đè nhau) · đo thật: dựng xong → SEO nền xong sau 105s (anh xem video là
  vừa) → bấm Kho **0,2 giây** · kiem_tram --sau ✅
- **SEO chạy SONG SONG với dựng — nút Kho còn 0 giây** (anh chốt 12/08: "giảm tối đa thời
  gian chờ ở các bước, rút ngắn time 1 video") · chuyển lệnh bắn SEO từ CUỐI lên ĐẦU hàm
  `dung()`: SEO chỉ cần tít + lời bình, có sẵn ngay dòng đọc kb · dựng ăn CPU (ffmpeg), SEO
  chờ mạng → chạy cùng không làm dựng chậm · đo thật: dựng 51s, SEO xong ở giây 55, bấm Kho
  **0 giây** (trước: 31–106 giây)
- **XUNG ĐỘT GHI phát hiện TRƯỚC khi gãy** — soi vùng ảnh hưởng thấy `cum_vang` cũng ghi
  `kich-ban.json` ở cuối khâu dựng, mà SEO song song cũng ghi tệp đó; kiểu ghi cũ (đọc cả
  tệp → ghi đè cả tệp) làm bên ghi SAU xoá sạch việc bên ghi TRƯỚC, im lặng không lỗi ·
  dựng module `kich_ban.py` — cửa GHI DUY NHẤT `ghi_gop()`: khoá fcntl → đọc lại bản mới
  nhất trên đĩa → gộp phần mình → `os.replace` nguyên khối · chuyển 3 đường ghi sang cửa
  này (cum_vang · SEO · cờ da_xep_kho) · test 60 lượt ghi ĐAN NHAU từ 2 luồng: giữ đủ mọi
  trường, không ai đè ai ✅ · chạy thật: cụm tô vàng + 23 thẻ SEO CÙNG CÒN sau khi song song
- **Luật an toàn kèm theo**: `_luu_loi` gỡ `tu_khoa`/`binh_luan_ghim`/`hashtag_seo` khi
  TIÊU ĐỀ đổi (lần dựng sau sinh lại); sửa LỜI BÌNH thì giữ nguyên SEO — theo đúng lời anh
  "sau khi bấm dựng cùng lắm chỉ sửa nội dung, SEO thường giữ nguyên" · kiem_tram --sau ✅
- **Chip "📦 chưa xếp kho" BÁO OAN 3 bài đã lên Drive** (anh bắt 12/08) · gốc: chip tin vào
  cờ `da_xep_kho` mà cờ đó MỚI thêm 12/08 — ba bài xếp kho trước đó (hộp 01/02/03 ngày
  11/08 nằm sẵn trên Drive) đương nhiên không có cờ; mốc lọc lại để "từ 2026-08-11" nên
  bắt oan đúng ngày cờ ra đời · sửa: đối chiếu SỔ KHO THÀNH PHẨM thật (`SO-VIDEO.jsonl`,
  so tiêu đề bỏ dấu) — có trong sổ thì gắn cờ HỒI TỐ luôn rồi bỏ qua, khỏi soi lại lần
  sau · chip giờ báo 0 bài, ba bài đã có cờ "(hồi tố từ sổ kho)" · kiem_tram --sau ✅
- **Đang chọn cảnh 4 mà ảnh cứ vào cảnh 11** (anh bắt 12/08) · CHẨN bằng CDP trên đúng bài
  anh mở: chọn cảnh không lỗi (bấm ô cảnh 4 → dangChon=3 ✅); lỗi ở khâu GÁN của dải kho
  nhà — `kbLay` lấy cảnh đích từ BADGE ≈N/🧠N của tấm (`o.dataset.cau`), chỉ theo dangChon
  khi anh tìm tay · thiết kế cũ hợp lúc LƯỚT NHANH chưa chọn cảnh nào, nhưng khi anh đã
  chủ động bấm chọn một cảnh thì ý anh phải thắng · sửa: `cau = dangPhu ? dangPhu.cau :
  dangChon` — badge chỉ còn để BÁO ("máy vốn gợi tấm này cho cảnh N") · giữ đường tắt cho
  người muốn theo máy: bấm THẲNG vào badge → nhảy tới cảnh đó rồi gán (hành vi có chủ
  đích, khác bấm vào ảnh) · CDP: bấm tấm badge-cảnh-1 lúc đang chọn cảnh 4 → vào cảnh 4 ✅,
  con trỏ ở lại cảnh 4 ✅, bấm badge → vào cảnh 1 ✅ · ca test đã ⌘Z hoàn · kiem_tram ✅
- **Chuỗi sau Duyệt lời: tìm lại vòng 2 + BÁO khi xong** (anh đặt 12/08: "bấm duyệt lời là
  tìm auto hết, cảnh nào chưa được phải tự tìm lại, xong thì thông báo") · KIỂM trước: chuỗi
  ĐÃ tìm sẵn cả bài từ 06/08 (bài 13/08 có đủ 12/12 câu ứng viên) — Chrome anh thấy lúc bấm
  Trang chọn là nó TÌM BÙ câu còn trắng, không phải "chưa tìm gì" · thêm ⑤a: câu nào trắng
  tay thì tự tìm lại bằng từ khoá RÚT GỌN 4 từ đầu (từ khoá dài hay ra 0 kết quả — Google
  càng nhiều chữ càng siết) · thêm báo Telegram + thông báo Mac khi chuỗi xong, kèm số cảnh
  đã có ảnh / còn trống
- **ĐỀ XUẤT ẢNH SÁT HƠN: chấm theo ĐỘ HIẾM của từ** (anh hỏi "nhãn/chủ thể đề xuất chưa sát
  nội dung, cải thiện được không") · CHẨN kho 873 ảnh: nhãn KHÔNG nghèo (86% đủ bộ chủ thể +
  ≥5 nhãn + mô tả ≥60 ký tự, 95% có chủ thể, 80% có nhãn giải) — bệnh nằm ở BỘ CHẤM: mọi từ
  trọng số như nhau, mà "2026" đeo 798/873 tấm, "asean cup 2026" 369 tấm → câu nào cũng khớp
  mấy nhãn đó, cả kho "hợp bài" ngang nhau, tấm đúng người chìm giữa 800 tấm chung chung ·
  thêm `_do_hiem()` IDF log(N/c) chuẩn hoá + cache theo mtime sổ (0 token, chạy tức thì):
  2026→0,10 · đình bắc→0,32 · popov→1,00 · thử công thức căn bậc hai trước, đo ra chênh lệch
  quá nhạt (2026 vẫn 0,51) nên đổi sang log · ĐO trên bài thật: TOP-10 mỗi câu trúng tên
  riêng 95% → **100%**; câu 4 "HLV Popov" trước xếp sau Kim Sang-sik, nay lên đầu ·
  kiem_tram --sau ✅
- **CHẨN chất lượng kho ảnh + vá từ điển đội** (anh nêu 3 bệnh 12/08: nhãn sai, mô tả sai,
  ảnh đội lạ lọt) · ĐO bằng mắt máy trên mẫu 20 tấm: chủ thể SAI **0/20** (9 đúng, 11 haiku
  không dám chắc), mô tả SAI HẲN **2/20 (10%)** — nhãn kho không tệ như cảm giác · cơ chế
  lọc đội lạ ĐANG chạy đúng (bài VN–Malaysia: 0 ảnh Thái lọt) · LỖ HỔNG THẬT: từ điển thiếu
  CÁCH GỌI TẮT — "tuyển Thái", "người Thái", "cầu thủ Thái", "samurai xanh", "sao vàng" đều
  KHÔNG bắt được, mà mắt máy viết nhãn theo đúng lối nói ấy · vá 48 cách gọi vào 12 đội
  TRONG TỪ ĐIỂN DRIVE (bảng `_DOI_TUYEN` trong code chỉ là dự phòng — sửa code không ăn,
  suýt tưởng vá hỏng) · đo lại 5 bài gần nhất: **0/150 tấm lọt đội lạ** · kiem_tram --sau ✅
- **Gửi model BẢN THU NHỎ 1000px — giảm ~73% token ảnh** (anh chốt 13/08 khi hạn mức tuần
  còn 13%) · ĐO trước: ảnh kho 2000×1333 = 3.555 token/tấm (token ảnh ≈ w×h/750), cả kho 892
  ảnh = 3,2 triệu; ảnh bài 1920px = 3.276/tấm, mắt máy ~18 tấm/bài = 59k, 10 video/ngày =
  0,59 triệu · CHỨNG MINH không mất chất lượng: chạy lại opus + sonnet trên bản 1000px của
  đúng 9 ảnh đã đo — vẫn đọc đúng SỐ ÁO (7), vẫn nhận ra Kim Sang-sik, vẫn tả đúng màu áo +
  logo · thêm `gap_anh.ban_nho()` (cache `_nho/` theo mtime nên ảnh crop/xoá-WM tự sinh lại;
  ảnh vốn nhỏ thì trả thẳng, không đẻ tệp) · nối vào 3 cửa gửi ảnh: mắt máy kiểm nháp ·
  gắn nhãn khi nhập kho · soát lại kho (loc_anh đã ghép lưới nhỏ, nhap_kho_video đã dùng
  thumb 640 — không đụng) · đo thật qua trạm: mắt máy kiểm đủ cảnh, gỡ 1 tấm lệch, token
  giảm 32–73% tuỳ cỡ ảnh gốc
- **Vá 3 chỗ gọi `claude` TÊN TRẦN** · trạm có khai PATH trong plist nên vẫn chạy — nhưng
  script chạy ngoài trạm (cron, launchd một-lần) thì FileNotFoundError CÂM · đổi sang dò
  đường đầy đủ `~/.local/bin/claude` như cum_vang: buoc1_viet · viet_loi_binh ·
  tram_tai_nguyen (mắt máy) · kiem_tram --sau ✅
- **HOÃN quét lại toàn kho tới sau reset thứ Sáu** — đo ra quét cả kho ≈ 1,1 triệu token,
  đúng bằng MỘT NGÀY sản xuất 10 video; hạn mức tuần của anh còn 13%, chạy bây giờ là mai
  không dựng nổi video
- **Ô phụ BIẾN MẤT khỏi trạm sau khi render** (anh bắt 13/08: "cảnh 9 ghi +2 phụ mà không
  thấy ô nào") · ĐO trên bài thật: **6/9 câu** mất ô phụ, không riêng câu 9 · dữ liệu CÒN
  NGUYÊN trong sổ (`anh_phu['8'] = [t14.jpg, t21.jpg]`) — lỗi thuần HIỂN THỊ · gốc: nhịp
  được tính LẠI sau khi có giọng thật, `so_phan` giảm đi thì ảnh phụ gán trước đó dư ra;
  `veCau` chỉ vẽ `soPhan-1` ô nên ảnh dư biến mất, anh không xoá cũng không sửa được ·
  cảnh dùng CLIP rơi hết vào đây (so_phan=1 vì anh tự quyết độ dài đoạn) · ĐÃ KIỂM xưởng:
  cũng chỉ dựng `soPhan` khung → **VIDEO KHÔNG SAI**, chỉ là ảnh nằm im trong sổ
- **Gốc sâu hơn: tính năng CŨ bị vô hiệu bởi một dòng** · toàn bộ xử lý "Ô DƯ" (class `du`,
  viền xám, mờ 50%, tooltip giải thích, chữ "Ô DƯ — nhịp hiện tại không dùng") ĐÃ LÀM ĐỦ từ
  việc #19, nhưng có lần refactor sau đó đặt cứng `const du = false;` khiến nhánh ấy không
  bao giờ chạy · sửa: `du = j >= soPhan-1` + `soO = max(soPhan-1, số ảnh phụ thật)` · CDP:
  câu 9 hiện lại 9b·9c (đánh dấu DƯ), cả bài 11 ô phụ trong đó 7 ô dư, ảnh hiện đủ ·
  kiem_tram --sau ✅
- **Cảnh CLIP nuốt mất ảnh phụ — BỎ hẳn khái niệm "ô dư"** (anh nói rõ 13/08: "cảnh 9 có
  1 chính + 2 phụ nhưng 2 cảnh phụ không lên hình; không cần ô dư làm gì; thừa ảnh thì để
  kho ứng viên") · GỐC THẬT: `nhip_canh` ép `so_phan = 1 if la_clip` và `xuong` `continue`
  ngay khi gặp cảnh clip → cảnh 9 dài 9,2s dùng clip 4s bị dựng thành MỘT khung, hai ảnh
  phụ bỏ thẳng · em hôm trước hiểu sai ý anh, đi hiện "ô dư" thay vì sửa gốc — nay bỏ hẳn
- **Ba tầng sửa đồng bộ** · `nhip_canh.chia_nhip(giay, la_clip, so_phu)` nhận thêm SỐ ẢNH
  PHỤ = ý người: gán mấy phụ thì mở bấy nhiêu khung, chặn trên bằng `so_o_toi_da()` (mỗi
  khung ≥2,5s) · `xuong` truyền so_phu + cảnh clip có phụ thì đi tiếp vào khâu chia, khung
  ĐẦU chính là đoạn clip (kèm khung né logo) · trạm truyền so_phu vào cùng hàm nên hai bên
  khớp từng ô; UI bỏ ô dư; route `gan-phu` từ chối ô vượt trần kèm lời nhắc "ảnh giữ trong
  kho, gán cho cảnh khác"
- **Đo bài thật**: trước — 6/9 câu có ảnh phụ không lên hình; sau — 9/9 câu khớp (câu 9:
  9,2s → 3 khung, đúng 1 chính + 2 phụ) · dựng lại: 15 cảnh con, 60,2s, chạy trọn ·
  kiem_tram --sau ✅

## 13/08 — cảnh 4b/4c không lên hình: xưởng tra CÂU-CỦA-CẢNH ba lần, hai lần trên mốc đã dịch
- **Sửa gì**: `xuong.py` chốt `mo_cau_goc` MỘT lần ngay sau khi cắt cảnh (mốc gốc); ba chỗ tra lại (`xep` ảnh chính · `canh_mo` khối clip ③d · `mo_cau` khối tách ③đ) nay đều ĐỌC nguồn đó.
- **Vì sao**: khối ③d cho cảnh clip mượn giây của hàng xóm bằng cách DỊCH mốc mở của cảnh kề (`canh[idx+1][0] += sau`). `mo_cau` tính SAU đó nên cảnh kề rơi tụt về câu trước: cảnh 4 lấy ảnh phụ của câu 3, cảnh 6 lấy của câu 5. Câu 3 chỉ có 1 phụ nên cảnh 4 còn báo 'thiếu 1 ảnh phụ'; cảnh 6 thì SAI IM LẶNG (câu 5 cũng có đúng 1 phụ nên đủ số, chỉ sai ảnh).
- **Đụng những đâu**: chỉ `xuong.py` (grep cả hệ: `mo_cau`/`canh_mo` không nơi nào khác dùng). `cau_goc` của khung đôi vốn đã đúng — nó là bản vá cục bộ 10/08 cho cùng họ bệnh này.
- **Đã kiểm**: `kiem_tram.py --sau` ĐẠT HẾT (thêm cổng ②⑨). Dựng lại bài `2026-08-13/video-2-bai-tay-14381f`: hết cảnh báo thiếu; trích khung so histogram — khung 2 = n04 (45% vs 35%), khung 3 = n06 (51% vs 46%) ở cả hai mốc đo → 4b/4c ĐÃ lên hình.

## 14/08 — kho ảnh: mỗi tấm nhớ MẮT NÀO đã nhìn + cờ duyệt tay bị gán quá tay
- **Sửa gì**: `nhap_kho_chu_the.py` thêm `BAC_MODEL` (haiku 1 · sonnet 2 · opus 3), mỗi lượt soát ghi `soat_model` / `soat_luc` / `soat_chac`; vòng soát chỉ đụng tấm chưa ai nhìn hoặc mới qua mắt yếu hơn. Thêm cờ `--chua-chac` (tầng opus chỉ dặm tấm sonnet tự nhận không chắc), `--lai` (ép soát lại), và lệnh `--tinh-hinh` xem kho đã soát tới đâu bằng CODE THUẦN, không tốn token.
- **Bắt được lỗi cũ**: route `/api/kho-nha-sua` nhận cả `tep_ds` (gắn nhãn hàng loạt) mà vẫn đóng dấu `nguoi_sua=True` → 746/986 tấm (76% kho) thoát vòng soát vĩnh viễn, trong đó có tấm nhãn ghi 'hlv calisto' còn mô tả lại là 'HLV Kim Sang-sik được cầu thủ ôm chúc mừng'. Tách khái niệm: `nguoi_sua` = có chạm vào, `nguoi_duyet` = thật sự duyệt nội dung (chỉ bật khi sửa MỘT tấm). Vòng soát nay miễn theo `nguoi_duyet`.
- **Đường lùi**: trước khi mắt máy đè nhãn, lưu bản cũ vào `nhan_truoc_soat` (nhãn + mô tả + chủ thể).
- **Đụng những đâu**: `nhap_kho_chu_the.py` (vòng soát, không đụng `nhap()` và `bo_nhan()`), `tram/tram_tai_nguyen.py` route `/api/kho-nha-sua` (thêm dòng, không đổi hành vi cũ).
- **Đã kiểm**: `kiem_tram.py --sau` ĐẠT HẾT. `--tinh-hinh` chạy đúng: 986 tấm, 780 chưa ai nhìn, 206 mắt cũ không rõ.

## 14/08 (chiều) — đồng hồ sản xuất + đoạn cắt vừa ô
- **Mới `dong_ho.py`**: 8 mốc (mo_viec · duyet_loi · chuoi_xong · duyet_anh · dung_bat_dau · dung_xong · kho_bat_dau · kho_xong), sổ nằm trong `kich-ban.json` khoá `dong_ho`, ghi qua `KB.ghi_gop` nên nhiều tiến trình chấm cùng lúc không giẫm nhau. Tên chặng đặt theo KHOẢNG (việc đã làm) chứ không theo mốc đích — nhìn bảng là hiểu.
- **Trạm**: route `/api/dong-ho`, ô góc trái dưới đếm từng giây, bấm xoè bảng từng chặng. Server giữ mốc, trình duyệt đếm — hỏi lại 15 giây/lần.
- **Gói đăng**: thêm mục 【7】 THỜI GIAN SẢN XUẤT; tên file đổi `goi-dang.txt` → `goi-dang_<slug tiêu đề>.txt` (anh mở nhiều bài cùng lúc khỏi lẫn tab).
- **Đoạn cắt VỪA Ô**: ô Đến đề xuất = Từ + độ dài ô thật (trước là 4 giây cứng), nhãn '✓ vừa ô' / '· ô cần N s', nút '⇥ vừa ô'. ĐỀ XUẤT không ép — anh vẫn kéo tự do. Ý nghĩa sâu: cảnh lái clip thì không ai phải nhường giây cho ai, mà phép nhường giây chính là gốc bệnh 'cảnh 4b/4c không lên hình' vá sáng nay.
- **Đã kiểm**: `kiem_tram.py --sau` ĐẠT HẾT (thêm cổng ②⑩ canh đủ 8 mốc + mục thời gian trong gói đăng). CDP: ô đồng hồ hiện 47:00 với mốc thử, bấm xoè được, không lỗi JS; oGiay(3)=3,1s đúng bằng 9,4s/3 ô.
- **CÒN NỢ**: xưởng vẫn cho clip mượn giây hàng xóm khi đoạn lệch — nên đổi thành cắt đuôi trong chính cảnh đó. Tách riêng vì đụng đúng khối vừa vá.

## 14/08 (trưa) — nút 'Mở kho' tụt về 'Mở việc' vì em đổi tên file gói đăng
- **Sửa**: `kho_video.py` (trên Drive) tách `TEP_TIEN_TO = ['goi-dang']`, `kiem_hop` kiểm theo tiền tố nên nhận cả tên cũ lẫn tên mới. Thử lại: hộp 01 (tên cũ) và 03 (tên mới) đều 'đủ 7 tệp'.
- **Cổng mới ②⑪**: nạp thật `kho_video.py` trên Drive, đối chiếu tên gói đăng xưởng ghi ra.
- **Đã kiểm**: `kiem_tram.py --sau` ĐẠT HẾT; API trạm trả `hop` đúng → nút về lại '📂 Mở kho'.
- **Còn tồn**: hai hộp TRÙNG cùng một video (02 và 03, md5 khớp) — chờ anh quyết bỏ cái nào.

## 14/08 (chiều) — đoạn clip anh cắt nay có đường về kho video
- **Mới**: `nhap_kho_video.nhap_doan_bai(viec)` — đọc `clip-canh.json` + clip trong `anh_phu`, cắt từng đoạn bằng ffmpeg rồi nhập với `loai='cat'`; chống trùng bằng dấu `nguon_doan`. CLI `--doan-bai <mã việc>`.
- **Nối**: `buoc3_xepkho.py` chạy nền song song với nhập kho ảnh (nút Kho vẫn nhanh).
- **Hồi tố**: chạy cho 3 bài gần nhất — kho video 4 → 15 dòng (13 cat, 2 goc).
- **Đã kiểm**: `kiem_tram.py --sau` ĐẠT HẾT (cổng ⑧b mới); CDP mở kho-nha-duyet tab Video thấy đủ 15 thẻ, không lỗi JS.

## 14/08 (chiều muộn) — đoạn vào kho: cắt đúng khung, chặn logo giữa, có đường lùi
- **Cắt theo khung**: `nhap_doan_bai` đọc khung né logo từ `clip-canh.json` + đuôi mã `clip::…::x,y,w,h`, áp `crop` khi cắt. Dấu chống trùng gồm cả khung.
- **Cổng chặn**: mắt máy trả thêm khoá `phu_giua` trong chính lượt gắn nhãn (không tốn thêm token) — thấy chữ/logo chèn giữa hình thì gỡ file, không ghi sổ. Thử thật: đoạn còn caption 'Svđ Pvf đã đạt hơn 60% tiến độ' bị CHẶN; đoạn anh đã khoanh khung thì cho qua.
- **Đường lùi**: sổ thêm `khung_da_cat` + `goc_kho` — cắt hụt thì quay về video gốc trong kho cắt lại, khỏi tìm nguồn từ đầu.
- **Đã kiểm**: `kiem_tram.py --sau` ĐẠT HẾT (cổng ⑧c mới, 3 mục).
- **Còn tồn**: 1 đoạn nhãn thô (`CHƯA nhãn mắt máy`) — chạy `--bo-nhan` sẽ bổ.

## 14/08 (tối) — từ khoá tiếng Anh · thanh % · nền cho 'một video nhiều cảnh'
- **Từ khoá tiếng Anh** (anh đo thật: ra ảnh ưng hơn): `goi_y.py` sinh thêm `tu_khoa_en` (tên quốc tế chuẩn, neo 'football' riêng chứ không trộn 'bóng đá'); vòng `_tim_san` quét CẢ HAI rổ rồi gộp, bỏ trùng, nới trần 40→60 ảnh/câu. Khai `tu_khoa_en`+`tu_khoa_2` vào whitelist `_luu_nhap`, `_chi_tiet`, payload `/api/viec` — cổng kiểm bắt được 2 chỗ quên, đã vá.
- **Thanh % thực thi** trong ô đồng hồ (`dhTienDo`), nối vào `theoDoiSauDuyet`. Dữ liệu có sẵn trong `VIEC_JOB` (da/tong), chỉ bày ra. CDP: vẽ đúng 42% (5/12).
- **Nền cho video dùng nhiều cảnh** (anh nói rõ: 'tải 1 lần dùng được cho nhiều cảnh'):
  · `tim_youtube(tu_khoa)` — tìm video 20s–10 phút, chưa tải; đo thật ra 3 video đúng chủ đề.
  · `ban_do_moc(tep)` — chia video thành ~14 khoảng, mắt máy tả từng khoảng, ghi vào sổ kho trường `moc`; trả tiền MỘT LẦN, lần sau đọc sổ. Đo thật v11 (9ph47): 10 mốc, đều sạch caption.
  · Trần tải hạ 15 → 10 phút theo anh chốt.
- **Đã kiểm**: `kiem_tram.py --sau` ĐẠT HẾT.
- **CÒN NỢ**: ① luật hạn mức mỗi bài (3–5 cảnh ghép · 2–4 cảnh video); ② khâu GHÉP mốc↔câu rồi tự cắt gán vào cảnh; ③ tự né logo cho đoạn cắt từ video mới tải.

## 14/08 (tối muộn) — mắt duyệt ảnh trên cảnh + xếp ứng viên theo sức khoẻ
- `_mat_kiem_nhap` nâng thành MẮT DUYỆT: soi MỌI ảnh đã gán (cả tay), trong CÙNG lượt haiku hỏi thêm wm/wm_chu/diem — không tốn thêm token. Watermark mép + có chữ → tự cắt (giữ bản gốc .truoc-cat-wm); giữa khung → máy gán thì gỡ, anh gán thì nhắc. Điểm 1–5 ghi vào sổ nhap.
- `_diem_anh_uv`: gán nháp hết lấy '6 tấm đầu Google' — xếp theo điểm ảnh + tỷ lệ hợp khung dọc + du_net. Đo thật: ảnh 1920×1920 lên đầu thay vì 6 bản 2560×1706 trùng nhau.
- Vòng siết: cắt oan 2 tấm → hoàn tác → đòi bằng chứng chữ → đo lại 0 oan (11 ảnh).
- Vá thêm: chuỗi sau Duyệt lời VỨT tu_khoa_en không ghi sổ (anh bắt); soiDi ở lại trong nhóm ảnh đã gán khi mở từ ảnh đã gán.
- `kiem_tram.py --sau` ĐẠT HẾT (cổng ⑧d 4 mục mới).

## 14/08 (khuya) — khung đôi CẤM ảnh dọc
- **Luật anh chốt**: 'chọn 2 ảnh ghép vào một cảnh thì phải chọn ảnh ngang — ảnh dọc là mất nhân vật'. Hình học: nửa khung đôi 1080×960 (tỷ lệ 1.125 ngang); ảnh dọc phải phóng ~1.7× cho đầy bề ngang → đầu/chân văng khỏi hình. Ngưỡng: w ≥ h là đạt (vuông mất ≤11%).
- **Chặn ở BA cửa**: ① `_gan_khung_doi` kiểm cả nửa trên (PIL mở file bài) lẫn nửa dưới (tra `kich_thuoc` trong sổ kho, cache `_kt_kho`) — dọc thì bỏ, đếm `doc_tren`/`doc_duoi`; ② prompt máy xếp nghĩa gắn dấu ▯DỌC vào từng ứng viên + câu cấm (model đọc nhãn chữ, không thấy hình — phải nói cho nó); ③ UI: anh ghép tay ảnh dọc thì KHÔNG cấm, chỉ nhắc to (tay người thắng máy). Không rõ kích thước → không chặn (đừng nghèo đề xuất vì thiếu dữ liệu).
- **Đo**: kho hiện 42/1009 tấm dọc. Test `_anh_ngang` 6 ca đều đúng.
- **Đã kiểm**: `kiem_tram.py --sau` ĐẠT HẾT (cổng ⑧e ba mục).

## 14/08 (đêm) — CẦU DÁN từ khoá dự án GPT (anh chốt 'đường ①')
- **Vì sao**: anh viết bài ở một dự án ChatGPT đã luyện, từ khoá tiếng Anh bên đó trúng hơn bộ gợi ý của trạm; trước phải chép TỪNG cảnh. API OpenAI không với tới 'dự án' (hướng dẫn tuỳ chỉnh + tệp + trí nhớ là của giao diện web), Chrome automation thì mong manh — nên chọn cầu dán.
- **Mới `tram/boc_goi_gpt.py`**: bóc khối GPT → {chỉ số câu: từ khoá}. KHỚP THEO CÂU (câu trích trong ngoặc kép) chứ không theo số thứ tự, vì 'ĐOẠN' của GPT ≠ 'CÂU' của trạm. Ba tầng khớp: trọn/chứa nhau → phần đầu 40 ký tự → chồng từ ≥50%. Không khớp thì BỎ, không đoán. Phân loại hai thứ tiếng bằng dấu tiếng Việt.
- **Trạm**: route `/api/tu-khoa-gpt`, nút 📋 Từ khoá GPT + cửa dán; cờ `tu_khoa_nguoi` đánh dấu câu anh dán — **chuỗi sau Duyệt lời không được đè** (không có phanh này thì anh dán xong bấm Duyệt lời phát nữa là bay sạch công chép tay).
- **Đã kiểm**: bộ bóc với định dạng GPT thật (khớp 3/4, phân loại đúng); CDP đầu-cuối trên bài video-5-bai-tay-407702 (khớp 3/9 câu dán thử, sổ ghi đúng); thử máy đè → phanh ăn 0/3; `kiem_tram.py --sau` ĐẠT HẾT (cổng ⑧f ba mục).

## 14/08 (khuya) — nạp QUY CHUẨN dự án GPT của anh vào bộ gợi từ khoá
- **Nguồn**: anh gửi 2 file quy chuẩn (đã lưu vào Drive kênh: `QUY-CHUAN-VIET-TIN.md`, `QUY-CHUAN-BO-SUNG.md`). Mục 17 là phần quyết định. Đối chiếu prompt cũ: THIẾU 3 luật.
- **Nạp vào `goi_y.py`**: ① luật 6b 'chọn cụm DỄ TÌM ĐƯỢC ẢNH THẬT' — tên ngoài từ điển thì cấm đứng một mình, phải chuyển sang đội+lứa+hành động (đây là gốc 2 bài hỏng cùng ngày); ② luật 6c tránh cụm kéo về ảnh rác (poster/thumbnail/highlight/tổng hợp); ③ câu tiếng Anh được kết bằng 'high resolution'.
- **Cầu chì code** `_ten_la_trong`: đối chiếu `nhan_vat` trong hồ sơ bài với từ điển thực thể; tên lạ thì GỠ khỏi câu lệnh + thêm tên đội (có bảng `_EN_DOI` cho câu tiếng Anh), ghi lý do vào ghi_chu. Bản đầu đoán mù đã báo oan «tiền đạo» — xem BRAIN.
- **Đã kiểm**: 6 mẫu câu thật (3 câu hỏng bị bắt, 3 câu sạch cho qua); chạy thật trên bài video-5-bai-tay-407702 → gỡ đúng 3 câu; `kiem_tram.py --sau` ĐẠT HẾT (cổng ⑧g).

## 14/08 (khuya) — bộ bóc gói GPT: thêm tầng mắt máy đọc hiểu
- **Anh bắt**: GPT trả mỗi lần một form; lần này từ khoá là DÒNG TRẦN (không gạch đầu dòng) → khuôn cứng bóc ra 0.
- **Sửa hai lớp**: ① nới khuôn (nhận dòng trần, cắt khối theo dòng có câu trích, loại dòng có dấu câu kể chuyện); ② thêm `_boc_bang_model()` — haiku đọc hiểu khi khuôn khớp < nửa số câu.
- **Đo**: khối kiểu anh vừa gặp → khuôn bắt được (0 token); khối VIẾT XUÔI hoàn toàn không khuôn → mắt máy khớp 3/4, tách đúng vi/en. UI báo rõ ⚡ khuôn hay 🧠 mắt máy.
- **Đã kiểm**: `kiem_tram.py --sau` ĐẠT HẾT (cổng ⑧h).

## 14/08 (khuya) — từ khoá phải neo THỜI ĐIỂM và BỐI CẢNH bài
- Prompt `goi_y.py` nay được đưa HỒ SƠ BÀI (`_mo_ta_ho_so`); thêm luật 6bb (chức danh chung → tên cụ thể / giải + năm); cầu chì `_neo_thoi_diem` chèn mốc cho 19 chức danh đổi theo thời gian (hlv, đội hình, áo đấu, bảng xếp hạng, head coach, squad, lineup…).
- Sửa 2 lỗi cầu chì phát hiện khi chạy thật: chèn đội theo tiêu đề (nay chỉ chèn khi câu chưa có đội), và 'AFF Cup' chắp từ neo phụ (sửa tại nguồn → ASEAN Cup).
- **Đo**: 6 mẫu `_neo_thoi_diem` đúng 6/6; chạy thật bài video-3-bai-tay-d0d9d6 → 0 câu dính AFF Cup, không còn câu hai đội, hầu hết câu có mốc ASEAN Cup 2026.
- `kiem_tram.py --sau` ĐẠT HẾT (cổng ⑧i ba mục).

## 15/08 — VIỆC 1 + VIỆC 2 của kế hoạch chuyển máy
- **Việc 1 — git**: `~/socbongda247` vào git, kho riêng tư github.com/anhlt148/socbongda247 (121 tệp). .gitignore chặn khoá, dữ liệu 8,3 GB, sổ học từng máy, 5 bản .bak. Quét hai lượt bằng mẫu chặt: 0 khoá lộ.
- **Việc 2 — đường dẫn ra khỏi mã**: `~/.config/socbongda247/may.json` (không lên git/Drive); `_do_drive()` + `_do_kho_nang()` tự dò cả Mac lẫn Windows; `NGUOI` để nhiều người khỏi trùng tên hộp thành phẩm. Route `/api/may` đọc+ghi, mục '💻 Máy này' trên trang phong cách có soi đường vừa nhập có thật không.
- **Git cứu một lần ngay trong ngày**: chèn route mới cắt nhầm vào giữa khối `/api/phong-cach`, lấy lại nguyên đoạn từ `git show HEAD:` — trước đây phải mò tay.
- `kiem_tram.py --sau` ĐẠT HẾT (cổng ⑧j, 5 mục).
- **CÒN**: việc 3 — script cài máy Windows (Task Scheduler thay launchd), hướng dẫn nhân viên, luật ai-sửa-code. Chờ anh xác nhận: máy đó có Google Drive for Desktop chưa, và nhân viên dùng tài khoản Claude nào (dùng chung tài khoản anh là rủi ro bị khoá).

## 15/08 — VIỆC 3: bộ cài máy Windows (máy thứ hai của anh)
- **`cai-windows.ps1`**: một lệnh `irm … | iex`. winget cài 6 công cụ (bỏ qua thứ đã có), git clone, dựng thư mục việc trên ổ D, ghi `may.json`, đăng ký Task Scheduler `SocBongDa247-Tram` chạy khi đăng nhập, tự kiểm bằng `/api/may`.
- **`HUONG-DAN-MAY-MOI.md`**: hướng dẫn theo thứ tự cho người ngồi máy đó.
- **Vá bám macOS**: `open`→`_mo_thu_muc()` (os.startfile trên Windows), `osascript`→`_bao_man_hinh()` (PowerShell toast); `kiem_tram.py` bỏ 4 đường `/Volumes` ghi cứng.
- **CHƯA THỬ THẬT** trên Windows — Mac không chạy được. Soi tĩnh: ngoặc cân, không biến lạ.
- `kiem_tram.py --sau` ĐẠT HẾT.

## 15/08 — DÁN LINK KHO LÀ ĐỦ
- **`CLAUDE.md`** ở gốc kho (8,3 KB): Claude Code tự đọc đầu phiên — hệ là gì, ba nhịp bắt buộc, 8 nguyên tắc, cách cài, lệnh hay dùng, luật nhiều người cùng làm.
- **`README.md`**: bảng 'nói thế này → Claude làm gì' cho người mở link.
- **Chuyển skill soc-kien-truc-su VÀO kho** `.claude/skills/` — trước sống trên Drive, máy khác kéo mã về là mất sạch BRAIN 50 KB + KIEN-TRUC + NHAT-KY. Nay git giữ lịch sử bài học luôn. Symlink `~/.claude/skills/soc-kien-truc-su` trỏ NGƯỢC vào kho; bản Drive đổi tên `.CHUYEN-VAO-REPO-15-08` để không còn hai nguồn.
- **Đã thử thật**: clone sang /tmp như máy trắng → đủ 8 tệp, 0 khoá lọt, 7 MB.
- Cổng ⑧k canh đủ 8 tệp. `kiem_tram.py --sau` ĐẠT HẾT.

## 15/08 — GỠ CHẶN CỨNG Windows
- **Mới `nen_tang.py`**: `khoa_ghi` (fcntl↔msvcrt), `tim_claude`, `thu_muc_tam`, `dang_chay`.
- Thay ở 11 tệp: bỏ hết `import fcntl`, gom 10 chỗ ghi cứng đường claude về một nguồn, `/tmp` → `thu_muc_tam()`, `chuan_ten.py` bỏ 2 đường `/Volumes`.
- **Cổng ⑥ `tang_windows()`**: nạp thử 11 module trong môi trường giả (chặn fcntl/pwd/grp/termios). Bắt ngay lỗi thứ tự import trong trạm.
- **Đo**: 11/11 nạp được · trạm thật trên Mac vẫn chạy · ghi sổ có khoá đúng cả hai môi trường · `kiem_tram.py --sau` ĐẠT HẾT.
- **CÒN CHƯA THỬ THẬT trên Windows**: bộ cài `cai-windows.ps1`, Task Scheduler, extension Chrome, ffmpeg/yt-dlp qua winget, và LaMa (xoá watermark) — venv `~/.cache/lama-venv` chưa có nhánh Windows, chức năng này sẽ mất bên đó.

## 15/08/2026 — extension tự báo khi chạy bản cũ

**Sửa gì:** `tram/extension/nen.js` gửi `?ext=<phiên bản manifest>` mỗi lượt hỏi
`/api/dang-lam`; route ấy trong `tram/tram_tai_nguyen.py` đọc `tram/extension/manifest.json`
rồi trả `ext_moi` + `ext_cu`; extension thấy `ext_cu` thì bật thông báo nhắc bấm ⟳ Tải lại.

**Vì sao:** anh hỏi "sau này extension vẫn update cập nhật được chứ?". Extension nạp kiểu
"giải nén" — `git pull` về file mới nhưng Chrome giữ bản đã nạp cho tới khi bấm ⟳. Lỗi
ÂM THẦM: trông vẫn chạy, chỉ thiếu đúng tính năng vừa thêm. Máy phụ ở xa, không ai soi được.

**Đụng đâu:** `nen.js` (1 chỗ gọi), route `/api/dang-lam` (1 chỗ), `HUONG-DAN-MAY-MOI.md`
mục D, cổng ⑧l trong `kiem_tram.py`.

**Đã kiểm:** gọi thật `?ext=1.3` → báo cũ ⚠ CÓ; `?ext=1.4` → ✅ đúng bản.
`kiem_tram.py --sau` ĐẠT HẾT.

**Vấp lại bẫy cũ (lần 4):** chèn khối mới bằng cách khớp chuỗi mà không xét khối đang
mở — khối ⑧l rơi vào GIỮA lời gọi `_bao(...)` của phím tắt, thành SyntaxError. Luật:
chèn xong phải `ast.parse` NGAY, và mốc chèn nên là chuỗi KẾT THÚC một câu lệnh
(dòng có `)` đóng), không phải dòng mở.

## 15/08/2026 — máy Windows không đọc được kho: kho RIÊNG TƯ

**Anh báo:** máy Windows dán link GitHub vào Claude Code thì chỉ thấy 404; phiên bên
đó đề xuất tải ZIP qua Drive, hoặc đổi kho sang Public 5 giây rồi đổi lại.

**Gốc:** kho `anhlt148/socbongda247` là PRIVATE. GitHub trả 404 cho người không có
quyền (giả vờ kho không tồn tại) nên lỗi trông rất khó hiểu.

**Lỗi nặng hơn của em:** chính bộ cài "một dòng" `irm raw.githubusercontent.com/... | iex`
CŨNG đọc kho riêng tư — tức hướng dẫn cài Windows em viết 15/08 CHƯA BAO GIỜ chạy được,
mà em vẫn báo "đã ổn để chạy máy kia". Tài liệu cài đặt là mã chạy trên máy người khác;
không thử được thì phải có cổng canh giả định của nó.

**Không chọn hai đường kia:** ZIP qua Drive thì máy phụ mất hẳn `git pull` (mỗi lần nâng
cấp lại ZIP tay). Public dù 5 giây cũng đủ cho bot crawl (GitHub có luồng sự kiện công
khai realtime) và kho có BRAIN 50 KB + nhật ký nội bộ.

**Đã làm:** đường khoá đọc — fine-grained PAT chỉ repo này, Contents Read-only.
- `cai-windows.ps1`: bước 2 mới lấy khoá ($T · $env:SOC_GH_TOKEN · hỏi), THỬ khoá qua
  api.github.com trước khi clone, cất vào Windows Credential Manager bằng
  `git credential approve` (không nhét vào .git/config), đường dự phòng có lau khoá.
- `capnhat.ps1` MỚI: nâng cấp một lệnh, lo đủ ba phần (mã · trạm · extension), kiểm
  việc đang chạy trước khi restart, in diff, chạy bộ kiểm.
- `HUONG-DAN-MAY-MOI.md` mục A2 mới: từng bước tạo khoá + cách thu hồi.
- README + CLAUDE.md: lệnh cài mang khoá; README nói rõ dán link cho phiên chưa có
  quyền thì chỉ thấy 404.
- `kiem_tram.py` tầng ⑦ `tang_may_phu()` — 11 mục canh bộ cài + ba tài liệu.

**Đã kiểm:** `kiem_tram.py --sau` ĐẠT HẾT. **CHƯA thử thật trên máy Windows** (không
cài được pwsh trên Mac — thiếu mật khẩu sudo), nên cú pháp PowerShell chỉ mới rà mắt.

## 16/08/2026 — extension tải ảnh/video CHẬP CHỜN: ba lỗi đua ghi chồng nhau

**Anh báo:** "tải ảnh, video lúc được lúc không · video 2 không thấy dù có tiếng kêu ·
ảnh 2·3·4 phải bấm tải lại trang mới thấy".

**Tái hiện:** bắn 6 lượt `/api/tai-len` ĐỒNG THỜI vào một bài thử → **mất sạch cả 6 tấm**.

**Ba gốc, chồng lên nhau:**
1. `gap_anh._so_tiep()` đặt tên bằng cách ĐẾM TỆP ĐANG CÓ → 6 luồng cùng ra `n00.jpg`,
   cùng ghi đè; khâu chống trùng thấy "ảnh của luồng khác" nên `os.remove` → xoá mất tệp
   luồng kia đang `Image.open` dở → "không đọc được ảnh". Sổ vân tay cũng đọc-sửa-ghi
   không khoá nên mất mục theo.
2. `_nhan_video_job` đếm `tay_*.mp4` — mà video ĐANG TẢI mang tên `tay_02.f399.mp4.part`,
   glob không thấy → gắp video 2 lúc video 1 chưa xong thì cả hai cùng ra số 01. Thêm:
   lượt tải hỏng KHÔNG dọn `.part` (đã thấy 2 mảnh 10 MB nằm lại ở 2 bài).
3. Trang nạp lại kho bằng cách RÌNH trạng thái "đang kéo", poll 4 giây. Nhận một tấm ảnh
   xong trong chưa tới một giây → poll trượt sạch → trang không bao giờ biết có ảnh mới.
   Video lâu nên bắt được, ảnh nhanh nên trượt — đúng cái "lúc được lúc không".

**Đã sửa:**
- `gap_anh.py`: `_khoa_thu_muc()` (Lock theo thư mục) + `_dat_cho()` xí tên bằng
  `O_CREAT|O_EXCL`; `nhan_tep` chạy trọn trong khoá; `_thu_hoach` dùng chung cơ chế xí
  tên; dọn tệp giữ chỗ khi tấm bị loại. Gỡ luôn 2 chỗ `import threading` TRONG THÂN HÀM.
- `tram_tai_nguyen.py`: video xí số bằng O_EXCL, glob nhìn `tay_NN*` mọi đuôi, dọn rác
  `.part` ở `finally`; khai sẵn `p_giu/tep/n` để finally không NameError khi job lỗi sớm.
- `_keo()` đếm LUỸ KẾ `xong`; UI so số luỹ kế thay vì rình trạng thái tức thời.
- `kiem_tram.py` tầng ⑨ `tang_dua_ghi()`: bắn 6 luồng thật vào `nhan_tep`, đếm lại.

**Đã kiểm:** test lại 6/6 tấm về đủ, tên riêng biệt, sổ vân tay khớp. `kiem_tram.py --sau`
ĐẠT HẾT. Dọn 2 mảnh `.part` tồn đọng.

## 16/08/2026 — kho mã chuyển sang CÔNG KHAI

**Anh chốt** sau khi em đo thật: repo KHÔNG chứa khoá/token nào (mọi `github_pat_...`
chỉ là chỗ điền mẫu), không có tệp khoá nào từng lọt vào lịch sử, không có số điện
thoại/email lạ. Cái mất khi công khai thuần là BÍ QUYẾT VẬN HÀNH (BRAIN 61 KB, nhật ký
71 KB, phân tích văn phong 60 KB) — không phải rủi ro an toàn.

**Đã làm:** `gh repo edit --visibility public`. Thử clone ẩn danh: ĐƯỢC. Bộ cài tải
trực tiếp: HTTP 200.

**Tài liệu + bộ cài theo sau:** lệnh cài bỏ khoá; `cai-windows.ps1` GIỮ đường khoá làm
dự phòng và tự hỏi khoá nếu clone hỏng (kho có thể đổi về riêng tư bất cứ lúc nào);
mục A2 trong hướng dẫn thu vào khối `<details>`.

**Cổng ⑦ nay HỎI THẲNG GitHub** repo đang công khai hay riêng tư rồi mới kết luận tài
liệu đúng hay sai — thay vì ghim cứng một trạng thái. Bỏ qua khối `<details>` khi soi.

**Vá kèm — cổng ④ tự làm bẩn chỗ nó đứng:** nó gửi ảnh kiểm vào bài thật, dọn ảnh nhưng
QUÊN dọn vân tay → lượt chạy sau bị chính mình chặn vì "TRÙNG". Lỗi có sẵn, chỉ lộ ra
SAU khi vá đua ghi (trước đó sổ vân tay bị đè nên vô tình sạch). Nay dọn cả vân tay, và
coi "TRÙNG" cũng là đạt — thứ cổng canh là CỬA CÓ THÔNG, không phải ảnh có mới.
Đã chạy `--sau` HAI LẦN LIÊN TIẾP, cả hai ĐẠT HẾT.

## 16/08/2026 — kho video: lọc gốc/cắt + video gốc chưa bao giờ vào kho

**Anh giao:** ① làm bộ lọc giữa video gốc và video đã cắt trong kho; ② tìm xem vì sao
video gốc tải về phục vụ các bài gần đây KHÔNG hiện trong kho, làm cho nó hiện lại.

**Chẩn đoán ②:** sổ kho video có 28 mục — **26 đoạn cắt, chỉ 2 video gốc**. Trong khi ổ
máy có **38 video gốc** (3,4 GB) nằm rải rác ở `<bài>/clip/tay/`. Gốc: `_nhan_video_job`
chỉ lưu vào thư mục bài + ghi `nguon-clip.json` của bài — **chưa bao giờ nhập kho chủ
thể**; chỉ khi anh CẮT một đoạn thì đoạn ấy mới vào kho (loai="cat"). Nên video gốc vô
hình với mọi bài khác.

**Đã làm:**
- Hồi tố: nhập 20 video gốc đủ tiêu chuẩn vào kho qua `_nhap_tep_video(..., loai="goc")`
  — dùng lại luồng chuẩn (3 lớp chống trùng + nhãn mắt máy + ảnh mồi), không viết luồng
  song song. Loại tệp <1,2 MB (mảnh tải hỏng) và `kho__v*.mp4` (bản kéo TỪ kho về bài —
  nhập lại là quay vòng).
- Lọc gốc/cắt: server nhận `?loai=goc|cat` và trả `so_goc`/`so_cat`. Lọc ở SERVER vì
  danh sách bị cắt còn 60 đoạn trước khi trả về — lọc phía trang là mất bớt.
- UI: ba chip `tất cả · 🎞 gốc · ✂ cắt`, chỉ hiện ở tab Video, tiêu đề đổi theo bộ lọc.
- Tên video gắp về mang nội dung bài (`tay_01_thai-lan-ca-khia-viet-nam.mp4`) — GIỮ
  tiền tố `tay_NN` vì mọi phép đếm số và glob dọn rác đều dựa vào nó.
- `slug_hoa` chuyển từ `buoc3_xepkho.py` sang `chuan_ten.py` — não một nguồn.
- Gương Drive BỎ QUA video >60 MB trong `video-chu-the/`: video gốc là thứ mỗi máy tự
  tải được, đẩy 3,4 GB lên Drive là phí dung lượng và băng thông.
- launchd `com.socbongda247.dongbokho` chạy gương 15 phút/lượt (python3, không qua zsh —
  TCC chặn shell đụng Drive).
- `kiem_tram.py` tầng ⑩ `tang_kho_video()` — 10 mục.

**Đã kiểm:** API ba trạng thái lọc (tất cả 39 / gốc 12 / cắt 27 — đúng từng con số) ·
bấm thật ba chip trên trình duyệt (13 gốc / 27 cắt / 40 tất cả, chip sáng đúng) · route
xem video gốc HTTP 200 · ảnh mồi HTTP 200 · không ô ảnh nào vỡ · `kiem_tram.py --sau`
ĐẠT HẾT.

**Bổ sung cùng ngày — hai lỗi bắt được KHI TEST bằng trình duyệt thật:**
- Chip "tất cả" bị vắt thành hai dòng → thêm `white-space:nowrap; flex:0 0 auto`.
- **Ảnh mồi không hiện trên lưới video** dù server trả 200: `loading="lazy"` không kích
  hoạt cho ảnh vừa chèn bằng innerHTML. Bỏ lazy cho lưới video (≤60 ô, ảnh 30 KB,
  localhost), giữ lazy cho lưới ảnh. Cổng ⑩ canh thêm mục này.
  *Cổng đầu tiên viết ra lại bắt oan chính lời bình luận giải thích — vì bình luận có
  nhắc chuỗi `loading="lazy"`. Bài học nhỏ: cổng soi chuỗi thì phải soi ĐÚNG thẻ, đừng
  cắt khối theo độ dài.*

## 16/08/2026 — video gốc tự vào kho khi xếp kho + sửa nút ⇥ vừa ô

**① Anh chốt:** "mỗi lần làm xong 1 content có dùng video gốc thì tự đẩy vào kho chung."

Khung đã có sẵn: nút Kho chạy nền `nhap_kho_chu_the.py` (ảnh) và `nhap_kho_video.py
--doan-bai` (đoạn cắt). Thiếu đúng video GỐC — cùng họ lỗi 14/08, chỉ khác tầng.
Nay thêm `nhap_goc_bai(viec)` và cho `nhap_doan_bai` gọi nó ở đầu: MỘT đường chạy, nút
Kho đã gọi sẵn nên không đẻ tiến trình thứ ba. Có thêm cờ `--goc-bai` để chạy riêng.
Test thật: bài thử có 1 video gốc → chạy đúng lệnh nút Kho gọi → v65 vào kho có nhãn
mắt máy; chạy lần hai → "BỎ QUA — đã trong kho". Dọn sạch bản thử sau khi kiểm.

**② Anh báo:** nút ⇥ vừa ô "dùng được một lần rồi không thấy hiện nữa". Tái hiện được
bằng trình duyệt thật, và là HAI lỗi chồng nhau:

- `tuDoiThiDenTheo()` — chạy mỗi lần TUA video, gõ ô Từ, bấm "⏱ Từ =" — tự dựng lại
  dòng chữ `#mcDai` (nên mất luôn phần "· ô cần 3.9s") và KHÔNG đụng `#mcVuaO`. Nút bị
  `display:none` từ lần bấm trước, chỉ `capNhatMc()` bật lại được → kẹt ẩn.
- `oGiay()` nhận mã ô PHỤ "5:0" rồi `+"5:0"` → NaN → trả 0. Ô phụ coi như không có độ
  dài; chạm vào một cảnh phụ là nút tắt vĩnh viễn tới khi đóng mở lại cửa cắt.

Sửa: `tuDoiThiDenTheo` giao trọn cho `capNhatMc`; `oGiay` tự tách `:` ngay trong nó
(chứ không bắt từng nơi gọi nhớ tách). Cổng ⑪ canh 8 mục, gồm cả "mọi đường đổi mốc
đều phải chạy qua capNhatMc".

**Đã kiểm:** ba vòng tua → kéo lệch → bấm vừa ô, cả trên ô chính lẫn ô phụ, nút hiện/ẩn
đúng từng bước và bấm ăn mọi lần. `kiem_tram.py --sau` ĐẠT HẾT hai lần liên tiếp.

## 16/08/2026 — máy phụ tự biết khi có bản nâng cấp

**Anh hỏi:** "mỗi lần update như này có auto lên git và auto về máy kia không? nếu ko
thì làm gì để nó auto hoặc có thông báo để máy kia biết mà update."

**Thực trạng:** lên git thì đã tự động (em push mỗi lần xong việc). Về máy kia thì
KHÔNG — phải tự nhớ chạy `git pull`, nhớ vài hôm rồi quên.

**Đã làm:**
- `_do_ban_moi()` + luồng nền `_canh_ban_moi()` trong trạm: hỏi `git ls-remote` mỗi 20
  phút (đo thật 1,1 giây/lượt nên không được để chặn trang), kết quả nằm trong `BAN_MOI`.
- `/api/dang-keo` trả kèm `ban_moi` — ĐI NHỜ lượt poll 4 giây đã có sẵn, đúng lối đã
  dùng cho cơ chế nhắc extension 15/08.
- Dải nhắc góc phải dưới + nút "⬇ Cập nhật ngay" / "để sau".
- `/api/cap-nhat`: từ chối 409 khi còn việc chạy dở · `pull --ff-only` · rồi tự thoát
  cho bộ quản lý dịch vụ bật lại; trang chờ trạm sống rồi tự nạp lại.
- **Windows chưa tự bật lại được** — Task Scheduler đăng ký từ 15/08 không có
  `RestartCount`, trạm thoát là chết luôn. Bổ sung vào `cai-windows.ps1`, và
  `capnhat.ps1` vá Task đã cài sẵn (bộ cài không áp dụng ngược được).

**Đã kiểm bằng cảnh THẬT:** đẩy một bản rỗng lên GitHub rồi lùi máy về bản trước → trạm
báo đúng "1 bản mới · máy đang chạy 0a3499e" → dải hiện trên trang → bấm nút → pull →
trạm tự thoát → launchd bật lại → máy về đúng bản mới → trạm báo "đã là bản mới nhất".
Chốt an toàn: bật một việc chạy nền rồi gọi cửa cập nhật → HTTP 409 kèm lời giải thích.
Bản thử đã gỡ khỏi GitHub. `kiem_tram.py --sau` ĐẠT HẾT hai lần liên tiếp; cổng ⑫ 10 mục.

## 16/08/2026 — chuỗi máy tự chạy xong, trang tự nạp lại

**Anh bắt:** "kiểm tra bước này báo gán nháp tài nguyên rồi mà không thấy? phải tải lại
trang mới có. em set up xong thì tự tải lại trang đi."

**HAI gốc:**
① Người canh job (`theoDoiSauDuyet`) chỉ sống trong TRANG ĐÃ BẤM Duyệt lời. Anh reload,
   mở bài khác rồi quay lại, hay mở trạm ở tab khác — mất người canh, chuỗi xong chẳng
   ai gọi `napViec`. Vòng đồng hồ vẫn poll nhưng chỉ nhìn "có job đang chạy không" —
   ảnh chụp tức thời, poll 6 giây rất dễ trượt đúng khoảnh khắc job kết thúc.
② **Sổ `VIEC_JOB_MA` (job này của bài nào) chỉ được 4/21 đường tạo job ghi vào.** Lập
   14/08 để thanh %% sống lại sau reload, vá vài đường rồi bỏ quên 17 đường còn lại —
   chúng đẻ job VÔ DANH: trạm biết có việc chạy mà không biết của bài nào.

**Sửa:** ghi sổ ở **MỘT CỬA** — `do_POST` nhớ `ma` của thân yêu cầu, `_js()` thấy phản
hồi mang mã job thì ghi luôn. Vá 21 chỗ rời rạc thì chắc sót, và đường thứ 22 thêm sau
này lại quên. Rồi `/api/dong-ho` trả `job_xong` (SỐ LUỸ KẾ), trang so với lần trước,
thấy tăng là `napViec` — không trượt được dù poll thưa cỡ nào.

**Tự soi ra hai lỗ hổng của chính bản vá, bịt trước khi nó cắn:**
- `/api/dong-ho` cũng trả khoá `"job"` nhưng là DICT mô tả bước đang chạy → lọt vào cửa
  ghi sổ là dùng dict làm khoá từ điển. Chặn bằng `isinstance(jid, str)`.
- Kết nối keep-alive dùng lại một handler cho nhiều lượt, nên `_ma_bai_than` của lượt
  POST trước còn dính sang lượt GET sau. Tách `_chay_post()` + `finally` dọn sạch.

**Đã kiểm:** chạy chuỗi thật rồi KHÔNG đụng gì thêm → trang tự nạp lại 3 lần (nhiều
đường cùng báo, chấp nhận được) rồi ĐỨNG YÊN 20 giây — không vòng lặp. Gọi xen GET liên
tục lúc job đang chạy: sổ vẫn đúng. Cổng ⑬ 8 mục. `kiem_tram.py --sau` ĐẠT HẾT hai lần.

## 16/08/2026 — tài nguyên bài trước dùng được cho bài sau

**Anh hỏi:** "làm thế nào để tài nguyên cho video 1 hiện luôn kho ảnh/video để phục vụ
cho video 2?"

**Đo thật:** ảnh chỉ vào kho chung khi bấm nút KHO (`buoc3_xepkho` gọi
`nhap_kho_chu_the.py`). Bài `video-4` hôm nay có 29 ảnh, chưa xếp kho → 29 tấm ấy vô
hình với mọi bài khác. Mà hai bài liên tiếp thường CÙNG chủ đề, nên ảnh dư của bài
trước lại đúng là thứ hợp bài sau nhất — công tìm mất trắng.

**Không viết luồng mới.** `nhap_kho_chu_the.py` vốn quét TOÀN BỘ `<bài>/anh/` (`[nt]*.jpg`),
kể cả tấm chưa gán cảnh nào — chỉ cần **gọi sớm hơn**. Hai mốc:
- **Cuối chuỗi sau Duyệt lời**: bài vừa có đủ ảnh tải về → đẩy vào kho ngay.
- **Lúc đổi bài** (`/api/viec/<ma>` thấy mã khác lần trước): vét nốt thứ anh gắp thêm
  bằng tay sau chuỗi — ảnh qua extension, video gốc kéo từ MXH. Vét cả `--goc-bai` cho
  video, theo luật "chính có gì phụ có nấy". Chạy nền, không chặn trang.

Kho vẫn sạch vì `nhap_kho_chu_the` giữ nguyên cổng lọc sẵn có (bẩn · nhỏ · trùng · lạc đề).

**Đã kiểm bằng cảnh thật:** mở bài video-4 (chưa xếp kho, kho có 0 tấm từ bài này) →
chuyển sang bài video-3 → trạm tự vét: **+2 tấm mới vào kho**, 24 tấm bỏ đúng vì đã có
sẵn (vốn lấy từ kho ra), 1 bẩn 1 nhỏ bị cổng loại. Cổng ⑭ 6 mục.
`kiem_tram.py --sau` ĐẠT HẾT hai lần liên tiếp.
