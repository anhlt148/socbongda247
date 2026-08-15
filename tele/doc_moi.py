#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐỌC tin CHƯA XỬ LÝ trong hộp thư Tele — phiên Claude gọi khi Monitor đánh thức.

In các dòng mới kể từ lần đọc trước rồi dời con trỏ (`da-doc.txt` = số byte đã đọc).
Chạy với `--nhin` thì chỉ xem, KHÔNG dời con trỏ.
"""
import json
import os
import sys

NHA = os.path.dirname(os.path.abspath(__file__))
HOP_DEN = os.path.join(NHA, "hop-den.jsonl")
DA_DOC = os.path.join(NHA, "da-doc.txt")

vt = 0
if os.path.exists(DA_DOC):
    try:
        vt = int(open(DA_DOC).read().strip() or 0)
    except ValueError:
        vt = 0
if not os.path.exists(HOP_DEN):
    sys.exit("hộp thư trống")
with open(HOP_DEN, encoding="utf-8") as f:
    f.seek(vt)
    moi = f.read()
    cuoi = f.tell()
if not moi.strip():
    print("(không có tin mới)")
    sys.exit(0)
from datetime import datetime
for dong in moi.strip().splitlines():
    try:
        d = json.loads(dong)
    except Exception:
        continue
    gio = datetime.fromtimestamp(d.get("luc", 0)).strftime("%H:%M")
    media = f" [{d.get('loai_media', '')}: {d.get('media', '')}]" if d.get("loai_media") else ""
    print(f"[{gio}] {d.get('nguoi', '?')}: {d.get('chu', '')}{media}")
if "--nhin" not in sys.argv:
    open(DA_DOC, "w").write(str(cuoi))
