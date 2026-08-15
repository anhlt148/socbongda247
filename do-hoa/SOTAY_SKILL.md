---
name: lam-card-do-hoa
description: >-
  Dựng CARD ĐỒ HOẠ số liệu cho video (1920×1080 PNG nét retina, chữ tiếng Việt chuẩn không ô vuông,
  tự canh chữ không tràn khung, nền gradient điện ảnh tối, tự tải cờ quốc gia): thẻ tiêu đề, số liệu
  khổng lồ, card ĐỐI ĐẦU (versus, có cờ + tỉ số), BẢNG XẾP HẠNG có thanh giá trị, SO SÁNH bằng thanh
  ngang, DÒNG THỜI GIAN. Kho stock (Pexels) KHÔNG có mấy thứ này — đây là nội dung GỐC (cộng điểm YPP).
  LUÔN dùng skill này khi Lê Tuấn Anh cần "card đồ hoạ", "card số liệu", "card đối đầu / versus", "bảng
  xếp hạng", "dòng thời gian", "card so sánh", "đồ hoạ số liệu cho video", hoặc khi skill tài nguyên
  (sudia-tim-tai-nguyen / fetch_football) đánh dấu cue là 🎨 CARD/canva/motion graphic cần tự dựng.
  Dùng cho MỌI kênh (bóng đá, sử-địa, kinh tế). Chạy bằng 1 file JSON → render cả loạt card một lệnh.
---

# lam-card-do-hoa — Card đồ hoạ số liệu nét xịn, tự động hoá cao

Thay Canva/After Effects cho các card số liệu hay gặp. Render 2× rồi thu nhỏ LANCZOS → cạnh chữ MỊN;
tự giảm cỡ chữ để KHÔNG tràn khung; font Be Vietnam Pro (đủ dấu tiếng Việt); tự tải cờ nước từ flagcdn.
Kết quả là PNG 1920×1080 nhét thẳng vào `tai_nguyen/NN_Phan/anh/` — engine dựng tự thêm Ken Burns.

## Cần (một lần mỗi máy)
Python có `pillow` + `numpy` (dùng chung venv với skill khác: `~/.cache/claude-earth-venv`, hoặc
`pip install pillow numpy`). Font đã kèm sẵn trong `assets/fonts/` (không cần cài).

## Cách chạy — 1 file JSON, render cả loạt
```bash
~/.cache/claude-earth-venv/bin/python scripts/render_card.py cards.json
```
`cards.json` là MẢNG các card, mỗi card 1 object có `type`, `out` (đường dẫn PNG) + trường riêng.
Render 1 card: `render_card.py --one spec.json --out card.png`. Mẫu đầy đủ: `references/mau-card.json`.

## 6 loại card (trường của từng loại)
- **title** — `{title, subtitle?, kicker?, accent?}`. Thẻ tiêu đề lớn, tự xuống dòng, gạch accent.
- **stat** — `{value, label?, note?}`. 1 con số khổng lồ + nhãn trên + chú dưới. Vd `{"value":"36","label":"Bàn thắng","note":"Kỷ lục một mùa Ngoại hạng"}`.
- **versus** — `{title?, left:{name,value,flag?,win?}, right:{...}}`. Đối đầu 2 phe, có cờ (flag = mã ISO 'no'/'br' hoặc tên nước 'Na Uy'), `win:true` tô số bằng accent.
- **leaderboard** — `{title, rows:[{name,value,highlight?}]}`. Bảng xếp hạng có thanh giá trị, `highlight:true` tô 1 dòng.
- **compare** — như leaderboard, để so sánh (dân số/diện tích), không đánh số hạng cứng.
- **timeline** — `{title, points:[{year,caption}]}`. Dòng thời gian ngang, mốc + chú thích.

Trường chung: `accent` (màu chủ đạo hex, vd `"#e11d2a"` đỏ bóng đá, `"#1d9bf0"` xanh, `"#0f9d58"` xanh lá),
`out` (đường dẫn PNG). Không set accent thì dùng đỏ mặc định.

