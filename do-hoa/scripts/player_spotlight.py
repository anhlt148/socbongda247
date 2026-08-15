#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ẢNH CẦU THỦ XÓA NỀN trên LƯỚI ĐEN CHUYỂN ĐỘNG → MP4 (kiểu kênh phân tích bóng đá hay dùng).

Tự tải ảnh cầu thủ (Wikipedia), XÓA NỀN (rembg), ghép lên nền lưới tối cuộn + quầng sáng accent + rim
sáng quanh người + zoom chậm cho "sống" → clip 1920×1080 để chèn intro/điểm nhấn/tiết lộ số liệu.

Dùng:
  python3 player_spotlight.py --player "Erling Haaland" --out haaland_spotlight.mp4 --accent "#e11d2a"
  python3 player_spotlight.py --photo anh_cauthu.png --out out.mp4        # tự đưa ảnh
Tuỳ chọn: --seconds 5 --fps 30 --accent "#e11d2a" --side center|left|right
Cần: rembg + pillow + numpy + ffmpeg (venv ~/.cache/claude-earth-venv).
"""
import argparse, io, json, os, subprocess, sys, tempfile, urllib.parse, urllib.request
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

W, H = 1920, 1080
UA = {"User-Agent": "player-spotlight/1.0 (football video)"}


def hexrgb(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))


def fetch_player(name, dst):
    """Lấy ảnh chính của cầu thủ từ Wikipedia (pageimages original)."""
    api = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "titles": name, "prop": "pageimages", "piprop": "original",
         "format": "json", "redirects": 1})
    with urllib.request.urlopen(urllib.request.Request(api, headers=UA), timeout=25) as r:
        data = json.load(r)
    pages = data.get("query", {}).get("pages", {})
    for p in pages.values():
        url = p.get("original", {}).get("source")
        if url:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as im:
                open(dst, "wb").write(im.read())
            return dst
    return None


def cutout(photo_path):
    """Xóa nền → RGBA chỉ còn cầu thủ, cắt sát khung."""
    from rembg import remove
    src = Image.open(photo_path).convert("RGBA")
    out = remove(src)
    bbox = out.getbbox()
    return out.crop(bbox) if bbox else out


GRID_DIRS = {"ltr": (-1.0, 0.0), "rtl": (1.0, 0.0), "up": (0.0, 1.0),
             "down": (0.0, -1.0), "diag": (-1.0, -0.6)}


def grid_bg(t, accent, gdir="ltr"):
    """1 khung nền: lưới tối CHẠY theo hướng (ltr=trái→phải, rtl=phải→trái, up/down/diag) + quầng
    accent + vignette. Trả mảng uint8 HxWx3."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.zeros((H, W, 3), np.float32)
    base[..., 0] = 8; base[..., 1] = 11; base[..., 2] = 20            # nền xanh đen
    G = 70.0; lw = 2.0; sp = 60.0                                     # bước lưới, độ dày, tốc độ chạy
    dx, dy = GRID_DIRS.get(gdir, (-1.0, 0.0))
    ox = (t * sp * dx) % G; oy = (t * sp * dy) % G
    line = (((xx + ox) % G < lw) | ((yy + oy) % G < lw)).astype(np.float32)
    depth = np.clip(yy / H, 0.15, 1.0)                                # lưới rõ dần xuống dưới
    gcol = np.array([70, 84, 110], np.float32)
    base += line[..., None] * gcol[None, None, :] * depth[..., None] * 0.5
    # quầng sáng accent giữa-dưới
    cx, cy = W * 0.5, H * 0.62
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    glow = np.exp(-d2 / (2 * (W * 0.26) ** 2))
    base += glow[..., None] * np.array(accent, np.float32)[None, None, :] * 0.34
    vig = 1 - 0.55 * np.clip(((xx - cx) ** 2 / (W * 0.62) ** 2 + (yy - H * 0.5) ** 2 / (H * 0.62) ** 2), 0, 1)
    base *= vig[..., None]
    return np.clip(base, 0, 255).astype(np.uint8)


def rim_glow(cut, accent, grow=7, blur=10, boost=1.5):
    """Quầng sáng accent viền quanh cầu thủ — MỎNG (grow/blur nhỏ) nhưng ĐẬM (boost alpha).
    Trước đây grow=18/blur=26 cho quầng dày & nhạt; anh Tuấn Anh 14/07 muốn mỏng lại + đậm hơn."""
    a = cut.split()[3]
    a = a.filter(ImageFilter.MaxFilter(2 * grow + 1)).filter(ImageFilter.GaussianBlur(blur))
    arr = np.asarray(a, np.float32) * boost                    # đậm hơn: nâng cường độ quầng
    a = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    glow = Image.new("RGBA", cut.size, accent + (0,))
    glow.putalpha(a)
    return glow


def feather_edges(cut, blur=2.6):
    """Làm MƯỢT rìa cutout để cầu thủ HÒA vào nền, hết cạnh gắt (anh Tuấn Anh 14/07):
    - erode 1px: bỏ viền màu nền còn sót của rembg (nguồn gây tương phản gắt quanh silhouette);
    - GaussianBlur alpha: feather mềm silhouette.
    ⚠ KHÔNG làm mờ-đáy Ở ĐÂY: nếu mờ đáy trước rồi mới dựng rim_glow thì quầng sẽ vẽ theo MÉP TRÊN
    của vùng mờ → sinh VỆT SÁNG NGANG cắt đôi cầu thủ (lỗi 14/07). Việc tan-đáy để SAU, cho cả
    người lẫn quầng, bằng bottom_dissolve()."""
    a = cut.split()[3]
    a = a.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(blur))
    cut.putalpha(a)
    return cut


