#!/usr/bin/env python3
"""BOT NGHE LỆNH — Sóc Bóng Đá 247

Chạy nền, nghe nhóm Telegram, trả lời lệnh và nhận ảnh chụp màn hình.

Lệnh:
  /tin            bảng tin nóng nhất (quét mới nếu bảng cũ quá 2 giờ)
  /lam <mã>       bắt làm video từ tin đó → viết lời bình, báo lại để duyệt
  /bo <mã>        bỏ tin — máy học để lần sau không đề xuất loại này
  /trangthai      ca hiện tại đang tới đâu
  /giupdo         danh sách lệnh

Gửi CHỮ / ẢNH / GHI ÂM (không phải lệnh /) → CHUYỂN VÀO HỘP THƯ PHIÊN CLAUDE
           (`tele/hop-den.jsonl`) — phiên đang trực sẽ đọc và TRẢ LỜI như chat 2 chiều
           (anh chốt 07/08). Bot chỉ lên tiếng khi KHÔNG có phiên nào trực.

VÌ SAO bot này là NGƯỜI NGHE DUY NHẤT: Telegram chỉ cho MỘT nơi giữ getUpdates mỗi bot —
07/08 từng chạy song song telecau (cầu phiên) + bot này, hai bên giành tin, anh nhắn mà
phiên không thấy gì. Từ đó gộp: bot này giữ getUpdates, việc chuyển phiên nó làm luôn.
"""
import json, os, re, subprocess, sys, tempfile, threading, time, traceback
import urllib.parse, urllib.request
from datetime import datetime

CAU_HINH = os.path.expanduser("~/.config/socbongda247/telebot.json")
BASE = os.path.dirname(os.path.abspath(__file__))
# RADAR nằm TRONG socbongda247 — bản đầu ghi GOC/radar (thư mục CHA) vì bot từng ở thư mục
# con; dọn về gốc thì đường lệch, /tin /lam tra bảng tin ở /Users/letuananh/radar (không có)
# → "Không thấy mã" dù mã đúng. Anh bắt trúng lỗi này 07/08.
RADAR = os.path.join(BASE, "radar")
CLAUDE_BIN = os.path.expanduser("~/.local/bin/claude")
HANG_CHO = os.path.join(BASE, "hang-cho.jsonl")
NHAT_KY = os.path.join(BASE, "nhat-ky-lenh.jsonl")
# hộp thư cầu 2 chiều với phiên Claude (Monitor của phiên canh file này)
HOP_PHIEN = os.path.join(BASE, "tele", "hop-den.jsonl")
MEDIA_PHIEN = os.path.join(BASE, "tele", "media")


def _cfg():
    return json.load(open(CAU_HINH))


def gui(text, chat_id=None):
    c = _cfg()
    d = {"chat_id": chat_id or c["chat_id"], "text": text[:4000]}
    try:
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{c['bot_token']}/sendMessage",
            data=urllib.parse.urlencode(d).encode(), timeout=25)
    except Exception as e:
        print("lỗi gửi:", e)


def _ghi_nhat_ky(ai, lenh, chi_tiet=""):
    with open(NHAT_KY, "a", encoding="utf-8") as f:
        f.write(json.dumps({"luc": datetime.now().isoformat(timespec="seconds"),
                            "ai": ai, "lenh": lenh, "chi_tiet": chi_tiet},
                           ensure_ascii=False) + "\n")


def _ban_tin_hom_nay(quet_neu_cu=2.0):
    p = os.path.join(RADAR, "ban-tin", datetime.now().strftime("%Y-%m-%d") + ".json")
    cu = (not os.path.exists(p)) or (time.time() - os.path.getmtime(p)) / 3600 > quet_neu_cu
    if cu:
        subprocess.run([sys.executable, os.path.join(RADAR, "san_tin.py"), "quet"],
                       capture_output=True, timeout=300)
    return json.load(open(p)) if os.path.exists(p) else []


