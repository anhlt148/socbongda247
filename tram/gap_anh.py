#!/usr/bin/env python3
"""GẮP ẢNH BẰNG TRÌNH DUYỆT THẬT — hai đường: tìm theo từ khoá, và bóc thẳng một bài báo.

Vì sao cần: `lay_anh.py` đọc HTML thô bằng urllib nên chỉ thấy ảnh nào nằm sẵn trong HTML.
Báo nạp ảnh bằng JavaScript thì nó về tay không — đúng chỗ ảnh Việt Anh quấn băng đầu bị kẹt
(sổ dự án 04/08). Trình duyệt thật chạy JS xong mới đọc DOM nên thấy hết.

Mọi ảnh vào đây đều phải qua CÙNG MỘT CỔNG WATERMARK với `lay_anh.py` — không mở cửa sau.
Bài học số 3 của sổ dự án: "phát hiện watermark mà không chặn thì bằng không".

Dùng:
    python3 gap_anh.py tim  "việt anh khâu vết thương" ~/socbongda247/viec/<mã>/anh 20
    python3 gap_anh.py boc  "https://báo.vn/bai-viet.html"  ~/socbongda247/viec/<mã>/anh 20
"""
import concurrent.futures as cf
import glob
import json
import os
import re
import shutil
import sys
import threading
import urllib.parse
import urllib.request

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp
import lay_anh

# ANH CHỐT 05/08: **ảnh phải từ FULL HD trở lên.** Đo được bằng cạnh dài ≥1920 VÀ cạnh ngắn
# ≥1080 — đo theo cạnh chứ không theo "rộng/cao", vì ảnh CHÂN DUNG cầu thủ 1080×1920 cũng là
# Full HD, mà đòi "rộng ≥1920" thì loại sạch ảnh dọc.
#
# Cái giá phải trả, đo trên kho thật 554 ảnh: chỉ 21% đạt chuẩn này (27% ở mức HD, 52% dưới HD).
# Google trả 56 ảnh cho một từ khoá thì chỉ 10 tấm đạt. Nên phải bù bằng cách XIN GOOGLE lọc
# ngay tại nguồn (`tbs=isz:lt,islt:2mp` — chỉ ảnh trên 2 megapixel), thay vì gắp về rồi vứt.
CANH_DAI_TOI_THIEU, CANH_NGAN_TOI_THIEU = 1920, 1080
# CHỈ giữ itp:photo (ảnh chụp thật — cắt poster/clipart/đồ hoạ). BỎ hẳn islt:2mp từ 07/08:
# ép "trên 2 megapixel" là ĐUỔI SẠCH ảnh báo Việt (VnExpress/Thanh Niên ~1200-2000px ≈ 1MP)
# → Google đắp bằng ảnh hãng quốc tế 4-8MP nên "cầu thủ Thái thất vọng" ra toàn Hàn với châu
# Âu (anh bắt bằng ảnh đối chứng). Đo A/B cùng từ khoá: lọc cũ top nguồn = FB-crawl/Instagram,
# 17/100 nguồn VN; bỏ 2MP + gl=vn → vnecdn 7 + znews 4 + sport5 4, đúng như anh tìm tay.
# ĐÚNG CHỦ ĐỀ trước, độ nét sau — cổng du_net vẫn gác, tấm nhỏ hiện "dưới chuẩn" cho người quyết.
LOC_GOOGLE_TO = "&tbs=itp:photo"


def du_net(w, h):
    """Đạt Full HD chưa — tính theo CẠNH nên đúng cho cả ảnh ngang lẫn ảnh dọc."""
    return max(w, h) >= CANH_DAI_TOI_THIEU and min(w, h) >= CANH_NGAN_TOI_THIEU
# Tỉ lệ cho phép. Nới hơn `lay_anh` (1,1–2,2) vì ảnh CHÂN DUNG cầu thủ (dọc) crop về khối gần
# vuông vẫn giữ nguyên mặt — chỉ ảnh QUÁ NGANG (băng-rôn, ảnh bìa) mới mất chủ thể. Ở trạm
# này người nhìn tận mắt trước khi chọn nên nới được; tỉ lệ vẫn hiện lên giao diện để soi.
TY_LE_MIN, TY_LE_MAX = 0.60, 2.20

# Nơi ảnh gắp về không lẫn với ảnh của `lay_anh` (a00.jpg…): t = tìm, b = bóc bài.
TIEN_TO = {"tim": "t", "boc": "b"}

_JS_GOOGLE = r"""(() => {
  const s = [...document.scripts].map(x => x.text).join('\n');
  const re = /\["(https?:\/\/[^"]{20,}?)",(\d{2,5}),(\d{2,5})\]/g;
  const ra = [], thay = new Set(); let m;
  while ((m = re.exec(s))) {
    let u = m[1].replace(/\\u003d/g, '=').replace(/\\u0026/g, '&').replace(/\\\//g, '/');
    if (/gstatic|googleusercontent|\.svg|\.gif|logo|icon/i.test(u)) continue;
    if (thay.has(u)) continue; thay.add(u);
    ra.push({u: u, h: +m[2], w: +m[3]});
  }
  return ra;
})()"""

