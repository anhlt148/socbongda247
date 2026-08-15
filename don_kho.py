#!/usr/bin/env python3
"""DỌN KHO ẢNH — giữ ổ khỏi đầy, mà không làm mất thứ còn cần.

Anh chốt 05/08: thư mục việc chuyển sang ổ DATA, và **sau 5 ngày kể từ khi XẾP KHO thì xoá**.

Vì sao phải có: mỗi video gắp về hàng trăm ảnh ứng viên nhưng chỉ dùng vài chục. Đo thật —
video Việt Anh 379 tấm / 173 MB, dùng 25 tấm; video Hubner 107 tấm, dùng 14. Chạy 10 video mỗi
ngày là nửa GB đổ vào ổ mỗi ngày, mà phần lớn không bao giờ đụng tới nữa. Chuyển chỗ mà không
dọn thì chỉ đổi nơi bị đầy — nhất là ổ DATA còn ít hơn ổ hệ thống (10 GB so với 44 GB).

Dọn theo HAI NHỊP, cố ý tách ra:

  ① NGAY khi đã xếp kho — vứt ảnh ứng viên KHÔNG dùng.
     Giữ lại: `anh/chon/` (ảnh thật sự vào video), các sổ (`so-nguon.jsonl`, `so-gap.jsonl`,
     `ban-do-cau.json`, `tram.json`, `cach-hien.json`, `lac-de.json`), kịch bản, giọng, video.
     Dựng lại video vẫn chạy được nguyên vẹn — chỉ mất kho ứng viên để chọn LẠI.

  ② SAU 5 NGÀY kể từ khi xếp kho — xoá cả thư mục việc.
     An toàn vì hộp giao hàng trên Drive đã có đủ 7 tệp: video, giọng, lời bình, gói đăng,
     thumbnail, ảnh QC, sổ nguồn. Thư mục việc lúc này chỉ còn là bản nháp.

**Không đụng vào việc CHƯA xếp kho** — dù cũ tới đâu. Việc chưa xếp kho là việc đang làm dở
hoặc bị bỏ giữa chừng; xoá nó là xoá công anh đã bỏ ra, không phải dọn rác.

Chạy:
    python3 don_kho.py            # xem sẽ dọn gì, KHÔNG xoá (mặc định)
    python3 don_kho.py --that     # dọn thật
    python3 don_kho.py --ngay 3   # đổi hạn giữ
"""
import argparse
import glob
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD

HAN_NGAY = 5                                    # anh chốt 05/08
# Thứ phải giữ lại sau nhịp ①. Mất mấy cái này là không dựng lại được video.
GIU = ("chon", "so-nguon.jsonl", "so-gap.jsonl", "ban-do-cau.json", "tram.json",
       "cach-hien.json", "lac-de.json", "nguon-anh.json", "blueprint.json")


def _da_xep_kho(viec):
    """Trả về giây (mtime) lúc xếp kho, hoặc None nếu chưa xếp.

    Dấu hiệu: có hộp trong kho thành phẩm trên Drive mang đúng tên video này.
    Đọc từ SO-VIDEO.jsonl cho chắc, vì tên hộp bị cắt ngắn nên so tên thư mục dễ trượt.
    """
    p = os.path.join(DD.KHO_VIDEO, "SO-VIDEO.jsonl")
    if not os.path.exists(p):
        return None
    try:
        kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    except Exception:
        return None
    tieu_de = (kb.get("tieu_de") or "").strip().lower()
    if not tieu_de:
        return None
    for dong in open(p, encoding="utf-8"):
        try:
            d = json.loads(dong)
        except Exception:
            continue
        if (d.get("tieu_de") or "").strip().lower() != tieu_de:
            continue
        hop = os.path.join(DD.KHO_VIDEO, d.get("hop") or d.get("ma") or "")
        if os.path.isdir(hop):
            return os.path.getmtime(hop)
    return None


def _nang(duong):
    n = 0
    for r, _, fs in os.walk(duong):
        for f in fs:
            try:
                n += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    return n


