#!/usr/bin/env python3
"""Gom thêm link báo cùng chủ đề từ bảng tin -> nhiều ảnh để CHỌN, thay vì lấy được gì dùng nấy.

Một bài báo chỉ cho 4-11 ảnh, phần lớn là ảnh nhỏ hoặc ảnh tác giả. Muốn chọn được ảnh
đúng người đúng trận thì phải có nhiều ảnh mà chọn — nên quét cả bảng tin theo từ khoá.
"""
import json, os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD

viec, tu_khoa = sys.argv[1], [t.lower() for t in sys.argv[2:]]
ds = json.load(open(os.path.join(DD.BAN_TIN, datetime.now().strftime("%Y-%m-%d") + ".json")))
tin = json.load(open(os.path.join(viec, "tin-goc.json")))

links = list(tin.get("cac_link") or [])
for t in ds:
    td = t["tieu_de"].lower()
    if not any(k in td for k in tu_khoa):
        continue
    for u in ([t.get("link")] + (t.get("cac_link") or [])):
        if u and "news.google.com" not in u and u not in links:
            links.append(u)
tin["cac_link"] = links
json.dump(tin, open(os.path.join(viec, "tin-goc.json"), "w"), ensure_ascii=False, indent=1)
print(f"{os.path.basename(viec)}: {len(links)} link để gom ảnh")
