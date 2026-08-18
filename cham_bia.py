#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHẤM ẢNH BÌA — máy tự soi bìa mình vừa dựng rồi cho điểm, như một người QC.

Anh chốt 18/08: "phải tự chấm được, đề cho anh bản tốt nhất".

VÌ SAO MÁY CHẤM ĐƯỢC MÀ KHÔNG CẦN AI HIỂU THẨM MỸ: phần lớn cái làm một tấm bìa hỏng
đều ĐO ĐƯỢC — mặt bị che, mặt quá nhỏ, chữ chìm vào nền, tấm bìa nhoè khi thu về cỡ
ngón tay. Chỗ máy thua người là "bìa này có hấp dẫn không"; chỗ máy thắng người là
KIÊN NHẪN: nó soi đủ bảy thước cho từng phương án, không mỏi mắt, không thiên vị
phương án nó vừa dựng.

BẢY THƯỚC (tổng 100):
  ① mặt rõ            22 — mặt chủ thể có bị che, bị dải chữ cắt, bị mép khung xén không
  ② cỡ mặt            16 — nhỏ quá không nhận ra ai; to quá thì ngợp, mất bối cảnh
  ③ rõ ở cỡ ngón tay  20 — THU VỀ 168×298 rồi đo. Thước quan trọng nhất mà người hay quên
  ④ chữ nổi           14 — chữ có chìm vào nền không
  ⑤ mặt đặt đúng chỗ  10 — quy tắc một phần ba
  ⑥ cân bằng           8 — khối lượng thị giác có dồn hết về một bên không
  ⑦ lớp phủ sạch      10 — ô tròn/nhãn có đè lên thứ quan trọng không

