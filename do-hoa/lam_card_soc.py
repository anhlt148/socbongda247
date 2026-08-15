#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MENU CHỌN CARD cho kênh Sóc (short 9:16) — "chọn là chạy".

Người dùng (hoặc trạm) chỉ CHỌN loại card + điền vài trường thân thiện; script tự dịch sang
spec của engine render_card, tự áp KHỔ của kênh (9:16 từ config), tự đặt tên theo SỐ CẢNH,
và render ra thư mục tài nguyên. Không cần biết JSON schema của engine, không gõ lệnh khổ.

Dùng:
  <venv>/python lam_card_soc.py picks.json            # đọc config_soc.json cùng thư mục
  <venv>/python lam_card_soc.py picks.json --config config_soc.json --ra thu_muc_khac

picks.json = danh sách card người chọn, mỗi card:
  versus : {"canh":3,"loai":"versus","tieu_de":"...","trai":["Tên","Điểm","macccờ"],"phai":["Tên","Điểm","macccờ","win"(tuỳ)]}
  stat   : {"canh":7,"loai":"stat","nhan":"...","so":"36","ghi_chu":"..."}
  bxh    : {"canh":11,"loai":"bxh","tieu_de":"...","hang":[["Tên",số,true(nổi bật, tuỳ)],...]}
  timeline:{"canh":9,"loai":"timeline","tieu_de":"...","moc":[["2020","..."],["2023","..."]]}
Mã cờ đặt trong assets/flags/ (vd br, gb-eng, no). Thiếu cờ thì bỏ phần tử cờ đi.
"""
import argparse, json, os, subprocess, sys, unicodedata, re

HERE = os.path.dirname(os.path.abspath(__file__))

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:24] or "card"

def to_spec(p, accent):
    """Dịch 1 lựa chọn thân thiện -> spec engine render_card."""
    loai = p.get("loai")
    base = {"accent": p.get("mau", accent)}
    if loai == "versus":
        tr, ph = p["trai"], p["phai"]
        left = {"name": tr[0], "value": str(tr[1])}
        if len(tr) > 2 and tr[2]: left["flag"] = tr[2]
        right = {"name": ph[0], "value": str(ph[1])}
        if len(ph) > 2 and ph[2]: right["flag"] = ph[2]
        if len(ph) > 3 and ph[3]: right["win"] = True
        if len(tr) > 3 and tr[3]: left["win"] = True
        return {**base, "type": "versus", "title": p.get("tieu_de", ""), "left": left, "right": right}
    if loai == "stat":
        return {**base, "type": "stat", "label": p.get("nhan", ""), "value": str(p.get("so", "")),
                "note": p.get("ghi_chu", "")}
    if loai in ("bxh", "leaderboard"):
        rows = [{"name": r[0], "value": r[1], **({"highlight": True} if len(r) > 2 and r[2] else {})}
                for r in p["hang"]]
        return {**base, "type": "leaderboard", "title": p.get("tieu_de", ""), "rows": rows}
    if loai == "timeline":
        pts = [{"year": m[0], "caption": m[1]} for m in p["moc"]]
        return {**base, "type": "timeline", "title": p.get("tieu_de", ""), "points": pts}
    raise SystemExit(f"❌ Cảnh {p.get('canh','?')}: loại card '{loai}' chưa hỗ trợ "
                     f"(dùng: versus / stat / bxh / timeline).")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("picks", help="File JSON các card người chọn.")
    ap.add_argument("--config", default=os.path.join(HERE, "config_soc.json"))
    ap.add_argument("--ra", help="Ghi đè thư mục ra (mặc định lấy từ config).")
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding="utf-8"))
    doc = cfg.get("khung", "9:16") == "9:16"
    accent = cfg.get("accent", "#e11d2a")
    py = cfg.get("python", sys.executable)
    out_dir = os.path.abspath(a.ra or os.path.join(HERE, cfg.get("out_dir", "cards_ra")))
    os.makedirs(out_dir, exist_ok=True)

    picks = json.load(open(a.picks, encoding="utf-8"))
    specs = []
    for p in picks:
        canh = int(p.get("canh", len(specs)))
        spec = to_spec(p, accent)
        ten = f"{canh:02d}_{slug(spec.get('title') or spec.get('label') or spec['type'])}.png"
        spec["out"] = os.path.join(out_dir, ten)
        specs.append(spec)

    tmp = os.path.join(out_dir, "_specs_tmp.json")
    json.dump(specs, open(tmp, "w"), ensure_ascii=False)
    cmd = [py, os.path.join(HERE, "scripts", "render_card.py"), tmp]
    if doc:
        cmd.append("--doc")
        vung = cfg.get("vung_card", [0.0, 1.0])      # card chỉ nằm trong dải này (chừa khung tiêu đề short)
        cmd += ["--doc-vung", f"{vung[0]},{vung[1]}"]
    r = subprocess.run(cmd)
    os.remove(tmp)
    if r.returncode == 0:
        print(f"\n✅ Xong {len(specs)} card {'DỌC 9:16' if doc else '16:9'} -> {out_dir}")
        for s in specs: print("   ", os.path.basename(s["out"]))
    else:
        raise SystemExit("❌ Có lỗi khi render — xem log ở trên.")

if __name__ == "__main__":
    main()
