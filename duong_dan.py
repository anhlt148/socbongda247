#!/usr/bin/env python3
"""MỘT NƠI KHAI ĐƯỜNG DẪN CHO CẢ HỆ — mọi file khác import từ đây, không tự đoán đường.

Vì sao có file này: ngày 04/08 thư mục bị dời một cấp, ba file tự tính đường bằng
`os.path.dirname(BASE)` nên trỏ trượt hết. Tệ nhất là `viet_loi_binh.py`: hồ sơ văn phong
không đọc được nhưng code lại `if os.path.exists(...) else ""` — nên nó chạy TIẾP với hồ sơ
RỖNG, không báo lỗi, và model viết ra thứ không đúng giọng kênh. Lỗi im lặng như thế đắt hơn
lỗi to tiếng nhiều lần.

Quy ước hai nhà (giữ nguyên từ sổ dự án):
  · Ổ MÁY  `~/socbongda247/`  — nơi CHẠY: tiến trình nền, thư mục việc, sổ học
  · DRIVE  `.../Kênh youtube Sóc bóng đá 247/` — nơi CHỨA: tài sản nhận diện, kho thành phẩm

Kiểm nhanh:  python3 duong_dan.py
"""
import os
import sys

# ── CẤU HÌNH RIÊNG TỪNG MÁY (anh chốt 15/08) ─────────────────────────────────
#
# Hệ này từ nay chạy trên NHIỀU MÁY: anh trên Mac, nhân viên trên Windows, sau còn
# thêm người nữa. Mỗi máy có ổ riêng, đường Drive riêng — nhưng CODE PHẢI GIỐNG HỆT
# NHAU, không được ai sửa đường dẫn trong mã rồi đẩy lên kho chung (đó là cách chắc
# chắn nhất để hai máy lệch nhau).
#
# Nên: đường dẫn ra khỏi mã, vào một tệp cấu hình của riêng máy —
#     ~/.config/socbongda247/may.json
# Tệp này KHÔNG lên git, KHÔNG lên Drive. Thiếu thì máy tự dò rồi tự tạo.
#
# Chia việc giữa ba nơi (anh chốt 15/08):
#   · KHO TÀI NGUYÊN → Drive, DÙNG CHUNG. Ảnh, video, nhãn mắt máy, từ điển — ai bồi
#     thêm thì cả nhà hưởng.
#   · THƯ MỤC VIỆC   → ổ máy, RIÊNG từng người. Bài đang làm là việc của một người;
#     để chung trên Drive là hai người ghi cùng một sổ, Drive đẻ bản trùng.
#   · THÀNH PHẨM     → Drive, dồn về MỘT chỗ cho cả nhà.
_CAU_HINH = os.path.expanduser("~/.config/socbongda247/may.json")


def _doc_cau_hinh():
    try:
        import json as _j
        return _j.load(open(_CAU_HINH, encoding="utf-8"))
    except Exception:
        return {}


def _do_drive():
    """Tự dò thư mục Drive của kênh — mỗi máy đăng nhập một tài khoản Google."""
    import glob as _g
    nen = [os.path.expanduser("~/Library/CloudStorage"),            # macOS
           os.path.expanduser("~"), "G:\\", "H:\\"]              # Windows
    for n in nen:
        for m in _g.glob(os.path.join(n, "GoogleDrive-*", "*")) + \
                _g.glob(os.path.join(n, "My Drive")) + \
                _g.glob(os.path.join(n, "Drive của tôi")):
            for d in _g.glob(os.path.join(m, "*", "*Sóc bóng đá 247*")) + \
                    _g.glob(os.path.join(m, "*Sóc bóng đá 247*")):
                if os.path.isdir(d):
                    return d
    return ""


def _do_kho_nang():
    """Ổ chứa thứ NẶNG (thư mục việc). macOS: /Volumes/DATA; Windows: D:\\ …"""
    for d in ("/Volumes/DATA/socbongda247", "D:\\socbongda247", "E:\\socbongda247"):
        if os.path.isdir(os.path.dirname(d)):
            return d
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "_kho")


_CH = _doc_cau_hinh()

