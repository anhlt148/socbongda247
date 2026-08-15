#!/usr/bin/env python3
"""ENGINE VIDEO v5 — dùng ĐÚNG template ảnh anh đã duyệt 04/08/2026.

Khác các bản trước: mọi thông số bố cục/màu/chữ đều LẤY TRỰC TIẾP từ
`template_tin_bong_da.py` (import, không chép lại) — sửa template một chỗ thì
video và ảnh preview luôn khớp nhau, không bao giờ lệch.

  · Nền: gradient rực hạ gắt 5% #E35C2F → #D33342 → #A51337
  · Chữ: Oswald condensed, trắng + nhấn #FFD400, tự co, sàn 56px
  · Ken Burns: PIL toạ độ số thực (không rung), zoom ≤12%
  · Ảnh 65% khung · banner 23% · hoà mờ 17,5% · hoạ tiết sân 6% · logo sóc + watermark
"""
import importlib.util, json, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, BASE_DIR) if False else None
import chuyen_dong                      # hai kiểu chuyển động: zoom / chạy ngang

BASE = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(BASE)
TPL_PATH = os.path.join(GOC, "template-v2", "template_tin_bong_da.py")
_spec = importlib.util.spec_from_file_location("tpl", TPL_PATH)
TPL = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(TPL)          # nguồn chân lý duy nhất về bố cục & màu

W, H = TPL.CANVAS["W"], TPL.CANVAS["H"]
L, MAU = TPL.LAYOUT, TPL.MAU
FPS = 30
ANH_CAO = int(H * L["anh_cao_ty_le"])
ANH_DAY = int(H * 0.745)               # mép dưới ảnh nằm sâu trong vùng màu đặc
ANH_TOP = ANH_DAY - ANH_CAO
ZOOM_MAX = 1.12

ANH = os.path.join(GOC, "pvf-anh-nho")
LOGO = os.path.join(GOC, "logo-soc", "logo247-tron-1024.png")   # logo chính v3 (anh chốt 04/08)
OUT = os.path.join(BASE, "build5")
os.makedirs(OUT, exist_ok=True)

TIEU_DE = "Siêu sân 60.000 chỗ ở Hưng Yên: mái vòm 8.600 tấn lần đầu có ở Việt Nam"
NHAN = ["60.000 chỗ", "8.600 tấn"]
KENH = "SÓC BÓNG ĐÁ 247"

# (ảnh, từ giây, đến giây) — mốc lấy từ whisper chạy trên chính file giọng
CANH = [
    ("a03.jpg", 0.00, 3.88), ("a10.jpg", 3.88, 6.16), ("a01.jpg", 6.16, 9.24),
    ("a09.jpg", 9.24, 12.12), ("a13.jpg", 12.12, 15.48), ("a02.jpg", 15.48, 19.66),
    ("a12.jpg", 19.66, 22.26), ("a11.jpg", 22.26, 24.90), ("a08.jpg", 24.90, 26.90),
    ("a05.jpg", 26.90, 29.60),
]
TONG = 29.6
CARD_TU, CARD_DEN = 15.48, 21.80       # card hiện đúng đoạn nói mái vòm


