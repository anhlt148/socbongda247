# BRAIN — Trạm duyệt tài nguyên (Sóc Bóng Đá 247)

> Sổ tự học của trạm. **Đọc file này TRƯỚC khi sửa hoặc chạy trạm.**
> Xong việc thì **ghi lại xuống đây** cái gì đúng, cái gì lệch, anh sửa gì.
> Bài học chắc chắn → ghi thẳng vào đây. Bài học chưa chắc hoặc dính tiền/bản quyền/pháp lý
> → ghi `hoc-cho-duyet.md` cùng thư mục, chờ anh duyệt rồi mới nhập.

Dựng ngày 05/08/2026. Nền: sổ bàn giao `YouTube Brain/wiki/projects/kenh-socbongda247.md` mục 6d.

---

## 1. Trạm này giải bài toán nào

Anh loại mẻ 60 giây ngày 04/08 vì ba cớ, trạm này lo cớ thứ hai:
**tài nguyên ghép sai** (nói Việt Anh đánh đầu mà lại hiện người khác).

Gốc rễ: **máy không soi được số áo.** Số 18 áo trắng là Hai Long, Việt Anh là số 20 và trận
đó đầu quấn băng trắng. Ảnh gom tự động về 30 tấm thì đa số là người khác — không phải lọc
kém, mà vì khâu này **phải là khâu của người**. Trước đó việc chọn ảnh làm bằng cách sửa tay
danh sách trong `chon_anh.py`; muốn đổi một tấm phải mở mã nguồn.

Và ảnh **neo theo CÂU chứ không theo CẢNH** — cảnh cắt theo nhịp 3-4 giây, lời chạy theo câu,
hai thứ lệch nhau ngay từ cảnh hai.

---

## 2. Bài học đã đúc (đều là thứ đo được, không phải phỏng đoán)

1. **Chrome headless bị chặn ở đúng nơi cần đến.** Đo 04/08: `--headless --dump-dom` vào
   Google ảnh → trả về đúng một trang reCAPTCHA 6.991 byte, không có lấy một ảnh; vào Bing
   ảnh → lưới kết quả nạp sau bằng JavaScript nên bản đổ DOM chỉ có phần khung (1 `murl`, mà
   lại là quảng cáo). **Trình duyệt THẬT có cửa sổ + hồ sơ riêng thì cả hai nơi đều trả bình
   thường** (đo lại: 98 URL ảnh gốc kèm kích thước thật). Đừng phí thời gian tối ưu headless.

2. **Và tuyệt đối không giải CAPTCHA.** Gặp CAPTCHA thì `cdp.dinh_captcha()` trả về `True`,
   trạm dừng và báo người. Đây là luật, không phải giới hạn kỹ thuật.

3. **Trình duyệt thật lấy được ảnh TO HƠN hẳn.** Cùng một bài VietnamNet: `lay_anh.py` (đọc
   HTML thô) về ảnh 1020×690 — đó là bản thu nhỏ trong thẻ `<img src>`. Bóc bằng trình duyệt
   thật, đọc `srcset` chọn bản lớn nhất → 1827×1218. Khung dọc 1080 thì chênh lệch này thấy
   rõ trên màn hình. **Khi cần ảnh nét, bóc bài bằng trạm chứ đừng dựa vào bước gom tự động.**

4. **Ảnh chân dung (dọc) KHÔNG phải ảnh rác.** `lay_anh.py` chặn tỉ lệ ngoài 1,1–2,2 nên loại
   sạch ảnh dọc — mà ảnh cầu thủ đứng thì phần lớn là ảnh dọc. Ở trạm nới xuống **0,60–2,20**
   vì crop về khối gần vuông trên ảnh dọc vẫn giữ nguyên mặt; chỉ ảnh QUÁ NGANG (băng-rôn,
   ảnh bìa) mới mất chủ thể. An toàn được vì ở đây **người nhìn tận mắt trước khi chọn**, và
   tỉ lệ vẫn hiện dưới mỗi ảnh để soi.

5. **Cổng watermark không có cửa sau.** Ảnh gắp qua trạm chạy đúng cổng của `lay_anh.py`
   (`_ocr_song_khong` → dấu nguồn → cờ vàng), không nới một ly. Bài học số 3 của sổ dự án:
   "phát hiện watermark mà không chặn thì bằng không" — đã để lọt `@nhipcongtruong` vào video
   đã giao rồi.

6. **Đã vá chỗ vênh sổ nguồn** (sổ dự án mục 6b để treo): cổng QC ra đọc sổ JSONL có trường
   `file`/`ket_qua`, còn `lay_anh.py` ghi `nguon-anh.json` JSON thường → truyền `--so` là cổng
   crash. Từ nay **trạm ghi `anh/so-nguon.jsonl` đúng khuôn cổng QC**, và chỉ ghi ảnh NGƯỜI ĐÃ
   DUYỆT — nên chữ "ĐẠT" trong sổ có nghĩa thật: qua cổng watermark **và** qua mắt người.
   → `buoc3_xepkho.py` giờ truyền `--so anh/so-nguon.jsonl` được rồi.

7. **Tách câu phải khớp từng chữ với xưởng.** Trạm và `xuong.py:moc_cau` dùng chung phép
   `re.split(r"(?<=[.!?…])\s+", loi_binh)`. Lệch một câu là bản đồ ảnh lệch theo cả video.
   Sửa một bên thì **phải sửa bên kia**.

8. **Mốc giây: có file giọng thì đo, không có thì mới ước.** Có `giong.mp3` → ffprobe (chính
   xác). Chưa có → ước theo 226 tiếng/phút (nhịp thật đo trên 3 video, **không phải 265**).
   Giao diện ghi rõ đang dùng cách nào để anh biết mốc giây tin được tới đâu.

9. **`scrollIntoView` gọi vô điều kiện thì cột tự nhích.** Mỗi lần vẽ lại nó đẩy cột một chút,
   câu 1 bị cắt mất nửa trên. Chỉ kéo khi câu đang chọn thật sự nằm ngoài tầm nhìn.

