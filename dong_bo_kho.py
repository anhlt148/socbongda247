#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GƯƠNG KHO TÀI NGUYÊN — ổ máy ↔ Drive, để hai máy dùng chung một kho.

Anh chốt 16/08: *"có chung kho, ở máy tính là lưu riêng và tự đẩy lên driver những cảnh
đã lấy về, nếu xoá ở máy/trạm thì cũng xoá trên drive luôn."*

Nghĩa là **ổ máy là chính chủ**, Drive là bản sao để máy kia đọc. Nhưng máy kia cũng bồi
ảnh vào kho khi nó xếp bài — nên gương một chiều thuần sẽ XOÁ MẤT phần đóng góp của họ.
Vì thế đây là gương **ba chiều**, dựa vào một cuốn sổ ghi "lần trước đồng bộ có những gì":

    ở MÁY, không ở DRIVE      → mới ở máy            → ĐẨY LÊN
    ở cả hai, khác cỡ         → máy là chính chủ     → ĐẨY LÊN (đè)
    không ở MÁY, CÓ trong sổ  → anh đã xoá           → XOÁ TRÊN DRIVE
    không ở MÁY, KHÔNG có sổ  → máy kia vừa thêm     → KÉO VỀ MÁY
    không ở DRIVE, CÓ trong sổ→ máy kia đã xoá       → XOÁ Ở MÁY

Không có cuốn sổ ấy thì không tài nào phân biệt "anh vừa xoá" với "họ vừa thêm" — hai
việc trông y hệt nhau nếu chỉ nhìn hai thư mục.

    python3 dong_bo_kho.py            # đồng bộ thật
    python3 dong_bo_kho.py --thu      # chỉ xem sẽ làm gì, không đụng tệp nào
