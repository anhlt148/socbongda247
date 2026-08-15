#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIỂM TRỨNG RENDER HIỆU ỨNG (anh Tuấn Anh 16/07) — chỉ soi asset ĐÃ QUA BỘ EDIT (FocusPop/Spotlight/
StatPop/Tactical/News/Quote/Lineup), xem RENDER có LỖI không; lỗi thì gắn cờ để render lại.

2 TẦNG:
  Tầng 1 — CƠ HỌC (máy tự chấm, không cần nhìn): file hỏng · thời lượng hụt · KHUNG TRƠN/ĐEN (render
    fail) · ĐỨNG HÌNH (mọi frame giống nhau) · TOÀN MỜ (FocusPop hỏng — độ nét cả khung quá thấp).
  Tầng 2 — THỊ GIÁC: trích khung các clip NGHI VẤN → ghép contact sheet để soi mắt xác nhận.

Dùng:  kiem_render.py <thư_mục_effects> [--xoa-loi]   (--xoa-loi: xoá clip lỗi để build render lại)
Cần: Pillow + numpy + ffmpeg/ffprobe (venv ~/.cache/claude-earth-venv).
"""
import argparse, glob, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

MIN_SEC = 4.5                 # clip ngắn hơn = render đứt
STD_TRON = 8.0                # std pixel < ngưỡng = khung trơn/đen (render fail)
SHARP_MO = 60.0              # độ nét khối cao nhất < ngưỡng = TOÀN MỜ (vd FocusPop hỏng)
FROZEN_DIFF = 1.2            # sai khác 2 khung < ngưỡng = đứng hình


def probe_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                        "default=nw=1:nk=1", p], capture_output=True, text=True, timeout=30)
    try: return float(r.stdout.strip())
    except ValueError: return 0.0


def frame(p, t, dst):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", p, "-frames:v", "1", dst],
                   capture_output=True, timeout=40)
    return dst if os.path.exists(dst) else None


def sac_net_khoi(im):
    """Độ nét CAO NHẤT trên lưới 4×4 (Laplacian variance từng khối). FocusPop đúng: chủ thể có 1 khối
    nét cao; FocusPop hỏng (mờ hết): mọi khối đều thấp."""
    g = np.asarray(im.convert("L").filter(ImageFilter.FIND_EDGES), np.float32)
    h, w = g.shape; best = 0.0
    for by in range(4):
        for bx in range(4):
            blk = g[by*h//4:(by+1)*h//4, bx*w//4:(bx+1)*w//4]
            best = max(best, float(blk.var()))
    return best


def kiem_clip(p, tmp):
    dur = probe_dur(p)
    if dur < 0.3:
        return "LỖI", "file hỏng / không đọc được"
    if dur < MIN_SEC:
        return "LỖI", f"thời lượng hụt ({dur:.1f}s < {MIN_SEC}s) — render đứt"
    f1 = frame(p, dur*0.5, os.path.join(tmp, "a.png"))
    f2 = frame(p, dur*0.85, os.path.join(tmp, "b.png"))
    if not f1:
        return "LỖI", "không trích được khung hình"
    a = np.asarray(Image.open(f1).convert("RGB"), np.float32)
    if a.std() < STD_TRON:
        return "LỖI", f"KHUNG TRƠN/ĐEN (std {a.std():.1f}) — render fail"
    if f2:
        b = np.asarray(Image.open(f2).convert("RGB"), np.float32)
        if np.abs(a-b).mean() < FROZEN_DIFF:
            return "NGỜ", "ĐỨNG HÌNH — mọi khung giống nhau (hiệu ứng không chạy?)"
    sn = sac_net_khoi(Image.open(f1))
    if sn < SHARP_MO:
        return "LỖI", f"TOÀN MỜ (nét khối cao nhất {sn:.0f} < {SHARP_MO:.0f}) — vd FocusPop hỏng"
    return "ĐẠT", f"{dur:.1f}s · nét {sn:.0f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--xoa-loi", action="store_true", help="xoá clip LỖI để build render lại")
    a = ap.parse_args()
    clips = sorted(glob.glob(os.path.join(a.dir, "*.mp4")))
    if not clips:
        print("Không có clip hiệu ứng."); return
    tmp = tempfile.mkdtemp(prefix="kiemr_")
    dat, loi, ngo = [], [], []
    thumbs = []
    for p in clips:
        v, ly = kiem_clip(p, tmp)
        nm = os.path.basename(p)
        (dat if v == "ĐẠT" else loi if v == "LỖI" else ngo).append((nm, ly))
        if v != "ĐẠT":
            fr = frame(p, probe_dur(p)*0.5, os.path.join(tmp, nm+".png"))
            if fr: thumbs.append((fr, f"{v}: {nm}"))
        print(f"  {'✅' if v=='ĐẠT' else '❌' if v=='LỖI' else '🟡'} {nm:34s} {ly}")
        if v == "LỖI" and a.xoa_loi:
            os.remove(p)
    # contact sheet các clip nghi vấn để soi mắt (tầng 2)
    if thumbs:
        cols = 4; rows = (len(thumbs)+cols-1)//cols; cw, ch = 440, 250
        sh = Image.new("RGB", (cols*cw, rows*(ch+22)), (18, 18, 22)); d = ImageDraw.Draw(sh)
        try: fnt = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)
        except Exception: fnt = ImageFont.load_default()
        for i, (fp, lab) in enumerate(thumbs):
            im = Image.open(fp).convert("RGB"); im.thumbnail((cw-8, ch-8))
            x = (i % cols)*cw; y = (i//cols)*(ch+22)
            sh.paste(im, (x+4, y+4)); d.text((x+4, y+ch+3), lab[:46], fill=(240, 120, 120), font=fnt)
        out = os.path.join(a.dir, "_kiem_render_sheet.jpg"); sh.save(out, quality=85)
        print(f"\n🖼  Soi mắt (tầng 2): {out}")
    print(f"\n===== ĐẠT {len(dat)} · ❌ LỖI {len(loi)} · 🟡 NGỜ {len(ngo)} / {len(clips)} clip =====")
    if loi and a.xoa_loi:
        print(f"   đã XOÁ {len(loi)} clip lỗi → chạy lại build để render lại.")
    sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()
