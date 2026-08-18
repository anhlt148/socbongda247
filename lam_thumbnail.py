#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ẢNH BÌA (THUMBNAIL) cho video Shorts — anh đặt 18/08.

Anh gửi 20 ảnh bìa của kênh dẫn đầu ngách và bảo "học cách tạo thum ấn tượng".
Mổ ra thì công thức của họ gồm SÁU phần, và năm phần hệ mình ĐÃ CÓ SẴN:

  ① DẢI CHỮ ĐỎ–CAM chiếm ~30% đáy, gradient dọc + hoa văn sân mờ   ✅ có
  ② CHỮ IN HOA đậm nghiêng, 2–3 dòng, canh trái                     ✅ có
  ③ CỤM TÔ VÀNG — điểm nhấn mạnh nhất, mắt bắt vào đó trước         ✅ có
  ④ THANH DỌC TRẮNG mảnh bên trái chữ                               ✅ có
  ⑤ WATERMARK mờ ở đáy                                              ✅ có
  ⑥ BỐ CỤC ẢNH bên trên — thứ DUY NHẤT còn thiếu                    ← file này lo

Năm phần đầu chính là bộ `lam_overlay` xưởng vẫn vẽ lên video, nên ảnh bìa dùng lại
nguyên si: bìa và video cùng một khuôn mặt, người xem nhận ra kênh ngay.

BỐN KIỂU BỐ CỤC ẢNH đọc được từ 20 mẫu, máy tự chọn theo nội dung bài:

  A · MỘT NGƯỜI CẬN CẢNH   — bài về một nhân vật. Ảnh dọc, mặt to, cắt từ ngực lên.
  B · ĐỐI ĐẦU (VS)         — bài có hai phe. Chia đôi theo đường CHÉO, mỗi bên một
                             người/đội, vạch sáng ở giữa. Kiểu ăn khách nhất của họ.
  C · GHÉP HAI KHUNG NGANG — bài kể hai chuyện. Trên/dưới, vạch ngăn mảnh.
  D · LƯỚI BỐN Ô           — bài điểm tin nhiều nhân vật.

Chọn kiểu là việc RẺ: đọc hồ sơ bài (mấy đội, mấy nhân vật) rồi quyết bằng code.
Không gọi model — bố cục là luật, không phải phán đoán.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD

TPL = DD.nap_template()
W, H = TPL.CANVAS["W"], TPL.CANVAS["H"]
L, MAU = TPL.LAYOUT, TPL.MAU
# Ảnh phủ tới đúng mép dải chữ mà TEMPLATE quy định — đọc từ template chứ đừng đoán,
# không thì bìa hở một vệt mờ giữa ảnh và dải chữ (QC bắt ngay lượt thử đầu).
TY_ANH = float(L.get("hoa_den_ty_le", 0.70)) + 0.015


def _mo(p):
    im = Image.open(p).convert("RGB")
    return im


def _phu_khung(im, w, h):
    """Phủ kín khung w×h, cắt phần thừa — KHÔNG bóp méo người."""
    tw, th = im.size
    ty = max(w / tw, h / th)
    im = im.resize((max(1, int(tw * ty)), max(1, int(th * ty))), Image.LANCZOS)
    x = (im.width - w) // 2
    # cắt lệch LÊN TRÊN một chút: mặt người thường ở phần trên khung, cắt giữa
    # là chặt mất trán hoặc lấy nhiều cỏ (đo trên 20 mẫu của họ)
    y = max(0, int((im.height - h) * 0.32))
    return im.crop((x, y, x + w, y + h))


def _nen_mo(im, w, h):
    """Nền mờ cho ảnh không đủ phủ — thà mờ còn hơn viền đen."""
    n = _phu_khung(im, w, h).filter(ImageFilter.GaussianBlur(28))
    return Image.eval(n, lambda v: int(v * 0.72))


def bo_cuc_A(anh, w, h):
    return _phu_khung(_mo(anh[0]), w, h)


