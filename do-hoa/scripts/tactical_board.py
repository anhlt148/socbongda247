#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SƠ ĐỒ CHIẾN THUẬT ĐỘNG — kể PHA BÓNG bằng sân 2D + quân di chuyển (resource_type: Tactical).
Tài nguyên TỰ TẠO 100% (nội dung gốc, điểm cộng YPP, không phụ thuộc footage tải).

Dùng:  python3 tactical_board.py pha_bong.json [-o out.mp4]
JSON spec (toạ độ sân chuẩn hoá 0-100, gốc trái-trên, x = dọc sân trái→phải khung hình):
{
  "ten": "ban1_haaland", "tieu_de": "Phút 79 — tạt cánh phải, Haaland đánh đầu",
  "seconds": 6, "fps": 30,
  "doi_a": {"ten": "NA UY",  "mau": "#e11d2a"},
  "doi_b": {"ten": "BRAZIL", "mau": "#f7d117"},
  "the": [
    {"loai":"cau_thu","doi":"a","so":9, "duong":[[55,62],[80,42]], "t":[1.2,4.2]},
    {"loai":"cau_thu","doi":"b","so":3, "duong":[[82,50],[84,44]], "t":[1.5,4.2]},
    {"loai":"bong","duong":[[72,90],[86,44]], "t":[3.0,4.4], "cong":22},
    {"loai":"no","vi_tri":[88,44], "t":4.6}          # vòng nổ tại điểm ghi bàn
  ]
}
Cần: pillow (venv ~/.cache/claude-earth-venv) + ffmpeg."""
import argparse, json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

SS = 2
W, H = 1920, 1080
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "assets", "fonts")
CO = (14, 46, 32)           # cỏ tối điện ảnh
CO2 = (11, 38, 27)          # sọc cỏ xen kẽ
VACH = (255, 255, 255, 70)  # vạch sân mờ


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), int(size))


def hexrgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def ease(p):
    return p * p * (3 - 2 * p)                      # smoothstep


def sxy(x, y):
    """toạ độ sân 0-100 → pixel khung SS (sân chiếm ~86% ngang, lệch lên chừa tiêu đề)."""
    px = (0.07 + 0.86 * x / 100) * W * SS
    py = (0.06 + 0.76 * y / 100) * H * SS
    return px, py


def pos_tren_duong(duong, p):
    """vị trí trên polyline tại tiến độ p (0-1), chia đều theo độ dài đoạn."""
    if len(duong) == 1:
        return duong[0]
    segs = []
    for i in range(len(duong) - 1):
        (x1, y1), (x2, y2) = duong[i], duong[i + 1]
        segs.append(math.hypot(x2 - x1, y2 - y1))
    total = sum(segs) or 1
    d = p * total
    for i, L in enumerate(segs):
        if d <= L or i == len(segs) - 1:
            q = d / L if L else 0
            (x1, y1), (x2, y2) = duong[i], duong[i + 1]
            return x1 + (x2 - x1) * q, y1 + (y2 - y1) * q
        d -= L
    return duong[-1]


def bong_cong(a, b, p, cong):
    """đường bóng cong (tạt/đường chuyền bổng): bezier lệch vuông góc `cong` đơn vị sân."""
    (x1, y1), (x2, y2) = a, b
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    cxp, cyp = mx + nx * cong, my + ny * cong
    x = (1 - p) ** 2 * x1 + 2 * (1 - p) * p * cxp + p ** 2 * x2
    y = (1 - p) ** 2 * y1 + 2 * (1 - p) * p * cyp + p ** 2 * y2
    return x, y


def ve_san(dr):
    # nền cỏ sọc
    dr.rectangle([0, 0, W * SS, H * SS], fill=CO)
    for i in range(0, 12):
        if i % 2 == 0:
            x0 = (0.07 + 0.86 * i / 12) * W * SS
            x1 = (0.07 + 0.86 * (i + 1) / 12) * W * SS
            dr.rectangle([x0, sxy(0, 0)[1], x1, sxy(0, 100)[1]], fill=CO2)
    lw = max(2, 3 * SS)
    x0, y0 = sxy(0, 0); x1, y1 = sxy(100, 100)
    dr.rectangle([x0, y0, x1, y1], outline=VACH, width=lw)
    # vạch giữa + vòng tròn
    dr.line([sxy(50, 0), sxy(50, 100)], fill=VACH, width=lw)
    cx, cy = sxy(50, 50); r = 0.09 * W * SS
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=VACH, width=lw)
    # vòng cấm 2 đầu (16m50 ước lệ)
    for gx, sgn in ((0, 1), (100, -1)):
        bx, by = sxy(gx, 21); bx2, by2 = sxy(gx + sgn * 16, 79)
        dr.rectangle(sorted([bx, bx2]) + [] if False else [min(bx, bx2), by, max(bx, bx2), by2], outline=VACH, width=lw)
        b5x, _ = sxy(gx + sgn * 6, 0)
        dr.rectangle([min(sxy(gx, 36)[0], b5x), sxy(0, 36)[1], max(sxy(gx, 36)[0], b5x), sxy(0, 64)[1]],
                     outline=VACH, width=lw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("-o", "--out", default="")
    a = ap.parse_args()
    sp = json.load(open(a.spec, encoding="utf-8"))
    fps = int(sp.get("fps", 30)); secs = max(5.0, float(sp.get("seconds", 6)))   # SÀN 5s (anh Tuấn Anh 14/07)
    n = int(fps * secs)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.spec)), f"{sp.get('ten','tactical')}.mp4")
    ca = hexrgb(sp.get("doi_a", {}).get("mau", "#e11d2a"))
    cb = hexrgb(sp.get("doi_b", {}).get("mau", "#f7d117"))
    f_so = font("BeVietnamPro-Bold.ttf", 30 * SS)
    f_tit = font("BeVietnamPro-Bold.ttf", 46 * SS)
    f_doi = font("BeVietnamPro-SemiBold.ttf", 28 * SS)

    # nền sân vẽ 1 lần
    base = Image.new("RGB", (W * SS, H * SS))
    ve_san(ImageDraw.Draw(base, "RGBA"))
    dr0 = ImageDraw.Draw(base, "RGBA")
    # tiêu đề + tên đội
    tit = sp.get("tieu_de", "")
    if tit:
        dr0.rectangle([0, int(H * SS * 0.885), W * SS, H * SS], fill=(5, 8, 14, 235))
        dr0.text((W * SS / 2, H * SS * 0.942), tit, font=f_tit, fill=(245, 247, 250), anchor="mm")
    dr0.text((sxy(2, 0)[0], H * SS * 0.028), sp.get("doi_a", {}).get("ten", ""), font=f_doi, fill=ca, anchor="lm")
    dr0.text((sxy(98, 0)[0], H * SS * 0.028), sp.get("doi_b", {}).get("ten", ""), font=f_doi, fill=cb, anchor="rm")

    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                           "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    R = 26 * SS                                        # bán kính quân
    for i in range(n):
        t = i / fps
        im = base.copy()
        dr = ImageDraw.Draw(im, "RGBA")
        for th in sp.get("the", []):
            tv = th.get("t")
            if not isinstance(tv, (list, tuple)):              # "t": 4.6 (mốc đơn) cũng nhận
                tv = [tv, tv + 0.6] if tv is not None else [0, secs]
            t0, t1 = tv[0], tv[-1]
            p = ease(min(1, max(0, (t - t0) / max(0.01, t1 - t0))))
            if th["loai"] == "cau_thu":
                x, y = pos_tren_duong(th["duong"], p)
                px, py = sxy(x, y)
                mau = ca if th.get("doi", "a") == "a" else cb
                # vệt đường chạy đã đi qua
                if p > 0.02:
                    pts = [sxy(*pos_tren_duong(th["duong"], p * q / 12)) for q in range(13)]
                    dr.line(pts, fill=mau + (90,), width=6 * SS)
                dr.ellipse([px - R, py - R, px + R, py + R], fill=mau, outline=(255, 255, 255), width=3 * SS)
                dr.text((px, py), str(th.get("so", "")), font=f_so, fill=(255, 255, 255), anchor="mm")
            elif th["loai"] == "bong":
                if t < t0:
                    continue
                A, B = th["duong"][0], th["duong"][-1]
                x, y = (bong_cong(A, B, p, th["cong"]) if th.get("cong") else pos_tren_duong(th["duong"], p))
                px, py = sxy(x, y)
                for k in range(6):                     # vệt bóng
                    q = max(0, p - 0.03 * k)
                    bx, by = (bong_cong(A, B, q, th["cong"]) if th.get("cong") else pos_tren_duong(th["duong"], q))
                    bpx, bpy = sxy(bx, by)
                    rr = (10 - k) * SS
                    dr.ellipse([bpx - rr, bpy - rr, bpx + rr, bpy + rr], fill=(255, 255, 255, 220 - 34 * k))
            elif th["loai"] == "no":
                if t < t0:
                    continue
                px, py = sxy(*th["vi_tri"])
                q = min(1, (t - t0) / 0.6)
                rr = (20 + 90 * q) * SS
                alp = int(230 * (1 - q))
                dr.ellipse([px - rr, py - rr, px + rr, py + rr], outline=(255, 255, 255, alp), width=8 * SS)
                dr.ellipse([px - rr * .6, py - rr * .6, px + rr * .6, py + rr * .6],
                           outline=ca + (alp,), width=6 * SS)
        ff.stdin.write(im.resize((W, H), Image.LANCZOS).tobytes())
    ff.stdin.close(); ff.wait()
    print(f"✅ {out}  ({secs}s · {fps}fps · sơ đồ chiến thuật tự tạo)")


if __name__ == "__main__":
    main()
