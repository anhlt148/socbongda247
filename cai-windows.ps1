# ═══════════════════════════════════════════════════════════════════════════
#  CÀI HỆ SÓC BÓNG ĐÁ 247 TRÊN MÁY WINDOWS  —  anh chốt 15/08/2026
#
#  Chạy MỘT LẦN trên máy mới. Mở PowerShell (chuột phải > Run as Administrator)
#  rồi dán nguyên dòng này:
#
#      irm https://raw.githubusercontent.com/anhlt148/socbongda247/main/cai-windows.ps1 | iex
#
#  Hoặc nếu đã tải mã về rồi:  .\cai-windows.ps1
#
#  Nó làm hết: cài công cụ, kéo mã về, dựng thư mục, đăng ký chạy nền, kiểm tra.
#  Thứ DUY NHẤT phải làm tay là chép hai tệp khoá — script sẽ nhắc đúng lúc.
# ═══════════════════════════════════════════════════════════════════════════
$ErrorActionPreference = "Stop"
$KHO  = "https://github.com/anhlt148/socbongda247.git"
$NHA  = "$env:USERPROFILE\socbongda247"
$CH   = "$env:USERPROFILE\.config\socbongda247"

function Buoc($n, $t) { Write-Host "`n[$n] $t" -ForegroundColor Cyan }
function Xong($t)     { Write-Host "    ✅ $t" -ForegroundColor Green }
function Nhac($t)     { Write-Host "    ⚠  $t" -ForegroundColor Yellow }
function Chet($t)     { Write-Host "    ❌ $t" -ForegroundColor Red; exit 1 }

Write-Host "`n════ CÀI HỆ SÓC BÓNG ĐÁ 247 ════" -ForegroundColor Yellow