# ── Hai nhà ──────────────────────────────────────────────────────────────────
MAY = os.path.dirname(os.path.abspath(__file__))
DRIVE = _CH.get("drive") or _do_drive() or os.path.join(
    os.path.expanduser("~"),
    "Library/CloudStorage/GoogleDrive-anhlt148@gmail.com/Drive của tôi",
    "Dự án với claude /Kênh youtube Sóc bóng đá 247",
)
# NGƯỜI LÀM — nhiều người cùng đẩy thành phẩm về một Drive thì hộp phải phân biệt
# được ai làm, không thì hai người cùng ngày là trùng tên hộp (anh nêu 15/08).
NGUOI = (_CH.get("nguoi") or os.environ.get("SOC_NGUOI")
         or os.path.basename(os.path.expanduser("~")))[:16]

# ── Trên ổ máy: thứ CHẠY ─────────────────────────────────────────────────────
RADAR = os.path.join(MAY, "radar")
BAN_TIN = os.path.join(RADAR, "ban-tin")            # bảng tin theo ngày
HOC_TU_ANH = os.path.join(RADAR, "hoc-tu-anh.jsonl")
# Bộ não phong cách — anh chốt 06/08: **một bản duy nhất, nằm trên Drive.**
# Trước đây có hai bản (Drive cho người đọc, ổ máy cho máy đọc) và chúng đã lệch nhau:
# bồi bộ não Drive bằng 100 short của Nhím mà máy vẫn viết theo hồ sơ cũ 04/08.
# Nay máy đọc thẳng bản Drive; muốn dạy lại máy thì chỉ việc sửa hai file này.
# Máy không nạp cả file — chỉ nạp phần nằm giữa mốc <!-- MÁY ĐỌC --> và <!-- HẾT MÁY ĐỌC -->
# (xem viet_loi_binh.py), nên bộ não dài bao nhiêu cũng không làm phình lời nhắc.
BO_NAO = os.path.join(DRIVE, "BO-NAO-PHONG-CACH.md")
THU_VIEN = os.path.join(DRIVE, "THU-VIEN-MAU-CAU.md")
VAN_PHONG = BO_NAO          # giữ tên cũ cho mã cũ khỏi gãy
# ── NHÀ THỨ BA: ổ DATA — nơi CHỨA THỨ NẶNG (anh chốt 05/08) ──────────────────
#
# Ổ hệ thống chỉ còn 45 GB, mà hệ này ăn ổ theo ba đường:
#   · thư mục việc — mỗi video gắp về hàng trăm ảnh ứng viên, dùng có vài chục
#     (video Việt Anh: 379 tấm / 173 MB, dùng 25 tấm)
#   · hồ sơ Chrome của trạm — 542 MB, phình theo số lần gắp ảnh
#   · kho nhạc + video stock — 467 MB, chỉ đọc, không cần đồng bộ lên mây
# Ổ DATA là ổ TRONG máy (Apple Fabric, Fixed) nên không lo rút nhầm như ổ cắm ngoài.
# Kèm `don_kho.py` dọn định kỳ — chuyển chỗ mà không dọn thì chỉ đổi nơi bị đầy.
#
# Mọi đường dưới đây đều TỰ RƠI VỀ chỗ cũ nếu ổ DATA không gắn được — hệ vẫn chạy, chỉ tốn ổ.
DATA = _CH.get("kho_nang") or _do_kho_nang()
_co_data = os.path.isdir(DATA)


def _o_data(ten, cu):
    """Đường trên ổ DATA nếu có, không thì rơi về chỗ cũ."""
    d = os.path.join(DATA, ten)
    return d if _co_data and os.path.isdir(d) else cu


VIEC = _CH.get("viec") or _o_data("viec", os.path.join(MAY, "viec"))


def so_video_ke(ngay):
    """Video thứ mấy trong ngày — để đặt tên `video-N-<chủ đề>` (anh chốt 05/08)."""
    import glob as _g
    return len(_g.glob(os.path.join(VIEC, ngay, "video-*"))) + 1


