#!/usr/bin/env python3
"""GỢI Ý TỪ KHOÁ + GHI CHÚ CẢNH cho từng câu — trạm phải mở ra là có sẵn, không bắt anh nghĩ.

Anh chốt 05/08: "khi dựng cái này em (Claude) phải gợi ý luôn từ khoá từng cảnh cho anh."
Bắt người ngồi nghĩ từ khoá cho 26 câu thì trạm chẳng đỡ được gì.

Hai tầng, theo luật "code trước, model sau":
  ① MODEL (chính) — MỘT lần gọi `claude -p` bằng **haiku** cho CẢ kịch bản (không phải mỗi
     câu một lần). Việc này là việc dễ: đọc câu, rút tên riêng, ghép từ khoá — haiku thừa sức,
     dùng model cao là đốt token vô ích.
  ② MẸO (dự phòng) — không có mạng / `claude` lỗi thì rút tên riêng bằng mã, ghép với "neo"
     của video. Kém hơn nhưng vẫn hơn ô trống.

Điều quan trọng nhất trong lời dặn model: **từ khoá phải có TÊN RIÊNG**. Máy không soi được
số áo — số 18 áo trắng là Hai Long chứ không phải Việt Anh — nên từ khoá kiểu "cầu thủ tranh
chấp" chỉ moi về ảnh người khác. Đó là lỗi đã làm hỏng hai mẻ video.

Chạy tay:  python3 goi_y.py ~/socbongda247/viec/<mã>
"""
import json
import os
import re
import subprocess
import unicodedata
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import duong_dan as DD                              # noqa: E402 — phép tách câu dùng chung

CLAUDE = os.path.expanduser("~/.local/bin/claude")
# Nâng haiku → SONNET (anh chốt 06/08 tối): từ khoá haiku gợi chưa trúng, anh phải tự gõ
# tìm lại nhiều — mất thời gian người, đắt hơn nhiều so với chênh giá model. Chọn từ khoá
# trúng đòi hỏi hình dung ẢNH NÀO TỒN TẠI cho tin này — việc VỪA, không phải việc dễ.
MODEL = "claude-sonnet-5"
HAN_GIO = 180