# ── 1. CÔNG CỤ ───────────────────────────────────────────────────────────────
# winget có sẵn trên Windows 10/11 bản mới. Mỗi thứ đều KIỂM TRƯỚC khi cài —
# máy đã có rồi thì bỏ qua, khỏi mất mười phút chờ vô ích.
Buoc 1 "Công cụ nền (Python · ffmpeg · yt-dlp · tesseract · Node · Git)"
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Chet "Máy chưa có winget. Cài 'App Installer' từ Microsoft Store rồi chạy lại."
}
$goi = @(
    @{ ten = "Python";     lenh = "python";    id = "Python.Python.3.12" },
    @{ ten = "Git";        lenh = "git";       id = "Git.Git" },
    @{ ten = "ffmpeg";     lenh = "ffmpeg";    id = "Gyan.FFmpeg" },
    @{ ten = "yt-dlp";     lenh = "yt-dlp";    id = "yt-dlp.yt-dlp" },
    @{ ten = "Tesseract";  lenh = "tesseract"; id = "UB-Mannheim.TesseractOCR" },
    @{ ten = "Node.js";    lenh = "node";      id = "OpenJS.NodeJS.LTS" }
)
foreach ($g in $goi) {
    if (Get-Command $g.lenh -ErrorAction SilentlyContinue) { Xong "$($g.ten) — đã có" }
    else {
        Write-Host "    … đang cài $($g.ten)"
        winget install --id $g.id -e --silent --accept-package-agreements `
            --accept-source-agreements | Out-Null
        Xong "$($g.ten) — vừa cài"
    }
}
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [Environment]::GetEnvironmentVariable("Path", "User")

# ── 2. MÃ NGUỒN ──────────────────────────────────────────────────────────────
Buoc 2 "Kéo mã về $NHA"
if (Test-Path "$NHA\.git") {
    git -C $NHA pull --ff-only | Out-Null
    Xong "đã có sẵn — vừa cập nhật bản mới nhất"
} else {
    git clone $KHO $NHA | Out-Null
    Xong "đã kéo về"
}
python -m pip install --quiet --upgrade pip pillow numpy 2>$null
Xong "thư viện Python (pillow · numpy)"

# ── 3. CLAUDE ────────────────────────────────────────────────────────────────
Buoc 3 "Claude Code"
if (Get-Command claude -ErrorAction SilentlyContinue) { Xong "đã có" }
else {
    npm install -g @anthropic-ai/claude-code 2>$null | Out-Null
    if (Get-Command claude -ErrorAction SilentlyContinue) { Xong "vừa cài" }
    else { Nhac "chưa cài được — chạy tay: npm install -g @anthropic-ai/claude-code" }
}
Nhac "Lát nữa mở PowerShell gõ 'claude' rồi đăng nhập bằng tài khoản của anh."

# ── 4. THƯ MỤC VÀ ĐƯỜNG DẪN ─────────────────────────────────────────────────
# Ổ chứa việc: ưu tiên ổ D (thường là ổ dữ liệu), không có thì dùng C.
Buoc 4 "Thư mục làm việc"
$o = if (Test-Path "D:\") { "D:" } else { $env:USERPROFILE }
$viec = "$o\socbongda247\viec"
New-Item -ItemType Directory -Force -Path $viec, $CH | Out-Null
Xong "thư mục việc: $viec"

# Drive: tìm ổ đã gắn của Google Drive for Desktop
$drive = $null
foreach ($d in @("G:", "H:", "I:")) {
    foreach ($m in @("$d\My Drive", "$d\Drive của tôi")) {
        if (Test-Path $m) { $drive = $m; break }
    }
    if ($drive) { break }
}
if ($drive) { Xong "Google Drive: $drive" }
else { Nhac "Chưa thấy Google Drive for Desktop — mở nó lên rồi vào trang phong cách bấm 🔍 Dò" }

$cauHinh = @{
    _ghi_chu = "Cấu hình RIÊNG máy này. Không lên git, không lên Drive."
    nguoi    = $env:USERNAME
    viec     = $viec
}
if ($drive) { $cauHinh["drive"] = $drive }
$cauHinh | ConvertTo-Json | Set-Content -Encoding UTF8 "$CH\may.json"
Xong "đã ghi cấu hình máy: $CH\may.json"

# ── 5. KHOÁ ─────────────────────────────────────────────────────────────────
# Khoá KHÔNG nằm trong kho code (lỡ đưa lên là lộ vĩnh viễn). Chép tay từ máy anh.
Buoc 5 "Hai tệp khoá — phải chép tay từ máy chính"
$thieu = @()
if (-not (Test-Path "$CH\telebot.json"))                 { $thieu += "$CH\telebot.json" }
if (-not (Test-Path "$env:USERPROFILE\.config\vbee\khoa.env")) {
    $thieu += "$env:USERPROFILE\.config\vbee\khoa.env" }
if ($thieu.Count -eq 0) { Xong "đã có đủ" }
else {
    Nhac "Còn thiếu — chép từ máy Mac sang đúng chỗ này:"
    $thieu | ForEach-Object { Write-Host "         $_" -ForegroundColor Yellow }
    Write-Host "         (thiếu telebot.json thì không có báo Telegram;" -ForegroundColor DarkGray
    Write-Host "          thiếu khoa.env thì không đọc được giọng VBee)" -ForegroundColor DarkGray
}

# ── 6. CHẠY NỀN ─────────────────────────────────────────────────────────────
# macOS dùng launchd, Windows dùng Task Scheduler. Trạm phải tự bật khi đăng nhập,
# không thì mỗi lần khởi động máy lại phải nhớ mở tay.
Buoc 6 "Đăng ký trạm tự chạy khi đăng nhập"
$tenTask = "SocBongDa247-Tram"
$py = (Get-Command python).Source
schtasks /Query /TN $tenTask 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { schtasks /Delete /TN $tenTask /F | Out-Null }
$hd = New-ScheduledTaskAction -Execute $py `
        -Argument "`"$NHA\tram\tram_tai_nguyen.py`"" -WorkingDirectory $NHA
$kh = New-ScheduledTaskTrigger -AtLogOn
$ct = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName $tenTask -Action $hd -Trigger $kh -Settings $ct `
    -Description "Trạm duyệt tài nguyên — Sóc Bóng Đá 247" -Force | Out-Null
Start-ScheduledTask -TaskName $tenTask
Xong "đã đăng ký + bật ngay ($tenTask)"

# ── 7. KIỂM ─────────────────────────────────────────────────────────────────
Buoc 7 "Kiểm lại"
Start-Sleep -Seconds 5
try {
    Invoke-WebRequest "http://localhost:8756/api/may" -UseBasicParsing -TimeoutSec 10 | Out-Null
    Xong "trạm đang chạy: http://localhost:8756"
} catch {
    Nhac "trạm chưa trả lời — xem lỗi bằng: python `"$NHA\tram\tram_tai_nguyen.py`""
}

Write-Host "`n════ XONG ════" -ForegroundColor Green
Write-Host @"

CÒN BA VIỆC LÀM TAY (mỗi việc một lần):

 1. Đăng nhập Claude — mở PowerShell, gõ:  claude
 2. Nạp extension Chrome:
      Chrome > chrome://extensions > bật "Chế độ dành cho nhà phát triển"
      > "Tải tiện ích đã giải nén" > chọn thư mục:
      $NHA\tram\extension
 3. Trỏ KHO TÀI NGUYÊN vào Drive dùng chung:
      Mở  http://localhost:8756/phong-cach  > mục 💻 Máy này
      > bấm 🔍 cạnh "Kho TÀI NGUYÊN" > chọn dòng có chữ "trên Drive"
      > 💾 Lưu > khởi động lại trạm

Mở trạm:  http://localhost:8756
"@ -ForegroundColor White