def bo_cuc_B(anh, w, h):
    """ĐỐI ĐẦU: chia đôi theo đường CHÉO + vạch sáng giữa (kiểu ăn khách nhất)."""
    ra = Image.new("RGB", (w, h), (12, 10, 10))
    trai = _phu_khung(_mo(anh[0]), int(w * 0.60), h)
    phai = _phu_khung(_mo(anh[1]), int(w * 0.60), h)
    ra.paste(trai, (0, 0))
    # mặt nạ chéo cho ảnh phải
    mn = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mn)
    d.polygon([(int(w * 0.46), h), (int(w * 0.56), 0), (w, 0), (w, h)], fill=255)
    ra.paste(phai, (w - phai.width, 0), mn.crop((w - phai.width, 0, w, h))
             .resize(phai.size))
    # vạch sáng ở đường chia
    v = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(v).line([(int(w * 0.46), h), (int(w * 0.56), 0)],
                           fill=(255, 232, 150, 210), width=9)
    ra = Image.alpha_composite(ra.convert("RGBA"),
                               v.filter(ImageFilter.GaussianBlur(3))).convert("RGB")
    return ra


def bo_cuc_C(anh, w, h):
    """Hai khung ngang trên/dưới, vạch ngăn mảnh."""
    ra = Image.new("RGB", (w, h), (12, 10, 10))
    cao = (h - 6) // 2
    ra.paste(_phu_khung(_mo(anh[0]), w, cao), (0, 0))
    ra.paste(_phu_khung(_mo(anh[1]), w, h - cao - 6), (0, cao + 6))
    ImageDraw.Draw(ra).rectangle([0, cao, w, cao + 6], fill=(248, 242, 232))
    return ra


