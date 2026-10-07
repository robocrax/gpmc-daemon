/* GPMC Daemon — single-page UI (vanilla, no build step) */
"use strict";

/* ---------------- icons ---------------- */
const I = {
  iris: `<svg class="brand__mark" viewBox="0 0 32 32" fill="none" aria-hidden="true"><circle cx="16" cy="16" r="14" stroke="currentColor" stroke-opacity=".18" stroke-width="1.5"/><g class="iris" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M16 4.5 A11.5 11.5 0 0 1 25.9 10.2 L16 16Z" fill="currentColor" fill-opacity=".9" stroke="none"/><path d="M27.5 16 A11.5 11.5 0 0 1 22.6 25.4 L16 16Z" fill="currentColor" fill-opacity=".55" stroke="none"/><path d="M19.5 27 A11.5 11.5 0 0 1 8.3 24.6 L16 16Z" fill="currentColor" fill-opacity=".8" stroke="none"/><path d="M4.5 18 A11.5 11.5 0 0 1 6.1 7.6 L16 16Z" fill="currentColor" fill-opacity=".4" stroke="none"/><path d="M11 5.4 A11.5 11.5 0 0 1 16 4.5 L16 16Z" fill="currentColor" fill-opacity=".65" stroke="none"/></g><circle cx="16" cy="16" r="3.4" fill="var(--bg)"/></svg>`,
  phone: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="6.5" y="2.5" width="11" height="19" rx="2.5"/><path d="M10.5 18.5h3"/></svg>`,
  server: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/></svg>`,
  cloud: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M7 18a4 4 0 0 1 0-8 5.5 5.5 0 0 1 10.6-1.3A3.8 3.8 0 0 1 18 18Z"/><path d="M12 11v6m0 0 2.2-2.2M12 17l-2.2-2.2"/></svg>`,
  arrow: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 12h14m0 0-5-5m5 5-5 5"/></svg>`,
  play: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>`,
  sync: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12a9 9 0 0 1-9 9c-2.5 0-4.8-1-6.4-2.7M3 12a9 9 0 0 1 9-9c2.5 0 4.8 1 6.4 2.7"/><path d="M3 20v-4h4M21 4v4h-4"/></svg>`,
  pause: `<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>`,
  resume: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`,
  gear: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 0 1-4 0v-.1A1.6 1.6 0 0 0 7 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1.1-2.7H1a2 2 0 0 1 0-4h.1A1.6 1.6 0 0 0 2.6 7a1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H7a1.6 1.6 0 0 0 1-1.5V1a2 2 0 0 1 4 0v.1A1.6 1.6 0 0 0 17 2.6a1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V7a1.6 1.6 0 0 0 1.5 1H23a2 2 0 0 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z"/></svg>`,
  kebab: `<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="12" cy="19" r="2"/></svg>`,
  trash: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 7h16M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2m2 0v12a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V7"/></svg>`,
  logs: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M8 6h12M8 12h12M8 18h12M3.5 6h.01M3.5 12h.01M3.5 18h.01"/></svg>`,
  relink: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M9 15 15 9M10.5 6.5l1-1a4 4 0 0 1 6 6l-1 1M13.5 17.5l-1 1a4 4 0 0 1-6-6l1-1"/></svg>`,
  x: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M6 6l12 12M18 6 6 18"/></svg>`,
  plus: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M12 5v14M5 12h14"/></svg>`,
  external: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M14 4h6v6M20 4l-9 9M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"/></svg>`,
  info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>`,
  alert: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>`,
  upload: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 16V4m0 0 5 5m-5-5-5 5M5 20h14"/></svg>`,
  phoneqr: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3m4 0v4m-4 0h4m-7 0h.01"/></svg>`,
};

/* ---------------- helpers ---------------- */
const $ = (sel, root = document) => root.querySelector(sel);
const app = () => document.getElementById("app");

function node(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
async function api(path, opts = {}) {
  const init = { ...opts };
  if (init.body && !(init.body instanceof FormData)) {
    init.headers = { "Content-Type": "application/json", ...(init.headers || {}) };
    init.body = JSON.stringify(init.body);
  }
  const res = await fetch(path, init);
  if (res.status === 401) { state.authed = false; renderLogin(); throw new Error("Session expired"); }
  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("json") ? await res.json() : await res.text();
  if (!res.ok) throw new Error((data && data.detail) || data || res.statusText);
  return data;
}
function toast(msg, kind = "info") {
  const icon = kind === "ok" ? I.check : kind === "err" ? I.alert : I.info;
  const t = node(`<div class="toast toast--${kind}">${icon}<div>${esc(msg)}</div></div>`);
  $("#toaster").appendChild(t);
  setTimeout(() => { t.style.opacity = "0"; t.style.transition = "opacity .3s"; setTimeout(() => t.remove(), 300); }, kind === "err" ? 6000 : 3500);
}
function fmtBytes(n) {
  if (!n) return "0 B";
  const u = ["B", "KB", "MB", "GB"]; let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(n < 10 && i > 0 ? 1 : 0)} ${u[i]}`;
}
function fmtClock(sec) {
  sec = Math.max(0, Math.round(sec));
  const m = Math.floor(sec / 60), s = sec % 60;
  if (m >= 60) { const h = Math.floor(m / 60); return `${h}h ${m % 60}m`; }
  return `${m}:${String(s).padStart(2, "0")}`;
}
function hue(str) { let h = 0; for (const c of String(str)) h = (h * 31 + c.charCodeAt(0)) % 360; return h; }

/* ---------------- state ---------------- */
const state = { session: null, authed: false, accounts: [], network: null, lanes: new Map(), pollTimer: null, tickTimer: null };

/* ---------------- boot ---------------- */
async function boot() {
  applyTheme(localStorage.getItem("gpmc_theme") || "dark");
  try {
    state.session = await api("/api/session");
  } catch { app().innerHTML = `<div class="center-pad">Can't reach the server. Is the daemon running?</div>`; return; }
  state.authed = state.session.authenticated;
  if (state.session.theme && state.session.theme !== "system") applyTheme(state.session.theme);
  if (!state.authed) { renderLogin(); return; }
  await enterDashboard();
}

