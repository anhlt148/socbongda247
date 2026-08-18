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


def _o_tron(nen, anh_ct, w, h):
    """Ô TRÒN góc trên phải chứa vật chứng (thẻ đỏ, bảng VAR, vật lạ).

    Kiểu ③ trong não: ô tròn tạo câu hỏi "cái gì trong đó?" — tò mò mạnh hơn cả tiêu đề.
    """
    d_o = int(w * 0.36)
    ct = _phu_khung(_mo(anh_ct), d_o, d_o)
    mn = Image.new("L", (d_o, d_o), 0)
    ImageDraw.Draw(mn).ellipse([0, 0, d_o - 1, d_o - 1], fill=255)
    x, y = w - d_o - int(w * 0.05), int(h * 0.05)
    vien = Image.new("RGBA", (d_o + 14, d_o + 14), (0, 0, 0, 0))
    ImageDraw.Draw(vien).ellipse([0, 0, d_o + 13, d_o + 13], fill=(255, 255, 255, 235))
    nen.paste(vien.convert("RGB"), (x - 7, y - 7), vien)
    nen.paste(ct, (x, y), mn)
    return nen


def bo_cuc_E(anh, w, h):
    """③ NGƯỜI + BẰNG CHỨNG TRÒN."""
    nen = _phu_khung(_mo(anh[0]), w, h)
    return _o_tron(nen, anh[1] if len(anh) > 1 else anh[0], w, h)


def bo_cuc_F(anh, w, h, ten=None, co=None):
    """⑤ DANH SÁCH NHÂN VẬT — 2–4 người kề nhau, nhãn tên dưới chân."""
    n = min(max(2, len(anh)), 4)
    ra = Image.new("RGB", (w, h), (12, 10, 10))
    cw = (w - (n - 1) * 4) // n
    for i in range(n):
        ra.paste(_phu_khung(_mo(anh[i]), cw, h), (i * (cw + 4), 0))
    if ten:
        d = ImageDraw.Draw(ra)
        try:
            fo = TPL._font(int(h * 0.030)) if hasattr(TPL, "_font") else None
        except Exception:
            fo = None
        for i, t in enumerate(ten[:n]):
            if not t:
                continue
            x0 = i * (cw + 4) + 10
            y0 = int(h * 0.86)
            tw = d.textlength(t.upper(), font=fo) if fo else len(t) * 14
            d.rounded_rectangle([x0, y0, x0 + tw + 26, y0 + int(h * 0.052)],
                                radius=8, fill=(250, 205, 40))
            d.text((x0 + 13, y0 + int(h * 0.010)), t.upper(), font=fo, fill=(24, 18, 12))
    return ra


def bo_cuc_G(anh, w, h):
    """⑧ SO SÁNH ĐỘI HÌNH — hai đội, hai khung ngang (khác ④ ở chỗ ảnh là tập thể)."""
    return bo_cuc_C(anh, w, h)


BO_CUC = {"A": bo_cuc_A, "B": bo_cuc_B, "C": bo_cuc_C, "D": bo_cuc_D,
          "E": bo_cuc_E, "F": bo_cuc_F, "G": bo_cuc_G}
# mã kiểu trong NÃO ↔ hàm dựng ở đây
NAO_MA = {"mot-nguoi": "A", "doi-dau": "B", "hai-khung": "C", "danh-sach": "F",
          "nguoi-inset": "E", "hai-doi-hinh": "G", "bang-chung": "C",
          "poster-tran": "B"}


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


def duong_nao():
    """Bộ não ảnh bìa nằm trong KHO TÀI NGUYÊN — dùng chung cả nhà, anh sửa thẳng vào
    đó không cần đụng mã (cùng lối với `luat-ghep-anh.md`)."""
    return os.path.join(DD.KHO_TAI_NGUYEN, "nao-thumbnail.md")


def _doc_nao():
    try:
        return open(duong_nao(), encoding="utf-8").read()
    except Exception:
        return ""