def tim_viec(x):
    """Nhận ĐƯỜNG DẪN, MÃ ĐẦY ĐỦ `2026-08-05/video-1-...`, hay chỉ TÊN VIDEO — đều ra.

    Từ 05/08 kho việc xếp theo NGÀY (anh chốt): `viec/<ngày>/video-N-<chủ đề>`. Gõ đủ cả
    ngày lẫn tên thì dài, nên cho gõ mỗi tên video cũng tìm ra — miễn không trùng.
    """
    import glob as _g
    x = x.rstrip("/")
    if os.path.isdir(x):
        return os.path.abspath(x)
    d = os.path.join(VIEC, x)                      # mã đầy đủ: 2026-08-05/video-1-...
    if os.path.isdir(d):
        return d
    hop = _g.glob(os.path.join(VIEC, "*", os.path.basename(x)))   # chỉ tên video
    if len(hop) == 1:
        return hop[0]
    if len(hop) > 1:
        raise SystemExit("DỪNG — tên này có ở nhiều ngày, gõ cả ngày:\n   "
                         + "\n   ".join(os.path.relpath(h, VIEC) for h in hop))
    raise SystemExit(f"DỪNG — không thấy thư mục việc: {x}\n   (kho việc ở {VIEC})")
LOG = os.path.join(MAY, "log")
HANG_CHO = os.path.join(MAY, "hang-cho.jsonl")

# ── Trên Drive: thứ CHỨA ─────────────────────────────────────────────────────
CONG_CU = os.path.join(DRIVE, "cong-cu")
TEMPLATE = os.path.join(CONG_CU, "template_tin_bong_da.py")   # nguồn chân lý bố cục/màu
QC_CONG_CHAN = os.path.join(CONG_CU, "qc_cong_chan.py")
DO_LOGO = os.path.join(CONG_CU, "do_logo.py")
KHO_VIDEO_PY = os.path.join(CONG_CU, "kho_video.py")
THU_VBEE = os.path.join(CONG_CU, "thu_vbee.py")

NHAN_DIEN = os.path.join(DRIVE, "nhan-dien")
LOGO = os.path.join(NHAN_DIEN, "logo247-tron-1024.png")
# KHO TÀI NGUYÊN — mặc định DÙNG CHUNG trên Drive (anh chốt 15/08). Máy nào muốn
# giữ bản trên ổ trong (nhanh hơn, nhưng KHÔNG chia sẻ được) thì khai trong may.json.
KHO_TAI_NGUYEN = _CH.get("kho_tai_nguyen") or \
    _o_data("kho-tai-nguyen", os.path.join(DRIVE, "kho-tai-nguyen"))
# BẢN SAO KHO TRÊN DRIVE — chỗ `dong_bo_kho.py` soi gương sang. Máy anh giữ kho ở ổ
# trong cho nhanh (KHO_TAI_NGUYEN), Drive là bản để máy khác đọc; máy nào đã trỏ thẳng
# KHO_TAI_NGUYEN vào Drive rồi thì để trống, khỏi tự soi gương với chính mình.
# ĐÍCH LƯU THỨ GẮP VỀ (anh chốt 17/08): "viec" = kho của bài đang mở (mặc định) ·
# "kho" = kho chủ thể dùng chung · đường dẫn tuyệt đối = thư mục riêng anh tự đặt.
# Vì sao cần: có lúc anh gắp tư liệu chẳng thuộc video nào — ép nó vào bài đang mở là
# làm bẩn bài, mà bỏ qua thì mất tư liệu.
DICH_ANH = str(_CH.get("dich_anh") or "viec").strip() or "viec"
DICH_VIDEO = str(_CH.get("dich_video") or "viec").strip() or "viec"

KHO_DRIVE = _CH.get("kho_drive") or (
    "" if "CloudStorage" in KHO_TAI_NGUYEN else os.path.join(DRIVE, "kho-tai-nguyen"))
NHAC = os.path.join(KHO_TAI_NGUYEN, "nhac")
VIDEO_STOCK = os.path.join(KHO_TAI_NGUYEN, "video-stock")
VIDEO_TRAN = os.path.join(KHO_TAI_NGUYEN, "video-tran")
KHO_VIDEO = os.path.join(DRIVE, "kho-video-thanh-pham")
KHONG_DAT_QC = _o_data("_KHONG-DAT-QC", os.path.join(DRIVE, "_KHONG-DAT-QC"))
CHROME_HO_SO = _o_data("chrome-tram", os.path.expanduser("~/.config/socbongda247/chrome-tram"))