## Quy trình tự động (khi skill tài nguyên đánh dấu 🎨 CARD)
1. `fetch_football.py`/`fetch_resources.py` định tuyến cue bản đồ/card/số liệu/dòng thời gian sang mục
   "🎨 CARD tự dựng" trong báo cáo (kèm thư mục đích + tiền tố cue `NN_`).
2. Trợ lý đọc báo cáo + lời bình cue đó, RÚT số liệu thật (tỉ số, cột mốc, xếp hạng) → viết `cards.json`,
   mỗi card `out` trỏ đúng `tai_nguyen/NN_Phan/anh/NN_<slug>.png` (đúng tiền tố cue để engine xếp hình).
3. Chạy render → xem BẰNG MẮT (Read từng PNG) kiểm chữ Việt/tràn khung/cờ đúng → sửa JSON nếu cần.
4. Ghi license_log: "Card đồ hoạ tự dựng (lam-card-do-hoa) — nội dung gốc, không vướng bản quyền".

## Nguyên tắc để KHÔNG lỗi vặt (đã cài sẵn)
- **SÀN THỜI LƯỢNG 6 GIÂY (luật anh Tuấn Anh 14/07/2026)**: MỌI sản phẩm VIDEO tự tạo ≥ 6s. Đã cắm
  `max(6.0, seconds)` trong 7 script động: `player_spotlight`, `focus_pop`, `stat_bubbles`,
  `quote_spotlight`, `breaking_news`, `tactical_board`, `lineup_board` — truyền `--seconds`/`"seconds"`
  nhỏ hơn 6 vẫn tự nâng lên 6. (Card PNG tĩnh do engine dựng cấp thời lượng khi ghép, không tính ở đây.)
- **Nét**: render 2× (SS) → thu nhỏ LANCZOS. Đừng bỏ bước này.
- **Không tràn**: mọi tiêu đề/nhãn qua `fit_font` (tự giảm cỡ tới khi vừa) + `wrap` (xuống dòng).
- **Chữ Việt**: chỉ dùng font trong `assets/fonts/` (Be Vietnam Pro đủ dấu). KHÔNG dùng font hệ thống
  ngẫu nhiên (dễ thiếu glyph → ô vuông).
- **Cờ**: `flag` nhận mã ISO hoặc tên nước (bảng `ISO` trong script — thêm nước mới vào đó); tự tải
  flagcdn, cache ở `assets/flags/`. Nước lạ chưa có trong bảng → truyền thẳng mã ISO.
- **Màu accent** nên khớp nhận diện kênh/chủ đề (đỏ bóng đá, xanh địa lý…) để cả loạt card đồng bộ.

## Ảnh cầu thủ XÓA NỀN trên LƯỚI ĐỘNG → MP4 (player_spotlight.py) — chất kênh phân tích bóng đá
```bash
~/.cache/claude-earth-venv/bin/python scripts/player_spotlight.py --player "Erling Haaland" --out haaland_spot.mp4 --accent "#e11d2a"
```
Tự tải ảnh cầu thủ (Wikipedia) → **xóa nền (rembg)** → ghép lên nền LƯỚI TỐI CHẠY + quầng accent +
rim sáng quanh người → clip 1920×1080, 5-8 giây. Dùng làm intro/điểm nhấn/tiết lộ (kiểu spotlight cầu
thủ kênh phân tích hay dùng). **Chuyển động (theo yêu cầu anh):**
- `--grid-dir ltr|rtl|up|down|diag` — LƯỚI chạy hướng nào (ltr = trái→phải).
- `--enter left|right` — cầu thủ ĐI VÀO từ cạnh, **nhỏ→to dần, trôi vào giữa** (giảm tốc mượt). Bỏ
  `--enter` (mặc định none) = đứng giữa zoom chậm.
