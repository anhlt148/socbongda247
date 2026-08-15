#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XỬ LÝ FOOTAGE NGUỒN (film look + BIẾN ĐỔI BẮT BUỘC — luật anh chốt 11/07/2026):
video lấy từ nguồn gốc (YouTube/tư liệu) BẮT BUỘC phải qua đủ 4 lớp trước khi vào video:
  1. LẬT NGANG (hflip) — mặc định BẬT (tắt bằng --khong-lat CHỈ cho đồ tự tạo/bản đồ).
  2. ZOOM 126% (--zoom 1.26) — crop LỆCH LÊN TRÊN (--bias-top 0.7: 70% phần cắt lấy từ mép trên)
     để nuốt LOGO ĐÀI + BẢNG TỈ SỐ thường nằm góc/cạnh trên.
  3. XOÁ LOGO/BẢNG TỈ SỐ còn sót: --xoa-goc "x:y:w:h" (delogo, toạ độ TRÊN KHUNG GỐC trước khi
     lật/zoom; lặp lại cờ này cho nhiều vùng).
  4. CHẤT PHIM: grain + màu vintage nhẹ + vignette (--manh 0..1.5, 0 = tắt lớp màu).
Sau khi chạy PHẢI trích 1 frame XEM BẰNG MẮT xác nhận sạch logo/tỉ số rồi mới dùng.

Dùng:  film_look.py vao.mp4 ra.mp4 [--zoom 1.26] [--khong-lat] [--bias-top 0.7]
                    [--xoa-goc "20:20:260:80"] [--manh 1.0]
Chỉ cần ffmpeg."""
import argparse, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("vao"); ap.add_argument("ra")
ap.add_argument("--zoom", type=float, default=1.26, help="1.26 = luật bắt buộc cho footage nguồn")
ap.add_argument("--khong-lat", action="store_true", dest="khong_lat",
                help="KHÔNG lật — chỉ dùng cho đồ tự tạo/bản đồ (footage nguồn phải lật)")
ap.add_argument("--bias-top", type=float, default=0.7, dest="bias_top",
                help="tỉ lệ phần cắt lấy từ mép TRÊN (0.7 = nuốt vùng logo/tỉ số phía trên)")
ap.add_argument("--xoa-goc", action="append", default=[], dest="xoa_goc",
                metavar="x:y:w:h", help="vùng delogo trên khung GỐC; lặp lại được nhiều lần")
ap.add_argument("--manh", type=float, default=1.0, help="độ đậm chất phim (0 = tắt màu/grain)")
a = ap.parse_args()

f = []
for vung in a.xoa_goc:                                   # xoá logo TRƯỚC khi lật/zoom (toạ độ gốc)
    x, y, w, h = vung.split(":")
    f.append(f"delogo=x={x}:y={y}:w={w}:h={h}")
if not a.khong_lat:
    f.append("hflip")
if a.zoom > 1.001:                                       # crop lệch lên trên rồi phóng lại cỡ cũ
    f.append(f"crop=floor(iw/{a.zoom}/2)*2:floor(ih/{a.zoom}/2)*2"
             f":floor((iw-iw/{a.zoom})/2)"
             f":floor((ih-ih/{a.zoom})*{a.bias_top})")
    f.append("scale=1920:1080:force_original_aspect_ratio=increase")
    f.append("crop=1920:1080")
if a.manh > 0:
    f.append(f"curves=preset=vintage,eq=saturation=0.92:contrast=1.05,"
             f"noise=alls={9*a.manh:.0f}:allf=t+u,vignette=PI/4.4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.vao, "-vf", ",".join(f),
                "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", a.ra], check=True)
bien_doi = [x for x in ["lật" if not a.khong_lat else None,
                        f"zoom {a.zoom:.0%}" if a.zoom > 1.001 else None,
                        f"xoá {len(a.xoa_goc)} vùng logo" if a.xoa_goc else None,
                        f"film ×{a.manh}" if a.manh > 0 else None] if x]
print(f"✅ {a.ra} ({' + '.join(bien_doi)}) — TRÍCH FRAME XEM MẮT xác nhận sạch logo/tỉ số trước khi dùng!")
