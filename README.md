# Sóc Bóng Đá 247 — dây chuyền sản xuất video Shorts

Hệ tự động hoá gần trọn việc làm video bóng đá 55–60 giây: từ tin → lời bình → tìm và
duyệt ảnh → dựng video 9:16 → đóng gói SEO → đẩy lên Drive.

Người dùng chỉ làm hai việc: **duyệt lời** và **duyệt ảnh**. Phần còn lại máy lo.

---

## 🚀 Dán link này vào Claude Code là xong

Mở Claude Code, dán:

```
https://github.com/anhlt148/socbongda247
```

Rồi nói việc cần làm bằng tiếng Việt bình thường:

| nói thế này | Claude sẽ làm |
|---|---|
| *"cài hệ này lên máy tôi"* | kéo mã, cài công cụ, dựng thư mục, bật trạm |
| *"trạm không mở được"* | soi log, tìm nguyên nhân, sửa, chạy cổng kiểm |
| *"ảnh tìm về không khớp nội dung"* | chẩn đoán bộ gợi từ khoá, sửa gốc, đo lại |
| *"thêm cho tôi tính năng X"* | vào cửa kiến trúc sư, rà vùng ảnh hưởng, làm, kiểm |

Claude tự đọc [`CLAUDE.md`](CLAUDE.md) — biết kiến trúc, biết luật đã trả giá, biết phải
chạy cổng hồi quy trước khi báo xong.

> **Kho này RIÊNG TƯ.** Dán link cho một phiên Claude chưa có quyền thì nó chỉ thấy 404 —
> GitHub giả vờ như kho không tồn tại. Máy mới phải cài bằng khoá đọc trước (bên dưới);
> **cài xong rồi thì Claude đọc mã ngay tại máy**, không cần link nữa.

---

## Cài trên máy mới

**Windows** — PowerShell (Run as Administrator):

```powershell
$T='github_pat_...'; irm -Headers @{Authorization="Bearer $T"} https://raw.githubusercontent.com/anhlt148/socbongda247/main/cai-windows.ps1 | iex
```

Kho **riêng tư** — `$T` là khoá chỉ-đọc anh cấp cho máy đó ([cách tạo](HUONG-DAN-MAY-MOI.md#a2-tạo-khoá-đọc-kho-mã--bước-bắt-buộc-thiếu-là-không-cài-được)).
Không có khoá thì GitHub trả 404, cả lệnh này lẫn `git clone` đều chết.

**macOS**:

```bash
git clone https://github.com/anhlt148/socbongda247.git ~/socbongda247
cd ~/socbongda247 && python3 kiem_tram.py
```

Từng bước chi tiết, kể cả bẫy Google Drive: [`HUONG-DAN-MAY-MOI.md`](HUONG-DAN-MAY-MOI.md)

---

## Dây chuyền

```
   tin  →  viết lời bình  →  ANH DUYỆT LỜI
                                   ↓
        máy tự chạy: gợi cụm tô vàng · thẻ số liệu · card đồ hoạ
                     · tìm ảnh (Việt + Anh) · xếp kho theo nghĩa
                     · đề xuất khung đôi · gán nháp · mắt máy soi lại
                                   ↓
                            ANH DUYỆT ẢNH
                                   ↓
    xưởng dựng 9:16  →  xem lại  →  xếp kho  →  Drive
```

Đo thật trên một video: **48 phút 55 giây** từ lúc mở việc tới lúc lên Drive, trong đó
duyệt ảnh chiếm **71%** — nút thắt là mắt người, không phải máy.

## Bên trong

| phần | việc |
|---|---|
| **Trạm** `localhost:8756` | duyệt lời · gán ảnh từng cảnh · dựng · xếp kho · kho ảnh dùng chung |
| **Xưởng** | ráp ảnh + giọng VBee + nhạc theo cảm xúc + thẻ số liệu → video dọc |
| **Kho chủ thể** | ảnh/video đã trả giá một lần, gắn nhãn bằng mắt máy, tra theo nội dung |
| **Extension Chrome** | gắp ảnh từ Google về thẳng kho, chống trùng bằng vân tay |
| **Bộ kiểm hồi quy** | năm tầng cổng chặn — mọi bẫy từng gãy đều có cổng canh |

## Nguyên tắc

**Rẻ trước, model sau** · **Não một nguồn** · **Máy làm nháp, người chốt** ·
**Trung thực hơn đầy đủ** · **Đo trước khi sửa**

Bài học đã trả giá nằm trong [`.claude/skills/soc-kien-truc-su/BRAIN.md`](.claude/skills/soc-kien-truc-su/BRAIN.md) —
50 KB, mỗi mục là một lần hệ gãy thật và cách phòng.

---

Kho riêng tư. Dữ liệu (thư mục việc, kho tài nguyên, khoá) không nằm ở đây — xem
`duong_dan.py`.
