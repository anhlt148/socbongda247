#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SA BÀN ĐỘI HÌNH (resource_type: Lineup) — học từ video mẫu 13:36 (11/07/2026):
sân trắng vẽ nét mảnh kiểu bảng chiến thuật + ẢNH MẶT cầu thủ trong vòng tròn đặt đúng vị trí,
nhãn vị trí (ST/LW/RW…) phía trên, các cầu thủ POP-IN lần lượt. Dùng cho: đội hình ra sân,
bộ ba tấn công, so sánh vai trò… (video bóng đá nào cũng cần).

Dùng:  lineup_board.py doi_hinh.json [-o ra.mp4]
JSON:
{ "ten":"bo_ba_bbc", "tieu_de":"Bộ ba BBC — Real Madrid 2016",
  "seconds":6, "cau_thu":[
    {"vi_tri":"ST","ten":"Karim Benzema","xy":[50,26]},      # ảnh tự tải Wikipedia theo "ten"
    {"vi_tri":"LW","ten":"Cristiano Ronaldo","xy":[22,44]},
    {"vi_tri":"RW","ten":"Gareth Bale","xy":[78,44],"anh":"duong/dan/tuy_chon.jpg"}
  ]}
xy = %% sân (gốc trái-trên, sân dọc nửa trên). Cần pillow + ffmpeg (+ mạng nếu ảnh auto)."""
import argparse, json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from player_spotlight import fetch_player

SS = 2
W, H = 1920, 1080
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "assets", "fonts")
NEN = (243, 245, 250)          # giấy trắng xanh nhẹ
NET = (28, 32, 40)             # nét vẽ sân


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), int(size))


def ease_pop(p):
    """pop-in có nảy nhẹ (overshoot)."""
    if p >= 1:
        return 1.0
    return 1 + 2.6 * (p - 1) * (p - 1) * ((1.7 + 1) * (p - 1) + 1.7) * -1 if False else \
        (1.2 * math.sin(p * math.pi * 0.6) if p < 0.833 else 1 + (1 - p) * 0.2)


def sxy(x, y):
    px = (0.24 + 0.52 * x / 100) * W * SS
    py = (0.10 + 0.78 * y / 100) * H * SS
    return px, py


def ve_san(dr):
    dr.rectangle([0, 0, W * SS, H * SS], fill=NEN)
    for gx in range(0, W * SS, 46 * SS):                       # giấy kẻ ô mờ
        dr.line([(gx, 0), (gx, H * SS)], fill=(210, 216, 228), width=1)
    for gy in range(0, H * SS, 46 * SS):
        dr.line([(0, gy), (W * SS, gy)], fill=(210, 216, 228), width=1)
    lw = 5 * SS
    x0, y0 = sxy(0, 0); x1, y1 = sxy(100, 100)
    dr.rectangle([x0, y0, x1, y1], outline=NET, width=lw)      # nửa sân dọc
    bx0, _ = sxy(18, 0); bx1, _ = sxy(82, 0); _, by = sxy(0, 26)
    dr.rectangle([bx0, y0, bx1, by], outline=NET, width=lw)    # vòng cấm
    gx0, _ = sxy(36, 0); gx1, _ = sxy(64, 0); _, gy = sxy(0, 9)
    dr.rectangle([gx0, y0, gx1, gy], outline=NET, width=lw)    # 5m50
    cx, cy = sxy(50, 26)                                       # cung tròn dưới vòng cấm (đúng tâm chấm 11m)
    r = (sxy(11, 0)[0] - sxy(0, 0)[0])
    dr.arc([cx - r, cy - r, cx + r, cy + r], 25, 155, fill=NET, width=lw)


def mat_tron(path, d):
    """ảnh chân dung → đĩa tròn viền: crop vuông phần ĐẦU (top-center) rồi mask tròn."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = min(w, int(h * 0.62))
    im = im.crop(((w - side) // 2, 0, (w + side) // 2, side)).resize((d, d), Image.LANCZOS)
    mask = Image.new("L", (d * 2, d * 2), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, d * 2, d * 2], fill=255)
    mask = mask.resize((d, d), Image.LANCZOS)
    dia = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    dia.paste(im, (0, 0), mask)
    vien = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    ImageDraw.Draw(vien).ellipse([0, 0, d - 1, d - 1], outline=(205, 212, 226, 255), width=max(3, d // 26))
    dia.alpha_composite(vien)
    return dia


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("-o", "--out", default="")
    a = ap.parse_args()
    sp = json.load(open(a.spec, encoding="utf-8"))
    fps = int(sp.get("fps", 30)); secs = max(5.0, float(sp.get("seconds", 6)))   # SÀN 5s (anh Tuấn Anh 14/07)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.spec)), f"{sp.get('ten','lineup')}.mp4")
    f_vt = font("BeVietnamPro-Black.ttf", 40 * SS)
    f_tit = font("BeVietnamPro-Bold.ttf", 44 * SS)

    base = Image.new("RGB", (W * SS, H * SS))
    dr0 = ImageDraw.Draw(base)
    ve_san(dr0)
    if sp.get("tieu_de"):
        dr0.text((W * SS / 2, H * SS * 0.955), sp["tieu_de"], font=f_tit, fill=NET, anchor="mm")

    D = int(120 * SS)                                          # đường kính đĩa mặt
    players = []
    cache = os.path.join(os.path.dirname(os.path.abspath(a.spec)), "_faces")
    os.makedirs(cache, exist_ok=True)
    for i, c in enumerate(sp.get("cau_thu", [])):
        path = c.get("anh") or os.path.join(cache, c["ten"].replace(" ", "_") + ".jpg")
        if not os.path.exists(path):
            print(f"⬇ ảnh {c['ten']}…")
            if not fetch_player(c["ten"], path):
                print(f"⚠️ không tải được ảnh {c['ten']} — dùng đĩa trống"); path = None
        players.append({"vt": c.get("vi_tri", ""), "xy": c["xy"], "t0": 0.6 + i * 0.55,
                        "dia": mat_tron(path, D) if path else None})

    n = int(secs * fps)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                           "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / fps
        im = base.copy()
        dr = ImageDraw.Draw(im)
        for p in players:
            q = min(1, max(0, (t - p["t0"]) / 0.5))
            if q <= 0:
                continue
            s = ease_pop(q)
            px, py = sxy(*p["xy"])
            d2 = max(2, int(D * s))
            # bóng mờ dưới đĩa
            dr.ellipse([px - d2 * .42, py + d2 * .40, px + d2 * .42, py + d2 * .58], fill=(205, 210, 222))
            if p["dia"]:
                dia = p["dia"].resize((d2, d2), Image.LANCZOS)
                im.paste(dia, (int(px - d2 / 2), int(py - d2 / 2)), dia)
            else:
                dr.ellipse([px - d2 / 2, py - d2 / 2, px + d2 / 2, py + d2 / 2],
                           fill=(224, 230, 242), outline=(205, 212, 226), width=4 * SS)
            if q > 0.55 and p["vt"]:
                dr.text((px, py - D * 0.78), p["vt"], font=f_vt,
                        fill=NET, anchor="mm")
        ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())
    ff.stdin.close(); ff.wait()
    print(f"✅ {out}  (sa bàn đội hình {secs}s — {len(players)} cầu thủ pop-in)")


if __name__ == "__main__":
    main()
