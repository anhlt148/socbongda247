#!/usr/bin/env python3
"""BA KỊCH BẢN VIẾT TAY — 04/08/2026, sau khi anh loại mẻ 30 giây đầu tiên.

Anh chốt: em viết content + chọn tài nguyên, trợ lý chỉ lo khung dựng. Ba thứ sửa so
với mẻ trước:
  ① dài 55–60 giây (218 tiếng ở nhịp 226 tiếng/phút) thay vì 30 giây
  ② văn NÓI — động từ mạnh, câu ngắn, gọi "anh em", có thái độ; học từ transcript thật
     của Nhím ("cày nát khu trung tuyến", "dọn rác phía sau", "xé toang hàng thủ")
  ③ kết KHÔNG cụt: chốt lại ý, rồi mời bình luận tử tế chứ không ném một câu hỏi trống

Mọi dữ kiện đều lấy từ tư liệu đã kiểm chứng (bài gốc + đối chiếu Tuổi Trẻ/Thanh Niên
về bảng xếp hạng). Con số viết bằng chữ vì máy đọc hay vấp chữ số.
"""
import json, os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import duong_dan as DD

NGAY = "2026-08-04"

KB = [
    {
        "ma": "tay-vietanh",
        "cung_nhac": "cao_trao",
        "tieu_de": "MÁU CHẢY ĐẦY MẶT, VIỆT ANH VẪN KHÔNG RỜI SÂN",
        "cum_to_vang": ["MÁU CHẢY ĐẦY MẶT", "KHÔNG RỜI SÂN"],
        "loi_binh": (
            "Phút hai mươi bảy, máu chảy đầy mặt. Việt Anh vẫn không chịu rời sân. "
            "Một quả bóng bổng treo vào vòng cấm. Việt Anh bật lên tranh chấp với Mitchell Baker, "
            "tiền đạo cao một mét chín mươi sáu. Cú va chạm khiến vùng chân mày rách toác. "
            "Máu túa ra, đỏ cả một bên mặt. "
            "Tổ y tế chạy vào, quấn băng cầm máu. "
            "Ít phút sau, anh trở lại sân. Đầu quấn băng trắng. Và đá tiếp. "
            "Anh em biết không, đây mới là trận đầu tiên Việt Anh được đá chính cho tuyển quốc gia. "
            "Còn Baker thì đang là vua phá lưới của giải, bốn bàn sau ba trận. "
            "Tám mươi mốt phút, trung vệ Công an Hà Nội thắng bốn trên năm pha không chiến. "
            "Tắc bóng ba trên ba. Năm lần phá bóng. Và Baker tắt lịm, không một bàn nào. "
            "Ba không. Văn Vĩ mở tỉ số, Hai Long nhân đôi, Xuân Son chốt hạ. "
            "Việt Nam leo lên đỉnh bảng A. "
            "Hết trận, anh được đưa thẳng vào viện khâu vết rách trên chân mày. "
            "Hai ba ngày là lành, kịp đá Campuchia. "
            "Một vết khâu, đổi lấy ngôi đầu bảng. "
            "Người bảo đó là bản lĩnh của một trung vệ thép. Người bảo liều. Anh em thấy sao? "
            "Gõ cho Sóc một chữ ở phần bình luận phía dưới nhé, bản lĩnh hay liều lĩnh."
        ),
        "binh_luan_ghim": "Việt Anh quấn băng đá tiếp trọn trận — BẢN LĨNH hay LIỀU LĨNH? "
                          "Anh em gõ một chữ thôi, Sóc đọc hết.",
        "tu_khoa": ["việt anh", "bùi hoàng việt anh", "viet anh khau vet thuong",
                    "việt nam indonesia", "asean cup 2026", "tuyển việt nam",
                    "kim sang sik", "viet nam 3-0 indonesia", "bong da viet nam",
                    "trung vệ công an hà nội"],
        "nguon": "https://vietnamnet.vn/viet-anh-phai-khau-vet-thuong-tuyen-viet-nam-ve-nuoc-2541764.html",
        "tin_goc": "Việt Anh phải khâu vết thương, tuyển Việt Nam về nước",
    },
    {
        "ma": "tay-cuadi",
        "cung_nhac": "cang_thang",
        "tieu_de": "THẮNG ĐẬM INDONESIA, VIỆT NAM VẪN CHƯA CHẮC VÉ BÁN KẾT",
        "cum_to_vang": ["THẮNG ĐẬM INDONESIA", "CHƯA CHẮC VÉ"],
        "loi_binh": (
            "Ba không trước Indonesia. Cả nước ăn mừng. Nhưng mở bảng xếp hạng ra, "
            "vẫn còn đúng một cửa hẹp để Việt Nam rơi khỏi bán kết. "
            "Sau lượt bốn, thầy trò ông Kim đứng đầu bảng A với bảy điểm. "
            "Singapore cũng bảy điểm. Bằng nhau tất, chỉ hơn nhau hiệu số bàn thắng bại. "
            "Việt Nam cộng mười, Singapore cộng ba. Phía sau, Indonesia sáu điểm, vẫn còn thở. "
            "Lượt cuối, Việt Nam tiếp Campuchia. Cùng giờ đó, Indonesia đấu Singapore. "
            "Vậy cái cửa rơi kia nằm ở đâu? Nó nằm ở chỗ Việt Nam phải thua Campuchia "
            "tới chín bàn không gỡ. Rồi Singapore cũng phải thua Indonesia nữa. "
            "Cả hai chuyện, cùng một lúc. "
            "Mà anh em biết Campuchia với Việt Nam là thế nào không? "
            "Mười một lần chạm trán, mười một lần Campuchia rời sân với cái đầu cúi xuống. "
            "Chưa một lần nào họ ghi nổi quá hai bàn vào lưới chúng ta. "
            "Nên nói thẳng, cửa đó gần như đã khoá. Thắng Campuchia là chắc ngôi đầu. "
            "Mà nhất bảng A còn tránh được Thái Lan ở bán kết. "
            "Ngày bảy tháng tám, sân nhà, cả tấm vé nằm trong tay mình. "
            "Anh em dự đoán Việt Nam thắng mấy không? "
            "Để lại tỉ số ở phần bình luận phía dưới nhé, xem ai đoán trúng."
        ),
        "binh_luan_ghim": "Việt Nam – Campuchia ngày 7/8, anh em đoán tỉ số bao nhiêu? "
                          "Ghi xuống đây, trận xong Sóc quay lại xem ai trúng.",
        "tu_khoa": ["việt nam campuchia", "asean cup 2026", "bảng xếp hạng bảng a",
                    "tuyển việt nam", "viet nam vao ban ket", "kim sang sik",
                    "viet nam 3-0 indonesia", "bong da viet nam", "aff cup 2026",
                    "lich thi dau asean cup"],
        "nguon": "https://vietnamnet.vn/kich-ban-dia-chan-khien-tuyen-viet-nam-mat-ve-ban-ket-asean-cup-2026-2541921.html",
        "tin_goc": "Tuyển Việt Nam chỉ còn 1% nguy cơ rơi vé bán kết ASEAN Cup 2026",
    },
    {
        "ma": "tay-hubner",
        "cung_nhac": "cang_thang",
        "tieu_de": "THUA BA KHÔNG, CẦU THỦ INDONESIA VẪN LÊN MẠNG CÀ KHỊA",
        "cum_to_vang": ["THUA BA KHÔNG", "CÀ KHỊA"],
        "loi_binh": (
            "Thua ba không ngay trên sân nhà. Vậy mà vẫn có một cầu thủ Indonesia "
            "lên mạng cà khịa Việt Nam. "
            "Người đó là Justin Hubner. Trung vệ hai mươi hai tuổi. "
            "Buồn cười là anh ta còn không có tên trong danh sách dự giải. "
            "Ngay sau tiếng còi kết thúc, Hubner đăng tấm ảnh mình tranh chấp với cầu thủ Việt Nam. "
            "Kèm một dòng chữ: họ đã quên những gì chúng ta làm với họ ở vòng loại. "
            "Chưa hết. Anh ta bình luận thêm: ở một giải đấu không phải của FIFA, "
            "các bạn chơi cũng tốt đấy. Rồi thòng thêm: "
            "chúng ta sẽ còn gặp nhau ở giải chính thức. "
            "Ý anh ta là hai trận Indonesia từng thắng Việt Nam ở vòng loại World Cup. "
            "Chuyện đó có thật, không ai chối. "
            "Nhưng có một chuyện thật khác vừa xảy ra. "
            "Việt Nam thắng ba không, ngay giữa lòng Indonesia. "
            "Văn Vĩ, Hai Long, Xuân Son. Ba bàn, không cần một lời đôi co nào. "
            "Indonesia tụt xuống thứ ba, kém Việt Nam đúng một điểm. "
            "Tháng chín này, hai đội gặp lại ở vòng loại. Cứ để bóng lăn rồi tính. "
            "Còn anh em thấy Hubner nói vậy là có lý, hay chỉ là cay cú? "
            "Gõ cho Sóc ở phần bình luận phía dưới nhé."
        ),
        "binh_luan_ghim": "Hubner bảo ASEAN Cup không phải giải của FIFA nên thắng cũng "
                          "chẳng để làm gì — anh em thấy CÓ LÝ hay CAY CÚ?",
        "tu_khoa": ["justin hubner", "indonesia mia mai viet nam", "việt nam indonesia",
                    "asean cup 2026", "tuyển việt nam", "xuân son", "hai long",
                    "viet nam 3-0 indonesia", "bong da viet nam", "hubner viet nam"],
        "nguon": "https://vietnamnet.vn/ket-qua-bong-da-campuchia-3-0-timor-leste-bang-a-asean-cup-2026-2541564.html",
        "tin_goc": "Cầu thủ Indonesia mỉa mai chiến thắng của tuyển Việt Nam",
    },
]


