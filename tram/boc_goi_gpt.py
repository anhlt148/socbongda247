#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BÓC GÓI TỪ KHOÁ ANH DÁN TỪ DỰ ÁN GPT — anh chốt 14/08 ("đường ①").

Anh viết bài ở một dự án ChatGPT đã luyện kỹ, bên đó ra từ khoá tiếng Anh rất trúng
(anh đo thật: tìm được ảnh ưng hơn hẳn bộ gợi ý của trạm). Trước nay anh phải chép
TỪNG CẢNH một sang trạm. Nay dán MỘT KHỐI, máy tự bóc và điền vào đúng câu.

Vì sao không gọi API OpenAI: "dự án" là thứ riêng của giao diện web (hướng dẫn tuỳ
chỉnh + tệp đính kèm + trí nhớ), API không với tới. Cầu dán giữ nguyên chỗ mạnh của
anh mà không thêm nhà cung cấp nào để hỏng.

KHỚP CÂU chứ không tin số thứ tự: GPT chia theo "ĐOẠN", trạm chia theo CÂU — hai cách
chia không trùng nhau. Mỗi khối GPT có kèm chính câu thoại (trong ngoặc kép), nên máy
so chuỗi để biết đoạn ấy ứng với câu nào. Đoạn nào không khớp được thì BỎ, không đoán
bừa — dặt vào sai câu còn hại hơn không có.

Dùng:  boc(chu_dan, cac_cau) -> {"tu_khoa": {i: "..."}, "tu_khoa_en": {i: "..."},
                                 "khop": n, "truot": [câu GPT không khớp được]}
