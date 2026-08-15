#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NỀN TẢNG — một nơi lo mọi khác biệt giữa macOS và Windows.

Anh chốt 15/08: hệ chạy trên máy thứ hai (Windows) cho người khác làm cùng. Rà thật
mới lộ ra trạm KHÔNG khởi động nổi bên đó — `import fcntl` là ImportError ngay dòng
đầu, vì fcntl chỉ có trên Unix.

Bài học: rà "lệnh hệ điều hành" thôi chưa đủ, phải rà cả **module chỉ có trên một hệ**.
Nay mọi chỗ ấy gom về đây — thêm hệ mới thì sửa MỘT tệp, không đi lùng khắp nơi.

Bốn thứ nền tảng:
  · khoa_ghi()   — khoá tệp khi ghi sổ (fcntl trên Unix, msvcrt trên Windows)
  · tim_claude() — đường tới Claude CLI, mỗi hệ một chỗ
  · thu_muc_tam()— chỗ ghi log tạm (/tmp trên Unix, %TEMP% trên Windows)
  · WINDOWS      — cờ để chỗ nào cần thì rẽ nhánh
"""
import os
import shutil
import sys
import tempfile

WINDOWS = os.name == "nt"
MAC = sys.platform == "darwin"

try:                                    # Unix
    import fcntl as _fcntl
except ImportError:                     # Windows
    _fcntl = None
try:                                    # Windows
    import msvcrt as _msvcrt
except ImportError:                     # Unix
    _msvcrt = None


class khoa_ghi:
    """Khoá tệp trong lúc ghi — chống hai tiến trình giẫm lên sổ của nhau.

    Dùng như câu lệnh `with`, thay cho lối cũ mở tệp rồi gọi fcntl.flock tay:

        with khoa_ghi(duong_so):
            ... đọc sổ, sửa, ghi lại ...

    Khoá đặt trên tệp `<sổ>.lock` chứ không trên chính sổ — ghi sổ theo lối
    ghi-tệp-tạm-rồi-đổi-tên (an toàn khi mất điện), mà đổi tên thì khoá trên sổ
    cũ bay mất. Khoá riêng một tệp thì không dính chuyện đó.

    Hệ nào không khoá được (không có cả fcntl lẫn msvcrt) thì vẫn CHO CHẠY —
    thà chấp nhận rủi ro hiếm còn hơn chặn cả dây chuyền vì một cơ chế phòng xa.
    """

    def __init__(self, duong_so, cho=True):
        self.p = duong_so if str(duong_so).endswith(".lock") else f"{duong_so}.lock"
        self.cho = cho
        self.f = None

    def __enter__(self):
        os.makedirs(os.path.dirname(self.p) or ".", exist_ok=True)
        self.f = open(self.p, "a+")
        try:
            if _fcntl:
                _fcntl.flock(self.f, _fcntl.LOCK_EX if self.cho else
                             (_fcntl.LOCK_EX | _fcntl.LOCK_NB))
            elif _msvcrt:
                # msvcrt khoá theo BYTE, không khoá cả tệp như flock — khoá 1 byte
                # đầu là đủ, vì mọi tiến trình đều khoá đúng byte ấy.
                self.f.seek(0)
                _msvcrt.locking(self.f.fileno(),
                                _msvcrt.LK_LOCK if self.cho else _msvcrt.LK_NBLCK, 1)
        except OSError:
            if not self.cho:
                self.f.close()
                self.f = None
                raise
        return self.f

    def __exit__(self, *_):
        if not self.f:
            return False
        try:
            if _fcntl:
                _fcntl.flock(self.f, _fcntl.LOCK_UN)
            elif _msvcrt:
                self.f.seek(0)
                _msvcrt.locking(self.f.fileno(), _msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        self.f.close()
        return False


_CLAUDE = None


def tim_claude():
    """Đường tới Claude CLI. Nhớ lại sau lần đầu — khỏi dò mỗi lượt gọi.

    Trước đây 7 tệp ghi cứng `~/.local/bin/claude`; trên Windows nó nằm chỗ khác
    hẳn, nên mọi việc cần mắt máy (gợi từ khoá, gắn nhãn ảnh, xếp kho theo nghĩa)
    đều chết câm. Nay hỏi một chỗ.
    """
    global _CLAUDE
    if _CLAUDE:
        return _CLAUDE
    ung = [os.path.expanduser("~/.local/bin/claude"),
           "/opt/homebrew/bin/claude", "/usr/local/bin/claude"]
    if WINDOWS:
        ung = [os.path.expandvars(r"%APPDATA%\npm\claude.cmd"),
               os.path.expandvars(r"%APPDATA%\npm\claude"),
               os.path.expanduser(r"~\AppData\Roaming\npm\claude.cmd")] + ung
    _CLAUDE = next((p for p in ung if os.path.exists(p)),
                   shutil.which("claude") or "claude")
    return _CLAUDE


def thu_muc_tam(ten=""):
    """Chỗ ghi log/tệp tạm — `/tmp` trên Unix, `%TEMP%` trên Windows.

    Truyền `ten` thì trả luôn đường đầy đủ và tạo sẵn thư mục cha.
    """
    goc = tempfile.gettempdir()
    if not ten:
        return goc
    p = os.path.join(goc, ten)
    os.makedirs(os.path.dirname(p) or goc, exist_ok=True)
    return p


def dang_chay(ten_tien_trinh):
    """Có tiến trình nào mang tên này đang chạy không — thay cho `pgrep -f`.

    Windows không có pgrep. Dùng tasklist / ps tuỳ hệ; hỏng thì trả None chứ đừng
    trả False — "không biết" khác "chắc chắn không có", và nhiều chỗ trong hệ dựa
    vào câu trả lời này để quyết có chạy trùng hay không.
    """
    import subprocess
    try:
        if WINDOWS:
            r = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                               capture_output=True, text=True, timeout=20)
        else:
            r = subprocess.run(["ps", "ax"], capture_output=True, text=True, timeout=20)
        return ten_tien_trinh.lower() in (r.stdout or "").lower()
    except Exception:
        return None


if __name__ == "__main__":
    print(f"  hệ        : {'Windows' if WINDOWS else 'macOS' if MAC else 'Linux'}")
    print(f"  khoá tệp  : {'fcntl' if _fcntl else 'msvcrt' if _msvcrt else 'KHÔNG CÓ'}")
    print(f"  claude    : {tim_claude()}")
    print(f"  thư mục tạm: {thu_muc_tam()}")
