#!/usr/bin/env python3
"""TRỢ LÝ SĂN TIN — Sóc Bóng Đá 247

Quét 38 nguồn mỗi sáng, gom tin trùng, chấm điểm độ nóng, xuất bảng tin xếp hạng
để anh chỉ việc đánh dấu tin nào làm video.

Nguyên tắc chấm điểm — thứ tự quan trọng:
  1. NHIỀU NGUỒN CÙNG ĐƯA  → tín hiệu mạnh nhất. Một tin 5 báo cùng đăng trong 6 giờ
     là tin thật sự nóng; một tin chỉ 1 báo đăng thì thường là tin nhỏ hoặc tin lá cải.
  2. ĐỘ MỚI                → tin nóng có hạn dùng; quá 24 giờ là mất sóng.
  3. DÍNH VIỆT NAM         → kênh Việt, tin không liên quan VN thì hay đến mấy cũng khó nổ.
  4. TỪ KHOÁ GÂY TÒ MÒ     → học từ chính tiêu đề các video đã nổ của đối thủ.

TỰ HỌC: mỗi lần anh chọn (hoặc bỏ) một tin, ghi vào `hoc-tu-anh.jsonl`. Lần chạy sau,
những cụm từ xuất hiện nhiều trong tin ĐƯỢC CHỌN sẽ được cộng điểm, cụm trong tin BỊ BỎ
sẽ bị trừ. Càng dùng càng chấm giống anh.

Dùng:
  python3 san_tin.py quet                    # quét, xuất bảng tin hôm nay
  python3 san_tin.py chon <mã> [<mã>...]     # đánh dấu tin sẽ làm  → máy học
  python3 san_tin.py bo   <mã> [<mã>...]     # đánh dấu tin bỏ qua  → máy học
  python3 san_tin.py hoc                     # xem máy đã học được gì
"""
import argparse, hashlib, html, json, os, re, sys, unicodedata
import urllib.request, concurrent.futures as cf
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from xml.etree import ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
SO_TIN = os.path.join(BASE, "ban-tin")
HOC = os.path.join(BASE, "hoc-tu-anh.jsonl")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "Chrome/126.0 Safari/537.36")


def _gg(q, hl, gl):
    return (f"https://news.google.com/rss/search?q={quote(q)}"
            f"&hl={hl}&gl={gl}&ceid={gl}:{hl.split('-')[0]}")


# ── 38 nguồn đã kiểm sống 04/08/2026 ──
NGUON = {
    # Báo Việt Nam (tin trong nước, nhanh nhất)
    "VnExpress": ("https://vnexpress.net/rss/the-thao.rss", "vn"),
    "Thanh Niên": ("https://thanhnien.vn/rss/the-thao.rss", "vn"),
    "Tuổi Trẻ": ("https://tuoitre.vn/rss/the-thao.rss", "vn"),
    "Dân Trí": ("https://dantri.com.vn/rss/the-thao.rss", "vn"),
    "Znews": ("https://znews.vn/rss/the-thao.rss", "vn"),
    "VTC": ("https://vtcnews.vn/rss/the-thao.rss", "vn"),
    "Vietnamnet": ("https://vietnamnet.vn/rss/the-thao.rss", "vn"),
    "TheThao247": ("https://thethao247.vn/trang-chu.rss", "vn"),
    "Người Lao Động": ("https://nld.com.vn/rss/the-thao.rss", "vn"),
    "24h": ("https://www.24h.com.vn/upload/rss/bongda.rss", "vn"),
    # Google News tiếng Việt — bắt cả tin gốc từ mạng xã hội khi báo đưa lại
    "GG tuyển VN": (_gg("đội tuyển Việt Nam", "vi", "VN"), "vn"),
    "GG V-League": (_gg("V-League", "vi", "VN"), "vn"),
    "GG cầu thủ xuất ngoại": (_gg("cầu thủ Việt Nam xuất ngoại", "vi", "VN"), "vn"),
    "GG Xuân Son": (_gg("Nguyễn Xuân Son", "vi", "VN"), "vn"),
    # Đông Nam Á — đối thủ trực tiếp, tin về họ dễ nổ ở VN
    "GG Thái": (_gg("ทีมชาติไทย ฟุตบอล", "th", "TH"), "dna"),
    "GG Indo": (_gg("timnas indonesia", "id", "ID"), "dna"),
    "GG Malay": (_gg("bola sepak Malaysia", "ms", "MY"), "dna"),
    "GG Sing": (_gg("Singapore football", "en-SG", "SG"), "dna"),
    "Bangkok Post": ("https://www.bangkokpost.com/rss/data/sports.xml", "dna"),
    "Straits Times": ("https://www.straitstimes.com/news/sport/rss.xml", "dna"),
    # Châu Á khác
    "GG Hàn": (_gg("한국 축구 대표팀", "ko", "KR"), "asia"),
    "GG Nhật": (_gg("サッカー日本代表", "ja", "JP"), "asia"),
    "GG Trung": (_gg("中国足球", "zh-CN", "CN"), "asia"),
    "SCMP": ("https://www.scmp.com/rss/95/feed", "asia"),
    # Châu Âu — tin lớn, dùng cho video góc quốc tế
    "GG Anh": (_gg("Premier League", "en-GB", "GB"), "eu"),
    "GG TBN": (_gg("fútbol La Liga", "es", "ES"), "eu"),
    "GG Pháp": (_gg("football Ligue 1", "fr", "FR"), "eu"),
    "GG Đức": (_gg("Bundesliga Fußball", "de", "DE"), "eu"),
    "GG Hà Lan": (_gg("Eredivisie voetbal", "nl", "NL"), "eu"),
    "BBC Sport": ("https://feeds.bbci.co.uk/sport/football/rss.xml", "eu"),
    "Sky Sports": ("https://www.skysports.com/rss/12040", "eu"),
    "Marca": ("https://e00-marca.uecdn.es/rss/futbol/primera-division.xml", "eu"),
    "AS": ("https://as.com/rss/futbol/primera.xml", "eu"),
    "Kicker": ("https://newsfeed.kicker.de/news/fussball", "eu"),
    "Voetbal NL": ("https://www.vi.nl/rss", "eu"),
    # Mạng xã hội (phần cào được)
    "Reddit soccer": ("https://www.reddit.com/r/soccer/hot/.rss", "mxh"),
    "Reddit highlights": ("https://www.reddit.com/r/footballhighlights/.rss", "mxh"),
}

