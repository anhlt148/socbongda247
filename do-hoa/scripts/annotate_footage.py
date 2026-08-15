#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TELESTRATOR — VẼ PHÂN TÍCH ĐÈ LÊN FOOTAGE (học từ video mẫu 4:55, 11/07/2026):
footage co vào KHUNG MÀU bo góc (kiểu TV phân tích) + bubble TÊN cầu thủ + ELLIPSE đánh dấu
vị trí + MŨI TÊN NÉT ĐỨT chỉ hướng chạy/đường chuyền — đúng chất BLV mổ băng.
LƯU Ý: footage nguồn phải qua film_look.py (lật + zoom 126% + sạch logo) TRƯỚC khi annotate.

Dùng:  annotate_footage.py video.mp4 chu_thich.json [-o ra.mp4]
JSON:
{ "khung":"#e8635a",                       # màu khung; "" = không khung
  "the":[                                  # toạ độ % TRÊN KHUNG VIDEO GỐC
    {"loai":"ten","text":"Ronaldo","xy":[38,18],"t":[0.4,5]},
    {"loai":"ellipse","xy":[40,36],"wh":[9,4.5],"t":[0.4,5]},
    {"loai":"muiten","tu":[44,36],"den":[86,28],"t":[1.0,5]}
  ]}
Cần pillow + ffmpeg."""
import argparse, json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "assets", "fonts")
W, H = 1920, 1080
SS = 2


def hexrgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def dashed_line(dr, p1, p2, fill, width, dash=26, gap=16):
    x1, y1 = p1; x2, y2 = p2
    L = math.hypot(x2 - x1, y2 - y1)
    if L < 1:
        return
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    d = 0
    while d < L:
        e = min(d + dash, L)
        dr.line([(x1 + ux * d, y1 + uy * d), (x1 + ux * e, y1 + uy * e)], fill=fill, width=width)
        d = e + gap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("spec"); ap.add_argument("-o", "--out", default="")
    a = ap.parse_args()
    sp = json.load(open(a.spec, encoding="utf-8"))
    out = a.out or os.path.splitext(a.video)[0] + "_anno.mp4"
    mau = sp.get("khung", "#e8635a")
    khung_on = bool(mau)
    kc = hexrgb(mau) if khung_on else (0, 0, 0)
    f_ten = ImageFont.truetype(os.path.join(FONTS, "BeVietnamPro-Bold.ttf"), 34 * SS)

    tmpdir = os.path.join(os.path.dirname(os.path.abspath(a.spec)), "_anno_tmp")
    os.makedirs(tmpdir, exist_ok=True)
    # video co 84% giữa khung → toạ độ chú thích map theo vùng video
    SC = 0.84 if khung_on else 1.0
    ox, oy = (1 - SC) / 2 * W * SS, (1 - SC) / 2 * H * SS

    def vxy(x, y):
        return ox + x / 100 * W * SC * SS, oy + y / 100 * H * SC * SS

    # 1) KHUNG PNG (nền màu + lỗ thủng bo góc + viền đen ngoài)
    lop = []                                                   # (png, t0, t1)
    if khung_on:
        kh = Image.new("RGBA", (W * SS, H * SS), (12, 12, 14, 255))
        d = ImageDraw.Draw(kh)
        d.rounded_rectangle([26 * SS, 26 * SS, W * SS - 26 * SS, H * SS - 26 * SS], radius=34 * SS, fill=kc + (255,))
        d.rounded_rectangle([ox, oy, ox + W * SC * SS, oy + H * SC * SS], radius=22 * SS, fill=(0, 0, 0, 0))
        p = os.path.join(tmpdir, "khung.png"); kh.save(p)
        lop.append((p, 0, 10 ** 4))
    # 2) từng chú thích 1 PNG
    for i, th in enumerate(sp.get("the", [])):
        im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if th["loai"] == "ten":
            x, y = vxy(*th["xy"])
            tw = d.textbbox((0, 0), th["text"], font=f_ten)[2]
            d.rounded_rectangle([x - tw / 2 - 20 * SS, y - 30 * SS, x + tw / 2 + 20 * SS, y + 30 * SS],
                                radius=30 * SS, fill=kc + (235,), outline=(255, 255, 255, 255), width=3 * SS)
            d.text((x, y), th["text"], font=f_ten, fill=(255, 255, 255), anchor="mm")
        elif th["loai"] == "ellipse":
            x, y = vxy(*th["xy"]); w2, h2 = th["wh"][0] / 100 * W * SC * SS, th["wh"][1] / 100 * H * SC * SS
            d.ellipse([x - w2, y - h2, x + w2, y + h2], fill=kc + (150,), outline=kc + (255,), width=5 * SS)
        elif th["loai"] == "muiten":
            p1, p2 = vxy(*th["tu"]), vxy(*th["den"])
            dashed_line(d, p1, p2, kc + (255,), 9 * SS)
            ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            for s in (-1, 1):
                d.line([p2, (p2[0] - 34 * SS * math.cos(ang + s * 0.45),
                             p2[1] - 34 * SS * math.sin(ang + s * 0.45))], fill=kc + (255,), width=9 * SS)
        p = os.path.join(tmpdir, f"the{i}.png")
        im.resize((W, H), Image.LANCZOS).save(p)
        t = th.get("t", [0, 10 ** 4])
        lop.append((p, t[0], t[-1]))

    # 3) ghép 1 lệnh ffmpeg: scale video (nếu khung) + overlay từng lớp với fade alpha
    ins = ["-i", a.video]
    for p, _, _ in lop:
        ins += ["-loop", "1", "-i", p]
    fc = []
    if khung_on:
        fc.append(f"[0:v]scale={int(W*SC/2)*2}:{int(H*SC/2)*2}[v0]")
        fc.append(f"color=c=black:s={W}x{H}:r=30[bg]")
        fc.append(f"[bg][v0]overlay=({W}-w)/2:({H}-h)/2[base]")
        cur = "base"
    else:
        cur = "0:v"
    for idx, (p, t0, t1) in enumerate(lop):
        lab = f"o{idx}"
        fc.append(f"[{idx+1}:v]format=rgba,fade=in:st={t0}:d=0.35:alpha=1[{lab}]")
        nxt = f"m{idx}"
        fc.append(f"[{cur}][{lab}]overlay=0:0:shortest=1[{nxt}]")
        cur = nxt
    # PNG -loop 1 là input VÔ HẠN → PHẢI chốt thời lượng đầu ra = thời lượng video, không thì ffmpeg treo
    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                         "-of", "default=nw=1:nk=1", a.video], capture_output=True, text=True)
    dur = float(pr.stdout.strip() or 8)
    cmd = ["ffmpeg", "-y", "-v", "error"] + ins + ["-filter_complex", ";".join(fc),
           "-map", f"[{cur}]", "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "fast", "-crf", "19",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(out):
        print(r.stderr[-600:]); sys.exit("❌ annotate lỗi")
    print(f"✅ {out}  (telestrator: khung + {len(sp.get('the', []))} chú thích)")


if __name__ == "__main__":
    main()
