#!/usr/bin/env python3
"""CHUẨN HOÁ + GỘP TÊN CHỦ THỂ — một nguồn dùng chung (anh đặt 10/08 khuya).

Nỗi đau: "thành long" và "lê phạm thành long" là MỘT người mà thành hai thẻ — bản cũ
chỉ so với bảng chuan-hoa-ten.json (ít tên), tên tự do trong sổ không được so nên biến
thể cứ đẻ song song, khó kiểm soát dần.

Luật gộp (theo thứ tự):
① Tra bảng `chuan-hoa-ten.json` (biến thể → tên chuẩn) — nhanh nhất.
② " vs " là trận đấu, không phải chủ thể → trả rỗng.
③ So TẬP-TỪ (bỏ dấu) với bảng VÀ với MỌI TÊN đang sống trong sổ: tên này là mảnh
   của tên kia ("thanh long" ⊆ "le pham thanh long") → về MỘT mối. Phía được giữ =
   tên có NHIỀU TẤM hơn trong sổ; hoà thì tên DÀI hơn (đầy đủ hơn).
④ TỪ CHẶN — phần chênh giữa hai tên mà chứa từ phân-thực-thể (u23, u19, nữ, futsal…)
   thì KHÔNG gộp: "U23 Việt Nam" ≠ "Việt Nam" dù tập từ chứa nhau.
⑤ Gộp được thì TỰ HỌC: ghi cặp biến thể → chuẩn vào bảng (flock) — lần sau tra ①
   trúng ngay, và mọi cửa (server, script nhập) cùng khôn lên.

Lệnh quét GỘP HỒI TỐ toàn kho (code thuần, không model):
    python3 chuan_ten.py --quet          # xem trước, chưa ghi
    python3 chuan_ten.py --quet --ghi    # gộp thật vào sổ + bảng
"""
import json
import os
import re
import time
import unicodedata

import duong_dan as DD
import nen_tang as NT

KHO = os.path.join(DD.KHO_TAI_NGUYEN, "anh-chu-the")
SO = os.path.join(KHO, "so-chu-the.jsonl")
SO_VIDEO = os.path.join(DD.KHO_TAI_NGUYEN, "video-chu-the", "so-video.jsonl")
BANG = os.path.join(KHO, "chuan-hoa-ten.json")

# từ phân-THỰC-THỂ: hai tên chỉ chênh nhau mấy từ này là HAI chủ thể khác nhau
TU_CHAN = {"u15", "u16", "u17", "u18", "u19", "u20", "u21", "u22", "u23",
           "nu", "futsal", "tre", "b", "ii"}