LOI_DAN = """Bạn là người đi tìm ảnh cho báo thể thao đã mười năm. Việc của bạn: đọc lời bình
rồi viết CÂU LỆNH TÌM ẢNH cho từng câu — thứ gõ vào Google ảnh là ra đúng tấm cần, không phải
thứ nghe cho hay.

Video: "{tieu_de}"
Tin gốc: {tin_goc}
Từ khoá cả video: {tu_khoa_kb}

════ NGHỀ TÌM ẢNH — SÁU LUẬT, THEO THỨ TỰ QUAN TRỌNG ════

**1. NEO NGÀNH — luật sống còn.** Mỗi từ khoá BẮT BUỘC có ít nhất một từ chỉ rõ đây là bóng đá:
   *bóng đá · cầu thủ · trận đấu · tuyển · ghi bàn · sân vận động · HLV · thủ môn* hoặc tên giải.
   Thiếu neo là Google hiểu sang chuyện khác ngay.
   ✗ "việt nam campuchia"      → ra ảnh du lịch, biên giới, chính trị, ẩm thực
   ✓ "tuyển việt nam campuchia bóng đá asean cup"
   ✗ "hà nội"                  → ra ảnh phố phường
   ✓ "câu lạc bộ hà nội fc cầu thủ"

**2. TÊN RIÊNG ĐẦY ĐỦ, không gọi tắt.** Google phân biệt rất kém tên ngắn.
   ✗ "việt anh"          → ra hàng chục người trùng tên
   ✓ "bùi hoàng việt anh trung vệ"
   Câu nào nói về MỘT người thì tên người đó đứng ĐẦU từ khoá.

**3. TẢ CẢNH BẰNG DANH TỪ NHÌN THẤY ĐƯỢC**, đừng tả cảm xúc hay diễn biến.
   Google tìm theo cái MẮT THẤY trong ảnh, không theo chuyện xảy ra.
   ✗ "việt anh bản lĩnh thép"   → không có khái niệm này trong ảnh
   ✓ "bùi hoàng việt anh băng quấn đầu thi đấu"
   Kho danh từ dùng được: *ăn mừng · giơ tay · ôm nhau · cúi mặt · khóc · tranh chấp trên không ·
   đánh đầu · sút bóng · cản phá · thẻ đỏ · băng quấn đầu · máu · nằm sân · bắt tay · giơ cúp ·
   khán đài · họp báo · đường hầm · băng ghế dự bị*

**4. THÊM MỐC GIẢI ĐẤU / NĂM** khi câu nói về một trận cụ thể — cắt sạch ảnh của mùa khác.
   ✓ "việt nam indonesia asean cup 2026 vòng bảng"

**5. BỐN ĐẾN BẢY TỪ, TOÀN DANH TỪ.** Không viết thành câu, không dấu ngoặc kép, không dấu cộng.
   ✗ "việt anh vẫn không chịu rời sân dù chảy máu"   → Google loãng ra
   ✓ "bùi hoàng việt anh chảy máu mặt trận indonesia"

**6. HAI GÓC KHÁC NHAU.** Cho mỗi câu hai câu lệnh:
   · `tu_khoa`   — bám sát nội dung câu nhất
   · `tu_khoa_2` — góc KHÁC HẲN để dự phòng: nếu góc một là cận cảnh người thì góc hai là toàn
     cảnh trận/khán đài, hoặc đổi sang tên đội thay vì tên người.
   Hai câu lệnh giống nhau thì coi như chỉ có một — vô ích.

**6b. CHỌN CỤM DỄ TÌM ĐƯỢC ẢNH THẬT** — luật đắt nhất, rút từ quy chuẩn dự án của anh
   (mục 17) sau khi hai bài liền hỏng vì phạm nó (14/08).
   Từ khoá đúng ngữ pháp mà tra không ra ảnh thì VÔ DỤNG. Internet chỉ có ảnh của người
   NỔI TIẾNG. Cầu thủ trẻ, cầu thủ hạng dưới, cầu thủ giải bán chuyên, cầu thủ Việt kiều
   chưa lên tuyển — thế giới KHÔNG có ảnh riêng của họ.
   · Tên có trong DANH SÁCH TÊN ở trên → dùng thoải mái, chắc chắn có ảnh.
   · Tên KHÔNG có trong danh sách đó → **CẤM để đứng một mình**. Phải chuyển sang
     ĐỘI + LỨA + HÀNH ĐỘNG + GIẢI: "U17 Việt Nam tiền đạo tập luyện" chứ đừng
     "Oliver Williams tiền đạo"; "hậu vệ Malaysia phòng ngự ASEAN Cup" chứ đừng
     "Alif Ahmad hậu vệ Malaysia".
   · Ưu tiên thứ có ảnh SẴN NHIỀU: đội tuyển, trận đấu lớn, sân vận động, buổi tập,
     họp báo, khoảnh khắc ăn mừng, khoảnh khắc thất vọng, khán đài.

**6bb. CHỨC DANH CHUNG PHẢI THÀNH NGƯỜI CỤ THỂ + ĐÚNG THỜI ĐIỂM** (anh chốt 14/08).
   "huấn luyện viên đội tuyển Malaysia" là câu lệnh HỎNG: Google trả ảnh đủ mọi đời
   HLV suốt hai chục năm, trong khi tin đang nói về người ĐANG tại vị.
   · Bài hoặc tin gốc có nêu TÊN người ấy → **dùng tên**, đừng dùng chức danh.
   · Không nêu tên → phải neo bằng **giải + năm** trong hồ sơ bài:
     ✓ "Malaysia head coach ASEAN Cup 2026" · ✓ "hlv malaysia asean cup 2026"
     ✗ "huấn luyện viên đội tuyển malaysia"  → không có thời điểm, ra ảnh đời nào cũng có
   · Cùng luật cho mọi thứ đổi theo thời gian: đội hình, áo đấu, sân, ban huấn luyện,
     bảng xếp hạng, chức vô địch. Ảnh cũ ba năm trước trông y hệt ảnh mới — chỉ có
     MỐC THỜI GIAN trong câu lệnh mới lọc được.
   · Bài nói về sự kiện ĐANG diễn ra (xem HỒ SƠ BÀI) → gần như câu nào cũng nên có
     tên giải hoặc năm.

**6c. TRÁNH ẢNH BẨN NGAY TỪ CÂU LỆNH** (quy chuẩn mục 17 của anh).
   Không dùng những cụm kéo về ảnh rác: tên kênh/trang tin, "poster", "thumbnail",
   "highlight", "review", "tổng hợp" — chúng trả về ảnh đầy chữ, logo to giữa hình,
   ảnh ghép nhiều khung. Ảnh dính logo GIỮA khung thì cắt mép không cứu được.

**7. THÊM MỘT CÂU LỆNH TIẾNG ANH** (`tu_khoa_en`) — anh đo thật 14/08: từ khoá tiếng Anh ra
   ảnh ưng ý hơn hẳn. Lý do: ảnh báo chí thể thao chất lượng cao (Getty, AFP, Reuters, các
   báo Anh ngữ) gắn chú thích tiếng Anh; tìm tiếng Việt là chỉ quét được báo Việt.
   · Dùng TÊN QUỐC TẾ chuẩn: "Vietnam national team", "Nguyen Xuan Son", "Kim Sang-sik",
     "My Dinh Stadium", "ASEAN Cup 2026" (KHÔNG viết "AFF Cup" nếu giải đã đổi tên).
   · Cùng luật như trên: 4–7 từ, toàn danh từ, có mốc giải/năm khi nói về một trận cụ thể.
   · Tên riêng KHÔNG DẤU, viết hoa đúng kiểu quốc tế.
   ✓ "Vietnam Malaysia ASEAN Cup 2026 semifinal"
   ✓ "Xuan Son celebration Vietnam national team"
   ✗ "Vietnam football emotional moment"  → trừu tượng, Google trả ảnh vu vơ
   · Câu tiếng Anh được phép kết bằng **"high resolution"** để đẩy ảnh sắc nét lên
     trước (quy chuẩn mục 17: ưu tiên Full HD / 2K / 4K). Chỉ thêm một lần ở cuối,
     đừng nhồi cả "HD 4K high resolution" — thừa chữ làm loãng kết quả.

════ CẤM ════
· KHÔNG đoán mặt cầu thủ trong ảnh — bạn không nhận ra mặt người, đoán bừa hại hơn không đoán.
· KHÔNG bịa tên đội, tên người, tên giải không có trong lời bình hoặc tin gốc ở trên.
· Câu trừu tượng (câu hỏi, lời mời bình luận, câu chốt) thì lấy bối cảnh chung của video —
  tên trận, tên đội, sân vận động — chứ đừng dựng ra cảnh không tồn tại.

`ghi_chu`: một câu ngắn dặn người chọn ảnh nhìn dấu gì để khỏi lấy nhầm (số áo, màu áo, băng
quấn đầu, đội nào, đang vui hay đang buồn). Không có gì để dặn thì để chuỗi rỗng.

HỒ SƠ BÀI (máy đã trích sẵn — dùng để neo THỜI ĐIỂM và gọi ĐÚNG TÊN):
{ho_so}

LỜI BÌNH:
{cac_cau}

Trả về DUY NHẤT một mảng JSON đúng {so_cau} phần tử, phần tử thứ i ứng với câu i:
[{{"tu_khoa": "...", "tu_khoa_2": "...", "tu_khoa_en": "...", "ghi_chu": "..."}}, ...]
Không giải thích gì thêm."""


