#!/usr/bin/env python3
"""Bước 3: đưa một thư mục việc vào kho thành phẩm — đủ 7 tệp chuẩn + gói đăng .txt.

Gói đăng để dạng .txt (anh chốt): mở ra copy thẳng sang YouTube Studio, không phải
đọc qua trình xem markdown. Video Shorts nên KHÔNG có chapters — dưới một phút thì
mốc chương vô nghĩa.
"""
import json, os, re, shutil, subprocess, sys, time, unicodedata
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD
import kich_ban as KB
import dong_ho as DH
import lam_tag

import nen_tang as NT

KHO_PY = DD.nap(DD.KHO_VIDEO_PY, "kho_video")


from chuan_ten import slug_hoa                    # noqa: E402 — não một nguồn (16/08)


def _bo_sung_seo(viec, kb):
    """Bài anh ĐƯA TAY thiếu từ khoá SEO + bình luận ghim → gói đăng nghèo (anh bắt 07/08
    đêm: mục TAGS 4 thẻ, mục GHIM trống). Haiku sinh một lượt cho đủ bộ như bài hệ thống,
    ghi ngược vào kich-ban.json để lần sau khỏi gọi lại.

    CHẠY SỚM ĐƯỢC (anh đặt 12/08): đây là khâu DUY NHẤT của nút Kho tốn thời gian thật
    (30–90 giây gọi model; phần cơ khí còn lại chỉ 0,8 giây). Nó chỉ cần TIÊU ĐỀ + LỜI
    BÌNH — có đủ từ lúc dựng xong. Nên xưởng bắn nó chạy NỀN ngay sau khi dựng, lúc anh
    xem video là nó làm xong; bấm Kho chỉ còn việc chép tệp.
    """
    if kb.get("tu_khoa") and kb.get("binh_luan_ghim"):
        return kb
    # CỜ ĐANG CHẠY: bấm Kho đúng lúc bản nền chưa xong thì CHỜ nó, đừng gọi model lần
    # hai — hai lượt cùng ghi kich-ban.json là đè nhau, mà cũng phí một lượt haiku
    co = os.path.join(viec, ".dang-seo")
    if os.path.exists(co) and time.time() - os.path.getmtime(co) < 300:
        print("  ⏳ SEO đang được sinh nền — chờ…")
        for _ in range(60):
            time.sleep(3)
            if not os.path.exists(co):
                break
        try:
            kb2 = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
            if kb2.get("tu_khoa") and kb2.get("binh_luan_ghim"):
                print("  ✓ dùng SEO bản nền vừa sinh xong")
                return kb2
        except Exception:
            pass
    open(co, "w").write("1")
    # Luật tag rút từ vụ anh soi volume 09/08: thẻ "X / x" dính đôi + danh từ chung
    # chung ("công nghệ mái", "trận lớn") volume 0 cả loạt. Model CHỈ chọn cụm người
    # xem thật gõ tìm; bản không dấu, tách dính, khử trùng do lam_tag lo (việc cơ khí).
    lenh = (f'Video Shorts bóng đá của kênh "Sóc Bóng Đá 247".\n'
            f'TÍT: {kb.get("tieu_de", "")}\nLỜI ĐỌC: {kb.get("loi_binh", "")}\n\n'
            'Trả về DUY NHẤT một khối JSON đúng khuôn:\n'
            '{"tu_khoa": [10-12 thẻ tag SEO YouTube. LUẬT: mỗi phần tử là MỘT cụm duy'
            ' nhất, CẤM ký tự "/" hay gộp nhiều biến thể vào một thẻ; KHÔNG cần bản'
            ' không dấu (máy tự sinh). Chỉ chọn cụm người xem THẬT SỰ gõ vào ô tìm kiếm'
            ' YouTube: tên riêng cầu thủ, đội bóng, giải đấu, sân bóng trong bài + cụm'
            ' tin quen thuộc ("tin bóng đá", "bóng đá việt nam", "bóng đá hôm nay").'
            ' TRÁNH danh từ chung bóc từ bài mà chẳng ai tìm ("công nghệ mái", "trận'
            ' lớn", "nâng cấp", "tiến độ xây dựng")], '
            '"binh_luan_ghim": "1-2 câu bình luận ghim giọng gần gũi, chốt bằng MỘT câu hỏi'
            ' cho người xem", "hashtag": ["3 hashtag không dấu, có #"]}')
    try:
        r = subprocess.run([NT.tim_claude(), "-p", "--model",
                            "claude-haiku-4-5-20251001", lenh],
                           capture_output=True, text=True, timeout=240)
        m = re.search(r"\{.*\}", r.stdout, re.S)
        d = json.loads(m.group(0))
        if not kb.get("tu_khoa"):
            # haiku hay đổi tên khoá — nhận cả tags/the/tu_khoa, phần tử nào là chữ thì lấy
            tho = (d.get("tu_khoa") or d.get("tags") or d.get("the") or [])
            kb["tu_khoa"] = lam_tag.chuan_hoa(tho)[:24]
            if not kb["tu_khoa"]:
                print("  ⚠ haiku không trả thẻ — đầu ra thô:", (r.stdout or "")[:200])
        if not kb.get("binh_luan_ghim"):
            kb["binh_luan_ghim"] = d.get("binh_luan_ghim", "")
        if d.get("hashtag"):
            kb["hashtag_seo"] = d["hashtag"][:5]
        # GHI QUA CỬA CHUNG có khoá (12/08): SEO chạy SONG SONG với xưởng dựng, mà
        # xưởng cũng ghi `cum_to_vang` vào chính tệp này — ghi đè cả tệp là mất một bên
        kb = KB.ghi_gop(viec, {k: kb[k] for k in
                               ("tu_khoa", "binh_luan_ghim", "hashtag_seo")
                               if k in kb})
        print(f"  bổ sung SEO cho bài đưa tay: {len(kb.get('tu_khoa', []))} thẻ + ghim")
    except Exception as e:
        print(f"  ⚠ không sinh được SEO bổ sung ({e}) — gói đăng sẽ dùng bộ tối thiểu")
    finally:
        try:                                       # gỡ cờ ở MỌI đường ra, kể cả khi lỗi
            os.path.exists(co) and os.remove(co)
        except OSError:
            pass
    return kb


