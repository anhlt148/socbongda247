#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NHỊP CẢNH — MỘT nguồn chân lý cho phép co giãn, cả XƯỞNG lẫn TRẠM cùng đọc.

Anh bắt 09/08: trạm chia nhịp một kiểu (chia đều thô theo tiếng), xưởng co giãn kiểu
khác — cảnh 0,9 giây hiển thị trơ trọi, ô phụ bị ẩn im lặng, anh nhìn trạm không đoán
được video sẽ ra sao. Đúng bệnh "một logic hai bản" đã ghi sổ ba lần.

Luật anh chốt (09/08): "cảnh 2 tổng 10,3 giây thì phải CẮT thời gian cho cảnh 1 để nó
có tối thiểu 2,5 giây, số còn lại mới chia đều cho ba khung hình ở cảnh 2".
  ① SỐ PHẦN tính theo độ dài GỐC của câu: ceil(dài / 5) — câu 10,3s = 3 khung, khớp số
    ô (chính + phụ) anh thấy và gán trên trạm.
  ② MƯỢN TRƯỚC: câu ngắn dưới 2,5s kéo giây từ hàng xóm (ưu tiên câu kề dài hơn), hàng
    xóm không được tụt dưới 2,5s × số phần của nó.
  ③ CHIA SAU: phần còn lại của mỗi câu chia đều cho các khung; nếu chia xong một khung
    tụt dưới 2,5s thì bớt khung (ô gán dư trạm phải HIỆN MỜ chứ không ẩn).
  Cảnh CLIP anh đã cắt tay: máy không đụng độ dài, không cho mượn, không tách.
"""
import math

CANH_MAX, CANH_MIN = 5.0, 2.5
NOI_LONG = 0.15          # câu 2,4s không đáng đi mượn — chỉ mượn khi hụt rõ


def so_o_toi_da(dai):
    """Một câu dài `dai` giây thì nhiều nhất chia được bao nhiêu khung (mỗi khung ≥ 2,5s).

    Đây là TRẦN SLOT (anh chốt 13/08): "cảnh chỉ có 3 slot mà chọn 5 ảnh thì chỉ lấy 3,
    hai ảnh còn lại về kho ứng viên, KHÔNG được sinh ra cảnh dư".
    """
    return max(1, int((float(dai) + 0.01) // CANH_MIN))


def chia_nhip(giay_cau, la_clip=None, so_phu=None):
    """giay_cau = [độ dài từng câu]; la_clip = [câu nào là cảnh clip do anh cắt tay];
    so_phu = [số ảnh/clip PHỤ anh đã gán cho từng câu] — ý người, máy phải tôn trọng.

    Trả về danh sách theo câu: {"dai": độ dài SAU co giãn, "so_phan": số khung,
    "muon": +giây đã mượn được / -giây đã cho mượn (0 nếu không đổi)}.
    Tổng "dai" luôn bằng tổng đầu vào — co giãn chỉ chuyển giây, không đẻ không nuốt.
    """
    d = [float(x) for x in giay_cau]
    n = len(d)
    la_clip = list(la_clip or [False] * n)
    so_phu = list(so_phu or [0] * n)
    so_phu += [0] * (n - len(so_phu))
    goc = list(d)

    # ① số phần theo độ dài GỐC — khớp số ô anh nhìn thấy trên trạm
    so_phan = [1 if la_clip[i] else max(1, math.ceil(d[i] / CANH_MAX - 1e-9))
               for i in range(n)]
    # ①b ẢNH PHỤ ANH ĐÃ GÁN LÀ Ý NGƯỜI (anh bắt 13/08: "cảnh 9 có 1 chính + 2 phụ mà
    #    2 cảnh phụ không lên hình sau khi render"). Trước đây cảnh có CLIP bị ép cứng
    #    1 khung, nên mọi ảnh phụ của cảnh đó bị bỏ thẳng — kể cả khi câu dài 9,2 giây
    #    thừa chỗ cho ba khung. Nay: gán bao nhiêu phụ thì mở bấy nhiêu khung, CHẶN
    #    TRÊN bằng trần slot để không khung nào ngắn dưới 2,5 giây.
    for i in range(n):
        if so_phu[i] > 0:
            so_phan[i] = max(so_phan[i], min(1 + so_phu[i], so_o_toi_da(d[i])))

    # ② câu hụt đi mượn HÀNG XÓM SÁT CẠNH (i±1, bên dài hơn trước) — không mượn của
    #   cảnh clip (mốc anh cắt tay, giây không được chảy xuyên qua nó)
    for i in range(n):
        if la_clip[i] or d[i] >= CANH_MIN - NOI_LONG:
            continue
        thieu = CANH_MIN - d[i]
        ke = [hx for hx in (i - 1, i + 1) if 0 <= hx < n and not la_clip[hx]]
        for hx in sorted(ke, key=lambda x: -d[x]):
            du = d[hx] - CANH_MIN * so_phan[hx]
            lay = min(thieu, max(du, 0.0))
            if lay > 0.01:
                d[hx] -= lay
                d[i] += lay
                thieu -= lay
            if thieu <= 0.01:
                break

    # ③ chia xong mà khung hụt thì bớt khung (không bao giờ bớt dưới 1)
    for i in range(n):
        # cảnh CLIP không có ảnh phụ → giữ nguyên 1 khung (anh tự quyết độ dài đoạn);
        # có ảnh phụ thì phải qua vòng cân này như mọi cảnh khác
        if la_clip[i] and not so_phu[i]:
            continue
        while so_phan[i] > 1 and d[i] / so_phan[i] < CANH_MIN - 0.01:
            so_phan[i] -= 1
        # chỉ TỰ THÊM khung cho cảnh KHÔNG phải clip — cảnh clip chỉ nở đúng số ô
        # anh đã gán, máy không tự đẻ thêm ô trống
        while not la_clip[i] and d[i] / so_phan[i] > CANH_MAX + 0.01:
            so_phan[i] += 1

    return [{"dai": round(d[i], 2), "so_phan": so_phan[i],
             "muon": round(d[i] - goc[i], 2)} for i in range(n)]


def _hang_xom(i, n):
    """Thứ tự đi mượn: sát cạnh trước (i+1, i-1), rồi loang dần ra xa."""
    for b in range(1, n):
        for hx in (i + b, i - b):
            if 0 <= hx < n:
                yield hx
