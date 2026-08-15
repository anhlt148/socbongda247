#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GỬI tin Telegram — chiều trả lời của cầu chat 2 chiều (phiên Claude gọi cái này).

Dùng:  python3 tele_gui.py "nội dung"              # gửi vào nhóm Sóc
       python3 tele_gui.py --rieng "nội dung"      # gửi chat riêng của anh
       python3 tele_gui.py --ma "nội dung"         # mã tin 6 hex bọc <code>: CHẠM LÀ COPY
       echo "nội dung dài" | python3 tele_gui.py - # đọc từ stdin

Tin dài quá 4000 ký tự tự cắt thành nhiều tin. Mặc định gửi chữ trơn (không parse_mode)
để không bao giờ chết vì ký tự đặc biệt — bài học bot BHXH: Markdown lỗi là tin im lặng
không đi. Cờ --ma bật HTML mode CHỈ để bọc mã tin (anh yêu cầu 07/08: "mã bấm vào là
copy được, gõ lại nhọc quá"); toàn bộ chữ được escape trước nên vẫn an toàn như chữ trơn.

Mẹo hay hơn nữa: viết lệnh dạng /lam_b1a8ab (gạch dưới liền) — Telegram coi cả cụm là
NÚT BẤM, anh chạm một cái là lệnh tự gửi, khỏi copy. bot_nghe đã hiểu dạng này.
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

CAU_HINH = os.path.expanduser("~/.config/socbongda247/telebot.json")


def gui(chu, rieng=False, ma_copy=False):
    d = json.load(open(CAU_HINH, encoding="utf-8"))
    chat = d["chat_id_rieng"] if rieng else d["chat_id"]
    tham = {"chat_id": chat}
    if ma_copy:
        # escape TOÀN BỘ trước, rồi mới bọc <code> quanh mã 6 hex đứng riêng —
        # thứ tự ngược lại là thẻ code bị escape mất
        chu = html.escape(chu, quote=False)
        chu = re.sub(r"(?<![\w/_])([0-9a-f]{6})(?![\w])", r"<code>\1</code>", chu)
        tham["parse_mode"] = "HTML"
    for i in range(0, len(chu), 4000):
        than = urllib.parse.urlencode({**tham, "text": chu[i:i + 4000]}).encode()
        r = json.load(urllib.request.urlopen(
            f"https://api.telegram.org/bot{d['bot_token']}/sendMessage",
            data=than, timeout=20))
        if not r.get("ok"):
            sys.exit(f"LỖI gửi: {r}")
    print("đã gửi")


if __name__ == "__main__":
    ds = [a for a in sys.argv[1:] if a not in ("--rieng", "--ma")]
    chu = sys.stdin.read() if (ds and ds[0] == "-") or not ds else " ".join(ds)
    gui(chu.strip(), rieng="--rieng" in sys.argv, ma_copy="--ma" in sys.argv)
