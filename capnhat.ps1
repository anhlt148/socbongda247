# ═══════════════════════════════════════════════════════════════════════════
#  NHẬN BẢN NÂNG CẤP  —  chạy trên máy Windows mỗi khi anh Tuấn Anh đẩy bản mới
#
#      cd $env:USERPROFILE\socbongda247; .\capnhat.ps1
#
#  Nó lo BA phần, vì nâng cấp không phải chỉ có `git pull`:
#      ① kéo mã mới        ② khởi động lại trạm    ③ nhắc nạp lại extension
#  Bỏ sót phần nào cũng thành lỗi ÂM THẦM: trông vẫn chạy, chỉ thiếu đúng cái
#  tính năng vừa thêm.
# ═══════════════════════════════════════════════════════════════════════════
$ErrorActionPreference = "Continue"
$NHA = "$env:USERPROFILE\socbongda247"

function Buoc($n, $t) { Write-Host "`n[$n] $t" -ForegroundColor Cyan }
function Xong($t)     { Write-Host "    OK  $t" -ForegroundColor Green }
function Nhac($t)     { Write-Host "    !   $t" -ForegroundColor Yellow }

Write-Host "`n==== NHAN BAN NANG CAP ====" -ForegroundColor Yellow

if (-not (Test-Path "$NHA\.git")) {
    Write-Host "    Chua co ma o $NHA. Chay bo cai truoc." -ForegroundColor Red
    exit 1
}

# ── 1. CÓ AI ĐANG DỰNG DỞ KHÔNG ─────────────────────────────────────────────
# Chuỗi sau Duyệt lời là luồng BÊN TRONG tiến trình trạm. Khởi động lại giữa
# chừng là giết nó, không kịp báo gì — anh Tuấn Anh đã mất một bài vì chuyện này.
Buoc 1 "Xem co viec nao dang chay khong"
$dangChay = Get-Process -Name "claude" -ErrorAction SilentlyContinue
if ($dangChay) {
    Nhac "Dang co viec chay nen (claude). Doi no xong roi hay cap nhat."
    $tra = Read-Host "    Van cap nhat? Go 'co' de tiep, Enter de dung"
    if ($tra -ne "co") { Write-Host "    Da dung. Chay lai sau." -ForegroundColor Yellow; exit 0 }
} else { Xong "khong co viec nao dang chay" }

# ── 2. KÉO MÃ MỚI ───────────────────────────────────────────────────────────
Buoc 2 "Keo ma moi ve"
$truoc = (git -C $NHA rev-parse --short HEAD)
git -C $NHA pull --ff-only
$sau = (git -C $NHA rev-parse --short HEAD)
if ($truoc -eq $sau) { Xong "da la ban moi nhat ($sau) — khong co gi doi" }
else {
    Xong "$truoc -> $sau"
    Write-Host "`n    Thay doi:" -ForegroundColor Cyan
    git -C $NHA log --oneline "$truoc..$sau"
}

# ── 3. KHỞI ĐỘNG LẠI TRẠM ───────────────────────────────────────────────────
# Trạm nạp mã .py MỘT LẦN lúc khởi động. Không restart thì mã mới nằm trên ổ mà
# trạm vẫn chạy mã cũ trong bộ nhớ.
Buoc 3 "Khoi dong lai tram"
schtasks /End /TN SocBongDa247-Tram 2>$null | Out-Null
Start-Sleep -Seconds 2
schtasks /Run /TN SocBongDa247-Tram 2>$null | Out-Null
Start-Sleep -Seconds 4
try {
    $r = Invoke-RestMethod -Uri "http://localhost:8756/api/may" -TimeoutSec 10
    Xong "tram song lai"
} catch {
    Nhac "Tram chua len. Thu: schtasks /Run /TN SocBongDa247-Tram"
}

# ── 4. EXTENSION ────────────────────────────────────────────────────────────
# Extension nạp kiểu "giải nén": Chrome đọc file MỘT LẦN lúc nạp rồi giữ trong
# bộ nhớ. git pull ve file moi ma Chrome van chay ban cu cho toi khi bam tai lai.
Buoc 4 "Extension Chrome"
$mf = "$NHA\tram\extension\manifest.json"
if (Test-Path $mf) {
    $pb = (Get-Content $mf -Raw | ConvertFrom-Json).version
    Nhac "Ma extension tren o dang la ban $pb."
    Write-Host "    Mo chrome://extensions -> tim 'Soc Bong Da 247' -> bam nut tai lai (vong tron)."
    Write-Host "    Khong nho cung khong sao: tram tu bao khi Chrome chay ban cu."
}

# ── 5. BẢO ĐẢM TRẠM TỰ BẬT LẠI ──────────────────────────────────────────────
# Trạm có nút "Cập nhật ngay": nó kéo mã rồi TỰ THOÁT để nạp lại. Task đăng ký trước
# 16/08 không có thiết lập tự bật lại, nên thoát là chết luôn. Vá tại chỗ, chạy lại
# nhiều lần cũng không sao.
Buoc 5 "Bao dam tram tu bat lai sau khi thoat"
try {
    $t = Get-ScheduledTask -TaskName "SocBongDa247-Tram" -ErrorAction Stop
    if ($t.Settings.RestartCount -lt 1) {
        $t.Settings.RestartCount = 999
        $t.Settings.RestartInterval = "PT1M"
        Set-ScheduledTask -TaskName "SocBongDa247-Tram" -Settings $t.Settings | Out-Null
        Xong "da bat che do tu khoi dong lai"
    } else { Xong "da co san" }
} catch { Nhac "khong doc duoc Task SocBongDa247-Tram: $_" }

# ── 6. CỔNG KIỂM ────────────────────────────────────────────────────────────
Buoc 6 "Chay bo kiem hoi quy"
python "$NHA\kiem_tram.py"

Write-Host "`nXong. Mo tram: http://localhost:8756`n" -ForegroundColor Green
