#!/bin/bash
# DỌN PHIÊN CLAUDE CODE CŨ  —  anh hỏi 18/08: "đóng bằng cách nào"
#
# Phiên Claude Code KHÔNG tự chết khi đóng cửa sổ. Chúng chạy nền tiếp, mỗi phiên ăn
# ~9% CPU và ~90 MB. Ngày 17/08 đo được 34 phiên treo — phiên lâu nhất từ 4 hôm trước —
# cộng lại hơn 300% CPU, tức ba nhân chạy hết công suất cho việc không ai dùng.
#
#   ./don-phien.sh          xem có gì, KHÔNG đụng vào
#   ./don-phien.sh dọn      đóng phiên chạy từ 1 ngày trở lên
#   ./don-phien.sh dọn-hết  đóng mọi phiên trừ phiên đang nói chuyện
#
# Phiên ĐANG dùng luôn được giữ — script truy chuỗi tiến trình cha để nhận ra nó.

set -u
lenh="${1:-xem}"

# phiên đang nói chuyện với anh: đi ngược từ chính script này lên
giu=""
p=$$
while [ "$p" != "1" ] && [ -n "$p" ]; do
  if ps -p "$p" -o command= 2>/dev/null | grep -q "claude-code"; then giu="$giu $p"; fi
  p=$(ps -p "$p" -o ppid= 2>/dev/null | tr -d ' ')
  [ -z "$p" ] && break
done

ds_cu=$(ps -Ao pid,etime,command | grep "[c]laude-code" | awk '$2 ~ /-/ {print $1}')
ds_all=$(ps -Ao pid,command | grep "[c]laude-code" | awk '{print $1}')

loc() {                     # bỏ phiên đang dùng khỏi danh sách
  for x in $1; do
    case " $giu " in *" $x "*) ;; *) echo "$x" ;; esac
  done
}

case "$lenh" in
  xem)
    echo "── PHIÊN CLAUDE CODE ─────────────────────────────"
    ps -Ao pid,pcpu,rss,etime,command -r | grep "[c]laude-code" |
      awk '{printf "  PID %-7s %5s%%  %5.0f MB  chạy %s\n",$1,$2,$3/1024,$4}'
    echo
    n_cu=$(loc "$ds_cu" | grep -c . || true)
    cpu=$(ps -Ao pcpu,command | grep "[c]laude-code" | awk '{s+=$1} END{printf "%.0f",s}')
    echo "  tổng: $(echo "$ds_all" | grep -c .) tiến trình · ăn ${cpu}% CPU"
    echo "  chạy từ 1 ngày trở lên: $n_cu  (đây là thứ nên dọn)"
    echo "  phiên đang dùng (luôn giữ):$giu"
    ;;
  dọn|don)
    ds=$(loc "$ds_cu")
    [ -z "$ds" ] && { echo "  không có phiên cũ nào — máy đang sạch"; exit 0; }
    echo "$ds" | xargs kill 2>/dev/null
    sleep 8
    con=$(for x in $ds; do ps -p "$x" >/dev/null 2>&1 && echo "$x"; done)
    [ -n "$con" ] && echo "$con" | xargs kill -9 2>/dev/null
    echo "  ✅ đã đóng $(echo "$ds" | grep -c .) tiến trình cũ"
    ;;
  dọn-hết|don-het)
    ds=$(loc "$ds_all")
    [ -z "$ds" ] && { echo "  chỉ còn phiên đang dùng — không có gì để dọn"; exit 0; }
    echo "$ds" | xargs kill 2>/dev/null
    sleep 8
    con=$(for x in $ds; do ps -p "$x" >/dev/null 2>&1 && echo "$x"; done)
    [ -n "$con" ] && echo "$con" | xargs kill -9 2>/dev/null
    echo "  ✅ đã đóng $(echo "$ds" | grep -c .) tiến trình, giữ lại phiên đang nói chuyện"
    ;;
  *)
    echo "  Dùng: ./don-phien.sh [xem | dọn | dọn-hết]" ;;
esac
