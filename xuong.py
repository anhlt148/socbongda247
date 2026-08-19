#!/usr/bin/env python3
"""XƯỞNG — nối cả dây thành một lệnh: kịch bản → giọng → ảnh → dựng → video hoàn chỉnh.

Khác `dung_video.py` (viết cứng cho đúng một video PVF): mọi thứ ở đây đều là THAM SỐ,
đọc từ `kich-ban.json` trong thư mục việc. Một lệnh chạy được cho bất kỳ tin nào.

Vì sao chia nhịp bằng TỈ LỆ SỐ TIẾNG chứ không chạy whisper: giọng máy đọc đều nhịp, nên
thời gian một câu tỉ lệ gần đúng với số tiếng của nó (sai số đo được ±0,2 giây). Mốc câu
chỉ dùng để CHỌN CHỖ CẮT CẢNH — sai vài phần mười giây không ai thấy, mà tiết kiệm được
một lượt chạy whisper cho mỗi video (luật: code trước, model sau).

  python3 xuong.py viec/2026-08-04-b2e7e1
"""
import glob, json, os, random, re, subprocess, sys, time
import urllib.request
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD
import chuyen_dong
import nhip_canh as NC

# SÀN TUYỆT ĐỐI CỦA MỘT CẢNH (anh chốt 18/08: "ưu tiên không nuốt cảnh").
# Chuẩn đẹp là 2,5s; nhưng cảnh ngắn hơn chuẩn VẪN GIỮ ĐƯỢC, miễn không tụt dưới mức
# này. Dưới 1,6 giây mắt chưa kịp nhận ra hình gì — lúc ấy gộp mới thật sự đúng.
SAN_CANH = 1.6
import cum_vang as CV                 # cụm tô vàng của tít — một bản, trạm + xưởng chung
import chon_nhac as CN                # chọn nhạc theo cảm xúc — một bản dùng chung (12/08)
import phong_cach as PC              # núm vặn chống dập khuôn — anh cấu hình trên trạm

DD.bat_buoc_du()
TPL = DD.nap_template()
W, H = TPL.CANVAS["W"], TPL.CANVAS["H"]
L, MAU = TPL.LAYOUT, TPL.MAU
FPS = 30
ANH_CAO = int(H * L["anh_cao_ty_le"])
ANH_DAY = int(H * 0.745)
ANH_TOP = ANH_DAY - ANH_CAO

# Cung nhạc theo giọng tin. Mặc định "cang_thang" — hợp tin thi đấu/kịch tính nhất.
CUNG_NHAC = {
    "thang": "chien_thang", "thua": "bi_trang", "chan_thuong": "bi_trang",
    "cang": "cang_thang", "ke": "tu_su", "mo": "mo_dau", "dinh": "cao_trao",
}


# ── GIỌNG ────────────────────────────────────────────────────────────────────
def _env():
    e = {}
    for line in open(DD.VBEE_ENV):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k] = v.strip().strip('"')
    return e


def doc_giong(text, out, toc_do=None, ma_giong=None):
    """Gọi VBee Ngọc Huyền. API chạy bất đồng bộ: gửi xong phải hỏi lại tới khi có link."""
    e = _env()
    app_id, key = e.get("VBEE_APP_ID"), e.get("VBEE_API_KEY")
    base = e.get("VBEE_BASE_URL", "https://vbee.vn/api/v1").rstrip("/")
    if not (app_id and key):
        sys.exit("DỪNG — thiếu khoá VBee trong " + DD.VBEE_ENV)
    payload = {"voice_code": ma_giong or DD.GIONG_MA, "input_text": text,
               "app_id": app_id,
               "audio_type": "mp3", "bitrate": 128,
               "speed_rate": str(toc_do or DD.GIONG_TOC_DO),
               "callback_url": "https://webhook.site/00000000-0000-0000-0000-000000000000"}
    req = urllib.request.Request(base + "/tts", data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        d = json.load(r)
    res = d.get("result") or d.get("data") or {}
    link = res.get("audio_link") or d.get("audio_link")
    rid = res.get("request_id") or d.get("request_id")
    for _ in range(30):
        if link:
            break
        time.sleep(2)
        pu = urllib.request.Request(base + f"/tts/{rid}",
                                    headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(pu, timeout=30) as r:
            dd = json.load(r)
        rr = dd.get("result") or dd.get("data") or {}
        link = rr.get("audio_link")
    if not link:
        sys.exit("DỪNG — VBee không trả file giọng")
    tho = out + ".tho.mp3"
    urllib.request.urlretrieve(link, tho)
    # nén động + chuẩn độ to: giọng đọc trên điện thoại phải đều, không lúc to lúc nhỏ
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tho, "-af",
                    "equalizer=f=180:t=q:w=1:g=2.5,equalizer=f=2600:t=q:w=1.4:g=2,"
                    "equalizer=f=5200:t=q:w=1.2:g=3,"
                    "acompressor=threshold=-20dB:ratio=3:attack=5:release=90,"
                    "loudnorm=I=-15:TP=-1.5:LRA=9", out], check=True)
    os.remove(tho)
    return out


def do_dai(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", f], capture_output=True, text=True)
    return float(r.stdout.strip())


def _nhap_tram(viec):
    """Đọc bản nháp trạm ghi (bản đồ ảnh, ghi chú, từ khoá, thẻ số liệu).

    Trạm ghi ở `anh/tram.json`. Xưởng chỉ cần đọc — thiếu file thì coi như chưa khai gì,
    đừng để cả mẻ dựng chết chỉ vì một video anh chưa đụng tới trên trạm.
    """
    p = os.path.join(viec, "anh", "tram.json")
    if not os.path.exists(p):
        return {}
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}


# ── NHỊP ─────────────────────────────────────────────────────────────────────
def moc_cau(loi_binh, tong):
    """Ước giây kết thúc từng câu theo tỉ lệ số tiếng — đủ chính xác để chọn chỗ cắt.
    Phép tách khai MỘT chỗ ở `duong_dan.TACH_CAU_RE` — trạm/gợi ý cùng dùng."""
    cau = [c.strip() for c in re.split(DD.TACH_CAU_RE, loi_binh) if c.strip()]
    tong_tieng = sum(len(c.split()) for c in cau) or 1
    mocs, cong = [], 0
    for c in cau:
        cong += len(c.split())
        mocs.append(round(cong / tong_tieng * tong, 2))
    return mocs


