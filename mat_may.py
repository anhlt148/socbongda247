#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MẮT MÁY — nhìn một tấm ảnh và trả về HIỂU BIẾT về nó, để lớp phủ biết chỗ nào cấm đè.

Anh hỏi 18/08: "công cụ có nhận diện được mọi thứ trên ảnh, đánh giá chủ thể và vị trí,
chọn chỗ tốt nhất cho lớp phủ không?". Có — và máy đã có sẵn đồ, chỉ chưa nối vào.

TRƯỚC (18/08 sáng): đoán bằng MÀU DA + đếm cạnh. Đoán được, nhưng là đoán — áo hồng,
tường gạch, sân đất đều lọt lưới màu da; mặt nhỏ trong đám đông thì trượt.

NAY: nhìn thật, hai tầng —
  · YuNet (227 KB)  → hộp khuôn mặt + 5 điểm mốc (2 mắt, mũi, 2 khoé miệng), tin cậy 0–1
  · U²-Net (168 KB) → mặt nạ CHỦ THỂ NỔI BẬT từng pixel: đâu là người, đâu là nền

Vì sao là module riêng chứ không viết thẳng vào lam_thumbnail.py: hai thư viện này
KHÔNG cài ở python hệ thống (3.14 chạy trạm/xưởng). Chúng sống trong venv riêng
~/.cache/socbongda247-mat. Module này chạy TRONG venv đó, in JSON ra màn hình; bên kia
gọi qua subprocess. Nhờ vậy venv của LaMa và của Google Earth không bị đụng vào —
luật "không làm hỏng cái đã chạy".