def bo_dau(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", s.replace("đ", "d")).strip()


def slug_hoa(s, dai=42):
    """Chuỗi tiếng Việt → tên tệp an toàn: bỏ dấu, đ→d, gì không phải chữ-số thành gạch.

    Ở một chỗ duy nhất (anh chốt "não một nguồn"): trước 16/08 hàm này nằm riêng trong
    `buoc3_xepkho.py`; nay tên video gắp về cũng cần nó, chép bản thứ hai là hai bản sẽ
    lệch nhau.
    """
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn") \
        .replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:dai].strip("-")


def _nfc(s):
    return unicodedata.normalize("NFC", s or "")


class BoGopTen:
    """Cache bảng + sổ theo mtime — gọi dày cũng rẻ."""

    def __init__(self):
        self._bang_mt = 0
        self._tra = {}
        self._so_mt = 0
        self._dem = {}          # tên (nguyên dấu) → số tấm trong sổ (ảnh + video)

    def _nap_bang(self):
        try:
            mt = os.path.getmtime(BANG)
        except OSError:
            return
        if mt == self._bang_mt:
            return
        try:
            bang = json.load(open(BANG, encoding="utf-8"))
        except Exception:
            return
        tra = {}
        for chuan, bien in bang.items():
            tra[bo_dau(chuan)] = chuan
            for b in bien:
                tra[bo_dau(b)] = chuan
        self._tra, self._bang_mt = tra, mt

    def _nap_so(self):
        mt = 0.0
        for p in (SO, SO_VIDEO):
            try:
                mt += os.path.getmtime(p)
            except OSError:
                pass
        if mt == self._so_mt:
            return
        dem = {}
        for p in (SO, SO_VIDEO):
            if not os.path.exists(p):
                continue
            for dong in open(p, encoding="utf-8"):
                try:
                    ct = _nfc(json.loads(dong).get("chu_the", "")).strip()
                except Exception:
                    continue
                if ct:
                    dem[ct] = dem.get(ct, 0) + 1
        self._dem, self._so_mt = dem, mt

    def _hoc(self, bien, chuan):
        """Ghi cặp biến thể → chuẩn vào bảng (flock) để mọi cửa cùng khôn."""
        if bo_dau(bien) == bo_dau(chuan):
            pass                              # khác mỗi dấu vẫn đáng ghi — tra ① trúng ngay
        try:
            with NT.khoa_ghi(BANG) as kh:
                try:
                    bang = json.load(open(BANG, encoding="utf-8"))
                except Exception:
                    bang = {}
                ds = bang.setdefault(chuan, [])
                if bien != chuan and bien not in ds:
                    ds.append(bien)
                    json.dump(bang, open(BANG, "w", encoding="utf-8"),
                              ensure_ascii=False, indent=1)
                    self._bang_mt = 0         # ép nạp lại lần tra sau
        except OSError:
            pass

    def chuan(self, ten):
        """Tên bất kỳ → tên chuẩn duy nhất (hoặc "" nếu không phải chủ thể)."""
        ten = _nfc(ten).strip()
        if not ten:
            return ""
        if " vs " in ten.lower():
            return ""
        if _ten_ghep(ten):
            return ten                         # tên ghép nhiều chủ thể — để nguyên
        self._nap_bang()
        k = bo_dau(ten)
        if k in self._tra:
            return self._tra[k]
        # so với bảng chuẩn trước (ít, nhanh)
        for k0, chuan in self._tra.items():
            if khop_gop(k, k0):
                self._hoc(ten, chuan)
                return chuan
        # rồi so với MỌI TÊN đang sống trong sổ — chỗ bản cũ bỏ sót
        self._nap_so()
        ung = []
        for ct, so in self._dem.items():
            if _ten_ghep(ct):
                continue
            k1 = bo_dau(ct)
            if k1 == k or khop_gop(k, k1):
                ung.append((not _co_nam(k1), so, len(ct), ct))
        if ung:
            # tên KHÔNG dính năm ưu tiên làm chuẩn ('văn hậu' thắng 'văn hậu 2024'
            # dù ít tấm hơn), rồi mới tới nhiều tấm, rồi tên dài (đầy đủ hơn)
            ung.append((not _co_nam(k), self._dem.get(ten, 0), len(ten), ten))
            ung.sort(reverse=True)
            chuan = ung[0][3]
            if chuan != ten:
                self._hoc(ten, chuan)
            return chuan
        return ten


def _la_day_con(ngan, dai):
    """Các từ của tên ngắn phải xuất hiện ĐÚNG THỨ TỰ trong tên dài — 'thanh long' ⊂
    'le pham thanh long' ✓; 'quang vinh' vs 'do vinh quang' ✗ (từ trùng nhưng ĐẢO
    thứ tự = người KHÁC, bẫy tên Việt suýt gộp Quang Vinh vào Đỗ Vinh Quang 10/08)."""
    i = 0
    for w in dai:
        if i < len(ngan) and w == ngan[i]:
            i += 1
    return i == len(ngan)


def _co_nam(k):
    return bool(re.search(r"\b(19|20)\d{2}\b", k))


def _ten_ghep(ten):
    """'Kim Sang-sik, Nguyễn Đình Triệu' / 'VFF & La Liga' = NHIỀU chủ thể một chuỗi —
    không đem gộp với ai (gộp là nuốt mất một bên)."""
    return ("," in ten) or ("&" in ten)


def khop_gop(k_a, k_b):
    """Hai CHUỖI bỏ-dấu có đáng gộp một mối: tập từ chứa nhau + phần chênh không phạm
    TU_CHAN + từ chung giữ đúng THỨ TỰ."""
    ta, tb = k_a.split(), k_b.split()
    if not ta or not tb:
        return False
    sa, sb = set(ta), set(tb)
    if not (sa <= sb or sb <= sa):
        return False
    if (sa ^ sb) & TU_CHAN:
        return False
    ngan, dai = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return _la_day_con(ngan, dai)


# ── QUÉT GỘP HỒI TỐ (code thuần) ─────────────────────────────────────────────
def quet(ghi=False):
    dem = {}
    for p in (SO, SO_VIDEO):
        if not os.path.exists(p):
            continue
        for dong in open(p, encoding="utf-8"):
            try:
                ct = _nfc(json.loads(dong).get("chu_the", "")).strip()
            except Exception:
                continue
            if ct:
                dem[ct] = dem.get(ct, 0) + 1
    # tên KHÔNG dính năm đứng trước làm chuẩn, rồi nhiều tấm, rồi dài
    ten_ds = sorted(dem, key=lambda t: (not _co_nam(bo_dau(t)), dem[t], len(t)),
                    reverse=True)
    doi, giu, chan = {}, [], []                # đổi: biến thể → chuẩn
    for t in ten_ds:
        if _ten_ghep(t):
            giu.append(t)                      # tên ghép nhiều chủ thể — để nguyên
            continue
        k_t = bo_dau(t)
        tu = set(k_t.split())
        dich = None
        for g in giu:
            if _ten_ghep(g):
                continue
            k_g = bo_dau(g)
            tu_g = set(k_g.split())
            if k_g == k_t or khop_gop(k_t, k_g):
                dich = g
                break
            if (tu <= tu_g or tu_g <= tu) and not khop_gop(k_t, k_g):
                chan.append((t, g))
        if dich:
            doi[t] = dich
        else:
            giu.append(t)
    print(f"Kho có {len(ten_ds)} tên · gộp được {len(doi)} biến thể về "
          f"{len(set(doi.values()))} tên chuẩn")
    for bien, chuan in sorted(doi.items(), key=lambda x: x[1]):
        print(f"   {bien!r} ({dem[bien]} tấm) → {chuan!r} ({dem[chuan]} tấm)")
    if chan:
        print("KHÔNG gộp (từ chặn — khác thực thể):")
        for a, b in chan[:20]:
            print(f"   {a!r} ↛ {b!r}")
    if not ghi or not doi:
        if not ghi:
            print("(xem trước — thêm --ghi để gộp thật)")
        return doi
    for p in (SO, SO_VIDEO):
        if not os.path.exists(p):
            continue
        with NT.khoa_ghi(p) as kh:
            ds = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
            n = 0
            for m in ds:
                ct = _nfc(m.get("chu_the", "")).strip()
                if ct in doi:
                    m["chu_the"] = doi[ct]
                    n += 1
            with open(p, "w", encoding="utf-8") as f:
                for m in ds:
                    f.write(json.dumps(m, ensure_ascii=False) + "\n")
        print(f"   {os.path.basename(p)}: đổi {n} dòng")
    b = BoGopTen()
    for bien, chuan in doi.items():
        b._hoc(bien, chuan)
    print("   đã ghi các cặp vào bảng chuẩn — mọi cửa từ giờ tra trúng ngay")
    return doi


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--quet", action="store_true")
    ap.add_argument("--ghi", action="store_true")
    a = ap.parse_args()
    if a.quet:
        quet(ghi=a.ghi)
