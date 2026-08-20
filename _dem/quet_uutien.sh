#!/bin/bash
# QUÉT ~200 TẤM ƯU TIÊN VIỆT NAM / THÁI LAN — anh đặt 20/08 sáng.
# Chia hai tầng theo luật "rẻ trước, đắt sau":
#   ① sonnet — 25 tấm CHƯA AI NHÌN (việc thường, model vừa là đủ)
#   ② opus   — ~175 tấm nhãn CHƯA CHẮC, ưu tiên nội dung Việt Nam / Thái Lan
# Qua launchd chứ không chạy từ phiên Claude (claude CLI lồng nhau bị EPERM).
cd "$HOME/socbongda247" || exit 1
L="$HOME/socbongda247/_dem/uutien-$(date +%Y%m%d-%H%M).log"
{
  echo "════ BẮT ĐẦU $(date '+%F %T') ════"
  echo "── ① sonnet: tấm chưa ai nhìn"
  KHO_MODEL=claude-sonnet-5 /opt/homebrew/bin/python3 nhap_kho_chu_the.py --soat \
      --loc="việt nam,thái lan,viet nam,thai lan" --so=25
  echo "── ② opus: nhãn chưa chắc, ưu tiên Việt Nam / Thái Lan"
  KHO_MODEL=claude-opus-5 /opt/homebrew/bin/python3 nhap_kho_chu_the.py --soat --chua-chac \
      --loc="việt nam,thái lan,viet nam,thai lan" --so=175
  echo "── tình hình sau khi quét"
  /opt/homebrew/bin/python3 nhap_kho_chu_the.py --tinh-hinh
  echo "════ XONG $(date '+%F %T') ════"
} >> "$L" 2>&1
ln -sf "$L" "$HOME/socbongda247/_dem/uutien-moi-nhat.log"
