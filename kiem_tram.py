#!/usr/bin/env python3
"""KIỂM HỒI QUY TRẠM — chạy TRƯỚC KHI BÁO XONG bất kỳ chức năng nào (anh chốt 11/08).

Luật anh đặt: "làm chức năng nào cũng phải kiểm cẩn thận để không làm hỏng chức năng
khác đã làm xong và kiểm thử ok". Luật suông thì lần sau vẫn quên, nên nó có RĂNG:
một lệnh soi hết những chỗ ĐÃ TỪNG GÃY.

    python3 ~/socbongda247/kiem_tram.py            # kiểm nhanh (~15 giây)
    python3 ~/socbongda247/kiem_tram.py --sau      # kiểm sâu: gọi thử cả route ghi

Năm tầng:
① CÚ PHÁP — mọi .py của xưởng/trạm + mọi <script> của các trang HTML (node --check).
② BẪY ĐÃ TỪNG GÃY (quét tĩnh):
   · import trong thân hàm đè module toàn cục → UnboundLocalError (gãy 2 lần: shutil
     10/08, base64 11/08 làm chết đường gửi ảnh của extension);
   · trường sổ mới quên khai vào whitelist _luu_nhap → lưu xong mất trắng;
   · trang 8756 quên nhúng /menu.js (luật menu chung).
③ ROUTE SỐNG — gọi thật mọi đường ĐỌC của trạm, phải trả 200 + JSON đúng khuôn.
④ LUỒNG CỐT LÕI — cửa nhận ảnh của extension (đường đã gãy 11/08) chạy trên sandbox
   rồi tự dọn, không đụng bài thật.
⑤ CẢNH CHÍNH ↔ CẢNH PHỤ — luật anh dặn 4 lần: tính năng nào của cảnh chính cũng
   phải có bản cho ô phụ (soi tĩnh, bắt ngay lúc code chứ không đợi anh phát hiện).

Thêm bẫy mới học được thì viết thẳng vào đây — đó là cách luật tự lớn lên.
"""
import ast
import builtins
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request

MAY = os.path.expanduser("~/socbongda247")
sys.path.insert(0, MAY)
import duong_dan as DD                      # noqa: E402 — đường theo MÁY
TRAM = os.path.join(MAY, "tram")
CONG = "http://127.0.0.1:8756"
PY = ["tram/tram_tai_nguyen.py", "tram/gap_anh.py", "xuong.py", "chuyen_dong.py", "nhip_canh.py",
      "chuan_ten.py", "nhap_kho_chu_the.py", "nhap_kho_video.py", "xoa_wm.py",
      "buoc3_xepkho.py", "lam_tag.py"]
HTML = ["tram-tai-nguyen.html", "tram-chon-anh.html", "kho-nha-duyet.html"]
# trường sổ tram.json — thêm trường mới mà quên khai ở _luu_nhap là LƯU XONG MẤT
TRUONG_SO = ["ban_do", "ghi_chu", "tu_khoa", "the_so", "anh_phu", "lat_anh",
             "ghep_canh", "nhap", "tu_khoa_phu", "ghi_chu_phu", "tu_khoa_vi",
             "tu_khoa_nguoi", "tu_khoa_video", "tu_khoa_dia"]

loi, canh = [], []


def _than_ham(nguon, ten):
    """Thân một hàm, cắt theo cây cú pháp — chuẩn xác dù hàm dài ngắn thế nào.

    Cắt bằng `nguon[i:i+N]` thì mỗi lần thêm chú thích là cổng lại báo oan, và người
    sửa sẽ nới N ra cho qua — cổng mất tác dụng mà không ai hay.
    """
    try:
        c = ast.parse(nguon)
    except SyntaxError:
        return ""
    for n in ast.walk(c):
        if isinstance(n, ast.FunctionDef) and n.name == ten:
            return ast.get_source_segment(nguon, n) or ""
    return ""


def _bao(ok, ten, them=""):
    print(("  ✅ " if ok else "  ❌ ") + ten + (f" — {them}" if them else ""))
    if not ok:
        loi.append(ten)


def _bien_chua_khai(src):
    """BIẾN ĐỌC MÀ CHƯA KHAI — thứ `ast.parse` không thấy vì cú pháp vẫn đúng.

    Bẫy 12/08: `xuong.py` in kết quả bằng biến `cung` (tên cũ, sau đổi thành
    `nhom_nhac`) — dựng xong xuôi hết 60 giây video rồi mới nổ NameError ở dòng in
    cuối cùng, anh nhận báo "dựng hỏng" trong khi video đã nằm sẵn trên đĩa. Cú pháp
    đúng nên cổng ① cũ cho qua; phải soi TÊN mới bắt được.

    Quét theo phạm vi hàm, có tính hàm LỒNG (tham số hàm con, biến hàm cha) — không
    thì báo giả tràn lan, mà cổng báo giả nhiều lần là cổng bị bỏ qua.
    """
    cay = ast.parse(src)
    ngoai = set(dir(builtins)) | {"__file__", "__name__", "__doc__"}
    for x in ast.walk(cay):
        if isinstance(x, (ast.Import, ast.ImportFrom)):
            ngoai |= {a.asname or a.name.split(".")[0] for a in x.names}
        elif isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            ngoai.add(x.name)
        elif isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
            ngoai.add(x.id)                      # gán ở bất kỳ đâu (kể cả toàn cục)

    def _ten_gan(f):
        """Mọi tên ĐƯỢC ĐẶT bên trong hàm f — tham số, gán, import, except, global."""
        ra = {a.arg for a in
              f.args.posonlyargs + f.args.args + f.args.kwonlyargs}
        if f.args.vararg:
            ra.add(f.args.vararg.arg)
        if f.args.kwarg:
            ra.add(f.args.kwarg.arg)
        for n in ast.walk(f):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                ra.add(n.id)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                ra.add(n.name)
                if n is not f:                   # tham số hàm CON cũng là tên hợp lệ
                    ra |= _ten_gan(n) if isinstance(n, ast.FunctionDef) else set()
            elif isinstance(n, ast.ExceptHandler) and n.name:
                ra.add(n.name)
            elif isinstance(n, (ast.Global, ast.Nonlocal)):
                ra |= set(n.names)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                ra |= {a.asname or a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.Lambda):       # tham số lambda cũng là tên hợp lệ
                ra |= {a.arg for a in
                       n.args.posonlyargs + n.args.args + n.args.kwonlyargs}
                if n.args.vararg:
                    ra.add(n.args.vararg.arg)
                if n.args.kwarg:
                    ra.add(n.args.kwarg.arg)
        return ra
    # CHỈ soi hàm CẤP NGOÀI CÙNG (kể cả method trong class) — hàm lồng bên trong được
    # soi luôn trong phạm vi hàm cha, vì `_ten_gan` gom tên của cả cây con. Soi hàm
    # lồng riêng lẻ là báo giả hàng loạt: nó dùng biến của hàm cha (closure) hoàn toàn
    # hợp lệ — đo thật 12/08: 4 mục báo giả (`mj`, `thu_muc`, `viec`, `x`).
    goc = [x for x in cay.body if isinstance(x, ast.FunctionDef)]
    for c in [x for x in cay.body if isinstance(x, ast.ClassDef)]:
        goc += [x for x in c.body if isinstance(x, ast.FunctionDef)]
    xau = []
    for f in goc:
        dat = _ten_gan(f)
        for n in ast.walk(f):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) \
                    and n.id not in dat and n.id not in ngoai:
                xau.append(f"dòng {n.lineno} trong {f.name}(): '{n.id}'")
    return sorted(set(xau))


def tang1_cu_phap():
    print("① CÚ PHÁP")
    for f in PY:
        p = os.path.join(MAY, f)
        if not os.path.exists(p):
            continue
        try:
            ast.parse(open(p, encoding="utf-8").read())
            ok, vet = True, ""
        except SyntaxError as e:
            ok, vet = False, f"dòng {e.lineno}: {e.msg}"
        _bao(ok, f"python {f}", vet)
        if ok:
            xau_bd = _bien_chua_khai(open(p, encoding="utf-8").read())
            _bao(not xau_bd, f"biến đã khai đủ · {f}", " · ".join(xau_bd[:3]))
    if subprocess.run(["which", "node"], capture_output=True).returncode == 0:
        for f in HTML:
            p = os.path.join(TRAM, f)
            src = open(p, encoding="utf-8").read()
            khoi = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", src, re.S)
            xau = []
            for i, k in enumerate(khoi):
                r = subprocess.run(["node", "--check", "-"], input=k,
                                   capture_output=True, text=True)
                if r.returncode:
                    xau.append(f"khối {i + 1}: " + (r.stderr or "").splitlines()[-1][:70])
            _bao(not xau, f"javascript {f}", " · ".join(xau))
    else:
        canh.append("không có node — bỏ qua kiểm cú pháp JS")


