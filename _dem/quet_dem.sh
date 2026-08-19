#!/bin/bash
# QUÉT NHÃN KHO ĐÊM — anh đặt 20/08. Hai tầng, rẻ trước đắt sau (luật tài nguyên tối thiểu):
#   ① sonnet quét 138 tấm CHƯA AI NHÌN — việc thường, model vừa là đủ
#   ② opus soi 486 tấm sonnet "không dám gọi tên" (chắc: vừa/thấp) — việc khó mới dùng mắt tinh
# Chạy qua launchd chứ KHÔNG chạy từ phiên Claude: claude CLI lồng nhau bị EPERM
# (chú thích sẵn trong nhap_kho_chu_the.py, bài học 10/08).
cd "$HOME/socbongda247" || exit 1
L="$HOME/socbongda247/_dem/quet-$(date +%Y%m%d).log"
{
  echo "════ BẮT ĐẦU $(date '+%F %T') ════"
  echo "── tầng ①: sonnet quét tấm CHƯA AI NHÌN"
  KHO_MODEL=claude-sonnet-5 /opt/homebrew/bin/python3 nhap_kho_chu_the.py --soat
  echo "── tầng ②: opus soi tấm nhãn CHƯA CHẮC"
  KHO_MODEL=claude-opus-5 /opt/homebrew/bin/python3 nhap_kho_chu_the.py --soat --chua-chac
  echo "── tình hình sau khi quét"
  /opt/homebrew/bin/python3 nhap_kho_chu_the.py --tinh-hinh
  echo "════ XONG $(date '+%F %T') ════"
} >> "$L" 2>&1
