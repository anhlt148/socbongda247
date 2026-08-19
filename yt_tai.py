#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MỘT CỬA cho mọi lần tải video bằng yt-dlp — luật khai một nơi, hai bên cùng đọc.

Anh báo 19/08: extension không tải được video YouTube, báo
"Requested format is not available". Điều tra: video ấy CÓ đủ format tới 1080p, chạy
tay thì tải ngon. Thủ phạm là **yt-dlp cũ 5 tháng** (bản 17/03 trong khi bản mới là
04/07) — YouTube đổi cách chặn liên tục, công cụ cũ là hết đường.

Ba bài học viết thành mã ở đây, để lần sau không phải điều tra lại:

① **Thông báo lỗi của yt-dlp nói dối.** "Requested format is not available" nghe như
   chọn sai định dạng, nên cả anh lẫn tôi đều đi soi format selector — trong khi gốc là
   YouTube trả về danh sách format RỖNG vì chặn. Sai bệnh thì chữa cả buổi không khỏi.

② **Trượt lần đầu thì ĐỔI CLIENT, đừng bỏ cuộc.** yt-dlp hỏi YouTube qua nhiều "cửa"
   (client). Cửa nào bị chặn thì cửa khác vẫn ăn — nhưng phải bảo nó thử.

③ **Công cụ cũ là bệnh nền.** Có cổng canh tuổi trong `kiem_tram.py`; quá 60 ngày là
   kêu, đừng đợi tới lúc anh không tải được video mới biết.
"""
import re
import shutil
import subprocess

# Định dạng muốn lấy — bốn nấc lùi dần, nấc cuối là "gì cũng được"
FORMAT = ("bv*[height<=1080][ext=mp4]+ba[ext=m4a]"
          "/bv*[height<=1080]+ba"
          "/b[height<=1080]"
          "/b")

# Các CỬA hỏi YouTube, thử lần lượt. Để trống = yt-dlp tự chọn (thường là đủ); các lượt
# sau ép cửa khác vì cửa mặc định có lúc bị chặn riêng.
CUA = ["", "default,android_vr,tv", "web_safari,mweb", "ios,android"]

# Bao lâu thì coi là CŨ. YouTube đổi cách chặn theo tháng, nên 60 ngày là rộng rãi rồi.
HAN_NGAY = 60


def them_cua(lenh, i):
    """Thêm tham số ép CỬA cho lượt thử thứ i. Lượt 0 để yt-dlp tự quyết."""
    c = CUA[i] if i < len(CUA) else ""
    return lenh + (["--extractor-args", f"youtube:player_client={c}"] if c else [])


def phien_ban():
    """Bản yt-dlp đang dùng, dạng 'YYYY.MM.DD' — chuỗi rỗng nếu không hỏi được."""
    y = shutil.which("yt-dlp")
    if not y:
        return ""
    try:
        r = subprocess.run([y, "--version"], capture_output=True, text=True, timeout=20)
        return (r.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def qua_cu(pb=None, han=HAN_NGAY):
    """yt-dlp có cũ quá không? Trả (cũ_rồi, số_ngày_tuổi)."""
    import datetime as _dt
    pb = pb if pb is not None else phien_ban()
    m = re.match(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", pb or "")
    if not m:
        return False, -1
    try:
        ra = _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return False, -1
    tuoi = (_dt.date.today() - ra).days
    return tuoi > han, tuoi


def dang_thu_lai(tho):
    """Lỗi này có đáng đổi cửa thử lại không?

    Video bị gỡ hay để riêng tư thì thử mười cửa cũng thế — đổi cửa chỉ có ích khi
    YouTube chặn hoặc trả danh sách format rỗng. Không phân biệt thì mỗi lần dán nhầm
    một link chết là máy ngồi thử bốn lượt vô ích, anh chờ mỏi mắt.
    """
    th = (tho or "").lower()
    if any(k in th for k in ("private video", "video unavailable", "has been removed",
                             "unsupported url", "no suitable", "age-restricted",
                             "members-only", "not a valid url")):
        return False
    return any(k in th for k in ("format is not available", "no video formats",
                                 "sign in", "bot", "failed to extract",
                                 "unable to download", "precondition check",
                                 "player response", "nsig", "throttl"))


def doi_loi(tho):
    """Đổi lời than của yt-dlp sang câu anh đọc là hiểu phải làm gì.

    Bản trước phun nguyên văn tiếng Anh lên màn hình. Anh đọc "Requested format is not
    available. Use --list-formats" thì biết làm gì? Câu ấy còn dẫn sai hướng nữa.
    """
    t = (tho or "").strip()
    th = t.lower()
    cu, tuoi = qua_cu()
    dem = f" (yt-dlp đã {tuoi} ngày tuổi — nên nâng cấp: brew upgrade yt-dlp)" if cu else ""
    if "format is not available" in th or "no video formats" in th:
        return ("YouTube đang chặn máy tải — đã thử đủ mọi cửa vẫn không lấy được danh "
                "sách chất lượng. Chờ vài phút rồi thử lại, hoặc dán link khác." + dem)
    if "sign in" in th or "bot" in th or "cookies" in th:
        return ("YouTube đòi đăng nhập để xác minh không phải máy. Thử lại sau ít phút, "
                "hoặc mở video ấy trong Chrome rồi gắp lại." + dem)
    if "private" in th or "unavailable" in th or "removed" in th:
        return "Video này đã bị gỡ, để riêng tư, hoặc chặn ở Việt Nam."
    if "age" in th and "restrict" in th:
        return "Video giới hạn độ tuổi — không tải được nếu chưa đăng nhập."
    if "timed out" in th or "timeout" in th:
        return "Mạng chậm hoặc video quá nặng — quá hạn chờ."
    if "unsupported url" in th or "no suitable" in th:
        return "Đường dẫn này không phải trang video mà máy tải được."
    return (t[-220:] or "yt-dlp chạy xong mà không ra tệp") + dem