function applyTheme(theme) {
  const root = document.documentElement;
  if (theme === "system") {
    const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    root.setAttribute("data-theme", dark ? "dark" : "light");
  } else root.setAttribute("data-theme", theme);
  localStorage.setItem("gpmc_theme", theme);
}

/* ---------------- login ---------------- */
function renderLogin() {
  stopPolling();
  app().setAttribute("aria-busy", "false");
  app().innerHTML = `
    <div class="login"><div class="login__card">
      <a class="brand">${I.iris}<div class="brand__text"><span class="brand__name">GPMC</span></div></a>
      <h1>Welcome back</h1>
      <p>Enter the password to manage your Google Photos backups.</p>
      <form id="loginForm">
        <div class="field"><input class="input" type="password" id="pw" placeholder="Password" autofocus autocomplete="current-password" /></div>
        <button class="btn btn--primary btn--block" type="submit">Unlock</button>
      </form>
    </div></div>`;
  $("#loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/api/login", { method: "POST", body: { password: $("#pw").value } });
      state.authed = true; await enterDashboard();
    } catch (err) { toast(err.message, "err"); }
  });
}

/* ---------------- dashboard shell ---------------- */
async function enterDashboard() {
  app().setAttribute("aria-busy", "false");
  try { state.network = await api("/api/network"); } catch { state.network = null; }
  app().innerHTML = `
    <div class="shell">
      <header class="topbar"><div class="wrap topbar__inner">
        <a class="brand">${I.iris}<div class="brand__text"><span class="brand__name">GPMC</span><span class="brand__sub">full-quality photo backup</span></div></a>
        <div class="topbar__status" id="globalStatus"></div>
        <div class="topbar__spacer"></div>
        <div class="topbar__actions">
          <button class="btn btn--icon btn--ghost" id="phoneBtn" title="Device sync (phones)">${I.phoneqr}</button>
          <button class="btn btn--icon btn--ghost" id="settingsBtn" title="Settings">${I.gear}</button>
          <button class="btn btn--primary" id="addBtn">${I.plus}<span>Connect</span></button>
        </div>
      </div></header>
      <main class="wrap" id="main"></main>
    </div>`;
  $("#addBtn").addEventListener("click", openConnectWizard);
  $("#settingsBtn").addEventListener("click", openSettings);
  $("#phoneBtn").addEventListener("click", openDeviceSync);
  state.lanes.clear();
  await refresh(true);
  startPolling();
}

async function refresh(initial = false) {
  let accounts;
  try { accounts = await api("/api/accounts"); } catch { return; }
  state.accounts = accounts;
  renderMain(initial);
  renderGlobalStatus();
}

function renderGlobalStatus() {
  const g = $("#globalStatus"); if (!g) return;
  const accs = state.accounts;
  if (!accs.length) { g.innerHTML = ""; return; }
  const queued = accs.reduce((s, a) => s + (a.runtime.queue_count || 0), 0);
  const uploading = accs.filter((a) => a.runtime.status === "uploading").length;
  const nexts = accs.filter((a) => a.enabled && a.runtime.next_run).map((a) => a.runtime.next_run - Date.now() / 1000).filter((n) => n > 0);
  const nextIn = nexts.length ? Math.min(...nexts) : null;
  let right = uploading ? `<span><span class="dot dot--live"></span>${uploading} uploading</span>` :
    nextIn != null ? `<span><span class="dot dot--idle"></span>next in ${fmtClock(nextIn)}</span>` :
    `<span><span class="dot dot--ok"></span>all backed up</span>`;
  g.innerHTML = `<span>${accs.length} account${accs.length > 1 ? "s" : ""}</span><span><span class="dot dot--amber"></span>${queued} queued</span>${right}`;
}

function renderMain(initial) {
  const main = $("#main");
  if (!state.accounts.length) { state.lanes.clear(); main.innerHTML = emptyState(); $("#heroConnect").addEventListener("click", openConnectWizard); return; }
  let board = document.getElementById("board");
  if (!board) {
    main.innerHTML = `<section class="board" id="board"><div class="board__head"><h2>Accounts</h2></div><div id="laneList"></div></section>`;
    board = document.getElementById("board");
  }
  const list = $("#laneList");
  const seen = new Set();
  for (const acc of state.accounts) {
    seen.add(acc.id);
    let entry = state.lanes.get(acc.id);
    if (!entry) { const el = buildLane(acc); list.appendChild(el.root); state.lanes.set(acc.id, el); entry = el; }
    updateLane(entry, acc);
  }
  for (const [id, el] of state.lanes) if (!seen.has(id)) { el.root.remove(); state.lanes.delete(id); }
}

function emptyState() {
  return `<section class="hero">
    <h1 class="hero__title">Your photos, backed up in full quality.</h1>
    <p class="hero__sub">Connect a Google account and GPMC keeps it mirrored to Google Photos — originals, not compressed copies. It runs around the clock on this server.</p>
    <div class="hero__cta"><button class="btn btn--primary" id="heroConnect">${I.plus}<span>Connect Google Photos</span></button></div>
    <div class="flow">
      <div class="flow__node">${I.phone}<b>Your phone</b><span>Camera roll syncs here</span></div>
      <div class="flow__arrow">${I.arrow}</div>
      <div class="flow__node">${I.server}<b>This server</b><span>Watches a folder 24/7</span></div>
      <div class="flow__arrow">${I.arrow}</div>
      <div class="flow__node">${I.cloud}<b>Google Photos</b><span>Uploaded at full quality</span></div>
    </div>
  </section>`;
}

