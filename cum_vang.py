#!/usr/bin/env python3
"""CỤM TÔ VÀNG của tiêu đề — MỘT bản dùng chung cho cả trạm lẫn xưởng.

Anh bắt 11/08: video lên sáng nay tít TRẮNG TRƠN, không còn cụm vàng làm điểm nhấn.
Gốc: việc chọn cụm vàng chỉ chạy trong chuỗi SAU DUYỆT LỜI. Bài anh paste tin từ GPT
vào trạm rồi dựng thẳng thì không ai chọn cụm — xưởng nhận danh sách rỗng và vẽ trắng
IM LẶNG, không kêu một tiếng. Đúng họ bệnh với thẻ số liệu hôm nay: một việc chỉ có
MỘT đường chạy, lệch đường là mất.

Nay: logic nằm ở đây, trạm gọi lúc duyệt lời, XƯỞNG GỌI LẠI lúc dựng nếu vẫn rỗng —
cửa cuối cùng trước khi lên hình, không lọt được nữa.

Việc dễ (chọn 1–2 cụm đắt trong MỘT câu) → haiku, đúng luật "hiệu quả tối đa, tài
nguyên tối thiểu".
"""
import json
import os
import re
import subprocess
import sys

MODEL = "claude-haiku-4-5-20251001"
# đường đầy đủ trước, tên trần sau: job chạy nền (launchd) có PATH khác hẳn shell
_CLAUDE = next((p for p in (os.path.expanduser("~/.local/bin/claude"),
                            "/opt/homebrew/bin/claude") if os.path.exists(p)), "claude")


def chon(tieu_de, timeout=120):
    """Chọn 1–2 cụm nguyên văn trong tiêu đề đáng tô vàng. Rỗng nếu không chọn được.

    Luôn kiểm cụm trả về có THẬT trong tiêu đề không — model bịa một chữ là lúc vẽ
    không khớp được, tô hụt hoặc tô lệch.
    """
    tieu_de = (tieu_de or "").strip()
    if not tieu_de:
        return []
    try:
        r = subprocess.run(
            [_CLAUDE, "-p", "--model", MODEL,
             "Tiêu đề video: " + tieu_de + "\n\nChọn 1-2 CỤM TỪ nguyên văn trong tiêu "
             "đề đáng tô màu nhấn nhất (cụm gây tò mò hoặc cú đấm của tít). Trả về DUY "
             "NHẤT JSON: {\"cum\": [\"...\"]} — cụm phải y nguyên chữ trong tiêu đề."],
            capture_output=True, text=True, timeout=timeout)
        m = re.search(r"\{.*\}", r.stdout, re.S)
        if not m:
            return []
        return [c for c in json.loads(m.group(0)).get("cum", [])
                if c and c.upper() in tieu_de.upper()][:2]
    except Exception:
        return []


def bao_dam(duong_kich_ban):
    """Đọc kịch bản, thiếu cụm vàng thì chọn rồi GHI LẠI. Trả về danh sách cụm.

    Dùng ở cửa cuối (xưởng, ngay trước khi vẽ tít): thà tốn một lượt haiku còn hơn ra
    một video tít trắng trơn rồi anh phải dựng lại.
    """
    try:
        kb = json.load(open(duong_kich_ban, encoding="utf-8"))
    except Exception:
        return []
    cum = kb.get("cum_to_vang") or []
    if cum:
        return cum
    cum = chon(kb.get("tieu_de", ""))
    if cum:
        # GHI QUA CỬA CHUNG có khoá (12/08): từ khi SEO chạy song song với xưởng, hai
        # tiến trình cùng sửa kich-ban.json — ghi đè cả tệp là xoá mất việc của nhau
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import kich_ban as KB
            KB.ghi_gop(os.path.dirname(duong_kich_ban), {"cum_to_vang": cum})
        except Exception:
            pass
    return cum


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else ""
    if os.path.isfile(p):
        print(bao_dam(p))
    else:
        print(chon(" ".join(sys.argv[1:])))
