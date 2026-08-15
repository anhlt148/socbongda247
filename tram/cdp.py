#!/usr/bin/env python3
"""TRÌNH DUYỆT THẬT — lái Chrome bằng CDP, chỉ dùng thư viện chuẩn của Python.

Vì sao KHÔNG dùng Chrome headless: đo ngày 04/08/2026 — `--headless --dump-dom` vào Google
ảnh thì Google trả về đúng một trang reCAPTCHA (6.991 byte, không có lấy một ảnh); vào Bing
ảnh thì lưới kết quả nạp sau bằng JavaScript nên bản đổ DOM chỉ có phần khung. Trình duyệt
THẬT (có cửa sổ, có hồ sơ riêng lưu cookie) thì cả hai nơi đều trả kết quả bình thường.
Anh chốt 04/08: "Nguồn ảnh: dùng TRÌNH DUYỆT THẬT mở Google ảnh gắp về".

Và KHÔNG bao giờ giải CAPTCHA. Gặp CAPTCHA thì dừng, báo người — đó là luật, không phải
giới hạn kỹ thuật.

Vì sao tự viết WebSocket: playwright/selenium đều CHƯA cài trên máy này, mà cài thêm một bộ
thư viện nặng chỉ để mở trang thì không đáng (luật "hiệu quả tối đa – tài nguyên tối thiểu").
Bắt tay WebSocket + đóng/mở khung tin là khoảng 70 dòng, đủ dùng cho việc mở trang và chạy JS.

Hồ sơ Chrome RIÊNG (`~/.config/socbongda247/chrome-tram`), cổng gỡ lỗi RIÊNG (9334) — không
đụng vào Chrome hằng ngày của anh, cũng không đụng hai cổng 9222/9223 của bot CSKH.

Thử nhanh:  python3 cdp.py "https://www.google.com/search?q=test&udm=2"
"""
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CONG = 9334
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import duong_dan as _DD                                   # noqa: E402
HO_SO = _DD.CHROME_HO_SO        # nằm ở ổ DATA — hồ sơ này phình tới 542 MB (đo 05/08)
TIEN_ICH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extension")

# Anh hỏi 05/08: "sao không mở tab tìm kiếm ngay trong Chrome đang mở mà lại mở Chrome khác?"
# → Trạm DÒ TRƯỚC các cổng gỡ lỗi đang mở; thấy Chrome nào đang bật sẵn thì mở tab NGAY TRONG
# đó. Không thấy cái nào mới bật Chrome riêng của trạm. Muốn dùng Chrome hằng ngày của anh thì
# bấm "MỞ CHROME CHO TRẠM.command" — nó bật lại Chrome thường kèm cổng 9334, từ đó mọi lần tìm
# đều mở tab ngay trong cửa sổ anh đang dùng.
# (Chrome KHÔNG mở được cổng gỡ lỗi cho một tiến trình đã chạy sẵn — bắt buộc phải bật kèm cờ.)
CONG_DO = [CONG, 9222, 9223]


# ── WebSocket tối giản (phía khách) ──────────────────────────────────────────
class WS:
    def __init__(self, url, timeout=30):
        rest = url.split("://", 1)[1]
        hostport, path = rest.split("/", 1)
        host, cong = hostport.split(":")
        self.s = socket.create_connection((host, int(cong)), timeout=timeout)
        self.s.settimeout(timeout)
        khoa = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\n"
                        f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {khoa}\r\nSec-WebSocket-Version: 13\r\n\r\n"
                        ).encode())
        dem = b""
        while b"\r\n\r\n" not in dem:
            m = self.s.recv(4096)
            if not m:
                raise ConnectionError("Chrome đóng kết nối khi bắt tay WebSocket")
            dem += m
        if b" 101 " not in dem.split(b"\r\n")[0]:
            raise RuntimeError("bắt tay WebSocket hỏng: " + dem.split(b"\r\n")[0].decode())
        self.dem = dem.split(b"\r\n\r\n", 1)[1]

    def _doc(self, n):
        while len(self.dem) < n:
            m = self.s.recv(65536)
            if not m:
                raise ConnectionError("Chrome đóng kết nối giữa chừng")
            self.dem += m
        ra, self.dem = self.dem[:n], self.dem[n:]
        return ra

    def _khung(self, opcode, data):
        dau = bytes([0x80 | opcode])
        n = len(data)
        if n < 126:
            dau += bytes([0x80 | n])
        elif n < 65536:
            dau += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            dau += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mk = os.urandom(4)                                   # khung của KHÁCH bắt buộc che
        return dau + mk + bytes(b ^ mk[i % 4] for i, b in enumerate(data))

    def gui(self, text):
        self.s.sendall(self._khung(0x1, text.encode()))

    def nhan(self):
        """Gộp cả khung bị chẻ — trả lời CDP dài (DOM, ảnh) hay bị chẻ làm nhiều khung."""
        gop = b""
        while True:
            b0, b1 = self._doc(2)
            fin, op, n = b0 & 0x80, b0 & 0x0F, b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._doc(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._doc(8))[0]
            body = self._doc(n) if n else b""
            if op == 0x8:
                raise ConnectionError("Chrome gửi khung đóng")
            if op == 0x9:                                     # ping → pong
                self.s.sendall(self._khung(0xA, body))
                continue
            if op == 0xA:
                continue
            gop += body
            if fin:
                return gop.decode("utf-8", "ignore")

    def dong(self):
        try:
            self.s.close()
        except Exception:
            pass


