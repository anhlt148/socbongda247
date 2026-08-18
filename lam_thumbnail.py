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


def bo_cuc_A(anh, w, h, phe=None):
    """① MỘT NGƯỜI — hiệu ứng bắt buộc: vignette (não mục E①)."""
    return _vignette(_phu_khung(_mo(anh[0]), w, h))


def bo_cuc_B(anh, w, h, phe=None):
    """② ĐỐI ĐẦU — chia CHÉO 8–15° · vệt sáng đường chia · ám màu theo phe (não E②).

    Chia chéo chứ không chia thẳng: chéo = động, thẳng = tĩnh. Vệt sáng biến đường chia
    thành tia sét — thiếu nó thì trông như ghép ảnh vụng (não mục G③).
    """
    ra = Image.new("RGB", (w, h), (12, 10, 10))
    x_d, x_t = int(w * 0.46), int(w * 0.57)      # chia CHÉO ~11 độ
    trai = _phu_khung(_mo(anh[0]), int(w * 0.62), h)
    phai = _phu_khung(_mo(anh[1]), int(w * 0.62), h)
    if phe:
        m0 = _mau_cua_phe(phe[0]) if len(phe) > 0 else None
        m1 = _mau_cua_phe(phe[1]) if len(phe) > 1 else None
        if m0:
            trai = _am_mau(trai, m0)
        if m1:
            phai = _am_mau(phai, m1)
    ra.paste(trai, (0, 0))
    mn = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mn).polygon([(x_d, h), (x_t, 0), (w, 0), (w, h)], fill=255)
    lop_p = Image.new("RGB", (w, h), (12, 10, 10))
    lop_p.paste(phai, (w - phai.width, 0))
    ra = Image.composite(lop_p, ra, mn)
    ra = _vet_sang(ra, x_t, x_d)
    return _vignette(ra, 0.30)

def bo_cuc_C(anh, w, h, phe=None):
    """④ HAI KHUNG NGANG — vạch trắng 5–7px, tối dần đáy (não E④)."""
    ra = Image.new("RGB", (w, h), (12, 10, 10))
    cao = (h - 6) // 2
    ra.paste(_phu_khung(_mo(anh[0]), w, cao), (0, 0))
    ra.paste(_phu_khung(_mo(anh[1]), w, h - cao - 6), (0, cao + 6))
    ImageDraw.Draw(ra).rectangle([0, cao, w, cao + 6], fill=(248, 242, 232))
    return _toi_dan_day(ra)


