#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CARD TIN NÓNG ĐỘNG (resource_type: News) — headline đập + ticker chạy, kiểu bản tin thể thao.
Tài nguyên TỰ TẠO 100% cho dạng video tin bóng đá / thông báo / chuyển nhượng.

Dùng:  python3 breaking_news.py tin.json [-o out.mp4]
JSON: { "ten":"tin_haaland", "tag":"TIN NÓNG", "tieu_de":"HAALAND LẬP CÚ ĐÚP VÀO LƯỚI BRAZIL",
        "phu_de":"Tứ kết World Cup 2026 · Na Uy 2-1 Brazil",
        "ticker":"NA UY VÀO BÁN KẾT · HAALAND 8 BÀN SAU 5 TRẬN · ĐỐI THỦ KẾ TIẾP: ANH",
        "mau":"#e11d2a", "seconds":6, "fps":30 }
Cần: pillow (venv ~/.cache/claude-earth-venv) + ffmpeg."""
import argparse, json, math, os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SS = 2
W, H = 1920, 1080
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "assets", "fonts")


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), int(size))


def hexrgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def ease_out(p):
    return 1 - (1 - p) ** 3


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


def nen(accent):
    """nền tối + lưới mờ + quầng màu accent (vẽ 1 lần)."""
    im = Image.new("RGB", (W * SS, H * SS), (7, 10, 18))
    dr = ImageDraw.Draw(im, "RGBA")
    for x in range(0, W * SS, 64 * SS):
        dr.line([(x, 0), (x, H * SS)], fill=(255, 255, 255, 9), width=1)
    for y in range(0, H * SS, 64 * SS):
        dr.line([(0, y), (W * SS, y)], fill=(255, 255, 255, 9), width=1)
    glow = Image.new("RGB", im.size, (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * SS * .55, -H * SS * .45, W * SS * 1.25, H * SS * .5],
               fill=tuple(int(c * 0.5) for c in accent))
    glow = glow.filter(ImageFilter.GaussianBlur(160 * SS))
    from PIL import ImageChops
    return ImageChops.screen(im, glow)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("-o", "--out", default="")
    a = ap.parse_args()
    sp = json.load(open(a.spec, encoding="utf-8"))
    fps = int(sp.get("fps", 30)); secs = max(5.0, float(sp.get("seconds", 6)))   # SÀN 5s (anh Tuấn Anh 14/07)
    n = int(fps * secs)
    accent = hexrgb(sp.get("mau", "#e11d2a"))
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.spec)), f"{sp.get('ten','tin')}.mp4")

    f_tag = font("BeVietnamPro-Black.ttf", 40 * SS)
    f_tit = font("BeVietnamPro-Black.ttf", 92 * SS)
    f_phu = font("BeVietnamPro-SemiBold.ttf", 40 * SS)
    f_tk = font("BeVietnamPro-Bold.ttf", 34 * SS)

    base = nen(accent)
    dr0 = ImageDraw.Draw(base)
    # đo trước để canh giữa khối chữ
    lines = wrap(dr0, sp.get("tieu_de", "").upper(), f_tit, W * SS * 0.84)
    lh = int(108 * SS)
    y_tit0 = int(H * SS * 0.40) - lh * (len(lines) - 1) // 2

    tk_text = ("  ·  ".join([sp.get("ticker", "")] * 3) + "  ·  ") if sp.get("ticker") else ""
    tk_w = dr0.textbbox((0, 0), tk_text, font=f_tk)[2] if tk_text else 1

    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                           "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / fps
        im = base.copy()
        dr = ImageDraw.Draw(im, "RGBA")
        # TAG "TIN NÓNG" trượt vào từ trái (0→0.5s) + nhịp thở nhẹ
        p1 = ease_out(min(1, t / 0.5))
        pulse = 1 + 0.03 * math.sin(t * 4.4)
        tag = (sp.get("tag") or "TIN NÓNG").upper()
        tw = dr.textbbox((0, 0), tag, font=f_tag)[2]
        bx = int(-tw * 1.3 + (W * SS * 0.08 + tw * 1.3) * p1)
        bh = int(72 * SS * pulse)
        by = int(H * SS * 0.235)
        dr.rectangle([bx - 26 * SS, by - bh // 2, bx + tw + 26 * SS, by + bh // 2], fill=accent)
        dr.text((bx, by), tag, font=f_tag, fill=(255, 255, 255), anchor="lm")
        # HEADLINE trượt lên + hiện dần (0.3→1.1s)
        p2 = ease_out(min(1, max(0, (t - 0.3) / 0.8)))
        off = int((1 - p2) * 70 * SS)
        alp = int(255 * p2)
        for li, ln in enumerate(lines):
            dr.text((W * SS * 0.08, y_tit0 + li * lh + off + 5 * SS), ln, font=f_tit,
                    fill=(0, 0, 0, min(alp, 160)), anchor="lm")          # bóng đổ
            dr.text((W * SS * 0.08, y_tit0 + li * lh + off), ln, font=f_tit,
                    fill=(245, 247, 250, alp), anchor="lm")
        # gạch accent + PHỤ ĐỀ (0.8→1.5s)
        p3 = ease_out(min(1, max(0, (t - 0.8) / 0.7)))
        y_phu = y_tit0 + len(lines) * lh + 8 * SS
        dr.rectangle([W * SS * 0.08, y_phu - 3 * SS, W * SS * 0.08 + W * SS * 0.30 * p3, y_phu + 3 * SS], fill=accent)
        if sp.get("phu_de"):
            dr.text((W * SS * 0.08, y_phu + 44 * SS), sp["phu_de"], font=f_phu,
                    fill=(165, 178, 195, int(255 * p3)), anchor="lm")
        # TICKER chạy đáy
        if tk_text:
            dr.rectangle([0, H * SS - 92 * SS, W * SS, H * SS], fill=(4, 6, 12, 235))
            dr.rectangle([0, H * SS - 96 * SS, W * SS, H * SS - 92 * SS], fill=accent)
            x0 = -int((t * 170 * SS) % (tk_w / 3))
            dr.text((x0, H * SS - 46 * SS), tk_text, font=f_tk, fill=(220, 228, 238), anchor="lm")
        ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())
    ff.stdin.close(); ff.wait()
    print(f"✅ {out}  ({secs}s · card tin nóng tự tạo)")


if __name__ == "__main__":
    main()