/* ---------------- lane ---------------- */
const STATUS = {
  uploading: { label: "Uploading", dot: "dot--live" },
  scanning: { label: "Scanning", dot: "dot--amber" },
  pending: { label: "Queued", dot: "dot--amber" },
  synced: { label: "Up to date", dot: "dot--ok" },
  error: { label: "Needs attention", dot: "dot--err" },
  disabled: { label: "Paused", dot: "dot--idle" },
  idle: { label: "Idle", dot: "dot--idle" },
};

function buildLane(acc) {
  const root = node(`<article class="lane" data-id="${acc.id}">
    <div class="lane__id">
      <div class="avatar"></div>
      <div class="lane__who"><div class="lane__email"></div><div class="lane__meta"></div></div>
    </div>
    <div class="film"></div>
    <div class="status">
      <div class="status__row"><div class="status__state"></div><div class="lane__actions"></div></div>
      <div class="status__count"></div>
      <div class="progress hidden"><div class="progress__bar"></div></div>
      <div class="status__sub"></div>
    </div>
  </article>`);
  const refs = {
    root,
    avatar: $(".avatar", root), email: $(".lane__email", root), meta: $(".lane__meta", root),
    film: $(".film", root), state: $(".status__state", root), count: $(".status__count", root),
    progress: $(".progress", root), bar: $(".progress__bar", root), sub: $(".status__sub", root),
    actions: $(".lane__actions", root),
    _filmSig: "", _acc: acc,
  };
  refs.actions.innerHTML = `
    <button class="btn btn--icon btn--ghost act-sync" title="Back up now">${I.sync}</button>
    <div class="menu"><button class="btn btn--icon btn--ghost act-menu" title="More">${I.kebab}</button></div>`;
  $(".act-sync", root).addEventListener("click", () => syncNow(refs._acc.id));
  $(".act-menu", root).addEventListener("click", (e) => openLaneMenu(e, refs._acc));
  return refs;
}

function updateLane(refs, acc) {
  refs._acc = acc;
  const rt = acc.runtime;
  const st = STATUS[rt.status] || STATUS.idle;
  refs.root.classList.toggle("is-uploading", rt.status === "uploading");
  refs.root.classList.toggle("is-disabled", rt.status === "disabled");

  const h = hue(acc.email);
  refs.avatar.style.background = `hsl(${h} 42% 32%)`;
  refs.avatar.style.color = "#fff";
  refs.avatar.textContent = (acc.email[0] || "?").toUpperCase();
  refs.email.textContent = acc.label && acc.label !== acc.email ? acc.label : acc.email;
  refs.email.title = acc.email;
  refs.meta.innerHTML = `<span>${esc(acc.email)}</span>`;

  // filmstrip (rebuild only when the preview set changes, to avoid thumbnail flicker)
  const preview = acc.preview || [];
  const sig = preview.map((p) => p.path).join("|") + "#" + rt.queue_count;
  if (sig !== refs._filmSig) {
    refs._filmSig = sig;
    if (!preview.length) {
      refs.film.innerHTML = rt.status === "uploading"
        ? `<span class="film__empty">Working through the queue…</span>`
        : `<span class="film__empty">${I.check} Nothing waiting — all backed up</span>`;
    } else {
      const max = 7;
      let html = preview.slice(0, max).map((p) => p.is_video
        ? `<div class="thumb thumb--video" title="${esc(p.name)}">${I.play}<span class="thumb__ext">${esc(p.ext)}</span></div>`
        : `<div class="thumb" title="${esc(p.name)}" style="background-image:url('/api/media/thumb?path=${encodeURIComponent(p.path)}')"></div>`
      ).join("");
      const extra = (rt.queue_count || preview.length) - Math.min(preview.length, max);
      if (extra > 0) html += `<div class="thumb thumb--more">+${extra}</div>`;
      refs.film.innerHTML = html;
    }
  }

  refs.state.innerHTML = `<span class="dot ${st.dot}"></span>${st.label}`;

  if (rt.status === "uploading") {
    const total = rt.total || rt.queue_count || 0;
    const done = rt.done || 0;
    refs.count.innerHTML = `${done}<small> / ${total} files</small>`;
    refs.progress.classList.remove("hidden");
    refs.bar.style.width = total ? `${Math.min(100, (done / total) * 100)}%` : "6%";
    const cur = rt.current_file ? `${esc(rt.phase || "uploading")} · ${esc(rt.current_file)}` : "starting…";
    refs.sub.innerHTML = `<span title="${esc(rt.current_file || "")}">${cur}</span>`;
  } else {
    refs.progress.classList.add("hidden");
    const q = rt.queue_count || 0;
    if (q > 0) {
      refs.count.innerHTML = `${q}<small> in queue</small>`;
    } else {
      refs.count.innerHTML = `<small>No files waiting</small>`;
    }
    if (rt.status === "error" && rt.last_error) refs.sub.innerHTML = `<span style="color:var(--err)">${esc(rt.last_error)}</span>`;
    else if (rt.status === "disabled") refs.sub.textContent = "Paused — won't upload until resumed";
    else if (acc.enabled && rt.next_run) { refs.sub.dataset.next = rt.next_run; refs.sub.dataset.q = q; tickLane(refs.sub); }
    else refs.sub.textContent = rt.last_success ? `Last backup ${rt.last_success}` : "Ready";
  }
}

function tickLane(subEl) {
  const next = Number(subEl.dataset.next || 0);
  const q = Number(subEl.dataset.q || 0);
  if (!next) return;
  const remain = next - Date.now() / 1000;
  if (q > 0) subEl.innerHTML = remain > 0 ? `Next backup in <b>${fmtClock(remain)}</b>` : `Starting…`;
  else subEl.innerHTML = `Watching for new photos · next check <b>${fmtClock(Math.max(0, remain))}</b>`;
}