# Neo ngành — CẦU CHÌ chạy bằng mã, không tin hoàn toàn vào model. Từ khoá nào không có lấy
# một chữ trong đây thì tự chắp thêm, vì thiếu neo là Google hiểu sang chuyện khác ngay
# (anh phản ánh 05/08: "việt nam campuchia" ra ảnh văn hoá, chính trị).
NEO = ("bóng đá", "cầu thủ", "trận đấu", "tuyển", "ghi bàn", "sân vận động", "hlv",
       "thủ môn", "cup", "cúp", "league", "fc", "vòng bảng", "bán kết", "chung kết",
       "aff", "asean", "v-league", "đội tuyển", "huấn luyện", "sân", "khán đài", "họp báo")


_EN_DOI = {"việt nam": "Vietnam", "malaysia": "Malaysia", "thái lan": "Thailand",
           "indonesia": "Indonesia", "singapore": "Singapore",
           "campuchia": "Cambodia", "philippines": "Philippines"}


def _bo_dau_nk(s):
    """Bỏ dấu + thường hoá + chỉ giữ chữ-số-khoảng trắng — chuỗi để SO KHỚP."""
    t = unicodedata.normalize("NFD", (s or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").replace("đ", "d")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def _ten_la_trong(tk, ten_la):
    """Câu lệnh có bám vào tên nào trong DANH SÁCH TÊN LẠ không → trả tên đó.

    Cầu chì cho luật 6b (quy chuẩn mục 17 của anh): internet chỉ có ảnh người nổi
    tiếng; tên ngoài từ điển thực thể thì tra không ra, Google trả ảnh vu vơ — hai
    bài 14/08 hỏng đúng vì vậy (Alif Ahmad · Oliver Williams).

    ĐỐI CHIẾU DANH SÁCH, KHÔNG ĐOÁN. Bản đầu em cho code tự dò "cụm hai chữ nào
    trông giống tên riêng" — nó bắt luôn «tiền đạo», «chỉ đạo» rồi thay bằng tên
    đội, câu lệnh thành rác. Nhân vật của bài đã được hồ sơ bài trích sẵn; lấy đúng
    danh sách ấy trừ đi từ điển là ra tên lạ, không cần đoán chữ nào cả.
    """
    t = " " + _bo_dau_nk(tk) + " "
    for ten in ten_la:
        k_ = _bo_dau_nk(ten)
        if k_ and f" {k_} " in t:
            return ten
    return ""


def _chac_neo(tk, neo_phu):
    """Không có neo ngành thì chắp thêm — cầu chì cuối cùng trước khi từ khoá ra Google."""
    t = (tk or "").strip()
    if not t:
        return t
    if any(n in t.lower() for n in NEO):
        return t
    return (t + " " + neo_phu).strip()


def _tach_cau(loi_binh):
    return [c.strip() for c in re.split(DD.TACH_CAU_RE, loi_binh or "") if c.strip()]


def _boc_json(chu):
    """Model hay bọc JSON trong ```json ... ``` hoặc kèm một câu dẫn — bóc lấy mảng."""
    chu = re.sub(r"^```(?:json)?|```$", "", chu.strip(), flags=re.M).strip()
    i, j = chu.find("["), chu.rfind("]")
    if i < 0 or j < 0:
        raise ValueError("không thấy mảng JSON trong câu trả lời")
    return json.loads(chu[i:j + 1])


# ── tầng ② mẹo, chạy bằng mã ─────────────────────────────────────────────────
_THUONG = {"Phút", "Một", "Hai", "Ba", "Bốn", "Năm", "Sáu", "Bảy", "Tám", "Chín", "Mười",
           "Và", "Còn", "Anh", "Người", "Hết", "Ít", "Nhưng", "Cú", "Tổ", "Trận", "Đó", "Nếu",
           "Có", "Không", "Vì", "Khi", "Sau", "Trước", "Rồi", "Thế", "Cả", "Từ", "Đến", "Giờ"}


def _ten_rieng(cau):
    """Rút cụm viết hoa GIỮA câu — tên người, tên đội. Chữ đầu câu thì bỏ vì câu nào cũng hoa."""
    ra, dang = [], []
    for k, tu in enumerate(cau.split()):
        sach = tu.strip(".,!?…:;\"'()")
        if k and sach[:1].isupper() and sach not in _THUONG:
            dang.append(sach)
        else:
            if len(dang) >= 1:
                ra.append(" ".join(dang))
            dang = []
    if dang:
        ra.append(" ".join(dang))
    return ra


def _meo(cau, neo):
    ra = []
    for c in cau:
        ten = _ten_rieng(c)
        ra.append({"tu_khoa": (" ".join(ten[:2]) + " " + neo).strip() if ten else neo,
                   "tu_khoa_2": neo, "ghi_chu": ""})
    return ra


# ── học từ anh: đọc hai sổ trước khi gợi ────────────────────────────────────
def _bai_hoc_tu_anh(toi_da=14):
    """Gom mẫu thật để model gợi giống kiểu anh gõ (anh chốt 06/08 tối).

    Hai sổ, hai loại vàng:
    · tim-anh-thanh-cong.jsonl — từ khoá ANH TỰ GÕ mà lấy được ảnh về (cả ô tìm trên trạm
      lẫn extension trong Chrome). Đây là chuẩn mực: nó ĐÃ ra ảnh thật.
    · sua-tu-khoa.jsonl — máy gợi X, anh đổi thành Y. Cho model thấy mình hay trượt kiểu gì.
    Sổ rỗng thì thôi — không nhét mục trống vào lời dặn."""
    ra = []
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # ~/socbongda247
    p1 = os.path.join(goc, "hoc", "tim-anh-thanh-cong.jsonl")
    p2 = os.path.join(goc, "hoc", "sua-tu-khoa.jsonl")
    try:
        dong = [json.loads(x) for x in open(p1, encoding="utf-8") if x.strip()]
        tot = []
        for m in dong[-toi_da:]:
            if m.get("tu_khoa") and m["tu_khoa"] not in tot:
                tot.append(m["tu_khoa"])
        if tot:
            ra.append("TỪ KHOÁ THẬT ANH ĐÃ GÕ VÀ LẤY ĐƯỢC ẢNH (bắt chước kiểu gõ này):\n"
                      + "\n".join(f"  · {t}" for t in tot))
    except FileNotFoundError:
        pass
    try:
        dong = [json.loads(x) for x in open(p2, encoding="utf-8") if x.strip()]
        cap = []
        for m in dong[-6:]:
            for d in m.get("doi", [])[:3]:
                cap.append(f"  · máy gợi: {d['may_goi']}  →  anh sửa: {d['anh_sua']}")
        if cap:
            ra.append("MÁY TỪNG GỢI TRƯỢT, ANH PHẢI SỬA (đừng lặp lại kiểu trượt này):\n"
                      + "\n".join(cap[-8:]))
    except FileNotFoundError:
        pass
    return ("\n\n════ HỌC TỪ CHÍNH ANH ════\n" + "\n\n".join(ra)) if ra else ""


# ── tầng ① model ─────────────────────────────────────────────────────────────
# chức danh/khái niệm ĐỔI THEO THỜI GIAN — đứng một mình là ra ảnh mọi thời kỳ
_CAN_MOC = ("huan luyen vien", "hlv", "doi hinh", "doi tuyen", "ban huan luyen",
            "thu mon", "doi truong", "ao dau", "bang xep hang", "nha vo dich",
            "head coach", "coach", "squad", "lineup", "captain", "kit",
            "standings", "champion", "manager")


def _neo_thoi_diem(tk, hs, la_en=False):
    """Chèn MỐC (giải · năm) vào câu lệnh nói về thứ đổi theo thời gian.

    Cầu chì cho luật 6bb (anh chốt 14/08): *"nội dung có đoạn huấn luyện viên đội
    tuyển Malaysia thì từ khoá tìm như thế sẽ ra rất nhiều đời huấn luyện viên, trong
    khi tin của mình đang nói về thời điểm hiện tại"*. Model được dặn rồi, nhưng dặn
    suông thì có lần nhớ lần quên — code phải bọc lót.

    Chỉ chèn khi: câu lệnh CÓ chức danh đổi theo thời gian, VÀ chưa có năm/tên giải.
    """
    if not tk:
        return tk
    k = _bo_dau_nk(tk)
    if not any(c in k for c in _CAN_MOC):
        return tk
    if re.search(r"\b20\d\d\b", tk):                 # đã có năm rồi
        return tk
    giai = (hs.get("giai") or "").split(";")[0].strip()
    if giai and _bo_dau_nk(giai)[:10] in k:            # đã có tên giải rồi
        return tk
    moc = giai or ("2026" if not re.search(r"\b20\d\d\b", tk) else "")
    if not moc:
        return tk
    return f"{tk} {moc}".strip()


def _mo_ta_ho_so(hs):
    """Hồ sơ bài → mấy dòng gọn cho prompt. Rỗng thì nói thẳng là chưa có."""
    if not hs:
        return "(chưa lập hồ sơ — hãy tự suy thời điểm từ tiêu đề và tin gốc)"
    d = []
    for khoa, nhan in (("nhan_vat", "Nhân vật"), ("doi", "Đội"), ("giai", "Giải"),
                       ("tran", "Trận"), ("thoi_diem", "Thời điểm")):
        v = hs.get(khoa)
        if v:
            d.append(f"· {nhan}: {', '.join(v) if isinstance(v, list) else v}")
    d.append("· Sự kiện đã diễn ra chưa: "
             + ("RỒI" if hs.get("da_dien_ra") else "CHƯA / đang tới"))
    if hs.get("cap_do"):
        d.append(f"· Cấp độ: {hs['cap_do']}")
    return "\n".join(d)


def _hoi_model(kb, cau):
    loi = LOI_DAN.format(
        tieu_de=kb.get("tieu_de", ""), tin_goc=kb.get("tin_goc", ""),
        tu_khoa_kb=", ".join(kb.get("tu_khoa", [])[:6]), so_cau=len(cau),
        ho_so=_mo_ta_ho_so(kb.get("_ho_so") or {}),
        cac_cau="\n".join(f"{i}. {c}" for i, c in enumerate(cau))) + _bai_hoc_tu_anh()
    r = subprocess.run([CLAUDE, "-p", "--model", MODEL, loi],
                       capture_output=True, text=True, timeout=HAN_GIO)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "claude -p lỗi")[-300:])
    ds = _boc_json(r.stdout)
    if len(ds) != len(cau):                                   # thiếu/thừa câu là hỏng bản đồ
        raise ValueError(f"model trả {len(ds)} mục, cần đúng {len(cau)}")
    return [{"tu_khoa": str(d.get("tu_khoa", "")).strip(),
             "tu_khoa_2": str(d.get("tu_khoa_2", "")).strip(),
             "tu_khoa_en": str(d.get("tu_khoa_en", "")).strip(),
             "ghi_chu": str(d.get("ghi_chu", "")).strip()} for d in ds]