def _kieu_bo_cuc(viec, so_anh, kb=None):
    """Chọn kiểu bìa theo NÃO (`nao-thumbnail.md`) — thứ tự ưu tiên trong mục "CÁCH CHỌN".

    Rẻ trước: tám điều kiện của não đều đọc được bằng luật (bài có ngày giờ trận không,
    có dẫn lời báo ngoài không, mấy nhân vật, mấy đội). Không câu nào cần model đoán —
    nên không gọi model.

    Não là file văn bản anh sửa được; mã chỉ giữ phần THI HÀNH. Sửa điều kiện trong não
    mà mã không biết thì vô ích, nên mọi mã kiểu ở đây phải khớp bảng NAO_MA.
    """
    hs = {}
    try:
        hs = json.load(open(os.path.join(viec, "anh", "ho-so-bai.json"),
                            encoding="utf-8"))
    except Exception:
        pass
    if kb is None:
        try:
            kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
        except Exception:
            kb = {}
    doi = [x for x in (hs.get("doi") or []) if x]
    nv = [x for x in (hs.get("nhan_vat") or []) if x]
    # TIÊU ĐỀ là nơi cô đọng nhất — quét cả lời bình (dài 60–80 chữ) thì từ khoá nào
    # cũng có thể lọt vào, và bài về MỘT người bị đẩy sang kiểu "danh sách" chỉ vì
    # trong lời bình có chữ "bổ sung" (QC 18/08 bắt được trên 3/8 bài).
    # Lời bình chỉ dùng cho hai luật cần bằng chứng ngoài tiêu đề: lịch trận và dẫn lời.
    tit_l = str(kb.get("tieu_de") or "").lower()
    loi_l = str(kb.get("loi_binh") or "").lower()
    chu = tit_l                                  # mặc định: chỉ tiêu đề
    chu_rong = tit_l + " " + loi_l               # cho luật cần soi rộng

    # ① trận SẮP đá — có ngày giờ/sân trong bài
    import re as _re
    co_lich = bool(_re.search(r"\b\d{1,2}[h:]\d{2}\b", chu_rong)) or \
        bool(_re.search(r"\bngày\s+\d{1,2}[/-]\d{1,2}", chu_rong))
    # Poster chỉ dùng khi bài THẬT SỰ về một trận CHƯA ĐÁ: phải có LỊCH CỤ THỂ (giờ
    # hoặc ngày) VÀ không được nhắc diễn biến đã xảy ra. Bản đầu bắt cả "sắp · đêm nay ·
    # sẽ gặp" nên bài tường thuật VAR cũng rơi vào poster — sai hẳn kiểu.
    da_dien_ra = any(t in chu_rong for t in ("đã ", "vừa ", "phút ", "ghi bàn", "thắng ",
                                        "thua ", "hoà ", "hòa ", "var", "thẻ đỏ",
                                        "kết thúc", "chung cuộc"))
    if co_lich and not da_dien_ra and len(doi) >= 2 and so_anh >= 2:
        return "B", "poster-tran"
    # ② dẫn lời / số liệu bên ngoài
    if any(t in chu for t in ("truyền thông", "báo ", "tờ ", "chuyên trang", "mạng xã hội",
                              "fan page", "bình luận", "viết rằng", "đưa tin")) \
            and so_anh >= 2:
        return "C", "bang-chung"
    # ③ giới thiệu nhiều người mới
    if any(t in chu for t in ("nhập tịch", "tân binh", "triệu tập", "danh sách",
                              "bổ sung", "ra mắt")) and len(nv) >= 2 and so_anh >= 2:
        return "F", "danh-sach"
    # ④ so hai tập thể
    if any(t in chu for t in ("đội hình", "lực lượng", "so sánh", "chất lượng đội")) \
            and len(doi) >= 2 and so_anh >= 2:
        return "G", "hai-doi-hinh"
    # ⑤ MỘT CHI TIẾT PHẢI CHO THẤY — đứng TRƯỚC đối đầu.
    # Bài nào của kênh cũng có hai đội trong hồ sơ (vì bài nào cũng nhắc trận), nên
    # "có hai đội" KHÔNG phân biệt được gì: để nó lên trước là mọi bài đều thành
    # đối đầu (QC 18/08: 8/8 bài cùng ra một kiểu — vô dụng).
    if any(t in chu for t in ("thẻ đỏ", "thẻ vàng", "var", "việt vị", "phạt đền",
                              "trọng tài", "tranh chấp", "chấn thương", "án phạt",
                              "công nghệ", "bảng điện")) and so_anh >= 2:
        return "E", "nguoi-inset"

    # ⑥ TIÊU ĐỀ XOAY QUANH MỘT TÊN NGƯỜI → chân dung. Nhận biết: tên người trong hồ
    # sơ bài có mặt trong tiêu đề, mà tên ĐỘI thì không (hoặc chỉ một đội).
    ten_trong_tit = [x for x in nv if x and x.lower() in tit_l]
    doi_trong_tit = [x for x in doi if x and x.lower() in tit_l]
    if len(ten_trong_tit) == 1 and len(doi_trong_tit) <= 1:
        return "A", "mot-nguoi"

    # ⑦ ĐỐI ĐẦU — chỉ khi tiêu đề nhắc CẢ HAI bên
    if len(doi_trong_tit) >= 2 and so_anh >= 2:
        return "B", "doi-dau"
    if len(ten_trong_tit) >= 2 and so_anh >= 2:
        return "B", "doi-dau"

    # ⑧ hai chuyện nối nhau
    if so_anh >= 2:
        return "C", "hai-khung"
    return "A", "mot-nguoi"


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
    ten_kieu = ""
    if kieu:
        kieu = kieu.upper()
        ten_kieu = next((k for k, v in NAO_MA.items() if v == kieu), kieu)
    else:
        kieu, ten_kieu = _kieu_bo_cuc(viec, len(anh), kb)
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
    return ra, ten_kieu or kieu, len(anh)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Dùng: python3 lam_thumbnail.py <mã việc> [kiểu A|B|C|D]")
    v = DD.tim_viec(sys.argv[1])
    p, k, n = lam(v, kieu=(sys.argv[2].upper() if len(sys.argv) > 2 else None))
    print(f"✅ {p}\n   bố cục {k} · dùng {n} ảnh ứng viên")
