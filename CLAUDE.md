# SÓC BÓNG ĐÁ 247 — DÂY CHUYỀN SẢN XUẤT VIDEO SHORTS

Claude đọc file này đầu mỗi phiên. Đọc xong là biết hệ này là gì, đang ở đâu, và
làm gì thì được, làm gì thì cấm.

**Chủ hệ: Lê Tuấn Anh.** Anh không phải lập trình viên — anh mô tả bằng ngôn ngữ
công việc, việc dịch sang kiến trúc và giữ cho hệ không gãy là việc của Claude.
Anh đã nói thẳng: *"sửa nhiều mệt lắm rồi"* — mỗi lần sửa phải ăn chắc.

---

## LÀM GÌ TRƯỚC KHI GÕ DÒNG CODE ĐẦU TIÊN

**Bắt buộc, không có ngoại lệ** — luật anh chốt 11/08 sau một đêm ba thứ đang chạy
tốt bị làm gãy cùng lúc:

```
Skill: soc-kien-truc-su      ← gọi skill này TRƯỚC, kể cả việc nhìn có vẻ nhỏ
```

Skill nằm ngay trong kho: `.claude/skills/soc-kien-truc-su/`

| đọc gì | để làm gì |
|---|---|
| `KIEN-TRUC.md` | bản đồ hệ — chỗ sắp sửa nằm đâu, đụng những đâu |
| `BRAIN.md` | 50 KB bài học **đã trả giá** — đọc để không giẫm lại |
| `NHAT-KY.md` | ai vừa đụng gì, hôm qua sửa gì |

---

## BA NHỊP CỦA MỌI THAY ĐỔI

### ① Trước khi sửa — rà vùng ảnh hưởng

```bash
grep -rn "<tên hàm|route|biến>" ~/socbongda247 --include="*.py" --include="*.html"
```

Trả lời cho được, viết ra chứ đừng nghĩ thầm:
- **Ai đang dùng thứ này?** Hàm dùng chung sửa một chỗ gãy bốn nơi.
- **Tên định đặt đã có chưa?** Route/hàm trùng tên là **lỗi câm** — không báo gì,
  chỉ âm thầm cướp việc của nhau.
- **Có luồng cũ làm việc này chưa?** Có thì DÙNG LẠI, đừng viết luồng song song.

**Đổi tên tệp / khoá sổ / route thì grep ĐỦ BỐN NƠI** — thiếu một là hỏng:
`~/socbongda247` · `cong-cu/` trên Drive · `~/.claude/skills/` · extension Chrome.

### ② Trong khi sửa — luật cứng

- **KHÔNG `import` trong thân hàm** nếu đầu tệp đã import — Python biến nó thành
  biến cục bộ CẢ HÀM, nhánh khác lăn ra `UnboundLocalError`. Đã gãy 3 lần.
- **Trường sổ mới phải khai vào whitelist `_luu_nhap`** — không khai thì lưu xong MẤT.
- **Cảnh chính có gì, cảnh phụ có nấy.** Nghĩ theo **Ô** = (câu, phần): ô chính mã
  `"3"`, ô phụ mã `"3:0"`. Luật này áp cho cả dòng chảy tài nguyên, không riêng giao diện.
- **Sửa `.py` của trạm thì kiểm cú pháp NGAY**, đừng đợi tới cuối:
  `python3 -c "import ast; ast.parse(open('...').read())"`
- **Việc UI thì phải CHỤP ẢNH NHÌN.** Cú pháp hợp lệ không có nghĩa là trông được.
  Đọc CSS của trang rồi bắt chước khuôn đang dùng, đừng đặt class mới.
- **KHÔNG khởi động lại trạm khi có job đang chạy** — chuỗi sau Duyệt lời là luồng
  bên trong tiến trình trạm, restart là giết nó, không kịp báo gì.
  Kiểm trước: `ps aux | grep "claude -p" | grep -v grep`

### ③ Sau khi sửa — chưa chạy cổng thì CHƯA ĐƯỢC BÁO XONG

```bash
python3 ~/socbongda247/kiem_tram.py --sau
```

Năm tầng: cú pháp · bẫy đã từng gãy · route sống · luồng cốt lõi · chính-phụ tương đương.
**Báo "xong" mà chưa chạy là vi phạm.** Học được bẫy mới thì viết thẳng vào
`kiem_tram.py` — luật phải tự lớn lên.

Rồi ghi **một dòng** vào `NHAT-KY.md`, bài học đáng nhớ thì thêm vào `BRAIN.md` theo
lối *bệnh → gốc → cách phòng*.

---

## HỆ NÀY GỒM GÌ

```
tin  →  viết lời  →  ANH DUYỆT LỜI  →  máy tự chạy 7 bước  →  ANH DUYỆT ẢNH
                                                                    ↓
                        Drive  ←  xếp kho  ←  xem lại  ←  xưởng dựng video
```

