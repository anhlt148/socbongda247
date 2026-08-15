#!/usr/bin/env python3
"""Bước 1 của xưởng: từ mã tin -> kịch bản JSON trong thư mục việc riêng.

Anh chốt 06/08: bước này gọi **skill `soc-content`** chứ không gọi hàm python nữa.
Vì sao đổi: script cũ (`viet_loi_binh.py`) gọi model nhưng KHÔNG có khung tự học — anh sửa
kịch bản bao nhiêu lần nó cũng không học được gì; lại đọc một hồ sơ văn phong riêng ở ổ máy,
đã lệch với bộ não trên Drive suốt từ 05/08 mà không ai biết.

Skill chạy tự động được y như trước: chỗ này gọi `claude -p`, launchd gọi chỗ này.
Đường cũ vẫn giữ (cờ --script) phòng khi skill trục trặc giữa ca sản xuất.
"""
import json, os, re, subprocess, sys, urllib.parse
from datetime import datetime


# đường đầy đủ trước, tên trần sau: script có thể chạy ngoài trạm (cron, launchd
# một-lần) nơi PATH không có ~/.local/bin — gọi tên trần là FileNotFoundError câm
_CLAUDE = NT.tim_claude()   # MỘT nguồn — nen_tang lo cả macOS lẫn Windows (15/08)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD
import nen_tang as NT                    # noqa: E402

DUNG_SCRIPT = "--script" in sys.argv
ap = [x for x in sys.argv[1:] if not x.startswith("--")]
if not ap:
    sys.exit("dùng: buoc1_viet.py <mã tin> [số giây] [--script]")
ma = ap[0]
giay = int(ap[1]) if len(ap) > 1 else 58        # anh chốt 06/08: bằng Nhím (trung vị 58s)

ngay = datetime.now().strftime("%Y-%m-%d")
ds = json.load(open(os.path.join(DD.BAN_TIN, ngay + ".json")))
tin = next((t for t in ds if t["ma"] == ma), None)
if not tin:
    sys.exit(f"không thấy mã {ma}")

viec = os.path.join(DD.VIEC, ngay, f"video-{DD.so_video_ke(ngay)}-{ma}")
os.makedirs(viec, exist_ok=True)


def qua_skill(tin, so_giay):
    """Gọi skill soc-content trong một phiên claude không ngữ cảnh."""
    lenh = (
        f"/soc-content Viết kịch bản {so_giay} giây cho tin dưới đây. "
        f"Đọc BRAIN.md và bộ não phong cách trước khi viết; lấy tư liệu bằng "
        f"cong-cu/doc_bai.py; trả về DUY NHẤT khối JSON theo mẫu trong skill, "
        f"không giải thích gì thêm.\n\n"
        f"Tiêu đề tin: {tin['tieu_de']}\n"
        f"Link: {tin.get('link', '')}\n"
        f"Link dự phòng: {' '.join((tin.get('cac_link') or [])[:4])}\n"
        f"Số báo cùng đưa: {tin.get('so_nguon', 1)}\n"
        f"Các nguồn: {', '.join((tin.get('cac_nguon') or [])[:8])}\n"
        f"Tin cách đây: {tin.get('tuoi_gio', '?')} giờ"
    )
    p = subprocess.run([_CLAUDE, "-p", lenh], capture_output=True, text=True, timeout=600)
    m = re.search(r"\{.*\}", p.stdout, re.S)
    if not m:
        return {"loi": "skill không trả JSON", "tho": (p.stdout or p.stderr)[:400]}
    try:
        return json.loads(m.group(0))
    except Exception as e:
        return {"loi": f"JSON hỏng: {e}", "tho": m.group(0)[:400]}


if DUNG_SCRIPT:
    import viet_loi_binh
    kq = viet_loi_binh.viet(tin, giay)
else:
    kq = qua_skill(tin, giay)
    # Bốn cửa tự kiểm chạy bằng code, không nhờ model tự chấm mình.
    if "loi" not in kq:
        sys.path.insert(0, os.path.join(DD.DRIVE_SKILL, "soc-content", "cong-cu")
                        if hasattr(DD, "DRIVE_SKILL") else
                        os.path.expanduser("~/.claude/skills/soc-content/cong-cu"))
        try:
            import kiem
            kq = kiem.kiem(kq, giay)
        except Exception as e:
            kq.setdefault("canh_bao", "")
            kq["canh_bao"] += f" (không chạy được cửa kiểm: {e})"

kq.setdefault("nguon_tin", tin.get("link"))
kq.setdefault("tin_goc", tin["tieu_de"])
kq.setdefault("so_nguon", tin.get("so_nguon", 1))

json.dump(kq, open(os.path.join(viec, "kich-ban.json"), "w"), ensure_ascii=False, indent=1)
json.dump(tin, open(os.path.join(viec, "tin-goc.json"), "w"), ensure_ascii=False, indent=1)
print(f"[{ma}] {'ĐẠT' if kq.get('dat') else 'KHÔNG ĐẠT: ' + str(kq.get('ly_do_khong_dat') or kq.get('loi'))}")
print(f"[{ma}] {kq.get('tieu_de','')}")
print(f"[{ma}] {kq.get('so_tieng_thuc','?')} tiếng ≈ {round(kq.get('so_tieng_thuc', 0) * 60 / 258, 1)} giây")
print(f"[{ma}] {viec}")
# Link bấm-là-vào-đúng-bài để anh duyệt (anh chốt 06/08: viết xong phải đưa link, đừng bắt
# anh tự mở trạm rồi dò trong danh sách).
ma_viec = os.path.relpath(viec, DD.VIEC)
print(f"[{ma}] DUYỆT LỜI: http://localhost:8756/?viec={urllib.parse.quote(ma_viec)}")
if kq.get("nguon_tin"):
    print(f"[{ma}] BÀI GỐC : {kq['nguon_tin']}")
