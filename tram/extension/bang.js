// Bảng nhỏ của tiện ích — TÁCH RA FILE RIÊNG, không viết thẳng trong .html.
// Manifest V3 CẤM script viết thẳng trong trang tiện ích (CSP chặn im lặng, không báo lỗi ra
// màn hình). Bản đầu em viết inline nên bảng đứng nguyên ở chữ "đang hỏi trạm…" — anh tưởng
// trạm không trả lời, mà thật ra đoạn mã chưa hề chạy. Đo lại: trạm trả lời trong 8 mili giây.
//
// Bảng này trả lời câu anh hỏi 05/08: "mỗi video một kho riêng thì biết gửi về kho nào?"
// → Gửi vào việc ĐANG MỞ trên trạm, và đổi được ngay tại đây, không phải sang trạm.

const TRAM = "http://127.0.0.1:8756";
const $ = (s) => document.querySelector(s);

async function hoi(duong, than) {
  const c = new AbortController();
  const gio = setTimeout(() => c.abort(), 6000);   // treo quá 6 giây thì thôi, báo cho người
  try {
    const r = await fetch(TRAM + duong, {
      signal: c.signal,
      ...(than ? { method: "POST", headers: { "Content-Type": "application/json" },
                   body: JSON.stringify(than) } : {}),
    });
    return await r.json();
  } finally { clearTimeout(gio); }
}

async function nap() {
  try {
    const [ds, dang] = await Promise.all([hoi("/api/viec"), hoi("/api/dang-lam")]);
    const s = $("#chonViec");
    s.innerHTML = ds.map((v) =>
      `<option value="${v.ma}">${v.tieu_de || v.ma}</option>`).join("");
    s.value = dang.ma || (ds[0] && ds[0].ma) || "";
    s.onchange = async () => {
      await hoi("/api/dang-lam", { ma: s.value });
      $("#tinh").textContent = "✓ từ giờ ảnh về kho này";
      capNhat();
    };
    capNhat();
  } catch (e) {
    $("#chonViec").innerHTML = "<option>không thấy trạm</option>";
    $("#tinh").innerHTML = '<span class="xau">Trạm chưa bật. Mở bằng '
      + '"MỞ TRẠM TÀI NGUYÊN.command" rồi mở lại bảng này.</span>';
  }
}

async function capNhat() {
  try {
    const ds = await hoi("/api/viec");
    const v = ds.find((x) => x.ma === $("#chonViec").value);
    if (v) $("#tinh").textContent = `${v.ma} · ${v.so_anh} ảnh trong kho · ${v.so_cau} câu`;
  } catch (e) { /* im lặng, dòng phụ thôi */ }
}

// Nút lấy video của tab đang mở — đường chính cho TikTok (nó chặn menu chuột phải).
// Việc tải giao cho phần nền làm rồi báo bằng thông báo góc màn hình, vì bảng popup
// đóng lại là script của nó chết — không ôm việc chạy vài phút ở đây được.
$("#layVideo").onclick = async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url || !tab.url.startsWith("http")) {
    $("#tinhVideo").innerHTML = '<span class="xau">tab này không có trang web</span>';
    return;
  }
  chrome.runtime.sendMessage({ viec: "soc-lay-video-tab", trang: tab.url });
  $("#tinhVideo").textContent = "⏳ đã giao cho Sóc — xong sẽ có thông báo góc màn hình";
};

nap();