def tang2_bay_cu():
    print("② BẪY ĐÃ TỪNG GÃY")
    # ②a import cục bộ đè module toàn cục
    for f in PY:
        p = os.path.join(MAY, f)
        if not os.path.exists(p):
            continue
        t = ast.parse(open(p, encoding="utf-8").read())
        tren = {n.name.split(".")[0] for x in ast.walk(t)
                if isinstance(x, ast.Import) and x.col_offset == 0 for n in x.names}
        tren |= {(x.names[0].asname or x.names[0].name) for x in ast.walk(t)
                 if isinstance(x, ast.ImportFrom) and x.col_offset == 0}
        xau = []
        for fn in [x for x in ast.walk(t)
                   if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for imp in ast.walk(fn):
                ten_ds = []
                if isinstance(imp, ast.Import):
                    ten_ds = [n.asname or n.name.split(".")[0] for n in imp.names]
                elif isinstance(imp, ast.ImportFrom):
                    ten_ds = [n.asname or n.name for n in imp.names]
                for ten in ten_ds:
                    if ten in tren:
                        xau.append(f"{fn.name}() dòng {imp.lineno}: {ten}")
        _bao(not xau, f"không import đè module — {f}", " · ".join(xau[:3]))
    # ②b trường sổ khai đủ ở cả ba cửa
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()

    def _than_ham(ten):
        """Thân hàm theo RANH GIỚI THẬT, không cắt bằng số ký tự.

        Bản cũ lấy `src[i : i+3000]`. Ngày 18/08 thêm mấy dòng chú thích vào
        `_luu_nhap` là `tu_khoa_phu` bị đẩy ra ngoài cửa sổ ấy → cổng báo TRƯỢT OAN
        một whitelist vẫn đang đủ. Cổng báo oan còn nguy hơn cổng không có: nó dạy
        người ta bỏ qua lời cảnh báo.
        """
        try:
            for nd in ast.walk(ast.parse(src)):
                if isinstance(nd, ast.FunctionDef) and nd.name == ten:
                    return ast.get_source_segment(src, nd) or ""
        except Exception:
            pass
        i = src.find(f"def {ten}")
        return src[i:i + 6000] if i >= 0 else ""

    than_luu = _than_ham("_luu_nhap")
    thieu = [t for t in TRUONG_SO if f'"{t}"' not in than_luu]
    _bao(not thieu, "trường sổ khai đủ trong _luu_nhap", " · ".join(thieu))
    than_ct = _than_ham("_chi_tiet")
    thieu2 = [t for t in TRUONG_SO if f'"{t}"' not in than_ct]
    _bao(not thieu2, "trường sổ trả về trong _chi_tiet", " · ".join(thieu2))
    # ②d ROUTE TRÙNG TÊN — bẫy 11/08: em thêm "/api/xep-kho" cho máy-xếp-nghĩa trong
    # khi đã có "/api/xep-kho" đóng gói video lên Drive. Route mới đứng trước nuốt hết
    # → nút 📦 Kho chạy nhầm việc, anh tưởng xếp kho hỏng. Route trùng là LỖI CÂM:
    # không báo gì, chỉ âm thầm cướp việc của nhau.
    # Cùng đường mà khác GET/POST là HỢP LỆ (vd /api/dang-lam đọc và ghi) — chỉ báo khi
    # trùng TRONG CÙNG một method, vì lúc đó nhánh sau không bao giờ chạy tới.
    trung = []
    for ten_pt in ("do_GET", "do_POST"):
        i0 = src.find(f"def {ten_pt}(")
        if i0 < 0:
            continue
        i1 = min([x for x in (src.find("\n    def do_GET(", i0 + 1),
                              src.find("\n    def do_POST(", i0 + 1),
                              src.find("\ndef main(", i0 + 1)) if x > 0] or [len(src)])
        tat = re.findall(r'if d == "(/api/[a-z0-9\-/]+)"', src[i0:i1])
        trung += [f"{ten_pt}: {x}" for x in sorted({y for y in tat if tat.count(y) > 1})]
    _bao(not trung, "không có route trùng tên", " · ".join(trung))
    # ②c luật menu chung cổng 8756
    for f in HTML:
        src_h = open(os.path.join(TRAM, f), encoding="utf-8").read()
        _bao("/menu.js" in src_h, f"nhúng menu chung — {f}")


def tang_chinh_phu():
    """CẢNH CHÍNH CÓ GÌ, CẢNH PHỤ CÓ NẤY — luật anh dặn ≥3 lần, em vẫn quên lần thứ 4
    (11/08: máy xếp nghĩa, gán nháp, ứng viên cảnh, gán nhanh đều BỎ QUÊN ô phụ).

    Luật trong đầu thì quên; cổng tự động thì không. Tầng này soi tĩnh: mỗi tính năng
    xử lý cảnh chính phải có dấu vết xử lý ô phụ tương ứng."""
    print("⑤ CẢNH CHÍNH ↔ CẢNH PHỤ (luật anh dặn 4 lần)")
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()
    ui = open(os.path.join(TRAM, "tram-tai-nguyen.html"), encoding="utf-8").read()

    def than_ham(ten, nguon=src):
        i = nguon.find("def " + ten)
        if i < 0:
            return ""
        j = nguon.find("\ndef ", i + 1)
        return nguon[i:j if j > 0 else len(nguon)]

    # ①  hàm máy phải đụng tới ô phụ
    for ten, dau in [("_xep_kho_nghia", ["tu_khoa_phu", "CẢNH PHỤ"]),
                     ("_gan_nhap_lo", ["anh_phu", "phan"])]:
        t = than_ham(ten)
        _bao(bool(t) and any(d in t for d in dau),
             f"{ten}() có xử ô phụ", "" if t else "không thấy hàm")
    # ②  route ứng viên + gán hàng loạt phải nhận 'phan'
    for r, dau in [("/api/ung-vien-canh", "phan_u"), ("/api/xep-kho-nghia-gan", "anh_phu")]:
        i = src.find(f'if d == "{r}"')
        kh = src[i:i + 4000] if i > 0 else ""
        _bao(dau in kh, f"{r} nhận ô phụ")
    # ③  UI gán nhanh phải duyệt theo Ô (chính+phụ), không theo câu
    _bao("gnDanhSachO" in ui and "gan-phu" in ui.split("GÁN NHANH")[-1][:6000],
         "⚡ gán nhanh duyệt cả ô phụ")
    # ④  không còn biến gnCau kiểu cũ (chỉ-cảnh-chính)
    _bao("gnCauTrongKe" not in ui, "không còn vòng duyệt chỉ-cảnh-chính")
    # ⑤  ÉP MÃ Ô THÀNH SỐ — bẫy 11/08, gãy HAI chỗ trong một buổi: dải kho nhà chết
    #    câm và cả lượt model xếp kho mất trắng, đều vì int("3:0"). Mã ô phụ có dấu
    #    hai chấm; muốn số câu thì .split(":")[0], muốn in ra thì _ten_ma_o().
    xau = []
    for m in re.finditer(r"int\(\s*(k|k_c|c|x|ma_o)\s*\)", src):
        d = src[:m.start()].count("\n") + 1
        dong = src.splitlines()[d - 1]
        # chỉ soi những vòng lặp trên SỔ MÃ Ô (xep/kho-xep) — ban_do/tu_khoa khoá thuần số
        truoc = src[max(0, m.start() - 300):m.start()]
        if re.search(r"\b(xep|xp|kho_xep|xep_ng)\b", truoc) and "split" not in dong:
            xau.append(f"dòng {d}: {dong.strip()[:70]}")
    _bao(not xau, "không ép mã ô thành số (int trên khoá xep)", " · ".join(xau[:3]))
    # ⑥  MỘT VIỆC MỘT ĐƯỜNG CHẠY — bẫy 11/08 dính BA lần một ngày (cụm tô vàng · thẻ
    #    số liệu · máy xếp/khung đôi): việc ảnh hưởng thành phẩm chỉ nằm ở nhánh phụ
    #    là lệch đường mất im lặng. Chuỗi sau-Duyệt-lời phải gọi đủ các máy.
    i_sd = src.find("def _sau_duyet_loi(")
    than_sd = src[i_sd:i_sd + 12000] if i_sd > 0 else ""
    for may in ("_xep_kho_nghia", "_gan_nhap_lo", "_mat_kiem_nhap"):
        _bao(may + "(" in than_sd, f"chuỗi sau duyệt gọi {may}()")
    # ⑦  CỔNG MD5 chống nhập trùng kho video — vụ v01≡v09 11/08: một video highlight
    #    vào kho HAI LẦN qua hai đường nhập khác nhau, đẻ 25 đoạn trùng. Cửa nhập duy
    #    nhất (_nhap_tep_video) phải giữ cổng này.
    try:
        src_v = open(os.path.join(MAY, "nhap_kho_video.py"), encoding="utf-8").read()
        i_nv = src_v.find("def _nhap_tep_video(")
        than_nv = src_v[i_nv:src_v.find("\ndef ", i_nv + 10)]
        _bao("_md5_tep(" in than_nv, "cửa nhập kho video có cổng md5 chống trùng")
        # ⑧ KHÔNG tách cảnh khi nhập (anh đổi 11/08: mỗi video vào kho = MỘT dòng
        #    goc/cat — scene-detect từng băm mỗi video thành 13–26 dòng làm kho rối)
        _bao("_tach_canh(" not in than_nv and '"loai"' in than_nv.replace("'", '"'),
             "nhập kho video: 1 video = 1 dòng có loai, không tách cảnh")
        # ⑧b ĐOẠN CLIP ANH CẮT PHẢI CÓ ĐƯỜNG VỀ KHO (anh bắt 14/08: cắt cả tuần mà
        #    kho-nha-duyet trống trơn). Ảnh có đường từ 10/08, video thì không — đúng
        #    họ lỗi "cảnh chính có gì cảnh phụ có nấy", nay áp cho TÀI NGUYÊN.
        src_b3 = open(os.path.join(MAY, "buoc3_xepkho.py"), encoding="utf-8").read()
        _bao("def nhap_doan_bai(" in src_v, "kho video có hàm nhập đoạn cắt của bài")
        _bao("nhap_kho_chu_the.py" in src_b3 and "--doan-bai" in src_b3,
             "xếp kho nhập CẢ ảnh LẪN đoạn clip vào kho chung")
        # ⑧c ĐOẠN VÀO KHO PHẢI SẠCH (anh duyệt 14/08): cắt theo khung né logo anh đã
        #    khoanh, và chặn đoạn có chữ/logo GIỮA khung (cắt mép không cứu được) —
        #    đúng luật đã áp cho ảnh từ 10/08. Kèm đường lùi: nhớ khung + video gốc.
        _bao("crop=trunc(iw*" in src_v and "khung['w']" in src_v.replace('"', "'"),
             "nhập đoạn: cắt theo khung né logo anh khoanh")
        _bao("phu_giua" in src_v and "KHÔNG NHẬP" in src_v,
             "cổng chặn chữ/logo GIỮA khung khi nhập đoạn")
        _bao("khung_da_cat" in src_v and "goc_kho" in src_v,
             "sổ kho nhớ khung đã cắt + video gốc (đường lùi khi cắt hụt)")
    except OSError:
        pass
    # ⑧d MẮT DUYỆT ẢNH TRÊN CẢNH (14/08): soi MỌI ảnh đã gán (cả tay lẫn máy),
    #    tự cắt watermark mép — nhưng CHỈ khi đọc ra CHỮ (đã cắt oan tấm Xuân Son
    #    vì tin lời "góc" không bằng chứng), ảnh anh gán tay thì không được gỡ.
    try:
        src_t2 = open(os.path.join(MAY, "tram", "tram_tai_nguyen.py"),
                      encoding="utf-8").read()
        _bao("wm_chu" in src_t2 and 'len(wm_chu) >= 3' in src_t2,
             "mắt duyệt chỉ cắt watermark khi ĐỌC RA CHỮ")
        _bao("_diem_anh_uv" in src_t2 and "sorted(" in src_t2,
             "gán nháp xếp ứng viên theo sức khoẻ ảnh, không theo thứ tự Google")
        i_mk = src_t2.find("def _mat_kiem_nhap(")
        than_mk = src_t2[i_mk:i_mk + 4000]
        _bao("for c in sorted(bd" in than_mk,
             "mắt duyệt soi MỌI ảnh trên cảnh (cả anh gán tay)")
        _bao("may_gan" in than_mk, "ảnh anh gán tay: máy không được gỡ, chỉ nhắc")
        # ⑧e KHUNG ĐÔI CẤM ẢNH DỌC (anh chốt 14/08): nửa khung là dải ngang, ảnh dọc
        #    vào là mất nhân vật. Chặn ở CẢ ba cửa: máy gán, prompt xếp nghĩa, UI nhắc.
        _bao("def _anh_ngang(" in src_t2 and "doc_tren" in src_t2 and "doc_duoi" in src_t2,
             "máy gán khung đôi chặn ảnh dọc cả hai nửa")
        _bao("▯DỌC" in src_t2, "prompt xếp nghĩa đánh dấu + cấm tấm dọc")
        # ⑧f CẦU DÁN TỪ KHOÁ GPT (anh chốt 14/08 "đường ①") — anh chép tay công sức
        #    của dự án GPT sang, máy KHÔNG được đè lên (mất là mất công anh).
        _bao("/api/tu-khoa-gpt" in src_t2 and "import boc_goi_gpt" in src_t2,
             "trạm có cửa nhận khối từ khoá GPT")
        _bao('if not nguoi.get(k_r)' in src_t2,
             "chuỗi sau Duyệt lời KHÔNG đè từ khoá anh dán")
        # ⑧g QUY CHUẨN MỤC 17 (dự án GPT của anh) nạp vào bộ gợi từ khoá 14/08:
        #    tên ngoài từ điển = thế giới không có ảnh → cấm đứng làm neo; đó là gốc
        #    hai bài hỏng cùng ngày (Alif Ahmad · Oliver Williams).
        src_gy = open(os.path.join(TRAM, "goi_y.py"), encoding="utf-8").read()
        _bao("DỄ TÌM ĐƯỢC ẢNH THẬT" in src_gy, "prompt có luật chọn cụm dễ tìm ảnh")
        _bao("def _ten_la_trong(" in src_gy and "ho-so-bai.json" in src_gy,
             "cầu chì tên lạ đối chiếu DANH SÁCH nhân vật (không đoán mù)")
        _bao("_EN_DOI" in src_gy, "cầu chì áp cho cả câu lệnh tiếng Anh")
        # ⑧i NEO THỜI ĐIỂM (anh chốt 14/08): "huấn luyện viên đội tuyển Malaysia" ra
        #    ảnh đủ mọi đời HLV — thứ đổi theo thời gian phải có mốc giải/năm; và tên
        #    giải phải là tên ĐANG DÙNG (ASEAN Cup, không phải AFF Cup).
        _bao("def _neo_thoi_diem(" in src_gy and "_CAN_MOC" in src_gy,
             "cầu chì chèn mốc giải/năm cho chức danh đổi theo thời gian")
        _bao("{ho_so}" in src_gy and "def _mo_ta_ho_so(" in src_gy,
             "prompt gợi từ khoá được đưa HỒ SƠ BÀI (giải · thời điểm)")
        _bao(src_gy.count("ASEAN Cup\", t, flags=re.I)") >= 1
             or 'r"\\bAFF\\s*Cup\\b"' in src_gy,
             "tên giải cũ AFF Cup được sửa thành ASEAN Cup")
        # ⑧h BÓC GÓI GPT PHẢI CÓ TẦNG MẮT MÁY (anh bắt 14/08: "GPT trả mỗi lần một
        #    form, a tưởng model tự đọc hiểu chứ?") — khuôn cứng đuổi theo văn người
        #    viết là cuộc đua không đích; code thử trước, bó tay thì để model đọc.
        src_bg = open(os.path.join(TRAM, "boc_goi_gpt.py"), encoding="utf-8").read()
        _bao("def _boc_bang_model(" in src_bg and "cho_model" in src_bg,
             "bộ bóc có tầng mắt máy đọc hiểu khi khuôn bó tay")
        try:
            import importlib.util as _iu2
            _sp2 = _iu2.spec_from_file_location(
                "_bg", os.path.join(TRAM, "boc_goi_gpt.py"))
            _bg = _iu2.module_from_spec(_sp2); _sp2.loader.exec_module(_bg)
            _r = _bg.boc('ĐOẠN 1\n"Câu thử nghiệm dài đủ để khớp được với bài."\n'
                         'Từ khóa:\n- Vietnam U17 striker\n- tiền đạo u17 việt nam',
                         ["Câu thử nghiệm dài đủ để khớp được với bài.", "Câu khác."])
            _bao(_r["khop"] == 1 and _r["tu_khoa_vi"].get("0") and _r["tu_khoa"].get("0"),
                 "bộ bóc khớp câu + tách đúng hai thứ tiếng")
        except Exception as _e:
            _bao(False, "bộ bóc gói GPT chạy được", str(_e)[:60])
        src_h2 = open(os.path.join(TRAM, "tram-tai-nguyen.html"), encoding="utf-8").read()
        _bao("ảnh DỌC" in src_h2 and "_a2.h > _a2.w" in src_h2,
             "UI nhắc khi anh ghép tay ảnh dọc")
    except OSError:
        pass
    # ⑧j NHIỀU MÁY CHẠY CHUNG MỘT MÃ (anh chốt 15/08): đường dẫn phải ra khỏi code,
    #    vào cấu hình RIÊNG từng máy — ai sửa đường trong mã rồi đẩy lên kho chung là
    #    hai máy lệch nhau ngay. Kho tài nguyên dùng chung trên Drive, việc thì riêng.
    try:
        src_dd = open(os.path.join(MAY, "duong_dan.py"), encoding="utf-8").read()
        _bao("_CAU_HINH" in src_dd and "may.json" in src_dd,
             "đường dẫn đọc từ cấu hình riêng máy (~/.config/…/may.json)")
        _bao("def _do_drive(" in src_dd and "def _do_kho_nang(" in src_dd,
             "máy mới tự dò được Drive và ổ chứa (kể cả Windows)")
        _bao("NGUOI = " in src_dd,
             "có dấu NGƯỜI LÀM để nhiều người khỏi trùng tên hộp thành phẩm")
        src_t3 = open(os.path.join(MAY, "tram", "tram_tai_nguyen.py"),
                      encoding="utf-8").read()
        _bao(src_t3.count('"/api/may"') >= 2, "trạm có cửa đọc + ghi đường dẫn máy")
        src_pc = open(os.path.join(TRAM, "phong-cach.html"), encoding="utf-8").read()
        _bao("m_kho_tai_nguyen" in src_pc and "mLuu" in src_pc,
             "trang phong cách có mục Máy này để đổi đường dẫn")
        _bao('class="khoi"' in src_pc.split("💻 Máy này")[0][-200:],
             "mục Máy này nằm trong KHUNG như các mục khác")
        _bao('button.do' in src_pc and "/api/may-do" in src_pc,
             "có nút 🔍 Dò — người dùng bấm chọn, không phải gõ đường dẫn")
        _bao("def _quet(" in src_t3 and "NFC" in src_t3,
             "bộ dò so tên bằng NFC (macOS lưu NFD, glob trượt)")
        # ⑧k DÁN LINK KHO LÀ ĐỦ (anh chốt 15/08): Claude trên máy mới phải tự đọc ra
        #    hệ này là gì và luật gì phải theo — thiếu CLAUDE.md hay thiếu skill trong
        #    kho là máy khác kéo về mất sạch 50 KB bài học đã trả giá.
        for t_, mo_ in ((("CLAUDE.md"), "Claude tự đọc đầu phiên"),
                        (("README.md"), "người mở link biết dùng thế nào"),
                        (("cai-windows.ps1"), "bộ cài máy Windows"),
                        (("HUONG-DAN-MAY-MOI.md"), "hướng dẫn người ngồi máy mới")):
            _bao(os.path.exists(os.path.join(MAY, t_)), f"kho có {t_} — {mo_}")
        for t_ in ("BRAIN.md", "KIEN-TRUC.md", "NHAT-KY.md", "SKILL.md"):
            _bao(os.path.exists(os.path.join(
                MAY, ".claude", "skills", "soc-kien-truc-su", t_)),
                f"skill kiến trúc sư TRONG kho: {t_}")
    except OSError:
        pass
    # ⑨  CẢNH THUỘC CÂU NÀO — CHỈ ĐƯỢC TRA MỘT LẦN, trên mốc GỐC (anh bắt 13/08:
    #    "tại sao cảnh 4b, 4c không được đưa vào video khi render?"). Khối clip ③d dịch
    #    mốc mở của cảnh kề để mượn giây; ai tra câu theo mốc SAU đó thì cảnh rơi tụt về
    #    câu trước và lấy nhầm ảnh phụ của câu ấy — IM LẶNG, không báo lỗi gì. Trước khi
    #    vá, xuong.py tra lại ba lần ở ba chỗ khác nhau; nay chốt một nguồn mo_cau_goc.
    # ⑩  ĐỒNG HỒ SẢN XUẤT (anh đặt 14/08) — phải đủ MỐC ĐẦU và MỐC CUỐI, không thì
    #    tổng thời gian thành vô nghĩa. Mốc cắm rải ở nhiều route nên rất dễ rơi rụng
    #    khi ai đó sửa route sau này.
    try:
        src_t = open(os.path.join(MAY, "tram", "tram_tai_nguyen.py"), encoding="utf-8").read()
        for moc in ("mo_viec", "duyet_loi", "chuoi_xong", "dung_bat_dau",
                    "dung_xong", "kho_bat_dau", "kho_xong"):
            _bao(f'DH.cham(' in src_t and f'"{moc}"' in src_t, f"đồng hồ có mốc {moc}")
        src_g = open(os.path.join(MAY, "buoc3_xepkho.py"), encoding="utf-8").read()
        _bao("_muc_thoi_gian(" in src_g and "goi-dang_" in src_g,
             "gói đăng: có mục thời gian + tên file mang tên video")
        # ⑪ TÊN TỆP TRONG HỘP = HỢP ĐỒNG với module kiểm hộp NẰM TRÊN DRIVE (bẫy 14/08:
        #    đổi goi-dang.txt → goi-dang_<slug>.txt, chỉ grep trong ~/socbongda247 nên
        #    bỏ sót kho_video.py; kiem_hop báo THIẾU TỆP → hộp không vào sổ → trạm tưởng
        #    bài chưa xếp kho, nút "📂 Mở kho" tụt về "📂 Mở việc" trỏ sang ổ DATA).
        import importlib.util as _iu
        _sp = _iu.spec_from_file_location("_kv", os.path.join(
            DD.CONG_CU, "kho_video.py"))
        _kv = _iu.module_from_spec(_sp)
        _sp.loader.exec_module(_kv)
        _bao("goi-dang" in getattr(_kv, "TEP_TIEN_TO", []) or
             "goi-dang.txt" in getattr(_kv, "TEP_CHUAN", []),
             "kho_video.kiem_hop nhận được tên gói đăng mà xưởng ghi ra")
    except OSError:
        pass
    try:
        src_x = open(os.path.join(MAY, "xuong.py"), encoding="utf-8").read()
        so_tra = src_x.count("enumerate(cau_moc) if b < m")
        _bao(so_tra <= 1 and "mo_cau_goc = [" in src_x,
             "xưởng tra câu-của-cảnh đúng MỘT lần trên mốc gốc",
             f"— đang tra {so_tra} lần" if so_tra > 1 else
             ("— thiếu mo_cau_goc" if "mo_cau_goc = [" not in src_x else ""))
    except OSError:
        pass


def _get(d):
    with urllib.request.urlopen(CONG + d, timeout=30) as r:
        return r.status, json.loads(r.read().decode())


def tang_cua_soi_dung_o():
    """CỬA SOI GÁN ĐÚNG Ô (anh bắt 18/08).

    Bệnh: anh gán ảnh cho ô PHỤ 10b (biến `dangPhu` trỏ 10b), rồi bấm 🔍 ở ô CHÍNH để
    cắt. Cửa soi mở mà không ai xoá `dangPhu`, nên `ganAnh()` vẫn nghĩ "đang chọn ô phụ"
    → ảnh của ô chính GHI ĐÈ lên ô phụ. Ảnh anh chọn cho 10b mất trắng; phải ⌘Z mới cứu,
    mà không để ý thì lên hình sai luôn.

    Gốc: cửa soi dựa vào TRẠNG THÁI CŨ bên ngoài để biết gán đi đâu, thay vì tự mang
    theo ô nguồn.
    """
    print("㉑ CỬA SOI GÁN ĐÚNG Ô (chính ≠ phụ)")
    ui = open(os.path.join(TRAM, "tram-tai-nguyen.html"), encoding="utf-8").read()

    _bao("function moSoi(k, lat, oNguon)" in ui,
         "cửa soi nhận Ô NGUỒN, không đoán từ trạng thái cũ")
    i = ui.find("function moSoi(k, lat, oNguon)")
    than = ui[i:i + 1800]
    _bao("dangPhu = null;" in than,
         "mở soi từ ô CHÍNH thì xoá dấu ô phụ còn sót")
    _bao("dangPhu = {cau: oNguon.cau, phan: +oNguon.o}" in than,
         "mở soi từ ô PHỤ thì trỏ đúng ô ấy")

    # ba nơi mở soi TỪ MỘT Ô đều phải truyền ô nguồn
    _bao("{cau, o: String(phan)}" in ui, "ô phụ → truyền ô nguồn")
    _bao("{cau: i, o: 'c'}" in ui, "ô chính → truyền ô nguồn")
    _bao("latBat(cau, o), {cau, o}" in ui, "ảnh thứ hai khung đôi → truyền ô nguồn")

    _bao("Gán cho <span id=\"soiCau\">" in ui and "cảnh ${dangPhu.cau + 1}" in ui,
         "nút Gán hiện ĐÚNG TÊN Ô (trước đây luôn ghi 'câu N' kể cả khi gán vào ô phụ)")

def tang_mat_may_cham_bia():
    """MẮT MÁY NHÌN ẢNH + BỘ CHẤM BÌA (anh chốt 18/08).

    Anh hỏi máy có tự nhận diện được mọi thứ trên bìa rồi chọn chỗ tốt nhất cho lớp
    phủ không. Có: YuNet nhận khuôn mặt, U²-Net tách chủ thể, rồi bộ chấm bảy thước
    soi từng phương án bìa và đề bản tốt nhất.

    Cổng này canh ba thứ dễ hỏng nhất: ĐƯỜNG LÙI (mắt máy chết thì bìa vẫn phải ra),
    THANG ĐIỂM (hai đường đo hai thang, quên chia là ngưỡng chết câm), và CHỖ GỌI
    (`lam` trả thêm giá trị, chỗ gọi cũ phải chịu được).
    """
    print("\n㉒ MẮT MÁY NHÌN ẢNH + BỘ CHẤM BÌA")
    try:
        _mm = open(os.path.join(MAY, "mat_may.py"), encoding="utf-8").read()
        _cb = open(os.path.join(MAY, "cham_bia.py"), encoding="utf-8").read()
        _tn3 = open(os.path.join(MAY, "lam_thumbnail.py"), encoding="utf-8").read()

        # ĐƯỜNG LÙI là thứ quan trọng nhất: bìa là khâu cuối trước khi đăng, thiếu venv
        # hay hỏng model thì vẫn phải ra bìa, chỉ kém tinh hơn.
        _bao("def _ban_do_quan_trong_doan(" in _tn3 and
             "_ban_do_quan_trong_doan(im, o_ngang, o_doc)" in _tn3,
             "mắt máy hỏng thì TỰ LÙI về cách đoán cũ, bìa không chết")
        _bao("def san_sang(" in _mm and "if not san_sang()" in _mm,
             "mắt máy tự khai chưa sẵn sàng thay vì lăn ra lỗi")

        # Hai đường đo cho hai thang điểm — quên chia là ngưỡng chết câm
        _bao("THANG_MAT, THANG_DOAN" in _tn3 and "/ THANG_MAT" in _tn3
             and "/ THANG_DOAN" in _tn3,
             "hai đường đo cùng chia về MỘT thang, ngưỡng không chết câm")
        _bao("NG_THU_NHO, NG_BO_HAN" in _tn3,
             "ngưỡng nhường chỗ khai một nơi, không rải số trong mã")

        # Mặt đo bằng hộp, nền đo bằng lưới — không đếm hai lần
        _bao("luoi_nen" in _mm and "luoi_nen" in _tn3,
             "lưới NỀN tách khỏi khuôn mặt — không đếm khuôn mặt hai lần")
        _bao("def _che_mat(" in _tn3 and "_che_mat(hop_ds" in _tn3,
             "che khuôn mặt đo bằng GIAO HỘP, chính xác tới pixel")

        # Bộ chấm — ĐỌC MÃ, không import: cổng phải nói được đúng/sai kể cả khi máy
        # thiếu thư viện ảnh, và import trong thân try làm rối cấu trúc.
        _t = re.search(r"TRONG = \{(.+?)\}", _cb, re.S)
        _sotr = dict(re.findall(r'"(\w+)": (\d+)', _t.group(1) if _t else ""))
        _bao(len(_sotr) == 7, "bộ chấm đủ bảy thước",
             "" if len(_sotr) == 7 else f"— đang có {len(_sotr)}")
        _tong_tr = sum(int(v) for v in _sotr.values())
        _bao(_tong_tr == 100, "bảy thước cộng lại tròn 100 điểm",
             "" if _tong_tr == 100 else f"— đang là {_tong_tr}")
        _bao("168" in _cb and "cỡ ngón tay" in _cb,
             "có thước RÕ Ở CỠ NGÓN TAY — thu về cỡ thật trên điện thoại rồi đo")
        # Anh bắt 18/08 lần hai: bộ chấm chỉ biết TRÁNH LỖI, không biết ĐẶT ĐẸP —
        # ô tròn nép sát dải chữ vẫn được điểm tuyệt đối. Cổng canh cả ba vế.
        _bao("DAI_CAO_O_TRON" in _tn3 and "def _muc_cao_o_tron(" in _tn3,
             "tầm cao ô tròn là RÀNG BUỘC (60–70% từ đáy), không phải tiêu chí chấm")
        _cd = _than_ham(_tn3, "_cho_dat_o_tron")
        _bao("_muc_cao_o_tron()" in _cd and "dưới trái" not in _cd,
             "chọn chỗ theo TẦM CAO chuẩn, đã bỏ lối dí bốn góc")
        _bao(all(k in _cb for k in ("cao_tu_day", "cach_dai", "lệch tầm")),
             "thước lớp phủ chấm cả THẨM MỸ: đúng tầm cao + cách dải chữ")
        _bao('"cach_dai"' in _tn3 and '"cao_tu_day"' in _tn3,
             "chỗ đặt ô tròn khai đủ số cho bộ chấm, không để bộ chấm đoán")
        _bao("float(v)" in _cb or "float(sum(" in _cb,
             "điểm ép về float thường, ghi được ra sổ json")

        # Nhiều phương án + chọn + dự bị
        _bao("def _cac_phuong_an(" in _tn3 and "ket.sort(key=lambda x: -x[\"diem\"])" in _tn3,
             "dựng NHIỀU phương án rồi chọn bản điểm cao nhất")
        _bao("thumbnail-du-bi" in _tn3 and "os.unlink(os.path.join(thu, _f))" in _tn3,
             "bản dự bị được DỌN trước khi ghi, không lẫn bản của lần trước")
        _bao("thumbnail-cham.json" in _tn3,
             "ghi báo cáo chấm để anh biết vì sao bản kia thua")
        _bao("if kieu:" in _tn3 and "ds, ten_kieu = [kieu.upper()]" in _tn3,
             "anh chỉ định kiểu thì máy tôn trọng, không tự chọn đè")

        # Chỗ gọi phải chịu được việc `lam` trả thêm giá trị
        _b3 = open(os.path.join(MAY, "buoc3_xepkho.py"), encoding="utf-8").read()
        _bao("*_ = TN.lam(" in _b3,
             "bước đóng gói nhận giá trị trả về kiểu mở, thêm trường không gãy")
    except Exception as e:
        _bao(False, "đọc được mắt máy + bộ chấm", str(e)[:80])



def tang_anh_bia():
    """ẢNH BÌA (anh đặt 18/08 sau khi gửi 20 mẫu của kênh dẫn đầu ngách).

    Công thức mổ được từ mẫu gồm sáu phần; năm phần đầu hệ đã có sẵn trong khuôn vẽ
    tiêu đề của xưởng (dải đỏ–cam · chữ hoa · tô vàng · thanh dọc · watermark), phần
    thứ sáu — BỐ CỤC ẢNH — là thứ file `lam_thumbnail.py` lo.
    """
    print("⑳ ẢNH BÌA CHO VIDEO")
    goc = os.path.dirname(TRAM)
    tn = open(os.path.join(goc, "lam_thumbnail.py"), encoding="utf-8").read()
    b3 = open(os.path.join(goc, "buoc3_xepkho.py"), encoding="utf-8").read()

    _bao(all(f"def bo_cuc_{k}(" in tn for k in "ABCD"),
         "đủ bốn bố cục: một người · đối đầu · hai khung ngang · lưới bốn ô")
    _bao("def _kieu_bo_cuc(" in tn and "claude" not in tn.lower(),
         "chọn bố cục bằng LUẬT (đọc hồ sơ bài), không gọi model")
    # BỘ NÃO ẢNH BÌA — anh sửa được mà không cần đụng mã
    _bao("def duong_nao(" in tn and "nao-thumbnail.md" in tn,
         "có bộ NÃO ảnh bìa trong kho tài nguyên (anh sửa thẳng, không đụng mã)")
    try:
        import duong_dan as _DD2
        _nao = open(os.path.join(_DD2.KHO_TAI_NGUYEN, "nao-thumbnail.md"),
                    encoding="utf-8").read()
        _bao(_nao.count("`") >= 16, "não mô tả đủ tám kiểu kèm mã")
        _bao("THỨ TỰ CHỌN KIỂU" in _nao, "não có thứ tự ưu tiên để chọn")
        _bao("KHÔNG phải điều kiện đối đầu" in _nao,
             "não ghi bài học: có hai đội KHÔNG đủ để gọi là đối đầu")
        _bao("GHI CHÚ CỦA ANH" in _nao, "não chừa chỗ cho anh ghi kinh nghiệm")
        # mã kiểu trong não phải khớp bảng ánh xạ, không thì sửa não mà mã không hiểu
        import lam_thumbnail as _TN2
        thieu = [k for k in _TN2.NAO_MA if f"`{k}`" not in _nao]
        _bao(not thieu, "mọi mã kiểu trong bảng ánh xạ đều có mặt trong não",
             " · ".join(thieu))
        _bao(all(v in _TN2.BO_CUC for v in _TN2.NAO_MA.values()),
             "mọi kiểu trong não đều có hàm dựng thật")
    except Exception as e:
        _bao(False, "đọc được bộ não ảnh bìa", str(e)[:70])
    _bao("chu_rong" in tn and "tit_l" in tn,
         "chỉ quét TIÊU ĐỀ (lời bình dài quét cả vào là kiểu nào cũng trúng)")
    # HIỆU ỨNG THỊ GIÁC (anh chốt 18/08: học bố cục · lớp ảnh · ô tròn · điểm nhấn,
    # KHÔNG cần học phần chữ vì hệ đang tốt)
    for ten_hu, ham in (("vignette — nền lùi chủ thể tiến", "_vignette"),
                        ("tối dần đáy — không có đường cắt cứng", "_toi_dan_day"),
                        ("ám màu theo phe", "_am_mau"),
                        ("vệt sáng ở đường chia", "_vet_sang"),
                        ("viền phát sáng", "_vien_sang"),
                        ("đổ bóng dưới chủ thể", "_do_bong")):
        _bao(f"def {ham}(" in tn, f"có hiệu ứng: {ten_hu}")
    _bao("MAU_PHE" in tn and "việt nam" in tn,
         "bảng màu theo phe (đỏ VN · vàng Malaysia · xanh Thái)")
    _bao("0.57" in tn and "chia CHÉO" in tn,
         "đối đầu chia CHÉO, không chia thẳng đứng")
    # LUẬT VÙNG CẤM (anh bắt 18/08: ô tròn đè trúng mặt cầu thủ)
    _bao("def _ban_do_quan_trong(" in tn,
         "có bản đồ 'chỗ nào KHÔNG được che' cho từng ảnh")
    _bao("da * 2.2" in tn or "da *" in tn,
         "màu da tính NẶNG hơn độ chi tiết — mặt người là thứ giữ chân người xem")
    _than_cd = _than_ham(tn, "_cho_dat_o_tron")
    _bao("_muc_cao_o_tron()" in _than_cd and '"phải"' in _than_cd and '"trái"' in _than_cd,
         "thử nhiều chỗ (tầm cao × trái/phải), không dí cứng một chỗ")
    # Logo chuyển từ "cộng điểm cho góc trên trái" sang ĐO GIAO với hộp logo thật
    # (18/08). Cổng canh theo cách mới, và canh chặt hơn: phải MỘT NGUỒN toạ độ, dùng
    # ở cả chỗ vẽ logo lẫn chỗ tránh logo — hai nơi ghi riêng là ngày nào đó lệch nhau.
    _bao("def _hop_logo(" in tn and "_che_hop(_hop_logo(" in tn,
         "góc logo là vùng cấm — đo bằng giao hộp, không đoán theo góc")
    _bao(tn.count("_hop_logo(") >= 3,
         "toạ độ logo MỘT NGUỒN: chỗ vẽ và chỗ tránh cùng đọc một hàm")
    _bao("d_o = int(d_o * 0.74)" in tn,
         "vướng thì THU NHỎ vật thể rồi thử lại")
    _bao("BỎ ô tròn" in tn,
         "vướng ở mọi góc thì BỎ HẲN — thà thoáng còn hơn che mặt")
    try:
        _nao3 = open(os.path.join(_DD2.KHO_TAI_NGUYEN, "nao-thumbnail.md"),
                     encoding="utf-8").read()
        _bao("LUẬT VÙNG CẤM" in _nao3 and "MỌI thứ đè lên ảnh" in _nao3,
             "não ghi luật vùng cấm áp cho MỌI lớp đè, không riêng ô tròn")
    except Exception:
        pass

    # CẮT THEO ast, KHÔNG đếm ký tự. Cắt 1500 ký tự thì thêm vài dòng chú thích là
    # cổng báo oan — đúng bệnh đã trả giá ngày 18/08 với cổng whitelist.
    than_o = _than_ham(tn, "_o_tron")
    _bao("0.355" in than_o and "GaussianBlur" in than_o,
         "ô tròn đúng thông số não: 32–38% bề ngang, có bóng quanh viền")
    try:
        _nao2 = open(os.path.join(_DD2.KHO_TAI_NGUYEN, "nao-thumbnail.md"),
                     encoding="utf-8").read()
        _bao("BẢY LỚP CỦA MỘT ẢNH BÌA" in _nao2,
             "não mô tả bảy lớp xếp chồng")
        _bao("NỀN PHẢI LÙI" in _nao2, "não ghi luật xuyên suốt về chiều sâu")
        _bao("không bàn ở đây" in _nao2,
             "não KHÔNG lấn sang phần chữ (anh chốt: phần đó đang tốt)")
    except Exception:
        pass
    _bao("KHÔNG phân biệt được gì" in tn,
         "không lấy 'có hai đội' làm điều kiện đối đầu")
    _bao("CO_NGUOI" in tn and "KHONG_NGUOI" in tn,
         "ưu tiên ảnh CÓ NGƯỜI, hạ điểm ảnh bảng điện/đồ hoạ")
    _bao('L.get("hoa_den_ty_le"' in tn,
         "ảnh phủ tới đúng mép dải chữ mà template quy định (đọc, không đoán)")
    _bao("TPL._lop_gradient" in tn and "TPL._fit_tieu_de" in tn,
         "dùng lại các LỚP của template — bìa và video cùng một khuôn mặt")
    _bao("DD.LOGO" in tn and "TPL._ve_watermark" in tn,
         "có logo kênh + watermark, hai dấu nhận biết")
    _bao("import lam_thumbnail" in b3 and "thumbnail.jpg" in b3,
         "bước đóng gói tự dựng bìa vào hộp")
    _bao("chưa dựng được ảnh bìa" in b3,
         "bìa hỏng KHÔNG làm hỏng cả hộp (chỉ cảnh báo)")

    # chạy thử thật trên một bài có ảnh
    try:
        import glob as _g
        import duong_dan as _DD
        bai = None
        for d in sorted(_g.glob(os.path.join(_DD.VIEC, "2026-*", "*")),
                        key=os.path.getmtime, reverse=True)[:12]:
            if os.path.exists(os.path.join(d, "kich-ban.json")) and \
                    _g.glob(os.path.join(d, "anh", "[nt]*.jpg")):
                bai = d
                break
        if bai:
            sys.path.insert(0, goc)
            import lam_thumbnail as _TN
            import tempfile as _tf
            with _tf.TemporaryDirectory() as _t:
                _p, _k, _n, *_ = _TN.lam(bai, os.path.join(_t, "b.jpg"),
                                          so_pa=1)   # cổng chỉ cần MỘT bản, khỏi tốn
                from PIL import Image as _I
                with _I.open(_p) as _im:
                    _bao(_im.size == (1080, 1920),
                         f"dựng thử ra bìa 1080×1920 (bố cục {_k}, {_n} ảnh)")
        else:
            print("   ·  (không có bài nào để dựng thử bìa)")
    except Exception as e:
        _bao(False, "dựng thử ảnh bìa", str(e)[:70])


def tang_soat_nuot_canh():
    """CẢNH BỊ NUỐT (anh chốt 18/08: "ưu tiên cảnh là video", "khi dựng tự kiểm xem có
    cảnh bị nuốt không, tự tìm nguyên nhân và khắc phục, theo dõi 6 lần dựng").

    Nuốt cảnh = hình anh gán cho một ô mà không lên video. Trước 18/08 chuyện này xảy
    ra ÂM THẦM: phép gộp cảnh vụn xoá hẳn một cảnh, chẳng ai báo.
    """
    print("⑲ SOÁT CẢNH BỊ NUỐT KHI DỰNG")
    xg = open(os.path.join(os.path.dirname(TRAM), "xuong.py"), encoding="utf-8").read()
    nc = open(os.path.join(os.path.dirname(TRAM), "nhip_canh.py"), encoding="utf-8").read()

    _bao("SAN_CANH" in xg, "có SÀN tuyệt đối cho độ dài cảnh")
    _bao("có HÌNH RIÊNG" in xg,
         "cảnh vụn CÓ HÌNH RIÊNG thì giữ lại, không gộp (ưu tiên không nuốt)")
    _bao("KHÔNG LÊN VIDEO" in xg, "cổng soát in ra hình nào không lên video")
    _bao("NGUYÊN NHÂN" in xg and "CÁCH CHỮA" in xg,
         "báo kèm nguyên nhân và cách chữa, không chỉ kêu suông")
    _bao("soat-nuot-canh.json" in xg, "có sổ theo dõi qua nhiều lần dựng")
    _bao("sach_lien_tiep" in xg and ">= 6" in xg,
         "đếm 6 lần dựng LIÊN TIẾP sạch thì tự đóng sổ")
    _bao('_so["da_dong"] = False' in xg,
         "có lần nào nuốt thì mở sổ lại, đếm từ đầu")

    # ưu tiên cảnh VIDEO: nhịp không được rút giây của clip, không gộp cảnh clip
    _bao("not la_clip[hx]" in nc, "nhịp KHÔNG mượn giây của cảnh clip")
    _bao("la_clip[i] or d[i] >=" in nc, "cảnh clip không bị coi là cảnh hụt để đi mượn")
    _bao("hx not in la_clip" in xg, "phép gộp không đụng vào cảnh clip")

    # chạy thử thật: câu ngắn kề clip thì clip phải NGUYÊN VẸN
    try:
        sys.path.insert(0, os.path.dirname(TRAM))
        import nhip_canh as _NC
        r = _NC.chia_nhip([1.8, 3.0, 4.0], [False, True, False], [0, 0, 0])
        _bao(abs(r[1]["muon"]) < 0.05,
             "chạy thử: câu ngắn kề clip → clip giữ nguyên độ dài")
    except Exception as e:
        _bao(False, "chạy thử nhịp bảo vệ clip", str(e)[:60])


def tang_query_thong_minh():
    """QUERY THÔNG MINH (anh duyệt 18/08 sau khi em đối chiếu tài liệu nâng cấp).

    Ba mục em đánh giá là ĐÁNG làm trong 32 mục của tài liệu:
      ① tách câu nhiều mốc thành nhiều câu lệnh (mục 8)
      ② câu lệnh tìm VIDEO khác câu tìm ẢNH (mục 17)
      ③ một câu tiếng bản địa khi bài nói về nước khác (mục 21)

    Hai mục CỐ Ý BỎ: 8 nhóm query và search budget 3 vòng — hệ đang lấy ~60 ảnh/câu,
    thừa ảnh chứ không thiếu; nhân năm số lượt tìm là phình đúng chỗ đang tắc (đo thật:
    duyệt ảnh chiếm 71% thời gian sản xuất một video).
    """
    print("⑱ QUERY THÔNG MINH (mốc hình · câu video · tiếng bản địa)")
    gy = open(os.path.join(TRAM, "goi_y.py"), encoding="utf-8").read()
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()

    _bao("moc_hinh" in gy and "tu_khoa_video" in gy and "tu_khoa_dia" in gy,
         "bộ gợi ý sinh đủ ba trường mới")
    _bao("def _cau_chi(" in gy,
         "có CẦU CHÌ bằng code — model quên luật thì code làm thay")

    # cầu chì phải kiểm được và phải đúng ở ba ca xương nhất
    sys.path.insert(0, TRAM)
    try:
        import goi_y as _GY
        d1 = {"tu_khoa": "Vietnam champions AFF Cup 2008, 2018, 2024", "tu_khoa_2": "",
              "moc_hinh": [], "tu_khoa_video": ""}
        b1 = _GY._cau_chi([d1], ["Đăng quang 2008, 2018, rồi 2024."])
        _bao(len(re.findall(r"\b20[0-4]\d\b", d1["tu_khoa"])) == 1,
             "câu lệnh chính chỉ còn MỘT mốc thời gian")
        _bao(len(d1["moc_hinh"]) == 3 and "," not in " ".join(d1["moc_hinh"]),
             "tách đúng 3 mốc và mốc SẠCH dấu phẩy (thứ tự dọn→tách)")

        d2 = {"tu_khoa": "Malaysia ticket price football", "tu_khoa_2": "",
              "moc_hinh": [], "tu_khoa_video": ""}
        _GY._cau_chi([d2], ["Vé tăng từ 30 lên 50 ringgit."])
        _bao(not d2["moc_hinh"] and not d2["tu_khoa_video"],
             "câu TĨNH (giá vé) thì cầu chì IM — không ép tìm video cho thứ không có video")

        d3 = {"tu_khoa": "Vietnam champions 2024", "tu_khoa_2": "",
              "moc_hinh": ["x 2008", "y 2024"], "tu_khoa_video": "Vietnam highlights"}
        b3 = _GY._cau_chi([d3], ["Vô địch 2008 và 2024."])
        _bao(d3["moc_hinh"] == ["x 2008", "y 2024"] and sum(b3.values()) == 0,
             "model đã làm đủ thì cầu chì KHÔNG đè lên")
    except Exception as e:
        _bao(False, "chạy thử cầu chì", str(e)[:70])

    _bao('"tu_khoa_video": d.get("tu_khoa_video"' in src
         and '"tu_khoa_dia": d.get("tu_khoa_dia"' in src,
         "hai trường mới khai vào whitelist (không khai là lưu xong MẤT)")
    _bao("if not (o_cu.get(str(j)) or \"\").strip():" in src,
         "mốc hình chỉ điền vào ô phụ ĐANG TRỐNG — không đè thứ anh gõ tay")
    _bao("len(r.get(\"anh\") or []) < 20" in src,
         "rổ tiếng bản địa chỉ bung khi chưa đủ 20 ảnh (đừng làm chậm ca thường)")


def tang_tu_khoa_anh():
    """TỪ KHOÁ TÌM ẢNH LÀ TIẾNG ANH (anh chốt 17/08: "tìm bằng tiếng Anh dễ ra ảnh phù
    hợp hơn"), nhưng KHO NHÀ gắn nhãn TIẾNG VIỆT nên phải giữ một câu Việt riêng để tra
    kho — không thì máy xếp kho trượt sạch rồi đi tải lại thứ kho đang có.
    """
    print("⑰ TỪ KHOÁ TÌM ẢNH BẰNG TIẾNG ANH")
    gy = open(os.path.join(TRAM, "goi_y.py"), encoding="utf-8").read()
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()
    bg = open(os.path.join(TRAM, "boc_goi_gpt.py"), encoding="utf-8").read()

    _bao("tu_khoa` và `tu_khoa_2` đều viết" in gy or "đều viết\n   BẰNG TIẾNG ANH" in gy,
         "luật gợi ý: hai câu chính viết bằng TIẾNG ANH")
    _bao('"tu_khoa_vi"' in gy, "vẫn sinh câu VIỆT riêng để tra kho")
    _bao('d[khoa] = _chac_neo' not in gy.split('d["tu_khoa_vi"] = _chac_neo')[0][-400:],
         "câu tiếng Anh KHÔNG bị chắp neo tiếng Việt (trộn tiếng làm loãng cả hai)")
    _bao('"football"' in gy, "câu tiếng Anh neo bằng 'football'")

    _bao("def _tk_kho(" in src, "trạm có MỘT hàm quyết 'tra kho thì dùng câu nào'")
    _bao("tu_khoa_vi" in src and "or (nh.get(\"tu_khoa\") or {}).get(k)" in src,
         "thiếu câu Việt thì lùi về câu Anh, không trả rỗng")
    _bao(src.count("_tk_kho(") >= 4, "mọi chỗ tra kho đều đi qua hàm ấy")
    # anh nhắc thêm 17/08: "tìm online dùng tiếng Anh, tìm trong kho dùng tiếng Việt"
    i_x = src.find("def _xep_kho_nghia")
    _bao("_tk_kho(nh, i)" in src[i_x:i_x + 3500],
         "máy xếp kho theo NGHĨA nhận câu VIỆT (nó đọc nhãn kho vốn ghi tiếng Việt)")
    i_t = src.find("def _tim_san")
    _bao('nh.get("tu_khoa", {})' in src[i_t:i_t + 1200],
         "tìm ảnh Google vẫn dùng câu ANH (đường ONLINE)")
    _bao("tu_khoa_en" not in src, "trạm không còn tên trường cũ (đổi vai thì đổi tên)")

    _bao('"tu_khoa": en or vi' in bg, "cầu dán GPT: câu ANH vào ô tìm")
    _bao('"tu_khoa_vi": vi' in bg, "cầu dán GPT: câu VIỆT lui về ô tra kho")

    # sổ nháp phải khai trường mới, không khai là lưu xong MẤT
    _bao('"tu_khoa_vi"' in src.split("def _luu_nhap")[1][:3000] if "def _luu_nhap" in src
         else False, "_luu_nhap khai tu_khoa_vi vào whitelist")


def tang_dich_luu():
    """CHỌN ĐƯỢC NƠI LƯU THỨ GẮP VỀ (anh chốt 17/08), mặc định KHO VIỆC.

    Ba đích: "viec" (bài đang mở) · "kho" (kho chủ thể dùng chung) · đường dẫn riêng.
    Cấu hình ở may.json, sửa trên trang phong cách.
    """
    print("⑯ ĐÍCH LƯU ẢNH / VIDEO GẮP VỀ")
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()
    ui = open(os.path.join(TRAM, "phong-cach.html"), encoding="utf-8").read()
    goc = os.path.dirname(TRAM)
    dd = open(os.path.join(goc, "duong_dan.py"), encoding="utf-8").read()

    _bao("DICH_ANH" in dd and "DICH_VIDEO" in dd, "duong_dan khai hai đích")
    _bao('"viec"' in dd and 'or "viec"' in dd, "MẶC ĐỊNH là kho việc")
    _bao("def _dich_luu(" in src, "có MỘT hàm quyết đích, dùng cho cả ảnh lẫn video")
    _bao('"dich_anh"' in src and '"dich_video"' in src,
         "/api/may nhận được hai khoá đích (không khai whitelist là lưu xong MẤT)")

    i = src.find("def _dich_luu(")
    than = src[i:i + 2000]
    _bao("may.json" in than, "đọc TƯƠI mỗi lượt — đổi đích là ăn ngay, khỏi khởi động lại")
    _bao("lưu về kho việc" in than and "os.path.isdir" in than,
         "đường riêng KHÔNG có thật thì lùi về kho việc, không ném tệp vào hư không")

    _bao('return self._chay_post("/api/kho-nha-tai-len", than)' in src,
         "đích KHO đi đúng đường kho chung đã có, không viết đường thứ hai")
    _bao("mb_x = round(os.path.getsize(tep)" in src,
         "đo cỡ tệp TRƯỚC khi nhánh đích kịp dời/xoá nó")
    _bao('if kieu_d == "viec":' in src,
         "sổ nguồn của BÀI chỉ ghi khi tệp nằm trong bài")

    _bao('v_m in ("viec", "kho")' in src,
         'không đem os.path.isdir("viec") ra hỏi rồi báo oan "không thấy thư mục"')
    _bao("can_bat_lai" in src and "can_bat_lai" in ui,
         "chỉ nhắc khởi động lại khi ĐƯỜNG DẪN GỐC đổi, không nhắc khi đổi đích")

    _bao("m_dich_anh" in ui and "m_dich_video" in ui, "trang có hai ô chọn đích")
    _bao('class="num an"' not in ui,
         "không dùng class CSS không tồn tại (bài học 15/08)")
    _bao("function veDich(" in ui,
         "ô nhập thư mục chỉ hiện khi chọn 'thư mục riêng'")


def tang_canh_dau_clip():
    """CẢNH ĐẦU LÀ CLIP THÌ CÓ DỰNG ĐƯỢC KHÔNG (anh bắt 17/08).

    Bấm Dựng báo "câu MỞ (câu 1) chưa có ảnh — cảnh đầu là cảnh giữ người xem", trong
    khi câu 1 ĐANG có clip 2,6 giây. Gốc: mọi phép đếm trong trạm chỉ nhìn `ban_do` —
    bản đồ của ẢNH. Clip nằm ở sổ riêng `clip-canh.json` nên câu chỉ có clip bị coi là
    trống: cổng duyệt chặn, bộ đếm báo "12/15" trong khi bài đủ 15/15.

    Đúng họ lỗi "cảnh chính có gì cảnh phụ có nấy", nhưng ở tầng LOẠI TÀI NGUYÊN: ảnh
    có đường đi, clip thì không.
    """
    print("⑮ CẢNH ĐẦU LÀ CLIP (đếm ảnh + clip chung một thước)")
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()

    _bao("def _cau_da_co(" in src, "có MỘT thước đo 'câu này đã có tài nguyên chưa'")
    _bao('"clip-canh.json"' in src and "_doc_clip_canh" in src, "thước đo đọc cả sổ clip")
    _bao('int(str(k).split(":")[0])' in src,
         "clip ở Ô PHỤ ('3:0') vẫn tính cho câu 3")

    # Không nơi nào được tự đếm lấy bằng ban_do nữa — đó chính là gốc bệnh
    _bao("co_gi = _cau_da_co(viec, nh)" in src, "cổng DUYỆT dùng thước đo chung")
    _bao('"da_gan": len(_cau_da_co(' in src, "bộ đếm 'x/y câu đã gán' dùng thước đo chung")
    _bao("da = len(_cau_da_co(viec, nh_x)" in src,
         "báo cuối chuỗi máy tự chạy dùng thước đo chung")
    _bao("chưa gán ảnh hay clip cho câu nào" in src
         and "chưa có ảnh hay clip" in src,
         "lời báo lỗi nói đúng sự thật (ảnh HAY clip), không chỉ nhắc ảnh")


def tang_kho_lien_bai():
    """TÀI NGUYÊN BÀI TRƯỚC CÓ DÙNG ĐƯỢC CHO BÀI SAU KHÔNG (anh hỏi 16/08).

    Trước nay ảnh chỉ vào kho chung lúc XẾP KHO — tức sau khi dựng xong hẳn. Anh làm
    bài 4 rồi sang bài 5 mà chưa xếp kho bài 4 thì mọi tấm vừa tải về là VÔ HÌNH với
    bài 5, công tìm mất trắng. Mà hai bài liên tiếp thường cùng chủ đề, nên ảnh dư của
    bài trước lại đúng là thứ hợp bài sau nhất.

    Hai mốc mới, không đẻ luồng nào: `nhap_kho_chu_the.py` vốn quét TOÀN BỘ `<bài>/anh/`
    kể cả tấm chưa gán — chỉ cần gọi sớm hơn.
    """
    print("⑭ TÀI NGUYÊN BÀI TRƯỚC DÙNG ĐƯỢC CHO BÀI SAU")
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()

    _bao("nhap-kho-som.log" in src,
         "chuỗi sau Duyệt lời xong → ảnh của bài vào kho chung ngay")
    _bao("def _vet_kho_bai(" in src, "có đường vét kho cho bài vừa rời")
    _bao("BAI_VUA_MO[0] != ma_v" in src,
         "đổi bài là vét kho bài cũ (mốc tự nhiên nhất: lúc anh cần kho đầy)")
    _bao('"--goc-bai", ma_cu' in src or '["--goc-bai", ma_cu]' in src,
         "vét CẢ video gốc, không chỉ ảnh (luật: chính có gì phụ có nấy)")

    # Nhập kho là việc NẶNG (gắn nhãn mắt máy) — phải chạy nền, đừng chặn trang
    i = src.find("def _vet_kho_bai(")
    than = src[i:i + 1400]
    _bao("subprocess.Popen" in than and "start_new_session=True" in than,
         "vét kho chạy NỀN, không chặn trang đang mở")

    # Kho thật: có bài nào vừa nhập sớm không
    try:
        import duong_dan as _DD
        so = os.path.join(_DD.KHO_TAI_NGUYEN, "anh-chu-the", "so-chu-the.jsonl")
        bai = {json.loads(l).get("nguon_bai", "") for l in open(so, encoding="utf-8")
               if l.strip()}
        _bao(len(bai) >= 20, f"kho gom ảnh từ {len(bai)} bài — dùng chéo được")
    except Exception as e:
        _bao(False, "đọc được sổ kho ảnh", str(e)[:60])


def tang_chuoi_xong_bao():
    """CHUỖI MÁY TỰ CHẠY XONG THÌ TRANG CÓ BIẾT KHÔNG.

    Anh bắt 16/08: "báo gán nháp tài nguyên rồi mà không thấy, phải tải lại trang mới
    có". Hai gốc:
    ① Người canh job (`theoDoiSauDuyet`) chỉ sống trong TRANG ĐÃ BẤM Duyệt lời. Reload
       hay mở bài khác giữa chừng là mất người canh — chuỗi xong chẳng ai nạp lại kho.
    ② Sổ `VIEC_JOB_MA` (job này của bài nào) lập 14/08 nhưng chỉ 4 trong 21 đường tạo
       job nhớ ghi vào; 17 đường còn lại đẻ job VÔ DANH. Trạm biết có việc đang chạy mà
       không biết của bài nào → không báo được cho trang nào cả.

    Vá 17 chỗ bằng tay thì chắc chắn sót và đường thứ 22 lại quên, nên ghi sổ ở MỘT CỬA:
    phản hồi POST nào mang mã job thì tự ghi.
    """
    print("⑬ CHUỖI MÁY TỰ CHẠY XONG → TRANG TỰ NẠP LẠI")
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()
    ui = open(os.path.join(TRAM, "tram-tai-nguyen.html"), encoding="utf-8").read()

    _bao("self._ma_bai_than = str(than.get(\"ma\")" in src,
         "mọi lượt POST đều nhớ mình thuộc bài nào")
    _bao("VIEC_JOB_MA[jid] = bai" in src,
         "ghi sổ job→bài ở MỘT CỬA (không vá 21 chỗ rời rạc)")
    _bao("isinstance(jid, str)" in src,
         "chỉ chuỗi mã job mới ghi sổ (/api/dong-ho cũng trả khoá 'job' nhưng là dict)")
    _bao("self._ma_bai_than = \"\"" in src,
         "dọn dấu vết sau mỗi lượt POST (keep-alive dùng lại handler)")
    _bao('"job_xong": xong_dh' in src, "trạm trả SỐ LUỸ KẾ job đã xong của bài")
    _bao("_jobXongTruoc" in ui and "await napViec(ma)" in ui,
         "trang so số luỹ kế rồi tự nạp lại kho")
    _bao("if (ma !== m) _jobXongTruoc = null;" in ui,
         "đổi bài thì đếm lại từ đầu (không thì nạp lại vô cớ)")

    # Đường tạo job mới sau này cũng phải đi qua cửa ấy — đếm để biết khi nào lệch
    n_job = len(re.findall(r'ma_job = f"', src))
    _bao(n_job >= 20, f"đếm được {n_job} đường tạo job — tất cả đi chung một cửa ghi sổ")


def tang_bao_ban_moi():
    """MÁY PHỤ CÓ BIẾT KHI ANH ĐẨY BẢN MỚI KHÔNG (anh hỏi 16/08).

    Trước nay: không. Anh nâng cấp ở máy Mac, máy phụ phải tự nhớ chạy `git pull` —
    nhớ vài hôm rồi quên, làm cả tuần trên bản cũ mà không hay biết. Cùng họ với lỗi
    extension chạy bản cũ (15/08): thứ được nạp một lần thì phải TỰ KHAI phiên bản.
    """
    print("⑫ NHẮC NÂNG CẤP CHO MÁY PHỤ")
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()
    ui = open(os.path.join(TRAM, "tram-tai-nguyen.html"), encoding="utf-8").read()
    goc = os.path.dirname(TRAM)

    _bao("def _do_ban_moi(" in src and "ls-remote" in src,
         "trạm tự hỏi GitHub xem có bản mới (ls-remote, không tải mã)")
    _bao("threading.Thread(target=_canh_ban_moi" in src,
         "hỏi trong LUỒNG NỀN — mỗi lượt mất ~1,1 giây, đừng để nó chặn trang")
    _bao('d_k["ban_moi"] = dict(BAN_MOI)' in src,
         "đi nhờ lượt gọi /api/dang-keo đã có sẵn, không đẻ đường hỏi mới")
    _bao('"/api/cap-nhat"' in src, "có cửa cập nhật một nút")
    _bao("đang có" in src and "việc chạy dở" in src,
         "cửa cập nhật TỪ CHỐI khi có việc đang chạy (restart giữa chừng là mất bài)")
    _bao('"pull", "--ff-only"' in src,
         "pull --ff-only: máy phụ lỡ sửa mã thì dừng và nói thẳng, không tự trộn")
    _bao("bangBanMoi" in ui and "bmCapNhat" in ui, "trang có dải nhắc + nút cập nhật")

    # Thoát xong PHẢI có ai bật lại, không thì cập nhật = tắt hẳn trạm
    plist = os.path.expanduser("~/Library/LaunchAgents/com.socbongda247.tram.plist")
    if os.path.exists(plist):
        _bao("<key>KeepAlive</key><true/>" in open(plist, encoding="utf-8").read(),
             "macOS: launchd tự bật lại trạm sau khi nó thoát")
    cai = open(os.path.join(goc, "cai-windows.ps1"), encoding="utf-8").read()
    _bao("-RestartCount" in cai, "Windows: bộ cài đăng ký Task CÓ tự bật lại")
    cn = open(os.path.join(goc, "capnhat.ps1"), encoding="utf-8").read()
    _bao("RestartCount = 999" in cn,
         "Windows: capnhat.ps1 vá được Task đã cài trước 16/08 (thiếu tự bật lại)")


def tang_vua_o():
    """NÚT ⇥ VỪA Ô — kéo đoạn cắt về đúng độ dài ô cảnh.

    Anh báo 16/08: "dùng được một lần sau đó không thấy nó hiện nữa khi đang biên tập
    cùng một content". Tái hiện được, và hoá ra HAI lỗi chồng nhau:

    ① `tuDoiThiDenTheo()` (chạy mỗi lần TUA video, gõ ô Từ, bấm "⏱ Từ =") tự dựng lại
       dòng chữ `#mcDai` mà KHÔNG đụng tới nút `#mcVuaO`. Nút bị `display:none` từ lần
       bấm trước, chỉ `capNhatMc()` mới bật lại được — nên nút kẹt ẩn dù đoạn đã lệch ô.
    ② `oGiay()` nhận mã ô PHỤ dạng "5:0" rồi làm `+"5:0"` → NaN → trả 0. Ô phụ coi như
       không có độ dài: dòng "· ô cần 3.9s" biến mất, nút tắt vĩnh viễn. Chạm vào một
       cảnh phụ là hỏng cho tới khi đóng mở lại cửa cắt.
    """
    print("⑪ NÚT ⇥ VỪA Ô (cửa cắt clip)")
    ui = open(os.path.join(TRAM, "tram-tai-nguyen.html"), encoding="utf-8").read()

    i = ui.find("function tuDoiThiDenTheo()")
    than = ui[i:ui.find("\n}", i)] if i > 0 else ""
    _bao("capNhatMc();" in than,
         "tuDoiThiDenTheo giao cho capNhatMc lo trọn vùng (không tự viết nửa vời)")
    _bao("$('#mcDai').textContent" not in than,
         "chỉ MỘT nơi dựng dòng chữ độ dài — hai nơi thì cái sau để lại nửa vời")

    j = ui.find("function oGiay(")
    than_o = ui[j:ui.find("\n}", j)] if j > 0 else ""
    _bao("String(iCau).split(':')" in than_o,
         "oGiay hiểu mã Ô PHỤ dạng \"5:0\" (cảnh phụ cũng phải kéo vừa ô)")

    # Mọi đường đổi mốc đều phải chạy qua capNhatMc, không đường nào được đi tắt
    for ten, dau in (("gõ ô Từ", "$('#mcTu').oninput"),
                     ("gõ ô Đến", "$('#mcDen').oninput"),
                     ("bấm ⏱ Từ =", "$('#mcLayTu').onclick"),
                     ("bấm ⏱ Đến =", "$('#mcLayDen').onclick"),
                     ("đổi cảnh", "$('#mcCau').onchange")):
        k = ui.find(dau)
        doan = ui[k:k + 200] if k > 0 else ""
        _bao("capNhatMc" in doan or "tuDoiThiDenTheo" in doan,
             f"{ten} → có cập nhật lại nút vừa ô")


def tang_kho_video():
    """KHO VIDEO — bộ lọc gốc/cắt, và video gốc có thật sự vào kho không.

    Vì sao thành cổng (anh báo 16/08): "video gốc tải về phục vụ những video gần đây
    không hiển thị trong kho". Gốc: đường gắp video của extension chỉ lưu vào
    `<bài>/clip/tay/`, KHÔNG nhập kho — chỉ đoạn ĐÃ CẮT mới vào. Kho có 26 đoạn cắt mà
    chỉ 2 video gốc, trong khi ổ máy có 38 video gốc nằm rải rác không ai thấy.
    """
    print("⑩ KHO VIDEO (lọc gốc/cắt · video gốc có vào kho không)")
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()
    ui = open(os.path.join(TRAM, "tram-tai-nguyen.html"), encoding="utf-8").read()

    _bao('loc_vb = (q.get("loai")' in src, "server nhận bộ lọc loai=goc|cat")
    _bao('"so_goc": so_goc' in src, "server trả số lượng từng loại để trang hiện lên nút")
    _bao("kbLocLoai" in ui and 'data-loc="goc"' in ui and 'data-loc="cat"' in ui,
         "trang có ba chip lọc: tất cả · gốc · cắt")
    _bao("$('#kbLocLoai').style.display = tab === 'video'" in ui,
         "chip lọc chỉ hiện ở tab Video (ảnh không có gốc/cắt)")
    _bao("_kbMa = '';" in ui, "đổi bộ lọc thì nạp lại thật, không bị 'bài này nạp rồi' chặn")
    # LƯỚI VẼ LẠI KHÔNG ĐƯỢC DÙNG loading="lazy" (bắt được 16/08 khi test bằng trình
    # duyệt thật): sau khi bấm chip lọc, innerHTML dựng ảnh mới mà trình duyệt KHÔNG kích
    # hoạt lazy cho chúng — network cho thấy nó vẫn tải ảnh của lượt trước, còn ảnh đang
    # hiện thì chưa từng được yêu cầu. Kết quả: 18 ô video gốc trống trơn, không báo lỗi.
    # Soi ĐÚNG thẻ ảnh, đừng soi cả khối: bình luận giải thích ngay trên nó cũng nhắc
    # chữ `loading="lazy"`, cắt khối theo độ dài là bắt oan chính lời giải thích.
    _bao('<img src="${esc(v.thumb)}" loading="lazy"' not in ui
         and '<img src="${esc(v.thumb)}" decoding="async"' in ui,
         'lưới VIDEO không dùng lazy (lưới vẽ lại thì lazy không kích hoạt)')

    # Tên video gắp về phải mang nội dung bài — nhưng PHẢI giữ tiền tố tay_NN, vì mọi
    # phép đếm số thứ tự và glob dọn rác trong hệ đều dựa vào nó.
    _bao("ten_noi_dung = slug_hoa(" in src, "video gắp về đặt tên theo nội dung bài")
    _bao('cuoi = f"tay_{n:02d}"' in src and '"-o", os.path.join(thu, f"{cuoi}.%(ext)s")' in src,
         "tên mới GIỮ tiền tố tay_NN (glob và phép đếm số không gãy)")

    # slug_hoa phải là MỘT nguồn — hai bản sẽ lệch nhau
    b3 = open(os.path.join(os.path.dirname(TRAM), "buoc3_xepkho.py"), encoding="utf-8").read()
    _bao("from chuan_ten import slug_hoa" in b3 and "def slug_hoa" not in b3,
         "slug_hoa chỉ có MỘT bản (chuan_ten.py)")

    # Kho thật: video gốc đã vào chưa
    try:
        import duong_dan as _DD
        kv = os.path.join(_DD.KHO_TAI_NGUYEN, "video-chu-the")
        so_v = [json.loads(l) for l in open(os.path.join(kv, "so-video.jsonl"),
                                            encoding="utf-8") if l.strip()]
        n_goc = len([m for m in so_v if m.get("loai") == "goc"])
            # VIDEO GỐC PHẢI TỰ VÀO KHO khi xếp kho (anh chốt 16/08). Cùng họ lỗi với đoạn
        # cắt 14/08, chỉ khác tầng — đoạn cắt có đường về kho, bản gốc thì không.
        src_v = open(os.path.join(os.path.dirname(TRAM), "nhap_kho_video.py"),
                     encoding="utf-8").read()
        _bao("def nhap_goc_bai(" in src_v, "có hàm nhập VIDEO GỐC của bài vào kho")
        _bao("n_goc = nhap_goc_bai(viec)" in src_v,
             "xếp kho kéo theo cả video gốc (một đường chạy, không đẻ tiến trình thứ ba)")
        _bao(n_goc >= 5, f"kho có video GỐC để anh mở ra cắt — {n_goc} bản",
             "kho gần như chỉ có đoạn đã cắt" if n_goc < 5 else "")
        mat = [m for m in so_v if not os.path.exists(os.path.join(kv, m.get("tep", "")))]
        _bao(not mat, "mọi mục trong sổ kho video đều còn tệp thật",
             f"{len(mat)} mục trỏ tới tệp đã mất" if mat else "")
    except Exception as e:
        _bao(False, "đọc được sổ kho video", str(e)[:70])


def tang_dua_ghi():
    """NHẬN NHIỀU TẤM CÙNG LÚC CÓ MẤT KHÔNG — chạy thật, không đọc mã đoán.

    Vì sao thành cổng: 16/08 anh báo "tải ảnh lúc được lúc không, ảnh 2·3·4 phải bấm
    tải lại trang mới thấy". Bắn 6 lượt ĐỒNG THỜI vào cửa nhận: MẤT SẠCH cả 6 tấm.
    Gốc là `_so_tiep()` đặt tên bằng cách ĐẾM TỆP ĐANG CÓ — sáu luồng cùng ra `n00`,
    đè nhau, rồi khâu chống trùng `os.remove` mất tệp luồng khác đang đọc dở.

    Cổng này gọi thẳng `gap_anh.nhan_tep` từ 6 luồng nên chạy được cả khi trạm tắt,
    và chạy được trên máy Windows.
    """
    print("⑨ NHẬN NHIỀU TẤM CÙNG LÚC (đua ghi)")
    goc = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(goc, "tram"))
    try:
        import gap_anh
        from PIL import Image, ImageDraw
    except ImportError as e:
        _bao(False, "nạp được gap_anh để thử", str(e))
        return

    def anh(i):
        im = Image.new("RGB", (1920, 1080), (255, 255, 255))
        d = ImageDraw.Draw(im)
        for o in range(12):                     # bàn cờ 4×3 theo bit của i — khác BỐ CỤC
            if (i * 7 + 1) >> (o % 8) & 1:      # THÔ, đúng thứ vân tay dHash nhìn
                x, y = (o % 4) * 480, (o // 4) * 360
                d.rectangle([x, y, x + 479, y + 359], fill=(10, 10, 10))
        b = io.BytesIO()
        im.save(b, "JPEG", quality=92)
        return b.getvalue()

    thu = tempfile.mkdtemp(prefix="soc-kiem-dua-")
    try:
        N = 6
        lo = [threading.Thread(target=lambda i=i: gap_anh.nhan_tep(
            [(f"thu{i}.jpg", anh(i), "", "")], thu)) for i in range(N)]
        [t.start() for t in lo]
        [t.join() for t in lo]
        con = sorted(f for f in os.listdir(thu) if f.endswith(".jpg"))
        _bao(len(con) == N, f"{N} tấm gửi cùng lúc thì còn đủ {N}",
             f"chỉ còn {len(con)}: {con}" if len(con) != N else "")
        _bao(len(set(con)) == len(con), "không tấm nào trùng tên tấm khác")
        p_vt = os.path.join(thu, "van-tay.json")
        vt = json.load(open(p_vt, encoding="utf-8")) if os.path.exists(p_vt) else {}
        _bao(len(vt) == len(con), "sổ vân tay khớp số ảnh (không bị đè)",
             f"sổ {len(vt)} ≠ ảnh {len(con)}" if len(vt) != len(con) else "")
    finally:
        shutil.rmtree(thu, ignore_errors=True)

    # Đường VIDEO cùng họ bệnh: số thứ tự tính bằng glob. Kiểm bằng chuỗi vì tải video
    # thật thì chậm và phụ thuộc mạng.
    src = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()
    _bao("O_CREAT | os.O_EXCL" in src, "video: xí số thứ tự nguyên tử (O_EXCL)")
    _bao('glob.glob(os.path.join(thu, f"tay_{n:02d}*"))' in src,
         "video: đếm số nhìn CẢ tệp đang tải (.part), không chỉ .mp4")
    _bao('d["xong"] = d.get("xong", 0)' in src,
         "bộ đếm luỹ kế để trang biết có hàng mới (poll không trượt)")
    ui = open(os.path.join(TRAM, "tram-tai-nguyen.html"), encoding="utf-8").read()
    _bao("_xongTruoc" in ui, "trang nạp lại kho theo số luỹ kế, không rình trạng thái tức thời")


def tang_may_phu():
    """CÀI ĐƯỢC TRÊN MÁY PHỤ KHÔNG — kiểm tài liệu và bộ cài có khớp thực tế không.

    Vì sao thành cổng: 15/08 máy Windows dán link kho vào Claude Code thì chỉ thấy
    404. Gốc: kho RIÊNG TƯ. Tệ hơn, chính bộ cài "một dòng" của em cũng chết cùng lý
    do — `irm raw.githubusercontent.com/...` cũng đọc kho riêng tư. Tức hướng dẫn cài
    em viết hôm trước CHƯA BAO GIỜ chạy được, mà em vẫn báo xong.

    Bài học: tài liệu cài đặt là MÃ CHẠY TRÊN MÁY NGƯỜI KHÁC. Không thử được thì ít
    nhất phải có cổng canh những giả định nó dựa vào.
    """
    print("⑦ MÁY PHỤ CÀI ĐƯỢC KHÔNG (bộ cài + tài liệu)")
    goc = os.path.dirname(os.path.abspath(__file__))

    cai = open(os.path.join(goc, "cai-windows.ps1"), encoding="utf-8").read()
    # Kho để CÔNG KHAI từ 16/08 nên lệnh cài không cần khoá. Nhưng bộ cài phải chạy được
    # CẢ HAI trạng thái — anh đổi kho về riêng tư lúc nào là quyền của anh, mà lúc ấy máy
    # phụ không được đứng chết với một lỗi 404 khó hiểu.
    _bao("$KEY" in cai and "Bearer $KEY" in cai,
         "bộ cài vẫn có đường khoá đọc, phòng khi kho đổi về riêng tư")
    _bao("kho công khai — không cần khoá" in cai,
         "kho công khai thì bộ cài KHÔNG hỏi khoá (đừng bắt người dùng nhập thứ vô nghĩa)")
    _bao("Kho có thể đã đổi về RIÊNG TƯ" in cai,
         "clone hỏng thì hỏi khoá tại chỗ, không chết câm")
    _bao("api.github.com/repos/anhlt148/socbongda247" in cai,
         "bộ cài THỬ khoá trước khi clone (sai thì báo ngay, không để 404 khó hiểu)")
    _bao("git credential approve" in cai,
         "khoá cất vào kho khoá Windows, không nhét vào địa chỉ kho")
    _bao("remote set-url origin $KHO" in cai,
         "đường dự phòng có LAU khoá khỏi địa chỉ kho")

    # Số bước phải liên tục 1,2,3… — chèn khối mới mà quên đánh lại số thì người
    # ngồi máy kia thấy "[3]" hai lần, tưởng script chạy lặp.
    so = [int(m) for m in re.findall(r'^Buoc (\d+) "', cai, re.M)]
    _bao(so == list(range(1, len(so) + 1)),
         f"số bước bộ cài liên tục 1..{len(so)}", f"đang là {so}" if so != list(range(1, len(so) + 1)) else "")

    _bao(os.path.exists(os.path.join(goc, "capnhat.ps1")),
         "có lệnh nâng cấp một dòng cho máy phụ (capnhat.ps1)")
    cn = open(os.path.join(goc, "capnhat.ps1"), encoding="utf-8").read() \
         if os.path.exists(os.path.join(goc, "capnhat.ps1")) else ""
    _bao("git" in cn and "schtasks" in cn and "extension" in cn.lower(),
         "lệnh nâng cấp lo ĐỦ BA phần: mã · trạm · extension")

    # Mọi tài liệu chỉ cách cài đều phải mang khoá — sót một tệp là người kia làm
    # theo tệp đó rồi tắc.
    # Lệnh cài trong tài liệu phải KHỚP trạng thái thật của kho — hỏi thẳng GitHub, đừng
    # đoán. Tài liệu bảo "dán khoá" mà kho công khai thì người đọc loay hoay tạo khoá vô
    # ích; ngược lại thì họ dán lệnh trần rồi ăn 404.
    rieng = None
    try:
        r = subprocess.run(["gh", "repo", "view", "anhlt148/socbongda247",
                            "--json", "isPrivate", "-q", ".isPrivate"],
                           capture_output=True, text=True, timeout=25)
        if r.returncode == 0:
            rieng = r.stdout.strip() == "true"
    except Exception:
        pass
    if rieng is None:
        print("   ·  (bỏ qua kiểm khớp tài liệu — không hỏi được GitHub)")
    else:
        for ten in ("README.md", "CLAUDE.md", "HUONG-DAN-MAY-MOI.md"):
            t = open(os.path.join(goc, ten), encoding="utf-8").read()
            if "cai-windows.ps1 | iex" not in t:
                continue
            # Bỏ khối <details> — đó là đường DỰ PHÒNG cố ý giữ lại (hướng dẫn cấp khoá
            # khi kho đổi về riêng tư), không phải lệnh cài người dùng đọc hằng ngày.
            chinh = re.sub(r"<details>.*?</details>", "", t, flags=re.S)
            co_khoa = "Bearer $T" in chinh
            _bao(co_khoa == rieng,
                 f"{ten}: lệnh cài khớp kho {'RIÊNG TƯ' if rieng else 'CÔNG KHAI'}",
                 "tài liệu đòi khoá mà kho công khai" if co_khoa and not rieng
                 else ("kho riêng tư mà lệnh cài không mang khoá" if rieng and not co_khoa else ""))


def tang_windows():
    """CHẠY ĐƯỢC TRÊN MÁY THỨ HAI KHÔNG — nạp thử mọi module trong môi trường GIẢ
    WINDOWS (chặn `fcntl`, thứ chỉ có trên Unix).

    Vì sao thành cổng: 15/08 anh hỏi "đã ổn để chạy trên máy kia chưa", rà mới lộ ra
    TRẠM KHÔNG KHỞI ĐỘNG NỔI — 6 tệp `import fcntl` là ImportError ngay dòng đầu.
    Trước đó em đã báo xong vì chỉ rà LỆNH hệ điều hành mà quên rà MODULE. Cổng này
    bắt được cả họ lỗi ấy, không riêng fcntl.
    """
    print("⑥ CHẠY ĐƯỢC TRÊN WINDOWS (nạp thử trong môi trường giả)")
    import tempfile as _tf
    gia = os.path.join(_tf.mkdtemp(), "gia-windows")
    os.makedirs(gia, exist_ok=True)
    for m in ("fcntl", "pwd", "grp", "termios"):        # module chỉ có trên Unix
        open(os.path.join(gia, m + ".py"), "w").write(
            f"raise ImportError(\"No module named '{m}'\")\n")
    mod = ["duong_dan", "nen_tang", "kich_ban", "chuan_ten", "nhip_canh", "dong_ho",
           "nhap_kho_chu_the", "nhap_kho_video", "xuong", "buoc3_xepkho"]
    ma = ("import sys; sys.path.insert(0, %r); sys.path[1:1] = [%r, %r]\n"
          % (gia, MAY, TRAM))
    for m in mod + ["tram_tai_nguyen"]:
        r = subprocess.run(
            [sys.executable, "-c", ma + f"import {m}"],
            capture_output=True, text=True, timeout=120,
            cwd=TRAM if m == "tram_tai_nguyen" else MAY)
        vet = (r.stderr or "").strip().splitlines()
        _bao(r.returncode == 0, f"nạp được khi KHÔNG có fcntl · {m}",
             vet[-1][:70] if vet and r.returncode else "")


def tang3_route():
    print("③ ROUTE SỐNG")
    try:
        with urllib.request.urlopen(CONG + "/", timeout=10) as r:
            song = r.status == 200
    except Exception as e:
        _bao(False, "trạm đang chạy", str(e)[:60])
        return None
    _bao(song, "trạm đang chạy")
    ma = None
    try:
        _, d = _get("/api/dang-lam")
        ma = d.get("ma")
        _bao(bool(ma), "/api/dang-lam", ma or "")
    except Exception as e:
        _bao(False, "/api/dang-lam", str(e)[:60])
    duong = ["/api/viec", "/api/kho-nha-ds?q=&loc=tat_ca&trang=0",
             "/api/kho-video-ds?q=&loc=tat_ca&trang=0", "/api/kho-nha-chuthe",
             "/api/kho-nha?q=" + urllib.request.quote("việt nam")]
    if ma:
        m_q = urllib.request.quote(ma, safe="")
        duong += [f"/api/viec/{m_q}", f"/api/kho-moi/{m_q}",
                  f"/api/kho-nha-bai?ma={m_q}&gioi_han=150&bo_qua=0"]
    for u in duong:
        try:
            ma_tt, d = _get(u)
            _bao(ma_tt == 200, u.split("?")[0], f"{ma_tt}")
        except Exception as e:
            _bao(False, u.split("?")[0], str(e)[:70])
    if ma:                                          # payload phải mang đủ trường sổ
        try:
            _, d = _get("/api/viec/" + urllib.request.quote(ma, safe=""))
            if d.get("loi"):
                _bao(False, "payload /api/viec", "trạm báo: " + str(d["loi"])[:70])
            else:
                thieu = [t for t in TRUONG_SO if t not in d]
                _bao(not thieu, "payload /api/viec mang đủ trường sổ", " · ".join(thieu))
        except Exception as e:
            _bao(False, "payload /api/viec", str(e)[:60])
    return ma


def tang4_luong(ma):
    """Cửa NHẬN ẢNH của extension — chính đường đã chết câm 11/08."""
    print("④ LUỒNG CỐT LÕI (cửa nhận ảnh extension)")
    import base64
    import io
    try:
        from PIL import Image
    except ImportError:
        canh.append("không có PIL — bỏ qua tầng ④")
        return
    b = io.BytesIO()
    Image.new("RGB", (900, 600), (33, 88, 33)).save(b, "JPEG")
    b64 = base64.b64encode(b.getvalue()).decode()

    def post(d, than):
        r = urllib.request.Request(CONG + d, json.dumps(than).encode(),
                                   {"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=90) as x:
            return json.loads(x.read().decode())
    if ma:
        try:
            r = post("/api/tai-len", {"ma": ma, "tep": [
                {"ten": "zz-kiem.jpg", "data": b64, "url": "https://kiem/zz.jpg",
                 "trang": "https://kiem"}]})
            # "TRÙNG" cũng tính là ĐẠT: cửa vẫn sống, chỉ là vân tay còn sót từ lượt kiểm
            # trước. Điều cổng này canh là CỬA CÓ THÔNG hay không, không phải ảnh có mới.
            thong = bool(r.get("anh")) or any("TRÙNG" in (h.get("loi") or "")
                                              for h in (r.get("hong") or []))
            _bao(thong, "extension → kho BÀI (/api/tai-len)", str(r)[:60])
            base = os.path.join(DD.VIEC, ma, "anh") + os.sep
            for a in (r.get("anh") or []):          # dọn ngay, không để rác trong bài
                for p in (base + a["tep"], base + "_thumb/anh__" + a["tep"]):
                    os.path.exists(p) and os.remove(p)
            # DỌN CẢ VÂN TAY. Quên khâu này thì lượt kiểm sau bị chính mình chặn vì
            # "trùng" — cổng tự làm bẩn chỗ nó đứng. (Lỗi có sẵn, chỉ lộ ra sau khi vá
            # đua ghi 16/08: trước đó sổ vân tay bị đè nên vô tình sạch.)
            for ten_so in ("van-tay.json", "van-tay-loi.json"):
                p_vt = base + ten_so
                if not os.path.exists(p_vt):
                    continue
                try:
                    so = json.load(open(p_vt, encoding="utf-8"))
                    bo = [a["tep"] for a in (r.get("anh") or [])]
                    con = {k: v for k, v in so.items() if k not in bo}
                    if len(con) != len(so):
                        json.dump(con, open(p_vt, "w", encoding="utf-8"),
                                  ensure_ascii=False)
                except Exception:
                    pass
            p_sg = os.path.join(DD.VIEC, ma, "anh", "so-gap.jsonl")
            if os.path.exists(p_sg):
                giu = [l for l in open(p_sg, encoding="utf-8")
                       if l.strip() and "zz-kiem" not in l]
                open(p_sg, "w", encoding="utf-8").writelines(giu)
        except Exception as e:
            _bao(False, "extension → kho BÀI (/api/tai-len)", str(e)[:90])
    try:
        r = post("/api/kho-nha-tai-len", {"tep": [
            {"ten": "zz-kiem.jpg", "data": b64, "url": "https://kiem/zz2.jpg",
             "tieu_de": "kiem hoi quy"}]})
        _bao(r.get("ok") is True, "extension → KHO CHUNG (/api/kho-nha-tai-len)",
             str(r)[:60])
        if r.get("so"):                             # dọn tấm vừa nhận
            import fcntl
            KHO = os.path.join(DD.KHO_TAI_NGUYEN, "anh-chu-the")
            SO = KHO + "/so-chu-the.jsonl"
            with open(SO + ".lock", "w") as kh:
                fcntl.flock(kh, fcntl.LOCK_EX)
                ds = [json.loads(l) for l in open(SO, encoding="utf-8") if l.strip()]
                for m in [x for x in ds if x.get("nguon") == "https://kiem/zz2.jpg"]:
                    p = os.path.join(KHO, m["tep"])
                    os.path.exists(p) and os.remove(p)
                ds = [x for x in ds if x.get("nguon") != "https://kiem/zz2.jpg"]
                with open(SO, "w", encoding="utf-8") as f:
                    for m in ds:
                        f.write(json.dumps(m, ensure_ascii=False) + "\n")
    except Exception as e:
        _bao(False, "extension → KHO CHUNG", str(e)[:90])


def tang_nhac():
    """⑥ KHO NHẠC 12 NHÓM — cầu chọn nhạc theo cảm xúc (dựng 12/08/2026).

    Vì sao có cổng này: trước 12/08, `cung_nhac` không ai sinh nên MỌI video rơi về
    đúng một cung nhạc — hỏng suốt nhiều tuần mà không cổng nào kêu. Nay canh cả kho
    lẫn đường chọn, và canh luôn hai bẫy đã trả giá.
    """
    print("⑥ KHO NHẠC + CẦU CHỌN THEO CẢM XÚC")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import chon_nhac as CN
    except Exception as e:
        return _bao(False, "nạp chon_nhac.py", str(e)[:90])

    ok_kho, dong = CN.kiem_kho()
    rong = [d for d in dong if d.startswith("✗")]
    _bao(ok_kho, f"kho 12 nhóm ({len(CN.CUNG_12)} nhóm)",
         "; ".join(rong)[:90] if rong else "")

    # Xưởng phải đi qua cầu, không được tự glob kho nhạc
    try:
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "xuong.py"), encoding="utf-8").read()
        _bao("CN.chon(" in src, "xuong.py gọi cầu chọn nhạc")
        _bao("DD.NHAC," not in src.replace(" ", ""),
             "xuong.py KHÔNG còn tự glob kho nhạc cũ")
    except Exception as e:
        _bao(False, "đọc xuong.py", str(e)[:90])

    # BẪY 1 (12/08): khớp chuỗi trần → "lay" lọt trong "malaysia" → tin đại chiến ra nhạc HÀI
    n, _, _ = CN.doan_cam_xuc("MALAYSIA KHÔNG THỂ DÙNG CHẢO LỬA BUKIT JALIL", "")
    _bao(n != "10_FUN_LIGHT", "không dính bẫy khớp-chuỗi-trần (malaysia→FUN)", n)

    # BẪY 2 (12/08): từ khoá theo CHỦ ĐỀ → nhóm PATRIOTIC nuốt mọi video nhắc tuyển VN
    n2, _, _ = CN.doan_cam_xuc("ĐỘI HÌNH TUYỂN VIỆT NAM ĐẤU MALAYSIA CÓ GÌ ĐÁNG CHÚ Ý", "")
    _bao(n2 != "11_PATRIOTIC_EPIC", "tên đội KHÔNG bị coi là cảm xúc", n2)

    # Không bao giờ trả rỗng — kể cả blueprint trắng trơn
    try:
        pth, nhom, _ = CN.chon({}, "kiem")
        _bao(bool(pth) and os.path.exists(pth), "chon() luôn ra file thật", nhom)
    except Exception as e:
        _bao(False, "chon() với blueprint rỗng", str(e)[:90])

    # Cung cũ vẫn chạy (tương thích ngược)
    try:
        _, nhom_cu, _ = CN.chon({"cung_nhac": "bi_trang"}, "kiem")
        _bao(nhom_cu == "07_SAD_TRIBUTE", "blueprint cung CŨ vẫn quy đúng nhóm", nhom_cu)
    except Exception as e:
        _bao(False, "quy cung cũ", str(e)[:90])



def tang_phong_cach():
    """⑦ PHONG CÁCH — cấu hình phong cách video (anh đặt 12/08/2026).

    Anh chốt: mỗi núm MỘT chỉ số (bỏ dải, bỏ đa dạng hoá). Cổng này canh đúng thứ dễ
    hỏng câm: cấu hình hỏng mà xưởng vẫn chạy hằng số cứng thì không ai biết.
    """
    print("⑦ PHONG CÁCH VIDEO")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import phong_cach as PC
    except Exception as e:
        return _bao(False, "nạp phong_cach.py", str(e)[:90])

    c = PC.doc()
    _bao(isinstance(c, dict) and "zoom_max" in c, "đọc được cấu hình")
    _bao(all(not isinstance(c[k], (list, tuple)) for k in PC.NUM),
         "mọi núm là MỘT chỉ số (không còn dải)")

    # Biên cứng phải chặn số điên — một cú gõ nhầm không được phá video
    xau = PC.chuan({"zoom_max": 99, "giong_toc_do": -5, "nhac_nhom": "khong_co_that",
                    "nhac_vao": 999})
    _bao(1.02 <= xau["zoom_max"] <= 1.20 and xau["nhac_nhom"] == "tu_dong"
         and 0.0 <= xau["nhac_vao"] <= 6.0, "kẹp biên chặn được giá trị điên")

    # Sổ bản CŨ lưu dải → phải tự quy về một số, không được nổ
    try:
        cu_ds = PC.chuan({"zoom_max": [1.07, 1.14],
                          "giong_ds": [{"ma": "x", "ten": "cũ", "toc_do": [1.0, 1.2]}]})
        _bao(not isinstance(cu_ds["zoom_max"], list)
             and not isinstance(cu_ds["giong_ds"][0]["toc_do"], list),
             "sổ bản CŨ (dải) tự quy về một số")
    except Exception as e:
        _bao(False, "đọc sổ bản cũ", str(e)[:80])

    # Cùng cấu hình → mọi video cùng thông số (đúng ý anh: không xoay nữa)
    a1, b1 = PC.cho_video("x/video-1"), PC.cho_video("x/video-2")
    _bao(a1["zoom_max"] == b1["zoom_max"] == c["zoom_max"],
         "mọi video dùng đúng chỉ số anh đặt")

    # Xưởng phải THẬT SỰ dùng
    try:
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "xuong.py"), encoding="utf-8").read()
        _bao("PC.cho_video(" in src, "xuong.py lấy thông số từ cấu hình")
        _bao("volume=0.11" not in src, "xuong.py KHÔNG còn âm lượng nhạc cứng")
        _bao("tran=ts[" in src, "trần một kiểu truyền tay (không dính tham số mặc định)")
        for ten, khoa in (("giọng vào", "ts[\"giong_vao\"]"), ("giọng ra", "ts[\"giong_ra\"]"),
                          ("nhạc vào", "ts[\"nhac_vao\"]"), ("nhạc ra", "ts[\"nhac_ra\"]")):
            _bao(khoa in src, f"xưởng dùng núm {ten}")
        # afade d=0 là LỖI ffmpeg — phải bỏ hẳn bộ lọc, không được truyền 0
        _bao("if vao > 0:" in src and "if ra > 0:" in src,
             "núm để 0 thì BỎ bộ lọc afade (d=0 là lỗi ffmpeg)")
    except Exception as e:
        _bao(False, "đọc xuong.py", str(e)[:90])

    # GIỌNG
    _bao(len(c.get("giong_ds") or []) >= 1, "danh sách giọng không rỗng",
         f"{len(c.get('giong_ds') or [])} giọng")
    _bao(len(PC.chuan({"giong_ds": []})["giong_ds"]) >= 1,
         "xoá hết giọng → tự trả về giọng đang chạy")
    _bao(bool(a1.get("giong_ma")), "cho_video trả mã giọng", a1.get("giong_ma", "")[:34])
    try:
        srcx = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "xuong.py"), encoding="utf-8").read()
        _bao("van_tay = f\"{ts['giong_ma']}" in srcx,
             "đệm giọng gồm MÃ GIỌNG (đổi giọng là đọc lại)")
    except Exception:
        pass

    for d in ("/phong-cach", "/api/phong-cach"):
        try:
            r = urllib.request.urlopen(CONG + d, timeout=8)
            _bao(r.status == 200, f"{d} — {r.status}")
        except Exception as e:
            _bao(False, d, str(e)[:70])
    try:
        rq = urllib.request.Request(CONG + "/api/thu-giong", data=b'{"ma":""}',
                                    headers={"Content-Type": "application/json"})
        _bao(urllib.request.urlopen(rq, timeout=10).status == 200, "/api/thu-giong — 200")
    except Exception as e:
        _bao(False, "/api/thu-giong", str(e)[:70])

    # Luật MENU CHUNG (anh chốt 10/08)
    try:
        mjs = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "tram", "menu.js"), encoding="utf-8").read()
        _bao("/phong-cach" in mjs, "trang có trong menu chung")
    except Exception as e:
        _bao(False, "đọc menu.js", str(e)[:70])