def _muc_thoi_gian(viec):
    """【7】 THỜI GIAN SẢN XUẤT — anh đặt 14/08: "muốn biết 1 video sản xuất trong bao lâu".

    In tổng + từng chặng kèm phần trăm, để nhìn một cái là biết khúc nào ăn thời gian.
    Việc nào chưa đủ mốc (bài cũ làm trước khi có đồng hồ) thì KHÔNG in mục này —
    thà thiếu còn hơn bịa số.
    """
    if not viec:
        return ""
    try:
        tk = DH.tong_ket(viec)
    except Exception:
        return ""
    if not tk.get("text"):
        return ""
    return ("【7】 THỜI GIAN SẢN XUẤT\n"
            + "-" * 64 + "\n" + tk["text"] + "\n")


def goi_dang(kb, tin, viec=None):
    """Gói đăng cho SHORTS: tiêu đề ngắn + #Shorts, mô tả 2 dòng, không chapters.

    KHÔNG ĐƯA LINK VÀO Ô MÔ TẢ (anh chốt 05/08). Link ngoài trong mô tả kéo người xem rời
    khỏi kênh, mà YouTube cũng phân phối dè chừng hơn với video có link ra ngoài.
    Nguồn tin vẫn được giữ — nhưng ở mục 【6】 GỐC TIN, là phần ghi chú NỘI BỘ để sau còn
    lần lại được, không dán lên YouTube.
    """
    td = kb["tieu_de"]
    tk = kb.get("tu_khoa") or []
    # tiêu đề đăng: chữ thường tự nhiên hơn cho khung Shorts, kèm #Shorts
    td_dang = td if td.endswith("#Shorts") else f"{td} #Shorts"
    hashtag = " ".join(kb.get("hashtag_seo") or
                       ["#socbongda247", "#bongdavietnam", "#aseancup2026"])
    hai_dong = kb["loi_binh"].split(".")[0].strip() + "."
    # chuan_hoa chạy LẦN CUỐI ngay trước khi in — kich-ban.json cũ (sinh trước 09/08)
    # vẫn còn thẻ dính đôi "X / x", qua đây là được tách sạch + đệm thẻ nhà + cắt 490.
    tags = ", ".join(lam_tag.chuan_hoa(tk, dem=("sóc bóng đá 247", "asean cup 2026",
                                                "tuyển việt nam", "bóng đá việt nam")))
    return f"""GÓI ĐĂNG — {DD.KENH} — {datetime.now():%d/%m/%Y}
================================================================

【1】 TIÊU ĐỀ  (dán vào ô Tiêu đề — {len(td_dang)} ký tự)
----------------------------------------------------------------
{td_dang}


【2】 MÔ TẢ  (dán vào ô Mô tả)
----------------------------------------------------------------
{hai_dong}
Tin nóng bóng đá Việt Nam mỗi ngày trên Sóc Bóng Đá 247.

{hashtag}


【3】 TAGS  (dán vào ô Thẻ)
----------------------------------------------------------------
{tags[:490]}


【4】 BÌNH LUẬN GHIM  (đăng xong dán ngay, rồi bấm ghim)
----------------------------------------------------------------
{kb.get('binh_luan_ghim', '')}


【5】 TRƯỚC KHI BẤM ĐĂNG
----------------------------------------------------------------
[ ] Chọn "Không, video này không dành cho trẻ em"
[ ] Ngôn ngữ: Tiếng Việt
[ ] Danh sách phát: Tin nóng bóng đá Việt
[ ] Hiển thị: Công khai (hoặc hẹn giờ đúng khung vàng)
[ ] Đăng xong: dán bình luận mục 4 và ghim lên đầu
[ ] Thumbnail Shorts: chỉ đặt được từ app YouTube trên điện thoại


【6】 GỐC TIN  (để kiểm lại khi cần)
----------------------------------------------------------------
Tin gốc  : {tin.get('tieu_de', '')}
Số nguồn : {kb.get('so_nguon', '?')} báo cùng đưa
Bài đã đọc: {kb.get('bai_da_doc') or kb.get('nguon_tin') or ''}
Cảnh báo : {kb.get('canh_bao', '(không)')}

{_muc_thoi_gian(viec)}"""


