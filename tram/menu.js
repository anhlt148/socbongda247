// MENU CHUNG cổng 8756 (anh ra luật 10/08: TẤT CẢ trang cùng cổng phải có nút mở
// đến nhau và nút quay về — trang mới nào cũng NHÚNG file này, một dòng:
//   <script src="/menu.js"></script>
// Menu tự nhận mã việc đang mở (biến toàn cục `ma` của trang, hoặc ?ma= / ?viec=
// trên URL) để các link mang theo đúng việc; trang đang đứng thì tô vàng.
(function () {
  function maHien() {
    try { if (typeof ma === 'string' && ma) return ma; } catch (e) {}
    const q = new URLSearchParams(location.search);
    return q.get('ma') || q.get('viec') || '';
  }
  function ve() {
    const m = maHien();
    const suffix = m ? '?ma=' + encodeURIComponent(m) : '';
    const viec = m ? '?viec=' + encodeURIComponent(m) : '';
    const cac = [
      ['←', 'javascript:history.back()', 'Quay lại trang trước'],
      ['🏠 Trạm', '/' + suffix, 'Trạm tài nguyên — duyệt cảnh, dựng video'],
      ['🖼 Chọn ảnh', '/chon-anh' + viec, 'Trang chọn ảnh cho từng cảnh'],
      ['🏷 Kho nhà', '/kho-nha-duyet', 'Duyệt nhãn kho chủ thể dùng chung'],
      ['🎚 Phong cách', '/phong-cach', 'Núm vặn chống dập khuôn: nhạc cảm xúc, zoom, trượt, giọng'],
    ];
    // CHỖ ĐẶT: trang nào khai sẵn ô #menuCho thì menu NẰM GỌN trong header của trang
    // đó (anh chốt 11/08: menu chiếm riêng một dòng là phí 40px chiều cao). Trang
    // không khai thì vẫn thành thanh riêng đầu body y như cũ — hai trang kia không đổi.
    const oCho = document.getElementById('menuCho');
    const day = document.createElement('div');
    day.id = 'menuChung';
    // CANH PHẢI trên MỌI trang (anh chốt 11/08: "3 trang trái phải lung tung") —
    // menu là thứ phụ, nép sát mép phải để nhường chỗ trái cho nội dung chính
    day.style.cssText = oCho
      ? 'display:flex;gap:5px;align-items:center;justify-content:flex-end;'
        + 'font:600 12px/1 -apple-system,"Segoe UI",sans-serif'
      : 'display:flex;gap:6px;align-items:center;justify-content:flex-end;'
        + 'background:#0b0908;border-bottom:1px solid #332a26;padding:6px 14px;'
        + 'font:600 12.5px/1 -apple-system,"Segoe UI",sans-serif';
    const duong = location.pathname;
    cac.forEach(function (c) {
      const a = document.createElement('a');
      a.textContent = c[0];
      a.href = c[1];
      a.title = c[2];
      const oDay = (c[1].split('?')[0] === duong);
      a.style.cssText = 'text-decoration:none;border-radius:8px;'
        + (oCho ? 'padding:4px 8px;' : 'padding:6px 10px;')
        + (oDay ? 'background:#FFD400;color:#14100f;pointer-events:none;'
                : 'color:#f4efe9;background:#0e0b0a;border:1px solid #332a26;');
      day.appendChild(a);
    });
    if (oCho) oCho.appendChild(day);
    else document.body.insertBefore(day, document.body.firstChild);
  }
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', ve);
  else ve();
})();

// ── CHUÔNG "TRẠM ĐÃ NÂNG CẤP" (kiến trúc sư đặt 11/08) ──────────────────────
// Lớp lỗi đã trả giá: tab trạm sống nhiều ngày, server nâng cấp/khởi động lại,
// tab cũ chạy JS cũ với sổ mới → chức năng chết CÂM (vụ "không phóng to được").
// Chuông so mốc khởi động server mỗi phút; lệch là giăng dải đỏ bảo tải lại.
// Đặt ở menu.js vì MỌI trang cổng 8756 đều nhúng file này — một nguồn, đủ ba trang.
(function () {
  var vGoc = null;
  function so() {
    fetch('/api/phien-ban').then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.v) return;
      if (vGoc === null) { vGoc = d.v; return; }
      if (d.v === vGoc || document.getElementById('chuongNangCap')) return;
      var b = document.createElement('div');
      b.id = 'chuongNangCap';
      b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:9999;'
        + 'background:#a3232b;color:#fff;padding:9px 14px;text-align:center;'
        + 'font-size:14px;cursor:pointer;box-shadow:0 2px 12px #0009';
      b.innerHTML = '⟳ <b>Trạm vừa nâng cấp</b> — tab này đang chạy bản cũ, dễ hỏng ngầm. '
        + 'Bấm vào đây để tải lại trang.';
      b.onclick = function () { location.reload(); };
      document.body.appendChild(b);
    }).catch(function () {});           // trạm tắt/mạng đứt thì im, không quấy
  }
  so();
  setInterval(so, 60000);
})();
