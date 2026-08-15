// TIỆN ÍCH CHROME "Sóc — gắp ảnh về kho" — phần chạy nền.
//
// Vì sao có nó (anh đề xuất 05/08): trạm đã gắp được ảnh từ Google và từ bài báo, nhưng ảnh
// nằm ở CHỖ KHÁC — Facebook cầu thủ, Instagram, diễn đàn — thì anh vẫn phải tải về máy rồi
// tải lên. Tiện ích xoá hẳn khúc vòng đó: chuột phải một ảnh ở BẤT KỲ trang nào là nó bay
// thẳng vào kho của việc anh đang mở trên trạm.
//
// Ảnh gửi lên vẫn đi đúng cửa `/api/tai-len` như khi anh dán tay: soi watermark đủ, nhưng
// KHÔNG vứt tấm nào — vì đây là ảnh NGƯỜI chủ động chỉ, không phải máy quét bừa.

const TRAM = "http://127.0.0.1:8756";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "soc-lay-anh",
    title: "📥 Gửi ảnh này về kho Sóc",
    contexts: ["image"],
  });
  chrome.contextMenus.create({
    id: "soc-chon-nhieu",
    title: "🖼 Chọn nhiều ảnh trên trang này…",
    contexts: ["page", "image"],
  });
  // KHO CHUNG (anh đặt 10/08 khuya): anh tự tìm Google, chuột phải là ảnh bay thẳng
  // vào kho chủ thể dùng chung — KHÔNG dính bài nào, nằm ngăn CHỜ GẮN NHÃN, lên trang
  // kho bấm quét là mắt máy nhận diện + gắn nhãn rồi nhập kho chính thức.
  chrome.contextMenus.create({
    id: "soc-lay-anh-kho",
    title: "🏠 Gửi ảnh này về KHO CHUNG (chờ nhãn)",
    contexts: ["image"],
  });
  // Video TikTok/Facebook/Instagram phát bằng blob: nên KHÔNG tải kiểu ảnh được — mục này
  // gửi LINK TRANG + cookie phiên về trạm, trạm tải nền bằng yt-dlp. Gắn cả context "page"
  // vì Facebook hay nuốt cú chuột phải trên video, Chrome chỉ thấy trang.
  chrome.contextMenus.create({
    id: "soc-lay-video",
    title: "🎬 Gửi video trang này về kho Sóc",
    contexts: ["page", "video", "link"],
  });
});

async function viecDangLam() {
  // Gửi kèm PHIÊN BẢN extension (anh hỏi 15/08: "sau này extension vẫn cập nhật
  // được chứ?"). Extension nạp kiểu "giải nén" thì `git pull` về file mới, nhưng
  // Chrome vẫn chạy bản đã nạp cho tới khi bấm ⟳ Tải lại — quên là dùng bản cũ mà
  // không ai biết. Nay trạm so với manifest trong kho và nhắc nếu lệch.
  const pb = chrome.runtime.getManifest().version;
  const r = await fetch(`${TRAM}/api/dang-lam?ext=${encodeURIComponent(pb)}`);
  if (!r.ok) throw new Error("trạm không trả lời");
  const d = await r.json();
  if (d.ext_cu) {
    bao("Extension đang chạy bản cũ",
        `Máy có bản ${d.ext_moi}, Chrome đang chạy ${pb}. `
        + "Mở chrome://extensions rồi bấm ⟳ Tải lại.");
  }
  if (!d.ma) throw new Error("trạm chưa mở việc nào");
  return d;
}

function bao(tieu_de, chu) {
  chrome.notifications.create({
    type: "basic", title: tieu_de, message: chu,
    iconUrl: chrome.runtime.getURL("icon/128.png"),   // logo kênh, cho dễ nhận ở góc màn hình
  });
}

// Tải ảnh ngay trong tiện ích rồi gửi byte sang trạm — KHÔNG đưa URL cho trạm tự tải.
// Lý do: nhiều trang (Facebook, Instagram) chỉ trả ảnh cho phiên đã đăng nhập; tiện ích chạy
// trong chính trình duyệt của anh nên có sẵn phiên đó, còn trạm gọi từ ngoài thì bị chặn.
async function guiAnh(srcUrl, trang) {
  const d = await viecDangLam();
  const r = await fetch(srcUrl);
  if (!r.ok) throw new Error(`không tải được ảnh (${r.status})`);
  const blob = await r.blob();
  if (blob.size < 8000) throw new Error("ảnh quá nhỏ, chắc là biểu tượng");
  const b64 = await new Promise((ok, hong) => {
    const f = new FileReader();
    f.onload = () => ok(f.result.split(",")[1]);
    f.onerror = hong;
    f.readAsDataURL(blob);
  });
  const ten = (srcUrl.split("/").pop() || "anh").split("?")[0].slice(0, 60) || "anh.jpg";
  const g = await fetch(`${TRAM}/api/tai-len`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ma: d.ma, tep: [{ ten, data: b64, url: srcUrl, trang }] }),
  });
  const kq = await g.json();
  if (kq.loi) throw new Error(kq.loi);
  return { d, kq };
}

