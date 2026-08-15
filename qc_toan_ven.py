#!/usr/bin/env python3
"""CỔNG 3 — TOÀN VẸN NHẬN DIỆN KÊNH: quét TOÀN video, không lấy mẫu một khung.

Vì sao phải có cổng này (anh bắt lỗi 04/08): video mất sạch tiêu đề, logo và watermark
từ giây thứ tư vẫn đi qua hai cổng cũ với dấu "ĐẠT" — vì hai cổng đó chỉ soi watermark
của nguồn khác, chúng không biết nhận diện của MÌNH còn hay mất. Và em kiểm bằng cách
trích đúng một khung ở giây 8: lấy mẫu một điểm cho một thứ hỏng theo thời gian thì
không bao giờ bắt được.

Cách kiểm: cứ mỗi `buoc` giây lấy một khung, xét ba vùng bắt buộc phải có mặt —
  ① dải màu đặc dưới đáy (gradient kênh)   ② logo góc trên trái   ③ watermark góc dưới phải
Khung nào thiếu bất kỳ vùng nào là CHẶN, kèm bảng khung có dấu thời gian để người nhìn.

BƯỚC MẶC ĐỊNH 0,5 GIÂY (anh chốt 04/08). Một video 57 giây ra khoảng 114 khung — dày đủ để
không lọt một cảnh nào, kể cả cảnh ngắn nhất (nhịp cắt của kênh là 3–4 giây, nên mỗi cảnh
được soi ít nhất 6 lần). Khung trích bằng MỘT lệnh ffmpeg `fps=1/buoc`, không gọi 114 lần —
gọi từng lần thì riêng chi phí khởi động ffmpeg đã tốn gấp mấy chục lần bản thân phép kiểm.

  python3 qc_toan_ven.py <video.mp4> [bước giây]
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

# Ba điểm dò, toạ độ theo khung 1080×1920 (chuẩn kênh)
DIEM = {
    "dải màu đáy": (540, 1878),
    "logo góc trên trái": (118, 112),
    "watermark góc dưới": (905, 1812),
}
# Màu gradient kênh ở đáy: cam-đỏ đậm. Ảnh nền lọt xuống đây thì R/G/B lệch hẳn.
DO_LECH_TOI_DA = 46


def _do_dai(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", f], capture_output=True, text=True)
    return float(r.stdout.strip())


def _trich_het(video, buoc, thu_muc=NT.thu_muc_tam("_qc_khung")):
    """Trích TOÀN BỘ khung cần kiểm bằng một lệnh ffmpeg duy nhất."""
    import glob as _g
    import shutil
    shutil.rmtree(thu_muc, ignore_errors=True)
    os.makedirs(thu_muc)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video,
                    "-vf", f"fps=1/{buoc}", "-q:v", "3",
                    os.path.join(thu_muc, "k_%05d.jpg")], check=True)
    return sorted(_g.glob(os.path.join(thu_muc, "k_*.jpg")))


def _mau_vung(im, xy, r=9):
    x, y = xy
    o = im.crop((max(x - r, 0), max(y - r, 0), min(x + r, im.width), min(y + r, im.height)))
    px = list(o.getdata())
    n = len(px)
    return tuple(sum(p[i] for p in px) // n for i in range(3))


def kiem(video, buoc=0.5, luu_bang=True):
    tong = _do_dai(video)
    tep = _trich_het(video, buoc)
    moc = [(i + 0.5) * buoc for i in range(len(tep))]
    chuan, thieu, anh = None, [], []
    for t, p in zip(moc, tep):
        im = Image.open(p).convert("RGB")
        mau = {k: _mau_vung(im, v) for k, v in DIEM.items()}
        if chuan is None:                      # khung đầu làm chuẩn — lúc này format chắc chắn còn
            chuan = mau
        else:
            for k in DIEM:
                lech = max(abs(mau[k][i] - chuan[k][i]) for i in range(3))
                if lech > DO_LECH_TOI_DA:
                    thieu.append((t, k, lech))
        if luu_bang:
            nho = im.copy(); nho.thumbnail((150, 150), Image.LANCZOS)
            anh.append((t, nho))

    bang = None
    if luu_bang and anh:
        bang = os.path.splitext(video)[0] + "__qc-toan-ven.jpg"
        COT = 14
        hang = (len(anh) + COT - 1) // COT
        w, h = anh[0][1].size
        ra = Image.new("RGB", (COT * w, hang * (h + 24)), (14, 14, 16))
        d = ImageDraw.Draw(ra)
        try:
            f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
        except Exception:
            f = ImageFont.load_default()
        hong = {round(t, 1) for t, _, _ in thieu}
        for i, (t, im) in enumerate(anh):
            x, y = (i % COT) * w, (i // COT) * (h + 24)
            ra.paste(im, (x, y + 24))
            xau = round(t, 1) in hong
            d.text((x + 4, y + 3), f"{t:.1f}s" + (" ✗" if xau else ""), font=f,
                   fill=(255, 70, 70) if xau else (170, 255, 170))
        ra.save(bang, quality=88)

    print(f"── CỔNG TOÀN VẸN: {os.path.basename(video)}  ({len(moc)} khung, mỗi {buoc}s)")
    if thieu:
        mat = {}
        for t, k, l in thieu:
            mat.setdefault(k, []).append(t)
        print("   ❌ KHÔNG ĐẠT — mất nhận diện kênh giữa chừng:")
        for k, ts in mat.items():
            print(f"      · {k}: mất ở {len(ts)}/{len(moc)} khung, sớm nhất giây {min(ts):.1f}")
        if bang:
            print(f"   Bảng khung: {bang}")
        return 1
    print(f"   ✅ ĐẠT — tiêu đề, logo, watermark có mặt ở cả {len(moc)} khung")
    if bang:
        print(f"   Bảng khung: {bang}")
    return 0


def _frange(a, b, s):
    x = a
    while x < b:
        yield x
        x += s


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("dùng: qc_toan_ven.py <video.mp4> [bước giây]")
    sys.exit(kiem(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.5))
