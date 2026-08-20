#!/usr/bin/env python3
"""KHO CHỦ THỂ dùng chung (anh chốt 10/08): ảnh đã trả giá một lần (tìm + soi + duyệt)
phải sống tiếp cho các bài sau, tra theo NHÃN NỘI DUNG chứ không theo tên file — vá
tận gốc họ lỗi "tái dùng mù" (vụ HLV Campuchia 09/08).

Hai ngăn:
  · len_hinh — ảnh từng được gán cảnh trong một bài đã dựng (qua mắt anh)
  · du_tru   — ảnh đẹp gom về mà bài đó không dùng đến (anh dặn 10/08: đừng bỏ phí)

LUẬT SẠCH (anh chốt 10/08): kho CHỈ chứa ảnh sạch watermark —
  · watermark ở RÌA (góc/dải trên dưới) → CẮT mép đó bỏ trước khi nhập;
  · watermark GIỮA KHUNG / thân ảnh → KHÔNG nhập (thà thiếu hơn bẩn);
  · ảnh anh đã crop tay (da_crop) coi là sạch.

Nhãn: MỘT lượt haiku vision cho cả bài (mắt máy + mồi ngữ cảnh = câu ảnh được gán,
từ khoá đã tìm ra nó) — trả tiền một lần lúc nhập; lúc TRA về sau là code thuần.

Dùng:  python3 nhap_kho_chu_the.py <mã việc | đường việc> [...]
       python3 nhap_kho_chu_the.py --hoi-to     # quét mọi bài trong kho việc
       … --soat --loc="việt nam,thái lan" --so=200   # soát 200 tấm, ưu tiên nội dung
"""
import glob
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tram"))
import duong_dan as DD
import nen_tang as NT                                        # noqa: E402
import gap_anh                                                # noqa: E402
from PIL import Image                                         # noqa: E402

KHO = os.path.join(DD.KHO_TAI_NGUYEN, "anh-chu-the")
SO = os.path.join(KHO, "so-chu-the.jsonl")
VT = os.path.join(KHO, "van-tay.json")
VT_LOI = os.path.join(KHO, "van-tay-loi.json")   # vân LÕI — bắt ảnh đã cắt mép (11/08)
SAN_CANH = 500                  # cạnh ngắn tối thiểu sau mọi phép cắt
CAT_MEP = 0.14                  # cắt 14% mép dính watermark rìa

# ─── BẬC MẮT MÁY (anh chốt 14/08) ────────────────────────────────────────────
# Quét lại cả kho tốn ~1,1 triệu token = một ngày sản xuất. Không được để lần sau
# thêm vài chục ảnh mới lại phải trả từng ấy lần nữa. Mỗi tấm nay NHỚ mình đã được
# CON MẮT NÀO nhìn: lượt quét bằng model bậc cao chỉ đụng tấm chưa ai nhìn hoặc mới
# chỉ mắt yếu hơn nhìn; tấm đã qua mắt bằng hoặc cao hơn thì bỏ qua sạch.
BAC_MODEL = {"haiku": 1, "sonnet": 2, "opus": 3}


def _bac_model(ten=None):
    """Tên model (dài hay ngắn) → bậc. Không nhận ra thì coi như bậc thấp nhất."""
    t = (ten or os.environ.get("KHO_MODEL", "claude-sonnet-5")).lower()
    for k, v in BAC_MODEL.items():
        if k in t:
            return v
    return 1


def _bac_da_soat(d):
    """Tấm này đã qua mắt bậc mấy rồi.

    Bản cũ chỉ có cờ trần `da_soat: true`, không ghi model — không biết là mắt nào
    nhìn thì phải coi như MẮT YẾU NHẤT (bậc 1) và cho quét lại. Thà tốn thêm ít
    token còn hơn giữ một nhãn sai nằm trong kho làm hỏng đề xuất ảnh về sau.
    """
    if d.get("soat_model"):
        return _bac_model(d["soat_model"])
    return 1 if d.get("da_soat") else 0


def _nfc(s):
    return unicodedata.normalize("NFC", s or "")


