#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LÀM CARD ĐỒ HOẠ cho video (bóng đá / sử-địa / kinh tế) — nét xịn, chữ Việt chuẩn, tự động hoá cao.

Kho stock KHÔNG có "card đối đầu 5 cúp–0", "đua Giày Vàng", "dòng thời gian", "số liệu đếm". Script
này tự dựng, 1920×1080 PNG, render 2× rồi thu nhỏ LANCZOS cho cạnh chữ MỊN như retina; tự canh cỡ chữ
để KHÔNG TRÀN khung; nền gradient điện ảnh tối; lề an toàn TV/điện thoại; font Be Vietnam Pro (đủ dấu
tiếng Việt, không ô vuông). Chạy bằng 1 file JSON chứa NHIỀU card → render cả loạt một lệnh.

Loại card:
  title       — thẻ tiêu đề lớn ("LẦN ĐẦU TIÊN TRONG LỊCH SỬ") + phụ đề + nhãn nhỏ.
  stat        — 1 con số KHỔNG LỒ + nhãn + chú ("36" / "BÀN THẮNG" / "kỷ lục Ngoại hạng").
  versus      — 2 phe đối đầu, mỗi phe tên + giá trị lớn + cờ; giữa là "VS". (Brazil 5 – 0 Na Uy)
  leaderboard — bảng xếp hạng có thanh giá trị (đua Giày Vàng: Messi 8, Haaland 7, Mbappé 7), tô sáng 1 dòng.
  compare     — so sánh 2-4 mục bằng thanh ngang (dân số, diện tích…).
  timeline    — dòng thời gian ngang, các mốc năm + chú thích (1981 → 1993 → 2026).

Dùng:
  python3 render_card.py cards.json                 # render mọi card trong file
  python3 render_card.py --one spec.json out.png    # render 1 card