_JS_BAI = r"""(() => {
  const ra = [], thay = new Set();
  const them = (u, w, h, ct) => {
    if (!u || !/^https?:/.test(u)) return;
    u = u.split(' ')[0];
    if (/\.svg|\.gif|sprite|logo|icon|avatar|placeholder|blank/i.test(u)) return;
    if (thay.has(u)) return; thay.add(u);
    ra.push({u: u, w: w || 0, h: h || 0, ct: ct || ''});
  };
  // CHÚ THÍCH ẢNH của nhà báo (anh hỏi 11/08 "làm sao gán nhãn đúng nhất") — caption
  // là nhãn CHUẨN NHẤT có thể có: người viết biết chính xác ai, ở đâu, ngày nào.
  // Lấy miễn phí, không tốn một token nào, và đúng hơn mắt máy đoán.
  const cap = (i) => {
    const f = i.closest('figure');
    let c = f && f.querySelector('figcaption');
    if (!c) {                                    // báo Việt hay dùng div/p .caption
      const h = i.closest('div,p,td');
      c = h && h.querySelector('.caption,.PhotoCMS_Caption,.image-caption,'
                               + '[class*="caption"],[class*="Caption"]');
    }
    let t = (c && c.textContent || '').trim();
    if (!t) t = (i.getAttribute('alt') || '').trim();
    if (!t) t = (i.getAttribute('title') || '').trim();
    return t.replace(/\s+/g, ' ').slice(0, 300);
  };
  document.querySelectorAll('img').forEach(i => {
    const ct = cap(i);
    if (i.srcset) {
      const to = i.srcset.split(',').map(x => x.trim())
        .sort((a, b) => (parseInt(b.split(' ')[1]) || 0) - (parseInt(a.split(' ')[1]) || 0))[0];
      them(to, i.naturalWidth, i.naturalHeight, ct);
    }
    them(i.currentSrc || i.src, i.naturalWidth, i.naturalHeight, ct);
    ['data-src', 'data-original', 'data-lazy-src', 'data-echo']
      .forEach(a => them(i.getAttribute(a), 0, 0, ct));
  });
  document.querySelectorAll('source[srcset]').forEach(s => them(s.srcset.split(',')[0].trim()));
  document.querySelectorAll('*').forEach(e => {
    const b = getComputedStyle(e).backgroundImage || '';
    const m = b.match(/url\("?(https?:[^")]+)"?\)/);
    if (m) them(m[1]);
  });
  return ra;
})()"""


def _so_tiep(thu_muc, tien_to):
    """Đánh số tiếp, không đè lên ảnh đã có trong thư mục."""
    co = glob.glob(os.path.join(thu_muc, f"{tien_to}*.jpg"))
    n = [int(m.group(1)) for f in co
         if (m := re.search(rf"{tien_to}(\d+)\.jpg$", os.path.basename(f)))]
    return max(n) + 1 if n else 0


# ── VÂN TAY ẢNH chống trùng (anh bắt 09/08: cùng một ảnh vào kho nhiều lần) ──────
# dHash 64 bit: thu về 9×8 xám, so sáng-tối từng cặp điểm kề — cùng ảnh dù khác cỡ/nén
# vẫn ra vân gần nhau. Khác ≤6 bit coi là TRÙNG. Sổ van-tay.json nằm cạnh ảnh.
# KHOÁ THEO THƯ MỤC KHO — anh báo 16/08: "tải ảnh lúc được lúc không, ảnh 2·3·4 phải
# bấm tải lại trang mới thấy". Tái hiện bằng 6 lượt gửi ĐỒNG THỜI: MẤT SẠCH cả 6 tấm.
#
# Gốc: `_so_tiep()` đặt tên bằng cách ĐẾM TỆP ĐANG CÓ. Sáu luồng cùng đếm ra `n00`,
# cùng ghi đè một tệp, rồi khâu chống trùng thấy "ảnh của luồng khác" nên `os.remove`
# — xoá mất tệp mà luồng kia đang đọc dở. Sổ vân tay cũng đọc-sửa-ghi không khoá nên
# mất mục theo. Ba lỗi chồng nhau, ra đúng cái "chập chờn".
#
# Trạm là MỘT tiến trình nhiều luồng (ThreadingHTTPServer) nên Lock theo thư mục là đủ
# và rẻ. Chống tiến trình KHÁC (script chạy tay) thì thêm O_EXCL lúc xí tên — xem _dat_cho.
_KHOA_KHO = {}
_KHOA_SO = threading.Lock()


def _khoa_thu_muc(thu_muc):
    """Mỗi thư mục kho một khoá riêng — hai bài khác nhau không phải chờ nhau."""
    k = os.path.abspath(thu_muc)
    with _KHOA_SO:
        if k not in _KHOA_KHO:
            _KHOA_KHO[k] = threading.Lock()
        return _KHOA_KHO[k]