def _bo_dau_nk(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")


import chuan_ten as CT                                        # noqa: E402
_BO_GOP = CT.BoGopTen()


def _chuan_hoa_ct(ten):
    """KIỂM SOÁT TRÙNG chủ thể — từ 10/08 khuya trỏ về module chuan_ten DÙNG CHUNG
    với server trạm (não một nguồn): so cả bảng lẫn MỌI TÊN trong sổ, tự học bảng,
    từ chặn U23/nữ/futsal không gộp."""
    return _BO_GOP.chuan(ten)


def _khu_trung_nhan(nh_ds):
    """Nhãn trong MỘT tấm không được trùng nhau (so bỏ dấu) — anh đặt 10/08."""
    thay, sach = set(), []
    for n in nh_ds:
        n = _nfc(str(n)).strip()
        k = _bo_dau_nk(n)
        if n and k not in thay:
            thay.add(k)
            sach.append(n)
    return sach[:12]


def _doc_so():
    if not os.path.exists(SO):
        return []
    return [json.loads(l) for l in open(SO, encoding="utf-8") if l.strip()]


def _vung_tu_chu(chu):
    """Chuỗi OCR 'góc dưới trái: …' → (danh sách mép cần cắt, có_vùng_không_cắt_được).

    'giữa khung' và các vùng thân ('thân trái/phải…' — OCR ghi ngoài bộ VUNG_TEN chuẩn)
    không cắt sạch được bằng phép cắt mép."""
    chu = chu or ""
    mep = set()
    if "góc trên" in chu or "dải trên" in chu:
        mep.add("tren")
    if "góc dưới" in chu or "dải dưới" in chu:
        mep.add("duoi")
    ban = ("giữa khung" in chu) or ("thân" in chu)
    return mep, ban


def _cat_sach(im, mep):
    """Cắt các mép dính watermark. Trả ảnh mới hoặc None nếu cắt xong quá bé."""
    w, h = im.size
    top = int(h * CAT_MEP) if "tren" in mep else 0
    day = h - (int(h * CAT_MEP) if "duoi" in mep else 0)
    im2 = im.crop((0, top, w, day))
    if min(im2.size) < SAN_CANH:
        return None
    return im2


def _tach_cau(loi):
    return [c.strip() for c in re.split(DD.TACH_CAU_RE, loi or "") if c.strip()]


def _nhan_may(ds_moi, kho_tam):
    """MỘT lượt haiku vision cho cả mẻ: đọc từng ảnh + mồi ngữ cảnh → nhãn chuẩn.
    Trục trặc thì rơi về nhãn thô từ mồi (cờ nhan_tho=True, lượt sau bổ)."""
    if not ds_moi:
        return {}
    # BẢN THU NHỎ cho mắt máy (anh chốt 13/08): 3.555 → 888 token/ảnh, đo thật vẫn
    # đọc đúng số áo + nhận đúng người. Ảnh lưu kho vẫn là bản gốc đầy đủ.
    dong = "\n".join(f"- {gap_anh.ban_nho(d['tep_tam'])} — gợi ý ngữ cảnh: {d['moi'][:160]}"
                     for d in ds_moi)
    # TỪ ĐIỂN THỰC THỂ (anh đặt 11/08): đưa danh sách TÊN vào prompt để mắt máy gọi
    # đúng tên người/đội/sân, thay vì tả chung chung "cầu thủ áo đỏ số 9"
    tu_dien = ""
    try:
        p_td = os.path.join(DD.KHO_TAI_NGUYEN, "tu-dien-thuc-the.json")
        td = json.load(open(p_td, encoding="utf-8"))
        cts = " · ".join(x["ten"] for x in td.get("cau_thu_vn", []))
        hlvs = " · ".join(x["ten"] for x in td.get("hlv", []))
        sans = " · ".join(x["ten"] for x in td.get("san_van_dong", []))
        dnas = " · ".join(x["ten"] + f" ({x.get('doi','')})"
                          for x in td.get("cau_thu_dna", []))
        clbs = " · ".join(v["ten"] for v in (td.get("clb_vleague") or {}).values())
        tu_dien = (
            "\n═══ TỪ ĐIỂN TÊN (nhận ra ai thì GỌI ĐÚNG TÊN, đừng tả chung chung; "
            "KHÔNG chắc thì để chu_the rỗng, cấm đoán bừa) ═══\n"
            f"• Cầu thủ VN/U23: {cts}\n"
            f"• HLV: {hlvs}\n"
            f"• CLB V.League: {clbs}\n"
            f"• Sân: {sans}\n"
            f"• Cầu thủ ĐNÁ khác: {dnas}\n"
            "═══════════════════════════════════\n")
    except Exception:
        pass
    # anh chốt 10/08: máy điền HẾT những gì nhìn thấy, THẬT CHI TIẾT — tên riêng và
    # năm anh tự bù khi máy không chắc
    lenh = (
        "Em là mắt máy gắn nhãn ảnh bóng đá, tả THẬT CHI TIẾT. Với TỪNG ảnh dưới đây: "
        "dùng tool Read mở ảnh, đối chiếu gợi ý ngữ cảnh (gợi ý có thể sai — tin MẮT "
        "trước).\n"
        + tu_dien +
        f"{dong}\n\n"
        "Trả về DUY NHẤT một khối JSON, khoá là TÊN TỆP (basename), giá trị:\n"
        '{"nhan": [6-12 nhãn TIẾNG VIỆT phủ đủ các lớp sau, lớp nào thấy thì ghi:\n'
        "  · HÀNH ĐỘNG cụ thể (dẫn bóng, đánh đầu, sút bóng, xoạc bóng, tranh chấp, "
        "ăn mừng trượt gối, ôm nhau, vỗ tay, phát biểu họp báo, nâng cúp, tung cờ…)\n"
        "  · THÂN PHẬN ÁO ĐẤU — BẮT BUỘC ghi nếu nhìn ra (anh dạy 11/08, luật đắt "
        "nhất): 'áo TUYỂN Việt Nam' / 'áo CLB Công an Hà Nội' / 'áo CLB Hà Nội FC' / "
        "'áo tập' / 'vest họp báo' / 'thường phục'. Một cầu thủ có hai thân phận — ảnh "
        "áo CLB KHÔNG dùng được cho bài về tuyển quốc gia, nên không ghi là sau này "
        "không lọc được.\n"
        "  · đội + màu áo + SỐ ÁO đọc được (vd: áo đỏ số 10, áo vàng đen số 7)\n"
        "  · bối cảnh (sân vận động ban đêm, khán đài kín, phòng họp báo, đường phố…)\n"
        "  · chữ/logo TO đọc được trong hình (tên giải trên backdrop, bảng tỷ số…)\n"
        "  · cảm xúc nổi bật (vỡ oà, thất vọng, căng thẳng, tự hào)],\n"
        ' "mo_ta": "MỘT câu giàu chi tiết tả đúng khung hình — ai làm gì, ở đâu, '
        'không khí thế nào", '
        '"chu_the": "tên người/đội CHÍNH — CHỈ khi chắc chắn, không thì chuỗi rỗng"}\n'
        "KHÔNG chắc tên ai thì chu_the để RỖNG — cấm đoán bừa tên người."
    )
    try:
        # prompt đi qua STDIN — để sau --allowedTools là bị cờ đó NUỐT làm tên tool,
        # CLI báo "Input must be provided" (dò ra 10/08)
        r = subprocess.run([NT.tim_claude(), "-p",
                            "--model", os.environ.get("KHO_MODEL",
                                                      "claude-haiku-4-5-20251001"),
                            "--allowedTools", "Read"],
                           input=lenh, capture_output=True, text=True, timeout=900)
        m = re.search(r"\{.*\}", r.stdout, re.S)
        return json.loads(m.group(0)) if m else {}
    except Exception as e:
        print(f"  ⚠ mắt máy nghẽn ({e}) — dùng nhãn thô từ mồi, lượt sau bổ")
        return {}


def nhap(viec):
    ma = os.path.relpath(viec, DD.VIEC)
    a_dir = os.path.join(viec, "anh")
    if not os.path.isdir(a_dir):
        print(f"{ma}: không có thư mục ảnh — bỏ qua")
        return 0
    os.makedirs(KHO, exist_ok=True)
    so = _doc_so()
    da_co_nguon = {(d.get("nguon_bai"), d.get("ten_goc")) for d in so}
    vt = json.load(open(VT)) if os.path.exists(VT) else {}
    vt_loi = json.load(open(VT_LOI)) if os.path.exists(VT_LOI) else {}
    # sổ lõi chưa có / thiếu tấm nào thì tính bù NGAY (một lần) — không thì cổng lõi
    # rỗng, coi như không có cổng
    for _t in {os.path.basename(f) for f in glob.glob(os.path.join(KHO, "*.jpg"))}:
        if _t not in vt_loi:
            try:
                vt_loi[_t] = gap_anh._dhash_loi(Image.open(os.path.join(KHO, _t)))
            except Exception:
                pass
    # mã bài này đã đóng góp ảnh nào → để CỘNG DẤU DÙNG cho tấm cũ khi gặp trùng
    dong_theo_tep = {d.get("tep"): d for d in so}

    # sổ của bài: ai được LÊN HÌNH, ảnh nào có watermark, ảnh nào lạc đề
    nh = {}
    p_tr = os.path.join(a_dir, "tram.json")
    if os.path.exists(p_tr):
        try:
            nh = json.load(open(p_tr, encoding="utf-8"))
        except Exception:
            nh = {}
    kb = {}
    p_kb = os.path.join(viec, "kich-ban.json")
    if os.path.exists(p_kb):
        try:
            kb = json.load(open(p_kb, encoding="utf-8"))
        except Exception:
            kb = {}
    cau_chu = _tach_cau(kb.get("loi_binh", ""))
    lac = {}
    p_lac = os.path.join(a_dir, "lac-de.json")
    if os.path.exists(p_lac):
        try:
            lac = json.load(open(p_lac, encoding="utf-8"))
        except Exception:
            lac = {}
    gap = {}
    p_gap = os.path.join(a_dir, "so-gap.jsonl")
    if os.path.exists(p_gap):
        for l in open(p_gap, encoding="utf-8"):
            try:
                d = json.loads(l)
                gap[d.get("tep", "")] = d
            except Exception:
                pass
    # ảnh đã crop tay / chữ OCR theo ẢNH GỐC từ sổ nguồn (chon/NN → goc anh/nXX)
    da_crop, chu_goc = set(), {}
    p_sn = os.path.join(a_dir, "so-nguon.jsonl")
    if os.path.exists(p_sn):
        for l in open(p_sn, encoding="utf-8"):
            try:
                d = json.loads(l)
                g = os.path.basename(d.get("goc", ""))
                if d.get("da_crop"):
                    da_crop.add(g)
                if d.get("chu_doc_duoc"):
                    chu_goc[g] = d["chu_doc_duoc"]
            except Exception:
                pass

    # tập LÊN HÌNH: ban_do + anh_phu (ảnh) + anh2 của khung đôi (ảnh) — kèm mồi câu
    len_hinh = {}
    for k, v in (nh.get("ban_do") or {}).items():
        if isinstance(v, str) and v.endswith(".jpg"):
            i = int(k)
            len_hinh.setdefault(os.path.basename(v), []).append(
                cau_chu[i] if i < len(cau_chu) else "")
    for k, ds in (nh.get("anh_phu") or {}).items():
        for v in (ds or []):
            if isinstance(v, str) and v.endswith(".jpg"):
                i = int(k)
                len_hinh.setdefault(os.path.basename(v), []).append(
                    cau_chu[i] if i < len(cau_chu) else "")
    for k, os_ in (nh.get("ghep_canh") or {}).items():
        for cfg in (os_ or {}).values():
            a2 = (cfg or {}).get("anh2") or ""
            if a2.endswith(".jpg"):
                i = int(k)
                len_hinh.setdefault(os.path.basename(a2), []).append(
                    cau_chu[i] if i < len(cau_chu) else "")

    tam = os.path.join(KHO, "_tam")
    os.makedirs(tam, exist_ok=True)
    ds_moi, bo = [], {"trung": 0, "ban": 0, "be": 0, "lac": 0, "co": 0}
    can_ghi_lai_so = [False]        # có cộng dấu dùng cho tấm cũ thì phải ghi lại sổ
    for p in sorted(glob.glob(os.path.join(a_dir, "[nt]*.jpg"))):
        ten = os.path.basename(p)
        if (ma, ten) in da_co_nguon:
            bo["co"] += 1
            continue
        if lac.get(ten, {}).get("lac_de") and ten not in len_hinh:
            bo["lac"] += 1
            continue
        g = gap.get(ten, {})
        chu_wm = " · ".join(x for x in (g.get("can_soi"), g.get("dau_nguon"),
                                        chu_goc.get(ten)) if x)
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            continue
        if ten in da_crop:
            im2 = im                               # anh đã tự cắt — coi là sạch
        else:
            mep, ban = _vung_tu_chu(chu_wm)
            if ban:
                bo["ban"] += 1                     # watermark giữa/thân — không cắt sạch nổi
                continue
            im2 = _cat_sach(im, mep) if mep else im
            if im2 is None:
                bo["be"] += 1
                continue
        if min(im2.size) < SAN_CANH:
            bo["be"] += 1
            continue
        van = gap_anh._dhash(im2)
        van_loi = gap_anh._dhash_loi(im2)
        # TRÙNG nếu khớp vân THƯỜNG hoặc vân LÕI (anh hỏi 11/08: ảnh cắt watermark rồi
        # có nhận ra không) — lõi nhìn phần giữa nên bản đã cắt mép vẫn khớp bản gốc
        trung_voi = next((t for t, v0 in vt.items()
                          if bin(int(van) ^ int(v0)).count("1") <= 6), None) \
            or gap_anh._tim_trung({}, 0, vt_loi, van_loi)
        if trung_voi:
            bo["trung"] += 1
            # CỘNG DẤU DÙNG cho tấm cũ (vá 11/08): trước đây `continue` thẳng nên ảnh
            # dùng ở bài 1 lẫn bài 3 mà sổ chỉ ghi bài 1 → bộ xoay vòng "ít dùng gần
            # đây" tưởng nó còn mới, đẩy lên đầu, video lặp hình
            d0 = dong_theo_tep.get(trung_voi)
            if d0 is not None and ten in len_hinh:
                dd = d0.setdefault("da_dung", [])
                if ma not in dd:
                    dd.append(ma)
                    can_ghi_lai_so[0] = True
            continue
        hang = "len_hinh" if ten in len_hinh else "du_tru"
        moi = " | ".join(x for x in [
            " / ".join(c[:70] for c in len_hinh.get(ten, [])[:2]),
            g.get("tu_khoa", ""), _nfc(g.get("ten_goc", ""))] if x)
        ten_kho = f"{ma.replace('/', '_')}__{ten}"
        p_tam = os.path.join(tam, ten_kho)
        im2.save(p_tam, quality=90)
        # ghi vân NGAY vào sổ tạm để ảnh sau trong CÙNG LƯỢT so được với ảnh trước
        # (vá 11/08: 5 cặp trùng trong kho đều là hai ảnh của cùng một bài — vì sổ chỉ
        # được cập nhật ở vòng GHI, sau khi lọc xong hết)
        vt[ten_kho] = str(van)
        vt_loi[ten_kho] = van_loi
        ds_moi.append({"ten_goc": ten, "tep_tam": p_tam, "ten_kho": ten_kho,
                       "hang": hang, "moi": moi, "van": van, "van_loi": van_loi,
                       "kich": f"{im2.width}x{im2.height}",
                       "url": g.get("url", ""), "giay_phep": g.get("giay_phep", ""),
                       "da_cat_wm": ten not in da_crop and bool(_vung_tu_chu(chu_wm)[0])})
    # dấu dùng vừa cộng cho tấm CŨ phải ghi lại cả sổ (append không sửa được dòng cũ)
    if can_ghi_lai_so[0]:
        with open(SO, "w", encoding="utf-8") as f:
            for d0 in so:
                f.write(json.dumps(d0, ensure_ascii=False) + "\n")
        json.dump(vt, open(VT, "w"))
        json.dump(vt_loi, open(VT_LOI, "w"))
    if not ds_moi:
        print(f"{ma}: không có ảnh mới ({bo})")
        return 0

    nhan = _nhan_may(ds_moi, tam)
    # nhãn NĂM + SỰ KIỆN tự đắp từ ngữ cảnh bài (anh đặt 10/08: "2026 đình bắc aff
    # vs campuchia" phải tra được mà không ai phải gõ tay) — code thuần, 0 model
    nam_bai = ma[:4] if re.match(r"20\d\d", ma) else ""
    MAU_GIAI = ["asean cup 2026", "aff cup", "asean championship", "sea games",
                "vong loai world cup", "vong loai asian cup", "v league"]
    chuoi_kb = _bo_dau_nk(kb.get("tieu_de", "") + " " + " ".join(kb.get("tu_khoa", [])))
    su_kien_bai = [g for g in MAU_GIAI if _bo_dau_nk(g) in chuoi_kb][:1]
    luc = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SO, "a", encoding="utf-8") as f:
        for d in ds_moi:
            os.replace(d["tep_tam"], os.path.join(KHO, d["ten_kho"]))
            vt[d["ten_kho"]] = str(d["van"])
            vt_loi[d["ten_kho"]] = d["van_loi"]
            n = nhan.get(d["ten_kho"]) or nhan.get(os.path.basename(d["tep_tam"])) or {}
            tho = not bool(n)
            nh_ds = n.get("nhan") or [t for t in re.split(r"[|/·]", d["moi"]) if t.strip()][:4]
            nh_ds = _khu_trung_nhan(list(nh_ds) + ([nam_bai] if nam_bai else [])
                                    + su_kien_bai)
            f.write(json.dumps({
                "tep": d["ten_kho"], "hang": d["hang"],
                "nhan": nh_ds,
                "chu_the": _chuan_hoa_ct(_nfc(n.get("chu_the", ""))),
                "mo_ta": _nfc(n.get("mo_ta", "")), "nhan_tho": tho,
                "nguon_bai": ma, "ten_goc": d["ten_goc"], "url": d["url"],
                "giay_phep": d["giay_phep"], "da_cat_wm": d["da_cat_wm"],
                "kich_thuoc": d["kich"],
                "da_dung": [ma] if d["hang"] == "len_hinh" else [],
                "luc_nhap": luc}, ensure_ascii=False) + "\n")
    json.dump(vt, open(VT, "w"))
    json.dump(vt_loi, open(VT_LOI, "w"))
    n_lh = sum(1 for d in ds_moi if d["hang"] == "len_hinh")
    print(f"{ma}: +{len(ds_moi)} vào kho ({n_lh} lên hình, {len(ds_moi) - n_lh} dự trữ)"
          f" · bỏ {bo}")
    return len(ds_moi)