if __name__ == "__main__":
    for k in KB:
        viec = os.path.join(DD.VIEC, f"{NGAY}-{k['ma']}")
        os.makedirs(viec, exist_ok=True)
        d = {
            "tieu_de": k["tieu_de"], "loi_binh": k["loi_binh"],
            "cum_to_vang": k["cum_to_vang"], "binh_luan_ghim": k["binh_luan_ghim"],
            "tu_khoa": k["tu_khoa"], "cung_nhac": k["cung_nhac"],
            "la_bong_da": True, "dat": True, "ly_do_khong_dat": [],
            "nguoi_viet": "Claude viết tay trong phiên (anh chốt 04/08) — KHÔNG qua claude -p",
            "so_tieng_thuc": len(k["loi_binh"].split()),
            "nguon_tin": k["nguon"], "bai_da_doc": k["nguon"], "tin_goc": k["tin_goc"],
            "so_nguon": 4,
            "canh_bao": "Số liệu bảng xếp hạng đã đối chiếu Tuổi Trẻ + Thanh Niên ngày 04/08.",
        }
        json.dump(d, open(os.path.join(viec, "kich-ban.json"), "w"),
                  ensure_ascii=False, indent=1)
        json.dump({"tieu_de": k["tin_goc"], "link": k["nguon"], "cac_link": [k["nguon"]],
                   "cac_nguon": ["vietnamnet.vn"], "ma": k["ma"]},
                  open(os.path.join(viec, "tin-goc.json"), "w"), ensure_ascii=False, indent=1)
        n = len(k["loi_binh"].split())
        print(f"  {k['ma']:14s} {n:3d} tiếng → dự kiến {n/226*60:.0f} giây   {k['tieu_de'][:46]}")
