#!/usr/bin/env python3
"""Kéo kho video nền SẠCH từ Mixkit — giấy phép miễn phí, không cần khoá, dùng được cả
video kiếm tiền. Đây là tầng nền của luật trộn anh chốt 04/08: ảnh + stock làm nền,
footage trận chỉ dùng cho khoảnh khắc chính."""
import os, re, subprocess, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
CHU_DE = ["football", "soccer", "stadium", "sport-fans", "goal"]
RA = DD.VIDEO_STOCK
os.makedirs(RA, exist_ok=True)

link = {}
for cd in CHU_DE:
    try:
        r = urllib.request.Request(f"https://mixkit.co/free-stock-video/{cd}/", headers=UA)
        h = urllib.request.urlopen(r, timeout=30).read().decode("utf-8", "replace")
    except Exception as e:
        print(f"  {cd}: lỗi {e}"); continue
    for u in set(re.findall(r"https://assets\.mixkit\.co/videos/\d+/\d+-1080\.mp4", h)):
        link[u.split("/")[-2]] = (u, cd)
    print(f"  {cd}: {len(h)//1000}KB trang")

print(f"\n{len(link)} clip 1080p tìm được")
for ma, (u, cd) in sorted(link.items()):
    p = os.path.join(RA, f"mixkit_{cd}_{ma}.mp4")
    if os.path.exists(p):
        continue
    try:
        urllib.request.urlretrieve(u, p)
        d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip()
        print(f"  ✓ {os.path.basename(p)}  {float(d):.1f}s  {os.path.getsize(p)/1e6:.1f}MB")
    except Exception as e:
        print(f"  ✗ {ma}: {e}")
print(f"\nkho: {RA}")
