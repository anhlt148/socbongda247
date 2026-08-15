#!/usr/bin/env python3
"""Lấy ảnh minh hoạ từ chính bài báo của tin — kèm ghi sổ nguồn.

Lọc bốn tầng:
  ① bỏ ảnh nhỏ, biểu tượng, quảng cáo, ảnh tác giả (theo tên tệp và kích thước)
  ② bỏ ảnh không đủ độ phân giải cho khung dọc 1080 (ảnh mờ lên video thấy ngay)
  ③ bỏ ảnh quá ngang hoặc quá dọc (crop về khung gần vuông sẽ mất chủ thể)
  ④ chạy dò watermark — ảnh dính dấu chìm giữa khung thì loại
"""
import concurrent.futures as cf, hashlib, json, os, re, shutil, subprocess, sys
import urllib.request
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD

_DO_LOGO = None


def _do_logo():
    """Nạp bộ dò watermark (trên Drive) một lần rồi dùng lại."""
    global _DO_LOGO
    if _DO_LOGO is None:
        _DO_LOGO = DD.nap(DD.DO_LOGO, "do_logo")
    return _DO_LOGO


def _ocr_song_khong():
    """Cổng chỉ có giá trị khi chính nó nhìn được. Tesseract thiếu gói tiếng Việt thì
    OCR trả RỖNG mà không báo lỗi — cổng hoá ra luôn cho qua, tưởng sạch mà không sạch
    (bài học 04/08: `brew install tesseract-lang`). Nên kiểm mắt trước khi gác cửa."""
    if not shutil.which("tesseract"):
        return False, "chưa cài tesseract (brew install tesseract tesseract-lang)"
    try:
        r = subprocess.run(["tesseract", "--list-langs"], capture_output=True,
                           text=True, timeout=20)
        co = set(r.stdout.split())
        thieu = {"vie", "eng"} - co
        if thieu:
            return False, f"tesseract thiếu gói ngôn ngữ {'+'.join(sorted(thieu))} " \
                          f"(brew install tesseract-lang)"
    except Exception as e:
        return False, f"không chạy được tesseract: {e}"
    return True, ""


# ── CỔNG HAI BẬC ─────────────────────────────────────────────────────────────
# Vì sao không chặn mọi ảnh có chữ ở góc: đo thực 04/08 trên ảnh VnExpress — một ảnh
# cầu thủ Việt Nam ăn mừng bị loại oan vì OCR đọc được biển quảng cáo sân ở góc dưới
# ("A SUSTAINABLE", "KANSAI"). Chữ trong ảnh KHÔNG phân biệt được "chữ của cảnh thật"
# (biển sân, số áo, băng-rôn) với "dấu dán đè". Chặn tất là vứt mất ảnh đẹp nhất.
#
#   BẬC 1 — CHẶN CỨNG: đọc ra tên báo / tên kênh / @tài khoản / ký hiệu bản quyền.
#           Dấu nguồn thật gần như luôn mang một trong các cụm này. Chặn là loại thẳng.
#   BẬC 2 — CỜ VÀNG:   chữ khác ở vùng góc/giữa. Không loại, nhưng ĐÁNH DẤU và xếp
#           xuống cuối hàng. Xưởng dùng hết ảnh sạch trước; phải đụng tới ảnh cờ vàng
#           thì báo lên để anh soi mắt (bài học 6: người vẫn bấm nút cuối).
#
# Nguyên tắc giữ nguyên từ bài học 3: KHÔNG có đường nào đi qua cổng mà không bị xét.
# Cờ vàng không phải "bỏ qua" — là "chuyển cho người", có ghi sổ.
VUNG_CHAN = ("góc trên trái", "góc trên phải", "góc dưới trái", "góc dưới phải",
             "dải trên", "dải dưới", "giữa khung")

DAU_NGUON = re.compile(
    # ký hiệu bản quyền & tài khoản
    r"(@\w|watermark|copyright|bản quyền|all rights|©|\.com|\.vn|\.net|\.tv|"
    # NHÀ ĐÀI — nguy hiểm nhất, ảnh chụp màn hình sóng luôn dính logo góc.
    # Thêm sau khi đo thực 04/08: một ảnh chụp sóng FPT Play lọt vào nhóm "sạch".
    r"fpt ?play|fptplay|vtv|vtc ?now|on ?sports|on ?football|k\+|kplus|tv360|sctv|"
    r"next ?sports|next ?media|htv|thvl|vieon|fifa\+|bein|sky ?sports|espn|"
    # hãng ảnh
    r"getty|reuters|afp|epa|ap photo|shutterstock|alamy|imago|icon ?sport|"
    # báo Việt Nam
    r"vnexpress|dantri|dân trí|tuoitre|tuổi trẻ|thanhnien|thanh niên|vietnamnet|"
    r"zing|znews|24h|thethao|bongda|bóng đá|kenh14|soha|nld|người lao động|vov|"
    r"baotintuc|tienphong|tiền phong|laodong|lao động|nhipcongtruong|"
    # mạng xã hội
    r"tiktok|douyin|kuaishou|facebook|youtube|instagram|threads)", re.I)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "Chrome/126.0 Safari/537.36")