def bo_cuc_D(anh, w, h, phe=None):
    """Lưới bốn ô — bài điểm tin nhiều nhân vật."""
    ra = Image.new("RGB", (w, h), (12, 10, 10))
    cw, ch = (w - 5) // 2, (h - 5) // 2
    for i, p in enumerate(anh[:4]):
        x = (i % 2) * (cw + 5)
        y = (i // 2) * (ch + 5)
        ra.paste(_phu_khung(_mo(p), cw, ch), (x, y))
    return ra


# ══ HIỆU ỨNG THỊ GIÁC (mục B của não) ═══════════════════════════════════════
# Luật xuyên suốt: NỀN PHẢI LÙI, CHỦ THỂ PHẢI TIẾN. Đây là khác biệt lớn nhất giữa bìa
# nghiệp dư và bìa của kênh dẫn đầu — không phải màu mè hơn, mà CÓ CHIỀU SÂU.

MAU_PHE = {                        # ám màu theo phe (mục B③)
    "việt nam": (196, 30, 30), "vietnam": (196, 30, 30),
    "malaysia": (212, 160, 20), "thái lan": (30, 70, 170), "thailand": (30, 70, 170),
    "indonesia": (200, 40, 40), "singapore": (200, 40, 40),
    "campuchia": (40, 90, 170), "philippines": (30, 110, 190),
}


def _vignette(im, manh=0.42):
    """Tối bốn góc, sáng giữa — mắt tự dồn vào chủ thể (mục A)."""
    w, h = im.size
    import numpy as _np
    yy, xx = _np.mgrid[0:h, 0:w]
    cx, cy = w / 2.0, h / 2.0
    r = _np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    k = _np.clip(1.0 - manh * _np.clip(r - 0.42, 0, None) ** 1.6, 0.25, 1.0)
    a = _np.asarray(im).astype(_np.float32)
    a *= k[..., None]
    return Image.fromarray(_np.clip(a, 0, 255).astype("uint8"))


def _toi_dan_day(im, ty=0.26):
    """Phần giáp dải chữ tối dần — không có đường cắt cứng (mục B⑤)."""
    w, h = im.size
    cao = int(h * ty)
    lop = Image.new("L", (w, cao))
    for y in range(cao):
        lop.putpixel((0, y), int(210 * (y / max(1, cao - 1)) ** 1.5))
    lop = lop.resize((w, cao))
    den = Image.new("RGB", (w, cao), (0, 0, 0))
    im.paste(den, (0, h - cao), lop)
    return im


def _am_mau(im, mau, manh=0.20):
    """Ám màu theo phe — nhận ra bài nói về ai trước cả khi đọc chữ (mục B③)."""
    lop = Image.new("RGB", im.size, mau)
    return Image.blend(im, lop, manh)


def _mau_cua_phe(ten):
    t = (ten or "").lower()
    for k, v in MAU_PHE.items():
        if k in t:
            return v
    return None


def _vet_sang(im, x_tren, x_duoi, rong=11):
    """Vệt sáng ở đường chia — đường chia thành tia sét, không phải nét ghép (mục B②)."""
    w, h = im.size
    v = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(v)
    d.line([(x_duoi, h), (x_tren, 0)], fill=(255, 236, 168, 225), width=rong)
    d.line([(x_duoi, h), (x_tren, 0)], fill=(255, 255, 235, 255), width=max(2, rong // 4))
    v = v.filter(ImageFilter.GaussianBlur(4))
    return Image.alpha_composite(im.convert("RGBA"), v).convert("RGB")


def _vien_sang(im, mau=(255, 210, 90), day=7, quang=30):
    """Viền phát sáng quanh khung chủ thể (mục B①)."""
    w, h = im.size
    v = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(v).rectangle([0, 0, w - 1, h - 1], outline=mau + (235,), width=day)
    q = v.filter(ImageFilter.GaussianBlur(quang // 2))
    return Image.alpha_composite(
        Image.alpha_composite(im.convert("RGBA"), q), v).convert("RGB")


def _do_bong(nen, o, xy, lech=16, mo=60):
    """Bóng mềm dưới chủ thể — đứng trên nền chứ không dán phẳng (mục B④)."""
    b = Image.new("RGBA", nen.size, (0, 0, 0, 0))
    ImageDraw.Draw(b).rectangle(
        [xy[0] + 6, xy[1] + lech, xy[0] + o.width - 6, xy[1] + o.height + lech],
        fill=(0, 0, 0, mo))
    b = b.filter(ImageFilter.GaussianBlur(18))
    return Image.alpha_composite(nen.convert("RGBA"), b).convert("RGB")


# Hai đường đo vùng cấm cho ra hai thang điểm khác nhau — mắt máy cộng 10,0 cho một
# khuôn mặt, đường đoán cũ chỉ tối đa 3,2. Nếu để nguyên thì ngưỡng "vướng quá thì bỏ ô
# tròn" bên dưới sẽ đúng với đường này và CHẾT CÂM với đường kia. Nên cả hai cùng chia
# về MỘT thước: 1,0 = chỗ cấm đè tuyệt đối.
_LOP_PHU = None   # lớp phủ vừa đặt: vướng bao nhiêu · cao bao nhiêu · cách dải chữ mấy.
                  # Bộ chấm đọc để chấm CẢ thẩm mỹ, không chỉ chấm "có đè lên gì không".

LOGO_TY = 0.115          # bề ngang logo kênh, theo tỷ lệ bề ngang bìa


def _hop_logo(W_n, H_n):
    """Chỗ LOGO KÊNH ngồi, trả (x0, y0, x1, y1).

    MỘT NGUỒN cho hai việc vốn hay lệch nhau: chỗ vẽ logo, và chỗ cấm lớp phủ đè lên.
    Trước đây chỗ vẽ ghi toạ độ cứng trong hàm vẽ, còn chỗ cấm thì đoán mò bằng cách
    cộng điểm cho "góc trên trái" — hai nơi, đổi một nơi là lệch.
    """
    d = int(W_n * LOGO_TY)
    x0 = int(L.get("le_trai", 96) * W_n / W) - 28
    return x0, 54, x0 + d, 54 + d


def _che_hop(hop, x, y, d):
    """Ô vuông (x,y,d,d) che mất bao nhiêu phần của một hộp? 0..1."""
    x0, y0, x1, y1 = hop
    gw = max(0.0, min(x + d, x1) - max(x, x0))
    gh = max(0.0, min(y + d, y1) - max(y, y0))
    dt = (x1 - x0) * (y1 - y0)
    return gw * gh * 0.79 / dt if dt > 0 else 0.0


THANG_MAT, THANG_DOAN = 10.0, 3.2
# Vướng tới đâu thì nhường: thu nhỏ còn ¾ → vẫn vướng thì bỏ hẳn vật thể đó.
NG_THU_NHO, NG_BO_HAN = 0.45, 0.62
# TẦM CAO ô tròn: tâm phải nằm trong dải này, tính theo chiều cao BÌA từ ĐÁY lên
# (anh chốt 18/08). Đây là RÀNG BUỘC chứ không phải tiêu chí chấm điểm — đặt ngoài dải
# thì dù không đè lên gì cũng vẫn xấu, mà bộ chấm cũ lại cho qua.
DAI_CAO_O_TRON = (0.60, 0.70)


def _muc_cao_o_tron(so=4):
    """Các nấc cao được phép, xếp từ CAO xuống thấp trong dải anh chốt."""
    a, b = DAI_CAO_O_TRON
    return [b - (b - a) * i / (so - 1) for i in range(so)]

def _ban_do_quan_trong(im, o_ngang=8, o_doc=12):
    """Bản đồ "chỗ nào KHÔNG được che" của một ảnh — lưới điểm, cao = cấm đè.

    Anh bắt 18/08: ô tròn đè trúng mặt cầu thủ. Gốc bệnh là đặt CỐ ĐỊNH góc trên phải,
    chẳng nhìn dưới đó có gì. Bản vá sáng 18/08 đoán bằng MÀU DA + đếm cạnh — đoán
    được, nhưng là đoán: áo hồng, tường gạch, sân đất đều lọt lưới màu da; mặt nhỏ
    trong đám đông thì trượt.

    Nay NHÌN THẬT qua mat_may.py (YuNet nhận mặt + U²-Net tách chủ thể). Ba lớp cộng
    lại: khuôn mặt (nặng áp đảo) · thân người (nặng vừa) · độ chi tiết (nền).

    Mắt máy hỏng hay thiếu venv thì TỰ LÙI về cách đoán cũ — bìa vẫn ra, chỉ kém tinh.
    Đây là chỗ không được phép chết: bìa là khâu cuối trước khi đăng.
    """
    import numpy as _np
    try:
        import mat_may
        d = mat_may.nhin_pil(im)
    except Exception:
        d = None
    if d and d.get("luoi"):
        q = _np.asarray(d["luoi"], _np.float32)
        if q.shape == (o_doc, o_ngang):
            return q / THANG_MAT        # về thang chung: 1.0 = cấm đè tuyệt đối
    return _ban_do_quan_trong_doan(im, o_ngang, o_doc) / THANG_DOAN


def _ban_do_quan_trong_doan(im, o_ngang=8, o_doc=12):
    """ĐƯỜNG LÙI — đoán bằng màu da + đếm cạnh, không cần thư viện ngoài.

    Giữ lại nguyên vẹn để bìa không bao giờ chết vì thiếu venv hay model.
    """
    import numpy as _np
    g = im.convert("RGB").resize((o_ngang * 12, o_doc * 12))
    a = _np.asarray(g).astype(_np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    da = ((R > 90) & (G > 40) & (B > 20) & (R > G + 12) & (G > B - 8)
          & (R - _np.minimum(G, B) > 14) & (R < 250)).astype(_np.float32)
    x = _np.asarray(g.convert("L")).astype(_np.float32)
    ct = _np.abs(_np.diff(x, axis=0, prepend=x[:1])) + \
        _np.abs(_np.diff(x, axis=1, prepend=x[:, :1]))
    ct = _np.clip(ct / 42.0, 0, 1)
    q = da * 2.2 + ct
    q = q.reshape(o_doc, 12, o_ngang, 12).mean(axis=(1, 3))
    return q          # logo do _hop_logo lo, không cộng vào lưới nữa (kẻo đếm hai lần)


def _hop_mat(im):
    """Danh sách hộp khuôn mặt trên ảnh — rỗng nếu mắt máy chưa sẵn sàng.

    Lưới 8×12 chỉ đủ để nói "vùng này đông thông tin"; mỗi ô rộng 135 px nên một
    khuôn mặt chạm mép ô là cả ô bị coi như cấm, và ô tròn bị đuổi đi oan. Muốn quyết
    đúng thì phải đo GIAO THẬT giữa vật định đặt và khuôn mặt — việc đó cần toạ độ
    hộp, không phải điểm lưới.
    Trả (danh sách hộp mặt, lưới NỀN). Lưới nền đã bỏ phần khuôn mặt ra — mặt được đo
    riêng bằng hộp, cộng cả hai vào một lưới là đếm nó hai lần và chỗ nào có mặt cũng
    thành cấm tuyệt đối, kể cả khi ô tròn chỉ chạm mép.
    """
    try:
        import mat_may
        d = mat_may.nhin_pil(im)
    except Exception:
        return [], None
    if not d:
        return [], None
    import numpy as _np
    nen = d.get("luoi_nen")
    return (d.get("mat") or []), (_np.asarray(nen, _np.float32) / THANG_MAT
                                  if nen else None)


def _che_mat(hop_ds, x, y, d, W, H):
    """Ô vuông (x,y,d,d) che mất bao nhiêu phần khuôn mặt? Trả 0..1, cao = che nhiều.

    Tính theo phần trăm CỦA KHUÔN MẶT chứ không phải của tấm ảnh: che 30% một khuôn
    mặt là hỏng, dù khuôn mặt ấy chỉ chiếm 3% tấm bìa.
    """
    te = 0.0
    for m in hop_ds:
        # nới 15% để chừa tóc, cằm, tai — YuNet chỉ khoanh phần lõi
        nx, ny = m["w"] * 0.15, m["h"] * 0.15
        mx0, my0 = m["x"] - nx, m["y"] - ny
        mx1, my1 = m["x"] + m["w"] + nx, m["y"] + m["h"] + ny
        gw = max(0.0, min(x + d, mx1) - max(x, mx0))
        gh = max(0.0, min(y + d, my1) - max(y, my0))
        dt = (mx1 - mx0) * (my1 - my0)
        if dt <= 0:
            continue
        # 0,79 = diện tích hình tròn nội tiếp / hình vuông — vật đặt là ô TRÒN
        che = gw * gh * 0.79 / dt
        # mặt to là chủ thể chính, mặt nhỏ thường là khán giả phía sau
        nang = 1.0 if m["w"] * m["h"] / (W * H) > 0.008 else 0.45
        te = max(te, che * nang)
    return te


def _cho_dat_o_tron(nen, d_o, le=0.05):
    """Chọn chỗ đặt ô tròn: ĐÚNG TẦM CAO trước, rồi mới xét trái hay phải.

    Anh bắt 18/08 (lần hai): ô tròn nằm thấp quá, nép sát mép dải chữ — "QC phải có
    thẩm mỹ cao chứ". Anh đúng, và đây là chỗ tôi làm thiếu.

    Bản trước thử BỐN GÓC và chấm bằng một câu hỏi duy nhất: "chỗ này có đè lên thứ
    quan trọng không?". Đó là TRÁNH LỖI, không phải THẨM MỸ. Góc dưới không đè lên gì
    thật — nhưng nó nằm ở 31–51% chiều cao tính từ đáy, mép dưới cách dải chữ vỏn vẹn
    52 px, nhìn như bị dồn xuống đáy. Không phạm lỗi nào, mà vẫn xấu.

    Nay tầm cao là RÀNG BUỘC, không phải thứ đem ra chấm điểm: tâm ô tròn phải nằm
    trong dải 60–70% chiều cao bìa tính từ đáy (anh chốt 18/08). Trong dải ấy mới xét
    tiếp trái hay phải, cao hay thấp hơn một chút, tuỳ chỗ nào ít vướng mặt người.
    """
    import numpy as _np
    W_n, H_n = nen.size
    hop_ds, luoi_nen = _hop_mat(nen)
    q = luoi_nen if luoi_nen is not None else _ban_do_quan_trong(nen)
    oh, ow = q.shape
    m = int(le * W_n)

    # ── các chỗ ĐƯỢC PHÉP đặt: bốn nấc cao trong dải anh chốt × hai bên trái/phải ──
    cho = []
    for i_t, t in enumerate(_muc_cao_o_tron()):
        y = int(H * (1 - t) - d_o / 2)                  # H = chiều cao BÌA, không phải ảnh nền
        y = max(m, min(y, H_n - d_o - m))               # vẫn phải nằm gọn trong ảnh nền
        for i_x, (ten_x, x) in enumerate((("phải", W_n - d_o - m), ("trái", m))):
            # phạt rất nhẹ: ngang điểm thì giữ thói quen đọc (phải trước, cao trước)
            cho.append((f"{ten_x} · {t*100:.0f}% từ đáy", x, y, i_t * 0.008 + i_x * 0.016))

    tot, diem_tot, ten_tot = None, 1e9, ""
    for ten, x, y, phat in cho:
        c0, c1 = int(x / W_n * ow), max(1, int((x + d_o) / W_n * ow))
        r0, r1 = int(y / H_n * oh), max(1, int((y + d_o) / H_n * oh))
        o = q[r0:r1, c0:c1]
        # NỀN — thân người, chi tiết. Chỗ tệ nhất nặng hơn điểm trung bình: đè lên một
        # góc số áo cũng là đè, dù phần còn lại toàn cỏ.
        d = 0.35 * float(o.mean()) + 0.65 * float(o.max()) + phat
        # MẶT — đo bằng giao hộp, chính xác tới pixel. Nhân 1,6 để một khuôn mặt bị che
        # nửa (0,5) đủ vượt ngưỡng bỏ hẳn, còn chạm mép vài chục pixel thì gần như
        # không tính — đúng như mắt người nhìn.
        d += 1.6 * _che_mat(hop_ds, x, y, d_o, W_n, H_n)
        # LOGO KÊNH — dấu nhận biết của kênh, che là mất. Biết chắc toạ độ nên đo thẳng.
        d += 1.2 * _che_hop(_hop_logo(W_n, H_n), x, y, d_o)
        if d < diem_tot:
            tot, diem_tot, ten_tot = (x, y), d, ten
    return tot, diem_tot, ten_tot


def _o_tron(nen, anh_ct, w, h):
    """Ô TRÒN góc trên phải chứa vật chứng (thẻ đỏ, bảng VAR, vật lạ).

    Kiểu ③ trong não: ô tròn tạo câu hỏi "cái gì trong đó?" — tò mò mạnh hơn cả tiêu đề.
    """
    d_o = int(w * 0.355)          # não mục C: 32–38% bề ngang
    ct = _phu_khung(_mo(anh_ct), d_o, d_o)
    mn = Image.new("L", (d_o, d_o), 0)
    ImageDraw.Draw(mn).ellipse([0, 0, d_o - 1, d_o - 1], fill=255)
    # CHỖ ĐẶT do bản đồ quyết, không dí cứng vào góc trên phải nữa (anh bắt 18/08:
    # ô tròn đè trúng mặt cầu thủ Thái Lan). Thử cả bốn góc, chọn góc ÍT quan trọng nhất.
    (x, y), _d, _ten = _cho_dat_o_tron(nen, d_o)
    # Vẫn vướng nặng ở MỌI góc → THU NHỎ ô tròn rồi thử lại. Thà ô nhỏ hơn mẫu một
    # chút còn hơn che mất khuôn mặt — mặt người là thứ giữ chân người xem, ô tròn chỉ
    # là gia vị.
    if _d > NG_THU_NHO:
        d_o = int(d_o * 0.74)
        (x, y), _d, _ten = _cho_dat_o_tron(nen, d_o)
    global _LOP_PHU
    if _d > NG_BO_HAN:
        print(f"  ⚠ ảnh nền kín người ở mọi chỗ được phép — BỎ ô tròn, để bìa thoáng")
        _LOP_PHU = {"vuong": _d, "bo": True}
        return nen
    y_dai = int(H * float(L.get("hoa_den_ty_le", 0.70))) + 26
    _LOP_PHU = {"vuong": _d, "bo": False,
                "cao_tu_day": (H - (y + d_o / 2)) / H,
                "cach_dai": (y_dai - (y + d_o)) / H}
    print(f"  ○ ô tròn đặt {_ten} · cách dải chữ {_LOP_PHU['cach_dai']*100:.0f}% "
          f"(điểm vướng {_d:.2f})")
    # bóng đen mờ quanh viền (não mục C) — ô tròn nổi hẳn khỏi ảnh nền
    bg = Image.new("RGBA", nen.size, (0, 0, 0, 0))
    ImageDraw.Draw(bg).ellipse([x - 16, y - 8, x + d_o + 16, y + d_o + 22],
                               fill=(0, 0, 0, 130))
    nen = Image.alpha_composite(nen.convert("RGBA"),
                                bg.filter(ImageFilter.GaussianBlur(15))).convert("RGB")
    vien = Image.new("RGBA", (d_o + 16, d_o + 16), (0, 0, 0, 0))
    ImageDraw.Draw(vien).ellipse([0, 0, d_o + 15, d_o + 15], fill=(255, 255, 255, 245))
    nen.paste(vien.convert("RGB"), (x - 8, y - 8), vien)
    nen.paste(ct, (x, y), mn)
    return nen


def bo_cuc_E(anh, w, h, phe=None):
    """③ NGƯỜI + Ô TRÒN VẬT CHỨNG — ô tròn + vignette (não E③).

    Ô tròn là chi tiết đắt nhất bộ mẫu: nó tạo câu hỏi mà tiêu đề không tạo được.
    """
    nen = _vignette(_phu_khung(_mo(anh[0]), w, h), 0.34)
    return _o_tron(nen, anh[1] if len(anh) > 1 else anh[0], w, h)


def bo_cuc_F(anh, w, h, phe=None, ten=None, co=None):
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


def bo_cuc_G(anh, w, h, phe=None):
    """⑧ SO SÁNH ĐỘI HÌNH — hai khung ngang, mỗi khung ám màu phe của đội (não E⑧)."""
    ra = Image.new("RGB", (w, h), (12, 10, 10))
    cao = (h - 6) // 2
    for i, (p_a, y, ch) in enumerate([(anh[0], 0, cao),
                                      (anh[1], cao + 6, h - cao - 6)]):
        kh = _phu_khung(_mo(p_a), w, ch)
        m = _mau_cua_phe(phe[i]) if phe and i < len(phe) else None
        if m:
            kh = _am_mau(kh, m, 0.17)
        ra.paste(kh, (0, y))
    ImageDraw.Draw(ra).rectangle([0, cao, w, cao + 6], fill=(248, 242, 232))
    return _toi_dan_day(ra)


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


def _ve_dai_chu(bia, tit, cum):
    """Vẽ dải chữ + tô vàng + logo + watermark lên ảnh nền đã dựng.

    Tách riêng để CẢ HAI đường dùng chung: bìa từ thư mục việc, và bìa dựng từ
    video đã đẩy lên. Hai bản vẽ khác nhau là hai kiểu bìa khác nhau — đúng bệnh
    "một logic hai bản" đã trả giá nhiều lần.
    """
    # ② DẢI CHỮ — dùng lại các LỚP của template (gradient · hoa văn sân · fit chữ ·
    #    watermark) nhưng CANH RIÊNG cho bìa.
    #    Vì sao không gọi thẳng `xuong.lam_overlay`: khuôn ấy vẽ cho VIDEO, chữ nằm sát
    #    mép trên dải và chừa khoảng trống bên dưới cho nội dung chạy. Bìa thì phải LẤP
    #    ĐẦY — 20/20 mẫu của kênh dẫn đầu đều vậy, chữ càng to càng bắt mắt trên lưới
    #    Shorts. Sửa `lam_overlay` là đụng vào video đang chạy tốt, nên tách đường.

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
        _lx, _ly, _lx1, _ly1 = _hop_logo(W, H)
        _lg = Image.open(DD.LOGO).convert("RGBA").resize(
            (_lx1 - _lx,) * 2, Image.LANCZOS)
        lop.alpha_composite(_lg, (_lx, _ly))
    except Exception as _e:
        print(f"  ⚠ không gắn được logo: {_e}")
    try:
        TPL._ve_watermark(lop, DD.KENH)     # đúng chữ ký xưởng dùng
    except Exception as _e:
        print(f"  ⚠ không vẽ được watermark: {_e}")
    return Image.alpha_composite(bia.convert("RGBA"), lop).convert("RGB")



def _cum_vang_tu_tit(tit):
    """Chọn cụm tô vàng khi không có kịch bản (bìa dựng từ video đã đẩy).

    Dùng lại module `cum_vang` của xưởng — MỘT nguồn chọn cụm, không viết bản thứ hai.
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import cum_vang as _CV
        for ten in ("chon", "chon_cum", "tu_tieu_de", "bao_dam"):
            f = getattr(_CV, ten, None)
            if callable(f):
                try:
                    r = f(tit)
                    if isinstance(r, (list, tuple)) and r:
                        return list(r)
                except Exception:
                    continue
    except Exception:
        pass
    # Module cụm vàng của xưởng cần đường dẫn kịch bản, bìa dựng từ video thì không có
    # → tự chọn theo LUẬT VÀNG của não: tô cái BẤT THƯỜNG, đừng tô cái hiển nhiên.
    return _cum_vang_theo_luat(tit)


# Từ mang cảm xúc/bất ngờ — thứ đáng tô. Rút từ tít của 20 mẫu: chúng luôn tô chỗ gây
# tò mò, không bao giờ tô tên đội hay từ nghề nghiệp.
TU_MANH = ("dớp", "hụt", "sốc", "quê", "cay", "tự hủy", "cà khịa", "chê", "mỉa",
           "bẽ", "ê chề", "vỡ mộng", "trắng tay", "lật kèo", "quay xe", "bất ngờ",
           "chưa từng", "lần đầu", "kỷ lục", "lịch sử", "duy nhất", "đầu tiên",
           "cuối cùng", "bí mật", "sự thật", "hé lộ", "tiết lộ", "thừa nhận")
TU_NHAT = ("việt nam", "bóng đá", "đội tuyển", "trận đấu", "cầu thủ", "asean",
           "aff", "cup", "giải", "vòng", "bảng")


def _cum_vang_theo_luat(tit):
    """Chọn 1–2 cụm đáng tô, thuần code."""
    import re as _re
    t = tit.strip()
    ra = []
    # ① cụm trong ngoặc kép — thứ người viết đã tự đánh dấu là đắt
    for m in _re.finditer(r"[“\"']([^”\"']{2,28})[”\"']", t):
        ra.append(m.group(1).strip())
    # ② tỷ số / con số có sức nặng
    for m in _re.finditer(r"\b\d+\s*[-–]\s*\d+\b|\b\d+\s+(?:lần|bàn|năm|tuổi)\b", t, _re.I):
        ra.append(m.group(0).strip())
    # ③ cụm chứa từ mạnh — lấy trọn cụm 2–4 từ quanh nó
    tu = t.split()
    tl = [x.lower().strip(",.:;!?“”\"'") for x in tu]
    for i, x in enumerate(tl):
        if any(x.startswith(k.split()[0]) and k.split()[0] == x for k in TU_MANH) or \
                any(k in " ".join(tl[i:i + 2]) for k in TU_MANH):
            ra.append(" ".join(tu[i:i + min(3, len(tu) - i)]).strip(",.:;!?"))
            break
    # bỏ cụm chỉ toàn từ nhạt
    ra = [c for c in ra if c and not all(w.lower() in TU_NHAT for w in c.split())]
    kq = []
    for c in ra:
        if c not in kq:
            kq.append(c)
    return kq[:2]


# Từ MẠNH — thứ khiến người ta dừng lại. Não mục "luật vàng": tô cái BẤT THƯỜNG, đừng
# tô cái hiển nhiên. "VIỆT NAM" ai cũng biết, tô cũng vô ích; "CÁI DỚP" mới là chỗ gợi
# tò mò. Bảng này rút từ tiêu đề 20 mẫu — toàn từ chỉ điều BẤT NGỜ hoặc TRÁI CHIỀU.
TU_MANH = (
    "dớp", "hụt", "mừng hụt", "quê", "cay", "sốc", "chê", "cà khịa", "khiêu khích",
    "tự hủy", "tự huỷ", "ế", "bán ế", "thất bại", "gục", "khóc", "bật khóc",
    "chưa từng", "lần đầu", "cuối cùng", "bất ngờ", "ngỡ ngàng", "quay xe",
    "lộ", "vạch trần", "thừa nhận", "tố", "đòi", "dọa", "doạ", "cấm",
    "tẩy trắng", "trắng trợn", "nói thẳng", "đùa", "gọi tên", "phá được",
    "vô địch", "chung kết", "thẻ đỏ", "var", "phạt đền", "nhập tịch",
)


def _tu_chon_cum_vang(tit):
    """Tự chọn cụm tô vàng từ tiêu đề khi không có kịch bản (bìa dựng từ video cũ).

    Ba lớp, ưu tiên giảm dần:
      ① cụm trong NGOẶC KÉP — người viết đã tự đánh dấu chỗ đắt
      ② con số / tỷ số — "3-1", "2 LẦN", "0-3": mắt bắt số nhanh hơn chữ
      ③ cụm chứa TỪ MẠNH — lấy từ ấy cùng một từ kề để thành cụm đọc được
    """
    import re as _r
    ra = []
    for m in _r.finditer(r"[\"“”']([^\"“”']{3,28})[\"“”']", tit):
        ra.append(m.group(1).strip())
    for m in _r.finditer(r"\b\d+\s*[-–]\s*\d+\b|\b\d+\s+(?:lần|bàn|năm|tuổi)\b",
                         tit, _r.I):
        ra.append(m.group(0).strip())
    tu = tit.split()
    thap = [t.lower().strip(",.:;!?\"“”'") for t in tu]
    for i, t in enumerate(thap):
        if any(t == k or (len(k.split()) == 1 and k in t) for k in TU_MANH):
            # Ghép về phía nào? Tiếng Việt hay có TỪ CHỈ ĐỊNH đứng trước danh từ mạnh
            # ("cái dớp", "cú sốc", "pha bẻ lái"). Ghép xuôi sang phải thì ra "DỚP VIỆT"
            # — cắt ngang cụm, đọc trẹo. Nên ngó sang trái trước.
            PHU = ("cái", "một", "những", "các", "cú", "pha", "vụ", "màn", "cơn",
                   "nỗi", "chuyện", "điều", "trận", "bàn")
            if i > 0 and thap[i - 1] in PHU:
                cum = " ".join(tu[i - 1:i + 1])
            elif i + 1 < len(tu):
                cum = " ".join(tu[i:i + 2])
            else:
                cum = tu[i]
            ra.append(cum.strip(",.:;!?"))
            break
    # bỏ trùng, giữ thứ tự
    xong = []
    for c in ra:
        if c and c not in xong:
            xong.append(c)
    return xong[:2]


def _loc_cum_vang(tit, cum):
    """Giữ cụm tô vàng ở mức ĐIỂM NHẤN, không để nó nuốt cả câu.

    Não mục "luật vàng": tô cái BẤT THƯỜNG, đừng tô cái hiển nhiên. Bìa dựng từ video
    không có kịch bản nên phải tự chọn cụm — và lượt đầu nó tô mất 3/4 tiêu đề, thành
    ra chẳng còn gì nổi bật (tô hết = không tô gì).
    Trần: tổng chữ tô vàng không quá 45% số từ của tiêu đề.
    """
    tu_tit = [t for t in tit.split() if t.strip()]
    if not tu_tit or not cum:
        return []
    tran = max(1, int(len(tu_tit) * 0.45))
    ra, dem = [], 0
    for c in sorted([str(x).strip() for x in cum if str(x).strip()], key=len):
        n = len([t for t in c.split() if t.strip()])
        if dem + n > tran:
            continue
        ra.append(c)
        dem += n
    return ra


def _dung_mot(viec, kieu, anh, tit, kb, phe):
    """Dựng MỘT phương án bìa. Trả (ảnh, ngữ cảnh để chấm).

    Tách khỏi `lam` để dựng được nhiều phương án rồi so — trước đây dựng thẳng một
    bản rồi ghi đè, không có gì để so.
    """
    cao_anh = int(H * TY_ANH)
    global _LOP_PHU
    _LOP_PHU = None
    nen = BO_CUC[kieu](anh, W, cao_anh, phe)
    bia = Image.new("RGB", (W, H), (18, 14, 12))
    bia.paste(nen, (0, 0))
    bia.paste(_nen_mo(_mo(anh[0]), W, H - cao_anh), (0, cao_anh))
    bia = _ve_dai_chu(bia, tit, _loc_cum_vang(tit, kb.get("cum_to_vang") or []))
    return bia, {"y_dai": int(H * float(L.get("hoa_den_ty_le", 0.70))) + 26,
                 "lop_phu": _LOP_PHU}


def _cac_phuong_an(viec, so_anh, kb):
    """Những kiểu bố cục ĐÁNG THỬ cho bài này — kiểu não chọn đứng đầu, rồi tới các
    kiểu hợp lệ khác.

    Không thử hết bảy kiểu: kiểu không đủ ảnh thì dựng ra bìa lặp ảnh, chấm cao cũng
    vô nghĩa. Thà ba phương án thật còn hơn bảy phương án có bốn cái giả.
    """
    dau, ten = _kieu_bo_cuc(viec, so_anh, kb)
    ds = [dau]
    hop = ["A", "E"]                       # một người: luôn dựng được
    if so_anh >= 2:
        hop += ["B", "C", "G"]
    if so_anh >= 4:
        hop += ["D"]
    for k in hop:
        if k not in ds:
            ds.append(k)
    return ds[:5], ten                     # trần 5 phương án ~9 giây, đủ để chọn


def lam(viec, ra=None, kieu=None, so_pa=None):
    """Dựng ảnh bìa cho một bài, TỰ CHẤM nhiều phương án rồi đề bản tốt nhất.

    Anh chốt 18/08: "phải tự chấm được, đề cho anh bản tốt nhất". Máy dựng tới năm
    phương án khác bố cục, soi từng bản qua bảy thước của `cham_bia`, lấy bản điểm
    cao nhất làm `thumbnail.jpg`; các bản còn lại để trong `thumbnail-du-bi/` để anh
    đổi nếu không ưng, kèm `thumbnail-cham.json` ghi rõ vì sao bản kia thua.

    Anh chỉ định kiểu (tham số `kieu`) thì tôn trọng, chỉ dựng đúng kiểu ấy — quyền
    quyết cuối vẫn là của anh, máy chỉ đề xuất.
    """
    kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    tit = (kb.get("tieu_de") or "").strip()
    if not tit:
        raise RuntimeError("bài chưa có tiêu đề — chưa làm bìa được")
    anh = _chon_anh(viec, 4)
    if not anh:
        raise RuntimeError("bài không có ảnh nào đủ đẹp để lên bìa")

    phe = []
    try:
        _hs = json.load(open(os.path.join(viec, "anh", "ho-so-bai.json"),
                             encoding="utf-8"))
        phe = [x for x in (_hs.get("doi") or []) if x][:2]
    except Exception:
        pass

    if kieu:
        ds, ten_kieu = [kieu.upper()], next(
            (k for k, v in NAO_MA.items() if v == kieu.upper()), kieu)
    else:
        ds, ten_kieu = _cac_phuong_an(viec, len(anh), kb)
    if so_pa:
        ds = ds[:max(1, int(so_pa))]

    try:
        import cham_bia
    except Exception:
        cham_bia = None

    ket = []
    for k in ds:
        if k in ("B", "C", "G") and len(anh) < 2:
            continue
        if k == "D" and len(anh) < 4:
            continue
        try:
            bia, ctx = _dung_mot(viec, k, anh, tit, kb, phe)
        except Exception as e:
            print(f"  ⚠ phương án {k} dựng hỏng: {type(e).__name__}: {e}")
            continue
        kq = cham_bia.cham(bia, ctx) if cham_bia else {"diem": 0, "muc": []}
        ket.append({"kieu": k, "ten": next((n for n, v in NAO_MA.items() if v == k), k),
                    "diem": kq["diem"], "muc": kq["muc"], "bia": bia})
        print(f"  · phương án {k} ({ket[-1]['ten']}) — {kq['diem']:.1f}/100")
    if not ket:
        raise RuntimeError("không dựng được phương án bìa nào")

    ket.sort(key=lambda x: -x["diem"])
    nhat = ket[0]
    ra = ra or os.path.join(viec, "thumbnail.jpg")
    nhat["bia"].save(ra, quality=93, subsampling=0)

    # bản dự bị + báo cáo chấm: anh không ưng bản máy chọn thì đổi ngay, khỏi dựng lại
    thu = os.path.join(os.path.dirname(ra), "thumbnail-du-bi")
    # DỌN TRƯỚC KHI GHI. Lần dựng trước để lại bản của nó ở đây; không dọn thì anh mở
    # thư mục ra thấy lẫn bản cũ với bản mới, và bản cũ có khi lại chính là kiểu vừa
    # được chọn — nhìn tưởng máy dựng trùng.
    if os.path.isdir(thu):
        for _f in os.listdir(thu):
            if _f.endswith(".jpg"):
                try:
                    os.unlink(os.path.join(thu, _f))
                except OSError:
                    pass
    if len(ket) > 1:
        os.makedirs(thu, exist_ok=True)
        for x in ket[1:]:
            # ĐIỂM ĐỨNG ĐẦU TÊN: thư mục tự xếp theo thứ hạng, anh liếc là biết bản nào
            # gần nhất với bản máy chọn
            x["bia"].save(os.path.join(thu, f"{x['diem']:.0f}-{x['kieu']}-{x['ten']}.jpg"),
                          quality=90, subsampling=0)
    try:
        with open(os.path.join(os.path.dirname(ra), "thumbnail-cham.json"),
                  "w", encoding="utf-8") as f:
            json.dump([{kk: vv for kk, vv in x.items() if kk != "bia"} for x in ket],
                      f, ensure_ascii=False, indent=1)
    except OSError:
        pass
    return ra, nhat["ten"], len(anh), nhat["diem"], ket


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Dùng: python3 lam_thumbnail.py <mã việc> [kiểu A|B|C|D]")
    v = DD.tim_viec(sys.argv[1])
    p, k, n, d, ket = lam(v, kieu=(sys.argv[2].upper() if len(sys.argv) > 2 else None))
    print(f"\n✅ {p}\n   bố cục {k} · dùng {n} ảnh ứng viên · ĐIỂM {d:.1f}/100")
    try:
        import cham_bia
        cham_bia.in_bang({"diem": d, "muc": ket[0]["muc"]}, f"bản được chọn ({k})")
        if len(ket) > 1:
            print("\n   bản dự bị (trong thumbnail-du-bi/):")
            for x in ket[1:]:
                thua = min(x["muc"], key=lambda m: m["duoc"] / max(1, m["trong"]))
                print(f"      {x['kieu']} {x['ten']:14s} {x['diem']:5.1f}  "
                      f"thua ở: {cham_bia.TEN_VIET[thua['ten']]} — {thua['noi']}")
    except Exception:
        pass


# ══ DỰNG BÌA TỪ VIDEO ĐÃ ĐẨY LÊN ═══════════════════════════════════════════
# Hộp thành phẩm chỉ có `video.mp4` + `loi-binh.txt` — không còn thư mục ảnh. Muốn làm
# bìa cho video cũ thì phải lấy hình từ chính video.
#
# BẪY: video ĐÃ CÓ dải chữ đỏ + tiêu đề ở đáy. Trích nguyên khung rồi dán vào bìa là
# CHỒNG HAI LỚP CHỮ. Nên chỉ lấy phần ảnh phía trên dải, cắt theo đúng tỷ lệ template.

def _trich_khung(p_video, thu_ra, so=14):
    """Trích `so` khung rải đều, CẮT BỎ phần dải chữ ở đáy."""
    import subprocess
    dai = 0.0
    try:
        r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries",
                            "format=duration", "-of", "csv=p=0", p_video],
                           capture_output=True, text=True, timeout=60)
        dai = float((r.stdout or "0").strip() or 0)
    except Exception:
        pass
    if dai <= 1:
        return []
    ty_giu = float(L.get("hoa_den_ty_le", 0.70))     # phần ảnh, chưa có chữ
    os.makedirs(thu_ra, exist_ok=True)
    ra = []
    for i in range(so):
        t = dai * (i + 0.6) / (so + 0.2)
        p = os.path.join(thu_ra, f"k{i:02d}.jpg")
        try:
            subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-ss", f"{t:.2f}",
                            "-i", p_video, "-frames:v", "1",
                            "-vf", f"crop=iw:trunc(ih*{ty_giu:.4f}/2)*2:0:0",
                            "-q:v", "2", p], timeout=90)
            if os.path.exists(p) and os.path.getsize(p) > 20000:
                ra.append(p)
        except Exception:
            pass
    return ra


def _diem_khung(p):
    """Chấm khung hình: NÉT · SÁNG VỪA · NHIỀU CHI TIẾT. Thuần code, 0 token.

    Không có mô tả mắt máy như ảnh trong bài, nên chấm bằng thứ đo được: khung mờ (lúc
    chuyển cảnh), khung tối, khung phẳng (một mảng màu) đều bị loại.
    """
    import numpy as _np
    try:
        with Image.open(p) as im:
            g = _np.asarray(im.convert("L").resize((320, 180))).astype(_np.float32)
    except Exception:
        return -1
    # độ nét: sai phân bậc hai (xấp xỉ Laplacian, không cần scipy)
    lap = (g[1:-1, 2:] + g[1:-1, :-2] + g[2:, 1:-1] + g[:-2, 1:-1] - 4 * g[1:-1, 1:-1])
    net = float(lap.var())
    sang = float(g.mean())
    tuong_phan = float(g.std())
    d = min(net / 900.0, 1.0) * 55                       # nét là chính
    d += 25 if 55 <= sang <= 195 else (8 if 35 <= sang <= 215 else 0)
    d += min(tuong_phan / 62.0, 1.0) * 20
    return round(d, 1)


def lam_tu_video(hop, ra=None, kieu=None, tit=None):
    """Dựng bìa cho một VIDEO ĐÃ ĐẨY LÊN — lấy hình từ chính video ấy."""
    import shutil
    import tempfile
    p_video = os.path.join(hop, "video.mp4")
    if not os.path.exists(p_video):
        raise RuntimeError(f"không thấy video.mp4 trong {hop}")
    if tit is None:
        p_lb = os.path.join(hop, "loi-binh.txt")
        tit = open(p_lb, encoding="utf-8").readline().strip() if os.path.exists(p_lb) else ""
    if not tit:
        raise RuntimeError("không đọc được tiêu đề")

    tam = tempfile.mkdtemp(prefix="bia-")
    try:
        khung = _trich_khung(p_video, tam)
        if not khung:
            raise RuntimeError("không trích được khung hình nào từ video")
        khung.sort(key=_diem_khung, reverse=True)
        # bỏ khung sát nhau (thường cùng một cảnh) — lấy đa dạng hơn
        chon, da = [], set()
        for k in khung:
            i = int(os.path.basename(k)[1:3])
            if any(abs(i - j) <= 1 for j in da):
                continue
            chon.append(k)
            da.add(i)
            if len(chon) >= 4:
                break
        chon = chon or khung[:4]

        cao_anh = int(H * TY_ANH)
        kieu = (kieu or "C").upper()
        ten_kieu = next((k for k, v in NAO_MA.items() if v == kieu), kieu)
        nen = BO_CUC[kieu](chon, W, cao_anh, None)
        bia = Image.new("RGB", (W, H), (18, 14, 12))
        bia.paste(nen, (0, 0))
        bia.paste(_nen_mo(_mo(chon[0]), W, H - cao_anh), (0, cao_anh))
        cum = _loc_cum_vang(tit, _cum_vang_tu_tit(tit) or _tu_chon_cum_vang(tit))
        bia = _ve_dai_chu(bia, tit, cum)
        ra = ra or os.path.join(hop, "thumbnail.jpg")
        bia.save(ra, quality=93, subsampling=0)
        return ra, ten_kieu, len(chon)
    finally:
        shutil.rmtree(tam, ignore_errors=True)
