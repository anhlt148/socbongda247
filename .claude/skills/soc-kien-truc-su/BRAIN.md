# BRAIN — kiến trúc sư trưởng hệ Sóc
> Viết theo lối **bệnh → gốc → cách phòng**. Chỉ ghi thứ đã TRẢ GIÁ THẬT.

### 11. Trường blueprint KHÔNG AI SINH — hỏng câm hàng tuần (12/08/2026)
- **Bệnh**: nhạc nền mọi video giống nhau, không ai để ý suốt nhiều tuần.
- **Gốc**: `xuong.py` đọc `kb.get("cung_nhac") or "cang_thang"`. Trường `cung_nhac` chưa
  bao giờ được sinh ra — cả trạm lẫn skill đều không ghi. Dấu `or <mặc định>` **nuốt trọn
  lỗi**: không nổ, không cảnh báo, chỉ lặng lẽ dùng mặc định mãi mãi.
- **Phòng**: mọi chỗ `kb.get(X) or <mặc định>` phải trả lời được "AI GHI X vào sổ?" — không
  chỉ ra được người ghi thì đó là **code chết, không phải tính năng**. Cách chữa: hàm chọn
  phải trả kèm `vi_sao` và IN RA LOG, để nhìn log là biết đang chạy nhánh nào.

### 12. Khớp chuỗi trần trên tiếng Việt bỏ dấu (12/08/2026)
- **Bệnh**: tin "MALAYSIA KHÔNG THỂ DÙNG CHẢO LỬA" được gán nhạc HÀI HƯỚC.
- **Gốc**: từ khoá `"lay"` (lầy) khớp lọt trong "ma**lay**sia". Bỏ dấu xong tiếng Việt đụng
  nhau dày đặc: `khẩn`↔`khán giả`, `nóng`↔`nông`.
- **Phòng**: ① khớp theo **ranh giới từ** (`(?<!\w)…(?!\w)`), cấm `in` chuỗi trần;
  ② từ khoá viết **CÓ DẤU**, bản bỏ dấu chỉ làm dự phòng khi lượt có dấu không ra gì.

### 13. Nhãn phân loại phải là CẢM XÚC, không phải CHỦ ĐỀ (12/08/2026)
- **Bệnh**: nhóm PATRIOTIC hút gần hết video vì từ khoá có "tuyển Việt Nam".
- **Gốc**: kênh nào cũng nhắc tuyển VN — đó là **chủ đề**, có mặt ở mọi bài, nên vô dụng để
  phân biệt. Cảm xúc mới là thứ phân biệt: "tự hào", "vinh quang", "nức lòng".
- **Phòng**: khi lập bộ từ khoá phân loại, hỏi "từ này có xuất hiện ở CẢ NHÓM KHÁC không?"
  Có thì nó là chủ đề, phải loại. Tên đội/giải/cầu thủ tuyệt đối không làm từ khoá cảm xúc.

## Bốn lần làm gãy đồ đang chạy (11/08/2026, một đêm)

### 1. Route trùng tên — lỗi CÂM
- **Bệnh**: nút 📦 Kho báo hỏng, trong khi script đóng gói chạy tay vẫn tốt.
- **Gốc**: em thêm `/api/xep-kho` cho máy-xếp-nghĩa, trong khi đã có `/api/xep-kho` là
  đóng gói video. Cùng `do_POST`, route mới đứng trước **nuốt hết**.
- **Phòng**: `grep` tên trước khi đặt. Cổng ②d trong `kiem_tram.py` quét route trùng
  (cùng đường khác GET/POST là hợp lệ — chỉ báo khi trùng trong cùng method).

### 2. Import trong thân hàm — `UnboundLocalError` (gãy 3 lần)
- **Bệnh**: cửa nhận ảnh của extension chết câm.
- **Gốc**: `import base64` trong một nhánh `do_POST` biến `base64` thành biến cục bộ CẢ
  HÀM; nhánh khác dùng trước là nổ.
- **Phòng**: đừng import trong thân hàm; bí thì `import shutil as _sh`. Cổng ②a quét.

### 3. Quên cảnh phụ (anh dặn 4 lần)
- **Bệnh**: bốn tính năng mới (máy xếp nghĩa · gán nháp · ứng viên cảnh · gán nhanh)
  đều chỉ làm cho cảnh chính.
- **Gốc**: em nghĩ theo "câu" thay vì theo "ô".
- **Phòng**: khái niệm **Ô = (câu, phần)**, mã `"3"` / `"3:0"`. Cổng tầng ⑤ canh từng
  tính năng. *Luật nằm trong đầu thì quên; nằm trong cổng thì không.*

### 4. Rút gọn UI làm mất thông tin trạng thái
- **Bệnh**: anh tưởng nút Mở trỏ sai ổ đĩa.
- **Gốc**: nút có hai trạng thái (đã xếp kho → Drive · chưa → DATA), chữ nút chính là
  thứ phân biệt; em gộp thành "📂 Mở" cho gọn.
- **Phòng**: rút gọn chỉ cắt phần thừa, không cắt phần phân biệt trạng thái.

### 5. Nhãn nút TRÙNG với nút khác (11/08/2026)
- **Bệnh**: hai nút "📦 Kho" nằm cạnh nhau trên thanh trên — anh bấm nhầm.
- **Gốc**: sửa lỗi trước (nút phải nói rõ trạng thái) em chọn nhãn "📦 Kho", không để ý
  nút xếp kho ngay bên cạnh đã mang đúng nhãn đó.
- **Phòng**: nhãn nút phải thoả **hai** điều — phân biệt được TRẠNG THÁI của chính nó,
  và KHÔNG trùng nhãn nút hành động khác trong cùng thanh. Sửa xong một lỗi UI thì liếc
  cả hàng nút bên cạnh, đừng chỉ nhìn nút mình vừa sửa.

### 6. Grid cột cứng làm rớt hàng (11/08/2026)
- **Bệnh**: nút 🏠 chiếm trọn một hàng riêng, khối công cụ mỗi cảnh phình 204px.
- **Gốc**: `.hang-o` khai `grid-template-columns: 1fr auto` = 2 cột, mà hàng đầu có 3
  phần tử → phần tử thứ 3 tự rớt xuống hàng mới (grid không báo lỗi, chỉ lặng lẽ xuống dòng).
- **Phòng**: hàng công cụ có số phần tử THAY ĐỔI thì dùng **flex**, đừng dùng grid cột
  cứng. Và luôn **đo trước** (đếm px từng hàng) mới biết mình đang mất bao nhiêu chỗ.

### 7. Thêm LOẠI mới mà quên sửa chỗ GHI (11/08/2026)
- **Bệnh**: máy gợi ra thẻ tỷ số đầy đủ, nhưng vào sổ thành thẻ rỗng — nút hiện mỗi "◌",
  bấm chốt không có gì để chốt.
- **Gốc**: hệ có HAI loại thẻ (số thường · tỷ số) nhưng đoạn ghi vào sổ chép CỨNG 5 trường
  của loại cũ. Thêm loại mới ở chỗ SINH mà quên chỗ GHI.
- **Phòng**: dữ liệu có nhiều LOẠI thì mọi cửa (sinh · ghi · đọc · vẽ · sửa) đều phải rẽ
  nhánh theo loại. Thêm loại mới thì grep tên loại đó, đếm đủ số cửa.
- **Bẫy kèm**: server đã `import` module skill vào bộ nhớ — vá file skill xong phải
  **restart trạm** mới ăn, không thì test lại vẫn ra kết quả cũ và tưởng vá hỏng.

### 8. Mã Ô có hai dạng — `int()` thẳng là nổ (11/08/2026)
- **Bệnh**: dải kho nhà trả 500 câm, cả lượt model xếp kho mất trắng, tiến độ gán nổ giữa
  chừng. Ba chỗ khác nhau, cùng một dòng lệnh: `int(k)` với `k = "3:0"`.
- **Gốc**: hệ có HAI dạng mã ô — `"3"` (cảnh chính) và `"3:0"` (cảnh phụ). Hôm thêm ô phụ
  vào máy xếp kho chỉ sửa chỗ SINH mã, không rà chỗ TIÊU THỤ mã. Cùng họ với bài học #7
  (thêm loại thẻ mà quên chỗ ghi).
- **Phòng**: muốn số câu thì `k.split(":")[0]`; muốn in cho anh xem thì `_ten_ma_o()` /
  `tenMaO()`. Đã có cổng `kiem_tram.py` ②⑤ canh `int()` trên khoá xep.
- **Luật rút ra**: dữ liệu có nhiều DẠNG (mã ô, loại thẻ, nguồn ảnh) thì mọi cửa đều phải
  rẽ nhánh. Thêm dạng mới ở một cửa = phải grep hết các cửa còn lại, đếm cho đủ.

### 9. Máy "không đề xuất gì" — phải chứng minh, đừng đoán (11/08/2026)
- **Bệnh**: máy gợi khung đôi trả 0 kết quả. Không có cách nào biết model đã cân nhắc rồi
  từ chối, hay prompt hỏng nên model chẳng hiểu gì.
- **Cách làm đúng**: (a) lưu BẢN THÔ model trả về ra file; (b) BUỘC model trả lời cho từng
  ca mà code đã dò thấy — hoặc đề xuất, hoặc nói rõ lý do từ chối. Sau khi thêm hai thứ
  này thì lộ ngay: model từ chối vì kho thiếu ảnh đội Nhật Bản, Triều Tiên, Palestine, Iran.
  Đó là hành vi ĐÚNG, và cái "lý do từ chối" chính là danh sách ảnh cần đi tìm.
- **Rộng hơn**: mọi cửa máy-gợi-ý đều nên trả kèm lý do khi nói "không có". Im lặng thì
  không phân biệt được máy giỏi với máy hỏng.

### 10. Một việc chỉ có MỘT đường chạy — lệch đường là mất (11/08/2026)
- **Bệnh**: video lên kênh với tít trắng trơn, mất hết chữ vàng điểm nhấn. Cùng buổi: thẻ
  số liệu cũng "không thấy đề xuất". Hai triệu chứng, một gốc.
- **Gốc**: cả hai việc (chọn cụm vàng · gợi thẻ số liệu) đều chỉ chạy trong chuỗi SAU DUYỆT
  LỜI. Anh đổi cách làm — paste tin viết sẵn từ GPT rồi dựng thẳng — là chuỗi đó không chạy,
  và hệ **im lặng** chấp nhận dữ liệu rỗng.
- **Phòng**:
  · Việc nào ảnh hưởng thành phẩm thì phải có **cửa cuối** ngay trước khi lên hình — thiếu
    thì tự làm bù, không thì kêu to. Xưởng là cửa cuối, không phải nơi chỉ biết vẽ.
  · Dữ liệu rỗng ở cửa cuối là **sự kiện đáng in ra log**, không bao giờ là chuyện thường.
  · Logic đó phải nằm ở MỘT module dùng chung, không chép bản sao vào từng đường chạy —
    chép rồi thì đường nào không có bản sao là đường đó mất tính năng.
- **Cách phát hiện sớm**: khi anh đổi cách nhập liệu (paste thay vì máy viết), rà ngay xem
  những gì chuỗi cũ vẫn âm thầm làm hộ mà đường mới không làm.

### 11. Hai chế độ dùng chung một khung — phải tắt lẫn nhau CẢ HAI CHIỀU (11/08/2026)
- **Bệnh**: thêm chế độ "khoanh vùng xoá watermark" dùng lại khung chọn vùng của crop. Bật
  WM thì có tắt crop, nhưng bật crop KHÔNG tắt WM → cả hai cùng true, Enter rơi vào nhánh
  crop và **cắt mất ảnh** trong khi người dùng tưởng đang xoá watermark.
- **Gốc**: làm loại trừ MỘT CHIỀU. Cùng họ với luật "cảnh chính có gì cảnh phụ có nấy" —
  quan hệ đối xứng thì phải cài đối xứng.
- **Phòng**: hai chế độ tranh nhau một tài nguyên (khung chọn, phím Enter, một vùng màn
  hình) thì mỗi hàm `bat*` phải tắt tất cả chế độ anh em, và mọi cửa thoát (`đóng`,
  `chuyển đối tượng`) phải dọn sạch cờ của cả hai.
- **Cách bắt**: CDP thử `batA(); batB(); [modeA, modeB]` — một dòng test bắt được thứ mắt
  đọc code rất dễ bỏ qua. Test tương tác nên soi TRẠNG THÁI sau khi trộn thao tác, không
  chỉ soi từng thao tác riêng lẻ.
- **Làm đúng ở việc này**: tái dùng bản gốc `_goc-crop/` nên nút "↩ Hoàn" cũ lo cả hai
  đường — thêm tính năng mà KHÔNG thêm nút cho anh phải nhớ.

### 12. Undo phải chụp ở ĐIỂM HỘI TỤ, và lịch sử sống theo TỪNG BÀI (11/08/2026)
- **Chọn điểm móc**: mọi đường sửa ảnh (gán, bỏ, kéo thả, khung đôi, nhận nháp, máy gán)
  đều kết thúc bằng veCau() vẽ lại — chụp snapshot Ở ĐÓ thì một chỗ móc phủ hết, kể cả
  tính năng thêm sau này. Ghi từng lệnh (command pattern) sẽ sót đường mới; chụp toàn
  cảnh vài KB thì không bao giờ sót.
- **Bẫy chết người**: đổi bài mà không xoá lịch sử → ⌘Z áp bản đồ ảnh bài CŨ đè bài MỚI
  (đúng họ tai nạn gán đè f04608). Lịch sử undo của dữ liệu theo-bài phải reset khi đổi bài.
- **Kèm**: áp snapshot phải LƯU SERVER NGAY (không chờ debounce) — undo xong F5 ngay mà
  chưa lưu là bước hoàn bốc hơi.

### 13. Cửa duyệt thủ công chỉ đáng giữ khi HOÀN TÁC ĐẮT (11/08/2026)
- **Diễn biến**: xoá watermark ban đầu làm cửa duyệt bản thử (✔ Thay / ✕ Giữ gốc) — anh
  dùng một ngày rồi bảo bỏ: "lưu là thay luôn". Đúng, vì hoàn tác đã RẺ (bản gốc luôn được
  cất, ↩ Hoàn một bấm): bước duyệt chỉ còn là một cú bấm thừa nhân với số ảnh mỗi ngày.
- **Luật**: thao tác có bản-gốc-giữ-lại + hoàn-một-bấm thì làm THẲNG, đừng chèn cửa xác
  nhận. Cửa duyệt người chỉ dành cho việc hoàn tác ĐẮT hoặc KHÔNG hoàn được (dựng video,
  xoá hẳn, đăng lên mạng).
- **Kèm**: ảnh chưa về máy (trang chọn) thì "xoá watermark" = GHI VÙNG chờ, máy vá lúc ảnh
  về — cùng khuôn với crop-ghi-vùng đã có, người dùng học một lần dùng được hai việc. Vùng
  khoanh trên ảnh gốc phải QUY ĐỔI toạ độ nếu ảnh về còn bị crop.

### 14. Một cửa sổ phục vụ HAI loại đối tượng — mọi nút trong đó phải rẽ nhánh đủ (11/08/2026)
- **Bệnh**: cửa soi ảnh dùng cho cả ảnh BÀI lẫn ảnh KHO, nhưng các nút ✂/🧽/↩/Enter chỉ
  viết cho ảnh bài (`dl.anh[soiK]`) — soi ảnh kho thì soiK=null: nút thì hiện mà bấm chặn
  im, Enter thì nổ. "Có nút mà không chạy" tệ hơn không có nút — người dùng tưởng hỏng.