BO_QUA = re.compile(
    r"(logo|icon|avatar|sprite|banner|ads?|quangcao|placeholder|blank|1x1|spacer|"
    r"favicon|thumb_w/(4|6|8)\d|/\d{2}x\d{2}/|author|tacgia|share|social)", re.I)


def _lay_url_anh(url_bai):
    try:
        r = urllib.request.Request(url_bai, headers={"User-Agent": UA})
        with urllib.request.urlopen(r, timeout=25) as res:
            h = res.read(500000).decode(res.headers.get_content_charset() or "utf-8", "replace")
    except Exception:
        return []
    # ưu tiên vùng bài viết nếu tách được
    m = re.search(r"(?is)<article[^>]*>(.*?)</article>", h)
    vung = m.group(1) if m else h
    urls = re.findall(r'(?:data-src|data-original|src)=["\']?(https?://[^"\'\s>]+\.(?:jpg|jpeg|png|webp)[^"\'\s>]*)', vung)
    urls += re.findall(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', h)
    sach, thay = [], set()
    for u in urls:
        u = u.replace("&amp;", "&")
        if BO_QUA.search(u) or u in thay:
            continue
        thay.add(u)
        sach.append(u)
    return sach[:25]


def _tai(u, thu_muc, i):
    try:
        r = urllib.request.Request(u, headers={"User-Agent": UA})
        with urllib.request.urlopen(r, timeout=25) as res:
            data = res.read(9_000_000)
        if len(data) < 25_000:                       # ảnh quá nhẹ = ảnh nhỏ/biểu tượng
            return None
        p = os.path.join(thu_muc, f"a{i:02d}.jpg")
        open(p, "wb").write(data)
        im = Image.open(p)
        im.load()
        w, h = im.size
        if w < 900 or h < 600:                       # không đủ nét cho khung 1080
            os.remove(p); return None
        ty = w / h
        if not (1.1 <= ty <= 2.2):                   # quá vuông hoặc quá ngang
            os.remove(p); return None
        im = im.convert("RGB")
        im.thumbnail((2200, 2200), Image.LANCZOS)    # thu để dựng nhanh
        im.save(p, quality=92)
        return {"tep": os.path.basename(p), "url": u, "kich_thuoc": f"{w}x{h}"}
    except Exception:
        try:
            os.path.exists(p) and os.remove(p)
        except Exception:
            pass
        return None


# Báo đưa ảnh thẳng trong HTML (đo 04/08/2026). Báo khác dùng JavaScript nạp ảnh nên
# HTML thô không có gì — ưu tiên ba báo này khi gom ảnh.
BAO_CO_ANH = ("tuoitre.vn", "vietnamnet.vn", "vnexpress.net", "thethao247.vn", "24h.com.vn")


def lay(url_bai, thu_muc, can=10, ten_nguon="", them_link=None, so_bai=5):
    """Gom ảnh từ NHIỀU bài trong cùng cụm tin — một bài thường chỉ 4-11 ảnh, không đủ.

    so_bai: quét bao nhiêu bài. Để 5 khi chạy tự động cho nhanh; nâng lên 12-20 khi cần
    NHIỀU ảnh để người CHỌN (bài học 04/08: ảnh sai người, sai trận là do không có gì
    mà chọn, chứ không phải do lọc kém).
    """
    os.makedirs(thu_muc, exist_ok=True)
    ds_link = [url_bai] + [u for u in (them_link or []) if u != url_bai]
    ds_link.sort(key=lambda u: 0 if any(b in u for b in BAO_CO_ANH) else 1)
    urls, thay = [], set()
    for u in ds_link[:so_bai]:
        for a in _lay_url_anh(u):
            if a not in thay:
                thay.add(a); urls.append((a, u))
        if len(urls) >= can * 2:
            break
    urls = [u for u, _ in urls]
    if not urls:
        return {"anh": [], "loi": "không tìm thấy ảnh trong bài (báo dùng JavaScript nạp ảnh)"}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        kq = [x for x in ex.map(lambda t: _tai(t[1], thu_muc, t[0]), enumerate(urls)) if x]
    # ── CỔNG WATERMARK — có mã thoát, không chỉ có lời mô tả ─────────────────
    # Bài học 04/08: "phát hiện watermark mà không chặn thì bằng không" — đã để lọt
    # @nhipcongtruong vào video đã giao. Trước bản này, đoạn code ở đây CHỈ cắt lấy N
    # ảnh đầu; phần dò hoàn toàn không tồn tại, dù mô tả đầu file nói là có.
    nhin_duoc, vi_sao = _ocr_song_khong()
    if not nhin_duoc:
        for a in kq:                                    # mù thì không gác cửa được
            p = os.path.join(thu_muc, a["tep"])
            os.path.exists(p) and os.remove(p)
        return {"anh": [], "loi": f"CỔNG WATERMARK MÙ — {vi_sao}. Dừng, không lấy ảnh nào."}

    dl = _do_logo()
    cach_ly = os.path.join(thu_muc, "_dinh-watermark")
    sach, co_vang, bi_loai = [], [], []
    for a in kq:
        p = os.path.join(thu_muc, a["tep"])
        if not os.path.exists(p):
            continue
        try:
            doc_duoc = dl.do_chu(p, la_anh=True)
        except Exception as e:                          # dò hỏng = coi như bẩn, không cho qua
            a["ly_do_loai"] = f"dò lỗi: {e}"
            bi_loai.append(a)
            os.makedirs(cach_ly, exist_ok=True)
            shutil.move(p, os.path.join(cach_ly, a["tep"]))
            continue

        chan = [f"{v}: “{c[:40]}”" for v, c in doc_duoc.items() if DAU_NGUON.search(c)]
        if chan:                                        # BẬC 1 — dấu nguồn, loại thẳng
            a["ly_do_loai"] = "dấu nguồn · " + " · ".join(chan)
            bi_loai.append(a)
            os.makedirs(cach_ly, exist_ok=True)
            shutil.move(p, os.path.join(cach_ly, a["tep"]))
            continue

        a["nguon_bai"], a["bao"] = url_bai, ten_nguon
        a["giay_phep"] = "ảnh báo chí — CHƯA xin phép"
        vang = [f"{v}: “{c[:40]}”" for v, c in doc_duoc.items() if v in VUNG_CHAN]
        if vang:                                        # BẬC 2 — cờ vàng, để người soi
            a["can_soi"] = " · ".join(vang)
            co_vang.append(a)
        else:
            a["can_soi"] = ""
            sach.append(a)

    # ảnh sạch đứng trước, cờ vàng xếp cuối — xưởng lấy từ đầu nên tự tránh ảnh nghi
    dung_duoc = (sach + co_vang)[:can]
    for a in kq:                                        # dọn ảnh dư không dùng tới
        p = os.path.join(thu_muc, a["tep"])
        if os.path.exists(p) and a not in dung_duoc:
            os.remove(p)

    json.dump({"anh": dung_duoc, "bi_loai": bi_loai, "nguon_bai": url_bai, "bao": ten_nguon,
               "so_sach": len([a for a in dung_duoc if not a["can_soi"]]),
               "so_co_vang": len([a for a in dung_duoc if a["can_soi"]]),
               "cong_watermark": "OCR vie+eng từng ảnh · bậc 1 chặn dấu nguồn · bậc 2 cờ vàng"},
              open(os.path.join(thu_muc, "nguon-anh.json"), "w"),
              ensure_ascii=False, indent=1)
    return {"anh": dung_duoc, "bi_loai": bi_loai,
            "so_sach": len([a for a in dung_duoc if not a["can_soi"]]),
            "so_co_vang": len([a for a in dung_duoc if a["can_soi"]])}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("dùng: lay_anh.py <url bài báo> <thư mục ra> [số ảnh cần]")
    can = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    r = lay(sys.argv[1], sys.argv[2], can)
    print(f"lấy được {len(r['anh'])} ảnh dùng được" + (f" — {r.get('loi','')}" if r.get("loi") else ""))
    for a in r["anh"]:
        co = "🟡" if a.get("can_soi") else "✅"
        print(f"   {co} {a['tep']}  {a['kich_thuoc']}"
              + (f"  cần soi: {a['can_soi'][:50]}" if a.get("can_soi") else ""))
    for a in r.get("bi_loai", []):
        print(f"   ⛔ {a['tep']}  loại: {a['ly_do_loai'][:70]}")