def bo_nhan(me=15):
    """Bổ nhãn cho các dòng nhan_tho (mắt máy nghẽn lúc nhập — vd chạy từ shell phiên
    Claude thì claude CLI lồng nhau bị EPERM; đường launchd thì chạy được)."""
    can = [d for d in _doc_so() if d.get("nhan_tho")]
    # --phan i/n: chia dải để CHẠY SONG SONG nhiều máy (10/08 — vòng chi tiết ~4
    # phút/mẻ, một máy mất 2,5 giờ; 3 máy còn ~50 phút). Sổ ghi có KHOÁ FILE.
    phan = next((a for a in sys.argv if re.match(r"^\d+/\d+$", a)), None)
    if phan:
        i_p, n_p = (int(x) for x in phan.split("/"))
        can = can[i_p::n_p]
    if not can:
        print("không còn nhãn thô nào")
        return
    for i in range(0, len(can), me):
        cum = can[i:i + me]
        ds = [{"tep_tam": os.path.join(KHO, d["tep"]), "moi":
               " | ".join([d.get("mo_ta", ""), " ".join(d.get("nhan", [])[:3])])}
              for d in cum]
        nhan = _nhan_may(ds, KHO)
        # KHOÁ FILE quanh đọc-merge-ghi: nhiều máy song song + anh sửa tay trên trang
        # duyệt — nguoi_sua là chân lý, máy không đè; không khoá là giẫm sổ nhau
        with NT.khoa_ghi(SO) as khoa:
            so = _doc_so()
            theo_tep = {d["tep"]: d for d in so}
            bo_duoc = 0
            for d in cum:
                m = theo_tep.get(d["tep"])
                n = nhan.get(d["tep"]) or {}
                if m is None or m.get("nguoi_sua") or not m.get("nhan_tho") or not n:
                    continue
                m["nhan"] = _khu_trung_nhan(n.get("nhan") or [])
                m["chu_the"] = _chuan_hoa_ct(_nfc(n.get("chu_the", "")))
                m["mo_ta"] = _nfc(n.get("mo_ta", ""))
                m["nhan_tho"] = False
                # ảnh extension tải tay chờ nhãn — mắt máy đã nhìn là nhập kho chính thức
                m.pop("cho_nhan", None)
                bo_duoc += 1
            with open(SO, "w", encoding="utf-8") as f:
                for d in so:
                    f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print(f"  mẻ {i // me + 1}{'(' + phan + ')' if phan else ''}: "
              f"bổ {bo_duoc}/{len(cum)}", flush=True)
    so = _doc_so()
    con = sum(1 for d in so if d.get("nhan_tho"))
    print(f"— còn nhãn thô: {con}/{len(so)}")
    if con == 0:                                   # máy CUỐI CÙNG xong mới đắp năm
        dap_nam_su_kien()