def tang_tai_video():
    """㉓ CÔNG CỤ TẢI VIDEO — bệnh NỀN, không ai thấy tới lúc anh đang làm thì hỏng.

    Anh báo 19/08: extension không tải được video YouTube, báo "Requested format is not
    available". Video ấy CÓ đủ format tới 1080p, chạy tay thì ngon. Thủ phạm: yt-dlp
    CŨ NĂM THÁNG (bản 17/03 trong khi bản mới là 04/07) — YouTube đổi cách chặn liên
    tục nên công cụ cũ là hết đường.

    Loại bệnh này không có cổng nào bắt được, vì mã không sai dòng nào. Nên cổng đây
    canh TUỔI công cụ, và canh cả ba bài học rút ra sau vụ ấy.
    """
    print("㉓ CÔNG CỤ TẢI VIDEO (yt-dlp)")
    try:
        sys.path.insert(0, MAY)
        import yt_tai as _YT
        pb = _YT.phien_ban()
        cu, tuoi = _YT.qua_cu(pb)
        _bao(bool(pb), f"có yt-dlp trên máy — bản {pb or 'KHÔNG THẤY'}")
        _bao(not cu, f"yt-dlp còn dùng được ({tuoi} ngày tuổi, hạn {_YT.HAN_NGAY} ngày)"
                     + ("" if not cu else " → chạy: brew upgrade yt-dlp"))
        tt = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()
        nk = open(os.path.join(MAY, "nhap_kho_video.py"), encoding="utf-8").read()
        _bao("YT.FORMAT" in tt and "YT.FORMAT" in nk,
             "hai đường tải dùng CHUNG một luật định dạng, không lệch nhau")
        _bao("YT.them_cua" in tt and "YT.them_cua" in nk,
             "trượt thì ĐỔI CỬA hỏi YouTube rồi thử lại, không bỏ cuộc ngay")
        _bao("YT.dang_thu_lai" in tt and "YT.dang_thu_lai" in nk,
             "video bị gỡ/riêng tư thì dừng luôn, không thử vô ích bốn lượt")
        _bao("YT.doi_loi" in tt and "YT.doi_loi" in nk,
             "lỗi dịch sang câu anh đọc là hiểu, không phun tiếng Anh của yt-dlp")
        _bao(_YT.dang_thu_lai("Requested format is not available")
             and not _YT.dang_thu_lai("Private video"),
             "phân biệt đúng lỗi đáng thử lại và lỗi vô vọng")
    except Exception as e:
        _bao(False, f"cổng yt-dlp lỗi: {type(e).__name__}: {e}")


