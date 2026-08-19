#!/usr/bin/env python3
"""KHO VIDEO CHỦ THỂ dùng chung (anh đặt 10/08): dán link là máy tự tải video về kho
chung, TÁCH CẢNH, gắn nhãn từng đoạn bằng mắt máy — mọi thứ như kho ảnh.

Sổ `so-video.jsonl`: MỖI DÒNG LÀ MỘT ĐOẠN {tep, tu, den, thumb, nhan, chu_the, mo_ta,
nhan_tho, tieu_de (video gốc), nguon_url, giay_phep, da_dung, luc_nhap} — tra theo nhãn
y hệt ảnh, lấy về bài là cắt đoạn thành clip tay của bài.

Dùng:
  --tai <url>            tải từ link (yt-dlp -N 8, ≤1080p, ≤10 phút) rồi tách + nhãn
  --nhap-tep <file> [tựa] nhập video CÓ SẴN trên máy (hồi tố clip tay bài cũ)
  --bo-nhan              bổ nhãn cho các đoạn còn thô (mẻ 15 khung/lượt haiku)
"""
import glob
import yt_tai as YT
import hashlib
import json
import os
import re
import subprocess
import tempfile
import sys
import unicodedata
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD
import nen_tang as NT                                        # noqa: E402

KHOV = os.path.join(DD.KHO_TAI_NGUYEN, "video-chu-the")
SOV = os.path.join(KHOV, "so-video.jsonl")
THUMB = os.path.join(KHOV, "thumb")
NGUONG_CANH = 0.30              # độ nhạy tách cảnh ffmpeg
DOAN_MIN = 1.5                  # đoạn ngắn hơn thì gộp về đoạn trước
DOAN_MAX_SO = 60                # trần đoạn mỗi video (chống video quá vụn)


def _nfc(s):
    return unicodedata.normalize("NFC", s or "")