def goi_y(viec, dung_model=True):
    kb = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
    # HỒ SƠ BÀI (nhân vật · giải · thời điểm) — bộ gợi từ khoá phải biết BỐI CẢNH thì
    # mới neo đúng thời điểm được (anh chốt 14/08: "hlv malaysia" ra đủ mọi đời HLV)
    try:
        kb["_ho_so"] = json.load(open(os.path.join(viec, "anh", "ho-so-bai.json"),
                                      encoding="utf-8"))
    except Exception:
        kb["_ho_so"] = {}
    cau = _tach_cau(kb.get("loi_binh", ""))
    if not cau:
        return {"tu_khoa": {}, "ghi_chu": {}, "cach": "—", "loi": "kịch bản không có lời bình"}
    neo = (kb.get("tu_khoa") or [""])[0]
    cach, loi = "mẹo (rút tên riêng bằng mã)", ""
    ds = None
    if dung_model:
        try:
            ds = _hoi_model(kb, cau)
            cach = f"Claude {MODEL.split('-')[1]}"
        except Exception as e:
            loi = f"{e}"
    if ds is None:
        ds = _meo(cau, neo)
    # neo phụ lấy từ chính kịch bản: tên giải / tên trận, không bịa
    neo_phu = "bóng đá"
    for t in (kb.get("tu_khoa") or []):
        if any(n in t.lower() for n in ("cup", "cúp", "league", "aff", "asean")):
            # tên giải trong kịch bản có thể còn viết kiểu CŨ ("AFF Cup") — sửa NGAY
            # tại nguồn neo, không thì nó chắp vào đuôi mọi câu lệnh (bắt 14/08)
            neo_phu = re.sub(r"\bAFF\s*Cup\b", "ASEAN Cup", t, flags=re.I) + " bóng đá"
            break
    # ── CẦU CHÌ TÊN LẠ (14/08, quy chuẩn mục 17) ──────────────────────────────
    ten_biet, ten_la = set(), []
    try:
        td = json.load(open(os.path.join(DD.KHO_TAI_NGUYEN,
                                         "tu-dien-thuc-the.json"), encoding="utf-8"))
        for kh in ("cau_thu_vn", "hlv", "cau_thu_dna"):
            ten_biet |= {_bo_dau_nk(x["ten"]) for x in td.get(kh, []) if x.get("ten")}
        ten_biet |= {_bo_dau_nk(x.get("ten", "")) for x in (td.get("san_van_dong") or [])}
        for v in (td.get("clb_vleague") or {}).values():
            ten_biet.add(_bo_dau_nk(v.get("ten", "")))
    except Exception:
        pass
    try:                                   # nhân vật của bài — hồ sơ đã trích sẵn
        hs = json.load(open(os.path.join(os.path.dirname(viec.rstrip("/")),
                                         os.path.basename(viec), "anh", "ho-so-bai.json"),
                            encoding="utf-8"))
        ten_la = [t for t in (hs.get("nhan_vat") or [])
                  if t and _bo_dau_nk(t) not in ten_biet]
    except Exception:
        ten_la = []
    doi_chinh = ""
    for t in [kb.get("tieu_de", "")] + (kb.get("tu_khoa") or []):
        for d_ in ("việt nam", "malaysia", "thái lan", "indonesia", "singapore",
                   "campuchia", "philippines"):
            if d_ in (t or "").lower():
                doi_chinh = d_
                break
        if doi_chinh:
            break
    if ten_la and doi_chinh:
        for d in ds:
            for khoa in ("tu_khoa", "tu_khoa_2", "tu_khoa_en"):
                la = _ten_la_trong(d.get(khoa, ""), ten_la)
                if not la:
                    continue
                # BỎ tên lạ, giữ nguyên phần còn lại; thêm đội nếu câu chưa có
                con = re.sub(re.escape(la), " ", d[khoa], flags=re.I)
                con = " ".join(con.split())
                # CHỈ chèn đội khi câu lệnh CHƯA có đội nào (sửa 14/08): bài về Alif
                # Ahmad (Malaysia) mà tiêu đề nhắc "VIỆT NAM" trước, cầu chì chèn
                # "việt nam" vào câu vốn đã có "Malaysia" → "việt nam hậu vệ Malaysia",
                # hai đội một câu, Google chẳng hiểu tìm gì.
                k_con = _bo_dau_nk(con)
                da_co_doi = any(_bo_dau_nk(x) in k_con for x in _EN_DOI) or \
                    any(_bo_dau_nk(x) in k_con for x in _EN_DOI.values())
                if not da_co_doi:
                    doi_v = doi_chinh if khoa != "tu_khoa_en" \
                        else _EN_DOI.get(doi_chinh, "")
                    if doi_v:
                        con = f"{doi_v} {con}".strip()
                d[khoa] = con
                d["ghi_chu"] = (d.get("ghi_chu", "") + f" · bỏ «{la}» — tên này "
                                "không có ảnh trên mạng").strip(" ·")
    hs_n = kb.get("_ho_so") or {}
    # TÊN GIẢI ĐÃ ĐỔI (quy chuẩn anh): giải nay là ASEAN Cup, model hay quen tay viết
    # "AFF Cup" — ảnh trả về là ảnh mùa cũ. Sửa cứng, khỏi trông chờ model nhớ.
    for d in ds:
        for khoa in ("tu_khoa", "tu_khoa_2", "tu_khoa_en"):
            if d.get(khoa):
                d[khoa] = re.sub(r"\bAFF\s*Cup\b", "ASEAN Cup", d[khoa], flags=re.I)
    for d in ds:
        for khoa in ("tu_khoa", "tu_khoa_2", "tu_khoa_en"):
            if d.get(khoa):
                d[khoa] = _neo_thoi_diem(d[khoa], hs_n, khoa == "tu_khoa_en")
    for d in ds:
        d["tu_khoa"] = _chac_neo(d.get("tu_khoa", ""), neo_phu)
        d["tu_khoa_2"] = _chac_neo(d.get("tu_khoa_2", ""), neo_phu)
        # TIẾNG ANH có neo riêng — chắp "football" chứ không chắp "bóng đá" vào câu
        # tiếng Anh (trộn hai thứ tiếng làm Google loãng cả hai). Anh chốt 14/08.
        en = d.get("tu_khoa_en", "")
        if en and not any(n in en.lower() for n in
                          ("football", "soccer", "match", "stadium", "cup", "team")):
            en = (en + " football").strip()
        d["tu_khoa_en"] = en
    return {"tu_khoa": {str(i): d["tu_khoa"] for i, d in enumerate(ds) if d["tu_khoa"]},
            "tu_khoa_2": {str(i): d["tu_khoa_2"] for i, d in enumerate(ds)
                          if d.get("tu_khoa_2") and d["tu_khoa_2"] != d["tu_khoa"]},
            "tu_khoa_en": {str(i): d["tu_khoa_en"] for i, d in enumerate(ds)
                           if d.get("tu_khoa_en")},
            "ghi_chu": {str(i): d["ghi_chu"] for i, d in enumerate(ds) if d["ghi_chu"]},
            "cach": cach, "loi": loi, "so_cau": len(cau)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("dùng: goi_y.py <thư mục việc>")
    r = goi_y(sys.argv[1])
    print(f"— {r['so_cau']} câu · gợi ý bằng {r['cach']}"
          + (f" (model hỏng: {r['loi'][:120]})" if r["loi"] else ""))
    for i in range(r["so_cau"]):
        print(f"  {int(i) + 1:>2}. {r['tu_khoa'].get(str(i), '—')}"
              + (f"   ↳ {r['ghi_chu'][str(i)]}" if r["ghi_chu"].get(str(i)) else ""))