10. **Ô từ khoá để TRỐNG là trạm hỏng một nửa** (anh chốt 05/08: *"khi dựng cái này em phải
    gợi ý luôn từ khoá từng cảnh cho anh"*). Bắt người nghĩ từ khoá cho 26 câu thì trạm chẳng
    đỡ được gì. → `goi_y.py`: **MỘT** lần gọi `claude -p` bằng **haiku** cho CẢ kịch bản, không
    phải mỗi câu một lần. Đo thật: 26 câu, một lượt, chất lượng đủ dùng ngay
    (câu 1 → "Việt Anh chấn thương", câu 4 → "Việt Anh Baker không chiến ↳ Baker cao 1m96").
    Đây là việc dễ — đọc câu, rút tên riêng, ghép từ khoá — dùng model cao là đốt token vô ích.
    Chạy tự động **một lần cho mỗi việc** rồi nhớ bằng cờ `goi_y_xong`, không gọi lại mỗi lần
    mở trang. Chạy tự động thì **chỉ điền ô còn trống**; anh bấm "gợi ý lại" mới ghi đè.

12. **Chỗ chậm nhất KHÔNG phải trình duyệt — là OCR.** Anh kêu "gõ tìm chờ rất lâu" (05/08).
    Bổ ra đo từng chặng: mở trang 2,4s · cuộn 2,7s · bóc 99 URL 0,0s · tải 54 ảnh 4,9s ·
    **soi watermark 1,7 giây MỘT TẤM, chạy tuần tự 47 tấm = 81 giây.** Đừng đoán, hãy bổ ra đo.
    Ba việc, làm cả ba → **40s xuống 18s**:
    · OCR song song 8 luồng (tesseract là tiến trình ngoài, Python nhả khoá — song song thật);
    · **dừng soi khi đã đủ số ảnh cần** (trước đó soi 47 tấm rồi chỉ giữ 18, phí 29 tấm);
    · tải gấp đôi số cần thay vì gấp ba, cuộn 2 lần thay vì 3.
    **Không nới một ly tiêu chuẩn cổng** — chỉ đổi cách chạy và số lượng đưa vào; ảnh chưa
    kịp soi thì bị XOÁ chứ không phải được cho qua.

13. **Màn hình đứng im = người dùng tưởng treo.** Kể cả khi đã nhanh, vẫn phải cho thấy đang
    làm tới đâu ("soi watermark 14/29"). Rẻ, mà bớt hẳn cảm giác chờ.

14. **Cờ "đang chạy" phải nhả ở MỌI lối ra.** Bản đầu, một lỗi mạng giữa chừng là `dangGap`
    kẹt `true` vĩnh viễn → từ đó bấm Tìm chỉ hiện "đang gắp ảnh, chờ lượt này xong đã" rồi
    thôi, không gọi trạm nữa. Anh tưởng "ảnh mới không về được", mà thật ra trạm chưa hề
    được gọi. Đã bọc try/catch + hạn 3 phút. **Lỗi im lặng kiểu này đắt hơn lỗi to tiếng.**

15. **Chrome không mở được cổng gỡ lỗi cho tiến trình ĐÃ chạy** — cờ phải có ngay lúc khởi
    động. Nên không thể "mở tab trong Chrome anh đang dùng" nếu Chrome đó bật lên không kèm
    cờ. Trạm dò trước các cổng 9334/9222/9223; thấy cái nào sống thì mở tab ngay trong đó.
    Muốn dùng Chrome hằng ngày thì chạy `MỞ CHROME CHO TRẠM.command` — nhớ tắt Chrome RIÊNG
    của trạm trước, nếu không nó vẫn đang giữ cổng 9334 và Chrome thường không chiếm được.

11. **Lời dặn model quyết định chất lượng từ khoá, không phải model nào.** Luật ăn tiền nhất:
    *từ khoá PHẢI có TÊN RIÊNG*. Bỏ luật này ra là model viết "cầu thủ tranh chấp bóng" —
    gõ vào Google ảnh thì ra người khác, đúng cái lỗi đã hỏng hai mẻ video. Luật thứ hai:
    câu trừu tượng (câu hỏi, lời kêu gọi bình luận) thì lấy bối cảnh chung của video, **đừng
    bịa ra cảnh không có thật**.

---

## 3. Chỗ còn hở — biết trước để khỏi vấp

- **Chưa có tầng CLIP.** Trạm mới lo ảnh. Chuẩn kênh là 70-30 ảnh-clip, mà `xuong.py` tự rải
  clip theo vị trí ngẫu nhiên chứ không theo câu. Muốn neo clip theo câu thì mở rộng `ban_do`
  thành `{câu: {loai: "anh"|"clip", tep: ...}}` — nhớ sửa cả xưởng.
- **Ảnh báo chí vẫn là vùng xám.** Sổ nguồn ghi rõ "CHƯA xin phép" cho từng tấm — đó là để
  sau này còn lần lại được, không phải là đã hợp lệ.
- **Cửa sổ Chrome của trạm hiện ra khi gắp ảnh.** Cố ý: anh nhìn thấy nó đang làm gì, và gặp
  CAPTCHA thì giải tay ngay trong cửa sổ đó rồi bấm tìm lại.
- **Hồ sơ Chrome riêng** `~/.config/socbongda247/chrome-tram`, cổng 9334 — không đụng Chrome
  hằng ngày, không đụng cổng 9222/9223 của bot CSKH.

## 4. Chưa vá (thấy khi làm trạm, để lại cho phiên sau)

- `duong_dan.py:57` ghi chú "~265 tiếng/phút" và `viet_loi_binh.py:96` nói với model
  "đọc 265 tiếng/phút" — **cả hai đều là số cũ đã bị bác bỏ**. Số tiếng gửi cho model thì
  tính đúng ở 226 (dòng 62) nên chưa hỏng video nào, nhưng hai chỗ chữ này sẽ lừa người đọc
  sau. Sửa cho thống nhất.

---

## 5. Sổ chạy — ghi mỗi lần dùng trạm

| Ngày | Việc | Kết quả | Anh sửa gì / học được gì |
|---|---|---|---|
| 05/08/2026 | Dựng trạm + chạy thử trọn dây trên `2026-08-05-thu-tram` (bản sao video Việt Anh) | 14/26 câu gán ảnh → 12 ảnh riêng → xưởng dựng lại video đọc đúng bản đồ câu | (chưa có phản hồi của anh) |

16. **Ô ảnh nhỏ thì cổng người vô dụng.** Bản đầu để ô 118px — anh phản ánh 05/08 là không
    chọn nổi. Mà cả trạm này sinh ra chỉ để người SOI ĐƯỢC SỐ ÁO (18 áo trắng là Hai Long,
    20 mới là Việt Anh). Ô nhỏ thì người ngồi đó cũng bằng không. Đã: mặc định 220px, thanh
    trượt 120–420px nhớ vào localStorage, và bấm 🔍 (hoặc Space khi đang rê chuột) mở ảnh
    **GỐC** toàn màn hình — có ← → lướt, Enter gán, Esc đóng. Cột kho cũng rộng hơn cột câu.

17. **Ảnh NGƯỜI tự đưa vào phải theo luật KHÁC ảnh máy đi lấy** (anh hỏi 05/08: ảnh tải từ
    Facebook cầu thủ thì đưa vào kiểu gì).
    · Máy đi lấy → lấy bừa, nên cổng phải VỨT bừa. Vứt là đúng.
    · Người chủ động đưa → vứt tấm anh cố tình chọn là sai. Ảnh Facebook cầu thủ hay có logo
      CLB, tên giải, khung ảnh; chặn cứng thì chẳng đưa được tấm nào.
    → Đường `nhan_tep()`: **soi đủ nhưng không vứt tấm nào**, chỉ dán nhãn 🔴 dấu nguồn ·
      🟡 chữ ở góc · ⚠ nhỏ hơn 900px. Không áp ngưỡng kích thước/tỉ lệ cứng như hai đường kia.
    **Nhưng cổng vẫn phải kín ở ĐẦU RA**, nếu không là lặp lại đúng bài học số 3. Nên chốt
    chặn dời sang lúc DUYỆT: tấm 🔴 đang gán vào câu nào thì trạm liệt kê ra, hỏi lại, và chỉ
    đi tiếp khi anh xác nhận — sổ nguồn ghi `bo_qua_dau_nguon: true` cùng chữ OCR đọc được,
    để sau còn lần lại được ai bỏ qua cái gì. Đã thử ngược bằng ảnh dán sẵn "@nhipcongtruong":
    trạm chặn đúng ở lần bấm đầu, và ghi đúng sổ ở lần xác nhận.

18. **"Báo về ở đâu" là câu hỏi thật, không phải chi tiết nhỏ.** Anh bấm dựng, video xong lúc
    01:24, anh hỏi lúc 01:30 vì **không hề biết nó đã xong** — trạm chỉ báo bằng một dòng chữ
    ở góc tự tắt sau 4 giây. Việc chạy 2 phút mà báo chớp nhoáng thì bằng không.
    Và anh **tưởng nó báo vào phiên chat Claude** — không được: trạm là tiến trình web độc lập,
    không có cổng nào nhắn vào phiên đang mở (y như bot Telegram, sổ dự án mục 3).
    → Ba nơi báo, đủ cho cả lúc anh ngồi trước máy lẫn lúc đi chỗ khác:
    · **ô trạng thái video nằm thường trực trên thanh đầu** (`05/08 01:24 · 12.3 MB`, và cảnh
      báo màu vàng nếu video CŨ HƠN bản duyệt — nghĩa là cần dựng lại);
    · **thông báo xong không tự tắt**, phải bấm Đóng;
    · **nhắn nhóm Telegram + thông báo góc màn hình Mac** khi xưởng dựng xong hoặc hỏng.

19. **Hai nút cạnh nhau mà phải nhớ thứ tự là lỗi thiết kế.** Anh hỏi 05/08: "có nút Dựng rồi
    thì nút Duyệt, nút Lưu nháp có ý nghĩa gì?" — câu hỏi đúng.
    · "Lưu nháp" THỪA thật: trạm tự lưu sau mỗi thao tác chưa đầy một giây. Đã bỏ, thay bằng
      dòng "✓ đã lưu HH:MM" cho thấy nó có lưu.
    · "DUYỆT" KHÔNG thừa (nó sinh `chon/`, `ban-do-cau.json`, sổ nguồn, và chặn ảnh 🔴) — bấm
      Dựng mà chưa Duyệt thì xưởng ráp bằng bản đồ CŨ, anh sửa ảnh xong video vẫn y nguyên.
      Nhưng bắt người nhớ thứ tự hai nút là sai. Đã gộp thành **"✓ CHỐT & DỰNG VIDEO"** một
      bấm; giữ "▶ Dựng lại" làm nút phụ cho lúc chỉ đổi nhạc/kịch bản chứ không đổi ảnh.

20. **Làm xong một bước thì phải MỞ ĐƯỢC tới kết quả ngay tại đó** (anh chốt 05/08). Báo
    "đã xếp kho" rồi để anh tự đi lần mò trong Finder là làm nửa việc — nhất là khi đường dẫn
    nằm sâu trong Drive, tên thư mục là slug tiếng Việt bỏ dấu.
    → Nút **📂 Mở thư mục** đổi nhãn theo trạng thái: chưa xếp kho thì mở *thư mục việc* trên
    ổ máy, xếp kho rồi thì mở *hộp trong kho thành phẩm*. Và xếp kho xong thì **tự mở luôn**.
    Cùng một luật với luật link-bấm-được trong `~/.claude/CLAUDE.md`: nhắc tới chỗ nào thì
    phải bấm được tới chỗ đó.

21. **Dán ảnh phải có NÚT BẤM, đừng chỉ dựa vào phím Cmd-V.** Anh kêu 05/08 là phải gửi ảnh
    qua Zalo → lưu về máy → tải lên, "vướng quá" — trong khi đường dán ĐÃ chạy (sổ gắp có
    `image.png` do anh dán). Chức năng chạy được mà người dùng không dùng thì cũng như chưa có.
    Ba chỗ hụt đã vá:
    · sự kiện `paste` chỉ ăn khi trang đang có tiêu điểm và con trỏ KHÔNG nằm trong ô nhập —
      bấm chuột lung tung một cái là hụt. → thêm nút **📋 Dán ảnh** đọc thẳng bộ nhớ tạm
      bằng `navigator.clipboard.read()` (localhost là nơi an toàn nên API này dùng được).
    · bộ lọc cũ `f.type.startsWith('image/')` vứt nhầm ảnh sao chép từ Finder/Preview (nhiều
      khi không mang kiểu image/*) → nhận thêm theo ĐUÔI TÊN tệp.
    · thả tệp trước đây phải nhắm đúng ô nét đứt nhỏ → giờ thả vào đâu trong cột kho cũng được.
    Lưu ý: `clipboard.read()` đòi trang đang có tiêu điểm — bấm nút thì luôn có, nên không sao;
    gọi bằng script từ ngoài thì báo "Document is not focused".

22. **Bộ lọc chỉ đo KÍCH THƯỚC thì mù về nội dung** (anh phản ánh 05/08: "có những ảnh không
    liên quan vẫn được đưa vào kho"). Google trả theo từ khoá nhưng trong trang có cả ảnh
    quảng cáo, ảnh khối "tìm kiếm liên quan", ảnh bãi biển, ảnh chăm sóc da — tất cả đều đủ to
    nên lọt hết. → `loc_anh.py`: xếp cả lô thành MỘT BẢNG đánh số rồi hỏi **haiku** một lượt
    (không hỏi từng ảnh). Chạy thật trên `tay-hubner`: **107 ảnh, 196 giây, bắt 17 tấm** —
    poster quảng cáo, bảng xếp hạng toàn chữ, ảnh lễ tân tuxedo, ảnh mờ.
    Hai luật cứng: **không bảo model đoán mặt cầu thủ** (nó không nhận ra, đoán bừa hại hơn),
    và **không xoá ảnh bị chấm** — model vẫn sai (nó chấm ảnh họp báo là "khung viền tiếp
    thị", mà ảnh họp báo dùng được). Chỉ mờ đi, đẩy xuống cuối, có nút bật lên xem lại.

23. **Google che URL gốc rất kín — đừng phí thời gian như em đã phí.** Anh đề xuất 05/08:
    "anh chọn luôn ảnh trên Google, em chỉ việc lấy về". Ý hay, nhưng ba cách đều đo và đều hỏng:
    · **ánh xạ theo thứ tự** ô lưới ↔ danh sách URL trong mã trang → lệch (65 ô / 99 URL);
    · **đọc ảnh trong khung xem lớn** → Google phục vụ bản `encrypted-tbn` của chính nó
      (738×411), không phải ảnh gốc, mà lại quá nhỏ cho khung dọc 1080;
    · **ánh xạ bằng tỉ lệ khung hình** → 12 ô thử: 2 khớp duy nhất, 5 mơ hồ, 5 không khớp
      (quá nhiều ảnh cùng tỉ lệ 1.5).
    DOM Google cũng không để lộ URL gốc ở bất kỳ thuộc tính nào. → Đã gỡ mã, đổi sang hướng
    "gắp về rồi lọc". Bài học chung: **thứ nhà cung cấp cố tình giấu thì đừng cố moi** — tìm
    đường khác đạt cùng mục đích (ở đây: người vẫn là người chọn, chỉ đổi chỗ chọn).

24. **Mỗi lệnh chạy Python là một tiến trình mới → `the_dung_chung()` mở TAB MỚI.** Em vấp
    cái này ba lần khi thử: mở Google ở tab A, lệnh sau đọc tab B trống trơn rồi kết luận sai.
    Thử việc gì dính trình duyệt thì **gộp hết vào MỘT script**. Và nhớ đóng tab thừa —
    một buổi thử để lại 6 tab.

25. **Câu hỏi của anh vạch ra chỗ nghẽn mà em không thấy** (05/08): *"tại sao em lấy được ảnh
    về kho mà anh lại không tự chọn được?"* — vì em **chưa bao giờ chọn**. Em bóc từ mã trang
    ra một DANH SÁCH url rồi lấy 18 cái đầu, mù tịt về tấm nào ra tấm nào. Anh thì nhìn theo
    VỊ TRÍ trên màn hình. Em đã phí cả buổi cố nối hai thứ đó **trên trang Google** (mục 23),
    trong khi lời giải nằm ở phía bên kia: **bày chính danh sách ấy ra TRONG TRẠM**.
    → `xem_truoc()` chỉ bóc url + kích thước, không tải gì; trạm dựng lưới bằng chính url gốc
    (trình duyệt của anh nạp thẳng, server không tốn gì); anh bấm tấm nào thì `lay_theo_url()`
    mới tải tấm ấy về và cho qua cổng watermark. Ảnh anh thấy CHÍNH LÀ url đó — hết chỗ lệch.
    Đo thật: bóc danh sách 6 giây / 54–57 ảnh; chọn 3 tấm → về 2 (1 tấm cổng chặn, có báo rõ).
    **Bài học nghề: khi bí, hỏi lại "mình đang cố nối hai đầu ở đâu?" — nhiều khi đổi CHỖ NỐI
    là xong, không cần phá cái đầu đang khoá.**

26. **Tiện ích Chrome giải được khúc mà trạm không với tới** (anh đề xuất 05/08). Trạm gắp
    được ảnh từ Google và từ bài báo, nhưng ảnh nằm ở Facebook cầu thủ, Instagram, diễn đàn
    thì anh vẫn phải tải về máy rồi tải lên. Tiện ích xoá khúc vòng đó: chuột phải một ảnh ở
    BẤT KỲ trang nào là nó bay thẳng vào kho của việc đang mở trên trạm.
    Ba chỗ đáng nhớ khi làm:
    · **Tải ảnh NGAY TRONG tiện ích rồi gửi byte sang trạm**, đừng đưa URL cho trạm tự tải —
      Facebook/Instagram chỉ trả ảnh cho phiên đã đăng nhập, mà tiện ích chạy trong chính
      trình duyệt của anh nên có sẵn phiên đó; trạm gọi từ ngoài thì bị chặn.
    · Trạm phải **mở CORS** (`Access-Control-Allow-Origin: *` + trả lời OPTIONS) vì tiện ích
      gọi từ origin `chrome-extension://`.
    · Trạm **nhớ việc đang mở** (`/api/dang-lam`) để tiện ích biết gửi ảnh về thư mục nào —
      không bắt anh khai lại mã việc mỗi lần gắp.
    Ảnh từ tiện ích đi đúng cửa `/api/tai-len`: soi watermark đủ, nhưng KHÔNG vứt tấm nào,
    vì đây là ảnh NGƯỜI chỉ tận tay (cùng luật với mục 17).

27. **Chuẩn ảnh: FULL HD trở lên** (anh chốt 05/08). Đo theo **cạnh dài ≥1920 VÀ cạnh ngắn
    ≥1080**, không đo theo "rộng/cao" — ảnh chân dung cầu thủ 1080×1920 cũng là Full HD, đòi
    "rộng ≥1920" là loại sạch ảnh dọc.
    **Nhưng siết không thôi thì chết đói:** đo kho thật 554 ảnh — chỉ 21% đạt; một lượt tìm
    Google trả 56 ảnh thì 10 tấm đạt (18%). Cách bù đúng là **xin Google lọc ngay tại nguồn**
    (`&tbs=isz:lt,islt:2mp` — chỉ ảnh trên 2 megapixel) chứ không phải gắp về rồi vứt.
    Đo lại sau khi thêm tham số: **88 ảnh bày ra, 72 tấm đạt Full HD (82%)** — vừa đúng chuẩn
    vừa NHIỀU HƠN trước. Bài học: gặp ngưỡng chất lượng thì việc đầu tiên là hỏi *"nguồn có
    cho mình lọc sẵn không?"*, đừng lao vào lọc ở đầu ra.
    Lưới CHỌN vẫn bày cả ảnh dưới chuẩn nhưng dán nhãn vàng và ẩn mặc định — có tấm quý mà
    đời chỉ có bản nhỏ, chặn cứng thì anh không còn đường lấy. Đường TẢI TỰ ĐỘNG thì chặn cứng.

28. **Đừng bắt người gõ 20-30 lượt tìm** (anh hỏi 05/08: "lấy đủ ảnh có khi phải gõ tìm 20-30
    lần, anh phải tự làm à?"). Không — trạm ĐÃ có từ khoá của TỪNG CÂU (Claude gợi lúc mở
    việc), nên nó tự chạy hết một lượt rồi bày ra MỘT lưới gom **theo câu**.
    Đo thật trên `tay-cuadi` (23 câu): gợi từ khoá 87 giây + tìm loạt 104 giây = **192 giây,
    276 ảnh, 100% đạt Full HD, không câu nào trắng tay**. Anh không gõ lần nào.
    Ba chỗ làm cho đúng:
    · **Chỉ bóc danh sách, không tải** — 6 giây một câu; tải hết 276 tấm rồi mới cho chọn thì
      vừa lâu vừa phí, mà phần lớn sẽ bị vứt.
    · **Bỏ ảnh trùng giữa các câu** — nhiều câu ra cùng từ khoá ("Việt Nam Indonesia" ở câu 1
      và 2); không lọc thì anh phải nhìn lại đúng những tấm vừa xem.
    · **Chọn tấm nào là GÁN THẲNG vào câu ấy** (`ban_do_url` ánh xạ url → tệp sau khi tải).
      Chọn xong cũng là xong bản đồ câu → ảnh, không phải làm hai lần.
    Tiện ích Chrome KHÔNG làm việc này — nó chỉ lấy ảnh lẻ ở trang đang xem. Hai thứ khác vai.

29. **Manifest V3 CẤM script viết thẳng trong trang tiện ích — và chặn IM LẶNG.** Bảng nhỏ của
    tiện ích đứng nguyên ở chữ "đang hỏi trạm…" (anh báo 05/08), anh tưởng trạm không trả lời;
    đo lại thì trạm trả lời trong **8 mili giây** — đoạn mã chưa hề chạy, CSP đã chặn từ đầu và
    không kêu một tiếng nào ra màn hình. Phải tách ra `bang.js` rồi `<script src>`.
    **Dấu hiệu nhận ra kiểu lỗi này: chữ khởi tạo đứng nguyên, cả nhánh thành công lẫn nhánh
    lỗi đều không chạy.** Không phải "chậm", mà là "chưa từng chạy".

30. **"Việc đang mở" phải GHI RA TỆP, đừng giữ trong bộ nhớ.** Anh hỏi đúng 05/08: "mỗi video
    một kho riêng thì tiện ích biết gửi về kho nào?" — nó hỏi `/api/dang-lam`. Nhưng nếu trạm
    khởi động lại (sửa mã, máy ngủ dậy) mà quên mất, nó rơi về "việc đầu danh sách" → **gửi
    ảnh nhầm kho, nhầm rất im lặng**, tới lúc dựng video mới lòi ra. Đã ghi ra
    `~/socbongda247/tram-dang-lam.txt`, thử ngược bằng cách giết trạm rồi bật lại: vẫn nhớ.
    Và cho **đổi việc ngay trong bảng tiện ích** — anh đang đứng ở Facebook thì đổi tại chỗ,
    không phải nhảy về tab trạm.

31. **Trang không tự hiện ảnh mới thì tiện ích chỉ tiện một nửa** (anh nêu 05/08: phải F5).
    Đã thêm vòng hỏi RẺ `/api/kho-moi/<mã>` (chỉ số ảnh + mốc thời gian) mỗi 4 giây.
    **Chỗ suýt hỏng:** cảnh THẬT của anh là gửi ảnh ở tab Facebook, tab trạm nằm NỀN — mà tab
    nền thì trình duyệt hãm `setInterval` lại, có khi vài chục giây mới chạy một lần. Nên phải
    bắt thêm `visibilitychange` + `focus`: **vừa quay lại tab là kiểm ngay**. Chỉ có
    `setInterval` thì anh vẫn phải ngồi chờ.

32. **Ảnh QUÁ NGANG (bảng tỷ số, bảng xếp hạng) — xưởng cắt mất hai bên nên vô dụng**
    (anh nêu 05/08). Xưởng luôn crop vào khối 1080×1248; ảnh tỉ lệ 3,1 thì chỉ còn ~28% ở
    giữa — đo thật trên ảnh bảng tỷ số: cắt xong chỉ còn mỗi "3-0", tên hai đội bay sạch.
    Ba cách dựng, người chọn cho từng ảnh (`anh/cach-hien.json`, xưởng đọc):
    · **cắt · zoom** — như cũ, hợp ảnh người (chủ thể tụ ở giữa);
    · **vừa khung** — thu cả tấm cho lọt bề ngang, nền mờ. Không mất gì, nhưng chữ nhỏ;
    · **trượt đọc** — phóng cho chữ TO nhất rồi trượt ngang hết bảng. Đọc được, nhưng cảnh
      phải đủ dài (đo: 3,5 giây cho bảng 1920px là vừa).
    Máy tự chọn "vừa khung" khi tỉ lệ ≥2,0 — nhưng **máy KHÔNG biết trong bảng chữ nào đáng
    đọc**, nên quyền chốt là của người. Đây là ranh giới thật giữa việc máy làm được và không.

33. **Cổng watermark DỜI từ cửa nhập sang bước DUYỆT** (anh chốt 05/08: "ảnh anh chọn tay thì
    cho pass, em chỉ check ở bước đưa vào cảnh và cảnh báo").
    Không phải bỏ cổng — là đặt nó **đúng chỗ**: soi 12–20 tấm THẬT SỰ lên hình, thay vì soi
    cả trăm tấm ứng viên rồi vứt phần lớn. Đo: lấy 6 tấm chọn tay về kho **1,5 giây** (trước
    ~10 giây); soi lúc duyệt 3 tấm hết **2,7 giây**. Thử ngược bằng ảnh dán "@nhipcongtruong":
    cổng chặn đúng ở lần bấm đầu, ghi sổ đủ khi anh xác nhận.
    · Đường MÁY đi lấy (bóc bài) vẫn soi ngay ở cửa nhập — máy lấy bừa thì phải vứt bừa.
    · Đường NGƯỜI chọn (lưới Google, dán, tiện ích) thì qua thẳng, dán nhãn **"chưa soi"** để
      anh không tưởng nó đã sạch. Nhãn ấy quan trọng: **im lặng để người hiểu nhầm là đã kiểm
      thì tệ hơn không kiểm.**
    Lý do đáng ghi: mắt nhìn ảnh nhỏ trên lưới KHÔNG thấy được dấu chìm mờ ở góc — nên "anh
    đã nhìn rồi" không thay được cổng, chỉ đổi được THỜI ĐIỂM soi.

34. **Đừng "đi tắt hộ" người dùng theo cách họ không đoán được.** Anh báo 05/08: đang ở câu 5,
    gán ảnh xong màn hình phóng thẳng xuống **câu 23**. Mã chạy đúng ý định ban đầu — em cho
    nhảy tới *"câu chưa có ảnh gần nhất"*, nghe thì thông minh. Nhưng sau lượt "Tìm loạt" thì
    phần lớn câu đã có ảnh, nên cái "gần nhất" ấy nằm tận cuối kịch bản.
    Người làm việc theo mạch TỪ TRÊN XUỐNG. Gán xong thì xuống **câu kế tiếp**, chấm hết —
    dù câu đó đã có ảnh (thấy có rồi thì anh tự bấm xuống tiếp, mất nửa giây).
    Luật rút ra: **máy đoán hộ mà người không lường trước được thì đó là lỗi, kể cả khi mã
    chạy đúng như đã viết.** Tự động hoá chỉ đáng khi nó đi đúng hướng người đang đi.

35. **Trạm cho gán ảnh theo CÂU, mà xưởng lại cắt cảnh theo ĐỒNG HỒ — hai thứ không ăn khớp,
    và hỏng IM LẶNG.** Anh bắt đúng 05/08: "cảnh 2 có ảnh sao dựng lại bỏ qua?"
    Đo ra: câu trung bình 2,2 giây, cảnh cắt 3–4 giây → mỗi cảnh nuốt gần hai câu, mà xưởng
    chỉ lấy ảnh của câu nằm GIỮA cảnh. Kết quả: **anh chọn 17 ảnh, 7 tấm không bao giờ lên
    hình** (câu 2, 3, 7, 9, 10, 14, 24) — không báo một tiếng.
    → Anh chốt: **ẢNH quyết định chỗ cắt**, không phải đồng hồ. `chia_nhip_theo_anh()`.
    Kết quả đo lại: 10/17 → **14/17 ảnh lên hình**, nhịp 15 cắt/phút (cũ 17 — gần như y nguyên).

36. **Hai chỗ máy KHÔNG tự chữa được thì phải BÁO, đừng im.** Cắt theo ảnh xong vẫn còn:
    · **cảnh 0,72 giây** — chớp mắt là qua, buộc phải gộp, nên ảnh của nó mất. Máy phải nói
      rõ MẤT TẤM NÀO (câu 9, 10, 15), chứ gộp im lặng là lặp lại đúng lỗi vừa sửa.
    · **quãng 17,2 giây một ảnh đứng suốt** — máy không bịa ra ảnh mới được. Tự ý cắt đôi
      cùng một tấm chỉ tạo cú nhảy hình vô nghĩa. Phải báo để ANH gán thêm ảnh.
    Cả hai giờ hiện ngay lúc bấm DUYỆT (hỏi lại: dựng luôn hay quay lại gán thêm), chứ không
    để anh xem xong video mới phát hiện thiếu.
    **Luật: cái gì máy đành chịu thì nói thẳng lúc đó, đừng để người phát hiện sau.**

37. **Chọn kiểu chuyển động theo HÌNH DÁNG ẢNH, thôi bốc ngẫu nhiên** (anh chốt 05/08):
    ảnh NGANG → chạy ngang · ảnh ĐỨNG → zoom in.
    Không chỉ là quy ước cho đều tay — đúng cả về kỹ thuật. Khung của kênh là khối 1080×1248,
    nên ảnh DỌC crop vào đó gần như không dư bề ngang: bắt nó trượt thì hoặc trượt được vài
    chục pixel (nhìn y như đứng yên), hoặc phải phóng to quá tay làm vỡ ảnh. Ảnh NGANG dư
    nhiều bề ngang, trượt mới có chỗ mà trượt.
    Thứ tự quyết định: tỉ lệ ≥2,0 → **vừa khung** (cắt là mất chữ) · ≥1,0 → **chạy ngang** ·
    <1,0 → **zoom in**. Ảnh vuông xếp vào nhóm ngang (crop xong vẫn dư ~170px để trượt).
    Người vẫn đè được bằng nút "Cách dựng" ở trạm cho từng ảnh.

38. **Vẽ lại cả lưới mỗi lần bấm một ô = đơ.** Anh báo 05/08: "check vào thì đơ không tích
    được, nhưng vẫn báo chọn được ảnh". Đúng — mỗi lần bấm, `veChonLuoi()` dựng lại
    `innerHTML` cả lưới **74–88 thẻ `<img>` trỏ thẳng ra mạng** → trình duyệt tải lại từng
    tấm → treo mấy giây, dấu tích chưa kịp hiện. Trạng thái thì vẫn đúng, nên nó "báo chọn
    được" mà mắt không thấy gì.
    → Tách hàm `danhDau()` chỉ đổi class + số thứ tự của ô vừa bấm. Đo lại: **bấm 3 tấm hết
    1 mili giây**, ảnh không tải lại lần nào.
    **Luật: đụng vào `innerHTML` của khối chứa ảnh mạng là phải trả giá bằng lượt tải lại.**

39. **Sau khi XOÁ, tiêu điểm phải Ở LẠI chỗ vừa đụng.** Anh báo: xoá ảnh ở câu 5 thì màn hình
    nhảy về câu 1. Vì nhánh xoá không đặt `dangChon`, nó giữ giá trị cũ (thường là 0) rồi
    `veCau()` kéo màn hình về đầu. Cùng họ với lỗi mục 34 — **mọi thao tác trên một câu đều
    phải neo tiêu điểm vào chính câu đó**, không có ngoại lệ.

40. **Ô nhập nào cũng phải ăn phím Enter.** Gõ từ khoá ở từng câu xong phải với tay bấm nút
    🔎 là thừa một nhịp × 26 câu. Enter = tìm luôn.

41. **Kho cả trăm tấm thì phải xoá được HÀNG LOẠT.** Nút "🗑 Chọn để xoá" bật chế độ chọn
    nhiều (bấm lần nữa là vứt); trong lưới đề xuất thì mỗi ô có ✕ để loại khỏi danh sách mà
    không cần tải về. Xoá ảnh đang gán vào câu thì gỡ luôn khỏi câu đó, đừng để bản đồ trỏ
    vào tệp không còn.

42. **Chọn kiểu đúng cho TỪNG cảnh vẫn có thể sai cho CẢ VIDEO** (anh chốt 05/08: không kiểu
    nào được quá **65%**). Luật mục 37 (ngang→chạy ngang, dọc→zoom) đúng ở mức từng ảnh, nhưng
    kho ảnh bóng đá gần như toàn ảnh ngang → cả video chạy ngang 100%, xem một lúc là đơn điệu,
    mắt người xem đoán trước được nhịp.
    → `can_bang_kieu()` chạy ở cấp cả video, sau khi đã chọn kiểu cho từng cảnh.
    Đổi cảnh nào cho ít hại nhất — đây mới là phần đáng nghĩ:
    · thừa NGANG → đổi sang zoom mấy tấm **gần vuông nhất** (tỉ lệ thấp nhất), vì chúng dư bề
      ngang ít nhất nên trượt vốn đã không đẹp; tấm càng ngang càng giữ để trượt.
    · thừa ZOOM → đổi sang ngang mấy tấm **ít dọc nhất** (tỉ lệ cao nhất), vì dọc quá thì phải
      phóng to mới có chỗ trượt, dễ vỡ.
    Không đụng vào cảnh "vừa khung"/"trượt đọc" (bảng biểu) và cảnh NGƯỜI đã tự chỉ định.
    Đo trên video Việt Anh: 21 cảnh → **13 ngang / 8 zoom (62%)**, cân lại 4 cảnh.
    Bài học chung: **luật đúng ở mức chi tiết vẫn phải kiểm lại ở mức tổng thể.**

43. **Nhịp lặp y hệt qua nhiều video là DẤU VÂN TAY của máy** (anh chốt 05/08: hướng zoom
    in/out, trượt trái/phải, chéo — phải tự cân đối theo tài nguyên từng video).
    Trước đó xưởng chỉ có **hai** kiểu chuyển động và cả hai đều một chiều cứng: zoom luôn
    phóng VÀO từ đúng tâm, trượt luôn TRÁI→PHẢI. Nhân lên hàng trăm video thì đó là chữ ký
    quá dễ đọc — và mục tiêu của kênh là **bật kiếm tiền trong 3 tháng**, tức là phải qua mắt
    người xét "nội dung sản xuất hàng loạt" (rủi ro số 2 trong sổ dự án).
    → `rai_huong()`: 6 hướng — trượt `→ ← ↘ ↗`, zoom `vào / ra` — cộng **tâm zoom lệch nhẹ**
    (±16%) mỗi cảnh một chỗ, vì zoom vào đúng giữa mọi lần cũng là dập khuôn.
    Hai luật rải, theo thứ tự: ① hai cảnh liền nhau không cùng hướng (chỗ dễ lộ nhất là hai cú
    trượt cùng chiều nối đuôi) ② hướng nào dùng ít thì ưu tiên, để không video nào "toàn trượt
    trái sang phải". Seed gắn với thư mục việc → **mỗi video một trật tự khác, mà dựng lại lần
    hai vẫn y như cũ** (không nhảy lung tung khi render lại).
    Đo: 3 video giả lập ra 3 trật tự khác hẳn, phân bố đều 2/2/2/2/2/2, **0 lần lặp liền kề**.
    Video Việt Anh thật: 21 cảnh → ↗3 ↘3 ←4 →3 zoom-vào 4 zoom-ra 4.

44. **Danh sách việc phải lọc theo NGÀY, mặc định hôm nay** (anh nêu 05/08: "tài nguyên chỉ có
    ngày 4 thôi à?"). Mỗi thư mục việc mang tên bắt đầu bằng ngày (`2026-08-04-…`), nên gom
    theo ngày là sẵn có. Đổ hết mọi ngày vào một ô chọn thì càng chạy càng dài, mà anh chỉ làm
    việc của hôm nay — chạy 10 video/ngày thì sau một tuần là 70 dòng.
    Mặc định hôm nay; hôm nay chưa có việc nào thì rơi về **ngày gần nhất có việc** (đừng hiện
    danh sách rỗng rồi để anh tưởng trạm hỏng). Ngày hôm nay hiện chữ "hôm nay" cho dễ nhận.

45. **Thư mục việc chuyển sang ổ DATA + dọn định kỳ** (anh chốt 05/08: "cho sang ổ DATA, cứ
    sau 5 ngày kể từ khi xếp kho thì xoá đi dữ liệu").
    Con số làm nên quyết định: mỗi video gắp về hàng trăm ảnh ứng viên nhưng chỉ dùng vài chục
    — video Việt Anh **379 tấm / 173 MB, dùng 25 tấm**; Hubner 107 tấm, dùng 14. Chạy 10 video
    mỗi ngày là nửa GB đổ vào ổ khởi động mỗi ngày.
    **Nhưng chuyển chỗ KHÔNG giải quyết được gì nếu không dọn** — phải nói thẳng với anh là ổ
    DATA còn ÍT HƠN ổ hệ thống (10 GB so với 44 GB). Chuyển mà im lặng là đẩy anh vào chỗ đầy
    nhanh hơn.
    `don_kho.py` dọn theo HAI NHỊP, cố ý tách:
    · **ngay khi đã xếp kho** → vứt ảnh ứng viên ngoài `chon/`, thư mục tạm `dung/` (20 MB rác,
      còn hơn cả video thành phẩm 13 MB), bảng soi ảnh, ảnh chứng cứ QC (hộp trên Drive đã có);
    · **sau 5 ngày kể từ khi xếp kho** → xoá cả thư mục việc.
    **Không đụng việc CHƯA xếp kho, dù cũ tới đâu** — đó là việc đang làm dở, xoá nó là xoá
    công anh bỏ ra chứ không phải dọn rác. Mặc định chạy chế độ XEM, phải thêm `--that` mới xoá.
    Đo thật: `tay-vietanh` 178 MB → **22 MB**, mà dựng lại video vẫn nguyên vẹn (25 ảnh `chon/`
    + đủ sổ). Lịch `com.socbongda247.donkho` chạy 3h20 hằng ngày.

46. **Đối chiếu hai bộ mã là cách bắt lỗi im lặng.** Làm `don_kho.py` xong thấy nó báo
    `tay-vietanh` ĐÃ xếp kho, trong khi trạm ghi "CHƯA vào kho" — một trong hai sai.
    Soi ra: **trạm sai**. Hàm `_tim_hop` của trạm so tên THƯ MỤC, mà tên hộp bị cắt còn 44 ký
    tự nên so chuỗi trượt; `don_kho` so TIÊU ĐỀ trong `SO-VIDEO.jsonl` nên đúng. Đã sửa trạm
    dùng cùng cách. Nếu không viết bộ dọn thì lỗi này còn nằm im lâu nữa.

47. **Kiểu thứ ba: CHẠY DỌC, ảnh đứng trượt từ DƯỚI LÊN** — anh chỉ 05/08, học từ Nhím Bóng Đá,
    tốc độ y như chạy ngang (10% khung/giây).
    Trước đó em cho ảnh dọc chỉ zoom, lấy cớ "ảnh dọc không dư bề ngang để trượt". Đúng phần
    bề ngang, nhưng **quên mất chiều cao**: ảnh dọc crop vào khung 1080×1248 thì dư ~546px
    theo trục dọc — thừa chỗ để trượt. Nhìn thiếu một trục.
    **Chỉ MỘT chiều: dưới lên.** Có lý riêng chứ không phải quy ước — ảnh chân dung thì kết ở
    khuôn mặt mới đúng nhịp kể; đi ngược lại là đẩy mặt người ra khỏi khung ở cuối cảnh.
    Đo bằng ảnh thử có "đầu" trên và chữ ở chân: khung đầu thấy phần chân, khung cuối kết trọn
    khuôn mặt — đúng ý.
    Trong nhóm ảnh đứng thì **chia đôi zoom / chạy dọc**, ưu tiên cho chạy dọc mấy tấm DỌC NHẤT
    (dư chiều cao nhiều nhất). Video Việt Anh: 21 cảnh → 13 ngang · 6 zoom · **2 chạy dọc**.

48. **Đổi chỗ lưu thì mọi lệnh gõ tay đều gãy.** Dời thư mục việc sang ổ DATA xong,
    `python3 xuong.py viec/<mã>` báo không thấy tệp — đường tương đối cũ trỏ vào chỗ đã trống.
    Thay vì bắt nhớ đường mới dài ngoằng, cho mọi bước nhận **luôn cái mã**:
    `python3 xuong.py 2026-08-04-tay-vietanh`. `DD.tim_viec()` nhận cả mã lẫn đường dẫn.
    Luật: **dời dữ liệu thì phải đi kèm sửa mọi lối vào dữ liệu đó**, không thì hôm sau vấp.

49. **Quét kỹ mới ra thủ phạm nặng nhất — HỒ SƠ CHROME 542 MB.** Anh bảo "quét kỹ để không
    bị sót" (05/08), và đúng là em đã sót: lúc đầu chỉ nhìn `~/socbongda247` (1,8 MB — nhẹ hều)
    với nhà kênh trên Drive, quên mất `~/.config/socbongda247/chrome-tram` — hồ sơ trình duyệt
    của trạm, **phình theo mỗi lần gắp ảnh**, nặng gần bằng cả kho tài nguyên.
    **Cách quét cho khỏi sót:** đừng nhìn theo "thư mục dự án", hãy `grep` mọi đường dẫn KHAI
    TRONG MÃ (`expanduser`, hằng số đường dẫn) rồi đo từng cái. Chỗ ăn ổ nhiều nhất thường nằm
    ngoài thư mục dự án — cache, hồ sơ trình duyệt, thư mục tạm.

50. **Một chỗ khai đường, mọi nơi theo — và luôn có đường lùi.** `duong_dan.py` giờ có hàm
    `_o_data(ten, cu)`: dùng ổ DATA nếu có, **tự rơi về chỗ cũ nếu ổ không gắn được**. Hệ vẫn
    chạy khi ổ DATA vắng mặt, chỉ tốn ổ hệ thống — thà chậm còn hơn chết.
    Đã chuyển: `viec/` · `chrome-tram/` · `kho-tai-nguyen/` (nhạc + video stock) · `demo/` ·
    `_KHONG-DAT-QC/`. Kết quả: ổ hệ thống 44 → **46 GB trống**, nhà kênh trên Drive 715 → 90 MB.
    **GIỮ trên Drive: `kho-video-thanh-pham`** — đây là thứ DUY NHẤT không tái tạo được (video
    đã dựng + gói đăng). Để trên Drive thì có bản sao trên mây; chuyển sang DATA là chỉ còn
    một bản, trên đúng một máy. Cần anh chốt riêng chứ không tự quyết.

51. **Xoá bản cũ thì phải đối chiếu số tệp TRƯỚC, và điều kiện tuỳ loại dữ liệu.** Dữ liệu quý
    thì đòi khớp tuyệt đối; hồ sơ trình duyệt (cache, tái tạo được) thì chỉ cần đích KHÔNG
    THIẾU hơn nguồn — Chrome ghi thêm/bớt vài tệp lúc tắt là chuyện thường, đòi khớp tuyệt đối
    là tự khoá tay mình. Và **tắt tiến trình đang dùng dữ liệu trước khi chuyển**.

52. **"Có thì chép, không thì thôi" là cách để CỔNG BIẾN MẤT.** Anh gặp 05/08: xếp kho báo
    `THIẾU: qc.png`. Bới ra thì `buoc3_xepkho.py` viết `if os.path.exists(qc): copy` — mà file
    ấy do CHÍNH cổng QC ra sinh. Video nào chưa ai chạy cổng bằng tay thì hộp thiếu tệp.
    **Nhưng thiếu tệp mới là triệu chứng nhẹ. Triệu chứng nặng là: video ĐI THẲNG RA HỘP MÀ
    KHÔNG QUA CỔNG NÀO.** Đúng bài học số 3 của sổ dự án, chỉ khác hình dạng.
    → `buoc3` giờ TỰ CHẠY cổng QC ra nếu chưa có, truyền luôn `--so so-nguon.jsonl`, và
    **cổng chặn thì DỪNG, không xếp kho** (`raise SystemExit`). Không sinh được ảnh chứng cứ
    cũng dừng.
    **Luật: chỗ nào viết `if exists(...)` quanh một bước KIỂM DUYỆT thì đó là cổng đã hỏng** —
    vì bước kiểm bị biến thành tuỳ chọn. Cổng phải là "chạy, hoặc dừng", không có nhánh thứ ba.

53. **Xếp kho lỗi để lại RÁC trong kho, phải dọn.** Ba lần bấm xếp kho hỏng là ba hộp thiếu
    tệp nằm lại trên Drive + ba dòng trong `SO-VIDEO.jsonl` — mà sổ ấy chính là chỗ `don_kho.py`
    và trạm dựa vào để biết "đã xếp kho chưa". Rác trong sổ làm sai luôn phép dò ấy.
    Cần: hộp không đủ 7 tệp thì **xoá cả hộp lẫn dòng sổ**, đừng để lại.

54. **Ảnh NHỎ mà ngang — banner trận đấu, ảnh đồ hoạ — cắt là hỏng, phóng là vỡ**
    (anh chỉ 05/08, kèm đúng một tấm mẫu BG Pathum vs Aston Villa).
    Luật "tỉ lệ ≥2,0 thì vừa khung" KHÔNG bắt được loại này: banner ấy tỉ lệ **1,78**, lọt
    dưới ngưỡng nên bị xử như ảnh ngang thường. Mà nó chỉ 460×259 — crop vào khối 1080×1248
    phải **phóng 4,8 lần**: vừa vỡ, vừa cụt mất hai logo và tên đội.
    → Thêm điều kiện thứ hai, tính bằng **mức phóng cần thiết** chứ không bằng tỉ lệ:
    `max(W/w, anh_cao/h) > 1,30` → dùng **vừa khung**. Và trong lúc render, `_render_vua_khung`
    **chặn luôn mức phóng ở 1,30** — thà ảnh nhỏ mà nét và thấy đủ, còn hơn to mà vỡ và cụt.
    Ngoại lệ anh nêu: **muốn phóng to để cắt bỏ logo** thì người tự chọn "cắt · zoom" ở trạm.

55. **Cùng một luật viết ở HAI NƠI là chắc chắn có ngày lệch.** Sửa xong mục 54, chạy thử thấy
    ảnh mới y hệt ảnh cũ. Vì luật chọn kiểu nằm ở hai chỗ: `chon_kieu()` (xưởng gọi) và một
    bản CHÉP LẠI bên trong `render_canh()`. Em sửa `chon_kieu` mà quên bản chép.
    → `render_canh` giờ gọi thẳng `chon_kieu()`. **Luật ở một chỗ, mọi nơi gọi vào đó.**
    Dấu hiệu nhận ra kiểu lỗi này: sửa xong mà kết quả không đổi một ly — đừng vội nghi phép
    tính, hãy tìm xem có bản chép thứ hai không.

56. **KHÔNG đưa link vào ô MÔ TẢ của gói đăng** (anh chốt 05/08). Link ngoài trong mô tả kéo
    người xem rời khỏi kênh, mà YouTube cũng phân phối dè chừng hơn với video có link ra ngoài.
    Nguồn tin **vẫn giữ**, nhưng ở mục 【6】 GỐC TIN — phần ghi chú NỘI BỘ để sau còn lần lại
    được (kiểm tin, đối chiếu bản quyền ảnh), không phải phần dán lên YouTube.
    Nhớ phân biệt hai loại nội dung trong cùng một tệp: **phần để COPY đi** và **phần để TRA
    LẠI**. Trộn chúng vào nhau là có ngày dán nhầm.

57. **Kho việc xếp theo NGÀY** (anh chốt 05/08): `viec/<ngày>/video-N-<chủ đề>`.
    Trước đó là một tầng phẳng `viec/2026-08-05-xuanson` — chạy 10 video/ngày thì sau một
    tuần là 70 thư mục nằm chung một chỗ, mà tên lại không nói video ấy nói về cái gì.
    Ba chỗ phải sửa theo, không được sót:
    · `glob(VIEC/*)` → **`glob(VIEC/*/*)`** ở `don_kho.py` và `_ds_viec()` của trạm;
    · **mã việc giờ là ĐƯỜNG TƯƠNG ĐỐI có dấu gạch chéo** (`2026-08-05/video-2-…`) — giao
      diện phải `encodeURIComponent`, nếu không URL vỡ ngay;
    · `buoc1_viet.py` tạo thư mục theo khuôn mới, đánh số bằng `DD.so_video_ke(ngày)`.
    `os.path.join(VIEC, ma)` thì **không cần sửa** — mã có gạch chéo vẫn ghép đúng. Đó là lý
    do chỉ phải đụng vào bốn tệp thay vì hai chục chỗ.
    `DD.tim_viec()` nhận cả ba cách gõ: đường dẫn · mã đầy đủ · **chỉ tên video** (tiện nhất,
    miễn không trùng ngày) — dời chỗ thì phải làm cho lối vào DỄ HƠN, không phải khó hơn.

58. **Con số trong sổ SAI thì mọi tính toán dựa vào nó đều sai — và sai rất khó thấy.**
    Sổ dự án ghi "ảnh 65% chiều cao khung", em lấy đó tính ngưỡng ảnh nhỏ. Chạy ra **9/20 cảnh
    thành "vừa khung"**, trong khi kho chỉ có 2 ảnh nhỏ. Số không khớp mới lần ra: khối ảnh
    thật cao **76% — 1080×1459**, không phải 1248. Với khối cao hơn thì ảnh HD 1280×720 cũng
    vượt ngưỡng, nên bị thu nhỏ oan.
    → Ngưỡng chỉnh lại theo con số THẬT: `PHONG_QUA_TAY = 2,30`. Kết quả: 19 ngang · 1 vừa
    khung, đúng bằng số ảnh nhỏ thật. Đã sửa luôn con số trong sổ dự án.
    **Cách bắt được: đối chiếu kết quả với thứ mình đếm được bằng tay.** "2 ảnh nhỏ mà 9 cảnh
    vừa khung" — chênh lệch ấy là thứ tố cáo, không phải cảm giác.

59. **In ra CĂN CỨ, không chỉ in KẾT QUẢ.** Nhịp hình cũ chỉ có `1:v · 2:n…` — thấy sai mà
    không biết vì sao. Thêm một dòng `soi kiểu: ngang×19 · vua×1 (01.jpg=ngang, 03.jpg=vua…)`
    là lộ ngay ảnh nào ra kiểu nào, dò ngược được về kích thước. Dòng ấy tốn một phút viết,
    tiết kiệm cả buổi mò.

## Nhận VIDEO từ extension (07/08/2026)

- **Video MXH phát bằng `blob:` — extension KHÔNG fetch được như ảnh.** Đường đúng: extension
  gửi LINK TRANG + cookie phiên về `/api/nhan-video`, trạm tải nền bằng yt-dlp (cookie ghi tệp
  tạm quyền 600, xoá ngay khi xong). Clip vào `<việc>/clip/tay/` + thumbnail + `nguon-clip.json`
  (tầng 3 — anh chỉ tay nghĩa là đã duyệt nội dung, nhưng bản quyền vẫn của người quay).
- **Cú pháp `--match-filter` của yt-dlp không có phép `|`** — muốn "quá 8 phút thì bỏ, thiếu
  trường thì cho qua" phải viết `duration<=?480` (dấu `?` sau phép so sánh). Viết
  `!duration | duration<=480` là chết ngay "Invalid filter part".
- **YouTube chặn tải ẩn danh từ máy này** (đòi cookie xác minh bot) — không sao: đích của cửa
  này là TikTok/FB/IG và extension LUÔN gửi kèm cookie. TikTok công khai tải được không cần
  cookie (đo thật: clip 54,8s về trong ~40 giây).
- Trang chủ / bảng tin thì yt-dlp không biết lấy video NÀO → trạm chặn sớm với lời hướng dẫn
  "mở video ra trang riêng". Đường thăm dò job dùng chung khuôn `/api/nhan-video/<job>`.

## GĐ2 — xem clip + cắt đoạn + gán cảnh (07/08/2026)

- Bấm clip trong dải 🎬 mở modal: video TUA ĐƯỢC nhờ route trả **HTTP 206 Range** (thiếu là
  <video> không seek nổi); nút "⏱ Từ/Đến = vị trí đang phát" nhanh hơn bắt anh gõ số.
- Gán ghi `anh/clip-canh.json` {câu → tep, tu, den}; xưởng đọc file này: câu có clip tự thành
  MỐC CẮT cảnh (ảnh kế thừa câu trước), render đúng đoạn (`bat_dau=tu`), và **giãn ranh giới
  hai cảnh lân cận** khi đoạn cắt lệch lời cảnh (mỗi hàng xóm giữ tối thiểu 1s, thiếu thì cắt
  bớt clip và báo). Tổng thời lượng + mọi mốc khác giữ nguyên — chỉ dịch 2 ranh giới.
- **Bài học Drive 07/08**: sổ kho thành phẩm nằm trên Drive; Drive tự cập nhật giữa ngày và
  siết quyền (EPERM) làm `/api/viec` chết 500 dây chuyền. Luật: thứ nằm ngoài ổ local chỉ
  được phép làm mất tính năng CỦA NÓ, phải bọc try — trạm sống bằng dữ liệu local.
- **Bổ sung theo anh duyệt (07/08 trưa):** cảnh gán clip phải HIỆN HÌNH trong ô ảnh của câu
  (route `/clip-thumb/<mã>/clip/tay/<tệp>?t=<giây>` cắt khung tại đúng mốc đầu đoạn, cache
  theo (tệp, giây)); và mỗi ĐOẠN ĐÃ CẮT vào sổ `anh/clip-doan.json` → hiện đầu kho ứng viên
  như một thẻ, bấm là gán cho câu đang chọn rồi nhảy câu kế (cùng nhịp với gắp ảnh), ✂ mở
  cắt lại, ✕ chỉ bỏ khỏi sổ không xoá tệp. Sổ dedup theo (tệp, tu, den) — gán một đoạn cho
  nhiều câu không nhân bản ghi.
- **Bấm thẻ đoạn = XEM ĐÚNG BẢN ĐÃ CẮT (anh chốt 07/08 trưa):** gán xong máy cắt luôn tệp
  đoạn thật vào `clip/doan/<tên>__<tu>-<den>.mp4` (re-encode, GIỮ TIẾNG để thẩm khoảnh khắc;
  xưởng vẫn cắt từ gốc và bỏ tiếng như cũ), route `/clip-doan-tep/...?tu=&den=` phát có Range.
  Cửa sổ XEM (mXem) tách khỏi cửa sổ CẮT (mClip): thẻ đoạn trong kho và ô clip ở câu đều mở
  mXem; nút ✂ trong mXem/thẻ mới sang mClip với mốc nạp sẵn. Xoá đoạn khỏi sổ chỉ xoá tệp
  bản-cắt khi KHÔNG câu nào còn dùng.
- **Vá file bằng nhiều mối nối edit thì mối nối là chỗ hỏng:** 07/08 dòng khai báo
  `async function xoaDoan` bị LẶP ĐÔI ở mối nối → script chết cả trang. Máy quét ngoặc tự chế
  báo nhầm (không hiểu regex) — tìm đúng bằng BISECT parser thật của node (prefix parse OK tới
  dòng nào, thủ phạm ở ngay dòng sau). Sau mỗi đợt sửa HTML/JS: parser thật, không tin quét thô.

## Xưởng TỰ NÉ watermark khi dựng (07/08/2026 — anh chốt sau 2 lần phải render lại)

- Tấm anh xác nhận "vẫn dùng" ở cổng DUYỆT: vị trí logo ĐÃ CÓ SẴN trong `so-nguon.jsonl`
  (OCR 7 vùng của lay_anh chạy từ trước) — xưởng đọc `bo_qua_dau_nguon` + rút tên vùng,
  truyền `tranh=[vùng]` vào render. KHÔNG tốn thêm lượt soi nào.
- `render_canh`: kẹp khung cắt TỪNG KHUNG HÌNH vào giới hạn né (mỗi góc chỉ cần né 1 trục,
  chọn trục còn dư); ảnh ngang trong khối dọc thì bề dọc KHÔNG có dư → có `zb` zoom-bù nâng
  dần (tối đa 1.45) tới khi đủ chỗ. Cảnh né bị cấm kiểu vừa-khung/trượt-dọc (hiện trọn ảnh).
  NGƯỜI đã chỉ cách hiển thị (cach-hien) thì tôn trọng, không ép né.
- `render_clip`: phóng 26% + cắt LỆCH về phía ngược logo (crop expression); vùng logo của
  ĐOẠN lấy bằng OCR 2 khung hình đúng đoạn cắt (cache `anh/vung-dau-clip.json`); caption
  giữa khung không né được — bỏ qua, chỉ né góc/dải.
- **Đo thật mới tin**: bài test đầu vô nghĩa vì (a) ảnh ngang tự né góc sẵn (đối chứng không
  lộ) và (b) thước đo đòi trắng 255 tuyệt đối trong khi JPEG+x264 làm trắng còn ~250. Chốt
  3 ca khó: đối chứng lộ 416–3060 điểm, bản né = 0 điểm tuyệt đối. Luật: bài test phải có
  ĐỐI CHỨNG DƯƠNG trước đã.
- Logo "giữa khung" máy chịu — in cảnh báo đỏ bảo anh đổi ảnh. OCR nghẽn (Drive khoá quyền)
  thì dựng vẫn chạy, chỉ mất phần né clip + in cảnh báo.
- **Ba vá 07/08 chiều theo lỗi anh bắt khi dùng thật:** ① cửa CẮT mở từ video GỐC không được
  tự dò "câu nào từng dùng video này" — cắt đoạn thứ hai là nó trỏ ngược câu 1, anh bấm GÁN
  thành ĐÈ đoạn câu 1 (luật: chỉ nạp đoạn cũ khi mở từ ô clip của câu / nút ✂ của đoạn;
  từ gốc thì luôn về câu đang chọn). ② cửa XEM bản cắt phải có Ô CHỌN CÂU + nút GÁN
  (xem xong gán được vào cảnh MÌNH MUỐN); thẻ đoạn thêm nút 🎬 gán-nhanh cho câu đang chọn.
  ③ bản cắt BỎ SẠCH TIẾNG (-an; các bản cũ đã bóc tiếng bằng -c:v copy) — anh chốt để chắc
  chắn không lồng âm; nghe tiếng thẩm khoảnh khắc thì ở cửa cắt video gốc. Kèm: sổ đoạn TỰ VÁ
  theo đĩa (tệp còn mà sổ thiếu thì dựng lại thẻ từ tên tệp) — không còn đoạn mồ côi vô hình.
- **Extension nhận cả YOUTUBE (anh thêm 07/08 chiều):** cùng cửa `/api/nhan-video`; khác biệt
  ① KHÔNG gửi cookie cho YouTube/TikTok (tài khoản KÊNH + gian hàng — không đem cookie đi tải
  máy cho nền tảng soi; chỉ FB/IG mới kèm cookie vì video cần phiên), ② trần thời lượng nới
  480→900s (highlight trận 10-15 phút tải về để cắt đoạn), ③ YouTube có lượt lùi
  `--extractor-args youtube:player_client=ios` khi bị đòi cookie xác minh bot. Đo thật:
  Shorts 59s về 3,7MB kèm thumbnail + sổ nguồn.
- **Tìm ảnh sai chủ đề vì bộ lọc 2MP (anh bắt bằng ảnh đối chứng 07/08):** "cầu thủ Thái thất
  vọng" ra toàn Hàn/châu Âu vì `islt:2mp` đuổi sạch ảnh báo Việt (~1MP) — Google đắp bằng ảnh
  hãng quốc tế to đùng nhưng lạc đề; anh tìm tay không lọc nên đúng. Đã bỏ 2MP, giữ `itp:photo`,
  thêm `gl=vn`. Đo A/B: lọc cũ top nguồn FB-crawl/Instagram; lọc mới vnecdn 7 + znews 4 +
  sport5 4 — khớp kết quả tay của anh. **Luật: ĐÚNG CHỦ ĐỀ trước, độ nét sau — lọc tại nguồn
  chỉ được lọc thứ không đổi thứ hạng nội dung.** Giá đánh đổi: tỉ lệ đạt-FullHD mỗi lượt tìm
  giảm (ảnh báo VN hay 1200-2000px) — tấm nhỏ hiện "dưới chuẩn" cho người quyết; thấy thiếu
  ảnh nét thì cân nhắc chế độ 2 lượt (lượt thiếu mới kèm lọc to).
- **Cảnh dài tự tách bằng ẢNH PHỤ (anh chốt 07/08 chiều — "cảnh dài phải tách để đưa thêm
  cảnh vào, dù thoại/từ khoá giống nhau"):** trang chọn lấy nhiều tấm → tấm cuối = ảnh chính,
  các tấm còn lại tự thành `anh_phu` của câu (nhập tram.json, /api/gan-phu); xưởng gặp cảnh
  >6s có phụ thì tách đều thành cảnh con ~3-4s chạy lần lượt chính → phụ, DỜI đúng chỉ số
  các cảnh clip phía sau (đã unit-test phép dời). Không phụ thì giữ nguyên + cảnh báo cũ.
  Kèm: số giây mỗi cảnh hiện MÀU VÀNG ở cột câu + dải cảnh trang chọn; câu >6s có nhãn
  "⏳ dài — chọn 2-3 tấm". Sửa lời làm số câu giảm thì anh_phu cũng được dọn theo.
- **Quãng 11 giây "một ảnh đứng suốt" hoá ra là CÂU DÍNH, không phải thiếu ảnh (anh bắt
  07/08 tối: "em kiểm tra lại đúng chưa?").** Phép tách câu không coi `.”` (chấm + đóng
  ngoặc) là kết câu → ba câu trích dẫn dính thành khối 42 tiếng. Bệnh nặng thêm vì phép tách
  bị chép ở BỐN chỗ (trạm, xưởng, goi_y, các tool skill trên Drive). Đã khai MỘT chỗ:
  `duong_dan.TACH_CAU_RE` (kết câu = [.!?…] hoặc [.!?…]+ngoặc đóng), mọi nơi trỏ về; tool
  trên Drive vá qua launchd (bài học phụ: chuỗi thay có `"` trần làm vỡ literal đích —
  phải escape `\"`). Sau vá: 20 câu, dài nhất 6,9s (câu đơn dài thật — ảnh phụ lo).
  **Luật cũ nhắc lại lần 4: con số/phép tính dùng ở hai nơi là phải khai một chỗ.**