def soat(han_ngay=HAN_NGAY):
    """Xem xét từng thư mục việc, trả về việc cần làm — KHÔNG xoá gì."""
    ra = []
    for d in sorted(glob.glob(os.path.join(DD.VIEC, "*", "*"))):   # <ngày>/<video-N-…>
        if not os.path.isdir(d):
            continue
        luc = _da_xep_kho(d)
        muc = {"viec": d, "ma": os.path.relpath(d, DD.VIEC), "nang": _nang(d),
               "xep_kho": luc, "viec_can_lam": "giữ nguyên"}
        if luc is None:
            muc["ly_do"] = "chưa xếp kho — đang làm dở, không đụng"
        else:
            tuoi = (time.time() - luc) / 86400
            muc["tuoi_ngay"] = round(tuoi, 1)
            if tuoi >= han_ngay:
                muc["viec_can_lam"] = "xoá cả thư mục"
                muc["ly_do"] = (f"xếp kho {tuoi:.1f} ngày trước — hộp trên Drive đã đủ 7 tệp")
            else:
                thua = _anh_thua(d)
                if thua:
                    muc["viec_can_lam"] = "vứt ảnh ứng viên không dùng"
                    muc["so_anh_thua"] = len(thua)
                    muc["nang_thua"] = sum(os.path.getsize(x) for x in thua if os.path.exists(x))
                    muc["ly_do"] = f"đã xếp kho {tuoi:.1f} ngày, còn giữ tới ngày thứ {han_ngay}"
                else:
                    muc["ly_do"] = "đã dọn rồi"
        ra.append(muc)
    return ra


def _anh_thua(viec):
    """Thứ vứt được sau khi đã xếp kho — ảnh ứng viên ngoài `anh/chon/`, và rác của xưởng.

    `dung/` là thư mục TẠM: từng cảnh render ra một tệp .mp4 rời rồi mới ghép. Đo trên video
    Việt Anh: 20 MB rác, còn hơn cả video thành phẩm (13 MB). Xưởng dựng lại là nó tự sinh
    lại, giữ chẳng để làm gì.
    """
    thua = []
    for thu in ("anh", "anh2"):
        thua += glob.glob(os.path.join(viec, thu, "*.jpg"))
    thua += glob.glob(os.path.join(viec, "anh", "_dinh-watermark", "*.jpg"))
    thua += glob.glob(os.path.join(viec, "anh", "_thumb", "*"))
    thua += glob.glob(os.path.join(viec, "dung", "*"))           # cảnh rời của xưởng
    thua += glob.glob(os.path.join(viec, "bang-anh.jpg"))        # bảng soi ảnh của bản cũ
    thua += glob.glob(os.path.join(viec, "video__qc-*"))         # ảnh chứng cứ QC, đã có trong hộp
    return thua


def don(han_ngay=HAN_NGAY, that=False):
    ds = soat(han_ngay)
    thu_hoi = 0
    for m in ds:
        if m["viec_can_lam"] == "xoá cả thư mục":
            thu_hoi += m["nang"]
            if that:
                shutil.rmtree(m["viec"], ignore_errors=True)
        elif m["viec_can_lam"] == "vứt ảnh ứng viên không dùng":
            thu_hoi += m.get("nang_thua", 0)
            if that:
                for p in _anh_thua(m["viec"]):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
                shutil.rmtree(os.path.join(m["viec"], "anh", "_thumb"), ignore_errors=True)
                shutil.rmtree(os.path.join(m["viec"], "anh", "_dinh-watermark"),
                              ignore_errors=True)
                shutil.rmtree(os.path.join(m["viec"], "dung"), ignore_errors=True)
    return ds, thu_hoi


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--that", action="store_true", help="dọn thật (mặc định chỉ xem)")
    ap.add_argument("--ngay", type=int, default=HAN_NGAY, help=f"hạn giữ (mặc định {HAN_NGAY})")
    a = ap.parse_args()

    ds, thu_hoi = don(a.ngay, a.that)
    print(f"KHO VIỆC: {DD.VIEC}")
    for m in ds:
        dau = {"giữ nguyên": "·", "vứt ảnh ứng viên không dùng": "🧹",
               "xoá cả thư mục": "🗑"}[m["viec_can_lam"]]
        print(f"  {dau} {m['ma']:44s} {m['nang']/1e6:7.1f} MB  {m['ly_do']}"
              + (f" ({m['so_anh_thua']} ảnh, {m['nang_thua']/1e6:.0f} MB)"
                 if m.get("so_anh_thua") else ""))
    print(f"\n{'ĐÃ THU HỒI' if a.that else 'SẼ THU HỒI'}: {thu_hoi/1e6:.0f} MB")
    if not a.that:
        print("(mới chỉ xem — thêm --that để dọn thật)")