def lenh_tin(ai):
    ds = _ban_tin_hom_nay()
    if not ds:
        return "Chưa quét được tin. Thử lại sau ít phút."
    d = [t for t in ds if t["vung"] == "vn"][:10] or ds[:10]
    dong = [f"📰 BẢNG TIN {datetime.now().strftime('%H:%M %d/%m')}", ""]
    for t in d:
        # /lam_mã liền gạch dưới = NÚT BẤM của Telegram — chạm là viết luôn, khỏi gõ
        dong.append(f"/lam_{t['ma']} · {t['diem']}đ · {t['so_nguon']} báo · {t['tuoi_gio']:.0f}h")
        dong.append(f"    {t['tieu_de'][:88]}")
    dong += ["", "Chạm /lam_mã để viết · /bo_mã để bỏ"]
    _ghi_nhat_ky(ai, "/tin")
    return "\n".join(dong)


# /lam gọi SKILL soc-content qua `claude -p` — đường chính thức từ 06/08 (máy viết cũ
# viet_loi_binh.py đã về hưu: không đọc bộ não trên Drive, không có khung tự học).
# Viết mất 3–5 phút nên chạy NỀN theo hàng đợi — vòng nghe tin không bị nghẽn.
HANG_VIET = []                                     # (ma, ai, chat, tieu_de tin)
_DANG_VIET = {"ma": ""}


def _viet_nen():
    import glob as _g
    while HANG_VIET:
        ma, ai, chat, tieu_de = HANG_VIET.pop(0)
        _DANG_VIET["ma"] = ma
        try:
            for lan in (1, 2):
                r = subprocess.run([CLAUDE_BIN, "-p", f"/soc-content {ma}"],
                                   capture_output=True, text=True, timeout=2400, cwd=BASE)
                # skill nằm trên Drive qua symlink — Drive chớp một cái là claude không
                # thấy lệnh ("Unknown command"), gặp đúng lỗi đó thì thử lại một lần
                if "Unknown command" not in (r.stdout or "") + (r.stderr or ""):
                    break
                time.sleep(20)
            sys.path.insert(0, BASE)
            import duong_dan as _dd
            # việc của tin nằm ở <VIEC>/<ngày>/video-N-<mã tin>
            ds = sorted(_g.glob(os.path.join(_dd.VIEC, "*", f"video-*-{ma}")),
                        key=os.path.getmtime, reverse=True)
            kb = {}
            if ds and os.path.exists(os.path.join(ds[0], "kich-ban.json")):
                kb = json.load(open(os.path.join(ds[0], "kich-ban.json"), encoding="utf-8"))
            if kb.get("dat"):
                vc = os.path.relpath(ds[0], _dd.VIEC)
                tieng = len((kb.get("loi_binh") or "").split())
                gui(f"✅ VIẾT XONG {ma}\n\nTÍT: {kb.get('tieu_de', '')}\n"
                    f"({len(kb.get('tieu_de', ''))} ký tự · {tieng} tiếng ≈ {tieng / 4.3:.0f} giây)\n\n"
                    f"Duyệt lời (mở trên máy):\n"
                    f"http://localhost:8756/?viec={urllib.parse.quote(vc, safe='')}"
                    + (f"\n\n⚠️ {kb['canh_bao'][:250]}" if kb.get("canh_bao") else ""), chat)
            else:
                duoi = ((r.stdout or "") + (r.stderr or "")).strip()[-450:]
                gui(f"⚠️ {ma}: chưa ra bản đạt.\n{duoi}", chat)
        except Exception as e:
            gui(f"❌ Lỗi khi viết {ma}: {e}", chat)
        finally:
            _DANG_VIET["ma"] = ""


def lenh_lam(ai, ma, chat=None):
    ds = _ban_tin_hom_nay(quet_neu_cu=6)
    tin = next((t for t in ds if t["ma"] == ma), None)
    if not tin:
        return f"Không thấy mã {ma}. Gõ /tin để xem bảng mới."
    # ghi sổ học của radar: tin anh CHỌN — chấm điểm lần sau giống anh hơn
    subprocess.run([sys.executable, os.path.join(RADAR, "san_tin.py"), "chon", ma],
                   capture_output=True, timeout=60)
    _ghi_nhat_ky(ai, "/lam", ma)
    HANG_VIET.append((ma, ai, chat or _cfg()["chat_id"], tin["tieu_de"]))
    if _DANG_VIET["ma"]:
        return (f"📥 Xếp hàng {ma} — đang viết {_DANG_VIET['ma']} trước, "
                "xong bài nào em báo bài đó.")
    threading.Thread(target=_viet_nen, daemon=True).start()
    return f"⏳ Đang viết: {tin['tieu_de'][:70]}…\n(3–5 phút — xong em gửi tít + link duyệt)"


