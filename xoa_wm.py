#!/usr/bin/env python3
"""XOÁ WATERMARK bằng LaMa inpainting local (anh duyệt 10/08 — bán tự động CÓ CỬA DUYỆT).

Chạy bằng python của venv ~/.cache/lama-venv (torch + simple-lama-inpainting, MPS trên M4):
    ~/.cache/lama-venv/bin/python3 xoa_wm.py --anh <đường ảnh> --vung x,y,w,h [x,y,w,h ...]
        [--ra <đường ảnh ra>]   # mặc định ghi cạnh ảnh gốc, đuôi .xoa-wm.jpg (bản THỬ)

- `--vung` theo TỶ LỆ 0..1 trên ảnh (cùng khuôn với khung crop của trạm); nhận nhiều vùng.
- SỐNG CÒN (bài học SẬP NGUỒN 10/08 17:14): KHÔNG đưa cả ảnh vào model. Bản đầu chạy
  LaMa trên toàn ảnh full-size → tiến trình phình ~30GB, hai lượt bấm song song là máy
  16GB kernel panic. Giờ CẮT MẢNH quanh vùng xoá (nới 2 lần mỗi chiều, trần 1280px),
  inpaint mảnh, dán về — RAM dưới ~2GB, nhanh hơn hẳn, chất lượng ngang vì LaMa chỉ
  cần ngữ cảnh quanh vùng.
- Mask nới 10px — LaMa vá mượt hơn khi mask phủ dư một chút.
- Script KHÔNG bao giờ đè ảnh gốc: chỉ sinh bản thử; việc THAY là của server trạm sau
  khi anh nhìn TRƯỚC/SAU và bấm ưng (giữ bản gốc hoàn được, như cơ chế crop).
- Giới hạn nói thật: watermark lưới phủ kín hay đè giữa mặt người thì vá vẫn để vết —
  loại ảnh, đừng cứu.

Việc CƠ KHÍ (model vision inpaint, không gọi LLM) — bài học vận hành ghi ở BRAIN của
skill soc-tai-nguyen.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

MANH_TRAN = 1280      # cạnh dài nhất của mảnh đưa vào model — trần cứng giữ RAM thấp


def _mask_net_chu(manh, o):
    """Tách NÉT CHỮ watermark trắng bán-trong trong ô (10/08 khuya — vụ 'cầu thủ mất
    chân'): mask cả ô là LaMa bịa lại cả giày nằm dưới chữ; chỉ mask đúng NÉT thì chi
    tiết giữa các con chữ còn nguyên. Nét = pixel SÁNG HƠN nền ước lượng (median blur)
    và BÃO HOÀ THẤP (trắng/xám). Trả None nếu tách không ra hồn (nét <0,5% ô — kéo
    nhầm chỗ không chữ; hoặc >60% ô — watermark đặc/nền trắng, mask cả ô còn hơn).

    Vụ 2 cùng đêm (VnExpress còn vết mờ): chữ ĐẶC TO có nét dày hơn cửa sổ median cố
    định 31 → "nền" ước ngay trên thân chữ, diff ≈ 0, chỉ bắt được viền → vá viền còn
    lõi. Sửa: cửa sổ median TỰ PHÓNG theo cỡ ô (≈ nửa cạnh ngắn, kẹp 31..99) + đóng
    hình thái (MORPH_CLOSE) bít lõi giữa các viền đã bắt."""
    import cv2
    a = np.array(manh)
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    ys, xs = np.where(o)
    canh_ngan = max(min(ys.max() - ys.min(), xs.max() - xs.min()), 1)
    k = min(99, max(31, (canh_ngan // 2) | 1))       # lẻ, 31..99, ~nửa cạnh ngắn ô
    nen = cv2.medianBlur(g, k)
    diff = cv2.subtract(g, nen)
    sat = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)[:, :, 1]
    net = ((diff > 10) & (sat < 90) & o).astype(np.uint8) * 255
    net = cv2.morphologyEx(net, cv2.MORPH_CLOSE, np.ones((17, 17), np.uint8))
    net[~o] = 0
    ty_le = (net > 0).sum() / max(o.sum(), 1)
    if not 0.005 < ty_le < 0.6:
        return None
    return cv2.dilate(net, np.ones((5, 5), np.uint8), iterations=1)


def _manh_quanh(v, w, h, noi_px=10):
    """Toạ độ pixel của vùng xoá + mảnh ngữ cảnh quanh nó (nới 2× mỗi chiều, kẹp biên)."""
    x0 = max(0, int(v["x"] * w) - noi_px)
    y0 = max(0, int(v["y"] * h) - noi_px)
    x1 = min(w, int((v["x"] + v["w"]) * w) + noi_px)
    y1 = min(h, int((v["y"] + v["h"]) * h) + noi_px)
    vw, vh = x1 - x0, y1 - y0
    mx0 = max(0, x0 - vw)
    my0 = max(0, y0 - vh)
    mx1 = min(w, x1 + vw)
    my1 = min(h, y1 + vh)
    return (x0, y0, x1, y1), (mx0, my0, mx1, my1)


def xoa(duong_anh, cac_vung, duong_ra=None, noi_px=10, kieu="tu"):
    from simple_lama_inpainting import SimpleLama
    anh = Image.open(duong_anh).convert("RGB")
    w, h = anh.size
    lama = SimpleLama()
    for v in cac_vung:
        (x0, y0, x1, y1), (mx0, my0, mx1, my1) = _manh_quanh(v, w, h, noi_px)
        if x1 <= x0 or y1 <= y0:
            continue
        manh = anh.crop((mx0, my0, mx1, my1))
        mw, mh = manh.size
        # mảnh vẫn to thì thu về trần rồi phóng lại — RAM là luật cứng
        ty_le = min(1.0, MANH_TRAN / max(mw, mh))
        if ty_le < 1.0:
            manh_nho = manh.resize((int(mw * ty_le), int(mh * ty_le)), Image.LANCZOS)
        else:
            manh_nho = manh
        nw, nh = manh_nho.size
        o_bool = np.zeros((nh, nw), dtype=bool)
        o_bool[int((y0 - my0) * ty_le):int((y1 - my0) * ty_le),
               int((x0 - mx0) * ty_le):int((x1 - mx0) * ty_le)] = True
        # kieu='tinh': mask theo nét chữ — giữ chi tiết (giày, chân) nằm dưới watermark;
        # kieu='dac': vá CẢ Ô — sạch nhất khi chữ nằm trên nền trơn (cỏ, khán đài mờ);
        # kieu='tu' (mặc định): thử tinh, tách không được thì lùi về cả ô
        if kieu == "dac":
            mask = o_bool.astype(np.uint8) * 255
        else:
            tinh = _mask_net_chu(manh_nho, o_bool)
            if tinh is None and kieu == "tinh":
                tinh = o_bool.astype(np.uint8) * 255
            mask = tinh if tinh is not None else o_bool.astype(np.uint8) * 255
        if not mask.any():
            continue
        va = lama(manh_nho, Image.fromarray(mask)).crop((0, 0, nw, nh))
        if ty_le < 1.0:
            va = va.resize((mw, mh), Image.LANCZOS)
        anh.paste(va.convert("RGB"), (mx0, my0))
    ra = duong_ra or duong_anh + ".xoa-wm.jpg"
    anh.save(ra, quality=93)
    return ra


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--anh", required=True)
    ap.add_argument("--vung", nargs="+", required=True,
                    help="mỗi vùng x,y,w,h theo tỷ lệ 0..1")
    ap.add_argument("--ra")
    ap.add_argument("--kieu", choices=["tu", "tinh", "dac"], default="tu")
    a = ap.parse_args()
    vungs = []
    for s in a.vung:
        x, y, w, h = (float(t) for t in s.split(","))
        vungs.append({"x": x, "y": y, "w": w, "h": h})
    print("ĐÃ XOÁ →", xoa(a.anh, vungs, a.ra, kieu=a.kieu))