def _dat_cho(thu_muc, tien_to, so_luong):
    """XÍ TRƯỚC tên tệp — tạo tệp rỗng ngay, để không ai giành mất.

    `O_CREAT | O_EXCL` là lời hứa của hệ điều hành: chỉ MỘT người tạo được tệp ấy, kẻ
    còn lại nhận FileExistsError. Nhờ vậy hai TIẾN TRÌNH khác nhau cũng không thể cùng
    xí một tên — thứ mà đếm-rồi-đặt-tên không bao giờ bảo đảm nổi.
    """
    ra, n = [], _so_tiep(thu_muc, tien_to)
    while len(ra) < so_luong:
        p = os.path.join(thu_muc, f"{tien_to}{n:02d}.jpg")
        try:
            os.close(os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            ra.append(p)
        except FileExistsError:
            pass
        n += 1
    return ra


def _dhash(im):
    g = im.convert("L").resize((9, 8), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for y in range(8):
        for x in range(8):
            bits = (bits << 1) | (1 if px[y * 9 + x] > px[y * 9 + x + 1] else 0)
    return bits


CAP_MODEL = 1000        # cạnh dài tối đa của ảnh GỬI CHO MODEL


def ban_nho(duong, cap=CAP_MODEL):
    """Bản THU NHỎ để gửi cho mắt máy — trả đường ảnh nhỏ (ảnh gốc không đụng tới).

    VÌ SAO (anh hỏi 13/08 "có tốn nhiều token không"): model tính token ảnh ≈ w×h/750.
    Ảnh kho 2000×1333 tốn 3.555 token/tấm; thu về 1000px còn 888 — RẺ HƠN BỐN LẦN.
    Đo thật trên 9 ảnh với cả sonnet lẫn opus: bản 1000px vẫn đọc đúng SỐ ÁO (số 7),
    vẫn nhận ra Kim Sang-sik, vẫn tả đúng màu áo + logo tài trợ. Không mất gì.

    Với nhịp 10 video/ngày, riêng khâu mắt máy kiểm ảnh nháp giảm 0,59 → 0,16 triệu
    token mỗi ngày.

    Cache cạnh ảnh trong `_nho/`, so mtime nên ảnh sửa (crop, xoá watermark) là tự
    sinh lại. Ảnh vốn đã nhỏ hơn ngưỡng thì dùng thẳng, khỏi đẻ tệp thừa.
    """
    try:
        if not os.path.exists(duong):
            return duong
        thu = os.path.join(os.path.dirname(duong), "_nho")
        ra = os.path.join(thu, os.path.basename(duong))
        if os.path.exists(ra) and os.path.getmtime(ra) >= os.path.getmtime(duong):
            return ra
        im = Image.open(duong)
        if max(im.size) <= cap:
            return duong
        os.makedirs(thu, exist_ok=True)
        im = im.convert("RGB")
        im.thumbnail((cap, cap), Image.LANCZOS)
        im.save(ra, quality=88)
        return ra
    except Exception:
        return duong        # hỏng thì dùng ảnh gốc — thà tốn token còn hơn mù


def _dhash_neo(im, tren=True, ty=0.5):
    """Vân của một DẢI NEO SÁT MÉP, cao bằng nửa BỀ NGANG.

    Chìa khoá: bề ngang KHÔNG đổi khi cắt mép trên/dưới, nên dải neo đo theo bề ngang
    là vùng ảnh y hệt nhau ở cả bản gốc lẫn bản đã cắt — vân trùng khít.
    """
    W, H = im.size
    hh = min(H, max(8, int(W * ty)))
    return _dhash(im.crop((0, 0, W, hh) if tren else (0, H - hh, W, H)))


def _dhash_loi(im):
    """VÂN NEO MÉP — trả chuỗi "<neo trên>,<neo dưới>" (anh hỏi 11/08: "ảnh cắt
    watermark rồi thì có nhận ra trùng với bản gốc không?").

    Đo thật hôm đó: CẮT mép 8% là vân thường đã lệch 8,5 bit — quá ngưỡng 6, hệ coi như
    hai ảnh khác nhau nên kho đẻ bản thứ hai. Dải watermark thật chiếm 8–15% chiều cao
    nên cắt xong gần như chắc lọt. (Xoá bằng LaMa thì khuôn hình không đổi, lệch 0,5
    bit — vân thường vẫn bắt tốt.)

    Bản đầu em thử "vân lõi giữa" và ĐO RA LÀ SAI: cắt mép dưới kéo tâm ảnh dịch lên
    nên lõi hai bản không trùng (lệch 10–14 bit, tệ hơn cả vân thường). Neo MÉP mới
    đúng — đo lại: cắt dưới 12% thì neo-trên lệch 1,3 bit, cắt trên 15% thì neo-dưới
    lệch 3,3 bit. Giữ cả hai vế để bắt được cắt ở bất kỳ mép nào.
    """
    return f"{_dhash_neo(im, True)},{_dhash_neo(im, False)}"


def _nap_van_tay(thu_muc):
    """Đọc sổ vân tay; ảnh có trên đĩa mà chưa có vân thì tính bổ sung, mục của ảnh đã
    xoá thì dọn — sổ luôn khớp thư mục dù ảnh vào bằng cửa nào."""
    p = os.path.join(thu_muc, "van-tay.json")
    so = {}
    if os.path.exists(p):
        try:
            so = {k: int(v) for k, v in json.load(open(p, encoding="utf-8")).items()}
        except Exception:
            so = {}
    con = {os.path.basename(f) for f in glob.glob(os.path.join(thu_muc, "*.jpg"))}
    so = {k: v for k, v in so.items() if k in con}
    for ten in sorted(con - set(so)):
        try:
            so[ten] = _dhash(Image.open(os.path.join(thu_muc, ten)))
        except Exception:
            pass
    return so, p


def _nap_van_loi(thu_muc):
    """Sổ VÂN LÕI đi SONG SONG sổ vân thường (`van-tay-loi.json`) — không đụng format
    sổ cũ nên mọi đường đọc sổ cũ vẫn chạy y nguyên."""
    p = os.path.join(thu_muc, "van-tay-loi.json")
    so = {}
    if os.path.exists(p):
        try:                                       # giá trị là CHUỖI "tren,duoi"
            so = {k: str(v) for k, v in json.load(open(p, encoding="utf-8")).items()
                  if "," in str(v)}                # bỏ mục format cũ (vân lõi giữa)
        except Exception:
            so = {}
    con = {os.path.basename(f) for f in glob.glob(os.path.join(thu_muc, "*.jpg"))}
    so = {k: v for k, v in so.items() if k in con}
    for ten in sorted(con - set(so)):
        try:
            so[ten] = _dhash_loi(Image.open(os.path.join(thu_muc, ten)))
        except Exception:
            pass
    return so, p


def _luu_van_tay(so, p):
    try:
        json.dump({k: str(v) for k, v in so.items()}, open(p, "w", encoding="utf-8"))
    except Exception:
        pass


def _tim_trung(so, h, so_loi=None, h_loi=None):
    """Trùng nếu khớp vân THƯỜNG *hoặc* một trong hai vân NEO MÉP (anh hỏi 11/08).

    Hai loại bù nhau: vân thường bắt ảnh khác cỡ / khác mức nén; vân neo bắt ảnh đã bị
    CẮT MÉP để bỏ watermark — neo trên cho ảnh cắt mép dưới, neo dưới cho cắt mép trên.
    """
    for ten, cu in so.items():
        if bin(h ^ cu).count("1") <= 6:
            return ten
    if so_loi and h_loi:
        tr, du = (h_loi.split(",") + ["0"])[:2]
        for ten, cu in so_loi.items():
            c = str(cu).split(",")
            if len(c) < 2:
                continue
            # ngưỡng 5 (chặt hơn vân thường một bậc): dải neo chỉ nhìn nửa ảnh nên dễ
            # đụng nhau hơn — nới thành 6 là bắt oan hai ảnh khác chụp cùng góc sân
            if bin(int(tr) ^ int(c[0])).count("1") <= 5 or \
               bin(int(du) ^ int(c[1])).count("1") <= 5:
                return ten
    return None


def _tai_mot(u, thu_muc, ten, referer="", so_vt=None, khoa=None, crop=None,
             so_loi=None):
    p = os.path.join(thu_muc, ten)
    try:
        dau = {"User-Agent": lay_anh.UA}
        if referer:
            dau["Referer"] = referer
        r = urllib.request.Request(u, headers=dau)
        with urllib.request.urlopen(r, timeout=25) as res:
            data = res.read(12_000_000)
        if len(data) < 25_000:
            return None
        open(p, "wb").write(data)
        im = Image.open(p)
        im.load()
        im = im.convert("RGB")
        # CROP anh vẽ sẵn trên trang chọn (09/08 — né watermark mà vẫn lấy được ảnh):
        # cắt NGAY sau tải; ảnh crop chủ đích thì người đã nhìn tận mắt nên bỏ cổng
        # cỡ/tỉ lệ (cùng lý với tu_chon bỏ soi), chỉ giữ sàn 300px chống ảnh vụn.
        if crop:
            W0, H0 = im.size
            x0 = max(0, int(float(crop["x"]) * W0))
            y0 = max(0, int(float(crop["y"]) * H0))
            x1 = min(W0, int((float(crop["x"]) + float(crop["w"])) * W0))
            y1 = min(H0, int((float(crop["y"]) + float(crop["h"])) * H0))
            if x1 - x0 >= 300 and y1 - y0 >= 300:
                im = im.crop((x0, y0, x1, y1))
        w, h = im.size
        # ảnh KHO NHÀ đã qua duyệt bài trước + đã cắt mép watermark (hay hụt vài chục px
        # so chuẩn Full HD — dò 10/08: 2200×1056 rụng êm ở cổng) → miễn cổng cỡ như ảnh
        # crop chủ đích, chỉ giữ sàn chống ảnh vụn
        kho_nha = "/kho-nha-anh/" in u
        if not crop and not kho_nha:
            if not du_net(w, h):                   # dưới Full HD — anh chốt 05/08 là không lấy
                os.remove(p)
                return None
        if kho_nha and min(w, h) < 300:
            os.remove(p)
            return None
            if not (TY_LE_MIN <= w / h <= TY_LE_MAX):
                os.remove(p)
                return None
        elif w < 300 or h < 300:
            os.remove(p)
            return None
        # chống TRÙNG (anh bắt 09/08): vân tay so với cả kho trước khi nhận — cùng ảnh
        # từ 2 nguồn/2 lượt tìm chỉ giữ MỘT. Tải song song 8 luồng nên phải khoá sổ.
        if so_vt is not None:
            h_vt = _dhash(im)
            h_loi = _dhash_loi(im)          # vân LÕI: bắt cả bản đã CẮT MÉP bỏ watermark
            with (khoa or _khoa_gia()):
                cu = _tim_trung(so_vt, h_vt, so_loi, h_loi)
                if cu:
                    # TRÙNG ảnh BÀI ĐÃ CÓ → đừng báo hỏng, TRỎ VỀ TẤM CŨ (anh bắt
                    # 11/08: bấm ảnh kho nhà toàn "nhận ảnh hỏng" — vì kho nhà nhập
                    # từ chính các bài nên tấm nào cũng dễ trùng ảnh bài đang có).
                    # Bên gọi cứ gán tấm cũ là xong, người dùng không thấy lỗi giả.
                    os.remove(p)
                    try:
                        w0, h0 = Image.open(os.path.join(thu_muc, cu)).size
                    except Exception:
                        w0, h0 = w, h
                    return {"tep": cu, "url": u, "kich_thuoc": f"{w0}x{h0}",
                            "ty_le": round(w0 / h0, 2) if h0 else 0, "trung": True}
                so_vt[ten] = h_vt
                if so_loi is not None:
                    so_loi[ten] = h_loi
        im.thumbnail((2200, 2200), Image.LANCZOS)
        im.save(p, quality=92)
        return {"tep": ten, "url": u, "kich_thuoc": f"{w}x{h}", "ty_le": round(w / h, 2)}
    except Exception:
        try:
            os.path.exists(p) and os.remove(p)
        except Exception:
            pass
        return None


def _khoa_gia():
    return threading.Lock()


def _gac_cong(ds, thu_muc, can=None, bao_tien=None):
    """CỔNG WATERMARK — y hệt cổng của `lay_anh.lay()`, không nới một ly.

    Bậc 0: cổng phải NHÌN ĐƯỢC đã (tesseract có tiếng Việt chưa). Mù thì xoá sạch, không
           lấy ảnh nào — cổng mù mà cho qua là tệ hơn không có cổng.
    Bậc 1: đọc ra dấu nguồn (@tên, .com, tên báo) → loại thẳng, đẩy vào _dinh-watermark.
    Bậc 2: có chữ ở góc/rìa → cờ vàng, vẫn giữ nhưng người phải soi.
    """
    nhin_duoc, vi_sao = lay_anh._ocr_song_khong()
    if not nhin_duoc:
        for a in ds:
            p = os.path.join(thu_muc, a["tep"])
            os.path.exists(p) and os.remove(p)
        return [], [], f"CỔNG WATERMARK MÙ — {vi_sao}. Dừng, không lấy ảnh nào."

    dl = lay_anh._do_logo()
    cach_ly = os.path.join(thu_muc, "_dinh-watermark")
    sach, vang, loai = [], [], []

    # OCR CHẠY SONG SONG. Đo 05/08: soi một tấm mất 1,7 giây (mỗi góc một lượt tesseract);
    # chạy tuần tự 47 tấm là 81 giây — đúng chỗ làm anh phải ngồi chờ. tesseract là tiến
    # trình ngoài nên Python nhả khoá trong lúc chờ, tám luồng chạy được song song thật.
    # Đây là đổi CÁCH CHẠY, KHÔNG nới tiêu chuẩn cổng: vẫn từng ấy phép soi, từng ấy mức chặn.
    def _soi(a):
        p = os.path.join(thu_muc, a["tep"])
        if not os.path.exists(p):
            return a, None, "mất tệp"
        try:
            return a, dl.do_chu(p, la_anh=True), ""
        except Exception as e:
            return a, None, f"dò lỗi: {e}"

    # …và DỪNG SỚM khi đã đủ ảnh cần. Trước đây soi hết 47 tấm rồi mới giữ 18 — 29 tấm soi
    # xong là vứt. Giờ đủ số thì thôi. Ảnh chưa kịp soi KHÔNG được dùng: nó không nằm trong
    # danh sách trả về nên `_thu_hoach` xoá — cổng vẫn kín, chỉ bớt việc thừa.
    xong, ket_qua = 0, []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        cho = {ex.submit(_soi, a): a for a in ds}
        for f in cf.as_completed(cho):
            ket_qua.append(f.result())
            xong += 1
            if bao_tien:
                bao_tien(xong, len(ds))
            if can and sum(1 for r in ket_qua if r[1] is not None) >= can:
                for g in cho:                             # đủ rồi, huỷ phần chưa chạy
                    g.cancel()
                break

    for a, doc_duoc, sai in ket_qua:
        p = os.path.join(thu_muc, a["tep"])
        if doc_duoc is None:                          # dò hỏng = coi như bẩn, không cho qua
            if sai == "mất tệp":
                continue
            a["ly_do_loai"] = sai
            loai.append(a)
            os.makedirs(cach_ly, exist_ok=True)
            os.path.exists(p) and shutil.move(p, os.path.join(cach_ly, a["tep"]))
            continue
        chan = [f"{v}: “{c[:40]}”" for v, c in doc_duoc.items() if lay_anh.DAU_NGUON.search(c)]
        if chan:
            a["ly_do_loai"] = "dấu nguồn · " + " · ".join(chan)
            loai.append(a)
            os.makedirs(cach_ly, exist_ok=True)
            shutil.move(p, os.path.join(cach_ly, a["tep"]))
            continue
        co = [f"{v}: “{c[:40]}”" for v, c in doc_duoc.items() if v in lay_anh.VUNG_CHAN]
        a["can_soi"] = " · ".join(co)
        (vang if co else sach).append(a)
    return sach, vang, ""


def soi_watermark(thu_muc, ds_ten):
    """Soi dấu nguồn nhưng KHÔNG vứt tấm nào — chỉ trả nhãn để bên gọi tự xử.

    Dùng ở hai chỗ NGƯỜI đã chọn bằng mắt: ảnh anh tự đưa vào, và bước DUYỆT.
    Khác `_gac_cong` (máy đi lấy → vứt bừa được).
    """
    ra = {t: {"dau_nguon": "", "can_soi": ""} for t in ds_ten}
    nhin_duoc, vi_sao = lay_anh._ocr_song_khong()
    if not nhin_duoc:
        for t in ra:
            ra[t]["canh_bao"] = f"CHƯA soi được watermark ({vi_sao})"
        return ra
    dl = lay_anh._do_logo()

    def _soi(t):
        p = os.path.join(thu_muc, t)
        if not os.path.exists(p):
            return t, {}
        try:
            return t, dl.do_chu(p, la_anh=True)
        except Exception:
            return t, {}

    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for t, doc in ex.map(_soi, ds_ten):
            ra[t]["dau_nguon"] = " · ".join(f"{v}: “{c[:40]}”" for v, c in doc.items()
                                            if lay_anh.DAU_NGUON.search(c))
            ra[t]["can_soi"] = " · ".join(f"{v}: “{c[:40]}”" for v, c in doc.items()
                                          if v in lay_anh.VUNG_CHAN)
    return ra


def _ghi_so(thu_muc, ds):
    """Sổ gắp — ghi thêm, không đè. Mỗi dòng một ảnh, đủ nguồn để trả lời 'ảnh này ở đâu ra'."""
    p = os.path.join(thu_muc, "so-gap.jsonl")
    with open(p, "a", encoding="utf-8") as f:
        for a in ds:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")


def _thu_hoach(cap, thu_muc, tien_to, can, chung, referer="", bao_tien=None, crops=None):
    """cap = [(url, w_bao, h_bao)] → tải song song → qua cổng → ghi sổ → trả danh sách."""
    os.makedirs(thu_muc, exist_ok=True)
    # Tải GẤP ĐÔI số cần (trước là gấp ba). Đo 05/08: 54 tấm tải về, 47 tấm qua lọc kích
    # thước, rồi soi watermark cả 47 mà chỉ giữ 18 — 29 tấm bị soi xong mới vứt đi.
    # Gấp đôi vẫn thừa đủ để bù số rụng ở cổng, mà bớt được một phần ba thời gian soi.
    lay = cap if chung.get("tu_chon") else cap[:can * 2]   # anh đã chỉ thì lấy đủ, không cắt
    # cap có thể là (u,w,h) hoặc (u,w,h,caption) — caption đi kèm để ghi vào sổ
    # XÍ TÊN NGUYÊN TỬ thay cho đếm-rồi-đặt-tên (cùng lỗi 16/08 với nhan_tep): hai job
    # tìm ảnh chạy song song trên cùng một bài từng đè lên tệp của nhau.
    viec = [(x[0], os.path.basename(t))
            for x, t in zip(lay, _dat_cho(thu_muc, tien_to, len(lay)))]
    _ct_theo_url = {x[0]: (x[3] if len(x) > 3 else "") for x in lay}
    so_vt, p_vt = _nap_van_tay(thu_muc)
    so_loi, p_loi = _nap_van_loi(thu_muc)         # vân LÕI đi kèm (anh hỏi 11/08)
    khoa_vt = threading.Lock()
    crops = crops or {}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        ra = [x for x in ex.map(lambda t: _tai_mot(t[0], thu_muc, t[1], referer,
                                                   so_vt, khoa_vt, crops.get(t[0]),
                                                   so_loi),
                                viec) if x]
    # Tên đã xí mà tấm rốt cuộc bị loại (ảnh nhỏ, tải hỏng, trùng) thì để lại một tệp
    # RỖNG nằm trong kho — trang trạm sẽ bày ra một ô ảnh vỡ. Dọn ngay.
    for _, ten_x in viec:
        px = os.path.join(thu_muc, ten_x)
        try:
            if os.path.exists(px) and os.path.getsize(px) == 0:
                os.remove(px)
        except OSError:
            pass
    _luu_van_tay(so_vt, p_vt)
    _luu_van_tay(so_loi, p_loi)

    # ANH CHỐT 05/08: ảnh anh CHỌN TAY thì cho qua thẳng, khỏi soi ở cửa nhập — anh đã nhìn
    # tận mắt trên lưới rồi, mà soi watermark là khâu chậm nhất (1,7 giây một tấm).
    # Cổng KHÔNG bị bỏ, chỉ DỜI sang bước DUYỆT: lúc ấy chỉ soi đúng những tấm thật sự vào
    # video (12–20 tấm thay vì cả trăm), nhanh hơn hẳn mà vẫn chặn trước khi lên hình.
    if chung.get("tu_chon"):
        for a in ra:
            a["can_soi"] = ""
            a["dau_nguon"] = ""
            a["chua_soi"] = True                   # đánh dấu: cổng sẽ soi ở bước duyệt
            a.update(chung)
            if _ct_theo_url.get(a.get("url")):     # CHÚ THÍCH của nhà báo
                a["chu_thich"] = _ct_theo_url[a["url"]]
        _ghi_so(thu_muc, ra)
        return {"anh": ra, "so_sach": len(ra), "so_co_vang": 0, "loi": ""}

    sach, vang, loi = _gac_cong(ra, thu_muc, can, bao_tien)
    if loi:
        return {"anh": [], "loi": loi}
    dung = (sach + vang)[:can]
    for a in ra:                                              # dọn ảnh dư, không để rác
        p = os.path.join(thu_muc, a["tep"])
        if os.path.exists(p) and a not in dung:
            os.remove(p)
    for a in dung:
        a.update(chung)
        a.setdefault("can_soi", "")
        if _ct_theo_url.get(a.get("url")):         # CHÚ THÍCH của nhà báo — nhãn chuẩn
            a["chu_thich"] = _ct_theo_url[a["url"]]
    _ghi_so(thu_muc, dung)
    return {"anh": dung, "so_sach": len([a for a in dung if not a["can_soi"]]),
            "so_co_vang": len([a for a in dung if a["can_soi"]]), "loi": ""}


# ── ĐƯỜNG 1: tìm theo từ khoá ────────────────────────────────────────────────
def tim(tu_khoa, thu_muc, can=18, cuon=2, bao_tien=None):
    q = urllib.parse.quote(tu_khoa)
    url = f"https://www.google.com/search?q={q}&udm=2&hl=vi&gl=vn" + LOC_GOOGLE_TO
    t = cdp.the_dung_chung()                       # mở tab NGAY TRONG Chrome đang bật
    try:
        t.di(url)
        if t.dinh_captcha():
            return {"anh": [], "loi": "Google hỏi CAPTCHA. KHÔNG tự giải — sang cửa sổ Chrome "
                                      "của trạm, giải một lần bằng tay rồi bấm tìm lại."}
        t.cuon(cuon, 0.9)
        thay = t.js(_JS_GOOGLE) or []
    except Exception as e:
        cdp.bo_the()                               # thẻ hỏng thì bỏ, lần sau tự dựng lại
        return {"anh": [], "loi": f"trình duyệt lỗi: {e}"}
    cap = [(x["u"], x["w"], x["h"]) for x in thay if du_net(x["w"], x["h"])]
    if not cap:
        return {"anh": [], "loi": f"không thấy ảnh đủ nét cho từ khoá “{tu_khoa}”"}
    return _thu_hoach(cap, thu_muc, TIEN_TO["tim"], can,
                      {"nguon_bai": url, "bao": "Google ảnh", "tu_khoa": tu_khoa,
                       "giay_phep": "ảnh tìm trên mạng — CHƯA xin phép"}, bao_tien=bao_tien)


# ── ĐƯỜNG 2: bóc thẳng một bài báo (kể cả bài nạp ảnh bằng JavaScript) ───────
def boc_bai(url_bai, thu_muc, can=18, cuon=4, bao_tien=None):
    t = cdp.the_dung_chung()
    try:
        t.di(url_bai)
        if t.dinh_captcha():
            return {"anh": [], "loi": "trang hỏi CAPTCHA — sang cửa sổ Chrome của trạm giải tay."}
        t.cuon(cuon, 0.8)                                     # ép ảnh lười nạp hết
        thay = t.js(_JS_BAI) or []
    except Exception as e:
        cdp.bo_the()
        return {"anh": [], "loi": f"trình duyệt lỗi: {e}"}
    bao = urllib.parse.urlparse(url_bai).netloc
    cap = [(x["u"], x["w"], x["h"], x.get("ct", "")) for x in thay]
    if not cap:
        return {"anh": [], "loi": "bài này không có ảnh nào lấy được"}
    return _thu_hoach(cap, thu_muc, TIEN_TO["boc"], can,
                      {"nguon_bai": url_bai, "bao": bao,
                       "giay_phep": "ảnh báo chí — CHƯA xin phép"}, referer=url_bai,
                      bao_tien=bao_tien)


# ── ĐƯỜNG 4: BÀY RA CHO ANH CHỌN, RỒI MỚI TẢI ─────────────────────────────────────────────
#
# Anh hỏi 05/08: "tại sao em lấy được ảnh về kho mà anh lại không tự chọn được?"
# Câu hỏi ấy chỉ đúng chỗ nghẽn: em có DANH SÁCH URL, còn anh nhìn theo VỊ TRÍ trên màn hình.
# Em chưa bao giờ "chọn" — em lấy 18 URL đầu danh sách, mù tịt về tấm nào ra tấm nào.
#
# Thế thì đừng cố chọn trên lưới của Google nữa: **bày chính danh sách ấy ra trong trạm**.
# Trình duyệt của anh nạp thẳng ảnh từ URL gốc (server không tải gì cả, không tốn gì), anh
# nhìn tận mắt rồi bấm tấm nào thì trạm mới tải tấm ấy về và cho qua cổng watermark.
# Ảnh anh thấy chính là URL đó — không còn chỗ nào để lệch.
def xem_truoc(tu_khoa, cuon=3, _lan=0):
    """Chỉ BÓC DANH SÁCH url + kích thước, KHÔNG tải ảnh. Nhanh vì không đụng mạng lần hai."""
    q = urllib.parse.quote(tu_khoa)
    url = f"https://www.google.com/search?q={q}&udm=2&hl=vi&gl=vn" + LOC_GOOGLE_TO
    t = cdp.the_dung_chung()
    try:
        t.di(url)
        if t.dinh_captcha():
            return {"anh": [], "loi": "Google hỏi CAPTCHA — giải tay trong cửa sổ Chrome "
                                      "của trạm rồi bấm lại."}
        t.cuon(cuon, 0.9)
        thay = t.js(_JS_GOOGLE) or []
    except Exception as e:
        cdp.bo_the()
        if _lan < 1:
            return xem_truoc(tu_khoa, cuon, _lan + 1)
        return {"anh": [], "loi": f"trình duyệt lỗi: {e}"}
    # Lưới CHỌN bày cả ảnh dưới chuẩn, nhưng dán nhãn — có tấm quý mà đời chỉ có bản nhỏ,
    # chặn cứng ở đây thì anh không còn đường lấy. Người nhìn thấy nhãn rồi tự quyết.
    ra = [{"u": x["u"], "w": x["w"], "h": x["h"], "ty_le": round(x["w"] / max(x["h"], 1), 2),
           "du_net": du_net(x["w"], x["h"])}
          for x in thay if TY_LE_MIN <= x["w"] / max(x["h"], 1) <= TY_LE_MAX
          and max(x["w"], x["h"]) >= 1000]
    ra.sort(key=lambda a: (not a["du_net"], -a["w"] * a["h"]))
    return {"anh": ra, "tu_khoa": tu_khoa, "loi": "" if ra else "không thấy ảnh nào đủ nét"}


def lay_theo_url(ds_url, thu_muc, tu_khoa="", bao_tien=None, crops=None):
    """Tải ĐÚNG những tấm anh đã chỉ. Vẫn qua đủ cổng watermark như mọi đường khác.
    crops = {url: {x,y,w,h} tỉ lệ 0-1} — vùng anh vẽ trên trang chọn, cắt ngay khi tải."""
    cap = [(u, 0, 0) for u in ds_url]
    return _thu_hoach(cap, thu_muc, TIEN_TO["tim"], len(cap),
                      {"nguon_bai": "google ảnh — anh tự chọn", "bao": "anh chọn trên Google",
                       "tu_khoa": tu_khoa, "tu_chon": True,
                       "giay_phep": "ảnh tìm trên mạng — CHƯA xin phép"},
                      bao_tien=bao_tien, crops=crops)


# ĐƯỜNG cũ "chọn ngay trên lưới Google" — ĐÃ THỬ 05/08, KHÔNG LÀM ĐƯỢC, đã gỡ mã.
# Google che URL gốc rất kín. Ba cách đều đo và đều hỏng, chi tiết trong BRAIN.md mục 22:
#   ① ánh xạ ô lưới ↔ danh sách URL trong mã trang theo thứ tự → lệch (65 ô / 99 URL)
#   ② bấm ô cho hiện khung xem lớn rồi đọc ảnh trong đó → Google phục vụ bản `encrypted-tbn`
#      của chính nó (738×411), không phải ảnh gốc, và quá nhỏ cho khung dọc 1080
#   ③ ánh xạ bằng tỉ lệ khung hình → 12 ô thử: 2 khớp duy nhất, 5 mơ hồ, 5 không khớp
# Thay bằng: gắp về kho rồi lọc — `loc_anh.py` chấm nhãn lạc đề, cộng nút ✕ vứt tay từng tấm.

# ── ĐƯỜNG 3: ảnh ANH TỰ ĐƯA VÀO (tải từ Facebook cầu thủ, chụp màn hình, ảnh riêng…) ──────
#
# Luật ở đường này KHÁC hai đường trên, và khác có chủ ý:
#   · Hai đường kia là MÁY đi lấy → máy lấy bừa thì phải có cổng vứt bừa. Vứt là đúng.
#   · Đường này là NGƯỜI chủ động đưa vào → vứt ảnh anh cố tình chọn là sai. Ảnh Facebook cầu
#     thủ hay có logo CLB, tên giải, khung ảnh — chặn cứng thì anh chẳng đưa được tấm nào.
# Nên ở đây: VẪN SOI ĐỦ, nhưng KHÔNG tự xoá tấm nào — chỉ dán nhãn để anh nhìn thấy mà cân:
#   🔴 dấu nguồn (@tên, .com, tên báo) · 🟡 có chữ ở góc · ⚠️ nhỏ hơn 900px (lên khung sẽ vỡ)
# Cổng vẫn kín ở ĐẦU RA: tấm 🔴 mà anh vẫn dùng thì lúc DUYỆT trạm hỏi lại, và sổ nguồn ghi rõ.
TIEN_TO["nguoi"] = "n"


def nhan_tep(ds_tep, thu_muc):
    """ds_tep = [(tên gốc, bytes)] → lưu vào kho, soi, trả danh sách kèm nhãn cảnh báo."""
    os.makedirs(thu_muc, exist_ok=True)
    # CẢ KHỐI nằm trong một khoá: xí tên · ghi ảnh · soi trùng · ghi sổ vân tay. Tách nhỏ
    # ra thì vẫn hở — khâu soi trùng phải thấy đúng những gì khâu ghi vừa làm, không thì
    # nó tưởng ảnh của luồng khác là "bản trùng" rồi xoá đi (đúng lỗi 16/08).
    with _khoa_thu_muc(thu_muc):
        return _nhan_tep_trong_khoa(ds_tep, thu_muc)


def _nhan_tep_trong_khoa(ds_tep, thu_muc):
    cho = _dat_cho(thu_muc, "n", len(ds_tep))      # xí đủ tên NGAY, không ai giành được
    so_vt, p_vt = _nap_van_tay(thu_muc)            # chống trùng (anh bắt 09/08)
    so_loi, p_loi = _nap_van_loi(thu_muc)          # + vân LÕI (anh hỏi 11/08)
    ra, i = [], 0
    for muc in ds_tep:
        ten_goc, du_lieu = muc[0], muc[1]
        u_goc = muc[2] if len(muc) > 2 else ""
        trang = muc[3] if len(muc) > 3 else ""
        p = cho[i]
        ten = os.path.basename(p)
        try:
            open(p, "wb").write(du_lieu)
            im = Image.open(p)
            im.load()
            w, h = im.size
            im = im.convert("RGB")
            h_vt = _dhash(im)
            h_loi = _dhash_loi(im)               # vân LÕI: bắt cả bản đã cắt mép
            cu = _tim_trung(so_vt, h_vt, so_loi, h_loi)
            if cu:
                os.remove(p)                       # trả lại chỗ đã xí
                i += 1                             # nhưng KHÔNG tái dùng tên ấy cho tấm sau
                ra.append({"tep": ten_goc, "loi": f"TRÙNG với {cu} đã có trong kho — bỏ qua"})
                continue
            so_vt[ten] = h_vt
            so_loi[ten] = h_loi
            im.thumbnail((2200, 2200), Image.LANCZOS)
            im.save(p, quality=92)
        except Exception as e:
            os.path.exists(p) and os.remove(p)      # trả lại chỗ đã xí
            i += 1
            ra.append({"tep": ten_goc, "loi": f"không đọc được ảnh: {e}"})
            continue
        i += 1
        canh = []
        if not du_net(w, h):
            canh.append(f"DƯỚI Full HD ({w}×{h}) — chuẩn kênh là cạnh dài ≥1920, ngắn ≥1080")
        ty = round(w / h, 2)
        if not (TY_LE_MIN <= ty <= TY_LE_MAX):
            canh.append(f"tỉ lệ {ty} nằm ngoài khoảng thường dùng — crop dễ mất chủ thể")
        ra.append({"tep": ten, "url": u_goc, "ten_goc": ten_goc, "kich_thuoc": f"{w}x{h}",
                   "ty_le": ty, "bao": "anh tự đưa", "nguon_bai": trang,
                   "giay_phep": "anh tự đưa — anh tự chịu trách nhiệm nguồn",
                   "canh_bao": " · ".join(canh), "can_soi": "", "dau_nguon": ""})

    # soi watermark — chỉ ĐỌC và dán nhãn, không xoá tấm nào
    tot = [a for a in ra if "loi" not in a]
    if tot:
        nhan = soi_watermark(thu_muc, [a["tep"] for a in tot])
        for a in tot:
            n = nhan.get(a["tep"], {})
            a["dau_nguon"], a["can_soi"] = n.get("dau_nguon", ""), n.get("can_soi", "")
            if n.get("canh_bao"):
                a["canh_bao"] = (a["canh_bao"] + " · " if a["canh_bao"] else "") + n["canh_bao"]
    _luu_van_tay(so_vt, p_vt)
    _luu_van_tay(so_loi, p_loi)                    # sổ vân LÕI đi kèm, đừng bỏ quên
    _ghi_so(thu_muc, tot)
    return {"anh": tot, "hong": [a for a in ra if "loi" in a],
            "so_dau_nguon": len([a for a in tot if a["dau_nguon"]])}


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    cach, doi_so, thu = sys.argv[1], sys.argv[2], sys.argv[3]
    can = int(sys.argv[4]) if len(sys.argv) > 4 else 18
    r = tim(doi_so, thu, can) if cach == "tim" else boc_bai(doi_so, thu, can)
    if r.get("loi"):
        sys.exit("DỪNG — " + r["loi"])
    print(f"gắp được {len(r['anh'])} ảnh  ({r['so_sach']} sạch · {r['so_co_vang']} cờ vàng)")
    for a in r["anh"]:
        print(f"   {'🟡' if a['can_soi'] else '✅'} {a['tep']}  {a['kich_thuoc']}  {a['url'][:70]}")
