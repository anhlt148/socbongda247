#!/usr/bin/env python3
"""PHONG CÁCH VIDEO — bộ núm vặn chống dập khuôn, dùng chung trạm + xưởng.

VÌ SAO CÓ FILE NÀY (anh đặt 12/08/2026):
  Kênh đăng nhiều Shorts mỗi ngày bằng cùng một dây chuyền. Nếu mọi video đều CÙNG
  mức zoom, CÙNG tốc độ trượt, CÙNG âm lượng nhạc, CÙNG tốc độ giọng thì bộ khung
  thành **dấu vân tay** — nhìn qua là biết máy làm hàng loạt. Anh chốt tinh thần này
  từ 05/08 khi bắt lỗi "video nào cũng zoom-vào-từ-tâm rồi trượt-trái-sang-phải".

CÁCH LÀM: anh đặt MỘT chỉ số cho mỗi núm (anh chốt 12/08 — bỏ khái niệm dải).
Xưởng đọc thẳng con số đó. Riêng danh sách GIỌNG có nhiều mục thì mỗi video rút một
giọng, gieo theo mã việc — dựng lại vẫn ra đúng giọng đó.

NÃO MỘT NGUỒN: cấu hình nằm ở `kho-tai-nguyen/phong-cach.json`. Trạm ghi, xưởng đọc.
Không đẻ bản sao.
"""
import json
import os
import random

import duong_dan as DD
import chon_nhac as CN

TEP = os.path.join(DD.KHO_TAI_NGUYEN, "phong-cach.json")

# Tên tiếng Việt của 12 nhóm cảm xúc — dùng cho trang cấu hình và cho log.
TEN_VIET = {
    "01_BREAKING_NEWS":    "Tin nóng · vừa có chuyện",
    "02_HYPE_MATCHDAY":    "Đại chiến · ngày thi đấu",
    "03_EPIC_VICTORY":     "Chiến thắng · vỡ oà",
    "04_TENSION_SUSPENSE": "Căng thẳng · nghẹt thở",
    "05_DRAMA_CONFLICT":   "Tranh cãi · đối đầu",
    "06_COMEBACK_HOPE":    "Trở lại · hy vọng",
    "07_SAD_TRIBUTE":      "Chia tay · tri ân",
    "08_ANALYSIS_NEUTRAL": "Phân tích · điềm tĩnh",
    "09_MYSTERY_RUMOR":    "Tin đồn · bí ẩn",
    "10_FUN_LIGHT":        "Vui · nhẹ nhàng",
    "11_PATRIOTIC_EPIC":   "Tự hào · hào hùng",
    "12_TRANSFER_NEWS":    "Chuyển nhượng · bom tấn",
}

# Biên CỨNG — anh gõ thế nào cũng không vượt được, để một cú gõ nhầm không phá video.
# (mặc_định, biên_dưới, biên_trên, số_lẻ)  — anh chốt 12/08: MỘT chỉ số, không dùng dải.
# ⚠ ĐO THẬT 12/08 trên giọng thật của kênh: fade vào 0,3s làm 0,3 giây ĐẦU tụt 14,2 dB —
# mất gần trọn tiếng đầu tiên, trong khi câu đầu của kênh chính là đọc lại tiêu đề.
# Fade vào chỉ để CHỐNG TIẾNG "BỤP" lúc mở file, việc đó cần 10–50ms là đủ (0,05s chỉ
# tụt 2,9 dB, tai không nghe ra). Đừng để quá 0,15s.
NUM = {
    "nhac_am_luong":  (0.11, 0.04, 0.25, 3),
    "nhac_vao":       (0.4,  0.0,  6.0,  2),
    "nhac_ra":        (2.5,  0.0,  6.0,  2),
    "giong_vao":      (0.05, 0.0,  4.0,  2),
    "giong_ra":       (0.4,  0.0,  4.0,  2),
    "zoom_max":       (1.12, 1.02, 1.20, 3),
    "pan_toc_do":     (0.10, 0.04, 0.18, 3),
    "lech_tam":       (0.16, 0.0,  0.30, 2),
    "tran_mot_kieu":  (0.65, 0.40, 0.90, 2),
    "giong_toc_do":   (1.10, 0.90, 1.30, 2),
}

# DANH SÁCH GIỌNG (anh đặt 12/08): mỗi giọng là một mã VBee + dải tốc độ RIÊNG.
# Mỗi video rút một giọng đang bật — kênh có nhiều chất giọng thì đỡ nhàm hơn hẳn
# một giọng đọc suốt hàng trăm video. Mặc định đúng giọng đang chạy, không đổi gì.
GIONG_MAC_DINH = [
    {"ma": DD.GIONG_MA, "ten": "Ngọc Huyền (Hà Nội, nữ)", "toc_do": 1.10, "bat": True},
]

MAC_DINH = {
    "nhac_nhom": "tu_dong",         # tu_dong | ngau_nhien | <mã nhóm>
    "giong_ds": [dict(g) for g in GIONG_MAC_DINH],
    **{k: v[0] for k, v in NUM.items()},
}


def _kep(x, lo, hi, le):
    try:
        return round(max(lo, min(hi, float(x))), le)
    except (TypeError, ValueError):
        return None


