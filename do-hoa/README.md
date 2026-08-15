# 🎨 Bộ công cụ đồ hoạ / edit ảnh — kênh bóng đá

Bộ công cụ tách từ skill `lam-card-do-hoa` để mang sang **trạm/kênh mới** (bóng đá short).
Tự chứa: đã kèm **font tiếng Việt**, **cờ**, **template**, **sổ tay**. Chỉ cần venv có sẵn là chạy được ngay.

## ⚙️ Chạy bằng đâu (QUAN TRỌNG)
Các tool cần `pillow + numpy + ffmpeg` (riêng spotlight/stat/quote/focus cần thêm `rembg`).
Đã có sẵn venv chung ở máy: `~/.cache/claude-earth-venv`. Gọi tool bằng python của venv đó:
```bash
~/.cache/claude-earth-venv/bin/python scripts/<tên_tool>.py ...
```
> ⚠️ **ĐỪNG tách rời `scripts/` khỏi `assets/`.** Các tool nạp font/cờ theo đường dẫn tương đối
> (`../assets/fonts`, `../assets/flags`). Giữ nguyên cây thư mục, nếu không chữ tiếng Việt sẽ thành ô vuông.

## 📦 Cấu trúc
```
bo-do-hoa-bongda/
├── scripts/            11 công cụ (.py)
├── assets/fonts/       BeVietnamPro (Black/Bold/SemiBold/Regular) + Oswald  ← chữ TV
├── assets/flags/       cờ (br, gb-eng, no) — thêm cờ khác vào đây theo mã ISO
├── references/mau-card.json   mẫu đầy đủ các loại card
├── samples/            mẫu đã render sẵn để xem minh hoạ
├── chay_mau.sh         chạy lại toàn bộ mẫu (kiêm ví dụ cách gọi)
├── SOTAY_SKILL.md      sổ tay gốc (cách dùng chi tiết + triết lý)
└── SOTAY_BRAIN.md      bài học đúc kết từ kênh gốc
```

## 🧰 11 công cụ

**Card tĩnh (PNG) — `render_card.py`** — 1 file lo mọi loại card số liệu:
`versus` (đối đầu, có cờ + tỉ số) · `stat` (1 số khổng lồ) · `leaderboard` (bảng xếp hạng có thanh) ·
`timeline` (dòng thời gian) · `compare` (so sánh thanh ngang).
```bash
~/.cache/claude-earth-venv/bin/python scripts/render_card.py cards.json     # mảng card
# xem mẫu đủ trường: references/mau-card.json
```

**Clip động (MP4):**
| Tool | Làm gì | Gọi mẫu |
|---|---|---|
| `player_spotlight.py` ⭐ | Ảnh cầu thủ **xoá nền** trên lưới đen chuyển động + quầng sáng + zoom | `--player "Erling Haaland" --out out.mp4 --accent "#e11d2a"` |
| `breaking_news.py` | Card **tin nóng** động (headline đập + ticker chạy) | `tin.json -o tin.mp4` |
| `quote_spotlight.py` | Card **câu trích dẫn** (ảnh + quote hiện từng dòng + tác giả) | `--photo a.png --quote "..." --author "..." --bg "#0b1f3a"` |
| `stat_bubbles.py` | Người + **số liệu đếm lên** cùng khung (bong bóng) | `--photo a.png --stat "36:Bàn thắng" --out out.mp4` |
| `lineup_board.py` | **Sa bàn đội hình** (cầu thủ pop-in theo vị trí) | `doi_hinh.json -o dh.mp4` |
| `tactical_board.py` | **Sơ đồ chiến thuật** động (kể pha bóng bằng sân 2D) | `pha_bong.json -o pha.mp4` |
| `annotate_footage.py` | **Telestrator** — vẽ mũi tên/vòng phân tích đè lên footage | `footage.mp4 -o out.mp4` |
| `focus_pop.py` | Làm **nổi chủ thể** trên chính ảnh đó (bokeh + parallax) | `--photo a.jpg --out out.mp4` |
| `film_look.py` | **Chỉnh màu điện ảnh + biến đổi** footage (hỗ trợ né bản quyền) | `footage.mp4 --manh 0.8` |
| `kiem_render.py` | Tiện ích **soi/kiểm** render (QC) | — |

> Cách viết các file JSON spec (`tin.json`, `doi_hinh.json`, `pha_bong.json`…): xem **`SOTAY_SKILL.md`**.

## 🔁 Lưu ý đồng bộ
Đây là BẢN COPY tại thời điểm mang sang. Skill gốc `lam-card-do-hoa` nếu về sau nâng cấp thì bản này
KHÔNG tự cập nhật — khi cần bản mới, copy lại `scripts/` + `assets/` từ skill gốc.

## 🎬 Xem minh hoạ
Mở thư mục `samples/` (đã render sẵn vài mẫu). Chạy lại tất cả: `bash chay_mau.sh`.
