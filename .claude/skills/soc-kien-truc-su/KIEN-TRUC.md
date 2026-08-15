# BẢN ĐỒ HỆ THỐNG — Sóc Bóng Đá 247
> Cập nhật 10/08/2026. Kiến trúc đổi thì SỬA FILE NÀY NGAY — bản đồ lệch thực địa còn
> nguy hơn không có bản đồ.

## 1. DÂY CHUYỀN (nhìn từ việc của anh)

```
săn tin / anh paste tin từ GPT
   → DUYỆT LỜI trên trạm  ─┬─ soát chính tả
                           ├─ ĐỌC TIN → ho-so-bai.json      ← trích thực thể
                           ├─ gợi từ khoá từng câu
                           ├─ gợi thẻ số liệu · card đồ hoạ
                           ├─ tìm sẵn ảnh web (ung-vien.json)
                           └─ GÁN NHÁP mọi ô + mắt máy kiểm
   → anh DUYỆT ẢNH (trạm) ─┬─ dải kho nhà · ⚡ gán nhanh (phím 1–8)
                           └─ 🧠 máy xếp theo nghĩa
   → CHỐT (_duyet)        ─┬─ cổng watermark · cổng nháp
                           ├─ chon/ + ban-do-cau.json + blueprint.json
                           └─ HỌC: ghi cặp câu↔ảnh vào hoc-ghep.jsonl
   → XƯỞNG DỰNG (xuong.py) → video.mp4
   → 📦 XẾP KHO (buoc3_xepkho.py) → hộp 7 tệp trên Drive + nhập ảnh vào kho chung
```

## 2. MÁY MÓC (`~/socbongda247/`)

| File | Dòng | Việc |
|---|---:|---|
| `tram/tram_tai_nguyen.py` | ~4200 | **Server trạm** cổng 8756 — 9 route GET, 49 route POST. Trái tim hệ. |
| `tram/tram-tai-nguyen.html` | ~3700 | Trang trạm chính: duyệt lời · gán ảnh · dải kho · ⚡ gán nhanh |
| `tram/tram-chon-anh.html` | ~630 | Trang chọn ảnh riêng cho từng cảnh |
| `tram/kho-nha-duyet.html` | ~830 | Trang duyệt nhãn kho chung (ảnh + video) |
| `tram/menu.js` | 55 | Menu chung mọi trang 8756 (luật: trang mới phải nhúng) |
| `tram/extension/` | ~330 | **TIỆN ÍCH CHROME** "Sóc — gắp ảnh về kho" (v1.4). `nen.js` chạy nền: 4 mục chuột phải + **2 phím tắt** (Alt+S kho việc · Alt+A kho chung, dò ảnh dưới con trỏ bằng `:hover`) · `lop-chon.js` lớp chọn nhiều ảnh · `bang.js` bảng popup đổi việc. **Mọi đường gửi ảnh đều phải đi qua `guiAnh`/`guiAnhKho`** — cấm fetch thẳng cửa trạm. Canh bằng `kiem_tram.py` ⑧ |
| `tram/gap_anh.py` | ~600 | **Gắp ảnh bằng trình duyệt thật** — tìm Google · bóc bài báo (kèm caption) · tải theo URL. **DÙNG CHUNG 4 nơi.** |
| `tram/cdp.py` | 326 | Điều khiển Chrome qua DevTools Protocol |
| `xuong.py` | ~1060 | **Xưởng dựng video** — ráp cảnh, thẻ, card, chuyển động |
| `chuyen_dong.py` | ~800 | Ken Burns · khung đôi · clip · thẻ số liệu |
| `nhip_canh.py` | 76 | **Nhịp cảnh DÙNG CHUNG** trạm ↔ xưởng (mượn trước, chia sau) |
| `chuan_ten.py` | 274 | **Chuẩn hoá + gộp tên chủ thể** (dùng chung 3 nơi) |
| `nhap_kho_chu_the.py` | ~520 | Nhập ảnh vào kho chung + gắn nhãn mắt máy + soát sonnet |
| `nhap_kho_video.py` | 241 | Tải video → tách cảnh → gắn nhãn |
| `xoa_wm.py` | 130 | Xoá watermark bằng LaMa (venv riêng, vá mảnh) |
| `buoc3_xepkho.py` | 217 | Đóng gói 7 tệp → Drive + nhập kho ảnh |
| `kiem_tram.py` | ~360 | **BỘ KIỂM HỒI QUY** — cú pháp · bẫy cũ · chính-phụ · route · luồng · nhạc · phong cách · **extension** (⑧, thêm 14/08). Chạy trước khi báo xong |
| `duong_dan.py` | 197 | Mọi đường dẫn khai MỘT chỗ |

## 3. KHO DỮ LIỆU