def _bo_dau(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")


import chuan_ten as CT                                        # noqa: E402
_BO_GOP = CT.BoGopTen()


def _chuan_hoa_ct(ten):
    """KIỂM SOÁT TRÙNG chủ thể — trỏ về module chuan_ten DÙNG CHUNG (10/08 khuya):
    so cả bảng lẫn MỌI TÊN trong sổ (ảnh + video), tự học bảng, từ chặn không gộp."""
    return _BO_GOP.chuan(ten)


def _khu_trung(nh_ds):
    thay, sach = set(), []
    for n in nh_ds:
        n = _nfc(str(n)).strip()
        k = _bo_dau(n)
        if n and k not in thay:
            thay.add(k)
            sach.append(n)
    return sach[:12]


def _doc_so():
    if not os.path.exists(SOV):
        return []
    return [json.loads(l) for l in open(SOV, encoding="utf-8") if l.strip()]


def _ghi_so(so):
    with NT.khoa_ghi(SOV) as khoa:
        with open(SOV, "w", encoding="utf-8") as f:
            for d in so:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")


def _tach_canh(tep):
    """Mốc đổi cảnh bằng ffmpeg scene-detect → [(từ, đến)] đã lọc đoạn vụn."""
    p = os.path.join(KHOV, tep)
    dai = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of", "csv=p=0", p],
                               capture_output=True, text=True).stdout.strip() or 0)
    r = subprocess.run(["ffmpeg", "-i", p, "-vf",
                        f"select='gt(scene,{NGUONG_CANH})',metadata=print",
                        "-an", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=1800)
    moc = sorted({round(float(m), 2) for m in
                  re.findall(r"pts_time:([\d.]+)", r.stderr or "")})
    diem = [0.0] + [m for m in moc if 0.5 < m < dai - 0.5] + [dai]
    ra = []
    for a, b in zip(diem, diem[1:]):
        if b - a < DOAN_MIN and ra:
            ra[-1] = (ra[-1][0], b)                # đoạn vụn gộp về đoạn trước
        else:
            ra.append((a, b))
    return ra[:DOAN_MAX_SO], dai


def _nhan_may(ds_moi):
    """MỘT lượt haiku cho mẻ khung đại diện — như kho ảnh (prompt CHI TIẾT)."""
    if not ds_moi:
        return {}
    dong = "\n".join(f"- {d['thumb_p']} — gợi ý ngữ cảnh: {d['moi'][:150]}"
                     for d in ds_moi)
    lenh = (
        "Em là mắt máy gắn nhãn KHUNG HÌNH cắt từ video bóng đá, tả THẬT CHI TIẾT. "
        "Với TỪNG ảnh dưới đây: dùng tool Read mở ảnh, đối chiếu gợi ý (có thể sai — "
        "tin MẮT trước).\n"
        f"{dong}\n\n"
        "Trả về DUY NHẤT một khối JSON, khoá là TÊN TỆP (basename), giá trị:\n"
        '{"nhan": [6-12 nhãn TIẾNG VIỆT: HÀNH ĐỘNG cụ thể (dẫn bóng, đánh đầu, sút, '
        "xoạc bóng, ăn mừng, phát biểu…), đội + màu áo + SỐ ÁO đọc được, bối cảnh, "
        'chữ/logo to trong hình, cảm xúc], '
        '"mo_ta": "MỘT câu giàu chi tiết tả khung hình", '
        '"chu_the": "tên người/đội CHÍNH — CHỈ khi chắc chắn, không thì rỗng", '
        '"phu_giua": true|false}\n'
        "KHÔNG chắc tên thì chu_the RỖNG — cấm đoán bừa.\n"
        'Khoá "phu_giua": có CHỮ hoặc LOGO do người làm video CHÈN ĐÈ lên vùng GIỮA '
        "hình không (caption, dòng tiêu đề, tên kênh, khung tỉ số) — thứ nằm ở giữa "
        "thì cắt mép không bỏ được, kho không nhận. Chữ/biển có SẴN TRONG CẢNH THẬT "
        "(bảng quảng cáo sân, áo đấu, biển hiệu) thì phu_giua = false. Chữ nằm sát "
        "RÌA khung cũng false — rìa đã có phép cắt mép lo."
    )
    try:
        r = subprocess.run([NT.tim_claude(), "-p",
                            "--model", os.environ.get("KHO_MODEL",
                                                      "claude-haiku-4-5-20251001"),
                            "--allowedTools", "Read"],
                           input=lenh, capture_output=True, text=True, timeout=900)
        m = re.search(r"\{.*\}", r.stdout, re.S)
        return json.loads(m.group(0)) if m else {}
    except Exception as e:
        print(f"  ⚠ mắt máy nghẽn ({e}) — nhãn thô, chạy --bo-nhan sau")
        return {}


def _md5_tep(p):
    """md5 cả tệp, đọc theo khối 1MB — file 113MB mất chưa tới nửa giây."""
    h = hashlib.md5()
    with open(p, "rb") as f:
        for khoi in iter(lambda: f.read(1 << 20), b""):
            h.update(khoi)
    return h.hexdigest()


def _nhap_tep_video(p_nguon, tieu_de="", url="", loai="goc", nguon_doan="",
                    khung_da_cat=None, goc_kho=""):
    os.makedirs(THUMB, exist_ok=True)
    # chống nhập TRÙNG lớp 1 (10/08): cùng đường gốc hoặc cùng cỡ tệp là bỏ qua — RẺ
    co = os.path.getsize(p_nguon)
    so_cu = _doc_so()
    for m in so_cu:
        if m.get("nguon_tep") == p_nguon or m.get("co_goc") == co:
            print(f"BỎ QUA — video này đã trong kho ({m.get('tep')})")
            return 0
    # lớp 2 — CỔNG MD5 NỘI DUNG (anh duyệt 11/08 sau vụ v01≡v09): hai đường nhập khác
    # nhau (tải link · hồi tố bài cũ) làm nguon_tep lẫn co_goc đều khác dù nội dung trùng
    # TỪNG BYTE — một video highlight vào kho hai lần, đẻ 25 đoạn trùng. Nay so md5 file
    # nguồn với MỌI file đã trong kho, đặt TRƯỚC khâu tách cảnh + nhãn mắt máy (đắt).
    # md5 file kho ghi vào sổ (md5_kho) — lần sau đọc sổ, khỏi tính lại; bản cũ thiếu
    # trường thì tính bù đúng một lần.
    md5_moi = _md5_tep(p_nguon)
    md5_kho = {m["tep"]: m["md5_kho"] for m in so_cu if m.get("md5_kho")}
    tinh_bu = False
    for f in glob.glob(os.path.join(KHOV, "v*.mp4")):
        tep_f = os.path.basename(f)
        if tep_f not in md5_kho:
            md5_kho[tep_f] = _md5_tep(f)
            tinh_bu = True
    if tinh_bu:
        for m in so_cu:
            if m.get("tep") in md5_kho:
                m["md5_kho"] = md5_kho[m["tep"]]
        _ghi_so(so_cu)
    tep_trung = next((t for t, h in md5_kho.items() if h == md5_moi), None)
    if tep_trung:
        # "đã có rồi" là kết quả THÀNH CÔNG, không phải lỗi (bài học 11/08)
        print(f"BỎ QUA — nội dung TRÙNG TỪNG BYTE với {tep_trung} đã trong kho")
        return 0
    n = 1 + max([int(m.group(1)) for f in glob.glob(os.path.join(KHOV, "v*.mp4"))
                 if (m := re.match(r"v(\d+)\.mp4$", os.path.basename(f)))], default=0)
    tep = f"v{n:02d}.mp4"
    subprocess.run(["cp", "-c", p_nguon, os.path.join(KHOV, tep)], check=False)
    if not os.path.exists(os.path.join(KHOV, tep)):
        import shutil
        shutil.copy2(p_nguon, os.path.join(KHOV, tep))
    # KHÔNG TÁCH CẢNH NỮA (anh đổi 11/08: "cắt 1 video mà kho hiện hàng chục đoạn" —
    # scene-detect băm mỗi video thành 13–26 dòng làm kho rối tung). Nay MỖI VIDEO VÀO
    # KHO = MỘT DÒNG: loai="goc" (tải link/video dài) hay "cat" (clip tay đã cắt từ
    # bài). Nhãn mắt máy vẫn GIÀU: nhìn 3 khung đầu–giữa–cuối rồi gộp về một dòng.
    dai = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of", "csv=p=0",
                                os.path.join(KHOV, tep)],
                               capture_output=True, text=True).stdout.strip() or 0)
    print(f"{tep}: {dai:.0f}s → 1 dòng ({loai})")
    ds_moi = []
    # video ngắn (đoạn cắt 4–5s) chỉ cần 1 khung giữa; dài mới cần 3 khung
    cac_moc = [0.5] if dai < 12 else [0.1, 0.5, 0.9]
    for i, ty in enumerate(cac_moc):
        th = f"{tep[:-4]}_{i:02d}.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-ss", f"{dai * ty:.2f}",
                        "-i", os.path.join(KHOV, tep), "-frames:v", "1",
                        "-vf", "scale=640:-2", os.path.join(THUMB, th)], timeout=60)
        ds_moi.append({"tep": tep, "thumb": th,
                       "thumb_p": os.path.join(THUMB, th), "moi": tieu_de})
    nhan = _nhan_may(ds_moi)
    luc = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # GỘP nhãn 3 khung về MỘT dòng: nhãn cộng dồn, mô tả + chủ thể lấy khung GIỮA
    # (khung giữa là mặt video), khung giữa thiếu thì lấy khung nào có
    gom_nhan, mo_ta, chu_the = [], "", ""
    th_giua = ds_moi[len(ds_moi) // 2]["thumb"]
    for d in ds_moi:
        nh = nhan.get(d["thumb"]) or {}
        gom_nhan += nh.get("nhan") or []
        if nh.get("mo_ta") and (not mo_ta or d["thumb"] == th_giua):
            mo_ta = nh["mo_ta"]
        if nh.get("chu_the") and (not chu_the or d["thumb"] == th_giua):
            chu_the = nh["chu_the"]
    co_nhan = any(nhan.get(d["thumb"]) for d in ds_moi)
    # ── CỔNG WATERMARK GIỮA KHUNG (anh duyệt 14/08) ──────────────────────────
    # Luật anh chốt cho ẢNH từ 10/08: "watermark ở RÌA thì cắt mép; GIỮA KHUNG thì
    # KHÔNG nhập — thà thiếu hơn bẩn". Video tới nay mới có cổng tương ứng.
    # Mắt máy trả lời trong CHÍNH lượt gắn nhãn nên không tốn thêm token.
    # (Đã thử hai cách thuần code trước khi đến đây: mắt tĩnh so pixel BÁO OAN 2/5 —
    #  giàn thép trắng trong cảnh drone bị chấm 5,35%; OCR tesseract đọc được ảnh
    #  sạch nhưng mù trước chữ trắng trên nền đỏ của caption video. Ghi lại để sau
    #  đừng ai làm lại hai đường ấy.)
    if loai == "cat" and any((nhan.get(d["thumb"]) or {}).get("phu_giua")
                             for d in ds_moi):
        try:
            os.remove(os.path.join(KHOV, tep))
            for d in ds_moi:
                th_p = os.path.join(THUMB, d["thumb"])
                os.path.exists(th_p) and os.remove(th_p)
        except OSError:
            pass
        print(f"🚫 KHÔNG NHẬP {tep} — mắt máy thấy CHỮ/LOGO CHÈN GIỮA HÌNH "
              f"(cắt mép không bỏ được). Muốn dùng thì cắt lại đoạn khác.")
        return 0
    so = _doc_so()
    so.append({
        "tep": tep, "tu": 0.0, "den": round(dai, 2), "thumb": th_giua,
        "loai": loai,                           # "goc" | "cat" — nhãn phân biệt trên UI
        "nhan": _khu_trung((gom_nhan or [tieu_de])
                           + ([luc[:4]] if luc[:4].startswith("20") else []))[:12],
        "chu_the": _chuan_hoa_ct(_nfc(chu_the)),
        "mo_ta": _nfc(mo_ta), "nhan_tho": not co_nhan,
        "tieu_de": _nfc(tieu_de), "nguon_url": url,
        "nguon_tep": p_nguon, "co_goc": co, "md5_kho": md5_moi,
        # dấu ĐOẠN GỐC: "<tệp gốc>#<từ>-<đến>" — cắt lại cùng một đoạn ra file khác byte
        # nên md5 không bắt được, phải có dấu riêng mới chống nhập trùng (14/08)
        **({"nguon_doan": nguon_doan} if nguon_doan else {}),
        # ĐƯỜNG LÙI khi anh khoanh khung hụt (anh duyệt 14/08): bản trong kho đã CẮT
        # CỨNG nên không mở rộng lại được — nhưng nhớ khung đã cắt + video gốc nằm đâu
        # thì còn quay về cắt lại, khỏi đi tìm nguồn từ đầu. Không tốn dung lượng:
        # video gốc vốn đã nằm sẵn trong kho.
        **({"khung_da_cat": khung_da_cat} if khung_da_cat else {}),
        **({"goc_kho": goc_kho} if goc_kho else {}),
        "giay_phep": "video mạng xã hội — dùng dạng trích dẫn tin tức",
        "da_dung": [], "luc_nhap": luc})
    _ghi_so(so)
    print(f"+1 dòng {loai} vào kho video ({'có' if co_nhan else 'CHƯA'} nhãn mắt máy)")
    return 1


def tim_youtube(tu_khoa, so=3, toi_da_giay=600):
    """Tìm video YouTube hợp từ khoá, trả [{url, tieu_de, giay}] — CHƯA tải.

    Anh chốt 14/08: chỉ lấy video DƯỚI 10 PHÚT cho đỡ nặng, và một video phải dùng
    được cho NHIỀU CẢNH khi dựng — nên ưu tiên video có nhiều pha khác nhau (bản tin,
    tổng hợp, phóng sự) chứ không phải clip một pha 15 giây.
    """
    r = subprocess.run(
        ["yt-dlp", "--no-warnings", "--flat-playlist", "--skip-download",
         "--print", "%(id)s\t%(title)s\t%(duration)s",
         f"ytsearch{so * 3}:{tu_khoa}"],
        capture_output=True, text=True, timeout=180)
    ra = []
    for dong in (r.stdout or "").splitlines():
        ph = dong.split("\t")
        if len(ph) < 3:
            continue
        try:
            gy = int(float(ph[2]))
        except ValueError:
            continue
        if not (20 <= gy <= toi_da_giay):        # quá ngắn thì không đủ nhiều cảnh
            continue
        ra.append({"url": f"https://www.youtube.com/watch?v={ph[0]}",
                   "tieu_de": ph[1][:120], "giay": gy})
        if len(ra) >= so:
            break
    return ra


def ban_do_moc(tep_kho, so_moc=14):
    """MỘT video → BẢN ĐỒ NHIỀU MỐC, để dựng lấy được nhiều đoạn từ cùng một tệp.

    Anh nói rõ 14/08: "ý a muốn là kiểu video tải 1 lần dùng được cho nhiều cảnh khi
    dựng ấy". Nên thay vì soi cả video như một khối, chia thành ~14 khoảng đều nhau,
    mắt máy nhìn MỘT khung mỗi khoảng rồi tả xem khoảng đó có gì. Dựng chỉ việc tra
    bản đồ: cảnh nói về ăn mừng thì lấy khoảng có ăn mừng.

    Trả tiền MỘT LẦN cho mỗi video: bản đồ ghi thẳng vào sổ kho (trường `moc`), lần
    sau dùng lại là đọc sổ — đúng luật "quét một lần, lưu dạng wiki".
    """
    so = _doc_so()
    dong = next((d for d in so if d.get("tep") == tep_kho), None)
    if dong is None:
        return []
    if dong.get("moc"):
        return dong["moc"]                       # đã soi rồi, đừng trả tiền lần hai
    p_v = os.path.join(KHOV, tep_kho)
    dai = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", p_v], capture_output=True, text=True).stdout.strip() or 0)
    if dai < 8:
        return []
    n = max(3, min(so_moc, int(dai // 6)))       # đừng chia nhỏ hơn 6 giây một khoảng
    buoc = dai / n
    os.makedirs(THUMB, exist_ok=True)
    ds_moi, moc = [], []
    for i in range(n):
        tu, den = i * buoc, (i + 1) * buoc
        th = f"{tep_kho[:-4]}_m{i:02d}.jpg"
        subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-ss", f"{tu + buoc / 2:.2f}",
                        "-i", p_v, "-frames:v", "1", "-vf", "scale=640:-2",
                        os.path.join(THUMB, th)], timeout=60)
        if not os.path.exists(os.path.join(THUMB, th)):
            continue
        ds_moi.append({"tep": tep_kho, "thumb": th,
                       "thumb_p": os.path.join(THUMB, th),
                       "moi": dong.get("tieu_de", "")})
        moc.append({"tu": round(tu, 1), "den": round(den, 1), "thumb": th})
    if not moc:
        return []
    nhan = _nhan_may(ds_moi)
    for m in moc:
        nh = nhan.get(m["thumb"]) or {}
        m["nhan"] = _khu_trung(nh.get("nhan") or [])
        m["mo_ta"] = _nfc(nh.get("mo_ta", ""))
        m["chu_the"] = _chuan_hoa_ct(_nfc(nh.get("chu_the", "")))
        m["phu_giua"] = bool(nh.get("phu_giua"))   # mốc dính caption thì dựng đừng lấy
    def _ghi(ds_v):
        for d in ds_v:
            if d.get("tep") == tep_kho:
                d["moc"] = moc
        return ds_v
    _ghi_so(_ghi(_doc_so()))
    sach = len([m for m in moc if not m["phu_giua"]])
    print(f"  🗺  {tep_kho}: bản đồ {len(moc)} mốc ({sach} mốc sạch, dùng cho nhiều cảnh)")
    return moc


def nhap_goc_bai(viec):
    """VIDEO GỐC anh gắp về bài → KHO VIDEO CHUNG (anh chốt 16/08: "mỗi lần làm xong 1
    content có dùng video gốc thì tự đẩy vào kho chung").

    Cùng họ lỗi với đoạn cắt hôm 14/08, chỉ khác tầng: đoạn cắt đã có đường về kho từ
    hôm ấy, còn BẢN GỐC vẫn nằm chết trong `<bài>/clip/tay/`. Rà 16/08: 38 video gốc,
    3,4 GB, chỉ 2 bản có mặt trong kho — công tìm và tải mất trắng với mọi bài sau.

    Bản gốc quý hơn đoạn cắt: từ nó cắt được đoạn KHÁC cho bài khác, còn đoạn đã cắt thì
    chỉ dùng được đúng một khuôn.
    """
    thu = os.path.join(viec, "clip", "tay")
    if not os.path.isdir(thu):
        return 0
    kb = {}
    try:
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    except Exception:
        pass
    them = 0
    for p_g in sorted(glob.glob(os.path.join(thu, "tay_*.mp4"))):
        #   · `kho__v*.mp4` là bản KÉO TỪ KHO về bài — nhập lại là quay vòng (glob trên
        #     đã loại sẵn vì chúng không mang tiền tố `tay_`)
        #   · dưới 1,2 MB là mảnh tải hỏng, không phải video
        try:
            if os.path.getsize(p_g) < 1_200_000:
                continue
        except OSError:
            continue
        them += _nhap_tep_video(p_g, tieu_de=kb.get("tieu_de", "")[:70], loai="goc",
                                nguon_doan=f"video gốc của bài {os.path.basename(viec)}")
    print(f"— {them} video GỐC mới vào kho video")
    return them


def nhap_doan_bai(viec):
    """ĐOẠN ANH CẮT TRONG BÀI → KHO VIDEO CHUNG (anh bắt 14/08: "video được cắt rồi để
    ghép vào video thì phải cho hiện ở kho-nha-duyet, mấy video cắt gần đây a ko thấy").

    Trước nay `nhap_kho_video.py` chỉ chạy hai đường: anh dán link tải mới, và bổ nhãn.
    Đoạn anh tự tay tua-cắt-gán vào cảnh thì KHÔNG có đường nào về kho — trong khi ảnh
    của bài thì có (xếp kho gọi `nhap_kho_chu_the.py`). Đúng họ lỗi "cảnh chính có gì
    cảnh phụ có nấy": một nửa tài nguyên có đường về kho, nửa kia không.

    Đoạn đã trả giá (tìm video · tua · canh mốc · né logo) phải sống tiếp cho bài sau.
    """
    nh = {}
    p_tram = os.path.join(viec, "anh", "tram.json")
    if os.path.exists(p_tram):
        try:
            nh = json.load(open(p_tram, encoding="utf-8"))
        except Exception:
            nh = {}
    # KHUNG NÉ LOGO đi cùng đoạn (anh bắt 14/08: "cắt có chọn khung bỏ watermark rồi mà
    # kho vẫn hiện nguyên khung có watermark"). Anh đã bỏ công khoanh khung trên trạm —
    # bản vào kho phải là bản SẠCH, không thì lần sau tái dùng lại dính logo y như cũ,
    # đúng luật "kho CHỈ chứa tài nguyên sạch watermark" anh chốt cho ảnh từ 10/08.
    doan = []                            # [(tệp tương đối, từ, đến, khung|None)]
    p_cc = os.path.join(viec, "anh", "clip-canh.json")
    if os.path.exists(p_cc):
        try:
            for v in json.load(open(p_cc, encoding="utf-8")).values():
                doan.append((v["tep"], float(v["tu"]), float(v["den"]), v.get("khung")))
        except Exception:
            pass
    for ds in (nh.get("anh_phu") or {}).values():   # ô PHỤ cũng gán được clip
        for x in (ds or []):
            if isinstance(x, str) and x.startswith("clip::"):
                ph = x.split("::")
                if len(ph) >= 4:
                    kh = None
                    if len(ph) > 4 and ph[4]:       # đuôi "x,y,w,h" theo TỶ LỆ 0–1
                        try:
                            xk, yk, wk, hk = (float(t) for t in ph[4].split(","))
                            kh = {"x": xk, "y": yk, "w": wk, "h": hk}
                        except ValueError:
                            kh = None
                    doan.append((ph[1], float(ph[2]), float(ph[3]), kh))
    n_goc = nhap_goc_bai(viec)         # bản GỐC trước, đoạn cắt sau
    if not doan:
        print("bài này không có đoạn clip nào")
        return n_goc
    kb = {}
    try:
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    except Exception:
        pass
    da_co = {m.get("nguon_doan") for m in _doc_so() if m.get("nguon_doan")}
    them = 0
    for tep_rel, tu, den, khung in doan:
        goc = os.path.join(viec, tep_rel)
        if not os.path.exists(goc) or den - tu < 0.5:
            continue
        # dấu chống trùng gồm CẢ KHUNG: cùng đoạn nhưng khung khác là bản khác hẳn
        k_dau = (f"@{khung['x']:.3f},{khung['y']:.3f},{khung['w']:.3f},{khung['h']:.3f}"
                 if khung else "")
        dau = f"{os.path.basename(tep_rel)}#{tu:.1f}-{den:.1f}{k_dau}"
        if dau in da_co:
            print(f"BỎ QUA — đoạn {dau} đã trong kho")
            continue
        with tempfile.TemporaryDirectory() as tam:
            ra = os.path.join(tam, f"doan_{int(tu)}_{int(den)}.mp4")
            loc = []
            if khung:
                # crop theo TỶ LỆ khung anh khoanh; ép số chẵn cho libx264 khỏi kêu
                loc = ["-vf", (f"crop=trunc(iw*{khung['w']:.6f}/2)*2:"
                               f"trunc(ih*{khung['h']:.6f}/2)*2:"
                               f"trunc(iw*{khung['x']:.6f}/2)*2:"
                               f"trunc(ih*{khung['y']:.6f}/2)*2")]
            r = subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-ss", f"{tu:.2f}", "-i", goc,
                 "-t", f"{den - tu:.2f}"] + loc + ["-c:v", "libx264", "-preset",
                 "veryfast", "-crf", "20", "-an", ra], capture_output=True, timeout=300)
            if r.returncode or not os.path.exists(ra):
                print(f"⚠ cắt hỏng {dau}: {(r.stderr or b'')[-160:].decode(errors='ignore')}")
                continue
            # nguồn tên "kho__vNN.mp4" = đoạn cắt từ video ĐÃ trong kho → nhớ tên gốc
            ten_g = os.path.basename(tep_rel)
            g_kho = ten_g[5:] if ten_g.startswith("kho__") else ""
            them += _nhap_tep_video(ra, tieu_de=kb.get("tieu_de", "")[:70],
                                    loai="cat", nguon_doan=dau,
                                    khung_da_cat=khung, goc_kho=g_kho)
        da_co.add(dau)
    print(f"— {them} đoạn mới vào kho video (trong {len(doan)} đoạn của bài)")
    return them + n_goc


