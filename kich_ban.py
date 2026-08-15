#!/usr/bin/env python3
"""SỔ KỊCH BẢN — một cửa GHI duy nhất cho `kich-ban.json`.

VÌ SAO CÓ FILE NÀY (anh đặt 12/08: "cho SEO chạy cùng lúc với dựng video"):
  Từ lúc SEO chạy SONG SONG với xưởng, hai tiến trình cùng sửa một tệp:
    · xưởng  → ghi `cum_to_vang` (cửa cuối chọn cụm tô vàng cho tít)
    · SEO    → ghi `tu_khoa`, `binh_luan_ghim`, `hashtag_seo`
  Kiểu ghi cũ (đọc cả tệp vào bộ nhớ lúc đầu → ghi đè lúc cuối) làm bên ghi SAU XOÁ
  SẠCH việc của bên ghi TRƯỚC — mà im lặng, không lỗi, chỉ mất dữ liệu. Đúng họ bệnh
  "một việc hai đường chạy" đã trả giá 11/08.

CÁCH LÀM: mọi đường ghi phải qua `ghi_gop()` — khoá tệp, ĐỌC LẠI bản mới nhất trên
đĩa, gộp phần mình sửa, rồi mới ghi. Không ai đè ai, dù chạy cùng lúc.
"""
import fcntl
import json
import os


def duong(viec):
    return os.path.join(viec, "kich-ban.json")


def doc(viec):
    try:
        return json.load(open(duong(viec), encoding="utf-8"))
    except Exception:
        return {}


def ghi_gop(viec, moi):
    """Gộp `moi` vào kịch bản trên đĩa DƯỚI KHOÁ. Trả bản sau khi gộp.

    Đọc-lại-rồi-mới-ghi là mấu chốt: bản trong bộ nhớ của tiến trình này có thể đã cũ
    (tiến trình kia vừa ghi thêm trường khác). Chỉ đè đúng những khoá mình mang tới.
    """
    p = duong(viec)
    p_khoa = p + ".khoa"
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p_khoa, "w") as f_khoa:
        fcntl.flock(f_khoa, fcntl.LOCK_EX)
        try:
            try:
                kb = json.load(open(p, encoding="utf-8"))
            except Exception:
                kb = {}
            kb.update(moi or {})
            tam = p + ".tam"
            json.dump(kb, open(tam, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            os.replace(tam, p)          # thay NGUYÊN KHỐI — không ai đọc phải bản dở
            return kb
        finally:
            fcntl.flock(f_khoa, fcntl.LOCK_UN)