- **Gốc**: thêm loại đối tượng mới vào cửa sổ cũ (kbXemTo mượn #soi) mà không rà lại TỪNG
  handler trong cửa sổ đó. Cùng họ bài học #12 (mã ô hai dạng) và #7 (hai loại thẻ).
- **Phòng**: mượn UI có sẵn cho đối tượng mới thì grep hết handler của UI đó, từng cái
  một trả lời "gặp đối tượng mới thì làm gì" — làm được / rẽ nhánh / chặn CÓ THÔNG BÁO.
  Cấm chặn im lặng.
- **Bẫy kèm**: ghi `textContent` lên nút có con bên trong là NUỐT MẤT phần tử con (span
  #soiCau) — chỗ khác getElementById ra null nổ chậm, khó lần. Nút có cấu trúc con thì
  dựng lại bằng innerHTML ở chỗ CHỦ SỞ HỮU nó, đừng để nơi mượn ghi đè.
- **Cách bắt**: test CHUỖI trạng thái trộn (kho → bài → kho), không chỉ test từng đường
  riêng — hai lỗi có sẵn đều chỉ lộ khi đảo vòng.

### 15. Trần cắt dữ liệu phải NHẤT QUÁN và phải KÊU (11/08/2026)
- **Bệnh**: Enter thêm nhãn báo "đã lưu" mà sổ không có. Route nhận cắt nhãn [:8] nhưng
  khâu khử trùng ngay dưới giữ [:12] — nhãn người dùng vừa thêm (đứng cuối) bị trần gạt
  rụng im lặng đúng khi tấm sẵn 8 nhãn máy.
- **Gốc**: hai con trần trong CÙNG một hàm khác nhau — mỗi lần thêm trần mới không rà
  trần cũ. Và trần cắt thì cắt IM — người dùng tưởng lưu rồi.
- **Phòng**: ① một hằng số trần cho một loại dữ liệu, không rải số trần khắp nơi;
  ② cái gì bị trần gạt phải trả lời cho client biết — server trả bản THẬT đã lưu, client
  so với bản nháp, lệch thì nói ra; ③ test phải dùng bản ghi ĐẦY (tấm 8 nhãn) chứ không
  chỉ bản ghi thưa.

### 16. Máy "chăm quá" cũng là bug — đừng sinh dữ liệu người dùng không xin (11/08/2026)
- **Bệnh**: anh cắt 1-2 đoạn mà kho video hiện 80 dòng "đoạn cắt". Không dòng nào do anh
  tạo — máy scene-detect tự băm mỗi video nhập kho thành 13–26 đoạn, kể cả CLIP TAY 6
  giây cũng bị đè ra tách tiếp.
- **Gốc**: tính năng "tách cảnh tự động" thiết kế cho video dài tải link, nhưng cửa nhập
  là MỘT hàm chung nên đường hồi tố clip tay (video vốn ĐÃ là thành phẩm cắt) cũng bị
  băm. Người dùng nhìn kho không phân biệt được đâu là của mình, đâu là máy đẻ.
- **Phòng**: ① dữ liệu máy TỰ SINH hàng loạt phải có cờ nguồn gốc (loai goc/cat) ngay từ
  ngày đầu — thiếu cờ thì lúc muốn dọn không biết giữ gì; ② tính năng tự động áp qua cửa
  chung phải hỏi "mọi ĐƯỜNG vào cửa này có cùng cần nó không"; ③ số dòng dữ liệu phình
  nhanh hơn số hành động người dùng là tín hiệu đáng ngờ, đừng đợi người dùng tự thấy.

### 17. Chữ trên nút phải nói ĐÚNG việc nó làm (11/08/2026)
- **Bệnh**: nút "👤 Gán cả loạt" — anh tưởng là gắn NHÃN, thực ra đặt CHỦ THỂ. Hệ quả kép:
  hiểu nhầm chức năng đang có, VÀ không ai nhận ra chức năng gắn nhãn loạt còn thiếu.
- **Gốc**: đặt tên nút theo THAO TÁC ("gán cả loạt") thay vì theo THỨ bị thay đổi ("đặt
  chủ thể"). Khi màn hình có hai loại dữ liệu gần nghĩa (chủ thể · nhãn), tên mơ hồ là
  người dùng tự suy — và suy sai.
- **Phòng**: nút sửa dữ liệu thì tên = ĐỘNG TỪ + TÊN TRƯỜNG ("Đặt CHỦ THỂ", "Thêm NHÃN"),
  không dùng tên chung chung. Hai trường gần nghĩa thì để cạnh nhau, khác màu, tooltip
  nói rõ đè hay cộng dồn.
- **Kèm luật dữ liệu**: sửa HÀNG LOẠT trường dạng danh sách phải có đường CỘNG DỒN riêng
  (`nhan_them`), không tái dùng đường ghi đè — đè hàng loạt là xoá sạch dữ liệu riêng của
  từng bản ghi mà người dùng không kịp thấy.

### 17. Đổi tên biến phải đổi ĐỦ, và cổng cú pháp KHÔNG bắt được tên sai (12/08/2026)
- **Bệnh**: đổi `cung` → `nhom_nhac` nhưng sót dòng `print` cuối hàm. Cú pháp vẫn đúng
  nên `ast.parse` cho qua; Python chỉ nổ lúc CHẠY TỚI dòng đó — mà dòng đó nằm SAU khi
  video đã dựng xong. Anh nhận thông báo "dựng hỏng" cho một video hoàn toàn lành.
- **Vì sao sống được 5 ngày**: dòng chết nằm ở cuối đường chạy dài nhất (dựng đủ 60s
  video mới tới). Test nhanh không chạm tới; chỉ ca chạy TRỌN mới lộ.
- **Phòng**: ① đổi tên biến thì grep tên CŨ trên cả file, đừng tin mắt; ② cổng kiểm
  phải soi TÊN chứ không chỉ soi cú pháp — `ast.parse` sạch không có nghĩa là chạy được.
- **Bài học về CHÍNH CỔNG**: bản đầu của bộ soi tên báo giả 4 mục, vá xong còn 2 (tham
  số lambda). Cổng mà báo giả thì lần sau người ta bỏ qua cả cái đúng — phải vặn tới khi
  im lặng trên toàn bộ mã đang chạy tốt, RỒI thử ngược (cắm lại đúng lỗi cũ) để chắc nó
  chưa bị điếc.

### 18. Việc nào KHÔNG cần người bấm thì đừng đợi người bấm (12/08/2026)
- **Bệnh**: nút Kho bắt anh chờ 30–100 giây. Đo ra: 99% thời gian là MỘT khâu gọi model
  (sinh thẻ SEO), phần cơ khí chỉ 0,8 giây.
- **Câu hỏi đúng**: khâu đó cần gì để chạy? Chỉ tiêu đề + lời bình — có sẵn từ lúc dựng
  xong. Vậy nó KHÔNG có lý do gì phải đợi anh bấm nút.
- **Luật**: mọi khâu chậm phải hỏi "đầu vào của nó sẵn từ bao giờ?" — sẵn sớm thì chạy
  nền từ lúc đó. Người dùng luôn có khoảng chết (xem video, đọc kết quả); lấp đúng vào
  đó là thời gian chờ biến mất mà không cần tối ưu một dòng code tính toán nào.
- **Bắt buộc kèm**: chạy nền phải có CỜ chống chạy trùng — người bấm sớm thì CHỜ bản nền,
  đừng khởi động lượt thứ hai (hai lượt cùng ghi một tệp là đè nhau, mà cũng phí model).
- **Đo trước, sửa sau**: nếu không đo từng khâu thì rất dễ đi tối ưu khâu chép file 0,02
  giây trong khi thủ phạm nằm chỗ khác.

### 19. Cho chạy SONG SONG thì phải soi ai CÙNG GHI một tệp (12/08/2026)
- **Tình huống**: đẩy khâu sinh SEO chạy cùng lúc với xưởng dựng để rút thời gian chờ.
  Nhìn thì vô hại — hai việc chẳng liên quan gì nhau.
- **Nhưng**: cả hai cùng ghi `kich-ban.json`. Kiểu ghi phổ biến trong hệ (đọc cả tệp vào
  bộ nhớ lúc đầu → `json.dump` đè cả tệp lúc cuối) khiến bên ghi SAU xoá sạch việc bên
  ghi TRƯỚC — **im lặng, không lỗi, chỉ mất dữ liệu**. Đúng họ bệnh tít trắng trơn 12/08.
- **Luật**: trước khi cho hai việc chạy song song, grep xem chúng cùng đụng TỆP nào /
  SỔ nào / THƯ MỤC nào. Cùng ghi một chỗ thì phải có cửa ghi chung: khoá → đọc lại →
  gộp → thay nguyên khối. Đừng tin "hai việc khác nhau nên chắc không đụng".
- **Cách test**: hai luồng ghi ĐAN NHAU vài chục lượt rồi kiểm còn đủ trường không —
  chạy tuần tự thì không bao giờ lộ.

### 20. Cờ mới không có hiệu lực HỒI TỐ — đừng lấy nó làm bằng chứng (12/08/2026)
- **Bệnh**: thêm cờ `da_xep_kho` rồi dùng "không có cờ = chưa làm" để nhắc việc. Mọi bản
  ghi TRƯỚC ngày có cờ đều bị kết tội oan, dù việc đã làm xong từ lâu.
- **Phòng**: cờ mới chỉ nói được về tương lai. Muốn kết luận quá khứ thì phải soi DẤU
  VẾT THẬT của việc đó (ở đây: hộp/sổ trên Drive), hoặc chạy một lượt hồi tố gắn cờ cho
  dữ liệu cũ NGAY khi thêm cờ.
- **Làm đúng luôn thể**: chỗ nào phát hiện "cũ mà đã làm rồi" thì gắn cờ luôn — lần sau
  khỏi soi lại, sổ tự lành dần.
- **Rộng hơn**: cảnh báo sai vài lần là người dùng thôi tin cả cảnh báo đúng. Nhắc việc
  phải dựa trên sự thật kiểm chứng được, không dựa vào một trường mới đẻ.

### 21. Máy gợi ý không được cãi lại thao tác CHỦ ĐỘNG của người (12/08/2026)
- **Bệnh**: anh bấm chọn cảnh 4, bấm một tấm trong dải kho → ảnh nhảy vào cảnh 11, vì
  tấm đó mang badge "máy gợi cho cảnh 11".
- **Gốc**: tính năng sinh ra cho cảnh LƯỚT NHANH (chưa chọn cảnh nào, bấm tấm là vào
  đúng cảnh máy gợi — rất tiện). Nhưng nó không phân biệt "người chưa chọn gì" với
  "người đã chọn rõ ràng", nên đè lên cả ý người.
- **Luật**: thao tác CHỦ ĐỘNG của người (bấm chọn, gõ vào ô, kéo thả) luôn thắng gợi ý
  của máy. Gợi ý chỉ được quyết khi người CHƯA nói gì.
- **Cách giữ cả hai**: đừng bỏ tiện lợi cũ — cho nó một CỬA RIÊNG rõ ràng (bấm thẳng vào
  badge = "làm theo máy"). Một cú bấm, hai vùng, hai ý nghĩa khác nhau.
- **Và nói ra**: khi máy làm khác gợi ý của chính nó, thông báo phải ghi rõ ("máy vốn gợi
  tấm này cho cảnh N") — người dùng mới hiểu hệ đang nghĩ gì.

### 22. Nhãn tốt mà đề xuất vẫn dở — lỗi ở BỘ CHẤM, không phải ở nhãn (13/08/2026)
- **Tình huống**: anh kêu đề xuất ảnh chưa sát nội dung. Phản xạ đầu là "nhãn nghèo, phải
  gắn nhãn kỹ hơn" — đo ra thì SAI: 86% ảnh đủ bộ (chủ thể + ≥5 nhãn + mô tả dài), 95% có
  tên chủ thể.
- **Bệnh thật**: bộ chấm cho mọi từ trọng số như nhau. Nhãn "2026" đeo 798/873 tấm, "asean
  cup 2026" 369 tấm — câu nào cũng khớp, nên gần như CẢ KHO đều "hợp bài" ngang nhau. Tấm
  đúng người đúng việc chìm lẫn giữa 800 tấm chung chung.
- **Chữa**: chấm theo ĐỘ HIẾM (IDF). Từ có mặt khắp kho gần như không cộng điểm; tên riêng
  hiếm ăn trọn. Code thuần, 0 token, cache theo mtime sổ.
- **Luật rút ra**: trước khi đi gắn nhãn kỹ hơn / gọi model to hơn, hãy ĐO xem dữ liệu có
  thật sự thiếu không. Rất nhiều lần dữ liệu đủ, chỉ cách ĐỌC dữ liệu là sai.
- **Đo cho đúng thứ người dùng nhìn**: đo TOP-1 thì thấy "không đổi gì" (12/12 cả trước lẫn
  sau) — vì tấm số một vốn đã đúng. Đổi sang đo TOP-10 (đúng thứ hiện trên dải kho) mới
  thấy 95% → 100%. Chọn sai thước đo thì cải tiến thật cũng thành vô hình.

### 23. Cổng lọc chỉ mạnh bằng TỪ ĐIỂN của nó (13/08/2026)
- **Bệnh**: ảnh "cầu thủ Thái Lan tập luyện" lọt vào bài Việt Nam–Malaysia, dù cổng lọc
  đội lạ đã có và chạy đúng.
- **Gốc**: từ điển chỉ có tên ĐẦY ĐỦ ("thai lan", "thailand", "voi chien"). Mắt máy viết
  nhãn theo lối nói thường — "tuyển Thái", "người Thái", "cầu thủ Thái" — không khớp cái
  nào, nên cổng coi như ảnh không thuộc đội nào và cho qua.
- **Phòng**: mỗi khi thêm luật lọc dựa trên từ điển, phải kiểm luôn ĐỘ PHỦ của từ điển
  bằng chính giọng văn của bên sinh dữ liệu (ở đây là mắt máy), không phải bằng tên chuẩn
  trong sách.
- **Bẫy kèm — sửa nhầm bản dự phòng**: bảng `_DOI_TUYEN` nằm trong code CHỈ dùng khi từ
  điển Drive vắng mặt. Sửa code xong đo vẫn trượt, suýt tưởng vá hỏng. Trước khi sửa một
  bảng dữ liệu, tra xem RUNTIME thật đang đọc bản nào.
- **Đo trước khi kết luận**: cảm giác "nhãn kho sai nhiều" — đo ra chủ thể sai 0/20, mô tả
  sai hẳn 10%. Sửa đúng chỗ hở (từ điển) rẻ hơn nhiều so với đi gắn nhãn lại cả kho.

### 24. Ảnh gửi model: thu nhỏ trước, token giảm ba phần tư mà không mất gì (13/08/2026)
- **Số đo**: model tính token ảnh ≈ w×h/750. Ảnh 2000×1333 tốn 3.555 token; thu về 1000px
  còn 888. Cả kho 892 ảnh: 3,2 triệu → 0,79 triệu.
- **Chứng minh trước khi tin**: chạy lại CÙNG bộ ảnh ở hai cỡ với cả opus lẫn sonnet — bản
  nhỏ vẫn đọc đúng số áo, vẫn nhận ra tên HLV, vẫn thấy logo tài trợ. Không đoán "chắc là
  đủ nét", phải đo.
- **Luật**: mọi cửa gửi ảnh cho model đều đi qua MỘT hàm thu nhỏ có cache. Ảnh gốc trong
  kho giữ nguyên — thu nhỏ chỉ là bản gửi đi.
- **Nhìn rộng**: token của việc chạy HẰNG NGÀY quan trọng hơn token của việc chạy một lần.
  Tối ưu khâu lặp lại (mắt máy mỗi bài) đáng giá hơn tối ưu khâu quét kho.
- **Kèm**: trước khi kết luận "chức năng X chưa từng chạy", kiểm xem môi trường CHẠY THẬT
  có khác môi trường test không — job test của em thiếu PATH nên `claude` không gọi được,
  suýt báo oan là mắt máy chết; trạm thật có khai PATH trong plist và vẫn chạy đúng.

### 25. Hằng số chết làm tính năng cũ ngừng chạy — im lặng (13/08/2026)
- **Bệnh**: ô phụ dư không hiện trên trạm, anh tưởng mất dữ liệu sau khi render.
- **Gốc**: tính năng "hiện ô DƯ" đã làm đủ từ trước (CSS, tooltip, nhãn cảnh báo) nhưng
  một lần sửa sau đó đặt `const du = false;` — cả nhánh code thành CHẾT. Không lỗi, không
  cảnh báo; chỉ là màn hình thiếu mất thứ đáng lẽ phải có.
- **Dấu hiệu nhận ra**: thấy biến cờ được gán CỨNG (`= false`, `= true`) ngay cạnh code
  xử lý công phu cho cả hai nhánh → gần như chắc chắn là tàn dư của một lần sửa vội.
- **Phòng**: khi rút gọn/refactor, đừng tắt nhánh bằng hằng số — xoá hẳn hoặc giữ nguyên
  điều kiện. Hằng số chết trông như code đang chạy nên không ai soi lại.
- **Kèm — dữ liệu và hiển thị lệch nhau**: nhịp tính lại làm số ô giảm, nhưng dữ liệu cũ
  vẫn nằm trong sổ. Chỗ nào hiển thị theo công thức thì phải lấy `max(công thức, số thật
  trong sổ)`, không thì dữ liệu thừa vô hình — người dùng không xoá được cái mình không
  nhìn thấy.

### 26. Người đã gán tay thì máy phải MỞ CHỖ, đừng đi hiển thị lời xin lỗi (13/08/2026)
- **Bệnh**: cảnh dùng clip bị ép cứng 1 khung, nên mọi ảnh phụ anh gán cho cảnh đó không
  bao giờ lên hình. Lần đầu em "sửa" bằng cách hiện chúng dưới dạng **ô dư** (mờ, có chú
  thích) — anh gạt ngay: "không cần ô dư làm gì".
- **Bài học**: khi dữ liệu người dùng không khớp với luật máy, phản xạ đúng là hỏi *luật
  máy có sai không*, chứ không phải trưng cái lệch lên màn hình rồi gọi đó là minh bạch.
  Anh gán 2 ảnh phụ = anh muốn 3 khung; câu 9,2 giây thừa sức chia 3 × 3,1s. Luật "cảnh
  clip luôn 1 khung" mới là cái sai.
- **Cách làm đúng**: cho ý người thành ĐẦU VÀO của phép tính (`so_phu` vào `chia_nhip`),
  có TRẦN rõ ràng (mỗi khung ≥2,5s), và chặn ngay từ CỬA NHẬP khi vượt trần — kèm câu
  nói cho người dùng biết ảnh đi đâu ("giữ trong kho, gán cho cảnh khác").
- **Ba tầng phải sửa cùng lúc**: công thức nhịp · xưởng dựng · trạm hiển thị. Sửa một
  tầng là lệch ngay — mà lệch kiểu này thì im lặng, chỉ lộ khi xem video.

## Lớp DỰ PHÒNG của bộ dò phải có TRẦN, không thì nó vơ (14/08)

**Bệnh**: hàm dò "ảnh nào đang dưới con trỏ" cho phím tắt extension có ba lớp — thẻ `img`,
`background-image`, rồi lớp dự phòng "phần tử đang trỏ chứa đúng một `img`". Lớp thứ ba duyệt
ngược lên tới `body`. Trang chỉ có MỘT tấm ảnh (bài Facebook đơn ảnh) mà anh bấm phím lúc trỏ
vào vùng trống thì `body` vẫn "chứa đúng 1 img" → gửi đi tấm anh **không hề trỏ tới**, im lặng.

**Gốc**: lớp dự phòng sinh ra để cứu ca khó (ảnh bị lớp phủ trong suốt che), nhưng không ai đặt
**biên** cho nó. Dự phòng không biên thì luôn tìm được *một cái gì đó* — y hệt bệnh "máy gợi ý
không có ngưỡng từ chối thì luôn bịa".

**Phòng**: mỗi lớp dự phòng phải trả lời được "phạm vi của tôi tới đâu". Ở đây: bỏ `html`/`body`,
chỉ soi 3 cấp sát con trỏ, và khối phải ≤60% màn hình. Trả rỗng rồi nói ra vẫn hơn đoán bừa —
mọi hành động GỬI ĐI cũng phải đòi bằng chứng như hành động HUỶ HOẠI.

**Cách bắt**: nghĩ ra ca "đáng lẽ phải trả rỗng" rồi thử — không chỉ thử ca "phải trả đúng".
Bộ dò chỉ được kiểm bằng ca dương tính thì cái nó vơ nhầm không bao giờ lộ.

**Bẫy kèm — phép thử sai làm mình suýt vá nhầm**: lần chạy đầu ca "không phải ảnh" báo SAI, em
suýt đi sửa hàm. Soi ra thì `scrollIntoView` làm lệch toạ độ giữa lúc tính và lúc rê chuột —
chuột vẫn đứng ở ô trước đó, hàm trả **đúng**. **Test tương tác phải in ra ĐANG TRỎ VÀO ĐÂU
cùng với kết quả**, không thì không phân biệt nổi "hàm sai" với "phép thử sai".

## Bài học thiết kế

- **Viết luồng song song = mầm lỗi.** Dải kho tự viết `kbLay` gọi thẳng `/api/gan` nên
  mất đường ghép đôi. Thấy luồng cũ thì dùng lại (tách phần nhận, giao phần gán).
- **"Đã có rồi" là kết quả THÀNH CÔNG, không phải thất bại.** Cửa chống trùng phải trả
  về cái đang có, đừng trả rỗng (vụ "nhận ảnh hỏng").
- **Máy gợi ý không có ngưỡng từ chối thì luôn bịa.** Cho phép trả rỗng + nói lý do.
- **Hai luật chấm cho hai việc**: BÀY cả kho → chấm mềm; TÌM một cụm → chấm nghiêm.
- **RAM là luật cứng**: đừng đưa ảnh full-size vào model vision; cắt mảnh + trần cạnh.
  Máy 16GB đã sập nguồn vì hai tiến trình LaMa ~30GB.
- **Đo trước khi sửa UI**: 75 nút ăn 35,3% màn → nút theo ngữ cảnh còn 22 nút / 5,3%.

## Bẫy khi TEST

- Trạm chính đọc `?viec=`, không phải `?ma=` — mở nhầm là thao tác lên **bài thật**.
- `buoc3_xepkho.py` chạy trên sandbox **vẫn tạo hộp thật trên Drive** — test xong phải xoá.
- Test kho qua `?ma=` để lại vết `da_dung` trong sổ — dọn sau test.
- Ảnh màu phẳng cho dhash suy biến → test chống trùng phải dùng ảnh có cấu trúc.
- Sửa .py xong **kiểm cú pháp ngay**, đừng để tới cuối mới chạy bộ kiểm.

## Tra lại thứ đã biết = tự chuốc lỗi im lặng (13/08, lần THỨ HAI cùng họ)

**Bệnh**: cảnh 4b, 4c anh gán đầy đủ nhưng không lên hình; cảnh 6 lấy nhầm ảnh của câu 5 mà không báo gì.

**Gốc**: `xuong.py` tra 'cảnh này thuộc câu nào' bằng cách dò mốc thời gian — và tra tới BA lần ở ba đoạn code khác nhau. Giữa các lần tra, khối clip ③d đã DỊCH mốc cảnh để cho clip mượn giây. Lần tra sau vì thế ra kết quả khác lần tra trước, lệch đúng vài phần mười giây — vừa đủ để cảnh rơi tụt về câu liền trước.

**Vì sao nguy**: khi câu trước tình cờ có ĐỦ số ảnh phụ, máy không báo lỗi gì cả — video ra sai ảnh mà log sạch bong. Cảnh 4 may là câu 3 thiếu một phụ nên còn có dòng '⚠ thiếu 1 ảnh phụ' để lần.

**Cách phòng**: thứ gì đã tính được một lần trên dữ liệu GỐC thì CHỐT lại thành biến, mọi nơi sau đó ĐỌC chứ không tra lại. Đây chính là luật 'não một nguồn' áp cho biến trong một hàm. Dấu hiệu nhận bệnh: **cùng một biểu thức dò tìm xuất hiện từ hai lần trở lên trong một hàm** — đó không phải trùng lặp vô hại, đó là hai nguồn chân lý đang chờ lệch nhau.

**Đã có cổng**: `kiem_tram.py` ②⑨ đếm số lần `enumerate(cau_moc) if b < m` trong `xuong.py`, quá một lần là trượt. 10/08 đã vá cục bộ bằng `cau_goc` cho riêng khung đôi — vá ngọn nên bệnh tái phát ở nhánh khác sau ba ngày.

## Cờ 'người đã sửa' phải phân biệt CHẠM VÀO với DUYỆT NỘI DUNG (14/08)

**Bệnh**: 76% kho ảnh miễn vòng soát chất lượng, dù trong đó có tấm nhãn và mô tả nói hai người khác nhau.

**Gốc**: một cờ `nguoi_sua` gánh hai nghĩa. Anh chọn 300 tấm gắn chung một nhãn 'AFF Cup' — thao tác đó chạm vào 300 dòng sổ, nhưng anh KHÔNG đọc mô tả của tấm nào cả. Cờ vẫn bật, và mọi máy về sau đọc cờ đó như 'người đã duyệt, máy đừng đụng'.

**Cách phòng**: khi một thao tác HÀNG LOẠT và một thao tác TỪNG CÁI cùng ghi một cờ, hỏi ngay: cờ này về sau ai đọc, và họ hiểu nó nghĩa gì? Nếu người đọc hiểu là 'đã được người xem xét' thì thao tác hàng loạt KHÔNG được phép bật nó. Đặt hai cờ, đừng tiếc.

**Họ hàng**: cùng bệnh với vụ 'tra lại thứ đã biết' (13/08) — đều là MỘT thứ mang hai nghĩa ở hai chỗ khác nhau, rồi lệch nhau âm thầm.

## Đổi TÊN TỆP là đổi HỢP ĐỒNG — và hợp đồng có thể nằm ngoài repo (14/08)

**Bệnh**: anh bấm Kho, video lên Drive bình thường, nhưng nút '📂 Mở kho' tụt thành '📂 Mở việc' và mở sang ổ DATA. Anh tưởng em tự ý đổi link.

**Gốc**: em đổi tên file gói đăng `goi-dang.txt` → `goi-dang_<slug>.txt`. Module kiểm hộp `kho_video.py` có hằng `TEP_CHUAN` liệt kê đúng tên cũ → `kiem_hop()` báo THIẾU TỆP → hộp không được coi là hợp lệ → trạm dò không ra hộp → nút đổi trạng thái.

**Vì sao rà vùng ảnh hưởng vẫn lọt**: em có grep `goi-dang` — nhưng chỉ trong `~/socbongda247`. `kho_video.py` sống trên **Drive** (`cong-cu/`), ngoài phạm vi grep. Luật 'rà ai dùng chung' mà quét thiếu một kho thì bằng không.

**Cách phòng**:
- Đổi tên tệp/khoá sổ/route → grep TOÀN BỘ các nơi code sống, không chỉ thư mục máy: `~/socbongda247`, `cong-cu/` trên Drive, `~/.claude/skills/`, extension Chrome.
- Kiểm theo TIỀN TỐ thay vì tên cứng khi tên tệp có phần thay đổi được.
- Cổng `kiem_tram.py` ⑪ nay NẠP THẬT `kho_video.py` trên Drive và đối chiếu — hợp đồng liên-kho phải được canh bằng máy, không bằng trí nhớ.

**Dấu hiệu nhận bệnh**: một nút/nhãn tự đổi trạng thái sau khi mình sửa chỗ tưởng như không liên quan. Nút đổi trạng thái = có cái gì đó đang KIỂM một điều kiện, đi tìm điều kiện ấy.

## Luật 'chính có gì phụ có nấy' áp cho cả TÀI NGUYÊN, không riêng giao diện (14/08)

**Bệnh**: anh cắt cả tuần đoạn video để ghép vào cảnh, nhưng trang kho-nha-duyet chỉ có 4 dòng — không đoạn nào của anh trong đó.

**Gốc**: ẢNH của bài có đường về kho chung (xếp kho gọi `nhap_kho_chu_the.py <viec>` từ 10/08). ĐOẠN VIDEO thì không — `nhap_kho_video.py` chỉ chạy hai đường: `--tai <url>` (anh dán link) và `--bo-nhan`. Đoạn anh tua-cắt-gán vào cảnh không có cửa nào dẫn về kho, nên công tìm + canh mốc + né logo mất trắng sau mỗi bài.

**Cách phòng**: luật 'cảnh chính có gì cảnh phụ có nấy' lâu nay chỉ được soi ở tầng GIAO DIỆN (nút, cờ lật, khung đôi). Nó áp cho cả DÒNG CHẢY TÀI NGUYÊN: mỗi loại tài nguyên anh bỏ công vào (ảnh, đoạn clip, thẻ số liệu, card đồ hoạ) đều phải có ĐỦ BỐN CỬA — vào bài, về kho chung, tra lại, và tái dùng. Thiếu một cửa là công của anh chảy ra ngoài mà không ai kêu.

**Cách hỏi để bắt sớm**: với mỗi loại tài nguyên, hỏi 'thứ này sau khi dùng xong đi đâu?' — trả lời được là có cửa, ngập ngừng là thiếu.

**Cổng ⑧b** canh `buoc3_xepkho.py` gọi đủ CẢ HAI đường nhập kho (ảnh + đoạn clip).

**Bẫy kỹ thuật kèm theo**: cắt lại cùng một đoạn ra file khác byte → md5 không bắt được trùng. Phải có dấu riêng `nguon_doan = "<tệp gốc>#<từ>-<đến>"` mới chống nhập lặp.

## Ba cách soi watermark: hai cách code THUẦN đều trượt, đừng làm lại (14/08)

Cần cổng chặn 'chữ/logo chèn GIỮA khung' cho video vào kho. Đã đo thật:

| cách | kết quả |
|---|---|
| **mắt tĩnh** so pixel đứng yên qua 4 khung | **BÁO OAN 2/5** — giàn thép trắng trong cảnh drone bay bị chấm 5,35% dù hình sạch trơn. Pixel không tách được 'vật tĩnh trong cảnh' với 'lớp phủ'. |
| **OCR tesseract** vùng giữa | **MÙ** trước caption video: chữ trắng trên nền đỏ, thử psm 6/7/11, `-l vie`, tăng tương phản, nhị phân, đảo màu — đều trả rác. (Tesseract KHÔNG hỏng: đọc đúng ảnh chữ dựng bằng PIL. Nó chỉ thua nhiễu nén video.) |
| **mắt máy trả lời trong CHÍNH lượt gắn nhãn** | ✅ chặn đúng, và **không tốn thêm token** vì lượt nhãn vốn đã nhìn khung hình rồi. |

**Bài học**: 'code trước, model sau' KHÔNG có nghĩa cố đấm ăn xôi bằng code. Việc phân biệt lớp phủ với vật thể trong cảnh là việc THỊ GIÁC NGỮ NGHĨA — code thuần làm dở. Chỗ đúng để tiết kiệm là **gộp câu hỏi vào lượt model đã có sẵn**, chứ không phải tránh model bằng mọi giá.

**Cách gộp**: thêm một khoá vào JSON mà mắt máy vốn đã trả (`phu_giua: true|false`), kèm định nghĩa rạch ròi — chữ CHÈN ĐÈ (caption, tên kênh) là true; chữ CÓ SẴN TRONG CẢNH (biển quảng cáo sân, áo đấu) là false; chữ sát rìa cũng false vì đã có phép cắt mép lo.

## Mắt máy nói 'có watermark' chưa phải bằng chứng — bắt nó CHÉP RA CHỮ (14/08)

**Bệnh**: lượt đầu của mắt duyệt cắt oan 2/11 tấm — tấm Xuân Son bay người KHÔNG có watermark bị báo 'góc', máy cắt 13% hai mép, mất một phần quả bóng.

**Gốc**: prompt hỏi 'có watermark ở đâu' — câu hỏi PHÂN LOẠI, model đoán cũng trả lời được. Hỏi kiểu đó là mời nó bịa.

**Sửa**: bắt kèm `wm_chu` — CHÉP ĐÚNG chữ đọc được. Không đọc ra chữ thì mặc định 'khong'; nghi mà không có chữ thì chỉ NHẮC, không đụng ảnh. Không bao giờ cắt hai mép cùng lúc. Đo lại: 0 cắt oan trên cùng bộ ảnh.

**Luật rút ra**: mọi hành động HUỶ HOẠI (cắt, xoá, gỡ) dựa trên phán đoán của model phải đòi BẰNG CHỨNG CỤ THỂ (chữ chép ra, toạ độ, số đọc được) — phán đoán suông chỉ đủ để cảnh báo. Cùng họ với 'máy gợi ý phải có quyền nói không có'.

**Kèm theo**: ảnh ANH gán tay — máy soi giúp watermark nhưng KHÔNG có quyền gỡ (anh chọn có ý); chỉ ảnh MÁY gán mới bị gỡ khi lệch. Quyền xử tỷ lệ với ai đã quyết.

## Restart trạm = giết mọi chuỗi đang chạy bên trong nó (14/08, em gây ra)

**Bệnh**: anh mở bài 17:19:43, bấm Duyệt lời; em `launchctl kickstart -k` trạm lúc 17:20:19 để nạp code mới — chuỗi sau Duyệt lời là THREAD TRONG TIẾN TRÌNH TRẠM, chết câm theo. Anh nhìn ô đồng hồ đếm 17 phút ở chặng 'mở việc', không biết máy sống hay chết.

**Luật mới — RESTART AN TOÀN**: trước khi kickstart trạm phải kiểm KHÔNG có job đang chạy (`pgrep -f 'claude -p'` con của trạm, hoặc hỏi /api/dong-ho các bài mới nhất). Có job → chờ xong hoặc báo anh. Trạm là NHÀ của mọi luồng nền — đập nhà lúc người còn ở trong là tai nạn.

**Vá kèm**: thanh %% trước chỉ sống trong trang lúc bấm Duyệt (reload là mù). Nay job ghi sổ phụ `VIEC_JOB_MA` (job→bài; để riêng vì dict VIEC_JOB bị 101 chỗ ghi đè cả cục), `/api/dong-ho` trả job đang chạy của bài, UI vẽ lại thanh %% mỗi 6 giây — reload hay mở máy khác đều thấy.

## Cầu chì phải ĐỐI CHIẾU DANH SÁCH, đừng đoán chữ nào giống tên riêng (14/08)

**Bệnh**: cầu chì 'tên lạ' bản đầu tự dò 'cụm hai chữ nào trông giống tên riêng' → bắt luôn «tiền đạo», «chỉ đạo», thay bằng tên đội, câu lệnh thành rác: *«u17 viet nam tap luyen việt nam U17 Việt Nam World Cup bóng đá»*.

**Sửa**: hồ sơ bài ĐÃ trích sẵn `nhan_vat`. Lấy đúng danh sách ấy trừ đi từ điển thực thể là ra tên lạ — chính xác, không cần đoán chữ nào cả. Đo lại: gỡ đúng 3 câu dính tên lạ, các câu khác nguyên vẹn.

**Luật**: khi cần nhận diện một loại thực thể, hỏi trước *'đã có ai trong hệ trích ra danh sách này chưa?'*. Có thì đối chiếu; chưa có thì tạo danh sách rồi đối chiếu. Đoán bằng mẫu chữ là hạ sách — cùng họ với bài học 'mắt máy nói có watermark chưa phải bằng chứng'.

## Văn bản NGƯỜI VIẾT thì đừng đuổi theo bằng regex (14/08, anh vạch đúng)

**Anh hỏi**: *"GPT trả về từ khoá mỗi lần không đồng nhất form, a tưởng model tự đọc hiểu chứ?"*

**Bệnh**: bộ bóc gói GPT bản đầu viết bằng khuôn cứng — đòi nhãn `ĐOẠN N`, dòng `Từ khóa:`, gạch đầu dòng. Lần dán thứ hai GPT trả kiểu khác (câu trong ngoặc kép + dòng trắng + từ khoá TRẦN) → bóc ra 0, báo 'không khớp được đoạn nào'.

**Gốc**: khối dán là VĂN BẢN NGƯỜI VIẾT, không phải giao thức máy. Nó không có hợp đồng định dạng nào cả. Viết regex chạy theo là cuộc đua không có đích — vá xong khuôn này, lần sau khuôn khác.

**Luật**: đầu vào có HỢP ĐỒNG (JSON, CSV, tên tệp, sổ nội bộ) → code bóc. Đầu vào là VĂN NGƯỜI VIẾT TỰ DO → phải có tầng model đọc hiểu. Ranh giới này quyết định ngay từ lúc thiết kế, đừng đợi hỏng mới nhận ra.

**Cách làm hai tầng** (giữ được cả rẻ lẫn bền): code thử trước — 0 token, ăn ngay với khuôn quen; khớp dưới nửa số câu thì gọi haiku đọc hiểu. UI nói rõ đã dùng cách nào (⚡ khuôn / 🧠 mắt máy) để anh biết mỗi lần tốn gì.

**Họ hàng**: cùng bài học với vụ OCR watermark — 'code trước, model sau' KHÔNG có nghĩa cố đấm ăn xôi bằng code ở việc vốn thuộc về model.

## Từ khoá tìm ảnh phải NEO THỜI ĐIỂM, không thì ra ảnh mọi thời kỳ (14/08)

**Anh nêu**: *"nội dung có đoạn 'huấn luyện viên đội tuyển Malaysia' thì từ khoá tìm như thế sẽ ra rất nhiều đời huấn luyện viên, trong khi tin của mình đang nói về thời điểm hiện tại — phải tự suy luận để đưa ra từ khoá sát hơn."*

**Gốc**: bộ gợi từ khoá dịch câu thoại sang câu lệnh mà KHÔNG có bối cảnh thời gian. Ảnh cũ ba năm trước trông y hệt ảnh mới — chỉ MỐC THỜI GIAN trong câu lệnh mới lọc được. Rộng hơn HLV: đội hình, ban huấn luyện, áo đấu, bảng xếp hạng, nhà vô địch, đội trưởng — mọi thứ đổi theo mùa.

**Ba lớp đã dựng**:
1. **Prompt biết bối cảnh** — nhét HỒ SƠ BÀI (nhân vật · đội · giải · thời điểm · đã diễn ra chưa) vào lời dặn. Trước đó prompt chỉ có tiêu đề + tin gốc + các câu, không hề biết bài thuộc giải nào.
2. **Luật 6bb** — chức danh chung phải thành TÊN cụ thể nếu bài có nêu; không nêu thì neo bằng giải + năm.
3. **Cầu chì `_neo_thoi_diem`** — code tự chèn mốc khi câu lệnh có chức danh đổi theo thời gian mà chưa có năm/giải. Model quên thì máy bọc lót.

**Hai lỗi bắt được khi chạy thật** (đều do cầu chì làm ẩu, đã sửa):
· chèn tên đội theo tiêu đề → bài về cầu thủ Malaysia mà tiêu đề nhắc 'VIỆT NAM' trước, thành *«việt nam hậu vệ Malaysia»* — hai đội một câu. Sửa: CHỈ chèn đội khi câu chưa có đội nào.
· tên giải cũ 'AFF Cup' chắp vào đuôi MỌI câu lệnh, vì neo phụ lấy thẳng từ kịch bản. Sửa tại nguồn neo. Giải đã đổi tên thì tên cũ ra ảnh mùa cũ.

**Luật rút ra**: mọi bộ sinh-truy-vấn phải được đưa BỐI CẢNH THỜI GIAN của việc, và phải có cầu chì code chèn mốc — vì model dịch chữ theo chữ thì không tự nhớ 'bây giờ là bao giờ'.

## Chèn UI vào trang có sẵn: ĐỌC CSS trước, và phải NHÌN ảnh chụp (15/08)

**Bệnh**: thêm mục 'Máy này' vào trang phong cách — nhãn bị ép thành cột dọc một chữ, ô nhập còn 26px, nút cao 249px. Anh chụp màn hình mới thấy.

**Hai lỗi chồng nhau**:
1. Tự đặt `class="hang"` — class ấy KHÔNG có trong CSS của trang. Trang dùng `.num` (lưới hai cột). Class không tồn tại thì trình duyệt không báo gì, chỉ lặng lẽ bỏ qua.
2. Chèn khối vào bên trong `<div style=display:flex>` của HÀNG NÚT cuối trang → mọi phần tử con thành một cột.

**Vì sao không tự phát hiện**: `node --check` bảo JS hợp lệ, cú pháp HTML không sai, cổng kiểm cũng qua. Không có cổng nào bắt được 'trông xấu'. Chỉ có mắt.

**Cách làm đúng lần sau**:
· ĐỌC CSS của trang, liệt kê class đang có, rồi bắt chước khuôn gần nhất — đừng đặt class mới.
· Sau khi chèn, ĐO bằng CDP: `getBoundingClientRect()` của khối và ô nhập; lệch hẳn so với các mục cũ là biết hỏng.
· Việc UI thì phải CHỤP ẢNH nhìn, không dừng ở 'cú pháp hợp lệ'.

**Bẫy phụ đã trả giá 3 lần trong lượt này**: tìm mốc chèn bằng chuỗi có kèm thụt lề (`'    <button ...'`) — file thụt 2 hay 4 space là trượt im lặng. Dùng chuỗi KHÔNG kèm thụt lề, hoặc `find` rồi cắt theo vị trí.

## NFD lại cắn: glob tên có dấu trên macOS TRƯỢT SẠCH (15/08, tái phát)

**Bệnh**: bộ dò Drive tìm `*Sóc bóng đá 247*` — 0 kết quả, dù thư mục sờ sờ ra đó. Cùng lúc `Kênh youtube*` (không dấu) lại tìm được.

**Gốc**: macOS lưu tên tệp dạng NFD (chữ và dấu tách rời), chuỗi trong mã Python là NFC. Glob so byte nên trượt hết. **Bài học này đã ghi sổ từ trước mà vẫn tái phát** — vì lần trước ghi cho 'script so tên file', lần này là 'glob', em không nhận ra cùng một bệnh.

**Luật rộng hơn**: mọi phép SO KHỚP TÊN có dấu tiếng Việt trên macOS — glob, `in`, `==`, `startswith`, khoá dict — đều phải `unicodedata.normalize('NFC', …)` CẢ HAI VẾ. Không có ngoại lệ nào cho glob.

**Cách né**: cần tìm thư mục theo tên có dấu thì đừng dùng glob — tự `os.listdir` rồi so chuỗi đã chuẩn hoá. Chậm hơn không đáng kể, mà đúng.

## Thiết kế công cụ: máy quét được thì máy phải quét (15/08)

Anh hỏi: *"nhân viên máy Windows muốn đẩy lên Drive chia sẻ thì phải thay đường dẫn thế nào cho dễ làm nhất, tiện nhất? Em thiết kế công cụ phải tiện dùng trả lời được câu hỏi như thế."*

Bản đầu em làm bốn ô nhập chữ — đúng chức năng, sai thiết kế. Người dùng phải tự biết đường dẫn Drive của mình dài thế nào, gõ đúng từng ký tự, gõ sai thì im lặng hỏng.

**Luật**: mỗi khi định bắt người dùng NHẬP một thứ mà máy có thể TÌM ĐƯỢC, hãy hỏi 'sao không để máy tìm rồi người bấm chọn?'. Kèm ba thứ: LÝ DO chọn được ('đã có sổ kho ảnh'), BẰNG CHỨNG (số mục bên trong), và thứ đáng chọn XẾP LÊN ĐẦU.

## Thư mục Google 'được chia sẻ' KHÔNG tự xuống máy (15/08)

Máy thứ hai đăng nhập Drive bằng tài khoản KHÁC, nên kho tài nguyên phải chia sẻ sang. Bẫy: Drive for Desktop chỉ đồng bộ **Drive của tôi** và **Drive dùng chung**; thứ người khác chia sẻ nằm ở **Được chia sẻ với tôi** — thấy trên web mà KHÔNG có trong ổ G:.

**Phải làm**: web → Được chia sẻ với tôi → chuột phải → Sắp xếp → **Thêm lối tắt vào Drive** → chọn Drive của tôi. Xong mới đồng bộ xuống.

**Vì sao đáng ghi**: người cài sẽ thấy 'đã chia sẻ rồi mà máy không có', rồi đi tìm lỗi ở phần mềm — trong khi lỗi nằm ở cách Google Drive hoạt động. Đã viết vào HUONG-DAN-MAY-MOI.md mục B4 kèm nhãn 'bước hay bị vấp nhất'.

## Tài liệu về CODE phải đi CÙNG code (15/08)

Skill kiến trúc sư — bản đồ hệ + 50 KB bài học — sống trên Drive, tách khỏi kho mã. Hôm nay dựng git mới lộ ra: máy khác `git clone` về thì có đủ mã nhưng **không có một chữ nào** về luật phải theo. Claude bên đó sẽ giẫm lại đúng những cái hố đã trả giá.

**Luật**: thứ nào MÔ TẢ code (kiến trúc, bài học, nhật ký thay đổi, hướng dẫn cài) thì phải nằm TRONG kho mã, không phải ở kho tài liệu riêng. Chúng đổi cùng nhịp với mã; tách ra là chắc chắn lệch. Thứ ở ngoài chỉ nên là DỮ LIỆU (ảnh, video, sổ học của từng máy).

**Kèm theo**: `CLAUDE.md` ở gốc kho là cửa vào — Claude Code tự đọc đầu mỗi phiên. Viết nó như viết cho người mới đến làm ca đêm: hệ là gì, cấm làm gì, làm xong phải kiểm gì.

## Rà 'chạy được trên hệ khác' phải rà cả MODULE, không riêng LỆNH (15/08)

**Bệnh**: em báo xong bộ cài Windows. Anh hỏi lại 'đã ổn chưa', rà thật thì TRẠM KHÔNG KHỞI ĐỘNG NỔI — 6 tệp `import fcntl`, module chỉ có trên Unix, ImportError ngay dòng đầu.

**Gốc**: em rà `open`, `osascript`, `launchctl` — tức LỆNH hệ điều hành — rồi kết luận 'hệ khá sạch'. Quên mất lớp sâu hơn: **module Python chỉ có trên một hệ** (fcntl, pwd, grp, termios, msvcrt, winreg). Lệnh thiếu thì mất một chức năng; module thiếu thì CHẾT NGAY LÚC NẠP.

**Danh sách phải rà khi mang hệ sang nền khác**:
1. module chỉ-một-hệ (`import fcntl` …) ← chết ngay lúc nạp
2. lệnh hệ điều hành (`open`, `pgrep`, `osascript`)
3. đường dẫn ghi cứng (`/tmp`, `/Volumes`, `~/.local/bin/…`)
4. cách chạy nền (launchd ↔ Task Scheduler)
5. mã hoá tên tệp (NFD trên macOS ↔ NFC)

**Cách kiểm KHÔNG cần máy kia**: dựng thư mục chứa `fcntl.py` chỉ có một dòng `raise ImportError`, đặt đầu `PYTHONPATH`, rồi nạp thử mọi module. Đúng cái Windows sẽ làm. Nay thành tầng ⑥ của `kiem_tram.py` — và nó bắt được ngay một lỗi mới em vừa tạo (dùng `NT` ở dòng 51, import ở dòng 56).

**Luật**: 'chạy được trên hệ khác' KHÔNG được kết luận bằng đọc mã. Phải nạp thử trong môi trường giả — rẻ, nhanh, và là bằng chứng thật.

## Thứ gì được NẠP MỘT LẦN thì phải tự báo khi lệch bản (15/08/2026)

**Bệnh:** máy phụ `git pull` xong, mã mới nằm sẵn trên ổ, nhưng extension Chrome vẫn chạy
bản cũ. Không báo lỗi, không đỏ chỗ nào — chỉ là tính năng vừa thêm không có. Người ngồi
máy đó báo "em làm theo hướng dẫn mà không thấy gì", còn mình soi mã thì mã đúng.

**Gốc:** extension nạp kiểu "giải nén" — Chrome đọc file MỘT LẦN lúc nạp rồi giữ trong bộ
nhớ. Cùng họ với mọi thứ nạp-một-lần: tiến trình trạm đang chạy (sửa .py không ăn cho tới
khi restart), skill đã nạp vào phiên, cấu hình đọc lúc khởi động.

**Cách phòng:** thứ nào nạp-một-lần thì phải **tự khai phiên bản mình đang chạy** cho phía
còn lại so. Ở đây: `nen.js` gửi `chrome.runtime.getManifest().version` kèm mỗi lượt hỏi
trạm; trạm đọc `manifest.json` trên ổ, lệch thì trả cờ `ext_cu` và extension bật thông báo.
Rẻ (ăn ké lượt gọi đã có sẵn), không cần ai nhớ. Cổng ⑧l canh cả hai vế.

## Chèn khối mã phải neo vào dòng ĐÓNG, không neo vào dòng MỞ (15/08/2026 — vấp lần 4)

**Bệnh:** khối kiểm mới rơi vào giữa lời gọi `_bao(khai == xuly, "...",` — dòng mốc trông
như một câu lệnh hoàn chỉnh nhưng thật ra là dòng ĐẦU của lời gọi nhiều dòng. Kết quả:
SyntaxError, bộ kiểm chết ngay dòng nạp.

**Gốc:** khớp chuỗi không nhìn thấy khối. Cùng họ với bẫy thụt lề đã ghi trước đó.

**Cách phòng:** neo mốc chèn vào dòng có dấu `)` đóng (kết thúc câu lệnh), và **`ast.parse`
ngay trong cùng lệnh chèn** — đừng đợi tới lúc chạy bộ kiểm mới biết.

## Tài liệu cài đặt là MÃ chạy trên máy người khác (15/08/2026)

**Bệnh:** viết xong `cai-windows.ps1` + ba tài liệu hướng dẫn, chạy bộ kiểm ĐẠT HẾT, báo
anh "đã ổn để chạy máy kia". Thực tế lệnh cài chết ngay dòng đầu ở máy đó: nó tải script
từ `raw.githubusercontent.com` của kho RIÊNG TƯ → 404.

**Gốc:** bộ kiểm chỉ soi mã CHẠY TRÊN MÁY NÀY. Tài liệu và bộ cài chạy trên máy KHÁC,
trong môi trường khác, với quyền khác — vùng đó không có cổng nào canh. Và em kiểm
"script có tồn tại, cú pháp trông ổn" chứ không kiểm "giả định nó dựa vào có đúng không".

**Cách phòng:** với mọi thứ chạy ở máy khác, liệt kê GIẢ ĐỊNH rồi biến từng giả định
thành một mục kiểm — kho công khai hay riêng tư · công cụ đã có chưa · quyền đọc/ghi ·
đường dẫn tồn tại không. Tầng ⑦ `tang_may_phu()` làm việc đó. Và khi chưa thử thật được
thì **nói thẳng là chưa thử**, đừng để "ĐẠT HẾT" nghe như đã nghiệm thu.

## Kho riêng tư: cấp khoá đọc, đừng mở Public dù chỉ 5 giây (15/08/2026)

**Cám dỗ:** đổi repo sang Public → clone → đổi lại Private. Nhanh, không phải học gì.

**Vì sao không:** GitHub có luồng sự kiện công khai theo thời gian thực, nhiều bot bám
để hốt kho mới mở. Kho này chứa BRAIN 50 KB, nhật ký, cách vận hành kênh — mã thì thường,
nhưng bí quyết vận hành mới là thứ đáng giá. Và nó không giải quyết gì lâu dài: lần nâng
cấp sau lại phải mở Public lần nữa.

**Đường đúng:** fine-grained PAT — chỉ đúng repo ấy, chỉ quyền `Contents: Read-only`,
có hạn, thu hồi bằng một cú bấm. Cất vào kho khoá của hệ điều hành
(`git credential approve`), KHÔNG nhét vào địa chỉ remote — nhét vào đó thì khoá nằm
chình ình trong `.git/config` và lộ ra mỗi lần `git remote -v`.

**Không tự tạo khoá hộ anh** — đó là chìa khoá tài khoản anh, anh tự bấm, em chỉ đường.

## Đếm-rồi-đặt-tên là lỗi đua ghi kinh điển (16/08/2026)

**Bệnh:** `n = số tệp đang có; ghi tệp thứ n` — chạy một mình thì đúng, chạy song song thì
hai người cùng ra một số rồi đè nhau. Ở hệ này nó gây ra "extension tải ảnh lúc được lúc
không" suốt nhiều ngày, và nặng hơn: khâu chống trùng tưởng ảnh của luồng khác là bản
trùng nên `os.remove` — xoá mất tệp người kia đang đọc.

**Cách phòng — hai lớp, dùng cả hai:**
- **Trong tiến trình**: `threading.Lock` theo THƯ MỤC (không phải khoá toàn cục — hai bài
  khác nhau đừng bắt chờ nhau). Bọc TRỌN khối đọc sổ → ghi tệp → soi trùng → ghi sổ; tách
  nhỏ ra là vẫn hở, vì khâu soi phải thấy đúng thứ khâu ghi vừa làm.
- **Giữa các tiến trình**: xí tên bằng `os.open(p, O_CREAT | O_EXCL)`. Đây là lời hứa của
  hệ điều hành — chỉ MỘT người tạo được, kẻ kia nhận `FileExistsError`. Script chạy tay
  ngoài trạm cũng không giành được.
- Xí chỗ thì phải **TRẢ chỗ**: tấm bị loại (trùng, hỏng, quá nhỏ) mà không xoá tệp rỗng
  thì kho đầy ô ảnh vỡ.

**Glob phải nhìn cả tệp ĐANG LÀM DỞ.** `tay_*.mp4` không khớp `tay_02.f399.mp4.part` —
việc đang chạy trở nên vô hình với việc kế tiếp. Đếm số thì glob theo TIỀN TỐ (`tay_02*`),
đừng theo đuôi.

## Đừng RÌNH trạng thái tức thời — hãy đếm LUỸ KẾ (16/08/2026)

**Bệnh:** trang poll 4 giây hỏi "có đang kéo gì không", thấy chuyển từ >0 về 0 thì nạp lại
kho. Việc kéo một tấm ảnh xong trong chưa tới một giây → poll trượt hoàn toàn → trang
không bao giờ biết có ảnh mới → anh phải F5. Việc CÀNG NHANH càng dễ trượt, nên nó biểu
hiện thành "chập chờn" chứ không phải hỏng hẳn — loại lỗi khó tin nhất.

**Gốc:** trạng thái tức thời là ảnh chụp; ai cũng có thể nhìn trượt giữa hai lần chụp.

**Cách phòng:** phía máy chủ giữ một **số đếm luỹ kế** (đã xong bao nhiêu lượt từ lúc chạy),
phía trang nhớ số lần trước và so. Số luỹ kế không trượt được — dù việc nhanh cỡ nào, dù
poll thưa cỡ nào. Áp cho mọi thứ kiểu "báo cho trang biết có hàng mới".

## Cổng kiểm không được làm bẩn chỗ nó đứng (16/08/2026)

**Bệnh:** cổng ④ gửi một tấm ảnh kiểm vào bài thật để chứng minh cửa nhận còn sống. Nó
dọn tấm ảnh, nhưng quên dọn MỤC VÂN TAY của tấm ấy. Lượt chạy sau, hệ chống trùng nhận
ra "ảnh này có rồi" và từ chối — cổng tự chặn chính mình, báo TRƯỢT một chức năng vẫn
đang tốt.

**Điều đáng nhớ hơn:** lỗi này CÓ SẴN từ lâu mà không lộ, vì trước đó sổ vân tay bị đua
ghi làm mất mục — hai lỗi che nhau. Vá lỗi này làm lộ lỗi kia. **Một cổng đang xanh
không chứng minh nó đúng; có khi nó xanh nhờ một lỗi khác.**

**Cách phòng:** cổng nào ghi vào dữ liệu thật thì phải dọn **đủ mọi dấu vết** — tệp, sổ
phụ, vân tay, chỉ mục. Và luôn **chạy bộ kiểm HAI LẦN LIÊN TIẾP**: lần hai trượt nghĩa
là cổng tự làm bẩn.

## Kiểm tài liệu thì HỎI THỰC TẾ, đừng ghim trạng thái (16/08/2026)

Cổng ⑦ ban đầu ghim cứng "kho là riêng tư nên lệnh cài phải mang khoá". Anh đổi kho sang
công khai là cổng báo trượt một tài liệu đang đúng. Nay nó hỏi thẳng
`gh repo view --json isPrivate` rồi mới đối chiếu. Nguyên tắc chung: **cổng canh sự KHỚP
giữa tài liệu và thực tế, không canh một giá trị cố định** — thực tế thay đổi là chuyện
bình thường, cổng phải đi theo.

## Thứ vào được kho mới tồn tại — lưu vào thư mục bài là chôn nó (16/08/2026)

**Bệnh:** anh gắp 38 video gốc về (3,4 GB) qua nhiều tuần, không tấm nào hiện trong kho.
Không ai báo lỗi, không có gì gãy — chúng chỉ đơn giản là **không tồn tại** với phần còn
lại của hệ, vì cửa gắp video lưu thẳng vào `<bài>/clip/tay/` rồi dừng ở đó.

**Gốc:** trong hệ này, KHO là nơi mọi thứ được nhìn thấy và tra cứu. Cửa nào đưa tài
nguyên vào mà không đi qua khâu nhập kho thì tài nguyên ấy chỉ dùng được đúng một lần,
cho đúng bài đang mở.

**Cách phòng:** thêm cửa nhận tài nguyên mới (ảnh, video, clip, nhạc) thì câu hỏi bắt
buộc là *"cái này có vào kho không?"* — nếu không thì nói rõ vì sao. Và mọi luồng nhập
kho đều gọi hàm nhập CHUẨN, không viết luồng riêng: hàm chuẩn đã mang sẵn ba lớp chống
trùng, nhãn mắt máy, ảnh mồi và ghi sổ — luồng riêng bao giờ cũng thiếu một trong số đó.

**Kèm theo:** thứ nặng thì nhập kho nhưng ĐỪNG đồng bộ lên Drive. Video gốc 100–600 MB
là thứ mỗi máy tự tải lại được; thứ đáng dùng chung là đoạn đã cắt (vài MB) và ảnh.

## `loading="lazy"` chết câm trên lưới VẼ LẠI (16/08/2026)

**Bệnh:** bấm chip lọc, lưới hiện đủ 18 ô video gốc — đúng số, đúng nhãn, đúng thời
lượng — nhưng **không ô nào có ảnh**. Không lỗi console, không 404; server trả ảnh HTTP
200 khi gọi thẳng, tệp trên đĩa đủ 30 KB.

**Gốc:** lưới được dựng lại bằng `innerHTML`. Với ảnh mang `loading="lazy"` trong một
container `overflow-y:auto`, trình duyệt KHÔNG kích hoạt tải cho lứa ảnh vừa chèn — nhìn
bảng network thấy nó vẫn đang tải ảnh của LƯỢT TRƯỚC, còn ảnh đang hiện thì chưa từng
được yêu cầu lần nào.

**Cách phòng:** lazy chỉ dành cho danh sách DÀI và tải THEO CUỘN (lưới ảnh hàng trăm
tấm). Lưới ngắn, vẽ lại theo thao tác, ảnh nhỏ lấy từ localhost thì bỏ lazy — nó không
tiết kiệm gì mà đổi lấy một lỗi câm. Dùng `decoding="async"` nếu vẫn muốn ảnh không chặn
dựng trang.

**Cách phát hiện, đáng nhớ hơn cả cách sửa:** `naturalWidth === 0` trên trang mà tệp vẫn
200 ở server nghĩa là **trình duyệt chưa từng hỏi**, không phải "ảnh hỏng". Đọc bảng
network để thấy nó đang hỏi gì — chính chỗ ấy lộ ra nó hỏi ảnh của lượt cũ. Chỉ nhìn ảnh
chụp màn hình thì rất dễ kết luận nhầm là "đang tải chậm" rồi bỏ qua.

## Hai đường cùng vẽ một vùng thì đường nào cũng phải vẽ ĐỦ (16/08/2026)

**Bệnh:** nút ⇥ vừa ô dùng được đúng một lần rồi biến mất cả buổi. Không lỗi, không
crash — chỉ là nó không bao giờ hiện lại.

**Gốc:** vùng giao diện ấy (dòng chữ độ dài + nút) có HAI đường cập nhật. `capNhatMc()`
vẽ đủ cả hai thứ; `tuDoiThiDenTheo()` chỉ vẽ dòng chữ, bỏ quên cái nút. Mà
`tuDoiThiDenTheo` lại là đường chạy nhiều nhất (mỗi lần tua video). Nút bị ẩn từ lần
bấm trước nên cứ nằm ẩn mãi.

**Cách phòng:** một vùng giao diện chỉ nên có MỘT hàm dựng lại nó; đường nào cần đổi dữ
liệu thì đổi xong gọi hàm ấy, đừng tự vẽ lấy một nửa. Dấu hiệu nhận ra trong lúc đọc mã:
thấy hai chỗ cùng ghi `textContent`/`style.display` cho cùng một phần tử là đã sai rồi.

**Đi kèm — trạng thái DÍNH nguy hiểm hơn trạng thái sai.** `display:none` không tự hết.
Thứ gì bị ẩn theo điều kiện thì mọi đường làm điều kiện ấy đổi đều phải tính lại, không
thì lỗi biểu hiện thành "tính năng biến mất" — kiểu lỗi người dùng khó mô tả nhất và
lập trình viên khó tin nhất.

## Mã ô phụ "5:0" phải tách NGAY TRONG hàm nhận nó (16/08/2026)

`oGiay("5:0")` làm `+"5:0"` → NaN → trả 0. Hàm gọi nó thì có chỗ tách `:` trước (moClip),
có chỗ không (capNhatMc, mcVuaO) — nên tính năng chạy đúng ở cảnh chính, chết câm ở cảnh
phụ. Đúng họ lỗi "cảnh chính có gì cảnh phụ có nấy" mà anh đã dặn bốn lần.

**Luật:** hàm nào nhận mã Ô thì tự chuẩn hoá mã ấy bên trong, đừng bắt nơi gọi nhớ hộ.
Mười nơi gọi là mười cơ hội quên.

## Tự cập nhật thì phải chắc CÓ AI BẬT LẠI (16/08/2026)

Nút "Cập nhật ngay" hoạt động theo lối: kéo mã → **tự thoát** → bộ quản lý dịch vụ bật
lại (mã `.py` chỉ đọc lúc khởi động, không thoát thì mã mới nằm trên ổ mà trạm vẫn chạy
bản cũ trong bộ nhớ).

Điều suýt bỏ sót: **macOS có `KeepAlive` trong plist nên tự bật lại, còn Task Scheduler
trên Windows thì không** — cấu hình đăng ký hôm 15/08 thiếu `RestartCount`. Nếu không rà,
người ngồi máy phụ bấm "Cập nhật ngay" là trạm tắt hẳn, không biết đường bật lại.

**Luật:** thiết kế nào dựa vào "tiến trình tự thoát rồi được bật lại" thì phải kiểm ĐỦ
MỌI NỀN nơi nó chạy, và phải có đường vá cho máy đã cài từ trước — sửa bộ cài không áp
dụng ngược cho máy cài rồi. Cùng họ với bài học "tài liệu cài đặt là mã chạy trên máy
người khác".

## Sổ nào cũng phải ghi ở MỘT CỬA, đừng rải ra 21 nơi (16/08/2026)

**Bệnh:** sổ `VIEC_JOB_MA` (job này thuộc bài nào) lập 14/08 để thanh %% sống lại sau
reload. Lúc ấy vá đúng 4 đường đang cần. Hôm nay đếm ra **21 đường tạo job — 17 đường
chưa bao giờ ghi sổ**. Chúng đẻ job vô danh: trạm biết có việc chạy mà không biết của
bài nào, nên chuỗi xong không báo được cho trang nào.

**Gốc:** vá theo nhu cầu trước mắt thì chỉ đúng cho những đường đang nghĩ tới. Đường thứ
5, thứ 12, và đường thêm tuần sau đều không biết là mình phải ghi sổ.

**Cách phòng:** tìm chỗ MỌI đường bắt buộc đi qua rồi ghi ở đó. Ở đây là hàm trả JSON:
phản hồi nào mang mã job thì ghi sổ, không cần route tự nhớ. Một chỗ, đúng cho cả đường
sẽ viết sau này. Dấu hiệu cần làm vậy: đếm được nhiều hơn 3 nơi phải nhớ cùng một việc.

**Kèm theo — vá xong phải soi lại chính bản vá.** Cửa chung nghĩa là mọi thứ đi qua đó,
kể cả thứ mình không nghĩ tới: một route GET cũng trả khoá `"job"` nhưng là dict, và
kết nối keep-alive dùng lại handler nên dấu vết lượt trước còn dính. Hai lỗi ấy em tự
tìm ra bằng cách đọc lại mã vừa viết, trước khi chúng kịp gây chuyện.

## Đừng viết luồng mới trước khi hỏi "luồng cũ chạy sớm hơn có được không" (16/08/2026)

Anh cần ảnh của bài trước dùng được cho bài sau. Phản xạ đầu tiên là viết một nguồn ứng
viên mới: quét ảnh các bài gần đây, chấm điểm liên quan, thêm ngăn trên giao diện — vài
trăm dòng, thêm một chỗ để hỏng.

Đọc kỹ mới thấy `nhap_kho_chu_the.py` **vốn đã** quét toàn bộ thư mục ảnh của bài, kể cả
tấm chưa dùng. Nó không thiếu năng lực — nó chỉ bị gọi QUÁ MUỘN (lúc xếp kho, tức sau khi
dựng xong hẳn). Việc phải làm là dời MỐC GỌI, không phải viết thêm.

**Câu hỏi nên đặt trước khi thiết kế:** thứ mình cần đã có ai làm được chưa, và nếu có
thì nó đang chạy SAI LÚC hay THIẾU NĂNG LỰC? Sai lúc thì dời mốc — rẻ hơn hàng chục lần
và không đẻ đường thứ hai để sau này lệch nhau.

**Chọn mốc theo THÓI QUEN NGƯỜI DÙNG, không theo sơ đồ kỹ thuật.** Mốc "đổi bài" đắt giá
vì đó đúng là khoảnh khắc anh cần kho đầy — không phải mốc nào đẹp trong luồng dữ liệu.

## Trang báo giấu link video trong JSON-LD, không phải trong thẻ <video> (16/08/2026)

Báo Việt Nam (VnExpress và cùng họ) dựng trình phát bằng JS: thẻ `<video>` chỉ mang
`blob:` — thứ chỉ sống trong tab, tải về là vô nghĩa. Nhưng chúng vẫn phải khai link
thật cho Google hiểu, và chỗ khai đó là khối `<script type="application/ld+json">`,
trường `contentUrl` của `VideoObject`. Đường ấy cho link CDN `.m3u8` tải được thẳng.

**Thứ tự dò nên là:** thẻ `<video>` (http thật) → `og:video` → JSON-LD `contentUrl`.
Và **đừng loại thẻ `<video>` theo kích thước**: trình phát chưa bấm play có `width = 0`.

**Có link media thật thì đưa yt-dlp link ấy, đừng đưa địa chỉ trang.** Đo trên VnExpress:
link JSON-LD ra đúng video 3:20; địa chỉ trang thì yt-dlp mò ra thứ khác, không đọc nổi
thời lượng. Ngược lại với MXH (YouTube, Facebook, TikTok) thì địa chỉ trang tốt hơn hẳn —
yt-dlp có bộ bóc riêng cho từng nền tảng. Nên chọn theo DẠNG của src, không chọn cứng.

## Tính năng "tự đoán" phải thử trên trang thật mới biết đúng sai (16/08/2026)

Hàm dò video viết xong đọc rất hợp lý: ba lớp, chấm điểm, đủ cả. Chạy thử trên một bài
VnExpress thì lộ ngay hai lỗi chí mạng — bộ lọc bề ngang giết mọi video chưa play, và
thứ tự thử của trạm chọn nhầm nguồn. Không thử thì cả hai lỗi ấy đến tay anh.

**Luật:** mã phải ĐOÁN thay người (không có con trỏ chỉ, không có lựa chọn tường minh)
thì bắt buộc thử trên ít nhất một trang thật thuộc đúng họ trang người dùng hay mở —
đọc mã không bao giờ thấy được `width = 0` hay `src` là `blob:`.

## Hai loại tài nguyên, hai cuốn sổ, một phép đếm — là gãy (17/08/2026)

**Bệnh:** ảnh gán cảnh ghi vào `ban_do`; clip gán cảnh ghi vào `clip-canh.json`. Mọi phép
đếm trong trạm chỉ đọc `ban_do`. Kết quả: cảnh chỉ có clip bị coi như trống — cổng duyệt
chặn không cho dựng, bộ đếm báo "12/15" trong khi bài đủ 15/15.

**Gốc:** clip là loại tài nguyên đến SAU. Lúc thêm nó, người viết chỉ lo phần "gán được
và dựng được", quên rằng khắp hệ còn hàng loạt chỗ hỏi câu *"cảnh này đã có gì chưa"* —
và tất cả những chỗ ấy đều đang hỏi sai cuốn sổ.

**Cách phòng:** thêm một LOẠI tài nguyên mới thì phải grep mọi nơi đang trả lời câu hỏi
"cảnh này đã có gì chưa" và cho chúng dùng chung MỘT thước đo. Đây là biến thể của luật
"cảnh chính có gì cảnh phụ có nấy", ở tầng loại tài nguyên thay vì tầng ô.

**Dấu hiệu nhận ra sớm:** thấy nhiều chỗ cùng viết `nh.get("ban_do")` rồi tự đếm — mỗi
chỗ như thế là một nơi sẽ quên loại tài nguyên tiếp theo. Gom về một hàm ngay, đừng chờ
tới lúc nó chặn người dùng giữa việc.

## Cấu hình người dùng đổi thường xuyên thì ĐỌC TƯƠI, đừng nạp lúc khởi động (17/08/2026)

Bản đầu để `DICH_ANH`/`DICH_VIDEO` đọc một lần lúc nạp module — y như các đường dẫn gốc.
Hệ quả: anh đổi đích trên trang là phải khởi động lại trạm mới ăn. Mà restart giữa lúc
đang dựng thì mất bài, nên mỗi lý do phải restart là một cái bẫy chờ sẵn.

**Phân biệt hai loại cấu hình:**
- **Đổi hiếm, ảnh hưởng sâu** (thư mục việc, kho, Drive): nạp lúc khởi động là đúng —
  đổi giữa phiên còn nguy hiểm hơn.
- **Đổi thường, ảnh hưởng một thao tác** (đích lưu, núm vặn): đọc tươi mỗi lượt. Tệp cấu
  hình vài trăm byte, đọc mỗi lần gắp ảnh là chi phí không đáng kể so với việc bắt người
  dùng restart.

Và lời nhắc trên giao diện phải nói đúng loại: nhắc "khởi động lại" cho thứ ăn ngay là
bắt người ta làm việc vô ích, rồi lần sau họ không tin lời nhắc nào nữa.

## Hai bên chưa nhả cổng thì bên mới không bind được — mà launchd vẫn báo "running" (17/08/2026)

Script test restart trạm ba lần trong vài giây. Tiến trình cũ treo, giữ cổng 8756;
tiến trình mới `OSError: [Errno 48] Address already in use` rồi chết. `launchctl print`
vẫn hiện `state = running` (vì launchd đã spawn), nên nhìn vào đó tưởng trạm sống.

**Cách nhận ra:** `curl` không vào được nhưng `lsof -ti :8756` CÓ tiến trình → đó là
tiến trình treo, không phải trạm đang phục vụ. Dọn bằng `lsof -ti :8756 | xargs kill -9`
rồi kickstart lại.

**Cách phòng:** đừng restart liên tiếp trong script test. Tốt hơn: thiết kế sao cho test
KHÔNG CẦN restart (xem bài học "đọc tươi" ở trên) — sửa gốc thay vì chờ giữa các lượt.

## Thêm luật vào prompt thì phải kèm CẦU CHÌ bằng code (18/08/2026)

**Bệnh:** thêm luật 8/9/10 vào prompt gợi từ khoá. Lượt thử đầu model làm đủ, mừng. Lượt
sau — cùng model, cùng prompt, cùng bài — bỏ trắng cả ba. Rồi lượt nữa lại nhét cả ba năm
vào một câu lệnh, đúng con bệnh mà luật vừa thêm sinh ra để chữa.

**Gốc:** model là hàm ngẫu nhiên. Prompt đã dài mười mục thì luật thêm sau nằm cuối, càng
dễ trôi. Không có gì bảo đảm lượt nào cũng nhớ.

**Cách phòng:** luật nào KIỂM ĐƯỢC BẰNG CODE thì phải có cầu chì code chạy sau model —
"câu có ≥2 năm mà không tách" là điều kiện regex, không cần model. Cầu chì phải:
- là **hàm riêng** (kiểm được bằng ca thử; cầu chì không test được là chỗ hỏng thầm lặng)
- **trả về số chỗ đã bù** (đo được mới biết nó có ăn hay nằm im vô ích)
- **không đè khi model đã làm đúng** — chỉ bù chỗ trống
- có ca thử cho cả **chiều ngược**: thứ KHÔNG nên bù thì phải im (câu giá vé không được
  ép sinh câu tìm video)

Đây là dạng cụ thể của luật nền "thứ gì CODE quyết được thì đừng để model quyết".

## Cổng kiểm cắt thân hàm bằng SỐ KÝ TỰ sẽ báo oan (18/08/2026)

Cổng canh whitelist lấy `src[i : i+3000]` từ `def _luu_nhap`. Thêm mấy dòng chú thích vào
hàm ấy là trường cuối bị đẩy ra ngoài cửa sổ → cổng báo TRƯỢT một whitelist vẫn đang đủ.

**Cổng báo oan nguy hơn cổng không có**: nó dạy người ta bỏ qua lời cảnh báo, rồi lần sau
cảnh báo thật cũng bị bỏ qua. Cắt theo **ranh giới cú pháp thật** (`ast.get_source_segment`),
đừng đếm ký tự. Sửa xong cổng ấy bắt được ngay một lỗi thật đang nằm im.

## Phép "dọn dẹp" nào xoá dữ liệu người dùng cũng phải NÓI TO (18/08/2026)

Xưởng có ba phép làm đẹp nhịp: mượn giây hàng xóm, gộp cảnh vụn, bớt khung. Cả ba đều
hợp lý — cảnh dưới 2,5 giây nhìn giật cục thật. Nhưng **gộp cảnh vụn XOÁ HẲN một cảnh**,
và ảnh anh chọn cho cảnh ấy biến mất không một dòng báo.

Anh mô tả bằng cảm giác: *"thi thoảng hay nuốt cảnh bên cạnh"* — cảm giác đúng, mà không
ai chỉ ra được vì log không hề nhắc tới.

**Luật:** thuật toán tối ưu nào ĐỘNG VÀO LỰA CHỌN CỦA NGƯỜI DÙNG (xoá cảnh, bỏ ảnh, đổi
thứ tự) thì phải:
- **đối chiếu vào–ra** rồi in ra chênh lệch, đừng tin là mình làm đúng
- **nói nguyên nhân + cách chữa**, không chỉ kêu "có gì đó bị bỏ"
- **có ngưỡng để KHÔNG tối ưu**: thà cảnh hơi ngắn hơn chuẩn còn hơn mất hẳn một cảnh

## Ưu tiên loại tài nguyên phải áp ở chỗ CHỌN, không chỉ chỗ bảo vệ (18/08/2026)

Nhịp cảnh vốn đã bảo vệ clip rất tốt: không rút giây của clip, không gộp cảnh clip. Nhưng
đo thật thì vẫn có clip bị nuốt — ở chỗ khác hẳn: **clip nằm tại ô PHỤ của một câu ngắn**.
Câu chỉ đủ một khung, khung ấy thuộc ô chính (là ảnh), clip ở ô phụ không có chỗ.

Bảo vệ ở tầng nhịp không cứu được thứ bị loại từ tầng CHỌN Ô. Khi ra luật ưu tiên một
loại tài nguyên, phải rà đủ mọi chỗ tài nguyên ấy có thể bị gạt — không chỉ chỗ dễ thấy.

## Học phong cách của người khác thì mổ ra thành PHẦN, rồi đếm phần mình đã có (18/08/2026)

Anh đưa 20 ảnh bìa của kênh dẫn đầu và bảo "học cách làm". Phản xạ đầu là dựng bộ vẽ mới
từ đầu. Mổ kỹ mới thấy công thức của họ gồm sáu phần, và **năm phần hệ mình đã có sẵn** —
nằm trong khuôn vẽ tiêu đề mà xưởng vẫn dùng cho video. Chỉ thiếu đúng phần bố cục ảnh.

Làm lại cả sáu phần thì vừa tốn, vừa đẻ ra bản thứ hai của thứ đã có (rồi hai bản lệch
nhau). Dùng lại năm phần còn có cái lợi to hơn: **bìa và video cùng một khuôn mặt**, người
xem nhận ra kênh ngay từ ảnh bìa.

**Cách mổ:** liệt kê từng yếu tố nhìn thấy được (màu, vị trí, cỡ chữ, thứ được nhấn), rồi
đối chiếu với mã hiện có — không mô tả cảm tính "trông chuyên nghiệp".

## Điểm cao không có nghĩa là ĐÁNG DÙNG — phải chấm đúng thứ nghề cần (18/08/2026)

Bộ chọn ảnh cho bìa chấm theo kích thước · độ nét · tỷ lệ khung. Ba tiêu chí ấy đều đúng,
và kết quả là bìa lấy phải **ảnh chụp màn hình LED sân vận động** — to, nét, tỷ lệ đẹp,
điểm cao nhất. Nhưng bìa mà không có gương mặt thì không ai bấm vào.

**Tiêu chí đo được dễ (pixel, tỷ lệ) hay lấn át tiêu chí quyết định (có mặt người không).**
Khi chấm điểm để CHỌN, phải hỏi: thứ nghề này thật sự sống bằng gì? Rồi cho tiêu chí ấy
trọng số áp đảo — ở đây là +45 cho ảnh có người, −40 cho đồ hoạ, đủ để lật ngược thứ hạng.

## Điều kiện phân loại phải PHÂN BIỆT ĐƯỢC, không chỉ đúng (18/08/2026)

Bộ chọn kiểu ảnh bìa có luật *"bài có hai đội → kiểu đối đầu"*. Luật ấy **đúng** — bài
đối đầu thì đúng là có hai đội. Nhưng chạy thật thì **8/8 bài cùng ra một kiểu**, vì bài
nào của kênh bóng đá cũng nhắc hai đội (bài nào cũng về một trận).

Một điều kiện đúng mà **mọi mẫu đều thoả** thì không phân loại được gì — nó chỉ làm ra
vẻ có phân loại. Trước khi tin một luật phân loại, phải chạy nó trên chục mẫu thật rồi
**đếm phân bố**: dồn hết vào một nhóm là luật vô dụng, dù logic nghe rất hợp lý.

Ở đây sửa bằng cách siết vào chỗ THẬT SỰ khác nhau: tiêu đề có gọi tên **cả hai bên** không.

## Quét văn bản dài để phân loại là mời từ khoá trúng bừa (18/08/2026)

Bộ chọn quét cả tiêu đề lẫn lời bình. Lời bình dài 60–80 chữ nên hầu như từ khoá nào
cũng xuất hiện đâu đó: 3/8 bài về MỘT nhân vật bị xếp vào kiểu "danh sách nhiều người"
chỉ vì trong lời bình có chữ "bổ sung".

**Phân loại thì đọc chỗ CÔ ĐỌNG NHẤT** — ở đây là tiêu đề. Văn bản dài chỉ dùng cho luật
cần bằng chứng cụ thể (tìm giờ, tìm ngày). Càng nhiều chữ đưa vào bộ khớp từ khoá, tỷ lệ
trúng nhầm càng cao — không phải càng nhiều dữ liệu càng chính xác.

## str.replace KHÔNG có assert = thay trượt im lặng (18/08/2026)

Vá bảy hàm bố cục trong một lượt `str.replace`. Sáu hàm ăn, hàm thứ bảy (`bo_cuc_B`)
trượt vì chuỗi cũ đã đổi ở patch trước — và **không có gì báo**: `replace` không tìm thấy
thì trả nguyên chuỗi cũ, script vẫn in "✅".

Ba mươi phút sau mới lộ ra, nhờ cổng kiểm canh nội dung hàm ấy.

**Luật:** mọi `str.replace` vá mã đều phải kèm `assert <chuỗi cũ> in s` NGAY TRƯỚC nó.
Vá nhiều khối trong một lượt thì mỗi khối một assert — không gộp. Khối dài hoặc đã sửa
nhiều lần thì đừng khớp chuỗi nữa: **cắt theo ranh giới hàm** (tìm `def x(` tới `def`
kế tiếp) rồi thay cả khối, chắc hơn hẳn.

Cùng họ với bài học "cổng cắt thân hàm bằng số ký tự" hôm nay — đều là chuyện **khớp
chuỗi trên mã đang thay đổi thì không đáng tin**.

## Cửa sổ mở ra phải MANG THEO ngữ cảnh, đừng đọc biến toàn cục (18/08/2026)

Cửa soi ảnh quyết định "gán vào đâu" bằng cách đọc biến `dangPhu` — thứ do thao tác
TRƯỚC ĐÓ đặt. Anh vừa đụng ô phụ rồi mở soi ở ô chính là nó gán nhầm, ghi đè mất ảnh đã
chọn. Không báo gì, phải ⌘Z mới cứu được.

**Gốc:** hai việc khác nhau (đang trỏ ô nào · cửa soi mở từ ô nào) dùng chung một biến.
Chúng chỉ tình cờ trùng nhau trong luồng thông thường.

**Cách phòng:** cửa sổ / hộp thoại / chế độ nào mở ra để thao tác lên MỘT đối tượng thì
phải nhận đối tượng ấy làm THAM SỐ, không đọc lại từ biến toàn cục. Biến toàn cục ghi
"đang ở đâu"; tham số ghi "làm cho cái nào" — trộn hai thứ là gán nhầm.

**Dấu hiệu nhận ra:** hàm mở giao diện có ít tham số hơn số thứ nó cần biết, và bù phần
thiếu bằng biến ngoài. Ở đây `moSoi(k, lat)` cần biết ba thứ nhưng chỉ nhận hai.

**Kèm theo — nhãn nút phải nói đúng việc nó sắp làm.** Nút ghi "Gán cho câu 10" nhưng
thật ra gán vào 10b thì người dùng không có cơ hội phát hiện trước khi bấm. Nhãn sai là
lớp phòng vệ cuối cùng bị gỡ mất.

## Thứ đặt lên ảnh phải HỎI ẢNH, đừng đặt theo toạ độ cố định (18/08/2026)

Ô tròn trên ảnh bìa đặt cứng ở góc trên phải — đúng như 20 mẫu tham khảo. Chạy vài bài
thì đè trúng mặt cầu thủ, phá chính cái luật "bìa sống bằng khuôn mặt" mà mình vừa viết.

Mẫu tham khảo đặt được ở góc ấy vì **người ta chọn ảnh trước rồi mới đặt**. Máy thì đặt
trước, không nhìn.

**Luật:** mọi vật thể chồng lên ảnh (ô tròn, nhãn, cờ, huy hiệu, thẻ số liệu) phải chọn
chỗ bằng cách CHẤM ĐIỂM VÙNG rồi né chỗ quan trọng — không dùng toạ độ cố định. Và phải
có **đường lùi cuối**: vướng ở mọi chỗ thì bỏ hẳn vật thể ấy, đừng cố nhét.

**Nhận ra "chỗ quan trọng" không cần AI.** Bài này chỉ dùng hai phép numpy: lọc màu da
(đỏ > lục > lam, chênh vừa phải) và đếm cạnh. Đủ để tách mặt–tay người khỏi cỏ, khán đài,
trời. Trước khi nghĩ tới cài mô hình nhận diện, hãy hỏi: mình cần nhận ra ĐỐI TƯỢNG, hay
chỉ cần biết CHỖ NÀO ĐÔNG THÔNG TIN?

**Vùng do hệ tự vẽ cũng phải khai là vùng cấm.** Logo kênh nằm góc trên trái — ảnh không
"biết" chuyện đó, nên phải cộng điểm cấm bằng tay. Quên bước này thì máy tránh được mặt
người nhưng lại đè lên logo của chính mình.

## Trước khi cài mô hình, hỏi lại mình cần NHẬN RA hay chỉ cần BIẾT CHỖ (18/08)

Sáng 18/08 tôi kết luận "máy không có bộ nhận diện khuôn mặt, cài thêm thì nặng ~200 MB"
rồi viết heuristic đoán bằng màu da. Chiều đi tìm lại thì máy **đã có sẵn cả hai**:
`lama-venv` có OpenCV 4.11 kèm `FaceDetectorYN`, `claude-earth-venv` có rembg và
`~/.u2net/u2net.onnx` (168 MB, tải từ 10/07). Model nhận mặt YuNet chỉ **227 KB**.

**Gốc:** kết luận "không có / quá nặng" rút ra từ trí nhớ, không từ việc đi soi máy.
Trên máy này có mười một venv, mỗi cái dựng cho một skill khác nhau — thứ mình cần
thường đã nằm sẵn trong một cái nào đó.

**Phòng:** trước khi nói "cần cài thêm", chạy đúng một vòng:
`find ~ /Volumes/DATA -maxdepth 4 -name pyvenv.cfg` rồi hỏi từng venv có gói gì. Mất
mười giây, đổi được cả một kết luận.

**Kèm theo:** cần model thì đừng mặc định kéo cả thư viện bọc nó. rembg kéo hàng chục
gói; chạy thẳng `u2net.onnx` bằng onnxruntime chỉ tốn ~30 dòng và dùng lại đúng model
đã tải.

## Đổi THANG ĐO thì phải đổi NGƯỠNG theo — không thì luật chết câm (18/08)

Thay ruột `_ban_do_quan_trong` bằng mắt máy: thang cũ tối đa 3,2 (màu da ×2,2 + cạnh),
thang mới cộng **10,0** cho một khuôn mặt. Hai ngưỡng `0,62` và `0,78` bên dưới vẫn nằm
nguyên — tức là **mọi chỗ đều vượt ngưỡng**, luật "vướng thì bỏ ô tròn" thành luôn đúng.
Không có lỗi nào nổ ra; bìa vẫn ra bình thường, chỉ là sai âm thầm.

**Phòng:** khi hai đường tính cùng nuôi một ngưỡng, bắt cả hai **chia về một thang quy
ước** (ở đây: `1,0 = cấm đè tuyệt đối`), khai hằng số ngay cạnh nhau, và cổng canh sự có
mặt của phép chia. Đã thêm vào `kiem_tram.py` tầng ㉒.

## Cùng một thứ đừng đếm ở hai nơi (18/08)

Khuôn mặt vừa cộng vào lưới, vừa đo bằng giao hộp → góc nào có mặt cũng thành cấm tuyệt
đối, kể cả khi lớp phủ chỉ chạm mép vài chục pixel. Logo cũng vậy: vừa "cộng điểm cho góc
trên trái", vừa đo giao hộp.

**Cách sửa đúng:** thứ nào **biết chắc toạ độ** thì đo bằng hộp (chính xác tới pixel), và
**gỡ hẳn** nó khỏi lưới ước lượng. Lưới chỉ còn lo phần không biết trước.

## write TRƯỚC parse là tự tay ghi ra tệp hỏng (18/08)

Trong một script vá tệp tôi viết `open(p,"w").write(s); ast.parse(s)`. Lần chạy ấy `s`
hỏng cú pháp — parse ném lỗi, nhưng **tệp đã bị ghi đè rồi**. Lần vá sau tưởng đang sửa
bản lành, hoá ra sửa trên bản hỏng, mất thêm ba lượt.

**Luật:** mọi script vá tệp phải `ast.parse(s)` **trước**, `write` **sau**. Không có ngoại lệ.

## Cắt thân hàm bằng đếm ký tự — bệnh này tái phát lần hai (18/08)

`than_o = tn[i_o:i_o + 1500]` báo oan ngay khi tôi thêm bốn dòng chú thích vào `_o_tron`.
Cùng loại với vụ `src[i:i+3000]` sáng cùng ngày. Người sửa sẽ có xu hướng **nới N ra cho
qua** — cổng mất tác dụng mà không ai hay.

**Đã làm:** thêm `_than_ham(nguon, ten)` dùng `ast.get_source_segment`, và chuyển cổng ô
tròn sang dùng nó. Còn năm chỗ khác trong `kiem_tram.py` vẫn cắt bằng đếm ký tự
(dòng ~284, 328, 747, 750, 780) — chuyển dần khi đụng tới.

## Tránh lỗi ≠ đặt đẹp — bộ chấm chỉ biết vế đầu thì vô dụng (18/08, anh bắt lần hai)

Làm xong bộ chấm bìa, tôi báo "đã chấm được thẩm mỹ". Anh nhìn bìa rồi hỏi lại: *"em đang
để sát mép với nền mờ của chữ. vậy QC kinh nghiệm cũng chấp nhận sao? QC phải có thẩm mỹ
cao chứ"*. Anh đúng.

**Bệnh:** bảy thước của tôi có sáu thước đo **lỗi** (mặt bị che, chữ chìm, bìa bệt, lệch
cân) và một thước đo lớp phủ — cũng chỉ hỏi *"có đè lên thứ quan trọng không"*. Ô tròn nép
sát dải chữ **không đè lên gì cả** nên được 10/10, trong khi nhìn vào thì rõ là xấu.

**Gốc:** tôi lấy "không phạm lỗi" làm định nghĩa của "đẹp". Hai thứ đó khác nhau: né hết
mọi thứ quan trọng rồi tấp vào chỗ thừa còn lại thì đúng luật, nhưng chẳng ai bố cục kiểu
ấy. Người có thẩm mỹ **chọn chỗ đẹp trước**, rồi mới tránh; máy của tôi làm ngược lại.

**Phòng — dùng cho mọi bộ chấm về sau:** với mỗi thứ máy đặt lên hình, hỏi đủ hai câu.
① *Có phạm lỗi không?* → đo bằng vùng cấm. ② *Chỗ ấy có phải chỗ ĐẸP không?* → phải có
**dải chuẩn** viết ra thành số (ở đây: tâm ô tròn 60–70% chiều cao tính từ đáy, cách dải
chữ ≥8%). Thiếu câu ② thì bộ chấm chỉ là bộ dò lỗi, đừng gọi nó là chấm thẩm mỹ.

**Và:** dải chuẩn nên làm **RÀNG BUỘC** (ngoài dải thì không được đặt), đừng làm tiêu chí
cộng trừ — để điểm cao ở mục khác không mua chuộc được một chỗ đặt xấu.

## Thông báo lỗi của công cụ ngoài có thể DẪN SAI HƯỚNG (19/08/2026)

**Bệnh:** anh báo extension không tải được video, lỗi *"Requested format is not
available. Use --list-formats"*. Câu ấy chỉ thẳng vào format selector, nên tôi đi soi
selector, soi user-agent, soi cookie, soi PATH — **bốn giả thuyết, trượt cả bốn**.

**Gốc:** yt-dlp cũ năm tháng. YouTube trả về danh sách format rỗng vì công cụ cũ không
qua được lớp chặn; yt-dlp thấy danh sách rỗng thì than "không có format anh yêu cầu" —
đúng về mặt kỹ thuật, sai hoàn toàn về mặt chỉ đường.

**Phòng:**
1. **Khi lỗi đến từ công cụ ngoài, hỏi TUỔI nó trước tiên.** yt-dlp, ffmpeg, trình
   duyệt, thư viện mạng — thứ nào phải chạy đua với một bên đang chủ động chặn thì cũ
   vài tháng là hỏng. Rẻ hơn mọi giả thuyết khác và hay đúng hơn.
2. **Đừng tin thông báo lỗi chỉ đường.** Nó tả TRIỆU CHỨNG ở tầng nó thấy, không phải
   nguyên nhân. Tái hiện thật rồi so hai bên khác nhau chỗ nào — đó mới là bằng chứng.
3. **Bệnh nền phải có cổng canh riêng.** Loại lỗi này không sai dòng mã nào nên không
   cổng nào bắt được; phải viết cổng đo TUỔI công cụ (`kiem_tram.py` tầng ㉓, hạn 60 ngày).
4. **Lỗi hiện cho anh phải dịch sang việc anh làm được.** "Requested format is not
   available" thì anh biết làm gì? Nay là: *"YouTube đang chặn máy tải — chờ vài phút
   rồi thử lại, hoặc dán link khác"*, kèm nhắc nâng cấp nếu công cụ đã quá hạn.

## Thêm luật mới thì phải hỏi: giá trị đó có thể là KIỂU KHÁC không? (19/08/2026)

**Bệnh:** 18/08 tôi thêm hai luật cùng dạng — "ô chính trống thì lấy ô phụ lên", "câu
ngắn thì cho clip lên hình". Cả hai viết `ban_do[i] = _ds[0]` mà không hỏi `_ds[0]` là
CÁI GÌ. Ô phụ chứa được hai kiểu: tên ảnh, và mã clip `clip::tệp::từ::đến`. Bản đồ ảnh
chỉ nuốt được kiểu thứ nhất.

**Vì sao thoát mọi cổng:** mã không sai cú pháp, không sai tên biến, test 18/08 chạy
sạch — vì bài thử hôm ấy ô phụ toàn là ảnh. Lỗi chỉ nổ khi gặp **tổ hợp** "ô chính
trống + ô phụ là clip", và nổ ở chỗ cách nơi gây lỗi cả trăm dòng.

**Phòng — ba việc, làm đủ cả ba:**
1. **Chép một giá trị từ chỗ A sang chỗ B thì hỏi: B nhận được mọi kiểu A có thể mang
   không?** Ở hệ này, chỗ nào chứa "hình" đều có thể là ảnh HOẶC clip — luật anh dặn
   09/08 ("bình đẳng ảnh/clip") chính là chuyện này, tôi quên áp cho luật mới.
2. **Đặt CẦU CHÌ ngay trước chỗ dùng, đừng chỉ vá nhánh ghi.** Nhánh ghi thì còn thêm
   nữa; cầu chì ở cửa ra chặn được cả những nhánh chưa viết. Cầu chì phải **nói ra**
   nó vừa cứu gì (`🔌`), không im lặng.
3. **Test phải có ca TỔ HỢP, không chỉ ca đơn.** "Ô chính trống" tôi có test. "Ô phụ là
   clip" tôi có test. Nhưng hai cái CÙNG LÚC thì không — và đó mới là ca chết.

## Quy trình của anh là SPEC, không phải ngoại lệ (19/08/2026)

**Bệnh:** xưởng chỉ hiểu sổ `ban_do` viết bằng tên trần (`07.jpg` trong `chon/`) — vì
tôi mặc định mọi bài đều đi qua chuỗi tự động có bước xếp kho đổi tên. Anh làm kiểu
khác: tự tìm ảnh, tự gán, bấm Dựng luôn — sổ khi ấy mang giọng `anh/n34.jpg`, xưởng
ghép mù thành `anh/chon/anh/n34.jpg` rồi chết.

**Gốc:** tôi coi luồng tự động là "đường chính" và luồng tay của anh là "đường phụ".
Ngược rồi — **người dùng đi đường nào, đường đó là đường chính.** Hệ có bao nhiêu cửa
ghi vào một sổ thì bộ đọc phải hiểu đủ bấy nhiêu giọng, không được giả định "trước đó
chắc chắn đã chạy bước X".

**Phòng:**
1. **Sổ nào có NHIỀU CỬA GHI thì bộ đọc phải phân giải qua MỘT hàm** hiểu mọi giọng
   (ở đây: `_duong_anh`). Đối chiếu ngay: `anh_phu`, `ghep_canh` đã làm đúng từ đầu —
   bệnh chỉ ở `ban_do` vì nó ra đời sớm nhất, trước khi có giọng thứ hai.
2. **Thêm cửa ghi mới cho một sổ thì rà MỌI BỘ ĐỌC của sổ đó** — máy gán nháp (18/08
   thêm giọng `anh/`) chính là "cửa ghi mới", mà hôm ấy không ai rà xưởng.
3. Tệp trong sổ mất → **kêu to + thay nền, không chết cả bài.** Một tấm ảnh hỏng
   không được giết 60 giây công dựng.

## Nhập một thứ mới vào kho thì thử luôn CA XẤU NHẤT của nó (20/08/2026)

Bản nhạc anh đưa dài 16 giây, kho cũ toàn bản 2–4 phút. Nếu tôi chỉ chép tệp vào kho
rồi báo xong, video sẽ **im tiếng từ giây 16** — mà không lỗi, không cảnh báo, chỉ lộ
khi anh ngồi xem lại.

Cái mới không sai; cái mới chỉ **khác** — và chỗ nó khác là chỗ hệ chưa từng bị thử.
Nhập ảnh khổ lạ, nhạc ngắn, clip dọc, tên có dấu: mỗi thứ đều mang một giả định ngầm
mà hệ cũ chưa bao giờ phải kiểm.

**Cách làm:** trước khi nhập, hỏi *"thứ này khác mọi thứ đang có ở điểm nào?"* rồi thử
đúng điểm đó. Ở đây là ĐỘ DÀI → thử ngay bản 16 giây trên video 62 giây, thấy im tiếng,
sửa gốc (xưởng tự lặp) chứ không chỉ vá bằng cách kéo dài riêng tệp ấy.

**Kèm theo:** nguồn ngoài đưa vào kho phải **mang dấu trong tên** (`-TIKTOK`) và có sổ
nguồn riêng — sau vài tháng không ai nhớ bản nào an toàn, bản nào cần kiểm trước khi đăng.

## Sửa đúng chỗ vừa gãy = mời bệnh quay lại (20/08/2026, lần thứ BA)

"Cắt thân hàm bằng đếm ký tự" đã gãy 18/08 hai lần, 20/08 lần nữa. Mỗi lần tôi sửa
đúng dòng vừa báo oan rồi đi tiếp — nên nó quay lại ở dòng khác, cùng một bệnh.

**Luật rút ra:** sửa xong một lỗi, hỏi ngay *"mẫu sai này còn ở đâu nữa?"* rồi
`grep` cả tệp — thường mất thêm hai phút, và đó là hai phút mua đứt cả họ lỗi.

Lần này: `grep` ra **4 chỗ**, sửa hết, rồi thêm cổng để **bộ kiểm tự soi chính nó** —
hễ ai viết lại `nguon[i:i+N]` là kêu ngay. Bệnh nào tái phát tới lần thứ ba thì đừng
sửa nữa, hãy **dựng cổng chặn cả họ**.

Ghi thêm cho nhớ: **cổng báo oan nguy hơn cổng không có** — nó dạy người ta bỏ qua
lời cảnh báo, và lần sau cổng kêu thật thì không ai tin nữa.

## Cắt danh sách cho gọn thì ô TÌM phải với tới bản đầy đủ (20/08/2026)

Dải thẻ chủ thể cắt top 40 cho gọn mắt — hợp lý. Nhưng ô tìm lại lọc **trên chính 40
tấm đã cắt**, nên 86/126 tên không cách nào tìm ra. Và trang còn hiện dòng "…gõ ô lọc",
tức **mời người dùng làm đúng cái việc không thể ra kết quả**.

**Chỗ đau nhất:** thứ vừa tạo bao giờ cũng ít dữ liệu nhất, nên xếp hạng thấp nhất, nên
bị cắt trước nhất — **đúng lúc cần tìm nhất thì chắc chắn không thấy**. Bệnh này không
lộ ở tên quen (Đình Bắc 143 ảnh, luôn nằm top), chỉ lộ đúng lúc anh vừa lập tên mới.

**Luật:** hễ hiển thị bản CẮT NGẮN của một danh sách, thì ô tìm/lọc của nó phải hỏi
**nguồn đầy đủ**, không được lọc trên bản đã cắt. Rà ngay các dải khác cùng họ (thẻ,
gợi ý, danh sách bài) — cùng một khuôn thì cùng một bệnh.

**Kèm:** giữ nguyên hành vi khi KHÔNG gõ gì (vẫn 40 thẻ). Thêm đường mới mà không đụng
đường cũ thì lỗi không lan — đây là cách sửa rẻ nhất về rủi ro.

## Test phải đi QUA ĐÚNG HÀM sẽ chạy thật, không viết lại logic để thử (20/08/2026)

Thêm cờ `--loc/--so` cho bộ quét nhãn, tôi thử bằng cách VIẾT LẠI phép lọc trong một
script thử — ra số đẹp, báo ổn. Nhưng khối cờ thật đã chèn NHẦM HÀM (thay-chuỗi theo
mẫu `phan = next(...)` có ở hai hàm), nên đường chạy thật không hề đi qua nó: opus
quét 669 tấm thay vì 136.

**Hai luật:**
1. **Thay/chèn mã theo chuỗi thì mẫu phải ĐỘC NHẤT trong tệp** — grep đếm số lần khớp
   trước khi thay; mẫu xuất hiện ≥2 lần thì neo thêm ngữ cảnh (tên hàm, chú thích gần
   đó). Cùng họ với bệnh "cắt thân hàm bằng đếm ký tự" — lần thứ TƯ họ này cắn.
2. **Thử tính năng mới bằng cách gọi ĐÚNG hàm sẽ chạy thật.** Viết lại logic để thử là
   thử cái mình NGHĨ, không phải cái máy SẼ LÀM. Muốn tránh gọi model thật thì vá tạm
   (monkeypatch subprocess) rồi nhìn dòng in đầu — 5 giây, bắt được ngay.

## Tính năng không ai biết = tính năng không tồn tại (20/08/2026)

Gán nhanh nằm trên trạm từ 11/08 với tooltip tử tế — anh CHƯA TỪNG BẤM, vì tooltip chỉ
hiện khi rê chuột đứng yên, mà không ai rê lên nút mình không hiểu. Máy xếp kho dọn cỗ
sau nút đó suốt chín ngày, 0% được dùng.

**Luật:** thứ muốn người dùng DÙNG thì phải tự giới thiệu tại chỗ họ đang đứng (trộn
vào luồng sẵn có, badge ngay trên lưới), không phải chờ họ khám phá. Tooltip là chú
thích cho người ĐÃ tò mò, không phải lời mời.

**Kèm:** thuật toán "đúng" có thể NGƯỢC với người — nhảy "ô trống kế theo vòng" là tối
ưu máy, nhưng người làm tuần tự thấy như bị giật ngược về đầu. Khi máy định làm gì
BẤT NGỜ (nhảy vị trí, đổi ngữ cảnh), thà đứng lại và NÓI một câu còn hơn tự quyết.

## Lỗi giao diện thì mở TRÌNH DUYỆT THẬT, đừng đoán từ mã (20/08/2026)

Anh báo "ảnh vẫn đen, popup tự thoát" — nếu tiếp tục đọc mã để đoán, tôi sẽ sửa sai
lần nữa. Mở Browser pane vào đúng bài của anh, 10 phút ra BA sự thật mã không nói:
- popup tự thoát vì bài chỉ còn 1 ô trống (thiết kế "đi ô trống" lỗi thời khi máy nháp
  phủ sẵn 16/17 ô) — đây là giả thuyết CHỈ dữ liệu thật mới xác nhận được;
- onerror tôi vừa viết hỏng cú pháp mà không có một dòng lỗi console nào — chỉ soi DOM
  (naturalWidth=0, không div báo) + chạy tay attribute mới lộ "missing )";
- ảnh 200 OK mà "đen" = chụp màn lúc chưa tải xong — suýt đi sửa một lỗi không có.

**Luật:** bug giao diện → tái hiện trong trình duyệt thật TRƯỚC khi sửa: đọc DOM
(complete/naturalWidth/offsetHeight), network (status thật từng ảnh), console; và thử
PHÍM THẬT sau khi sửa. Mã nói "phải chạy được"; chỉ trình duyệt nói "có chạy không".

**Kèm hai luật con:**
- Đừng nhét mã vào thuộc tính on* của HTML sinh bằng chuỗi — ba tầng nháy lồng nhau
  hỏng im re. Gắn addEventListener sau render; nhớ nhánh ảnh chết TRƯỚC khi gắn
  (`complete && !naturalWidth`).
- Tính năng "đi ô trống" từng đúng khi ô trống nhiều; máy nháp phủ sẵn làm nó lỗi
  thời. Tính năng phải XÉT LẠI khi bối cảnh dùng đổi, không phải chỉ khi nó gãy.

## "Nhanh hơn" thật sự = bớt việc thừa, rồi mới đến chạy khéo (20/08/2026)

Ba nấc của cùng một bài toán tăng tốc, đúc từ chuỗi hôm nay:
1. **Bớt việc thừa** (tầng A): 90% câu kho đã dày — không tìm web nữa. Ăn nhất,
   rẻ nhất, và chính ANH chỉ ra ("tìm song song thì trùng"), không phải em.
2. **Chạy khéo** (tầng B): hai việc KHÁC tài nguyên thì song song — nhưng chỉ sau
   khi đã bớt thừa, không thì là "làm việc thừa nhanh hơn".
3. **Đổi công cụ** (opus): đo hai lượt trên prompt thật mới dám nói — model TO hơn
   hoá ra NHANH gấp đôi. Trực giác "to = chậm" sai; một phép đo 10 phút cứu khỏi
   một quyết định sai dài hạn.

Kèm: máy được phép nói "không có" (ô trống của model xếp kho) hoá ra là TÍN HIỆU ĐIỀU
PHỐI quý — tầng C dùng chính câu trả lời đó để quyết tìm web bổ sung. Thiết kế cho
máy quyền từ chối không chỉ chống bịa — nó còn cho tầng sau thứ để bám vào.