/* ---------------- lane actions ---------------- */
async function syncNow(id) {
  try { const r = await api(`/api/accounts/${id}/sync`, { method: "POST" }); toast(r.status === "busy" ? "Already running" : "Backup started", r.status === "busy" ? "info" : "ok"); refresh(); }
  catch (e) { toast(e.message, "err"); }
}

function openLaneMenu(ev, acc) {
  ev.stopPropagation();
  closeMenus();
  const menu = ev.currentTarget.closest(".menu");
  const paused = !acc.enabled;
  const pop = node(`<div class="menu__pop">
    <button class="menu__item" data-a="settings">${I.gear} Settings</button>
    <button class="menu__item" data-a="logs">${I.logs} Activity &amp; logs</button>
    <button class="menu__item" data-a="upload">${I.upload} Add photos…</button>
    <button class="menu__item" data-a="pause">${paused ? I.resume : I.pause} ${paused ? "Resume" : "Pause"}</button>
    <div class="menu__sep"></div>
    <button class="menu__item" data-a="relink">${I.relink} Reconnect</button>
    <button class="menu__item menu__item--danger" data-a="delete">${I.trash} Remove account</button>
  </div>`);
  menu.appendChild(pop);
  pop.addEventListener("click", async (e) => {
    const a = e.target.closest(".menu__item")?.dataset.a; if (!a) return;
    closeMenus();
    if (a === "settings") openAccountModal(acc, "settings");
    else if (a === "logs") openAccountModal(acc, "logs");
    else if (a === "upload") openAccountModal(acc, "upload");
    else if (a === "pause") { try { const r = await api(`/api/accounts/${acc.id}/pause`, { method: "POST" }); toast(r.enabled ? "Resumed" : "Paused", "ok"); refresh(); } catch (err) { toast(err.message, "err"); } }
    else if (a === "relink") openConnectWizard(acc);
    else if (a === "delete") confirmDelete(acc);
  });
}
function closeMenus() { document.querySelectorAll(".menu__pop").forEach((m) => m.remove()); }
document.addEventListener("click", (e) => { if (!e.target.closest(".menu")) closeMenus(); });

/* ---------------- polling ---------------- */
function startPolling() {
  stopPolling();
  state.pollTimer = setInterval(() => refresh(), 1800);
  state.tickTimer = setInterval(() => {
    document.querySelectorAll(".status__sub[data-next]").forEach(tickLane);
    renderGlobalStatus();
  }, 1000);
}
function stopPolling() { clearInterval(state.pollTimer); clearInterval(state.tickTimer); }

/* ---------------- modal infra ---------------- */
function openModal(inner, opts = {}) {
  closeModal();
  const scrim = node(`<div class="scrim" id="scrim"></div>`);
  const modal = node(`<div class="modal ${opts.wide ? "modal--wide" : ""}" role="dialog" aria-modal="true"></div>`);
  modal.appendChild(inner);
  scrim.appendChild(modal);
  document.body.appendChild(scrim);
  scrim.addEventListener("click", (e) => { if (e.target === scrim) closeModal(); });
  document.addEventListener("keydown", escClose);
  return modal;
}
function closeModal() { const s = $("#scrim"); if (s) s.remove(); document.removeEventListener("keydown", escClose); }
function escClose(e) { if (e.key === "Escape") closeModal(); }
function modalHead(title, sub) {
  return `<div class="modal__head"><div><h3>${esc(title)}</h3>${sub ? `<p>${esc(sub)}</p>` : ""}</div><button class="btn btn--icon btn--ghost" onclick="closeModal()">${I.x}</button></div>`;
}
window.closeModal = closeModal;

/* ---------------- connect wizard ---------------- */
function openConnectWizard(existing) {
  const relink = existing && existing.id;
  const setupUrl = (state.network && state.network.embedded_setup_url) || "https://accounts.google.com/EmbeddedSetup";
  const inner = node(`<div>
    ${modalHead(relink ? `Reconnect ${existing.email}` : "Connect Google Photos", "Sign in once — we turn it into a secure upload key for this account.")}
    <div class="modal__body">
      <div class="step">
        <div class="step__num">1</div>
        <div class="step__body">
          <h4>Open Google sign-in</h4>
          <p>Sign in, then tap <b>I agree</b>. The page may freeze on a spinner — that's expected.</p>
          <div class="qr-row">
            <a class="btn btn--primary" href="${setupUrl}" target="_blank" rel="noopener">${I.external} Open sign-in</a>
            <div class="qr-box"><img alt="Scan to open sign-in on your phone" src="/api/qr?data=${encodeURIComponent(setupUrl)}" /></div>
            <div class="qr-cap">…or scan to open it<br/>on your phone</div>
          </div>
        </div>
      </div>
      <div class="step">
        <div class="step__num">2</div>
        <div class="step__body">
          <h4>Copy the sign-in token</h4>
          <ol>
            <li>Open your browser's developer tools (right-click → <b>Inspect</b>, or F12).</li>
            <li>Go to <b>Application</b> (or <b>Storage</b>) → <b>Cookies</b> → <span class="inline-code">accounts.google.com</span>.</li>
            <li>Copy the value of the <span class="inline-code">oauth_token</span> cookie.</li>
          </ol>
        </div>
      </div>
      <div class="step">
        <div class="step__num">3</div>
        <div class="step__body">
          <h4>Paste it here</h4>
          <div class="field"><input class="input input--mono" id="oauthTok" placeholder="oauth2_4/..." autocomplete="off" spellcheck="false" /></div>
          <div class="field" style="margin-bottom:0"><input class="input" id="connLabel" placeholder="Label (optional, e.g. &quot;Family phone&quot;)" value="${esc(relink ? existing.label || "" : "")}" /></div>
        </div>
      </div>
      <details style="margin-top:4px">
        <summary class="muted" style="cursor:pointer;font-size:13px">Already have an auth_data string? Paste it instead</summary>
        <div class="field" style="margin-top:12px;margin-bottom:0"><textarea class="textarea" id="rawAuth" placeholder="androidId=...&Email=...&Token=..."></textarea></div>
      </details>
    </div>
    <div class="modal__foot">
      <button class="btn btn--ghost" onclick="closeModal()">Cancel</button>
      <button class="btn btn--primary" id="connectGo">${relink ? "Reconnect account" : "Connect account"}</button>
    </div>
  </div>`);
  const btn = $("#connectGo", inner);
  btn.addEventListener("click", async () => {
    const tok = $("#oauthTok", inner).value.trim();
    const raw = $("#rawAuth", inner).value.trim();
    const label = $("#connLabel", inner).value.trim();
    if (!tok && !raw) { toast("Paste the oauth_token (or an auth_data string).", "err"); return; }
    btn.disabled = true; btn.innerHTML = `<span class="spinner"></span> Connecting…`;
    try {
      const r = raw
        ? await api("/api/connect/raw", { method: "POST", body: { auth_data: raw, label } })
        : await api("/api/connect/token", { method: "POST", body: { oauth_token: tok, label } });
      closeModal();
      showConnected(r);
      refresh();
    } catch (e) {
      toast(e.message, "err");
      btn.disabled = false; btn.textContent = relink ? "Reconnect account" : "Connect account";
    }
  });
  openModal(inner, { wide: true });
  setTimeout(() => $("#oauthTok", inner)?.focus(), 50);
}