# Từ khoá dính Việt Nam — tin có mới dễ nổ trên kênh Việt
VIET = ["việt nam", "vietnam", "v-league", "vleague", "xuân son", "quang hải", "hoàng đức",
        "tiến linh", "đình bắc", "văn hậu", "công phượng", "kim sang", "filip nguyễn",
        "rafaelson", "nguyễn xuân son", "thể công", "hà nội fc", "nam định", "cahn",
        "hoàng anh gia lai", "hagl", "bình dương", "thanh hoá", "u23 việt nam", "u20 việt nam"]

# Môn KHÁC bóng đá — loại thẳng, kênh chỉ làm bóng đá
MON_KHAC = ["bóng chuyền", "bóng rổ", "cầu lông", "tennis", "quần vợt", "bơi lội", "điền kinh",
            "cờ vua", "boxing", "võ thuật", "đua xe", "f1", "golf", "bi-a", "billiards",
            "thể hình", "esports", "pickleball", "bóng bàn", "xe đạp", "marathon"]

# Cụm gây tò mò — rút từ tiêu đề các video đã nổ của kênh đối thủ
TO_MO = ["vì sao", "lý do", "bất ngờ", "lộ diện", "tiết lộ", "sự thật", "gây sốc", "chấn động",
         "quyết định", "chia tay", "chốt", "xác nhận", "phản ứng", "chỉ trích", "mỉa mai",
         "kỷ lục", "lịch sử", "đầu tiên", "cao nhất", "đắt nhất", "chấn thương", "nghỉ thi đấu",
         "triệu đô", "tỷ đồng", "nhập tịch", "xuất ngoại"]


def _sach(s):
    # Giải mã HAI LẦN: nhiều RSS mã hoá hai lớp (&amp;apos; → &apos; → '). Bản cũ giải
    # một lần nên tiêu đề còn nguyên "&apos;" — lọt thẳng vào tiêu đề video và vào lệnh
    # gửi model. Giải tới khi không đổi nữa, tối đa 3 vòng cho khỏi lặp vô tận.
    s = re.sub(r"<[^>]+>", " ", s or "")
    for _ in range(3):
        moi = html.unescape(s)
        if moi == s:
            break
        s = moi
    return " ".join(s.split())