def doc():
    """Đọc cấu hình. Thiếu/hỏng file → trả mặc định. KHÔNG BAO GIỜ nổ."""
    d = dict(MAC_DINH)
    try:
        if os.path.exists(TEP):
            d.update(json.load(open(TEP, encoding="utf-8")) or {})
    except Exception:
        pass
    return chuan(d)


def chuan(d):
    """Kẹp mọi giá trị vào biên cứng + sửa dải ngược đầu. Trả bản đã sạch."""
    ra = {}
    nhom = str(d.get("nhac_nhom") or "tu_dong")
    ra["nhac_nhom"] = nhom if (nhom in ("tu_dong", "ngau_nhien") or nhom in CN.CUNG_12) \
        else "tu_dong"
    for k, (md, lo, hi, le) in NUM.items():
        v = _kep(d.get(k, md), lo, hi, le)
        ra[k] = md if v is None else v

    # ── DANH SÁCH GIỌNG ─────────────────────────────────────────────────────
    _, tlo, thi, tle = NUM["giong_toc_do"]
    ds = []
    for g in (d.get("giong_ds") or []):
        ma = str((g or {}).get("ma") or "").strip()
        if not ma:
            continue                        # dòng trống → bỏ, không để rác vào sổ
        td = g.get("toc_do", NUM["giong_toc_do"][0])
        if isinstance(td, (list, tuple)):    # sổ bản cũ lưu dải → lấy giữa dải
            td = (float(td[0]) + float(td[-1])) / 2
        v = _kep(td, tlo, thi, tle)
        ds.append({"ma": ma, "ten": (str(g.get("ten") or "").strip() or ma),
                   "toc_do": NUM["giong_toc_do"][0] if v is None else v,
                   "bat": bool(g.get("bat", True))})
    # KHÔNG BAO GIỜ để danh sách rỗng — xoá hết thì trả về giọng đang chạy, không thì
    # xưởng mất giọng và cả mẻ video hỏng câm.
    ra["giong_ds"] = ds or [dict(g) for g in GIONG_MAC_DINH]
    return ra


def ghi(d):
    os.makedirs(os.path.dirname(TEP), exist_ok=True)
    sach = chuan(d)
    tam = TEP + ".tmp"
    json.dump(sach, open(tam, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tam, TEP)                    # ghi nguyên tử — mất điện không để lại file cụt
    return sach


def cho_video(viec, kb=None):
    """Lấy bộ thông số cho một video. Anh chốt 12/08: MỘT chỉ số, dùng thẳng.

    Chỉ còn một chỗ vẫn xoay theo video: khi anh bật NHIỀU giọng đọc thì mỗi video rút
    một giọng (gieo theo mã việc → dựng lại vẫn ra đúng giọng đó).
    """
    c = doc()
    rnd = random.Random(f"phongcach|{viec}")
    ra = {k: c[k] for k in NUM if k != "giong_toc_do"}

    # nhóm nhạc
    nhom_dat = c["nhac_nhom"]
    if nhom_dat == "ngau_nhien":
        co = [n for n in CN.CUNG_12 if CN._bai_trong(n)]
        ra["nhac_nhom"] = rnd.choice(co) if co else CN.MAC_DINH
        ra["nhac_vi_sao"] = "anh đặt NGẪU NHIÊN trong kho"
    elif nhom_dat in CN.CUNG_12:
        ra["nhac_nhom"] = nhom_dat
        ra["nhac_vi_sao"] = "anh ghim cứng nhóm này"
    else:
        ra["nhac_nhom"] = None              # None = để chon_nhac tự dò theo nội dung
        ra["nhac_vi_sao"] = "máy dò theo nội dung"

    # giọng: nhiều giọng thì mỗi video một giọng, một giọng thì luôn là giọng đó
    bat_ds = [g for g in c["giong_ds"] if g.get("bat")] or c["giong_ds"]
    g = rnd.choice(bat_ds)
    ra["giong_ma"] = g["ma"]
    ra["giong_ten"] = g["ten"]
    ra["giong_toc_do"] = g["toc_do"]
    ra["_so_giong"] = len(bat_ds)
    return ra


def ap_vao_chuyen_dong(cd, ts):
    """Áp thông số của video này lên module chuyển động.

    Đặt thuộc tính module vì `chuyen_dong` đọc hằng số LÚC GỌI (dòng 508–532), không
    phải lúc import. Gọi NGAY TRƯỚC khi dựng từng video. `tran_mot_kieu` là tham số
    mặc định của hàm (chốt lúc def) nên KHÔNG đặt được kiểu này — phải truyền tay.
    """
    cd.ZOOM_MAX = ts["zoom_max"]
    cd.PAN_TOC_DO = ts["pan_toc_do"]
    cd.LECH_TAM = ts["lech_tam"]


if __name__ == "__main__":
    c = doc()
    print(f"Cấu hình: {TEP}")
    print(f"  nhạc: {c['nhac_nhom']}")
    for k in NUM:
        print(f"  {k:<16}{c[k]}")
    print(f"  giọng: {len(c['giong_ds'])} giọng")
    for g in c["giong_ds"]:
        print(f"     {'☑' if g['bat'] else '☐'} {g['ten']}  ×{g['toc_do']}  ({g['ma']})")
