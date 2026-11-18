/* Quality Vault — preview-before-download viewer (shared by every tool page).
   Each page sets window.QV = {gh, files, zip, sheets} before loading this file. */
(function () {
  const Q = window.QV || {};
  const FILES = Q.files || {}, ZIP = Q.zip || [], SHEETS = Q.sheets || [];
  const $ = id => document.getElementById(id);
  const M = $("qv-modal"), body = $("qv-body");
  if (!M) return;
  const esc = t => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const kb = n => n < 1024 ? n + " bytes" : (n / 1024).toFixed(1) + " KB";
  let lastFocus = null, codeText = "";

  function highlight(line, lang) {
    if (lang === "md") return esc(line);
    let inS = null, cut = -1;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (inS) { if (c === "\\") i++; else if (c === inS) inS = null; }
      else if (c === '"' || c === "'") inS = c;
      else if (c === "#") { cut = i; break; }
    }
    const code = cut < 0 ? line : line.slice(0, cut), cm = cut < 0 ? "" : line.slice(cut);
    const kw = lang === "py"
      ? /\b(def|class|return|if|elif|else|for|while|in|import|from|as|with|try|except|raise|lambda|None|True|False|and|or|not|is)\b/g
      : /\b(function|return|if|else|for|while|in|TRUE|FALSE|NULL|NA|Inf|switch|stop|library|structure)\b/g;
    let out = "", last = 0, re = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, m;
    while ((m = re.exec(code))) {
      out += esc(code.slice(last, m.index)).replace(kw, '<span class="kw">$1</span>');
      out += '<span class="st">' + esc(m[0]) + "</span>"; last = re.lastIndex;
    }
    out += esc(code.slice(last)).replace(kw, '<span class="kw">$1</span>');
    return out + (cm ? '<span class="cm">' + esc(cm) + "</span>" : "");
  }

  function csvRows(text) {
    const rows = []; let row = [], f = "", q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) { if (c === '"' && text[i + 1] === '"') { f += '"'; i++; } else if (c === '"') q = false; else f += c; }
      else if (c === '"') q = true;
      else if (c === ",") { row.push(f); f = ""; }
      else if (c === "\n") { row.push(f.replace(/\r$/, "")); rows.push(row); row = []; f = ""; }
      else f += c;
    }
    if (f !== "" || row.length) { row.push(f); rows.push(row); }
    return rows;
  }

  async function sha256(buf) {
    if (!(window.crypto && crypto.subtle)) return "open the page over https to see the checksum";
    const h = await crypto.subtle.digest("SHA-256", buf);
    return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, "0")).join("");
  }

  async function openFile(name) {
    const info = FILES[name]; if (!info) return;
    lastFocus = document.activeElement;
    $("qv-title").textContent = name; $("qv-meta").textContent = info.label + " · loading…";
    $("qv-sha").textContent = "calculating…"; body.innerHTML = ""; codeText = "";
    $("qv-dl").href = name; $("qv-dl").setAttribute("download", name);
    $("qv-gh").href = Q.gh + name;
    $("qv-copy").style.display = info.kind === "code" || info.kind === "csv" ? "" : "none";
    $("qv-note").textContent = info.kind === "code" ? "Read it first — this is exactly the file you'll download."
      : info.kind === "xlsx" ? "Opens in Excel, LibreOffice or Google Sheets. Contains formulas only."
      : info.kind === "zip" ? "Preview any file inside before downloading the whole set." : "";
    M.classList.add("open"); document.body.style.overflow = "hidden"; $("qv-close").focus();
    try {
      const res = await fetch(name, { cache: "no-store" });
      if (!res.ok) throw new Error(res.status);
      const buf = await res.arrayBuffer();
      sha256(buf).then(h => $("qv-sha").textContent = h);
      if (info.kind === "code" || info.kind === "csv") {
        codeText = new TextDecoder().decode(buf);
        const lines = codeText.replace(/\n$/, "").split("\n");
        $("qv-meta").textContent = `${info.label} · ${lines.length} lines · ${kb(buf.byteLength)}`;
        if (info.kind === "csv") {
          const rows = csvRows(codeText.replace(/\n$/, ""));
          body.innerHTML = '<div class="qv-info" style="overflow:auto"><table><thead><tr>' +
            rows[0].map(h => "<th>" + esc(h) + "</th>").join("") + "</tr></thead><tbody>" +
            rows.slice(1).map(r => "<tr>" + r.map(c => '<td class="' + (c !== "" && isFinite(c) ? "n" : "") + '">' + esc(c) + "</td>").join("") + "</tr>").join("") +
            "</tbody></table></div>";
        } else {
          body.innerHTML = '<pre class="qv-code">' + lines.map(l => '<span class="l">' + (highlight(l, info.lang) || " ") + "</span>").join("") + "</pre>";
        }
      } else if (info.kind === "img") {
        $("qv-meta").textContent = `${info.label} · ${kb(buf.byteLength)}`;
        body.innerHTML = '<div class="qv-info" style="background:#fff"><img src="' + name + '" alt="" style="width:100%;display:block"></div>';
      } else if (info.kind === "xlsx") {
        $("qv-meta").textContent = `${info.label} · ${kb(buf.byteLength)}`;
        body.innerHTML = `<div class="qv-info"><b>What's inside</b>
          <p>${SHEETS.length} sheets. Input cells are highlighted; everything else is a standard Excel formula you can click and inspect.</p>
          <table><thead><tr><th>Sheet</th><th>Contents</th></tr></thead><tbody>` +
          SHEETS.map(([s, d]) => `<tr><td>${esc(s)}</td><td>${esc(d)}</td></tr>`).join("") +
          `</tbody></table>
          <p style="margin-top:1.25rem"><b style="color:var(--text)">No macros, no external links.</b> The .xlsx format cannot store macros (that would need .xlsm), so Excel will not show a security prompt.</p></div>`;
      } else if (info.kind === "zip") {
        $("qv-meta").textContent = `${info.label} · ${ZIP.length} files · ${kb(buf.byteLength)}`;
        body.innerHTML = '<div class="qv-info"><b>Contents</b><p>Every file is also listed on this page, so you can preview each one on its own.</p>' +
          ZIP.map(([f, z]) => `<div class="zl"><span>${esc(f)} <span style="color:var(--muted)">· ${z}</span></span>` +
            (FILES[f] ? `<button type="button" data-file="${esc(f)}">Preview</button>` : "") + `</div>`).join("") + "</div>";
      }
    } catch (e) {
      $("qv-meta").textContent = info.label;
      body.innerHTML = '<div class="qv-info"><p>Preview could not load (' + esc(String(e.message || e)) + '). You can still read the file on GitHub.</p></div>';
      $("qv-sha").textContent = "—";
    }
  }
  function closeFile() { M.classList.remove("open"); document.body.style.overflow = ""; if (lastFocus) lastFocus.focus(); }
  document.addEventListener("click", e => { const b = e.target.closest("[data-file]"); if (b) { e.preventDefault(); openFile(b.dataset.file); } });
  $("qv-close").onclick = closeFile;
  M.addEventListener("click", e => { if (e.target === M) closeFile(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && M.classList.contains("open")) closeFile(); });
  $("qv-copy").onclick = () => navigator.clipboard && navigator.clipboard.writeText(codeText).then(() => {
    $("qv-copy").textContent = "Copied"; setTimeout(() => $("qv-copy").textContent = "Copy code", 1500); });
  if (location.hash && FILES[decodeURIComponent(location.hash.slice(1))]) openFile(decodeURIComponent(location.hash.slice(1)));

  // figure tabs (Python / R chart) and copy buttons on code blocks
  document.querySelectorAll(".fig-tabs button").forEach(b => b.onclick = () => {
    document.querySelectorAll(".fig-tabs button").forEach(x => x.classList.toggle("on", x === b));
    document.querySelectorAll("[data-fig]").forEach(f => f.hidden = f.dataset.fig !== b.dataset.t);
  });
})();
