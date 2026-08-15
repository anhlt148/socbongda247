#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FOCUS-POP (resource_type: FocusPop) — học từ video mẫu BLV Anh Quân 0:20 (11/07/2026):
chủ thể tách nền SẮC NÉT nổi trên CHÍNH bức ảnh đó được phóng to + blur mạnh (bokeh sân vận động
phía sau), zoom chậm LỆCH PHA giữa nền và chủ thể (parallax) + hạt grain phim → 1 tấm ảnh action
tĩnh biến thành cảnh động sang như footage máy quay nét nông.

Dùng:  focus_pop.py --photo anh.jpg --out ra.mp4 [--seconds 6 --zoom-bg 1.14 --zoom-fg 1.06 --dark 0.72]
Cần: rembg + pillow + numpy (venv ~/.cache/claude-earth-venv) + ffmpeg."""
import argparse, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from player_spotlight import cutout                     # tái dùng máy tách nền (rembg u2net)

W, H = 1920, 1080


def cover(im, w, h, scale=1.0):
    """phủ kín khung w×h (crop giữa), nhân thêm scale."""
    r = max(w / im.width, h / im.height) * scale
    im2 = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x = (im2.width - w) // 2
    y = (im2.height - h) // 2
    return im2.crop((x, y, x + w, y + h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=6)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--zoom-bg", type=float, default=1.14, dest="zbg")
    ap.add_argument("--zoom-fg", type=float, default=1.06, dest="zfg")
    ap.add_argument("--blur", type=float, default=22)
    ap.add_argument("--dark", type=float, default=0.72, help="độ tối nền (1 = giữ nguyên)")
    ap.add_argument("--grain", type=float, default=0.5, help="0 = tắt hạt phim")
    a = ap.parse_args()
    a.seconds = max(5.0, a.seconds)          # SÀN 5s (luật anh Tuấn Anh 14/07): mọi sản phẩm ≥ 5 giây

    src = Image.open(a.photo).convert("RGB")
    cut = cutout(a.photo)                               # RGBA chủ thể
    # nền: chính ảnh đó, blur mạnh + tối bớt (bokeh)
    bg0 = cover(src, W, H, 1.0).filter(ImageFilter.GaussianBlur(a.blur))
    bg0 = Image.eval(bg0, lambda v: int(v * a.dark))
    # chủ thể: cắt sát, đặt giữa-thấp, cao ~96% khung
    bb = cut.getbbox()
    cut = cut.crop(bb)
    # làm MỀM mép cutout (feather 2px) — mép cứng lộ viền, bản mẫu chuyển rất mượt
    alpha = cut.split()[3].filter(ImageFilter.GaussianBlur(2)).point(lambda v: min(255, int(v * 1.06)))
    cut.putalpha(alpha)
    fh = int(H * 0.96)
    fw = int(cut.width * fh / cut.height)
    cut = cut.resize((fw, fh), Image.LANCZOS)

    n = int(a.seconds * a.fps)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(a.fps), "-i", "-",
                           "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    # vignette tính sẵn
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vig = np.clip(1 - 0.28 * np.clip(d - 0.55, 0, None), 0, 1)[..., None]

    for i in range(n):
        p = i / max(1, n - 1)
        # nền zoom NHANH hơn chủ thể một chút → cảm giác parallax nét nông
        zb = 1 + (a.zbg - 1) * p
        zf = 1 + (a.zfg - 1) * p
        frame = cover(bg0, W, H, zb)
        fw2, fh2 = int(cut.width * zf), int(cut.height * zf)
        c2 = cut.resize((fw2, fh2), Image.LANCZOS)
        frame.paste(c2, ((W - fw2) // 2, H - fh2), c2)   # chân chạm đáy khung
        arr = np.asarray(frame, dtype=np.float32)
        arr *= vig                                       # vignette
        if a.grain > 0:                                  # hạt phim + đốm bụi trắng thưa
            rng = np.random.default_rng(i)
            arr += rng.normal(0, 5.5 * a.grain, arr.shape).astype(np.float32)
            dots = rng.random((H, W)) > (1 - 0.00012 * a.grain)
            arr[dots] = np.minimum(arr[dots] + 160, 255)
        ff.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    print(f"✅ {a.out}  (focus-pop {a.seconds}s — nền bokeh + chủ thể nét + parallax + grain)")


if __name__ == "__main__":
    main()
