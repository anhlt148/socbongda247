#!/usr/bin/env python3
"""CHỌN NHẠC NỀN THEO CẢM XÚC NỘI DUNG — cầu nối kho 12 nhóm vào xưởng dựng.

VÌ SAO CÓ FILE NÀY (chẩn đoán 12/08/2026):
  `xuong.py` chọn nhạc bằng `kb.get("cung_nhac")`, nhưng KHÔNG AI sinh trường đó —
  kiểm 5/5 blueprint thật đều `cung_nhac = None`, và dict `CUNG_NHAC` trong xuong.py
  là code chết (không ai sinh `giong_tin`). Hệ quả: MỌI video của kênh từ trước tới
  nay đều rơi về đúng một cung `cang_thang` với 3 file. Kho nhạc mới không tự sửa
  được chuyện đó — phải NỐI cửa chọn cảm xúc, và đó là việc của file này.

NGUYÊN TẮC (theo luật kiến trúc hệ Sóc):
  · Não một nguồn — chỉ file này biết cách chọn nhạc; xưởng và trạm cùng gọi.
  · Rẻ trước, model sau — dò cảm xúc bằng LUẬT CỨNG (từ khoá tiếng Việt), 0 token.
    Model chỉ cần khi anh muốn nâng cấp về sau, không bắt buộc.
  · KHÔNG BAO GIỜ để xưởng chết vì nhạc — bốn tầng dự phòng, luôn trả về một file.
  · Trung thực — trả kèm `vi_sao` và `do_chac` để log nói rõ vì sao chọn nhóm đó.
"""
import glob
import json
import os
import random
import re
import unicodedata
from datetime import datetime

import duong_dan as DD

# Kho 12 nhóm (dựng 12/08/2026). Tách khỏi NHAC cũ để KHÔNG phá đường render đang chạy.
KHO_12 = os.path.join(DD.KHO_TAI_NGUYEN, "SOC_BONG_DA_247_MUSIC_LIBRARY")

