# CÀI HỆ SÓC BÓNG ĐÁ 247 TRÊN MÁY MỚI

Tờ này dành cho người ngồi ở **máy Windows** — làm theo đúng thứ tự, mỗi bước một lần
duy nhất. Xong rồi thì hằng ngày chỉ việc mở trạm và làm video.

---

## A. TRƯỚC KHI BẮT ĐẦU — làm ở máy chính (Mac)

Hai việc này **anh Tuấn Anh làm**, không phải người ngồi máy Windows.

### A1. Chia sẻ kho tài nguyên trên Google Drive

Kho tài nguyên là chỗ chứa ảnh, video, nhãn máy đã học — cả nhà dùng chung, ai bồi
thêm thì mọi người hưởng.

1. Mở Google Drive trên web, tìm thư mục **`kho-tai-nguyen`** trong thư mục kênh
2. Chuột phải → **Chia sẻ**
3. Nhập email Google của máy Windows, chọn quyền **Người chỉnh sửa** (Editor)
4. Làm y hệt với thư mục **`kho-video-thanh-pham`** — nơi dồn thành phẩm của cả nhà

### A2. Khoá đọc kho mã — **hiện KHÔNG cần**

Kho mã đang để **công khai** (anh chốt 16/08) nên máy nào cũng kéo được, không cần
đăng nhập hay khoá gì. Bỏ qua mục này.

<details>
<summary>Chỉ mở ra khi kho đã đổi về riêng tư</summary>

Lúc ấy máy chưa có quyền sẽ nhận 404 — GitHub giả vờ như kho không tồn tại. Cấp một
khoá **chỉ đọc, chỉ mở đúng kho này** (đừng đăng nhập tài khoản GitHub của anh trên
máy đó — thế là trao cả tài khoản):

1. Mở [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new)
2. **Token name**: `may-windows-soc` · **Expiration**: 1 year
3. **Repository access** → **Only select repositories** → chọn **`socbongda247`**
4. Khối **Permissions** khởi đầu TRỐNG — bấm **+ Add permissions**, gõ `Contents`,
   đổi thành **Read-only**. GitHub tự thêm kèm **Metadata: Read-only**, cứ để nguyên.
5. **Generate token** → chép chuỗi `github_pat_…` (chỉ hiện một lần)

Rồi cài bằng lệnh mang khoá:

```powershell
$T='github_pat_...'; irm -Headers @{Authorization="Bearer $T"} https://raw.githubusercontent.com/anhlt148/socbongda247/main/cai-windows.ps1 | iex
```

