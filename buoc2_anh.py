#!/usr/bin/env python3
"""Bước 2: gom ảnh cho một thư mục việc, từ bài gốc + các bài cùng cụm."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD
import lay_anh

viec = DD.tim_viec(sys.argv[1])
can = int(sys.argv[2]) if len(sys.argv) > 2 else 12
tin = json.load(open(os.path.join(viec, "tin-goc.json")))
kb = json.load(open(os.path.join(viec, "kich-ban.json")))
url = kb.get("nguon_tin") or tin.get("link")
r = lay_anh.lay(url, os.path.join(viec, "anh"), can,
                ten_nguon=(tin.get("cac_nguon") or [""])[0],
                them_link=tin.get("cac_link") or [],
                so_bai=int(sys.argv[3]) if len(sys.argv) > 3 else 5)
print(f"{os.path.basename(viec)}: {len(r['anh'])} ảnh dùng được {r.get('loi','')}")
