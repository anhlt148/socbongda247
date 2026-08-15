#!/usr/bin/env python3
"""LỌC ẢNH LẠC ĐỀ — soi NỘI DUNG ảnh, không chỉ đo kích thước.

Anh phản ánh 05/08: "có những ảnh không liên quan vẫn được đưa vào kho ứng viên". Đúng —
cổng cũ chỉ đo rộng/cao/tỉ lệ và dò watermark, tức là nó mù về nội dung. Google trả về theo
từ khoá nhưng trong trang có cả ảnh quảng cáo, ảnh khối "tìm kiếm liên quan", ảnh bãi biển,
ảnh chăm sóc da… và tất cả đều lọt qua vì chúng đủ to.

Cách làm (theo luật "hiệu quả tối đa – tài nguyên tối thiểu"):
  · KHÔNG hỏi model từng ảnh một. Xếp cả lô thành MỘT BẢNG có đánh số rồi hỏi MỘT lượt.
    Đo thật: 12 ảnh, một lượt haiku, 31 giây.
  · Dùng **haiku** — phân biệt "ảnh bóng đá" với "ảnh bãi biển" là việc dễ.

Hai điều KHÔNG làm, có chủ ý:
  · KHÔNG bảo model đoán mặt cầu thủ. Sổ dự án ghi rõ: Claude không nhận diện cầu thủ qua
    khuôn mặt. Nó chỉ được phép nói ảnh này CÓ PHẢI bóng đá không, có phải quảng cáo không.
  · KHÔNG xoá ảnh bị chấm lạc đề. Model vẫn sai được — ví dụ nó chấm ảnh bảng xếp hạng là
    "chụp màn hình chữ", trong khi video nói "leo lên đỉnh bảng A" thì tấm đó lại dùng được.
    Nên chỉ DÁN NHÃN và đẩy xuống cuối kho; người vẫn bật lên xem được.

Chạy tay:  python3 loc_anh.py <thư mục anh> "<chủ đề video>"
"""
import glob
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

CLAUDE = os.path.expanduser("~/.local/bin/claude")
MODEL = "claude-haiku-4-5-20251001"
O, COT = 260, 5                                    # cỡ ô và số cột trong bảng gửi model
LO = 20                                            # mỗi lượt hỏi tối đa ngần này ảnh
HAN_GIO = 180

LOI_DAN = """Đọc ảnh {bang}. Đó là lưới ảnh, mỗi ô có SỐ màu vàng ở góc trên bên trái.

Video sắp làm nói về: "{chu_de}"

Cho tôi biết ô nào KHÔNG dùng được cho video này. CHỈ tính thứ RÕ RÀNG lạc đề:
  · không phải bóng đá (phong cảnh, đồ ăn, chăm sóc da, thời trang, xe cộ, bất động sản…)
  · ảnh quảng cáo, ảnh bìa sản phẩm, ảnh có khung viền tiếp thị
  · ảnh chụp màn hình toàn chữ, ảnh biểu đồ khô khan
  · môn thể thao KHÁC bóng đá
  · ảnh quá mờ, quá tối, hoặc là ảnh ghép nhiều ô nhỏ

TUYỆT ĐỐI KHÔNG đoán xem người trong ảnh là cầu thủ nào. Bạn không nhận ra mặt người, và
đoán bừa thì hại hơn không đoán. Ảnh cứ là bóng đá thì để người tự soi số áo.
Còn phân vân thì cho là DÙNG ĐƯỢC — thà để lọt một tấm thừa còn hơn vứt mất tấm đúng.

Trả về DUY NHẤT một mảng JSON, đủ mọi ô, không giải thích gì thêm:
[{{"o": 1, "lac_de": true, "vi_sao": "ảnh bãi biển"}}, {{"o": 2, "lac_de": false, "vi_sao": ""}}]"""


def _lam_bang(ds, ra):
    """Xếp ảnh thành bảng có đánh số. Một ảnh để model nhìn, rẻ hơn nhiều so với gửi từng tấm."""
    hang = (len(ds) + COT - 1) // COT
    bang = Image.new("RGB", (COT * O, hang * (O + 28)), (16, 16, 18))
    d = ImageDraw.Draw(bang)
    try:
        f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 24)
    except Exception:
        f = ImageFont.load_default()
    for i, p in enumerate(ds):
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            continue
        im.thumbnail((O - 8, O - 8), Image.LANCZOS)
        x, y = (i % COT) * O, (i // COT) * (O + 28)
        bang.paste(im, (x + 4, y + 28 + (O - 8 - im.height) // 2))
        d.text((x + 7, y + 2), str(i + 1), font=f, fill=(255, 212, 0))
    bang.save(ra, quality=84)
    return ra


def _hoi(bang, chu_de):
    r = subprocess.run([CLAUDE, "-p", "--model", MODEL, "--allowedTools", "Read"],
                       input=LOI_DAN.format(bang=bang, chu_de=chu_de),
                       capture_output=True, text=True, timeout=HAN_GIO)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "claude -p lỗi")[-300:])
    chu = re.sub(r"^```(?:json)?|```$", "", r.stdout.strip(), flags=re.M).strip()
    i, j = chu.find("["), chu.rfind("]")
    if i < 0 or j < 0:
        raise ValueError("model không trả mảng JSON")
    return json.loads(chu[i:j + 1])


def soi(thu_muc, chu_de, chi_moi=True, bao_tien=None):
    """Chấm nhãn lạc đề cho ảnh trong kho. Kết quả ghi `lac-de.json` = {tên tệp: {...}}."""
    p_ra = os.path.join(thu_muc, "lac-de.json")
    da = {}
    if os.path.exists(p_ra):
        try:
            da = json.load(open(p_ra, encoding="utf-8"))
        except Exception:
            da = {}
    ds = sorted(glob.glob(os.path.join(thu_muc, "*.jpg")))
    ds = [p for p in ds if not os.path.basename(p).startswith("_")]
    if chi_moi:                                    # đã chấm rồi thì thôi, đừng hỏi lại
        ds = [p for p in ds if os.path.basename(p) not in da]
    if not ds:
        return {"da_soi": 0, "lac_de": 0, "loi": ""}

    tmp = os.path.join(thu_muc, "_bang-loc.jpg")
    soi_duoc, lac = 0, 0
    for k in range(0, len(ds), LO):
        lo = ds[k:k + LO]
        try:
            _lam_bang(lo, tmp)
            kq = _hoi(tmp, chu_de)
        except Exception as e:
            return {"da_soi": soi_duoc, "lac_de": lac, "loi": str(e)}
        for m in kq:
            i = int(m.get("o", 0)) - 1
            if not (0 <= i < len(lo)):
                continue
            ten = os.path.basename(lo[i])
            da[ten] = {"lac_de": bool(m.get("lac_de")),
                       "vi_sao": str(m.get("vi_sao", ""))[:80]}
            soi_duoc += 1
            lac += bool(m.get("lac_de"))
        if bao_tien:
            bao_tien(min(k + LO, len(ds)), len(ds))
    os.path.exists(tmp) and os.remove(tmp)
    json.dump(da, open(p_ra, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"da_soi": soi_duoc, "lac_de": lac, "loi": ""}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("dùng: loc_anh.py <thư mục anh> \"<chủ đề video>\"")
    r = soi(sys.argv[1], sys.argv[2], chi_moi="--lai" not in sys.argv)
    print(f"soi {r['da_soi']} ảnh · {r['lac_de']} tấm lạc đề"
          + (f" · lỗi: {r['loi']}" if r["loi"] else ""))