function showConnected(r) {
  const inner = node(`<div>
    <div class="modal__body" style="text-align:center;padding:36px 28px">
      <svg class="success-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-opacity=".25"/><path d="M8 12.5l2.5 2.5L16 9"/></svg>
      <h3 style="font-size:20px;margin-bottom:6px">${r.action === "updated" ? "Account reconnected" : "You're connected"}</h3>
      <p class="muted" style="margin:0 auto;max-width:36ch">${esc(r.email)} is ready. Drop photos into its folder (<span class="inline-code">${esc(r.folder)}</span>) or point Syncthing at it, and GPMC takes care of the rest.</p>
    </div>
    <div class="modal__foot" style="justify-content:center">
      <button class="btn btn--ghost" onclick="closeModal()">Done</button>
      <button class="btn btn--primary" id="setupPhone">${I.phoneqr} Set up my phone</button>
    </div>
  </div>`);
  $("#setupPhone", inner).addEventListener("click", () => { closeModal(); openDeviceSync(); });
  openModal(inner);
}

/* ---------------- device sync (syncthing) ---------------- */
function openDeviceSync() {
  const inner = node(`<div>
    ${modalHead("Device Sync", "Pair phones to Syncthing and choose which account each one backs up to.")}
    <div class="modal__body" id="dsBody"><div class="center-pad"><span class="spinner spinner--lg"></span></div></div>
  </div>`);
  openModal(inner, { wide: true });
  renderDeviceSync($("#dsBody", inner));
}