Chạy tay:  python3 cham_bia.py <ảnh bìa> [<ảnh bìa> ...]
"""
import os, sys

TRONG = {"mat_ro": 22, "co_mat": 16, "ro_nho": 20, "chu_noi": 14,
         "cho_dat": 10, "can_bang": 8, "phu_sach": 10}


def _mn(x, a, b):
    """Điểm 0..1 theo kiểu "trong khoảng thì trọn điểm, ra ngoài thì tụt dần"."""
    if a <= x <= b:
        return 1.0
    d = (a - x) if x < a else (x - b)
    rong = max(1e-6, (b - a))
    return max(0.0, 1.0 - d / rong)


def cham(p_bia, ctx=None):
    """Chấm một tấm bìa. Trả dict có `diem` (0..100) và `muc` — từng thước kèm lời."""
    import numpy as np
    from PIL import Image
    ctx = ctx or {}
    im = Image.open(p_bia).convert("RGB") if isinstance(p_bia, str) else p_bia.convert("RGB")
    W, H = im.size
    y_dai = ctx.get("y_dai") or int(H * 0.70)

    try:
        import mat_may
        d = mat_may.nhin_pil(im) or {}
    except Exception:
        d = {}
    mat = d.get("mat") or []
    # chỉ tính khuôn mặt nằm ở PHẦN ẢNH; mặt lọt xuống dải chữ là đã bị che rồi
    to = max(mat, key=lambda m: m["w"] * m["h"], default=None)

    muc = []

    # ① MẶT RÕ ────────────────────────────────────────────────────────────────
    if not to:
        muc.append(("mat_ro", 0.15, "không thấy khuôn mặt nào — bìa mất chỗ bám mắt"))
    else:
        d_ = 1.0
        loi = []
        if to["y"] + to["h"] > y_dai:
            d_ -= 0.55
            loi.append("mặt bị dải chữ cắt")
        if to["x"] < 6 or to["x"] + to["w"] > W - 6:
            d_ -= 0.30
            loi.append("mặt chạm mép ngang")
        if to["y"] < 4:
            d_ -= 0.25
            loi.append("đỉnh đầu bị xén")
        if to["tin"] < 0.75:
            d_ -= 0.15
            loi.append(f"mặt mờ (tin cậy {to['tin']:.2f})")
        muc.append(("mat_ro", max(0.0, d_), "; ".join(loi) or "mặt rõ, không bị che"))

    # ② CỠ MẶT ────────────────────────────────────────────────────────────────
    if to:
        # Đo theo BỀ NGANG, không theo diện tích. Mắt người cảm nhận cỡ khuôn mặt theo
        # chiều ngang; đo bằng diện tích thì một khuôn mặt to đẹp chỉ ra 4,5% và bộ
        # chấm kêu "nhỏ quá" trong khi nhìn vào thì rất rõ. (Hiệu chỉnh 18/08 trên ba
        # bìa thật của kênh: 21% · 24% nhìn đẹp, 11% thì đúng là xa và khó nhận ra.)
        ty = to["w"] / W * 100
        muc.append(("co_mat", _mn(ty, 15, 34),
                    f"mặt rộng {ty:.0f}% bề ngang bìa" +
                    (" — nhỏ, khó nhận ra ai" if ty < 15 else
                     " — to quá, mất bối cảnh" if ty > 34 else "")))
    else:
        muc.append(("co_mat", 0.2, "không đo được vì không thấy mặt"))

    # ③ RÕ Ở CỠ NGÓN TAY ──────────────────────────────────────────────────────
    # Trên điện thoại, tấm bìa hiện ra cỡ ~168 px ngang. Bìa nào cũng đẹp khi xem to;
    # thứ phân biệt bìa tốt với bìa xoàng là còn đọc được gì khi thu nhỏ.
    nho = np.asarray(im.resize((168, int(168 * H / W))).convert("L"), np.float32)
    tuong_phan = float(nho.std()) / 62.0
    sac = float((np.abs(np.diff(nho, axis=0)).mean() +
                 np.abs(np.diff(nho, axis=1)).mean())) / 15.0
    d3 = min(1.0, 0.6 * min(tuong_phan, 1.3) + 0.4 * min(sac, 1.3))
    muc.append(("ro_nho", d3,
                f"thu về cỡ ngón tay: tương phản {tuong_phan:.2f} · nét {sac:.2f}" +
                (" — bệt, nhìn xa thành một mảng" if d3 < 0.55 else "")))

    # ④ CHỮ NỔI ───────────────────────────────────────────────────────────────
    dai = np.asarray(im.crop((0, y_dai, W, H)).convert("L"), np.float32)
    if dai.size:
        sang = float((dai > 200).mean())       # tỷ lệ pixel chữ trắng/vàng
        chenh = float(dai.std()) / 70.0
        d4 = min(1.0, 0.55 * min(chenh, 1.2) + 0.45 * _mn(sang * 100, 8, 30))
        muc.append(("chu_noi", d4,
                    f"chữ chiếm {sang*100:.0f}% dải, chênh sáng {chenh:.2f}" +
                    (" — chữ chìm vào nền" if d4 < 0.55 else "")))
    else:
        muc.append(("chu_noi", 0.5, "không có dải chữ"))

    # ⑤ MẶT ĐẶT ĐÚNG CHỖ ──────────────────────────────────────────────────────
    if to:
        cx = (to["x"] + to["w"] / 2) / W
        cy = (to["y"] + to["h"] / 2) / y_dai
        # Khoảng ĐẸP đo từ bìa thật của kênh, không bê nguyên quy tắc một phần ba của
        # ảnh ngang sang: bìa 9:16 lấy ảnh chân dung toàn thân thì khuôn mặt nằm khá
        # cao là chuyện thường và nhìn vẫn đẹp (hai bìa đẹp nhất của kênh đo được
        # dọc 0,18 và 0,37 — thước cũ chấm cả hai đều trượt).
        d5 = 0.55 * _mn(cx, 0.30, 0.70) + 0.45 * _mn(cy, 0.15, 0.42)
        muc.append(("cho_dat", d5,
                    f"tâm mặt ở ngang {cx:.2f} · dọc {cy:.2f} của phần ảnh"))
    else:
        muc.append(("cho_dat", 0.3, "không đo được"))

    # ⑥ CÂN BẰNG ──────────────────────────────────────────────────────────────
    g = np.asarray(im.crop((0, 0, W, y_dai)).resize((32, 48)).convert("L"), np.float32)
    ct = np.abs(np.diff(g, axis=1, prepend=g[:, :1]))
    tong = ct.sum() + 1e-6
    trai = ct[:, :16].sum() / tong
    lech = abs(trai - 0.5) * 2                 # 0 = cân, 1 = dồn hết một bên
    muc.append(("can_bang", max(0.0, 1.0 - lech * 1.25),
                f"khối lượng thị giác lệch {lech*100:.0f}% về " +
                ("trái" if trai > 0.5 else "phải")))

    # ⑦ LỚP PHỦ SẠCH ──────────────────────────────────────────────────────────
    v = ctx.get("vuong_lop_phu")
    if v is None:
        muc.append(("phu_sach", 0.85, "bìa không có lớp phủ rời"))
    else:
        # Dưới 0,45 là chỗ đặt sạch — không có gì để trừ. Trừ tuyến tính từ 0 thì một
        # ô tròn đặt đàng hoàng (0,32) vẫn mất nửa số điểm, và bìa có ô tròn luôn
        # thua bìa trơn dù ô tròn đặt đúng chỗ.
        muc.append(("phu_sach", 1.0 if v <= 0.45 else max(0.0, 1.0 - (v - 0.45) / 0.17),
                    f"lớp phủ vướng {v:.2f}" +
                    (" — đè lên chỗ quan trọng" if v > 0.45 else " — đặt sạch")))

    # ÉP VỀ float THƯỜNG: numpy trả float32, mà float32 thì json.dump không ghi được —
    # bìa dựng xong rồi vẫn lăn ra lỗi ở bước ghi báo cáo.
    muc = [(k, float(v), n) for k, v, n in muc]
    tong_d = float(sum(TRONG[k] * v for k, v, _ in muc))
    return {"diem": round(tong_d, 1),
            "muc": [{"ten": k, "diem": round(v, 3), "trong": TRONG[k],
                     "duoc": round(TRONG[k] * v, 1), "noi": n} for k, v, n in muc]}


TEN_VIET = {"mat_ro": "mặt rõ", "co_mat": "cỡ mặt", "ro_nho": "rõ cỡ ngón tay",
            "chu_noi": "chữ nổi", "cho_dat": "mặt đúng chỗ",
            "can_bang": "cân bằng", "phu_sach": "lớp phủ sạch"}


def in_bang(kq, ten=""):
    print(f"\n  ▸ {ten}   TỔNG {kq['diem']:.1f}/100")
    for m in kq["muc"]:
        thanh = "█" * round(m["diem"] * 10) + "·" * (10 - round(m["diem"] * 10))
        print(f"      {TEN_VIET[m['ten']]:16s} {thanh} {m['duoc']:4.1f}/{m['trong']:<3d} {m['noi']}")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        in_bang(cham(p), os.path.basename(os.path.dirname(p)) or p)