# ── LỚP PHỦ TĨNH ─────────────────────────────────────────────────────────────
def lam_overlay(tieu_de, nhan, ra, goc_wm=None):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y_khoi = int(H * L["hoa_den_ty_le"]) + 26
    img.alpha_composite(TPL._lop_gradient(W, H, y_khoi))
    img.alpha_composite(TPL._lop_hoa_van_san(W, H))

    d = ImageDraw.Draw(img)
    x_chu = L["le_trai"] + L["thanh_doc_rong"] + L["thanh_doc_cach_chu"]
    rong = W - x_chu - L["le_phai"]
    cao_cho_phep = H - L["le_duoi"] - y_khoi
    font, dong, size = TPL._fit_tieu_de(d, tieu_de.upper(), rong, cao_cho_phep)
    if size < L["title_size_min"]:
        sys.exit(f"DỪNG — tiêu đề dài quá, phải co xuống {size}px (sàn {L['title_size_min']}). "
                 f"Rút gọn tiêu đề rồi chạy lại.")
    buoc = int(size * L["dong_cach"])
    # Tô vàng theo TỪ trên TOÀN tiêu đề rồi mới chia dòng (dùng chung bộ đã vá trong template
    # 06/08). Bản cũ tô theo từng dòng — cụm vắt qua hai dòng là trắng hết, và lỗi này đã vá
    # ở render() nhưng xưởng có hàm vẽ RIÊNG nên lọt: lần thứ ba bệnh "một logic hai bản"
    # (hồ sơ văn phong 2 nơi → nhịp đọc 2 con số → giờ vẽ tít 2 chỗ). Vẽ tít giờ dùng
    # _danh_dau_tu/_gop_manh của template — sửa luật tô là sửa MỘT chỗ.
    nhan_tu = TPL._danh_dau_tu(tieu_de.upper(), [h.upper() for h in nhan])
    y, k = y_khoi, 0
    for ln in dong:
        tu_dong = ln.split()
        x = x_chu
        for txt, la_nhan in TPL._gop_manh(tu_dong, nhan_tu[k:k + len(tu_dong)]):
            d.text((x, y), txt, font=font, fill=MAU["chu_nhan"] if la_nhan else MAU["chu"])
            x += d.textlength(txt, font=font)
        k += len(tu_dong)
        y += buoc
    # thanh dọc neo cứng theo số dòng chuẩn (anh chốt 06/08), không co theo tít ngắn dài
    cao_thanh = L.get("thanh_doc_dong", 4) * buoc
    d.rounded_rectangle([L["le_trai"], y_khoi + 6, L["le_trai"] + L["thanh_doc_rong"],
                         y_khoi + cao_thanh],
                        radius=L["thanh_doc_rong"] // 2, fill=MAU["thanh_doc"])
    lg = Image.open(DD.LOGO).convert("RGBA").resize((int(W * 0.115),) * 2, Image.LANCZOS)
    img.alpha_composite(lg, (L["le_trai"] - 28, 54))
    TPL._ve_watermark(img, DD.KENH, goc=goc_wm)      # goc_wm=None → mặc định template (10°)
    img.save(ra)
    return ra, len(dong), size


# ── DỰNG ─────────────────────────────────────────────────────────────────────
def xep_anh(ds_anh, so_canh, seed=7, theo_thu_tu=False):
    """Rải ảnh cho các cảnh: dùng hết ảnh có, không để hai cảnh liền nhau trùng ảnh.

    theo_thu_tu=True khi ảnh đã được người CHỌN và đánh số theo mạch kể — lúc đó tuyệt
    đối không xáo, vì ảnh số 1 là nhân vật của câu hook, ảnh cuối là ảnh của câu chốt.
    """
    if not ds_anh:
        sys.exit("DỪNG — không có ảnh nào để dựng")
    if theo_thu_tu:
        return [ds_anh[i % len(ds_anh)] for i in range(so_canh)]
    rnd = random.Random(seed)
    kho = list(ds_anh)
    rnd.shuffle(kho)
    ra, i = [], 0
    while len(ra) < so_canh:
        if i >= len(kho):
            rnd.shuffle(kho)
            if kho[0] == ra[-1] and len(kho) > 1:
                kho[0], kho[1] = kho[1], kho[0]
            i = 0
        ra.append(kho[i]); i += 1
    return ra


def xep_clip(so_canh, ty_le=0.30, seed=11):
    """Chọn cảnh nào dùng CLIP thay ảnh — chuẩn kênh 70-30 ảnh-video (anh chốt).

    Ba luật: cảnh đầu luôn là ẢNH (hook phải là người thật, đúng nhân vật của tin);
    không hai clip liền nhau (mắt cần điểm nghỉ); cảnh cuối cũng để ảnh cho câu chốt.
    """
    rnd = random.Random(seed)
    ung_vien = list(range(1, max(so_canh - 1, 2)))
    rnd.shuffle(ung_vien)
    chon = []
    for i in ung_vien:
        if len(chon) >= round(so_canh * ty_le):
            break
        if all(abs(i - c) > 1 for c in chon):
            chon.append(i)
    return sorted(chon)


def kho_clip():
    """Clip được phép chèn — CHỈ lấy từ hai ngăn ĐÃ DUYỆT, không lấy kho thô.

    Bài học 04/08 (anh loại mẻ hai): kho stock Mixkit tải về 9 clip thì cả 9 đều lạc —
    sân tập nghiệp dư, cổ động viên Nhật/Brazil ngồi phòng khách, một clip là người tập
    tạ, sân vận động thì ở London. Clip bóng đá chung chung KHÔNG dùng được cho tin
    tuyển quốc gia: người xem nhận ra ngay đó không phải trận đang nói.
    Muốn dùng clip thì phải là footage ĐÚNG TRẬN, hoặc stock đã có người xem và duyệt.
    """
    ds = sorted(glob.glob(os.path.join(DD.VIDEO_TRAN, "*.mp4")))
    ds += sorted(glob.glob(os.path.join(DD.VIDEO_STOCK,
                                        "da-duyet", "*.mp4")))
    return ds


def _vung_dau_clip(viec, cc):
    """QUÉT ĐOẠN CLIP sắp lên hình (anh chốt 07/08 tối): xác định toạ độ bảng tỉ số, logo
    đài, watermark và mọi lớp phủ đáng ngờ khác, trả vùng cần né — render sẽ cắt lệch +
    zoom cho chúng văng khỏi khung. Hai mắt bổ nhau, clip dưới 5 giây nên quét dày:

      · MẮT CHỮ  — OCR 7 vùng trên 4 khung hình rải đều đoạn: bắt tên đài, @tài khoản,
        chữ tỉ số… (thứ có chữ).
      · MẮT TĨNH — so 4 khung theo thời gian: pixel ĐỨNG YÊN giữa cảnh đang chuyển động
        chính là lớp phủ (logo thuần hình, khung tỉ số đồ hoạ — thứ OCR mù). Chỉ soi khi
        cả khung CÓ chuyển động thật, không thì cảnh tĩnh nào cũng thành "lớp phủ" oan.

    Caption giữa khung không né nổi bằng cắt — chỉ cảnh báo. Cache theo (tệp, đoạn)."""
    import tempfile
    import lay_anh
    p = os.path.join(viec, "anh", "vung-dau-clip.json")
    khoa = f"{cc['tep']}|{cc['tu']}|{cc['den']}"
    so = {}
    if os.path.exists(p):
        try:
            so = json.load(open(p, encoding="utf-8"))
        except Exception:
            so = {}
    if khoa in so:
        return so[khoa]
    src = os.path.join(viec, cc["tep"])
    tu, den = float(cc["tu"]), float(cc["den"])
    thay = set()
    # rút 4 khung rải đều TRONG ĐOẠN sẽ lên hình
    khung = []
    for f in (0.1, 0.4, 0.65, 0.9):
        tam = tempfile.mktemp(suffix=".png")
        try:
            subprocess.run(["ffmpeg", "-y", "-v", "quiet",
                            "-ss", f"{max(tu + (den - tu) * f, 0):.2f}",
                            "-i", src, "-frames:v", "1", tam], timeout=30)
            if os.path.exists(tam):
                khung.append(tam)
        except Exception:
            pass
    if len(khung) < 3:                     # không có khung thì đừng im lặng phán "sạch"
        print(f"    ⚠ quét clip: chỉ rút được {len(khung)} khung từ {cc['tep']} — BỎ QUÉT, "
              f"coi như CHƯA soi (không dám kết luận sạch)")
        return []
    # ── mắt CHỮ
    try:
        ok, _ = lay_anh._ocr_song_khong()
        dl = lay_anh._do_logo() if ok else None
    except Exception as e:                 # máy OCR nằm trên Drive — nghẽn thì còn mắt tĩnh
        print(f"    ⚠ mắt chữ nghỉ ({e}) — còn mắt soi lớp phủ tĩnh")
        dl = None
    # HAI MẮT BỎ PHIẾU CHÉO (chốt sau 3 vòng đo 07/08 tối — OCR đơn thuần bị rác-trên-cỏ
    # lặp giống nhau qua các khung lừa):
    #   · mẫu DẤU NGUỒN (tên đài/@/.vn) → né ngay, một khung là đủ;
    #   · chữ lặp ≥3/4 khung → chỉ né khi MẮT TĨNH xác nhận vùng đó đóng băng;
    #   · mắt tĩnh mù (cả nền vốn tĩnh) → đòi chuẩn khắt: lặp 4/4 khung VÀ token có
    #     nguyên âm/chữ số (rác OCR kiểu "sss/lll" bị loại).
    VUNG_NE = {"góc trên trái", "góc trên phải", "góc dưới trái", "góc dưới phải",
               "dải trên", "dải dưới"}
    dem_token = {}                                     # (vùng, token) → số khung xuất hiện
    if dl:
        for f in khung:
            try:
                for v, chu in dl.do_chu(f, la_anh=True).items():
                    c = (chu or "").strip()
                    if len(c) < 3:
                        continue
                    if v == "giữa khung":
                        print(f"    ⚠ clip có CHỮ GIỮA KHUNG (caption?) — cắt không né "
                              f"được, anh cân nhắc: “{c[:40]}”")
                        continue
                    if v not in VUNG_NE:
                        continue
                    if lay_anh.DAU_NGUON.search(c):
                        thay.add(v)
                        continue
                    for tk in {t.lower() for t in c.split() if len(t) >= 2}:
                        dem_token[(v, tk)] = dem_token.get((v, tk), 0) + 1
            except Exception:
                pass
    # ── mắt TĨNH
    vung_tinh, mat_tinh_chay = set(), False
    if len(khung) >= 3:
        try:
            import numpy as np
            from PIL import Image as _Anh
            a = np.stack([np.asarray(_Anh.open(f).convert("L").resize((160, 90)),
                                     dtype=np.float32) for f in khung])
            lech = a.std(axis=0)                       # độ nhúc nhích từng pixel qua 4 khung
            # LỚP PHỦ = pixel vừa ĐÓNG BĂNG vừa CÓ NÉT (viền hộp, nét chữ), đếm theo CỤM.
            # Đo thật 07/08 trên khung 160×90: vùng có logo/bảng tỉ số ra 169–373 pixel-phủ,
            # vùng sạch (kể cả cỏ phẳng đóng băng — không nét, và nhà cửa flycam — có nét
            # nhưng vẫn nhúc nhích) chỉ ≤42. Ngưỡng 100 nằm giữa với biên an toàn 4 lần.
            if float(lech.mean()) >= 4.0:              # clip đứng im hoàn toàn thì mù, thôi
                mat_tinh_chay = True
                tb = a.mean(axis=0)
                net = np.zeros_like(tb)
                net[:, 1:] += np.abs(np.diff(tb, axis=1))
                net[1:, :] += np.abs(np.diff(tb, axis=0))
                phu = (lech < 5.0) & (net > 12.0)
                H, W2 = phu.shape
                hop = {"góc trên trái": (0, 0, int(W2 * .32), int(H * .24)),
                       "góc trên phải": (int(W2 * .68), 0, W2, int(H * .24)),
                       "góc dưới trái": (0, int(H * .76), int(W2 * .32), H),
                       "góc dưới phải": (int(W2 * .68), int(H * .76), W2, H),
                       "dải trên": (0, 0, W2, int(H * .14)),
                       "dải dưới": (0, int(H * .86), W2, H)}
                for ten_v, (x1, y1, x2, y2) in hop.items():
                    if int(phu[y1:y2, x1:x2].sum()) >= 100:
                        vung_tinh.add(ten_v)
                thay |= vung_tinh
        except Exception as e:
            print(f"    ⚠ mắt tĩnh lỗi: {e}")
    # ── bỏ phiếu chéo cho chữ-lặp: rác OCR trên cỏ cũng lặp giống nhau, nên chữ-lặp chỉ
    # được né khi mắt tĩnh GẬT vùng đó. Mắt tĩnh mù (nền vốn tĩnh — không có trọng tài)
    # thì chỉ tin mẫu DẤU NGUỒN đã né ở trên, không phán thêm — thà sót còn hơn né oan,
    # đằng nào clip tầng MXH cũng qua mắt anh duyệt.
    if mat_tinh_chay:
        for (v, tk), n in dem_token.items():
            if n >= 3 and v in vung_tinh:
                thay.add(v)
    for f in khung:
        try:
            os.remove(f)
        except OSError:
            pass
    so[khoa] = sorted(thay)
    try:
        json.dump(so, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
    return so[khoa]


def dung(viec):
    kb = json.load(open(os.path.join(viec, "kich-ban.json")))
    if not kb.get("dat"):
        sys.exit(f"DỪNG — kịch bản chưa đạt: {kb.get('ly_do_khong_dat') or kb.get('loi')}")
    tmp = os.path.join(viec, "dung"); os.makedirs(tmp, exist_ok=True)

    # ── SEO CHẠY SONG SONG VỚI DỰNG (anh chốt 12/08: "giảm tối đa thời gian chờ ở
    # các bước") ──────────────────────────────────────────────────────────────────
    # Bắn NGAY ĐẦU, không đợi dựng xong: SEO chỉ cần TIÊU ĐỀ + LỜI BÌNH, đã có sẵn
    # trong `kb` từ dòng trên. Dựng ăn CPU (ffmpeg), SEO chỉ chờ mạng — chạy cùng
    # không làm dựng chậm. Xưởng dựng ~1–2 phút, SEO ~1,5 phút → dựng xong là SEO
    # cũng gần xong, bấm Kho chỉ còn chép tệp (đo được 0,2 giây).
    # An toàn: cả hai cùng ghi kich-ban.json nhưng đi qua cửa chung có khoá
    # (`kich_ban.ghi_gop`) nên không đè nhau; cờ `.dang-seo` chặn gọi model lần hai.
    if not (kb.get("tu_khoa") and kb.get("binh_luan_ghim")):
        try:
            subprocess.Popen(
                [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              "buoc3_xepkho.py"), "--seo", viec],
                stdout=open(os.path.join(viec, "seo-nen.log"), "w"),
                stderr=subprocess.STDOUT, start_new_session=True)
            print("  ⚙ SEO chạy SONG SONG (thẻ + bình luận ghim) — bấm Kho sẽ tức thì")
        except Exception as e:
            print(f"  ⚠ không bắn được SEO nền ({e}) — nút Kho sẽ tự sinh")

    # ── PHONG CÁCH RIÊNG CHO VIDEO NÀY (anh cấu hình ở trang /phong-cach, 12/08/2026) ──
    # Anh đặt DẢI, mỗi video rút một giá trị trong dải — gieo theo mã việc nên video nào
    # cũng khác video nào mà dựng lại vẫn ra y hệt. Chống "dấu vân tay dây chuyền".
    ts = PC.cho_video(viec, kb)
    PC.ap_vao_chuyen_dong(chuyen_dong, ts)
    print(f"  🎚 phong cách: zoom {ts['zoom_max']} · trượt {ts['pan_toc_do']}"
          f" · lệch tâm {ts['lech_tam']} · nhạc {ts['nhac_am_luong']}"
          f" (vào {ts['nhac_vao']}s / ra {ts['nhac_ra']}s)"
          f" · giọng vào {ts['giong_vao']}s / ra {ts['giong_ra']}s")
    print(f"  🎙 giọng: {ts['giong_ten']} ({ts['giong_ma']}) ×{ts['giong_toc_do']}"
          f" — chọn trong {ts['_so_giong']} giọng đang bật")

    # ① giọng — PHẢI KHỚP LỜI HIỆN TẠI. Trước 07/08 chỉ hỏi "có giong.mp3 chưa": anh sửa
    # lời xong dựng lại vẫn ra GIỌNG CŨ (anh bắt tối 07/08, mất một lần render). Nay mỗi lần
    # đọc giọng đều ghi kèm chính văn bản đã đọc (giong.mp3.loi) — lời đổi một chữ là đọc lại.
    giong = os.path.join(viec, "giong.mp3")
    p_loi_da_doc = giong + ".loi"
    loi_da_doc = None
    if os.path.exists(p_loi_da_doc):
        try:
            loi_da_doc = open(p_loi_da_doc, encoding="utf-8").read()
        except OSError:
            pass
    # DẤU VÂN TAY gồm CẢ MÃ GIỌNG + TỐC ĐỘ, không chỉ lời (vá 12/08 khi mở nhiều giọng):
    # anh đổi danh sách giọng mà lời không đổi thì bản cũ vẫn dùng lại file giọng CŨ —
    # đúng họ lỗi anh đã bắt tối 07/08, chỉ khác biến số. Đổi bất cứ thứ nào → đọc lại.
    van_tay = f"{ts['giong_ma']}|{ts['giong_toc_do']}|{kb['loi_binh']}"
    if not os.path.exists(giong) or loi_da_doc != van_tay:
        if os.path.exists(giong):
            print("  lời/giọng đã ĐỔI so với bản cũ" if loi_da_doc is not None
                  else "  giọng cũ không rõ đọc từ đâu", "→ đọc lại giọng VBee…")
        else:
            print("  đọc giọng VBee…")
        doc_giong(kb["loi_binh"], giong, ts["giong_toc_do"], ts["giong_ma"])
        open(p_loi_da_doc, "w", encoding="utf-8").write(van_tay)
    tong = do_dai(giong) + 0.55           # chừa đuôi cho câu chốt không bị cụt
    print(f"  giọng {tong:.1f}s")

    # ② NHỊP CẮT — ảnh anh gán quyết định chỗ cắt (anh chốt 05/08), không phải đồng hồ
    cau_moc = moc_cau(kb["loi_binh"], tong)
    ban_do = {}
    p_bd = os.path.join(viec, "anh", "ban-do-cau.json")
    if os.path.exists(p_bd):
        ban_do = {int(k): v for k, v in json.load(open(p_bd)).items()}
    # ②b CLIP GÁN THEO CÂU (GĐ2 trạm, anh đặt 07/08): anh xem clip trên trạm, cắt đoạn,
    # gán vào câu — xưởng thi hành đúng đoạn đó. Câu có clip phải MỞ một cảnh riêng nên
    # thêm mốc cắt vào bản đồ (ảnh kế thừa câu trước, đằng nào clip cũng đè lên).
    clip_canh = {}
    p_cc = os.path.join(viec, "anh", "clip-canh.json")
    if os.path.exists(p_cc):
        try:
            clip_canh = {int(k): v for k, v in json.load(open(p_cc)).items()}
        except Exception:
            clip_canh = {}
    def _tach_clip(ma):
        """clip::tệp::từ::đến[::x,y,w,h] → dict cho clip_canh; None nếu không phải clip.

        BẢN ĐỒ ẢNH CHỈ ĐƯỢC CHỨA ẢNH. Mã clip lọt vào đó là xưởng ghép nó với thư mục
        `anh/chon/` rồi đưa cho bộ đọc ảnh — ra `anh/chon/clip::clip/tay/...mp4::51.6`
        và chết ngay. Anh gặp đúng lỗi này 19/08.
        """
        if not (isinstance(ma, str) and ma.startswith("clip::")):
            return None
        ph = ma.split("::")
        if len(ph) < 4:
            return None
        try:
            d = {"tep": ph[1], "tu": float(ph[2]), "den": float(ph[3])}
        except ValueError:
            return None
        if len(ph) > 4 and ph[4]:
            try:
                _x, _y, _w, _h = (float(t) for t in ph[4].split(","))
                d["khung"] = {"x": _x, "y": _y, "w": _w, "h": _h}
            except ValueError:
                pass
        return d

    _da_doi_len = set()          # câu nào đã dời ô phụ b lên làm ô chính
    _ap_som = {}                 # ô phụ anh gán, bản dùng chung cho cả dựng lẫn soát
    if ban_do:
        # Ô CHÍNH TRỐNG MÀ CÓ Ô PHỤ → DỜI Ô PHỤ LÊN LÀM Ô CHÍNH (anh chốt 18/08).
        # Cổng soát bắt được 18/08 trên bài thật: câu 4 anh chỉ gán hình vào ô phụ 4b,
        # ô chính bỏ trống — thế là CẢ HAI cùng mất. Ô chính trống nên câu ấy không vào
        # bản đồ cảnh, kéo theo ô phụ chẳng còn chỗ mà lên hình.
        # Nuốt trọn công anh chọn hình, mà chẳng ai báo. Nay dời lên, hình vẫn lên đúng
        # câu ấy — chỉ đổi ô, không đổi nội dung.
        _ap_som.update({int(k): [x for x in (v or []) if x] for k, v in
                        (_nhap_tram(viec).get("anh_phu") or {}).items() if v})
        # ƯU TIÊN CẢNH VIDEO (anh chốt 18/08: "em phải luôn ưu tiên cảnh là video").
        # Câu ngắn chỉ mở nổi MỘT khung mà ô chính là ẢNH còn ô phụ là CLIP → đổi chỗ:
        # clip lên ô chính, ảnh xuống ô phụ. Không đổi thì clip anh đã bỏ công tìm, cắt,
        # khoanh khung né logo bị nuốt trọn — còn tấm ảnh tĩnh thì lên hình.
        # Đổi chỗ chứ KHÔNG bỏ ảnh: ảnh xuống ô phụ, câu nào đủ dài vẫn dùng tới.
        for _i, _ds in list(_ap_som.items()):
            if _i in ban_do and _ds and "::" in str(_ds[0]) \
                    and "::" not in str(ban_do[_i]):
                if NC.so_o_toi_da(cau_moc[_i] - (cau_moc[_i - 1] if _i else 0.0)) <= 1:
                    _cl = _tach_clip(_ds[0])
                    if _cl and _i not in clip_canh:
                        # Clip đi vào SỔ CLIP, ảnh Ở NGUYÊN ô chính làm nền. Bản 18/08
                        # đổi chỗ thẳng vào ban_do — mà ban_do chỉ được chứa ẢNH.
                        clip_canh[_i] = _cl
                        _ds.pop(0)
                        print(f"  ⇄ câu {_i + 1}: chỉ đủ MỘT khung → cho CLIP lên hình "
                              f"(ưu tiên cảnh video), ảnh làm nền")
        for _i, _ds in _ap_som.items():
            if _i not in ban_do and _ds:
                _cl = _tach_clip(_ds[0])
                if _cl:
                    # Ô phụ là CLIP: vào sổ clip, không vào bản đồ ảnh. Ảnh nền để
                    # nhánh ngay dưới mượn của câu trước — clip vẫn lên hình đúng câu.
                    if _i not in clip_canh:
                        clip_canh[_i] = _cl
                    _da_doi_len.add(_i)
                    print(f"  ↑ câu {_i + 1}: ô chính trống → dời CLIP ở ô phụ b lên "
                          f"({os.path.basename(_cl['tep'])[:40]})")
                    continue
                ban_do[_i] = _ds[0]
                _da_doi_len.add(_i)      # ô phụ b của câu này ĐÃ thành ô chính
                print(f"  ↑ câu {_i + 1}: ô chính trống → dời hình ở ô phụ b lên "
                      f"({os.path.basename(str(_ds[0]))[:40]})")
        # ── CẦU CHÌ: bản đồ ảnh KHÔNG BAO GIỜ được chứa mã clip ──────────────
        # Ba nhánh ở trên đều có thể lỡ tay đẩy mã clip vào đây, và hậu quả không hiện
        # ra ngay: xưởng ghép nó với `anh/chon/` rồi mới chết ở bộ đọc ảnh, cách chỗ
        # gây lỗi cả trăm dòng. Chặn tại đây thì dù nhánh nào sai, bài vẫn dựng được và
        # máy nói rõ nó vừa cứu chuyện gì.
        for _i in [k for k, v in ban_do.items() if _tach_clip(v)]:
            _cl = _tach_clip(ban_do.pop(_i))
            if _i not in clip_canh:
                clip_canh[_i] = _cl
            _da_doi_len.discard(_i)
            print(f"  🔌 câu {_i + 1}: mã clip lọt vào bản đồ ẢNH → chuyển sang sổ clip")

        for i in sorted(clip_canh):
            if i not in ban_do:
                for j in range(i - 1, -1, -1):
                    if j in ban_do:
                        ban_do[i] = ban_do[j]
                        break
    canh, bi_gop, qua_dai = (chuyen_dong.chia_nhip_theo_anh(cau_moc, ban_do, tong)
                             if ban_do else (None, [], []))
    if canh:
        print(f"  {len(canh)} cảnh cắt THEO ẢNH ĐÃ GÁN "
              f"({len(ban_do)} câu có ảnh riêng), nhịp {len(canh)/(tong/60):.0f} cắt/phút")
        if bi_gop:
            print(f"  ⚠️  {len(bi_gop)} ảnh KHÔNG lên hình — câu {[i+1 for i in bi_gop]} "
                  f"quá ngắn (dưới 1 giây) nên phải gộp vào cảnh trước")
        for b, k in qua_dai:
            print(f"  ⚠️  {b}s–{k}s ({k-b:.1f} giây) chỉ có MỘT ảnh — nên gán thêm ảnh cho đoạn này")
    else:
        canh = chuyen_dong.chia_nhip(cau_moc, tong, seed=hash(viec) % 999)
        print(f"  {len(canh)} cảnh, nhịp {len(canh)/(tong/60):.0f} cắt/phút")

    # ②c CẢNH NÀO THUỘC CÂU NÀO — CHỐT MỘT LẦN, NGAY ĐÂY, TRÊN MỐC GỐC.
    # Anh bắt 13/08: "tại sao cảnh 4b, 4c lại không được đưa vào video khi render?" —
    # gốc bệnh là chỗ này tra đi tra lại. Cảnh clip mượn giây của hàng xóm (③d) làm mốc
    # mở của cảnh KỀ SAU lùi lại vài phần mười giây; tra câu theo mốc ĐÃ DỊCH thì cảnh
    # rơi tụt về câu trước, kéo theo ảnh phụ của câu trước lên hình. Cảnh 4 nhận ảnh phụ
    # của câu 3, cảnh 6 nhận của câu 5 — im lặng, không báo lỗi gì.
    # Đúng họ lỗi đã ghi sổ 10/08 ("tra lại câu theo mốc SAU co giãn là trượt biên") mà
    # lần ấy chỉ vá cho khung đôi bằng cau_goc, còn hai chỗ tra khác vẫn tra theo mốc.
    # Nay: MỘT NGUỒN duy nhất, mọi nơi đọc lại chứ không ai được tự tra.
    mo_cau_goc = [next((ic for ic, m in enumerate(cau_moc) if b < m), len(cau_moc) - 1)
                  for (b, k) in canh]

    # ③ ảnh — ưu tiên thư mục "chon" nếu người đã lọc tay
    thu_chon = os.path.join(viec, "anh", "chon")
    chon_tay = os.path.isdir(thu_chon) and bool(glob.glob(os.path.join(thu_chon, "*.jpg")))
    kho_anh = sorted(glob.glob(os.path.join(thu_chon, "*.jpg"))) if chon_tay else \
              sorted(glob.glob(os.path.join(viec, "anh", "a*.jpg")))
    print(f"  {len(kho_anh)} ảnh" + (" (chọn tay, giữ nguyên thứ tự)" if chon_tay else ""))
    xep = xep_anh(kho_anh, len(canh), theo_thu_tu=chon_tay)

    # ③b cảnh nào dùng clip video
    clips_kho = kho_clip()
    vi_tri_clip = xep_clip(len(canh)) if clips_kho else []
    rnd_c = random.Random(viec)
    rnd_c.shuffle(clips_kho)

    # ③c BẢN ĐỒ CÂU → ẢNH (cách chữa dứt bệnh "nói người này, hiện người kia")
    #
    # Ảnh phải neo vào CÂU chứ không vào CẢNH. Cảnh cắt theo nhịp 3-4 giây, lời chạy theo
    # câu — hai thứ này lệch nhau ngay từ cảnh thứ hai, nên xếp ảnh theo thứ tự cảnh thì
    # tới giữa video là trượt hẳn. Anh bắt đúng lỗi này 04/08: câu nói Việt Anh đánh đầu
    # mà hiện ảnh hai cầu thủ khác tranh chấp.
    #
    # Ảnh nào đặt vào câu nào là quyết định của NGƯỜI ở trạm duyệt tài nguyên, engine chỉ
    # thi hành đúng bản đồ. Claude không nhận diện cầu thủ qua khuôn mặt — chỗ dựa là số áo,
    # tên in trên lưng áo, màu áo, bối cảnh sân và chú thích ảnh của báo.
    # Cách hiển thị NGƯỜI chọn cho từng ảnh (cắt đầy khung / vừa khung / trượt đọc).
    # Anh nêu 05/08: bảng tỷ số ngang lấy về mà xưởng cắt mất hai bên nên vô dụng.
    cach_hien = {}
    p_ch = os.path.join(viec, "anh", "cach-hien.json")
    if os.path.exists(p_ch):
        try:
            cach_hien = json.load(open(p_ch, encoding="utf-8"))
        except Exception:
            cach_hien = {}
    # cach-hien ghi theo TÊN GỐC, còn chon/ đánh số lại — tra qua bản dịch của trạm
    ten_goc_chon = {}
    p_tg = os.path.join(viec, "anh", "ten-goc-chon.json")
    if os.path.exists(p_tg):
        try:
            ten_goc_chon = json.load(open(p_tg, encoding="utf-8"))
        except Exception:
            ten_goc_chon = {}

    if ban_do:
        thu = os.path.join(viec, "anh", "chon")

        def _duong_anh(dang):
            """Giá trị trong ban_do → đường ảnh THẬT. Sổ này có HAI giọng:

            · tên trần `07.jpg`      — ảnh đã qua bước xếp kho, nằm trong `anh/chon/`
            · đường   `anh/n34.jpg`  — ảnh máy nháp/extension tải về, nằm ngay `anh/`

            Giọng thứ hai ra đời khi anh GÁN TAY rồi bấm Dựng luôn, không chờ chuỗi
            xếp kho đổi tên (anh kể rõ quy trình 19/08). Bản cũ chỉ hiểu giọng đầu,
            ghép mù `chon/ + anh/n34.jpg` → FileNotFoundError. Xưởng phải hiểu CẢ HAI
            — như `anh_phu` và `ghep_canh` vốn đã ghép từ gốc bài xưa nay.
            """
            if not dang:
                return None
            cac = ([os.path.join(viec, dang)] if "/" in dang else
                   [os.path.join(thu, dang), os.path.join(viec, "anh", dang)])
            for c in cac:
                if os.path.exists(c):
                    return c
            return None

        xep, dang = [], None
        for i_cau in mo_cau_goc:
            # lấy ảnh theo câu MỞ cảnh, không theo điểm giữa: cảnh giờ mở đúng tại câu anh
            # gán ảnh, nên lấy ở giữa là lại trượt sang câu sau (đúng lỗi vừa sửa).
            for i in range(i_cau, -1, -1):          # câu chưa khai thì kế thừa câu trước
                if i in ban_do:
                    dang = ban_do[i]; break
            d_that = _duong_anh(dang)
            if dang and not d_that:
                # tệp anh gán đã mất (dọn kho, đổi tên) — KÊU TO rồi dùng ảnh nền thay,
                # để cả bài không chết vì một tấm; cổng soát cảnh cuối vẫn đếm lại đủ.
                print(f"  ⚠ ảnh anh gán '{dang}' không còn trên đĩa — thay bằng ảnh nền")
            xep.append(d_that or kho_anh[0])
        dung_that = len({os.path.basename(x) for x in xep})
        print(f"  ảnh neo theo câu · {dung_that}/{len(set(ban_do.values()))} ảnh anh chọn LÊN HÌNH")
    elif chon_tay:
        xep, k = [], 0
        for i in range(len(canh)):
            if i in vi_tri_clip and clips_kho:
                xep.append(None)
            else:
                xep.append(kho_anh[k % len(kho_anh)]); k += 1

    # ③d CLIP THEO CÂU — tìm cảnh MỞ đúng câu đã gán, rồi GIÃN cảnh lân cận cho khớp
    # đoạn cắt (anh chốt 07/08: "cảnh 3,2s mà clip 4s thì tự giãn cảnh kế trước và sau").
    # Chỉ dịch RANH GIỚI hai bên cảnh clip nên tổng thời lượng và mọi mốc khác giữ nguyên;
    # hàng xóm không được tụt dưới 1 giây, thiếu thì cắt bớt đoạn clip và báo.
    clip_cua_canh = {}
    if clip_canh and ban_do:
        canh = [list(c) for c in canh]
        canh_mo = mo_cau_goc                       # ②c — không tra lại theo mốc
        for i_cau, cc in sorted(clip_canh.items()):
            idx = next((x for x, ic in enumerate(canh_mo) if ic == i_cau), None)
            if idx is None:
                print(f"  ⚠️  clip gán câu {i_cau + 1} không có cảnh mở riêng — bỏ qua")
                continue
            can = max(0.8, float(cc["den"]) - float(cc["tu"]))
            b, k = canh[idx]
            lech = can - (k - b)
            if abs(lech) >= 0.05:
                du_truoc = (canh[idx - 1][1] - canh[idx - 1][0] - 1.0) if idx > 0 else 0.0
                du_sau = (canh[idx + 1][1] - canh[idx + 1][0] - 1.0) \
                    if idx + 1 < len(canh) else 0.0
                if lech > 0:                       # clip dài hơn lời cảnh → mượn hàng xóm
                    truoc = min(lech / 2 if du_sau > 0 else lech, max(du_truoc, 0.0))
                    sau = min(lech - truoc, max(du_sau, 0.0))
                else:                              # clip ngắn hơn → trả giây cho hàng xóm
                    truoc = lech / 2 if (idx > 0 and idx + 1 < len(canh)) \
                        else (lech if idx > 0 else 0.0)
                    sau = lech - truoc if idx + 1 < len(canh) else 0.0
                if idx > 0:
                    canh[idx - 1][1] -= truoc
                    canh[idx][0] -= truoc
                if idx + 1 < len(canh):
                    canh[idx][1] += sau
                    canh[idx + 1][0] += sau
                thieu = can - (canh[idx][1] - canh[idx][0])
                if thieu > 0.05:
                    cc = dict(cc)
                    cc["den"] = float(cc["tu"]) + (canh[idx][1] - canh[idx][0])
                    print(f"  ⚠️  cảnh {idx + 1}: hàng xóm không đủ giây cho mượn — "
                          f"cắt đoạn clip còn {cc['den'] - float(cc['tu']):.1f}s")
                else:
                    print(f"  cảnh {idx + 1} dùng CLIP {can:.1f}s (lời {k - b:.1f}s) → "
                          f"mượn {truoc:+.1f}s cảnh trước · {sau:+.1f}s cảnh sau")
            clip_cua_canh[idx] = cc
        vi_tri_clip = [v for v in vi_tri_clip if v not in clip_cua_canh]

    # ③đ NGUYÊN TẮC NHỊP CẢNH (anh chốt 07/08 tối): mọi cảnh ẢNH phải nằm trong
    # [2,5s – 5s] — dài quá thì đơ, ngắn quá thì vụn. Ba phép theo thứ tự:
    #   ① cảnh > 5s TÁCH đều thành phần ≤5s; ảnh lấy từ Ô CẢNH PHỤ anh điền trên trạm
    #     (anh_phu — ảnh hoặc đoạn clip "clip::tệp::từ::đến"); thiếu phụ thì dùng lại
    #     ảnh chính (mỗi phần một kiểu chuyển động cho có nhịp cắt) + nhắc anh điền.
    #   ② cảnh < 2,5s MƯỢN giây của hàng xóm còn dư (hàng xóm không được tụt dưới 2,5s).
    #   ③ cảnh CLIP anh tự cắt đoạn thì giữ nguyên — anh đã quyết độ dài, máy không đụng.
    CANH_MAX, CANH_MIN = 5.0, 2.5
    # DÙNG LẠI `_ap_som` — bản đã qua hai phép chỉnh ở trên (dời ô phụ lên khi ô chính
    # trống · đổi chỗ để clip lên ô chính). Đọc lại từ đĩa là quay về bản CHƯA chỉnh,
    # nên phép đổi chỗ coi như chưa từng xảy ra và cổng soát báo oan.
    # Tấm đã dời lên ô chính thì cắt khỏi ô phụ — khỏi lên hình HAI LẦN.
    anh_phu = {i: (v[1:] if i in _da_doi_len else v)
               for i, v in _ap_som.items() if v} if ban_do else {}
    cap_cung_anh = set()                           # các cặp cảnh con dùng CHUNG một ảnh
    o_cua = ["c"] * len(canh)                      # video không qua trạm: mọi cảnh coi là ô chính
    cau_goc = None                                 # sẽ xây trong ③đ khi có ban_do
    if ban_do:
        canh = [list(c) for c in canh]
        # ②c — ĐỌC nguồn đã chốt, KHÔNG tra lại: tới đây mốc cảnh đã bị ③d dịch vì clip
        # mượn giây, tra theo mốc là cảnh kề clip rơi tụt về câu trước (anh bắt 13/08).
        mo_cau = list(mo_cau_goc)
        # CO GIÃN bằng module nhip_canh DÙNG CHUNG với trạm (anh chốt 09/08: "cắt thời
        # gian cho cảnh ngắn đủ 2,5s trước, còn lại mới chia đều cho các khung") — trạm
        # hiển thị gì thì xưởng dựng đúng cái đó, hết cảnh một logic hai bản.
        la_clip_cau = [idx in clip_cua_canh or idx in vi_tri_clip
                       for idx in range(len(canh))]
        # số ảnh PHỤ anh đã gán cho từng cảnh — ý người, nhịp phải mở đủ ô (13/08)
        so_phu_cau = [len([x for x in (anh_phu.get(mo_cau[idx]) or []) if x])
                      for idx in range(len(canh))]
        nhip = NC.chia_nhip([k - b for (b, k) in canh], la_clip_cau, so_phu_cau)
        moc_chay = canh[0][0]
        for idx, nh in enumerate(nhip):
            if abs(nh["muon"]) > 0.05:
                print(f"  cảnh {idx + 1}: {'mượn' if nh['muon'] > 0 else 'cho mượn'} "
                      f"{abs(nh['muon']):.1f}s → {nh['dai']:.1f}s")
            canh[idx][0] = moc_chay
            moc_chay += nh["dai"]
            canh[idx][1] = moc_chay
        # ① tách cảnh dài. o_cua chạy SONG SONG với canh2: mỗi cảnh video nhớ mình sinh
        # từ Ô NÀO của trạm ("c" = ô chính, "0"/"1"… = ô phụ theo SỐ SLOT trên giao diện,
        # None = clip) — cảnh đôi và lật giờ tính THEO Ô độc lập (anh chốt 09/08:
        # chính/phụ không dây dưa nhau), thiếu map này là không biết ô nào ghép ô nào.
        # cau_goc chạy SONG SONG với canh2: mỗi cảnh con NHỚ CÂU NGUỒN từ lúc cắt (anh
        # bắt 10/08: tra lại câu theo mốc thời gian SAU co giãn nhịp là trượt biên —
        # khung đôi câu 10 áp nhầm sang cảnh câu 11, còn cảnh câu 10 mất nửa dưới)
        canh2, xep2, clip2, vtc2, o_cua, cau_goc = [], [], {}, [], [], []
        for idx, ((b, k), a) in enumerate(zip(canh, xep)):
            if idx in clip_cua_canh and nhip[idx]["so_phan"] <= 1:
                clip2[len(canh2)] = clip_cua_canh[idx]
                # clip giữ Ô THẬT "c" (anh ra luật 09/08 khuya: clip bình đẳng ảnh —
                # cần ô để tra cờ lật per-ô + khung đôi; trước đây None là mất dấu)
                canh2.append([b, k]); xep2.append(a); o_cua.append("c")
                cau_goc.append(mo_cau[idx]); continue
            if idx in vi_tri_clip:
                vtc2.append(len(canh2))
                canh2.append([b, k]); xep2.append(a); o_cua.append(None)
                cau_goc.append(mo_cau[idx]); continue
            dai = k - b
            so = nhip[idx]["so_phan"]              # số khung từ module nhịp dùng chung
            if so <= 1:
                canh2.append([b, k]); xep2.append(a); o_cua.append("c")
                cau_goc.append(mo_cau[idx]); continue
            buoc = dai / so
            phu = []                               # [(số slot trên trạm, đường/mã clip)]
            for sl, p in enumerate(anh_phu.get(mo_cau[idx], [])):
                if isinstance(p, str) and p.startswith("clip::"):
                    phu.append((sl, p))            # đoạn clip cho cảnh phụ — giữ nguyên mã
                elif p and os.path.exists(os.path.join(viec, p)):
                    phu.append((sl, os.path.join(viec, p)))
            # khung ĐẦU: cảnh clip thì là chính đoạn clip anh cắt (anh bắt 13/08 —
            # trước đây cảnh clip bị bỏ qua cả khâu chia nên ảnh phụ không lên hình)
            dau = ("c", "clip::" + clip_cua_canh[idx]["tep"]
                   + f"::{clip_cua_canh[idx]['tu']}::{clip_cua_canh[idx]['den']}"
                   + ((f"::{clip_cua_canh[idx]['khung']['x']},{clip_cua_canh[idx]['khung']['y']},"
                       f"{clip_cua_canh[idx]['khung']['w']},{clip_cua_canh[idx]['khung']['h']}")
                      if clip_cua_canh[idx].get("khung") else "")) \
                if idx in clip_cua_canh else ("c", a)
            hinh = [dau] + [(str(sl), p) for sl, p in phu]
            thieu_phu = so - 1 - len(phu)
            for j in range(so):
                o, h = hinh[j] if j < len(hinh) else ("c", a)   # thiếu → dùng lại ô chính
                canh2.append([b + j * buoc, b + (j + 1) * buoc])
                if isinstance(h, str) and h.startswith("clip::"):
                    # dạng: clip::tệp::từ::đến[::x,y,w,h] — đuôi thứ 5 là KHUNG né logo
                    # người tự chọn trên trạm (anh đặt 09/08 tối), vắng thì như cũ
                    ph = h.split("::")
                    clip2[len(canh2) - 1] = {"tep": ph[1], "tu": float(ph[2]),
                                             "den": float(ph[3])}
                    if len(ph) > 4 and ph[4]:
                        try:
                            x_k, y_k, w_k, h_k = (float(t) for t in ph[4].split(","))
                            clip2[len(canh2) - 1]["khung"] = {"x": x_k, "y": y_k,
                                                              "w": w_k, "h": h_k}
                        except ValueError:
                            pass
                    xep2.append(a); o_cua.append(o)   # clip ô phụ giữ SỐ SLOT thật
                    cau_goc.append(mo_cau[idx])
                else:
                    if h == a and j > 0:
                        cap_cung_anh.add(len(canh2) - 1)
                    xep2.append(h); o_cua.append(o)
                    cau_goc.append(mo_cau[idx])
            print(f"  cảnh {idx + 1} dài {dai:.1f}s → tách {so} phần {buoc:.1f}s"
                  + (f" — ⚠ thiếu {thieu_phu} ảnh phụ, phần thiếu dùng lại ảnh chính "
                     f"(điền thêm ở ô cảnh phụ trên trạm)" if thieu_phu > 0 else ""))
        canh, xep, clip_cua_canh, vi_tri_clip = canh2, xep2, clip2, vtc2
        # (phép mượn giây đã chuyển vào nhip_canh.chia_nhip — chạy TRƯỚC vòng tách)
        # ②b còn cảnh vụn (kẹt cạnh clip / hàng xóm cạn) → GỘP vào cảnh ảnh kề: một ảnh
        # trải hai câu — chính là phép "kế thừa" quen thuộc, còn hơn một cảnh 1-2s giật cục
        i2 = 0
        while i2 < len(canh):
            la_clip = set(clip_cua_canh) | set(vi_tri_clip)
            if i2 in la_clip:
                i2 += 1
                continue
            d_i = canh[i2][1] - canh[i2][0]
            if d_i >= CANH_MIN - 0.15:
                i2 += 1
                continue
            ung = next((hx for hx in (i2 - 1, i2 + 1)
                        if 0 <= hx < len(canh) and hx not in la_clip
                        and (canh[hx][1] - canh[hx][0]) + d_i <= CANH_MAX + 0.01), None)
            if ung is None:
                print(f"  ⚠ cảnh {i2 + 1} vụn {d_i:.1f}s kẹt giữa các cảnh clip — giữ nguyên")
                i2 += 1
                continue
            # ĐỪNG NUỐT CẢNH CÓ HÌNH RIÊNG (anh chốt 18/08: "kiểm xem có cảnh bị nuốt
            # không, có thì tự khắc phục"). Gộp là XOÁ HẲN một cảnh — ảnh anh chọn cho
            # nó không bao giờ lên hình, mà chẳng ai báo.
            # Chỉ đáng gộp khi cảnh vụn và cảnh kề DÙNG CHUNG một hình (gộp lại thì
            # người xem không mất gì). Hai hình khác nhau thì thà để cảnh ngắn hơn
            # chuẩn 2,5s — miễn còn trên SÀN TUYỆT ĐỐI, dưới sàn mới thật sự giật.
            h_i2 = str(xep[i2] or "")
            h_ung = str(xep[ung] or "")
            if h_i2 and h_ung and h_i2 != h_ung and d_i >= SAN_CANH:
                print(f"  cảnh {i2 + 1} vụn {d_i:.1f}s nhưng có HÌNH RIÊNG "
                      f"→ giữ lại, không gộp (ưu tiên không nuốt cảnh)")
                i2 += 1
                continue
            giu = ung if (canh[ung][1] - canh[ung][0]) >= d_i else i2
            lo, hi = min(i2, ung), max(i2, ung)
            print(f"  cảnh {i2 + 1} vụn {d_i:.1f}s → GỘP với cảnh kề "
                  f"({canh[lo][0]:.1f}–{canh[hi][1]:.1f}s, một ảnh trải hai câu)")
            canh[lo] = [canh[lo][0], canh[hi][1]]
            xep[lo] = xep[giu]
            o_cua[lo] = o_cua[giu]                 # ô nguồn đi theo ảnh được giữ
            cau_goc[lo] = cau_goc[giu]             # câu nguồn cũng đi theo ảnh được giữ
            del canh[hi], xep[hi], o_cua[hi], cau_goc[hi]
            clip_cua_canh = {(k - 1 if k > hi else k): v
                             for k, v in clip_cua_canh.items()}
            vi_tri_clip = [(k - 1 if k > hi else k) for k in vi_tri_clip]
            cap_cung_anh = {(k - 1 if k > hi else k) for k in cap_cung_anh if k != hi}
            i2 = lo + 1

    # ══ ③d CỔNG SOÁT CẢNH BỊ NUỐT (anh chốt 18/08) ═══════════════════════════
    # "Khi dựng video thì tự kiểm xem có cảnh bị nuốt không, nếu có thì tự tìm nguyên
    # nhân và khắc phục. Chạy thử khoảng 6 lần sản xuất video, nếu không có cảnh nào
    # bị nuốt thì tự kết thúc việc kiểm tra."
    #
    # Nuốt cảnh = hình anh đã gán cho một ô mà KHÔNG lên video. Ba đường dẫn tới:
    #   ① gộp cảnh vụn — xoá hẳn một cảnh. ĐÃ CHẶN ở trên: chỉ gộp khi hai cảnh dùng
    #      chung một hình, hoặc khi cảnh ngắn dưới sàn 1,6s (lúc ấy gộp mới đúng).
    #   ② nhịp bớt khung — ô phụ bị cắt vì mỗi khung sẽ ngắn dưới 2,5s
    #   ③ trần ô — câu 6s chỉ chứa 2 ô, gán 3 hình thì tấm thứ ba rơi
    #
    # Cổng ĐẾM LIÊN TIẾP: sáu lần dựng thật liên tiếp không nuốt cảnh nào thì tự đóng
    # sổ, từ đó chỉ in một dòng gọn. Có lần nào nuốt là đếm lại từ đầu.
    try:
        _so_o_len = 0
        _da_len = set()
        for _i_c, _o in enumerate(o_cua):
            _cau_c = cau_goc[_i_c] if _i_c < len(cau_goc) else None
            if _cau_c is None:
                continue
            _so_o_len += 1
            if _o is not None:
                _da_len.add((_cau_c, str(_o)))
        _nuot = []
        for _c_s, _ds in (anh_phu or {}).items():
            for _j, _a in enumerate([x for x in (_ds or [])]):
                if _a and (_c_s, str(_j)) not in _da_len:
                    _nuot.append((_c_s, _j, os.path.basename(str(_a))))

        _p_so = os.path.expanduser("~/.config/socbongda247/soat-nuot-canh.json")
        os.makedirs(os.path.dirname(_p_so), exist_ok=True)
        try:
            _so = json.load(open(_p_so, encoding="utf-8"))
        except Exception:
            _so = {"sach_lien_tiep": 0, "tong_lan": 0, "da_dong": False, "lich_su": []}
        _so["tong_lan"] = _so.get("tong_lan", 0) + 1
        _so["sach_lien_tiep"] = 0 if _nuot else _so.get("sach_lien_tiep", 0) + 1
        _so["lich_su"] = (_so.get("lich_su") or [])[-19:] + [
            {"ma": os.path.basename(viec), "luc": time.strftime("%Y-%m-%d %H:%M"),
             "nuot": len(_nuot), "o_len_hinh": _so_o_len}]
        _da_dong_truoc = _so.get("da_dong")
        if _so["sach_lien_tiep"] >= 6:
            _so["da_dong"] = True

        if _nuot:
            _so["da_dong"] = False               # có nuốt là mở sổ lại, theo dõi tiếp
            print(f"  ⚠️  {len(_nuot)} HÌNH ANH GÁN KHÔNG LÊN VIDEO:")
            for _c_s, _j, _ten in _nuot[:8]:
                print(f"       cảnh {_c_s + 1}{chr(98 + _j)} · {_ten}")
            print("       NGUYÊN NHÂN: câu quá ngắn nên nhịp không mở đủ ô "
                  "(mỗi ô cần ≥ 2,5 giây).")
            print("       CÁCH CHỮA: bớt hình phụ ở câu đó, hoặc viết lời dài thêm "
                  "cho câu ấy rồi đọc lại giọng.")
            print(f"       (đếm lại từ đầu — cần 6 lần dựng liên tiếp sạch mới đóng sổ)")
        elif not _da_dong_truoc:
            _con = max(0, 6 - _so["sach_lien_tiep"])
            print(f"  ✅ soát cảnh: {_so_o_len} ô lên hình đủ, không cảnh nào bị nuốt"
                  + (f"  ({_so['sach_lien_tiep']}/6 lần sạch"
                     + (f", còn {_con} lần)" if _con else ") — ĐÓNG SỔ THEO DÕI ✔")))
        else:
            print(f"  ✅ soát cảnh: đủ {_so_o_len} ô (sổ đã đóng sau 6 lần sạch)")
        json.dump(_so, open(_p_so, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception as _e:
        print(f"  ⚠ không soát được cảnh bị nuốt: {_e}")

    # ③e vùng watermark cần né (anh chốt 07/08): tấm anh xác nhận "vẫn dùng" ở cổng
    # DUYỆT thì lúc dựng khung cắt phải TỰ né vùng logo — vị trí đọc từ sổ nguồn
    # (OCR theo 7 vùng đã chạy sẵn ở trạm, không tốn thêm lượt soi nào).
    vung_anh, chu_anh = {}, {}
    p_sn = os.path.join(viec, "anh", "so-nguon.jsonl")
    if os.path.exists(p_sn):
        for dong in open(p_sn, encoding="utf-8"):
            try:
                d_sn = json.loads(dong)
            except Exception:
                continue
            chu_anh[d_sn.get("file", "")] = d_sn.get("chu_doc_duoc", "") or ""
            if d_sn.get("bo_qua_dau_nguon") and not d_sn.get("da_crop"):
                # ảnh đã CROP: vùng watermark cũ tính theo ảnh trước khi cắt — vô nghĩa,
                # thường chính watermark là phần bị cắt bỏ → thôi né (tự soi 09/08)
                vs = chuyen_dong.doc_vung_tranh(d_sn.get("chu_doc_duoc", ""))
                if vs:
                    vung_anh[d_sn["file"]] = vs

    def _anh_co_chu(duong_a):
        """Ảnh CHỤP nhưng có CHỮ TO trong khung (backdrop CHAMPIONS, banner tài trợ) —
        lật là chữ ngược lộ liễu (bắt được ngay ở ca thử 09/08). Tra OCR sẵn của cổng
        vào (không tốn lượt soi): có cụm chữ dài ≥7 ký tự hoặc ≥3 cụm ≥4 ký tự → coi
        như có chữ, ĐỪNG lật."""
        ten = os.path.basename(duong_a or "")
        chu = chu_anh.get(ten) or chu_anh.get(os.path.basename(
            ten_goc_chon.get(ten, "")), "")
        cum = [c for c in re.findall(r"[A-Za-zÀ-ỹ]{4,}", chu)]
        return any(len(c) >= 7 for c in cum) or len(cum) >= 3

    # ③g LẬT ẢNH + CẢNH ĐÔI theo TỪNG Ô (anh chốt 09/08: chính/phụ ĐỘC LẬP hoàn toàn)
    # · lat_anh: MẶC ĐỊNH LẬT trái-phải mọi cảnh ảnh CHỤP; sổ chỉ ghi Ô anh TẮT —
    #   key "5" = ô chính câu 6, "5:0" = ô phụ 1 của câu 6. Đồ hoạ/bảng KHÔNG lật.
    # · ghep_canh: {"câu": {"ô": {"anh2": "anh/x.jpg", "dao": bool}}} — Ô NÀO bật thì
    #   chính ảnh của ô đó đứng cùng anh2 CỦA RIÊNG NÓ trong khung đôi trên/dưới.
    nh_tram = _nhap_tram(viec)
    lat_khai = nh_tram.get("lat_anh", {})
    ghep_khai = nh_tram.get("ghep_canh", {})
    # câu nguồn LẤY TỪ SỔ CẮT (cau_goc ghi lúc tách cảnh) — tra lại theo mốc thời gian
    # là trượt biên sau co giãn nhịp (anh bắt 10/08: ghép câu 10 áp nhầm cảnh câu 11).
    # Video KHÔNG qua trạm thì không có vòng tách nên cảnh vẫn một-đối-một với bản gốc,
    # đọc thẳng mo_cau_goc — vẫn là MỘT nguồn, không ai tra lại theo mốc nữa (②c 13/08).
    cau_cua = cau_goc if cau_goc is not None else list(mo_cau_goc[:len(canh)])
    def _ben_ghep(x):
        """Một NỬA khung đôi: đường ảnh (tuyệt đối) hoặc mã clip:: → dict cho render."""
        if isinstance(x, str) and x.startswith("clip::"):
            ph = x.split("::")
            b = {"clip": {"tep": os.path.join(viec, ph[1]), "tu": float(ph[2]),
                          "den": float(ph[3])}}
            if len(ph) > 4 and ph[4]:
                try:
                    xk, yk, wk, hk = (float(t) for t in ph[4].split(","))
                    b["clip"]["khung"] = {"x": xk, "y": yk, "w": wk, "h": hk}
                except ValueError:
                    pass
            return b
        return {"anh": x}

    ghep_canh_i = {}
    if ghep_khai and ban_do:
        for i_c, c_i in enumerate(cau_cua):
            o = o_cua[i_c]
            cfg = (ghep_khai.get(str(c_i)) or {}).get(o) if o else None
            # cờ "tat": anh tắt khung đôi nhưng vẫn GIỮ ảnh thứ hai để bật lại — xưởng
            # phải tôn trọng, không thì tắt trên trạm mà dựng vẫn ghép (anh bắt 09/08)
            if not cfg or cfg.get("tat"):
                continue
            a2 = cfg.get("anh2") or ""
            # nửa thứ hai: ẢNH hoặc ĐOẠN CLIP (anh ra luật 09/08 khuya — mọi tổ hợp)
            if a2.startswith("clip::"):
                ben2 = _ben_ghep(a2)
                if not os.path.exists(ben2["clip"]["tep"]):
                    print(f"  ⚠ câu {c_i + 1}: nửa thứ hai là clip nhưng tệp mất — bỏ qua")
                    continue
            elif a2 and os.path.exists(os.path.join(viec, a2)):
                ben2 = {"anh": os.path.join(viec, a2)}
            else:
                print(f"  ⚠ câu {c_i + 1} ô {'chính' if o == 'c' else 'phụ ' + str(int(o) + 1)}"
                      f" bật GHÉP ĐÔI nhưng chưa có nửa thứ hai — bỏ qua")
                continue
            # nửa CỦA Ô: cảnh này là cảnh CLIP thì nửa đó là clip, không thì là ảnh
            if i_c in clip_cua_canh:
                cc0 = clip_cua_canh[i_c]
                ben1 = {"clip": {"tep": os.path.join(viec, cc0["tep"]),
                                 "tu": float(cc0["tu"]), "den": float(cc0.get("den", 0))}}
                if cc0.get("khung"):
                    ben1["clip"]["khung"] = cc0["khung"]
            elif xep[i_c]:
                ben1 = {"anh": xep[i_c]}
            else:
                continue
            tren, duoi = (ben2, ben1) if cfg.get("dao") else (ben1, ben2)
            ghep_canh_i[i_c] = (tren, duoi)

    def _lat_o(i_c):
        """Cờ lật của cảnh i_c theo Ô nguồn — ẢNH mặc định KHÔNG lật (anh đổi 09/08,
        sổ ghi true mới bật); CLIP mặc định LẬT (anh ra luật 09/08 khuya — né trùng
        nội dung nguồn, sổ ghi false mới tắt)."""
        o = o_cua[i_c] or "c"
        k = str(cau_cua[i_c]) if o == "c" else f"{cau_cua[i_c]}:{o}"
        v = lat_khai.get(k)
        if i_c in clip_cua_canh:
            return v is not False
        return v is True

    # ④ lớp phủ
    # CỬA CUỐI CHO CỤM TÔ VÀNG (anh bắt 11/08: video sáng nay tít TRẮNG TRƠN). Việc chọn
    # cụm vốn chỉ chạy trong chuỗi sau-Duyệt-lời; bài paste tin rồi dựng thẳng thì không
    # ai chọn, và xưởng vẽ trắng IM LẶNG. Nay thiếu thì tự chọn tại đây rồi ghi lại kịch
    # bản — thà tốn một lượt haiku còn hơn ra video hỏng phải dựng lại.
    cum_vang_ds = kb.get("cum_to_vang") or []
    if not cum_vang_ds:
        cum_vang_ds = CV.bao_dam(os.path.join(viec, "kich-ban.json"))
        print(f"  ⚠ kịch bản thiếu cụm tô vàng — tự chọn: "
              f"{' · '.join(cum_vang_ds) if cum_vang_ds else 'KHÔNG CHỌN ĐƯỢC, tít sẽ trắng'}")
    overlay, sd, cx = lam_overlay(kb["tieu_de"], cum_vang_ds,
                                  os.path.join(tmp, "overlay.png"),
                                  goc_wm=kb.get("goc_watermark"))
    print(f"  tiêu đề {sd} dòng, cỡ {cx}px · vàng: "
          f"{' · '.join(cum_vang_ds) if cum_vang_ds else '(không có)'}")

    # ⑤ CHỌN KIỂU CHUYỂN ĐỘNG TRƯỚC, cân cho cả video rồi mới render
    #
    # Chọn theo hình dáng từng ảnh là đúng cho từng cảnh, nhưng gom cả video lại thì hỏng:
    # kho ảnh bóng đá gần như toàn ảnh ngang nên cả video chạy ngang 100%, nhìn một lúc là
    # đơn điệu (anh chốt 05/08: không kiểu nào được quá 65%).
    ds_ty, ds_kieu, ds_tranh, ep_vua = [], [], [], set()
    for i, anh in enumerate(xep):
        ten_a = os.path.basename(anh or "")
        rieng = cach_hien.get(ten_a) or cach_hien.get(       # người đã chỉ định thì tôn trọng
            os.path.basename(ten_goc_chon.get(ten_a, "")))   # (tra cả tên gốc trước khi chốt)
        if i in clip_cua_canh or (i in vi_tri_clip and clips_kho):
            ds_ty.append(1.0); ds_kieu.append("clip"); ds_tranh.append(None); continue
        if i in ghep_canh_i:                       # cảnh đôi: kiểu riêng, không cân không rải
            ds_ty.append(1.0); ds_kieu.append("ghep"); ds_tranh.append(None); continue
        # cách hiển thị NGƯỜI đã chỉ tay (vd bảng tỷ số phải "vừa khung") thì tôn trọng,
        # không ép né — còn lại tấm có dấu nguồn là máy tự né vùng logo
        vs = None if rieng else vung_anh.get(os.path.basename(anh or ""))
        if vs and "giữa khung" in vs:
            print(f"  ⚠️  cảnh {i + 1}: dấu nguồn nằm GIỮA KHUNG — máy không né nổi, "
                  f"anh cân nhắc đổi ảnh")
            vs = [v for v in vs if v != "giữa khung"] or None
        la_bang = False
        try:
            im_i = Image.open(anh)
            w, h = im_i.size
            # đồ hoạ bảng biểu (BXH, tỷ số) máy TỰ nhận → ép VỪA KHUNG, zoom/cắt là mất
            # cột tên đội với cột điểm (anh bắt 08/08); bảng thắng cả phép né watermark
            la_bang = not rieng and chuyen_dong.la_do_hoa_bang(im_i)
        except Exception:
            w, h = 16, 9
        if la_bang:
            vs = None
            print(f"  cảnh {i + 1}: ảnh ĐỒ HOẠ BẢNG BIỂU → hiện vừa khung trọn vẹn")
        ds_tranh.append(vs)
        if vs:
            print(f"  cảnh {i + 1}: NÉ dấu nguồn ở {', '.join(vs)}")
        ds_ty.append(w / max(h, 1))
        ds_kieu.append(rieng or ("vua" if la_bang else
                                 chuyen_dong.chon_kieu(w, h, W, ANH_CAO)))
        if la_bang:
            ep_vua.add(i)
    from collections import Counter as _C
    print("  soi kiểu: " + " · ".join(f"{k}×{n}" for k, n in _C(ds_kieu).most_common())
          + "   (ảnh: " + ", ".join(f"{os.path.basename(a or '?')}={ds_kieu[i]}"
                                    for i, a in enumerate(xep[:6])) + " …)")
    ds_kieu, loi_can = chuyen_dong.can_bang_kieu(ds_kieu, ds_ty,
                                                 tran=ts['tran_mot_kieu'])
    # hai phần tách từ một cảnh mà DÙNG CHUNG ảnh (thiếu phụ) thì phải KHÁC kiểu chuyển
    # động — cùng kiểu là nhìn như một cảnh dài, mất luôn nhịp cắt vừa tách
    for i_c in sorted(cap_cung_anh):
        if 0 < i_c < len(ds_kieu) and ds_kieu[i_c] == ds_kieu[i_c - 1] \
                and ds_kieu[i_c] not in ("clip", "ghep"):
            ds_kieu[i_c] = "zoom" if ds_kieu[i_c] != "zoom" else "ngang"
    for i_c in ep_vua:                             # bảng biểu không cho phép cân kiểu đổi đi
        ds_kieu[i_c] = "vua"
    if loi_can:
        print(f"  {loi_can}")
    # HƯỚNG chuyển động rải theo cả video: không lặp liền kề, dùng đều các hướng.
    # Anh chốt 05/08: video nào cũng zoom-vào-từ-tâm rồi trượt-trái-sang-phải, lặp qua hàng
    # trăm video, là dấu vân tay quá dễ nhận — nền tảng đọc ra "máy làm" ngay.
    ds_huong = chuyen_dong.rai_huong(ds_kieu, seed=hash(viec) % 99991)

    # THẺ SỐ LIỆU chồng dải y 930–1270 giữa khung (thẻ 940×340 thả tại y=930 — xem bước
    # chồng thẻ phía dưới). Cảnh nào trùng giờ hiện thẻ thì báo render_canh để kiểu
    # "vừa khung" đẩy ảnh lên né (anh dặn 08/08: thẻ che mất hai dòng chữ cuối của đồ hoạ
    # trong khi phía trên khung còn trống).
    the_so_som = _nhap_tram(viec).get("the_so", {})
    co_tyso = any(isinstance(t, dict) and t.get("loai") == "ty_so"
                  for t in the_so_som.values())
    THE_VUNG = (860, 1310) if co_tyso else (930, 1270)   # thẻ tỷ số cao hơn → vùng né rộng hơn
    gio_the = []
    for k_t in the_so_som:
        c_t = int(k_t)
        if c_t < len(cau_moc):
            gio_the.append((cau_moc[c_t - 1] if c_t else 0.0, cau_moc[c_t]))

    clips, kieus, dem_clip = [], [], 0
    for i, ((b, k), anh) in enumerate(zip(canh, xep)):
        out = os.path.join(tmp, f"c{i:02d}.mp4")
        if i in ghep_canh_i:
            # cảnh ĐÔI — mọi tổ hợp ảnh/clip (anh ra luật 09/08 khuya). Cờ lật per nửa:
            # nửa ẢNH theo luật ảnh (sổ bật + không đồ hoạ/chữ), nửa CLIP mặc định LẬT
            tren, duoi = ghep_canh_i[i]
            o_g = o_cua[i] or "c"
            k_lat = str(cau_cua[i]) if o_g == "c" else f"{cau_cua[i]}:{o_g}"
            v_lat = lat_khai.get(k_lat)

            def _lat_ben(ben):
                if "clip" in ben:
                    return v_lat is not False
                return (v_lat is True
                        and not chuyen_dong.la_do_hoa_bang(Image.open(ben["anh"]))
                        and not _anh_co_chu(ben["anh"]))

            def _vua_ben(ben):
                # nửa "vừa khung" = NGƯỜI đặt cách hiện "vua" cho ảnh đó, hoặc máy tự
                # nhận đồ hoạ bảng — hiện TRỌN, không cover cắt mất cột (anh bắt 10/08)
                if "anh" not in ben:
                    return False
                ten_b = os.path.basename(ben["anh"])
                rieng_b = cach_hien.get(ten_b) or cach_hien.get(
                    os.path.basename(ten_goc_chon.get(ten_b, "")))
                if rieng_b:
                    return rieng_b == "vua"
                try:
                    return chuyen_dong.la_do_hoa_bang(Image.open(ben["anh"]))
                except Exception:
                    return False

            lat_2 = (_lat_ben(tren), _lat_ben(duoi))
            vua_2 = (_vua_ben(tren), _vua_ben(duoi))
            if any(vua_2):
                print(f"  cảnh {i + 1}: khung đôi có nửa VỪA KHUNG "
                      f"({'trên' if vua_2[0] else ''}{' dưới' if vua_2[1] else ''})")
            if "anh" in tren and "anh" in duoi:    # hai ảnh: giữ đường PIL cũ (Ken Burns)
                ki = chuyen_dong.render_ghep_doc(tren["anh"], duoi["anh"], out, W, H,
                                                 ANH_CAO, ANH_TOP, k - b, FPS,
                                                 seed=i * 23 + 7, lat=lat_2, vua=vua_2)
            else:
                if i in clip_cua_canh:
                    dem_clip += 1
                print(f"  cảnh {i + 1}: KHUNG ĐÔI hỗn hợp "
                      f"({'▶' if 'clip' in tren else '🖼'}/{'▶' if 'clip' in duoi else '🖼'})")
                ki = chuyen_dong.render_ghep_mix(tren, duoi, out, W, H, ANH_CAO, ANH_TOP,
                                                 k - b, FPS, seed=i * 23 + 7, lat=lat_2,
                                                 vua=vua_2)
        elif i in clip_cua_canh:
            # clip anh tự cắt đoạn trên trạm — dùng ĐÚNG tệp, ĐÚNG mốc đầu anh chọn;
            # soi logo của đúng đoạn đó và né (clip MXH gần như luôn dính logo góc)
            cc = clip_cua_canh[i]; dem_clip += 1
            # người đã TỰ CHỌN khung né logo trên trạm → tôn trọng tuyệt đối, máy thôi né
            vs_clip = None if cc.get("khung") else _vung_dau_clip(viec, cc)
            if cc.get("khung"):
                print(f"  cảnh {i + 1}: CẮT KHUNG anh chọn {cc['khung']}")
            elif vs_clip:
                print(f"  cảnh {i + 1}: NÉ dấu clip ở {', '.join(vs_clip)}")
            # clip TAY hiện TRỌN khung, thiếu trên dưới nền mờ đắp (anh chốt 09/08 đêm
            # — zoom-fill cũ làm vỡ hình); mặc định LẬT (luật 09/08 khuya); gặp thẻ số
            # liệu thì tự đẩy lên vùng còn lại, khoảng trống trên dưới chia đều
            co_the_c = any(min(k, d_t) - max(b, t_t) > 0.3 for (t_t, d_t) in gio_the)
            ki = chuyen_dong.render_clip(os.path.join(viec, cc["tep"]), out, W, H,
                                         ANH_CAO, ANH_TOP, k - b, FPS,
                                         bat_dau=float(cc["tu"]), seed=i * 31 + 5,
                                         tranh=vs_clip or None, khung=cc.get("khung"),
                                         du_khung=True, lat=_lat_o(i),
                                         ne_the=THE_VUNG if co_the_c else None)
        elif i in vi_tri_clip and clips_kho:
            src = clips_kho[dem_clip % len(clips_kho)]; dem_clip += 1
            ki = chuyen_dong.render_clip(src, out, W, H, ANH_CAO, ANH_TOP, k - b, FPS,
                                         seed=i * 31 + 5)
        else:
            co_the = any(min(k, d_t) - max(b, t_t) > 0.3 for (t_t, d_t) in gio_the)
            # lật trái-phải MẶC ĐỊNH cho ảnh chụp (các kiểu cover) — kiểu "vua"/"doc" là
            # đồ hoạ/bảng, chữ lật ngược là lộ nên không đụng; ảnh chụp có CHỮ TO trong
            # khung (backdrop/banner, tra OCR cổng vào) cũng không lật; vùng né lật theo
            lat = (_lat_o(i) and ds_kieu[i] in ("zoom", "ngang", "dungdoc")
                   and not _anh_co_chu(anh))
            tranh_i = chuyen_dong.lat_vung(ds_tranh[i]) if lat else ds_tranh[i]
            ki = chuyen_dong.render_canh(anh, out, W, H, ANH_CAO, ANH_TOP, k - b, FPS,
                                         kieu=ds_kieu[i], seed=i * 17 + 3,
                                         huong=ds_huong[i], tranh=tranh_i,
                                         ne_the=THE_VUNG if co_the else None, lat=lat)
        clips.append(out); kieus.append(ki)
    TEN_HUONG = {"trai_phai": "→", "phai_trai": "←", "cheo_xuong": "↘", "cheo_len": "↗",
                 "vao": "+", "ra": "−", "duoi_len": "↑"}
    print("  nhịp hình: " + " · ".join(
        f"{i+1}:{'▶' if ds_kieu[i] == 'clip' else ('d' if ds_kieu[i] == 'dungdoc' else ds_kieu[i][0])}"
        f"{TEN_HUONG.get(ds_huong[i], '')}"
        for i in range(len(kieus))) + f"   ({dem_clip}/{len(canh)} cảnh là clip)")
    import collections as _c
    _d = _c.Counter(h for h in ds_huong if h)
    print("  hướng: " + " · ".join(f"{TEN_HUONG.get(h, h)}{n}" for h, n in sorted(_d.items())))

    # đường dẫn TUYỆT ĐỐI: ffmpeg concat giải đường tương đối theo thư mục chứa list.txt,
    # không theo thư mục đang đứng — ghi tương đối là hỏng ngay
    with open(os.path.join(tmp, "list.txt"), "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    ghep = os.path.join(tmp, "ghep.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", os.path.join(tmp, "list.txt"), "-c", "copy", ghep], check=True)

    # ⑥ nhạc nền theo cung cảm xúc — qua cầu dùng chung `chon_nhac.py` (dựng 12/08/2026).
    # TRƯỚC ĐÂY: `cung = kb.get("cung_nhac") or "cang_thang"` — nhưng KHÔNG AI sinh trường
    # `cung_nhac` (kiểm 5/5 blueprint thật đều None), nên MỌI video của kênh đều rơi về
    # đúng một cung với 3 file. Nay module tự dò cảm xúc từ tiêu đề + lời bình, đọc kho
    # 12 nhóm, và có 4 tầng dự phòng nên không bao giờ trả về rỗng.
    kb_nhac = dict(kb, nhom_nhac=ts["nhac_nhom"]) if ts["nhac_nhom"] else kb
    nhac, nhom_nhac, vi_sao_nhac = CN.chon(kb_nhac, viec)
    print(f"  ♪ nhạc {nhom_nhac} — {os.path.basename(nhac)}  ({vi_sao_nhac})")

    final = os.path.join(viec, "video.mp4")
    # -loop 1 cho lớp phủ: biến ảnh tĩnh thành LUỒNG liên tục. Không có nó thì lớp phủ chỉ
    # có đúng một frame, hết frame là hết — và bất kỳ thay đổi thuộc tính nào giữa chừng
    # cũng thổi bay tiêu đề với logo. -t phía dưới cắt đúng độ dài nên loop không tràn.
    # ── THẺ SỐ LIỆU chồng lên cảnh (anh chốt 06/08) ──────────────────────────────────
    # Anh khai trên trạm "câu nào hiện thẻ gì"; ở đây vẽ ra rồi chồng đúng đoạn câu ấy được
    # đọc. Trước đây thẻ viết cứng trong dung_short_v5.py cho mỗi video sân PVF — không dùng
    # lại được cho tin khác.
    nhap_the, loc_the, so_dau_vao = [], "", 4
    the_y = {}                                     # đỉnh từng thẻ sau khi neo đáy
    # Danh sách thẻ SẼ VẼ lọc MỘT lần — vòng vẽ PNG lẫn vòng ghép filter phía dưới cùng
    # đọc từ đây. Trước đây hai vòng lọc riêng: thẻ anh đã BỎ (cờ bo_the — trạm giữ dấu
    # để máy gợi không đè lại) và thẻ rỗng ruột vẫn lọt vòng vẽ → khung viền vàng trống
    # trơn chồng lên ảnh (anh bắt 08/08 ở bài Đình Bắc); mà lọc lệch nhau giữa hai vòng
    # thì filter tham chiếu thẻ không tồn tại, ffmpeg sập.
    the_tho = _nhap_tram(viec).get("the_so", {})
    def _the_co_ruot(t):
        if t.get("loai") == "ty_so":               # thẻ tỷ số: ruột là ty_so + 2 đội
            return bool(str(t.get("ty_so", "")).strip()) and (t.get("trai") or t.get("phai"))
        return any(str(t.get(x, "")).strip() for x in ("nhan", "so", "dong1", "dong2"))

    the_khai = {k: t for k, t in the_tho.items()
                if int(k) < len(cau_moc) and not t.get("bo_the") and _the_co_ruot(t)}
    if the_khai:
        sys.path.insert(0, os.path.join(DD.DRIVE, "cong-cu"))
        try:
            import the_so_lieu as TSL
            for k in sorted(the_khai, key=int):
                i = int(k)
                t = the_khai[k]
                p = os.path.join(tmp, f"the{i:02d}.png")
                if t.get("loai") == "ty_so":       # thẻ TỶ SỐ TRẬN kính mờ (anh đặt 09/08)
                    TSL.lam_the_ty_so(t, p)
                else:
                    TSL.lam_the(t.get("nhan", ""), t.get("so", ""), t.get("donvi", ""),
                                t.get("dong1", ""), t.get("dong2", ""), p)
                # neo ĐÁY mọi thẻ ở y=1300 — thẻ tỷ số cao hơn thẻ thường, neo đỉnh cũ
                # (930) là nó tràn xuống đè khối tiêu đề
                the_y[i] = 1300 - Image.open(p).height
                tu = cau_moc[i - 1] if i else 0.0
                den = cau_moc[i]
                # -loop 1 BẮT BUỘC: ảnh tĩnh không lặp thì chỉ có ĐÚNG MỘT khung hình,
                # overlay hiện một phần nghìn giây rồi tắt — nhìn như thẻ không chạy.
                # Đây đúng là lỗi đã ghi trong sổ với lớp phủ tiêu đề, em lặp lại 06/08.
                nhap_the += ["-loop", "1", "-framerate", str(FPS), "-i", p]
                loc_the += (f"[{so_dau_vao}]format=rgba,"
                            f"fade=t=in:st={tu:.2f}:d=0.35:alpha=1,"
                            f"fade=t=out:st={max(den - 0.35, tu):.2f}:d=0.35:alpha=1[the{i}];")
                so_dau_vao += 1
        except Exception as e:
            print(f"  ⚠️  không dựng được thẻ số liệu: {e}")
            nhap_the, loc_the = [], ""

    # chồng lần lượt từng thẻ lên luồng hình
    nhanh = "[0:v][1:v]overlay=0:0:eof_action=repeat,setsar=1"
    if loc_the:
        nhanh += "[v0];"
        ds = [int(k) for k in sorted(the_khai, key=int) if int(k) < len(cau_moc)]
        for n, i in enumerate(ds):
            tu = cau_moc[i - 1] if i else 0.0
            den = cau_moc[i]
            vao, ra_ = f"[v{n}]", ("[vout]" if n == len(ds) - 1 else f"[v{n+1}]")
            y0 = the_y.get(i, 930)
            nhanh += (f"{vao}[the{i}]overlay=(W-w)/2:"
                      f"'{y0}+40*(1-min((t-{tu:.2f})/0.35,1))':"
                      f"enable='between(t,{tu:.2f},{den:.2f})'{ra_};")
        nhanh = nhanh.rstrip(";")
    else:
        nhanh += "[vout]"

    # ── ÂM THANH: vào/ra êm cho CẢ giọng lẫn nhạc (anh đặt 12/08) ──────────────
    # afade với d=0 là lỗi ffmpeg, nên núm để 0 thì BỎ HẲN bộ lọc chứ không truyền 0.
    # Giọng có adelay 120ms ở đầu → fade vào bắt đầu sau chỗ đó mới không cắt mất tiếng.
    def _fade(vao, ra, dai, tre=0.0):
        z = ""
        if vao > 0:
            z += f",afade=t=in:st={tre:.2f}:d={vao}"
        if ra > 0:
            z += f",afade=t=out:st={max(dai - ra, 0):.2f}:d={ra}"
        return z

    # NHẠC NGẮN HƠN VIDEO → LẶP cho đủ. Trước đây `atrim=0:tong` cắt đúng độ dài, nhưng
    # nguồn hết ở giây 16 thì phần sau IM TIẾNG mà chẳng ai báo gì — bản nhạc 16 giây anh
    # thêm 20/08 lộ ra chuyện này. `aloop` rẻ hơn nối tệp và không đụng gì tới nhánh cũ:
    # nhạc đã đủ dài thì vòng lặp không bao giờ chạy tới.
    _nhac_giay = 0.0
    try:
        _r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=nw=1:nk=1", nhac],
                            capture_output=True, text=True, timeout=30)
        _nhac_giay = float((_r.stdout or "0").strip() or 0)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    _lap = ""
    if 0 < _nhac_giay < tong:
        _lap = f"aloop=loop=-1:size={int(_nhac_giay * 44100)},"
        print(f"  ♺ nhạc {_nhac_giay:.0f}s ngắn hơn video {tong:.0f}s → lặp cho đủ")

    f_giong = _fade(ts["giong_vao"], ts["giong_ra"], tong, 0.12)
    f_nhac = _fade(ts["nhac_vao"], ts["nhac_ra"], tong)
    fc = (f"{loc_the}{nhanh};"
          f"[2:a]adelay=120|120,volume=1.3,alimiter=limit=0.95{f_giong}[voice];"
          f"[3:a]{_lap}atrim=0:{tong},volume={ts['nhac_am_luong']}{f_nhac}[bgm];"
          f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=0[aout]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", ghep,
                    "-loop", "1", "-framerate", str(FPS), "-i", overlay,
                    "-i", giong, "-i", nhac, *nhap_the, "-filter_complex", fc,
                    "-map", "[vout]", "-map", "[aout]", "-t", f"{tong}",
                    # medium thay slow (anh kêu dựng chậm 08/08): CRF 20 giữ nguyên nên chất
                    # lượng hình gần như y hệt, chỉ tệp nặng hơn chút — đổi lại khâu nén cuối
                    # nhanh gần gấp đôi trên video 60-70 giây.
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final], check=True)
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                                   "-of", "json", final], capture_output=True, text=True).stdout)
    v = [s for s in d["streams"] if s["codec_type"] == "video"][0]
    print(f"  XONG → {final}")
    print(f"  {v['width']}x{v['height']} · {float(d['format']['duration']):.1f}s · "
          f"{int(d['format']['size'])/1e6:.1f} MB · nhạc {nhom_nhac}")
    # Anh chốt 08/08 (lần 2): BỎ quét QC video thành phẩm — mọi cảnh báo dấu nguồn dồn về
    # hộp KIỂM QC TRƯỚC DỰNG trên trạm (dựa trên sổ cổng vào từng tài nguyên), anh pass là
    # dựng thẳng một mạch cho nhanh. Chất lượng giữ bằng: cổng VÀO từng ảnh/clip + máy né
    # vùng dấu nguồn khi render + mắt anh ở hộp kiểm trước chốt.
    return final


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("dùng: xuong.py <thư mục việc>")
    dung(DD.tim_viec(sys.argv[1]))
