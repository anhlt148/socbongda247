#!/usr/bin/env python3
"""Xếp ảnh thành BẢNG có đánh số để người nhìn một lần rồi chọn — thay vì mở từng tấm."""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont

viec = sys.argv[1]
ds = sorted(glob.glob(os.path.join(viec, "anh", "a*.jpg")))
COT, O = 6, 300
hang = (len(ds) + COT - 1) // COT
ra = Image.new("RGB", (COT * O, hang * (O + 26)), (18, 18, 20))
d = ImageDraw.Draw(ra)
try:
    f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
except Exception:
    f = ImageFont.load_default()
for i, p in enumerate(ds):
    im = Image.open(p).convert("RGB")
    im.thumbnail((O - 6, O - 6), Image.LANCZOS)
    x, y = (i % COT) * O, (i // COT) * (O + 26)
    ra.paste(im, (x + 3, y + 26 + (O - 6 - im.height) // 2))
    d.text((x + 6, y + 2), os.path.basename(p).replace(".jpg", ""), font=f, fill=(255, 212, 0))
out = os.path.join(viec, "bang-anh.jpg")
ra.save(out, quality=88)
print(f"{out}  ({len(ds)} ảnh)")
