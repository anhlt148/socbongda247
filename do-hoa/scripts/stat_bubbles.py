#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STAT BUBBLES (resource_type: StatPop) — học từ video mẫu 11:46 (11/07/2026):
nhân vật cutout đứng giữa nền tối vignette, các VÒNG TRÒN KEM chứa SỐ LIỆU TO pop-in lần lượt
hai bên, SỐ ĐẾM LÊN từ 0. Thay card số liệu tĩnh khi muốn số liệu + con người trong cùng 1 cảnh.

Dùng:  stat_bubbles.py --photo cau_thu.jpg --out ra.mp4 \
         --stat "2700:Phút thi đấu" --stat "31:Bàn thắng" [--mau "#c0392b"] [--nen "#160b0b"]
Cần: rembg + pillow (venv ~/.cache/claude-earth-venv) + ffmpeg."""
import argparse, math, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from player_spotlight import cutout

SS = 2
W, H = 1920, 1080
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "assets", "fonts")


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), int(size))


def fit_font(txt, name, size, max_w, min_size=20):
    """Co cỡ chữ tới khi bề ngang ≤ max_w (chống tràn khỏi vòng tròn)."""
    size = int(size)
    while size > min_size:
        f = font(name, size)
        if f.getbbox(txt)[2] <= max_w:
            return f
        size -= 2
    return font(name, min_size)


def wrap_fit(txt, name, size, max_w, max_lines=2, min_size=16):
    """Vừa CO cỡ vừa XUỐNG DÒNG cho nhãn dài (vd 'BÓNG VÀNG LIÊN TIẾP') nằm gọn trong vòng."""
    words = txt.split()
    size = int(size)
    while size > min_size:
        f = font(name, size); lines = []; cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if f.getbbox(t)[2] <= max_w:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        if len(lines) <= max_lines and all(f.getbbox(l)[2] <= max_w for l in lines):
            return f, lines
        size -= 2
    return font(name, min_size), [txt]


def hexrgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def ease_pop(p):
    return min(1.06, 1.25 * math.sin(min(p, 1) * math.pi * 0.55)) if p < 1 else 1.0


def layout(n):
    """Bố cục CÂN theo SỐ LƯỢNG số liệu (anh Tuấn Anh 14/07): trả (tâm-x nhân vật, [(fx,fy)…], tỉ-lệ-R).
    Lỗi cũ: 4 vị trí cứng → 1 số liệu bị dí sát mép trái, phải trống. Nay tính theo N + tỷ lệ vàng
    (φ≈0.618), cân đều trái/phải cho mọi N:
    - N chẵn (2,4): nhân vật GIỮA, bubble chia đối xứng 2 bên → cân tuyệt đối.
    - N lẻ (1,3): nhân vật lệch phải ĐIỂM VÀNG (~0.63), bubble dồn cột TRÁI cách đều → khối cân nhau.
    R thu nhỏ khi nhiều bubble để không tràn/đè."""
    if n <= 1:
        return 0.63, [(0.30, 0.50)], 1.0
    if n == 2:
        return 0.50, [(0.185, 0.50), (0.815, 0.50)], 0.95
    if n == 3:
        return 0.65, [(0.265, 0.235), (0.265, 0.50), (0.265, 0.765)], 0.60
    return 0.50, [(0.185, 0.305), (0.815, 0.305), (0.185, 0.735), (0.815, 0.735)], 0.80


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stat", action="append", required=True, metavar="SO:NHAN",
                    help='vd "2700:Phút thi đấu" — lặp tối đa 4 lần')
    ap.add_argument("--mau", default="#c0392b")
    ap.add_argument("--nen", default="#160b0b")
    ap.add_argument("--seconds", type=float, default=6.5)
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    a.seconds = max(5.0, a.seconds)          # SÀN 5s (luật anh Tuấn Anh 14/07): mọi sản phẩm ≥ 5 giây
    mau = hexrgb(a.mau); nen = hexrgb(a.nen)
    stats = []
    for s in a.stat[:4]:
        so, _, nhan = s.partition(":")
        stats.append({"so": so.strip(), "nhan": nhan.strip()})

    # nền tối + vignette + chấm halftone mờ
    base = Image.new("RGB", (W * SS, H * SS), nen)
    dr0 = ImageDraw.Draw(base, "RGBA")
    for gy in range(0, H * SS, 26 * SS):
        for gx in range((gy // (26 * SS) % 2) * 13 * SS, W * SS, 26 * SS):
            dr0.ellipse([gx, gy, gx + 3 * SS, gy + 3 * SS], fill=(255, 255, 255, 7))
    vig = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(vig).ellipse([-W * SS * .2, -H * SS * .3, W * SS * 1.2, H * SS * 1.3], fill=48)
    vig = vig.filter(ImageFilter.GaussianBlur(160 * SS))
    base = Image.composite(Image.new("RGB", base.size, tuple(min(255, c + 26) for c in nen)), base, vig)

    cut = cutout(a.photo)
    bb = cut.getbbox(); cut = cut.crop(bb)
    alpha = cut.split()[3].filter(ImageFilter.GaussianBlur(2))
    cut.putalpha(alpha)
    fh = int(H * SS * 0.90)
    cut = cut.resize((int(cut.width * fh / cut.height), fh), Image.LANCZOS)

    subj_cx, vi_tri, rs = layout(len(stats))                  # bố cục cân theo số lượng số liệu
    # CHỐNG TRÀN MÉP (anh Tuấn Anh 16/07): dáng chạy/giang tay quá RỘNG bị cắt cụt ở mép phải.
    # Cap bề ngang chủ thể ≤ nửa-hơn khung (n=1) / hẹp hơn khi nhiều bubble → giữ trọn người trong khung.
    maxw = int(W * SS * (0.50 if len(stats) <= 1 else 0.40))
    if cut.width > maxw:
        cut = cut.resize((maxw, int(cut.height * maxw / cut.width)), Image.LANCZOS)
    MARGIN = int(0.03 * W * SS)                                # lề an toàn 2 mép
    f_so = font("BeVietnamPro-Black.ttf", int(96 * SS * rs))
    f_nh = font("BeVietnamPro-Bold.ttf", int(40 * SS * rs))
    R = int(215 * SS * rs)                                     # bán kính bubble (thu nhỏ khi nhiều)
    num_dy = int(26 * SS * rs); lab_dy = int(62 * SS * rs)     # lệch dọc số/nhãn theo cỡ bubble
    # CHỐNG TRÀN (anh Tuấn Anh 14/07): co cỡ + xuống dòng cho SỐ và NHÃN nằm gọn trong vòng tròn
    for st in stats:
        st["numf"] = fit_font(str(st["so"]), "BeVietnamPro-Black.ttf", 96 * SS * rs, int(R * 1.45))
        st["labf"], st["lablines"] = wrap_fit(st["nhan"], "BeVietnamPro-Bold.ttf", 40 * SS * rs, int(R * 1.42), 2)

    n = int(a.seconds * a.fps)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(a.fps), "-i", "-",
                           "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / a.fps
        im = base.copy()
        z = 1 + 0.02 * t / a.seconds
        c2 = cut.resize((int(cut.width * z), int(cut.height * z)), Image.LANCZOS)
        px = int(subj_cx * W * SS - c2.width / 2)
        px = min(px, W * SS - c2.width - MARGIN)              # không tràn mép phải
        px = max(px, MARGIN)                                  # không tràn mép trái
        im.paste(c2, (px, H * SS - c2.height), c2)
        dr = ImageDraw.Draw(im, "RGBA")
        for k, st in enumerate(stats):
            t0 = 0.9 + k * 0.8
            q = (t - t0) / 0.55
            if q <= 0:
                continue
            s = ease_pop(q)
            cx, cy = vi_tri[k][0] * W * SS, vi_tri[k][1] * H * SS
            r2 = int(R * min(s, 1.06))
            dr.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(246, 240, 226, 252),
                       outline=(20, 16, 14, 90), width=4 * SS)
            # SỐ ĐẾM LÊN trong 0.8s sau khi bubble hiện
            m = re.match(r"^(\d[\d.,]*)(.*)$", st["so"])
            if m and q > 0:
                digits = re.sub(r"[^\d]", "", m.group(1))
                target = int(digits) if digits else 0
                cnt = int(target * min(1, max(0, (t - t0) / 0.8)))
                so_txt = f"{cnt:,}".replace(",", ".") if len(digits) > 3 else str(cnt)
                so_txt += m.group(2)
            else:
                so_txt = st["so"]
            dr.text((cx, cy - num_dy), so_txt, font=st["numf"], fill=mau, anchor="mm")
            lines = st["lablines"]; lh = int(st["labf"].size * 1.06)
            y0 = cy + lab_dy - (len(lines) - 1) * lh // 2      # canh giữa khối nhãn nhiều dòng
            for li, ln in enumerate(lines):
                dr.text((cx, y0 + li * lh), ln, font=st["labf"], fill=(30, 26, 24), anchor="mm")
        ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())
    ff.stdin.close(); ff.wait()
    print(f"✅ {a.out}  (stat bubbles {a.seconds}s — {len(stats)} số liệu đếm lên)")


if __name__ == "__main__":
    main()