"""
import argparse
import json
import os
import shutil
import sys
import unicodedata as ud
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD                                                    # noqa: E402
import nen_tang as NT                                                     # noqa: E402

SO = os.path.expanduser("~/.config/socbongda247/da-dong-bo-kho.json")

# PHANH AN TOÀN: xoá quá tỉ lệ này trong một lượt thì DỪNG, đòi người xác nhận.
# Vì sao cần: ổ DATA chưa gắn, hoặc Drive chưa tải xong, thì một bên trông như RỖNG —
# gương mù quáng sẽ quét sạch bên kia. Mất 1741 tấm ảnh đã trả giá cả tháng.
NGUONG_XOA = 0.15
TOI_THIEU_DE_XOA = 50        # kho ít hơn ngần này tệp thì đừng tin, đừng xoá gì


def _nfc(x):
    """macOS lưu tên có dấu ở dạng NFD; so chuỗi phải chuẩn hoá cả hai vế, không thì
    'Xuân Sơn' ở máy và 'Xuân Sơn' trên Drive thành hai tệp khác nhau."""
    return ud.normalize("NFC", x)


# VIDEO GỐC NẶNG KHÔNG LÊN DRIVE. Video gốc gắp từ mạng về hay 100–600 MB một tệp
# (đo 16/08: 38 tệp = 3,4 GB) — đẩy lên là ngốn dung lượng Drive và băng thông cho thứ
# mỗi máy tự tải được. Thứ đáng dùng chung là ĐOẠN ĐÃ CẮT (vài MB) và ẢNH.
TRAN_VIDEO_MB = 60


def _bo_qua(rel, co):
    """Tệp này có nằm ngoài phạm vi gương không."""
    return rel.startswith("video-chu-the/") and co > TRAN_VIDEO_MB * 1_000_000


def _quet(goc):
    """{đường tương đối (NFC): cỡ tệp} — bỏ rác hệ điều hành và thứ ngoài phạm vi."""
    ra = {}
    if not os.path.isdir(goc):
        return ra
    for thu, _, tep in os.walk(goc):
        for t in tep:
            if t in (".DS_Store", "Icon\r") or t.startswith("._"):
                continue
            p = os.path.join(thu, t)
            try:
                co = os.path.getsize(p)
            except OSError:
                continue
            rel = _nfc(os.path.relpath(p, goc))
            if _bo_qua(rel, co):
                continue
            ra[rel] = co
    return ra


def _quet_on_dinh(goc, lan=4, cho=5):
    """Quét tới khi thư mục ĐỨNG YÊN hai lượt liền — gương chỉ soi được mặt nước phẳng.

    Vì sao (đo thật 16/08): Google Drive for Desktop trong lúc đồng bộ làm thư mục thay
    đổi liên tục — lượt quét đầu thấy 1204 tệp lạ (`nhac/phieu_luu/*.mp3`, `kho-index.json`),
    kiểm lại 30 giây sau thì chúng KHÔNG TỒN TẠI. Nếu tin lượt quét ấy, gương sẽ "kéo về"
    hàng nghìn tệp ma rồi ghi vào sổ, và lượt sau lại tưởng anh đã xoá ngần ấy.

    Trả về (bảng, ổn_định). Không ổn định thì để người gọi tự quyết dừng.
    """
    import time
    truoc = _quet(goc)
    for _ in range(lan):
        time.sleep(cho)
        sau = _quet(goc)
        if sau == truoc:
            return sau, True
        truoc = sau
    return truoc, False


def _doc_so():
    try:
        return json.load(open(SO, encoding="utf-8"))
    except Exception:
        return {}


def _ghi_so(d):
    os.makedirs(os.path.dirname(SO), exist_ok=True)
    tam = SO + ".tam"
    json.dump(d, open(tam, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tam, SO)


# Dấu hiệu BẮT BUỘC phải có trong đường dẫn thì mới nhận là kho của kênh này.
# Vì sao (suýt hỏng 16/08): dò mù `*/*/kho-tai-nguyen` trỏ trúng kho của kênh BÉ ĐOÁN GIỎI
# — chạy thật là đổ 2033 tệp kho Sóc trộn vào kho kênh kia, hai kho hỏng cả hai. Cùng họ
# với bài học "tên tệp không phải bằng chứng nội dung".
DAU_HIEU_KENH = "sóc bóng đá"


def duong_drive():
    """Thư mục kho trên Drive. Cấu hình là chân lý; dò chỉ là đường lùi, và dò có kiểm."""
    ch = getattr(DD, "KHO_DRIVE", "")
    if ch and os.path.isdir(ch):
        return ch
    import glob
    thay = []
    for goc in glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*")):
        for ten_gd in ("My Drive", "Drive của tôi"):
            for q in glob.glob(os.path.join(goc, ten_gd, "*", "*", "kho-tai-nguyen")):
                if os.path.isdir(q) and DAU_HIEU_KENH in _nfc(q).lower():
                    thay.append(q)
    if len(thay) == 1:
        return thay[0]
    if len(thay) > 1:
        print("  ⚠ thấy NHIỀU kho trên Drive, không đoán bừa — khai rõ KHO_DRIVE trong may.json:")
        for q in thay:
            print(f"      {_nfc(q)}")
    return ""


def dong_bo(thu=False, ep=False):
    may = DD.KHO_TAI_NGUYEN
    dri = duong_drive()
    if not dri:
        print("❌ không tìm thấy kho trên Drive — khai KHO_DRIVE trong may.json")
        return 1
    if not os.path.isdir(may):
        print(f"❌ không thấy kho ở ổ máy: {may} (ổ DATA đã gắn chưa?)")
        return 1

    a, on_a = _quet_on_dinh(may)
    b, on_b = _quet_on_dinh(dri)
    so = _doc_so()
    if not (on_a and on_b):
        ben = "ổ máy" if not on_a else "Drive"
        print(f"  ⏳ {ben} đang thay đổi (đồng bộ chưa xong) — DỪNG, không kết luận vội.")
        print("     Chờ biểu tượng Google Drive hết quay rồi chạy lại.")
        return 3
    len_a, len_b = len(a), len(b)

    day = [k for k, v in a.items() if b.get(k) != v]                  # máy → Drive
    keo = [k for k in b if k not in a and k not in so]                # máy kia vừa thêm
    xoa_dri = [k for k in b if k not in a and k in so]                # anh đã xoá
    xoa_may = [k for k in so if k not in b and k in a]                # máy kia đã xoá

    print(f"  ổ máy {len_a} tệp · Drive {len_b} tệp · sổ lần trước {len(so)} tệp")
    print(f"  ĐẨY LÊN {len(day)} · KÉO VỀ {len(keo)} · "
          f"XOÁ trên Drive {len(xoa_dri)} · XOÁ ở máy {len(xoa_may)}")

    # ── PHANH ────────────────────────────────────────────────────────────────
    tong_xoa = len(xoa_dri) + len(xoa_may)
    nen = max(len_a, len_b, 1)
    # LẦN ĐẦU (sổ rỗng) thì mọi thứ bên Drive đều "lạ" — đừng kéo ồ ạt, chỉ đẩy lên rồi
    # ghi sổ; lượt sau mới phân biệt được ai thêm ai xoá.
    if not so and keo:
        print(f"  ℹ lần đầu chạy — bỏ qua {len(keo)} tệp lạ bên Drive, chỉ đẩy lên và ghi sổ")
        keo = []
    if not ep and len(keo) / nen > NGUONG_XOA and len(keo) > 20:
        print(f"\n  ⛔ DỪNG — định kéo về {len(keo)}/{nen} tệp ({len(keo)/nen:.0%}). Bên Drive"
              " nhiều thứ lạ bất thường; xem lại rồi chạy với --ep nếu đúng ý.")
        return 2
    if not ep and tong_xoa and (len_a < TOI_THIEU_DE_XOA or len_b < TOI_THIEU_DE_XOA
                                or tong_xoa / nen > NGUONG_XOA):
        print(f"\n  ⛔ DỪNG — định xoá {tong_xoa}/{nen} tệp ({tong_xoa/nen:.0%}), quá "
              f"ngưỡng {NGUONG_XOA:.0%}.")
        print("     Thường là một bên chưa sẵn sàng (ổ chưa gắn, Drive chưa tải xong),")
        print("     KHÔNG phải anh thật sự xoá ngần ấy. Xem lại rồi chạy với --ep nếu đúng ý.")
        return 2

    if thu:
        for ten, ds in (("ĐẨY LÊN", day), ("KÉO VỀ", keo),
                        ("XOÁ trên Drive", xoa_dri), ("XOÁ ở máy", xoa_may)):
            for k in ds[:8]:
                print(f"    {ten:<16} {k}")
            if len(ds) > 8:
                print(f"    {ten:<16} … và {len(ds) - 8} tệp nữa")
        return 0

    def _chep(g, d):
        os.makedirs(os.path.dirname(d) or ".", exist_ok=True)
        shutil.copy2(g, d)

    n = 0
    for k in day:
        try:
            _chep(os.path.join(may, k), os.path.join(dri, k)); n += 1
        except Exception as e:
            print(f"    ✗ đẩy {k}: {e}")
    for k in keo:
        try:
            _chep(os.path.join(dri, k), os.path.join(may, k)); n += 1
        except Exception as e:
            print(f"    ✗ kéo {k}: {e}")
    for goc, ds in ((dri, xoa_dri), (may, xoa_may)):
        for k in ds:
            try:
                p = os.path.join(goc, k)
                os.path.exists(p) and os.remove(p); n += 1
            except Exception as e:
                print(f"    ✗ xoá {k}: {e}")

    _ghi_so(_quet(may))          # sổ ghi trạng thái SAU khi đồng bộ, theo phía chính chủ
    print(f"  ✅ xong {n} việc · {datetime.now():%H:%M:%S}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Gương kho tài nguyên ổ máy ↔ Drive")
    ap.add_argument("--thu", action="store_true", help="chỉ xem sẽ làm gì, không đụng tệp")
    ap.add_argument("--ep", action="store_true", help="bỏ phanh an toàn (biết chắc mới dùng)")
    a = ap.parse_args()
    # MỘT LỆNH MỘT MÁY: hai lượt đồng bộ chạy chồng nhau sẽ thấy trạng thái dở dang của
    # nhau rồi kết luận sai (tưởng bên kia vừa xoá).
    with NT.khoa_ghi(SO):
        sys.exit(dong_bo(thu=a.thu, ep=a.ep))


if __name__ == "__main__":
    main()
