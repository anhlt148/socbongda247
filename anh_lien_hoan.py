#!/usr/bin/env python3
"""BẬC 3 CỦA CỔNG BẢN QUYỀN — xếp mọi ảnh sắp dùng lên MỘT tấm để anh liếc một cái.

Vì sao phải có bậc này (đo thực 04/08/2026, không phải phỏng đoán):

  · OCR BỎ SÓT: ảnh dán rõ ràng "@nhipcongtruong" chữ trắng trên nền cỏ — tesseract
    đọc ra "uong" và "YTÀ". Nhìn thấy loang loáng mà không đọc nổi thành chữ.
  · OCR BÁO NHẦM: ảnh cầu thủ Việt Nam ăn mừng bị cờ vàng vì OCR đọc biển quảng cáo
    sân ("A SUSTAINABLE", "KANSAI"). Đó là cảnh thật, không phải dấu dán đè.
  · Trên tám ảnh của một bài báo: hai ảnh sạch, sáu cờ vàng — trong sáu cái đó chỉ
    MỘT là dấu thật (logo FPT Play), còn lại là rác OCR ("LỒỘ", "oun", "gga").

Nên: máy chặn được cái nó ĐỌC RA TÊN (bậc 1) và đánh dấu cái nó nghi (bậc 2), nhưng
quyết định cuối phải là mắt người. Mắt người bắt watermark trong một phần giây — thứ
mà OCR làm sai theo cả hai chiều. Tấm ảnh liên hoàn này làm việc đó tốn 10 giây/video.

Hợp với bài học 6 của kênh: hệ thống tự động chín phần, người bấm nút cuối.

Dùng:
  python3 anh_lien_hoan.py <thư mục ảnh> [ra.png]
"""
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD

O_RONG = 520          # bề ngang mỗi ô
COT = 4
LE = 16
CAO_NHAN = 46

# Bốn góc + giữa: nơi dấu chìm hay nằm. Vẽ khung mờ lên đó để mắt biết nhìn vào đâu.
VUNG_SOI = [(0.00, 0.00, 0.34, 0.16), (0.66, 0.00, 1.00, 0.16),
            (0.00, 0.84, 0.34, 1.00), (0.66, 0.84, 1.00, 1.00),
            (0.30, 0.40, 0.70, 0.60)]


def lam(thu_muc, ra=None):
    so = os.path.join(thu_muc, "nguon-anh.json")
    ghi_chu = {}
    if os.path.exists(so):
        d = json.load(open(so, encoding="utf-8"))
        ghi_chu = {a["tep"]: a.get("can_soi", "") for a in d.get("anh", [])}

    teps = sorted(f for f in os.listdir(thu_muc)
                  if f.lower().endswith((".jpg", ".jpeg", ".png")) and not f.startswith("_"))
    if not teps:
        return None, 0

    tpl = DD.nap_template()
    fnhan = tpl._font(tpl.FONT["title"], 26, 600)
    fnho = tpl._font(tpl.FONT["title"], 20, 400)

    hang = (len(teps) + COT - 1) // COT
    o_cao = int(O_RONG * 0.72)
    W = COT * O_RONG + (COT + 1) * LE
    H = hang * (o_cao + CAO_NHAN) + (hang + 1) * LE + 64
    tam = Image.new("RGB", (W, H), (22, 22, 26))
    d = ImageDraw.Draw(tam)
    d.text((LE, 18), f"SOI BẢN QUYỀN — {len(teps)} ảnh — {os.path.basename(thu_muc)}",
           font=tpl._font(tpl.FONT["title"], 32, 700), fill=(255, 212, 0))

    for i, t in enumerate(teps):
        c, r = i % COT, i // COT
        x = LE + c * (O_RONG + LE)
        y = 64 + LE + r * (o_cao + CAO_NHAN + LE)
        try:
            im = Image.open(os.path.join(thu_muc, t)).convert("RGB")
        except Exception:
            continue
        im.thumbnail((O_RONG, o_cao), Image.LANCZOS)
        ox, oy = x + (O_RONG - im.width) // 2, y + (o_cao - im.height) // 2
        tam.paste(im, (ox, oy))

        # khoanh vùng hay có dấu chìm — hướng mắt, không kết luận thay
        for (a, b, c2, d2) in VUNG_SOI:
            d.rectangle([ox + a * im.width, oy + b * im.height,
                         ox + c2 * im.width, oy + d2 * im.height],
                        outline=(255, 212, 0, 90), width=1)

        nghi = ghi_chu.get(t, "")
        d.rectangle([x, y + o_cao, x + O_RONG, y + o_cao + CAO_NHAN],
                    fill=(70, 55, 0) if nghi else (32, 32, 38))
        d.text((x + 8, y + o_cao + 4), ("🟡 " if nghi else "") + t,
               font=fnhan, fill=(255, 212, 0) if nghi else (225, 225, 225))
        if nghi:
            d.text((x + 8, y + o_cao + 26), nghi[:52], font=fnho, fill=(240, 200, 120))

    ra = ra or os.path.join(thu_muc, "_SOI-BAN-QUYEN.png")
    tam.save(ra)
    return ra, len(teps)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("dùng: anh_lien_hoan.py <thư mục ảnh> [ra.png]")
    p, n = lam(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"{n} ảnh → {p}" if p else "không có ảnh nào trong thư mục")