def dap_nam_su_kien():
    """Đắp nhãn NĂM + SỰ KIỆN từ ngữ cảnh bài — chạy Ở CUỐI vòng bổ nhãn (chạy song
    song là bị vòng đè mất, dò 10/08). Code thuần, chạy lại bao nhiêu lần cũng được."""
    MAU_GIAI = ["asean cup 2026", "aff cup", "asean championship", "sea games",
                "vong loai world cup", "vong loai asian cup", "v league"]
    cache = {}

    def su_kien(ma_b):
        if ma_b not in cache:
            ra = []
            try:
                kb = json.load(open(os.path.join(DD.VIEC, ma_b, "kich-ban.json"),
                                    encoding="utf-8"))
                chuoi = _bo_dau_nk(kb.get("tieu_de", "")
                                   + " " + " ".join(kb.get("tu_khoa", [])))
                ra = [g for g in MAU_GIAI if _bo_dau_nk(g) in chuoi][:1]
            except Exception:
                pass
            cache[ma_b] = ra
        return cache[ma_b]

    so = _doc_so()
    them = 0
    for m in so:
        nb = m.get("nguon_bai", "")
        co = [_bo_dau_nk(x) for x in m.get("nhan", [])]
        nam = nb[:4] if re.match(r"20\d\d", nb) else ""
        if nam and not any(nam in c for c in co):
            m.setdefault("nhan", []).append(nam)
            them += 1
        for g in su_kien(nb):
            if not any(_bo_dau_nk(g.split()[0]) in c for c in co):
                m.setdefault("nhan", []).append(g)
                break
    with open(SO, "w", encoding="utf-8") as f:
        for m in so:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    print(f"— đắp năm/sự kiện: +{them} nhãn năm")