// Gửi ảnh về KHO CHUNG — không cần việc đang làm; tiêu đề tab (chính là từ khoá anh
// đang tìm Google) đi kèm làm MỒI cho mắt máy gắn nhãn sau này.
async function guiAnhKho(srcUrl, trang, tieuDe) {
  const r = await fetch(srcUrl);
  if (!r.ok) throw new Error(`không tải được ảnh (${r.status})`);
  const blob = await r.blob();
  if (blob.size < 8000) throw new Error("ảnh quá nhỏ, chắc là biểu tượng");
  const b64 = await new Promise((ok, hong) => {
    const f = new FileReader();
    f.onload = () => ok(f.result.split(",")[1]);
    f.onerror = hong;
    f.readAsDataURL(blob);
  });
  const ten = (srcUrl.split("/").pop() || "anh").split("?")[0].slice(0, 60) || "anh.jpg";
  const g = await fetch(`${TRAM}/api/kho-nha-tai-len`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tep: [{ ten, data: b64, url: srcUrl, trang, tieu_de: tieuDe }] }),
  });
  const kq = await g.json();
  if (kq.loi) throw new Error(kq.loi);
  return kq;
}

// URL có dạng trang video riêng chưa? (watch/reel/video/shorts/p — đủ ba nền tảng)
const laLinkVideo = (u) => /\/(videos?|reels?|watch|shorts|p)\/|[?&]v=/.test(u || "");

// Gửi một VIDEO về trạm: trạm tải nền bằng yt-dlp, extension thăm dò tới khi xong rồi báo.
// Cookie CHỈ gửi kèm cho Facebook/Instagram (video ở đó cần phiên đăng nhập; cookie chỉ
// chạy tới localhost:8756). YouTube/TikTok tải ẨN DANH — đó là tài khoản KÊNH và gian
// hàng của anh, không đem cookie đi tải máy để khỏi bị nền tảng soi (anh thêm YouTube 07/08).
async function guiVideo(trang, src) {
  const d = await viecDangLam();
  const canCookie = /facebook\.com|fb\.watch|instagram\.com/.test(trang);
  const cookies = !canCookie ? [] : await new Promise((ok) =>
    chrome.cookies.getAll({ url: trang }, (ds) => ok(ds || [])));
  const r = await fetch(`${TRAM}/api/nhan-video`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ma: d.ma, trang, src: src || "", cookies }),
  });
  const dau = await r.json();
  if (dau.loi) throw new Error(dau.loi);
  bao("⏳ Sóc đang tải clip…", `${d.tieu_de || d.ma}\nxong sẽ báo lại ở góc màn hình`);
  for (let i = 0; i < 100; i++) {                  // tối đa ~8 phút
    await new Promise((t) => setTimeout(t, 5000));
    const kq = await (await fetch(`${TRAM}/api/nhan-video/${dau.job}`)).json();
    if (kq.xong) {
      if (kq.loi) throw new Error(kq.loi);
      bao("✅ Clip đã về kho Sóc",
          `${kq.tep} · ${kq.giay}s · ${kq.mb} MB\n${d.tieu_de || d.ma}\n`
          + "🔴 nguồn MXH — đã ghi sổ, QC sẽ soi khi dựng");
      return;
    }
  }
  throw new Error("quá 8 phút chưa xong — mở trạm xem lại");
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "soc-chon-nhieu") {
    chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["lop-chon.js"] });
    return;
  }
  if (info.menuItemId === "soc-lay-video") {
    try {
      const trang = info.pageUrl || (tab && tab.url) || "";
      // chuột phải trúng LINK của một video (thẻ reel trong bảng tin) thì ưu tiên link đó
      const dich = laLinkVideo(info.linkUrl) ? info.linkUrl : trang;
      const src = (info.srcUrl && info.srcUrl.startsWith("http")) ? info.srcUrl : "";
      await guiVideo(dich, src);
    } catch (e) {
      bao("❌ Chưa lấy được video", e.message + "\n(Trạm đã bật chưa? localhost:8756)");
    }
    return;
  }
  if (info.menuItemId === "soc-lay-anh-kho") {
    try {
      const kq = await guiAnhKho(info.srcUrl, info.pageUrl || (tab && tab.url) || "",
                                 (tab && tab.title) || "");
      bao(kq.so ? "🏠 Đã vào KHO CHUNG — chờ gắn nhãn" : "🏠 Kho đã có tấm này rồi",
          kq.so ? "Lên trang kho bấm 📥 Quét gắn nhãn khi gom đủ loạt"
                : "Vân tay trùng ảnh sẵn trong kho — không nhận đúp");
    } catch (e) {
      bao("❌ Chưa gửi được về kho", e.message + "\n(Trạm đã bật chưa? localhost:8756)");
    }
    return;
  }
  if (info.menuItemId !== "soc-lay-anh") return;
  try {
    const { d, kq } = await guiAnh(info.srcUrl, info.pageUrl || (tab && tab.url) || "");
    const a = (kq.anh || [])[0] || {};
    bao("✅ Đã vào kho Sóc",
        `${d.tieu_de || d.ma}\n${a.kich_thuoc || ""}`
        + (kq.so_dau_nguon ? "\n🔴 tấm này CÓ DẤU NGUỒN — cân nhắc trước khi dùng" : ""));
  } catch (e) {
    bao("❌ Chưa gửi được", e.message + "\n(Trạm đã bật chưa? localhost:8756)");
  }
});

