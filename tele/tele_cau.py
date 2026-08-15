#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CẦU TELEGRAM 2 CHIỀU — người-canh 0 token, cho anh ra lệnh cho Claude từ điện thoại.

Anh đặt bài 07/08/2026: "làm cho a chát được với em 2 chiều qua tele, để a ra lệnh cho em
từ điện thoại, em làm trên phiên này được."

Kiến trúc theo đúng mẫu bot CSKH (người-canh rẻ + phiên xử):
  · Script này chạy 24/7 bằng launchd, KHÔNG gọi model — chỉ long-poll Telegram getUpdates
    rồi chép tin mới vào `hop-den.jsonl`. Gần như 0 tài nguyên.
  · Phiên Claude đang mở dùng Monitor canh `hop-den.jsonl` — có dòng mới là tỉnh dậy, đọc,
    làm việc, rồi trả lời bằng `tele_gui.py`.
  · Bot: @socbongda247_bot (bot RIÊNG của kênh Sóc, chiều nhận trống — đã kiểm 07/08;
    bot chung nhà @anhlt_claude_2026_bot thì chiều nhận thuộc webhook web kho, CẤM đụng).

Chỉ nghe hai phòng: nhóm "Kênh YTB Sóc bóng đá 247" và chat riêng của anh (khai trong
telebot.json). Tin từ chỗ khác bỏ qua. Ảnh/tài liệu anh gửi (hay gửi ảnh chụp bài FB để
làm video) được tải luôn về `media/` để phiên đọc thẳng.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

NHA = os.path.dirname(os.path.abspath(__file__))
HOP_DEN = os.path.join(NHA, "hop-den.jsonl")
OFFSET = os.path.join(NHA, "offset.txt")
MEDIA = os.path.join(NHA, "media")
CAU_HINH = os.path.expanduser("~/.config/socbongda247/telebot.json")


def _cfg():
    d = json.load(open(CAU_HINH, encoding="utf-8"))
    return d["bot_token"], {str(d.get("chat_id", "")), str(d.get("chat_id_rieng", ""))}


def _goi(tk, duong, tham_so=None, timeout=65):
    u = f"https://api.telegram.org/bot{tk}/{duong}"
    if tham_so:
        u += "?" + urllib.parse.urlencode(tham_so)
    return json.load(urllib.request.urlopen(u, timeout=timeout))


def _tai_media(tk, file_id, ten_goc):
    """Tải ảnh/tài liệu về máy để phiên Claude đọc thẳng, trả về đường dẫn."""
    try:
        r = _goi(tk, "getFile", {"file_id": file_id}, timeout=30)
        duong_xa = r["result"]["file_path"]
        os.makedirs(MEDIA, exist_ok=True)
        ten = f"{int(time.time())}-{os.path.basename(ten_goc or duong_xa)}"
        dich = os.path.join(MEDIA, ten)
        urllib.request.urlretrieve(
            f"https://api.telegram.org/file/bot{tk}/{duong_xa}", dich)
        return dich
    except Exception:
        return ""


def _bien(tk, m):
    """Rút một tin Telegram thành một dòng gọn cho hộp thư."""
    d = {"luc": m.get("date", 0),
         "chat": str(m.get("chat", {}).get("id", "")),
         "nguoi": (m.get("from", {}).get("first_name", "")
                   + " " + m.get("from", {}).get("last_name", "")).strip(),
         "chu": m.get("text") or m.get("caption") or ""}
    if m.get("photo"):                              # lấy cỡ to nhất
        d["media"] = _tai_media(tk, m["photo"][-1]["file_id"], "anh.jpg")
        d["loai_media"] = "ảnh"
    elif m.get("document"):
        d["media"] = _tai_media(tk, m["document"]["file_id"],
                                m["document"].get("file_name", "tep"))
        d["loai_media"] = "tài liệu"
    elif m.get("voice"):
        d["media"] = _tai_media(tk, m["voice"]["file_id"], "voice.ogg")
        d["loai_media"] = "ghi âm"
    elif m.get("video"):
        d["loai_media"] = "video (không tải — nặng, cần thì bảo)"
    return d


def chay():
    tk, phong = _cfg()
    off = 0
    if os.path.exists(OFFSET):
        try:
            off = int(open(OFFSET).read().strip() or 0)
        except ValueError:
            off = 0
    print(f"CẦU TELE · nghe {len(phong)} phòng · hộp thư {HOP_DEN}")
    while True:
        try:
            r = _goi(tk, "getUpdates", {"timeout": 50, "offset": off + 1})
            for up in r.get("result", []):
                off = max(off, up["update_id"])
                m = up.get("message") or up.get("edited_message")
                if not m or str(m.get("chat", {}).get("id", "")) not in phong:
                    continue
                d = _bien(tk, m)
                if not d["chu"] and not d.get("media"):
                    continue
                with open(HOP_DEN, "a", encoding="utf-8") as f:
                    f.write(json.dumps(d, ensure_ascii=False) + "\n")
                print(f"→ {d['nguoi']}: {d['chu'][:60]}")
            open(OFFSET, "w").write(str(off))
        except KeyboardInterrupt:
            raise
        except Exception as e:                       # mạng chập chờn thì nghỉ nhịp rồi thử lại
            print("⚠", e)
            time.sleep(10)


if __name__ == "__main__":
    chay()