# ── Chrome ───────────────────────────────────────────────────────────────────
def _hoi(duong, cach="GET", cong=CONG, timeout=6):
    r = urllib.request.Request(f"http://127.0.0.1:{cong}/json{duong}", method=cach)
    with urllib.request.urlopen(r, timeout=timeout) as res:
        return json.loads(res.read().decode())


def dang_song(cong=CONG):
    try:
        _hoi("/version", cong=cong, timeout=2)
        return True
    except Exception:
        return False


def tim_cong():
    """Cổng của Chrome ĐANG MỞ sẵn, nếu có — để mở tab ngay trong cửa sổ anh đang dùng."""
    for c in CONG_DO:
        if dang_song(c):
            return c
    return None


def bat(cong=CONG, cho=25):
    """Bật Chrome (CÓ cửa sổ) nếu chưa chạy. Đã chạy rồi thì dùng lại, không bật thêm."""
    if dang_song(cong):
        return True
    os.makedirs(HO_SO, exist_ok=True)
    if not os.path.exists(CHROME):
        raise RuntimeError(f"không thấy Chrome ở {CHROME}")
    # Nạp thẳng tiện ích gắp ảnh vào Chrome của trạm (anh chốt 06/08 — anh không tìm ra thư mục
    # để cài tay, mà cài tay thì mỗi lần dựng lại hồ sơ Chrome là mất, phải cài lại).
    # Nạp bằng cờ thì tiện ích có mặt mọi lần trạm mở Chrome, không cần ai làm gì.
    cac_co = [CHROME, f"--remote-debugging-port={cong}", f"--user-data-dir={HO_SO}",
              "--no-first-run", "--no-default-browser-check", "--disable-features=Translate",
              "--password-store=basic", "--window-size=1280,900", "--window-position=60,60"]
    # Chỉ NẠP THÊM, không dùng --disable-extensions-except: cờ đó tắt mọi tiện ích khác trong
    # hồ sơ, mai kia anh cài thêm thứ gì vào Chrome của trạm là mất mà không hiểu vì sao.
    if os.path.isfile(os.path.join(TIEN_ICH, "manifest.json")):
        cac_co.append(f"--load-extension={TIEN_ICH}")
    subprocess.Popen(
        cac_co + ["about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True)
    het = time.time() + cho
    while time.time() < het:
        if dang_song(cong):
            time.sleep(1.2)                                   # cho cửa sổ đầu ổn định
            return True
        time.sleep(0.4)
    raise RuntimeError(f"Chrome không mở được cổng gỡ lỗi {cong} sau {cho} giây")


def tat(cong=CONG):
    subprocess.run(["pkill", "-f", f"remote-debugging-port={cong}"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Tab:
    """Một thẻ Chrome. Dùng theo kiểu `with Tab() as t:` để chắc chắn đóng lại."""

    def __init__(self, cong=None, timeout=30):
        cong = cong or tim_cong() or CONG          # có Chrome mở sẵn thì vào thẳng đó
        bat(cong)
        self.cong = cong
        t = _hoi("/new?about:blank", "PUT", cong)
        self.id = t["id"]
        self.ws = WS(t["webSocketDebuggerUrl"], timeout)
        self._n = 0
        self.goi("Page.enable")
        self.goi("Runtime.enable")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.dong()

    def goi(self, cach, **tham_so):
        self._n += 1
        ma = self._n
        self.ws.gui(json.dumps({"id": ma, "method": cach, "params": tham_so}))
        while True:                                           # bỏ qua sự kiện, chờ đúng id
            d = json.loads(self.ws.nhan())
            if d.get("id") == ma:
                if "error" in d:
                    raise RuntimeError(f"{cach}: {d['error'].get('message')}")
                return d.get("result", {})

    def js(self, bieu_thuc, timeout_s=25):
        r = self.goi("Runtime.evaluate", expression=bieu_thuc, returnByValue=True,
                     awaitPromise=True, timeout=int(timeout_s * 1000))
        if r.get("exceptionDetails"):
            raise RuntimeError("JS lỗi: " + json.dumps(r["exceptionDetails"])[:200])
        return r.get("result", {}).get("value")

    def di(self, url, cho=18, lang=0.8):
        """Mở trang rồi CHỜ nạp xong. Chờ theo readyState chứ không ngủ mò một khoảng cố định."""
        self.goi("Page.navigate", url=url)
        het = time.time() + cho
        while time.time() < het:
            try:
                if self.js("document.readyState") == "complete":
                    break
            except Exception:
                pass
            time.sleep(0.3)
        time.sleep(lang)                                      # cho JS nạp nốt phần lười
        return self

    def bam(self, x, y):
        """Bấm chuột THẬT tại toạ độ. `element.click()` bằng JS không đánh thức được những
        trang bắt sự kiện chuột ở tầng dưới — Google ảnh là một trong số đó."""
        for loai in ("mousePressed", "mouseReleased"):
            self.goi("Input.dispatchMouseEvent", type=loai, x=x, y=y,
                     button="left", clickCount=1, buttons=1)
        return self

    def o_cua(self, chon, thu=0):
        """Toạ độ giữa của phần tử thứ `thu` khớp bộ chọn — để bấm chuột thật vào đó."""
        return self.js(f"""(() => {{
          const ds = [...document.querySelectorAll({json.dumps(chon)})];
          const e = ds[{int(thu)}]; if (!e) return null;
          const r = e.getBoundingClientRect();
          if (r.width < 8 || r.height < 8) return null;
          return {{x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2)}};
        }})()""")

    def cuon(self, lan=3, nghi=1.0):
        """Cuộn xuống để lưới ảnh nạp thêm — Google/Bing đều nạp lười theo cuộn."""
        for _ in range(lan):
            try:
                self.js("window.scrollBy(0, window.innerHeight*0.9)")
            except Exception:
                break
            time.sleep(nghi)
        return self

    def dinh_captcha(self):
        """Có CAPTCHA thì DỪNG và báo người — tuyệt đối không tự giải."""
        try:
            return bool(self.js(
                "!!(document.querySelector('form#captcha-form, .g-recaptcha, iframe[src*=recaptcha]'))"
            ))
        except Exception:
            return False

    def dong(self):
        try:
            self.ws.dong()
            urllib.request.urlopen(f"http://127.0.0.1:{self.cong}/json/close/{self.id}",
                                   timeout=4).read()
        except Exception:
            pass


# ── một thẻ dùng chung, KHÔNG đóng sau mỗi lần tìm ───────────────────────────
# Anh muốn nhìn thấy nó đang tìm gì; mở-đóng thẻ liên tục thì cửa sổ nhấp nháy, mà lần nào
# cũng dựng lại kết nối cũng chậm hơn. Giữ một thẻ, hỏng thì tự dựng lại.
_THE = None
_KHOA = threading.Lock()


def the_dung_chung(timeout=30):
    global _THE
    with _KHOA:
        if _THE is not None:
            try:
                _THE.js("1")                       # còn sống không
                _THE.goi("Page.getNavigationHistory")   # thử thêm một lượt: gửi được nhưng
                return _THE                              # phía kia đã đóng thì lỗi lộ ra đây
            except Exception:
                try:
                    _THE.dong()
                except Exception:
                    pass
                _THE = None
        _THE = Tab(timeout=timeout)
        return _THE


def bo_the():
    global _THE
    with _KHOA:
        if _THE is not None:
            try:
                _THE.dong()
            except Exception:
                pass
            _THE = None


if __name__ == "__main__":
    import sys
    u = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com/search?q=test&udm=2"
    print("cổng đang dùng:", tim_cong() or f"(chưa có Chrome nào mở — sẽ tự bật cổng {CONG})")
    with Tab() as t:
        t.di(u)
        print("tiêu đề:", t.js("document.title"))
        print("CAPTCHA:", t.dinh_captcha())
        print("số ảnh trong DOM:", t.js("document.images.length"))