Chạy tay:  ~/.cache/socbongda247-mat/bin/python mat_may.py <ảnh> [--ve ra.jpg]
"""
import hashlib, json, os, sys

VENV = os.path.expanduser("~/.cache/socbongda247-mat")
PY = os.path.join(VENV, "bin", "python")
KHO_MODEL = os.path.expanduser("~/.cache/socbongda247-models")
YUNET = os.path.join(KHO_MODEL, "yunet.onnx")
U2NET = os.path.expanduser("~/.u2net/u2net.onnx")
CACHE = os.path.expanduser("~/.cache/socbongda247-models/nhin")

O_NGANG, O_DOC = 8, 12          # lưới chấm điểm, khớp với _ban_do_quan_trong cũ

# ══════════════════════════════════════════════════════════════════════════════
# PHẦN CHẠY TRONG VENV — cần cv2 + onnxruntime
# ══════════════════════════════════════════════════════════════════════════════

def _tim_mat(im_bgr):
    """Hộp khuôn mặt + điểm mốc. Ngưỡng 0.55: thà bỏ sót mặt mờ còn hơn báo oan cái áo."""
    import cv2
    h, w = im_bgr.shape[:2]
    # ảnh dọc 1080×1920 mà mặt nhỏ thì YuNet dễ trượt → cho nó nhìn ở cỡ vừa
    ty = 1.0
    if max(w, h) > 1280:
        ty = 1280.0 / max(w, h)
        im_bgr = cv2.resize(im_bgr, (int(w * ty), int(h * ty)))
    hh, ww = im_bgr.shape[:2]
    d = cv2.FaceDetectorYN.create(YUNET, "", (ww, hh), 0.55, 0.3, 500)
    _n, f = d.detect(im_bgr)
    ra = []
    if f is None:
        return ra
    for r in f:
        x, y, bw, bh = [float(v) / ty for v in r[:4]]
        ra.append({"x": x, "y": y, "w": bw, "h": bh, "tin": float(r[-1]),
                   "moc": [[float(r[4 + i * 2]) / ty, float(r[5 + i * 2]) / ty]
                           for i in range(5)]})
    ra.sort(key=lambda m: -(m["w"] * m["h"]))
    return ra


def _mat_na_chu_the(im_rgb):
    """Mặt nạ CHỦ THỂ NỔI BẬT bằng U²-Net, trả mảng 0..1 cỡ 320×320.

    Chạy thẳng onnxruntime, KHÔNG qua thư viện rembg — rembg kéo theo cả chục gói mà
    ta chỉ cần đúng một phép chạy model. Model thì đã nằm sẵn ở ~/.u2net từ 10/07.
    """
    import numpy as np, onnxruntime as ort, cv2
    if not os.path.exists(U2NET):
        return None
    x = cv2.resize(im_rgb, (320, 320)).astype(np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], np.float32)) / \
        np.array([0.229, 0.224, 0.225], np.float32)
    x = x.transpose(2, 0, 1)[None]
    s = ort.InferenceSession(U2NET, providers=["CPUExecutionProvider"])
    d0 = s.run(None, {s.get_inputs()[0].name: x})[0][0, 0]
    mi, ma = float(d0.min()), float(d0.max())
    return (d0 - mi) / (ma - mi + 1e-8)


def nhin_that(p):
    """Nhìn một tấm ảnh, trả hiểu biết đầy đủ. CHỈ chạy được trong venv có cv2."""
    import numpy as np, cv2
    im = cv2.imread(p)
    if im is None:
        raise SystemExit(f"không đọc được ảnh: {p}")
    h, w = im.shape[:2]
    rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    mat = _tim_mat(im)
    mn = _mat_na_chu_the(rgb)

    # ── LƯỚI QUAN TRỌNG: chỗ nào tuyệt đối không được đè lớp phủ ────────────────
    q = np.zeros((O_DOC, O_NGANG), np.float32)

    # ① độ chi tiết — nền tảng, nhẹ nhất (số áo, chữ trên áo, hoạ tiết)
    g = cv2.resize(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY),
                   (O_NGANG * 12, O_DOC * 12)).astype(np.float32)
    ct = np.abs(np.diff(g, axis=0, prepend=g[:1])) + \
        np.abs(np.diff(g, axis=1, prepend=g[:, :1]))
    q += np.clip(ct / 42.0, 0, 1).reshape(O_DOC, 12, O_NGANG, 12).mean(axis=(1, 3))

    # ② CHỦ THỂ — người/vật nổi bật. Nặng gấp ~2,5 lần chi tiết.
    luoi_ng = np.zeros((O_DOC, O_NGANG), np.float32)
    if mn is not None:
        import numpy as _n
        mm = cv2.resize(mn, (O_NGANG * 12, O_DOC * 12))
        luoi_ng = mm.reshape(O_DOC, 12, O_NGANG, 12).mean(axis=(1, 3))
        q += luoi_ng * 2.5

    nen = q.copy()      # lưới NỀN: thân người + chi tiết + logo, KHÔNG có khuôn mặt

    # ③ KHUÔN MẶT — thứ giữ chân người xem. Nặng áp đảo, và nới rộng 25% quanh hộp
    #    để chừa tóc, cằm, tai (YuNet chỉ khoanh phần lõi).
    for m in mat:
        nx = m["w"] * 0.25
        ny = m["h"] * 0.25
        c0 = max(0, int((m["x"] - nx) / w * O_NGANG))
        c1 = min(O_NGANG, int(np.ceil((m["x"] + m["w"] + nx) / w * O_NGANG)))
        r0 = max(0, int((m["y"] - ny) / h * O_DOC))
        r1 = min(O_DOC, int(np.ceil((m["y"] + m["h"] + ny) / h * O_DOC)))
        if c1 > c0 and r1 > r0:
            # mặt to thì cấm tuyệt đối; mặt nhỏ (khán giả) cấm nhẹ hơn
            ty = m["w"] * m["h"] / (w * h)
            q[r0:r1, c0:c1] += 10.0 if ty > 0.008 else 3.0

    # ④ GÓC TRÊN TRÁI là chỗ LOGO KÊNH. Ảnh không tự biết, phải khai bằng tay.
    q[:max(1, O_DOC // 7), :max(1, O_NGANG // 4)] += 1.4

    # ── hộp bao chủ thể (dùng cho Nấc ②: chấm bố cục) ──────────────────────────
    hop = None
    if mn is not None:
        ys, xs = (mn > 0.5).nonzero()
        if len(xs) > 40:
            hop = {"x0": float(xs.min()) / 320 * w, "x1": float(xs.max()) / 320 * w,
                   "y0": float(ys.min()) / 320 * h, "y1": float(ys.max()) / 320 * h,
                   "ty_le": float((mn > 0.5).mean())}

    # Logo kênh KHÔNG cộng vào lưới nữa: bên làm bìa biết chắc toạ độ logo và đo
    # thẳng bằng giao hộp. Cộng cả hai nơi là đếm hai lần, góc trái bị loại oan.

    return {"w": w, "h": h, "mat": mat, "luoi": q.tolist(),
            "luoi_nen": nen.tolist(),
            "luoi_nguoi": luoi_ng.tolist(), "chu_the": hop,
            "co_mat_na": mn is not None}


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN GỌI TỪ NGOÀI — chạy ở python hệ thống, không cần cv2
# ══════════════════════════════════════════════════════════════════════════════

def san_sang():
    """Mắt máy dùng được chưa? Thiếu thứ gì thì bên gọi tự lùi về cách đoán cũ."""
    return os.path.exists(PY) and os.path.exists(YUNET)


def nhin(p, dung_cache=True):
    """Nhìn ảnh, trả dict — hoặc None nếu mắt máy chưa sẵn sàng.

    CÓ CACHE vì U²-Net tốn ~1,5 giây. Một tấm ảnh nền được nhiều phương án bìa dùng
    lại, cache làm lượt sau gần như tức thì. Khoá cache = nội dung tệp, nên ảnh sửa
    rồi thì tự tính lại, không cần dọn tay.
    """
    import subprocess
    if not san_sang():
        return None
    try:
        with open(p, "rb") as f:
            khoa = hashlib.md5(f.read()).hexdigest()[:16]
    except OSError:
        return None
    os.makedirs(CACHE, exist_ok=True)
    kp = os.path.join(CACHE, khoa + ".json")
    if dung_cache and os.path.exists(kp):
        try:
            with open(kp, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            pass
    try:
        r = subprocess.run([PY, os.path.abspath(__file__), p],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"  ⚠ mắt máy lỗi: {(r.stderr or '').strip()[:200]}")
            return None
        d = json.loads(r.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        print(f"  ⚠ mắt máy không chạy được ({type(e).__name__}) — lùi về cách đoán cũ")
        return None
    try:
        with open(kp, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except OSError:
        pass
    return d



def nhin_pil(im):
    """Nhìn một ảnh đang nằm trong bộ nhớ (PIL Image) — cho bộ làm bìa gọi giữa chừng.

    Khoá cache tính từ NỘI DUNG ảnh, nên cùng một ảnh nền được nhiều phương án bìa
    dùng lại thì chỉ tốn 1,6 giây cho lượt đầu, các lượt sau gần như tức thì.
    """
    import tempfile
    if not san_sang():
        return None
    try:
        khoa = hashlib.md5(im.convert("RGB").tobytes()).hexdigest()[:16]
    except Exception:
        return None
    os.makedirs(CACHE, exist_ok=True)
    kp = os.path.join(CACHE, khoa + ".json")
    if os.path.exists(kp):
        try:
            with open(kp, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            pass
    fd, tam = tempfile.mkstemp(suffix=".png", prefix="nhin-")
    os.close(fd)
    try:
        im.convert("RGB").save(tam)
        d = nhin(tam, dung_cache=False)
    finally:
        try:
            os.unlink(tam)
        except OSError:
            pass
    if d:
        try:
            with open(kp, "w", encoding="utf-8") as f:
                json.dump(d, f)
        except OSError:
            pass
    return d

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(json.dumps(nhin_that(sys.argv[1])))