async function renderDeviceSync(body) {
  body.innerHTML = `<div class="center-pad"><span class="spinner spinner--lg"></span></div>`;
  let st;
  try { st = await api("/api/syncthing/status"); }
  catch (e) { body.innerHTML = `<p class="muted">${esc(e.message)}</p><div class="modal__foot" style="padding:16px 0 0;border:none"><button class="btn btn--ghost" onclick="closeModal()">Close</button></div>`; return; }

  if (!st.available) {
    body.innerHTML = `<div class="ds-note">${I.info}<div>Syncthing isn't running on this server yet. The Proxmox installer sets it up automatically; otherwise install Syncthing and reopen this.<br/><span class="muted" style="font-size:12px">Looked for its config at <span class="inline-code">${esc(st.config_path || "")}</span></span></div></div>
      <div class="modal__foot" style="padding:16px 0 0;border:none"><button class="btn btn--ghost" onclick="closeModal()">Close</button></div>`;
    return;
  }

  const hasAccts = st.accounts.length > 0;
  const accOpts = (sel) => st.accounts.map((a) => `<option value="${a.id}" ${a.id === sel ? "selected" : ""}>${esc(a.label)}</option>`).join("");

  const pendRows = st.pending.map((p) => `
    <div class="ds-row">
      <span class="ds-dot ds-dot--pend"></span>
      <div class="ds-row__main"><b>${esc(p.name || "New phone")}</b><span>waiting to link · ${esc(p.id.slice(0, 7))}…</span></div>
      <select class="select ds-sel" data-dev="${esc(p.id)}" ${hasAccts ? "" : "disabled"}>${accOpts()}</select>
      <button class="btn btn--sm btn--primary ds-link" data-dev="${esc(p.id)}" data-name="${esc(p.name || "")}" ${hasAccts ? "" : "disabled"}>Link</button>
    </div>`).join("");

  const devRows = st.devices.map((d) => `
    <div class="ds-row">
      <span class="ds-dot ${d.connected ? "ds-dot--on" : "ds-dot--off"}"></span>
      <div class="ds-row__main"><b>${esc(d.name || d.id.slice(0, 7))}</b><span>${d.connected ? "online" : "offline"} · ${esc(d.id.slice(0, 7))}…</span></div>
      <select class="select ds-sel ds-change" data-dev="${esc(d.id)}" ${hasAccts ? "" : "disabled"}>${accOpts(d.account_id)}</select>
      <button class="btn btn--icon btn--ghost ds-remove" data-dev="${esc(d.id)}" title="Remove phone">${I.trash}</button>
    </div>`).join("");

  body.innerHTML = `
    <div class="ds-server">
      <div class="qr-box"><img alt="Server device ID" src="/api/qr?data=${encodeURIComponent(st.my_id)}" /></div>
      <div class="ds-server__info">
        <h4>Add this server on your phone</h4>
        <p class="muted">Install Syncthing (Android: “Syncthing” / “Syncthing-Fork”; iOS: “Möbius Sync”), add a remote device and scan this QR — or paste the ID. It then appears under Phones to link.</p>
        <div class="ds-id"><code>${esc(st.my_id)}</code><button class="btn btn--sm ds-copy" data-copy="${esc(st.my_id)}">Copy ID</button>${st.gui_url ? `<a class="btn btn--sm btn--ghost" href="${esc(st.gui_url)}" target="_blank" rel="noopener">${I.external} Syncthing GUI</a>` : ""}</div>
      </div>
    </div>
    ${!hasAccts ? `<div class="ds-note">${I.info}<div>Connect a Google account first — then you can choose which account a phone backs up to.</div></div>` : ""}
    <h4 class="ds-h">Phones</h4>
    <div class="ds-list">
      ${pendRows}${devRows}
      ${(!st.pending.length && !st.devices.length) ? `<p class="muted" style="padding:8px 2px">No phones yet. Add this server in your phone's Syncthing app, then hit Refresh.</p>` : ""}
    </div>
    <details class="ds-add">
      <summary class="muted">Add a phone by Device ID instead</summary>
      <div class="field" style="margin-top:12px"><input class="input input--mono" id="dsNewId" placeholder="XXXXXXX-XXXXXXX-XXXXXXX-…" autocomplete="off" spellcheck="false" /></div>
      <div class="grid-2">
        <div class="field" style="margin-bottom:10px"><input class="input" id="dsNewName" placeholder="Name (e.g. Mum's iPhone)" /></div>
        <div class="field" style="margin-bottom:10px"><select class="select" id="dsNewAcct" ${hasAccts ? "" : "disabled"}>${accOpts()}</select></div>
      </div>
      <button class="btn btn--primary" id="dsAddBtn" ${hasAccts ? "" : "disabled"}>Link phone</button>
    </details>
    <div class="ds-tip muted">On the phone: when the shared folder appears, accept it, point it at your <b>camera/DCIM</b> folder, and set it to <b>Send Only</b>. Several phones can back up to the same account.</div>
    <div class="modal__foot" style="padding:16px 0 0;border:none">
      <button class="btn btn--ghost" id="dsRefresh">Refresh</button>
      <div style="flex:1"></div>
      <button class="btn btn--primary" onclick="closeModal()">Done</button>
    </div>`;

  body.querySelectorAll(".ds-copy").forEach((b) => b.addEventListener("click", () => { try { navigator.clipboard.writeText(b.dataset.copy); } catch {} toast("Device ID copied", "ok"); }));
  $("#dsRefresh", body).addEventListener("click", () => renderDeviceSync(body));
  body.querySelectorAll(".ds-link").forEach((b) => b.addEventListener("click", () => {
    const sel = body.querySelector(`.ds-sel[data-dev="${b.dataset.dev}"]`);
    dsLink(b.dataset.dev, b.dataset.name, sel && sel.value, body);
  }));
  body.querySelectorAll(".ds-change").forEach((sel) => sel.addEventListener("change", () => dsLink(sel.dataset.dev, "", sel.value, body)));
  body.querySelectorAll(".ds-remove").forEach((b) => b.addEventListener("click", async () => {
    if (!confirm("Remove this phone from Syncthing? Its photos already uploaded stay in Google Photos.")) return;
    try { await api(`/api/syncthing/devices/${encodeURIComponent(b.dataset.dev)}`, { method: "DELETE" }); toast("Phone removed", "ok"); renderDeviceSync(body); }
    catch (e) { toast(e.message, "err"); }
  }));
  const addBtn = $("#dsAddBtn", body);
  if (addBtn) addBtn.addEventListener("click", () => dsLink($("#dsNewId", body).value, $("#dsNewName", body).value, $("#dsNewAcct", body).value, body));
}

async function dsLink(deviceId, name, accountId, body) {
  if (!deviceId || !deviceId.trim()) { toast("Enter a Device ID", "err"); return; }
  if (!accountId) { toast("Pick an account for this phone", "err"); return; }
  try {
    await api("/api/syncthing/link", { method: "POST", body: { device_id: deviceId.trim(), name: name || "", account_id: Number(accountId) } });
    toast("Phone linked", "ok");
    renderDeviceSync(body);
  } catch (e) { toast(e.message, "err"); renderDeviceSync(body); }
}

/* ---------------- account modal (settings / logs / upload) ---------------- */
function openAccountModal(acc, tab = "settings") {
  const s = acc;
  const inner = node(`<div>
    ${modalHead(acc.label && acc.label !== acc.email ? acc.label : acc.email, acc.email)}
    <div class="modal__body">
      <div class="tabs">
        <button data-t="settings">Settings</button>
        <button data-t="upload">Add photos</button>
        <button data-t="logs">Activity</button>
      </div>
      <div id="tabBody"></div>
    </div>
  </div>`);
  const body = $("#tabBody", inner);
  const tabs = inner.querySelectorAll(".tabs button");
  const select = (t) => { tabs.forEach((b) => b.classList.toggle("is-active", b.dataset.t === t)); drawTab(t); };
  tabs.forEach((b) => b.addEventListener("click", () => select(b.dataset.t)));

  function drawTab(t) {
    if (t === "settings") body.innerHTML = settingsForm(s);
    if (t === "settings") wireSettingsForm(body, s);
    if (t === "upload") { body.innerHTML = uploadPane(s); wireUpload(body, s); }
    if (t === "logs") { body.innerHTML = `<div class="logs" id="logBox"><div class="logs__empty">Loading…</div></div><div class="modal__foot" style="padding:16px 0 0;border:none"><button class="btn btn--ghost" onclick="closeModal()">Close</button></div>`; loadLogs(s.id, $("#logBox", body)); }
  }
  openModal(inner, { wide: true });
  select(tab);
}

function settingsForm(s) {
  const opt = (v, cur, label) => `<option value="${v}" ${v === cur ? "selected" : ""}>${label}</option>`;
  return `
    <div class="field"><label>Label</label><input class="input" id="f_label" value="${esc(s.label || "")}" placeholder="${esc(s.email)}" /></div>
    <div class="grid-2">
      <div class="field"><label>Album</label><select class="select" id="f_album_mode">
        ${opt("auto", s.album_mode, "Auto — one album per subfolder")}
        ${opt("custom", s.album_mode, "A specific album")}
        ${opt("none", s.album_mode, "No album")}
      </select></div>
      <div class="field" id="customAlbumWrap" style="${s.album_mode === "custom" ? "" : "display:none"}"><label>Album name</label><input class="input" id="f_album_name" value="${esc(s.album_name || "")}" placeholder="My Album" /></div>
    </div>
    <div class="grid-2">
      <div class="field"><label>Upload threads</label><input class="input" type="number" id="f_threads" min="1" max="16" value="${s.threads}" /></div>
      <div class="field"><label>Retries per cycle</label><input class="input" type="number" id="f_retries" min="1" max="10" value="${s.max_retries}" /></div>
    </div>
    <div style="margin-top:4px">
      <div class="toggle"><div class="toggle__text"><b>Delete after upload</b><span>Remove the local file once it's safely in Google Photos</span></div>
        <label class="switch"><input type="checkbox" id="f_delete" ${s.delete_after ? "checked" : ""}/><span class="switch__track"></span></label></div>
      <div class="toggle"><div class="toggle__text"><b>Storage saver quality</b><span>Upload compressed copies instead of originals</span></div>
        <label class="switch"><input type="checkbox" id="f_saver" ${s.saver ? "checked" : ""}/><span class="switch__track"></span></label></div>
      <div class="toggle"><div class="toggle__text"><b>Count against Google storage</b><span>Off = uploads don't use your quota where eligible</span></div>
        <label class="switch"><input type="checkbox" id="f_quota" ${s.use_quota ? "checked" : ""}/><span class="switch__track"></span></label></div>
      <div class="toggle"><div class="toggle__text"><b>Include subfolders</b><span>Scan the account folder recursively</span></div>
        <label class="switch"><input type="checkbox" id="f_recursive" ${s.recursive ? "checked" : ""}/><span class="switch__track"></span></label></div>
      <div class="toggle"><div class="toggle__text"><b>Active</b><span>Turn off to pause backups for this account</span></div>
        <label class="switch"><input type="checkbox" id="f_enabled" ${s.enabled ? "checked" : ""}/><span class="switch__track"></span></label></div>
    </div>
    <div class="field" style="margin-top:16px"><label>Heartbeat URL (optional)</label><input class="input" id="f_heartbeat" value="${esc(s.heartbeat_url || "")}" placeholder="https://… pinged after a successful backup" /></div>
    <div class="modal__foot" style="padding:16px 0 0;border:none">
      <button class="btn btn--ghost" onclick="closeModal()">Cancel</button>
      <button class="btn btn--primary" id="saveAcc">Save changes</button>
    </div>`;
}
function wireSettingsForm(root, s) {
  const mode = $("#f_album_mode", root);
  mode.addEventListener("change", () => { $("#customAlbumWrap", root).style.display = mode.value === "custom" ? "" : "none"; });
  $("#saveAcc", root).addEventListener("click", async () => {
    const payload = {
      label: $("#f_label", root).value.trim(),
      album_mode: mode.value,
      album_name: $("#f_album_name", root)?.value.trim() || "",
      threads: Number($("#f_threads", root).value) || 3,
      max_retries: Number($("#f_retries", root).value) || 3,
      delete_after: $("#f_delete", root).checked,
      saver: $("#f_saver", root).checked,
      use_quota: $("#f_quota", root).checked,
      recursive: $("#f_recursive", root).checked,
      enabled: $("#f_enabled", root).checked,
      skip_existing_filenames: s.skip_existing_filenames,
      heartbeat_url: $("#f_heartbeat", root).value.trim(),
    };
    try { await api(`/api/accounts/${s.id}`, { method: "PUT", body: payload }); toast("Settings saved", "ok"); closeModal(); refresh(); }
    catch (e) { toast(e.message, "err"); }
  });
}

function uploadPane(s) {
  return `<p class="muted" style="margin-top:0">Add photos or videos straight into <span class="inline-code">${esc(s.folder)}</span>. They'll upload on the next cycle (or hit Back up now).</p>
    <label class="drop" id="drop">${I.upload}<div>Drop files here, or click to choose</div><input type="file" id="fileInput" multiple accept="image/*,video/*" hidden /></label>
    <div id="upStatus" class="muted" style="margin-top:12px;font-size:13px"></div>
    <div class="modal__foot" style="padding:16px 0 0;border:none"><button class="btn btn--ghost" onclick="closeModal()">Close</button></div>`;
}
function wireUpload(root, s) {
  const drop = $("#drop", root), input = $("#fileInput", root), status = $("#upStatus", root);
  const send = async (files) => {
    if (!files || !files.length) return;
    const fd = new FormData();
    [...files].forEach((f) => fd.append("files", f));
    status.innerHTML = `<span class="spinner"></span> Uploading ${files.length} file(s)…`;
    try { const r = await api(`/api/accounts/${s.id}/upload`, { method: "POST", body: fd }); status.textContent = `Added ${r.saved} file(s). They'll back up shortly.`; refresh(); }
    catch (e) { status.textContent = ""; toast(e.message, "err"); }
  };
  input.addEventListener("change", () => send(input.files));
  ["dragover", "dragenter"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("is-over"); }));
  ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("is-over"); }));
  drop.addEventListener("drop", (e) => send(e.dataTransfer.files));
}

