#!/usr/bin/env python3
"""CHUYỂN ĐỘNG ẢNH — học từ kênh Nhím Bóng Đá (anh chốt 04/08/2026).

  ① ZOOM IN    — ảnh đứng yên tại chỗ, phóng to dần. KHÔNG trượt ngang.
  ② CHẠY NGANG — ảnh trượt từ trái sang phải, KHÔNG phóng to.
  ③ CHẠY DỌC   — ảnh ĐỨNG trượt từ DƯỚI LÊN, tốc độ y như chạy ngang. Học từ Nhím Bóng Đá
                 (anh chỉ 05/08). Ảnh dọc crop vào khung 1080×1248 thì dư ~546px chiều cao —
                 đúng chỗ để trượt. Đi từ dưới lên nên KẾT ở phần trên: với ảnh chân dung
                 cầu thủ, đó là kết ở khuôn mặt.
  ④ VỪA KHUNG  — thu cả tấm cho lọt bề ngang, nền mờ (ảnh quá ngang: bảng tỷ số…).
  ⑤ TRƯỢT ĐỌC  — phóng cho chữ to nhất rồi trượt hết bề ngang (bảng cần ĐỌC được).

Không bao giờ trộn hai kiểu trong cùng một cảnh — vừa zoom vừa trượt là dấu hiệu của người
dựng non tay, mắt người xem không biết bám vào đâu.

**CHỌN KIỂU THEO HÌNH DÁNG ẢNH — anh chốt 05/08/2026, thay cho bốc ngẫu nhiên:**
  · ảnh NGANG (rộng ≥ cao) → CHẠY NGANG
  · ảnh ĐỨNG  (cao > rộng) → ZOOM IN **hoặc CHẠY DỌC** (chia đôi, xem `can_bang_kieu`)
Không chỉ là quy ước cho đều tay, mà đúng cả về kỹ thuật: khung của kênh là khối 1080×1248,
nên ảnh DỌC crop vào đó gần như không dư bề ngang — bắt nó trượt thì hoặc trượt được vài
chục pixel (nhìn như đứng yên), hoặc phải phóng to quá tay làm vỡ ảnh. Ảnh NGANG thì dư
nhiều bề ngang, trượt mới có chỗ mà trượt.

Cả hai đều render bằng PIL với toạ độ SỐ THỰC. Đây là điều kiện bắt buộc: bộ lọc zoompan
của ffmpeg làm tròn toạ độ về pixel nguyên nên ảnh nhảy từng bước, nhìn ra rung chứ không
ra chuyển động (đo được: độ giật 8,874 so với 0,051 khi dùng PIL).
"""
import os
import random
import subprocess
import tempfile
from PIL import Image, ImageFilter

ZOOM_MAX = 1.12          # phóng tối đa 12% — anh chốt trần 15%

# TỐC ĐỘ TRƯỢT NGANG — đo trực tiếp từ video Nhím Bóng Đá (04/08/2026):
# bốn đoạn trượt dài 2,6s đến 30,3s, tốc độ 8,8% – 14,4%, TRUNG BÌNH 11,3% bề ngang khung
# mỗi giây. Đặt theo % khung/GIÂY chứ không theo % quãng đường — nếu tính theo quãng đường
# thì cảnh ngắn sẽ trượt nhanh gấp đôi cảnh dài, và người xem thấy chóng mặt (lỗi bản đầu:
# đo được 20,5%/giây, gần gấp đôi Nhím, anh nhận ra ngay khi xem).
PAN_TOC_DO = 0.10        # anh chốt: 10% bề ngang khung mỗi giây (Nhím 11,3%)

# Bù hàm làm mượt: chuyển động vào chậm - giữa nhanh - ra chậm, nên tốc độ ở GIỮA cảnh
# cao hơn tốc độ trung bình khoảng 19% (đo thực: đặt 0,11 thì máy đo ra 13,1%).
# Chia hệ số này để con số ĐO ĐƯỢC đúng bằng PAN_TOC_DO anh đặt.
BU_LAM_MUOT = 1.19


# Ảnh QUÁ NGANG (bảng tỷ số, ảnh ghép, băng-rôn) — anh nêu 05/08: lấy về mà xưởng "không
# biên tập được". Đúng: xưởng luôn CẮT ảnh vào khối 1080×1248, nên ảnh tỉ lệ 2,5 thì chỉ còn
# 35% bề ngang ở giữa — với ảnh người thì vẫn giữ được mặt, nhưng với BẢNG CHỮ thì mất chữ
# là hỏng hẳn. Trên ngưỡng này thì đổi cách: thu VỪA BỀ NGANG, không cắt tí nào, phần trên
# dưới lấp bằng nền mờ của chính ảnh đó.
TY_LE_VUA_KHUNG = 2.0

# ẢNH NHỎ — anh chỉ 05/08: banner trận đấu, ảnh đồ hoạ, ảnh chụp lại từ mạng thường vừa NGANG
# vừa BÉ (kiểu 460×259). Crop vào khối 1080×1248 thì phải phóng gần NĂM LẦN — vỡ nát, mà lại
# mất hai bên nên không thấy hết vật thể. Anh chốt: những tấm này để NGUYÊN cỡ nhỏ, đặt giữa,
# nền mờ phủ trên dưới — thà ảnh nhỏ mà nét và thấy đủ, còn hơn to mà vỡ và cụt.
# HAI ngưỡng khác nhau, đừng gộp làm một (bài học 05/08: gộp thì 11/20 cảnh thành "vừa
# khung", cả ảnh báo chí tử tế cũng bị thu nhỏ, video nhìn như dán tem):
#   · PHONG_QUA_TAY — trên mức này thì ĐỔI SANG vừa khung. Ảnh báo 1020×680 chỉ cần phóng
#     1,84 lần, vẫn nét, cứ cắt bình thường. Banner 460×259 cần 4,8 lần — cái đó mới phải đổi.
#   · PHONG_TOI_DA  — khi ĐÃ vừa khung thì không phóng quá mức này, để ảnh còn nét.
# Ngưỡng tính theo KHỐI ẢNH THẬT: 1080×1459 (76% chiều cao khung — sổ dự án ghi nhầm 65%,
# phát hiện 05/08 khi số cảnh "vừa khung" nhiều bất thường). Với khối cao 1459 thì ảnh HD
# 1280×720 cần phóng 2,03 lần — vẫn xem được trên điện thoại, đừng vội thu nhỏ nó.
# Chỉ ảnh dưới 720p thật (990×568 → 2,57 lần) mới đáng đổi sang vừa khung.
PHONG_QUA_TAY = 2.30
PHONG_TOI_DA = 1.30
# Trần phóng RIÊNG cho cảnh "vừa khung" (anh bắt 09/08 tối: ảnh lịch thi đấu 399×501
# chọn vừa khung mà lên video vẫn là tem nhỏ giữa khung — cap 1.30 chặn nó ở 519px).
# Vừa khung dùng cho ĐỒ HOẠ/bảng/băng-rôn: màu phẳng, phóng 2-3 lần vẫn xem tốt trên
# điện thoại — ưu tiên ĐẦY KHUNG. 3.5 là phanh chống nát cho ảnh quá bé (dưới ~310px).
PHONG_VUA_KHUNG = 3.5