def tai(url):
    os.makedirs(KHOV, exist_ok=True)
    co = open(os.path.join(KHOV, ".dang-tai"), "w")
    co.write(url)
    co.close()
    try:
        tieu_de = subprocess.run(["yt-dlp", "--no-warnings", "--skip-download",
                                  "--print", "title", "--playlist-items", "1", url],
                                 capture_output=True, text=True,
                                 timeout=120).stdout.strip()[:120]
        tam = os.path.join(KHOV, "_tai.%(ext)s")
        # Cùng luật với trạm (yt_tai.py) — trượt thì ĐỔI CỬA hỏi YouTube rồi thử lại.
        # Khai luật ở MỘT chỗ để hai bên không lệch nhau: 19/08 trạm tải hỏng vì yt-dlp
        # cũ, mà bên này cũng sẽ hỏng y hệt nếu chỉ vá một bên.
        lenh = ["yt-dlp", "--no-update", "--no-warnings", "--no-playlist",
                "-N", "8", "--playlist-items", "1",
                "--match-filter", "duration<=?600",
                "-f", YT.FORMAT, "--merge-output-format", "mp4",
                "-o", tam, url]
        p = os.path.join(KHOV, "_tai.mp4")
        tho = ""
        for i_cua in range(len(YT.CUA)):
            r = subprocess.run(YT.them_cua(lenh, i_cua),
                               capture_output=True, text=True, timeout=1800)
            if os.path.exists(p) and os.path.getsize(p) >= 50000:
                break
            tho = (r.stderr or "").strip()
            if not YT.dang_thu_lai(tho):
                break
        if not os.path.exists(p) or os.path.getsize(p) < 50000:
            print("TẢI HỎNG:", YT.doi_loi(tho))
            return 0
        so = _nhap_tep_video(p, tieu_de, url)
        os.remove(p)
        return so
    finally:
        try:
            os.remove(os.path.join(KHOV, ".dang-tai"))
        except OSError:
            pass


