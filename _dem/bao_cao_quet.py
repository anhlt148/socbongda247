#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BÁO CÁO ĐÊM QUÉT NHÃN KHO — anh dậy là đọc được ngay, không phải hỏi.

Đọc sổ kho (`so-chu-the.jsonl`) + log đêm, dựng báo cáo theo lối anh chốt 03/08:
KẾT LUẬN trước, số liệu sau, và nói rõ điểm mù.
"""
import json, os, re, sys, collections, datetime as dt

KHO = "/Volumes/DATA/socbongda247/kho-tai-nguyen/anh-chu-the"
SO = os.path.join(KHO, "so-chu-the.jsonl")


def doc_so():
    ds = []
    for l in open(SO, encoding="utf-8"):
        try:
            ds.append(json.loads(l))
        except ValueError:
            pass
    # sổ ghi nối đuôi — bản ghi SAU đè bản trước cho cùng một tấm
    m = {}
    for d in ds:
        if d.get("tep"):
            m[d["tep"]] = {**m.get(d["tep"], {}), **d}
    return list(m.values())


def bao_cao(log=None):
    so = doc_so()
    n = len(so)
    mat = collections.Counter(d.get("soat_model") or
                              ("cũ (không rõ mắt)" if d.get("da_soat") else "CHƯA AI NHÌN")
                              for d in so if not d.get("nguoi_duyet"))
    chac = collections.Counter((d.get("soat_chac") or "—") for d in so
                               if not d.get("nguoi_duyet") and d.get("da_soat"))
    duyet = sum(1 for d in so if d.get("nguoi_duyet"))
    chu = collections.Counter((d.get("chu_the") or "").strip() for d in so
                              if (d.get("chu_the") or "").strip())

    r = []
    A = r.append
    A("# BÁO CÁO ĐÊM QUÉT NHÃN KHO ẢNH")
    A("")
    chua = mat.get("CHƯA AI NHÌN", 0)
    yeu = chac.get("thap", 0) + chac.get("vua", 0)
    A(f"**Kết luận:** kho {n} tấm — còn **{chua} tấm chưa ai nhìn**, "
      f"**{yeu} tấm nhãn chưa chắc**, {chu and len(chu) or 0} chủ thể được gọi tên.")
    A("")
    if log and os.path.exists(log):
        t = open(log, encoding="utf-8").read()
        me = re.findall(r"mẻ \d+: chữa (\d+)/(\d+)", t)
        if me:
            capnhat = sum(int(a) for a, _ in me)
            xem = sum(int(b) for _, b in me)
            nghi = [d for d in so if d.get("soat_nghi")]
            A("## Đêm nay máy làm gì")
            A("")
            A(f"- Soi **{xem} tấm** qua {len(me)} mẻ")
            A(f"- Ghi lại nhãn cho **{capnhat} tấm** "
              f"({capnhat/max(1,xem)*100:.0f}% số tấm đã soi)")
            A(f"- Trong đó **{len(nghi)} tấm máy đọc ra TÊN KHÁC HẲN** tên đang ghi "
              f"— đây mới là chỗ nhãn cũ nhiều khả năng sai")
            A("")
            A("> Lưu ý cách đọc: \"ghi lại nhãn\" **không đồng nghĩa** \"nhãn cũ sai\" — "
              "máy ghi lại cho mọi tấm nó nhìn, kể cả tấm vốn đã đúng. Con số đáng lo là "
              "dòng thứ ba.")
            A("")
            if nghi:
                A("**Vài tấm máy nghi tên sai — anh liếc qua rồi quyết:**")
                A("")
                # Gộp theo CẶP (tên đang ghi → tên máy đọc ra): sáu tấm cùng một bài mà
                # in sáu dòng giống hệt nhau thì anh đọc không ra vấn đề gì.
                cap = collections.Counter()
                for d in nghi:
                    may = (d.get("soat_nghi") or "").replace("mắt máy đọc ra:", "").strip()
                    cap[(d.get("chu_the") or "(trống)", may)] += 1
                for (cu, may), sl in cap.most_common(10):
                    A(f"- **{cu}** → máy đọc ra **{may}** · {sl} tấm")
                A("")
    A("## Kho giờ ra sao")
    A("")
    A("| mắt đã nhìn | số tấm |")
    A("|---|---|")
    for k, v in mat.most_common():
        A(f"| {k} | {v} |")
    A(f"| (anh duyệt tay, miễn soát) | {duyet} |")
    A("")
    if chac:
        A("**Máy tự chấm độ chắc của nhãn:**")
        A("")
        ten = {"cao": "nhìn rõ, nhãn chắc", "vua": "có người mà không dám gọi tên",
               "thap": "ảnh mờ/khuất, nên để mắt tinh nhìn lại"}
        for k, v in chac.most_common():
            A(f"- **{v}** tấm — {k} · {ten.get(k, '')}")
        A("")
    A("## Kho biết những ai (12 chủ thể nhiều ảnh nhất)")
    A("")
    for k, v in chu.most_common(12):
        A(f"- {v:4d} ảnh — {k}")
    A("")
    A("## Điểm mù — phải nói trước")
    A("")
    A("- Máy tự chấm độ chắc của chính mình, **không ai kiểm lại** — tấm ghi \"chắc cao\" "
      "vẫn có thể sai người.")
    A("- Nhãn đúng **không bảo đảm tra kho ra đúng**: còn phụ thuộc bộ tra và từ khoá của câu.")
    A("- Số nhãn được chữa đo mức **sai của nhãn cũ**, chưa đo mức **đúng của nhãn mới**.")
    return "\n".join(r)


if __name__ == "__main__":
    log = sys.argv[1] if len(sys.argv) > 1 else None
    print(bao_cao(log))