def xep(viec):
    kb = json.load(open(os.path.join(viec, "kich-ban.json")))
    kb = _bo_sung_seo(viec, kb)
    # Bài anh ĐƯA TAY vào trạm (nút ➕ Bài mới) không có tin-goc.json — thiếu thì dùng bản
    # tối thiểu, đừng sập cả bước xếp kho (anh gặp 07/08 đêm với video-5-bai-tay).
    p_tin = os.path.join(viec, "tin-goc.json")
    if os.path.exists(p_tin):
        tin = json.load(open(p_tin))
    else:
        tin = {"tieu_de": kb.get("tieu_de", ""), "link": "",
               "nguon": kb.get("nguon_tin", "bài đưa tay vào trạm"), "cac_link": []}
    # Anh chốt 08/08 (lần 2): xếp kho KHÔNG quét QC nữa — cảnh báo dấu nguồn đã dồn về hộp
    # KIỂM QC TRƯỚC DỰNG trên trạm (anh pass rồi mới dựng được), tài nguyên nào cũng đã qua
    # cổng VÀO từ lúc gắp. Nút Kho giờ chỉ còn: SEO (một lần mỗi bài) + chép tệp lên Drive.
    # VIDEO PHẢI TOÀN VẸN mới được vào kho (anh dính 09/08: bấm Kho đúng lúc xưởng đang
    # dựng lại → chép file GHI DỞ 7,9MB thiếu moov, QuickTime không mở nổi). Ba phòng tuyến:
    # ① xưởng đang chạy → chặn TRƯỚC khi tạo hộp (không đẻ hộp rác); ② ffprobe đọc được
    # bản nguồn; ③ chép xong ffprobe lại bản TRONG HỘP — Drive chép lỗi cũng bắt được.
    p_video = os.path.join(viec, "video.mp4")
    if subprocess.run(["pgrep", "-f", "xuong.py"], capture_output=True).returncode == 0:
        raise SystemExit("DỪNG — xưởng ĐANG DỰNG video. Chờ dựng xong rồi bấm Kho lại.")

    def _prob(f):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", f], capture_output=True, text=True, timeout=60)
        try:
            return float(r.stdout.strip())
        except ValueError:
            return 0.0

    dai_goc = _prob(p_video)
    if dai_goc < 3.0:
        raise SystemExit("DỪNG — video.mp4 dở dang hoặc hỏng (ffprobe không đọc được). "
                         "Dựng lại video rồi bấm Kho.")

    ngay = datetime.now().strftime("%Y-%m-%d")
    hop = KHO_PY.tao(ngay, slug_hoa(kb["tieu_de"]), kb["tieu_de"])

    # Anh chốt 08/08: hộp KHÔNG chứa qc.png + thumbnail.jpg nữa — anh không dùng đến.
    # Cổng QC vẫn CHẠY như thường (ảnh chứng cứ nằm lại thư mục việc trên DATA).
    shutil.copy2(p_video, os.path.join(hop, "video.mp4"))
    if abs(_prob(os.path.join(hop, "video.mp4")) - dai_goc) > 0.5:
        raise SystemExit("DỪNG — bản video CHÉP VÀO HỘP đọc không lành (Drive chép lỗi?). "
                         "Bấm Kho lại lần nữa.")
    shutil.copy2(os.path.join(viec, "giong.mp3"), os.path.join(hop, "giong.mp3"))

    # ẢNH BÌA (anh đặt 18/08: "trong thư mục đóng gói chưa có thumbnail"). Dựng ngay
    # lúc đóng gói vì đây là chỗ mọi thứ đã chốt: tiêu đề cuối, cụm tô vàng cuối, ảnh
    # đã duyệt. Dựng sớm hơn thì tiêu đề còn đổi, bìa lệch với video.
    # Bìa hỏng KHÔNG được làm hỏng cả hộp — thiếu bìa thì anh tự làm được, còn hộp
    # thiếu video thì mất cả buổi.
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import lam_thumbnail as TN
        # `lam` trả thêm ĐIỂM CHẤM và danh sách phương án (18/08) — nhận bằng *_ để
        # lần sau nó trả thêm gì nữa thì chỗ này cũng không gãy.
        p_bia, kieu_bia, _n, _diem, *_ = TN.lam(viec, os.path.join(hop, "thumbnail.jpg"))
        print(f"  🖼  ảnh bìa: bố cục {kieu_bia} · {_diem:.0f}/100 điểm "
              f"→ {os.path.basename(p_bia)}")
    except Exception as e:
        print(f"  ⚠ chưa dựng được ảnh bìa: {e}")

    open(os.path.join(hop, "loi-binh.txt"), "w", encoding="utf-8").write(
        kb["tieu_de"] + "\n\n" + kb["loi_binh"] + "\n")
    # TÊN FILE mang theo tên video (anh đặt 14/08): hộp nào cũng một file "goi-dang.txt"
    # thì mở vài bài cùng lúc là lẫn tab, không biết cái nào của bài nào.
    ten_gd = f"goi-dang_{slug_hoa(kb['tieu_de'])[:60]}.txt"
    open(os.path.join(hop, ten_gd), "w", encoding="utf-8").write(goi_dang(kb, tin, viec))

    # Sổ nguồn: ưu tiên sổ của TRẠM DUYỆT TÀI NGUYÊN (`so-nguon.jsonl`) — sổ đó chỉ ghi ảnh
    # THẬT SỰ vào video và đã qua mắt người, còn `nguon-anh.json` là sổ GOM (ghi cả ảnh gom về
    # rồi bỏ không dùng). Video nào chưa qua trạm thì rơi về sổ gom như cũ.
    so = os.path.join(viec, "anh", "so-nguon.jsonl")
    ng = os.path.join(viec, "anh", "nguon-anh.json")
    if os.path.exists(so):
        ds_anh = [json.loads(l) for l in open(so, encoding="utf-8")]
    else:
        nguon = json.load(open(ng)) if os.path.exists(ng) else {}
        ds_anh = nguon.get("anh", [])
    json.dump({"anh": ds_anh, "video": [], "nhac": ["Mixkit — giấy phép miễn phí"],
               "bai_goc": kb.get("bai_da_doc") or kb.get("nguon_tin"),
               "ghi_chu": "ảnh báo chí — CHƯA xin phép, dùng dạng trích dẫn tin tức"},
              open(os.path.join(hop, "nguon.json"), "w"), ensure_ascii=False, indent=1)

    du = KHO_PY.kiem_hop(hop)
    print(f"{'✅' if du else '❌'} {hop}")
    # Bài xong → ảnh của nó vào KHO CHỦ THỂ dùng chung (anh chốt 10/08): chạy NỀN
    # detach — nút Kho phải nhanh (anh chốt 08/08), gắn nhãn mắt máy chạy sau vài phút.
    try:
        subprocess.Popen([sys.executable,
                          os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "nhap_kho_chu_the.py"), viec],
                         stdout=open(os.path.join(viec, "nhap-kho-chu-the.log"), "w"),
                         stderr=subprocess.STDOUT, start_new_session=True)
        print("  🏠 đang nhập ảnh bài này vào kho chủ thể (chạy nền)")
    except Exception as e:
        print(f"  ⚠ không khởi động được nhập kho chủ thể ({e})")
    # ĐOẠN CLIP anh cắt tay cũng phải về kho — luật "cảnh chính có gì cảnh phụ có nấy"
    # áp cho TÀI NGUYÊN: ảnh có đường về kho từ 10/08, còn đoạn video thì không, nên
    # anh cắt cả tuần mà kho-nha-duyet vẫn trống trơn (anh bắt 14/08). Chạy nền như ảnh.
    # Từ 16/08 lượt này gánh CẢ VIDEO GỐC trong `clip/tay/` (anh chốt: "làm xong content
    # có dùng video gốc thì tự đẩy vào kho chung") — cùng một tiến trình, không đẻ thêm.
    try:
        subprocess.Popen([sys.executable,
                          os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "nhap_kho_video.py"), "--doan-bai", viec],
                         stdout=open(os.path.join(viec, "nhap-kho-video.log"), "w"),
                         stderr=subprocess.STDOUT, start_new_session=True)
        print("  🎬 đang nhập VIDEO GỐC + đoạn clip của bài vào kho video (chạy nền)")
    except Exception as e:
        print(f"  ⚠ không khởi động được nhập kho video ({e})")
    # CỜ ĐÃ XẾP KHO (11/08): trạm dựa vào cờ này để nhắc "bài dựng xong >1 ngày chưa
    # xếp kho" — không xếp thì ảnh tốt của bài không vào kho chung, công tìm mất trắng.
    try:
        kb_c = json.load(open(os.path.join(viec, "kich-ban.json"), encoding="utf-8"))
        KB.ghi_gop(viec, {"da_xep_kho": datetime.now().strftime("%Y-%m-%d %H:%M")})
    except Exception as e:
        print(f"  ⚠ không ghi được cờ đã-xếp-kho: {e}")
    return hop


if __name__ == "__main__":
    # --seo <việc>: CHỈ sinh SEO rồi thoát. Xưởng bắn đường này chạy NỀN ngay sau khi
    # dựng xong, để lúc anh bấm Kho thì thẻ + bình luận ghim đã nằm sẵn trong kịch bản.
    if "--seo" in sys.argv:
        v = DD.tim_viec(sys.argv[sys.argv.index("--seo") + 1])
        _bo_sung_seo(v, json.load(open(os.path.join(v, "kich-ban.json"),
                                       encoding="utf-8")))
    else:
        for v in sys.argv[1:]:
            xep(DD.tim_viec(v))
