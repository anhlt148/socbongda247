#!/usr/bin/env python3
"""TRỢ LÝ VIẾT LỜI BÌNH — từ một tin ra kịch bản video 30 giây.

Ba bước:
  ① Đọc thêm bài gốc (lấy chi tiết, số liệu — tiêu đề RSS quá ngắn để viết)
  ② Đối chiếu: tin có mấy nguồn cùng đưa → biết số liệu nào chắc
  ③ Gọi model viết theo HỒ SƠ VĂN PHONG đã rút từ 100 video đã nổ

Ra một JSON: tiêu đề, lời bình, cụm tô vàng, câu bình luận ghim, cảnh báo nếu có.
Model chỉ được dùng số liệu có trong tư liệu — cấm bịa; phần này ghi thẳng vào lệnh.
"""
import json, os, re, subprocess, sys, tempfile
import urllib.request


# đường đầy đủ trước, tên trần sau: script có thể chạy ngoài trạm (cron, launchd
# một-lần) nơi PATH không có ~/.local/bin — gọi tên trần là FileNotFoundError câm
_CLAUDE = next((p for p in (os.path.expanduser("~/.local/bin/claude"),
                            "/opt/homebrew/bin/claude") if os.path.exists(p)), "claude")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD

BASE = DD.MAY
HO_SO = DD.VAN_PHONG


def _phan_may_doc(duong_dan):
    """Lấy phần nằm giữa <!-- MÁY ĐỌC --> và <!-- HẾT MÁY ĐỌC --> của một file bộ não.

    Anh chốt 06/08: bộ não chỉ còn MỘT bản, nằm trên Drive, dùng chung cho người và máy.
    Nhưng bản đó dài (luật viết + sổ học + ghi chú phương pháp) mà máy chỉ cần phần luật.
    Nên đánh mốc trong file: sửa bộ não là máy đổi theo ngay, không phải chép sang đâu cả,
    và lời nhắc không phình theo phần dành cho người đọc.

    Không thấy mốc thì trả cả file — thà lời nhắc dài còn hơn máy viết thiếu luật.
    """
    if not os.path.exists(duong_dan):
        raise FileNotFoundError(
            f"thiếu bộ não phong cách: {duong_dan}\n"
            "Bộ não nằm trên Google Drive — kiểm xem Drive đã đồng bộ chưa."
        )
    chu = open(duong_dan, encoding="utf-8").read()
    m = re.search(r"<!--\s*MÁY ĐỌC\s*-->(.*?)<!--\s*HẾT MÁY ĐỌC\s*-->", chu, re.S)
    return (m.group(1) if m else chu).strip()
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "Chrome/126.0 Safari/537.36")


def _doc_bai(url, gioi_han=6000):
    """Tải bài gốc, bóc phần chữ. Google News chuyển hướng nên phải theo dấu."""
    try:
        r = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(r, timeout=25) as res:
            raw = res.read(400000)
            enc = res.headers.get_content_charset() or "utf-8"
        h = raw.decode(enc, "replace")
        h = re.sub(r"(?is)<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>", " ", h)
        # Ưu tiên vùng bài viết — nhưng phải lấy khối <article> DÀI NHẤT, không phải khối
        # đầu tiên. Bài học 04/08: VietnamNet mở đầu bằng một <article> chứa video nhúng
        # dài vỏn vẹn 234 ký tự; lấy nhầm khối đó thì hàm tưởng bài quá mỏng, nhảy sang
        # link khác trong cụm, và model viết về một bài của báo khác hẳn.
        khoi = re.findall(r"(?is)<article[^>]*>(.*?)</article>", h)
        if khoi:
            dai_nhat = max(khoi, key=len)
            if len(re.sub(r"(?s)<[^>]+>", " ", dai_nhat).split()) >= 120:
                h = dai_nhat                       # đủ dày mới tin là bài chính
        chu = re.sub(r"(?s)<[^>]+>", " ", h)
        chu = re.sub(r"&[a-z]+;|&#\d+;", " ", chu)
        chu = " ".join(chu.split())
        return chu[:gioi_han]
    except Exception as e:
        return ""


def _goi_model(loi_nhac, timeout=180):
    p = subprocess.run([_CLAUDE, "-p"], input=loi_nhac, capture_output=True,
                       text=True, timeout=timeout)
    return p.stdout.strip()


NHIP_DOC = 258      # tiếng/phút — giọng VBee Ngọc Huyền, tốc độ 1.1, đo 05/08