- `--seconds 6` (5-8), `--accent`, `--photo <ảnh.png>` (tự đưa ảnh thay vì tải), `--side` (khi none).
Cần **rembg** (`pip install rembg onnxruntime`; lần đầu tự tải model u2net ~176MB).
Ghi license_log: "Ảnh cầu thủ Wikipedia (CC) + hiệu ứng tự dựng — biến đổi mạnh, ghi công".

## ⚽ SƠ ĐỒ CHIẾN THUẬT ĐỘNG → MP4 (tactical_board.py) — resource_type: `Tactical` (mới 11/07/2026)
Kể PHA BÓNG bằng sân 2D điện ảnh + quân di chuyển + bóng bay cong + vòng nổ ghi bàn — **thay thế
footage khi tường thuật pha bóng** (tin bóng đá, pha bóng lịch sử không có hình, mô tả đội hình).
Tài nguyên GỐC 100%, không rủi ro bản quyền.
```bash
~/.cache/claude-earth-venv/bin/python scripts/tactical_board.py pha_bong.json -o pha1.mp4
```
JSON: toạ độ sân 0-100; `the[]` gồm `cau_thu` (doi a/b, so áo, `duong` = polyline chạy, `t`=[bắt đầu,
kết thúc]), `bong` (`cong`: độ cong đường tạt/chọc khe), `no` (vòng nổ tại điểm ghi bàn, `t` mốc đơn).
Trợ lý tự DÀN CẢNH từ scene_note của blueprint (vd "tạt cánh phải, số 9 đánh đầu, 2 hậu vệ kèm"):
đặt 3-6 quân là đủ kể chuyện, đừng xếp cả 22 người. 6s/pha là chuẩn.

## 📰 CARD TIN NÓNG ĐỘNG → MP4 (breaking_news.py) — resource_type: `News` (mới 11/07/2026)
Headline kiểu bản tin thể thao: tag đỏ trượt vào + tiêu đề đập + ticker chạy đáy — cho video TIN
bóng đá (chuyển nhượng, kết quả, chấn thương, thông báo).
```bash
~/.cache/claude-earth-venv/bin/python scripts/breaking_news.py tin.json -o tin1.mp4
```
JSON: `{tag, tieu_de, phu_de, ticker, mau, seconds}`. Ticker nên 3-5 tin ngắn VIẾT HOA ngăn `·`.

## Bản đồ taxonomy TỰ TẠO (blueprint v2 → module nào)
`Card`→render_card.py · `Tactical`→tactical_board.py · `News`→breaking_news.py ·
`Spotlight`→player_spotlight.py · `FocusPop`→focus_pop.py · `Quote`→quote_spotlight.py ·
`Lineup`→lineup_board.py · `StatPop`→stat_bubbles.py ·
`Map`→style_flagmap.py (sudia-tim-tai-nguyen) · `Flyby`→skill sudia-bay-google-earth.
Công cụ xử lý footage (không phải loại cảnh): film_look.py (bắt buộc cho nguồn) ·
annotate_footage.py (telestrator — vẽ phân tích đè footage).
Mục tiêu hệ thống: **≥25% cảnh mỗi video là tự tạo** (video tin tức ≥50%) — vừa giảm phụ thuộc
tải, vừa tăng tính gốc cho YPP.

## 🎞 Hiệu ứng học từ VIDEO MẪU #2 (8 mốc, 11/07/2026) — 3 đã build, 4 chờ build
**Đã build (test bằng dữ liệu thật):**
- **lineup_board.py** (`Lineup`, mẫu 13:36): sa bàn trắng kẻ nét + ẢNH MẶT cầu thủ (tự tải Wikipedia,
  crop tròn) pop-in tại vị trí + nhãn ST/LW/RW. JSON: cau_thu[{vi_tri,ten,xy}]. Dùng: đội hình ra
  sân, bộ ba/tứ tấu, so vai trò.