async function loadLogs(id, box) {
  try {
    const d = await api(`/api/accounts/${id}/logs`);
    const items = [...(d.live || [])];
    if (!items.length && (!d.history || !d.history.length)) { box.innerHTML = `<div class="logs__empty">No activity yet.</div>`; return; }
    const live = (d.live || []).map((l) => `<div class="log log--${l.level}"><time>${esc(l.ts)}</time><span>${esc(l.message)}</span></div>`).join("");
    const hist = (d.history || []).map((l) => `<div class="log log--${l.level}"><time>${esc((l.ts || "").slice(11, 19))}</time><span>${esc(l.message)}</span></div>`).join("");
    box.innerHTML = live + (live && hist ? `<div class="menu__sep"></div>` : "") + hist || `<div class="logs__empty">No activity yet.</div>`;
  } catch (e) { box.innerHTML = `<div class="logs__empty">${esc(e.message)}</div>`; }
}

function confirmDelete(acc) {
  const inner = node(`<div>
    ${modalHead("Remove account", "")}
    <div class="modal__body">
      <p>Remove <b>${esc(acc.email)}</b> from GPMC? This deletes the stored sign-in key. Your photos already in Google Photos are untouched.</p>
      <div class="toggle" style="margin-top:8px"><div class="toggle__text"><b>Also delete its local folder</b><span>Removes queued files not yet uploaded</span></div>
        <label class="switch"><input type="checkbox" id="delFolder"/><span class="switch__track"></span></label></div>
    </div>
    <div class="modal__foot"><button class="btn btn--ghost" onclick="closeModal()">Cancel</button><button class="btn btn--danger" id="doDelete">Remove account</button></div>
  </div>`);
  $("#doDelete", inner).addEventListener("click", async () => {
    try { await api(`/api/accounts/${acc.id}?delete_folder=${$("#delFolder", inner).checked}`, { method: "DELETE" }); toast("Account removed", "ok"); closeModal(); refresh(); }
    catch (e) { toast(e.message, "err"); }
  });
  openModal(inner);
}