def soat(me=8):
    """MÁY TỰ SOÁT + TỰ CHỮA toàn kho (anh đặt 10/08: một số nhãn sai hẳn, không thể
    sửa từng tấm). Model TO (sonnet, đặt qua KHO_MODEL) nhìn từng tấm kèm nhãn hiện
    tại: đúng → 'ok', sai → VIẾT LẠI. Tấm anh đã duyệt nội dung tay (nguoi_duyet) miễn soát.

    CHỈ QUÉT CÁI CẦN (anh chốt 14/08): tấm đã qua mắt bậc BẰNG hoặc CAO HƠN mắt
    đang chạy thì bỏ qua — chạy lại lệnh này mười lần cũng không đốt thêm token.
    Muốn ép soát lại tất thì thêm cờ `--lai` trên dòng lệnh.
    """
    bac = _bac_model()
    lai = "--lai" in sys.argv
    so_het = _doc_so()
    # MIỄN SOÁT theo cờ DUYỆT NỘI DUNG, không theo cờ "có chạm vào" (anh bắt 14/08):
    # `nguoi_sua` bật cả khi gắn nhãn hàng loạt — anh thêm một nhãn chung cho cụm
    # chứ chưa đọc mô tả từng tấm, mà 746/986 tấm vì thế thoát vòng soát vĩnh viễn.
    xet = [d for d in so_het if not d.get("nguoi_duyet") and not d.get("nhan_tho")]
    can = [d for d in xet if lai or _bac_da_soat(d) < bac]
    # TẦNG HAI (anh chốt phương án 2 tầng 12/08): mắt tinh KHÔNG quét lại cả kho —
    # chỉ dặm những tấm mắt tầng dưới tự nhận là chưa chắc. Không có cửa này thì
    # chạy opus là quét trọn 986 tấm, đắt gấp mấy lần mà phần lớn chẳng chữa được gì.
    if "--chua-chac" in sys.argv:
        can = [d for d in can if d.get("soat_chac") in ("vua", "thap")]
    # ── ƯU TIÊN THEO NỘI DUNG: --loc "việt nam,thái lan" (anh đặt 20/08) ─────────
    # Kho lớn dần, quét trọn một lượt là tốn và lâu. Anh làm bài về tuyển Việt Nam và
    # Thái Lan gần như hằng ngày, nên nhãn của hai nhóm ấy đáng đúng trước. So chuỗi
    # BỎ DẤU để "viet nam" cũng bắt được "Tuyển Việt Nam"; soi cả chủ thể, nhãn, mô tả
    # lẫn TÊN BÀI (tên tệp mang mã bài, thường lộ rõ trận nào).
    loc = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--loc=")), "")
    if loc:
        cum = [_bo_dau_nk(x.strip()) for x in loc.split(",") if x.strip()]

        def _hop(d):
            kho = _bo_dau_nk(" ".join([
                str(d.get("chu_the") or ""), " ".join(d.get("nhan") or []),
                str(d.get("mo_ta") or ""), str(d.get("tep") or "")]))
            return any(c in kho for c in cum)

        truoc = len(can)
        uu = [d for d in can if _hop(d)]
        con = [d for d in can if not _hop(d)]
        can = uu + con          # hợp lọc lên ĐẦU, phần còn lại vẫn giữ để --so cắt
        print(f"  ưu tiên {len(uu)}/{truoc} tấm khớp: {loc}")

    # ── GIỚI HẠN SỐ TẤM: --so=200 ────────────────────────────────────────────────
    # Anh ra số lượng cụ thể thì làm đúng số ấy — biết trước tốn bao nhiêu, dừng ở đâu.
    so_ep = next((int(a.split("=", 1)[1]) for a in sys.argv
                  if a.startswith("--so=") and a.split("=", 1)[1].isdigit()), 0)
    if so_ep:
        can = can[:so_ep]

    phan = next((a for a in sys.argv if re.match(r"^\d+/\d+$", a)), None)
    if phan:
        i_p, n_p = (int(x) for x in phan.split("/"))
        can = can[i_p::n_p]
    ten_bac = next((k for k, v in BAC_MODEL.items() if v == bac), "?")
    print(f"mắt {ten_bac} (bậc {bac}) · kho {len(so_het)} tấm · "
          f"bỏ qua {len(xet) - len(can)} tấm đã qua mắt bằng/cao hơn"
          + (" · ÉP SOÁT LẠI TẤT" if lai else ""))
    print(f"soát {len(can)} tấm, mẻ {me}")
    if not can:
        print("  — không tấm nào cần soát, dừng (không tốn token)")
        return
    for i in range(0, len(can), me):
        cum = can[i:i + me]
        dong = "\n".join(
            f"- {gap_anh.ban_nho(os.path.join(KHO, d['tep']))}\n"
            f"  nhãn hiện tại: {d.get('chu_the', '')} | {', '.join(d.get('nhan', [])[:8])}"
            f" | {d.get('mo_ta', '')[:100]}"
            for d in cum)
        lenh = (
            "Em là giám khảo nhãn ảnh bóng đá. Với TỪNG ảnh dưới đây: dùng tool Read "
            "mở ảnh, ĐỐI CHIẾU nhãn hiện tại với cái nhìn thấy.\n"
            "BIẾT TRƯỚC: phần TÊN CHỦ THỂ và một số NHÃN là do người chủ kho tự đặt tay "
            "— coi là ĐÚNG, đừng bỏ. Phần MÔ TẢ thì chưa ai duyệt, sai nhiều, cứ viết "
            "lại thẳng tay. Nhãn hiện có thường THIẾU chứ không sai: hãy THÊM cho đủ "
            "các lớp (hành động, áo đấu, bối cảnh, chữ trong hình, cảm xúc) thay vì "
            "thay thế. Chỉ khi mắt em thấy tên chủ thể MÂU THUẪN hẳn với ảnh thì mới "
            "ghi tên em đọc được vào khoá chu_the — máy sẽ đánh dấu cho người soi lại "
            "chứ không tự sửa.\n"
            f"{dong}\n\n"
            "Trả về DUY NHẤT một khối JSON, khoá là TÊN TỆP (basename):\n"
            '· nhãn ĐÚNG với ảnh → giá trị là chuỗi "ok"\n'
            "· nhãn SAI/lệch nhiều → giá trị là nhãn MỚI: "
            '{"nhan": [6-12 nhãn chi tiết: hành động, đội+màu áo+số áo, bối cảnh, chữ '
            'to trong hình, cảm xúc], "mo_ta": "một câu tả đúng ảnh", '
            '"chu_the": "tên CHẮC CHẮN hoặc rỗng", "chac": "cao|vua|thap"}\n'
            "Nghi ngờ tên người thì chu_the RỖNG — cấm đoán bừa.\n"
            'Khoá "chac" là em tự chấm MÌNH: "cao" = nhìn rõ, nhãn chắc chắn đúng; '
            '"vua" = nhãn đúng nhưng có mặt người mà em không dám gọi tên; '
            '"thap" = ảnh mờ/khuất/khó đoán, nên để mắt tinh hơn nhìn lại. '
            'Ảnh nào chỉ cần trả "ok" thì thêm dòng riêng "<tên tệp>#chac": "cao|vua|thap".'
        )
        try:
            r = subprocess.run([NT.tim_claude(), "-p",
                                "--model", os.environ.get("KHO_MODEL",
                                                          "claude-sonnet-5"),
                                "--allowedTools", "Read"],
                               input=lenh, capture_output=True, text=True, timeout=900)
            m = re.search(r"\{.*\}", r.stdout, re.S)
            kq = json.loads(m.group(0)) if m else {}
        except Exception as e:
            print(f"  ⚠ mẻ nghẽn ({e})")
            continue
        with NT.khoa_ghi(SO) as khoa:
            so = _doc_so()
            theo = {d["tep"]: d for d in so}
            sua = 0
            for d in cum:
                v = kq.get(d["tep"])
                m0 = theo.get(d["tep"])
                if m0 is None or m0.get("nguoi_duyet") or v is None:
                    continue
                # GIỮ BẢN CŨ trước khi đè — anh có thể đã tự tay thêm nhãn đúng cho
                # tấm này qua lượt gắn hàng loạt. Mắt máy sai thì còn đường lùi.
                if isinstance(v, dict) and "nhan_truoc_soat" not in m0:
                    m0["nhan_truoc_soat"] = {"nhan": list(m0.get("nhan", [])),
                                             "mo_ta": m0.get("mo_ta", ""),
                                             "chu_the": m0.get("chu_the", "")}
                # DẤU MẮT MÁY (14/08): nhớ mắt nào nhìn, nhìn lúc nào, tự chấm chắc
                # tới đâu — để lượt sau chỉ đụng tấm chưa ai nhìn hoặc mắt yếu nhìn.
                m0["da_soat"] = True                      # giữ cho bản cũ khỏi gãy
                m0["soat_model"] = ten_bac
                m0["soat_luc"] = datetime.now().isoformat(timespec="seconds")
                chac = (v.get("chac") if isinstance(v, dict) else None) \
                    or kq.get(d["tep"] + "#chac") or "cao"
                m0["soat_chac"] = chac if chac in ("cao", "vua", "thap") else "cao"
                if isinstance(v, dict):
                    # ── BA MỨC TIN, KHÔNG ĐỐI XỬ NHƯ NHAU (anh nói rõ 14/08) ──
                    # Trên tấm anh đã chạm: anh CHỈ đặt chủ thể và THÊM nhãn, KHÔNG
                    # đụng mô tả. Nên:
                    #   · chu_the anh đặt = CHÂN LÝ — máy không được xoá, chỉ được điền
                    #     vào chỗ còn trống. (Lượt 10:15 chưa có luật này đã xoá mất 19
                    #     cái tên quý: Kim Sang-sik, Xuân Son, Đình Bắc, sân Bukit Jalil…)
                    #   · nhan anh thêm = ĐÚNG NHƯNG CHƯA ĐỦ — máy BỔ SUNG, không thay.
                    #   · mo_ta = anh chưa duyệt bao giờ — máy viết lại tự do.
                    nguoi_cham = m0.get("nguoi_sua")
                    nh_may = [x for x in (v.get("nhan") or []) if str(x).strip()]
                    m0["nhan"] = _khu_trung(
                        (list(m0.get("nhan", [])) + nh_may) if nguoi_cham
                        else (nh_may or m0.get("nhan", [])))
                    m0["mo_ta"] = _nfc(v.get("mo_ta", "")) or m0.get("mo_ta", "")
                    ct_may = _chuan_hoa_ct(_nfc(v.get("chu_the", "")))
                    ct_cu = m0.get("chu_the", "")
                    if nguoi_cham and ct_cu:
                        # máy nhìn ra tên KHÁC hẳn → không tự sửa, ĐÁNH DẤU để anh soi
                        if ct_may and _bo_dau_nk(ct_may) != _bo_dau_nk(ct_cu):
                            m0["soat_nghi"] = f"mắt máy đọc ra: {ct_may}"
                    else:
                        m0["chu_the"] = ct_may
                    # chủ thể phải có mặt trong nhãn thì cửa tra kho mới bắt được
                    ct = m0.get("chu_the")
                    if ct and _bo_dau_nk(ct) not in {_bo_dau_nk(x) for x in m0["nhan"]}:
                        m0["nhan"] = _khu_trung([ct] + m0["nhan"])
                    sua += 1
            with open(SO, "w", encoding="utf-8") as f:
                for d in so:
                    f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print(f"  mẻ {i // me + 1}{'(' + phan + ')' if phan else ''}: "
              f"chữa {sua}/{len(cum)}", flush=True)
    dap_nam_su_kien()


