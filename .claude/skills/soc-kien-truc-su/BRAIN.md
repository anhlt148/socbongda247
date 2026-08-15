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
