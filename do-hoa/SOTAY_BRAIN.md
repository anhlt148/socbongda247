# BRAIN — lam-card-do-hoa

Sổ bài học của skill (theo luật tự học trong `~/.claude/CLAUDE.md`). Đọc trước khi chạy, cập nhật sau khi chạy. Bài học chưa chắc/nhạy cảm → ghi `hoc-cho-duyet.md` chờ duyệt.

## Bài học đã kiểm chứng
_(chưa có — ghi dần sau mỗi lần chạy)_

## Lỗi đã gặp + cách né
_(chưa có)_

## Nhật ký cập nhật
- 30/07/2026: khởi tạo sổ theo đợt vá luật tự học cho toàn bộ skill.

## Timeline: chữ mốc phải ở yên "phần đất" của mốc (08/08/2026)
Anh bắt 2 lỗi ở card timeline: (1) mốc đầu/cuối căn giữa mù quáng → nửa chữ văng ra ngoài
khung; (2) sau khi kẹp vào lề toàn khung thì chú thích dài của 2 mốc trườn về giữa ĐÈ NHAU.
Luật đúng: mỗi mốc có vùng [điểm-giữa-với-mốc-trước, điểm-giữa-với-mốc-sau] — chữ (cả năm
lẫn chú thích) wrap theo bề rộng vùng và kẹp tâm trong vùng đó. Kèm: cỡ chữ năm 54→62,
chú thích 30→38 (anh chê nhỏ).

## 5 nền random (anh đặt 08/08/2026)
NEN = navy/tím/rêu/vang/than — đều nền tối để chữ trắng + accent đỏ kênh nổi như nhau.
Máy rút thăm mỗi card, không lặp nền của card LIỀN TRƯỚC trong cùng lần chạy;
spec["nen"] ép tay được. Đừng thêm nền sáng — chữ trắng của mọi loại card sẽ chìm.

## Khổ card 4:3 + cờ tự nhận (anh chốt 08/08/2026)
- Card 16:9 vào khung video dọc là thừa cả mảng nền trên dưới → đổi W,H = 1440×1080 (4:3),
  card chiếm 810px dải ảnh thay vì 607px, chữ nhìn lớn hẳn. Mọi toạ độ layout theo % nên
  không phải sửa từng card.
- Cờ TỰ NHẬN từ chữ trên thẻ (tim_co + dan_hang_co): timeline lấy từ tít, stat từ
  nhãn/ghi chú, BXH + versus tra theo TÊN từng dòng (flag_img đã nhận tên tiếng Việt).
  KHONG_TU_QUET = {anh, y/ý, my, ma, lao} — trùng từ tiếng Việt thường, các nước đó
  muốn cờ phải khai "flag" tay. Logo liên đoàn/CLB + áo đấu CHƯA làm (cần kho asset
  riêng + cân nhắc bản quyền) — đừng hứa với anh là tự có.

## BXH: máy tự sắp hạng + số liệu phải chính thống (anh bắt 08/08/2026)
Card BXH từng vẽ Indonesia 7 điểm ĐỨNG TRÊN Singapore 8 điểm vì máy vẽ tin mù thứ tự đầu
vào. Hai luật: (1) card_leaderboard tự sắp value giảm dần (sắp ổn định — bằng điểm giữ thứ
tự người khai vì họ đã xếp theo hiệu số; bảng cố ý khác điểm thì khai "giu_thu_tu": true);
(2) SỐ LIỆU BXH không được bịa/nhớ mang máng — tra nguồn chính thống (báo lớn, trang giải)
rồi mới điền. Bảng A ASEAN Cup 2026 chung cuộc đã kiểm chứng 08/08: VN 10 (3T1H, hòa 0-0
Singapore) · Singapore 8 (2T2H) · Indonesia 7 (2T1H1B) · Campuchia 3 (chỉ thắng Timor 3-0)
· Timor Leste 0.

## Kẹp vị trí thôi CHƯA đủ — cỡ chữ cũng phải theo đất (anh bắt lần hai 08/08/2026)
Vá lần 1 kẹp toạ độ chữ mốc vào phần đất nhưng vẫn dùng CỠ CỨNG 62 — mốc dài
("Trận Campuchia - Mỹ Đình") chữ to hơn cả đất, kẹp kiểu gì cũng tràn. Luật đủ hai vế:
fit_font theo bề rộng đất TRƯỚC, kẹp toạ độ SAU. Kèm vá gốc: prompt goi_y_card bắt tên
mốc ≤16 ký tự, chi tiết dài đẩy xuống chú thích.
Bài học kiểm thử: vá lỗi tràn phải thử bằng CHUỖI DÀI NHẤT có thể gặp, không phải chuỗi
mẫu ngắn — lần 1 em thử "ASEAN Cup 2024" nên không lộ.

## Khung chống vỡ ba tầng cho MỌI chữ trên card (anh chốt 08/08/2026)
Anh yêu cầu "đúng trên mọi cỡ chữ, số từ, mượt trong mọi tình huống" — vá theo từng ca là
chạy theo đuôi lỗi mãi. Khung chung áp cho cả 5 loại card:
  ① fit_font co cỡ theo bề rộng CHO PHÉP (có min_size đọc được, không co vô hạn);
  ② co hết cỡ vẫn tràn → cat_ngan cắt "…" (vua_hoac_cat gộp ①+②);
  ③ chữ nhiều → wrap có toi_da dòng, dòng cuối "…";
kèm các guard dữ liệu: rows/points rỗng → bỏ qua êm; value không phải số ("3-1") →
_so_an_toan trả None → không sort, không vẽ vạch tỉ lệ, chỉ ghi chữ; đông hàng → cỡ chữ,
cờ, vạch co theo khe (min(46, gap×0.52)).
Đã tra tấn 6 ca cực đoan (tít 90 ký tự, 5 mốc tên dài, BXH 9 hàng, value chuỗi, note dài,
tên đội siêu dài) — không ca nào tràn/đè/sập. Luật kiểm thử: mỗi lần sửa layout phải chạy
lại BỘ TRA TẤN này, không thử mỗi ca đẹp.