def tang_extension():
    """⑧ TIỆN ÍCH CHROME — nơi code sống NGOÀI thư mục máy, dễ lọt khỏi mọi cổng khác.

    Ba bệnh canh ở đây, cả ba đều thuộc loại LỖI CÂM (bấm mà không có gì xảy ra):
    · khai phím tắt / mục menu mà quên viết nhánh xử lý → "có nút mà không chạy"
    · viết luồng gửi ảnh SONG SONG thay vì dùng lại guiAnh/guiAnhKho → mất cổng
      watermark, mất chống trùng vân tay (đúng bệnh dải kho tự viết `kbLay`)
    · phím tắt chỉ làm một đích trong khi menu có hai → luật "chính có gì phụ có nấy"
    """
    print("⑧ TIỆN ÍCH CHROME (extension)")
    EXT = os.path.join(TRAM, "extension")
    mp = os.path.join(EXT, "manifest.json")
    try:
        mf = json.load(open(mp, encoding="utf-8"))
        _bao(True, "manifest.json đọc được")
    except Exception as e:
        _bao(False, "manifest.json đọc được", str(e)[:70])
        return
    js_files = ["nen.js", "bang.js", "lop-chon.js"]
    if subprocess.run(["which", "node"], capture_output=True).returncode == 0:
        for f in js_files:
            p = os.path.join(EXT, f)
            if not os.path.exists(p):
                continue
            r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
            _bao(r.returncode == 0, f"cú pháp {f}",
                 (r.stderr or "").splitlines()[-1][:70] if r.returncode else "")
    nen = open(os.path.join(EXT, "nen.js"), encoding="utf-8").read()

    # ⑧a phím tắt khai ↔ xử lý (thiếu vế nào cũng là bấm phím không thấy gì xảy ra)
    khai = set((mf.get("commands") or {}).keys())
    xuly = set(re.findall(r'"(soc-phim-[a-z0-9-]+)"\s*:', nen))
    _bao(khai == xuly, "phím tắt: manifest ↔ nen.js khớp",
         f"thừa manifest {sorted(khai - xuly)} · thừa js {sorted(xuly - khai)}"
         if khai != xuly else "")
    _bao("chrome.commands.onCommand" in nen, "có người nghe phím tắt (onCommand)")

    # ⑧m PHÍM TẮT TẢI VIDEO (anh đặt 16/08: "bấm phím tắt là tải được video luôn từ
    #    các web, giống như tải ảnh"). Khác ảnh ở chỗ KHÔNG có con trỏ chỉ đúng cái
    #    nào — mã phải tự đoán, nên ba lớp dò phải còn đủ.
    _bao("soc-phim-video" in (mf.get("commands") or {}), "manifest khai phím tắt VIDEO")
    _bao("function _docVideoTrang" in nen, "có mắt dò video trong trang")
    _bao("og:video" in nen, "lớp dò 2: thẻ meta og:video")
    _bao("application/ld+json" in nen and "contentUrl" in nen,
         "lớp dò 3: khối JSON-LD (đường DUY NHẤT ăn với báo VN — đo thật VnExpress)")
    _bao("querySelectorAll(\"video\")]" in nen and "width >= 80" not in nen,
         "KHÔNG lọc thẻ video theo bề ngang (chưa bấm play thì width = 0)")
    src_t = open(os.path.join(TRAM, "tram_tai_nguyen.py"), encoding="utf-8").read()
    _bao("la_media" in src_t and "m3u8" in src_t,
         "trạm thử LINK MEDIA trước địa chỉ trang khi extension bóc được link thật")

    # ⑧l EXTENSION BÁO KHI CHẠY BẢN CŨ (anh hỏi 15/08: "sau này extension vẫn cập
    #    nhật được chứ?"). Extension nạp kiểu "giải nén": git pull về file mới mà
    #    Chrome vẫn chạy bản đã nạp cho tới khi bấm ⟳ Tải lại — lỗi ÂM THẦM, trông
    #    vẫn chạy nhưng thiếu đúng tính năng vừa thêm.
    _bao("chrome.runtime.getManifest().version" in nen and "ext=" in nen,
         "extension gửi phiên bản của nó lên trạm")
    _bao('"ext_cu"' in open(os.path.join(TRAM, "tram_tai_nguyen.py"),
                            encoding="utf-8").read(),
         "trạm so phiên bản, nhắc khi extension chạy bản cũ")

    # ⑧b mục menu chuột phải khai ↔ xử lý
    menu = set(re.findall(r'id:\s*"([a-z0-9-]+)"', nen))
    clicked = nen.split("contextMenus.onClicked", 1)[-1]
    thieu = sorted(m for m in menu if f'"{m}"' not in clicked)
    _bao(not thieu, "mọi mục chuột phải đều có nhánh xử lý", " · ".join(thieu))

    # ⑧c CHỐNG LUỒNG SONG SONG — mỗi cửa gửi ảnh chỉ được GỌI ở đúng một nơi.
    # Đếm trên MÃ THẬT, không đếm chú thích: bản đầu của cổng này báo giả ngay lần
    # chạy đầu vì lời dẫn đầu file có nhắc tên cửa (bài học #17 — cổng báo giả thì
    # lần sau người ta bỏ qua cả cái đúng).
    ma_that = "\n".join(l for l in nen.splitlines() if not l.strip().startswith("//"))
    for cua, chu in [("/api/tai-len", "guiAnh"), ("/api/kho-nha-tai-len", "guiAnhKho")]:
        n = len(re.findall(r"fetch\([^)]*" + re.escape(cua), ma_that))
        _bao(n == 1, f"cửa {cua} chỉ gọi ở một chỗ ({chu})",
             f"thấy {n} chỗ fetch — có ai viết luồng song song?" if n != 1 else "")

    # ⑧d hai đích phải đủ đôi ở CẢ menu lẫn phím tắt
    for ten, dat in [("menu chuột phải", menu), ("phím tắt", khai)]:
        co_viec = any("kho" not in x for x in dat) if ten == "phím tắt" else \
            any(x == "soc-lay-anh" for x in dat)
        co_kho = any("kho" in x for x in dat)
        _bao(co_viec and co_kho, f"{ten}: có đủ CẢ kho việc lẫn KHO CHUNG",
             f"đang có {sorted(dat)}" if not (co_viec and co_kho) else "")