def lenh_bo(ai, ma):
    subprocess.run([sys.executable, os.path.join(RADAR, "san_tin.py"), "bo", ma],
                   capture_output=True, timeout=60)
    _ghi_nhat_ky(ai, "/bo", ma)
    return f"✗ Đã bỏ {ma}. Tôi ghi lại để lần sau bớt đề xuất loại tin này."


def lenh_trangthai():
    n = 0
    if os.path.exists(HANG_CHO):
        n = sum(1 for _ in open(HANG_CHO, encoding="utf-8"))
    p = os.path.join(RADAR, "ban-tin", datetime.now().strftime("%Y-%m-%d") + ".json")
    tin = len(json.load(open(p))) if os.path.exists(p) else 0
    gio = datetime.now().hour
    ca = "sáng (đăng 7:30)" if gio < 10 else ("trưa (đăng 12:00)" if gio < 16 else "tối (đăng 19:30)")
    return (f"📊 Ca hiện tại: {ca}\n"
            f"• Bảng tin hôm nay: {tin} cụm tin\n"
            f"• Hàng chờ dựng: {n} kịch bản\n"
            f"• Giờ máy: {datetime.now().strftime('%H:%M %d/%m/%Y')}")


def _ocr(duong_dan):
    """Đọc chữ trong ảnh chụp màn hình.

    Thử ba kiểu bố cục rồi lấy kết quả đọc được nhiều chữ nhất — ảnh chụp màn hình
    điện thoại có nhiều vùng (thanh trạng thái, khung chat, ảnh trong bài) nên không
    kiểu nào luôn thắng. Ảnh nhỏ thì phóng to trước, chữ nhỏ OCR hay trượt.
    """
    goc = duong_dan
    try:
        from PIL import Image
        im = Image.open(duong_dan)
        if max(im.size) < 1600:                       # phóng ảnh nhỏ lên cho dễ đọc
            r = 1600 / max(im.size)
            im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
            goc = tempfile.mktemp(suffix=".png")
            im.save(goc)
    except Exception:
        pass
    tot = ""
    for psm in ("6", "3", "4"):
        try:
            r = subprocess.run(["tesseract", goc, "stdout", "-l", "vie+eng", "--psm", psm],
                               capture_output=True, text=True, timeout=90)
            v = " ".join(r.stdout.split())
            if len(v) > len(tot):
                tot = v
        except Exception:
            continue
    return tot


def xu_ly_anh(ai, file_id, muon_lam=False):
    c = _cfg()
    try:
        info = json.load(urllib.request.urlopen(
            f"https://api.telegram.org/bot{c['bot_token']}/getFile?file_id={file_id}", timeout=25))
        path = info["result"]["file_path"]
        tmp = tempfile.mktemp(suffix=os.path.splitext(path)[1] or ".jpg")
        urllib.request.urlretrieve(
            f"https://api.telegram.org/file/bot{c['bot_token']}/{path}", tmp)
    except Exception as e:
        return f"Không tải được ảnh: {e}"
    chu = _ocr(tmp)
    if len(chu) < 25:
        return ("Đọc được rất ít chữ trong ảnh. Anh chụp cận phần chữ giúp em — "
                "chụp cả bài thì chữ bị nhỏ, máy đọc trượt.")
    # đối chiếu với bảng tin: báo nào đã đưa tin này chưa
    ds = _ban_tin_hom_nay(quet_neu_cu=6)
    tu = {w.lower() for w in re.findall(r"[A-Za-zÀ-ỹ]{4,}", chu)}
    khop = []
    for t in ds[:400]:
        tt = {w.lower() for w in re.findall(r"[A-Za-zÀ-ỹ]{4,}", t["tieu_de"])}
        if tt and len(tu & tt) / len(tt) >= 0.35:
            khop.append(t)
    with open(HANG_CHO, "a", encoding="utf-8") as f:
        f.write(json.dumps({"luc": datetime.now().isoformat(timespec="seconds"),
                            "ai": ai, "nguon": "ảnh chụp màn hình",
                            "chu_doc_duoc": chu[:1500],
                            "bao_da_dua": [t["ma"] for t in khop[:3]]},
                           ensure_ascii=False) + "\n")
    _ghi_nhat_ky(ai, "ảnh", chu[:80])
    tl = [f"🖼 Đọc được từ ảnh ({len(chu)} ký tự):", chu[:600], ""]
    if khop:
        tl.append(f"✅ ĐÃ ĐỐI CHIẾU: {len(khop)} tin trên báo trùng nội dung này —")
        for t in khop[:3]:
            tl.append(f"   [{t['ma']}] {t['so_nguon']} báo · {t['tieu_de'][:70]}")
        tl.append("\nLàm video từ nguồn báo (có số liệu kiểm chứng): /lam " + khop[0]["ma"])
    else:
        tl.append("⚠️ CHƯA KIỂM CHỨNG: không báo nào đưa tin này.")
        tl.append("Đã ghi vào hàng chờ nhưng em chưa dựng — tin chỉ có trên mạng xã hội")
        tl.append("mà không nguồn nào xác nhận thì rủi ro sai cao.")
        tl.append("Anh muốn làm vẫn được, nhắn: /lam-anh")
    if muon_lam:
        tl.append("")
        tl.append("📌 Anh ghi /lam kèm ảnh — đã đưa vào hàng chờ ưu tiên.")
    return "\n".join(tl)