- **stat_bubbles.py** (`StatPop`, mẫu 11:46): cutout giữa + vòng tròn kem SỐ LIỆU TO pop-in lần lượt,
  số ĐẾM LÊN. `--stat "2700:Phút thi đấu"` (≤4). Thay stat card tĩnh khi muốn người + số cùng cảnh.
- **annotate_footage.py** (telestrator, mẫu 4:55): khung màu bo góc kiểu TV phân tích + bubble tên +
  ellipse vị trí + mũi tên NÉT ĐỨT đè footage. Chạy SAU film_look. ⚠️ Bẫy đã dính: input PNG `-loop 1`
  vô hạn → PHẢI chốt `-t <dur video>` không thì ffmpeg treo (đã cài trong script).
**Đã giải mã, CHỜ BUILD (spec đủ để dựng khi cần):**
- `pop_duotone` (mẫu 0:10): chủ thể GIỮ MÀU + posterize nhẹ; NỀN nhuộm 1 tông (duotone) + halftone
  chấm + khung đen TV. Là "chất nền" nhận diện của cả phong cách pop.
- `pop_stage` (mẫu 4:46): cutout người thật đứng trong BỐI CẢNH VẼ PHẲNG (cỏ nõn, biển quảng cáo
  khối màu, khán đài vẽ) — cần bộ nền minh hoạ generative.
- `photo_callouts` (mẫu 19:02): chủ thể màu + các nhân vật phụ hiện trong VÒNG TRÒN ĐEN TRẮNG pop-in
  lần lượt quanh — kể quan hệ nhân vật ("trong khi Neymar, Hazard, Bale gục ngã…").
- `quote-pop` (mẫu 0:01): biến thể quote nền màu SÁNG phẳng + chữ đen + khung TV (thêm --style cho
  quote_spotlight).

## 🎞 3 hiệu ứng HỌC TỪ VIDEO MẪU BLV Anh Quân (11/07/2026 — quy trình 👁 chạy thật lần đầu)
- **focus_pop.py** (`FocusPop`, mẫu 0:20): 1 ảnh action → cảnh động "nét nông": chủ thể tách nền
  SẮC trên chính ảnh đó blur bokeh + zoom lệch pha (parallax) + grain. `--photo a.jpg --out ra.mp4`.
  Đã feather mép cutout 2px — đừng bỏ (mép cứng lộ viền). Nâng cấp mọi ảnh tĩnh của kho.
- **quote_spotlight.py** (`Quote`, mẫu 5:49): cutout + nền màu phẳng hoạ tiết dấu + khối trích dẫn
  viền trắng, chữ hiện TỪNG DÒNG + tác giả. `--photo --quote --author --bg "#4a0e12"`. Đúng kỹ thuật
  "chìa bằng chứng" khi trích phát ngôn/báo chí.
- **film_look.py** (không phải resource_type — MÁY XỬ LÝ FOOTAGE NGUỒN, mẫu 0:10 + luật anh chốt
  11/07/2026): footage lấy từ nguồn gốc BẮT BUỘC qua đủ 4 lớp — **lật ngang** (mặc định bật;
  `--khong-lat` chỉ cho đồ tự tạo) + **zoom 126%** (crop lệch lên `--bias-top 0.7` nuốt logo/tỉ số
  mép trên) + **xoá logo/watermark sót** (`--xoa-goc "x:y:w:h"` toạ độ khung gốc, lặp được nhiều
  vùng) + chất phim grain/vintage/vignette (`--manh`). Chạy xong PHẢI trích frame XEM MẮT xác nhận
  sạch — bài học thật: watermark ĐÁY khung không bị crop-lệch-lên nuốt, phải delogo. (Hiệu ứng
  "khung social trên gradient" 0:51 → ghi sổ chờ hợp nhất engine T1.)