if __name__ == "__main__":
    sau = "--sau" in sys.argv
    tang1_cu_phap()
    tang2_bay_cu()
    tang_chinh_phu()
    ma = tang3_route()
    tang_nhac()
    tang_phong_cach()
    tang_extension()
    tang_windows()          # chạy được trên máy thứ hai không (15/08)
    tang_may_phu()          # CÀI được trên máy thứ hai không (15/08)
    tang_dua_ghi()          # nhận nhiều tấm cùng lúc có mất không (16/08)
    tang_kho_video()        # kho video: lọc gốc/cắt + video gốc có vào kho (16/08)
    tang_vua_o()            # nút ⇥ vừa ô còn hiện lại được không (16/08)
    tang_bao_ban_moi()      # máy phụ có biết khi anh đẩy bản mới không (16/08)
    tang_chuoi_xong_bao()   # chuỗi máy tự chạy xong → trang tự nạp lại (16/08)
    tang_kho_lien_bai()     # tài nguyên bài trước dùng cho bài sau (16/08)
    tang_canh_dau_clip()    # cảnh đầu là clip có dựng được không (17/08)
    tang_dich_luu()         # chọn được nơi lưu thứ gắp về (17/08)
    tang_tu_khoa_anh()      # từ khoá tìm ảnh bằng tiếng Anh (17/08)
    tang_query_thong_minh() # mốc hình · câu video · tiếng bản địa (18/08)
    tang_soat_nuot_canh()   # cảnh bị nuốt khi dựng + ưu tiên clip (18/08)
    tang_anh_bia()          # ảnh bìa cho video (18/08)
    tang_cua_soi_dung_o()   # cửa soi gán đúng ô, không đè ô phụ (18/08)
    tang_mat_may_cham_bia()  # mắt máy nhìn ảnh + bộ chấm bìa (18/08)
    tang_tai_video()        # yt-dlp còn mới không + luật tải chung (19/08)
    if sau:
        tang4_luong(ma)
    else:
        print("④ (bỏ qua luồng ghi — thêm --sau để kiểm cả cửa nhận ảnh)")
    print()
    for c in canh:
        print("⚠ " + c)
    if loi:
        print(f"❌ TRƯỢT {len(loi)} mục — SỬA XONG MỚI ĐƯỢC BÁO XONG:")
        for x in loi:
            print("   · " + x)
        sys.exit(1)
    print("✅ ĐẠT HẾT — không có chức năng cũ nào bị gãy")