// Bảng popup nhờ lấy video của tab đang mở (đường dành cho TikTok — nó chặn chuột phải)
chrome.runtime.onMessage.addListener((tin) => {
  if (tin.viec !== "soc-lay-video-tab") return;
  guiVideo(tin.trang, "").catch((e) =>
    bao("❌ Chưa lấy được video", e.message + "\n(Trạm đã bật chưa? localhost:8756)"));
});

// ─────────────────────────────────────────────────────────────────────────────
// PHÍM TẮT (anh đặt 14/08). Chuột phải → rê xuống → bấm mục là BA nhịp; gắp một
// loạt ảnh thì ba nhịp nhân mấy chục tấm là mỏi tay. Nay chỉ cần TRỎ CHUỘT vào
// ảnh rồi bấm phím: Alt+S về kho việc, Alt+A về kho chung.
//
// Làm sao biết "ảnh nào đang trỏ" mà KHÔNG phải cắm script theo dõi chuột chạy
// thường trực trên mọi trang anh mở (kể cả ngân hàng, mail)? Mượn chính trạng
// thái :hover mà trình duyệt vốn đã tự giữ. Lúc bấm phím mới bơm một mẩu mã vào
// trang hỏi "img:hover là tấm nào" rồi rút ra ngay — không để lại gì.
//
// Hai phím DÙNG LẠI guiAnh/guiAnhKho của menu chuột phải: cùng đường ống, cùng
// cổng watermark, cùng chống trùng vân tay. Không viết luồng song song.
// Menu có hai đích thì phím tắt cũng phải có đủ hai — luật "chính có gì phụ có nấy".

const PHIM = {
  "soc-phim-anh-viec": { kho: false, ten: "kho việc" },
  "soc-phim-anh-kho":  { kho: true,  ten: "KHO CHUNG" },
};