# ── 12 nhóm cảm xúc + từ khoá dò ─────────────────────────────────────────────
# HAI LUẬT ĐÃ TRẢ GIÁ 12/08/2026, đừng phá:
#  ① Từ khoá viết CÓ DẤU. Bỏ dấu xong tiếng Việt đụng nhau chết người:
#     "khẩn" ↔ "khán giả", "nóng" ↔ "nông" → tin "cảnh báo với CĐV" bị xếp tin-khẩn.
#     (Vẫn có đường bỏ dấu làm DỰ PHÒNG cho nguồn viết không dấu — xem doan_cam_xuc.)
#  ② Từ khoá phải là CẢM XÚC, không phải CHỦ ĐỀ. Bản đầu để "tuyển Việt Nam" trong
#     nhóm PATRIOTIC → nhóm đó nuốt gần hết video vì kênh nào cũng nhắc tuyển VN.
#     Tên đội, tên giải, tên cầu thủ KHÔNG được làm từ khoá cảm xúc.
CUNG_12 = {
    "01_BREAKING_NEWS": [
        "chính thức", "vừa xong", "tin nóng", "khẩn cấp", "thông báo", "xác nhận",
        "mới nhất", "bất ngờ", "vừa được", "công bố", "gấp rút", "ngay lúc này",
    ],
    "02_HYPE_MATCHDAY": [
        "đại chiến", "chung kết", "bán kết", "derby", "đối đầu", "so tài", "quyết đấu",
        "tứ kết", "chạm trán", "trận cầu", "đại tiệc", "nóng bỏng", "rực lửa",
    ],
    "03_EPIC_VICTORY": [
        "vô địch", "chiến thắng", "nâng cúp", "kỷ lục", "ghi bàn", "bàn thắng",
        "thắng đậm", "hạ gục", "lên ngôi", "đăng quang", "vinh danh", "toả sáng",
        "tỏa sáng", "kỳ tích", "vỡ oà", "vỡ òa",
    ],
    "04_TENSION_SUSPENSE": [
        "penalty", "luân lưu", "quyết định", "nguy cơ", "bị loại", "chấn thương",
        "án phạt", "chờ kết quả", "căng não", "nghẹt thở", "sinh tử", "cửa tử",
        "cái dớp", "đáng sợ", "cảnh báo", "thấp thỏm", "hồi hộp",
    ],
    "05_DRAMA_CONFLICT": [
        "tranh cãi", "khẩu chiến", "phát ngôn", "chỉ trích", "mâu thuẫn", "var",
        "trọng tài", "scandal", "cà khịa", "mỉa mai", "đáp trả", "gây sốc", "tố cáo",
        "nói thẳng", "đòi nợ", "thách thức", "bức xúc", "dằn mặt",
    ],
    "06_COMEBACK_HOPE": [
        "trở lại", "hồi sinh", "ngược dòng", "vượt khó", "tái xuất", "bình phục",
        "hy vọng", "lột xác", "vươn lên", "cơ hội", "làm lại", "tin vui",
    ],
    "07_SAD_TRIBUTE": [
        "giải nghệ", "chia tay", "qua đời", "tri ân", "nhìn lại", "khép lại",
        "nước mắt", "bật khóc", "chia buồn", "lời tạm biệt", "tiếc nuối", "ngậm ngùi",
        "dấu chấm hết", "một thời",
    ],
    "08_ANALYSIS_NEUTRAL": [
        "phân tích", "thống kê", "đội hình", "chiến thuật", "so sánh", "giá trị",
        "vì sao", "lý do", "số liệu", "bảng xếp hạng", "chỉ số", "đánh giá",
        "dữ liệu", "sự thật", "thực hư",
    ],
    "09_MYSTERY_RUMOR": [
        "tin đồn", "chưa xác nhận", "bí ẩn", "được cho là", "nghi vấn", "đồn đoán",
        "úp mở", "bí mật", "âm thầm", "chưa rõ", "theo nguồn tin", "hé lộ",
        "đằng sau", "ít ai biết",
    ],
    "10_FUN_LIGHT": [
        "hài hước", "hậu trường", "trêu", "buồn cười", "khoảnh khắc vui", "lầy",
        "chế ảnh", "vui nhộn", "đố vui", "bá đạo", "tấu hài", "cười ra nước mắt",
    ],
    "11_PATRIOTIC_EPIC": [
        "tự hào", "cờ đỏ sao vàng", "quốc ca", "vinh quang", "rạng danh", "nức lòng",
        "cả nước", "triệu con tim", "niềm tự hào", "làm rạng rỡ", "cờ tổ quốc",
        "màu cờ sắc áo", "hào hùng",
    ],
    "12_TRANSFER_NEWS": [
        "chuyển nhượng", "here we go", "gia nhập", "ký hợp đồng", "bom tấn",
        "cập bến", "mức phí", "triệu euro", "bản hợp đồng", "chiêu mộ", "gia hạn",
        "rời clb", "hét giá", "phá vỡ hợp đồng",
    ],
}

# 7 cung CŨ (kho nhac/ mà xuong.py đang đọc) → nhóm mới. Giữ để blueprint cũ vẫn chạy.
MAP_CUNG_CU = {
    "mo_dau": "01_BREAKING_NEWS", "cang_thang": "04_TENSION_SUSPENSE",
    "cao_trao": "03_EPIC_VICTORY", "bi_trang": "07_SAD_TRIBUTE",
    "tu_su": "08_ANALYSIS_NEUTRAL", "chien_thang": "11_PATRIOTIC_EPIC",
    "hoi_hop": "09_MYSTERY_RUMOR",
}

