
## Mắt máy & bộ chấm bìa (18/08)

```
lam_thumbnail.lam(viec)
   ├─ _cac_phuong_an()  → tối đa 5 kiểu bố cục đáng thử
   ├─ với mỗi kiểu: _dung_mot() → bìa
   │     └─ _o_tron() → _cho_dat_o_tron() → _hop_mat() ─┐
   │                                                     ├→ mat_may.nhin_pil()
   │                     _ban_do_quan_trong() ───────────┘   (venv riêng, subprocess)
   ├─ cham_bia.cham(bia)  → 7 thước, 0–100
   └─ chọn cao nhất → thumbnail.jpg
        bản còn lại → thumbnail-du-bi/<điểm>-<kiểu>-<tên>.jpg
        báo cáo     → thumbnail-cham.json
```

| tệp | vai |
|---|---|
| `mat_may.py` | nhìn ảnh: hộp khuôn mặt (YuNet) + mặt nạ chủ thể (U²-Net) + lưới nền. Chạy trong venv riêng `~/.cache/socbongda247-mat`, gọi qua subprocess, cache theo nội dung ảnh |
| `cham_bia.py` | bảy thước chấm bìa, mỗi thước kèm câu nhận xét |
| `lam_thumbnail.py` | dựng nhiều phương án, chấm, chọn, lưu dự bị |

**Ba chỗ dễ gãy** (cổng ㉒ canh): đường lùi khi mắt máy hỏng · thang điểm hai đường phải
chia về một thước · chỗ gọi `lam()` phải nhận giá trị trả về kiểu mở.