def bo_nhan(me=15):
    can = [d for d in _doc_so() if d.get("nhan_tho")]
    if not can:
        print("không còn đoạn nhãn thô")
        return
    for i in range(0, len(can), me):
        cum = can[i:i + me]
        ds = [{"thumb": d["thumb"], "thumb_p": os.path.join(THUMB, d["thumb"]),
               "moi": d.get("tieu_de", "")} for d in cum]
        nhan = _nhan_may(ds)
        so = _doc_so()
        for m in so:
            n = nhan.get(m.get("thumb"))
            if not n or m.get("nguoi_sua") or not m.get("nhan_tho"):
                continue
            m["nhan"] = _khu_trung(n.get("nhan") or [])
            m["chu_the"] = _chuan_hoa_ct(_nfc(n.get("chu_the", "")))
            m["mo_ta"] = _nfc(n.get("mo_ta", ""))
            m["nhan_tho"] = False
        _ghi_so(so)
        print(f"  mẻ {i // me + 1}: xong", flush=True)


if __name__ == "__main__":
    if "--tai" in sys.argv:
        tai(sys.argv[sys.argv.index("--tai") + 1])
    elif "--nhap-tep" in sys.argv:
        i = sys.argv.index("--nhap-tep")
        # hồi tố clip tay của bài = đoạn ĐÃ CẮT → dòng "cat" (video tải link mới là "goc")
        _nhap_tep_video(sys.argv[i + 1],
                        sys.argv[i + 2] if len(sys.argv) > i + 2 else "", loai="cat")
    elif "--goc-bai" in sys.argv:
        nhap_goc_bai(DD.tim_viec(sys.argv[sys.argv.index("--goc-bai") + 1]))
    elif "--doan-bai" in sys.argv:
        nhap_doan_bai(DD.tim_viec(sys.argv[sys.argv.index("--doan-bai") + 1]))
        sys.exit(0)
    if "--bo-nhan" in sys.argv:
        bo_nhan()