def _chuan(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", s)


def _tu_khoa(tieu_de):
    """Rút cụm từ khoá để gom tin trùng (bỏ từ nối, giữ từ ≥4 ký tự)."""
    bo = {"cua", "cho", "voi", "trong", "khong", "duoc", "nhung", "nguoi", "sau", "truoc",
          "the", "and", "for", "with", "from", "that", "this", "sport", "bong", "footbal"}
    return {t for t in _chuan(tieu_de).split() if len(t) >= 4 and t not in bo}


def _lay(item):
    ten, (url, vung) = item
    try:
        r = urllib.request.Request(url, headers={"User-Agent": UA,
                                                 "Accept": "application/rss+xml,application/xml,text/xml,*/*"})
        with urllib.request.urlopen(r, timeout=25) as res:
            raw = res.read()
        root = ET.fromstring(raw)
        ra = []
        for it in root.iter():
            if not it.tag.endswith(("item", "entry")):
                continue
            td = pub = link = ""
            for c in it:
                t = c.tag.split("}")[-1]
                if t == "title":
                    td = _sach(c.text)
                elif t in ("pubDate", "published", "updated"):
                    pub = c.text or ""
                elif t == "link":
                    link = c.get("href") or c.text or ""
            if td:
                ra.append({"tieu_de": td, "nguon": ten, "vung": vung,
                           "gio": pub, "link": link})
        return ra
    except Exception:
        return []


def _tuoi_gio(s):
    for f in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
              "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            d = datetime.strptime(s.strip(), f)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - d).total_seconds() / 3600
        except Exception:
            continue
    return 999


def _hoc_da_biet():
    """Đọc sổ học: cụm nào anh hay chọn (+), cụm nào hay bỏ (−)."""
    diem = {}
    if not os.path.exists(HOC):
        return diem
    for l in open(HOC, encoding="utf-8"):
        try:
            d = json.loads(l)
        except Exception:
            continue
        w = 1.0 if d["quyet"] == "chon" else -0.6
        for t in _tu_khoa(d["tieu_de"]):
            diem[t] = diem.get(t, 0) + w
    return diem


def quet():
    with cf.ThreadPoolExecutor(max_workers=14) as ex:
        tat_ca = [x for ds in ex.map(_lay, NGUON.items()) for x in ds]
    print(f"kéo về {len(tat_ca)} tin thô từ {len(NGUON)} nguồn")

    # gom tin trùng: hai tin coi là một nếu chia sẻ ≥55% từ khoá
    cum = []
    for t in tat_ca:
        tdl = t["tieu_de"].lower()
        if any(m in tdl for m in MON_KHAC):        # bỏ tin môn khác
            continue
        tk = _tu_khoa(t["tieu_de"])
        if len(tk) < 3:
            continue
        for c in cum:
            # so với từ khoá GỐC của cụm, không phải tập đã phình — tránh cụm nuốt lẫn nhau
            chung = len(tk & c["goc"])
            if chung / min(len(tk), len(c["goc"])) >= 0.5 and chung >= 3:
                c["tin"].append(t)
                c["tu_khoa"] |= tk
                break
        else:
            cum.append({"goc": set(tk), "tu_khoa": tk, "tin": [t]})

    hoc = _hoc_da_biet()
    kq = []
    for c in cum:
        # đại diện: ưu tiên tin có link BÁO TRỰC TIẾP (Google News mã hoá link, không tải
        # được bài gốc) — trong cùng cụm thường có cả bản từ báo VN, dùng bản đó
        truc_tiep = [t for t in c["tin"] if "news.google.com" not in (t.get("link") or "")]
        nguon_uu_tien = truc_tiep or c["tin"]
        dai_dien = min(nguon_uu_tien, key=lambda x: _tuoi_gio(x["gio"]))
        td_thuong = _chuan(dai_dien["tieu_de"])
        nguon_khac = len({t["nguon"] for t in c["tin"]})
        tuoi = _tuoi_gio(dai_dien["gio"])

        d_nguon = min(nguon_khac, 6) * 12                       # tối đa 72
        d_moi = 25 if tuoi <= 6 else (15 if tuoi <= 12 else (8 if tuoi <= 24 else 0))
        d_viet = 30 if any(v in td_thuong or v in dai_dien["tieu_de"].lower() for v in VIET) else 0
        d_tomo = min(sum(3 for k in TO_MO if k in dai_dien["tieu_de"].lower()), 12)
        d_hoc = max(-15, min(15, sum(hoc.get(t, 0) for t in c["tu_khoa"]) * 2))
        tong = d_nguon + d_moi + d_viet + d_tomo + d_hoc

        # PHẠT TIN CŨ. Bản cũ chỉ CỘNG điểm mới (tối đa 25) nên tin 25 ngày tuổi vẫn được
        # 78 điểm ngang tin nóng 0 giờ — chỉ nhờ nhiều báo cùng đưa. Đo thực 04/08: hai tin
        # 605 giờ và 469 giờ nằm ngay top bảng. Kênh tin nóng mà đưa tin cũ là mất uy tín
        # với người xem, nên quá hạn phải bị TRỪ chứ không chỉ hết được cộng.
        if tuoi > 36:
            tong *= 0.45 if tuoi > 72 else 0.7

        kq.append({
            "ma": hashlib.md5(td_thuong.encode()).hexdigest()[:6],
            "diem": round(tong), "tieu_de": dai_dien["tieu_de"],
            "so_nguon": nguon_khac, "tuoi_gio": round(tuoi, 1),
            "vung": dai_dien["vung"], "link": dai_dien["link"],
            "cac_nguon": sorted({t["nguon"] for t in c["tin"]}),
            "cac_link": [t["link"] for t in c["tin"]
                         if t.get("link") and "news.google.com" not in t["link"]][:5],
            "chi_tiet": {"nguồn": d_nguon, "mới": d_moi, "dính VN": d_viet,
                         "tò mò": d_tomo, "học từ anh": round(d_hoc, 1)},
        })
    kq.sort(key=lambda x: -x["diem"])

    os.makedirs(SO_TIN, exist_ok=True)
    ngay = datetime.now().strftime("%Y-%m-%d")
    p = os.path.join(SO_TIN, f"{ngay}.json")
    json.dump(kq, open(p, "w"), ensure_ascii=False, indent=1)

    print(f"gom thành {len(kq)} cụm tin\n")
    print(f"{'MÃ':7s}{'ĐIỂM':>5s} {'NGUỒN':>6s} {'GIỜ':>6s}  TIÊU ĐỀ")
    print("─" * 100)
    for t in kq[:25]:
        v = {"vn": "🇻🇳", "dna": "🌏", "asia": "🌏", "eu": "🇪🇺", "mxh": "💬"}.get(t["vung"], "  ")
        print(f"{t['ma']:7s}{t['diem']:>5} {t['so_nguon']:>6} {t['tuoi_gio']:>5.0f}h {v} {t['tieu_de'][:78]}")
    print(f"\nbảng tin đầy đủ: {p}")
    print("Đánh dấu:  python3 san_tin.py chon <mã>   |   python3 san_tin.py bo <mã>")
    return kq


def _ghi_hoc(ma_list, quyet):
    ngay = datetime.now().strftime("%Y-%m-%d")
    p = os.path.join(SO_TIN, f"{ngay}.json")
    if not os.path.exists(p):
        sys.exit("chưa có bảng tin hôm nay — chạy `quet` trước")
    ds = json.load(open(p))
    idx = {t["ma"]: t for t in ds}
    with open(HOC, "a", encoding="utf-8") as f:
        for m in ma_list:
            if m not in idx:
                print("không thấy mã", m)
                continue
            f.write(json.dumps({"ngay": ngay, "ma": m, "quyet": quyet,
                                "tieu_de": idx[m]["tieu_de"]}, ensure_ascii=False) + "\n")
            print(f"  {'✓ chọn' if quyet=='chon' else '✗ bỏ'}: {idx[m]['tieu_de'][:70]}")


def xem_hoc():
    hoc = _hoc_da_biet()
    if not hoc:
        print("chưa học được gì — hãy dùng `chon`/`bo` vài lần")
        return
    tot = sorted(hoc.items(), key=lambda x: -x[1])[:15]
    xau = sorted(hoc.items(), key=lambda x: x[1])[:15]
    n = sum(1 for _ in open(HOC, encoding="utf-8"))
    print(f"đã học từ {n} lần anh đánh dấu\n")
    print("CỤM ANH HAY CHỌN (cộng điểm):")
    for t, d in tot:
        if d > 0:
            print(f"  +{d:>5.1f}  {t}")
    print("\nCỤM ANH HAY BỎ (trừ điểm):")
    for t, d in xau:
        if d < 0:
            print(f"  {d:>6.1f}  {t}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="lenh", required=True)
    sub.add_parser("quet")
    a = sub.add_parser("chon"); a.add_argument("ma", nargs="+")
    b = sub.add_parser("bo"); b.add_argument("ma", nargs="+")
    sub.add_parser("hoc")
    n = ap.parse_args()
    if n.lenh == "quet":
        quet()
    elif n.lenh == "chon":
        _ghi_hoc(n.ma, "chon")
    elif n.lenh == "bo":
        _ghi_hoc(n.ma, "bo")
    else:
        xem_hoc()