# Nhóm rỗng thì mượn nhóm GẦN NGHĨA nhất — không nhảy bừa sang cảm xúc trái ngược.
HANG_XOM = {
    "01_BREAKING_NEWS": ["12_TRANSFER_NEWS", "02_HYPE_MATCHDAY", "08_ANALYSIS_NEUTRAL"],
    "02_HYPE_MATCHDAY": ["03_EPIC_VICTORY", "11_PATRIOTIC_EPIC", "01_BREAKING_NEWS"],
    "03_EPIC_VICTORY": ["11_PATRIOTIC_EPIC", "02_HYPE_MATCHDAY", "06_COMEBACK_HOPE"],
    "04_TENSION_SUSPENSE": ["09_MYSTERY_RUMOR", "05_DRAMA_CONFLICT", "02_HYPE_MATCHDAY"],
    "05_DRAMA_CONFLICT": ["04_TENSION_SUSPENSE", "09_MYSTERY_RUMOR", "01_BREAKING_NEWS"],
    "06_COMEBACK_HOPE": ["03_EPIC_VICTORY", "11_PATRIOTIC_EPIC", "02_HYPE_MATCHDAY"],
    "07_SAD_TRIBUTE": ["08_ANALYSIS_NEUTRAL", "06_COMEBACK_HOPE", "09_MYSTERY_RUMOR"],
    "08_ANALYSIS_NEUTRAL": ["12_TRANSFER_NEWS", "09_MYSTERY_RUMOR", "01_BREAKING_NEWS"],
    "09_MYSTERY_RUMOR": ["04_TENSION_SUSPENSE", "08_ANALYSIS_NEUTRAL", "12_TRANSFER_NEWS"],
    "10_FUN_LIGHT": ["01_BREAKING_NEWS", "08_ANALYSIS_NEUTRAL", "12_TRANSFER_NEWS"],
    "11_PATRIOTIC_EPIC": ["03_EPIC_VICTORY", "02_HYPE_MATCHDAY", "06_COMEBACK_HOPE"],
    "12_TRANSFER_NEWS": ["01_BREAKING_NEWS", "09_MYSTERY_RUMOR", "08_ANALYSIS_NEUTRAL"],
}

MAC_DINH = "01_BREAKING_NEWS"     # kênh tin bóng đá — trung tính nhất khi không đoán được


def _khong_dau(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("đ", "d"))


def _quet(chuoi_td, chuoi_lb, bo_dau):
    diem, trung = {}, {}
    for nhom, tu_khoa in CUNG_12.items():
        d, hit = 0, []
        for tk in tu_khoa:
            k = _khong_dau(tk) if bo_dau else tk
            # KHỚP THEO RANH GIỚI TỪ. Bẫy 12/08: "lay" lọt trong "ma-LAY-sia" →
            # tin đại chiến bị xếp nhóm HÀI. Khớp chuỗi trần là cấm.
            mau = r"(?<![\w])" + re.escape(k) + r"(?![\w])"
            if re.search(mau, chuoi_td):
                d += 3
                hit.append(tk)
            elif re.search(mau, chuoi_lb):
                d += 1
                hit.append(tk)
        if d:
            diem[nhom], trung[nhom] = d, hit
    return diem, trung


def doan_cam_xuc(tieu_de, loi_binh=""):
    """Dò nhóm cảm xúc bằng LUẬT CỨNG. Trả (nhom, do_chac, vi_sao).

    Quét hai lượt: CÓ DẤU trước (chính xác), không ra gì mới quét bản bỏ dấu
    (dự phòng cho nguồn tin viết không dấu). Tiêu đề nặng gấp 3 lời bình.
    do_chac: 'cao' · 'vua' · 'thap'.
    """
    td, lb = (tieu_de or "").lower(), (loi_binh or "").lower()
    diem, trung = _quet(td, lb, False)
    nguon = "có dấu"
    if not diem:
        diem, trung = _quet(_khong_dau(td), _khong_dau(lb), True)
        nguon = "không dấu"
    if not diem:
        return MAC_DINH, "thap", "không thấy từ khoá cảm xúc nào — dùng nhóm mặc định"
    xep = sorted(diem.items(), key=lambda x: -x[1])
    nhom, d1 = xep[0]
    d2 = xep[1][1] if len(xep) > 1 else 0
    chac = "cao" if d1 >= d2 * 2 and d1 >= 3 else ("vua" if d1 > d2 else "thap")
    return nhom, chac, f"khớp {', '.join(trung[nhom][:3])} ({d1}đ, {nguon})"


def _bai_trong(nhom):
    return sorted(glob.glob(os.path.join(KHO_12, nhom, "*.mp3")))


# ── SỔ NHẠC ĐÃ DÙNG (anh đặt 12/08: "giờ kho nhiều bài rồi, chọn ngẫu nhiên") ──
# Ngẫu nhiên thuần vẫn lặp: đo trên 30 video gần nhất, ngày 10/08 có hai video ăn
# cùng một bài TENSION. Kênh chạy 10 video/ngày, người xem lướt liên tiếp là nghe
# lại ngay — nên phải NHỚ bài nào vừa dùng, đúng như luật "ảnh ít dùng gần đây"
# của kho ảnh. Sổ nằm cạnh kho nhạc, một dòng JSON mỗi lần chọn.
SO_NHAC = os.path.join(KHO_12, "nhac-da-dung.jsonl")