# ── Bên ngoài ────────────────────────────────────────────────────────────────
# Khoá VBee — dời 06/08 về chỗ dùng chung theo MÁY (cùng lối với ~/.config/gmail).
# Trước đây trỏ vào ~/bossbaby-tiktok-agent/.env — một dự án TikTok bỏ hoang từ 15/05.
# Suýt xoá thư mục đó cho gọn ổ thì cả dây chuyền Sóc mất giọng đọc.
# Bài học: khoá dùng chung phải nằm ở ~/.config, đừng mượn nhờ thư mục dự án khác.
VBEE_ENV = os.path.expanduser("~/.config/vbee/khoa.env")
if not os.path.exists(VBEE_ENV):                       # đường cũ, phòng khi chưa dời xong
    _cu = os.path.expanduser("~/bossbaby-tiktok-agent/.env")
    if os.path.exists(_cu):
        VBEE_ENV = _cu
BOT_CAU_HINH = os.path.expanduser("~/.config/socbongda247/telebot.json")

# ── Chuẩn kênh đã chốt 04/08/2026 (sổ dự án mục 5) ───────────────────────────
GIONG_MA = "hn_female_ngochuyen_full_24k-st"        # VBee Ngọc Huyền
GIONG_TOC_DO = 1.1                                  # ~265 tiếng/phút
KENH = "SÓC BÓNG ĐÁ 247"

# Thứ BẮT BUỘC phải có mới chạy được xưởng. Thiếu một cái là dừng, không chạy tiếp
# với giá trị rỗng — đây chính là bài học của lỗi hồ sơ văn phong rỗng.
BAT_BUOC = {
    "hồ sơ văn phong": VAN_PHONG,
    "template bố cục": TEMPLATE,
    "logo sóc": LOGO,
    "kho nhạc": NHAC,
    "khoá VBee": VBEE_ENV,
}


def kiem(im_lang=False):
    """Kiểm mọi đường dẫn bắt buộc. Trả về danh sách cái thiếu."""
    thieu = [f"{ten}: {p}" for ten, p in BAT_BUOC.items() if not os.path.exists(p)]
    if not im_lang:
        for ten, p in BAT_BUOC.items():
            print(f"  {'✅' if os.path.exists(p) else '❌'} {ten:18s} {p}")
    return thieu


def bat_buoc_du():
    """Gọi ở đầu mỗi công cụ. Thiếu đường dẫn thì DỪNG HẲN, không chạy nửa vời."""
    thieu = kiem(im_lang=True)
    if thieu:
        sys.exit("DỪNG — thiếu tài sản bắt buộc:\n  " + "\n  ".join(thieu))


def nap_template():
    """Nạp template bố cục làm module. Một nguồn chân lý cho cả ảnh preview và video."""
    import importlib.util
    if not os.path.exists(TEMPLATE):
        sys.exit(f"DỪNG — không thấy template: {TEMPLATE}")
    spec = importlib.util.spec_from_file_location("tpl", TEMPLATE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def nap(ten_file, ten_module):
    """Nạp một công cụ trên Drive làm module (do_logo, kho_video, thu_vbee…)."""
    import importlib.util
    if not os.path.exists(ten_file):
        sys.exit(f"DỪNG — không thấy công cụ: {ten_file}")
    spec = importlib.util.spec_from_file_location(ten_module, ten_file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


if __name__ == "__main__":
    print("SÓC BÓNG ĐÁ 247 — kiểm đường dẫn\n")
    print(f"  ổ máy: {MAY}")
    print(f"  Drive: {DRIVE}\n")
    thieu = kiem()
    print()
    if thieu:
        print(f"❌ thiếu {len(thieu)} thứ bắt buộc — xưởng KHÔNG chạy được")
        sys.exit(1)
    print("✅ đủ tài sản bắt buộc")


# ── TÁCH CÂU DÙNG CHUNG (khai MỘT chỗ — trạm, xưởng, gợi ý cùng đọc từ đây) ──
# Kết câu = [.!?…] HOẶC [.!?…] + ngoặc đóng ("/”/'). Thiếu vế ngoặc đóng thì ba câu trích
# dẫn dính thành một khối 42 tiếng ≈ 11 giây "một ảnh đứng suốt" — anh bắt 07/08 chiều.
# Vế (?!Com|Net…): tên trang viết kiểu "Bola. Com" trong lời bình bị tách thành câu rác
# "Bola." 0,3 giây (anh bắt 08/08 trên trang chọn ảnh) — sau dấu chấm mà gặp đuôi miền
# thì coi như vẫn đang giữa câu, không tách.
TACH_CAU_RE = r"(?:(?<=[.!?…])|(?<=[.!?…][\"”’']))\s+(?!(?:Com|Net|Org|Vn|Id)\b)"