## 👁 HỌC HIỆU ỨNG MỚI TỪ VIDEO MẪU (quy trình chính thức, anh chốt 11/07/2026)
Khi anh thả video/ảnh mẫu ("hiệu ứng ở giây X hay đấy"), trợ lý chạy vòng 5 bước:
1. **Trích frame**: ffmpeg lấy 5–10 khung quanh mốc giây → XEM BẰNG MẮT.
2. **Mổ xẻ**: cấu trúc lớp (nền/lưới/glow/chủ thể/chữ), màu chủ đạo, font dạng gì; so các frame liên
   tiếp suy ra chuyển động (hướng, tốc độ, ease).
3. **Phân loại tỉnh táo**: (a) module sẵn có chỉnh tham số · (b) thêm tùy chọn vào module cũ ·
   (c) đáng viết module mới (như tactical_board/breaking_news) · (d) KHÔNG đáng tự tạo (3D/particle
   nặng) → nói thẳng, đề xuất thay thế. Đừng cố tái tạo mọi thứ.
4. **Tái tạo + tự chấm**: code PIL/ffmpeg → render → đặt frame mình cạnh frame gốc → so mắt → chỉnh
   → lặp tới đạt. Học Ý TƯỞNG, không sao chép nguyên xi asset (bản mình = nội dung gốc, sạch YPP).
5. **Nhập kho để Agent TỰ ĐỀ XUẤT**: đăng ký 3 chỗ — SKILL.md này (bản đồ taxonomy → module),
   system prompt Agent Biên kịch (`cong-cu/agent-xu-ly-kich-ban-system-prompt.md`: thêm resource_type
   + luật khi nào dùng), dropdown Trạm kiểm duyệt. Từ đó blueprint tự đề cử loại cảnh mới ở Cửa 1.
Tiền lệ: player_spotlight (anh tả hiệu ứng từ video tham chiếu → thành module), tactical_board +
breaking_news (build → render → soi mắt → sửa bug → nhập taxonomy trong 1 buổi).

## Mở rộng
Thêm loại card mới: viết 1 hàm `card_<tên>(img, d, spec)` rồi khai vào dict `RENDER`. Cần card ĐỘNG
(số đếm lên, thanh mọc dần) → sinh chuỗi frame + ghép ffmpeg (khung sẵn có, chưa bật mặc định).
Bản đồ quốc gia tô cờ (flag-map) → dùng `style_flagmap.py`/`flagmap_equirect.py` bên
`sudia-tim-tai-nguyen`/`sudia-bay-google-earth`, không làm ở đây.

## Tự học & tài nguyên (luật não gốc — áp từ 30/07/2026)

Skill này tuân 2 luật chung trong `~/.claude/CLAUDE.md`:

**1. Tự học – tự nâng cấp liên tục:**
- Trước khi chạy: đọc `BRAIN.md` cạnh SKILL.md này và áp bài học cũ.
- Sau khi chạy: tự phân tích kết quả (đúng gì, lệch gì, người dùng sửa gì) → cập nhật `BRAIN.md` ngay, không chờ nhắc.
- Hai ngăn: bài học chắc đúng → ghi thẳng `BRAIN.md`; chưa chắc hoặc nhạy cảm (tiền, khách hàng, pháp lý) → ghi `hoc-cho-duyet.md` chờ anh duyệt rồi mới nhập BRAIN.
- Nếu skill đã có cơ chế học riêng (hồ sơ, máy học, sổ...) thì BRAIN.md bổ sung, không thay thế.

**2. Hiệu quả tối đa – tài nguyên tối thiểu:**
- Việc cơ khí/dễ → giao agent model thấp (haiku); việc vừa → sonnet; chỉ việc khó/sáng tạo/quyết định quan trọng mới dùng model cao.
- Code trước, model sau: việc script/lệnh làm được thì chạy script, không đốt token model.
- Đọc chắt lọc: chỉ đọc phần cần, ưu tiên bản đúc kết (wiki/sổ/state) thay vì nguồn thô; không quét lại cái đã đánh dấu xong.
