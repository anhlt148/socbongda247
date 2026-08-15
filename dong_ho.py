#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐỒNG HỒ SẢN XUẤT — đo một video mất bao lâu, từ lúc mở việc tới lúc lên Drive.

Anh đặt 14/08: *"a muốn biết 1 video sản xuất trong bao lâu, có bộ đếm thời gian toàn
bộ quá trình hiện trên 1 góc nhỏ màn hình, kể từ lúc bấm nút tạo việc đến khi đẩy xong
video lên Drive. Tổng thời gian và thời gian từng bước set vào file gói đăng."*

Vì sao cần: mọi cải tiến tốc độ tới nay đều đoán mò — "nút Kho chậm", "chờ tìm ảnh
lâu". Có đồng hồ thì biết chắc khúc nào ăn thời gian, sửa đúng chỗ đau nhất. Đúng luật
"đo trước khi sửa".

Cách dùng — chỉ hai hàm:
    DH.cham(viec, "duyet_loi")        # đóng mốc, gọi bao nhiêu lần cũng được
    DH.tong_ket(viec)                 # {tong_giay, cac_buoc: [...], text: "…"}

Sổ nằm trong `kich-ban.json`, khoá `dong_ho` — ghi qua kich_ban.ghi_gop (cửa GHI duy
nhất có khoá fcntl), nên nhiều tiến trình chấm cùng lúc cũng không giẫm nhau.
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kich_ban as KB                                         # noqa: E402

# Thứ tự các chặng + tên tiếng Việt để in ra cho anh đọc. Mốc nào chưa có thì bỏ qua,
# không bịa: video làm dở, làm lại, hay bỏ giữa chừng đều phải in trung thực.
CHANG = ["mo_viec", "duyet_loi", "chuoi_xong", "duyet_anh",
         "dung_bat_dau", "dung_xong", "kho_bat_dau", "kho_xong"]

# Tên đặt theo KHOẢNG (việc đã làm trong khoảng đó), không theo mốc đích — nhìn bảng
# là biết ngay khúc nào ăn thời gian, khỏi phải dịch trong đầu.
TEN_KHOANG = {
    ("mo_viec", "duyet_loi"):        "anh đọc + duyệt lời",
    ("duyet_loi", "chuoi_xong"):     "máy tự chạy: gợi thẻ · tìm ảnh · xếp kho · gán nháp",
    ("chuoi_xong", "duyet_anh"):     "ANH DUYỆT ẢNH trên trạm",
    ("chuoi_xong", "dung_bat_dau"):  "ANH DUYỆT ẢNH trên trạm",
    ("duyet_anh", "dung_bat_dau"):   "",          # hai mốc cùng lúc — không in
    ("dung_bat_dau", "dung_xong"):   "xưởng dựng video",
    ("dung_xong", "kho_bat_dau"):    "anh xem lại video",
    ("kho_bat_dau", "kho_xong"):     "đóng gói + đẩy lên Drive",
}


def _p(viec):
    return os.path.join(viec, "kich-ban.json")


def doc(viec):
    """Sổ mốc của việc này: {tên mốc: chuỗi ISO}. Chưa có gì thì trả {}."""
    try:
        return (json.load(open(_p(viec), encoding="utf-8")).get("dong_ho") or {})
    except Exception:
        return {}


def cham(viec, buoc, ghi_de=False):
    """Đóng mốc `buoc` cho việc này.

    Mặc định KHÔNG ghi đè: mốc đầu tiên là mốc thật. Anh bấm Dựng ba lần thì
    `dung_bat_dau` vẫn là lần đầu — vì thời gian anh đã bỏ ra là từ lần đầu.
    Riêng các mốc KẾT THÚC (…_xong) thì ghi đè, vì lần chạy cuối mới là lần ăn.
    """
    so = doc(viec)
    if buoc in so and not (ghi_de or buoc.endswith("_xong")):
        return so
    so[buoc] = datetime.now().isoformat(timespec="seconds")
    try:
        KB.ghi_gop(viec, {"dong_ho": so})
    except Exception:
        pass
    return so


def _giay(a, b):
    try:
        return max(0.0, (datetime.fromisoformat(b) - datetime.fromisoformat(a))
                   .total_seconds())
    except Exception:
        return 0.0


def dep(giay):
    """123 giây → '2 phút 3 giây'. Đọc bằng mắt người, không phải bằng máy."""
    giay = int(round(giay))
    gio, du = divmod(giay, 3600)
    phut, gy = divmod(du, 60)
    if gio:
        return f"{gio} giờ {phut} phút"
    if phut:
        return f"{phut} phút {gy} giây"
    return f"{gy} giây"


def tong_ket(viec):
    """Tổng thời gian + từng chặng. Chặng nào thiếu mốc thì KHÔNG in (đừng đoán)."""
    so = doc(viec)
    co = [(k, t) for k in CHANG if (t := so.get(k))]
    if len(co) < 2:
        return {"tong_giay": 0, "cac_buoc": [], "text": "", "bat_dau": "", "ket_thuc": ""}
    tong = _giay(co[0][1], co[-1][1])
    buoc = []
    for i in range(len(co) - 1):
        (k0, t0), (k1, t1) = co[i], co[i + 1]
        gy = _giay(t0, t1)
        ten = TEN_KHOANG.get((k0, k1), f"{k0} → {k1}")
        if not ten or gy < 0.5:        # hai mốc trùng lúc — đừng bày dòng 0 giây
            continue
        buoc.append({"tu": k0, "den": k1, "ten": ten,
                     "giay": round(gy, 1), "dep": dep(gy),
                     "phan_tram": round(gy / tong * 100) if tong else 0})
    dong = [f"TỔNG: {dep(tong)}   ({co[0][1][:16].replace('T', ' ')}"
            f" → {co[-1][1][:16].replace('T', ' ')})", ""]
    rong = max(len(b["ten"]) for b in buoc)
    for b in buoc:
        thanh = "█" * max(1, round(b["phan_tram"] / 5))
        dong.append(f"  {b['ten']:<{rong}}  {b['dep']:>14}  {b['phan_tram']:>3}% {thanh}")
    return {"tong_giay": round(tong, 1), "cac_buoc": buoc, "text": "\n".join(dong),
            "bat_dau": co[0][1], "ket_thuc": co[-1][1]}


if __name__ == "__main__":                       # xem tay: python3 dong_ho.py <mã việc>
    import duong_dan as DD
    for a in sys.argv[1:]:
        v = DD.tim_viec(a)
        tk = tong_ket(v)
        print(f"\n═══ {os.path.basename(v)} ═══")
        print(tk["text"] or "  (chưa đủ mốc để tính)")
