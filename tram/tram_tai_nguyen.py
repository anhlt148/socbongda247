#!/usr/bin/env python3
"""TRẠM DUYỆT TÀI NGUYÊN — cửa người số 2 của kênh Sóc Bóng Đá 247.

Việc của trạm: bày lời bình ra TỪNG CÂU theo đúng thứ tự kể, mỗi câu một ô ảnh, để anh
quyết định ảnh nào vào câu nào. Xong bấm DUYỆT, trạm tự sinh đủ thứ cho xưởng dựng.

Vì sao có trạm này (sổ dự án 04/08):
  · Trước đó việc chọn ảnh làm bằng cách SỬA TAY danh sách trong `chon_anh.py` — muốn đổi
    một tấm phải mở mã nguồn. Không phải cách để chạy 3–5 video mỗi ngày.
  · "Ảnh phải neo theo CÂU, không theo CẢNH": cảnh cắt theo nhịp 3-4 giây, lời chạy theo câu,
    hai thứ lệch nhau ngay từ cảnh hai (video Việt Anh: 26 câu / 16 cảnh / 14 ảnh). Xưởng đã
    đọc `anh/ban-do-cau.json`, nhưng chưa có chỗ nào để NGƯỜI làm ra cái bản đồ ấy. Đây là chỗ đó.
  · Ảnh gom tự động phần lớn là NGƯỜI KHÁC (số 18 áo trắng là Hai Long, không phải Việt Anh).
    Máy không soi được số áo — nên khâu này là khâu của người, và trạm phải bày cho dễ soi.

Ba thứ trạm sinh ra khi anh bấm DUYỆT:
  ① `anh/chon/NN.jpg`         — ảnh đã chọn, đánh số theo mạch kể (xưởng đọc)
  ② `anh/ban-do-cau.json`     — {chỉ số câu → tên ảnh}, câu chưa khai thì kế thừa câu trước
  ③ `anh/so-nguon.jsonl`      — sổ nguồn đúng khuôn cổng QC ra đang đọc (`qc_cong_chan.py`)
  ④ `anh/blueprint.json`      — 8 trường y hệt hệ cũ, để sau muốn ghép hai hệ thì ghép được

Chạy:  python3 tram_tai_nguyen.py [--cong 8756]
       → http://localhost:8756/
"""
import argparse
import base64
import glob
import hashlib
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PIL import Image


# đường đầy đủ trước, tên trần sau: script có thể chạy ngoài trạm (cron, launchd
# một-lần) nơi PATH không có ~/.local/bin — gọi tên trần là FileNotFoundError câm
TRAM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(TRAM))
sys.path.insert(0, TRAM)
import duong_dan as DD
import nen_tang as NT                                        # noqa: E402
_CLAUDE = NT.tim_claude()   # MỘT nguồn — nen_tang lo cả macOS lẫn Windows (15/08)
import nhip_canh as NC                                        # noqa: E402 — nhịp DÙNG CHUNG với xưởng
import gap_anh                                                # noqa: E402
import kich_ban as KB_SO                                      # noqa: E402 — cửa ghi kịch bản có khoá
from chuan_ten import slug_hoa                                # noqa: E402 — tên tệp theo nội dung
import dong_ho as DH                                          # noqa: E402 — đo thời gian sản xuất
import lay_anh                                                # noqa: E402 — cổng OCR watermark
import concurrent.futures as cf                               # noqa: E402
import goi_y as GY
import boc_goi_gpt as BG                                       # noqa: E402 — bóc gói từ khoá anh dán                                            # noqa: E402
import loc_anh as LOC                                         # noqa: E402
import cum_vang as CV                                         # noqa: E402 — cụm tô vàng, DÙNG CHUNG với xưởng
import chon_nhac as CN                                        # noqa: E402 — chọn nhạc, DÙNG CHUNG với xưởng
import phong_cach as PC                                       # noqa: E402 — núm vặn chống dập khuôn
import xuong as XU                                            # noqa: E402 — dùng LẠI doc_giong của xưởng để thử giọng

TRANG = os.path.join(TRAM, "tram-tai-nguyen.html")
TRANG_CHON = os.path.join(TRAM, "tram-chon-anh.html")   # trang chọn ảnh riêng (anh chốt 06/08)
HANG_DOI = os.path.join(DD.MAY, "hang_doi.jsonl")             # cùng khuôn với hệ cũ
THU_ANH = ("anh", "anh2")                                     # nơi chứa ảnh ứng viên
# Nhịp đọc THẬT của giọng Ngọc Huyền ở speed 1.1, đo trên 3 video ngày 04/08 (không phải 265
# như ước ban đầu). Cùng con số với `viet_loi_binh.py`. Chỉ dùng khi CHƯA có file giọng —
# có giọng rồi thì đo thẳng bằng ffprobe, chính xác hơn hẳn.
TIENG_MOT_PHUT = 226

# PHIÊN BẢN TRẠM = mốc lúc server KHỞI ĐỘNG. Trang so mốc này định kỳ; lệch nghĩa là
# trạm đã nâng cấp/khởi động lại sau khi tab được mở → chuông đỏ bảo anh tải lại.
# (Sinh từ lớp lỗi 11/08: tab sống lâu chạy JS cũ với sổ mới → chết câm không ai biết.)
PHIEN_BAN_TRAM = int(time.time())

VIEC_JOB = {}                                                 # việc gắp ảnh đang chạy nền
# ĐANG KÉO VỀ KHO — đếm theo việc để trang hiện "⏳ đang kéo 1 video · 5 ảnh" (anh đặt
# 09/08 khuya: kéo lâu không thấy động tĩnh là tưởng lỗi bấm kéo lại lần hai)
DANG_KEO = {}

# ── CÓ BẢN NÂNG CẤP MỚI KHÔNG (anh hỏi 16/08: "làm gì để máy kia biết mà update") ──
# Anh sửa ở máy Mac rồi đẩy lên GitHub; máy phụ không có cách nào biết ngoài việc tự
# nhớ chạy `git pull`. Nhớ được vài hôm rồi quên, làm cả tuần trên bản cũ mà không hay.
#
# Trạm tự hỏi GitHub — nhưng hỏi NGẦM, mỗi 20 phút một lượt trong luồng riêng, vì mỗi
# lượt mất ~1,1 giây đường mạng. Kết quả nằm sẵn trong bộ nhớ, trang đọc tức thì và
# ĐI NHỜ lượt gọi `/api/dang-keo` vốn đã poll 4 giây/lần — không đẻ thêm đường hỏi mới.
BAN_MOI = {"co": False, "sha": "", "dang": "", "so": 0, "luc": "", "loi": ""}
GOC_MA = os.path.dirname(TRAM)


def _git(*doi, cho=25):
    r = subprocess.run(["git", "-C", GOC_MA, *doi], capture_output=True, text=True,
                       timeout=cho)
    return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode


def _do_ban_moi():
    """Một lượt hỏi GitHub. `ls-remote` chỉ đọc con trỏ nhánh — không tải mã về, nhẹ."""
    try:
        dang, _, _ = _git("rev-parse", "HEAD")
        xa, err, ma = _git("ls-remote", "origin", "refs/heads/main")
        if ma or not xa:
            BAN_MOI.update(loi=(err or "không hỏi được GitHub")[:120])
            return
        sha = xa.split()[0]
        co = bool(sha) and sha != dang
        so = 0
        if co:
            # đếm xem lệch bao nhiêu bản — nói "có 3 bản mới" dễ hiểu hơn một mã băm
            dem, _, m2 = _git("rev-list", "--count", f"HEAD..{sha}")
            if m2:                                  # chưa có bản ghi ấy ở máy → fetch nhẹ
                _git("fetch", "--quiet", "origin", "main", cho=60)
                dem, _, m2 = _git("rev-list", "--count", f"HEAD..{sha}")
            so = int(dem) if dem.isdigit() else 0
        BAN_MOI.update(co=co, sha=sha[:7], dang=dang[:7], so=so, loi="",
                       luc=datetime.now().strftime("%H:%M"))
    except Exception as e:
        BAN_MOI.update(loi=str(e)[:120])


def _canh_ban_moi():
    while True:
        _do_ban_moi()
        time.sleep(1200)                            # 20 phút một lượt


threading.Thread(target=_canh_ban_moi, daemon=True).start()


def _keo(ma, loai, so):
    """Đếm việc đang kéo, VÀ đếm luỹ kế số lượt đã xong.

    Vì sao cần `xong` (anh báo 16/08 "ảnh 2·3·4 phải bấm tải lại trang mới thấy"):
    trang poll 4 giây một lần để biết lúc nào kéo xong mà nạp lại kho. Kéo một tấm ảnh
    chỉ mất chưa tới một giây — poll TRƯỢT HOÀN TOÀN cửa sổ ấy, trang không bao giờ
    biết có ảnh mới. Video tải lâu nên bắt được; ảnh nhanh nên trượt. Đúng cái "lúc
    được lúc không".

    Số đang-kéo là ẢNH CHỤP TỨC THỜI — ai cũng có thể nhìn trượt. Số luỹ kế thì KHÔNG
    trượt được: trang chỉ cần so với lần trước, thấy tăng là biết có hàng mới.
    """
    with KHOA:
        d = DANG_KEO.setdefault(ma, {"video": 0, "anh": 0, "xong": 0})
        d[loai] = max(0, d[loai] + so)
        if so < 0:
            d["xong"] = d.get("xong", 0) + (-so)


# ── KHO CHỦ THỂ dùng chung (anh chốt 10/08) ──────────────────────────────────
KHO_CHU_THE = os.path.join(DD.KHO_TAI_NGUYEN, "anh-chu-the")
SO_CHU_THE = os.path.join(KHO_CHU_THE, "so-chu-the.jsonl")
KHO_VIDEO_CT = os.path.join(DD.KHO_TAI_NGUYEN, "video-chu-the")
SO_VIDEO_CT = os.path.join(KHO_VIDEO_CT, "so-video.jsonl")


def _so_video_ct(sua=None):
    """Đọc/ghi sổ kho video (khoá file — script nhập cũng ghi song song)."""
    os.makedirs(KHO_VIDEO_CT, exist_ok=True)
    with NT.khoa_ghi(SO_VIDEO_CT) as khoa:
        ds = []
        if os.path.exists(SO_VIDEO_CT):
            ds = [json.loads(l) for l in open(SO_VIDEO_CT, encoding="utf-8")
                  if l.strip()]
        if sua is None:
            return ds
        ds = sua(ds)
        with open(SO_VIDEO_CT, "w", encoding="utf-8") as f:
            for d in ds:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        return ds


def _bo_dau_k(s):
    import unicodedata as _u
    s = _u.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if _u.category(c) != "Mn").replace("đ", "d")


def _lev1(a, b):
    """Khoảng cách soạn thảo ≤1? (chịu gõ sai/thiếu MỘT ký tự — 'dinh bak' vẫn ra)"""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = j = khac = 0
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1
            j += 1
            continue
        khac += 1
        if khac > 1:
            return False
        if la == lb:
            i += 1
        j += 1
    return True


def _mo_rong_q(q):
    """Mở rộng truy vấn qua BẢNG TÊN CHUẨN: gõ biến thể ('việt nam', 'hlv kim') thì
    tự hiểu là tên chuẩn ('Tuyển Việt Nam', 'Kim Sang-sik')."""
    _BO_GOP._nap_bang()                             # cache theo mtime — gọi dày vẫn rẻ
    k = _bo_dau_k(q).strip()
    chuan = _BO_GOP._tra.get(k)
    return _bo_dau_k(chuan) if chuan else k


def _diem_khop(q, cac_truong):
    """BỘ TÌM THÔNG MINH dùng chung (anh đặt 10/08): bỏ dấu, khớp THEO TỪ (đủ mọi từ,
    không cần thứ tự), chịu gõ sai 1 ký tự, hiểu biến thể tên; điểm cao khi khớp ở
    trường quan trọng (chu_the > nhan > mo_ta). Trả 0 = không khớp.

    cac_truong = [(chuỗi, trọng số), ...]"""
    tu_q = _mo_rong_q(q).split()
    if not tu_q:
        return 1
    tong = 0
    for t in tu_q:
        tot = 0
        for chuoi, trong in cac_truong:
            for w in _bo_dau_k(chuoi).split():
                if w == t:
                    diem = 3
                elif t in w or w.startswith(t):
                    diem = 2
                elif len(t) >= 3 and len(w) >= 3 and _lev1(t, w):
                    diem = 1
                else:
                    continue
                tot = max(tot, diem * trong)
        if tot == 0:
            return 0                               # một từ trượt là trượt cả câu
        tong += tot
    return tong


_HIEM = {"mt": 0, "w": {}}


def _do_hiem():
    """TỪ CÀNG PHỔ BIẾN TRONG KHO CÀNG ÍT ĐÁNG GIÁ (anh hỏi 12/08: "đề xuất nhiều ảnh
    nhưng chưa sát nội dung").

    Chẩn trên kho thật 873 ảnh: nhãn "2026" đeo lên 798 tấm, "asean cup 2026" 369 tấm,
    "sân vận động" 107 tấm. Bộ chấm cũ cho mọi từ trọng số như nhau, nên câu nào cũng
    khớp mấy nhãn ấy → gần như CẢ KHO đều "hợp bài" ngang nhau, tấm đúng người đúng
    việc chìm lẫn giữa 800 tấm chung chung.

    Cách chữa rẻ nhất (0 token, chạy tức thì): chấm theo ĐỘ HIẾM. Từ có mặt ở 90% kho
    gần như không phân biệt được gì → hệ số ~0,1; tên riêng hiếm như "đình bắc" →
    hệ số ~1. Cache theo mtime sổ nên gọi hàng nghìn lần vẫn rẻ.
    """
    try:
        mt = os.path.getmtime(SO_CHU_THE)
    except OSError:
        return {}
    if _HIEM["mt"] != mt:
        dem, tong = {}, 0
        try:
            for dong in open(SO_CHU_THE, encoding="utf-8"):
                try:
                    m = json.loads(dong)
                except Exception:
                    continue
                tong += 1
                # đếm theo ẢNH, không theo lượt: một tấm nhắc "2026" hai lần vẫn là một
                for t in {w for n in (m.get("nhan") or []) + [m.get("chu_the", "")]
                          for w in _bo_dau_k(n).split()}:
                    dem[t] = dem.get(t, 0) + 1
        except OSError:
            return {}
        # IDF chuẩn log(N/c), chuẩn hoá theo mốc "hiếm = có mặt ở 5 ảnh", kẹp [0,10; 1].
        # Thử công thức căn bậc hai trước, đo ra chênh lệch quá nhạt (2026 vẫn 0,51 dù
        # đeo 91% kho) — log mới tách bạch: 2026 → 0,10 · đình bắc → 0,40 · tên hiếm → 0,87
        import math as _mt
        chuan = _mt.log(max(tong / 5, 2.0))
        _HIEM.update(mt=mt, w={t: max(0.10, min(1.0, _mt.log(max(tong / c, 1.01)) / chuan))
                               for t, c in dem.items()} if tong else {})
    return _HIEM["w"]


def _diem_mem(tu_q, cac_truong):
    """Như _diem_khop nhưng KHÔNG bắt trúng đủ mọi từ — trượt một từ vẫn được tính
    phần còn lại (anh đặt 11/08: bày CẢ KHO theo mức liên quan, đừng lọc sạch trơn).
    Nhận sẵn danh sách từ đã bỏ dấu để gọi hàng nghìn lần vẫn rẻ.

    Từ 12/08 nhân thêm HỆ SỐ HIẾM: khớp "đình bắc" đáng hơn khớp "2026" nhiều lần."""
    hiem = _do_hiem()
    tong, trung = 0, 0
    for t in tu_q:
        tot = 0
        for chuoi, trong in cac_truong:
            for w in chuoi:
                if w == t:
                    diem = 3
                elif len(t) >= 3 and (t in w or w.startswith(t)):
                    diem = 2
                elif len(t) >= 4 and len(w) >= 4 and _lev1(t, w):
                    diem = 1
                else:
                    continue
                tot = max(tot, diem * trong)
        if tot:
            tong += tot * hiem.get(t, 1.0)     # từ phổ biến khắp kho → gần như không cộng
            trung += 1
    if not tu_q:
        return 0
    # thưởng theo TỶ LỆ từ trúng — tấm trúng 3/4 từ phải trên tấm trúng 1/4 dù điểm thô
    # ngang nhau (khớp sâu một từ hiếm không bằng khớp rộng cả cụm)
    return tong * (1 + trung / len(tu_q))


# Đội tuyển hay lẫn vào nhau trong kho — nhận diện bằng CODE, không cần model.
# Mỗi mục: tên chuẩn → các cách gọi (bỏ dấu) để dò trong lời bài lẫn nhãn ảnh.
_DOI_TUYEN = {
    # Thêm 12/08 các cách gọi TẮT mà mắt máy hay viết ("tuyển Thái", "u23 Thái"…) —
    # thiếu chúng thì ảnh đội lạ lọt qua cổng lọc (anh bắt: ảnh "cầu thủ Thái Lan tập
    # luyện" lọt vào bài Việt Nam–Malaysia). Cổng lọc chỉ mạnh bằng từ điển của nó.
    "viet nam": ["viet nam", "vietnam", "vn", "tuyen viet nam", "dt viet nam",
                 "tuyen viet", "sao vang", "rong vang"],
    "malaysia": ["malaysia", "malay", "harimau", "tuyen malay", "ho malay"],
    "thai lan": ["thai lan", "thailand", "voi chien", "fa thailand", "tuyen thai",
                 "u23 thai", "u20 thai", "nguoi thai", "cau thu thai", "doi thai"],
    "indonesia": ["indonesia", "indo", "garuda", "tuyen indo", "nguoi indo"],
    "campuchia": ["campuchia", "cambodia", "tuyen campuchia", "angkor"],
    "singapore": ["singapore", "tuyen singapore", "su tu bien"],
    "myanmar": ["myanmar", "tuyen myanmar"],
    "lao": ["lao", "tuyen lao"],
    "philippines": ["philippines", "philippine", "tuyen philippines"],
    "dong timor": ["dong timor", "timor"],
    "trung quoc": ["trung quoc", "china", "tuyen trung quoc"],
    "han quoc": ["han quoc", "korea", "tuyen han quoc", "nguoi han"],
    "nhat ban": ["nhat ban", "japan", "tuyen nhat", "nguoi nhat", "samurai"],
    "an do": ["an do", "india", "tuyen an do"],
    "nepal": ["nepal"],
}


LUAT_GHEP = os.path.join(DD.KHO_TAI_NGUYEN, "luat-ghep-anh.md")
_LUAT = {"mtime": 0, "chu": ""}
_NHAN_GOIY = {"mt": None, "ds": []}      # cache gợi ý nhãn kho (ảnh + video), theo mtime sổ


def _tom_tat_bong_da():
    """Tóm tắt KIẾN THỨC TUYỂN QUỐC GIA để nhét vào prompt (anh khoanh vùng 11/08:
    trọng tâm AFF/ASEAN Cup, CLB chỉ đủ để lọc). Chỉ lấy mục `chac` cao/vừa — số liệu
    lung lay thì đừng đưa cho máy dùng."""
    try:
        kt = json.load(open(os.path.join(DD.KHO_TAI_NGUYEN,
                                         "kien-thuc-tuyen-qg.json"), encoding="utf-8"))
    except Exception:
        return ""
    vd = [f"{x['nam']}: {x['vo_dich']}" for x in kt.get("lich_su_vo_dich", [])
          if x.get("vo_dich") and x.get("chac") in ("cao", "vua")][-8:]
    dt = [f"{x['doi']} ({x.get('biet_danh','')}, áo {x.get('ao','?')})"
          for x in kt.get("doi_thu_chinh", [])]
    mc = [f"{x['luc']}: {x['viec']}" for x in kt.get("moc_tuyen_vn", [])
          if x.get("chac") == "cao"][-5:]
    return ("\n═══ BỐI CẢNH GIẢI (ASEAN Cup / AFF Cup) ═══\n"
            f"• Thể thức: {kt.get('giai', {}).get('the_thuc', '')}\n"
            f"• Vô địch gần đây — {' · '.join(vd)}\n"
            f"• Đội mạnh khu vực: {' · '.join(dt)}\n"
            f"• Mốc đáng nhớ của tuyển VN: {' · '.join(mc)}\n"
            "═══════════════════════════════\n")


def _doc_luat_ghep():
    """NÃO LUẬT NGHIỆP VỤ (anh đặt 11/08: "cần có skill để có não, biết tư duy so sánh
    giữa nội dung bài và nhãn tài nguyên"). File nằm cạnh kho, server nạp vào prompt,
    skill soc-ghep-anh cũng đọc chính nó — một nguồn, không đẻ bản sao."""
    try:
        mt = os.path.getmtime(LUAT_GHEP)
    except OSError:
        return ""
    if mt != _LUAT["mtime"]:
        try:
            _LUAT.update(mtime=mt, chu=open(LUAT_GHEP, encoding="utf-8").read())
        except Exception:
            return ""
    return _LUAT["chu"]


TU_DIEN = os.path.join(DD.KHO_TAI_NGUYEN, "tu-dien-thuc-the.json")
_TD = {"mtime": 0, "d": {}}


def _doc_tu_dien():
    """TỪ ĐIỂN THỰC THỂ (anh đặt 11/08: "phải có list CLB, cầu thủ, sân, HLV… để có
    CĂN CỨ phân loại"). Máy tra file này thay vì bảng cứng trong code — anh thêm tên
    mới vào từ điển là mọi cửa nhận ra ngay, khỏi sửa code."""
    try:
        mt = os.path.getmtime(TU_DIEN)
    except OSError:
        return {}
    if mt != _TD["mtime"]:
        try:
            _TD.update(mtime=mt, d=json.load(open(TU_DIEN, encoding="utf-8")))
        except Exception:
            return _TD["d"]
    return _TD["d"]


# CLB V.League — ảnh mặc áo CLB KHÔNG dùng cho bài về tuyển quốc gia (Luật 1, anh dạy
# 11/08 từ ca thật: Đình Bắc áo Công an Hà Nội lọt vào bài tuyển).
# Bảng dưới là BẢN DỰ PHÒNG khi chưa có từ điển; có từ điển thì lấy từ đó.
_CLB_GOC = {
    "cong an ha noi": ["cong an ha noi", "cahn", "cong an hn"],
    "cong an tphcm": ["cong an tphcm", "cong an tp hcm", "catphcm"],
    "ha noi fc": ["ha noi fc", "clb ha noi"],
    "the cong viettel": ["the cong", "viettel"],
    "nam dinh": ["nam dinh", "thep xanh nam dinh"],
    "binh duong": ["binh duong", "becamex"],
    "hagl": ["hagl", "hoang anh gia lai"],
    "slna": ["slna", "song lam nghe an"],
    "thanh hoa": ["thanh hoa", "dong a thanh hoa"],
    "hai phong": ["hai phong"],
    "binh dinh": ["binh dinh"],
    "da nang": ["da nang", "shb da nang"],
    "khanh hoa": ["khanh hoa"],
    "quang nam": ["quang nam"],
    "ha tinh": ["ha tinh", "hong linh ha tinh"],
}
# Dấu hiệu bài nói về TUYỂN QUỐC GIA (không phải CLB)
_DAU_TUYEN = ["tuyen quoc gia", "doi tuyen", "tuyen viet nam", "aff", "sea games",
              "vong loai world cup", "world cup", "asian cup", "asiad", "u23", "u22",
              "giao huu quoc te", "fifa days"]
# Dấu hiệu bài nói về CLB / giải trong nước
_DAU_CLB = ["v league", "vleague", "v.league", "cup quoc gia", "sieu cup",
            "afc champions", "giai hang nhat", "clb"]


def _bang_clb():
    """Bảng CLB: ưu tiên TỪ ĐIỂN (anh sửa được), thiếu thì rơi về bảng gốc trong code."""
    td = _doc_tu_dien().get("clb_vleague") or {}
    if not td:
        return _CLB_GOC
    return {k: [_bo_dau_k(x) for x in (v.get("goi") or [k])] for k, v in td.items()}


def _clb_trong(chuoi):
    k = " " + _bo_dau_k(chuoi) + " "
    return {t for t, cach in _bang_clb().items() if any(f" {c} " in k for c in cach)}


def _la_bai_tuyen(chuoi):
    """Bài này nói về TUYỂN hay về CLB? Trả True nếu rõ ràng là tuyển."""
    k = " " + _bo_dau_k(chuoi) + " "
    t = sum(1 for x in _DAU_TUYEN if f" {x} " in k)
    c = sum(1 for x in _DAU_CLB if f" {x} " in k)
    return t > 0 and t >= c


def _bang_doi():
    """Bảng ĐỘI TUYỂN: ưu tiên từ điển, thiếu thì bảng gốc."""
    td = _doc_tu_dien().get("tuyen_quoc_gia") or {}
    if not td:
        return _DOI_TUYEN
    return {k: [_bo_dau_k(x) for x in (v.get("goi") or [k])] for k, v in td.items()}


def _doi_trong(chuoi):
    """Những ĐỘI TUYỂN được nhắc trong một đoạn chữ (bỏ dấu, khớp theo cụm)."""
    k = " " + _bo_dau_k(chuoi) + " "
    return {t for t, cach in _bang_doi().items() if any(f" {c} " in k for c in cach)}


def _thuc_the_bai(viec, nh, kb):
    """ĐỘI có mặt trong bài — dùng để LOẠI ảnh đội khác (anh bắt 11/08: bài Việt Nam
    đấu Malaysia mà đề xuất ảnh tuyển Thái Lan, vì nhãn nào cũng có 'cầu thủ', 'đội
    tuyển', 'sân vận động' nên chấm chữ thấy giống nhau).

    Đây là kiểu "thông minh đóng băng": luật cứng bằng code, 0 token, chạy tức thì —
    thứ gì code quyết được thì đừng để model quyết."""
    chuoi = " ".join([kb.get("tieu_de", ""), kb.get("loi_binh", ""),
                      kb.get("tin_goc", ""),
                      " ".join(str(v) for v in (nh.get("tu_khoa") or {}).values()),
                      " ".join(str(v) for o in (nh.get("tu_khoa_phu") or {}).values()
                               for v in (o or {}).values())])
    return _doi_trong(chuoi)


HOC_GHEP = os.path.join(KHO_CHU_THE, "hoc-ghep.jsonl")
_HOC = {"mtime": 0, "ds": []}


def _ghi_hoc_ghep(ma, cau_chu, tu_khoa, m_anh):
    """SỔ HỌC GHÉP ẢNH (anh hỏi 11/08: "làm sao máy thông minh mà ít dùng model").

    Mỗi lần ANH tự tay chọn một tấm cho một câu, ghi lại cặp (ý câu ↔ nhãn ảnh anh
    chọn). Lần sau gặp câu na ná, code thuần tra sổ này rồi CỘNG ĐIỂM cho tấm mang
    nhãn tương tự — máy bắt chước gu anh mà không tốn một token nào.

    Đây là cách rẻ nhất để máy khôn lên: model chỉ cần giỏi MỘT LẦN, quyết định của
    anh thì đóng băng lại thành luật dùng mãi."""
    try:
        d = {"luc": datetime.now().strftime("%Y-%m-%d %H:%M"), "ma": ma,
             "cau": (cau_chu or "")[:180], "tu_khoa": (tu_khoa or "")[:90],
             "chu_the": m_anh.get("chu_the", ""),
             "nhan": (m_anh.get("nhan") or [])[:6]}
        with NT.khoa_ghi(HOC_GHEP) as kh:
            with open(HOC_GHEP, "a", encoding="utf-8") as f:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        _HOC["mtime"] = 0
    except Exception:
        pass


def _nap_hoc_ghep():
    try:
        mt = os.path.getmtime(HOC_GHEP)
    except OSError:
        return []
    if mt != _HOC["mtime"]:
        ds = []
        for l in open(HOC_GHEP, encoding="utf-8"):
            try:
                d = json.loads(l)
            except Exception:
                continue
            ds.append((set(_bo_dau_k(d.get("cau", "") + " "
                                     + d.get("tu_khoa", "")).split()),
                       _bo_dau_k(d.get("chu_the", "")),
                       set(_bo_dau_k(" ".join(d.get("nhan") or [])).split())))
        _HOC.update(mtime=mt, ds=ds)
    return _HOC["ds"]


def _diem_hoc(tu_cau, m):
    """Điểm THƯỞNG theo sổ học: câu na ná mà anh từng chọn tấm mang nhãn thế này."""
    hoc = _nap_hoc_ghep()
    if not hoc or not tu_cau:
        return 0
    ct = _bo_dau_k(m.get("chu_the", ""))
    nh_a = set(_bo_dau_k(" ".join(m.get("nhan") or [])).split())
    tot = 0
    for tu_h, ct_h, nh_h in hoc:
        chung = len(tu_cau & tu_h)
        if chung < 2:                               # câu phải thật sự giống mới tính
            continue
        if ct and ct == ct_h:
            tot = max(tot, 6 + chung)               # đúng chủ thể anh từng chọn
        elif nh_a & nh_h:
            tot = max(tot, 2 + min(len(nh_a & nh_h), 3))
    return tot


def _kho_nha_bai(ma, gioi_han=150, bo_qua=0, q=""):
    """CẢ KHO NHÀ liên quan tới BÀI này, xếp theo mức liên quan (anh đặt 11/08:
    "list ảnh nghèo nàn quá — hiện hết ảnh kho gắn nhãn hợp lý, xếp theo thứ tự liên
    quan ưu tiên, tối đa 150, gọi thêm được").

    Khác /api/kho-nha (tra MỘT từ khoá của MỘT câu): ở đây chấm điểm mỗi tấm với TỪ
    KHOÁ CỦA MỌI CÂU + tiêu đề, giữ điểm cao nhất và NHỚ tấm ấy hợp câu nào — giao
    diện hiện "≈ câu N" để anh biết thả vào đâu. Tấm ĐANG dùng trong bài bị loại."""
    viec = os.path.join(DD.VIEC, ma)
    nh = _nhap(viec)
    try:
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    except Exception:
        kb = {}
    truy = []                                       # [(chỉ số câu | None, [từ bỏ dấu])]
    if (q or "").strip():
        # ANH TỰ TÌM (11/08 chiều): chỉ chấm theo đúng cụm anh gõ, bỏ qua từ khoá bài —
        # anh gõ tay là anh biết mình muốn gì, đừng để từ khoá bài kéo kết quả đi chỗ khác
        truy.append((None, _mo_rong_q(q).split()))
    else:
        for k, v in (nh.get("tu_khoa") or {}).items():
            if (v or "").strip():
                truy.append((int(k), _mo_rong_q(v).split()))
        for k, o in (nh.get("tu_khoa_phu") or {}).items():
            for j, v in (o or {}).items():
                if (v or "").strip():
                    truy.append((int(k), _mo_rong_q(v).split()))
        if kb.get("tieu_de"):                       # tít làm lưới vét chung cho cả bài
            truy.append((None, _bo_dau_k(kb["tieu_de"]).split()))
    if not truy or not os.path.exists(SO_CHU_THE):
        return {"tong": 0, "ds": []}
    dang_dung = {os.path.basename(str(v)) for v in (nh.get("ban_do") or {}).values() if v}
    for ds_ap in (nh.get("anh_phu") or {}).values():
        dang_dung |= {os.path.basename(str(x)) for x in (ds_ap or []) if x}
    # HỒ SƠ BÀI (máy đã đọc tin) là nguồn CHUẨN nhất; không có thì mới quét chuỗi thô
    hs_bai = _doc_ho_so_bai(ma)
    doi_bai = set()
    for x in (hs_bai.get("doi") or []):
        doi_bai |= _doi_trong(x)
    if not doi_bai:
        doi_bai = _thuc_the_bai(viec, nh, kb)
    # LUẬT 1 (anh dạy 11/08): bài về TUYỂN thì ảnh mặc áo CLB không dùng được, dù đúng
    # người. Xác định thân phận của BÀI một lần, rồi soi từng tấm ở vòng dưới.
    chuoi_bai = " ".join([kb.get("tieu_de", ""), kb.get("loi_binh", ""),
                          kb.get("tin_goc", "")])
    bai_tuyen = (hs_bai.get("cap_do") in ("tuyen", "u23")) if hs_bai.get("cap_do") \
        else _la_bai_tuyen(chuoi_bai)
    clb_bai = _clb_trong(chuoi_bai)                  # CLB mà chính bài có nhắc
    # sổ học tra theo TỪ của câu: gom sẵn tập từ mỗi câu (thoại + từ khoá)
    cau_ds = _tach_cau(kb.get("loi_binh", ""))
    tu_cau_hoc = {}
    for i_c, c_txt in enumerate(cau_ds):
        tu_cau_hoc[i_c] = set(_bo_dau_k(
            c_txt + " " + str((nh.get("tu_khoa") or {}).get(str(i_c), ""))).split())
    tu_q_hoc = set(_bo_dau_k(q).split()) if (q or "").strip() else set()
    ra, loai_doi, loai_clb = [], 0, 0
    for dong in open(SO_CHU_THE, encoding="utf-8"):
        try:
            m = json.loads(dong)
        except Exception:
            continue
        if m.get("cho_nhan"):                       # chưa gắn nhãn thì chưa đáng bày
            continue
        # LOẠI ẢNH ĐỘI KHÁC (anh bắt 11/08): tấm nhắc đội mà bài KHÔNG nhắc đội nào
        # trong số đó thì vứt — "Tuyển Thái Lan" không có cửa vào bài Việt Nam-Malaysia.
        # Bài không nhắc đội nào (tin ngoài lề) thì không lọc, kẻo loại oan.
        phat_la = 0
        if doi_bai:
            # Đội lạ nằm ở CHỦ THỂ hay NHÃN (hai trường mạnh) → LOẠI thẳng, kể cả khi
            # ảnh có kèm đội của bài: ảnh trận Việt–Thái vẫn là SAI TRẬN với bài
            # Việt–Malaysia (anh bắt 11/08, vòng siết thứ hai).
            manh = _doi_trong(m.get("chu_the", "") + " " + " ".join(m.get("nhan", [])))
            if manh - doi_bai:
                loai_doi += 1
                continue
            # Đội lạ chỉ thấp thoáng trong MÔ TẢ thì không loại oan, chỉ hạ điểm mạnh
            if _doi_trong(m.get("mo_ta", "")) - doi_bai:
                phat_la = 1
        # LUẬT 1 — bài về TUYỂN mà ảnh mặc áo CLB (mà bài không nhắc CLB đó) thì LOẠI:
        # đúng người nhưng SAI THÂN PHẬN, lên hình là người xem thấy ngay
        if bai_tuyen:
            clb_anh = _clb_trong(m.get("chu_the", "") + " "
                                 + " ".join(m.get("nhan", [])) + " "
                                 + m.get("mo_ta", ""))
            if clb_anh - clb_bai:
                loai_clb += 1
                continue
        if (q or "").strip():
            # TÌM TAY dùng bộ tìm NGHIÊM (_diem_khop — trượt một từ là trượt cả cụm),
            # cùng luật với ô tìm trang kho anh đã quen. Chấm mềm ở đây là hỏng: gõ
            # "xyzabc không có" mà ra 356 tấm vì mấy từ phổ thông khớp bừa (11/08).
            tot = _diem_khop(q, [(m.get("chu_the", ""), 3),
                                 (" ".join(m.get("nhan", [])), 2),
                                 (m.get("mo_ta", ""), 1)])
            cau_tot = None
        else:
            truong = [([w for w in _bo_dau_k(m.get("chu_the", "")).split()], 3),
                      ([w for w in _bo_dau_k(" ".join(m.get("nhan", []))).split()], 2),
                      ([w for w in _bo_dau_k(m.get("mo_ta", "")).split()], 1)]
            tot, cau_tot = 0, None
            for i_c, tu_q in truy:
                d = _diem_mem(tu_q, truong)
                if d > tot:
                    tot, cau_tot = d, i_c
        if tot <= 0:
            continue
        diem = tot + (4 if m.get("hang") == "len_hinh" else 0) \
            - min(len(m.get("da_dung", [])), 5) * 2
        # SỔ HỌC: anh từng chọn tấm kiểu này cho câu na ná → cộng điểm (0 token)
        diem += _diem_hoc(tu_cau_hoc.get(cau_tot) or tu_q_hoc, m)
        if phat_la:                                 # mô tả thấp thoáng đội lạ → xuống hạng
            diem *= 0.4
        ra.append((diem, cau_tot, m))
    ra.sort(key=lambda x: (-x[0], x[2].get("luc_nhap", "")))
    # BẢN MÁY XẾP (ngữ nghĩa) đè lên xếp hạng thô: tấm nào model đã ghép cho câu nào
    # thì lên ĐẦU và mang đúng số câu ấy — anh mở ra là thấy bản chuẩn nhất trước.
    if not (q or "").strip():
        xep = (_doc_kho_xep(ma) or {}).get("xep") or {}
        uu = {}
        for k_c, v in xep.items():
            for thu, t in enumerate(v.get("tep") or []):
                # mã ô phụ là "3:0" — int() thẳng là NỔ, mà nổ ở đây thì cả dải kho
                # nhà chết câm (lỗi ngầm từ hôm thêm ô phụ vào máy xếp, bắt 11/08).
                # Nhãn ≈N là số CÂU nên lấy phần trước dấu hai chấm.
                uu[t] = (int(k_c.split(":")[0]), thu)
        if uu:
            ra.sort(key=lambda x: (x[2]["tep"] not in uu,
                                   uu.get(x[2]["tep"], (0, 0))[1], -x[0]))
            # Cảnh nào MODEL đã kết luận "kho không có ảnh hợp" thì tấm khớp-từ cho
            # cảnh ấy KHÔNG được mang nhãn ≈N nữa (11/08: đó chính là bệnh "đề xuất cho
            # có" — cảnh nói về công an mà dán ≈ vào ảnh sân trống). Hạ về nhãn "bài".
            # chỉ tính Ô CHÍNH: ô phụ rỗng KHÔNG có nghĩa là cả câu bí — ô chính vẫn
            # có thể đủ ảnh, gỡ nhãn ≈ của câu đó là oan
            trong = {int(k) for k, v in xep.items()
                     if ":" not in k and not (v.get("tep") or [])}
            ra = [(d, uu[m["tep"]][0] if m["tep"] in uu
                   else (None if c in trong else c), m) for d, c, m in ra]
    tong = len(ra)
    # XEN KẼ THEO CẢNH (anh đặt 11/08): xếp thuần theo điểm thì 150 tấm đầu toàn hợp
    # MỘT câu có từ khoá rộng ("tuyển việt nam") — bày ra vẫn nghèo theo kiểu khác.
    # Chia theo câu rồi lấy vòng tròn: mỗi vòng một tấm tốt nhất của mỗi câu, câu
    # CHƯA CÓ ẢNH đi trước. Nhờ vậy 150 tấm phủ đủ mọi cảnh của bài.
    theo_cau = {}
    for x in ra:
        theo_cau.setdefault(x[1], []).append(x)
    chua_co = {i for i in range(200) if not (nh.get("ban_do") or {}).get(str(i))}
    thu_tu = sorted(theo_cau, key=lambda c: (
        c is None,                                  # nhóm "theo tít" xuống cuối
        c not in chua_co if c is not None else True,  # câu chưa có ảnh lên trước
        c if c is not None else 999))
    xen = []
    while any(theo_cau[c] for c in thu_tu):
        for c in thu_tu:
            if theo_cau[c]:
                xen.append(theo_cau[c].pop(0))
    ra = xen
    may_xep, trong_may = set(), []
    if not (q or "").strip():
        bxep = _doc_kho_xep(ma) or {}
        for v in (bxep.get("xep") or {}).values():
            may_xep |= set(v.get("tep") or [])
        trong_may = bxep.get("trong") or []
    ket = []
    for diem, cau_tot, m in ra[bo_qua:bo_qua + gioi_han]:
        ket.append({"tep": m["tep"], "u": "/kho-nha-anh/" + m["tep"],
                    "chu_the": m.get("chu_the", ""), "mo_ta": m.get("mo_ta", ""),
                    "nhan": m.get("nhan", [])[:4], "hang": m.get("hang", ""),
                    "cau": cau_tot, "diem": round(diem, 1),
                    "may": m["tep"] in may_xep,     # model đã ghép tấm này cho câu đó
                    "da_dung": len(m.get("da_dung", [])),
                    "trong_bai": m["tep"] in dang_dung})
    return {"tong": tong, "ds": ket, "co_may_xep": bool(may_xep),
            "trong_may": trong_may, "loai_doi": loai_doi,
            "loai_clb": loai_clb, "bai_tuyen": bai_tuyen,
            "doi_bai": sorted(doi_bai)}


def _trich_ho_so_bai(ma):
    """ĐỌC TIN → HỒ SƠ BÀI (anh chốt 11/08: "tin viết sẵn bên GPT, anh chỉ paste; khi
    lưu và duyệt cần đọc nội dung rồi gọi đúng tài nguyên").

    Mắt xích còn thiếu của cả dây chuyền: trước nay máy chỉ có TỪ KHOÁ dạng chuỗi chữ
    cho từng câu — tra kho bằng chữ thì mới ra chuyện "công an" lấy ảnh sân trống. Nay
    đọc MỘT LƯỢT ra hồ sơ CÓ CẤU TRÚC: ai, đội nào, giải nào, trận nào, đã diễn ra
    chưa, cảm xúc gì. Hồ sơ ấy mới là thứ tra kho được chính xác, và là mồi chuẩn cho
    mọi ảnh gắp về sau.

    Chạy MỘT lần trong chuỗi sau Duyệt lời (rẻ), lưu `anh/ho-so-bai.json`."""
    viec = os.path.join(DD.VIEC, ma)
    try:
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    except Exception:
        return {}
    chuoi = "\n".join([kb.get("tieu_de", ""), kb.get("loi_binh", ""),
                       kb.get("tin_goc", "")])[:6000]
    if not chuoi.strip():
        return {}
    lenh = (
        "Đọc bản tin bóng đá dưới đây rồi rút ra HỒ SƠ có cấu trúc. Chỉ ghi thứ CÓ "
        "TRONG BÀI, không suy diễn, không bịa.\n\n" + chuoi +
        "\n\nTrả về DUY NHẤT JSON:\n"
        '{"nhan_vat": ["tên người được nhắc, đầy đủ nếu bài ghi đầy đủ"],\n'
        ' "doi": ["đội tuyển/CLB được nhắc"],\n'
        ' "giai": "tên giải (AFF Cup/ASEAN Cup/SEA Games/V.League…) + năm nếu có",\n'
        ' "tran": "trận nào, vòng nào (vd: Việt Nam - Malaysia, bán kết lượt về)",\n'
        ' "thoi_diem": "ngày giờ bài nhắc, nếu có",\n'
        ' "da_dien_ra": true/false,   ← TIN NÓI VỀ VIỆC ĐÃ XẢY RA hay SẮP xảy ra\n'
        ' "cap_do": "tuyen" | "clb" | "u23",   ← bài nói về tuyển quốc gia hay CLB\n'
        ' "cam_xuc": "cung cảm xúc chính: xót xa/tự hào/bất công/tò mò/vỡ lẽ/căng thẳng",\n'
        ' "hinh_can": ["3-6 loại HÌNH ẢNH mà bài này cần, nói bằng lời thường: '
        'vd \'cầu thủ X trong màu áo tuyển\', \'sân Mỹ Đình đông khán giả\', '
        '\'HLV họp báo\'"]}\n'
        "da_dien_ra=false thì TUYỆT ĐỐI không có ảnh ăn mừng/tỷ số của trận đó.")
    try:
        r = subprocess.run(
            [NT.tim_claude(), "-p", "--model",
             os.environ.get("KHO_MODEL", "claude-sonnet-5")],
            input=lenh, capture_output=True, text=True, timeout=300)
        m = re.search(r"\{.*\}", r.stdout, re.S)
        hs = json.loads(m.group(0)) if m else {}
    except Exception as e:
        return {"loi": str(e)}
    if not isinstance(hs, dict) or not hs:
        return {}
    # chuẩn hoá tên người/đội qua từ điển — hồ sơ phải nói CÙNG NGÔN NGỮ với nhãn kho
    hs["nhan_vat"] = [_chuan_hoa_ct(x) or x for x in (hs.get("nhan_vat") or [])][:10]
    hs["doi"] = [str(x) for x in (hs.get("doi") or [])][:8]
    hs["luc"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        os.makedirs(os.path.join(viec, "anh"), exist_ok=True)
        json.dump(hs, open(os.path.join(viec, "anh", "ho-so-bai.json"), "w",
                           encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
    return hs


def _doc_ho_so_bai(ma):
    try:
        return json.load(open(os.path.join(DD.VIEC, ma, "anh", "ho-so-bai.json"),
                              encoding="utf-8"))
    except Exception:
        return {}


# ═══════ KHUNG ĐÔI — BA KIỂU CONTENT CẦN HAI ẢNH (anh chỉ ra 11/08, việc #58) ═══════
# ① HAI CHỦ THỂ A và B — hai đội bóng, hai cầu thủ cùng được nhắc trong một câu
# ② CHỦ THỂ + DẪN CHỨNG/SỐ LIỆU — "Đình Bắc" đi kèm bảng xếp hạng vua phá lưới
# ③ SO SÁNH — hai vế đối đầu nhau hoặc bổ nghĩa cho nhau
# Cụm dưới đây cố ý CHẶT: "hơn", "còn", "trước" quá phổ biến trong tiếng Việt, để vào
# thì câu nào cũng dính cờ, mà cờ dính hết thì bằng không có cờ.
_NOI_DOI = ["vs", "doi dau", "dau voi", "cham tran", "so tai", "quyet dau", "chu nha",
            "so voi", "trong khi", "nguoc lai", "khac voi", "trai nguoc", "mot ben",
            "hon han", "vuot mat", "kem xa", "ap dao", "ngang tai", "canh tranh"]
_DAU_SO_LIEU = ["bang xep hang", "vua pha luoi", "thong ke", "xep thu", "dan dau",
                "so lieu", "thanh tich", "ky luc", "bang diem", "chi so", "ty le",
                "phong do", "top ", "hang dau", "bang a", "bang b", "bang c"]


def _ten_ma_o(k):
    """Mã Ô → tên anh đọc được: "9" → "10" (cảnh chính), "9:0" → "10b" (ô phụ đầu).

    Cả hệ dùng hai kiểu mã này lẫn nhau; chỗ nào in ra cho anh xem đều phải qua đây,
    và tuyệt đối không `int()` thẳng mã ô — ô phụ có dấu hai chấm là nổ (đã gãy hai
    lần trong một buổi 11/08: dải kho nhà chết câm, lượt model xếp kho mất trắng).
    """
    p = str(k).split(":")
    return str(int(p[0]) + 1) + (chr(98 + int(p[1])) if len(p) > 1 else "")


def _do_khung_doi(cau, ho_so=None):
    """CODE dò thô câu nào CÓ DÁNG khung đôi — 0 token, chạy tức thì.

    KHÔNG tự quyết. Kết quả chỉ đi vào prompt như GỢI Ý để model soi kỹ mấy câu này —
    chia việc đúng chỗ mạnh của mỗi bên: code bắt được CẤU TRÚC (hai tên riêng, từ nối
    đối đầu, dấu số liệu), model mới biết KHO có tấm nào ghép được. Đúng luật "rẻ
    trước, model sau": phần nào code làm được thì đừng bắt model quét lại.
    """
    nv = [x for x in ((ho_so or {}).get("nhan_vat") or []) if x]
    ra = {}
    for i, c in enumerate(cau):
        k = " " + _bo_dau_k(c) + " "
        dau = []
        if len(_doi_trong(c)) >= 2:
            dau.append("hai ĐỘI cùng câu")
        co_nv = [t for t in nv if f" {_bo_dau_k(t)} " in k]
        if len(co_nv) >= 2:
            dau.append("hai NHÂN VẬT: " + ", ".join(co_nv[:3]))
        if any(f" {t} " in k or k.startswith(f" {t}") for t in _NOI_DOI):
            dau.append("từ nối đối đầu/so sánh")
        if any(t in k for t in _DAU_SO_LIEU):
            dau.append("có dẫn chứng/số liệu")
        if dau:
            ra[i] = dau
    return ra


def _xep_kho_nghia(ma, bao_tien=None, so_ung_vien=140):
    """MÁY XẾP KHO THEO NGỮ NGHĨA (anh đặt 11/08 tối: "tìm ảnh từ kho chưa thông minh,
    chấp nhận model cao để đảm bảo chính xác").

    Vì sao cần: tra kho bằng KHỚP TỪ không hiểu nghĩa — câu "công an siết an ninh sân
    Mỹ Đình" mà kho không có ảnh công an thì nó bám chữ "sân vận động" rồi bày ảnh sân
    TRỐNG. Máy phải hiểu "ăn mừng" ≠ "đứng chào cờ", "họp báo" ≠ "trên sân".

    Kiến trúc HAI TẦNG (luật hiệu quả tối đa – tài nguyên tối thiểu):
    ① CODE lọc thô lấy ~140 ứng viên khá nhất cho cả bài — rẻ, 0 token;
    ② MỘT lượt model đọc NHÃN DẠNG CHỮ của 140 tấm + toàn bộ câu, ghép theo nghĩa.
       Không cần nhìn ảnh: nhãn đã do mắt máy tả rất chi tiết lúc nhập kho (số áo, hành
       động, bối cảnh) — đọc chữ vừa đủ chính xác vừa rẻ hơn nhìn ảnh cả trăm lần.
    Dùng sonnet (KHO_MODEL) vì đây là việc SUY XÉT ngữ nghĩa, không phải việc cơ khí.

    LUẬT CỨNG: câu nào kho KHÔNG có tấm hợp thì trả RỖNG — cấm chọn bừa cho đủ. Đây là
    chính bệnh anh bắt sáng nay ("5 phương án" bày sân trống cho câu nói về công an).
    """
    viec = os.path.join(DD.VIEC, ma)
    nh = _nhap(viec)
    try:
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    except Exception:
        kb = {}
    cau = _tach_cau(kb.get("loi_binh", ""))
    if not cau:
        return {"loi": "bài chưa có lời"}
    # ① lọc thô: gom ứng viên của MỌI câu bằng code (đã xen kẽ đủ cảnh)
    tho = _kho_nha_bai(ma, gioi_han=so_ung_vien, bo_qua=0)
    ds_uv = tho.get("ds") or []
    if not ds_uv:
        return {"loi": "kho chưa có tấm nào hợp bài"}
    if bao_tien:
        bao_tien(f"máy đọc {len(ds_uv)} tấm kho + {len(cau)} câu", 0, 1)
    dong_anh = []
    for k, m in enumerate(ds_uv):
        ta = " · ".join(x for x in [m.get("chu_the", ""),
                                    ", ".join(m.get("nhan", [])[:5]),
                                    (m.get("mo_ta", "") or "")[:110]] if x)
        # dấu NGANG/DỌC (anh chốt 14/08): model chọn theo nhãn chữ, không thấy hình —
        # phải nói cho nó biết tấm nào dọc, vì khung đôi CẤM ảnh dọc (mất nhân vật)
        ng = _anh_ngang(kich_thuoc=m.get("kich_thuoc", ""))
        dong_anh.append(f"[{k}]{'▯DỌC ' if ng is False else ' '}{ta}")
    # MỌI Ô, KHÔNG CHỈ CẢNH CHÍNH (luật anh "cảnh chính có gì cảnh phụ có nấy" — em
    # quên lần thứ tư 11/08). Ô phụ dùng khoá "3:0" và phải mang ẢNH KHÁC ô chính dù
    # cùng câu thoại, vì nó sinh ra chính để đổi hình cho đúng nhịp 2,5–5s.
    dong_cau = []
    tk = nh.get("tu_khoa") or {}
    tkp = nh.get("tu_khoa_phu") or {}
    giay = _moc_cau(cau, _do_dai_giong(viec)
                    or sum(len(c.split()) for c in cau) / TIENG_MOT_PHUT * 60)
    for i, c in enumerate(cau):
        tkc = (tk.get(str(i)) or "").strip()
        dong_cau.append(f"({i}) {c}" + (f"   ⟨từ khoá: {tkc}⟩" if tkc else ""))
        d_i = giay[i] - (giay[i - 1] if i else 0.0)
        so_phan = NC.chia_nhip([d_i], [False])[0]["so_phan"] if d_i else 1
        for j in range(max(0, so_phan - 1)):
            tj = ((tkp.get(str(i)) or {}).get(str(j)) or "").strip()
            dong_cau.append(
                f"({i}:{j}) [CẢNH PHỤ của câu {i + 1} — CÙNG lời, phải chọn ảnh KHÁC "
                f"hẳn ô chính để đổi hình] {c}"
                + (f"   ⟨từ khoá riêng: {tj}⟩" if tj else ""))
    luat = _doc_luat_ghep()
    lenh = (
        "Em là biên tập viên hình ảnh của kênh bóng đá. Dưới đây là KHO ẢNH (mỗi dòng "
        "là một tấm, kèm mô tả do mắt máy ghi) và LỜI BÌNH của video (mỗi dòng một "
        "câu). Việc của em: với TỪNG CÂU, chọn tối đa 4 tấm HỢP NGHĨA nhất để minh hoạ.\n\n"
        + (f"════ NÃO LUẬT NGHIỆP VỤ CỦA KÊNH (đọc kỹ, áp đủ) ════\n{luat}\n"
           "════════════════════════════════════════\n\n" if luat else "")
        + _tom_tat_bong_da()
        + (lambda h: (f"\n═══ HỒ SƠ BÀI NÀY (máy đã đọc tin) ═══\n"
                      f"• Nhân vật: {', '.join(h.get('nhan_vat') or []) or '—'}\n"
                      f"• Đội: {', '.join(h.get('doi') or []) or '—'}\n"
                      f"• Giải: {h.get('giai') or '—'} · Trận: {h.get('tran') or '—'}\n"
                      f"• Cấp độ: {h.get('cap_do') or '—'} · "
                      f"{'ĐÃ diễn ra' if h.get('da_dien_ra') else 'CHƯA diễn ra — cấm ảnh ăn mừng/tỷ số'}\n"
                      f"• Hình bài cần: {' · '.join(h.get('hinh_can') or []) or '—'}\n"
                      "══════════════════════════\n") if h else "")(_doc_ho_so_bai(ma))
        + "KHO ẢNH:\n" + "\n".join(dong_anh) + "\n\nLỜI BÌNH:\n" + "\n".join(dong_cau) +
        "\n\nLUẬT BẮT BUỘC:\n"
        "① HỢP NGHĨA, không phải trùng chữ. Câu nói về CÔNG AN/AN NINH mà kho chỉ có "
        "ảnh sân trống thì để RỖNG — tuyệt đối không lấy ảnh sân chỉ vì câu có chữ "
        "'sân vận động'. Thà thiếu còn hơn sai.\n"
        "② Đúng NGƯỜI, đúng ĐỘI, đúng TRẬN, đúng CẢM XÚC. 'ăn mừng' phải là ảnh ăn "
        "mừng thật, không phải ảnh đứng chào cờ. Câu nhắc tên ai thì ưu tiên ảnh có "
        "đúng người đó.\n"
        "③ MỘT tấm chỉ dùng cho MỘT câu — chọn rồi thì đừng chọn lại cho câu khác.\n"
        "④ Câu nào không có tấm nào thật sự hợp thì trả mảng rỗng. Được phép để trống "
        "nhiều câu — đó là thông tin quý (anh sẽ biết phải đi tìm thêm).\n"
        "⑤ KHUNG ĐÔI — hai ảnh chia đôi khung TRÊN/DƯỚI trong CÙNG một cảnh. Chỉ đề "
        "xuất khi câu thuộc một trong BA kiểu sau:\n"
        "   · hai_chu_the — câu nhắc HAI chủ thể (hai đội bóng, hai cầu thủ): mỗi nửa "
        "khung một chủ thể;\n"
        "   · dan_chung — câu nói về MỘT người/đội KÈM số liệu, bảng xếp hạng, thống "
        "kê, kỷ lục: nửa trên là người, nửa dưới là bảng/biểu/khoảnh khắc chứng minh;\n"
        "   · so_sanh — hai vế đối đầu nhau hoặc bổ nghĩa cho nhau.\n"
        "   Nửa TRÊN và nửa DƯỚI phải nói HAI ý khác nhau — hai tấm cùng một người, "
        "cùng một khoảnh khắc thì KHÔNG phải khung đôi, chỉ là thừa ảnh.\n"
        "   Mỗi bài thường CHỈ 1–3 cảnh xứng đáng khung đôi. Không có cặp thật sự hợp "
        "thì BỎ TRƯỜNG NÀY — thà một ảnh đúng còn hơn hai ảnh gượng.\n"
        "   CẤM chọn tấm đánh dấu ▯DỌC cho khung đôi — nửa khung đôi là dải NGANG, "
        "nhét ảnh dọc vào là đầu và chân nhân vật văng khỏi hình. Cả nửa trên lẫn "
        "nửa dưới đều phải là ảnh ngang.\n"
        + ((lambda dd: ("\n⟨CODE đã dò thấy mấy câu sau CÓ DÁNG khung đôi — soi kỹ, "
                        "nhưng vẫn tự quyết, dò máy có thể sai⟩\n"
                        + "\n".join(f"   · câu ({i}): {' ; '.join(v)}"
                                    for i, v in sorted(dd.items()))
                        + "\n   Với MỖI câu vừa liệt kê: hoặc trả trường \"doi\", "
                          "hoặc trả \"doi_bo\": \"<vì sao kho không ghép đôi được — "
                          "thiếu ảnh vế nào>\". Không được lờ đi câu nào.\n")
            if dd else "")(_do_khung_doi(cau, _doc_ho_so_bai(ma)))) +
        "\nTrả về DUY NHẤT JSON, KHOÁ LÀ MÃ Ô y như trong LỜI BÌNH ở trên "
        "(\"3\" là cảnh chính câu 4, \"3:0\" là cảnh phụ thứ nhất của câu đó):\n"
        "{\"<mã ô>\": {\"chon\": [<số thứ tự tấm>, ...], \"vi_sao\": \"<một câu "
        "ngắn>\", \"doi\": {\"tren\": <số tấm>, \"duoi\": <số tấm>, \"kieu\": "
        "\"hai_chu_the|dan_chung|so_sanh\", \"vi_sao\": \"<vì sao cảnh này cần hai "
        "ảnh>\"}}}. Trường \"doi\" KHÔNG bắt buộc — chỉ thêm cho ô thật sự cần khung "
        "đôi, ô còn lại bỏ hẳn trường này. Ô nào không có tấm hợp thì {\"chon\": [], "
        "\"vi_sao\": \"kho không có ảnh <thứ đang thiếu>\"}. PHẢI trả đủ MỌI Ô có "
        "trong lời bình, kể cả cảnh phụ.")
    try:
        r = subprocess.run(
            [NT.tim_claude(), "-p", "--model",
             os.environ.get("KHO_MODEL", "claude-sonnet-5")],
            input=lenh, capture_output=True, text=True, timeout=600)
        # GIỮ BẢN THÔ của model: khi máy "không đề xuất gì" thì đây là bằng chứng duy
        # nhất phân biệt "model đã cân nhắc rồi từ chối" với "prompt hỏng, model không
        # hiểu". Không có nó thì chỉ còn đoán mò (11/08).
        try:
            open(os.path.join(viec, "anh", "kho-xep-tho.txt"), "w",
                 encoding="utf-8").write(r.stdout)
        except OSError:
            pass
        m_j = re.search(r"\{.*\}", r.stdout, re.S)
        phan = json.loads(m_j.group(0)) if m_j else {}
    except Exception as e:
        return {"loi": f"máy xếp nghẽn: {e}"}
    xep, da_chon = {}, set()
    for k_c, v in (phan or {}).items():
        k_c = str(k_c).strip()
        if not re.fullmatch(r"\d+(:\d+)?", k_c):   # "3" (chính) hoặc "3:0" (phụ)
            continue
        if not isinstance(v, dict):
            continue
        teps = []
        for idx in (v.get("chon") or [])[:4]:
            try:
                m = ds_uv[int(idx)]
            except (ValueError, IndexError, TypeError):
                continue
            if m["tep"] in da_chon:                 # luật ③: một tấm một câu
                continue
            da_chon.add(m["tep"])
            teps.append(m["tep"])
        # KHUNG ĐÔI (#58): model chỉ ra cặp trên/dưới thì ép tấm TRÊN làm ảnh chính của
        # ô (nửa trên khung là ảnh của ô — xưởng đọc `dao=False` là hiểu vậy), và gỡ
        # tấm DƯỚI khỏi danh sách chọn để nó không bị gán nhầm làm ảnh chính ô khác.
        doi = None
        dv = v.get("doi")
        if isinstance(dv, dict):
            t_t = t_d = ""
            try:
                t_t = ds_uv[int(dv["tren"])]["tep"]
                t_d = ds_uv[int(dv["duoi"])]["tep"]
            except (KeyError, TypeError, ValueError, IndexError):
                pass
            if t_t and t_d and t_t != t_d:
                teps = [t_t] + [x for x in teps if x not in (t_t, t_d)]
                da_chon.update((t_t, t_d))
                doi = {"tren": t_t, "duoi": t_d,
                       "kieu": str(dv.get("kieu", ""))[:24],
                       "vi_sao": str(dv.get("vi_sao", ""))[:160]}
        xep[k_c] = {"tep": teps, "vi_sao": str(v.get("vi_sao", ""))[:160]}
        if doi:
            xep[k_c]["doi"] = doi
        elif v.get("doi_bo"):        # model đã soi rồi từ chối — giữ LÝ DO cho anh biết
            xep[k_c]["doi_bo"] = str(v["doi_bo"])[:160]   # thiếu ảnh vế nào thì đi tìm
    ra = {"luc": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "so_uv": len(ds_uv), "xep": xep,
          "so_doi": sum(1 for v in xep.values() if v.get("doi")),
          "co_anh": sum(1 for v in xep.values() if v["tep"]),
          # GIỮ MÃ Ô DẠNG CHUỖI: ô phụ mang mã "9:0", int() nó là nổ (bắt 11/08 —
          # cả lượt model xếp kho mất trắng vì một dòng ép kiểu ở cuối hàm)
          "trong": sorted((k for k, v in xep.items() if not v["tep"]),
                          key=lambda k: [int(x) for x in k.split(":")])}
    try:
        json.dump(ra, open(os.path.join(viec, "anh", "kho-xep.json"), "w",
                           encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
    return ra


def _tran_o_cua_cau(viec, i_cau):
    """Câu này nhiều nhất chứa được bao nhiêu KHUNG (mỗi khung ≥ 2,5 giây).

    Anh chốt 13/08: "cảnh chỉ có 3 slot mà chọn 5 ảnh thì chỉ lấy 3, hai ảnh còn lại về
    kho ứng viên, KHÔNG được sinh ra cảnh dư". Trần này là cùng một phép tính bên
    `nhip_canh.so_o_toi_da` — xưởng và trạm không được lệch nhau một ô nào.
    """
    try:
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
        cau = _tach_cau(kb.get("loi_binh", ""))
        moc = _moc_cau(cau, _do_dai_giong(viec)
                       or sum(len(c.split()) for c in cau) / TIENG_MOT_PHUT * 60)
        d_i = moc[i_cau] - (moc[i_cau - 1] if i_cau else 0.0)
        return NC.so_o_toi_da(d_i)
    except Exception:
        return 8                     # không tính được thì đừng chặn oan


def _doc_kho_xep(ma):
    try:
        return json.load(open(os.path.join(DD.VIEC, ma, "anh", "kho-xep.json"),
                              encoding="utf-8"))
    except Exception:
        return {}


def _kho_nha_tim(q, toi_da=30):
    """Tra kho theo nhãn — CODE THUẦN (khớp chuỗi bỏ dấu), xếp hạng: khớp nhiều từ >
    hàng lên-hình > ÍT dùng gần đây (kênh 10 video/ngày mà tấm nào cũng lặp là người
    xem ngán + YouTube đánh trùng) > mới nhập."""
    if not os.path.exists(SO_CHU_THE) or not _bo_dau_k(q).strip():
        return []
    ra = []
    for dong in open(SO_CHU_THE, encoding="utf-8"):
        try:
            m = json.loads(dong)
        except Exception:
            continue
        khop = _diem_khop(q, [(m.get("chu_the", ""), 3),
                              (" ".join(m.get("nhan", [])), 2),
                              (m.get("mo_ta", ""), 1)])
        if not khop:
            continue
        diem = khop + (5 if m.get("hang") == "len_hinh" else 0) \
            - min(len(m.get("da_dung", [])), 5) * 2
        ra.append((diem, khop, m))
    ra.sort(key=lambda x: (-x[0], x[2].get("luc_nhap", "")))
    ket = []
    for diem, khop, m in ra[:toi_da]:
        w, h = 0, 0
        try:
            w, h = (int(x) for x in m.get("kich_thuoc", "0x0").split("x"))
        except ValueError:
            pass
        ket.append({"tep": m["tep"], "u": "/kho-nha-anh/" + m["tep"],
                    "nhan": m.get("nhan", []), "chu_the": m.get("chu_the", ""),
                    "mo_ta": m.get("mo_ta", ""), "hang": m.get("hang", ""),
                    # điểm khớp THÔ (chưa cộng hạng/trừ đã-dùng) — máy gán nháp cần nó
                    # để đặt ngưỡng "khớp chắc mới nhận", bonus hạng không nói lên độ khớp
                    "khop": khop,
                    "w": w, "h": h, "da_dung": len(m.get("da_dung", []))})
    return ket


import chuan_ten as CT                                        # noqa: E402
_BO_GOP = CT.BoGopTen()


def _chuan_hoa_ct(ten):
    """KIỂM SOÁT TRÙNG chủ thể — từ 10/08 khuya trỏ về module chuan_ten DÙNG CHUNG
    với script nhập kho (não một nguồn). Nâng cấp so bản cũ: so tập-từ với MỌI TÊN
    đang sống trong sổ (không chỉ bảng) — "thành long" tự về "lê phạm thành long",
    gộp được là tự ghi bảng học vĩnh viễn; từ chặn U23/nữ/futsal không gộp."""
    return _BO_GOP.chuan(ten)


def _kho_nha_da_dung(ten, ma):
    """Ảnh kho được lấy về một bài → ghi vào da_dung (một lần mỗi bài) để máy xếp hạng
    biết đường xoay vòng, tránh lặp ảnh giữa các video liền nhau."""
    with KHOA:
        try:
            ds = [json.loads(l) for l in open(SO_CHU_THE, encoding="utf-8") if l.strip()]
        except Exception:
            return
        doi = False
        for m in ds:
            if m.get("tep") == ten and ma not in m.get("da_dung", []):
                m.setdefault("da_dung", []).append(ma)
                doi = True
        if doi:
            with open(SO_CHU_THE, "w", encoding="utf-8") as f:
                for m in ds:
                    f.write(json.dumps(m, ensure_ascii=False) + "\n")
# Việc anh đang mở trên trạm — tiện ích Chrome hỏi chỗ này để biết gửi ảnh về thư mục nào.
# GHI RA TỆP chứ không giữ trong bộ nhớ: trạm khởi động lại (em sửa mã, máy ngủ dậy…) mà quên
# mất việc đang mở thì tiện ích rơi về "việc đầu danh sách" — gửi ảnh nhầm kho, mà nhầm rất
# im lặng, tới lúc dựng video mới biết.
DANG_LAM_TEP = os.path.join(DD.MAY, "tram-dang-lam.txt")


def _dang_lam(dat=None):
    if dat is not None:
        open(DANG_LAM_TEP, "w", encoding="utf-8").write(dat)
        return dat
    try:
        ma_dl = open(DANG_LAM_TEP, encoding="utf-8").read().strip()
    except Exception:
        return ""
    # việc BỊ XOÁ thì đừng trỏ vào nữa — bản cũ vẫn trả mã chết, trang mở lên là 500
    # câm (bộ kiểm hồi quy bắt 11/08). Mốc là KỊCH BẢN chứ không phải thư mục: thư mục
    # có thể hồi sinh do một cú nhận ảnh lạc vào mã cũ mà bên trong rỗng ruột.
    if ma_dl and not os.path.exists(os.path.join(DD.VIEC, ma_dl, "kich-ban.json")):
        return ""
    return ma_dl
KHOA = threading.Lock()
VIEC_JOB_MA = {}     # job → mã bài (sổ riêng: dict job bị các bước ghi đè cả cục)
WM_KHOA = threading.Lock()   # MỘT tiến trình LaMa một lúc — bài học sập nguồn 10/08


# ── đọc thư mục việc ─────────────────────────────────────────────────────────
def _tach_cau(loi_binh):
    """Tách câu — phép tách khai MỘT chỗ ở `duong_dan.TACH_CAU_RE`, xưởng/gợi ý cùng dùng."""
    return [c.strip() for c in re.split(DD.TACH_CAU_RE, loi_binh or "") if c.strip()]


def _do_dai_giong(viec):
    g = os.path.join(viec, "giong.mp3")
    if not os.path.exists(g):
        return None
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", g], capture_output=True, text=True, timeout=20)
        return float(r.stdout.strip())
    except Exception:
        return None


def _moc_cau(cau, tong):
    """Giây kết thúc từng câu, chia theo tỉ lệ số tiếng — cùng phép tính với xưởng."""
    tong_tieng = sum(len(c.split()) for c in cau) or 1
    ra, cong = [], 0
    for c in cau:
        cong += len(c.split())
        ra.append(round(cong / tong_tieng * tong, 2))
    return ra


def _so_anh(viec):
    """Gom mọi thứ đã biết về từng tấm ảnh: nguồn, kích thước, cờ vàng."""
    ra = {}
    p = os.path.join(viec, "anh", "nguon-anh.json")            # sổ của lay_anh (JSON thường)
    if os.path.exists(p):
        try:
            d = json.load(open(p, encoding="utf-8"))
            for a in d.get("anh", []):
                ra["anh/" + a["tep"]] = a
        except Exception:
            pass
    p = os.path.join(viec, "anh", "so-gap.jsonl")              # sổ của gap_anh (JSONL)
    if os.path.exists(p):
        for dong in open(p, encoding="utf-8"):
            try:
                a = json.loads(dong)
                ra["anh/" + a["tep"]] = a
            except Exception:
                pass
    return ra


def _danh_sach_anh(viec):
    so = _so_anh(viec)
    try:
        c_hien = json.load(open(os.path.join(viec, "anh", "cach-hien.json"), encoding="utf-8"))
    except Exception:
        c_hien = {}
    p_lac = os.path.join(viec, "anh", "lac-de.json")
    lac = {}
    if os.path.exists(p_lac):
        try:
            lac = json.load(open(p_lac, encoding="utf-8"))
        except Exception:
            lac = {}
    ra = []
    for thu in THU_ANH:
        for p in sorted(glob.glob(os.path.join(viec, thu, "*.jpg"))):
            duong = f"{thu}/{os.path.basename(p)}"
            m = so.get(duong, {})
            co_goc = os.path.exists(os.path.join(viec, "anh", "_goc-crop",
                                                 os.path.basename(p)))
            try:
                w, h = Image.open(p).size
            except Exception:
                continue
            ra.append({"crop_goc": co_goc, "duong": duong, "w": w, "h": h, "ty_le": round(w / h, 2),
                       "bao": m.get("bao", ""), "url": m.get("url", ""),
                       "tu_khoa": m.get("tu_khoa", ""), "can_soi": m.get("can_soi", ""),
                       "dau_nguon": m.get("dau_nguon", ""), "canh_bao": m.get("canh_bao", ""),
                       "ten_goc": m.get("ten_goc", ""),
                       "cach_hien": c_hien.get(os.path.basename(p), ""),
                       "chua_soi": bool(m.get("chua_soi")),
                       "lac_de": bool(lac.get(os.path.basename(p), {}).get("lac_de")),
                       "vi_sao_lac": lac.get(os.path.basename(p), {}).get("vi_sao", ""),
                       "moi": os.path.getmtime(p)})
    ra.sort(key=lambda a: -a["moi"])                           # ảnh vừa gắp nằm trên đầu
    return ra


def _tim_hop(viec):
    """Video này đã đóng hộp vào kho thành phẩm trên Drive chưa?

    So bằng TIÊU ĐỀ trong `SO-VIDEO.jsonl`, không so tên thư mục: tên hộp bị cắt còn 44 ký tự
    nên so chuỗi rất dễ trượt — bản đầu báo "CHƯA vào kho" cho video đã nằm sẵn trong kho
    (phát hiện 05/08 khi đối chiếu với `don_kho.py`). Sổ mới là chỗ chép đúng tiêu đề.
    """
    try:
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    except Exception:
        return ""
    td = (kb.get("tieu_de") or "").strip().lower()
    p = os.path.join(DD.KHO_VIDEO, "SO-VIDEO.jsonl")
    # Sổ kho nằm TRÊN DRIVE — Drive tự cập nhật 07/08 rồi siết quyền, đọc là EPERM và cả
    # /api/viec chết 500 theo. Kho hỏng chỉ được phép làm mất chữ "đã vào kho", không được
    # kéo sập trạm: mọi thứ khác của trạm đều là dữ liệu local.
    try:
        if not td or not os.path.exists(p):
            return ""
        for dong in open(p, encoding="utf-8"):
            try:
                d = json.loads(dong)
            except Exception:
                continue
            if (d.get("tieu_de") or "").strip().lower() != td:
                continue
            hop = d.get("hop") or d.get("ma") or ""
            if os.path.isdir(os.path.join(DD.KHO_VIDEO, hop)):
                return hop
    except OSError:
        return ""
    return ""


def _duong_mo(ma, dich):
    """Thư mục cần mở trong Finder: hộp trong kho thành phẩm, hay thư mục việc trên ổ máy."""
    viec = os.path.join(DD.VIEC, ma)
    if dich == "hop":
        hop = _tim_hop(viec)
        return os.path.join(DD.KHO_VIDEO, hop) if hop else ""
    return viec


def _tin_video(viec):
    """Anh hỏi 05/08: "chạy rồi khi nào xong, báo về ở đâu?" — dựng xong lúc 01:24 mà anh không
    biết, vì trạm chỉ báo bằng dòng chữ nhỏ tự tắt sau 4 giây. Việc chạy 2 phút thì thông báo
    chớp nhoáng là vô dụng. Từ giờ trạng thái video nằm THƯỜNG TRỰC trên thanh đầu."""
    p = os.path.join(viec, "video.mp4")
    if not os.path.exists(p):
        return {"co": False}
    # Video xưởng dựng ra nằm trong THƯ MỤC VIỆC trên ổ máy. Nó chỉ sang kho thành phẩm
    # trên Drive khi chạy `buoc3_xepkho.py` — bước đóng gói 7 tệp để đăng. Anh hỏi 05/08:
    # "dựng xong lưu ở đâu, không thấy trong kho thành phẩm" — đúng, vì trạm chưa gọi bước đó.
    hop = _tim_hop(viec)
    return {"co": True, "mb": round(os.path.getsize(p) / 1e6, 1), "duong": p, "hop": hop,
            "luc": datetime.fromtimestamp(os.path.getmtime(p)).strftime("%d/%m %H:%M"),
            "moi_hon_duyet": os.path.getmtime(p) >= os.path.getmtime(
                os.path.join(viec, "anh", "ban-do-cau.json"))
            if os.path.exists(os.path.join(viec, "anh", "ban-do-cau.json")) else False}


def _nhap(viec):
    p = os.path.join(viec, "anh", "tram.json")
    if os.path.exists(p):
        try:
            d = json.load(open(p, encoding="utf-8"))
            # LỌC KHOÁ RÁC ngay cửa đọc: một bản giao diện lỗi từng ghi khoá "NaN" vào bản
            # đồ (07/08) → _duyet vỡ int('NaN'). Khoá theo-câu phải là SỐ; rác thì bỏ êm —
            # đọc là sạch, lần lưu kế tiếp tự ghi đè bản sạch.
            for tr in ("ban_do", "ghi_chu", "tu_khoa", "the_so", "anh_phu", "nhap",
                       "tu_khoa_phu", "ghi_chu_phu"):
                if isinstance(d.get(tr), dict):
                    d[tr] = {k: v for k, v in d[tr].items()
                             if str(k).lstrip("-").isdigit()}
            return d
        except Exception:
            pass
    return {"ban_do": {}, "ghi_chu": {}, "tu_khoa": {}, "tu_khoa_en": {},
            "tu_khoa_2": {}, "goi_y_xong": False}


def _ds_viec():
    ra = []
    # Kho việc xếp theo NGÀY (anh chốt 05/08): <ngày>/<video-N-chủ đề>.
    # Mã việc từ đây là ĐƯỜNG TƯƠNG ĐỐI, có dấu gạch chéo — giao diện phải
    # encodeURIComponent khi nhét vào URL, nếu không là vỡ đường.
    for d in sorted(glob.glob(os.path.join(DD.VIEC, "*", "*")), reverse=True):
        if not os.path.isdir(d):
            continue
        kb = os.path.join(d, "kich-ban.json")
        if not os.path.exists(kb):
            continue
        try:
            k = json.load(open(kb, encoding="utf-8"))
        except Exception:
            continue
        cau = _tach_cau(k.get("loi_binh", ""))
        nh = _nhap(d)
        ra.append({
            "ma": os.path.relpath(d, DD.VIEC), "tieu_de": k.get("tieu_de", ""),
            "so_cau": len(cau), "da_gan": len(nh.get("ban_do", {})),
            "so_anh": len(_danh_sach_anh(d)),
            "co_giong": os.path.exists(os.path.join(d, "giong.mp3")),
            "da_duyet": os.path.exists(os.path.join(d, "anh", "ban-do-cau.json")),
            "co_video": os.path.exists(os.path.join(d, "video.mp4")),
        })
    return ra


def _soi_canh_bao_nhip(cau, giay_tho, la_clip, ban_do_ten, a_phu, g_canh):
    """Soi trước khi chốt: quãng nào MỘT HÌNH đứng quá lâu, câu nào kẹt vụn cạnh clip.

    Viết lại 09/08 (anh bắt cảnh báo KÊU OAN): bản cũ dùng chia_nhip_theo_anh đời trước —
    không biết cảnh phụ, khung đôi, phép mượn giây — nên câu đã đủ hình vẫn bị kêu
    "một ảnh đứng suốt". Bản này tính đúng theo hệ hiện tại:
      · câu có ảnh PHỤ dùng được / KHUNG ĐÔI bật / là CLIP → coi như có đổi hình;
      · các câu liên tiếp dùng CÙNG một ảnh (kế thừa) mà không đổi hình → cộng quãng;
      · quãng một-hình > 6 giây mới cảnh báo, kèm mốc giây THEO NHỊP đã co giãn.
    Hàm thuần — không đọc đĩa, không ghi gì — để test được bằng dữ liệu thật."""
    nhip2 = NC.chia_nhip(giay_tho, la_clip)
    n = len(cau)
    anh_hl, dang = [], None
    for i in range(n):
        if str(i) in ban_do_ten:
            dang = ban_do_ten[str(i)]
        anh_hl.append(dang)
    doi_hinh = []
    for i in range(n):
        phu_ok = len([v for v in (a_phu.get(str(i)) or []) if v])
        gc = (g_canh.get(str(i)) or {}).get("c") or {}
        co_ghep = bool(gc.get("anh2")) and not gc.get("tat")
        doi_hinh.append(la_clip[i] or phu_ok > 0 or co_ghep)
    moc2 = []
    chay = 0.0
    for i in range(n):
        moc2.append((chay, chay + nhip2[i]["dai"]))
        chay += nhip2[i]["dai"]
    ra = []
    i = 0
    while i < n:
        if la_clip[i] or doi_hinh[i] or not anh_hl[i]:
            i += 1
            continue
        j = i
        while (j + 1 < n and not la_clip[j + 1] and not doi_hinh[j + 1]
               and anh_hl[j + 1] == anh_hl[i]):
            j += 1
        b, k = moc2[i][0], moc2[j][1]
        if k - b > 6.0:
            ra.append(f"đoạn {b:.1f}s–{k:.1f}s ({k - b:.0f} giây, câu {i + 1}"
                      + (f"–{j + 1}" if j > i else "")
                      + ") chỉ có MỘT hình đứng suốt — nên gán thêm ảnh phụ hoặc bật khung đôi")
        i = j + 1
    for i in range(n):
        if not la_clip[i] and nhip2[i]["dai"] < 2.35 and any(la_clip):
            ra.append(f"câu {i + 1} chỉ {nhip2[i]['dai']:.1f}s kẹt cạnh cảnh clip "
                      "— sẽ bị gộp vào cảnh kề")
    return ra


def _chi_tiet(ma):
    viec = os.path.join(DD.VIEC, ma)
    if not os.path.exists(os.path.join(viec, "kich-ban.json")):
        # nói THẲNG là không còn việc này, đừng ném 500 câm (bài học 11/08)
        return {"loi": f"không còn việc {ma} — chọn việc khác ở ô trên cùng"}
    k = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    cau = _tach_cau(k.get("loi_binh", ""))
    tong = _do_dai_giong(viec) or round(sum(len(c.split()) for c in cau) / TIENG_MOT_PHUT * 60, 1)
    moc = _moc_cau(cau, tong)
    nh = _nhap(viec)
    # NHỊP HIỂN THỊ = NHỊP XƯỞNG SẼ DỰNG (module nhip_canh dùng chung — anh bắt 09/08:
    # trạm chia đều thô nên cảnh 0,9s trơ trọi, ô phụ ẩn; giờ trạm cho xem đúng phép
    # mượn/chia mà xưởng sẽ làm: câu ngắn được kéo đủ 2,5s, câu cho mượn hiện phần còn lại)
    clip_c = _doc_clip_canh(viec)
    giay_tho = [(moc[i] - (moc[i - 1] if i else 0.0)) for i in range(len(cau))]
    # số ảnh PHỤ đã gán → nhịp mở đủ ô (anh chốt 13/08: cảnh 9 có 1 chính + 2 phụ thì
    # phải chia 3 khung, kể cả khi cảnh dùng clip). Trạm và xưởng cùng truyền tham số
    # này nên hai bên vẫn khớp từng ô.
    _ap = nh.get("anh_phu") or {}
    so_phu_c = [len([x for x in (_ap.get(str(i)) or []) if x]) for i in range(len(cau))]
    nhip = NC.chia_nhip(giay_tho, [str(i) in clip_c for i in range(len(cau))], so_phu_c)
    ds, chay = [], 0.0
    for i, c in enumerate(cau):
        d_i = nhip[i]["dai"]
        ds.append({"i": i, "chu": c, "tieng": len(c.split()),
                   "tu": round(chay, 1), "den": round(chay + d_i, 1),
                   "so_phan": nhip[i]["so_phan"], "muon": nhip[i]["muon"]})
        chay += d_i
    return {"ma": ma, "tieu_de": k.get("tieu_de", ""), "tu_khoa_kb": k.get("tu_khoa", []),
            # cửa duyệt LỜI gộp vào trạm 06/08 — giao diện cần nguyên văn lời để anh sửa
            "loi_binh": k.get("loi_binh", ""),
            "da_duyet_loi": k.get("da_duyet_loi", ""),
            "nguon_tin": k.get("nguon_tin", ""), "tin_goc": k.get("tin_goc", ""),
            "tong_giay": round(tong, 1), "giong_that": _do_dai_giong(viec) is not None,
            "cau": ds, "anh": _danh_sach_anh(viec),
            "clip": _danh_sach_clip(viec),
            "clip_canh": _doc_clip_canh(viec),
            "clip_doan": _doc_clip_doan(viec),
            "ban_do": nh.get("ban_do", {}), "ghi_chu": nh.get("ghi_chu", {}),
            "anh_phu": nh.get("anh_phu", {}),
            "lat_anh": nh.get("lat_anh", {}),
            "ghep_canh": nh.get("ghep_canh", {}),
            "tu_khoa": nh.get("tu_khoa", {}), "goi_y_xong": nh.get("goi_y_xong", False),
            # từ khoá TIẾNG ANH + góc phụ — trang cần để hiện và để tìm lại (14/08)
            "tu_khoa_en": nh.get("tu_khoa_en", {}), "tu_khoa_2": nh.get("tu_khoa_2", {}),
            "tu_khoa_nguoi": nh.get("tu_khoa_nguoi", {}),
            "nhap": nh.get("nhap", {}),
            "tu_khoa_phu": nh.get("tu_khoa_phu", {}),
            "ghi_chu_phu": nh.get("ghi_chu_phu", {}),
            "the_so": nh.get("the_so", {}),
            "video": _tin_video(viec),
            "da_duyet": os.path.exists(os.path.join(viec, "anh", "ban-do-cau.json")),
            # Gộp hai nút "chốt & dựng" và "dựng lại" làm một (anh chốt 06/08): máy tự biết
            # bản đồ ảnh có đổi kể từ lần chốt hay không, việc gì bắt anh nhớ mà chọn nút.
            # Khớp  → dựng thẳng, khỏi chạy lại cổng QC watermark cho mất công.
            # Lệch → phải chốt lại rồi mới dựng.
            "chot_khop": _chot_khop(viec, nh.get("ban_do", {}))}


def _chot_khop(viec, ban_do):
    """Bản đồ ảnh đang gán có khớp bản đã chốt lần trước không."""
    p = os.path.join(viec, "anh", "ban-do-cau.json")
    if not os.path.exists(p):
        return False
    try:
        chot = json.load(open(p, encoding="utf-8"))
    except Exception:
        return False
    # ban-do-cau.json khai theo {chỉ số câu → tên ảnh}, câu chưa khai thì kế thừa câu trước,
    # nên chỉ so những câu CÓ khai ở cả hai bên.
    return {str(k): os.path.basename(str(v)) for k, v in chot.items()} == \
           {str(k): os.path.basename(str(v)) for k, v in ban_do.items() if v}


# ── lưu & duyệt ──────────────────────────────────────────────────────────────
def _gop_the(cu, moi):
    """Gộp thẻ số liệu, KHÔNG để trang cũ xoá mất thẻ máy vừa gợi (vá 06/08).

    Chuyện đã xảy ra: anh mở trạm, để đó; máy chạy gợi ý ghi hai thẻ mới vào đĩa; trang đang
    mở không biết nên vẫn giữ bản cũ trong bộ nhớ, và lần tự lưu kế tiếp nó đè sạch.
    Cách vá: thẻ mang cờ `goi_y` (máy đề xuất, anh chưa xem) thì KHÔNG cho client xoá —
    chỉ anh bấm ✕ mới xoá được, mà lúc ấy client gửi kèm cờ `bo_the` cho từng câu.
    Thẻ anh đã chốt (không còn cờ goi_y) thì client toàn quyền, vì đó là bản anh cầm.
    """
    if moi is None:                       # trang cũ không biết trường này → giữ nguyên
        return cu
    ra = dict(moi)
    for k, v in (cu or {}).items():
        if k not in ra and v.get("goi_y") and not v.get("bo_the"):
            ra[k] = v                     # thẻ máy gợi mà client chưa biết → giữ lại
    return ra


SO_HOC_TK = os.path.join(DD.MAY, "hoc", "sua-tu-khoa.jsonl")
SO_TIM_OK = os.path.join(DD.MAY, "hoc", "tim-anh-thanh-cong.jsonl")


def _ghi_tim_ok(ma, tu_khoa, so_lay, nguon):
    """Ghi TỪ KHOÁ ANH GÕ MÀ TÌM RA ẢNH DÙNG ĐƯỢC (anh chốt 06/08 tối).

    Anh phàn nàn: máy gợi từ khoá chưa trúng, anh phải tự gõ tìm lại nhiều. Mỗi lần anh tự
    tìm rồi LẤY ảnh về là một mẫu vàng — từ khoá đó chứng minh ra ảnh thật. Gom đủ vài chục
    mẫu là goi_y.py học được kiểu gõ của anh (nó đọc sổ này mỗi lần gợi).
    Hai nguồn cùng chảy vào đây: ô tìm trên trạm, và extension Sóc (địa chỉ trang Google
    có sẵn từ khoá trong tham số q)."""
    tu_khoa = (tu_khoa or "").strip()
    if not tu_khoa or so_lay <= 0:
        return
    os.makedirs(os.path.dirname(SO_TIM_OK), exist_ok=True)
    with open(SO_TIM_OK, "a", encoding="utf-8") as f:
        f.write(json.dumps({"luc": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "viec": ma, "tu_khoa": tu_khoa, "so_lay": so_lay,
                            "nguon": nguon}, ensure_ascii=False) + "\n")


def _ghi_hoc_tu_khoa(viec, ma, tk_moi):
    """Anh sửa từ khoá nào thì ghi lại, để lần sau máy gợi đỡ sai (anh chốt 06/08).

    Anh giữ cửa người ở khâu này — anh muốn tự soi từ khoá trước khi cho tải ảnh. Nhưng cửa
    người mà máy không học thì mãi mãi nặng như nhau. Ghi lại "máy gợi X, anh đổi thành Y"
    là cách duy nhất để đến ngày anh gần như không phải sửa nữa.

    Bản máy gợi được đóng băng ở `anh/goi-y-goc.json` ngay lần gợi đầu — không có mốc gốc
    thì sửa vài lượt là không ai biết máy gợi ra sao nữa.
    """
    p_goc = os.path.join(viec, "anh", "goi-y-goc.json")
    if not os.path.exists(p_goc):
        return
    try:
        goc = json.load(open(p_goc, encoding="utf-8")).get("tu_khoa", {})
    except Exception:
        return
    doi = []
    for k, v in (tk_moi or {}).items():
        cu = (goc.get(k) or "").strip()
        moi = (v or "").strip()
        if cu and moi and cu != moi:
            doi.append({"cau": int(k), "may_goi": cu, "anh_sua": moi})
    if not doi:
        return
    os.makedirs(os.path.dirname(SO_HOC_TK), exist_ok=True)
    with open(SO_HOC_TK, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "luc": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "viec": ma, "so_doi": len(doi), "doi": doi,
        }, ensure_ascii=False) + "\n")


def _giu_neu_quet_trang(khoa, d, cu):
    """Trường dict: client gửi RỖNG mà bản cũ có ≥2 mục → nghi trang nạp hụt, giữ bản cũ.
    (Người thật bỏ từng chiếc một nên mỗi cú lưu chỉ giảm dần, không về 0 một phát.)"""
    moi = d.get(khoa, cu.get(khoa, {}))
    if not moi and len(cu.get(khoa) or {}) >= 2:
        print(f"  ⚠ chặn cú lưu quét trắng {khoa} — giữ bản cũ")
        return cu.get(khoa, {})
    return moi


def _thu_giong(than):
    """THỬ MỘT MÃ GIỌNG VBee trước khi anh lưu vào danh sách.

    Gõ sai mã giọng thì cả mẻ video hỏng mà mãi mới biết — nên phải thử được TRƯỚC.
    Dùng lại đúng đường gọi của xưởng (`xuong.doc_giong`) chứ không viết luồng song song:
    một bản, sai thì sai cùng chỗ, sửa một lần ăn cả hai.
    """
    ma = str(than.get("ma") or "").strip()
    if not ma:
        return {"ok": False, "loi": "chưa nhập mã giọng"}
    toc = than.get("toc_do") or 1.1
    out = os.path.join(tempfile.gettempdir(), f"thu-giong-{abs(hash(ma)) % 99999}.mp3")
    try:
        XU.doc_giong("Xin chào, đây là giọng thử của kênh Sóc Bóng Đá 247.", out,
                     toc_do=toc, ma_giong=ma)
    except SystemExit as e:                     # doc_giong dùng sys.exit khi VBee từ chối
        return {"ok": False, "loi": str(e)[:160]}
    except Exception as e:
        return {"ok": False, "loi": f"{type(e).__name__}: {str(e)[:150]}"}
    if not os.path.exists(out) or os.path.getsize(out) < 4096:
        return {"ok": False, "loi": "VBee trả file rỗng — mã giọng nhiều khả năng không đúng"}
    return {"ok": True, "giay": round(_do_dai_mp3(out), 1),
            "nghe": "/thu-giong.mp3?ma=" + urllib.parse.quote(ma)}


def _do_dai_mp3(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _phong_cach_thu(cau_hinh):
    """XEM TRƯỚC cho trang phong cách — KHÔNG lưu gì.

    Anh chốt 12/08: mỗi núm MỘT chỉ số, nên bảng không còn để so 6 video khác nhau nữa.
    Việc còn lại của nó: soi xem giọng nào sẽ đọc bài nào (khi anh bật nhiều giọng), và
    nói thẳng nếu cấu hình có chỗ đáng ngờ.
    """
    goc = PC.TEP
    tam = goc + ".thu"
    ds = []
    try:
        PC.ghi.__globals__["TEP"] = tam        # ghi ra file tạm, KHÔNG đụng cấu hình thật
        PC.doc.__globals__["TEP"] = tam
        PC.ghi(cau_hinh or {})
        for i in range(1, 7):
            t = PC.cho_video(f"2026-08-12/video-{i}-thu")
            ds.append({"ten": f"video {i}", "giong_ten": t["giong_ten"],
                       "giong_toc_do": t["giong_toc_do"],
                       "nhac_nhom": t["nhac_nhom"]})
    finally:
        PC.ghi.__globals__["TEP"] = goc
        PC.doc.__globals__["TEP"] = goc
        if os.path.exists(tam):
            os.remove(tam)

    c = PC.chuan(cau_hinh or {})
    canh = []
    if c["nhac_am_luong"] > 0.16:
        canh.append("nhạc <b>{:.2f}</b> là to — dễ lấn lời bình".format(c["nhac_am_luong"]))
    if c["giong_vao"] > 0.15:
        canh.append("giọng to dần <b>{}s</b> — chữ ĐẦU sẽ bị hạ âm lượng rõ; "
                    "câu đầu của kênh là đọc lại tiêu đề, để 0,05 thôi"
                    .format(c["giong_vao"]))
    if c["lech_tam"] == 0:
        canh.append("lệch tâm <b>0</b> — video nào cũng phóng từ chính giữa")
    n_giong = len([g for g in c["giong_ds"] if g.get("bat")])
    dg = ("⚠ " + " · ".join(canh)) if canh else "✅ Cấu hình không có chỗ nào đáng ngại."
    dg += (f"<br>🎙 <b>{n_giong}</b> giọng đang bật"
           + (" — mỗi video rút một giọng, xem bảng trên." if n_giong > 1
              else " — mọi video cùng một giọng."))
    return {"ds": ds, "danh_gia": dg}


def _luu_nhap(ma, d):
    viec = os.path.join(DD.VIEC, ma)
    os.makedirs(os.path.join(viec, "anh"), exist_ok=True)
    cu = _nhap(viec)
    # TRƯỜNG THIẾU thì KẾ THỪA bản cũ — client chỉ muốn lưu một thứ (vd từ khoá) không được
    # phép vô tình đè trắng thứ khác. Và CHẶN XOÁ-TRẮNG-MỘT-PHÁT: 16:44 07/08 một trang nạp
    # hụt dữ liệu (trạm đang khởi động lại) đã gửi ban_do RỖNG đè mất 20 câu anh vừa gán —
    # bỏ gán hợp lệ chỉ đi từng chiếc, không bao giờ cả bản đồ về 0 trong một cú lưu.
    bd = d.get("ban_do", cu.get("ban_do", {}))
    if not bd and len([v for v in (cu.get("ban_do") or {}).values() if v]) >= 2:
        print(f"  ⚠ chặn cú lưu xoá trắng ban_do của {ma} — giữ bản cũ")
        bd = cu.get("ban_do", {})
    ra = {"ban_do": bd,
          "ghi_chu": d.get("ghi_chu", cu.get("ghi_chu", {})),
          "tu_khoa": d.get("tu_khoa", cu.get("tu_khoa", {})),
          # từ khoá TIẾNG ANH cho từng câu (anh chốt 14/08 — ảnh báo chí Anh ngữ đẹp
          # hơn hẳn). Phải khai ở đây, không thì lưu xong MẤT (luật whitelist).
          "tu_khoa_en": d.get("tu_khoa_en", cu.get("tu_khoa_en", {})),
          # câu nào từ khoá do ANH dán từ GPT — máy không được đè (14/08)
          "tu_khoa_nguoi": d.get("tu_khoa_nguoi", cu.get("tu_khoa_nguoi", {})),
          "tu_khoa_2": d.get("tu_khoa_2", cu.get("tu_khoa_2", {})),
          # Thẻ số liệu chồng lên cảnh (anh chốt 06/08) — {chỉ số câu: {nhan,so,donvi,dong1,dong2}}
          "the_so": _gop_the(cu.get("the_so", {}), d.get("the_so")),
          # ảnh phụ tách cảnh dài — client cũ không biết trường này thì KẾ THỪA bản cũ,
          # đừng để trang đang mở đè mất (cùng bài học với the_so 06/08)
          "anh_phu": d.get("anh_phu", cu.get("anh_phu", {})),
          # lật (sổ ghi ô BẬT true — anh đổi 09/08) + khung đôi {câu: {ô: {anh2, dao, tat}}}.
          # Cùng phanh chống XOÁ-TRẮNG như ban_do: trang nạp hụt (trạm đang khởi động lại)
          # gửi sổ rỗng không được phép quét sạch cấu hình anh đã đặt — bỏ hợp lệ chỉ đi
          # từng chiếc một (bài học mất 20 câu 07/08).
          "lat_anh": _giu_neu_quet_trang("lat_anh", d, cu),
          "ghep_canh": _giu_neu_quet_trang("ghep_canh", d, cu),
          # cờ ◌ NHÁP máy gán (Phương án ① — anh duyệt 10/08): {câu: {nguon, go?, mat?}}
          "nhap": d.get("nhap", cu.get("nhap", {})),
          # TỪ KHOÁ + GHI CHÚ RIÊNG CHO Ô PHỤ (anh chốt 11/08 — "cảnh phụ có mọi chức
          # năng như cảnh chính"): {câu: {ô: "..."}}. Cảnh phụ cùng thoại nhưng phải
          # ĐỔI HÌNH, nên nó cần từ khoá tìm ảnh khác hẳn cảnh chính.
          "tu_khoa_phu": d.get("tu_khoa_phu", cu.get("tu_khoa_phu", {})),
          "ghi_chu_phu": d.get("ghi_chu_phu", cu.get("ghi_chu_phu", {})),
          "goi_y_xong": d.get("goi_y_xong", cu.get("goi_y_xong", False)),
          "cap_nhat": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    p_chinh = os.path.join(viec, "anh", "tram.json")
    if os.path.exists(p_chinh):                    # phao: luôn giữ bản NGAY TRƯỚC đó
        try:
            shutil.copy2(p_chinh, p_chinh + ".truoc")
        except OSError:
            pass
    json.dump(ra, open(p_chinh, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    _ghi_hoc_tu_khoa(viec, ma, ra["tu_khoa"])
    return ra


SO_HOC = os.path.join(DD.MAY, "hoc", "sua-loi.jsonl")


def _luu_loi(ma, tieu_de, loi_binh, duyet=False):
    """Lưu lời bình anh sửa trên trạm — VÀ ghi lại ANH ĐÃ SỬA GÌ.

    Anh chốt 06/08: gộp duyệt lời vào chung trạm này, không dựng trạm riêng.

    Phần ghi lại mới là thứ đáng giá nhất. Skill `soc-content` viết ra bản đầu, anh sửa câu
    chữ, so hai bản là ra bài học. Trước 06/08 không có trạm nên vòng này ĐỨT hẳn — máy viết
    bao nhiêu lần cũng không biết mình sai chỗ nào, anh phải sửa đi sửa lại cùng một lỗi.

    Bản máy viết được giữ nguyên ở `kich-ban-goc.json` ngay lần sửa đầu, để về sau còn đối
    chiếu. Không có mốc gốc thì sửa vài lượt là không ai biết máy viết ra sao nữa.
    """
    viec = os.path.join(DD.VIEC, ma)
    p_kb = os.path.join(viec, "kich-ban.json")
    if not os.path.exists(p_kb):
        return {"loi": "chưa có kịch bản cho việc này"}
    kb = json.load(open(p_kb, encoding="utf-8"))

    p_goc = os.path.join(viec, "kich-ban-goc.json")
    if not os.path.exists(p_goc):          # lần sửa đầu: đóng băng bản máy viết làm mốc
        json.dump(kb, open(p_goc, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    goc = json.load(open(p_goc, encoding="utf-8"))

    doi = (tieu_de.strip() != (kb.get("tieu_de") or "").strip()
           or loi_binh.strip() != (kb.get("loi_binh") or "").strip())
    # SEO giờ sinh SONG SONG lúc dựng (anh chốt 12/08) nên nó chốt theo TÍT lúc ấy.
    # Anh bảo sau khi bấm dựng "cùng lắm chỉ sửa nội dung, SEO thường giữ nguyên" —
    # nên CHỈ khi TIÊU ĐỀ đổi mới gỡ SEO để lần dựng sau sinh lại; sửa lời thì giữ
    # (thẻ tag bám tên riêng trong tít là chính, lời đổi vài câu không làm lệch).
    doi_tit = bool(tieu_de.strip()) and tieu_de.strip() != (kb.get("tieu_de") or "").strip()
    if doi_tit:
        kb.pop("tu_khoa", None)
        kb.pop("binh_luan_ghim", None)
        kb.pop("hashtag_seo", None)
    if tieu_de.strip():
        kb["tieu_de"] = tieu_de.strip()
    kb["loi_binh"] = loi_binh.strip()
    kb["so_tieng_thuc"] = len(kb["loi_binh"].split())
    # 258 tiếng/phút — giọng VBee Ngọc Huyền tốc độ 1.1, đo 05/08. Khai một chỗ ở đây thôi.
    kb["giay_uoc"] = round(kb["so_tieng_thuc"] * 60 / 258, 1)
    kb["nguoi_sua"] = True
    if doi:
        kb.pop("da_soat_chinh_ta", None)   # lời đổi rồi thì kết quả soát cũ hết giá trị
        # Cụm tô vàng phải SỐNG THEO TÍT MỚI (lỗi 06/08 tối: anh sửa "ĐÁP LẠI BA CHỮ" thành
        # "ĐÁP LẠI CỰC GỌN", cụm cũ không còn trong tít → cả tít trắng trơn không ai biết vì sao).
        # So mờ bỏ dấu câu — "HÌNH B," vẫn khớp cụm "HÌNH B".
        def _sachtu(t):
            return re.sub(r"^[^\wÀ-ỹ]+|[^\wÀ-ỹ]+$", "", t.upper())
        tit_tu = [_sachtu(t) for t in kb.get("tieu_de", "").split()]
        con = []
        for cum in kb.get("cum_to_vang", []) or []:
            ct = [_sachtu(x) for x in cum.split()]
            if ct and any(tit_tu[i:i + len(ct)] == ct
                          for i in range(len(tit_tu) - len(ct) + 1)):
                con.append(cum)
        kb["cum_to_vang"] = con              # rỗng thì bước sau duyệt sẽ chọn lại
    if duyet:
        kb["da_duyet_loi"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json.dump(kb, open(p_kb, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # Sửa lời thì SỐ CÂU đổi theo — phải dọn bản đồ ảnh cho khớp.
    # Lỗi 06/08: anh cắt lời từ 24 câu xuống 22, bản đồ vẫn giữ gán cho câu 22 và 23 đã biến
    # mất, trạm hiện "23/22 câu đã gán" — số đã gán lớn hơn tổng số câu.
    so_cau = len(_tach_cau(kb["loi_binh"]))
    nh = _nhap(viec)
    bo = [k for k in nh.get("ban_do", {}) if int(k) >= so_cau]
    canh_bao = ""
    if bo:
        for k in bo:
            nh["ban_do"].pop(k, None)
            nh.get("ghi_chu", {}).pop(k, None)
            nh.get("tu_khoa", {}).pop(k, None)
            nh.get("anh_phu", {}).pop(k, None)
        _luu_nhap(ma, nh)
        canh_bao = f"lời ngắn lại còn {so_cau} câu — đã bỏ {len(bo)} ảnh gán cho câu không còn nữa"

    if doi or duyet:                        # ghi sổ học — skill soc-content đọc file này
        os.makedirs(os.path.dirname(SO_HOC), exist_ok=True)
        with open(SO_HOC, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "luc": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "viec": ma,
                "tieu_de_may": goc.get("tieu_de", ""),
                "tieu_de_anh": kb.get("tieu_de", ""),
                "loi_may": goc.get("loi_binh", ""),
                "loi_anh": kb.get("loi_binh", ""),
                "tieng_may": len((goc.get("loi_binh") or "").split()),
                "tieng_anh": kb["so_tieng_thuc"],
                "da_duyet": bool(duyet),
            }, ensure_ascii=False) + "\n")
    return {"ok": True, "so_tieng": kb["so_tieng_thuc"], "giay_uoc": kb["giay_uoc"],
            "da_duyet_loi": kb.get("da_duyet_loi", ""), "co_doi": doi,
            "so_cau": so_cau, "canh_bao": canh_bao}


def _tim_san(ma, chi_cau=None, bao_tien=None, chi_thieu=False, tk_ep=None):
    """TÌM SẴN ảnh cho từng câu, cache vào anh/ung-vien.json (anh chốt 06/08 tối).

    Nỗi đau: mỗi lượt tìm Google mất ~6 giây, hai chục câu là anh ngồi chờ cả buổi —
    "mỗi cảnh a phải enter đi tìm soi chờ mất thời gian quá". Nay máy tìm hết MỘT LƯỢT
    ngay sau Duyệt lời (lúc anh còn đang đọc), trang chọn ảnh mở ra là ứng viên nằm sẵn.
    Giữ tối đa 40 ứng viên mỗi câu; trùng url giữa các câu thì câu trước giữ, câu sau bỏ
    (đỡ bày một tấm hai nơi). chi_cau=N để tìm lại RIÊNG một câu (nút Tìm lại).
    """
    viec = os.path.join(DD.VIEC, ma)
    p_uv = os.path.join(viec, "anh", "ung-vien.json")
    cache = {}
    if os.path.exists(p_uv):
        try:
            cache = json.load(open(p_uv, encoding="utf-8"))
        except Exception:
            cache = {}
    nh = _nhap(viec)
    tk = {int(k): v for k, v in nh.get("tu_khoa", {}).items() if (v or "").strip()}
    if chi_cau is not None:
        # tk_ep: TỪ KHOÁ RIÊNG của ô phụ (anh chốt 11/08) — tìm cho ô phụ thì đừng
        # dùng từ khoá của câu, cảnh phụ cần hình KHÁC hẳn cảnh chính
        if (tk_ep or "").strip():
            tk = {int(chi_cau): tk_ep.strip()}
        else:
            tk = {int(chi_cau): tk.get(int(chi_cau), "")} if tk.get(int(chi_cau)) else {}
    thay = set()
    if chi_thieu:
        # Anh chốt 06/08 tối: mở trang chọn giữa chừng thì CHỈ tự tìm cho cảnh CHƯA GÁN
        # và chưa có ứng viên — cảnh đã gán hay đã có cache thì để yên (muốn thì Tìm lại tay).
        da_gan = {int(k) for k in nh.get("ban_do", {}) if nh["ban_do"].get(k)}
        tk = {i: v for i, v in tk.items()
              if i not in da_gan and not (cache.get(str(i), {}).get("anh"))}
        for v in cache.values():                 # ảnh đã nằm ở cache cũ thì đừng bày trùng
            for a in v.get("anh", []):
                thay.add(a["u"])
    elif chi_cau is not None:                    # tìm lại 1 câu: đừng coi ảnh câu khác là trùng
        pass
    else:
        cache = {}                               # tìm cả bài: làm mới toàn bộ
    n, tong = 0, len(tk)
    import random as _rd
    for i in sorted(tk):
        n += 1
        if bao_tien:
            bao_tien(f"tìm sẵn ảnh — câu {i + 1} ({n}/{tong})", n, tong)
        if n > 1:
            time.sleep(_rd.uniform(2.5, 6.0))      # giãn nhịp người thật — Google nghi máy
        try:
            r = gap_anh.xem_truoc(tk[i])
            # ── QUÉT THÊM BẰNG TIẾNG ANH (anh chốt 14/08) ────────────────────
            # Anh đo thật: từ khoá tiếng Anh ra ảnh ưng ý hơn hẳn, vì ảnh báo chí
            # thể thao chất lượng cao (Getty/AFP/Reuters, báo Anh ngữ) gắn chú
            # thích tiếng Anh — tìm tiếng Việt là chỉ quét được báo Việt.
            # Gộp hai rổ, tiếng Việt đứng trước (sát nội dung câu hơn), tiếng Anh
            # bù phần ảnh đẹp. Trùng URL thì bỏ.
            tk_en = (nh.get("tu_khoa_en") or {}).get(str(i), "").strip()
            if tk_en and not tk_ep:
                time.sleep(_rd.uniform(2.0, 4.5))
                try:
                    r_en = gap_anh.xem_truoc(tk_en)
                    if not (r_en.get("loi") or "").startswith("CAPTCHA"):
                        co = {a["u"] for a in r.get("anh", [])}
                        r["anh"] = list(r.get("anh", [])) + [
                            a for a in r_en.get("anh", []) if a["u"] not in co]
                        r["tu_khoa_en"] = tk_en
                except Exception:
                    pass                          # tiếng Anh hỏng thì vẫn còn rổ Việt
        except Exception as e:
            cache[str(i)] = {"tu_khoa": tk[i], "anh": [], "loi": str(e)}
            continue
        if "CAPTCHA" in (r.get("loi") or ""):
            # DỪNG CẢ LOẠT ngay — 07/08 tối máy đập 10 câu liên tiếp vào tường CAPTCHA,
            # Google càng khoá gắt. Các câu còn lại ghi rõ lý do để trang chọn hiện đúng.
            for j in sorted(tk):
                if str(j) not in cache or not cache.get(str(j), {}).get("anh"):
                    cache[str(j)] = {"tu_khoa": tk[j], "anh": [],
                                     "loi": "DỪNG loạt vì Google hỏi CAPTCHA — giải ở cửa "
                                            "sổ Chrome trạm rồi bấm tìm lại"}
            break
        ds = []
        for a in r.get("anh", []):
            if a["u"] in thay:
                continue
            thay.add(a["u"])
            ds.append(a)
            if len(ds) >= 60:           # hai rổ (Việt + Anh) nên nới trần từ 40
                break
        cache[str(i)] = {"tu_khoa": tk[i], "anh": ds, "loi": r.get("loi", ""),
                         **({"tu_khoa_en": r["tu_khoa_en"]} if r.get("tu_khoa_en") else {}),
                         "luc": datetime.now().strftime("%H:%M:%S")}
    os.makedirs(os.path.dirname(p_uv), exist_ok=True)
    json.dump(cache, open(p_uv, "w", encoding="utf-8"), ensure_ascii=False)
    return cache


def _chay_tim_san_job(ma_job, ma, chi_cau=None, chi_thieu=False, tk_ep=None):
    def bao(buoc, da, tong):
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": False, "buoc": buoc, "da": da, "tong": tong}
    try:
        c = _tim_san(ma, chi_cau, bao, chi_thieu, tk_ep)
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True,
                                "tong_anh": sum(len(v.get("anh", [])) for v in c.values())}
    except Exception as e:
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "loi": str(e)}


CONG = 8756          # main() ghi đè theo --cong — luồng nháp cần biết cổng để tự gọi mình


_VT_KHO = {"mtime": 0, "ds": []}


def _trung_kho(duong_anh):
    """QUY TẮC ANH ĐẶT 11/08: máy KHÔNG được tải về tấm đã có trong kho chung.

    So vân tay ảnh vừa tải với van-tay.json của kho chủ thể (cùng phép dhash + ngưỡng
    6 bit như gap_anh, nên cùng thước đo). Chỉ áp cho MÁY tự tải — anh chọn tay thì
    không chặn, vì đó là quyết định của người."""
    p_vt = os.path.join(KHO_CHU_THE, "van-tay.json")
    try:
        mt = os.path.getmtime(p_vt)
    except OSError:
        return False
    if mt != _VT_KHO["mtime"]:
        try:
            _VT_KHO.update(mtime=mt,
                           ds=[int(v) for v in json.load(open(p_vt)).values()])
        except Exception:
            return False
    try:
        from PIL import Image as _ImV
        h = gap_anh._dhash(_ImV.open(duong_anh))
    except Exception:
        return False
    return any(bin(h ^ cu).count("1") <= 6 for cu in _VT_KHO["ds"])


def _gan_nhap_lo(ma, bao_tien=None):
    """PHƯƠNG ÁN ① (anh duyệt 10/08): máy GÁN NHÁP mọi câu còn trống — anh chỉ duyệt.

    Thứ tự nguồn cho từng câu: ① KHO NHÀ (nhãn mắt máy đã qua soát sonnet — chỉ nhận tấm
    khớp CHẮC, khop ≥ 4 tức trúng chủ thể + thêm một vế) → ② ứng viên Google đã tìm sẵn
    (ung-vien.json, thử lần lượt 3 tấm đầu). Cả hai đường đều đi qua gap_anh.lay_theo_url
    — MỘT cửa nhận ảnh duy nhất: vân tay chống trùng, thumbnail, sổ gắp, cổng watermark
    đều tự có, không mở lối riêng nào cho máy cả.

    Cảnh máy gán mang cờ ◌ trong sổ `nhap` {câu: {nguon: kho|web|thieu}} — trạm hiện
    viền cam, anh ✓ nhận hoặc đổi ảnh; anh đụng tay vào câu nào cờ câu đó tự rơi.
    Một tấm chỉ gán MỘT câu (kênh 10 video/ngày, cảnh lặp là người xem ngán)."""
    viec = os.path.join(DD.VIEC, ma)
    nh = _nhap(viec)
    bd = dict(nh.get("ban_do", {}))
    nhap = dict(nh.get("nhap", {}))
    tk = {int(k): v for k, v in nh.get("tu_khoa", {}).items() if (v or "").strip()}
    uv = {}
    p_uv = os.path.join(viec, "anh", "ung-vien.json")
    if os.path.exists(p_uv):
        try:
            uv = json.load(open(p_uv, encoding="utf-8"))
        except Exception:
            uv = {}
    da_dung = {v for v in bd.values() if v}          # đường ảnh đã lên hình trong bài
    kho_da_lay = set()                                # tệp kho đã lấy trong lượt này
    # MỌI Ô TRỐNG, kể cả Ô PHỤ (luật anh "cảnh chính có gì cảnh phụ có nấy" — em quên
    # lần thứ tư 11/08; nay bộ kiểm tầng ⑤ canh chỗ này). Ô phụ mang mã "3:0".
    ap_n = dict(nh.get("anh_phu", {}))
    try:
        _kb_n = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
        _cau_n = _tach_cau(_kb_n.get("loi_binh", ""))
        _moc_n = _moc_cau(_cau_n, _do_dai_giong(viec)
                          or sum(len(c.split()) for c in _cau_n) / TIENG_MOT_PHUT * 60)
    except Exception:
        _cau_n, _moc_n = [], []
    thieu = []
    for i in sorted(tk):
        if not bd.get(str(i)):
            thieu.append(str(i))
        if i < len(_moc_n):
            d_i = _moc_n[i] - (_moc_n[i - 1] if i else 0.0)
            sp = NC.chia_nhip([d_i], [False])[0]["so_phan"] if d_i else 1
            for j in range(max(0, sp - 1)):
                if not (ap_n.get(str(i)) or [""] * (j + 1))[j:j + 1] or \
                        not (ap_n.get(str(i)) or [])[j:j + 1][0:1] or \
                        not ((ap_n.get(str(i)) or [])[j] if j < len(ap_n.get(str(i)) or []) else ""):
                    thieu.append(f"{i}:{j}")
    ket = {"kho": 0, "web": 0, "thieu": 0, "tim_them": 0, "may_xep": 0}
    # bản MÁY XẾP THEO NGHĨA (nếu đã chạy) — nguồn chuẩn nhất, dùng trước khớp từ
    xep_ng = (_doc_kho_xep(ma) or {}).get("xep") or {}
    # KHO KHÔNG CÓ THÌ TỰ ĐI TÌM (anh đặt 11/08): câu nào chưa có ứng viên web sẵn thì
    # gọi luôn một lượt tìm Google cho riêng nó — đừng để "máy bí" chỉ vì chưa ai tìm.
    chua_uv = [i for i in thieu if not (uv.get(str(i), {}).get("anh"))]
    if chua_uv:
        try:
            if bao_tien:
                bao_tien(f"kho thiếu — đi tìm web cho {len(chua_uv)} câu", 0, len(thieu))
            _tim_san(ma, None, None, chi_thieu=True)
            uv = json.load(open(p_uv, encoding="utf-8")) if os.path.exists(p_uv) else uv
            ket["tim_them"] = len(chua_uv)
        except Exception as e:
            print(f"  ⚠ không tìm thêm được ảnh web: {e}")
    for n, ma_o in enumerate(thieu, 1):
        i = int(ma_o.split(":")[0])                 # câu gốc (ô phụ dùng chung thoại)
        la_phu = ":" in ma_o
        if bao_tien:
            ten_o = f"cảnh {i + 1}" + (chr(98 + int(ma_o.split(':')[1])) if la_phu else "")
            bao_tien(f"gán nháp — {ten_o} ({n}/{len(thieu)})", n, len(thieu))
        duong, nguon = "", ""
        # ①a MÁY XẾP THEO NGHĨA đứng TRƯỚC (anh đặt 11/08 tối): bản model đọc nhãn
        # chuẩn hơn hẳn khớp từ. Câu nào model bảo "kho không có" thì BỎ QUA kho luôn,
        # đi thẳng xuống web — khỏi mất công lấy tấm khớp-chữ mà sai nghĩa.
        may_c = (xep_ng.get(ma_o) or {})
        for t_may in (may_c.get("tep") or []):
            if t_may in kho_da_lay:
                continue
            u_noi = (f"http://127.0.0.1:{CONG}/kho-nha-anh/"
                     f"{urllib.parse.quote(t_may)}?ma={urllib.parse.quote(ma)}")
            try:
                r = gap_anh.lay_theo_url([u_noi], os.path.join(viec, "anh"), tk[i])
                if r.get("anh"):
                    duong, nguon = "anh/" + r["anh"][0]["tep"], "kho"
                    kho_da_lay.add(t_may)
                    ket["may_xep"] = ket.get("may_xep", 0) + 1
                    break
            except Exception:
                pass
        if not duong and ma_o in xep_ng and not (may_c.get("tep") or []):
            bo_kho_cau = True                       # model đã kết luận kho không có
        else:
            bo_kho_cau = False
        # ① kho nhà theo KHỚP TỪ — chỉ dùng khi chưa có bản máy xếp cho câu này
        for ung in ([] if (duong or bo_kho_cau) else _kho_nha_tim(tk[i], toi_da=6)):
            if ung.get("khop", 0) < 4:
                break
            if ung["tep"] in kho_da_lay:
                continue
            u_noi = (f"http://127.0.0.1:{CONG}/kho-nha-anh/"
                     f"{urllib.parse.quote(ung['tep'])}?ma={urllib.parse.quote(ma)}")
            try:
                r = gap_anh.lay_theo_url([u_noi], os.path.join(viec, "anh"), tk[i])
                if r.get("anh"):
                    duong, nguon = "anh/" + r["anh"][0]["tep"], "kho"
                    kho_da_lay.add(ung["tep"])
                    break
            except Exception:
                pass
        # ② ứng viên Google tìm sẵn — thử tối đa 6 tấm đầu chưa dùng; tấm nào TRÙNG
        # ảnh đã có trong kho chung thì VỨT rồi thử tấm kế (quy tắc anh đặt 11/08:
        # cấm tải về trùng kho — vừa tốn chỗ vừa làm video lặp hình)
        if not duong:
            # XẾP THEO SỨC KHOẺ trước khi thử (14/08) — trước đây lấy 6 tấm ĐẦU
            # theo thứ tự Google, nên tấm 480×360 chen trước tấm 2560×1706.
            _ds_uv = sorted((uv.get(str(i), {}).get("anh") or []),
                            key=_diem_anh_uv, reverse=True)[:6]
            for a in _ds_uv:
                if a.get("u") in da_dung:
                    continue
                try:
                    r = gap_anh.lay_theo_url([a["u"]], os.path.join(viec, "anh"), tk[i])
                    if not r.get("anh"):
                        continue
                    d_moi = "anh/" + r["anh"][0]["tep"]
                    p_moi = os.path.join(viec, d_moi)
                    if _trung_kho(p_moi):
                        try:
                            os.remove(p_moi)
                            th_m = os.path.join(viec, "anh", "_thumb",
                                                d_moi.replace("/", "__"))
                            os.path.exists(th_m) and os.remove(th_m)
                        except OSError:
                            pass
                        ket["bo_trung"] = ket.get("bo_trung", 0) + 1
                        continue
                    duong, nguon = d_moi, "web"
                    break
                except Exception:
                    pass
        if duong:
            da_dung.add(duong)
            if la_phu:                              # Ô PHỤ → sổ anh_phu
                c0, j0 = ma_o.split(":")
                o_ds = list(ap_n.get(c0) or [])
                while len(o_ds) <= int(j0):
                    o_ds.append("")
                o_ds[int(j0)] = duong
                ap_n[c0] = o_ds
            else:
                bd[ma_o] = duong
                nhap[ma_o] = {"nguon": nguon}
            ket[nguon] += 1
        else:
            if not la_phu:
                nhap[ma_o] = {"nguon": "thieu"}
            ket["thieu"] += 1
        # lưu TỪNG Ô — chết giữa chừng thì phần đã gán vẫn còn, chạy lại chỉ vá chỗ thiếu
        _luu_nhap(ma, {**nh, "ban_do": bd, "nhap": nhap, "anh_phu": ap_n})
    # KHUNG ĐÔI (#58) chạy CUỐI: phải có ảnh thứ nhất rồi mới ghép được nửa thứ hai
    try:
        ket["doi"] = _gan_khung_doi(ma, bao_tien).get("dat", 0)
    except Exception as e:
        print(f"  ⚠ khung đôi: {e}")
    return ket


def _anh_ngang(p_anh=None, kich_thuoc=""):
    """Ảnh có NGANG đủ cho MỘT NỬA khung đôi không (anh chốt 14/08: "chọn 2 ảnh ghép
    vào một cảnh thì phải chọn ảnh ngang, chọn ảnh dọc là bị mất nhân vật").

    Hình học không cãi được: video dọc 1080×1920 chia đôi, mỗi nửa 1080×960 — tỷ lệ
    1.125 NGANG. Nhét ảnh dọc 2:3 vào là phải phóng ~1.7 lần cho đầy bề ngang, đầu
    và chân nhân vật văng khỏi khung. Ảnh vuông trở lên (w ≥ h) mất ≤11%%, chấp nhận.
    Nhận kích thước từ SỔ ("wxh") hoặc mở file — trả True/False/None (không rõ)."""
    try:
        if kich_thuoc:
            w, h = (int(x) for x in kich_thuoc.split("x"))
        elif p_anh and os.path.exists(p_anh):
            w, h = Image.open(p_anh).size
        else:
            return None
        return w >= h
    except Exception:
        return None


_SO_KHO_KT = {}                                    # cache tệp kho → "wxh" cho lượt chạy


def _kt_kho(ten_tep):
    """Kích thước một tấm trong KHO CHỦ THỂ — đọc sổ một lần rồi nhớ."""
    if not _SO_KHO_KT:
        try:
            for m in (json.loads(l) for l in open(
                    os.path.join(KHO_CHU_THE, "so-chu-the.jsonl"),
                    encoding="utf-8") if l.strip()):
                _SO_KHO_KT[m.get("tep", "")] = m.get("kich_thuoc", "")
        except OSError:
            pass
    return _SO_KHO_KT.get(ten_tep, "")


def _gan_khung_doi(ma, bao_tien=None):
    """Lấy nửa THỨ HAI về bài cho những ô máy đã đề xuất khung đôi (việc #58).

    Chạy SAU khi ô đã có ảnh thứ nhất: nửa TRÊN là ảnh của ô, nửa DƯỚI là tấm máy chọn
    thêm (nên `dao=False`). Cờ `goi_y` để trạm hiện nhãn cam + nút ✓/✕ — máy làm nháp,
    anh chốt (luật "cửa duyệt của người").

    Ô nào ANH đã tự bật khung đôi thì KHÔNG đụng — tay người luôn thắng máy.
    Ảnh về bài qua đúng cửa `gap_anh.lay_theo_url` như mọi đường khác: vân tay chống
    trùng, thumbnail, sổ gắp, cổng watermark đều tự có, không mở lối riêng cho máy.
    """
    viec = os.path.join(DD.VIEC, ma)
    nh = _nhap(viec)
    bd = dict(nh.get("ban_do", {}))
    ap = dict(nh.get("anh_phu", {}))
    gh = {k: dict(v) for k, v in (nh.get("ghep_canh") or {}).items()}
    tk = nh.get("tu_khoa", {}) or {}
    xep_ng = (_doc_kho_xep(ma) or {}).get("xep") or {}
    can = [(k, v["doi"]) for k, v in sorted(xep_ng.items())
           if isinstance(v, dict) and isinstance(v.get("doi"), dict)
           and (v["doi"].get("duoi") or "")]
    ket = {"dat": 0, "bo_qua": 0, "thieu": 0, "xet": len(can)}
    for n, (ma_o, d) in enumerate(can, 1):
        c0 = ma_o.split(":")[0]
        o_g = "c" if ":" not in ma_o else ma_o.split(":")[1]   # sổ ghep_canh: "c"/"0"/"1"
        if bao_tien:
            bao_tien(f"khung đôi — cảnh {int(c0) + 1}"
                     f"{'' if o_g == 'c' else chr(98 + int(o_g))} ({n}/{len(can)})",
                     n, len(can))
        ds_p = ap.get(c0) or []
        a1 = bd.get(c0, "") if o_g == "c" else (
            ds_p[int(o_g)] if int(o_g) < len(ds_p) else "")
        cu = (gh.get(c0) or {}).get(o_g) or {}
        # chưa có ảnh thứ nhất thì không ghép được; anh đã tự gán nửa hai thì để yên
        if not a1 or (cu.get("anh2") and not cu.get("goi_y")):
            ket["bo_qua"] += 1
            continue
        # ── CẢ HAI NỬA PHẢI NGANG (anh chốt 14/08) ──────────────────────────
        # Nửa trên dọc → thôi không đề xuất khung đôi cho ô này (ghép là mất
        # nhân vật cả hai nửa); nửa dưới máy chọn mà dọc → bỏ tấm đó. Không rõ
        # kích thước thì KHÔNG chặn (đừng nghèo đề xuất vì thiếu dữ liệu).
        if not a1.startswith("clip::") and                 _anh_ngang(os.path.join(viec, a1)) is False:
            ket["bo_qua"] += 1
            ket["doc_tren"] = ket.get("doc_tren", 0) + 1
            continue
        if _anh_ngang(kich_thuoc=_kt_kho(d.get("duoi", ""))) is False:
            ket["bo_qua"] += 1
            ket["doc_duoi"] = ket.get("doc_duoi", 0) + 1
            continue
        u_noi = (f"http://127.0.0.1:{CONG}/kho-nha-anh/"
                 f"{urllib.parse.quote(d['duoi'])}?ma={urllib.parse.quote(ma)}")
        try:
            r = gap_anh.lay_theo_url([u_noi], os.path.join(viec, "anh"),
                                     tk.get(c0, "") or "")
        except Exception:
            r = {}
        if not r.get("anh"):
            ket["thieu"] += 1
            continue
        d2 = "anh/" + r["anh"][0]["tep"]
        if d2 == a1:                       # trùng chính ảnh nửa trên — ghép thành vô nghĩa
            ket["bo_qua"] += 1
            continue
        gh.setdefault(c0, {})[o_g] = {"anh2": d2, "tat": False, "dao": False,
                                      "goi_y": True, "kieu": d.get("kieu", ""),
                                      "vi_sao": d.get("vi_sao", "")}
        ket["dat"] += 1
        # lưu TỪNG Ô — chết giữa chừng thì phần đã ghép vẫn còn
        _luu_nhap(ma, {**nh, "ghep_canh": gh})
    return ket


def _diem_anh_uv(a):
    """Chấm SỨC KHOẺ một ứng viên web — thuần code, không tốn token (anh bắt 14/08:
    "ảnh đẹp, nét hơn, tình huống rõ hơn thì không được chọn, mà chọn ảnh kém hơn").

    Gốc bệnh: bộ gán nháp thử "6 tấm đầu" theo ĐÚNG THỨ TỰ Google trả — mà thứ tự ấy
    xếp theo mức khớp từ khoá, không theo chất lượng hình. Tấm 2560×1706 nằm sau tấm
    480×360 là chuyện thường.

    Ba tiêu chí đo được bằng máy (còn "tình huống rõ" thì mắt máy chấm ở bước sau):
      · to = nét — số điểm ảnh, có trần để ảnh khổng lồ không nuốt hết điểm;
      · KHUNG DỌC/VUÔNG hợp Shorts hơn ảnh quá ngang (ảnh 3:1 lên khung dọc là mất
        sạch hai bên hoặc phải nền mờ);
      · cờ `du_net` mà bộ tìm đã đo sẵn.
    """
    w, h = float(a.get("w") or 0), float(a.get("h") or 0)
    if w < 300 or h < 300:
        return 0.0
    d = min(w * h / 2_000_000.0, 1.0) * 55          # 2 triệu điểm ảnh là đủ đẹp
    ty = w / h if h else 9
    d += (25 if ty <= 1.45 else 16 if ty <= 1.85 else 6 if ty <= 2.4 else 0)
    d += 20 if a.get("du_net") else 0
    return round(d, 1)


def _mo_thu_muc(p):
    """Mở thư mục trong trình quản lý tệp — Mac dùng `open`, Windows `explorer`.

    Hệ chạy trên máy thứ hai của anh (Windows) từ 15/08, nên mọi lệnh gọi hệ điều
    hành phải rẽ nhánh. Thiếu nhánh Windows thì nút "📂 Mở kho" chết câm bên đó.
    """
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", p], timeout=15, capture_output=True)
        elif os.name == "nt":
            os.startfile(p)                            # noqa: S606 — API chuẩn Windows
        else:
            subprocess.run(["xdg-open", p], timeout=15, capture_output=True)
        return True
    except Exception:
        return False


def _bao_man_hinh(text):
    """Thông báo góc màn hình. Mac: osascript. Windows: PowerShell toast.

    Không có thì thôi — báo Telegram vẫn chạy, đừng để cả luồng chết vì một
    thông báo không hiện được.
    """
    try:
        if sys.platform == "darwin":
            subprocess.run(["osascript", "-e",
                            f'display notification {json.dumps(text)} '
                            f'with title "Trạm tài nguyên"'],
                           timeout=10, capture_output=True)
        elif os.name == "nt":
            ps = ("[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications,"
                  " ContentType=WindowsRuntime] > $null; "
                  "$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(0);"
                  f"$t.GetElementsByTagName('text')[0].AppendChild($t.CreateTextNode("
                  f"{json.dumps(text)})) > $null; "
                  "[Windows.UI.Notifications.ToastNotificationManager]"
                  "::CreateToastNotifier('Trạm tài nguyên').Show("
                  "[Windows.UI.Notifications.ToastNotification]::new($t))")
            subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           timeout=10, capture_output=True)
    except Exception:
        pass


def _cat_mep_anh(p_anh, mep, ty=0.13):
    """Cắt dải mép dính watermark, GIỮ bản gốc cạnh bên để anh hoàn tác được.

    Dùng chung một tỷ lệ 13% với cửa nhập kho chủ thể — cùng một luật thì cùng một
    con số, đừng để hai nơi cắt hai kiểu (bài học "não một nguồn").
    """
    try:
        im = Image.open(p_anh)
        w, h = im.size
        tren = int(h * ty) if "tren" in mep else 0
        duoi = h - (int(h * ty) if "duoi" in mep else 0)
        if duoi - tren < 300 or w < 300:          # cắt xong quá bé thì thà giữ nguyên
            return False
        goc = p_anh + ".truoc-cat-wm"
        if not os.path.exists(goc):
            shutil.copy2(p_anh, goc)
        im.crop((0, tren, w, duoi)).save(p_anh, quality=92)
        return True
    except Exception:
        return False


def _mat_kiem_nhap(ma):
    """MẮT MÁY kiểm nội dung các cảnh nháp: nhìn ảnh + đọc câu, tấm lệch thì GỠ.

    Việc phân loại khớp/lệch là việc dễ → haiku (luật hiệu quả tối đa – tài nguyên tối
    thiểu). Trạm chạy trong launchd nên gọi claude được (phiên Claude Code thì không —
    bài học EPERM). Tấm bị gỡ giữ cờ {go: lý do} để trạm nói cho anh biết vì sao trống."""
    viec = os.path.join(DD.VIEC, ma)
    nh = _nhap(viec)
    bd = dict(nh.get("ban_do", {}))
    nhap = dict(nh.get("nhap", {}))
    k = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    cau = _tach_cau(k.get("loi_binh", ""))
    # gửi BẢN THU NHỎ cho mắt máy (anh chốt 13/08) — 3.276 → 888 token/ảnh, đo thật
    # là vẫn đọc đúng số áo và nhận đúng người; ảnh gốc trong bài không đụng tới
    # SOI MỌI ẢNH ĐANG NẰM TRÊN CẢNH, không riêng ảnh máy gán (anh bắt 14/08: "ảnh
    # ghép vào cảnh chọn ảnh có watermark, a phải mở từng ảnh được chọn ra kiểm tra").
    # Ảnh anh tự gán trước nay không qua cửa này — mà đó đúng là những tấm anh đang
    # phải soi tay. Khác biệt về QUYỀN XỬ: ảnh MÁY gán thì lệch nội dung là gỡ; ảnh
    # ANH gán thì máy KHÔNG gỡ (anh chọn có ý), chỉ lo phần watermark.
    cap = [(c, cau[int(c)], gap_anh.ban_nho(os.path.join(viec, bd[c])))
           for c in sorted(bd, key=lambda x: int(str(x).split(":")[0]))
           if bd.get(c) and str(c).isdigit() and int(c) < len(cau)
           and not (nhap.get(c) or {}).get("go")
           and not (nhap.get(c) or {}).get("mat")
           and os.path.exists(os.path.join(viec, bd[c]))]
    ket = {"kiem": 0, "go": 0}
    for dau in range(0, len(cap), 8):                # mẻ 8 — vừa một hơi haiku
        me = cap[dau:dau + 8]
        dong = "\n".join(f"#{c} · CÂU: {chu}\n   ẢNH: {p}" for c, chu, p in me)
        prompt = (
            "Em là biên tập viên video bóng đá. Với TỪNG mục dưới đây: dùng tool Read mở "
            "tệp ảnh, rồi trả lời ảnh có KHỚP nội dung câu thoại không. Khớp = đúng người/"
            "đội/bối cảnh câu đang nói (ảnh minh hoạ chung cùng chủ đề vẫn tính là khớp); "
            "Lệch = sai người, sai đội, sai môn, hoặc ảnh vô nghĩa với câu.\n\n"
            "ĐỒNG THỜI soi hai thứ nữa (anh bắt 14/08: phải mở từng ảnh kiểm tay, "
            "mất nhiều thời gian):\n"
            "· \"wm\" — CHỮ/LOGO CHÈN ĐÈ lên ảnh (tên trang, @tài khoản, chữ ký ảnh) "
            "nằm ở đâu: \"khong\" | \"tren\" | \"duoi\" | \"giua\".\n"
            "· \"wm_chu\" — CHÉP ĐÚNG chữ em đọc được trong watermark đó. KHÔNG đọc "
            "được chữ nào cụ thể thì wm = \"khong\" và wm_chu = \"\".\n"
            "  MẶC ĐỊNH LÀ \"khong\". Chỉ khai có watermark khi em ĐỌC RA CHỮ. "
            "Chữ CÓ SẴN trong cảnh thật — biển quảng cáo quanh sân, chữ trên áo đấu, "
            "bảng tỉ số đài truyền hình, tên giải trên băng-rôn — KHÔNG phải watermark.\n"
            "· \"diem\" — chất lượng dùng cho video, 1..5: 5 = nét căng, chủ thể rõ, "
            "tình huống kể được chuyện; 3 = tạm được; 1 = mờ, xa, rối, chẳng thấy gì.\n\n"
            + dong +
            "\n\nTrả về DUY NHẤT JSON: {\"<số>\": {\"khop\": true/false, "
            "\"wm\": \"khong|tren|duoi|giua\", \"wm_chu\": \"\", \"diem\": 1-5, "
            "\"ly_do\": \"<chỉ khi lệch, ngắn gọn>\"}}")
        try:
            r = subprocess.run(
                [_CLAUDE, "-p", "--model", "claude-haiku-4-5-20251001",
                 "--allowedTools", "Read"],
                input=prompt, capture_output=True, text=True, timeout=300)
            m = re.search(r"\{.*\}", r.stdout, re.S)
            phan = json.loads(m.group(0)) if m else {}
        except Exception:
            continue
        for c, _chu, _p in me:
            v = phan.get(c) or phan.get(str(int(c)))
            if not isinstance(v, dict):
                continue
            ket["kiem"] += 1
            nhap.setdefault(c, {})
            may_gan = (nhap[c].get("nguon") in ("kho", "web"))
            if not v.get("khop") and may_gan:
                bd.pop(c, None)                       # gỡ tấm lệch — ô về trống chờ anh
                nhap[c]["go"] = v.get("ly_do", "lệch nội dung")
                ket["go"] += 1
                continue
            nhap[c]["mat"] = "khop"
            try:
                nhap[c]["diem"] = int(v.get("diem") or 0)
            except (TypeError, ValueError):
                pass
            # ── WATERMARK: RÌA thì CẮT, GIỮA thì GỠ (anh chốt 14/08) ──────────
            # Luật kho ảnh anh đặt 10/08 nay áp cho cả ảnh đang gán vào cảnh: rìa
            # cắt được thì máy cắt luôn, giữa khung thì thà để trống còn hơn lên
            # hình bẩn. Trước nay anh phải MỞ TỪNG ẢNH kiểm bằng mắt.
            wm = str(v.get("wm") or "khong").lower()
            wm_chu = str(v.get("wm_chu") or "").strip()
            # CHỈ CẮT KHI ĐỌC RA CHỮ (siết 14/08 sau khi cắt oan 2 tấm): mắt máy báo
            # "góc" trên tấm Xuân Son bay người — ảnh KHÔNG hề có watermark, máy cắt
            # 13% hai mép làm mất một phần quả bóng. Không có bằng chứng chữ thì
            # không được đụng vào ảnh; và không bao giờ cắt hai mép cùng lúc.
            if wm in ("tren", "duoi") and len(wm_chu) >= 3:
                if _cat_mep_anh(os.path.join(viec, bd[c]), (wm,)):
                    nhap[c]["wm_cat"] = f"{wm} · {wm_chu[:40]}"
                    ket["cat"] = ket.get("cat", 0) + 1
            elif wm in ("tren", "duoi", "goc"):    # nghi mà không đọc được chữ → chỉ nhắc
                nhap[c]["canh_bao"] = "⚠ nghi có watermark ở mép — soi lại nếu thấy bẩn"
            elif wm == "giua" and len(wm_chu) >= 3:
                if may_gan:                       # máy chọn thì máy chịu, gỡ ra
                    bd.pop(c, None)
                    nhap[c]["go"] = "watermark GIỮA khung — cắt mép không bỏ được"
                    ket["go"] += 1
                else:                             # anh chọn thì chỉ CẢNH BÁO, giữ ảnh
                    nhap[c]["canh_bao"] = "⚠ watermark GIỮA khung — nên đổi ảnh khác"
                ket["wm_giua"] = ket.get("wm_giua", 0) + 1
        _luu_nhap(ma, {**nh, "ban_do": bd, "nhap": nhap})
    return ket


def _chay_gan_nhap_job(ma_job, ma):
    def bao(buoc, da, tong):
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": False, "buoc": buoc, "da": da, "tong": tong}
    try:
        r = _gan_nhap_lo(ma, bao)
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": False, "buoc": "mắt máy kiểm nháp"}
        g = _mat_kiem_nhap(ma)
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "gan": r, "mat": g}
    except Exception as e:
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "loi": str(e)}


def _chay_kiem_ct(ma_job, ma, tieu_de, loi_binh):
    """Nút KIỂM CHÍNH TẢ riêng, chạy TRƯỚC khi duyệt (anh chốt 06/08 tối).

    Trước đây soát chính tả nằm sau nút Duyệt — tức anh duyệt một bản CHƯA soát, máy sửa sau
    lưng anh. Ngược đời. Giờ: anh bấm kiểm → máy lưu bản anh đang gõ, soát (chỉ chính tả và
    dấu câu, ngữ nghĩa giữ nguyên — luật đã rào ba lớp trong soat_chinh_ta.py), báo kết quả
    lên màn hình → anh đọc rồi mới bấm Duyệt lời.
    """
    viec = os.path.join(DD.VIEC, ma)
    try:
        _luu_loi(ma, tieu_de, loi_binh, duyet=False)     # lưu đúng bản anh đang thấy
        sys.path.insert(0, os.path.expanduser("~/.claude/skills/soc-content/cong-cu"))
        import soat_chinh_ta
        r = soat_chinh_ta.soat(viec, ghi=True)
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "loi": r.get("loi", ""),
                                "co_doi": r.get("co_doi", False),
                                "da_sua": r.get("da_sua", [])}
    except Exception as e:
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "loi": str(e), "da_sua": []}


def _sau_duyet_loi(ma_job, ma):
    """Anh bấm Duyệt lời xong thì máy TỰ ĐI TIẾP (anh chốt 06/08).

    Trước đây duyệt xong là dừng, anh phải quay ra bảo Claude "chạy tiếp đi" — như thế thì
    tự động hoá còn nghĩa gì. Hai việc nối liền:
      ① soát CHÍNH TẢ — chỉ lỗi gõ, không đụng câu chữ (anh duyệt rồi tức là ưng cách viết)
      ② gợi từ khoá ảnh cho từng câu, để anh mở phần gán tài nguyên ra là có sẵn
    """
    viec = os.path.join(DD.VIEC, ma)
    ra = {"xong": False, "buoc": "soát chính tả"}
    with KHOA:
        VIEC_JOB[ma_job] = dict(ra)
    tin = []
    try:
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
        if kb.get("da_soat_chinh_ta"):
            raise StopIteration           # anh đã bấm kiểm trước khi duyệt — khỏi soát lại
        sys.path.insert(0, os.path.expanduser("~/.claude/skills/soc-content/cong-cu"))
        import soat_chinh_ta
        r = soat_chinh_ta.soat(viec, ghi=True)
        if r.get("loi"):
            tin.append("chính tả: " + r["loi"])
        elif r.get("co_doi"):
            tin.append(f"sửa {len(r.get('da_sua', []))} lỗi chính tả")
        else:
            tin.append("chính tả sạch")
    except StopIteration:
        tin.append("chính tả đã kiểm trước khi duyệt")
    except Exception as e:
        tin.append(f"không soát được chính tả: {e}")

    # ĐỌC TIN → HỒ SƠ BÀI (anh chốt 11/08): làm TRƯỚC gợi từ khoá, vì mọi bước sau
    # (gợi từ khoá, tra kho, máy xếp, gán nháp) đều dùng hồ sơ này làm gốc.
    with KHOA:
        VIEC_JOB[ma_job] = {"xong": False, "buoc": "đọc tin, lập hồ sơ bài", "tin": tin}
    try:
        hs = _trich_ho_so_bai(ma)
        if hs and not hs.get("loi"):
            tin.append("hồ sơ bài: "
                       + " · ".join(x for x in [", ".join(hs.get("nhan_vat") or []),
                                                hs.get("giai") or "",
                                                hs.get("tran") or ""] if x)[:90])
    except Exception as e:
        tin.append(f"không lập được hồ sơ bài: {e}")

    with KHOA:
        VIEC_JOB[ma_job] = {"xong": False, "buoc": "gợi từ khoá ảnh", "tin": tin}
    try:
        r = GY.goi_y(viec)
        nh = _nhap(viec)
        tk, gc = dict(nh.get("tu_khoa", {})), dict(nh.get("ghi_chu", {}))
        # Lời vừa đổi thì từ khoá cũ có thể trỏ sai câu — ghi đè hết cho khớp bản mới.
        # TỪ KHOÁ ANH DÁN TỪ GPT LÀ CHÂN LÝ (14/08) — máy gợi lại thì chỉ điền vào
        # câu anh CHƯA dán. Không có phanh này thì anh dán xong, bấm Duyệt lời phát
        # nữa là công chép tay bay sạch (đúng họ lỗi đã ghi sổ nhiều lần).
        nguoi = nh.get("tu_khoa_nguoi") or {}
        for k_r, v_r in r["tu_khoa"].items():
            if not nguoi.get(k_r):
                tk[k_r] = v_r
        gc.update(r["ghi_chu"])
        # Đóng băng bản MÁY gợi làm mốc — về sau so với bản anh sửa mới rút được bài học.
        json.dump({"tu_khoa": r["tu_khoa"], "ghi_chu": r["ghi_chu"],
                   "luc": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                  open(os.path.join(viec, "anh", "goi-y-goc.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        # TỪ KHOÁ TIẾNG ANH phải ghi vào sổ, không thì vòng tìm không thấy mà dùng
        # (anh bắt 14/08: "chưa thấy tìm từ khoá theo tiếng anh" — bộ gợi ý CÓ sinh ra,
        # nhưng chỗ này chỉ nhặt tu_khoa + ghi_chu rồi vứt phần tiếng Anh đi).
        tk_en = dict(nh.get("tu_khoa_en", {}))
        for k_r, v_r in (r.get("tu_khoa_en") or {}).items():
            if not nguoi.get(k_r):
                tk_en[k_r] = v_r
        tk_2 = dict(nh.get("tu_khoa_2", {}))
        tk_2.update(r.get("tu_khoa_2") or {})
        _luu_nhap(ma, {"ban_do": nh.get("ban_do", {}), "ghi_chu": gc, "tu_khoa": tk,
                       "tu_khoa_en": tk_en, "tu_khoa_2": tk_2,
                       "tu_khoa_nguoi": nguoi, "goi_y_xong": True})
        tin.append(f"gợi từ khoá cho {len(r['tu_khoa'])} câu")
    except Exception as e:
        tin.append(f"không gợi được từ khoá: {e}")

    # ②b cụm tô vàng rỗng (anh đổi tít làm cụm cũ chết) → chọn lại từ tít mới.
    # Việc dễ — chọn 1-2 cụm đắt trong MỘT câu — haiku đủ.
    try:
        # DÙNG CHUNG module cum_vang — xưởng cũng gọi chính nó ở cửa cuối. Trước đây
        # logic nằm riêng ở đây nên bài không đi qua chuỗi này là mất cụm vàng, video
        # ra tít trắng trơn mà chẳng ai kêu (anh bắt 11/08). Một logic, một bản.
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
        if kb.get("tieu_de") and not kb.get("cum_to_vang"):
            cum = CV.bao_dam(os.path.join(viec, "kich-ban.json"))
            if cum:
                tin.append("chọn lại cụm tô vàng: " + " · ".join(cum))
    except Exception as e:
        tin.append(f"không chọn lại được cụm tô vàng: {e}")

    # ③ gợi THẺ SỐ LIỆU — câu nào có con số đáng làm nổi (anh chốt 06/08: phải tự gợi cả
    # nội dung lẫn vị trí, anh chỉ sửa thêm bớt). Gợi xong đánh cờ "goi_y" để giao diện
    # hiện khác màu — anh nhìn là biết cái nào máy đề, cái nào mình đã chốt.
    with KHOA:
        VIEC_JOB[ma_job] = {"xong": False, "buoc": "gợi thẻ số liệu", "tin": tin}
    try:
        sys.path.insert(0, os.path.expanduser("~/.claude/skills/soc-tai-nguyen/cong-cu"))
        import goi_y_the
        r = goi_y_the.goi_y(viec, ghi=True)
        n = len(r.get("the", []))
        tin.append(f"gợi {n} thẻ số liệu" if n else "không có số nào đáng gắn thẻ")
    except Exception as e:
        tin.append(f"không gợi được thẻ: {e}")

    # ④ gợi CARD đồ hoạ — cảnh nào đáng thay ảnh bằng versus/bxh/timeline, RENDER LUÔN
    # vào kho (anh chốt 06/08 tối: card cũng phải tự gợi theo kịch bản, anh chỉ sửa hoặc bỏ).
    with KHOA:
        VIEC_JOB[ma_job] = {"xong": False, "buoc": "gợi card đồ hoạ", "tin": tin}
    try:
        sys.path.insert(0, os.path.expanduser("~/.claude/skills/soc-tai-nguyen/cong-cu"))
        import goi_y_card
        r = goi_y_card.goi_y(viec, ghi=True)
        n = len(r.get("da_render", []))
        tin.append(f"render {n} card đề xuất" if n else "không có cảnh nào đáng dùng card")
    except Exception as e:
        tin.append(f"không gợi được card: {e}")

    # ⑤ TÌM SẴN ảnh cho từng câu — bước lâu nhất (~6 giây/câu) nên để cuối; chạy lúc anh
    # còn đang đọc lời thì thời gian chờ thành thời gian máy (anh chốt 06/08 tối).
    try:
        def bao5(buoc, da, tong):
            with KHOA:
                VIEC_JOB[ma_job] = {"xong": False, "buoc": buoc, "da": da, "tong": tong,
                                    "tin": tin}
        c = _tim_san(ma, None, bao5)
        tin.append(f"tìm sẵn {sum(len(v.get('anh', [])) for v in c.values())} ảnh ứng viên "
                   f"cho {len(c)} câu")
        # ⑤a TÌM LẠI VÒNG 2 cho câu TRẮNG TAY (anh đặt 12/08: "cảnh nào tìm chưa được
        # phải tự tìm lại"). Từ khoá dài hay ra 0 kết quả — Google càng nhiều chữ càng
        # siết. Vòng 2 rút gọn còn 4 từ đầu (thường là TÊN RIÊNG + hành động) rồi tìm
        # lại đúng những câu đó. Trước đây việc này đợi anh mở Trang chọn mới chạy —
        # đúng họ bệnh "một việc một đường chạy".
        trang = [i for i, v in c.items() if not (v.get("anh") or [])]
        if trang:
            nh_t = _nhap(viec)
            tk_t = nh_t.get("tu_khoa") or {}
            n_bu = 0
            for i_t in trang:
                cu_t = (tk_t.get(str(i_t)) or "").strip()
                ngan = " ".join(cu_t.split()[:4])
                if not ngan or ngan == cu_t:
                    continue
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "tin": tin,
                                        "buoc": f"tìm lại câu {i_t + 1} bằng từ khoá ngắn"}
                try:
                    r_t = _tim_san(ma, int(i_t), None, tk_ep=ngan)
                    if (r_t.get(int(i_t)) or r_t.get(str(i_t)) or {}).get("anh"):
                        n_bu += 1
                except Exception:
                    pass
            tin.append(f"tìm lại vòng 2: {n_bu}/{len(trang)} câu trắng tay đã có ảnh"
                       if trang else "")
    except Exception as e:
        tin.append(f"không tìm sẵn được ảnh: {e}")

    # ⑤b MÁY XẾP KHO THEO NGHĨA + ĐỀ XUẤT KHUNG ĐÔI — vào CHUỖI (vá 11/08: bài Bukit
    # Jalil "sân 90k vs 18k chỗ" không có đề xuất khung đôi nào vì bước này chỉ chạy
    # khi anh bấm 🧠 tay — đúng họ bệnh "một việc một đường chạy" lần thứ ba trong
    # ngày). Đặt TRƯỚC gán nháp vì gán nháp đọc bản máy xếp làm nguồn ①a — có bản
    # xếp thì nháp chuẩn hơn hẳn khớp từ. Một lượt sonnet mỗi bài, anh đã chốt
    # "chấp nhận model cao để chính xác" cho đúng khâu này.
    try:
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": False, "buoc": "máy xếp kho theo nghĩa", "tin": tin}
        r5b = _xep_kho_nghia(ma)
        if r5b.get("loi"):
            tin.append(f"máy xếp kho: {r5b['loi']}")
        else:
            tin.append(f"máy xếp {r5b.get('co_anh', 0)} ô theo nghĩa"
                       + (f", đề xuất {r5b['so_doi']} khung đôi" if r5b.get("so_doi") else ""))
    except Exception as e:
        tin.append(f"không xếp kho theo nghĩa được: {e}")

    # ⑥ GÁN NHÁP toàn bộ (Phương án ① — anh duyệt 10/08): kho nhà → ứng viên Google,
    # rồi mắt máy kiểm nội dung, tấm lệch tự gỡ. Anh mở trạm ra là bài đã dựng nháp sẵn,
    # việc của anh chỉ còn lướt duyệt ✓ hoặc đổi tấm chưa ưng.
    try:
        def bao6(buoc, da, tong):
            with KHOA:
                VIEC_JOB[ma_job] = {"xong": False, "buoc": buoc, "da": da, "tong": tong,
                                    "tin": tin}
        r6 = _gan_nhap_lo(ma, bao6)
        tin.append(f"gán nháp {r6['kho']} tấm kho nhà + {r6['web']} tấm web"
                   + (f" (tự tìm thêm {r6['tim_them']} câu)" if r6.get("tim_them") else "")
                   + (f", bỏ {r6['bo_trung']} tấm trùng kho" if r6.get("bo_trung") else "")
                   + (f", {r6['thieu']} câu bí" if r6["thieu"] else ""))
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": False, "buoc": "mắt máy kiểm nháp", "tin": tin}
        g6 = _mat_kiem_nhap(ma)
        if g6.get("go"):
            tin.append(f"mắt máy gỡ {g6['go']} tấm lệch nội dung")
        elif g6.get("kiem"):
            tin.append(f"mắt máy kiểm {g6['kiem']} cảnh nháp: đều khớp")
    except Exception as e:
        tin.append(f"không gán nháp được: {e}")

    with KHOA:
        VIEC_JOB[ma_job] = {"xong": True, "tin": tin}
    # BÁO KHI XONG HẾT (anh đặt 12/08: "tìm xong hết thì thông báo") — chuỗi này chạy
    # 3–6 phút, anh bấm Duyệt lời xong là đi làm việc khác. Báo về Telegram + thông
    # báo Mac, kèm SỐ CẢNH CÒN TRỐNG để anh biết có phải mở trạm gấp không.
    try:
        nh_x = _nhap(viec)
        bd_x = nh_x.get("ban_do") or {}
        kb_x = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
        so_cau = len(_tach_cau(kb_x.get("loi_binh", "")))
        da = sum(1 for i in range(so_cau) if (bd_x.get(str(i)) or "").strip())
        _bao_ve(f"✅ Xong chuỗi sau Duyệt lời — {kb_x.get('tieu_de','')[:52]}\n"
                f"{da}/{so_cau} cảnh đã có ảnh nháp"
                + (f" · {so_cau - da} cảnh còn trống" if da < so_cau else " · đủ cả bài")
                + "\n" + " · ".join(t for t in tin[-4:] if t))
    except Exception:
        pass
    DH.cham(viec, "chuoi_xong")      # ⏱ từ đây là thời gian ANH duyệt ảnh


def _duyet(ma, bo_qua_dau_nguon=False, bo_qua_nhap=False):
    """Chốt: sinh chon/ + ban-do-cau.json + so-nguon.jsonl + blueprint.json, rồi báo hàng đợi."""
    viec = os.path.join(DD.VIEC, ma)
    nh = _nhap(viec)
    ban_do = {int(k): v for k, v in nh.get("ban_do", {}).items() if v}
    if not ban_do:
        return {"ok": False, "loi": "chưa gán ảnh cho câu nào"}
    if 0 not in ban_do:
        return {"ok": False, "loi": "câu MỞ (câu 1) chưa có ảnh — cảnh đầu là cảnh giữ người xem"}

    # CỔNG NHÁP (Phương án ① 10/08): cảnh ◌ máy gán mà anh chưa ✓ nhận thì chưa được chốt
    # — nháp là thứ MẮT NGƯỜI chưa xem, cho qua im lặng là phản bội chính chữ "duyệt".
    con_nhap = [int(c) for c, v in (nh.get("nhap") or {}).items()
                if v.get("nguon") in ("kho", "web") and not v.get("go")
                and ban_do.get(int(c))]
    if con_nhap and not bo_qua_nhap:
        return {"ok": False, "can_xac_nhan_nhap": True,
                "cau_nhap": sorted(c + 1 for c in con_nhap),
                "loi": f"{len(con_nhap)} cảnh máy gán nháp (◌) anh chưa duyệt"}
    if con_nhap:                                     # anh xác nhận vượt cổng = đã xem hết
        _luu_nhap(ma, {**nh, "nhap": {c: v for c, v in nh.get("nhap", {}).items()
                                      if int(c) not in con_nhap}})

    k = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    cau = _tach_cau(k.get("loi_binh", ""))
    so = _so_anh(viec)

    # ĐÂY LÀ CỔNG WATERMARK THẬT SỰ — anh chốt 05/08 dời về đây.
    # Ảnh anh chọn tay không bị soi ở cửa nhập nữa (anh đã nhìn tận mắt), nên cổng phải đứng
    # ở đúng chỗ này: soi những tấm SẮP LÊN HÌNH, ngay trước khi chốt. Chỉ 12–20 tấm nên
    # nhanh, mà vẫn giữ đúng bài học số 3 của sổ dự án: "phát hiện watermark mà không chặn
    # thì bằng không" — @nhipcongtruong từng lọt vào một video đã giao.
    chua_soi = sorted({d for d in ban_do.values()
                       if so.get(d, {}).get("chua_soi") or "dau_nguon" not in so.get(d, {})})
    if chua_soi:
        theo_thu = {}
        for d in chua_soi:
            theo_thu.setdefault(d.split("/")[0], []).append(d.split("/")[-1])
        for thu, tens in theo_thu.items():
            nhan = gap_anh.soi_watermark(os.path.join(viec, thu), tens)
            for t, n in nhan.items():
                so.setdefault(f"{thu}/{t}", {}).update(
                    {"dau_nguon": n.get("dau_nguon", ""), "can_soi": n.get("can_soi", "")})
        # ghi lại nhãn vào sổ để lần sau khỏi soi lại
        p_so = os.path.join(viec, "anh", "so-gap.jsonl")
        if os.path.exists(p_so):
            dong = []
            for l in open(p_so, encoding="utf-8"):
                try:
                    x = json.loads(l)
                    k = "anh/" + x["tep"]
                    if k in so:
                        x["dau_nguon"] = so[k].get("dau_nguon", "")
                        x["can_soi"] = so[k].get("can_soi", "")
                        x.pop("chua_soi", None)
                    dong.append(json.dumps(x, ensure_ascii=False) + "\n")
                except Exception:
                    dong.append(l)
            open(p_so, "w", encoding="utf-8").writelines(dong)

    dinh = [(i, d, so[d]["dau_nguon"]) for i, d in sorted(ban_do.items())
            if so.get(d, {}).get("dau_nguon")]
    if dinh and not bo_qua_dau_nguon:
        return {"ok": False, "can_xac_nhan": True,
                "dinh": [{"cau": i + 1, "anh": d, "doc_duoc": v} for i, d, v in dinh],
                "loi": f"{len(dinh)} ảnh đang dùng có DẤU NGUỒN của bên khác"}

    # ① chép ảnh vào chon/, đánh số THEO MẠCH KỂ (thứ tự câu), ảnh dùng lại giữ nguyên số
    ra_chon = os.path.join(viec, "anh", "chon")
    shutil.rmtree(ra_chon, ignore_errors=True)
    os.makedirs(ra_chon)
    danh, ban_do_ten, thieu = {}, {}, []
    for i in sorted(ban_do):
        duong = ban_do[i]
        goc = os.path.join(viec, duong)
        if not os.path.exists(goc):
            thieu.append(duong)
            continue
        if duong not in danh:
            ten = f"{len(danh) + 1:02d}.jpg"
            shutil.copy2(goc, os.path.join(ra_chon, ten))
            danh[duong] = ten
        ban_do_ten[str(i)] = danh[duong]
    if thieu:
        return {"ok": False, "loi": "thiếu tệp: " + ", ".join(thieu[:4])}

    # ② bản đồ câu → ảnh (xưởng đọc file này)
    json.dump(ban_do_ten, open(os.path.join(viec, "anh", "ban-do-cau.json"), "w",
                               encoding="utf-8"), ensure_ascii=False, indent=1)
    # ②b bản dịch TÊN MỚI → TÊN GỐC: cach-hien (kiểu hiển thị anh chỉ) ghi theo tên gốc,
    # mà chon/ đánh số lại — thiếu bản dịch này thì chỉ-định-kiểu không bao giờ khớp khoá
    # ở bài đã chốt (bug ngầm, lộ 08/08 vụ bảng xếp hạng).
    json.dump({ten: duong for duong, ten in danh.items()},
              open(os.path.join(viec, "anh", "ten-goc-chon.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # ③ sổ nguồn ĐÚNG KHUÔN cổng QC ra đang đọc: mỗi dòng một tài nguyên, có trường
    #    `file` và `ket_qua`. Trước bản này `lay_anh` ghi JSON thường nên truyền --so là
    #    cổng crash (chỗ vênh ghi trong sổ dự án mục 6b). Từ đây sổ do TRẠM ghi, và chỉ ghi
    #    ảnh NGƯỜI ĐÃ DUYỆT — nên "ĐẠT" ở đây có nghĩa thật: qua cổng watermark VÀ qua mắt người.
    p_so = os.path.join(viec, "anh", "so-nguon.jsonl")
    with open(p_so, "w", encoding="utf-8") as f:
        for duong, ten in danh.items():
            m = so.get(duong, {})
            ly_do = []
            if m.get("can_soi"):
                ly_do.append("cờ vàng: " + m["can_soi"])
            if m.get("dau_nguon"):
                ly_do.append("DẤU NGUỒN: " + m["dau_nguon"] + " — anh xác nhận vẫn dùng")
            f.write(json.dumps({
                "file": ten, "goc": duong, "nguon": m.get("bao", "") or "chưa ghi nguồn",
                "url": m.get("url", ""), "giay_phep": m.get("giay_phep", ""),
                "chu_doc_duoc": (m.get("dau_nguon") or m.get("can_soi", ""))[:200],
                "ly_do": ly_do,
                # Ghi thẳng ĐẠT cho tấm dính dấu nguồn thì cổng QC ra không chặn nữa — nên
                # phải nói thật là anh đã BỎ QUA, và ghi rõ ai bỏ qua.
                "ket_qua": "ĐẠT", "bo_qua_dau_nguon": bool(m.get("dau_nguon")),
                "nguoi_duyet": "Lê Tuấn Anh (trạm tài nguyên)",
                "luc": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }, ensure_ascii=False) + "\n")

    # ④ blueprint 8 trường — cùng ngôn ngữ với hệ cũ (id, voiceover_text, scene_note,
    #    search_keywords, resource_type, visual_movement, sfx, estimated_duration)
    tong = _do_dai_giong(viec) or sum(len(c.split()) for c in cau) / TIENG_MOT_PHUT * 60
    moc = _moc_cau(cau, tong)
    ghi_chu, tu_khoa = nh.get("ghi_chu", {}), nh.get("tu_khoa", {})
    bp, dang = [], None
    for i, c in enumerate(cau):
        if i in ban_do:
            dang = ban_do_ten[str(i)]
        bp.append({
            "id": i + 1, "voiceover_text": c, "scene_note": ghi_chu.get(str(i), ""),
            "search_keywords": tu_khoa.get(str(i), ""),
            "resource_type": "Ảnh", "visual_movement": "Ken Burns", "sfx": "",
            "estimated_duration": round(moc[i] - (moc[i - 1] if i else 0), 2),
            "anh": dang,
        })
    json.dump(bp, open(os.path.join(viec, "anh", "blueprint.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # Soi trước xem cắt cảnh theo ảnh anh gán thì có tấm nào KHÔNG lên hình được không.
    # Báo ngay tại đây, đừng để anh xem video xong mới phát hiện thiếu (anh bắt đúng lỗi này
    # 05/08 ở câu 2 — 7 tấm bị bỏ im lặng).
    canh_bao = []
    try:
        tong2 = _do_dai_giong(viec) or sum(len(c.split()) for c in cau) / TIENG_MOT_PHUT * 60
        moc2 = _moc_cau(cau, tong2)
        giay_tho = [moc2[i] - (moc2[i - 1] if i else 0) for i in range(len(cau))]
        clip_c2 = _doc_clip_canh(viec)
        canh_bao = _soi_canh_bao_nhip(
            cau, giay_tho, [str(i) in clip_c2 for i in range(len(cau))],
            ban_do_ten, nh.get("anh_phu") or {}, nh.get("ghep_canh") or {})
    except Exception:
        pass

    # ⑦ TỰ HỌC KHI CHỐT (anh chốt 11/08: "tự học sau khi chạy xuất video lên kho").
    # Đây là điểm học ĐẮT NHẤT của cả dây chuyền: ảnh lên tới đây là ảnh ĐÃ QUA MẮT ANH
    # — chính xác hơn mọi phỏng đoán của máy. Ghi cặp (ý câu ↔ nhãn ảnh) + hồ sơ bài để
    # lần sau gặp tin cùng kiểu là tra ra ngay, không phải hỏi model lại.
    try:
        hs_h = _doc_ho_so_bai(ma)
        so_kho = {}
        if os.path.exists(SO_CHU_THE):
            for dg in open(SO_CHU_THE, encoding="utf-8"):
                try:
                    mk = json.loads(dg)
                    so_kho[mk.get("tep", "")] = mk
                except Exception:
                    pass
        p_gap_h = os.path.join(viec, "anh", "so-gap.jsonl")
        theo_tep = {}
        if os.path.exists(p_gap_h):
            for dg in open(p_gap_h, encoding="utf-8"):
                try:
                    g = json.loads(dg)
                    theo_tep["anh/" + g.get("tep", "")] = g
                except Exception:
                    pass
        n_hoc = 0
        for i_c, duong_c in sorted(ban_do.items()):
            if i_c >= len(cau):
                continue
            g = theo_tep.get(duong_c) or {}
            # nhãn của tấm: ưu tiên CHÚ THÍCH nhà báo, rồi nhãn kho, rồi từ khoá đã tìm
            ten_kho = os.path.basename(str(g.get("url", ""))).split("?")[0]
            mk = so_kho.get(ten_kho) or {}
            m_hoc = {"chu_the": mk.get("chu_the", ""),
                     "nhan": (mk.get("nhan") or [])[:6] or
                             ([g["chu_thich"]] if g.get("chu_thich") else [])}
            if not (m_hoc["chu_the"] or m_hoc["nhan"]):
                continue
            _ghi_hoc_ghep(ma, cau[i_c],
                          (nh.get("tu_khoa") or {}).get(str(i_c), ""), m_hoc)
            n_hoc += 1
        if n_hoc:
            print(f"  📘 học {n_hoc} cặp câu↔ảnh từ bài vừa chốt"
                  + (f" · hồ sơ: {hs_h.get('giai', '')}" if hs_h else ""))
    except Exception as e:
        print(f"  ⚠ không ghi được sổ học khi chốt: {e}")

    _lenh(f"tài nguyên ĐÃ DUYỆT cho {ma} ({len(danh)} ảnh / {len(cau)} câu) — chờ dựng", "trạm")
    return {"ok": True, "so_anh": len(danh), "so_cau_gan": len(ban_do_ten), "tong_cau": len(cau),
            "canh_bao": canh_bao,
            "chon": os.path.join(viec, "anh", "chon")}


def _bao_ve(text):
    """BÁO VỀ ĐÂU khi dựng xong (anh hỏi 05/08 — anh tưởng nó báo vào phiên chat).

    Trạm là một tiến trình web ĐỘC LẬP, không có đường nào nhắn vào phiên Claude đang mở —
    y như bot Telegram không chen vào phiên đang mở được (sổ dự án mục 3). Nên báo về hai nơi
    anh THẬT SỰ nhìn thấy khi đang làm việc khác:
      ① nhóm Telegram "Kênh YTB Sóc bóng đá 247" — nhận được cả trên điện thoại
      ② thông báo góc màn hình Mac
    Trên trang trạm thì đã có ô trạng thái video nằm thường trực, không tự tắt.
    """
    try:
        c = json.load(open(DD.BOT_CAU_HINH, encoding="utf-8"))
        urllib.request.urlopen(urllib.request.Request(
            f"https://api.telegram.org/bot{c['bot_token']}/sendMessage",
            data=urllib.parse.urlencode({"chat_id": c["chat_id"], "text": text}).encode(),
            method="POST"), timeout=15).read()
    except Exception:
        pass
    _bao_man_hinh(text)


def _chay_loc(ma_job, ma):
    viec = os.path.join(DD.VIEC, ma)
    try:
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
        chu_de = f"{kb.get('tieu_de','')} — {kb.get('tin_goc','')}"

        def tien(x, n):
            with KHOA:
                VIEC_JOB[ma_job] = {"xong": False, "buoc": "soi nội dung ảnh",
                                    "da": x, "tong": n}

        r = LOC.soi(os.path.join(viec, "anh"), chu_de, bao_tien=tien)
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "ok": not r["loi"], "loi": r["loi"],
                                "da_soi": r["da_soi"], "lac_de": r["lac_de"],
                                "anh": _danh_sach_anh(viec)}
    except Exception as e:
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "ok": False, "loi": str(e)}


def _chay_dung(ma_job, ma):
    """Gọi thẳng xưởng dựng video. Trước bản này trạm chỉ GHI LỆNH vào hàng đợi — mà hàng đợi
    thì chưa có ai đi lấy, nên bấm duyệt xong video không hề được dựng lại. Anh hỏi đúng chỗ
    đó 05/08. Hàng đợi vẫn giữ (để sau nối bot Telegram), nhưng nó là SỔ GHI VIỆC, không phải
    đường chạy — đường chạy là hàm này."""
    viec = os.path.join(DD.VIEC, ma)
    try:
        r = subprocess.run([sys.executable, os.path.join(DD.MAY, "xuong.py"), viec],
                           capture_output=True, text=True, timeout=900, cwd=DD.MAY)
        ra = (r.stdout or "").strip().splitlines()
        vid = os.path.join(viec, "video.mp4")
        with KHOA:
            if r.returncode == 0 and os.path.exists(vid):
                DH.cham(viec, "dung_xong", ghi_de=True)   # ⏱ lần dựng CUỐI mới là lần ăn
            VIEC_JOB[ma_job] = {
                "xong": True, "ok": r.returncode == 0 and os.path.exists(vid),
                "loi": "" if r.returncode == 0 else (r.stderr or "")[-400:],
                "nhat_ky": ra[-6:], "video": vid,
                "nang_mb": round(os.path.getsize(vid) / 1e6, 1) if os.path.exists(vid) else 0}
        _bao_ve(f"✅ Dựng xong video {ma}\n"
                f"{round(os.path.getsize(vid) / 1e6, 1)} MB · {ra[-1] if ra else ''}\n"
                f"Xem ở trạm: http://localhost:8756/video/{ma}"
                if r.returncode == 0 and os.path.exists(vid)
                else f"❌ Dựng hỏng video {ma}\n{(r.stderr or '')[-200:]}")
    except subprocess.TimeoutExpired:
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "ok": False, "loi": "xưởng chạy quá 15 phút"}
    except Exception as e:
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "ok": False, "loi": str(e)}


def _lenh(text, nguon="trạm"):
    """Hàng đợi lệnh — CÙNG ĐỊNH DẠNG hệ cũ (id/time/text/trang_thai) + thêm trường `nguon`.
    Trường thêm không làm hỏng bên đọc cũ, mà biết được lệnh từ trạm hay từ bot Telegram."""
    d = {"id": int(time.time() * 1000), "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
         "text": text, "nguon": nguon, "trang_thai": "pending"}
    with open(HANG_DOI, "a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return d


# ── gắp ảnh chạy nền ─────────────────────────────────────────────────────────
def _chay_goi_y(ma_job, ma, de_len=False):
    """Gợi ý từ khoá + ghi chú cho TỪNG CÂU (anh chốt 05/08: trạm mở ra là phải có sẵn).

    de_len=False (chạy tự động lần đầu): chỉ điền vào ô CÒN TRỐNG, không đụng chữ anh đã gõ.
    de_len=True  (anh bấm "gợi ý lại"): ghi đè hết.
    """
    viec = os.path.join(DD.VIEC, ma)
    try:
        r = GY.goi_y(viec)
        nh = _nhap(viec)
        tk, gc = dict(nh.get("tu_khoa", {})), dict(nh.get("ghi_chu", {}))
        for k, v in r["tu_khoa"].items():
            if de_len or not tk.get(k):
                tk[k] = v
        for k, v in r["ghi_chu"].items():
            if de_len or not gc.get(k):
                gc[k] = v
        tk_en = dict(nh.get("tu_khoa_en", {}))
        for k, v in (r.get("tu_khoa_en") or {}).items():
            if de_len or not tk_en.get(k):
                tk_en[k] = v
        tk_2 = dict(nh.get("tu_khoa_2", {}))
        for k, v in (r.get("tu_khoa_2") or {}).items():
            if de_len or not tk_2.get(k):
                tk_2[k] = v
        _luu_nhap(ma, {"ban_do": nh.get("ban_do", {}), "ghi_chu": gc, "tu_khoa": tk,
                       "tu_khoa_en": tk_en, "tu_khoa_2": tk_2,
                       "goi_y_xong": True})
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "loi": r.get("loi", ""), "cach": r["cach"],
                                "so": len(r["tu_khoa"]), "tu_khoa": tk, "ghi_chu": gc}
    except Exception as e:
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "loi": f"{e}", "so": 0,
                                "vet": traceback.format_exc()[-700:]}


def _chay_gap(ma_job, ma, cach, doi_so, can):
    viec = os.path.join(DD.VIEC, ma)

    def bao_tien(xong, tong):
        """Màn hình đứng im 25 giây thì anh tưởng treo. Cho thấy nó đang soi tới đâu."""
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": False, "buoc": "soi watermark",
                                "da": xong, "tong": tong}

    try:
        thu = os.path.join(viec, "anh")
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": False, "buoc": "mở trang + tải ảnh"}
        r = (gap_anh.tim(doi_so, thu, can, bao_tien=bao_tien) if cach == "tim"
             else gap_anh.boc_bai(doi_so, thu, can, bao_tien=bao_tien))
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "loi": r.get("loi", ""),
                                "so": len(r.get("anh", [])),
                                "anh": _danh_sach_anh(viec)}
    except Exception as e:
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "loi": f"{e}", "so": 0,
                                "vet": traceback.format_exc()[-700:]}


# ── ảnh nhỏ ──────────────────────────────────────────────────────────────────
DO_HOA = os.path.join(DD.MAY, "do-hoa")


def _tao_card(viec, than):
    """Render card đồ hoạ NGAY TRONG TRẠM — "chọn card là ra" (anh chốt 06/08 tối).

    Điểm cắm an toàn anh chỉ: render xong bỏ .jpg vào <việc>/anh/ là _danh_sach_anh tự liệt kê,
    trạm hiện như ảnh thường để gán cho câu — KHÔNG đổi data model.
    Menu do-hoa/lam_card_soc.py lo phần dịch lựa chọn → spec engine + khổ dọc 9:16 chừa 30%
    dưới cho khung tiêu đề (config_soc.json). Ở đây chỉ: gói pick → gọi menu → đổi PNG ra JPG
    (trạm chỉ liệt kê và phục vụ .jpg — _an_toan chặn đuôi khác) → trả danh sách ảnh mới.
    """
    import glob as _g       # tempfile/shutil đã có ở đầu file — import lại là SHADOW
                            # cả hàm, nhánh chạy trước sẽ UnboundLocalError (bài học 11/08)
    canh = int(than.get("canh", 0))
    pick = {"canh": canh, "loai": than.get("loai")}
    for k in ("tieu_de", "trai", "phai", "nhan", "so", "ghi_chu", "hang", "moc", "mau"):
        if k in than and than[k] not in (None, ""):
            pick[k] = than[k]
    tam = tempfile.mkdtemp(prefix="card-")
    try:
        p_pick = os.path.join(tam, "picks.json")
        json.dump([pick], open(p_pick, "w", encoding="utf-8"), ensure_ascii=False)
        r = subprocess.run([sys.executable, os.path.join(DO_HOA, "lam_card_soc.py"),
                            p_pick, "--ra", tam],
                           capture_output=True, text=True, timeout=120)
        png = sorted(_g.glob(os.path.join(tam, "*.png")))
        if r.returncode != 0 or not png:
            return {"loi": "render card hỏng: " + (r.stderr or r.stdout or "")[-300:]}
        ra = os.path.join(viec, "anh", f"card_{canh:02d}.jpg")
        os.makedirs(os.path.dirname(ra), exist_ok=True)
        Image.open(png[0]).convert("RGB").save(ra, quality=92)
        return {"ok": True, "tep": f"anh/card_{canh:02d}.jpg", "anh": _danh_sach_anh(viec)}
    except subprocess.TimeoutExpired:
        return {"loi": "render card quá 120 giây"}
    finally:
        shutil.rmtree(tam, ignore_errors=True)


def _don_sau_doi_anh(viec, duong):
    """Ảnh vừa bị THAY RUỘT (crop / hoàn crop): thumbnail cache và vân tay cũ đều sai —
    xoá để hệ tự tính lại từ file mới. Quên bước này là kho hiện thumbnail cũ còn máy
    chống trùng thì cầm vân của ảnh đã không còn tồn tại."""
    t = os.path.join(viec, "anh", "_thumb", duong.replace("/", "__"))
    os.path.exists(t) and os.remove(t)
    p_vt = os.path.join(viec, "anh", "van-tay.json")
    try:
        so = json.load(open(p_vt, encoding="utf-8"))
        if os.path.basename(duong) in so:
            del so[os.path.basename(duong)]
            json.dump(so, open(p_vt, "w", encoding="utf-8"))
    except Exception:
        pass


def _thumb(viec, duong):
    goc = os.path.join(viec, duong)
    ra = os.path.join(viec, "anh", "_thumb", duong.replace("/", "__"))
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    if os.path.exists(ra) and os.path.getmtime(ra) >= os.path.getmtime(goc):
        return ra
    im = Image.open(goc).convert("RGB")
    im.thumbnail((420, 420), Image.LANCZOS)
    im.save(ra, quality=82)
    return ra


def _an_toan(duong):
    """Chỉ cho đi vào đúng hai thư mục ảnh, không cho lùi ra ngoài thư mục việc."""
    duong = urllib.parse.unquote(duong).lstrip("/")
    if ".." in duong or duong.startswith("/"):
        return None
    thu = duong.split("/")[0]
    return duong if thu in THU_ANH and duong.endswith(".jpg") else None


# ── clip từ mạng xã hội (extension gửi link + cookie, trạm tải bằng yt-dlp) ──
# Vì sao đi đường này (anh yêu cầu 07/08): video TikTok/Facebook/Instagram phát bằng `blob:`
# — extension KHÔNG fetch được như ảnh. Nhưng yt-dlp đọc được cả ba nền tảng, chỉ thiếu phiên
# đăng nhập; extension bù đúng chỗ đó bằng cách gửi kèm cookie của trang. Cookie chỉ đi tới
# localhost, ghi ra tệp tạm quyền 600 và xoá ngay khi tải xong.
UA_CLIP = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def _cookie_netscape(cookies):
    """Đổi cookie kiểu chrome.cookies.getAll sang khuôn Netscape mà yt-dlp đọc."""
    dong = ["# Netscape HTTP Cookie File"]
    for c in cookies or []:
        dom, ten = c.get("domain", ""), c.get("name", "")
        if not dom or not ten:
            continue
        het = int(c.get("expirationDate") or time.time() + 30 * 86400)
        dong.append("\t".join([dom, "TRUE" if dom.startswith(".") else "FALSE",
                               c.get("path") or "/", "TRUE" if c.get("secure") else "FALSE",
                               str(het), ten, c.get("value", "")]))
    return "\n".join(dong) + "\n"


def _danh_sach_clip(viec):
    """Clip đã gắp về ngăn tay của việc này — trạm bày ra cho anh bấm xem."""
    thu = os.path.join(viec, "clip", "tay")
    so = {}
    p_so = os.path.join(thu, "nguon-clip.json")
    if os.path.exists(p_so):
        try:
            for m in json.load(open(p_so, encoding="utf-8")):
                so[m.get("tep", "")] = m
        except Exception:
            pass
    ra = []
    for p in sorted(glob.glob(os.path.join(thu, "*.mp4"))):
        ten = os.path.basename(p)
        m = so.get(ten, {})
        ra.append({"tep": ten, "giay": m.get("giay", 0),
                   "mb": round(os.path.getsize(p) / 1048576, 1),
                   "trang": m.get("trang", "")})
    return ra


def _doc_clip_canh(viec):
    """Bản đồ câu → đoạn clip đã gán ({"3": {tep, tu, den}}). Xưởng đọc cùng file này."""
    p = os.path.join(viec, "anh", "clip-canh.json")
    if not os.path.exists(p):
        return {}
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}


def _doc_clip_doan(viec):
    """SỔ ĐOẠN ĐÃ CẮT — mỗi đoạn anh từng cắt+gán là một ứng viên trong kho, gắp lại cho
    cảnh khác được (anh đặt 07/08). Xoá đoạn khỏi sổ KHÔNG xoá tệp clip gốc.

    TỰ VÁ SỔ THEO ĐĨA (vá 07/08 chiều): tệp bản-cắt còn nằm trong `clip/doan/` mà sổ
    không ghi (sổ hỏng, thao tác dở dang thời còn lỗi gán) thì dựng lại mục từ TÊN TỆP —
    anh phải luôn thấy ĐỦ các đoạn đã cắt trong kho, không có đoạn mồ côi vô hình."""
    p = os.path.join(viec, "anh", "clip-doan.json")
    ds = []
    if os.path.exists(p):
        try:
            ds = json.load(open(p, encoding="utf-8"))
        except Exception:
            ds = []
    co = {(x.get("tep"), x.get("tu"), x.get("den")) for x in ds}
    for f in sorted(glob.glob(os.path.join(viec, "clip", "doan", "*.mp4"))):
        m = re.match(r"(.+)__([\d.]+)-([\d.]+)\.mp4$", os.path.basename(f))
        if not m:
            continue
        tep, tu, den = f"clip/tay/{m.group(1)}.mp4", float(m.group(2)), float(m.group(3))
        if ((tep, tu, den) not in co
                and os.path.exists(os.path.join(viec, "clip", "tay", m.group(1) + ".mp4"))):
            ds.append({"tep": tep, "tu": tu, "den": den, "luc": ""})
    return ds


def _cat_doan(viec, ten, tu, den, khung=None):
    """Cắt ĐOẠN thành tệp riêng trong `clip/doan/` (cache theo tệp+mốc) — anh chốt 07/08:
    bấm thẻ đoạn phải XEM ĐÚNG BẢN ĐÃ CẮT, không phải video gốc. BỎ SẠCH TIẾNG (anh chốt
    07/08 chiều: bản cắt phải câm để chắc chắn không lồng âm khi dựng); muốn nghe tiếng
    thẩm khoảnh khắc thì mở cửa cắt video GỐC.

    khung {x,y,w,h}: đoạn có KHUNG NÉ LOGO thì bản xem cũng phải là KHUNG ĐÃ CẮT (anh bắt
    09/08 đêm — trước đó xem lại vẫn thấy toàn cảnh). Bản crop lưu tên riêng đuôi __k…
    (đuôi này cố tình KHÔNG lọt regex tự-vá sổ — kẻo mỗi bản crop đẻ một mục mồ côi)."""
    src = os.path.join(viec, "clip", "tay", ten)
    duoi = ""
    if khung:
        duoi = (f"__k{int(khung['x'] * 1000)}-{int(khung['y'] * 1000)}"
                f"-{int(khung['w'] * 1000)}-{int(khung['h'] * 1000)}")
    ra = os.path.join(viec, "clip", "doan", f"{ten[:-4]}__{tu:.1f}-{den:.1f}{duoi}.mp4")
    if os.path.exists(ra) or not os.path.exists(src):
        return ra
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    loc = []
    if khung:
        loc = ["-vf", (f"crop=floor(iw*{khung['w']:.4f}/2)*2:floor(ih*{khung['h']:.4f}/2)*2:"
                       f"floor(iw*{khung['x']:.4f}):floor(ih*{khung['y']:.4f})")]
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-ss", f"{tu:.2f}", "-i", src,
                        "-t", f"{max(den - tu, 0.1):.2f}"] + loc + ["-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "21", "-an", "-movflags",
                        "+faststart", ra], timeout=120)
    except Exception:
        pass
    return ra


def _thumb_clip(viec, ten, t):
    """Hình mồi của clip tại giây t — cắt một khung, cache theo (tệp, giây)."""
    src = os.path.join(viec, "clip", "tay", ten)
    ra = os.path.join(viec, "anh", "_thumb", f"clipf__{ten}__{t:.1f}.jpg")
    if os.path.exists(ra) or not os.path.exists(src):
        return ra
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    # +0.2s né khung mờ đầu đoạn; trượt (t sát cuối clip) thì lấy đúng t
    for ss in (t + 0.2, t, 0.0):
        try:
            subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-ss", f"{max(ss, 0):.2f}",
                            "-i", src, "-frames:v", "1", "-vf", "scale=420:-2", ra],
                           timeout=30)
        except Exception:
            pass
        if os.path.exists(ra) and os.path.getsize(ra) > 500:
            break
    return ra


def _nhan_video_job(ma_job, ma, trang, src, cookies):
    """Tải một video MXH về `<việc>/clip/tay/` — chạy nền, extension thăm dò tới khi xong.

    Clip vào NGĂN TAY (tầng 3 theo luật tim_clip): anh tự chỉ tay nghĩa là anh đã duyệt nội
    dung, nhưng bản quyền vẫn là của người quay — ghi sổ nguồn để cổng QC và phần ghi công soi.
    """
    viec = os.path.join(DD.VIEC, ma)
    thu = os.path.join(viec, "clip", "tay")
    p_ck = p_giu = tep = None
    n = 0
    _keo(ma, "video", +1)
    try:
        if not os.path.isdir(viec):
            raise RuntimeError(f"không thấy thư mục việc {ma}")
        os.makedirs(thu, exist_ok=True)
        url = (trang or "").strip()
        vp = urllib.parse.urlparse(url)
        if not vp.path.strip("/") and not vp.query:
            raise RuntimeError("đang đứng ở TRANG CHỦ / bảng tin — bấm mở video ra trang "
                               "riêng của nó (URL đổi thành /watch, /reel, /video…) rồi hãy gắp")
        # SỐ THỨ TỰ PHẢI XÍ NGUYÊN TỬ (anh báo 16/08 "video 2 không thấy"). Hai lỗi ở
        # đây: ① glob chỉ nhìn `tay_*.mp4`, mà video ĐANG TẢI mang tên `tay_02.f399.mp4.part`
        # — gắp video thứ hai trong lúc video đầu chưa xong thì cả hai cùng ra số 01 rồi
        # đè nhau; ② đếm-rồi-đặt-tên không bao giờ nguyên tử. Nay nhìn MỌI tệp `tay_*`
        # (kể cả .part) và xí chỗ bằng O_EXCL — hệ điều hành bảo đảm chỉ một người xí được.
        n = 0
        while True:
            n += 1
            if glob.glob(os.path.join(thu, f"tay_{n:02d}*")):
                continue
            try:
                os.close(os.open(os.path.join(thu, f"tay_{n:02d}.giu"),
                                 os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                break
            except FileExistsError:
                continue
        p_giu = os.path.join(thu, f"tay_{n:02d}.giu")
        # TÊN THEO NỘI DUNG (anh đặt 16/08: "tên video lấy về phải đặt theo nội dung bài
        # để dễ nhận diện"). GIỮ NGUYÊN tiền tố `tay_NN` — mọi phép đếm số và glob trong
        # hệ đều dựa vào nó; đổi cả tên là gãy hàng loạt chỗ không liên quan.
        try:
            kb_t = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
            ten_noi_dung = slug_hoa(kb_t.get("tieu_de", ""), 46)
        except Exception:
            ten_noi_dung = ""
        cuoi = f"tay_{n:02d}" + (f"_{ten_noi_dung}" if ten_noi_dung else "")
        tep = os.path.join(thu, f"{cuoi}.mp4")
        if cookies:
            fd, p_ck = tempfile.mkstemp(prefix="soc-ck-", suffix=".txt")
            os.write(fd, _cookie_netscape(cookies).encode())
            os.close(fd)
            os.chmod(p_ck, 0o600)
        # Thử link TRANG trước (yt-dlp có bộ bóc riêng cho từng nền tảng); trang không ăn
        # mà chuột phải trúng được src http thật (hiếm — đa số là blob:) thì thử nốt đường
        # đó. YouTube (anh yêu cầu 07/08): có thêm lượt lùi giả app iOS — YouTube thỉnh
        # thoảng chặn máy lạ đòi cookie, mà cookie tài khoản KÊNH thì không được đem dùng.
        cac_luot = []
        for u in [x for x in (url, src) if x and x.startswith("http")]:
            cac_luot.append((u, []))
            if "youtube.com" in u or "youtu.be" in u:
                cac_luot.append((u, ["--extractor-args", "youtube:player_client=ios"]))
        loi_cuoi = ""
        for u, them in cac_luot:
            with KHOA:
                VIEC_JOB[ma_job] = {"xong": False, "buoc": "yt-dlp đang tải…"}
            lenh = ["yt-dlp", "--no-update", "--no-warnings", "--no-playlist",
                    # -N 8: tải 8 mảnh HLS/DASH song song — đo là chỗ ăn thời gian nhất
                    # (anh kêu kéo video lâu 09/08 khuya); server MXH giới hạn tốc độ
                    # TỪNG kết nối chứ không giới hạn tổng
                    "-N", "8",
                    "--playlist-items", "1", "--socket-timeout", "30",
                    # <=? — quá 15 phút thì bỏ (highlight trận hay 10-15p, tải về để cắt
                    # đoạn), video KHÔNG khai độ dài thì vẫn cho qua
                    "--match-filter", "duration<=?900",
                    "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba"
                          "/b[height<=1080]/b",
                    "--merge-output-format", "mp4", "--user-agent", UA_CLIP,
                    "-o", os.path.join(thu, f"{cuoi}.%(ext)s"), u] + them
            if p_ck:
                lenh[1:1] = ["--cookies", p_ck]
            if u == src and url:
                lenh[1:1] = ["--referer", url]
            try:
                r = subprocess.run(lenh, capture_output=True, text=True, timeout=900)
            except subprocess.TimeoutExpired:
                loi_cuoi = "tải quá 15 phút — mạng chậm hoặc video quá nặng"
                continue
            if os.path.exists(tep) and os.path.getsize(tep) > 50000:
                break
            loi_cuoi = ((r.stderr or r.stdout or "").strip()[-300:]
                        or "yt-dlp chạy xong mà không ra tệp")
        else:
            raise RuntimeError(loi_cuoi or "không có đường nào để tải")

        giay = 0.0
        try:
            pr = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", tep],
                                capture_output=True, text=True, timeout=30)
            giay = round(float((pr.stdout or "0").strip() or 0), 1)
        except Exception:
            pass
        try:                                       # hình mồi để sau này bày lên trạm
            subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-ss", str(min(1.0, giay / 2)),
                            "-i", tep, "-frames:v", "1", "-vf", "scale=420:-2",
                            tep[:-4] + ".jpg"], timeout=60)
        except Exception:
            pass
        p_so = os.path.join(thu, "nguon-clip.json")
        so = []
        if os.path.exists(p_so):
            try:
                so = json.load(open(p_so, encoding="utf-8"))
            except Exception:
                so = []
        so.append({"tep": os.path.basename(tep), "trang": url, "tang": 3,
                   "cach": "extension", "giay": giay,
                   "luc": datetime.now().isoformat(timespec="seconds"),
                   "ghi_chu": "anh tự chỉ tay từ MXH — bản quyền của người quay, QC phải soi"})
        json.dump(so, open(p_so, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "loi": "", "tep": os.path.basename(tep),
                                "giay": giay,
                                "mb": round(os.path.getsize(tep) / 1048576, 1)}
    except Exception as e:
        with KHOA:
            VIEC_JOB[ma_job] = {"xong": True, "loi": str(e)}
    finally:
        _keo(ma, "video", -1)
        # DỌN RÁC: tệp giữ chỗ, và mảnh `.part`/`.f###` của lượt tải hỏng. Không dọn thì
        # kho đầy mảnh vụn (đã thấy tay_02.f399.mp4.part 10 MB nằm lại ở 2 bài) và lần
        # sau đếm số bị nhiễu.
        try:
            if p_giu and os.path.exists(p_giu):
                os.remove(p_giu)
        except OSError:
            pass
        if n and not (tep and os.path.exists(tep) and os.path.getsize(tep) > 50000):
            for rac in glob.glob(os.path.join(thu, f"tay_{n:02d}*")):
                try:
                    os.remove(rac)
                except OSError:
                    pass
        if p_ck:
            try:
                os.remove(p_ck)
            except OSError:
                pass


# ── server ───────────────────────────────────────────────────────────────────
class Tay(BaseHTTPRequestHandler):
    server_version = "TramTaiNguyen/1.0"

    def log_message(self, *a):
        pass

    def _tra(self, ma, kieu, than):
        if isinstance(than, str):
            than = than.encode("utf-8")
        self.send_response(ma)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(than)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")     # cho tiện ích Chrome gọi vào
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(than)

    def _js(self, d, ma=200):
        self._tra(ma, "application/json; charset=utf-8",
                  json.dumps(d, ensure_ascii=False).encode())

    def _tep(self, p):
        if not os.path.exists(p):
            return self._tra(404, "text/plain; charset=utf-8", "không thấy tệp")
        kieu = mimetypes.guess_type(p)[0] or "application/octet-stream"
        self._tra(200, kieu, open(p, "rb").read())

    def _tep_khuc(self, p):
        """Phục vụ tệp CÓ Range (206) — video muốn TUA mượt trong <video> thì bắt buộc."""
        if not os.path.exists(p):
            return self._tra(404, "text/plain; charset=utf-8", "không thấy tệp")
        m = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range") or "")
        if not m:
            return self._tep(p)
        co = os.path.getsize(p)
        dau = int(m.group(1) or 0)
        cuoi = min(int(m.group(2)) if m.group(2) else co - 1, co - 1)
        if dau > cuoi:
            return self._tra(416, "text/plain; charset=utf-8", "khúc không hợp lệ")
        with open(p, "rb") as f:
            f.seek(dau)
            than = f.read(cuoi - dau + 1)
        self.send_response(206)
        self.send_header("Content-Type", mimetypes.guess_type(p)[0] or "video/mp4")
        self.send_header("Content-Length", str(len(than)))
        self.send_header("Content-Range", f"bytes {dau}-{cuoi}/{co}")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(than)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        d, q = u.path, urllib.parse.parse_qs(u.query)
        try:
            if d == "/api/phien-ban":                    # tab so mốc khởi động server
                return self._js({"v": PHIEN_BAN_TRAM})
            if d in ("/", "/index.html"):
                return self._tep(TRANG)
            if d == "/chon-anh":
                return self._tep(TRANG_CHON)
            if d.startswith("/api/ung-vien/"):
                viec = os.path.join(DD.VIEC, urllib.parse.unquote(d.split("/", 3)[3]))
                p_uv = os.path.join(viec, "anh", "ung-vien.json")
                if not os.path.exists(p_uv):
                    return self._js({})
                return self._js(json.load(open(p_uv, encoding="utf-8")))
            if d == "/api/viec":
                return self._js(_ds_viec())
            if d.startswith("/api/dang-keo/"):
                # trang poll để hiện "⏳ đang kéo x video · y ảnh về kho" (anh đặt 09/08)
                ma_k = urllib.parse.unquote(d.split("/", 3)[3])
                with KHOA:
                    d_k = dict(DANG_KEO.get(ma_k) or {"video": 0, "anh": 0, "xong": 0})
                d_k["ban_moi"] = dict(BAN_MOI)     # đi nhờ, khỏi đẻ đường hỏi mới
                return self._js(d_k)
            if d == "/kho-nha-duyet":
                return self._tep(os.path.join(TRAM, "kho-nha-duyet.html"))
            if d == "/phong-cach":                       # trang núm vặn chống dập khuôn
                return self._tep(os.path.join(TRAM, "phong-cach.html"))
            if d == "/thu-giong.mp3":                    # nghe lại bản vừa thử
                ma_g = (q.get("ma") or [""])[0]
                pt = os.path.join(tempfile.gettempdir(),
                                  f"thu-giong-{abs(hash(ma_g)) % 99999}.mp3")
                if not os.path.exists(pt):
                    return self._js({"loi": "chưa có bản thử — bấm ▶ Thử trước"}, 404)
                return self._tep(pt)
            if d == "/api/phong-cach":
                return self._js({"cau_hinh": PC.doc(), "mac_dinh": PC.MAC_DINH,
                                 "ten_viet": PC.TEN_VIET,
                                 "dem": {n: len(CN._bai_trong(n)) for n in PC.TEN_VIET}})
            if d == "/api/may-do":
                # DÒ HỘ NGƯỜI DÙNG (anh chốt 15/08: "nhân viên máy Windows muốn đẩy
                # lên Drive chia sẻ thì phải thay đường dẫn thế nào cho DỄ LÀM NHẤT").
                # Bắt người ta gõ tay một đường dẫn dài là thiết kế lười — máy quét
                # được thì máy phải quét, người chỉ việc BẤM CHỌN.
                import glob as _g
                loai = (q.get("loai", ["kho_tai_nguyen"])[0] or "").strip()
                nen = [os.path.expanduser("~/Library/CloudStorage"),   # macOS
                       os.path.expanduser("~"), "G:\\", "H:\\",     # Windows
                       "/Volumes", "D:\\", "E:\\"]
                ra_d, thay = [], set()

                def _them(duong, vi_sao):
                    duong = os.path.normpath(duong)
                    if duong in thay or not os.path.isdir(duong):
                        return
                    thay.add(duong)
                    try:
                        so = len([x for x in os.listdir(duong)[:400]])
                    except OSError:
                        so = 0
                    ra_d.append({"duong": duong, "vi_sao": vi_sao, "so_muc": so})

                def _quet(nen_ds, ten, sau=4):
                    """Tìm thư mục có tên CHỨA `ten`, trong vài cấp đầu.

                    KHÔNG dùng glob cho phần có dấu tiếng Việt: macOS lưu tên dạng NFD
                    (chữ và dấu tách rời), chuỗi trong mã là NFC — glob "*Sóc bóng đá*"
                    trượt sạch dù thư mục sờ sờ ra đó. Bài học đã ghi sổ, nay tái phát.
                    Nên: tự duyệt thư mục rồi SO CHUỖI ĐÃ CHUẨN HOÁ cả hai vế.
                    Không quét đệ quy cả ổ — Drive vài chục nghìn tệp, quét sâu là treo.
                    """
                    import unicodedata as _u
                    kim = _u.normalize("NFC", ten.strip("*")).lower()
                    # thư mục hệ thống / rác — vào đó là quét cả đời không xong
                    _BO = {"library", "applications", "system", "windows", ".git",
                           "node_modules", "__pycache__", "program files",
                           "program files (x86)", "$recycle.bin", "appdata"}
                    ra_q, tang = [], list(nen_ds)
                    for _ in range(sau):
                        ke = []
                        for n_ in tang:
                            try:
                                for x in os.listdir(n_):
                                    dd = os.path.join(n_, x)
                                    if (x.startswith(".") or x.lower() in _BO
                                            or not os.path.isdir(dd)):
                                        continue
                                    if kim in _u.normalize("NFC", x).lower():
                                        ra_q.append(dd)
                                    else:
                                        ke.append(dd)
                            except OSError:
                                pass
                        if len(ke) > 400:          # bề ngang quá rộng thì dừng, khỏi treo
                            break
                        tang = ke
                    return ra_q

                if loai == "kho_tai_nguyen":
                    # ưu tiên kho THẬT: thư mục tên kho-tai-nguyen, hoặc có sổ kho bên trong
                    if True:
                        for m in _quet(nen, "kho-tai-nguyen"):
                            dau = "đã có sổ kho ảnh" if os.path.exists(
                                os.path.join(m, "anh-chu-the", "so-chu-the.jsonl")) \
                                else "thư mục tên kho-tai-nguyen"
                            _them(m, ("trên Drive · " if "Drive" in m or "CloudStorage" in m
                                      else "") + dau)
                elif loai == "drive":
                    goc_dr = []
                    for n in nen:
                        goc_dr += _g.glob(os.path.join(n, "GoogleDrive-*", "*")) + \
                            _g.glob(os.path.join(n, "My Drive")) + \
                            _g.glob(os.path.join(n, "Drive của tôi"))
                    for k_ in _quet(goc_dr, "*Sóc bóng đá 247*", sau=3):
                        _them(k_, "✅ thư mục kênh — chọn cái này")
                    for m in goc_dr:
                        _them(m, "gốc Drive (kênh chưa có, sẽ tạo trong đây)")
                elif loai == "viec":
                    for n in ("/Volumes", "D:\\", "E:\\", os.path.expanduser("~")):
                        for m in _g.glob(os.path.join(n, "*", "socbongda247", "viec")) + \
                                _g.glob(os.path.join(n, "socbongda247", "viec")):
                            _them(m, "kho việc sẵn có")
                    for n in ("/Volumes", "D:\\", "E:\\"):
                        for m in _g.glob(os.path.join(n, "*")):
                            if os.path.isdir(m) and not os.path.basename(m).startswith("."):
                                _them(os.path.join(m, "socbongda247", "viec"),
                                      "ổ trống — sẽ tạo mới ở đây")
                # xếp: thứ CÓ THẬT và nhiều nội dung lên trước
                ra_d.sort(key=lambda x: (-x["so_muc"], len(x["duong"])))
                return self._js({"ds": ra_d[:8], "loai": loai})
            if d == "/api/may":                          # ĐỌC đường dẫn máy này
                p_m = os.path.expanduser("~/.config/socbongda247/may.json")
                try:
                    ch_m = json.load(open(p_m, encoding="utf-8"))
                except Exception:
                    ch_m = {}
                return self._js({"cau_hinh": ch_m, "dang_dung": {
                    "nguoi": DD.NGUOI, "drive": DD.DRIVE, "kho_nang": DD.DATA,
                    "viec": DD.VIEC, "kho_tai_nguyen": DD.KHO_TAI_NGUYEN,
                    "kho_video": DD.KHO_VIDEO}})
            if d == "/menu.js":
                return self._tep(os.path.join(TRAM, "menu.js"))
            if d == "/api/kho-nha-ds":
                # trang DUYỆT NHÃN kho (anh hỏi 10/08: kiểm nhãn đúng không, sai sửa đâu)
                q_k = (q.get("q") or [""])[0]
                loc = (q.get("loc") or ["tat_ca"])[0]
                trang_k = int((q.get("trang") or ["0"])[0])
                ds_k, so_cho = [], 0
                if os.path.exists(SO_CHU_THE):
                    for dong in open(SO_CHU_THE, encoding="utf-8"):
                        try:
                            m = json.loads(dong)
                        except Exception:
                            continue
                        if m.get("cho_nhan"):      # ảnh extension tải tay — đếm mọi lọc
                            so_cho += 1
                        # tách 2 loại (anh bắt 10/08 tưởng phải sửa 100%): "chưa nhìn"
                        # = nhãn thô mượn câu bài, máy SẼ tự thay — đừng sửa tay;
                        # "chưa chắc tên" = máy ĐÃ nhìn, tả đúng ảnh, chỉ thiếu tên riêng
                        if loc == "chua_chac" and (m.get("nhan_tho") or m.get("chu_the")):
                            continue
                        if loc == "chua_nhin" and not m.get("nhan_tho"):
                            continue
                        if loc == "cho_nhan" and not m.get("cho_nhan"):
                            continue
                        if loc in ("len_hinh", "du_tru") and m.get("hang") != loc:
                            continue
                        # lọc theo kết quả QUÉT WATERMARK (anh đặt 11/08)
                        if loc == "wm_chac" and m.get("wm_muc") != "chac":
                            continue
                        if loc == "wm_nghi" and m.get("wm_muc") != "nghi":
                            continue
                        if loc == "wm_chua" and m.get("wm_quet"):
                            continue
                        if q_k:
                            kh = _diem_khop(q_k, [(m.get("chu_the", ""), 3),
                                                  (" ".join(m.get("nhan", [])), 2),
                                                  (m.get("mo_ta", ""), 1)])
                            if not kh:
                                continue
                            m["_kh"] = kh
                        ds_k.append(m)
                if q_k:                            # có truy vấn: xếp theo độ khớp
                    ds_k.sort(key=lambda m: -m.pop("_kh", 0))
                else:
                    ds_k.sort(key=lambda m: (not m.get("nhan_tho"),
                                             m.get("chu_the", "") != "",
                                             m.get("luc_nhap", "")))
                return self._js({"tong": len(ds_k), "so_cho_nhan": so_cho,
                                 "ds": ds_k[trang_k * 60:(trang_k + 1) * 60]})
            if d == "/api/kho-video-bai":
                # 🎬 ĐOẠN VIDEO KHO HỢP BÀI (anh đặt 11/08: "kho ứng viên không thấy đề
                # xuất video có sẵn — làm 2 tab ảnh/video, tìm kiếm như nhau").
                # CÙNG THƯỚC CHẤM với ảnh: q tay → _diem_khop (nghiêm); không q → _diem_mem
                # theo chữ của bài (tiêu đề + từ khoá + hồ sơ), phạt đội lạ như ảnh.
                ma_vb = (q.get("ma") or [""])[0]
                q_vb = (q.get("q") or [""])[0]
                # BỘ LỌC GỐC / ĐÃ CẮT (anh đặt 16/08). Lọc ở ĐÂY chứ không ở trang: danh
                # sách bị cắt còn 60 đoạn trước khi trả về, lọc phía trang là mất bớt.
                loc_vb = (q.get("loai") or [""])[0]        # "" | goc | cat
                viec_vb = os.path.join(DD.VIEC, ma_vb)
                chuoi_bai = ""
                try:
                    kb_vb = json.load(open(os.path.join(viec_vb, "kich-ban.json"),
                                           encoding="utf-8"))
                    nh_vb = _nhap(viec_vb)
                    hs_vb = _doc_ho_so_bai(ma_vb)
                    chuoi_bai = " ".join(
                        [kb_vb.get("tieu_de", "")]
                        + [str(v) for v in (nh_vb.get("tu_khoa") or {}).values()]
                        + (hs_vb.get("nhan_vat") or []) + (hs_vb.get("doi") or []))
                except Exception:
                    pass
                tu_bai = _bo_dau_k(chuoi_bai).split()
                doi_bai = _doi_trong(chuoi_bai)
                ds_vb = []
                for m in _so_video_ct():
                    # đoạn LÀ QUẢNG CÁO (mô tả mắt máy mở đầu bằng "Quảng cáo"/"Khung
                    # quảng cáo") thì không bày — kiểm kho 11/08 thấy 12 đoạn Samsung/
                    # đăng-ký-kênh lọt đề xuất. CHỈ lọc mô tả MỞ ĐẦU vậy: cảnh thật có
                    # biển quảng cáo sau lưng cầu thủ vẫn phải được bày, lọc theo chữ
                    # ở giữa câu là oan.
                    # mục cũ không ghi `loai` thì coi là ĐOẠN CẮT — kho sinh ra từ
                    # việc cắt, video gốc mới là ngoại lệ và luôn được ghi nhãn rõ.
                    loai_m = "goc" if m.get("loai") == "goc" else "cat"
                    if loc_vb in ("goc", "cat") and loai_m != loc_vb:
                        continue
                    mo_v = (m.get("mo_ta", "") or "").strip().lower()
                    if mo_v.startswith(("quảng cáo", "khung quảng cáo")):
                        continue
                    chu_v = " ".join([m.get("chu_the", ""),
                                      " ".join(m.get("nhan", [])),
                                      m.get("mo_ta", ""), m.get("tieu_de", "")])
                    if _bo_dau_k(q_vb).strip():    # tìm tay: nghiêm, trượt là loại
                        diem = _diem_khop(q_vb, [(m.get("chu_the", ""), 3),
                                                 (" ".join(m.get("nhan", [])), 2),
                                                 (m.get("mo_ta", "") + " "
                                                  + m.get("tieu_de", ""), 1)])
                        if not diem:
                            continue
                    else:                          # bày theo liên quan: mềm, không lọc trơn
                        diem = _diem_mem(tu_bai, [
                            (_bo_dau_k(m.get("chu_the", "")).split(), 3),
                            (_bo_dau_k(" ".join(m.get("nhan", []))).split(), 2),
                            (_bo_dau_k(m.get("mo_ta", "") + " "
                                       + m.get("tieu_de", "")).split(), 1)])
                    # đoạn nhắc ĐỘI LẠ (không có trong bài) → xuống hạng như ảnh
                    if doi_bai and (_doi_trong(chu_v) - doi_bai):
                        diem *= 0.4
                    ds_vb.append((diem, m))
                ds_vb.sort(key=lambda x: -x[0])
                _tat = [m for m in _so_video_ct()
                        if not (m.get("mo_ta", "") or "").strip().lower()
                        .startswith(("quảng cáo", "khung quảng cáo"))]
                so_goc = len([m for m in _tat if m.get("loai") == "goc"])
                ra_vb = [{"tep": m["tep"], "tu": m.get("tu", 0), "den": m.get("den", 0),
                          "giay": round(float(m.get("den", 0)) - float(m.get("tu", 0)), 1),
                          "loai": m.get("loai", ""),   # goc | cat — nhãn phân biệt (11/08)
                          "thumb": "/kho-video-thumb/" + (m.get("thumb") or ""),
                          "chu_the": m.get("chu_the", ""),
                          "nhan": (m.get("nhan") or [])[:4],
                          "mo_ta": (m.get("mo_ta", "") or "")[:140]}
                         for diem, m in ds_vb[:60]]
                return self._js({"tong": len(ds_vb), "ds": ra_vb,
                                 "so_goc": so_goc, "so_cat": len(_tat) - so_goc})
            if d == "/api/kho-wm-quet":
                # 🧽 QUÉT WATERMARK CẢ KHO (anh đặt 11/08: "tìm tất cả ảnh có watermark
                # để cắt/xoá một lần, định kỳ quét lại"). Dùng ĐÚNG cổng OCR của cửa
                # nhập (do_logo + DAU_NGUON) — không đẻ tiêu chuẩn thứ hai.
                # Mặc định chỉ quét ảnh CHƯA quét lần nào (`wm_quet`) — quét lại cả kho
                # thì gửi lai=1. Kết quả ghi thẳng vào sổ để lần sau lọc là có ngay.
                lai_q = bool(than.get("lai"))
                ma_job = f"wq{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "soi watermark cả kho"}

                def chay_wq(mj=ma_job, lai=lai_q):
                    try:
                        nhin, vi_sao = lay_anh._ocr_song_khong()
                        if not nhin:
                            with KHOA:
                                VIEC_JOB[mj] = {"xong": True,
                                                "loi": f"cổng OCR mù — {vi_sao}"}
                            return
                        dl_q = lay_anh._do_logo()
                        with KHOA:
                            ds_q = [json.loads(l) for l in
                                    open(SO_CHU_THE, encoding="utf-8") if l.strip()]
                        can = [m for m in ds_q
                               if (lai or not m.get("wm_quet"))
                               and os.path.exists(os.path.join(KHO_CHU_THE,
                                                               m.get("tep", "")))]
                        if not can:
                            with KHOA:
                                VIEC_JOB[mj] = {"xong": True, "quet": 0, "dinh": 0,
                                                "nghi": 0}
                            return
                        ket = {}

                        def _soi_mot(m):
                            p = os.path.join(KHO_CHU_THE, m["tep"])
                            try:
                                return m["tep"], dl_q.do_chu(p, la_anh=True)
                            except Exception:
                                return m["tep"], None
                        xong_q = 0
                        with cf.ThreadPoolExecutor(max_workers=8) as ex:
                            for tep_q, doc in ex.map(_soi_mot, can):
                                xong_q += 1
                                if xong_q % 10 == 0:
                                    with KHOA:
                                        VIEC_JOB[mj] = {
                                            "xong": False,
                                            "buoc": f"soi watermark {xong_q}/{len(can)}",
                                            "da": xong_q, "tong": len(can)}
                                if doc is None:
                                    continue
                                vung = []
                                for ten_v, chu in doc.items():
                                    if not (chu or "").strip():
                                        continue
                                    chac = bool(lay_anh.DAU_NGUON.search(chu))
                                    if not chac and ten_v not in lay_anh.VUNG_CHAN:
                                        continue
                                    x0, y0, x1, y1 = dl_q.VUNG[ten_v]
                                    vung.append({"ten": ten_v, "chu": chu[:60],
                                                 "chac": chac,
                                                 "x": round(x0, 4), "y": round(y0, 4),
                                                 "w": round(x1 - x0, 4),
                                                 "h": round(y1 - y0, 4)})
                                ket[tep_q] = vung
                        luc_q = datetime.now().strftime("%Y-%m-%d %H:%M")
                        dinh = nghi = 0
                        with KHOA:
                            ds_q = [json.loads(l) for l in
                                    open(SO_CHU_THE, encoding="utf-8") if l.strip()]
                            for m in ds_q:
                                if m.get("tep") not in ket:
                                    continue
                                v = ket[m["tep"]]
                                m["wm_quet"] = luc_q
                                m["wm_vung"] = v
                                m["wm_muc"] = ("chac" if any(x["chac"] for x in v)
                                               else "nghi" if v else "sach")
                                dinh += m["wm_muc"] == "chac"
                                nghi += m["wm_muc"] == "nghi"
                            with open(SO_CHU_THE, "w", encoding="utf-8") as f:
                                for m in ds_q:
                                    f.write(json.dumps(m, ensure_ascii=False) + "\n")
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "quet": len(ket),
                                            "dinh": dinh, "nghi": nghi}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": str(e)}
                threading.Thread(target=chay_wq, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/kho-wm-xu":
                # XỬ HÀNG LOẠT ảnh dính watermark: "xoa" = LaMa vá tại chỗ (giữ khuôn
                # hình — nên vẫn nhận ra trùng về sau), "cat" = cắt bỏ dải chứa vùng.
                # ĐÈ LUÔN ảnh gốc như anh dặn; bản gốc cất thùng rác để hoàn.
                kieu_x = than.get("kieu") if than.get("kieu") in ("xoa", "cat") else "xoa"
                tep_ds_x = [os.path.basename(t) for t in (than.get("tep_ds") or [])]
                if not tep_ds_x:
                    return self._js({"loi": "chưa chọn ảnh nào"}, 400)
                ma_job = f"wx{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "đang xử watermark"}

                def chay_wx(mj=ma_job, ds_t=tep_ds_x, kieu=kieu_x):
                    lama = os.path.expanduser("~/.cache/lama-venv/bin/python3")
                    rac = os.path.join(KHO_CHU_THE, "thung-rac")
                    os.makedirs(rac, exist_ok=True)
                    with KHOA:
                        so_x = [json.loads(l) for l in
                                open(SO_CHU_THE, encoding="utf-8") if l.strip()]
                    theo = {m.get("tep"): m for m in so_x}
                    xong_x, loi_x = 0, []
                    for n_x, tep in enumerate(ds_t, 1):
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": False,
                                            "buoc": f"{'xoá' if kieu == 'xoa' else 'cắt'}"
                                                    f" watermark {n_x}/{len(ds_t)}",
                                            "da": n_x, "tong": len(ds_t)}
                        m = theo.get(tep)
                        p = os.path.join(KHO_CHU_THE, tep)
                        vung = (m or {}).get("wm_vung") or []
                        if not (m and os.path.exists(p) and vung):
                            loi_x.append(f"{tep}: chưa quét hoặc không có vùng")
                            continue
                        goc = os.path.join(rac, tep + ".goc-wm")
                        try:
                            if kieu == "cat":
                                im_x = Image.open(p).convert("RGB")
                                W_x, H_x = im_x.size
                                # cắt bỏ dải chứa MỌI vùng dính, theo mép gần nhất
                                tren = max([v["y"] + v["h"] for v in vung
                                            if v["y"] + v["h"] <= 0.35] or [0])
                                duoi = min([v["y"] for v in vung if v["y"] >= 0.65]
                                           or [1])
                                y0_x, y1_x = int(H_x * tren), int(H_x * duoi)
                                if y1_x - y0_x < H_x * 0.5:
                                    loi_x.append(f"{tep}: cắt xong còn quá ít hình")
                                    continue
                                os.path.exists(goc) or shutil.copy2(p, goc)
                                im_x.crop((0, y0_x, W_x, y1_x)).save(p, quality=92)
                            else:
                                if not os.path.exists(lama):
                                    loi_x.append("chưa cài venv LaMa")
                                    break
                                ra_x = p + ".va.jpg"
                                with WM_KHOA:      # MỘT LaMa một lúc (bài học sập nguồn)
                                    r_x = subprocess.run(
                                        [lama, os.path.join(DD.MAY, "xoa_wm.py"),
                                         "--anh", p, "--ra", ra_x, "--kieu", "tu",
                                         "--vung"]
                                        + [f"{v['x']},{v['y']},{v['w']},{v['h']}"
                                           for v in vung],
                                        capture_output=True, text=True, timeout=300,
                                        cwd="/tmp")
                                if not (r_x.returncode == 0 and os.path.exists(ra_x)):
                                    loi_x.append(f"{tep}: LaMa hỏng")
                                    continue
                                os.path.exists(goc) or shutil.copy2(p, goc)
                                os.replace(ra_x, p)
                            # VÂN TAY phải tính lại cho ảnh MỚI — không thì cổng chống
                            # trùng còn nhớ vân của bản có watermark
                            im_m = Image.open(p)
                            for ten_s, ham in (("van-tay.json", gap_anh._dhash),
                                               ("van-tay-loi.json", gap_anh._dhash_loi)):
                                p_s = os.path.join(KHO_CHU_THE, ten_s)
                                s_v = json.load(open(p_s)) if os.path.exists(p_s) else {}
                                s_v[tep] = str(ham(im_m))
                                json.dump(s_v, open(p_s, "w"))
                            m["wm_vung"] = []
                            m["wm_muc"] = "sach"
                            m["wm_da_xu"] = f"{kieu}·{datetime.now():%Y-%m-%d %H:%M}"
                            m["nguoi_sua"] = True
                            xong_x += 1
                        except Exception as e:
                            loi_x.append(f"{tep}: {e}")
                    with KHOA:
                        with open(SO_CHU_THE, "w", encoding="utf-8") as f:
                            for m in so_x:
                                f.write(json.dumps(m, ensure_ascii=False) + "\n")
                    with KHOA:
                        VIEC_JOB[mj] = {"xong": True, "so": xong_x,
                                        "loi_ds": loi_x[:5]}
                threading.Thread(target=chay_wx, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/kho-nhan-goiy":
                # GỢI Ý NHÃN ĐÃ CÓ (anh đặt 11/08): gom nhãn + chủ thể của CẢ kho ảnh
                # lẫn kho video kèm tần suất, trả MỘT lần — client lọc KHÔNG DẤU tức
                # thì khi gõ, khỏi gọi lại mỗi phím. Cache theo mtime hai sổ.
                try:
                    mt_g = (os.path.getmtime(SO_CHU_THE) if os.path.exists(SO_CHU_THE) else 0,
                            os.path.getmtime(SO_VIDEO_CT) if os.path.exists(SO_VIDEO_CT) else 0)
                except OSError:
                    mt_g = (0, 0)
                if _NHAN_GOIY.get("mt") != mt_g:
                    dem_g = {}
                    for p_g in (SO_CHU_THE, SO_VIDEO_CT):
                        if not os.path.exists(p_g):
                            continue
                        for dong_g in open(p_g, encoding="utf-8"):
                            try:
                                m_g = json.loads(dong_g)
                            except Exception:
                                continue
                            for n_g in (m_g.get("nhan") or []) + ([m_g["chu_the"]]
                                        if m_g.get("chu_the") else []):
                                n_g = str(n_g).strip()
                                # nhãn năm ("2026") hay chuỗi quá ngắn không đáng gợi
                                if len(n_g) < 3 or n_g.isdigit():
                                    continue
                                k_g = n_g.lower()
                                if k_g in dem_g:
                                    dem_g[k_g][1] += 1
                                else:
                                    dem_g[k_g] = [n_g, 1]
                    _NHAN_GOIY.update(mt=mt_g, ds=sorted(
                        ({"n": v[0], "d": v[1], "k": _bo_dau_k(v[0])}
                         for v in dem_g.values()), key=lambda x: -x["d"]))
                return self._js({"ds": _NHAN_GOIY.get("ds") or []})
            if d == "/api/kho-video-ds":
                q_k = (q.get("q") or [""])[0]
                loc = (q.get("loc") or ["tat_ca"])[0]
                trang_k = int((q.get("trang") or ["0"])[0])
                ds_k = []
                for m in _so_video_ct():
                    if loc == "chua_chac" and (m.get("nhan_tho") or m.get("chu_the")):
                        continue
                    if loc == "chua_nhin" and not m.get("nhan_tho"):
                        continue
                    if _bo_dau_k(q_k).strip():
                        kh = _diem_khop(q_k, [(m.get("chu_the", ""), 3),
                                              (" ".join(m.get("nhan", [])), 2),
                                              (m.get("mo_ta", "") + " "
                                               + m.get("tieu_de", ""), 1)])
                        if not kh:
                            continue
                        m["_kh"] = kh
                    ds_k.append(m)
                if _bo_dau_k(q_k).strip():
                    ds_k.sort(key=lambda m: -m.pop("_kh", 0))
                dang_tai = os.path.exists(os.path.join(KHO_VIDEO_CT, ".dang-tai"))
                return self._js({"tong": len(ds_k), "dang_tai": dang_tai,
                                 "ds": ds_k[trang_k * 60:(trang_k + 1) * 60]})
            if d.startswith("/kho-video-thumb/"):
                t_v = os.path.basename(urllib.parse.unquote(d.split("/", 2)[2]))
                return self._tep(os.path.join(KHO_VIDEO_CT, "thumb", t_v))
            if d.startswith("/kho-video-xem/"):
                t_v = os.path.basename(urllib.parse.unquote(d.split("/", 2)[2]))
                return self._tep_khuc(os.path.join(KHO_VIDEO_CT, t_v))
            if d == "/api/kho-nha-chuthe":
                # THẺ CHỦ THỂ bấm chọn (anh đặt 10/08: đỡ gõ tay) — trộn bộ tên quen
                # của kênh + các tên đã có trong sổ (đếm tần suất), anh gõ tên mới một
                # lần là lần sau tự thành thẻ
                SEED = ["Nguyễn Đình Bắc", "Nguyễn Xuân Son", "Quang Hải", "Tiến Linh",
                        "Hoàng Đức", "Kim Sang-sik", "Tuyển Việt Nam", "Tuyển Malaysia",
                        "Tuyển Thái Lan", "Tuyển Indonesia", "Tuyển Campuchia"]
                dem = {}
                if os.path.exists(SO_CHU_THE):
                    for dong in open(SO_CHU_THE, encoding="utf-8"):
                        try:
                            ct = _chuan_hoa_ct(json.loads(dong).get("chu_the", ""))
                        except Exception:
                            continue
                        if ct:
                            dem[ct] = dem.get(ct, 0) + 1
                for s_ct in SEED:
                    dem.setdefault(_chuan_hoa_ct(s_ct) or s_ct, dem.get(s_ct, 0))
                ra_ct = [{"ten": t, "so": n} for t, n in
                         sorted(dem.items(), key=lambda x: -x[1])]
                return self._js(ra_ct[:40])
            if d == "/api/kho-nha":
                # KHO CHỦ THỂ dùng chung (anh chốt 10/08): tra theo NHÃN bằng code thuần
                # — không tốn model; ảnh đã sạch watermark + qua soi từ lúc nhập
                return self._js(_kho_nha_tim((q.get("q") or [""])[0]))
            if d == "/api/ung-vien-canh":
                # ỨNG VIÊN CHO MỘT CẢNH — nguồn nuôi CHẾ ĐỘ GÁN NHANH (anh đặt 11/08
                # khuya: "khâu tìm và gán cảnh là đau đầu nhất vì chậm"). Trộn 3 nguồn
                # theo đúng thứ tự tin cậy: ① model xếp theo nghĩa · ② kho nhà khớp từ
                # khoá (đã lọc đội lạ, có sổ học) · ③ ảnh web đã tìm sẵn.
                ma_u = urllib.parse.unquote((q.get("ma") or [""])[0])
                cau_u = int((q.get("cau") or ["0"])[0])
                # Ô PHỤ cũng phải có ứng viên (luật anh: cảnh chính có gì cảnh phụ có
                # nấy — em quên lần thứ tư, 11/08). phan="" là ô chính.
                phan_u = (q.get("phan") or [""])[0]
                so_u = min(int((q.get("so") or ["8"])[0]), 16)
                viec_u = os.path.join(DD.VIEC, ma_u)
                nh_u = _nhap(viec_u)
                tk_u = ((nh_u.get("tu_khoa_phu") or {}).get(str(cau_u), {})
                        .get(phan_u, "") if phan_u != "" else "") \
                    or (nh_u.get("tu_khoa") or {}).get(str(cau_u), "")
                dang_dung_u = {os.path.basename(str(v))
                               for v in (nh_u.get("ban_do") or {}).values() if v}
                for ds_ap in (nh_u.get("anh_phu") or {}).values():
                    dang_dung_u |= {os.path.basename(str(x)) for x in (ds_ap or []) if x}
                ra_u, thay_u = [], set()
                kh_o = f"{cau_u}:{phan_u}" if phan_u != "" else str(cau_u)
                # ① model xếp theo nghĩa (khoá ô: "3" cho chính, "3:0" cho phụ)
                for t in ((_doc_kho_xep(ma_u).get("xep") or {})
                          .get(kh_o, {}).get("tep") or []):
                    if t in thay_u or t in dang_dung_u:
                        continue
                    thay_u.add(t)
                    ra_u.append({"u": "/kho-nha-anh/" + t, "tep": t, "nguon": "may",
                                 "nhan": "🧠 máy chọn"})
                # ② kho nhà theo từ khoá câu — dùng đúng bộ lọc của dải kho (đội lạ đã
                #    bị loại, sổ học đã cộng điểm) rồi giữ tấm hợp CHÍNH câu này
                if len(ra_u) < so_u and tk_u.strip():
                    for m in _kho_nha_bai(ma_u, gioi_han=60, q=tk_u).get("ds", []):
                        if len(ra_u) >= so_u:
                            break
                        if m["tep"] in thay_u or m["tep"] in dang_dung_u:
                            continue
                        thay_u.add(m["tep"])
                        ra_u.append({"u": m["u"], "tep": m["tep"], "nguon": "kho",
                                     "nhan": "🏠 " + (m.get("chu_the")
                                                      or (m.get("nhan") or [""])[0])[:22]})
                # ③ ảnh web đã tìm sẵn
                if len(ra_u) < so_u:
                    try:
                        uv_u = json.load(open(os.path.join(viec_u, "anh",
                                                           "ung-vien.json"),
                                              encoding="utf-8"))
                    except Exception:
                        uv_u = {}
                    for a in (uv_u.get(str(cau_u), {}).get("anh") or []):
                        if len(ra_u) >= so_u:
                            break
                        if a.get("u") in thay_u or not a.get("du_net"):
                            continue
                        thay_u.add(a["u"])
                        ra_u.append({"u": a["u"], "nguon": "web",
                                     "nhan": "🌐 " + (a.get("tieu_de") or "ảnh web")[:22]})
                return self._js({"cau": cau_u, "phan": phan_u,
                                 "tu_khoa": tk_u, "ds": ra_u})
            if d == "/api/kho-nha-bai":
                # CẢ KHO liên quan bài này, xếp theo mức liên quan — 150 tấm mỗi lượt,
                # bấm "gọi thêm" là lấy tiếp (anh đặt 11/08)
                return self._js(_kho_nha_bai(
                    urllib.parse.unquote((q.get("ma") or [""])[0]),
                    gioi_han=min(int((q.get("gioi_han") or ["150"])[0]), 300),
                    bo_qua=int((q.get("bo_qua") or ["0"])[0]),
                    q=(q.get("q") or [""])[0]))
            if d.startswith("/kho-nha-thu-wm/"):
                # bản THỬ xoá watermark — anh soi trước/sau rồi mới chốt thay
                ten_k = os.path.basename(urllib.parse.unquote(d.split("/", 2)[2]))
                p_k = os.path.join(KHO_CHU_THE, "thung-rac", "thu-wm", ten_k)
                if ".." in ten_k or not os.path.exists(p_k):
                    return self._tra(404, "text/plain", "khong thay")
                return self._tep(p_k)
            if d.startswith("/kho-nha-anh/"):
                ten_k = os.path.basename(urllib.parse.unquote(d.split("/", 2)[2]))
                p_k = os.path.join(KHO_CHU_THE, ten_k)
                if ".." in ten_k or not os.path.exists(p_k):
                    return self._tra(404, "text/plain", "khong thay")
                ma_dung = (q.get("ma") or [""])[0]
                if ma_dung:                        # ảnh được LẤY về một bài → ghi sổ đã dùng
                    _kho_nha_da_dung(ten_k, ma_dung)
                    # SỔ HỌC: chỉ ghi khi ANH tự chọn (?cau=), không ghi lượt máy tự gán —
                    # máy học chính mình thì càng ngày càng lệch (11/08)
                    c_hoc = (q.get("cau") or [""])[0]
                    if c_hoc.isdigit():
                        try:
                            viec_h = os.path.join(DD.VIEC, ma_dung)
                            kb_h = json.load(open(os.path.join(viec_h, "kich-ban.json"),
                                                  encoding="utf-8"))
                            cau_h = _tach_cau(kb_h.get("loi_binh", ""))
                            i_h = int(c_hoc)
                            m_h = next((json.loads(l) for l in
                                        open(SO_CHU_THE, encoding="utf-8") if l.strip()
                                        and json.loads(l).get("tep") == ten_k), None)
                            if m_h and i_h < len(cau_h):
                                _ghi_hoc_ghep(ma_dung, cau_h[i_h],
                                              (_nhap(viec_h).get("tu_khoa") or {})
                                              .get(str(i_h), ""), m_h)
                        except Exception:
                            pass
                return self._tep(p_k)
            if d == "/api/dang-lam":
                ma = _dang_lam() or (_ds_viec() or [{}])[0].get("ma", "")
                try:
                    k = json.load(open(os.path.join(DD.VIEC, ma, "kich-ban.json"),
                                       encoding="utf-8"))
                except Exception:
                    k = {}
                # PHIÊN BẢN EXTENSION (anh hỏi 15/08). Extension nạp kiểu "giải
                # nén": `git pull` về file mới nhưng Chrome vẫn chạy bản đã nạp cho
                # tới khi bấm ⟳ Tải lại. Đây là lỗi ÂM THẦM — mọi thứ trông vẫn
                # chạy, chỉ là thiếu tính năng vừa thêm. Nay so ngay tại cửa
                # extension vốn đã gọi, không tốn thêm lượt nào.
                ext = (q.get("ext", [""])[0] or "").strip()
                ext_moi = ""
                try:
                    ext_moi = str(json.load(open(
                        os.path.join(TRAM, "extension", "manifest.json"),
                        encoding="utf-8")).get("version", ""))
                except Exception:
                    pass
                return self._js({"ma": ma, "tieu_de": k.get("tieu_de", ""),
                                 "ext_moi": ext_moi,
                                 "ext_cu": bool(ext and ext_moi and ext != ext_moi)})
            if d == "/api/dong-ho":
                # ⏱ ĐỒNG HỒ SẢN XUẤT (anh đặt 14/08) — trạm hỏi mỗi vài giây để vẽ ô
                # góc màn hình. Trả mốc THÔ + tổng kết; đếm từng giây do trình duyệt lo,
                # server không phải thức canh.
                ma_dh = (q.get("ma", [""])[0] or "").strip()
                v_dh = os.path.join(DD.VIEC, ma_dh) if ma_dh else ""
                if not v_dh or not os.path.isdir(v_dh):
                    return self._js({"co": False})
                tk_dh = DH.tong_ket(v_dh)
                # JOB ĐANG CHẠY của bài (anh bắt 14/08: reload trang là mất thanh %,
                # "không biết có đang chạy hay không") — quét VIEC_JOB tìm job chưa
                # xong mang mã bài này, trang vẽ lại thanh % từ đây.
                j_dh = None
                with KHOA:
                    for jid, jv in VIEC_JOB.items():
                        if not jv.get("xong") and VIEC_JOB_MA.get(jid) == ma_dh:
                            j_dh = {"buoc": jv.get("buoc", ""),
                                    "da": jv.get("da"), "tong": jv.get("tong")}
                return self._js({"co": True, "moc": DH.doc(v_dh),
                                 "tong_giay": tk_dh["tong_giay"],
                                 "cac_buoc": tk_dh["cac_buoc"], "text": tk_dh["text"],
                                 "job": j_dh})
            if d == "/api/nhac-nho":
                # 📥📦 HAI LỖ HỔNG IM LẶNG của luồng nhập kho (anh duyệt vá 11/08):
                # ① ảnh extension tải về nằm ngăn chờ-nhãn mà không ai nhắc ở trạm chính;
                # ② bài dựng xong >1 ngày chưa xếp kho → ảnh tốt không vào kho chung.
                so_cho = 0
                try:
                    for dong_n in open(SO_CHU_THE, encoding="utf-8"):
                        try:
                            if json.loads(dong_n).get("cho_nhan"):
                                so_cho += 1
                        except Exception:
                            pass
                except OSError:
                    pass
                chua_xep = []
                # ĐỐI CHIẾU SỔ KHO THÀNH PHẨM, đừng chỉ tin cờ (anh bắt 12/08: ba bài
                # ĐÃ có hộp trên Drive vẫn bị nhắc "chưa xếp kho"). Lý do: cờ
                # `da_xep_kho` mới thêm 12/08, bài xếp kho trước đó không có cờ — mà
                # mốc lọc lại để từ 11/08 nên bắt oan đúng ngày cờ ra đời.
                # Sự thật nằm ở sổ kho: bài nào có tiêu đề trong đó là đã xếp rồi.
                tit_da_xep = set()
                try:
                    p_so_kho = os.path.join(os.path.dirname(DD.KHO_VIDEO_PY),
                                            "..", "kho-video-thanh-pham",
                                            "SO-VIDEO.jsonl")
                    for dong_k in open(os.path.normpath(p_so_kho), encoding="utf-8"):
                        try:
                            tit_da_xep.add(_bo_dau_k(json.loads(dong_k)
                                                     .get("tieu_de", ""))[:60])
                        except Exception:
                            pass
                except OSError:
                    pass
                try:
                    for ngay_n in sorted(os.listdir(DD.VIEC), reverse=True)[:4]:
                        if ngay_n.startswith("."):
                            continue
                        d_ng = os.path.join(DD.VIEC, ngay_n)
                        for b_n in (os.listdir(d_ng) if os.path.isdir(d_ng) else []):
                            v_n = os.path.join(d_ng, b_n)
                            p_v = os.path.join(v_n, "video.mp4")
                            if not os.path.exists(p_v):
                                continue
                            if time.time() - os.path.getmtime(p_v) < 24 * 3600:
                                continue
                            try:
                                kb_n = json.load(open(os.path.join(v_n, "kich-ban.json"),
                                                      encoding="utf-8"))
                            except Exception:
                                continue
                            if kb_n.get("da_xep_kho"):
                                continue
                            tit_n = _bo_dau_k(kb_n.get("tieu_de", ""))[:60]
                            if tit_n and tit_n in tit_da_xep:
                                # có trong sổ kho rồi → gắn cờ luôn, khỏi soi lại lần sau
                                try:
                                    KB_SO.ghi_gop(v_n, {"da_xep_kho": "(hồi tố từ sổ kho)"})
                                except Exception:
                                    pass
                                continue
                            chua_xep.append({"ma": f"{ngay_n}/{b_n}",
                                             "tieu_de": kb_n.get("tieu_de", "")[:60]})
                except OSError:
                    pass
                return self._js({"cho_nhan": so_cho, "chua_xep": chua_xep[:5]})
            if d.startswith("/api/kho-moi/"):
                # Chỉ trả SỐ ẢNH + mốc thời gian mới nhất, không trả cả danh sách — giao diện
                # hỏi mỗi vài giây nên phải rẻ. Khác số cũ thì giao diện mới đi lấy danh sách.
                viec = os.path.join(DD.VIEC, urllib.parse.unquote(d.split("/", 3)[3]))
                ds = [p for t in THU_ANH
                      for p in glob.glob(os.path.join(viec, t, "*.jpg"))]
                # đếm cả clip gắp tay — để trang đang mở tự thấy clip vừa về
                ds += glob.glob(os.path.join(viec, "clip", "tay", "*.mp4"))
                return self._js({"so": len(ds),
                                 "moi": max((os.path.getmtime(x) for x in ds), default=0)})
            if d.startswith("/api/viec/"):
                return self._js(_chi_tiet(urllib.parse.unquote(d.split("/", 3)[3])))
            if (d.startswith("/api/gap/") or d.startswith("/api/goi-y/")
                    or d.startswith("/api/dung/") or d.startswith("/api/loc/")
                    or d.startswith("/api/xem-truoc/") or d.startswith("/api/lay-chon/")
                    or d.startswith("/api/tim-loat/") or d.startswith("/api/nhan-video/")):
                with KHOA:
                    return self._js(VIEC_JOB.get(d.split("/", 3)[3], {"xong": False}))
            if d == "/api/lenh":
                if not os.path.exists(HANG_DOI):
                    return self._js([])
                return self._js([json.loads(x) for x in open(HANG_DOI, encoding="utf-8")][-30:])
            if d.startswith("/video/"):
                viec = os.path.join(DD.VIEC, urllib.parse.unquote(d.split("/", 2)[2]))
                # _tep_khuc chứ không phải _tep: trả nguyên khối là <video> hết tua
                # (trình duyệt cần Range/206 mới nhảy vị trí được) — anh bắt 08/08.
                return self._tep_khuc(os.path.join(viec, "video.mp4"))
            if d.startswith("/clip-doan-tep/"):
                # phát BẢN ĐÃ CẮT của một đoạn: /clip-doan-tep/<mã>/clip/tay/<tệp>?tu=..&den=..
                phan = urllib.parse.unquote(d.split("/", 2)[2])
                i = phan.rfind("/clip/tay/")
                if i < 0:
                    return self._tra(400, "text/plain; charset=utf-8", "không thấy ngăn clip")
                ma_c, ten = phan[:i], phan[i + len("/clip/tay/"):]
                if "/" in ten or ".." in ten or ".." in ma_c or not ten.endswith(".mp4"):
                    return self._tra(400, "text/plain; charset=utf-8", "đường dẫn không hợp lệ")
                try:
                    tu = max(0.0, min(float((q.get("tu") or ["0"])[0]), 3600.0))
                    den = max(tu + 0.1, min(float((q.get("den") or ["3"])[0]), 3600.0))
                except ValueError:
                    return self._tra(400, "text/plain; charset=utf-8", "mốc không hợp lệ")
                khung_q = None
                try:                               # &kh=x,y,w,h → bản xem là KHUNG ĐÃ CẮT
                    so_kh = [float(t) for t in (q.get("kh") or [""])[0].split(",")]
                    if len(so_kh) == 4 and all(0 <= v <= 1 for v in so_kh):
                        khung_q = dict(zip("xywh", so_kh))
                except ValueError:
                    pass
                return self._tep_khuc(
                    _cat_doan(os.path.join(DD.VIEC, ma_c), ten, tu, den, khung_q))
            if d.startswith("/clip-thumb/"):
                # hình mồi của clip tại giây t: /clip-thumb/<mã>/clip/tay/<tệp>?t=2.0
                phan = urllib.parse.unquote(d.split("/", 2)[2])
                i = phan.rfind("/clip/tay/")
                if i < 0:
                    return self._tra(400, "text/plain; charset=utf-8", "không thấy ngăn clip")
                ma_c, ten = phan[:i], phan[i + len("/clip/tay/"):]
                if "/" in ten or ".." in ten or ".." in ma_c or not ten.endswith(".mp4"):
                    return self._tra(400, "text/plain; charset=utf-8", "đường dẫn không hợp lệ")
                try:
                    t = max(0.0, min(float((q.get("t") or ["0"])[0]), 3600.0))
                except ValueError:
                    t = 0.0
                return self._tep(_thumb_clip(os.path.join(DD.VIEC, ma_c), ten, t))
            if d.startswith("/clip/"):
                # tệp clip gắp tay: /clip/<mã việc>/clip/tay/<tệp> — chỉ .mp4/.jpg trong ngăn tay
                phan = urllib.parse.unquote(d.split("/", 2)[2])
                i = phan.rfind("/clip/tay/")
                if i < 0:
                    return self._tra(400, "text/plain; charset=utf-8", "không thấy ngăn clip")
                ma_c, ten = phan[:i], phan[i + len("/clip/tay/"):]
                if ("/" in ten or ".." in ten or ".." in ma_c
                        or not (ten.endswith(".mp4") or ten.endswith(".jpg"))):
                    return self._tra(400, "text/plain; charset=utf-8", "đường dẫn không hợp lệ")
                return self._tep_khuc(os.path.join(DD.VIEC, ma_c, "clip", "tay", ten))
            if d.startswith("/anh/") or d.startswith("/thumb/"):
                # Mã việc CÓ dấu gạch chéo từ 05/08 (kho xếp theo ngày: <ngày>/video-N-<mã>),
                # nên không tách cứng theo dấu gạch chéo thứ ba được nữa — làm thế thì mã việc
                # bị cắt còn mỗi phần ngày, đường ảnh thừa ra tên thư mục việc, và cổng an toàn
                # chặn hết. Đó là lý do kho ảnh hiện toàn ô đen ngày 06/08.
                # Cách đúng: tìm ranh giới ở thư mục ảnh — trước nó là mã việc, sau nó là ảnh.
                nho = d.startswith("/thumb/")
                phan = urllib.parse.unquote(d.split("/", 2)[2])
                vt, thu = -1, None
                for t in THU_ANH:
                    i = phan.rfind(f"/{t}/")
                    if i > vt:
                        vt, thu = i, t
                if vt < 0:
                    return self._tra(400, "text/plain; charset=utf-8", "không thấy thư mục ảnh")
                ma, duong = phan[:vt], phan[vt + 1:]
                duong = _an_toan(duong)
                if not duong:
                    return self._tra(400, "text/plain; charset=utf-8", "đường dẫn không hợp lệ")
                viec = os.path.join(DD.VIEC, ma)
                return self._tep(_thumb(viec, duong) if nho else os.path.join(viec, duong))
            return self._tra(404, "text/plain; charset=utf-8", "không có đường này")
        except Exception as e:
            return self._js({"loi": str(e), "vet": traceback.format_exc()[-600:]}, 500)

    def do_OPTIONS(self):
        self._tra(204, "text/plain", b"")

    def do_POST(self):
        d = urllib.parse.urlparse(self.path).path
        n = int(self.headers.get("Content-Length") or 0)
        try:
            than = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._js({"loi": "thân yêu cầu không phải JSON"}, 400)
        try:
            if d == "/api/may":
                # ĐƯỜNG DẪN RIÊNG MÁY NÀY (anh chốt 15/08). Khác phong-cach.json ở
                # chỗ: phong cách nằm TRONG kho tài nguyên nên DÙNG CHUNG cả nhà;
                # còn đường dẫn thì mỗi máy một kiểu — Mac trỏ /Volumes/DATA,
                # Windows trỏ D:\. Để chung là hai máy giẫm nhau ngay.
                p_m = os.path.expanduser("~/.config/socbongda247/may.json")
                try:
                    cu_m = json.load(open(p_m, encoding="utf-8"))
                except Exception:
                    cu_m = {}
                for k_m in ("nguoi", "drive", "kho_nang", "viec", "kho_tai_nguyen"):
                    if k_m in than:
                        v_m = str(than[k_m] or "").strip()
                        if v_m:
                            cu_m[k_m] = v_m
                        else:
                            cu_m.pop(k_m, None)    # để trống = trả về cho máy tự dò
                cu_m["_ghi_chu"] = ("Cấu hình RIÊNG máy này. KHÔNG lên git, KHÔNG lên "
                                    "Drive. Đổi xong phải khởi động lại trạm.")
                os.makedirs(os.path.dirname(p_m), exist_ok=True)
                json.dump(cu_m, open(p_m, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
                # soi ngay xem đường mới có thật không — đừng để anh lưu xong mới biết sai
                kiem = {k_m: (os.path.isdir(v_m) if k_m != "nguoi" else True)
                        for k_m, v_m in cu_m.items() if not k_m.startswith("_")}
                return self._js({"ok": True, "cau_hinh": cu_m, "co_that": kiem,
                                 "nhac": "Khởi động lại trạm để đường mới có hiệu lực"})
            if d == "/api/phong-cach":                   # LƯU cấu hình phong cách
                return self._js({"ok": True, "cau_hinh": PC.ghi(than)})
            if d == "/api/phong-cach-thu":               # BẢNG THỬ — xem trước, KHÔNG lưu
                return self._js(_phong_cach_thu(than))
            if d == "/api/thu-giong":                    # thử mã giọng VBee trước khi lưu
                return self._js(_thu_giong(than))
            if d == "/api/dang-lam":
                return self._js({"ok": True, "ma": _dang_lam(than.get("ma", ""))})
            if d == "/api/luu":
                return self._js(_luu_nhap(than["ma"], than))
            if d == "/api/tim-san":
                ma_job = f"t{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "chuẩn bị"}
                    VIEC_JOB_MA[ma_job] = than["ma"]
                threading.Thread(target=_chay_tim_san_job, daemon=True,
                                 args=(ma_job, than["ma"], than.get("cau"),
                                       bool(than.get("chi_thieu")),
                                       than.get("tu_khoa"))).start()
                return self._js({"job": ma_job})
            if d == "/api/gan":
                # gán một ảnh cho một câu — trang chọn ảnh gọi sau khi tải xong
                viec = os.path.join(DD.VIEC, than["ma"])
                nh = _nhap(viec)
                bd = dict(nh.get("ban_do", {}))
                bd[str(than["cau"])] = than["duong"]
                nh["ban_do"] = bd
                # anh tự tay gán = cảnh này người đã xem — cờ ◌ nháp (nếu có) tự rơi
                nh["nhap"] = {c: v for c, v in (nh.get("nhap") or {}).items()
                              if c != str(than["cau"])}
                _luu_nhap(than["ma"], nh)
                return self._js({"ok": True, "ban_do": bd, "nhap": nh["nhap"]})
            if d == "/api/tu-khoa-gpt":
                # CẦU DÁN (anh chốt 14/08 "đường ①"): anh viết bài ở dự án ChatGPT đã
                # luyện, bên đó ra từ khoá tiếng Anh trúng hơn — trước phải chép TỪNG
                # cảnh, nay dán MỘT khối, máy khớp theo CÂU rồi điền vào đúng ô.
                # Từ khoá anh dán là CHÂN LÝ: ghi đè bản máy tự gợi, và chuỗi sau
                # Duyệt lời không được đè ngược (xem cờ tu_khoa_nguoi).
                ma_g = (than.get("ma") or "").strip()
                chu = than.get("chu") or ""
                viec_g = os.path.join(DD.VIEC, ma_g)
                if not ma_g or not os.path.isdir(viec_g):
                    return self._js({"loi": "chưa chọn việc"}, 400)
                try:
                    kb_g = json.load(open(os.path.join(viec_g, "kich-ban.json"),
                                          encoding="utf-8"))
                except OSError:
                    return self._js({"loi": "việc chưa có kịch bản"}, 400)
                cau_g = _tach_cau(kb_g.get("loi_binh", ""))
                r_g = BG.boc(chu, cau_g)
                if not r_g["khop"]:
                    return self._js({"loi": "không khớp được đoạn nào với câu trong bài "
                                            "— kiểm lại xem có dán kèm câu thoại không",
                                     **r_g}, 400)
                nh_g = _nhap(viec_g)
                tk_g = dict(nh_g.get("tu_khoa", {})); tk_g.update(r_g["tu_khoa"])
                en_g = dict(nh_g.get("tu_khoa_en", {})); en_g.update(r_g["tu_khoa_en"])
                nguoi = dict(nh_g.get("tu_khoa_nguoi", {}))
                for k_g in list(r_g["tu_khoa"]) + list(r_g["tu_khoa_en"]):
                    nguoi[k_g] = True
                _luu_nhap(ma_g, {**nh_g, "tu_khoa": tk_g, "tu_khoa_en": en_g,
                                 "tu_khoa_nguoi": nguoi})
                return self._js({"ok": True, **r_g})
            if d == "/api/bai-moi":
                # Anh ĐƯA BÀI TỪ NGOÀI vào trạm (anh chốt 07/08 đêm — content từ GPT, anh
                # tự viết, hay bất cứ đâu): tạo việc mới với kịch bản đó, từ đấy đi đúng
                # dây chuyền cũ (duyệt lời → từ khoá → tìm sẵn ảnh → dựng).
                tieu_de = (than.get("tieu_de") or "").strip()
                loi = (than.get("loi_binh") or "").strip()
                if not tieu_de or not loi:
                    return self._js({"loi": "cần đủ cả TÍT và LỜI"}, 400)
                ngay = datetime.now().strftime("%Y-%m-%d")
                thu_ngay = os.path.join(DD.VIEC, ngay)
                os.makedirs(thu_ngay, exist_ok=True)
                so = 1 + len(glob.glob(os.path.join(thu_ngay, "video-*")))
                # MÃ giống hệt bài hệ thống `video-N-<mã 6 hex>` nhưng đeo tiền tố
                # bai-tay (anh chốt 10/08): nhìn mã biết ngay nguồn, hex băm từ tiêu đề
                # + giờ tạo nên hai bài tay cùng ngày không bao giờ trùng nhau
                ma_hex = hashlib.md5(f"{tieu_de}{time.time()}".encode()).hexdigest()[:6]
                ma_moi = f"{ngay}/video-{so}-bai-tay-{ma_hex}"
                viec = os.path.join(DD.VIEC, ma_moi)
                os.makedirs(os.path.join(viec, "anh"), exist_ok=True)
                json.dump({
                    "tieu_de": tieu_de, "loi_binh": loi, "dat": True,
                    "cum_to_vang": [],           # chuỗi sau duyệt sẽ tự chọn (haiku)
                    "nguon_tin": "bài anh đưa tay vào trạm",
                    "tin_goc": than.get("ghi_chu", ""),
                    "canh_bao": "Bài đưa từ ngoài — máy chưa kiểm tư liệu, anh tự chịu "
                                "trách nhiệm dữ kiện.",
                    "luc_tao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }, open(os.path.join(viec, "kich-ban.json"), "w", encoding="utf-8"),
                    ensure_ascii=False, indent=1)
                # tin-goc tối thiểu — các bước sau (xếp kho, SEO) đều trông chờ file này
                json.dump({"tieu_de": tieu_de, "link": "", "cac_link": [],
                           "nguon": "bài anh đưa tay vào trạm"},
                          open(os.path.join(viec, "tin-goc.json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
                _dang_lam(ma_moi)                # trạm + extension trỏ ngay về việc mới
                DH.cham(viec, "mo_viec")         # ⏱ mốc GỐC của đồng hồ sản xuất
                return self._js({"ok": True, "ma": ma_moi})
            if d == "/api/gan-phu":
                # ẢNH PHỤ cho câu (anh chốt 07/08: cảnh dài phải tách để đưa thêm ảnh vào,
                # dù thoại/từ khoá giống nhau): trang chọn lấy nhiều tấm thì các tấm ngoài
                # tấm-cuối thành phụ của câu. Xưởng đọc từ nhập, cảnh >6s tự tách cảnh con.
                viec = os.path.join(DD.VIEC, than["ma"])
                nh = _nhap(viec)
                ap = dict(nh.get("anh_phu", {}))
                cau = str(int(than["cau"]))
                if "phan" in than:                 # thao tác TỪNG Ô: đặt / bỏ một cảnh phụ
                    phan = int(than["phan"])
                    if not (0 <= phan < 8):
                        return self._js({"loi": "chỉ số cảnh phụ không hợp lệ"}, 400)
                    # TRẦN SLOT (anh chốt 13/08): "cảnh chỉ có 3 slot mà chọn 5 ảnh thì
                    # chỉ lấy 3, hai ảnh còn lại về kho ứng viên, KHÔNG sinh cảnh dư".
                    # Ô ngoài trần thì TỪ CHỐI thẳng — ảnh vẫn nằm trong kho của bài,
                    # anh gán cho cảnh khác được ngay.
                    if not than.get("bo"):
                        tran = _tran_o_cua_cau(viec, int(cau))
                        if phan + 1 >= tran:
                            return self._js(
                                {"loi": f"cảnh {int(cau)+1} chỉ đủ chỗ cho {tran} khung "
                                        f"(mỗi khung tối thiểu 2,5 giây) — ảnh giữ trong "
                                        f"kho, gán cho cảnh khác nhé"}, 400)
                    o = list(ap.get(cau, []))
                    while len(o) <= phan:
                        o.append("")
                    if than.get("bo"):
                        o[phan] = ""
                    else:
                        gt = than.get("gia_tri", "")
                        ok_anh = (isinstance(gt, str) and gt.endswith(".jpg")
                                  and gt.split("/")[0] in THU_ANH and ".." not in gt)
                        # clip::tệp::từ::đến[::x,y,w,h] — đuôi thứ 5 là KHUNG né logo
                        # (quên nới cổng này 09/08 tối là gán clip vào ô phụ chết cứng —
                        # anh bắt; đuôi phải là 4 số 0–1 mới nhận)
                        ok_clip = False
                        if isinstance(gt, str) and gt.startswith("clip::clip/tay/") \
                                and ".." not in gt:
                            ph_gt = gt.split("::")
                            try:
                                if len(ph_gt) in (4, 5):
                                    float(ph_gt[2]); float(ph_gt[3])
                                    if len(ph_gt) == 5:
                                        so_k = [float(t) for t in ph_gt[4].split(",")]
                                        ok_clip = (len(so_k) == 4
                                                   and all(0 <= v <= 1 for v in so_k))
                                    else:
                                        ok_clip = True
                            except ValueError:
                                pass
                        if not (ok_anh or ok_clip):
                            return self._js({"loi": "giá trị cảnh phụ không hợp lệ"}, 400)
                        o[phan] = gt
                    while o and not o[-1]:
                        o.pop()
                    if o:
                        ap[cau] = o
                    else:
                        ap.pop(cau, None)
                else:                              # cả danh sách (trang chọn lấy nhiều tấm)
                    ds = [x for x in (than.get("ds") or []) if isinstance(x, str)]
                    if ds:
                        ap[cau] = ds[:6]
                    else:
                        ap.pop(cau, None)
                nh["anh_phu"] = ap
                _luu_nhap(than["ma"], nh)
                return self._js({"ok": True, "anh_phu": ap})
            if d == "/api/gan-clip":
                # gán ĐOẠN clip vào câu: {ma, cau, tep, tu, den} · bỏ gán: {ma, cau, bo:1}
                # xoá đoạn khỏi sổ ứng viên: {ma, xoa_doan: {tep, tu, den}}
                viec = os.path.join(DD.VIEC, than["ma"])
                cc, cd = _doc_clip_canh(viec), _doc_clip_doan(viec)
                p_cc = os.path.join(viec, "anh", "clip-canh.json")
                p_cd = os.path.join(viec, "anh", "clip-doan.json")
                os.makedirs(os.path.dirname(p_cc), exist_ok=True)
                if than.get("xoa_doan"):
                    s = than["xoa_doan"]
                    cd = [x for x in cd if not (x.get("tep") == s.get("tep")
                                                and x.get("tu") == s.get("tu")
                                                and x.get("den") == s.get("den"))]
                    json.dump(cd, open(p_cd, "w", encoding="utf-8"),
                              ensure_ascii=False, indent=1)
                    # tệp bản-cắt chỉ dọn khi KHÔNG câu nào còn dùng đúng đoạn đó
                    con_dung = any(v.get("tep") == s.get("tep") and v.get("tu") == s.get("tu")
                                   and v.get("den") == s.get("den") for v in cc.values())
                    if not con_dung and s.get("tep"):
                        goc_ten = (f"{os.path.basename(s['tep'])[:-4]}"
                                   f"__{float(s['tu']):.1f}-{float(s['den']):.1f}")
                        for f_don in glob.glob(os.path.join(
                                viec, "clip", "doan", goc_ten + "*.mp4")):
                            try:                   # dọn cả bản gốc lẫn các bản crop __k…
                                os.remove(f_don)
                            except OSError:
                                pass
                    return self._js({"ok": True, "clip_canh": cc, "clip_doan": cd})
                # chi_kho=1: chỉ ghi đoạn vào KHO ứng viên + cắt sẵn bản xem, KHÔNG gán
                # câu chính — dùng khi gán đoạn vào Ô PHỤ (đường anh_phu) từ cửa cắt
                cau = str(int(than.get("cau", 0)))
                if than.get("bo"):
                    cc.pop(cau, None)
                else:
                    tep = than["tep"]
                    if not (tep.startswith("clip/tay/") and tep.endswith(".mp4")
                            and "/" not in tep[len("clip/tay/"):] and ".." not in tep):
                        return self._js({"loi": "tệp clip không hợp lệ"}, 400)
                    tu, den = float(than["tu"]), float(than["den"])
                    if den - tu < 0.8:
                        return self._js({"loi": "đoạn cắt phải từ 0,8 giây trở lên"}, 400)
                    doan = {"tep": tep, "tu": round(tu, 2), "den": round(den, 2)}
                    # KHUNG CROP tự chọn (anh đặt 09/08 tối): vùng {x,y,w,h} tỉ lệ 0–1
                    # trên khung video gốc để né logo nằm trong hình — xưởng cắt vùng này
                    # trước khi dựng. Kẹp về biên an toàn, vùng bé hơn 5% coi như không.
                    kh = than.get("khung")
                    if isinstance(kh, dict):
                        try:
                            x0 = max(0.0, min(float(kh["x"]), 0.95))
                            y0 = max(0.0, min(float(kh["y"]), 0.95))
                            w0 = max(0.05, min(float(kh["w"]), 1.0 - x0))
                            h0 = max(0.05, min(float(kh["h"]), 1.0 - y0))
                            doan["khung"] = {"x": round(x0, 4), "y": round(y0, 4),
                                             "w": round(w0, 4), "h": round(h0, 4)}
                        except Exception:
                            pass
                    if not than.get("chi_kho"):
                        cc[cau] = dict(doan)
                    # mỗi đoạn đã cắt vào sổ ứng viên — gắp lại cho cảnh khác được;
                    # đoạn đã có mà khung đổi thì cập nhật khung của mục cũ
                    trung = next((x for x in cd
                                  if x.get("tep") == doan["tep"] and x.get("tu") == doan["tu"]
                                  and x.get("den") == doan["den"]), None)
                    if trung is None:
                        cd.append({**doan,
                                   "luc": datetime.now().isoformat(timespec="seconds")})
                        json.dump(cd, open(p_cd, "w", encoding="utf-8"),
                                  ensure_ascii=False, indent=1)
                    elif trung.get("khung") != doan.get("khung"):
                        if doan.get("khung"):
                            trung["khung"] = doan["khung"]
                        else:
                            trung.pop("khung", None)
                        json.dump(cd, open(p_cd, "w", encoding="utf-8"),
                                  ensure_ascii=False, indent=1)
                    _thumb_clip(viec, os.path.basename(tep), doan["tu"])  # mồi sẵn cho UI
                    # cắt sẵn bản đoạn để bấm thẻ là XEM NGAY, không chờ ffmpeg —
                    # có khung thì bản xem cũng là khung đã cắt
                    _cat_doan(viec, os.path.basename(tep), doan["tu"], doan["den"],
                              doan.get("khung"))
                json.dump(cc, open(p_cc, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                # anh tự tay gán/bỏ clip vào câu chính = người đã xem cảnh này — cờ ◌ rơi
                if not than.get("chi_kho"):
                    nh = _nhap(viec)
                    if str(cau) in (nh.get("nhap") or {}):
                        nh["nhap"] = {c: v for c, v in nh["nhap"].items() if c != str(cau)}
                        _luu_nhap(than["ma"], nh)
                return self._js({"ok": True, "clip_canh": cc, "clip_doan": cd})
            if d == "/api/kho-nha-sua":
                # anh sửa nhãn = CHÂN LÝ (nguoi_sua) — máy bổ nhãn sau không được đè.
                # Nhận MỘT tấm (tep) hoặc CẢ LOẠT (tep_ds — anh bắt 10/08: sửa từng tấm
                # 3 ô thì bao giờ xong; chọn cụm gõ chủ thể MỘT lần / xác nhận cả trang)
                tep_ds = set(than.get("tep_ds") or ([than["tep"]] if than.get("tep") else []))
                with KHOA:
                    ds_s = [json.loads(l) for l in open(SO_CHU_THE, encoding="utf-8")
                            if l.strip()]
                    for m in ds_s:
                        if m.get("tep") not in tep_ds:
                            continue
                        if "nhan" in than:
                            # trần 12 khớp với trần sau-khử-trùng bên dưới — bản cũ cắt
                            # [:8] ở đây làm nhãn anh VỪA THÊM (đứng cuối) rụng im lặng
                            # khi tấm sẵn 8 nhãn máy (bắt 11/08 khi test Enter-tự-lưu)
                            m["nhan"] = [str(x).strip() for x in than["nhan"]
                                         if str(x).strip()][:12]
                        # THÊM nhãn (cộng dồn, không đè) — dùng cho GẮN NHÃN HÀNG LOẠT
                        # (anh đặt 11/08). "nhan" là ghi đè cả bộ, loạt mà đè là mất
                        # sạch nhãn riêng của từng tấm.
                        for n_t in (than.get("nhan_them") or []):
                            n_t = str(n_t).strip()
                            if n_t:
                                m.setdefault("nhan", []).append(n_t)
                        if than.get("chu_the") is not None:
                            ct = _chuan_hoa_ct(str(than["chu_the"]))
                            m["chu_the"] = ct
                            if ct and ct.lower() not in [n.lower() for n in m.get("nhan", [])]:
                                m.setdefault("nhan", []).insert(0, ct)
                        # KHỬ NHÃN TRÙNG trong tấm (anh đặt 10/08) — so bỏ dấu
                        thay, sach = set(), []
                        for n_ in m.get("nhan", []):
                            k_ = _bo_dau_k(n_)
                            if k_ and k_ not in thay:
                                thay.add(k_)
                                sach.append(n_)
                        m["nhan"] = sach[:12]
                        if "mo_ta" in than:
                            m["mo_ta"] = str(than["mo_ta"]).strip()
                        m["nhan_tho"] = False
                        m["nguoi_sua"] = True      # cả nút "✓ nhãn máy đúng" cũng đóng dấu
                        # DUYỆT NỘI DUNG ≠ CHẠM VÀO TẤM (anh bắt 14/08). Gắn nhãn HÀNG
                        # LOẠT là anh thêm một nhãn chung cho cả cụm — anh KHÔNG hề đọc
                        # mô tả của từng tấm. Đóng dấu "người đã sửa" rồi miễn soát cả
                        # tấm là sai: 746/986 tấm thoát vòng soát vì cớ đó, trong đó có
                        # tấm nhãn ghi "hlv calisto" mà mô tả lại là Kim Sang-sik.
                        # Chỉ lượt sửa TỪNG TẤM mới là anh thật sự duyệt nội dung.
                        if len(tep_ds) == 1:
                            m["nguoi_duyet"] = True
                    with open(SO_CHU_THE, "w", encoding="utf-8") as f:
                        for m in ds_s:
                            f.write(json.dumps(m, ensure_ascii=False) + "\n")
                # sửa MỘT tấm thì trả bộ nhãn THẬT đã lưu — client đồng bộ chip theo
                # sự thật server (khử trùng, trần 12) thay vì tin bản nháp của mình
                ra_sua = {"ok": True, "so": len(tep_ds)}
                if len(tep_ds) == 1:
                    t1 = next(iter(tep_ds))
                    ra_sua["nhan"] = next((m.get("nhan") for m in ds_s
                                           if m.get("tep") == t1), None)
                return self._js(ra_sua)
            if d == "/api/kho-video-tai":
                # dán link → máy tự tải về kho video chung (anh đặt 10/08) — chạy nền
                url_v = (than.get("url") or "").strip()
                if not url_v.startswith("http"):
                    return self._js({"loi": "link không hợp lệ"}, 400)
                subprocess.Popen([sys.executable,
                                  os.path.join(DD.MAY, "nhap_kho_video.py"),
                                  "--tai", url_v],
                                 stdout=open(NT.thu_muc_tam("kho-video-tai.log"), "a"),
                                 stderr=subprocess.STDOUT, start_new_session=True)
                return self._js({"ok": True})
            if d == "/api/kho-video-sua":
                ids = set(tuple(x) for x in (than.get("ids") or []))

                def _sua_v(ds_v):
                    for m in ds_v:
                        if (m.get("tep"), m.get("tu")) not in ids:
                            continue
                        if than.get("chu_the") is not None:
                            ct = _chuan_hoa_ct(str(than["chu_the"]))
                            m["chu_the"] = ct
                            if ct and ct.lower() not in [n.lower()
                                                         for n in m.get("nhan", [])]:
                                m.setdefault("nhan", []).insert(0, ct)
                        if "nhan" in than:
                            m["nhan"] = [str(x).strip() for x in than["nhan"]
                                         if str(x).strip()]
                        # THÊM nhãn cộng dồn cho GẮN NHÃN LOẠT — y hệt bên kho ảnh
                        for n_t in (than.get("nhan_them") or []):
                            n_t = str(n_t).strip()
                            if n_t:
                                m.setdefault("nhan", []).append(n_t)
                        # khử nhãn trùng (so bỏ dấu) — loạt gắn nhiều lần vẫn sạch
                        thay_v, sach_v = set(), []
                        for n_v in m.get("nhan", []):
                            k_v = _bo_dau_k(n_v)
                            if k_v and k_v not in thay_v:
                                thay_v.add(k_v)
                                sach_v.append(n_v)
                        m["nhan"] = sach_v[:12]
                        if "mo_ta" in than:
                            m["mo_ta"] = str(than["mo_ta"]).strip()
                        if "khung" in than:        # ✂ khung né logo của đoạn (10/08)
                            kh_v = than["khung"]
                            if isinstance(kh_v, dict):
                                try:
                                    m["khung"] = {k: round(max(0.0, min(float(kh_v[k]), 1.0)), 4)
                                                  for k in ("x", "y", "w", "h")}
                                except Exception:
                                    pass
                            else:
                                m.pop("khung", None)
                            continue               # chỉ sửa khung: đừng đóng dấu nhãn
                        thay, sach = set(), []
                        for n_ in m.get("nhan", []):
                            k_ = _bo_dau_k(n_)
                            if k_ and k_ not in thay:
                                thay.add(k_)
                                sach.append(n_)
                        m["nhan"] = sach[:12]
                        m["nhan_tho"] = False
                        m["nguoi_sua"] = True
                    return ds_v
                _so_video_ct(_sua_v)
                return self._js({"ok": True, "so": len(ids)})
            if d == "/api/kho-video-xoa":
                ids = set(tuple(x) for x in (than.get("ids") or []))

                def _xoa_v(ds_v):
                    giu = [m for m in ds_v if (m.get("tep"), m.get("tu")) not in ids]
                    bo = [m for m in ds_v if (m.get("tep"), m.get("tu")) in ids]
                    con_tep = {m.get("tep") for m in giu}
                    for m in bo:
                        try:
                            os.remove(os.path.join(KHO_VIDEO_CT, "thumb",
                                                   m.get("thumb", "")))
                        except OSError:
                            pass
                        if m.get("tep") not in con_tep:   # tệp không còn đoạn nào → dọn
                            try:
                                os.remove(os.path.join(KHO_VIDEO_CT, m["tep"]))
                            except OSError:
                                pass
                            con_tep.add(m.get("tep"))
                    return giu
                _so_video_ct(_xoa_v)
                return self._js({"ok": True, "so": len(ids)})
            if d == "/api/kho-video-nhin-lai":
                ids = set(tuple(x) for x in (than.get("ids") or []))

                def _nl_v(ds_v):
                    for m in ds_v:
                        if (m.get("tep"), m.get("tu")) in ids:
                            m["nhan_tho"] = True
                            m.pop("nguoi_sua", None)
                    return ds_v
                _so_video_ct(_nl_v)
                if subprocess.run(["pgrep", "-f", "nhap_kho_video"],
                                  capture_output=True).returncode != 0:
                    subprocess.Popen([sys.executable,
                                      os.path.join(DD.MAY, "nhap_kho_video.py"),
                                      "--bo-nhan"],
                                     env={**os.environ, "KHO_MODEL": "claude-sonnet-5"},
                                     stdout=open(NT.thu_muc_tam("kho-video-tai.log"), "a"),
                                     stderr=subprocess.STDOUT, start_new_session=True)
                return self._js({"ok": True, "so": len(ids)})
            if d == "/api/kho-video-goc":
                # 🎬 MỞ VIDEO GỐC KHO ĐỂ CẮT TẠI CHỖ (anh đặt 11/08: "đoạn cắt sẵn chỉ
                # 4 giây, không lấy được đoạn ưng ý"). Không chép file: HARDLINK video
                # gốc vào clip/tay của bài (cùng volume DATA — 0 byte thêm), từ đó modal
                # cắt sẵn có của bài dùng được nguyên bộ: kéo chọn đoạn · khung né logo ·
                # gán chính/phụ · ✂ cắt lưu kho nhiều đoạn liền tay.
                ma_g = than.get("ma", "")
                tep_g = os.path.basename(than.get("tep", ""))
                goc_v = os.path.join(KHO_VIDEO_CT, tep_g)
                viec_g = os.path.join(DD.VIEC, ma_g)
                if not (os.path.exists(goc_v) and os.path.isdir(viec_g)):
                    return self._js({"loi": "không thấy video kho hoặc bài"}, 404)
                thu_g = os.path.join(viec_g, "clip", "tay")
                os.makedirs(thu_g, exist_ok=True)
                ten_g = "kho__" + tep_g            # tên riêng, không đụng khuôn tay_NN
                dich_g = os.path.join(thu_g, ten_g)
                if not os.path.exists(dich_g):
                    try:
                        os.link(goc_v, dich_g)     # cùng volume → hardlink 0 byte
                    except OSError:
                        shutil.copy2(goc_v, dich_g)
                return self._js({"ok": True, "tep": ten_g})
            if d == "/api/kho-video-lay":
                # LẤY ĐOẠN VỀ BÀI ĐANG LÀM: cắt thành clip tay của bài — từ đó mọi đồ
                # nghề clip (cắt lại, khung né logo, lật) dùng được như thường
                ma_lay = than.get("ma") or _dang_lam()
                viec = os.path.join(DD.VIEC, ma_lay)
                if not os.path.isdir(viec):
                    return self._js({"loi": "không thấy bài đang làm"}, 400)
                thu = os.path.join(viec, "clip", "tay")
                os.makedirs(thu, exist_ok=True)
                ids = [tuple(x) for x in (than.get("ids") or [])]
                so_v = {(m.get("tep"), m.get("tu")): m for m in _so_video_ct()}
                lay_dc = 0
                for i_d in ids:
                    m = so_v.get(i_d)
                    if not m:
                        continue
                    n_t = 1 + max([int(mm.group(1)) for f in
                                   glob.glob(os.path.join(thu, "tay_*.mp4"))
                                   if (mm := re.search(r"tay_(\d+)",
                                                       os.path.basename(f)))], default=0)
                    ra_t = os.path.join(thu, f"tay_{n_t:02d}.mp4")
                    loc_v = []
                    kh_m = m.get("khung")
                    if kh_m:                       # đoạn có khung né logo → cắt luôn
                        loc_v = ["-vf",
                                 (f"crop=floor(iw*{kh_m['w']:.4f}/2)*2:"
                                  f"floor(ih*{kh_m['h']:.4f}/2)*2:"
                                  f"floor(iw*{kh_m['x']:.4f}):floor(ih*{kh_m['y']:.4f})")]
                    subprocess.run(["ffmpeg", "-y", "-v", "quiet",
                                    "-ss", f"{float(m['tu']):.2f}",
                                    "-i", os.path.join(KHO_VIDEO_CT, m["tep"]),
                                    "-t", f"{float(m['den']) - float(m['tu']):.2f}"]
                                   + loc_v +
                                   ["-c:v", "libx264", "-preset", "veryfast",
                                    "-crf", "20", "-an", ra_t], timeout=300)
                    if os.path.exists(ra_t) and os.path.getsize(ra_t) > 20000:
                        lay_dc += 1

                        def _dd(ds_v, i_dd=i_d):
                            for mm in ds_v:
                                if (mm.get("tep"), mm.get("tu")) == i_dd \
                                        and ma_lay not in mm.get("da_dung", []):
                                    mm.setdefault("da_dung", []).append(ma_lay)
                            return ds_v
                        _so_video_ct(_dd)
                return self._js({"ok": True, "so": lay_dc, "ma": ma_lay})
            if d == "/api/kho-nha-tai-len":
                # EXTENSION tải ảnh Google TAY về THẲNG KHO CHUNG (anh đặt 10/08 khuya):
                # ảnh vào ngăn CHỜ GẮN NHÃN (cờ cho_nhan, để riêng), tiêu đề trang tìm
                # làm MỒI cho mắt máy; bấm quét là máy nhận diện + gắn nhãn rồi nhập kho.
                # KHÔNG `import base64` trần ở đây: do_POST đã dùng base64 ở nhánh
                # /api/tai-len — một import cục bộ là Python coi base64 là biến CỤC BỘ
                # của CẢ HÀM, nhánh kia chạy trước liền UnboundLocalError (11/08 làm
                # extension chết hẳn đường gửi ảnh; cùng họ với vụ shutil hôm qua)
                import hashlib as _hh
                from io import BytesIO
                from PIL import Image as _ImK
                nhan_ds, trung = [], 0
                p_vt = os.path.join(KHO_CHU_THE, "van-tay.json")
                try:
                    vt = json.load(open(p_vt))
                except Exception:
                    vt = {}
                for t in (than.get("tep") or [])[:20]:
                    try:
                        im = _ImK.open(BytesIO(base64.b64decode(t["data"]))).convert("RGB")
                    except Exception:
                        continue
                    if min(im.size) < 300:
                        continue                   # bé quá — biểu tượng, không đáng kho
                    dau = str(gap_anh._dhash(im))
                    if dau in vt.values():
                        trung += 1
                        continue
                    ten_k = ("web_" + datetime.now().strftime("%Y%m%d-%H%M%S") + "_"
                             + _hh.md5((t.get("url") or t.get("ten", "")).encode())
                             .hexdigest()[:4] + ".jpg")
                    im.save(os.path.join(KHO_CHU_THE, ten_k), quality=90)
                    vt[ten_k] = dau
                    nhan_ds.append({
                        "tep": ten_k, "hang": "du_tru", "nhan": [], "chu_the": "",
                        # tiêu đề trang Google = từ khoá anh đang tìm → mồi rất trúng
                        "mo_ta": CT._nfc((t.get("tieu_de") or "")[:160]),
                        "nhan_tho": True, "cho_nhan": True,
                        "kich_thuoc": f"{im.size[0]}x{im.size[1]}",
                        "nguon": t.get("url", ""),
                        "luc_nhap": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                if nhan_ds:
                    json.dump(vt, open(p_vt, "w"))
                    with KHOA:
                        with open(SO_CHU_THE, "a", encoding="utf-8") as f:
                            for m in nhan_ds:
                                f.write(json.dumps(m, ensure_ascii=False) + "\n")
                return self._js({"ok": True, "so": len(nhan_ds), "trung": trung})
            if d == "/api/kho-nha-quet-nhan":
                # QUÉT GẮN NHÃN ngăn chờ: thắp máy nền bổ nhãn (haiku — việc thường),
                # bo_nhan xử mọi tấm nhan_tho và tự bỏ cờ cho_nhan khi xong
                if subprocess.run(["pgrep", "-f", "nhap_kho_chu_the"],
                                  capture_output=True).returncode == 0:
                    return self._js({"ok": True, "dang_chay": True})
                subprocess.Popen([sys.executable,
                                  os.path.join(DD.MAY, "nhap_kho_chu_the.py"),
                                  "--bo-nhan"],
                                 stdout=open(NT.thu_muc_tam("khonha-quet-nhan.log"), "a"),
                                 stderr=subprocess.STDOUT, start_new_session=True)
                return self._js({"ok": True})
            if d == "/api/kho-nha-nhin-lai":
                # GẮN LẠI NHÃN (anh hỏi 10/08): trả các tấm về hàng chờ mắt máy —
                # bỏ cả dấu người sửa (anh chủ động đòi nhìn lại) — rồi thắp máy nền
                tep_ds = set(than.get("tep_ds") or [])
                with KHOA:
                    ds_s = [json.loads(l) for l in open(SO_CHU_THE, encoding="utf-8")
                            if l.strip()]
                    for m in ds_s:
                        if m.get("tep") in tep_ds:
                            m["nhan_tho"] = True
                            m.pop("nguoi_sua", None)
                    with open(SO_CHU_THE, "w", encoding="utf-8") as f:
                        for m in ds_s:
                            f.write(json.dumps(m, ensure_ascii=False) + "\n")
                if not subprocess.run(["pgrep", "-f", "nhap_kho_chu_the"],
                                      capture_output=True).returncode == 0:
                    # tấm ANH ĐÃ THẤY SAI → lượt nhìn lại dùng model TO (10/08)
                    subprocess.Popen([sys.executable,
                                      os.path.join(DD.MAY, "nhap_kho_chu_the.py"),
                                      "--bo-nhan"],
                                     env={**os.environ, "KHO_MODEL": "claude-sonnet-5"},
                                     stdout=open(NT.thu_muc_tam("khonha-nhin-lai.log"), "a"),
                                     stderr=subprocess.STDOUT, start_new_session=True)
                return self._js({"ok": True, "so": len(tep_ds)})
            if d == "/api/kho-nha-xoa":
                # xoá = chuyển THÙNG RÁC + trả lại dòng sổ để client HOÀN TÁC được
                # (anh chê 10/08: xoá nhầm là mất luôn)
                tep_ds = set(than.get("tep_ds") or ([than["tep"]] if than.get("tep") else []))
                bo_dong = []
                with KHOA:
                    ds_s = [json.loads(l) for l in open(SO_CHU_THE, encoding="utf-8")
                            if l.strip()]
                    bo_dong = [m for m in ds_s if m.get("tep") in tep_ds]
                    ds_s = [m for m in ds_s if m.get("tep") not in tep_ds]
                    with open(SO_CHU_THE, "w", encoding="utf-8") as f:
                        for m in ds_s:
                            f.write(json.dumps(m, ensure_ascii=False) + "\n")
                    rac = os.path.join(KHO_CHU_THE, "thung-rac")
                    os.makedirs(rac, exist_ok=True)
                    p_vt_k = os.path.join(KHO_CHU_THE, "van-tay.json")
                    try:
                        vt_k = json.load(open(p_vt_k))
                    except Exception:
                        vt_k = None
                    for t_x in tep_ds:
                        p_x = os.path.join(KHO_CHU_THE, os.path.basename(t_x))
                        try:
                            os.path.exists(p_x) and os.replace(
                                p_x, os.path.join(rac, os.path.basename(t_x)))
                        except OSError:
                            pass
                        if vt_k is not None:
                            vt_k.pop(t_x, None)
                    if vt_k is not None:
                        json.dump(vt_k, open(p_vt_k, "w"))
                return self._js({"ok": True, "so": len(tep_ds), "hoan": bo_dong})
            if d == "/api/kho-nha-crop":
                # CẮT LOGO tại chỗ trong kho (anh hỏi 10/08) — bản gốc giữ ở thùng rác
                # đuôi .goc để hoàn được; sổ cập nhật cỡ + đánh dấu đã cắt
                ten_c = os.path.basename(than.get("tep", ""))
                p_c = os.path.join(KHO_CHU_THE, ten_c)
                if not os.path.exists(p_c):
                    return self._js({"loi": "không thấy ảnh"}, 404)
                try:
                    from PIL import Image as _Im
                    im_c = _Im.open(p_c).convert("RGB")
                    W0, H0 = im_c.size
                    x0 = max(0, int(float(than["x"]) * W0))
                    y0 = max(0, int(float(than["y"]) * H0))
                    x1 = min(W0, int((float(than["x"]) + float(than["w"])) * W0))
                    y1 = min(H0, int((float(than["y"]) + float(than["h"])) * H0))
                    if x1 - x0 < 300 or y1 - y0 < 300:
                        return self._js({"loi": "vùng giữ quá bé (dưới 300px)"}, 400)
                    rac = os.path.join(KHO_CHU_THE, "thung-rac")
                    os.makedirs(rac, exist_ok=True)
                    goc_c = os.path.join(rac, ten_c + ".goc")
                    if not os.path.exists(goc_c):  # giữ bản gốc NHẤT
                        shutil.copy2(p_c, goc_c)   # shutil đã import ở đầu file
                    im_c.crop((x0, y0, x1, y1)).save(p_c, quality=90)
                    w_m, h_m = x1 - x0, y1 - y0
                except Exception as e:
                    return self._js({"loi": str(e)}, 500)
                with KHOA:
                    ds_s = [json.loads(l) for l in open(SO_CHU_THE, encoding="utf-8")
                            if l.strip()]
                    for m in ds_s:
                        if m.get("tep") == ten_c:
                            m["kich_thuoc"] = f"{w_m}x{h_m}"
                            m["da_cat_wm"] = True
                    with open(SO_CHU_THE, "w", encoding="utf-8") as f:
                        for m in ds_s:
                            f.write(json.dumps(m, ensure_ascii=False) + "\n")
                try:                               # vân tay tính lại theo ảnh mới
                    sys.path.insert(0, TRAM)
                    import gap_anh as _ga
                    from PIL import Image as _Im2
                    p_vt_k = os.path.join(KHO_CHU_THE, "van-tay.json")
                    vt_k = json.load(open(p_vt_k)) if os.path.exists(p_vt_k) else {}
                    vt_k[ten_c] = str(_ga._dhash(_Im2.open(p_c)))
                    json.dump(vt_k, open(p_vt_k, "w"))
                except Exception:
                    pass
                return self._js({"ok": True, "kich_thuoc": f"{w_m}x{h_m}"})
            if d == "/api/kho-nha-crop-hoan":
                ten_c = os.path.basename(than.get("tep", ""))
                goc_c = os.path.join(KHO_CHU_THE, "thung-rac", ten_c + ".goc")
                if not os.path.exists(goc_c):
                    return self._js({"loi": "ảnh này chưa cắt lần nào"}, 400)
                os.replace(goc_c, os.path.join(KHO_CHU_THE, ten_c))
                return self._js({"ok": True})
            if d == "/api/xoa-wm":
                # XOÁ WATERMARK bằng LaMa local (anh duyệt 10/08 — bán tự động CÓ CỬA
                # DUYỆT): sinh bản THỬ, KHÔNG đè gốc; anh nhìn trước/sau rồi mới chốt.
                ten_c = os.path.basename(than.get("tep", ""))
                p_c = os.path.join(KHO_CHU_THE, ten_c)
                vungs = [v for v in (than.get("vung") or [])
                         if all(k in v for k in ("x", "y", "w", "h"))]
                if not os.path.exists(p_c) or not vungs:
                    return self._js({"loi": "thiếu ảnh hoặc vùng"}, 400)
                lama_py = os.path.expanduser("~/.cache/lama-venv/bin/python3")
                if not os.path.exists(lama_py):
                    return self._js({"loi": "chưa cài venv LaMa (~/.cache/lama-venv)"}, 500)
                thu_d = os.path.join(KHO_CHU_THE, "thung-rac", "thu-wm")
                os.makedirs(thu_d, exist_ok=True)
                p_thu = os.path.join(thu_d, ten_c)
                ma_job = f"wm{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "LaMa đang vá vùng xoá"}

                kieu_wm = than.get("kieu") if than.get("kieu") in ("tu", "tinh", "dac") \
                    else "tu"

                def chay_wm(mj=ma_job, p=p_c, ra=p_thu, vs=vungs, kw=kieu_wm):
                    try:
                        # MỘT LaMa một lúc — 17:14 hôm nay hai lượt bấm chạy song song
                        # là máy 16GB sập nguồn (Jetsam 2 tiến trình Python ~30GB).
                        # Bấm chồng thì lượt sau XẾP HÀNG chờ, không bao giờ chạy đè.
                        with WM_KHOA:
                            r = subprocess.run(
                                [lama_py, os.path.join(DD.MAY, "xoa_wm.py"), "--anh", p,
                                 "--ra", ra, "--kieu", kw, "--vung"]
                                + [f"{v['x']},{v['y']},{v['w']},{v['h']}" for v in vs],
                                capture_output=True, text=True, timeout=300, cwd="/tmp")
                        ok = r.returncode == 0 and os.path.exists(ra)
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "ok": ok,
                                            "loi": "" if ok else (r.stderr or "")[-300:]}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "ok": False, "loi": str(e)}
                threading.Thread(target=chay_wm, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/wm-bai":
                # XOÁ WATERMARK CHO ẢNH ỨNG VIÊN CỦA BÀI (anh đặt 11/08) — trước đây chỉ
                # kho chung mới xoá được, ảnh gắp về bài dính watermark là phải bỏ hoặc
                # cắt cụt. Cùng cỗ máy LaMa, cùng cửa duyệt: sinh bản THỬ, không đè gốc.
                viec = os.path.join(DD.VIEC, than["ma"])
                duong = than.get("duong", "")
                if not (duong.startswith("anh/") and ".." not in duong):
                    return self._js({"loi": "đường ảnh không hợp lệ"}, 400)
                p_a = os.path.join(viec, duong)
                vungs = [v for v in (than.get("vung") or [])
                         if all(k in v for k in ("x", "y", "w", "h"))]
                if not os.path.exists(p_a) or not vungs:
                    return self._js({"loi": "thiếu ảnh hoặc vùng"}, 400)
                lama_py = os.path.expanduser("~/.cache/lama-venv/bin/python3")
                if not os.path.exists(lama_py):
                    return self._js({"loi": "chưa cài venv LaMa (~/.cache/lama-venv)"}, 500)
                thu_d = os.path.join(viec, "anh", "_thu-wm")
                os.makedirs(thu_d, exist_ok=True)
                p_thu = os.path.join(thu_d, os.path.basename(duong))
                ma_job = f"wb{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "LaMa đang vá vùng xoá"}
                kieu_wb = than.get("kieu") if than.get("kieu") in ("tu", "tinh", "dac") \
                    else "tu"

                def chay_wb(mj=ma_job, p=p_a, ra=p_thu, vs=vungs, kw=kieu_wb):
                    try:
                        # MỘT LaMa một lúc — hai lượt song song từng làm máy 16GB sập
                        # nguồn (10/08). Dùng CHUNG khoá với đường kho, không mở khoá riêng.
                        with WM_KHOA:
                            r = subprocess.run(
                                [lama_py, os.path.join(DD.MAY, "xoa_wm.py"), "--anh", p,
                                 "--ra", ra, "--kieu", kw, "--vung"]
                                + [f"{v['x']},{v['y']},{v['w']},{v['h']}" for v in vs],
                                capture_output=True, text=True, timeout=300, cwd="/tmp")
                        ok = r.returncode == 0 and os.path.exists(ra)
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "ok": ok,
                                            "loi": "" if ok else (r.stderr or "")[-300:]}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "ok": False, "loi": str(e)}
                threading.Thread(target=chay_wb, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/wm-bai-chot":
                # anh ƯNG bản thử → đè ảnh bài. Bản gốc cất vào ĐÚNG CHỖ crop vẫn cất
                # (`anh/_goc-crop/`) nên nút "↩ Hoàn" sẵn có tự dùng được — không đẻ
                # thêm nút hoàn tác thứ hai cho anh phải nhớ cái nào là cái nào.
                viec = os.path.join(DD.VIEC, than["ma"])
                duong = than.get("duong", "")
                if not (duong.startswith("anh/") and ".." not in duong):
                    return self._js({"ok": False, "loi": "đường ảnh không hợp lệ"})
                p_a = os.path.join(viec, duong)
                p_thu = os.path.join(viec, "anh", "_thu-wm", os.path.basename(duong))
                if not (os.path.exists(p_a) and os.path.exists(p_thu)):
                    return self._js({"ok": False, "loi": "chưa có bản thử để thay"})
                thu_goc = os.path.join(viec, "anh", "_goc-crop")
                os.makedirs(thu_goc, exist_ok=True)
                bk = os.path.join(thu_goc, os.path.basename(duong))
                if not os.path.exists(bk):        # giữ bản GỐC NHẤT, xoá mấy lần vẫn hoàn được
                    shutil.copy2(p_a, bk)
                os.replace(p_thu, p_a)
                _don_sau_doi_anh(viec, duong)     # dọn thumbnail cũ, không thì anh vẫn thấy ảnh cũ
                return self._js({"ok": True, "anh": _danh_sach_anh(viec)})
            if d == "/api/xoa-wm-chot":
                # anh ƯNG bản thử → thay ảnh kho; bản gốc giữ .goc-wm để hoàn
                ten_c = os.path.basename(than.get("tep", ""))
                p_c = os.path.join(KHO_CHU_THE, ten_c)
                p_thu = os.path.join(KHO_CHU_THE, "thung-rac", "thu-wm", ten_c)
                if not (os.path.exists(p_c) and os.path.exists(p_thu)):
                    return self._js({"loi": "chưa có bản thử để thay"}, 400)
                rac = os.path.join(KHO_CHU_THE, "thung-rac")
                os.makedirs(rac, exist_ok=True)
                goc_c = os.path.join(rac, ten_c + ".goc-wm")
                if not os.path.exists(goc_c):
                    shutil.copy2(p_c, goc_c)      # shadow cục bộ đã dọn sạch 11/08
                os.replace(p_thu, p_c)
                with KHOA:
                    ds_s = [json.loads(l) for l in open(SO_CHU_THE, encoding="utf-8")
                            if l.strip()]
                    for m in ds_s:
                        if m.get("tep") == ten_c:
                            m["da_xoa_wm"] = True
                    with open(SO_CHU_THE, "w", encoding="utf-8") as f:
                        for m in ds_s:
                            f.write(json.dumps(m, ensure_ascii=False) + "\n")
                try:                               # vân tay theo ảnh mới
                    import gap_anh as _ga
                    from PIL import Image as _Im3
                    p_vt = os.path.join(KHO_CHU_THE, "van-tay.json")
                    vt = json.load(open(p_vt)) if os.path.exists(p_vt) else {}
                    vt[ten_c] = str(_ga._dhash(_Im3.open(p_c)))
                    json.dump(vt, open(p_vt, "w"))
                except Exception:
                    pass
                return self._js({"ok": True})
            if d == "/api/xoa-wm-hoan":
                ten_c = os.path.basename(than.get("tep", ""))
                goc_c = os.path.join(KHO_CHU_THE, "thung-rac", ten_c + ".goc-wm")
                if not os.path.exists(goc_c):
                    return self._js({"loi": "ảnh này chưa xoá watermark lần nào"}, 400)
                p_c = os.path.join(KHO_CHU_THE, ten_c)
                os.replace(goc_c, p_c)
                with KHOA:                         # gỡ cờ đã-xoá trong sổ
                    ds_s = [json.loads(l) for l in open(SO_CHU_THE, encoding="utf-8")
                            if l.strip()]
                    for m in ds_s:
                        if m.get("tep") == ten_c:
                            m.pop("da_xoa_wm", None)
                    with open(SO_CHU_THE, "w", encoding="utf-8") as f:
                        for m in ds_s:
                            f.write(json.dumps(m, ensure_ascii=False) + "\n")
                try:                               # vân tay quay về theo bản gốc
                    import gap_anh as _ga
                    from PIL import Image as _Im4
                    p_vt = os.path.join(KHO_CHU_THE, "van-tay.json")
                    vt = json.load(open(p_vt)) if os.path.exists(p_vt) else {}
                    vt[ten_c] = str(_ga._dhash(_Im4.open(p_c)))
                    json.dump(vt, open(p_vt, "w"))
                except Exception:
                    pass
                return self._js({"ok": True})
            if d == "/api/kho-nha-hoan":
                # HOÀN TÁC xoá: kéo ảnh từ thùng rác về + trả dòng sổ
                dong_h = than.get("dong") or []
                with KHOA:
                    rac = os.path.join(KHO_CHU_THE, "thung-rac")
                    ds_s = [json.loads(l) for l in open(SO_CHU_THE, encoding="utf-8")
                            if l.strip()]
                    co_tep = {m.get("tep") for m in ds_s}
                    for m in dong_h:
                        t_h = m.get("tep", "")
                        if t_h in co_tep:
                            continue
                        p_r = os.path.join(rac, os.path.basename(t_h))
                        if os.path.exists(p_r):
                            os.replace(p_r, os.path.join(KHO_CHU_THE,
                                                         os.path.basename(t_h)))
                        ds_s.append(m)
                    with open(SO_CHU_THE, "w", encoding="utf-8") as f:
                        for m in ds_s:
                            f.write(json.dumps(m, ensure_ascii=False) + "\n")
                return self._js({"ok": True, "so": len(dong_h)})
            if d == "/api/tao-card":
                viec = os.path.join(DD.VIEC, than["ma"])
                return self._js(_tao_card(viec, than))
            if d == "/api/kiem-chinh-ta":
                ma_job = f"c{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "soát chính tả"}
                threading.Thread(target=_chay_kiem_ct, daemon=True,
                                 args=(ma_job, than["ma"], than.get("tieu_de", ""),
                                       than.get("loi_binh", ""))).start()
                return self._js({"job": ma_job})
            if d == "/api/luu-loi":
                r = _luu_loi(than["ma"], than.get("tieu_de", ""),
                             than.get("loi_binh", ""), bool(than.get("duyet")))
                # Duyệt lời xong là MÁY TỰ ĐI TIẾP, không chờ ai bảo (anh chốt 06/08).
                if than.get("duyet") and not r.get("loi"):
                    DH.cham(os.path.join(DD.VIEC, than["ma"]), "duyet_loi")   # ⏱
                    ma_job = f"s{int(time.time() * 1000)}"
                    with KHOA:
                        VIEC_JOB[ma_job] = {"xong": False, "buoc": "chuẩn bị"}
                    VIEC_JOB_MA[ma_job] = than["ma"]
                    threading.Thread(target=_sau_duyet_loi, daemon=True,
                                     args=(ma_job, than["ma"])).start()
                    r["job_tiep"] = ma_job
                return self._js(r)
            if d == "/api/ho-so-bai":
                # đọc lại tin → lập hồ sơ (anh sửa lời xong bấm lại cho khớp)
                ma_job = f"hs{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "đọc tin, lập hồ sơ bài"}

                def chay_hs(mj=ma_job, m_v=than["ma"]):
                    try:
                        r = _trich_ho_so_bai(m_v)
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "ho_so": r}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": str(e)}
                threading.Thread(target=chay_hs, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/goi-y-the":
                # GỢI THẺ SỐ LIỆU CHẠY TAY (anh hỏi 11/08: "sao không thấy đề xuất thẻ
                # nữa"). Máy gợi vốn chỉ chạy trong chuỗi SAU DUYỆT LỜI — bài chưa duyệt,
                # hoặc anh sửa lời sau khi duyệt, thì không có đường nào gợi lại. Nay có.
                ma_job = f"gt{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "máy đọc lời, tìm số đắt"}

                def chay_gt(mj=ma_job, m_v=than["ma"]):
                    try:
                        sys.path.insert(0, os.path.expanduser(
                            "~/.claude/skills/soc-tai-nguyen/cong-cu"))
                        import goi_y_the
                        r = goi_y_the.goi_y(os.path.join(DD.VIEC, m_v), ghi=True)
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "so": len(r.get("the", [])),
                                            "the": r.get("the", []),
                                            "loi": r.get("loi", "")}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": str(e)}
                threading.Thread(target=chay_gt, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/goi-y-doi":
                # ⿻ MÁY GỢI KHUNG ĐÔI CHẠY TAY (việc #58). Trong luồng gán nháp thì
                # khung đôi tự chạy ở cuối; nút này để chạy lại cho bài anh đã gán tay
                # xong — không phải gán lại từ đầu chỉ để có khung đôi.
                ma_d = than["ma"]
                if not ((_doc_kho_xep(ma_d) or {}).get("xep") or {}):
                    return self._js({"loi": "chưa có bản máy xếp kho — bấm 🧠 trước"}, 400)
                ma_job = f"gd{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "máy soi cảnh cần hai ảnh"}

                def chay_gd(mj=ma_job, m_v=ma_d):
                    def bao(b, x, n):
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": False, "buoc": b}
                    try:
                        r = _gan_khung_doi(m_v, bao)
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, **r}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": str(e)}
                threading.Thread(target=chay_gd, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/xep-kho-nghia":
                # 🧠 MÁY XẾP KHO THEO NGỮ NGHĨA (anh đặt 11/08 tối) — model cao đọc
                # nhãn + lời rồi ghép; xong thì dải kho tự bày theo bản này
                ma_job = f"xk{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "máy đọc kho + lời"}

                def chay_xk(mj=ma_job, m_v=than["ma"]):
                    def bao(b, x, n):
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": False, "buoc": b}
                    try:
                        r = _xep_kho_nghia(m_v, bao)
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, **r}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": str(e)}
                threading.Thread(target=chay_xk, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/xep-kho-nghia-gan":
                # GÁN HÀNG LOẠT theo bản máy xếp: mỗi câu lấy tấm ĐẦU model chọn.
                # Cảnh nào anh đã tự gán thì KHÔNG đụng (chỉ điền chỗ trống), trừ khi
                # gửi de_len=1. Ảnh về bài qua đúng cửa lay_theo_url như mọi đường khác.
                ma_g = than["ma"]
                viec_g = os.path.join(DD.VIEC, ma_g)
                xep_g = (_doc_kho_xep(ma_g) or {}).get("xep") or {}
                if not xep_g:
                    return self._js({"loi": "chưa có bản máy xếp — bấm 🧠 trước"}, 400)
                ma_job = f"xg{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "gán theo bản máy xếp"}

                def chay_xg(mj=ma_job, m_v=ma_g, v_v=viec_g, xp=xep_g,
                            de_len=bool(than.get("de_len"))):
                    try:
                        nh_g = _nhap(v_v)
                        bd_g = dict(nh_g.get("ban_do", {}))
                        nhap_g = dict(nh_g.get("nhap", {}))
                        tk_g = nh_g.get("tu_khoa", {}) or {}
                        so_g, n_c = 0, 0
                        # MỌI Ô, kể cả cảnh phụ (khoá "3:0") — luật chính/phụ tương đương
                        ap_g = dict(nh_g.get("anh_phu", {}))

                        def _da_co(k):
                            if ":" in k:
                                c0, j0 = k.split(":")
                                return bool((ap_g.get(c0) or [])[int(j0):int(j0) + 1]
                                            and (ap_g.get(c0) or [])[int(j0)])
                            return bool(bd_g.get(k))
                        can = [(k, v) for k, v in sorted(
                                   xp.items(), key=lambda x: (int(x[0].split(":")[0]),
                                                              x[0].count(":")))
                               if v.get("tep") and (de_len or not _da_co(k))]
                        for k_c, v in can:
                            n_c += 1
                            with KHOA:
                                VIEC_JOB[mj] = {"xong": False,
                                                # mã ô phụ "3:0" — int() thẳng là nổ
                                                "buoc": f"gán cảnh {_ten_ma_o(k_c)}",
                                                "da": n_c, "tong": len(can)}
                            u_noi = (f"http://127.0.0.1:{CONG}/kho-nha-anh/"
                                     f"{urllib.parse.quote(v['tep'][0])}"
                                     f"?ma={urllib.parse.quote(m_v)}")
                            try:
                                r = gap_anh.lay_theo_url([u_noi],
                                                         os.path.join(v_v, "anh"),
                                                         tk_g.get(k_c.split(":")[0], ""))
                            except Exception:
                                continue
                            if not r.get("anh"):
                                continue
                            duong_g = "anh/" + r["anh"][0]["tep"]
                            if ":" in k_c:                  # Ô PHỤ
                                c0, j0 = k_c.split(":")
                                o_ds = list(ap_g.get(c0) or [])
                                while len(o_ds) <= int(j0):
                                    o_ds.append("")
                                o_ds[int(j0)] = duong_g
                                ap_g[c0] = o_ds
                            else:
                                bd_g[k_c] = duong_g
                                nhap_g[k_c] = {"nguon": "kho", "may_xep": True}
                            so_g += 1
                            _luu_nhap(m_v, {**nh_g, "ban_do": bd_g, "nhap": nhap_g,
                                            "anh_phu": ap_g})
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "so": so_g,
                                            # mã ô giữ CHUỖI — ô phụ là "9:0"
                                            "trong": [k for k, v in xp.items()
                                                      if not v.get("tep")]}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": str(e)}
                threading.Thread(target=chay_xg, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/gan-nhap":
                # chạy TAY lại vòng gán nháp (bài duyệt lời từ trước khi có Phương án ①,
                # hoặc anh gỡ vài tấm muốn máy đề cử lại)
                ma_job = f"gn{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "gán nháp"}
                threading.Thread(target=_chay_gan_nhap_job, daemon=True,
                                 args=(ma_job, than["ma"])).start()
                return self._js({"job": ma_job})
            if d == "/api/nhap-chot":
                # anh ✓ NHẬN cảnh nháp: một câu ({cau}) hoặc cả loạt ({tat_ca:1}).
                # Chỉ rơi cờ cảnh ĐANG CÓ ẢNH — cờ "thiếu"/"máy gỡ" giữ lại làm dấu
                # câu còn trống, anh gán tay thì cờ tự rơi ở /api/gan.
                viec = os.path.join(DD.VIEC, than["ma"])
                nh = _nhap(viec)
                bd, nhap = nh.get("ban_do", {}), dict(nh.get("nhap", {}))
                if than.get("tat_ca"):
                    bo = [c for c, v in nhap.items()
                          if v.get("nguon") in ("kho", "web") and not v.get("go")
                          and bd.get(c)]
                else:
                    bo = [str(than["cau"])] if bd.get(str(than["cau"])) else []
                for c in bo:
                    nhap.pop(c, None)
                nh["nhap"] = nhap
                _luu_nhap(than["ma"], nh)
                return self._js({"ok": True, "nhap": nhap, "da_nhan": len(bo)})
            if d == "/api/duyet":
                _luu_nhap(than["ma"], than)
                return self._js(_duyet(than["ma"], bool(than.get("bo_qua_dau_nguon")),
                                       bool(than.get("bo_qua_nhap"))))
            if d == "/api/lenh":
                return self._js(_lenh(than.get("text", ""), than.get("nguon", "trạm")))
            if d == "/api/gap":
                ma_job = f"g{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False}
                threading.Thread(target=_chay_gap, daemon=True, args=(
                    ma_job, than["ma"], than.get("cach", "tim"), than.get("doi_so", ""),
                    int(than.get("can", 18)))).start()
                return self._js({"job": ma_job})
            if d == "/api/tim-loat":
                # Anh hỏi 05/08: "để lấy đủ ảnh có khi phải gõ tìm 20-30 lần, anh phải tự làm
                # à?" — không. Trạm đã có sẵn từ khoá cho TỪNG CÂU (Claude gợi ý lúc mở việc),
                # nên nó tự chạy hết một lượt rồi bày ra MỘT lưới gom theo câu. Anh không gõ
                # lần nào, chỉ ngồi chọn. Bóc danh sách chứ không tải nên rẻ: ~6 giây một câu.
                ma_job = f"n{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "chuẩn bị"}
                    VIEC_JOB_MA[ma_job] = than["ma"]
                viec = os.path.join(DD.VIEC, than["ma"])

                def chay3(mj=ma_job, v=viec):
                    try:
                        nh = _nhap(v)
                        tk = {int(k): x for k, x in nh.get("tu_khoa", {}).items() if x.strip()}
                        kb = json.load(open(os.path.join(v, "kich-ban.json"), encoding="utf-8"))
                        cau = _tach_cau(kb.get("loi_binh", ""))
                        nhom, thay, n = [], set(), 0
                        for i in sorted(tk):
                            n += 1
                            with KHOA:
                                VIEC_JOB[mj] = {"xong": False, "buoc": f"tìm “{tk[i][:28]}”",
                                                "da": n, "tong": len(tk)}
                            r = gap_anh.xem_truoc(tk[i])
                            ds = []
                            for a in r.get("anh", []):
                                if a["u"] in thay:     # ảnh đã hiện ở câu trước thì thôi,
                                    continue           # đỡ bày trùng cho anh phải nhìn hai lần
                                thay.add(a["u"])
                                ds.append(a)
                                if len(ds) >= 12:
                                    break
                            nhom.append({"cau": i, "chu": cau[i] if i < len(cau) else "",
                                         "tu_khoa": tk[i], "anh": ds})
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": "", "nhom": nhom,
                                            "tong_anh": sum(len(x["anh"]) for x in nhom)}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": str(e), "nhom": []}
                threading.Thread(target=chay3, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/xem-truoc":
                ma_job = f"x{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "mở Google, bóc danh sách ảnh"}

                def chay(mj=ma_job, tk=than.get("tu_khoa", "")):
                    try:
                        r = gap_anh.xem_truoc(tk)
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": r["loi"], "anh": r["anh"]}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": str(e), "anh": []}
                threading.Thread(target=chay, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/lay-chon":
                # Anh đã CHỌN ảnh từ kết quả tìm → từ khoá này ra ảnh thật, ghi sổ học.
                _ghi_tim_ok(than["ma"], than.get("tu_khoa", ""),
                            len(than.get("urls", [])), "tram")
                ma_job = f"c{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "tải ảnh anh chọn"}
                viec = os.path.join(DD.VIEC, than["ma"])

                def chay2(mj=ma_job, v=viec, u=than.get("urls", []),
                          tk=than.get("tu_khoa", ""), crops=than.get("crops") or {},
                          wms=than.get("wms") or {}, ma_v=than["ma"]):
                    def tien(x, n):
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": False, "buoc": "soi watermark",
                                            "da": x, "tong": n}
                    _keo(ma_v, "anh", +len(u))
                    try:
                        r = gap_anh.lay_theo_url(u, os.path.join(v, "anh"), tk,
                                                 bao_tien=tien, crops=crops)
                        # 🧽 VÙNG XOÁ WM GHI TỪ TRANG CHỌN (anh đặt 11/08): ảnh về rồi
                        # mới vá được. Nếu ảnh đồng thời bị CROP thì quy đổi toạ độ vùng
                        # (anh khoanh trên ảnh GỐC, ảnh về đã bị cắt); vùng nằm ngoài
                        # phần giữ = watermark đã bị cắt đi, khỏi vá.
                        for url_w, vg in wms.items():
                            tep_w = next((a["tep"] for a in r.get("anh", [])
                                          if a.get("url") == url_w), None)
                            if not tep_w:
                                continue
                            bx = dict(vg)
                            c = crops.get(url_w)
                            if c and c.get("w") and c.get("h"):
                                bx = {"x": (vg["x"] - c["x"]) / c["w"],
                                      "y": (vg["y"] - c["y"]) / c["h"],
                                      "w": vg["w"] / c["w"], "h": vg["h"] / c["h"]}
                            x0 = max(0.0, bx["x"]); y0 = max(0.0, bx["y"])
                            x1 = min(1.0, bx["x"] + bx["w"]); y1 = min(1.0, bx["y"] + bx["h"])
                            if x1 - x0 < 0.004 or y1 - y0 < 0.004:
                                continue           # vùng đã bị crop cắt mất
                            with KHOA:
                                VIEC_JOB[mj] = {"xong": False,
                                                "buoc": f"xoá watermark {tep_w}"}
                            p_w = os.path.join(v, "anh", tep_w)
                            lama_w = os.path.expanduser("~/.cache/lama-venv/bin/python3")
                            if not os.path.exists(lama_w):
                                print("  ⚠ chưa cài venv LaMa — bỏ vá vùng WM")
                                break
                            p_ra = p_w + ".vá.jpg"
                            try:
                                with WM_KHOA:      # MỘT LaMa một lúc (bài học sập nguồn 10/08)
                                    rw = subprocess.run(
                                        [lama_w, os.path.join(DD.MAY, "xoa_wm.py"),
                                         "--anh", p_w, "--ra", p_ra, "--kieu", "tu",
                                         "--vung", f"{x0},{y0},{x1 - x0},{y1 - y0}"],
                                        capture_output=True, text=True, timeout=300,
                                        cwd="/tmp")
                                if rw.returncode == 0 and os.path.exists(p_ra):
                                    # giữ gốc vào _goc-crop — nút ↩ Hoàn sẵn có lo hoàn tác
                                    tg = os.path.join(v, "anh", "_goc-crop")
                                    os.makedirs(tg, exist_ok=True)
                                    bk_w = os.path.join(tg, tep_w)
                                    os.path.exists(bk_w) or shutil.copy2(p_w, bk_w)
                                    os.replace(p_ra, p_w)
                                    _don_sau_doi_anh(v, "anh/" + tep_w)
                                else:
                                    print(f"  ⚠ vá WM {tep_w} hỏng: {(rw.stderr or '')[-160:]}")
                            except Exception as e_w:
                                print(f"  ⚠ vá WM {tep_w}: {e_w}")
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": r.get("loi", ""),
                                            "so": len(r.get("anh", [])),
                                            # url → tệp: giao diện cần cái này để gán ảnh vừa
                                            # tải vào ĐÚNG câu anh đã chọn nó cho
                                            "ban_do_url": {a["url"]: "anh/" + a["tep"]
                                                           for a in r.get("anh", [])},
                                            "anh": _danh_sach_anh(v)}
                    except Exception as e:
                        with KHOA:
                            VIEC_JOB[mj] = {"xong": True, "loi": str(e), "so": 0}
                    finally:
                        _keo(ma_v, "anh", -len(u))
                threading.Thread(target=chay2, daemon=True).start()
                return self._js({"job": ma_job})
            if d == "/api/loc":
                ma_job = f"l{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "soi nội dung ảnh"}
                threading.Thread(target=_chay_loc, daemon=True,
                                 args=(ma_job, than["ma"])).start()
                return self._js({"job": ma_job})
            if d == "/api/cach-hien":
                # Máy đoán được ảnh QUÁ NGANG (tỉ lệ ≥2) thì đừng cắt, nhưng KHÔNG đoán được
                # trong bảng ấy chữ nào đáng đọc. Nên cách hiển thị để NGƯỜI chốt.
                viec = os.path.join(DD.VIEC, than["ma"])
                p_ch = os.path.join(viec, "anh", "cach-hien.json")
                try:
                    ch = json.load(open(p_ch, encoding="utf-8"))
                except Exception:
                    ch = {}
                ten, kieu = than.get("tep", ""), than.get("kieu", "")
                if kieu:
                    ch[ten] = kieu
                else:
                    ch.pop(ten, None)               # bỏ chọn = trả về cho máy tự quyết
                json.dump(ch, open(p_ch, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                return self._js({"ok": True, "cach_hien": ch})
            if d == "/api/xoa-nhieu":
                # Xoá HÀNG LOẠT — kho gắp về cả trăm tấm, vứt từng cái thì mỏi tay.
                viec = os.path.join(DD.VIEC, than["ma"])
                nh = _nhap(viec)
                xong, hong = 0, []
                for duong in than.get("duongs", []):
                    d2 = _an_toan(duong)
                    if not d2:
                        hong.append(duong)
                        continue
                    p2 = os.path.join(viec, d2)
                    try:
                        os.path.exists(p2) and os.remove(p2)
                        th = os.path.join(viec, "anh", "_thumb", d2.replace("/", "__"))
                        os.path.exists(th) and os.remove(th)
                        xong += 1
                    except Exception:
                        hong.append(duong)
                    nh["ban_do"] = {k: v for k, v in nh.get("ban_do", {}).items() if v != d2}
                _luu_nhap(than["ma"], nh)
                return self._js({"ok": True, "xong": xong, "hong": hong,
                                 "anh": _danh_sach_anh(viec), "ban_do": nh["ban_do"]})
            if d == "/api/crop-anh":
                # CẮT ẢNH TẠI CHỖ (anh đặt 09/08: xử phần watermark mà vẫn muốn lấy):
                # bản gốc NHẤT được giữ ở anh/_goc-crop/ để hoàn tác; ảnh cắt đè CÙNG TÊN
                # nên mọi tham chiếu (bản đồ, khung đôi, sổ nguồn) tự theo.
                viec = os.path.join(DD.VIEC, than["ma"])
                duong = than.get("duong", "")
                if not (duong.startswith("anh/") and duong.endswith(".jpg")
                        and ".." not in duong):
                    return self._js({"ok": False, "loi": "đường ảnh không hợp lệ"})
                p_a = os.path.join(viec, duong)
                if not os.path.exists(p_a):
                    return self._js({"ok": False, "loi": "không thấy ảnh"})
                try:
                    bx = [max(0.0, min(1.0, float(than[k]))) for k in ("x", "y", "w", "h")]
                except (KeyError, ValueError):
                    return self._js({"ok": False, "loi": "vùng cắt không hợp lệ"})
                im = Image.open(p_a).convert("RGB")
                W_a, H_a = im.size
                x0, y0 = int(bx[0] * W_a), int(bx[1] * H_a)
                x1 = min(W_a, int((bx[0] + bx[2]) * W_a))
                y1 = min(H_a, int((bx[1] + bx[3]) * H_a))
                if x1 - x0 < 120 or y1 - y0 < 120:
                    return self._js({"ok": False, "loi": "vùng cắt quá nhỏ — kéo rộng hơn"})
                thu_goc = os.path.join(viec, "anh", "_goc-crop")
                os.makedirs(thu_goc, exist_ok=True)
                bk = os.path.join(thu_goc, os.path.basename(duong))
                if not os.path.exists(bk):         # giữ bản GỐC NHẤT — crop nhiều lần vẫn
                    shutil.copy2(p_a, bk)          # hoàn được về nguyên thủy
                im.crop((x0, y0, x1, y1)).save(p_a, quality=92)
                _don_sau_doi_anh(viec, duong)
                # toạ độ vùng watermark trong sổ nguồn tính theo ẢNH CŨ — sau crop chúng
                # vô nghĩa (thường watermark chính là phần bị cắt đi). Đánh dấu da_crop
                # để xưởng thôi né vùng cho ảnh này (tự soi 09/08).
                p_sn = os.path.join(viec, "anh", "so-nguon.jsonl")
                if os.path.exists(p_sn):
                    try:
                        dong_moi = []
                        for dong_sn in open(p_sn, encoding="utf-8"):
                            try:
                                d_sn = json.loads(dong_sn)
                                if os.path.basename(d_sn.get("file", "")) == os.path.basename(duong):
                                    d_sn["da_crop"] = True
                                dong_moi.append(json.dumps(d_sn, ensure_ascii=False) + "\n")
                            except Exception:
                                dong_moi.append(dong_sn)
                        open(p_sn, "w", encoding="utf-8").writelines(dong_moi)
                    except Exception:
                        pass
                return self._js({"ok": True, "anh": _danh_sach_anh(viec)})
            if d == "/api/crop-undo":
                viec = os.path.join(DD.VIEC, than["ma"])
                duong = than.get("duong", "")
                bk = os.path.join(viec, "anh", "_goc-crop", os.path.basename(duong))
                p_a = os.path.join(viec, duong)
                if not (duong.startswith("anh/") and os.path.exists(bk)):
                    return self._js({"ok": False, "loi": "không có bản gốc để hoàn"})
                shutil.copy2(bk, p_a)
                os.remove(bk)
                _don_sau_doi_anh(viec, duong)
                return self._js({"ok": True, "anh": _danh_sach_anh(viec)})
            if d == "/api/xoa-anh":
                # Vứt hẳn tấm rác khỏi kho. Đây là ảnh ứng viên, chưa vào video — xoá là
                # xoá bản tải về, không đụng gì tới video hay bản đồ câu đã chốt.
                viec = os.path.join(DD.VIEC, than["ma"])
                duong = _an_toan(than.get("duong", ""))
                if not duong:
                    return self._js({"ok": False, "loi": "đường dẫn không hợp lệ"})
                p = os.path.join(viec, duong)
                os.path.exists(p) and os.remove(p)
                th = os.path.join(viec, "anh", "_thumb", duong.replace("/", "__"))
                os.path.exists(th) and os.remove(th)
                nh = _nhap(viec)                    # gỡ khỏi các câu đang gán tấm này
                nh["ban_do"] = {k: v for k, v in nh.get("ban_do", {}).items() if v != duong}
                _luu_nhap(than["ma"], nh)
                return self._js({"ok": True, "anh": _danh_sach_anh(viec),
                                 "ban_do": nh["ban_do"]})
            if d == "/api/mo":
                # Anh chốt 05/08: xếp kho xong phải bấm được là MỞ THẲNG tới thư mục chứa,
                # đừng bắt đi lần mò trong Finder.
                p = _duong_mo(than["ma"], than.get("dich", "hop"))
                if not p or not os.path.isdir(p):
                    return self._js({"ok": False, "loi": "chưa có thư mục đó"})
                _mo_thu_muc(p)
                return self._js({"ok": True, "duong": p})
            if d == "/api/xep-kho":
                viec = os.path.join(DD.VIEC, than["ma"])
                DH.cham(viec, "kho_bat_dau")     # ⏱
                r = subprocess.run([sys.executable,
                                    os.path.join(DD.MAY, "buoc3_xepkho.py"), viec],
                                   capture_output=True, text=True, timeout=600, cwd=DD.MAY)
                ra = (r.stdout or "").strip().splitlines()
                ok = r.returncode == 0 and any("✅" in x for x in ra)
                if ok:
                    DH.cham(viec, "kho_xong")    # ⏱ MỐC CUỐI — video đã nằm trên Drive
                    _bao_ve(f"📦 Đã xếp kho: {than['ma']}\n{ra[-1][:160] if ra else ''}"
                            + "\n⏱ cả bài: " + (DH.dep(DH.tong_ket(viec)["tong_giay"])
                                                or "—"))
                return self._js({"ok": ok, "nhat_ky": ra[-4:],
                                 "loi": "" if ok else (r.stderr or "\n".join(ra))[-400:]})
            if d == "/api/dung":
                v_d = os.path.join(DD.VIEC, than["ma"])
                DH.cham(v_d, "duyet_anh")        # ⏱ khép chặng anh duyệt ảnh
                DH.cham(v_d, "dung_bat_dau")
                ma_job = f"d{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "xưởng đang dựng (~2 phút)"}
                threading.Thread(target=_chay_dung, daemon=True,
                                 args=(ma_job, than["ma"])).start()
                return self._js({"job": ma_job})
            if d == "/api/tai-len":
                # Ảnh anh tự đưa vào (tải từ Facebook cầu thủ, chụp màn hình…). Gửi lên dạng
                # base64 cho gọn — không phải dựng bộ đọc multipart chỉ để nhận vài tấm ảnh.
                viec = os.path.join(DD.VIEC, than["ma"])
                ds = [(t.get("ten", "khong-ten"), base64.b64decode(t["data"]),
                       t.get("url", ""), t.get("trang", ""))
                      for t in than.get("tep", [])]
                if not ds:
                    return self._js({"loi": "không có tệp nào"}, 400)
                _keo(than["ma"], "anh", +len(ds))
                try:
                    r = gap_anh.nhan_tep(ds, os.path.join(viec, "anh"))
                finally:
                    _keo(than["ma"], "anh", -len(ds))
                # Trang nguồn là Google thì tham số q chính là TỪ KHOÁ anh đã gõ trong Chrome.
                # Ghi sổ SAU nhan_tep và chỉ khi ảnh LƯU THÀNH CÔNG (anh dặn 06/08: gõ thì
                # chưa học vội — lúc đầu có thể gõ trật; LƯU ĐƯỢC ẢNH mới chứng minh từ khoá
                # đúng). Ảnh hỏng/không đọc được thì lần gắp đó không dạy được gì.
                if r.get("anh"):
                    for _, _, _, trang in ds:
                        if "google." in trang and "q=" in trang:
                            try:
                                q = urllib.parse.parse_qs(
                                    urllib.parse.urlparse(trang).query).get("q", [""])[0]
                                _ghi_tim_ok(than["ma"], q, len(r["anh"]), "extension")
                                break
                            except Exception:
                                pass
                r["anh_kho"] = _danh_sach_anh(viec)
                return self._js(r)
            if d == "/api/nhan-video":
                # extension gửi link trang video (+ cookie phiên) — trạm tải nền bằng yt-dlp
                ma_job = f"v{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False, "buoc": "chuẩn bị"}
                    VIEC_JOB_MA[ma_job] = than["ma"]
                threading.Thread(target=_nhan_video_job, daemon=True,
                                 args=(ma_job, than["ma"], than.get("trang", ""),
                                       than.get("src", ""), than.get("cookies") or [])).start()
                return self._js({"job": ma_job})
            if d == "/api/cap-nhat":
                # ANH BẤM LÀ MÁY TỰ CẬP NHẬT (anh chốt 16/08). Ba chốt an toàn:
                #  ① có việc đang chạy thì TỪ CHỐI — chuỗi sau Duyệt lời là luồng bên
                #    trong tiến trình này, khởi động lại giữa chừng là giết nó không kịp
                #    báo gì (anh đã mất một bài vì chuyện đó 12/08).
                #  ② `--ff-only`: máy phụ lỡ sửa mã thì DỪNG và nói thẳng, đừng tự trộn.
                #  ③ pull xong mới thoát; bộ quản lý dịch vụ (launchd trên Mac,
                #    Task Scheduler trên Windows) bật lại — mã .py chỉ nạp lúc khởi động,
                #    không thoát thì mã mới nằm trên ổ mà trạm vẫn chạy bản cũ.
                with KHOA:
                    ban = [k for k, v in VIEC_JOB.items() if not v.get("xong")]
                if ban:
                    return self._js({"loi": f"đang có {len(ban)} việc chạy dở — "
                                            "chờ xong rồi cập nhật, không thì mất việc"}, 409)
                ra, err, ma_g = _git("pull", "--ff-only", "origin", "main", cho=180)
                if ma_g:
                    return self._js({"loi": (err or ra or "git pull hỏng")[:300]}, 500)
                _do_ban_moi()
                if than.get("khoi_dong_lai"):
                    threading.Timer(1.0, lambda: os._exit(0)).start()
                return self._js({"ok": True, "ket_qua": ra[-400:],
                                 "dang": BAN_MOI.get("dang", "")})
            if d == "/api/goi-y":
                ma_job = f"y{int(time.time() * 1000)}"
                with KHOA:
                    VIEC_JOB[ma_job] = {"xong": False}
                threading.Thread(target=_chay_goi_y, daemon=True,
                                 args=(ma_job, than["ma"], bool(than.get("de_len")))).start()
                return self._js({"job": ma_job})
            return self._tra(404, "text/plain; charset=utf-8", "không có đường này")
        except Exception as e:
            return self._js({"loi": str(e), "vet": traceback.format_exc()[-600:]}, 500)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cong", type=int, default=8756)
    a = ap.parse_args()
    global CONG
    CONG = a.cong
    if not os.path.isdir(DD.VIEC):
        sys.exit(f"DỪNG — không thấy thư mục việc {DD.VIEC}")
    n = len(_ds_viec())
    print(f"TRẠM DUYỆT TÀI NGUYÊN · {n} thư mục việc · http://localhost:{a.cong}/")
    print("   Ctrl-C để tắt")
    ThreadingHTTPServer(("127.0.0.1", a.cong), Tay).serve_forever()


if __name__ == "__main__":
    main()