Mỗi card là 1 object; xem references/mau-card.json để biết các trường. Cần: pillow + numpy (venv).
`--animate` (tuỳ chọn) cho stat/leaderboard/compare → xuất MP4 số đếm lên / thanh mọc dần.
"""
import argparse, json, math, os, re, subprocess, sys, tempfile, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

SS = 2                              # hệ số siêu lấy mẫu (render 2× → thu nhỏ cho nét)
# 4:3 thay vì 16:9 (anh chê 08/08: card ngang dẹt vào khung dọc 9:16 là thừa cả mảng nền
# trên dưới) — card cao hơn chiếm 810px thay 607px của dải ảnh, chữ nhìn lớn hẳn.
W, H = 1440, 1080
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
FLAGDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "flags")
FONT_FILE = {"regular": "BeVietnamPro-Regular.ttf", "semibold": "BeVietnamPro-SemiBold.ttf",
             "bold": "BeVietnamPro-Bold.ttf", "black": "BeVietnamPro-Black.ttf"}
# tên nước tiếng Việt/Anh → mã ISO của flagcdn (thêm nước mới vào đây khi cần)
# Kênh bóng đá ĐÔNG NAM Á mà bảng gốc không có nước ĐNÁ nào — anh gõ "Thái Lan" là mất cờ
# (06/08: card VN 5-0 Thái Lan ra thiếu cờ Thái). Bổ sung đủ ĐNÁ + châu Á + các nền lớn.
ISO = {"na uy": "no", "norway": "no", "brazil": "br", "brasil": "br", "anh": "gb-eng", "england": "gb-eng",
       "vietnam": "vn", "việt nam": "vn", "viet nam": "vn", "pháp": "fr", "france": "fr",
       "đức": "de", "germany": "de", "argentina": "ar", "tây ban nha": "es", "spain": "es",
       "bồ đào nha": "pt", "portugal": "pt", "ý": "it", "italy": "it", "hà lan": "nl", "netherlands": "nl",
       # Đông Nam Á
       "thái lan": "th", "thai lan": "th", "thailand": "th",
       "indonesia": "id", "campuchia": "kh", "cambodia": "kh",
       "malaysia": "my", "singapore": "sg", "philippines": "ph",
       "lào": "la", "lao": "la", "laos": "la", "myanmar": "mm",
       "brunei": "bn", "đông timor": "tl", "timor leste": "tl", "timor-leste": "tl",
       # châu Á hay gặp
       "hàn quốc": "kr", "han quoc": "kr", "korea": "kr", "south korea": "kr",
       "nhật bản": "jp", "nhat ban": "jp", "japan": "jp", "nhật": "jp",
       "trung quốc": "cn", "trung quoc": "cn", "china": "cn",
       "iraq": "iq", "iran": "ir", "qatar": "qa", "saudi arabia": "sa", "ả rập xê út": "sa",
       "uae": "ae", "úc": "au", "uc": "au", "australia": "au", "ấn độ": "in", "an do": "in",
       "uzbekistan": "uz", "triều tiên": "kp", "trieu tien": "kp", "north korea": "kp",
       # nền lớn khác
       "mỹ": "us", "my": "us", "usa": "us", "mexico": "mx", "nga": "ru", "russia": "ru",
       "bỉ": "be", "belgium": "be", "croatia": "hr", "morocco": "ma", "ma rốc": "ma",
       "uruguay": "uy", "colombia": "co", "chile": "cl", "nhật bản": "jp"}


def _khong_dau(s):
    import unicodedata as _u
    s = _u.normalize("NFD", s)
    return "".join(c for c in s if _u.category(c) != "Mn").replace("đ", "d")

_theme = {"bg_top": (12, 17, 33), "bg_bot": (4, 6, 12), "accent": (225, 29, 42),
          "text": (245, 247, 250), "sub": (150, 165, 185), "muted": (105, 118, 135),
          "panel": (255, 255, 255, 16)}

# 5 bảng màu NỀN (anh đặt 08/08: đổi random khi tạo thẻ cho khỏi nhàm) — đều là nền TỐI
# để chữ trắng + accent đỏ thương hiệu nổi như nhau trên cả 5. spec["nen"] chỉ định tay
# được; không chỉ định thì máy rút thăm, tránh lặp lại nền của card LIỀN TRƯỚC trong
# cùng một lần chạy.
NEN = {"navy":   ((12, 17, 33), (4, 6, 12)),     # xanh đêm — nền gốc của kênh
       "tim":    ((26, 13, 38), (9, 4, 15)),     # tím than
       "reu":    ((10, 27, 21), (3, 9, 7)),      # xanh rêu tối
       "vang":   ((36, 11, 17), (13, 3, 6)),     # đỏ rượu vang trầm
       "than":   ((23, 25, 30), (7, 8, 10))}     # xám than
_nen_truoc = [None]

def chon_nen(spec):
    import random as _rd
    ten = spec.get("nen")
    if ten not in NEN:
        con = [t for t in NEN if t != _nen_truoc[0]]
        ten = _rd.choice(con)
    _nen_truoc[0] = ten
    _theme["bg_top"], _theme["bg_bot"] = NEN[ten]
    return ten


def hexrgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))


def font(weight, size):
    return ImageFont.truetype(os.path.join(FONTS, FONT_FILE.get(weight, FONT_FILE["bold"])), int(size))


def tsize(draw, text, fnt):
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0], b[3] - b[1]


def fit_font(draw, text, weight, max_w, start, min_size=18):
    """Giảm cỡ chữ tới khi VỪA bề ngang max_w — chống tràn khung tuyệt đối."""
    s = start
    while s > min_size:
        f = font(weight, s)
        if tsize(draw, text, f)[0] <= max_w:
            return f
        s -= 2
    return font(weight, min_size)


def wrap(draw, text, fnt, max_w, toi_da=None):
    """Xuống dòng theo bề ngang; toi_da = số dòng tối đa — quá thì dòng cuối cắt '…'
    (không giới hạn là chú thích dài tràn xuống đáy card, anh dặn 08/08: phải mượt
    trong MỌI tình huống)."""
    words = text.split(); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if tsize(draw, t, fnt)[0] <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if toi_da and len(lines) > toi_da:
        lines = lines[:toi_da]
        lines[-1] = cat_ngan(draw, lines[-1] + "…", fnt, max_w)
    return lines


def cat_ngan(draw, text, fnt, max_w):
    """Chữ vẫn tràn dù đã co tới cỡ tối thiểu → cắt bớt + '…'. Tầng chống vỡ CUỐI CÙNG:
    thà mất vài ký tự cuối còn hơn chữ văng ra ngoài khung."""
    if tsize(draw, text, fnt)[0] <= max_w:
        return text
    while len(text) > 2 and tsize(draw, text + "…", fnt)[0] > max_w:
        text = text[:-1]
    return text + "…"


def vua_hoac_cat(draw, text, weight, max_w, start, min_size=24):
    """Co cỡ chữ tới khi vừa; co hết cỡ mà vẫn tràn thì cắt '…'. Trả (font, chữ đã xử)."""
    f = fit_font(draw, text, weight, max_w, start, min_size)
    return f, cat_ngan(draw, text, f, max_w)


def gradient_bg(accent):
    """Nền gradient dọc tối + quầng sáng accent mờ ở trên — chất điện ảnh."""
    top, bot = np.array(_theme["bg_top"]), np.array(_theme["bg_bot"])
    t = np.linspace(0, 1, H * SS)[:, None]
    arr = (top * (1 - t) + bot * t).astype(np.uint8)
    arr = np.repeat(arr[:, None, :], W * SS, axis=1)
    img = Image.fromarray(arr, "RGB").convert("RGB")
    # quầng accent mờ phía trên
    glow = Image.new("RGB", img.size, (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy, r = W * SS // 2, int(H * SS * 0.12), int(W * SS * 0.55)
    gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(c * 0.5) for c in accent))
    glow = glow.filter(ImageFilter.GaussianBlur(180 * SS // 2))
    img = Image.blend(img, ImageChops_screen(img, glow), 0.5)
    return img


def ImageChops_screen(a, b):
    from PIL import ImageChops
    return ImageChops.screen(a, b)


def draw_text(draw, xy, text, fnt, fill, anchor="la"):
    draw.text(xy, text, font=fnt, fill=fill, anchor=anchor)


def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)


def flag_img(name, h):
    """Trả ảnh cờ nước (bo góc) cao h px, tự tải từ flagcdn (cache). name = ISO ('no') hoặc tên nước."""
    t = str(name).strip().lower()
    # ba nấc: tra thẳng → tra bản bỏ dấu → nếu là mã 2 ký tự thì tin; còn lại BỎ CỜ,
    # đừng ghép chữ có dấu/khoảng trắng vào URL flagcdn rồi chết im (lỗi 06/08)
    code = ISO.get(t) or ISO.get(_khong_dau(t))
    if not code:
        if re.fullmatch(r"[a-z]{2}(-[a-z]{2,3})?", t):
            code = t
        else:
            return None
    os.makedirs(FLAGDIR, exist_ok=True)
    p = os.path.join(FLAGDIR, f"{code}.png")
    if not os.path.exists(p):
        try:
            req = urllib.request.Request(f"https://flagcdn.com/w320/{code}.png",
                                         headers={"User-Agent": "card-do-hoa/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r, open(p, "wb") as f:
                f.write(r.read())
        except Exception:
            return None
    try:
        fl = Image.open(p).convert("RGBA")
    except Exception:
        return None
    w = int(fl.width * h / fl.height)
    fl = fl.resize((w, h), Image.LANCZOS)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=int(h * 0.12), fill=255)
    fl.putalpha(mask)
    return fl


# Tên nước KHÔNG quét tự động — trùng từ tiếng Việt thường ("anh" đại từ, "ý" trong
# "chú ý", "lao" trong "lao động", "my"/"ma" âm tiết thường). Các nước này vẫn hiện cờ
# khi khai "flag" tay trong spec.
KHONG_TU_QUET = {"anh", "y", "ý", "my", "ma", "lao"}


def tim_co(*van_ban, toi_da=2):
    """Quét tên quốc gia trong chữ của card → mã cờ, để tự chèn cờ cho sinh động
    (anh đặt 08/08). Ưu tiên tên dài trước để 'việt nam' thắng 'nam'."""
    chu = " ".join(v for v in van_ban if v).lower()
    ra = []
    for ten in sorted(ISO, key=len, reverse=True):
        if ten in KHONG_TU_QUET or len(_khong_dau(ten)) < 4 and " " not in ten:
            continue
        if re.search(rf"(?<![\wàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
                     rf"ùúủũụưừứửữựỳýỷỹỵđ]){re.escape(ten)}(?![\wàáảãạăằắẳẵặâầấẩẫậ"
                     rf"èéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ])", chu):
            ma = ISO[ten]
            if ma not in ra:
                ra.append(ma)
            chu = chu.replace(ten, " ")          # tên đã ăn cờ thì xoá, tránh trùng lặp
        if len(ra) >= toi_da:
            break
    return ra


def dan_hang_co(img, ds_ma, cx, cy, cao):
    """Dán một hàng cờ (căn giữa tại cx) — trả bề rộng đã chiếm, 0 nếu không có cờ."""
    anh_co = [c for c in (flag_img(m, cao) for m in ds_ma) if c]
    if not anh_co:
        return 0
    khe = int(cao * 0.35)
    rong = sum(c.width for c in anh_co) + khe * (len(anh_co) - 1)
    x = cx - rong // 2
    for c in anh_co:
        img.paste(c, (x, cy - c.height // 2), c)
        x += c.width + khe
    return rong


# ---------- các loại card ----------
def card_title(img, d, spec):
    acc = _theme["accent"]; m = int(W * SS * 0.10)
    if spec.get("kicker"):
        f = font("bold", 34 * SS)
        draw_text(d, (m, int(H * SS * 0.30)), spec["kicker"].upper(), f, acc, "lm")
    title = spec.get("title", "")
    f = fit_font(d, title, "black", W * SS - 2 * m, 150 * SS)
    lines = wrap(d, title, f, W * SS - 2 * m)
    lh = tsize(d, "Ag", f)[1] * 1.22
    y = H * SS // 2 - lh * len(lines) / 2
    for ln in lines:
        draw_text(d, (m, y), ln, f, _theme["text"], "lm"); y += lh
    d.rounded_rectangle([m, y + 10 * SS, m + 120 * SS, y + 20 * SS], radius=6 * SS, fill=acc)
    if spec.get("subtitle"):
        f2 = fit_font(d, spec["subtitle"], "semibold", W * SS - 2 * m, 44 * SS)
        draw_text(d, (m, y + 55 * SS), spec["subtitle"], f2, _theme["sub"], "lm")


def card_stat(img, d, spec):
    acc = _theme["accent"]
    # cờ tự nhận từ chữ trên thẻ (anh đặt 08/08) — có cờ thì đội hàng đầu, chữ hạ nhẹ xuống
    co = tim_co(spec.get("label", ""), spec.get("note", ""))
    co_cao = dan_hang_co(img, co, W * SS // 2, int(H * SS * 0.11), 72 * SS) if co else 0
    y_label = 0.25 if co_cao else 0.20
    num = str(spec.get("value", ""))
    f = fit_font(d, num, "black", int(W * SS * 0.86), 440 * SS)
    draw_text(d, (W * SS // 2, int(H * SS * 0.52)), num, f, _theme["text"], "mm")
    if spec.get("label"):
        # nhãn/ghi chú dài: co tới ngưỡng đọc được rồi xuống dòng (tối đa 2), không co vô hạn
        fl = fit_font(d, spec["label"].upper(), "bold", int(W * SS * 0.86), 76 * SS, min_size=44)
        for j, ln in enumerate(wrap(d, spec["label"].upper(), fl, int(W * SS * 0.86), toi_da=2)):
            draw_text(d, (W * SS // 2, int(H * SS * y_label) + j * int(80 * SS)), ln, fl, acc, "mm")
    if spec.get("note"):
        fn = fit_font(d, spec["note"], "semibold", int(W * SS * 0.86), 50 * SS, min_size=34)
        for j, ln in enumerate(wrap(d, spec["note"], fn, int(W * SS * 0.86), toi_da=2)):
            draw_text(d, (W * SS // 2, int(H * SS * 0.82) + j * int(56 * SS)), ln, fn, _theme["sub"], "mm")


def _side(img, d, cx, name, value, flag, acc, highlight=False):
    top = int(H * SS * 0.30)
    fl = flag_img(flag, 90 * SS) if flag else None
    if fl:
        img.paste(fl, (cx - fl.width // 2, top), fl)
    fn, chu_ten = vua_hoac_cat(d, str(name).upper(), "bold", int(W * SS * 0.40), 72 * SS,
                               min_size=36)
    draw_text(d, (cx, top + 130 * SS), chu_ten, fn, _theme["text"], "mm")
    fv, chu_v = vua_hoac_cat(d, str(value), "black", int(W * SS * 0.38), 210 * SS)
    draw_text(d, (cx, int(H * SS * 0.62)), chu_v, fv, acc if highlight else _theme["text"], "mm")


def card_versus(img, d, spec):
    acc = _theme["accent"]
    L, R = spec["left"], spec["right"]
    if spec.get("title"):
        ft, chu_t = vua_hoac_cat(d, spec["title"].upper(), "bold", int(W * SS * 0.86),
                                 56 * SS, min_size=38)
        draw_text(d, (W * SS // 2, int(H * SS * 0.12)), chu_t, ft, _theme["sub"], "mm")
    # không khai cờ thì thử tra theo TÊN — tên là quốc gia thì tự ra cờ (anh đặt 08/08)
    _side(img, d, int(W * SS * 0.26), L["name"], L.get("value", ""),
          L.get("flag") or L["name"], acc, L.get("win"))
    _side(img, d, int(W * SS * 0.74), R["name"], R.get("value", ""),
          R.get("flag") or R["name"], acc, R.get("win"))
    fv = font("black", 96 * SS)
    draw_text(d, (W * SS // 2, int(H * SS * 0.50)), "VS", fv, acc, "mm")


def _so_an_toan(v):
    """'10' → 10.0; '3-1', 'DNF', None → None. Máy gợi hay điền số dạng chữ — float()
    thẳng tay là sập cả card (chống vỡ 08/08)."""
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def card_leaderboard(img, d, spec):
    acc = _theme["accent"]; m = int(W * SS * 0.12)
    # BXH thì điểm cao ĐỨNG TRÊN — máy tự sắp, không tin mù thứ tự đầu vào (anh bắt
    # 08/08: Indonesia 7 điểm đứng trên Singapore 8 điểm). Sắp ỔN ĐỊNH: bằng điểm giữ
    # thứ tự người khai (người đã xếp theo hiệu số). Bảng cố ý không theo điểm
    # (hạng do tiêu chí khác quyết) thì khai "giu_thu_tu": true.
    # Giá trị KHÔNG phải số ("3-1") → không sắp, không vẽ vạch dài ngắn — chỉ ghi chữ.
    rows = spec.get("rows") or []
    if not rows:
        return
    du_so = all(_so_an_toan(r.get("value")) is not None for r in rows)
    if du_so and not spec.get("giu_thu_tu"):
        rows = sorted(rows, key=lambda r: -_so_an_toan(r["value"]))
    if spec.get("title"):
        ft, chu_t = vua_hoac_cat(d, spec["title"].upper(), "black", W * SS - 2 * m, 60 * SS,
                                 min_size=40)
        draw_text(d, (m, int(H * SS * 0.14)), chu_t, ft, _theme["text"], "lm")
    mx = max((_so_an_toan(r["value"]) or 0 for r in rows), default=1) or 1
    n = len(rows); top = int(H * SS * 0.28); gap = int(H * SS * 0.62 / n)
    # đông hàng thì chữ + cờ + vạch co theo khe, không thì hàng nọ đè hàng kia
    co_chu = min(46 * SS, int(gap * 0.52))
    barx = m + int(W * SS * 0.24); barw = int(W * SS * 0.44)
    for i, r in enumerate(rows):
        y = top + i * gap; hl = r.get("highlight")
        fr = font("black", co_chu)
        draw_text(d, (m, y), f"{i+1}", fr, acc if hl else _theme["muted"], "lm")
        # tên là quốc gia thì dán cờ nhỏ trước tên cho sinh động (anh đặt 08/08)
        x_ten = m + 60 * SS
        co = flag_img(r.get("flag") or r.get("name", ""), min(44 * SS, int(gap * 0.5)))
        if co:
            img.paste(co, (x_ten, y - co.height // 2), co)
            x_ten += co.width + 16 * SS
        fn, chu_ten = vua_hoac_cat(d, str(r.get("name", "")), "bold",
                                   barx - x_ten - 20 * SS, co_chu)
        draw_text(d, (x_ten, y), chu_ten, fn, _theme["text"], "lm")
        bh = max(int(gap * 0.42), 8 * SS)
        d.rounded_rectangle([barx, y - bh // 2, barx + barw, y + bh // 2], radius=bh // 2, fill=(38, 46, 64))
        so = _so_an_toan(r.get("value"))
        vw = int(barw * max(so, 0) / mx) if so is not None else 0
        d.rounded_rectangle([barx, y - bh // 2, barx + max(vw, bh), y + bh // 2], radius=bh // 2,
                            fill=acc if hl else (110, 125, 145))
        fv, chu_v = vua_hoac_cat(d, str(r.get("value", "")), "black",
                                 W * SS - (barx + barw + 30 * SS) - 20 * SS, co_chu)
        draw_text(d, (barx + barw + 30 * SS, y), chu_v, fv, _theme["text"], "lm")


def card_compare(img, d, spec):
    card_leaderboard(img, d, {**spec, "rows": [{"name": r["name"], "value": r["value"],
                     "highlight": r.get("highlight")} for r in spec["rows"]]})


def _ve_giua_kep(d, x, y, text, fnt, fill, lo, hi):
    """Vẽ chữ căn giữa tại x nhưng KẸP trong vùng [lo, hi] — mốc đầu/cuối timeline đứng
    sát mép, căn giữa mù quáng là nửa chữ văng ra ngoài khung (anh bắt 08/08: 'ASEAN Cup
    2024' cụt đầu). Vùng theo TỪNG MỐC chứ không toàn khung: kẹp toàn khung làm chú thích
    hai mốc dài trườn về giữa rồi ĐÈ LÊN NHAU."""
    w = tsize(d, text, fnt)[0]
    x = max(lo + w // 2, min(x, hi - w // 2))
    draw_text(d, (x, y), text, fnt, fill, "mm")


def card_timeline(img, d, spec):
    acc = _theme["accent"]; m = int(W * SS * 0.10)
    y_title = int(H * SS * 0.20)
    if spec.get("title"):
        # tên nước trong tít → dán cờ ngay sau chữ cho sinh động (anh đặt 08/08)
        co = [flag_img(ma, 58 * SS) for ma in tim_co(spec["title"])]
        co = [c for c in co if c]
        cho_co = sum(c.width + 22 * SS for c in co)
        # tít dài quá 1 dòng thì xuống dòng (tối đa 2) — co mãi là chữ bé không đọc nổi
        ft = fit_font(d, spec["title"].upper(), "black", W * SS - 2 * m - cho_co, 66 * SS,
                      min_size=44)
        dong_t = wrap(d, spec["title"].upper(), ft, W * SS - 2 * m - cho_co, toi_da=2)
        for j, ln in enumerate(dong_t):
            draw_text(d, (m, y_title + j * int(74 * SS)), ln, ft, _theme["text"], "lm")
        x_co = m + tsize(d, dong_t[0], ft)[0] + 26 * SS
        for c in co:
            img.paste(c, (x_co, y_title - c.height // 2), c)
            x_co += c.width + 22 * SS
    pts = spec.get("points") or []
    n = len(pts); y = int(H * SS * 0.60)
    x0, x1 = m + 40 * SS, W * SS - m - 40 * SS
    le = int(W * SS * 0.035)                         # lề mép khung cho chữ
    d.line([(x0, y), (x1, y)], fill=(90, 100, 120), width=4 * SS)
    xs = [x0 + (x1 - x0) * i // max(1, n - 1) for i in range(n)]
    for i, p in enumerate(pts):
        x = xs[i]
        # PHẦN ĐẤT của mốc: từ điểm giữa với mốc trước đến điểm giữa với mốc sau —
        # chữ mốc nào ở yên đất mốc đó, không trườn sang hàng xóm
        lo = le if i == 0 else (xs[i - 1] + x) // 2 + 10 * SS
        hi = W * SS - le if i == n - 1 else (x + xs[i + 1]) // 2 - 10 * SS
        d.ellipse([x - 16 * SS, y - 16 * SS, x + 16 * SS, y + 16 * SS], fill=acc)
        # Chuỗi chống vỡ đủ ba tầng (anh chốt 08/08 — mượt trong MỌI tình huống):
        # ① fit_font co cỡ theo phần đất → ② co hết cỡ vẫn tràn thì cắt "…" →
        # ③ kẹp toạ độ trong đất. Nhiều mốc thì đất hẹp, cả ba tầng đều phải sống.
        fy, chu_nam = vua_hoac_cat(d, str(p.get("year", "")), "black", hi - lo, 62 * SS,
                                   min_size=28)
        _ve_giua_kep(d, x, y - 62 * SS, chu_nam, fy, _theme["text"], lo, hi)
        cap = p.get("caption", "")
        fc = font("semibold", 38 * SS) if n <= 3 else font("semibold", 32 * SS)
        cao_dong = 47 * SS if n <= 3 else 40 * SS
        for j, ln in enumerate(wrap(d, cap, fc, hi - lo, toi_da=3)):
            _ve_giua_kep(d, x, y + 52 * SS + j * cao_dong, ln, fc, _theme["sub"], lo, hi)


RENDER = {"title": card_title, "stat": card_stat, "versus": card_versus,
          "leaderboard": card_leaderboard, "compare": card_compare, "timeline": card_timeline}


def to_doc(img16, zone=(0.0, 1.0)):
    """Card ngang 1920x1080 -> khung DỌC 1080x1920: nền = chính card phóng to+làm mờ (tối nhẹ),
    card sắc canh giữa trong VÙNG cho phép `zone`=(trên,dưới) theo tỉ lệ chiều cao.
    VD zone=(0,0.70): card chỉ nằm 70% trên, chừa 30% dưới cho khung tiêu đề của short."""
    VW, VH = 1080, 1920
    bg = ImageOps.fit(img16, (VW, VH), method=Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (VW, VH), (0, 0, 0)), 0.40)
    fh = int(img16.height * VW / img16.width)                      # 1080 x 607
    fg = img16.resize((VW, fh), Image.LANCZOS)
    z0, z1 = int(zone[0] * VH), int(zone[1] * VH)                  # dải cho phép đặt card
    y = z0 + (z1 - z0 - fh) // 2                                   # canh giữa TRONG dải
    y = max(0, min(y, VH - fh))
    canvas = bg.copy()
    canvas.paste(fg, (0, y))
    return canvas


def render_one(spec, out_path, doc=False, zone=(0.0, 1.0)):
    if spec.get("accent"):
        _theme["accent"] = hexrgb(spec["accent"])
    chon_nen(spec)                       # rút thăm 1 trong 5 nền (spec["nen"] ép tay được)
    img = gradient_bg(_theme["accent"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    fn = RENDER.get(spec["type"])
    if not fn:
        raise SystemExit(f"Loại card không hỗ trợ: {spec['type']}")
    fn(img, d, spec)
    img = img.convert("RGB").resize((W, H), Image.LANCZOS)      # thu nhỏ 2×→1× cho nét
    if doc:                                                     # khung dọc 9:16 cho short/reels
        img = to_doc(img, zone)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards", nargs="?", help="File JSON danh sách card (mỗi card có 'out').")
    ap.add_argument("--one", help="File JSON 1 card.")
    ap.add_argument("--out", help="Đường dẫn ra (dùng với --one).")
    ap.add_argument("--doc", action="store_true", help="Xuất khung DỌC 9:16 (1080x1920) cho short/reels/tiktok.")
    ap.add_argument("--doc-vung", default="0,1", help="Dải đặt card theo tỉ lệ cao 'trên,dưới' (vd 0,0.70 = chừa 30%% dưới cho tiêu đề).")
    args = ap.parse_args()
    zone = tuple(float(x) for x in args.doc_vung.split(","))
    if args.one:
        spec = json.load(open(args.one, encoding="utf-8"))
        print("OK:", render_one(spec, args.out or spec.get("out", "card.png"), doc=args.doc, zone=zone))
        return
    specs = json.load(open(args.cards, encoding="utf-8"))
    if isinstance(specs, dict):
        specs = specs.get("cards", [specs])
    for i, spec in enumerate(specs):
        out = spec.get("out") or f"card_{i:02d}.png"
        _theme["accent"] = hexrgb(specs[0].get("accent", "#e11d2a")) if isinstance(specs, list) else _theme["accent"]
        print("✅", render_one(spec, out, doc=args.doc, zone=zone))


if __name__ == "__main__":
    main()