def bo_cuc_D(anh, w, h):
    """Lưới bốn ô — bài điểm tin nhiều nhân vật."""
    ra = Image.new("RGB", (w, h), (12, 10, 10))
    cw, ch = (w - 5) // 2, (h - 5) // 2
    for i, p in enumerate(anh[:4]):
        x = (i % 2) * (cw + 5)
        y = (i // 2) * (ch + 5)
        ra.paste(_phu_khung(_mo(p), cw, ch), (x, y))
    return ra


BO_CUC = {"A": bo_cuc_A, "B": bo_cuc_B, "C": bo_cuc_C, "D": bo_cuc_D}


# Từ khoá cho biết trong ảnh CÓ NGƯỜI — đọc từ mô tả mắt máy đã chấm sẵn lúc nhập kho.
# QC 18/08 bắt được: bìa lấy phải ảnh MÀN HÌNH LED "VAR CHECKING" làm nửa bên phải —
# to, nét, đúng tỷ lệ nên điểm cao, mà chẳng có mặt người nào. Bìa sống bằng KHUÔN MẶT:
# 20/20 mẫu của kênh dẫn đầu đều có ít nhất một gương mặt rõ.
CO_NGUOI = ("cầu thủ", "người", "hlv", "huấn luyện", "trọng tài", "cổ động",
            "khán giả", "fan", "đội hình", "ăn mừng", "mặt", "gương mặt", "chân dung")
KHONG_NGUOI = ("bảng điện", "màn hình", "led", "bảng tỷ số", "logo", "biểu tượng",
               "sân vận động trống", "cỏ", "khán đài trống", "đồ hoạ", "infographic")


def _diem_anh(p, mo_ta=""):
    """Ảnh nào đáng lên bìa: CÓ NGƯỜI · to · nét · khung dọc. Thuần code, 0 token."""
    try:
        with Image.open(p) as im:
            w, h = im.size
    except Exception:
        return -1
    if w < 500 or h < 500:
        return -1
    d = min(w * h / 2_500_000.0, 1.0) * 55
    ty = w / h
    d += 30 if ty <= 1.2 else 20 if ty <= 1.6 else 8 if ty <= 2.1 else 0
    t = (mo_ta or "").lower()
    if any(k in t for k in CO_NGUOI):
        d += 45                      # có người là điều kiện gần như bắt buộc của bìa
    if any(k in t for k in KHONG_NGUOI):
        d -= 40                      # bảng điện, đồ hoạ: nét đẹp mà bìa nhìn nhạt
    return d


def _chon_anh(viec, can):
    """Lấy `can` ảnh đẹp nhất của bài — ưu tiên ảnh ĐÃ GÁN CẢNH ĐẦU.

    Cảnh đầu là cảnh giữ người xem, ảnh của nó thường là tấm anh chọn kỹ nhất. Sau đó
    mới tới các tấm khác xếp theo điểm. Không lấy trùng.
    """
    thu = os.path.join(viec, "anh")
    if not os.path.isdir(thu):
        return []
    uu = []
    try:
        nh = json.load(open(os.path.join(thu, "tram.json"), encoding="utf-8"))
        bd = nh.get("ban_do") or {}
        for k in sorted(bd, key=lambda x: int(x)):
            v = str(bd[k] or "")
            if v and "::" not in v:          # bỏ clip, bìa cần ảnh tĩnh
                uu.append(os.path.join(viec, v) if not os.path.isabs(v) else v)
    except Exception:
        pass
    # MÔ TẢ MẮT MÁY của từng tấm — đã chấm sẵn lúc nhập kho, đọc lại không tốn gì
    mt = {}
    p_sn = os.path.join(thu, "so-nguon.jsonl")
    if os.path.exists(p_sn):
        for dong in open(p_sn, encoding="utf-8"):
            try:
                d_sn = json.loads(dong)
                mt[d_sn.get("tep", "")] = " ".join(str(d_sn.get(k, "")) for k in
                                                   ("mo_ta", "chu_the", "nhan", "tu_khoa"))
            except Exception:
                pass
    con = sorted((os.path.join(thu, f) for f in os.listdir(thu)
                  if f.lower().endswith((".jpg", ".jpeg", ".png"))
                  and not f.startswith("_")),
                 key=lambda q: _diem_anh(q, mt.get(os.path.basename(q), "")),
                 reverse=True)
    ra = []
    for p in uu + con:
        if p not in ra and os.path.exists(p) \
                and _diem_anh(p, mt.get(os.path.basename(p), "")) > 0:
            ra.append(p)
        if len(ra) >= can:
            break
    return ra


def _kieu_bo_cuc(viec, so_anh):
    """Chọn kiểu bố cục bằng LUẬT, không gọi model.

    Hai phe (bài có hai đội) → ĐỐI ĐẦU, kiểu ăn khách nhất của họ.
    Nhiều nhân vật → lưới bốn ô. Còn lại: một người cận cảnh nếu chỉ có một ảnh đẹp.
    """
    hs = {}
    try:
        hs = json.load(open(os.path.join(viec, "anh", "ho-so-bai.json"),
                            encoding="utf-8"))
    except Exception:
        pass
    doi = [x for x in (hs.get("doi") or []) if x]
    nv = [x for x in (hs.get("nhan_vat") or []) if x]
    if len(doi) >= 2 and so_anh >= 2:
        return "B"
    if len(nv) >= 4 and so_anh >= 4:
        return "D"
    if so_anh >= 2 and len(nv) >= 2:
        return "C"
    return "A"


def lam(viec, ra=None, kieu=None):
    """Dựng ảnh bìa cho một bài. Trả đường dẫn tệp đã ghi."""
    kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    tit = (kb.get("tieu_de") or "").strip()
    if not tit:
        raise RuntimeError("bài chưa có tiêu đề — chưa làm bìa được")
    can = 4 if (kieu or "") == "D" else 2
    anh = _chon_anh(viec, max(can, 4))
    if not anh:
        raise RuntimeError("bài không có ảnh nào đủ đẹp để lên bìa")
    kieu = kieu or _kieu_bo_cuc(viec, len(anh))
    if kieu in ("B", "C") and len(anh) < 2:
        kieu = "A"
    if kieu == "D" and len(anh) < 4:
        kieu = "C" if len(anh) >= 2 else "A"

    # ① phần ảnh
    cao_anh = int(H * TY_ANH)
    nen = BO_CUC[kieu](anh, W, cao_anh)
    bia = Image.new("RGB", (W, H), (18, 14, 12))
    bia.paste(nen, (0, 0))
    # nền dưới lấy màu ảnh cho liền mạch, dải chữ sẽ phủ lên
    bia.paste(_nen_mo(_mo(anh[0]), W, H - cao_anh), (0, cao_anh))

    # ② dải chữ + tô vàng + watermark: DÙNG LẠI đúng bộ vẽ của xưởng, để bìa và
    #    video cùng một khuôn mặt (xem chú thích đầu file)
    # ② DẢI CHỮ — dùng lại các LỚP của template (gradient · hoa văn sân · fit chữ ·
    #    watermark) nhưng CANH RIÊNG cho bìa.
    #    Vì sao không gọi thẳng `xuong.lam_overlay`: khuôn ấy vẽ cho VIDEO, chữ nằm sát
    #    mép trên dải và chừa khoảng trống bên dưới cho nội dung chạy. Bìa thì phải LẤP
    #    ĐẦY — 20/20 mẫu của kênh dẫn đầu đều vậy, chữ càng to càng bắt mắt trên lưới
    #    Shorts. Sửa `lam_overlay` là đụng vào video đang chạy tốt, nên tách đường.
    cum = kb.get("cum_to_vang") or []
    y_dai = int(H * float(L.get("hoa_den_ty_le", 0.70))) + 26
    lop = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lop.alpha_composite(TPL._lop_gradient(W, H, y_dai))
    lop.alpha_composite(TPL._lop_hoa_van_san(W, H))
    d = ImageDraw.Draw(lop)
    x_chu = L["le_trai"] + L["thanh_doc_rong"] + L["thanh_doc_cach_chu"]
    rong = W - x_chu - L["le_phai"]
    # bìa được dùng CẢ chiều cao dải (video phải chừa `le_duoi` cho nội dung)
    cao_dung = H - y_dai - 96
    font, dong, cx = TPL._fit_tieu_de(d, tit.upper(), rong, cao_dung)
    cao_dong = int(cx * 1.24)
    y = y_dai + max(28, (cao_dung - cao_dong * len(dong)) // 2)
    # thanh dọc trắng chạy đúng chiều cao khối chữ
    d.rectangle([L["le_trai"], y - 6, L["le_trai"] + L["thanh_doc_rong"],
                 y + cao_dong * len(dong) + 2], fill=MAU["thanh_doc"])
    kho_vang = [c.upper() for c in cum if c]
    for l_i, dg in enumerate(dong):
        x = x_chu
        for tu in dg.split(" "):
            mau = MAU["chu"]
            for cv in kho_vang:
                if tu.strip(".,:;!?\"'“”") and tu.strip(".,:;!?\"'“”") in cv:
                    mau = MAU["chu_nhan"]
                    break
            d.text((x, y + l_i * cao_dong), tu + " ", font=font, fill=mau)
            x += d.textlength(tu + " ", font=font)
    # LOGO KÊNH góc trái trên + WATERMARK đáy phải — hai dấu nhận biết kênh, mẫu nào
    # của họ cũng có. Gọi đúng chữ ký hàm của template (đã đọc, không đoán).
    try:
        _lg = Image.open(DD.LOGO).convert("RGBA").resize(
            (int(W * 0.115),) * 2, Image.LANCZOS)
        lop.alpha_composite(_lg, (L["le_trai"] - 28, 54))
    except Exception as _e:
        print(f"  ⚠ không gắn được logo: {_e}")
    try:
        TPL._ve_watermark(lop, DD.KENH)     # đúng chữ ký xưởng dùng
    except Exception as _e:
        print(f"  ⚠ không vẽ được watermark: {_e}")
    bia = Image.alpha_composite(bia.convert("RGBA"), lop).convert("RGB")

    ra = ra or os.path.join(viec, "thumbnail.jpg")
    bia.save(ra, quality=93, subsampling=0)
    return ra, kieu, len(anh)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Dùng: python3 lam_thumbnail.py <mã việc> [kiểu A|B|C|D]")
    v = DD.tim_viec(sys.argv[1])
    p, k, n = lam(v, kieu=(sys.argv[2].upper() if len(sys.argv) > 2 else None))
    print(f"✅ {p}\n   bố cục {k} · dùng {n} ảnh ứng viên")