- **NHỊP CẢNH CỨNG [2,5s – 5s] + Ô CẢNH PHỤ (anh chốt 07/08 tối, "e làm lại đi"):** bản đầu
  em giấu ảnh phụ sau luồng chọn-nhiều-tấm — anh không THẤY nên coi như chưa làm. Bản đúng:
  câu dài >5s thì trạm SINH Ô CẢNH PHỤ nhìn thấy được ngay dưới câu (9b, 9c — viền vàng, số
  giây từng phần), nhận cả ẢNH (bấm ô rồi bấm kho) lẫn ĐOẠN CLIP (cửa xem đoạn có mục "└ cảnh
  phụ"); giá trị "clip::tệp::từ::đến" trong anh_phu. Xưởng thi hành 3 phép theo thứ tự:
  ① tách cảnh >5s (ceil/5 — phần nào cũng tự nhiên nằm trong [2,5–5]); thiếu phụ thì dùng lại
  ảnh chính nhưng ĐẢO KIỂU chuyển động cho có nhịp cắt; ② cảnh <2,5s mượn giây hàng xóm (giữ
  hàng xóm ≥2,5; KHÔNG mượn xuyên cảnh clip — độ dài clip do anh quyết); ③ còn vụn (kẹt cạnh
  clip) thì GỘP vào cảnh ảnh kề = một ảnh trải hai câu. Unit-test ca khó nhất (11,2s tách 3 +
  vụn 1,3s kẹt cạnh clip): ra [3.0 · 3.73 · 3.73 · 3.73 · 4.8] — sạch khung.
  **Bài học giao tiếp: tính năng người dùng không NHÌN THẤY thì coi như chưa tồn tại.**
- **Hai lỗi CHỐT & DỰNG 07/08 tối (anh bắt cả hai):** ① khoá "NaN" lọt bản đồ vì ô ảnh CẢNH
  PHỤ bị bộ bắt-bấm của ô ảnh thường chụp chung (`stopPropagation` KHÔNG chặn listener cùng
  phần tử — phải `stopImmediatePropagation`); `_nhap` giờ lọc khoá không-phải-số ngay cửa đọc.
  ② **MẤT DỮ LIỆU THẬT**: "Tìm lại" ở trang chọn gửi `/api/luu` kèm cả `ban_do` nó vừa nạp —
  nạp đúng lúc trạm restart nên cầm bản RỖNG, đè trắng 20 câu anh gán. Vá hai lớp: client chỉ
  gửi trường nó muốn lưu; `_luu_nhap` kế thừa trường thiếu VÀ TỪ CHỐI cú lưu đưa ban_do ≥2
  gán về 0 trong một phát (bỏ gán hợp lệ đi từng chiếc). **Luật vàng: API lưu nhận bản-toàn-
  phần từ client là quả bom — mọi trường thiếu phải kế thừa, mọi cú thu hẹp lớn phải nghi.**
- **"Sửa đến đâu giữ công anh đến đó" (anh mắng đúng 07/08 tối, sau vụ mất bản đồ):** quy
  trình vá khi NGƯỜI đang thao tác trên trạm — ① hạn chế kickstart giữa phiên anh làm (trang
  nạp đúng lúc restart là cầm dữ liệu hụt), cần thì báo trước một câu; ② mọi kho trạng thái
  có PHAO: `_luu_nhap` giờ tự giữ `tram.json.truoc` trước mỗi lần ghi — khôi phục 100% trong
  một phút; ③ mất thật thì còn đường KHÔI PHỤC TỪ DẤU VẾT: sổ gắp (so-gap.jsonl) ghi mỗi ảnh
  kèm từ khoá của câu → đối chiếu từ khoá từng câu + mốc giờ tệp là dựng lại được bản đồ
  (07/08 cứu 15/20 câu, câu trùng từ khoá đánh ⚠ cho anh soi).
- **Giọng đọc phải KHỚP LỜI, không phải "có file là dùng" (anh bắt 07/08 tối, mất một lần
  render):** xưởng thấy `giong.mp3` tồn tại là dùng lại — anh sửa lời xong dựng lại vẫn ra
  giọng CŨ. Vá: mỗi lần đọc giọng ghi kèm chính văn bản đã đọc (`giong.mp3.loi`); dựng so
  lời hiện tại với dấu đó, lệch một chữ là đọc lại VBee. Giọng cũ không có dấu → đọc lại cho
  chắc. **Luật chung: cache phải khoá theo NỘI DUNG nguồn, không khoá theo "file đã có".**
- **Gộp Kiểm chính tả vào nút Duyệt lời (anh chốt 07/08 tối) + bug Lưu làm sập khối Content:**
  ① nút ✓ Duyệt lời giờ tự soát chính tả trước (sonnet, báo rõ từng chỗ sửa ngay màn hình)
  rồi mới khoá lời + thả chuỗi — một nút một mạch, nút Kiểm riêng đã bỏ (backend
  /api/kiem-chinh-ta giữ nguyên, chuỗi sau-duyệt vẫn skip nhờ cờ da_soat). ② bug: veLoi gấp
  khối theo da_duyet_loi MỖI Lần vẽ lại — bấm 💾 Lưu (lưu xong nạp lại) là khối sập trước
  mặt anh. Luật: trạng thái gấp/mở do NGƯỜI đặt thì máy chỉ được đổi ở lần vẽ đầu của việc
  (loiDaVe) hoặc đúng hành động duyệt.

## Máy quét lớp phủ trong CLIP trước khi dựng (anh đặt 07/08 tối — chốt sau 5 vòng đo)

- Mọi cảnh clip khi dựng đều qua `_vung_dau_clip`: rút 4 khung của ĐÚNG đoạn lên hình, tìm
  toạ độ bảng tỉ số / logo đài / watermark, trả vùng né → render cắt lệch + zoom cho văng.
- **Kiến trúc 3 tầng bằng chứng** (một tầng đơn lẻ đều bị lừa — đã đo từng ca):
  ① mẫu DẤU NGUỒN trong chữ OCR (tên đài/@/.vn) → né ngay;
  ② MẮT TĨNH: pixel vừa ĐÓNG BĂNG (std<5 qua 4 khung) vừa CÓ NÉT (gradient>12), đếm CỤM
    theo vùng — ≥100 pixel-phủ (khung 160×90) là lớp phủ. Số đo: vùng có logo 169–373,
    vùng sạch ≤42 (cỏ phẳng đóng băng nhưng không nét; nhà flycam có nét nhưng nhúc nhích);
  ③ chữ-lặp ≥3/4 khung chỉ được né khi mắt tĩnh GẬT vùng đó (rác OCR trên cỏ cũng lặp
    y hệt nhau!). Mắt tĩnh mù (clip đứng im, lech<4) → chỉ tin ①, thà sót còn hơn né oan.
- Caption GIỮA KHUNG không né nổi bằng cắt — chỉ in cảnh báo cho anh cân nhắc đổi đoạn.
- Không rút được khung → BỎ QUÉT + KHÔNG cache (bài học: lượt hỏng từng cache [] thành
  "sạch dởm"; và harness test launchd phải khai PATH — không thì ffmpeg chết im, quét mù).
- Đối chứng dương cuối: clip giả (logo VTV3 + bảng tỉ số) → bắt đúng 3 vùng; hai đoạn thật
  sạch → 0 vùng, không né oan.
- **Hai bệnh lộ khi anh chạy thật 07/08 đêm:** ① Chrome trạm TỰ CẬP NHẬT giữa phiên
  (150→151) làm thẻ CDP của tiến trình trạm thành THẺ MA — job tìm sẵn treo "1/21" mười
  phút; đường tìm test từ tiến trình mới chạy 3,6s → thuốc là kickstart trạm. Nghi treo
  kiểu này: soi version Chrome có nhảy số không. ② Google hỏi CAPTCHA mà máy ĐẬP TIẾP 10
  câu liên tục → càng bị khoá gắt. Đã vá: gặp CAPTCHA là DỪNG CẢ LOẠT + ghi lý do từng câu;
  thêm giãn nhịp người thật 2,5–6s giữa các lượt tìm. Luật CAPTCHA giữ nguyên: máy không
  bao giờ tự giải — chỉ người giải ở cửa sổ Chrome trạm.
- **Cửa "➕ Bài mới" (anh chốt 07/08 đêm — "GPT đang viết hay hơn em"):** anh dán TÍT + LỜI
  từ bất cứ đâu (GPT, tự viết, báo) → `/api/bai-moi` tạo việc mới trong ngày (video-N-slug,
  kich-ban dat=true, cụm vàng rỗng để chuỗi haiku tự chọn, cảnh báo "bài đưa từ ngoài —
  máy chưa kiểm tư liệu"), đặt luôn làm việc đang-mở rồi nhảy tới. Từ đó đi nguyên dây
  chuyền cũ: Duyệt lời → chính tả → từ khoá → tìm sẵn → chọn ảnh → dựng. Bài anh dán +
  duyệt cũng vào sổ học như mẫu văn anh ưng — nguồn học quý không kém vết sửa.
  · Vá bồi 07/08 đêm: mở CỬA NHẬP mới thì phải đi kiểm CẢ CHUỖI HẠ NGUỒN — bài-tay đầu tiên
  của anh dựng xong, bấm Kho là sập vì buoc3_xepkho đòi tin-goc.json. Nay: bai-moi tự tạo
  tin-goc tối thiểu, VÀ xếp kho chịu được thiếu file (bản tối thiểu từ kich-ban).
- **Ảnh ĐỒ HOẠ BẢNG BIỂU máy tự nhận, ép VỪA KHUNG (anh bắt 08/08: BXH bị zoom mất cột tên
  đội + cột điểm):** nhận bằng độ TẬP TRUNG MÀU — đồ hoạ nền phẳng: top-8 màu ≥80% (đo thật:
  BXH 98%/57 cụm, ảnh chụp 39–58%/123–241 cụm). `chuyen_dong.la_do_hoa_bang` khai một chỗ;
  xưởng ép kiểu "vua", bảng THẮNG cả phép né watermark lẫn phép cân-kiểu-65%. Cách người chỉ
  tay (cach-hien) vẫn đứng trên tất cả.
  · Vá bồi 08/08: ảnh anh chụp "vẫn lỗi" hoá ra là BẢN DỰNG CŨ trong cache trình phát —
  khung 53s bóc từ file thật đã chuẩn; trước khi tin "vá chưa ăn" phải BÓC KHUNG TỪ FILE
  hiện tại mà đối chứng. Và lộ bug ngầm: cach-hien ghi theo TÊN GỐC, chon/ đánh số lại →
  chỉ-định-kiểu chưa bao giờ khớp khoá ở bài đã chốt. Vá: _duyet ghi `ten-goc-chon.json`
  (tên mới → gốc), xưởng tra hai nấc; đã backfill bài 08/08.


## Đồ hoạ AI phải nhận bằng HAI mắt: màu dồn + cạnh sắc (08/08/2026)
Anh bắt: ảnh đồ hoạ AI (4 cúp "6 LẦN Á QUÂN", 1536×1024 cỡ máy sinh) bị cắt mất chữ khi
render. Gốc: mắt "màu dồn top-8 ≥80%" chỉ bắt được đồ hoạ NỀN PHẲNG (BXH 92–99%); đồ hoạ
AI có gradient + ảnh lồng chỉ dồn 71–79% → trượt → bị coi là ảnh chụp → kiểu zoom cắt mép.
Vá trong chuyen_dong.la_do_hoa_bang: thêm mắt CẠNH SẮC (chữ/viền tạo cạnh gắt 8,6–15,6%
điểm ảnh vs ảnh chụp 1,3–5,7%) — màu ≥65% VÀ cạnh ≥7% cũng tính đồ hoạ. Phải đủ CẢ HAI vế:
ảnh khán đài đông người cạnh sắc 11% nhưng màu 28% — một mắt là ép vua nhầm.
Bài học chung: ngưỡng nhận dạng phải đo trên MẪU THẬT ĐA DẠNG (bảng phẳng + đồ hoạ AI +
ảnh chụp), một con số cắt đôi thế giới thì sớm muộn cũng gặp ca nằm giữa.
Bổ sung cùng ngày: thêm cửa ③ màu ≥55% VÀ cạnh ≥10% cho ĐỒ HOẠ LAI ẢNH THẬT (n31: 4 cúp
+ nửa khung cầu thủ, màu chỉ dồn 59%) — cửa ② bỏ sót vì ảnh thật chiếm nửa khung kéo màu
loãng. Screenshot bài báo cũng lọt cửa ③, chủ đích: zoom là mất tít.

## Cổng QC phải đứng TRƯỚC cửa kho (08/08/2026 — vụ hộp 04 dở dang)
Xếp kho bản cũ TẠO HỘP + GHI SỔ "cho-dang" rồi mới chạy cổng QC — QC chặn là để lại hộp
3 tệp + dòng sổ rác mà bot đăng sẽ tưởng hàng thật. Đã đảo: QC đạt mới tạo hộp/ghi sổ.
Bài học chung: bước nào có thể CHẶN thì phải đứng trước mọi bước GHI DẤU VẾT (tạo thư mục,
ghi sổ) — không thì mỗi lần chặn là một bãi rác phải dọn tay.
Kèm luật thẻ: cảnh có thẻ số liệu → kiểu vừa-khung tự đẩy ảnh lên né dải thẻ (930–1270)
nếu đáy ảnh thò vào, chừa trần 30px; không thò thì giữ nguyên.

## Nút Kho chậm: dời QC về cuối xưởng + hộp gọn (anh kêu 08/08/2026)
Nút Kho vốn làm tuần tự: SEO haiku (nếu bài thiếu tags/ghim, 10–30s) → cổng QC quét cả
video (~20–40s) → chép 18MB lên Drive → thumbnail. Vá: cổng QC chạy NGAY CUỐI xưởng
(dựng vốn vài phút, cõng thêm QC không ai cảm nhận; PNG cũ bị xoá trước khi soi bản mới),
nên bấm Kho chỉ còn SEO-1-lần + chép tệp. Hộp xuất bản bỏ thumbnail.jpg + qc.png (anh
không dùng — TEP_CHUAN còn 5 tệp); cổng QC vẫn CHẶN như cũ, ảnh chứng cứ nằm ở thư mục
việc trên DATA.

## Cảnh báo QC phải ĐẾN MẮT anh, không nằm trong stdout (anh hỏi 08/08/2026)
Cổng QC có 3 mức: ❌ CHẶN (exit 1 — nút Kho hiện banner đỏ) · ⚠️ ĐẠT CÓ ĐIỀU KIỆN
(exit 0, chỉ in stdout → TRƯỚC GIỜ BỊ NUỐT, anh chưa từng thấy) · ✅ ĐẠT. Đã vá: QC chạy
cuối xưởng, mức ⚠️/❌ nhắn thẳng Tele kèm đường ảnh chồng. Bài học: "phát hiện mà cảnh báo
không đến mắt người thì bằng không phát hiện" — mọi cổng chặn mới phải trả lời câu
"ai THẤY kết quả này, ở đâu?" ngay lúc thiết kế.

## QC dồn về TRƯỚC CHỐT, sau đó dựng một mạch (anh chốt 08/08/2026 — lần 2 trong ngày)
Anh đổi kiến trúc QC: bỏ quét video thành phẩm (20–40s/lần) lẫn quét ở nút Kho — mọi cảnh
báo dấu nguồn dồn về HỘP KIỂM TRƯỚC DỰNG trên trạm (client tổng hợp từ nhãn 🔴🟡 của sổ
cổng vào, chỉ hiện khi CÓ gì đáng ngờ), anh pass là chạy thẳng: dựng → kho không quét gì
nữa. Chất lượng dựa 3 tầng còn lại: cổng VÀO từng tài nguyên lúc gắp + máy né vùng dấu
nguồn khi render + mắt anh ở hộp kiểm. Kèm: preset nén cuối slow→medium (CRF giữ 20) —
nhanh gần gấp đôi khâu encode, chất lượng hình coi như không đổi.
Bài học nhịp làm: cùng một cổng QC, sáng anh muốn "cảnh báo phải đến mắt", chiều muốn
"nhanh là ưu tiên" — cứ làm đúng yêu cầu mới nhất nhưng GIỮ các tầng chặn không tốn giờ.

## Thẻ đã BỎ vẫn bị vẽ thành khung rỗng (anh bắt 08/08/2026)
Trạm ghi cờ {bo_the: true} khi anh bỏ thẻ (cố ý giữ dấu để máy gợi không đè thẻ mới vào
câu anh đã từ chối) — nhưng xưởng không biết cờ, thấy có mục là vẽ → khung viền vàng
RỖNG RUỘT chồng lên ảnh. Vá: xưởng lọc the_so MỘT lần (bỏ bo_the + thẻ rỗng ruột) rồi
cả vòng vẽ PNG lẫn vòng ghép filter dùng chung danh sách đó — lọc lệch nhau giữa hai
vòng là filter tham chiếu thẻ không tồn tại, ffmpeg sập.
Bài học giao ước dữ liệu: cờ trạng thái do MỘT bên đặt ra (trạm) thì MỌI bên đọc sổ
(xưởng, máy gợi) phải được dạy về nó ngay lúc đặt — không thì cờ thành bẫy.

## Lật ảnh mặc định + cảnh đôi (anh đặt 09/08/2026)
· LẬT trái-phải mặc định mọi cảnh ảnh CHỤP (né trùng nội dung) — sổ lat_anh chỉ ghi câu
  anh TẮT (nút ↔ trên hàng câu). BA lớp không lật: đồ hoạ/bảng (kiểu vua/doc), ảnh chụp
  có CHỮ TO trong khung (tra OCR sẵn của cổng vào — ca CHAMPIONS lật ngược bắt được ngay
  ở lần thử đầu), và câu anh tắt tay. Vùng né watermark LẬT THEO ảnh (lat_vung đổi
  trái↔phải) — quên là né hụt. Clip KHÔNG lật (chưa làm).
· CẢNH ĐÔI (nút ⿻): ảnh chính + ảnh phụ ô 1 chia đôi khối ảnh trên/dưới theo mẫu đối đầu
  kênh dẫn đầu; bấm lần 2 đảo trên/dưới, lần 3 tắt. Cảnh dài tách phần thì mọi phần dùng
  cùng cặp (chiều zoom đổi), ảnh phụ ô 2+ không dùng — log nhắc. Khâu tách cảnh phải BIẾT
  câu ghép để không lấy mất phụ ô 1 (ghep_som đọc trước ③đ).
Bài học: chức năng "mặc định bật" phải đi kèm danh sách ca KHÔNG ĐƯỢC bật do máy tự nhận —
người chỉ xử ngoại lệ cuối cùng.

## Vân tay ảnh chống trùng ở MỌI cửa nhận (anh bắt 09/08/2026)
Cùng một ảnh vào kho nhiều lần (2 lượt tìm, 2 nguồn, extension gửi lại) mà không ai bắt.
Vá: dHash 64-bit (9×8 xám, so sáng-tối cặp điểm kề — cùng ảnh khác cỡ/nén vẫn ra vân gần
nhau, khác ≤6 bit = trùng), sổ van-tay.json cạnh ảnh, tự bổ sung vân cho ảnh cũ + dọn mục
chết mỗi lần nạp. Chặn ở CẢ hai cửa: _tai_mot (tìm/lấy về kho — tải 8 luồng song song nên
phải khoá sổ) và nhan_tep (extension + kéo thả — trùng thì báo về danh sách hỏng với tên
ảnh gốc). Đã dọn 14 ảnh trùng tồn đọng trong 5 việc, remap ban_do/anh_phu về tấm giữ.
Bài học: kho nào có NHIỀU CỬA NHẬN thì phép kiểm trùng phải nằm ở tầng ghi-vào-kho dùng
chung, không nằm ở từng cửa.

## Khung đôi + lật nâng thành PER-Ô — chính/phụ độc lập hoàn toàn (anh chốt 09/08/2026)
Anh sửa thiết kế: "cảnh chính có nút gì, cảnh phụ có nút đó" — mỗi Ô (chính "c", phụ "0"/"1"…)
tự mang: nút ↔ lật riêng (sổ lat_anh key "cau" / "cau:j"), nút ⿻ khung đôi riêng với ẢNH
THỨ HAI của chính nó (ghep_canh = {câu: {ô: {anh2, dao}}}; luồng: bấm ⿻ → ô nhấp nháy chờ
→ bấm ảnh trong kho → thành anh2). Xưởng: ③đ build o_cua (cảnh video → ô nguồn) chạy song
song canh/xep, gộp vụn phải del/remap o_cua cùng nhịp — lệch một chỗ là ghép sai ô.
MỌI nút phải có title tiếng Việt đầy đủ — trạm sẽ có nhân viên vận hành, không phải mình anh.
HẠN CHẾ ĐÃ BIẾT (nói thật với anh): mắt chống-lật-chữ chỉ tra OCR vùng RÌA của cổng vào —
TÊN/SỐ ÁO nằm giữa ảnh đội hình vẫn bị lật ngược; anh thấy ngứa mắt thì tắt ↔ ô đó.
Bài học: yêu cầu "A ghép với B" hôm trước có thể thành "A và B mỗi người tự ghép" hôm sau —
thiết kế data theo Ô/đơn vị nhỏ nhất ngay từ đầu thì lần đổi sau chỉ là thêm key.

## Một nút KHÔNG gánh ba việc (anh bắt 09/08/2026)
Nút ⿻ vòng 3 trạng thái bật→đảo→tắt: anh bấm lần 3 định đảo lại thì mất ảnh thứ hai —
"tự xoá ảnh". Tách: ⿻ chỉ BẬT/TẮT (tắt vẫn giữ anh2 trong sổ, cờ "tat", hiện ⿻· để biết
còn nhớ ảnh), ⇅ riêng chỉ ĐẢO trên/dưới (bấm mãi cũng chỉ đổi chỗ). Xưởng phải đọc cờ tat.
Kèm: cửa xem ảnh TO lật theo cờ lật của ô mở nó (moSoi(k, lat)) — xem trước phải đúng
chiều sẽ lên hình, không thì duyệt một đằng dựng một nẻo.
Luật giao diện: thao tác PHÁ (xoá/tắt) không được nằm cùng nút với thao tác SỬA, và không
bao giờ là "bấm tiếp lần nữa" của một chuỗi — người bấm nhanh sẽ mất dữ liệu.

## Khung đôi: rà 7 lỗi dễ gặp một lượt (anh bắt "xoá 1 bay cả 2" 09/08/2026)
Gốc vụ chính: xoá ảnh GỐC của ô đang ghép → cấu hình khung đôi mồ côi, UI không còn chỗ
hiện ảnh thứ hai → nhìn như mất cả cặp. Luật "XOÁ 1 CÒN 1": xoá ảnh gốc thì ảnh thứ hai
ĐÔN LÊN thay (cả ô chính lẫn ô phụ). Kèm 6 bẫy cùng họ vá một lượt: chặn chọn ảnh thứ hai
trùng ảnh gốc; vứt ảnh khỏi kho thì gỡ mọi khung đôi trỏ vào nó; đổi việc reset trạng thái
chờ-gán; ô chứa CLIP không cho bật khung đôi; ảnh phụ + ảnh khung đôi mang nhãn "đang dùng"
trong kho (Nᵖ/N⿻) cho nhân viên khỏi vứt nhầm.
Bài học rà lỗi: một tính năng mới đụng DỮ LIỆU THAM CHIẾU (A trỏ B) thì phải rà đủ vòng
đời của B: B bị xoá? bị thay? trùng A? người đổi ngữ cảnh giữa chừng? — chứ không chỉ
đường đi xuôi.

## Lật ảnh: anh đổi mặc định thành KHÔNG lật (09/08/2026 chiều)
Sáng đặt "mặc định lật để né trùng", chiều anh đổi: MẶC ĐỊNH GIỮ NGUYÊN chiều, ô nào muốn
lật thì bấm ↔ bật (nút sáng vàng khi đang lật, sổ lat_anh ghi true cho ô bật). Sổ cũ ghi
false vẫn đọc đúng nghĩa. Máy vẫn tự KHÔNG lật đồ hoạ/ảnh có chữ dù ô được bật.

## Tiêu điểm ở lại đúng ô vừa đụng — lần 2 (09/08/2026)
Bấm ⿻ ở cảnh 11 → trang nhảy về cảnh 1: veCau cuộn về `.dang` (dangChon) mà 4 nút mới
(↔/⿻/⇅/ô ảnh 2) không đặt lại dangChon. Đúng bệnh 05/08 tái phát khi thêm nút mới.
Vá: helper tieuDiemO(cau, o) gọi ĐẦU mọi handler nút per-ô. LUẬT CỨNG: thêm bất kỳ nút
nào vào hàng câu là dòng đầu handler phải đặt tiêu điểm — không có ngoại lệ.

## Tự test UI bằng Chrome trạm trước khi giao (anh dặn 09/08/2026: "cứ để a làm rồi mới
## phát hiện ra thế này ko ổn")
Quy trình đã dựng và PHẢI chạy sau mỗi đợt sửa UI đáng kể: nhân bản một việc cũ thành
zz-test-ui → mở trạm qua cdp.Tab (Chrome 9334) → chạy kịch bản thao tác thật (bấm nút,
gán ảnh, xoá, đảo, chuyển việc) → kiểm state + scroll + console error từng bước → xoá bài
test. Lần đầu chạy 24/24 pass. Kèm phanh server mới: _giu_neu_quet_trang cho lat_anh +
ghep_canh (trang nạp hụt gửi sổ rỗng không được quét sạch cấu hình — cùng họ vụ mất 20
câu 07/08). Nguyên tắc: lỗi phải do MÁY tìm ra trước, anh chỉ nghiệm thu.

## Nhịp cảnh về MỘT nguồn: nhip_canh.py (anh chốt 09/08/2026)
Anh bắt: cảnh 0,9s hiển thị trơ trọi + ô phụ ẩn im lặng — vì trạm chia đều thô còn xưởng
co giãn kiểu riêng (bệnh "một logic hai bản" lần 4). Luật anh: "cắt giờ cho cảnh ngắn đủ
2,5s TRƯỚC, còn lại mới chia đều cho các khung". Module ~/socbongda247/nhip_canh.py giờ là
nguồn chân lý duy nhất: ① số khung theo độ dài GỐC (ceil/5 — khớp số ô anh gán), ② câu hụt
mượn hàng xóm sát cạnh (không mượn của clip, hàng xóm giữ ≥2,5×số khung), ③ chia xong khung
hụt thì bớt khung; tổng luôn bảo toàn. Xưởng ③đ và server _chi_tiet cùng import — trạm thấy
gì xưởng dựng đúng cái đó (đối chứng cùng ca: trạm 2,5/8,7·3 khung = log xưởng y hệt).
Ô phụ gán DƯ số khung: HIỆN MỜ nhãn "Ô DƯ" chứ không ẩn — dữ liệu người gán không bao giờ
biến mất im lặng khỏi mắt họ.

## Crop tại chỗ + cửa phóng thành bàn duyệt liền mạch (anh đặt 09/08/2026)
· KHO: cửa soi có ✂ Crop (C) — kéo chọn VÙNG GIỮ, Enter cắt; server giữ BẢN GỐC NHẤT ở
  anh/_goc-crop/ nên ↩ Hoàn (U) luôn về nguyên thủy dù cắt bao nhiêu lần; ảnh cắt đè
  CÙNG TÊN nên mọi tham chiếu tự theo; _don_sau_doi_anh xoá thumb + vân tay cũ (quên là
  thumbnail hiện bản cũ + máy chống trùng cầm vân ma).
· TRANG CHỌN: phóng to có ‹ › (←/→) + ✂ ghi VÙNG THEO URL (badge ✂ trên tile), server cắt
  ngay lúc tải về (crop chủ đích bỏ cổng cỡ/tỉ lệ như tu_chon, sàn 300px); cửa phóng hiện
  CHỮ CẢNH đang focus, Enter = tấm đang phóng thành ảnh chính → tự sang cảnh kế + chữ mới.
· Anh BỎ "Ô DƯ" cùng ngày (không yêu cầu mà tự bày — dễ nhầm): chỉ hiện đúng số khung,
  ảnh phụ dư vẫn nằm sổ chờ lời dài ra. Bài học: tính minh bạch dữ liệu KHÔNG được trả
  giá bằng rối giao diện — thứ người không cần thấy thì đừng bày, chỉ cần không mất.
· Test CDP bắt được lỗi thật (e.target.matches nổ với phím bắn từ document) — giữ nết
  test bằng máy trước khi giao.

## "Test kỹ chưa?" — câu hỏi đó chính là một lượt test (09/08/2026)
Anh hỏi lại một câu, rà thêm vòng nữa ra 2 lỗi thật chưa phủ: ① crop vẽ trên ảnh ĐANG LẬT
phải soi gương vùng trước khi gửi server (không thì cắt lệch gương); ② ảnh đã crop phải
đánh dấu da_crop vào sổ nguồn để xưởng THÔI né vùng watermark cũ (toạ độ theo ảnh trước
khi cắt — vô nghĩa, thường watermark chính là phần đã cắt bỏ). Kèm bịt 2 lỗ test:
crop-lúc-tải end-to-end (gốc 2200×1517 → đúng 1100×758) và crop-qua-API rồi DỰNG trọn bài.
Luật test bổ sung: tính năng chạm ẢNH phải test giao với MỌI biến đổi ảnh đang có
(lật, né vùng, vân tay, thumbnail) — không chỉ test tính năng đứng một mình.

## Cảnh báo trước chốt phải nói cùng ngôn ngữ với hệ đang chạy (anh bắt 09/08/2026)
Dialog chốt kêu "đoạn 0–6,4s một ảnh đứng suốt" trong khi câu đó có cả khung đôi lẫn cảnh
phụ — vì máy soi dùng chia_nhip_theo_anh ĐỜI TRƯỚC (chưa biết cảnh phụ/khung đôi/mượn giây).
Viết lại thành _soi_canh_bao_nhip: hàm THUẦN (không đọc đĩa) tính trên nhip_canh + anh_phu
+ ghep_canh + clip; chỉ kêu khi quãng MỘT-HÌNH thật sự >6s (gộp cả chuỗi câu kế thừa cùng
ảnh), khung đôi tắt vẫn tính là một hình. Test 2 chiều: bài thật hết kêu oan + 6 ca giả
cảnh báo thật vẫn bắt đủ.
Bài học lặp lần 5 của "một logic hai bản": NÂNG CẤP hệ nhịp thì phải grep MỌI nơi còn gọi
hàm nhịp đời cũ (chia_nhip_theo_anh) — cảnh báo/soi trước là chỗ dễ quên nhất vì nó không
làm hỏng video, chỉ nói sai.

## Khung đôi: mép nối hoà tan (anh nâng cấp 09/08/2026 chiều)
Hai nửa khung đôi trước dán cạnh cứng — anh muốn "không có cảm giác ranh giới". Vá trong
render_ghep_doc: mỗi nửa cắt CAO THÊM nửa dải (~120px, min(120, nua//3)) để CHỒNG LẤN,
ảnh trên đè lên ảnh dưới bằng mặt nạ gradient 255→0 trong dải — hai ảnh tan vào nhau.
Mặt nạ build một lần bằng bytes (không numpy), zoom ngược chiều hai nửa giữ nguyên.

## Kho chỉ nhận video TOÀN VẸN (anh dính 09/08/2026: bấm Kho lúc xưởng đang dựng)
Bấm Kho đúng lúc xưởng đang encode → chép file GHI DỞ (7,9MB thiếu moov) lên Drive,
QuickTime không mở nổi. Ba phòng tuyến mới trong buoc3, đứng TRƯỚC khi tạo hộp:
① pgrep xuong.py — xưởng đang chạy là DỪNG (kèm lời nhắn chờ); ② ffprobe bản nguồn
(duration ≥3s mới nhận); ③ chép xong ffprobe LẠI bản trong hộp, lệch >0,5s là báo
Drive chép lỗi. Hộp 03 hỏng đã thay video lành (57,5s khớp hai đầu).
Bài học: file ĐANG GHI cũng là một trạng thái dữ liệu — mọi cửa CHÉP/ĐÓNG GÓI phải hỏi
"nguồn có đang bị ai ghi dở không, bản chép ra có đọc lại được không".

## Watermark xoay đi lên tuỳ chỉnh (anh chốt 09/08/2026)
"SÓC BÓNG ĐÁ 247" giờ XOAY ĐI LÊN về phải, cấu hình LAYOUT["watermark_goc"] trong template
(nguồn chân lý bố cục, mặc định 10°; 0 = ngang như cũ); ghi đè riêng từng bài bằng
"goc_watermark" trong kich-ban.json (xưởng truyền qua lam_overlay). Xoay SAU phép nghiêng
italic, neo ĐÁY-PHẢI giữ nguyên nên đổi góc không trôi vị trí.

## Thẻ TỶ SỐ TRẬN kính mờ (anh đặt 09/08/2026 theo mẫu "HẾT GIỜ")
Loại thẻ mới loai="ty_so" đi trọn dây chuyền: ① lam_the_ty_so trong the_so_lieu.py (Drive)
— khung bo tròn nền tối bán trong suốt (spec["mo"] 0–1, MẶC ĐỊNH 0.74 — 0.62 đo thử còn
trong quá chữ khó đọc trên cảnh sáng), vạch vàng đỉnh, tiêu giãn ký tự, cờ TRÒN flagcdn
viền sáng (cache flags-cache/), tỷ số 118px "3 – 1", ghi bàn ≤3 dòng/đội, CAO ĐỘNG theo
số dòng; ② goi_y_the tự đề xuất khi bài có trận + tự bóc đội/cờ/tỷ số/ghi bàn — cửa kiểm:
tên đội phải có trong bài (loại cả thẻ nếu bịa), tỷ số nguyên văn, mục ghi bàn không có
gốc trong bài thì BỎ MỤC (test: giữ Đình Bắc/Vakhim thật, loại "Bịa Tên", chặn 5-0);
③ xưởng neo ĐÁY mọi thẻ y=1300 (thẻ cao thấp khác nhau, neo đỉnh là tràn xuống tít) +
vùng né thẻ nở (860,1310) khi bài có ty_so + bộ lọc thẻ-rỗng phải hiểu ruột ty_so;
④ trạm: hộp thẻ 2 chế độ (Số liệu / ⚽ Tỷ số trận) + thanh kéo mờ⟷đặc, nút hàng câu hiện
"⚽ 3-1 (VIỆT NAM)".
Bẫy đã né: ví dụ JSON trong f-string PHẢI {{ }} — ast.parse pass mà runtime nổ NameError
(identifiers tiếng Việt parse được thành biểu thức so sánh!); test build prompt bằng mock
subprocess mới bắt được.

## Bài PVF: tài nguyên khan hiếm thì ĐÀO KHO NHÀ trước (09/08/2026)
Anh đưa content sẵn, than "tài nguyên lấy khó, không đúng, khan hiếm". Lời giải: ①BÓC KHUNG
từ video PVF kênh tự dựng trước đó (demo kỹ thuật + bản 60s cũ), crop bỏ dải logo+tít
(0,265,1080,1235) → 14 ảnh công trường chính chủ sạch bản quyền — thứ Google không có;
②tái dùng ảnh ĐÃ DUYỆT từ việc cũ (CĐV, đội tuyển); ③Google chỉ gắp phần thế giới có sẵn
(National Stadium, Mỹ Đình). Model dùng đúng chỗ: em (phiên) chỉ map ảnh↔câu bằng mắt,
thẻ tự khai bằng tay từ số trong bài (0 token sinh), pipeline gợi ý không cần gọi.
Toàn tuyến qua API trạm: bai-moi → tai-len (base64, dedup vân tay chặn 1 trùng) → gap →
duyet → dung → xep-kho. Video 64,4s có thẻ 60% + thẻ mái 12-20 PHÚT + khung đôi PVF/NS.
