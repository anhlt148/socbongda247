#!/bin/bash
# ĐỢT HAI — anh đặt 200 tấm, đợt một mới làm được 64 vì luật "chỉ quét cái cần".
# 309 tấm nhãn "chưa chắc" ĐỀU ĐÃ QUA MẮT OPUS đêm qua, nên `--chua-chac` chỉ còn
# 11 tấm mới: opus không soi lại chính tấm nó đã soi — đúng luật, không phải hỏng.
# Muốn quét tiếp thì phải đụng lớp khác: 669 tấm SONNET CHẤM "CAO" mà opus chưa nhìn.
# Đáng soi, vì đêm qua chính lớp "sonnet tự tin" lòi ra 6 tấm Xuân Son mang nhãn
# "Tuyển Malaysia". Bỏ cờ --chua-chac, giữ ưu tiên Việt Nam / Thái Lan.
cd "$HOME/socbongda247" || exit 1
L="$HOME/socbongda247/_dem/uutien2-$(date +%Y%m%d-%H%M).log"
{
  echo "════ BẮT ĐẦU $(date '+%F %T') ════"
  echo "── opus soi lớp sonnet chấm 'cao', ưu tiên Việt Nam / Thái Lan"
  KHO_MODEL=claude-opus-5 /opt/homebrew/bin/python3 nhap_kho_chu_the.py --soat \
      --loc="việt nam,thái lan,viet nam,thai lan" --so=136
  echo "── tình hình sau khi quét"
  /opt/homebrew/bin/python3 nhap_kho_chu_the.py --tinh-hinh
  echo "════ XONG $(date '+%F %T') ════"
} >> "$L" 2>&1
