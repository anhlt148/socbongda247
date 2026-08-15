#!/usr/bin/env python3
"""Ghi BRAIN đợt 11/08: cảnh phụ đủ chức năng + 5 phương án thay + bug import shadow."""
import os

BRAIN = os.path.expanduser("~/.claude/skills/soc-tai-nguyen/BRAIN.md")
BAI = """
## 11/08/2026 — cảnh phụ đủ chức năng · 5 phương án thay · bẫy import shadow (LẶP LẠI)

- **BẪY IMPORT SHADOW TÁI PHẠM** (đã ghi 10/08 mà vẫn dính): thêm `import base64` trần
  trong một nhánh của `do_POST` → base64 thành biến CỤC BỘ CẢ HÀM → nhánh /api/tai-len
  chạy trước là UnboundLocalError, **extension chết hẳn đường gửi ảnh** mà không ai báo.
  Đã dọn SẠCH mọi import cục bộ đè module toàn cục trong file và có SCRIPT QUÉT:
  ast.walk tìm Import/ImportFrom trong FunctionDef mà tên trùng import ở col_offset 0.
  → Luật: KHÔNG bao giờ import trong thân hàm nếu module đã có ở đầu file. Chạy quét
  này sau mỗi lần thêm route mới.
- **Chẩn 500 của trạm**: log launchd /tmp/tram.log có thể toàn BrokenPipe (nhiễu, do
  client đóng sớm). Muốn thấy traceback THẬT: ghi mốc `wc -l` trước, gọi lại API, rồi
  `tail -n +mốc`. Nhanh hơn nữa: body 500 của trạm đã kèm sẵn trường "vet".
- **Cảnh phụ có mọi chức năng như cảnh chính** (anh chốt 11/08 — họ luật "cảnh chính có
  gì cảnh phụ có nấy"): ô TỪ KHOÁ RIÊNG + 🔎 tìm + 🏠 kho nhà + ghi chú + 🎴 card. Sổ
  mới `tu_khoa_phu`/`ghi_chu_phu` {câu: {ô: ...}} (nhớ khai vào whitelist _luu_nhap +
  _nhap + _chi_tiet, thiếu một chỗ là mất khi lưu). moKhoNha(cau, phan) và trang chọn
  nhận `&phan=` → gán vào ô phụ; /api/tim-san thêm tham số `tu_khoa` để tìm theo từ
  khoá riêng của ô phụ. KHÔNG thêm thẻ số liệu cho ô phụ vì thẻ chạy theo CÂU (đã phủ).
- **5 PHƯƠNG ÁN THAY THẾ** (/api/phuong-an): dải trên đầu cột kho, theo ô ĐANG chọn —
  kho nhà trước (rẻ, có nhãn) rồi bù ảnh web tìm sẵn, loại mọi tấm đang dùng trong bài.
  Bấm một tấm = nhận về bài + thay ảnh ô đó + cờ ◌ nháp tự rơi. Cache theo khoá
  `ma|cau|phan` để đổi cảnh mới gọi lại, không hỏi server mỗi lần vẽ.
"""

with open(BRAIN, "a", encoding="utf-8") as f:
    f.write(BAI)
print("Đã ghi BRAIN:", BRAIN)
