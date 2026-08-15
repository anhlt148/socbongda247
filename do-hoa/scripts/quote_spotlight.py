#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QUOTE-SPOTLIGHT (resource_type: Quote) — học từ video mẫu BLV Anh Quân 5:49 (11/07/2026):
nhân vật tách nền đứng trên NỀN MÀU PHẲNG đậm có hoạ tiết dấu +, bên cạnh là KHỐI TRÍCH DẪN
bo viền trắng, chữ HIỆN DẦN TỪNG DÒNG — đúng kỹ thuật "chìa bằng chứng" (trích phát ngôn
cầu thủ/HLV/báo chí) của kênh phân tích bóng đá.

Dùng:  quote_spotlight.py --photo cau_thu.jpg --quote "..." [--author "The Athletic"]
       [--bg "#4a0e12" --out ra.mp4 --seconds 7]
Cần: rembg + pillow (venv ~/.cache/claude-earth-venv) + ffmpeg."""
import argparse, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from player_spotlight import cutout

SS = 2
W, H = 1920, 1080
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "assets", "fonts")


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), int(size))


def hexrgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def ease(p):
    return p * p * (3 - 2 * p)


def wrap(dr, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        thu = (cur + " " + w).strip()
        if dr.textbbox((0, 0), thu, font=fnt)[2] <= max_w:
            cur = thu
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True)
    ap.add_argument("--quote", required=True)
    ap.add_argument("--author", default="")
    ap.add_argument("--bg", default="#4a0e12")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=7)
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    a.seconds = max(5.0, a.seconds)          # SÀN 5s (luật anh Tuấn Anh 14/07): mọi sản phẩm ≥ 5 giây
    bgc = hexrgb(a.bg)

    # nền phẳng + hoạ tiết dấu + (vẽ 1 lần)
    base = Image.new("RGB", (W * SS, H * SS), bgc)
    dr0 = ImageDraw.Draw(base, "RGBA")
    for gy in range(0, H * SS, 130 * SS):
        for gx in range((gy // (130 * SS) % 2) * 65 * SS, W * SS, 130 * SS):
            L = 9 * SS
            dr0.line([(gx - L, gy), (gx + L, gy)], fill=(255, 255, 255, 26), width=2 * SS)
            dr0.line([(gx, gy - L), (gx, gy + L)], fill=(255, 255, 255, 26), width=2 * SS)
    # bóng sàn nhẹ dưới chân nhân vật
    dr0.ellipse([W * SS * 0.06, H * SS * 0.92, W * SS * 0.44, H * SS * 1.02], fill=(0, 0, 0, 70))

    cut = cutout(a.photo)
    bb = cut.getbbox(); cut = cut.crop(bb)
    fh = int(H * SS * 0.9)
    cut = cut.resize((int(cut.width * fh / cut.height), fh), Image.LANCZOS)

    f_q = font("BeVietnamPro-Bold.ttf", 46 * SS)
    f_a = font("BeVietnamPro-Regular.ttf", 32 * SS)
    dr_tmp = ImageDraw.Draw(base)
    box_x, box_w = int(W * SS * 0.42), int(W * SS * 0.52)
    pad = 36 * SS
    lines = wrap(dr_tmp, f'“{a.quote}”', f_q, box_w - 2 * pad)
    lh = int(64 * SS)
    box_h = pad * 2 + lh * len(lines) + (52 * SS if a.author else 0)
    box_y = int(H * SS * 0.38) - box_h // 2 + int(H * SS * 0.06)

    n = int(a.seconds * a.fps)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(a.fps), "-i", "-",
                           "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / a.fps
        im = base.copy()
        dr = ImageDraw.Draw(im, "RGBA")
        # nhân vật trượt vào từ trái (0→0.8s) + thở zoom rất nhẹ
        p1 = ease(min(1, t / 0.8))
        z = 1 + 0.025 * (t / a.seconds)
        c2 = cut.resize((int(cut.width * z), int(cut.height * z)), Image.LANCZOS)
        cx = int(-c2.width * 0.6 + (W * SS * 0.05 + c2.width * 0.6) * p1)
        im.paste(c2, (cx, H * SS - c2.height + int(H * SS * 0.02)), c2)
        # khung trích dẫn vẽ viền chạy (0.5→1.2s)
        p2 = ease(min(1, max(0, (t - 0.5) / 0.7)))
        if p2 > 0:
            dr.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=22 * SS,
                                 outline=(255, 255, 255, int(255 * p2)), width=5 * SS)
        # chữ hiện DẦN TỪNG DÒNG (bắt đầu 1.0s, mỗi dòng 0.45s)
        for li, ln in enumerate(lines):
            p3 = ease(min(1, max(0, (t - 1.0 - li * 0.45) / 0.5)))
            if p3 <= 0:
                continue
            dr.text((box_x + pad, box_y + pad + li * lh + int((1 - p3) * 14 * SS)), ln,
                    font=f_q, fill=(255, 255, 255, int(255 * p3)), anchor="la")
        if a.author:
            p4 = ease(min(1, max(0, (t - 1.0 - len(lines) * 0.45) / 0.6)))
            if p4 > 0:
                dr.text((box_x + pad, box_y + box_h - pad - 18 * SS), "— " + a.author,
                        font=f_a, fill=(235, 205, 160, int(255 * p4)), anchor="lm")
        ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())
    ff.stdin.close(); ff.wait()
    print(f"✅ {a.out}  (quote-spotlight {a.seconds}s — cutout + trích dẫn hiện từng dòng)")


if __name__ == "__main__":
    main()