def lam_overlay():
    """Lớp phủ tĩnh: gradient + hoạ tiết sân + tiêu đề + thanh dọc + logo + watermark.

    Dùng chính các hàm của template nên trùng khít với ảnh preview đã duyệt.
    """
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y_khoi = int(H * L["hoa_den_ty_le"]) + 26
    img.alpha_composite(TPL._lop_gradient(W, H, y_khoi))
    img.alpha_composite(TPL._lop_hoa_van_san(W, H))

    d = ImageDraw.Draw(img)
    x_chu = L["le_trai"] + L["thanh_doc_rong"] + L["thanh_doc_cach_chu"]
    rong = W - x_chu - L["le_phai"]
    cao_cho_phep = H - L["le_duoi"] - y_khoi
    font, dong, size = TPL._fit_tieu_de(d, TIEU_DE.upper(), rong, cao_cho_phep)
    buoc = int(size * L["dong_cach"])
    y = y_khoi
    for ln in dong:
        x = x_chu
        for txt, nhan in TPL._tach_cum(ln, [h.upper() for h in NHAN]):
            d.text((x, y), txt, font=font, fill=MAU["chu_nhan"] if nhan else MAU["chu"])
            x += d.textlength(txt, font=font)
        y += buoc
    d.rounded_rectangle([L["le_trai"], y_khoi + 6, L["le_trai"] + L["thanh_doc_rong"],
                         y_khoi + int(len(dong) * buoc * 1.32)],
                        radius=L["thanh_doc_rong"] // 2, fill=MAU["thanh_doc"])

    lg = Image.open(LOGO).convert("RGBA").resize((int(W * 0.115),) * 2, Image.LANCZOS)
    img.alpha_composite(lg, (L["le_trai"] - 28, 54))
    TPL._ve_watermark(img, KENH)

    p = os.path.join(OUT, "overlay.png")
    img.save(p)
    print(f"  overlay: tiêu đề {len(dong)} dòng, cỡ {size}px")
    return p


def lam_card():
    cw, ch = 940, 340
    img = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, cw, ch], radius=30, fill=(10, 10, 12, 232),
                        outline=MAU["chu_nhan"] + (255,), width=6)
    d.text((46, 34), "MÁI VÒM THÉP", font=TPL._font(TPL.FONT["title"], 40, 600),
           fill=MAU["chu"])
    fb = TPL._font(TPL.FONT["title"], 116, 700)
    d.text((42, 74), "8.600", font=fb, fill=MAU["chu_nhan"])
    d.text((42 + d.textlength("8.600", font=fb) + 20, 134), "TẤN",
           font=TPL._font(TPL.FONT["title"], 58, 700), fill=MAU["chu"])
    fs = TPL._font(TPL.FONT["title"], 34, 500)
    d.text((46, 222), "TỰ ĐÓNG MỞ TRONG 12 PHÚT", font=fs, fill=(238, 238, 238, 240))
    d.text((46, 268), "LẦN ĐẦU TIÊN CÓ Ở VIỆT NAM", font=fs, fill=(255, 120, 120, 245))
    p = os.path.join(OUT, "card.png")
    img.save(p)
    return p


def canh_anh(i, ten, dur, kieu=None):
    """Dựng một cảnh — chọn ngẫu nhiên ZOOM IN hoặc CHẠY NGANG (học từ Nhím Bóng Đá).

    Không bao giờ trộn hai kiểu trong cùng cảnh. Cả hai render bằng PIL toạ độ số thực
    nên không rung.
    """
    out = os.path.join(OUT, f"c{i:02d}.mp4")
    k = chuyen_dong.render_canh(os.path.join(ANH, ten), out, W, H, ANH_CAO, ANH_TOP,
                                dur, FPS, kieu=kieu, seed=i * 17 + 3)
    return out, k


def main():
    overlay, card = lam_overlay(), lam_card()
    clips, kieus = [], []
    for i, (t, b, k) in enumerate(CANH):
        c, ki = canh_anh(i, t, k - b)
        clips.append(c); kieus.append(ki)
    print("  chuyển động: " + " · ".join(f"{i+1}:{k}" for i, k in enumerate(kieus)))
    with open(os.path.join(OUT, "list.txt"), "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    ghep = os.path.join(OUT, "ghep.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", os.path.join(OUT, "list.txt"), "-c", "copy", ghep], check=True)

    nhac = os.path.join(GOC, "nhac_bongda", "chien_thang", "mixkit_1030.mp3")
    giong = os.path.join(BASE, "giong30.mp3")
    final = os.path.join(BASE, "PVF-30s-v5.mp4")
    fc = (
        f"[0:v][1:v]overlay=0:0[v1];"
        f"[2:v]loop=loop=-1:size=1:start=0,format=rgba,"
        f"fade=t=in:st={CARD_TU}:d=0.35:alpha=1,"
        f"fade=t=out:st={CARD_DEN-0.35:.2f}:d=0.35:alpha=1[cardf];"
        f"[v1][cardf]overlay=(W-w)/2:'930+40*(1-min((t-{CARD_TU})/0.35,1))':"
        f"enable='between(t,{CARD_TU},{CARD_DEN})'[vout];"
        f"[3:a]adelay=120|120,volume=1.35,alimiter=limit=0.95[voice];"
        f"[4:a]atrim=0:{TONG},volume=0.11,afade=t=out:st={TONG-2.5}:d=2.5[bgm];"
        f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=0[aout]"
    )
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", ghep, "-i", overlay, "-i", card,
                    "-i", giong, "-i", nhac, "-filter_complex", fc,
                    "-map", "[vout]", "-map", "[aout]", "-t", f"{TONG}",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final], check=True)
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                                   "-of", "json", final], capture_output=True, text=True).stdout)
    v = [s for s in d["streams"] if s["codec_type"] == "video"][0]
    print(f"XONG → {final}\n{v['width']}x{v['height']} | "
          f"{float(d['format']['duration']):.1f}s | {int(d['format']['size'])/1e6:.1f} MB "
          f"| {len(CANH)} cảnh, nhịp {len(CANH)/(TONG/60):.0f} cắt/phút")


if __name__ == "__main__":
    main()