def _doc_so_nhac():
    """[(bài, mã việc)] theo thứ tự dùng, cũ → mới."""
    ra = []
    try:
        for d in open(SO_NHAC, encoding="utf-8"):
            d = d.strip()
            if not d:
                continue
            try:
                m = json.loads(d)
                ra.append((m.get("bai", ""), m.get("viec", "")))
            except Exception:
                pass
    except OSError:
        pass
    return ra


def _ghi_so_nhac(bai, viec, nhom):
    try:
        os.makedirs(os.path.dirname(SO_NHAC), exist_ok=True)
        with open(SO_NHAC, "a", encoding="utf-8") as f:
            f.write(json.dumps({"bai": os.path.basename(bai), "viec": viec,
                                "nhom": nhom,
                                "luc": datetime.now().strftime("%Y-%m-%d %H:%M")},
                               ensure_ascii=False) + "\n")
    except OSError:
        pass


def _chon_it_lap(ds, rn, viec, nhom, ghi=True):
    """Chọn trong `ds` sao cho ÍT LẶP nhất, mà DỰNG LẠI vẫn ra đúng bài cũ.

    ① Bài này đã dựng rồi (có trong sổ) → trả LẠI đúng bài nhạc lần trước. Dựng lại
       để sửa một cảnh mà nhạc đổi là hỏng cả cảm giác đã duyệt.
    ② Chưa dựng → bỏ những bài vừa dùng gần đây, ngẫu nhiên trong phần còn lại.
       Hết bài mới thì lấy trong nhóm LÂU CHƯA DÙNG NHẤT — không bao giờ bí.
    """
    so = _doc_so_nhac()
    if viec:
        ten_v = os.path.basename(viec.rstrip("/"))
        for bai, v in reversed(so):                # lần dùng GẦN NHẤT của chính bài này
            if v and os.path.basename(v.rstrip("/")) == ten_v:
                cu = [p for p in ds if os.path.basename(p) == bai]
                if cu:
                    return cu[0], " · giữ nhạc lần dựng trước"
    # thứ tự dùng gần đây: bài xuất hiện càng muộn trong sổ càng "nóng"
    lan_cuoi = {}
    for i, (bai, _v) in enumerate(so):
        lan_cuoi[bai] = i
    chua = [p for p in ds if os.path.basename(p) not in lan_cuoi]
    if chua:
        chon_p = rn.choice(chua)
        ghi and _ghi_so_nhac(chon_p, viec, nhom)
        return chon_p, f" · bài MỚI ({len(chua)}/{len(ds)} chưa dùng)"
    # tất cả đã dùng → lấy trong nửa LÂU NHẤT, rồi mới ngẫu nhiên (đỡ đoán trước được)
    xep = sorted(ds, key=lambda p: lan_cuoi.get(os.path.basename(p), -1))
    cu_nhat = xep[:max(1, len(xep) // 2)]
    chon_p = rn.choice(cu_nhat)
    ghi and _ghi_so_nhac(chon_p, viec, nhom)
    return chon_p, " · lâu chưa dùng nhất"


def kiem_kho():
    """Soi kho: trả (ok, dòng báo cáo). Dùng cho kiem_tram.py và chạy tay."""
    if not os.path.isdir(KHO_12):
        return False, [f"✗ KHÔNG THẤY kho 12 nhóm: {KHO_12}"]
    dong, ok = [], True
    for nhom in CUNG_12:
        ds = _bai_trong(nhom)
        hong = [p for p in ds if not os.path.exists(p) or os.path.getsize(p) < 10240]
        if not ds:
            ok = False
            dong.append(f"✗ {nhom}: RỖNG")
        elif hong:
            ok = False
            dong.append(f"✗ {nhom}: {len(hong)} file hỏng/rỗng")
        else:
            dong.append(f"✓ {nhom}: {len(ds)} bài")
    return ok, dong


def chon(kb, viec=""):
    """Chọn một file nhạc cho bài. Trả (duong_dan, nhom, vi_sao). KHÔNG BAO GIỜ trả None.

    Thứ tự ưu tiên:
      ① blueprint khai thẳng `nhom_nhac` (anh chốt tay trên trạm)
      ② blueprint có `cung_nhac` cũ → quy sang nhóm mới (tương thích ngược)
      ③ tự dò từ tiêu đề + lời bình
    Rồi bốn tầng dự phòng để xưởng không bao giờ chết vì thiếu nhạc.
    """
    kb = kb or {}
    nhom = (kb.get("nhom_nhac") or "").strip()
    if nhom in CUNG_12:
        vi_sao = "anh chốt tay trong blueprint"
        chac = "cao"
    else:
        cu = (kb.get("cung_nhac") or "").strip()
        if cu in MAP_CUNG_CU:
            nhom, chac = MAP_CUNG_CU[cu], "cao"
            vi_sao = f"quy từ cung cũ '{cu}'"
        else:
            loi = kb.get("loi_binh") or ""
            if isinstance(loi, list):
                loi = " ".join(str(x.get("cau", x) if isinstance(x, dict) else x) for x in loi)
            nhom, chac, vi_sao = doan_cam_xuc(kb.get("tieu_de") or "", loi)

    rn = random.Random(f"{viec}|{nhom}")           # cùng bài → cùng nhạc, dựng lại không đổi

    # ① đúng nhóm
    ds = _bai_trong(nhom)
    if ds:
        bai, ghi_chu = _chon_it_lap(ds, rn, viec, nhom)
        return bai, nhom, f"{vi_sao} · chắc {chac}{ghi_chu}"

    # ② hàng xóm gần nghĩa
    for hx in HANG_XOM.get(nhom, []):
        ds = _bai_trong(hx)
        if ds:
            bai, ghi_chu = _chon_it_lap(ds, rn, viec, hx)
            return bai, hx, f"{vi_sao} · nhóm {nhom} RỖNG → mượn {hx}{ghi_chu}"

    # ③ bất kỳ bài nào trong kho mới
    ds = sorted(glob.glob(os.path.join(KHO_12, "*", "*.mp3")))
    if ds:
        bai, ghi_chu = _chon_it_lap(ds, rn, viec, "?")
        return bai, "?", f"{vi_sao} · kho nhóm hỏng → lấy bừa trong kho 12{ghi_chu}"

    # ④ kho CŨ 7 cung — lưới đỡ cuối, để dây chuyền không đứng
    ds = sorted(glob.glob(os.path.join(DD.NHAC, "*", "*.mp3")))
    if ds:
        return rn.choice(ds), "kho-cu", f"{vi_sao} · KHO 12 KHÔNG DÙNG ĐƯỢC → rơi về kho cũ"

    raise RuntimeError(f"Không có bài nhạc nào dùng được. Kho 12: {KHO_12} · kho cũ: {DD.NHAC}")


if __name__ == "__main__":
    ok, dong = kiem_kho()
    print("\n".join(dong))
    print(("✅ kho nhạc 12 nhóm ĐẠT" if ok else "⚠️ kho nhạc có vấn đề") + "\n")
    for td in ["MALAYSIA KHÔNG THỂ DÙNG CHẢO LỬA BUKIT JALIL",
               "HLV CAMPUCHIA NÓI THẲNG VỀ VIỆT NAM, DỰ ĐOÁN THẦY TRÒ KIM SANG-SIK",
               "CHÍNH THỨC: ĐÌNH BẮC GIA NHẬP CLB MỚI VỚI MỨC PHÍ KỶ LỤC",
               "NƯỚC MẮT NGÀY CHIA TAY: TIỀN VỆ TUYỂN VIỆT NAM GIẢI NGHỆ",
               "TIN ĐỒN: HLV BÍ ẨN SẮP DẪN DẮT TUYỂN THÁI LAN",
               "PHÂN TÍCH: VÌ SAO ĐỘI HÌNH NÀY KHIẾN MALAYSIA ĐAU ĐẦU"]:
        p, nhom, vs = chon({"tieu_de": td}, "thu")
        print(f"  {nhom:<22}{os.path.basename(p)[:44]:<46}| {vs}")
        print(f"    ↳ {td[:60]}")
