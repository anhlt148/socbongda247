#!/usr/bin/env python3
"""Chép ảnh ĐÃ CHỌN TAY vào thư mục chon/, đánh số theo đúng mạch kể của lời bình.

Vì sao phải làm tay: máy lọc ảnh chỉ biết kích thước và tỉ lệ, nó không biết trong ảnh
là AI và có đúng TRẬN không. Mẻ 30 giây đầu dính đúng lỗi đó — ảnh Văn Hậu, Anh Khoa
lọt vào video nói về Việt Anh, và ảnh trận sân nhà áo đỏ lọt vào tin trận sân khách áo trắng.
Ở đây ảnh xếp theo thứ tự, cảnh một luôn là ảnh nhân vật chính.
"""
import os, shutil, sys

def chep(viec, ds):
    ra = os.path.join(viec, "anh", "chon")
    shutil.rmtree(ra, ignore_errors=True); os.makedirs(ra)
    for i, t in enumerate(ds, 1):
        thu, ten = (t.split("/") if "/" in t else ("anh", t))
        g = os.path.join(viec, thu, ten + ".jpg")
        if not os.path.exists(g):
            print(f"  ! thiếu {t}"); continue
        shutil.copy2(g, os.path.join(ra, f"{i:02d}.jpg"))
    print(f"{os.path.basename(viec)}: {len(os.listdir(ra))} ảnh đã chọn")

V = "viec/2026-08-04-"
# ① VIỆT ANH — mở bằng chính anh (số 20, đầu quấn băng), rồi bám mạch va chạm → đá tiếp → thắng
chep(V + "tay-vietanh", [
    "anh2/a00", "anh/a14", "anh/a21", "anh2/a02", "anh/a22", "anh/a28", "anh/a31",
    "anh2/a00", "anh/a29", "anh/a16", "anh/a13", "anh2/a03", "anh2/a02", "anh/a06",
])
# ② CỬA ĐI TIẾP — trận VN-Indo, rồi chuyển sang cầu thủ Campuchia áo đỏ số 5
chep(V + "tay-cuadi", [
    "anh/a00", "anh/a20", "anh/a21", "anh/a22", "anh/a17", "anh/a50", "anh/a55",
    "anh/a51", "anh/a56", "anh/a23", "anh/a24", "anh/a03", "anh/a16", "anh/a15",
])
# ③ HUBNER — tranh chấp VN-Indo là xương sống, xen ảnh ăn mừng cho đoạn "ba bàn"
chep(V + "tay-hubner", [
    "anh/a13", "anh/a23", "anh/a24", "anh/a26", "anh/a27", "anh/a25", "anh/a21",
    "anh/a12", "anh/a14", "anh/a15", "anh/a56", "anh/a57", "anh/a03", "anh/a30",
])
