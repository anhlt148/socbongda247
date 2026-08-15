#!/usr/bin/env python3
"""Chuẩn hoá tag SEO YouTube — MỘT nguồn chân lý cho mọi chỗ sinh tag.

Bài học 09/08 (anh soi volume trên YouTube Studio khi đăng bài PVF): model trả thẻ
dạng "Sân PVF / san pvf" — bản có dấu và không dấu DÍNH trong một thẻ, thành chuỗi
không ai gõ tìm bao giờ → volume 0 cả loạt. Trong khi các thẻ sạch máy tự đệm
("asean cup 2026", "tuyển việt nam") đều có volume thật.

Nguyên tắc "code trước, model sau": bỏ dấu là việc cơ khí — code làm, model KHÔNG
được giao nữa. Model chỉ chọn cụm CÓ DẤU mà người xem thật sự gõ tìm; mọi biến thể
không dấu, tách dính, khử trùng, cắt trần 500 ký tự do đây lo.
"""
import re
import unicodedata


def bo_dau(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")


def chuan_hoa(tho, dem=(), tran=490):
    """Nhận list thẻ thô từ model (+ thẻ đệm mặc định của kênh), trả list thẻ sạch:

    - thẻ dính đôi "X / y" (hoặc "X | y", "X; y") → tách thành từng thẻ riêng
    - mỗi thẻ có dấu tự sinh thêm bản không dấu (nếu khác bản gốc)
    - khử trùng không phân biệt hoa thường, giữ thứ tự xuất hiện
    - tổng độ dài (nối ", ") không vượt trần — ô Thẻ YouTube chặn ở 500 ký tự
    """
    sach, thay = [], set()

    def them(t):
        t = re.sub(r"\s+", " ", t).strip(" .,;:-").strip()
        if not t or len(t) > 60:
            return
        k = t.lower()
        if k in thay:
            return
        thay.add(k)
        sach.append(t)

    for t in list(tho or []) + list(dem):
        if not isinstance(t, str):
            continue
        for manh in re.split(r"\s*[/|;]\s*", t):
            them(manh)
            khong_dau = bo_dau(manh)
            if khong_dau.lower() != manh.lower():
                them(khong_dau)

    ra, dai = [], 0
    for t in sach:
        dai += len(t) + 2
        if dai > tran:
            break
        ra.append(t)
    return ra


if __name__ == "__main__":
    thu = chuan_hoa(["Sân PVF / san pvf", "Tuyển Việt Nam / tuyen viet nam",
                     "Công nghệ mái", "sân Mỹ Đình"],
                    dem=("sóc bóng đá 247", "asean cup 2026"))
    for t in thu:
        print("·", t)