def bottom_dissolve(img, frac=0.14):
    """Làm TAN dần cạnh DƯỚI của 1 lớp RGBA (người HOẶC quầng) vào nền — nhân alpha với dốc 0→1.
    Áp SAU khi đã dựng quầng, cho CẢ hai lớp cùng dốc → đáy dịu về 0, KHÔNG để lại mép sáng nội bộ,
    và xoá luôn vệt quầng ngang ở mép cắt dưới của ảnh gốc."""
    a = np.asarray(img.split()[3], np.float32)
    hh = a.shape[0]; f = int(hh * frac)
    if f > 4:
        # a[hh-f:] là các dòng TỪ TRÊN vùng mờ XUỐNG đáy → phải 1.0 (đục) ở trên, 0.0 (tan) ở đáy.
        # BUG 14/07: dùng linspace(0,1) làm dòng TRÊN thành trong suốt → VẠCH CẮT NGANG người. Sửa: 1→0.
        a[hh - f:, :] *= np.linspace(1.0, 0.0, f)[:, None]     # trên đục → đáy tan mượt, KHÔNG có vạch
        img.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--player"); ap.add_argument("--photo"); ap.add_argument("--out", required=True)
    ap.add_argument("--accent", default="#e11d2a"); ap.add_argument("--seconds", type=float, default=6)
    ap.add_argument("--fps", type=int, default=30); ap.add_argument("--side", default="center")
    ap.add_argument("--grid-dir", default="ltr", choices=list(GRID_DIRS),
                    help="Hướng lưới chạy: ltr(trái→phải), rtl, up, down, diag.")
    ap.add_argument("--enter", default="none", choices=["none", "left", "right"],
                    help="Cầu thủ ĐI VÀO: từ trái/phải, nhỏ→to dần, trôi vào giữa. 'none'=đứng giữa zoom chậm.")
    args = ap.parse_args()
    args.seconds = max(5.0, args.seconds)    # SÀN 5s (luật anh Tuấn Anh 14/07): mọi sản phẩm ≥ 5 giây
    accent = hexrgb(args.accent)
    tmp = tempfile.mkdtemp(prefix="spot_")

    photo = args.photo
    if not photo:
        if not args.player:
            raise SystemExit("Cần --player hoặc --photo.")
        photo = fetch_player(args.player, os.path.join(tmp, "p.jpg"))
        if not photo:
            raise SystemExit(f"Không lấy được ảnh '{args.player}' từ Wikipedia — thử --photo.")
    print("[1/3] Xóa nền cầu thủ (rembg)…")
    cut = cutout(photo)
    # KHÔNG CỤT ĐẦU/TAY (anh Tuấn Anh 14/07): chừa lề trên/dưới + tính kích thước để LÚC ZOOM HẾT
    # cỡ vẫn nằm trong khung (đỉnh đầu ≥ lề trên). Rộng quá (giang tay) thì co theo bề ngang.
    TOP = int(H * 0.055); BOT = int(H * 0.03); ZMAX = 1.03
    avail = H - TOP - BOT
    ph = int(avail / ZMAX); pw = int(cut.width * ph / cut.height)
    if pw > W * 0.60:
        pw = int(W * 0.60); ph = int(cut.height * pw / cut.width)
    cut = cut.resize((pw, ph), Image.LANCZOS)
    cut = feather_edges(cut)                                    # rìa mượt (chưa tan đáy)
    glow = rim_glow(cut, accent)                                # quầng mỏng + đậm, theo silhouette SẠCH
    bottom_dissolve(cut); bottom_dissolve(glow)                 # tan đáy CẢ 2 lớp → hết vệt sáng cắt đôi
    px = {"center": (W - pw) // 2, "left": int(W * 0.08), "right": int(W * 0.92 - pw)}.get(args.side, (W - pw) // 2)
    py = H - BOT - ph

    print(f"[2/3] Dựng {args.seconds}s lưới động + ghép…")
    n = int(args.seconds * args.fps)
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(args.fps),
         "-i", "pipe:0", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", args.out],
        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    cxc = px + pw / 2                                                 # tâm x khi đứng giữa
    for i in range(n):
        t = i / args.fps
        frame = Image.fromarray(grid_bg(t, accent, args.grid_dir)).convert("RGBA")
        if args.enter in ("left", "right"):
            # ĐI VÀO: nhỏ→to, trôi từ cạnh vào giữa, giảm tốc mượt (ease-out) rồi giữ
            p = min(1.0, t / max(0.2, args.seconds * 0.68)); p = 1 - (1 - p) ** 3
            sc = 0.42 + 0.58 * p
            startcx = W * (0.20 if args.enter == "left" else 0.80)
            cx = startcx + (cxc - startcx) * p
            zw, zh = max(2, int(pw * sc)), max(2, int(ph * sc))
            ox = int(cx - zw / 2); oy = H - BOT - zh
        else:
            z = 1.0 + (ZMAX - 1.0) * (i / n)                          # zoom chậm, CAP ZMAX (khỏi đẩy đầu ra)
            zw, zh = int(pw * z), int(ph * z)
            ox = px - (zw - pw) // 2; oy = H - BOT - zh               # neo đáy có lề → đỉnh ≥ TOP, không cụt đầu
        cz = cut.resize((zw, zh), Image.LANCZOS); gz = glow.resize((zw, zh), Image.LANCZOS)
        frame.alpha_composite(gz, (ox, oy)); frame.alpha_composite(cz, (ox, oy))
        enc.stdin.write(frame.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait()
    print(f"[3/3] XONG: {args.out}")


if __name__ == "__main__":
    main()
