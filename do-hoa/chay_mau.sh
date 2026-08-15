#!/bin/bash
# Dựng MẪU minh hoạ + là ví dụ cách gọi từng tool. Chạy: bash chay_mau.sh
cd "$(dirname "$0")"; PY=/Users/letuananh/.cache/claude-earth-venv/bin/python; S=samples
echo "1/3 render_card (4 card tĩnh)..."; $PY scripts/render_card.py "$S/_cards.json"
echo "2/3 breaking_news (card tin nóng MP4)..."; $PY scripts/breaking_news.py "$S/_tin.json" -o "$S/5_tin_nong.mp4"
echo "3/3 player_spotlight (spotlight cầu thủ MP4, tải ảnh + xoá nền ~1phút)..."; $PY scripts/player_spotlight.py --player "Erling Haaland" --out "$S/6_spotlight_haaland.mp4" --accent "#e11d2a" --seconds 5
echo "XONG. Mẫu ở: $S/"