// Mẩu mã chạy TRONG trang — trả về địa chỉ ảnh đang bị trỏ chuột.
// Ba lớp dò, vì ảnh trên web có ba lối vẽ khác nhau.
function _docAnhHover() {
  const lay = (im) => (im && (im.currentSrc || im.src)) || "";
  const ok = (u) => u && u.startsWith("http");

  const ims = document.querySelectorAll("img:hover");       // ① thẻ <img> thường
  if (ims.length) {
    const u = lay(ims[ims.length - 1]);                     // tấm sâu nhất = tấm chuột nằm trên
    if (ok(u)) return u;
  }
  // Chuỗi tổ tiên đang trỏ, BỎ html/body: trang chỉ có một tấm ảnh (bài Facebook đơn
  // ảnh) mà anh bấm phím lúc trỏ vào vùng trống thì body vẫn "chứa đúng 1 img" — cứ
  // thế mà gửi là gửi tấm anh KHÔNG hề trỏ tới, lại im lặng. Thà trả rỗng và nói ra.
  const chuoi = [...document.querySelectorAll(":hover")]
    .filter((e) => e !== document.documentElement && e !== document.body);
  for (let i = chuoi.length - 1; i >= 0; i--) {             // ② ảnh vẽ bằng background-image
    const nen = getComputedStyle(chuoi[i]).backgroundImage || "";
    const m = nen.match(/url\(["']?(https?:[^"')]+)/);
    if (m) return m[1];
  }
  // ③ ảnh bị lớp phủ trong suốt che — chỉ soi 3 cấp SÁT con trỏ, và khối đó phải NHỎ
  // (≤60% màn hình). Khối to bằng cả trang mà chứa một tấm ảnh thì trỏ vào chỗ trống
  // nào cũng "trúng" tấm ấy — đó là vơ nhầm, không phải dò đúng.
  const man = innerWidth * innerHeight;
  for (let i = chuoi.length - 1; i >= Math.max(0, chuoi.length - 3); i--) {
    const o = chuoi[i].getBoundingClientRect ? chuoi[i].getBoundingClientRect() : null;
    if (!o || o.width * o.height > man * 0.6) continue;
    const con = chuoi[i].querySelectorAll ? chuoi[i].querySelectorAll("img") : [];
    if (con.length === 1) { const u = lay(con[0]); if (ok(u)) return u; }
  }
  return "";
}

// Lời nhắn hiện NGAY TRÊN TRANG, không dùng thông báo góc màn hình: gắp liên tục
// mấy chục tấm mà mỗi tấm một thông báo hệ thống thì dồn đống, phải đi tắt từng cái.
function _veBaoTrang(chu, lanh) {
  const id = "__soc_bao";
  let h = document.getElementById(id);
  if (!h) {
    h = document.createElement("div");
    h.id = id;
    h.style.cssText = "position:fixed;right:18px;bottom:18px;z-index:2147483647;"
      + "font:700 14px/1.45 -apple-system,sans-serif;padding:11px 16px;border-radius:12px;"
      + "box-shadow:0 8px 28px #0007;max-width:340px;pointer-events:none;white-space:pre-line";
    document.documentElement.appendChild(h);
  }
  h.style.background = lanh ? "#14100f" : "#7a1420";
  h.style.color = lanh ? "#FFD400" : "#ffe9ec";
  h.textContent = chu;
  clearTimeout(h.__gio);
  h.__gio = setTimeout(() => h.remove(), 2600);
}

async function _hoiAnhDuoiChuot(tabId) {
  const kq = await chrome.scripting.executeScript({
    target: { tabId, allFrames: true },        // ảnh hay nằm trong khung con (Facebook, báo)
    func: _docAnhHover,
  });
  for (const r of kq) if (r && r.result) return r.result;
  return "";
}

async function _baoTrang(tabId, chu, lanh) {
  try {
    await chrome.scripting.executeScript({ target: { tabId }, func: _veBaoTrang, args: [chu, !!lanh] });
  } catch (e) {
    bao(lanh ? "🐿 Sóc" : "❌ Sóc", chu);       // trang cấm bơm mã thì lùi về thông báo góc
  }
}

chrome.commands.onCommand.addListener(async (lenh) => {
  const dat = PHIM[lenh];
  if (!dat) return;
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url || !tab.url.startsWith("http")) {
    bao("❌ Phím tắt không dùng được ở đây", "Chỉ chạy trên trang web thường (http/https).");
    return;
  }
  let u = "";
  try {
    u = await _hoiAnhDuoiChuot(tab.id);
  } catch (e) {
    bao("❌ Trang này chặn tiện ích", "Dùng chuột phải → mục 📥 như cũ.");
    return;
  }
  if (!u) {
    await _baoTrang(tab.id, "🐿 Chưa thấy ảnh nào dưới con trỏ\nrê chuột lên đúng tấm rồi bấm lại", false);
    return;
  }
  await _baoTrang(tab.id, `🐿 Đang gửi về ${dat.ten}…`, true);
  try {
    if (dat.kho) {
      const kq = await guiAnhKho(u, tab.url, tab.title || "");
      await _baoTrang(tab.id, kq.so ? "🏠 Đã vào KHO CHUNG — chờ gắn nhãn"
                                    : "🏠 Kho đã có tấm này rồi (trùng vân tay)", true);
    } else {
      const { d, kq } = await guiAnh(u, tab.url);
      const a = (kq.anh || [])[0] || {};
      await _baoTrang(tab.id,
        `✅ Đã vào kho: ${d.tieu_de || d.ma}\n${a.kich_thuoc || ""}`
        + (kq.so_dau_nguon ? "\n🔴 tấm này CÓ DẤU NGUỒN" : ""), true);
    }
  } catch (e) {
    await _baoTrang(tab.id, "❌ " + e.message, false);
  }
});

// Lớp chọn nhiều gửi ảnh về qua đây
chrome.runtime.onMessage.addListener((tin, nguoi_gui, traLoi) => {
  if (tin.viec !== "soc-gui-nhieu") return;
  (async () => {
    let xong = 0, hong = 0;
    for (const u of tin.urls) {
      try { await guiAnh(u, tin.trang); xong++; } catch (e) { hong++; }
    }
    bao("Sóc — gắp ảnh xong", `đã vào kho ${xong} ảnh` + (hong ? ` · ${hong} tấm hỏng` : ""));
    traLoi({ xong, hong });
  })();
  return true;                                     // giữ đường trả lời cho việc chạy lâu
});