Thu hồi lúc nào cũng được: [Personal access tokens](https://github.com/settings/tokens?type=beta) → **Revoke**.

</details>

### A3. Chép hai tệp khoá

Khoá không nằm trong kho mã (đưa lên là lộ vĩnh viễn). Chép tay qua USB hoặc gửi
riêng — **đừng gửi qua chat công khai**:

| tệp trên Mac | chép sang Windows |
|---|---|
| `~/.config/socbongda247/telebot.json` | `C:\Users\<tên>\.config\socbongda247\telebot.json` |
| `~/.config/vbee/khoa.env` | `C:\Users\<tên>\.config\vbee\khoa.env` |

Thiếu `telebot.json` thì không có báo Telegram. Thiếu `khoa.env` thì không đọc được
giọng VBee — tức không dựng được video.

---

## B. TRÊN MÁY WINDOWS

### B1. Cài bằng một lệnh

Mở **PowerShell** (bấm Start, gõ *PowerShell*, chuột phải → **Run as Administrator**),
dán nguyên dòng này rồi Enter:

```powershell
irm https://raw.githubusercontent.com/anhlt148/socbongda247/main/cai-windows.ps1 | iex
```

Nó tự cài Python, ffmpeg, yt-dlp, Tesseract, Node, Git; kéo mã về; dựng thư mục; đăng
ký trạm tự chạy mỗi khi đăng nhập Windows. Mất khoảng 10–15 phút lần đầu.

Máy nào đã có sẵn thứ gì thì nó bỏ qua thứ đó, không cài lại.

### B2. Đăng nhập Claude

```powershell
claude
```

Đăng nhập bằng **tài khoản của anh Tuấn Anh** — đây là máy thứ hai của anh.

### B3. Nạp extension Chrome

Extension để gắp ảnh từ Google về thẳng kho.

1. Chrome → gõ vào thanh địa chỉ: `chrome://extensions`
2. Bật **Chế độ dành cho nhà phát triển** (góc trên bên phải)
3. Bấm **Tải tiện ích đã giải nén**
4. Chọn thư mục: `C:\Users\<tên>\socbongda247\tram\extension`

### B4. Kéo kho tài nguyên xuống máy — **BƯỚC HAY BỊ VẤP NHẤT**

Thư mục anh chia sẻ ở bước A1 **không tự xuống máy**. Google Drive for Desktop chỉ
đồng bộ thứ nằm trong *Drive của tôi*, còn thứ người khác chia sẻ thì nằm ở
*Được chia sẻ với tôi* — nhìn thấy trên web nhưng **không có trong ổ G:**.

Phải tạo lối tắt:

1. Mở Google Drive trên **web** → mục **Được chia sẻ với tôi**
2. Tìm thư mục **`kho-tai-nguyen`**
3. Chuột phải → **Sắp xếp** → **Thêm lối tắt vào Drive**
4. Chọn **Drive của tôi** → **Thêm**
5. Chờ Google Drive for Desktop đồng bộ (vài phút, kho 1,4 GB)
6. Mở File Explorer, kiểm tra thấy thư mục trong `G:\My Drive\` là được

Làm y hệt với `kho-video-thanh-pham`.

### B5. Trỏ trạm vào kho dùng chung

1. Mở [http://localhost:8756/phong-cach](http://localhost:8756/phong-cach)
2. Kéo xuống mục **💻 Máy này**
3. Ô **Người làm**: gõ tên ngắn để phân biệt (ví dụ `tam`, `quang`) — thành phẩm sẽ
   mang dấu này, nhiều người làm cùng ngày khỏi đè lên nhau
4. Bấm **🔍** cạnh **Kho TÀI NGUYÊN** → chọn dòng có chữ **"trên Drive"**
5. Bấm **🔍** cạnh **Thư mục DRIVE của kênh** → chọn dòng có dấu ✅
6. Bấm **💾 Lưu đường dẫn máy này**
7. Khởi động lại trạm:

```powershell
schtasks /End /TN SocBongDa247-Tram; schtasks /Run /TN SocBongDa247-Tram
```

---

## C. KIỂM TRA XONG CHƯA

Mở PowerShell trong thư mục hệ:

```powershell
cd $env:USERPROFILE\socbongda247; python kiem_tram.py
```

Ra dòng **"✅ ĐẠT HẾT"** là cài xong. Có dòng ❌ thì chụp màn hình gửi anh Tuấn Anh.

---

## D. HẰNG NGÀY

| việc | cách làm |
|---|---|
| Mở trạm | [http://localhost:8756](http://localhost:8756) |
| Trạm không mở được | `schtasks /Run /TN SocBongDa247-Tram` |
| Lấy bản nâng cấp mới của anh | `cd $env:USERPROFILE\socbongda247; git pull; .\capnhat.ps1` |

### Nhận bản nâng cấp — **một lệnh, nó lo đủ ba phần**

```powershell
cd $env:USERPROFILE\socbongda247; git pull; .\capnhat.ps1
```

`capnhat.ps1` kiểm xem có việc nào đang dựng dở không (khởi động lại giữa chừng là
**giết** việc đó), kéo mã, khởi động lại trạm, in ra những gì vừa đổi, rồi chạy bộ kiểm.

Ba phần của một lần nâng cấp — thiếu phần nào cũng thành lỗi âm thầm:

| phần | vì sao cần |
|---|---|
| `git pull` | mã mới về ổ |
| khởi động lại trạm | trạm nạp mã `.py` **một lần** lúc chạy; không restart thì nó vẫn chạy mã cũ trong bộ nhớ |
| nạp lại extension | `git pull` kéo file mới về ổ, nhưng Chrome giữ bản đã nạp cho tới khi bấm ⟳ |

Nạp lại extension: `chrome://extensions` → tìm ô **Sóc Bóng Đá 247** → bấm **⟳** (Tải lại).

Không cần nhớ. Trạm tự so phiên bản: extension chạy bản cũ thì hiện thông báo
*"Extension đang chạy bản cũ — máy có bản X, Chrome đang chạy Y"* ngay lần gắp ảnh kế tiếp.

---

## E. HAI ĐIỀU KHÔNG ĐƯỢC LÀM

**Không sửa mã trên máy này.** Anh Tuấn Anh nâng cấp ở máy Mac rồi đẩy lên; máy này
chỉ `git pull` để nhận. Sửa ở đây thì lần `git pull` sau sẽ đụng nhau và mất công.

**Không dựng cùng một bài với người khác.** Thư mục việc của mỗi máy là riêng, nhưng
nếu hai người cùng mở một bài trên kho chung thì sổ ghi ảnh sẽ giẫm lên nhau. Mỗi
người làm bài của mình.