/* ---------------- global settings ---------------- */
async function openSettings() {
  let cfg;
  try { cfg = await api("/api/settings"); } catch (e) { toast(e.message, "err"); return; }
  const theme = localStorage.getItem("gpmc_theme") || cfg.theme || "dark";
  const opt = (v, label) => `<option value="${v}" ${v === theme ? "selected" : ""}>${label}</option>`;
  const inner = node(`<div>
    ${modalHead("Settings", "")}
    <div class="modal__body">
      <div class="grid-2">
        <div class="field"><label>Backup interval (minutes)</label><input class="input" type="number" id="s_interval" min="1" max="1440" value="${cfg.sync_interval_min}" /><div class="hint">How often GPMC checks the folders and uploads.</div></div>
        <div class="field"><label>Appearance</label><select class="select" id="s_theme">${opt("dark", "Dark")}${opt("light", "Light")}${opt("system", "Match system")}</select></div>
      </div>
      <div class="field"><label>Notification webhook (optional)</label><input class="input" id="s_webhook" value="${esc(cfg.webhook_url || "")}" placeholder="Discord / Slack / ntfy URL" /><div class="hint">Posts a line when a backup finishes or fails.</div></div>
      <div class="field"><label>UI password</label><input class="input" type="password" id="s_pw" placeholder="${cfg.has_password ? "•••••••• (set — leave blank to keep)" : "Set a password to lock the UI"}" /><div class="hint">${cfg.has_password ? "Type a new one to change it, or a single space then save to remove." : "Optional — locks this dashboard."}</div></div>
      <div class="toggle"><div class="toggle__text"><b>Allow revealing sign-in keys</b><span>Lets you copy an account's raw auth_data from the UI</span></div>
        <label class="switch"><input type="checkbox" id="s_reveal" ${cfg.allow_reveal_auth ? "checked" : ""}/><span class="switch__track"></span></label></div>
      <div class="toggle"><div class="toggle__text"><b>Device sync (phones)</b><span>Pair phones with Syncthing and map each to an account</span></div>
        <button type="button" class="btn btn--sm" id="dsFromSettings">Manage phones</button></div>
      <div class="hint" style="margin-top:16px">Config: <span class="inline-code">${esc(cfg.config_dir)}</span><br/>Media: <span class="inline-code">${esc(cfg.sync_dir)}</span></div>
    </div>
    <div class="modal__foot">
      <button class="btn btn--ghost" id="logoutBtn">Log out</button>
      <div style="flex:1"></div>
      <button class="btn btn--ghost" onclick="closeModal()">Cancel</button>
      <button class="btn btn--primary" id="saveSettings">Save</button>
    </div>
  </div>`);
  $("#s_theme", inner).addEventListener("change", (e) => applyTheme(e.target.value));
  $("#dsFromSettings", inner).addEventListener("click", () => { closeModal(); openDeviceSync(); });
  $("#logoutBtn", inner).addEventListener("click", async () => { try { await api("/api/logout", { method: "POST" }); } catch {} location.reload(); });
  $("#saveSettings", inner).addEventListener("click", async () => {
    const pw = $("#s_pw", inner).value;
    const payload = {
      sync_interval_min: Number($("#s_interval", inner).value) || 5,
      webhook_url: $("#s_webhook", inner).value.trim(),
      allow_reveal_auth: $("#s_reveal", inner).checked,
      theme: $("#s_theme", inner).value,
      password: pw === "" ? null : pw.trim(),
    };
    try { await api("/api/settings", { method: "POST", body: payload }); applyTheme(payload.theme); toast("Settings saved", "ok"); closeModal(); }
    catch (e) { toast(e.message, "err"); }
  });
  openModal(inner, { wide: true });
}

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if ((localStorage.getItem("gpmc_theme") || "dark") === "system") applyTheme("system");
});

boot();