def _phien_dang_truc():
    """Có phiên Claude nào đang canh hộp thư không (Monitor = một tiến trình tail -f)."""
    try:
        r = subprocess.run(["pgrep", "-f", "tail.*hop-den"],
                           capture_output=True, text=True, timeout=5)
        return bool(r.stdout.strip())
    except Exception:
        return False


def _tai_media_phien(file_id, ten_goc):
    """Tải ảnh/ghi âm anh gửi về máy để phiên Claude đọc thẳng."""
    c = _cfg()
    try:
        info = json.load(urllib.request.urlopen(
            f"https://api.telegram.org/bot{c['bot_token']}/getFile?file_id={file_id}",
            timeout=25))
        path = info["result"]["file_path"]
        os.makedirs(MEDIA_PHIEN, exist_ok=True)
        dich = os.path.join(MEDIA_PHIEN,
                            f"{int(time.time())}-{os.path.basename(ten_goc or path)}")
        urllib.request.urlretrieve(
            f"https://api.telegram.org/file/bot{c['bot_token']}/{path}", dich)
        return dich
    except Exception:
        return ""


def _chuyen_phien(ai, chu, chat, media="", loai_media=""):
    """Đưa tin vào hộp thư phiên. Không có phiên trực thì báo lại một câu cho anh yên tâm."""
    with open(HOP_PHIEN, "a", encoding="utf-8") as f:
        f.write(json.dumps({"luc": int(time.time()), "nguoi": ai, "chu": chu,
                            "media": media, "loai_media": loai_media, "chat": chat},
                           ensure_ascii=False) + "\n")
    if not _phien_dang_truc():
        gui("📨 Đã ghi vào hộp thư, nhưng hiện KHÔNG có phiên Claude nào đang trực — "
            "tin sẽ được xử khi phiên mở lại. Lệnh máy vẫn chạy: /tin /lam /bo /trangthai",
            chat)


GIUP = """🤖 Trợ lý Sóc Bóng Đá 247

/tin — bảng tin nóng nhất
/lam <mã> — viết kịch bản video từ tin đó
/bo <mã> — bỏ tin, tôi học để lần sau bớt đề xuất
/trangthai — ca hiện tại tới đâu
/giupdo — bảng này

Nhắn CHỮ / gửi ẢNH / GHI ÂM → chuyển thẳng phiên Claude đang trực, Claude trả lời tại đây
(ảnh muốn đi đường OCR-đối chiếu báo cũ: ghi caption /lam)"""