| Nơi | Ổ | Chứa |
|---|---|---|
| `/Volumes/DATA/socbongda247/viec/<ngày>/<mã bài>/` | DATA | thư mục VIỆC: kịch bản, giọng, ảnh, clip, sổ |
| `/Volumes/DATA/socbongda247/kho-tai-nguyen/anh-chu-the/` | DATA | **kho ảnh dùng chung** (~650 tấm) + `so-chu-the.jsonl` · `van-tay.json` · `hoc-ghep.jsonl` |
| `…/kho-tai-nguyen/video-chu-the/` | DATA | kho video (~114 đoạn) |
| `…/kho-tai-nguyen/*.json/.md` | DATA | **NÃO**: `luat-ghep-anh.md` · `tu-dien-thuc-the.json` · `ho-so-cau-thu.json` · `kien-thuc-tuyen-qg.json` |
| `…/Drive của tôi/…/kho-video-thanh-pham/` | **DRIVE** | hộp video HOÀN THÀNH (7 tệp/hộp) |

**Sổ trong mỗi việc** (`anh/`): `tram.json` (bản đồ gán — trường mới phải khai vào
`_luu_nhap`) · `ho-so-bai.json` · `ung-vien.json` · `kho-xep.json` · `so-gap.jsonl` ·
`clip-canh.json` · `ban-do-cau.json` · `blueprint.json`

### Nhạc nền (dựng 12/08/2026)
- **Kho**: `kho-tai-nguyen/SOC_BONG_DA_247_MUSIC_LIBRARY/` — 12 nhóm CẢM XÚC, 65 bản ghi
  Mixkit (88 tên file, chênh là liên kết cứng cho bài hợp nhiều nhóm), mọi bài chấm ≥8.0.
  Hồ sơ bản quyền + CSV nằm ở `00_DATABASE/`.
- **Cầu chọn**: `chon_nhac.py` — NÃO MỘT NGUỒN cho việc chọn nhạc. Dò cảm xúc từ tiêu đề +
  lời bình bằng luật cứng (0 token), 4 tầng dự phòng nên không bao giờ trả rỗng.
  Thứ tự ưu tiên: `nhom_nhac` trong blueprint (anh chốt tay) → `cung_nhac` cũ (quy đổi) → tự dò.
- **Xưởng** `xuong.py` chỉ gọi `CN.chon(kb, viec)`, KHÔNG tự glob kho nhạc.
- **Kho CŨ** `kho-tai-nguyen/nhac/` (7 cung, 21 file) giữ nguyên làm lưới đỡ tầng 4.
- **Cổng canh**: `kiem_tram.py` tầng ⑥.

### Phong cách video — chống dập khuôn (12/08/2026)
- **Cấu hình**: `kho-tai-nguyen/phong-cach.json` · trang `/phong-cach` trên trạm.
- **Module**: `phong_cach.py` — anh đặt DẢI, `cho_video(viec)` rút giá trị tất định theo mã
  việc. Biên cứng trong `NUM` chặn giá trị điên. Tắt `bat` thì mọi video dùng giữa dải.
- **Xưởng** đọc ở đầu `dung()`: zoom · trượt · lệch tâm · trần một kiểu · nhóm nhạc ·
  âm lượng + fade nhạc · tốc độ giọng. Không còn hằng số cứng cho mấy thứ này.
- **Cổng canh**: `kiem_tram.py` tầng ⑦.

## 4. CỔNG GÁC (đừng mở cửa sau)

| Cổng | Ở đâu | Chặn gì |
|---|---|---|
| Watermark | `_duyet()` | ảnh mang dấu nguồn bên khác lên hình |
| Nháp ◌ | `_duyet()` | cảnh máy gán mà anh chưa xem |
| Vân tay | `gap_anh._tai_mot` | ảnh trùng trong bài; trùng thì TRỎ VỀ tấm cũ (không báo hỏng) |
| Trùng kho | `_trung_kho()` | máy tải về tấm đã có trong kho chung |
| Đội lạ / áo CLB | `_kho_nha_bai()` | ảnh sai đội, sai thân phận (Luật 1) |
| Một-LaMa-một-lúc | `WM_KHOA` | hai tiến trình nặng song song (đã gây sập nguồn) |

## 5. QUYỀN & MÔI TRƯỜNG (bẫy của máy này)

- **Drive bị TCC chặn với shell của phiên Claude.** Ghi vào `~/.claude/skills/` hay
  Drive phải đi qua **launchd one-shot plist** chạy `/opt/homebrew/bin/python3`.
- **`claude` CLI không gọi lồng được từ phiên Claude Code** (EPERM) — server trạm chạy
  trong launchd nên gọi được.
- **pip/venv phải `cd /tmp` trước** (cwd nằm trong Drive bị chặn thì pip crash).
- Trạm: `launchctl kickstart -k gui/501/com.socbongda247.tram`, log `/tmp/tram.log`.
  **Chỉ restart khi xưởng rảnh** (`pgrep -f xuong.py`).
- Test giao diện bằng CDP: trạm chính đọc **`?viec=`**, KHÔNG phải `?ma=`.