def viet(tin, so_giay=58):
    """tin = một mục trong bảng tin của san_tin.py

    Mặc định 58 giây — anh chốt 06/08 lấy theo Nhím (100 video của họ có độ dài
    trung vị 58 giây, lời 229 tiếng). Video 30 giây cũ quá ngắn để kể trọn một câu
    chuyện có bản lề lật mạch, mà bản lề mới là thứ giữ người xem.
    """
    # Nhịp đọc: dùng MỘT hằng số duy nhất cho cả tính toán lẫn lời nhắc.
    # Bản cũ tính bằng 226 nhưng lại bảo model là 265 — hai chỗ lệch nhau, phát hiện 06/08.
    # 226 là số đo ngày 04/08 trên ba video; đo lại 05/08 trên hai file giọng mới ra 258–261.
    # Nhím đọc 238 tiếng/phút, giọng mình nhanh hơn ~8% nên cùng số tiếng sẽ ra video ngắn hơn.
    so_tieng = int(so_giay * NHIP_DOC / 60)
    # thử lần lượt các link báo trực tiếp tới khi lấy được nội dung đủ dài
    tu_lieu, bai_da_doc = "", None
    for u in ([tin.get("link")] if tin.get("link") else []) + (tin.get("cac_link") or []):
        if not u or "news.google.com" in u:
            continue
        tu_lieu = _doc_bai(u)
        if len(tu_lieu) > 800:
            bai_da_doc = u
            break
    # KHÔNG dùng `if exists else ""`: hồ sơ rỗng thì model vẫn viết, nhưng viết sai giọng
    # kênh mà không ai biết. Thiếu hồ sơ là lỗi phải DỪNG, không phải lỗi bỏ qua được.
    ho_so = (_phan_may_doc(DD.BO_NAO) + "\n\n" + _phan_may_doc(DD.THU_VIEN))

    loi_nhac = f"""Bạn là biên tập viên của kênh YouTube Shorts "Sóc Bóng Đá 247" — kể chuyện
bóng đá Việt Nam trong 30 giây. Viết kịch bản cho MỘT video từ tin dưới đây.

=== BỘ NÃO PHONG CÁCH CỦA KÊNH (bắt buộc theo) ===
Đo từ 100 short của kênh dẫn đầu ngách. Học KHUÔN và VỐN TỪ, tuyệt đối không chép nguyên câu.
{ho_so[:14000]}

=== TIN CẦN LÀM ===
Tiêu đề tin: {tin['tieu_de']}
Số báo cùng đưa tin: {tin.get('so_nguon', 1)}
Các nguồn: {', '.join(tin.get('cac_nguon', [])[:8])}
Tin cách đây: {tin.get('tuoi_gio', '?')} giờ

=== TƯ LIỆU LẤY TỪ BÀI GỐC ===
{tu_lieu if tu_lieu else "(không tải được bài gốc — chỉ có tiêu đề)"}

=== YÊU CẦU ===
1. TIÊU ĐỀ VIDEO: **70–80 ký tự** (đo được kênh dẫn đầu dùng trung bình 76 — tít dài là CỐ Ý,
   đủ chỗ cho trọn một mệnh đề nhân–quả; tít cụt là vứt mất chỗ giữ chân người xem).
   VIẾT HOA TOÀN BỘ. Không chấm than, không emoji, không hashtag — đo được kênh dẫn đầu
   dùng 0%. Theo một trong sáu khuôn tít trong bộ não. Ưu tiên khuôn có dấu phẩy chia hai vế
   (vế 1 dựng bối cảnh, vế 2 bung cú đấm) — gần một nửa số tít dùng khuôn này.
   Không spoil đáp án. Không hứa thứ tư liệu không có.
2. LỜI BÌNH: khoảng {so_tieng} tiếng (video {so_giay} giây, giọng đọc {NHIP_DOC} tiếng/phút).
   Bốn nhịp: **câu đầu ĐỌC LẠI NGUYÊN TIÊU ĐỀ, không sót chữ nào** (98/100 video của kênh
   dẫn đầu làm vậy) → bối cảnh ngắn hai ba câu → diễn biến kể theo CẢM XÚC CỦA NGƯỜI,
   không theo mốc phút trận đấu → chốt theo một trong bốn kiểu chốt trong bộ não.
   **Phải có ít nhất một BẢN LỀ lật mạch** ("Nhưng đằng sau đó là…", "Lý do ư?",
   "Nhưng sự thật là…") — thiếu bản lề thì nghe như đọc báo.
   Mỗi câu một ĐỘNG TỪ MẠNH, đừng ba tính từ. Câu ngắn 12–18 tiếng, không từ đệm thừa.
   MỌI CON SỐ VIẾT BẰNG CHỮ (tám nghìn sáu trăm, không viết 8.600) vì máy đọc hay sai;
   mỗi video tối đa hai ba con số, chọn con số biết kể chuyện.
   Xưng "anh em" và tự xưng "Sóc" — nhưng CHỈ ở ba chỗ: khi mời người xem nghĩ cùng,
   khi hỏi ý ở đoạn chốt, khi bênh vực ai đó. Rắc đều cả bài là nhão.
3. CỤM TÔ VÀNG: 1-2 cụm ngắn trong tiêu đề để tô màu nhấn.
4. BÌNH LUẬN GHIM: một câu hỏi có ĐÚNG HAI PHE trả lời.
5. TỪ KHOÁ: 8-12 cụm tìm kiếm YouTube. Mỗi phần tử là MỘT cụm duy nhất — CẤM ký tự
   "/" hay gộp nhiều biến thể vào một thẻ; KHÔNG cần bản không dấu (máy tự sinh).
   Chỉ chọn cụm người xem THẬT SỰ gõ tìm: tên riêng cầu thủ, đội bóng, giải đấu,
   sân bóng + cụm tin quen thuộc ("tin bóng đá", "bóng đá việt nam"). TRÁNH danh
   từ chung bóc từ bài mà chẳng ai tìm ("công nghệ mái", "trận lớn", "nâng cấp").
6. KIỂM CHỦ ĐỀ: đọc tư liệu rồi trả lời tin này có thật sự về BÓNG ĐÁ không.
   Kênh chỉ làm bóng đá. Tin về bóng chuyền, bóng rổ, tennis… dù có chữ "Việt Nam"
   trong tiêu đề vẫn phải loại. Ghi vào trường "la_bong_da": true/false.

=== LUẬT SỰ THẬT — QUAN TRỌNG NHẤT ===
- CHỈ dùng thông tin có trong tư liệu trên. TUYỆT ĐỐI không bịa số liệu, không suy đoán.
- Nếu tư liệu quá mỏng để viết đủ {so_tieng} tiếng, viết ngắn hơn và ghi vào "canh_bao".
- Nếu tin chỉ có 1 nguồn đưa, ghi cảnh báo "tin một nguồn, cần kiểm thêm".

Trả về DUY NHẤT một khối JSON, không giải thích gì thêm:
{{"tieu_de": "...", "loi_binh": "...", "cum_to_vang": ["..."],
  "binh_luan_ghim": "...", "tu_khoa": ["..."], "la_bong_da": true,
  "canh_bao": "..." }}"""

    ra = _goi_model(loi_nhac)
    m = re.search(r"\{.*\}", ra, re.S)
    if not m:
        return {"loi": "model không trả JSON", "tho": ra[:400]}
    try:
        d = json.loads(m.group(0))
    except Exception as e:
        return {"loi": f"JSON hỏng: {e}", "tho": m.group(0)[:400]}
    import lam_tag
    d["tu_khoa"] = lam_tag.chuan_hoa(d.get("tu_khoa"))
    d["so_tieng_thuc"] = len(d.get("loi_binh", "").split())
    # HAI CỬA TỰ KIỂM trước khi cho qua xưởng
    loi = []
    if d.get("la_bong_da") is False:
        loi.append("KHÔNG PHẢI BÓNG ĐÁ — loại")
    if len(d.get("tieu_de", "")) > 60:
        loi.append(f"tiêu đề {len(d['tieu_de'])} ký tự, quá 60")
    if d["so_tieng_thuc"] < so_tieng * 0.6:
        loi.append(f"lời bình chỉ {d['so_tieng_thuc']} tiếng, cần ~{so_tieng}")
    if re.search(r"\d", d.get("loi_binh", "")):
        loi.append("lời bình còn chữ số — phải viết bằng chữ để máy đọc đúng")
    # Cửa LỆCH TƯ LIỆU: model được dặn tự khai khi tư liệu không khớp tiêu đề tin. Khai
    # rồi mà vẫn cho chạy tiếp thì lời khai vô nghĩa — video sẽ nói về một tin khác hẳn
    # tin mình chọn (đã xảy ra 04/08 với hai kịch bản liền).
    if re.search(r"LỆCH|KHÔNG khớp", d.get("canh_bao", ""), re.I):
        loi.append("TƯ LIỆU LỆCH TIÊU ĐỀ TIN — model đọc phải bài khác, cần lấy lại tư liệu")
    d["bai_da_doc"] = bai_da_doc
    d["dat"] = not loi
    d["ly_do_khong_dat"] = loi
    d["nguon_tin"] = tin.get("link")
    d["tin_goc"] = tin["tieu_de"]
    d["so_nguon"] = tin.get("so_nguon", 1)
    return d


if __name__ == "__main__":
    ap = sys.argv[1:]
    if not ap:
        sys.exit("dùng: viet_loi_binh.py <mã tin> [số giây]  (mã lấy từ bảng tin)")
    ma = ap[0]
    giay = int(ap[1]) if len(ap) > 1 else 30
    from datetime import datetime
    bt = os.path.join(DD.BAN_TIN, datetime.now().strftime("%Y-%m-%d") + ".json")
    ds = json.load(open(bt))
    tin = next((t for t in ds if t["ma"] == ma), None)
    if not tin:
        sys.exit(f"không thấy mã {ma} trong {bt}")
    print(f"Đang viết cho: {tin['tieu_de'][:70]}…\n")
    kq = viet(tin, giay)
    print(json.dumps(kq, ensure_ascii=False, indent=1))