def xu_ly(u):
    m = u.get("message") or u.get("edited_message")
    if not m:
        return
    chat = str(m.get("chat", {}).get("id", ""))
    ai = (m.get("from", {}) or {}).get("first_name", "?")
    c = _cfg()
    if chat not in (str(c.get("chat_id")), str(c.get("chat_id_rieng"))):
        return
    if m.get("photo"):
        # Ảnh về tay PHIÊN (anh hay gửi ảnh chụp bài FB để đặt làm video — phiên đọc ảnh
        # giỏi hơn OCR nhiều). Muốn đường OCR-đối-chiếu cũ thì ghi caption bắt đầu bằng /lam.
        cap = (m.get("caption") or "").strip()
        if cap.lower().startswith("/lam"):
            gui("🔍 Đang đọc ảnh…", chat)
            gui(xu_ly_anh(ai, m["photo"][-1]["file_id"], muon_lam=True), chat)
            return
        duong = _tai_media_phien(m["photo"][-1]["file_id"], "anh.jpg")
        _chuyen_phien(ai, cap, chat, media=duong, loai_media="ảnh")
        return
    if m.get("voice"):
        duong = _tai_media_phien(m["voice"]["file_id"], "voice.ogg")
        _chuyen_phien(ai, (m.get("caption") or "").strip(), chat,
                      media=duong, loai_media="ghi âm")
        return
    if m.get("video") or m.get("video_note"):
        # anh gửi VIDEO MẪU thấy hay để phiên mổ xẻ học văn phong (anh chốt 07/08).
        # Bot API chỉ tải được tệp ~20MB — trượt thì xin LINK, đừng im lặng.
        v = m.get("video") or m.get("video_note")
        duong = _tai_media_phien(v["file_id"], "video.mp4")
        if duong:
            _chuyen_phien(ai, (m.get("caption") or "").strip(), chat,
                          media=duong, loai_media="video")
        else:
            gui("⚠️ Video này em tải không được (bot Telegram chỉ tải được tệp ~20MB). "
                "Anh gửi LINK video (YouTube/TikTok/FB) là chắc ăn nhất.", chat)
        return
    if m.get("document"):
        duong = _tai_media_phien(m["document"]["file_id"],
                                 m["document"].get("file_name", "tep"))
        _chuyen_phien(ai, (m.get("caption") or "").strip(), chat,
                      media=duong, loai_media="tài liệu")
        return
    t = (m.get("text") or m.get("caption") or "").strip()
    if not t:
        return
    # /lam_b1a8ab (gạch dưới liền) = dạng NÚT BẤM của Telegram — chạm là gửi, anh khỏi gõ
    # mã (anh yêu cầu 07/08). Đổi về dạng có khoảng trắng rồi xử như thường.
    t = re.sub(r"^/(lam|bo)_([0-9a-f]{6})\b", r"/\1 \2", t, flags=re.I)
    low = t.lower()
    if low.startswith(("/start", "/giupdo", "/help")):
        gui(GIUP, chat)
    elif low.startswith("/tin"):
        gui("🔎 Đang quét tin…", chat)
        gui(lenh_tin(ai), chat)
    elif low.startswith("/lam"):
        p = t.split()
        gui(lenh_lam(ai, p[1], chat) if len(p) > 1 else "Thiếu mã. Ví dụ: /lam 844e26", chat)
    elif low.startswith("/bo"):
        p = t.split()
        gui(lenh_bo(ai, p[1]) if len(p) > 1 else "Thiếu mã. Ví dụ: /bo 844e26", chat)
    elif low.startswith("/trangthai"):
        gui(lenh_trangthai(), chat)
    elif t.startswith("/"):
        gui("Chưa có lệnh đó. Gõ /giupdo để xem danh sách.", chat)
    else:
        # Chữ trơn = anh đang NÓI CHUYỆN với phiên Claude — chuyển hộp thư, phiên trả lời.
        # (Trước 07/08 chỗ này tự ghi "hàng chờ ý tưởng" và trả lời máy — anh tưởng lỗi.)
        _chuyen_phien(ai, t, chat)


def chay():
    c = _cfg()
    tok = c["bot_token"]
    off = None
    print(f"Bot đang nghe nhóm {c.get('chat_ten','')} … (Ctrl-C để dừng)")
    gui("🟢 Trợ lý đã lên. Gõ /giupdo để xem lệnh.")
    while True:
        try:
            url = f"https://api.telegram.org/bot{tok}/getUpdates?timeout=50"
            if off:
                url += f"&offset={off}"
            d = json.load(urllib.request.urlopen(url, timeout=70))
            for u in d.get("result", []):
                off = u["update_id"] + 1
                try:
                    xu_ly(u)
                except Exception:
                    traceback.print_exc()
        except Exception:
            time.sleep(4)


if __name__ == "__main__":
    chay()