| phần | tệp | việc |
|---|---|---|
| **Trạm** | `tram/tram_tai_nguyen.py` (~5500 dòng) | localhost:8756 — anh duyệt lời, gán ảnh, dựng, xếp kho |
| **Xưởng** | `xuong.py` | ráp ảnh + giọng + nhạc + thẻ → video 9:16 |
| **Nhịp cảnh** | `nhip_canh.py` | **một nguồn** chia cảnh — trạm và xưởng cùng đọc |
| **Gợi từ khoá** | `tram/goi_y.py` | mỗi câu ra câu lệnh tìm ảnh (Việt + Anh) |
| **Kho chủ thể** | `nhap_kho_chu_the.py` · `nhap_kho_video.py` | ảnh/video dùng chung, nhãn mắt máy |
| **Đường dẫn** | `duong_dan.py` | **mọi đường khai ở đây**, đọc cấu hình riêng từng máy |
| **Đồng hồ** | `dong_ho.py` | đo thời gian sản xuất từng chặng |
| **Bộ kiểm** | `kiem_tram.py` | cổng hồi quy — chạy trước khi báo xong |

**Dữ liệu KHÔNG nằm trong kho này:** thư mục việc (~7 GB, riêng từng máy), kho tài
nguyên (~1,4 GB, dùng chung qua Drive), khoá (`~/.config/`). Xem `duong_dan.py`.

---

## NGUYÊN TẮC THIẾT KẾ (đã trả giá mới có)

1. **Rẻ trước, model sau** — nhãn giàu làm một lần → luật cứng bằng code → sổ học từ
   quyết định của anh → model cao chỉ cho ca khó. *Nhưng*: "code trước" KHÔNG có nghĩa
   cố đấm ăn xôi bằng code ở việc vốn thuộc về model (phân biệt lớp phủ với vật thể
   trong cảnh, đọc văn bản người viết tự do). Chỗ đúng để tiết kiệm là **gộp câu hỏi
   vào lượt model đã có sẵn**.
2. **Não một nguồn** — luật/từ điển/hồ sơ nằm MỘT chỗ. Không đẻ bản sao; hai bản sẽ lệch.
3. **Cửa duyệt của người** — máy làm nháp, anh chốt. Việc khó hoàn tác phải có đường lùi.
4. **Trung thực hơn đầy đủ** — số liệu mang `chac: cao|vua|thap`; thà thiếu còn hơn sai.
5. **Đo trước khi sửa** — đừng chỉnh theo cảm tính.
6. **Một lệnh, một máy** — việc nặng (ffmpeg, LaMa) phải có khoá.
7. **Hành động huỷ hoại phải đòi bằng chứng** — cắt/xoá/gỡ dựa trên phán đoán của model
   thì bắt nó chép ra bằng chứng cụ thể; phán đoán suông chỉ đủ để cảnh báo.
8. **Máy quét được thì máy quét** — đừng bắt người nhập thứ máy tìm được.

---

## KHI ANH BÁO LỖI

1. **Tái hiện trước, đừng đoán.** Chạy thật, đọc log thật (`/tmp/tram.log`).
2. **Tách tầng**: script chạy tay có lỗi không? Không thì lỗi ở đường gọi (route, UI, quyền).
3. **Sửa GỐC, không vá ngọn.** Hỏi "vì sao lỗi này xảy ra được" trước khi hỏi "sửa sao".
4. **Nói thẳng nguyên nhân**, kể cả khi lỗi là của mình.
5. Thêm cổng chặn vào `kiem_tram.py` nếu lỗi có thể tái phát.

---

## CÀI TRÊN MÁY MỚI

**Windows** — một lệnh trong PowerShell (Run as Administrator):

```powershell
irm https://raw.githubusercontent.com/anhlt148/socbongda247/main/cai-windows.ps1 | iex
```

**macOS** — kho đã sẵn ở `~/socbongda247`; đường dẫn khai trong
`~/.config/socbongda247/may.json`, sửa được ở [trang phong cách](http://localhost:8756/phong-cach)
mục **💻 Máy này** (có nút 🔍 dò hộ).

Chi tiết từng bước, kể cả bẫy Google Drive: [`HUONG-DAN-MAY-MOI.md`](HUONG-DAN-MAY-MOI.md)

---

## LỆNH HAY DÙNG

```bash
python3 ~/socbongda247/kiem_tram.py --sau          # cổng hồi quy — TRƯỚC khi báo xong
python3 ~/socbongda247/xuong.py <mã việc>          # dựng lại một video
python3 ~/socbongda247/nhap_kho_chu_the.py --tinh-hinh   # kho ảnh đã soát tới đâu
launchctl kickstart -k gui/501/com.socbongda247.tram     # khởi động lại trạm (macOS)
```

---

## NHIỀU NGƯỜI CÙNG LÀM

Anh trên Mac, người khác trên máy thứ hai (Windows). **Mã giống hệt nhau trên mọi máy** —
ai sửa đường dẫn trong mã rồi đẩy lên là hai máy lệch ngay.

- **Kho tài nguyên** → Drive, dùng chung: ai bồi ảnh thì cả nhà hưởng
- **Thư mục việc** → ổ máy, riêng từng người: hai người ghi chung một sổ là Drive đẻ bản trùng
- **Thành phẩm** → Drive, dồn một chỗ; mỗi máy khai `nguoi` để hộp khỏi trùng tên

**Chỉ sửa mã ở máy chính.** Máy phụ chỉ `git pull`.