def _nen_mo(im, W, H, mo=34, toi=0.78):
    nen = im.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(mo))
    return Image.eval(nen, lambda v: int(v * toi))


TRAN_MOT_KIEU = 0.65     # anh chốt 05/08: một kiểu không được chiếm quá 65% số cảnh

# HƯỚNG chuyển động — anh chốt 05/08: "tự cân đối theo tài nguyên từng video, tránh dập khuôn
# cứng nhắc lặp lại khiến nền tảng đánh giá là máy".
# Đây không phải chuyện thẩm mỹ vặt: video nào cũng zoom-vào-từ-tâm rồi trượt-trái-sang-phải,
# lặp qua hàng trăm video, là một dấu vân tay quá dễ nhận. Người dựng thật không ai làm y hệt
# nhau hai lần.
HUONG_NGANG = ("trai_phai", "phai_trai", "cheo_xuong", "cheo_len")
# Chạy dọc chỉ có MỘT chiều: dưới lên. Đây là cách Nhím làm, và nó có lý — ảnh chân dung thì
# kết ở khuôn mặt mới đúng nhịp kể; đi ngược lại là bỏ mặt người ra khỏi khung ở cuối cảnh.
HUONG_ZOOM = ("vao", "ra")
# Tâm zoom lệch nhẹ khỏi chính giữa — zoom vào đúng tâm mọi lần cũng là một kiểu dập khuôn.
LECH_TAM = 0.16