# alias dùng chung tên hàm khử trùng (soat dùng _khu_trung như kho video)
_khu_trung = _khu_trung_nhan


def tinh_hinh():
    """Kho đã được mắt nào nhìn tới đâu — CODE THUẦN, không tốn một token nào.

    Anh xem cái này để biết còn phải quét bao nhiêu, và lượt sau nên chạy mắt gì.
    """
    so = _doc_so()
    xet = [d for d in so if not d.get("nguoi_duyet") and not d.get("nhan_tho")]
    from collections import Counter
    mat = Counter(d.get("soat_model") or ("cũ (không rõ mắt)" if d.get("da_soat")
                                          else "CHƯA AI NHÌN") for d in xet)
    chac = Counter(d.get("soat_chac", "—") for d in xet if d.get("soat_model"))
    print(f"KHO {len(so)} tấm · {len(so) - len(xet)} tấm miễn soát "
          f"(anh đã DUYỆT NỘI DUNG tay — gắn nhãn hàng loạt KHÔNG tính)\n")
    print("  đã qua mắt:")
    for k, v in mat.most_common():
        print(f"    {v:>5} tấm — {k}")
    if chac:
        print("\n  mắt tự chấm độ chắc:")
        for k, v in sorted(chac.items()):
            ghi = {"cao": "nhìn rõ, nhãn chắc", "vua": "có người mà không dám gọi tên",
                   "thap": "ảnh mờ/khuất, nên để mắt tinh nhìn lại"}.get(k, "")
            print(f"    {v:>5} tấm — {k}  {ghi}")
        can_op = sum(v for k, v in chac.items() if k in ("vua", "thap"))
        print(f"\n  → tầng opus sẽ đụng {can_op} tấm "
              f"(lệnh: KHO_MODEL=claude-opus-5 … --soat --chua-chac)")
    for bac_ten, bac_so in (("haiku", 1), ("sonnet", 2), ("opus", 3)):
        con = len([d for d in xet if _bac_da_soat(d) < bac_so])
        print(f"  chạy mắt {bac_ten:<7} bây giờ → quét {con} tấm")


if __name__ == "__main__":
    if "--tinh-hinh" in sys.argv:
        tinh_hinh()
        sys.exit(0)
    if "--soat" in sys.argv:
        soat()
        sys.exit(0)
    if "--bo-nhan" in sys.argv:
        bo_nhan()
        sys.exit(0)
    if "--hoi-to" in sys.argv:
        cac = sorted(glob.glob(os.path.join(DD.VIEC, "*", "video-*")))
    else:
        cac = [DD.tim_viec(x) for x in sys.argv[1:]]
    tong = sum(nhap(v) for v in cac if os.path.isdir(v))
    print(f"— TỔNG: +{tong} ảnh · kho: {KHO}")