"""
import json
import os
import re
import subprocess
import unicodedata

import nen_tang as NT

# dòng từ khoá: "- abc", "• abc", "* abc", "`abc`", "1. abc"
_DONG_TK = re.compile(r"^\s*(?:[-–—*•·]|\d+[.)])\s*(.+?)\s*$")
# câu thoại GPT trích: nằm trong " " hoặc “ ” hoặc ' ' — lấy cả dòng in đậm **...**
_TRICH = re.compile(r"[\"“”'’]([^\"“”]{12,400})[\"“”'’]|^\*\*(.{12,400})\*\*\s*$", re.M)
# nhãn mở khối: "ĐOẠN 3", "CẢNH 2", "SCENE 4", "Câu 5"
_NHAN_KHOI = re.compile(r"^\s*(?:#{1,4}\s*)?(?:\*\*)?\s*"
                        r"(?:ĐOẠN|DOAN|CẢNH|CANH|CÂU|CAU|SCENE|PART)\s*\d+",
                        re.I | re.M)
# dòng rác cần bỏ khi gom từ khoá
_BO_DONG = re.compile(r"^\s*(?:từ\s*kh(?:o|ó)a|tu\s*khoa|keywords?|ảnh\s*nên\s*dùng|"
                      r"anh\s*nen\s*dung|gợi\s*ý\s*ảnh|note|ghi\s*chú|ghi\s*chu)\s*[:：]?\s*$",
                      re.I)


def _khong_dau(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.sub(r"[^a-z0-9 ]+", " ", s)


def _rut(s):
    """Chuỗi so khớp: bỏ dấu, bỏ dấu câu, ép một khoảng trắng."""
    return " ".join(_khong_dau(s).split())


def _co_dau_viet(s):
    """Có ký tự tiếng Việt có dấu → coi là từ khoá tiếng Việt."""
    return any(unicodedata.category(c) == "Mn"
               for c in unicodedata.normalize("NFD", s or "")) or "đ" in (s or "").lower()


def _tach_khoi(chu):
    """Cắt khối theo nhãn ĐOẠN/CẢNH; không có nhãn thì cắt theo dòng trống kép."""
    moc = [m.start() for m in _NHAN_KHOI.finditer(chu)]
    if len(moc) >= 2:
        moc.append(len(chu))
        return [chu[moc[i]:moc[i + 1]] for i in range(len(moc) - 1)]
    # không có nhãn ĐOẠN → cắt tại mỗi DÒNG CÓ CÂU TRÍCH (kiểu GPT trả 14/08:
    # câu trong ngoặc kép, dòng trắng, rồi các từ khoá trần bên dưới)
    dong = chu.splitlines()
    moc_t = [i for i, d in enumerate(dong)
             if re.match(r'^\s*[“"\'][^"”]{12,}', d.strip())]
    if len(moc_t) >= 2:
        moc_t.append(len(dong))
        return ["\n".join(dong[moc_t[i]:moc_t[i + 1]]) for i in range(len(moc_t) - 1)]
    kh = [k.strip() for k in re.split(r"\n\s*\n\s*\n?", chu) if k.strip()]
    return kh if len(kh) >= 2 else [chu]


def _tu_khoa_trong(khoi):
    """Mọi dòng gạch đầu dòng trong khối = ứng viên từ khoá."""
    ra = []
    for dong in khoi.splitlines():
        if _BO_DONG.match(dong):
            continue
        m = _DONG_TK.match(dong)
        # DÒNG TRẦN cũng là từ khoá (anh bắt 14/08: GPT mỗi lần một kiểu, lần này
        # trả thẳng "My Dinh Stadium Vietnam night" không gạch đầu dòng nào).
        # Loại dòng có dấu câu kể chuyện — đó là văn, không phải câu lệnh tìm ảnh.
        t = (m.group(1) if m else dong).strip()
        if not m:
            if (not t or t.startswith(("“", "\"", "'", "#", "**"))
                    or len(t.split()) > 9 or re.search(r"[.,;:?!…]", t)
                    or _NHAN_KHOI.match(t)):
                continue
        t = t.strip().strip("`*_“”\"'")
        t = re.sub(r"\s*[:：]\s*$", "", t)
        # bỏ dòng dẫn dắt kiểu "Ảnh nên dùng: CĐV Việt Nam chờ đợi"
        if re.match(r"^(?:ảnh|anh|hình|hinh)\s+(?:nên|nen)\s", t, re.I):
            continue
        if 3 <= len(t) <= 90:
            ra.append(t)
    return ra


def _cau_trich(khoi):
    """Câu thoại GPT nhắc trong khối, để khớp về câu thật của bài."""
    for m in _TRICH.finditer(khoi):
        t = (m.group(1) or m.group(2) or "").strip()
        if len(_rut(t)) >= 12:
            return t
    return ""


def _tim_cau(trich, rut_cau, da_dung):
    """Câu GPT trích ↔ chỉ số câu thật. Ưu tiên câu CHƯA dùng, khớp chứa nhau."""
    r = _rut(trich)
    if not r:
        return None
    # ① khớp trọn hoặc chứa nhau
    for i, rc in enumerate(rut_cau):
        if i in da_dung:
            continue
        if r == rc or (len(r) > 20 and (r in rc or rc in r)):
            return i
    # ② khớp theo phần đầu (GPT hay cắt bớt đuôi bằng dấu ba chấm)
    dau = r[:40]
    for i, rc in enumerate(rut_cau):
        if i not in da_dung and len(dau) >= 20 and rc.startswith(dau):
            return i
    # ③ chồng từ nhiều nhất, phải đủ đậm mới nhận
    tu_r = set(r.split())
    tot, diem = None, 0.0
    for i, rc in enumerate(rut_cau):
        if i in da_dung:
            continue
        tu_c = set(rc.split())
        if not tu_c:
            continue
        d = len(tu_r & tu_c) / max(len(tu_r | tu_c), 1)
        if d > diem:
            tot, diem = i, d
    return tot if diem >= 0.5 else None


CLAUDE = NT.tim_claude()


def _boc_bang_model(chu_dan, cac_cau):
    """MẮT MÁY ĐỌC HIỂU khối anh dán — dùng khi khuôn cứng bó tay.

    Anh nói đúng 14/08: *"GPT trả về từ khoá mỗi lần không đồng nhất form, a tưởng
    model tự đọc hiểu chứ?"*. Đúng vậy: khối dán là VĂN BẢN NGƯỜI VIẾT, mỗi lượt một
    kiểu — có lần "ĐOẠN 1 / Từ khóa: / - abc", có lần chỉ câu trong ngoặc kép rồi các
    dòng trần. Bắt regex chạy theo là cuộc đua không có đích.

    Chia việc đúng chỗ mạnh: code thử trước (0 token, ăn ngay với khuôn quen), bó tay
    thì haiku đọc — hiểu văn lộn xộn là việc model giỏi nhất mà code dở nhất.
    """
    dong_cau = "\n".join(f"[{i}] {c}" for i, c in enumerate(cac_cau))
    lenh = (
        "Dưới đây là DANH SÁCH CÂU của một video, và một KHỐI GỢI Ý TỪ KHOÁ tìm ảnh "
        "do người khác viết (định dạng tự do, không theo khuôn nào).\n\n"
        "Việc của em: đọc hiểu khối đó, gán từ khoá về ĐÚNG CÂU mà nó nói tới.\n"
        "· Khối thường nhắc lại câu thoại rồi liệt kê từ khoá bên dưới — bám vào đó.\n"
        "· Mỗi câu lấy MỘT từ khoá tiếng Việt và MỘT từ khoá tiếng Anh, chọn cụm giàu "
        "danh từ cụ thể nhất (tên đội, tên người, sân, hành động, giải, năm).\n"
        "· Câu nào khối không nhắc tới thì BỎ TRỐNG — cấm đoán, gán sai còn hại hơn.\n"
        "· Chỉ lấy từ khoá TÌM ẢNH, bỏ mọi dòng bình luận/giải thích/tiêu đề.\n\n"
        f"═══ CÂU CỦA BÀI ═══\n{dong_cau}\n\n"
        f"═══ KHỐI DÁN ═══\n{chu_dan[:12000]}\n\n"
        'Trả về DUY NHẤT một khối JSON: {"<số câu>": {"vi": "...", "en": "..."}, …}\n'
        "Không giải thích gì thêm.")
    r = subprocess.run([CLAUDE, "-p", "--model", "claude-haiku-4-5-20251001"],
                       input=lenh, capture_output=True, text=True, timeout=300)
    m = re.search(r"\{.*\}", r.stdout or "", re.S)
    if not m:
        raise RuntimeError((r.stderr or "model không trả JSON")[-160:])
    d = json.loads(m.group(0))
    vi, en = {}, {}
    for k, v in d.items():
        if not str(k).lstrip("-").isdigit() or not isinstance(v, dict):
            continue
        i = int(k)
        if not (0 <= i < len(cac_cau)):
            continue
        if str(v.get("vi") or "").strip():
            vi[str(i)] = str(v["vi"]).strip()
        if str(v.get("en") or "").strip():
            en[str(i)] = str(v["en"]).strip()
    return {"tu_khoa": vi, "tu_khoa_en": en,
            "khop": len(set(vi) | set(en)), "truot": [], "so_cau": len(cac_cau)}


def boc(chu_dan, cac_cau, cho_model=True):
    """Khối anh dán + danh sách câu của bài → từ khoá theo chỉ số câu.

    Tiếng Việt vào `tu_khoa`, tiếng Anh vào `tu_khoa_en` (dựa vào dấu tiếng Việt).
    Mỗi câu lấy MỘT từ khoá mỗi loại — dài nhất trong khối, vì câu dài mang nhiều
    danh từ neo hơn (cùng lối chọn với bộ gợi ý của trạm).
    """
    ra_vi, ra_en, truot = {}, {}, []
    rut_cau = [_rut(c) for c in cac_cau]
    da_dung = set()
    for khoi in _tach_khoi(chu_dan or ""):
        ds = _tu_khoa_trong(khoi)
        if not ds:
            continue
        trich = _cau_trich(khoi)
        i = _tim_cau(trich, rut_cau, da_dung)
        if i is None:
            truot.append((trich or khoi.strip().splitlines()[0])[:70])
            continue
        da_dung.add(i)
        vi = [t for t in ds if _co_dau_viet(t)]
        en = [t for t in ds if not _co_dau_viet(t)]
        if vi:
            ra_vi[str(i)] = max(vi, key=len)
        if en:
            ra_en[str(i)] = max(en, key=len)
    ra = {"tu_khoa": ra_vi, "tu_khoa_en": ra_en, "cach": "khuôn",
          "khop": len(da_dung), "truot": truot, "so_cau": len(cac_cau)}
    # KHUÔN BÓ TAY → NHỜ MODEL ĐỌC. Ngưỡng nửa số câu: bóc được vài câu lẻ tẻ nghĩa là
    # khuôn đang đoán sai chỗ chứ không phải khối chỉ có bấy nhiêu.
    if cho_model and len(da_dung) < max(2, len(cac_cau) // 2):
        try:
            r2 = _boc_bang_model(chu_dan, cac_cau)
            if r2["khop"] > len(da_dung):
                r2["cach"] = "mắt máy đọc hiểu"
                return r2
        except Exception as e:
            ra["loi_model"] = str(e)[:120]
    return ra