def la_do_hoa_bang(im):
    """Ảnh ĐỒ HOẠ (bảng xếp hạng, tỷ số, card chữ, đồ hoạ AI) — phải hiện VỪA KHUNG trọn
    vẹn, zoom/cắt là mất chữ mất cột (anh bắt 08/08 ở cảnh BXH, rồi ảnh AI 4 cúp bị cắt).

    Hai cửa, đo thật trên kho việc 08/08:
      ① MÀU DỒN: đồ hoạ nền phẳng dồn về vài màu — BXH top-8 màu chiếm 92–99%, ảnh chụp
        trận chỉ 28–66% → ngưỡng 80% biên rộng.
      ② CẠNH SẮC (cho đồ hoạ AI nền gradient/ảnh lồng, màu chỉ dồn 71–79% nên trượt cửa ①):
        chữ với viền đồ hoạ tạo cạnh gắt dày đặc — đo được 8,6–15,6% điểm ảnh, trong khi
        ảnh chụp nét mềm chỉ 1,3–5,7% → màu dồn ≥65% VÀ cạnh sắc ≥7% cũng tính là đồ hoạ.
        Cần CẢ hai vế: ảnh khán đài đông người cạnh sắc tới 11% nhưng màu chỉ dồn 28%.
      ③ ĐỒ HOẠ LAI ẢNH THẬT (nửa khung là ảnh cầu thủ nên màu chỉ dồn 55–65% — ca n31 4 cúp
        + cầu thủ, anh bắt lần hai 08/08): màu ≥55% VÀ cạnh sắc ≥10% (chữ phải THẬT dày mới
        dám nhận ở vùng màu loãng này). Screenshot bài báo cũng lọt cửa này — chủ đích:
        loại đó zoom là mất tít, vừa khung mới đúng."""
    from collections import Counter
    nho = im.convert("RGB").resize((160, 100))
    d = Counter((r // 32, g // 32, b // 32) for r, g, b in nho.getdata())
    n = 160 * 100
    mau = sum(c for _, c in d.most_common(8)) / n
    if mau >= 0.80:
        return True
    if mau < 0.55:
        return False
    import numpy as np
    g = np.asarray(im.convert("L").resize((320, max(int(320 * im.height / im.width), 4))),
                   dtype=np.int16)
    sac = ((np.abs(g[1:-1, 2:] - g[1:-1, :-2])
            + np.abs(g[2:, 1:-1] - g[:-2, 1:-1])) > 120).mean()
    return sac >= (0.07 if mau >= 0.65 else 0.10)


def chon_kieu(w, h, W=1080, anh_cao=1248):
    """Kiểu mặc định theo hình dáng VÀ cỡ ảnh (anh chốt 05/08)."""
    ty = w / max(h, 1)
    if ty >= TY_LE_VUA_KHUNG:
        return "vua"                                 # quá ngang: cắt là mất chữ
    # Phải phóng bao nhiêu lần mới lấp kín khối ảnh? Quá PHONG_TOI_DA là sẽ vỡ → đừng cắt,
    # để nguyên cỡ nhỏ trên nền mờ. Đây là chỗ bắt ảnh banner/đồ hoạ nhỏ mà tỉ lệ chưa tới 2,0.
    if max(W / max(w, 1), anh_cao / max(h, 1)) > PHONG_QUA_TAY:
        return "vua"
    return "ngang" if ty >= 1.0 else "zoom"


def rai_huong(ds_kieu, seed=None):
    """Rải HƯỚNG cho từng cảnh: không lặp liền kề, và dùng đều các hướng trong một video.

    Hai luật, theo thứ tự:
      ① hai cảnh liền nhau KHÔNG cùng hướng — chỗ dễ lộ nhất là hai cú trượt cùng chiều nối
        đuôi nhau, mắt bắt ra ngay là máy rải;
      ② trong cùng một video, hướng nào dùng ít thì ưu tiên — để không có video nào "toàn
        trượt trái sang phải".
    `seed` gắn với thư mục việc nên mỗi video ra một cách rải khác, mà chạy lại vẫn y như cũ
    (dựng lại lần hai không nhảy lung tung).
    """
    rnd = random.Random(seed)
    dem = {h: 0 for h in HUONG_NGANG + HUONG_ZOOM}
    ra, truoc = [], None
    for k in ds_kieu:
        if k == "dungdoc":
            ra.append("duoi_len")                    # chạy dọc chỉ có một chiều
            truoc = "duoi_len"
            continue
        if k not in ("ngang", "zoom"):
            ra.append(None)                          # "vừa khung"/"trượt đọc"/clip: không có hướng
            truoc = None
            continue
        chon = list(HUONG_NGANG if k == "ngang" else HUONG_ZOOM)
        con = [h for h in chon if h != truoc] or chon
        it_nhat = min(dem[h] for h in con)
        con = [h for h in con if dem[h] == it_nhat]
        h = rnd.choice(con)
        dem[h] += 1
        ra.append(h)
        truoc = h
    return ra


def can_bang_kieu(ds_kieu, ds_ty, tran=TRAN_MOT_KIEU):
    """Kéo tỉ lệ ngang/zoom của CẢ VIDEO về không quá 65/35 (anh chốt 05/08).

    Vì sao cần: chọn kiểu theo hình dáng từng ảnh là đúng cho từng cảnh, nhưng gom cả video
    lại thì hỏng — kho ảnh bóng đá gần như toàn ảnh ngang, nên cả video chạy ngang 100%,
    nhìn một lúc là đơn điệu, mắt người xem đoán trước được nhịp.

    Đổi cảnh nào cho ít hại nhất:
      · thừa NGANG → đổi sang zoom mấy tấm GẦN VUÔNG nhất (tỉ lệ thấp nhất) — chúng dư bề
        ngang ít nhất nên trượt vốn đã không đẹp; tấm càng ngang càng giữ lại để trượt.
      · thừa ZOOM  → đổi sang ngang mấy tấm ÍT DỌC nhất (tỉ lệ cao nhất) — dọc quá thì
        phóng to mới có chỗ trượt, dễ vỡ ảnh.
    Không đụng vào cảnh kiểu "vua"/"doc" (ảnh bảng biểu) và cảnh NGƯỜI đã tự chỉ định.
    """
    doi_duoc = [i for i, k in enumerate(ds_kieu) if k in ("ngang", "zoom")]
    if len(doi_duoc) < 3:
        return ds_kieu, ""
    ra = list(ds_kieu)
    for nhieu, it in (("ngang", "zoom"), ("zoom", "ngang")):
        co = [i for i in doi_duoc if ra[i] == nhieu]
        if len(co) <= round(len(doi_duoc) * tran):
            continue
        can_doi = len(co) - int(len(doi_duoc) * tran)
        # ngang thừa → đổi tấm gần vuông nhất trước; zoom thừa → đổi tấm ít dọc nhất trước
        thu_tu = sorted(co, key=lambda i: ds_ty[i], reverse=(nhieu == "zoom"))
        for i in thu_tu[:can_doi]:
            ra[i] = it
        n = sum(1 for i in doi_duoc if ra[i] == "ngang")
        ra, them = _chia_anh_doc(ra, ds_ty)
        return ra, (f"cân lại {can_doi} cảnh cho khỏi lệch một kiểu "
                    f"({n} ngang / {len(doi_duoc) - n} zoom){them}")
    ra, them = _chia_anh_doc(ra, ds_ty)
    return ra, (f"chia ảnh dọc{them}" if them else "")


def _chia_anh_doc(ds_kieu, ds_ty):
    """Trong nhóm ảnh ĐỨNG, chia đôi: một nửa zoom, một nửa CHẠY DỌC (dưới lên).

    Ảnh dọc mà cảnh nào cũng zoom thì cũng là một kiểu dập khuôn — mà ảnh dọc lại có sẵn chỗ
    trượt theo chiều cao. Ưu tiên cho chạy dọc những tấm DỌC NHẤT (tỉ lệ thấp nhất), vì càng
    dọc thì phần dư chiều cao càng nhiều, trượt càng có chỗ.
    """
    doc = [i for i, k in enumerate(ds_kieu) if k == "zoom" and ds_ty[i] < 1.0]
    if len(doc) < 2:
        return ds_kieu, ""
    ra = list(ds_kieu)
    for i in sorted(doc, key=lambda i: ds_ty[i])[:len(doc) // 2]:
        ra[i] = "dungdoc"
    n = sum(1 for k in ra if k == "dungdoc")
    return ra, f" · {n} cảnh ảnh dọc cho chạy dọc dưới lên"


def _render_vua_khung(im, out, W, H, anh_cao, anh_top, dur, fps, n, ne_the=None):
    """VỪA KHUNG — thu cả tấm cho lọt bề ngang, không cắt mất gì, nền là bản mờ của chính nó.

    Dùng cho bảng tỷ số, bảng xếp hạng, ảnh ghép, băng-rôn — thứ mà nội dung nằm TRẢI RỘNG
    chứ không tụ ở giữa. Chuyển động chỉ zoom RẤT nhẹ (4%), vì chữ mà trượt ngang thì người
    xem chưa đọc xong đã trôi mất.

    ne_the=(y0, y1): cảnh này có THẺ SỐ LIỆU chồng lên dải y0–y1. Anh dặn 08/08: thẻ che
    mất mấy dòng chữ cuối của đồ hoạ trong khi phía trên khung còn trống — nếu đáy ảnh thò
    vào dải thẻ thì ĐẨY ảnh lên vừa đủ để thoát, nhưng không bao giờ đẩy sát quá trần
    (chừa lề 30px); không thò thì giữ nguyên, không đổi bố cục vô cớ.
    """
    nen = _nen_mo(im, W, H)
    r = W / im.width
    cao = int(im.height * r)
    if cao > anh_cao:                                # quá cao thì thu theo chiều cao
        r = anh_cao / im.height
        cao = anh_cao
    # Trần phóng NỚI cho vừa khung (anh chỉnh 09/08, đè chốt 05/08 cho riêng kiểu này):
    # người đã chọn "vừa khung" là muốn thấy TRỌN và TO — ảnh nhỏ cũng phóng cho đầy
    # bề ngang; chỉ phanh ở PHONG_VUA_KHUNG chống nát ảnh quá bé.
    if r > PHONG_VUA_KHUNG:
        r = PHONG_VUA_KHUNG
        cao = int(im.height * r)
        print(f"    ⚠ vừa khung: ảnh quá bé ({im.width}×{im.height}), phóng kịch "
              f"{PHONG_VUA_KHUNG}× vẫn chưa đầy bề ngang")
    rong = int(im.width * r)
    goc = im.resize((max(rong, 2), max(cao, 2)), Image.LANCZOS)

    day = 0
    if ne_the:
        cao_max = int(cao * 1.04)                    # cỡ TO NHẤT trong cảnh (cuối cú zoom 4%)
        dinh = anh_top + (anh_cao - cao_max) // 2
        tho = dinh + cao_max - (ne_the[0] - 12)      # đáy ảnh thò vào thẻ bao nhiêu (+12 lề)
        if tho > 0:
            day = min(tho, max(dinh - 30, 0))        # đẩy vừa đủ thoát, kịch trần thì thôi
            if day < tho:
                print(f"    ⚠ thẻ che {tho}px, chỉ đẩy được {day}px (ảnh đã gần chạm trần)")

    p = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for k in range(n):
        t = k / (n - 1) if n > 1 else 0
        e = t * t * (3 - 2 * t)
        z = 1.0 + 0.04 * e                           # nhúc nhích cho đỡ chết cứng, đủ để đọc
        w2, h2 = max(int(rong * z), 2), max(int(cao * z), 2)
        fg = goc.resize((w2, h2), Image.BICUBIC)
        fr = nen.copy()
        fr.paste(fg, ((W - w2) // 2, anh_top + (anh_cao - h2) // 2 - day))
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    return "vua"


def _render_truot_doc(im, out, W, H, anh_cao, anh_top, dur, fps, n):
    """TRƯỢT ĐỌC — phóng ảnh cho CAO bằng khung (chữ to nhất có thể) rồi trượt ngang hết bề
    ngang trong đúng thời lượng cảnh. Dùng cho bảng tỷ số / bảng xếp hạng khi anh muốn ĐỌC
    được chữ; đổi lại phải cho cảnh đủ dài, chữ trôi nhanh thì đọc không kịp."""
    nen = _nen_mo(im, W, H)
    r = anh_cao / im.height
    goc = im.resize((max(int(im.width * r), 2), anh_cao), Image.LANCZOS)
    du = max(goc.width - W, 0)
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for k in range(n):
        t = k / (n - 1) if n > 1 else 0
        e = t * t * (3 - 2 * t)
        x = int(du * e)
        fr = nen.copy()
        fr.paste(goc.crop((x, 0, x + W, anh_cao)), (0, anh_top))
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    return "đọc"


# ── né watermark khi dựng (anh chốt 07/08) ───────────────────────────────────
# Anh đã xác nhận "vẫn dùng" một tấm dính dấu nguồn thì khâu dựng phải TỰ né: đọc vùng
# logo từ nhãn OCR (7 vùng của lay_anh), rồi ép khung cắt + hướng chạy sao cho vùng đó
# KHÔNG BAO GIỜ lọt vào khung hình. Trước đây cảnh báo xong vẫn dựng nguyên — anh phải
# cho render lại bằng tay.
VUNG_TEN = ("góc trên trái", "góc trên phải", "góc dưới trái", "góc dưới phải",
            "dải trên", "dải dưới", "giữa khung")
# logo chiếm cỡ này ở mép ảnh là phổ biến — né rộng tay một chút cho chắc
NE_NGANG, NE_DOC = 0.22, 0.16


def doc_vung_tranh(chu):
    """Rút tên vùng từ chuỗi nhãn kiểu 'góc trên phải: "nike" · dải dưới: "@abc"'."""
    return [v for v in VUNG_TEN if v in (chu or "")]


def _gioi_han_tranh(vungs, iw, ih, cw, ch):
    """Khoảng cho phép của GỐC khung cắt (x0, y0) để mọi vùng cần né nằm ngoài khung.

    Trả (x_lo, x_hi, y_lo, y_hi) hoặc None nếu không né nổi (logo giữa khung, hoặc
    khung cắt to gần bằng ảnh). Mỗi góc chỉ cần né theo MỘT trục — chọn trục còn dư."""
    mw, mh = iw * NE_NGANG, ih * NE_DOC
    x_lo, x_hi, y_lo, y_hi = 0.0, max(iw - cw, 0.0), 0.0, max(ih - ch, 0.0)
    for v in vungs:
        if v == "giữa khung":
            return None
        if v in ("dải trên", "dải dưới"):
            if ih - ch < mh:
                return None
            if v == "dải trên":
                y_lo = max(y_lo, mh)
            else:
                y_hi = min(y_hi, ih - ch - mh)
            continue
        trai = "trái" in v
        tren = "trên" in v
        du_x, du_y = iw - cw, ih - ch
        if du_x >= mw:                               # né theo bề ngang được
            if trai:
                x_lo = max(x_lo, mw)
            else:
                x_hi = min(x_hi, iw - cw - mw)
        elif du_y >= mh:                             # hết cửa ngang thì né theo bề dọc
            if tren:
                y_lo = max(y_lo, mh)
            else:
                y_hi = min(y_hi, ih - ch - mh)
        else:
            return None
    if x_lo > x_hi + 0.5 or y_lo > y_hi + 0.5:
        return None
    return (x_lo, min(x_hi, max(iw - cw, 0.0)), y_lo, min(y_hi, max(ih - ch, 0.0)))


def _kep(v, lo, hi):
    return max(lo, min(v, hi))


def lat_vung(vs):
    """Lật danh sách TÊN VÙNG né theo trục dọc: ảnh đã lật trái-phải thì logo ở 'góc trên
    trái' nằm sang 'góc trên phải' — vùng né phải lật theo, không thì né hụt."""
    if not vs:
        return vs
    return [v.replace("trái", "\0").replace("phải", "trái").replace("\0", "phải")
            for v in vs]


def render_ghep_doc(src_tren, src_duoi, out, W, H, anh_cao, anh_top, dur, fps=30,
                    seed=None, lat=(False, False), vua=(False, False)):
    """CẢNH ĐÔI (anh đặt 09/08, theo mẫu đối đầu của kênh dẫn đầu): hai ảnh xếp DỌC chia
    đôi khối ảnh — đội A trên, đội B dưới, mỗi nửa cover kín, zoom nhẹ NGƯỢC CHIỀU nhau
    cho sống động. lat = (lật ảnh trên?, lật ảnh dưới?).

    vua = (nửa trên vừa khung?, nửa dưới vừa khung?) — anh bắt 10/08: BXH trong khung
    đôi bị cover cắt mất cột tên đội lẫn cột điểm. Nửa "vừa khung" hiện TRỌN ảnh
    (contain — ảnh ngang khớp bề ngang, ảnh dọc khớp bề dọc, máy tự biết), phần thiếu
    nền mờ của chính nó đắp; và ĐỨNG TĨNH — bảng số liệu đứng yên mới đọc được số,
    nửa kia vẫn zoom là đủ sống động.

    MÉP NỐI HOÀ TAN (anh nâng cấp 09/08 chiều): hai nửa CHỒNG LẤN một dải ~100px quanh
    đường nối, ảnh trên tan dần vào ảnh dưới bằng mặt nạ gradient — hết cảm giác hai tấm
    dán cạnh nhau có ranh giới cứng."""
    rnd = random.Random(seed)
    nua = anh_cao // 2
    dai_hoa = min(120, nua // 3)                     # bề dày dải hoà mép
    nua_c = nua + dai_hoa // 2                       # mỗi nửa cao thêm nửa dải để chồng lấn
    cap = []
    for src, l, v in ((src_tren, lat[0], vua[0]), (src_duoi, lat[1], vua[1])):
        im = Image.open(src).convert("RGB")
        if l:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if v:                                        # nửa VỪA KHUNG: dựng sẵn MỘT lần
            s = min(W / im.width, nua_c / im.height)
            fg = im.resize((max(int(im.width * s), 2), max(int(im.height * s), 2)),
                           Image.LANCZOS)
            tam = _nen_mo(im, W, nua_c)
            tam.paste(fg, ((W - fg.width) // 2, (nua_c - fg.height) // 2))
            cap.append(("vua", tam))
            continue
        s = max(W / im.width, nua_c / im.height) * 1.10   # dư 10% cho cú zoom nhẹ
        cap.append(("fill",
                    im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)))
    # mặt nạ cho ảnh TRÊN: đặc hoàn toàn, riêng dải cuối tan dần 255→0
    dong_mask = (b"\xff" * W) * (nua_c - dai_hoa)
    for j in range(dai_hoa):
        dong_mask += bytes([int(255 * (1 - j / max(dai_hoa - 1, 1)))]) * W
    mask_tren = Image.frombytes("L", (W, nua_c), dong_mask)
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = max(int(round(dur * fps)), 2)
    nen = Image.new("RGB", (W, H), (8, 8, 10))
    chieu = rnd.choice([1, -1])                      # nửa trên zoom vào thì nửa dưới lùi ra
    for k in range(n):
        t = k / (n - 1) if n > 1 else 0
        e = t * t * (3 - 2 * t)
        fr = nen.copy()
        o2 = []
        for idx, (loai_n, im) in enumerate(cap):
            if loai_n == "vua":                    # nửa vừa khung đứng TĨNH, chữ nét
                o2.append(im)
                continue
            z = 1.0 + 0.05 * (e if (chieu > 0) == (idx == 0) else (1 - e))
            w2, h2 = int(W * z), int(nua_c * z)
            cx, cy = im.width // 2, im.height // 2
            o2.append(im.crop((cx - w2 // 2, cy - h2 // 2, cx + w2 // 2, cy + h2 // 2))
                        .resize((W, nua_c), Image.BICUBIC))
        # dưới TRƯỚC, trên đè lên SAU với mặt nạ tan — dải giữa là hai ảnh hoà vào nhau
        fr.paste(o2[1], (0, anh_top + nua - dai_hoa // 2))
        fr.paste(o2[0], (0, anh_top), mask_tren)
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    return "ghep"


def render_canh(src, out, W, H, anh_cao, anh_top, dur, fps=30, kieu=None, seed=None,
                huong=None, tranh=None, ne_the=None, lat=False):
    """Dựng một cảnh. kieu = 'zoom' | 'ngang' | None (chọn ngẫu nhiên).
    tranh = danh sách vùng watermark cần né (xem doc_vung_tranh).
    ne_the = (y0, y1): cảnh có THẺ SỐ LIỆU chồng dải này — kiểu "vừa khung" sẽ đẩy ảnh
    lên né thẻ nếu bị che (các kiểu cover phủ kín khối, không có chỗ đẩy nên bỏ qua).
    lat = lật ảnh trái-phải (anh đặt 09/08, mặc định bật cho ảnh CHỤP ở tầng xưởng —
    né trùng lặp nội dung; vùng né watermark được lật theo TRƯỚC khi truyền vào đây)."""
    rnd = random.Random(seed)
    im = Image.open(src).convert("RGB")
    if lat:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if kieu is None:
        # GỌI THẲNG chon_kieu, đừng chép lại luật ở đây. Bản trước có hai nơi cùng quyết định
        # một việc — sửa luật "ảnh nhỏ thì đừng cắt" ở `chon_kieu` mà quên chỗ này, nên chạy
        # thử thấy y hệt bản cũ (05/08). Luật nằm MỘT chỗ, mọi nơi gọi vào đó.
        kieu = chon_kieu(im.width, im.height, W, anh_cao)
    n = max(int(round(dur * fps)), 2)

    # cảnh phải NÉ watermark thì hai kiểu hiện trọn ảnh (vừa khung / trượt dọc) là cấm —
    # chúng không cắt gì nên logo chắc chắn lên hình. Ép về zoom, kiểu duy nhất né được sâu.
    if tranh and kieu in ("vua", "doc", "dungdoc"):
        kieu = "zoom"
    if kieu == "dungdoc":
        kieu = "ngang"                               # dùng chung nhánh trượt, khác mỗi trục
        huong = "duoi_len"
    if kieu == "vua":
        return _render_vua_khung(im, out, W, H, anh_cao, anh_top, dur, fps, n, ne_the)
    if kieu == "doc":
        return _render_truot_doc(im, out, W, H, anh_cao, anh_top, dur, fps, n)

    # phóng ảnh lên đủ lớn: kiểu chạy ngang cần dư bề ngang để trượt
    s = max(W / im.width, anh_cao / im.height) * (1.55 if kieu == "ngang" else 1.25)
    if tranh:
        s *= 1.22                                    # né cần dư nhiều hơn để đẩy logo ra rìa
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    iw, ih = im.size
    nen = _nen_mo(im, W, H)

    p = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)

    base = min(iw / W, ih / anh_cao)
    # né watermark cần ĐỘ DƯ quanh khung cắt. Ảnh ngang nằm trong khối dọc thì bề dọc
    # KHÔNG có dư (khung ôm sát chiều cao) — logo ở dải trên/dưới sẽ không né nổi nếu
    # không zoom sâu thêm. zb = mức zoom bù, nâng dần tới khi đủ chỗ né.
    zb = 1.0
    if tranh:
        while zb < 1.45 and not _gioi_han_tranh(tranh, iw, ih,
                                                W * base / zb, anh_cao * base / zb):
            zb += 0.05
        if zb >= 1.45:
            print(f"    ⚠ né {tranh}: zoom tới 1.45 vẫn không đủ chỗ — né phần được")
    if huong is None:
        huong = rnd.choice(HUONG_ZOOM if kieu == "zoom" else HUONG_NGANG)
    # tâm zoom lệch nhẹ, mỗi cảnh một chỗ — zoom vào đúng giữa mọi lần cũng là dập khuôn
    fx = 0.5 + rnd.uniform(-LECH_TAM, LECH_TAM)
    fy = 0.5 + rnd.uniform(-LECH_TAM, LECH_TAM)
    for k in range(n):
        t = k / (n - 1) if n > 1 else 0
        # nới nhẹ hai đầu cho chuyển động không giật khi vào/ra cảnh
        e = t * t * (3 - 2 * t)

        if kieu == "zoom":
            z = (1.0 + (ZOOM_MAX - 1) * e) if huong == "vao" \
                else (ZOOM_MAX - (ZOOM_MAX - 1) * e)     # phóng RA: bắt đầu to, lùi dần
            z *= zb                                  # zoom bù để có chỗ né watermark
            cw, ch = W * base / z, anh_cao * base / z
            x0 = (iw - cw) * fx                      # lệch tâm nhẹ, không cứng ở chính giữa
            y0 = (ih - ch) * fy
        else:                                        # trượt, zoom cố định
            cw, ch = W * base / zb, anh_cao * base / zb
            du = max(iw - cw, 0)                     # phần ảnh dư ra hai bên
            du_y = max(ih - ch, 0)                   # phần dư trên dưới (dùng cho trượt chéo)
            # quãng trượt tính từ TỐC ĐỘ × thời lượng, không phải % phần dư
            quang = min(cw * (PAN_TOC_DO / BU_LAM_MUOT) * dur, du)
            if huong == "duoi_len":
                # CHẠY DỌC: đứng yên bề ngang, trượt từ DƯỚI lên TRÊN — cùng tốc độ với
                # chạy ngang (anh chỉ 05/08, học từ Nhím).
                x0 = du / 2
                qy = min(ch * (PAN_TOC_DO / BU_LAM_MUOT) * dur, du_y)
                y0 = (du_y + qy) / 2 - qy * e        # bắt đầu ở phần dưới, kết ở phần trên
                if tranh:
                    gh = _gioi_han_tranh(tranh, iw, ih, cw, ch)
                    if gh:
                        x0, y0 = _kep(x0, gh[0], gh[1]), _kep(y0, gh[2], gh[3])
                fg = im.resize((W, anh_cao), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
                fr = nen.copy()
                fr.paste(fg, (0, anh_top))
                p.stdin.write(fr.tobytes())
                continue
            nguoc = huong in ("phai_trai", "cheo_len")
            x0 = ((du + quang) / 2 - quang * e) if nguoc else ((du - quang) / 2 + quang * e)
            if huong in ("cheo_xuong", "cheo_len") and du_y > 8:
                qy = min(ch * (PAN_TOC_DO / BU_LAM_MUOT) * dur * 0.55, du_y)
                y0 = ((du_y + qy) / 2 - qy * e) if huong == "cheo_len" \
                    else ((du_y - qy) / 2 + qy * e)
            else:
                y0 = (ih - ch) / 2

        if tranh:
            # kẹp khung cắt vào vùng cho phép — logo không bao giờ lọt khung, kể cả
            # giữa chừng chuyển động (kẹp TỪNG KHUNG HÌNH, không phải chỉ điểm đầu/cuối)
            gh = _gioi_han_tranh(tranh, iw, ih, cw, ch)
            if gh:
                x0, y0 = _kep(x0, gh[0], gh[1]), _kep(y0, gh[2], gh[3])
        fg = im.resize((W, anh_cao), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
        fr = nen.copy()
        fr.paste(fg, (0, anh_top))
        p.stdin.write(fr.tobytes())

    p.stdin.close()
    p.wait()
    return kieu


def render_ghep_mix(tren, duoi, out, W, H, anh_cao, anh_top, dur, fps=30,
                    lat=(False, False), seed=None, vua=(False, False)):
    """CẢNH ĐÔI HỖN HỢP (anh ra luật 09/08 khuya: clip bình đẳng với ảnh trong mọi bố
    cục) — mỗi nửa là ẢNH hoặc ĐOẠN VIDEO: 1 video + 1 ảnh, 2 video đều được.

    tren/duoi: {"anh": đường ảnh} hoặc {"clip": {"tep", "tu", "khung"?}}.

    Thông số khớp HỆT bản hai-ảnh (render_ghep_doc): nửa khối, dải hoà mép gradient,
    nền 0x08080a — người xem không phân biệt được cảnh đôi loại nào với loại nào.
    Mắt biên tập: nửa ẢNH đứng TĨNH — nửa video bên cạnh đã tự chuyển động, cả hai
    cùng động là giật mắt; khung né logo của đoạn clip vẫn cắt trước khi vào nửa."""
    nua = anh_cao // 2
    dai_hoa = min(120, nua // 3)
    nua_c = (nua + dai_hoa // 2) // 2 * 2          # CHẴN 2px — yuv420 hạ cạnh lẻ làm
    # mask lệch 1px với hình là alphamerge sập (đo 09/08: 788 vs 789)
    # mặt nạ nửa TRÊN: đặc hoàn toàn, dải cuối tan dần — đúng công thức bản hai-ảnh
    dong = (b"\xff" * W) * (nua_c - dai_hoa)
    for j in range(dai_hoa):
        dong += bytes([int(255 * (1 - j / max(dai_hoa - 1, 1)))]) * W
    mask = os.path.join(tempfile.gettempdir(), f"ghep_mask_{W}x{nua_c}_{dai_hoa}.png")
    if not os.path.exists(mask):
        Image.frombytes("L", (W, nua_c), dong).save(mask)

    vao, loc = [], []
    for k, (ben, l, v) in enumerate(((tren, lat[0], vua[0]), (duoi, lat[1], vua[1]))):
        cat = ""
        kh = (ben.get("clip") or {}).get("khung")
        if kh:
            cat = (f"crop=floor(iw*{kh['w']:.4f}/2)*2:floor(ih*{kh['h']:.4f}/2)*2:"
                   f"floor(iw*{kh['x']:.4f}):floor(ih*{kh['y']:.4f}),")
        if l:
            cat += "hflip,"
        if "clip" in ben:
            vao += ["-ss", f"{float(ben['clip']['tu']):.2f}", "-t", f"{dur + 0.4:.2f}",
                    "-i", ben["clip"]["tep"]]
            # đoạn ngắn hơn cảnh thì đóng băng khung cuối — concat không được hụt frame
            dem = "tpad=stop_mode=clone:stop_duration=4,"
        else:
            vao += ["-loop", "1", "-t", f"{dur + 0.4:.2f}", "-i", ben["anh"]]
            dem = ""
        if v and "anh" in ben:
            # nửa VỪA KHUNG (anh bắt 10/08): hiện TRỌN ảnh — nền mờ chính nó + contain giữa
            loc.append(f"[{k}:v]{cat}{dem}split=2[s{k}a][s{k}b];"
                       f"[s{k}a]scale={W}:{nua_c}:force_original_aspect_ratio=increase,"
                       f"crop={W}:{nua_c},gblur=sigma=30,eq=brightness=-0.16[nn{k}];"
                       f"[s{k}b]scale={W}:{nua_c}:force_original_aspect_ratio=decrease,"
                       f"crop=trunc(iw/2)*2:trunc(ih/2)*2[fg{k}];"
                       f"[nn{k}][fg{k}]overlay=floor((W-w)/4)*2:floor((H-h)/4)*2,"
                       f"setsar=1[b{k}]")
        else:
            loc.append(f"[{k}:v]{cat}{dem}scale={W}:{nua_c}:"
                       f"force_original_aspect_ratio=increase,crop={W}:{nua_c},setsar=1[b{k}]")
    fc = (f"color=c=0x08080a:s={W}x{H}:r={fps}[bg0];" + ";".join(loc) + ";"
          f"[2:v]format=gray[mk];[b0][mk]alphamerge[b0a];"
          f"[bg0][b1]overlay=0:{anh_top + nua - dai_hoa // 2}[l1];"
          f"[l1][b0a]overlay=0:{anh_top},fps={fps},format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + vao +
                   ["-loop", "1", "-t", f"{dur + 0.4:.2f}", "-i", mask,
                    "-filter_complex", fc, "-map", "[v]", "-an", "-t", f"{dur:.3f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out],
                   check=True)
    return "ghep"


def render_clip(src, out, W, H, anh_cao, anh_top, dur, fps=30, bat_dau=None, seed=None,
                tranh=None, khung=None, du_khung=False, lat=False, ne_the=None):
    """Dựng một cảnh từ CLIP VIDEO (stock sạch hoặc footage) thay vì ảnh tĩnh.

    Anh chốt 04/08: video toàn ảnh tĩnh nhìn đơ, phải có clip xen vào. Clip đặt đúng
    khối ảnh như mọi cảnh khác (cùng bề cao, cùng vị trí) để nhịp mắt không bị giật.
    Không thêm Ken Burns — clip đã tự chuyển động, chồng thêm là rối.

    bat_dau: giây bắt đầu cắt trong clip nguồn. None thì lấy ngẫu nhiên, tránh 3 giây
    đầu (nhiều clip stock mở bằng khung tĩnh hoặc mờ dần).

    khung: {x,y,w,h} tỉ lệ 0–1 — vùng NGƯỜI TỰ CHỌN trên trạm để né logo trong hình
    (anh đặt 09/08 tối). Có khung thì cắt vùng đó trước khi dựng, cả hình chính lẫn nền
    mờ (nền lấy từ vùng sạch — không thì logo vẫn lảng vảng trong nền); và BỎ né tự
    động `tranh` — người đã tự cắt thì máy đừng cắt chồng thêm lần nữa.

    du_khung=True (anh chốt 09/08 đêm, cho CLIP TAY cắt gán vào cảnh): hiện TRỌN khung
    hình — lọt hết bề ngang, thiếu trên dưới thì nền mờ đắp — thay vì zoom-fill như cũ
    (phóng cho kín khối rồi cắt hai bên là vỡ hình, anh thử và bắt). Clip stock dọc/đủ
    khung vẫn đi đường fill cũ.

    lat=True: LẬT GƯƠNG trái-phải cả hình lẫn nền mờ — luật 09/08 khuya: clip tay mặc
    định lật (né trùng nội dung với nguồn), tắt được từng ô trên trạm.

    ne_the=(y0, y1): cảnh có THẺ SỐ LIỆU — khối clip fit đặt TRONG vùng còn lại phía
    trên thẻ, khoảng trống trên/dưới CHIA ĐỀU (anh chốt 09/08 khuya, mắt biên tập:
    hình lửng giữa thẻ và trần phải cân, không dính thẻ cũng không dính trần).
    """
    rnd = random.Random(seed)
    try:
        d = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
            capture_output=True, text=True).stdout.strip())
    except Exception:
        d = dur + 4
    if bat_dau is None:
        bat_dau = rnd.uniform(0.6, max(d - dur - 0.6, 0.8)) if d > dur + 2 else 0

    # setsar=1 là BẮT BUỘC, không phải cho đẹp: clip stock hay có tỉ lệ điểm ảnh lẻ
    # (đo được 10240:10239). Ghép chung với cảnh ảnh (1:1) thì thuộc tính luồng đổi giữa
    # chừng, ffmpeg dựng lại bộ lọc, và lớp phủ tĩnh đã hết frame nên MẤT HẲN từ đó tới
    # cuối video — mất cả tiêu đề, logo, watermark. Anh bắt được lỗi này 04/08.
    # Cảnh phải NÉ watermark: phóng thêm 26% rồi cắt LỆCH về phía ngược với logo — logo
    # bị đẩy hẳn ra ngoài khung (anh chốt 07/08; nền mờ phía sau đã gblur 30 + tối nên
    # logo trong nền không đọc được). Không né thì giữ đúng phép cũ, không đổi một li.
    cat = ""
    if khung:
        # crop chẵn 2 điểm ảnh (yuv420 kỵ số lẻ), kẹp trong khung hình
        cat = (f"crop=floor(iw*{khung['w']:.4f}/2)*2:floor(ih*{khung['h']:.4f}/2)*2:"
               f"floor(iw*{khung['x']:.4f}):floor(ih*{khung['y']:.4f}),")
        tranh = None
    if du_khung:
        tranh = None                               # fit trọn khung thì né-lệch hết nghĩa
    if lat:
        cat += "hflip,"                            # lật cả hình chính lẫn nền mờ cho khớp
    if tranh:
        vx, vy = "(iw-ow)/2", "(ih-oh)/2"
        chu = " ".join(tranh)
        if "phải" in chu:
            vx = "0"                                 # logo bên phải → cắt dính mép TRÁI
        elif "trái" in chu:
            vx = "iw-ow"
        if "trên" in chu:
            vy = "ih-oh"                             # logo phía trên → cắt dính mép DƯỚI
        elif "dưới" in chu:
            vy = "0"
        fg = (f"[0:v]scale={int(W * 1.26)}:{int(anh_cao * 1.26)}:"
              f"force_original_aspect_ratio=increase,"
              f"crop={W}:{anh_cao}:{vx}:{vy}[fg];")
    # vùng dọc khả dụng: có THẺ thì chỉ tới mép trên thẻ (chừa 12px) — clip tự đẩy lên
    # và khoảng trống trên/dưới còn lại chia đều
    vung_cao, vung_top = anh_cao, anh_top
    if ne_the and du_khung:
        vung_cao = max(ne_the[0] - 12 - anh_top, 320)
        print(f"    clip né thẻ: fit trong vùng {vung_cao}px phía trên thẻ, cân đều trên dưới")
    if du_khung:
        # FIT trọn: lọt trong vùng W×vung_cao giữ tỉ lệ, cạnh chẵn 2px cho yuv420
        fg = (f"[0:v]{cat}scale={W}:{vung_cao}:force_original_aspect_ratio=decrease,"
              f"crop=trunc(iw/2)*2:trunc(ih/2)*2[fg];")
    else:
        fg = (f"[0:v]{cat}scale={W}:{anh_cao}:force_original_aspect_ratio=increase,"
              f"crop={W}:{anh_cao}[fg];")
    # fit thì đặt GIỮA vùng (offset chẵn 2px); fill thì fg đúng cỡ khối, đặt sát mép
    vi_tri = (f"floor((W-w)/4)*2:{vung_top}+floor(({vung_cao}-h)/4)*2"
              if du_khung else f"0:{anh_top}")
    fc = (f"[0:v]{cat}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"gblur=sigma=30,eq=brightness=-0.16[bg];"
          + fg +
          f"[bg][fg]overlay={vi_tri},fps={fps},setsar=1,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{bat_dau:.2f}", "-i", src,
                    "-filter_complex", fc, "-map", "[v]", "-an", "-t", f"{dur:.3f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out], check=True)
    return "clip"


def chia_nhip_theo_anh(mocs, ban_do, tong, san=1.0, tran=6.0):
    """Cắt cảnh THEO ẢNH NGƯỜI ĐÃ GÁN, không theo đồng hồ (anh chốt 05/08).

    Vì sao đổi: cách cũ cắt 3–4 giây rồi lấy ảnh của câu nằm GIỮA cảnh. Nhưng câu của kênh
    này trung bình chỉ 2,2 giây nên mỗi cảnh nuốt gần hai câu — câu không rơi vào giữa thì
    ảnh KHÔNG BAO GIỜ lên hình. Đo trên video Việt Anh: anh chọn 17 ảnh, **7 tấm bị bỏ im
    lặng**. Anh phát hiện đúng ở câu 2.

    Trả về (canh, bi_gop, qua_dai):
      · canh    — [(bắt đầu, kết thúc)]
      · bi_gop  — chỉ số câu có ảnh nhưng cảnh ngắn dưới `san` nên phải gộp, ẢNH KHÔNG LÊN HÌNH
      · qua_dai — [(bắt đầu, kết thúc)] quãng dài quá `tran` giây mà không có ảnh mới

    Hai thứ sau KHÔNG tự chữa được, phải báo người:
      · cảnh 0,7 giây thì không thể là một cảnh — buộc phải gộp, nhưng phải nói mất ảnh nào;
      · quãng 17 giây một ảnh thì đứng hình chán — máy không bịa ra ảnh mới được, phải anh
        gán thêm. Tự ý cắt đôi cùng một tấm chỉ tạo cú nhảy hình vô nghĩa.
    """
    if not ban_do:
        return None, [], []
    bat_dau = [0.0] + list(mocs[:-1])                # giây BẮT ĐẦU của từng câu
    moc_cau_co_anh = sorted(i for i in ban_do if 0 <= i < len(bat_dau))
    diem = sorted({0.0} | {bat_dau[i] for i in moc_cau_co_anh})
    tho = []
    for k, b in enumerate(diem):
        ket = diem[k + 1] if k + 1 < len(diem) else tong
        tho.append([b, min(ket, tong)])

    # gộp cảnh QUÁ ngắn vào cảnh trước — và ghi lại ảnh nào vì thế mà không lên hình
    canh, bi_gop = [], []
    for c in tho:
        if canh and c[1] - c[0] < san:
            canh[-1][1] = c[1]
            i = next((x for x in moc_cau_co_anh if abs(bat_dau[x] - c[0]) < 0.01), None)
            if i is not None:
                bi_gop.append(i)
        else:
            canh.append(c)
    if len(canh) > 1 and canh[-1][1] - canh[-1][0] < san:
        canh[-2][1] = canh[-1][1]
        canh.pop()

    qua_dai = [(round(b, 1), round(k, 1)) for b, k in canh if k - b > tran]
    return [(round(b, 3), round(k, 3)) for b, k in canh], bi_gop, qua_dai


def chia_nhip(mocs, tong, ngan=3.0, dai=4.0, seed=None):
    """Chia timeline thành các cảnh dài 3–4 giây NGẪU NHIÊN, bám mốc câu nói.

    Nguyên tắc: nhịp cắt ngẫu nhiên trong khoảng 3–4 giây, nhưng ưu tiên cắt đúng chỗ
    kết thúc một câu — cắt giữa câu làm người xem hụt. mocs = danh sách giây kết thúc câu.
    """
    rnd = random.Random(seed)
    canh, t = [], 0.0
    while t < tong - 0.4:
        muc = rnd.uniform(ngan, dai)
        dich = t + muc
        # tìm mốc câu gần đích nhất, lệch không quá 0,9 giây thì cắt theo câu
        gan = [m for m in mocs if abs(m - dich) <= 0.9 and m > t + ngan * 0.6]
        ket = min(gan, key=lambda m: abs(m - dich)) if gan else min(dich, tong)
        ket = min(ket, tong)
        if ket - t < 1.2:                            # cảnh quá ngắn thì gộp vào cảnh trước
            if canh:
                canh[-1] = (canh[-1][0], ket)
            t = ket
            continue
        canh.append((t, ket))
        t = ket
    if canh and canh[-1][1] < tong:
        canh[-1] = (canh[-1][0], tong)
    return canh
