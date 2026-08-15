// LỚP CHỌN NHIỀU ẢNH — phủ lên trang đang xem, mỗi ảnh đủ to mọc một nút ＋.
// Dùng khi một trang có nhiều ảnh đáng lấy (album Facebook, bài báo nhiều hình): thay vì
// chuột phải từng tấm, bấm chọn một loạt rồi gửi một lượt.
(() => {
  if (window.__socLopChon) { window.__socLopChon(); return; }

  const chon = new Set();
  const css = document.createElement("style");
  css.textContent = `
    .soc-cham{position:absolute;z-index:2147483000;top:8px;left:8px;width:32px;height:32px;
      border:0;border-radius:9px;background:#D33342;color:#fff;font:800 16px/1 sans-serif;
      cursor:pointer;box-shadow:0 2px 10px #0008}
    .soc-cham.co{background:#FFD400;color:#241a00}
    .soc-thanh{position:fixed;left:50%;transform:translateX(-50%);bottom:24px;z-index:2147483600;
      background:#14100f;color:#f4efe9;font:600 15px/1.4 -apple-system,sans-serif;
      padding:13px 18px;border-radius:14px;box-shadow:0 10px 34px #000a;border:1px solid #443;
      display:flex;gap:12px;align-items:center}
    .soc-thanh button{font:700 14px/1 sans-serif;border:0;border-radius:9px;padding:10px 16px;
      cursor:pointer;background:#332a26;color:#f4efe9}
    .soc-thanh button.chinh{background:#FFD400;color:#241a00}`;
  document.documentElement.appendChild(css);

  const thanh = document.createElement("div");
  thanh.className = "soc-thanh";
  const chu = document.createElement("span");
  const nutGui = document.createElement("button");
  nutGui.className = "chinh";
  const nutThoat = document.createElement("button");
  nutThoat.textContent = "Thoát";
  thanh.append(chu, nutGui, nutThoat);
  document.body.appendChild(thanh);

  const ve = () => {
    chu.textContent = `SÓC · đã chọn ${chon.size} ảnh`;
    nutGui.textContent = `Gửi ${chon.size} ảnh về kho`;
    nutGui.disabled = !chon.size;
  };

  const gan = () => {
    document.querySelectorAll("img").forEach((im) => {
      if (im.dataset.socGan) return;
      if (im.naturalWidth < 400 || im.naturalHeight < 300) return;
      im.dataset.socGan = "1";
      const boc = im.parentElement;
      if (!boc) return;
      if (getComputedStyle(boc).position === "static") boc.style.position = "relative";
      const n = document.createElement("button");
      n.className = "soc-cham";
      n.textContent = "+";
      n.onclick = (ev) => {
        ev.preventDefault(); ev.stopPropagation();
        const u = im.currentSrc || im.src;
        if (chon.has(u)) { chon.delete(u); n.classList.remove("co"); n.textContent = "+"; }
        else { chon.add(u); n.classList.add("co"); n.textContent = chon.size; }
        ve();
      };
      boc.appendChild(n);
    });
  };

  const nhip = setInterval(gan, 1200);             // trang nạp thêm ảnh khi cuộn
  gan(); ve();

  nutGui.onclick = () => {
    nutGui.disabled = true; chu.textContent = "SÓC · đang gửi…";
    chrome.runtime.sendMessage(
      { viec: "soc-gui-nhieu", urls: [...chon], trang: location.href },
      (kq) => { chu.textContent = `SÓC · xong ${kq ? kq.xong : 0} ảnh`; nutGui.disabled = false; });
  };
  const dong = () => {
    clearInterval(nhip);
    document.querySelectorAll(".soc-cham").forEach((e) => e.remove());
    document.querySelectorAll("[data-soc-gan]").forEach((e) => delete e.dataset.socGan);
    thanh.remove(); css.remove();
    window.__socLopChon = null;
  };
  nutThoat.onclick = dong;
  window.__socLopChon = dong;                      // gọi lần nữa thì tắt lớp phủ
})();
