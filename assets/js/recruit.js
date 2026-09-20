/* ==========================================================================
   干员寻访 · Operator Recruitment
   从当日档案中随机抽取条目，作为进入解读 / 雷达的入口。
   依赖 app.js 暴露的 window.AG。
   ========================================================================== */
(function () {
  "use strict";

  var $ = function (s) { return document.querySelector(s); };
  var SEEN_KEY = "all_game_recruited";

  var overlay = $("#recruit");
  var stage = $("#recruit-stage");
  var result = $("#recruit-result");
  var hint = $("#recruit-hint");

  var store = { date: "", ids: [] };
  var busy = false;

  /* ------------------------------ 已寻访记录 ------------------------------ */

  function loadStore() {
    try {
      var raw = JSON.parse(localStorage.getItem(SEEN_KEY) || "{}");
      store.date = raw.date || "";
      store.ids = Array.isArray(raw.ids) ? raw.ids : [];
    } catch (e) {
      store = { date: "", ids: [] };
    }
  }

  function saveStore() {
    try { localStorage.setItem(SEEN_KEY, JSON.stringify(store)); } catch (e) {}
  }

  function syncDate() {
    var d = window.AG && window.AG.date ? window.AG.date() : "";
    if (d && store.date !== d) { store.date = d; store.ids = []; saveStore(); }
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* ------------------------------ 开合 ------------------------------ */

  function open() {
    overlay.classList.add("is-open");
    document.body.style.overflow = "hidden";
    syncDate();
    updateHint();
  }

  function close() {
    overlay.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  /* ------------------------------ 抽取 ------------------------------ */

  function pool() {
    var all = (window.AG && window.AG.items) ? window.AG.items() : [];
    return all.filter(function (it) { return store.ids.indexOf(it.id || it.title) === -1; });
  }

  function draw(n) {
    var p = pool();
    if (!p.length) return [];
    var out = [];
    var bag = p.slice();
    while (out.length < n && bag.length) {
      var i = Math.floor(Math.random() * bag.length);
      out.push(bag.splice(i, 1)[0]);
    }
    out.forEach(function (it) { store.ids.push(it.id || it.title); });
    saveStore();
    return out;
  }

  function updateHint() {
    var all = (window.AG && window.AG.items) ? window.AG.items() : [];
    var left = pool().length;
    if (!all.length) {
      hint.textContent = "档案尚未载入，请稍候。";
      return;
    }
    hint.innerHTML = "今日档案共 <b>" + all.length + "</b> 则动向，" +
      "已寻访 <b>" + (all.length - left) + "</b> 则，剩余 <b>" + left + "</b> 则可抽取；" +
      "已抽到的不会重复出现。";
  }

  /* ------------------------------ 结果渲染 ------------------------------ */

  function opCard(item) {
    var id = item.id || item.title;
    var hasEssay = !!(item.essay && item.essay.length) || !!item.problem || !!item.insight;
    var tags = (item.tags || []).map(function (t) {
      return '<span class="tag">' + esc(t) + "</span>";
    }).join("");

    var actions =
      (hasEssay
        ? '<button class="btn btn--solid" type="button" data-focus="' + esc(id) + '">查看完整解读 →</button>'
        : '<button class="btn" type="button" data-find="' + esc(item.title) + '">在雷达中定位</button>') +
      (item.abs_url
        ? '<a class="btn" href="' + esc(item.abs_url) + '" target="_blank" rel="noopener">原文 →</a>'
        : "");

    return '<article class="opcard" data-klass="' + window.AG.klassOf(item) + '">' +
      '<div class="opcard__top">' +
        window.AG.klassChip(item, false) +
        '<span class="micro">' + esc(item.section || "其他交叉方向") + "</span>" +
        (item.curated ? '<span class="tag tag--new" style="margin-left:auto">精读</span>' : "") +
      "</div>" +
      '<h3 class="opcard__name">' + esc(item.title) + "</h3>" +
      (item.title_en ? '<p class="opcard__en">' + esc(item.title_en) + "</p>" : "") +
      (item.glance || item.summary_short
        ? '<p class="opcard__glance">' + esc(item.glance || item.summary_short) + "</p>"
        : "") +
      (tags ? '<div class="opcard__tags">' + tags + "</div>" : "") +
      '<div class="opcard__go">' + actions + "</div>" +
      "</article>";
  }

  function renderResult(list) {
    if (!list.length) {
      result.innerHTML =
        '<div class="recruit__empty">今日档案已全部寻访完毕。<br />可以点「重置寻访记录」再来一轮，' +
        "或等明日更新后的新动向。</div>";
      result.classList.add("is-on");
      return;
    }
    result.innerHTML =
      '<div class="result__grid' + (list.length === 1 ? " result__grid--single" : "") + '">' +
      list.map(opCard).join("") + "</div>";
    result.classList.add("is-on");

    Array.prototype.forEach.call(result.querySelectorAll("[data-focus]"), function (b) {
      b.addEventListener("click", function () {
        close();
        window.AG.focus(b.getAttribute("data-focus"));
      });
    });
    Array.prototype.forEach.call(result.querySelectorAll("[data-find]"), function (b) {
      b.addEventListener("click", function () {
        close();
        window.AG.find(b.getAttribute("data-find"));
      });
    });
  }

  /* ------------------------------ 寻访流程 ------------------------------ */

  function run(n) {
    if (busy) return;
    syncDate();
    if (!(window.AG && window.AG.items().length)) {
      hint.textContent = "档案尚未载入，请稍候再试。";
      return;
    }
    busy = true;
    result.classList.remove("is-on");
    result.innerHTML = "";
    stage.classList.add("is-on");
    hint.textContent = "正在检索罗德岛人事档案…";

    setTimeout(function () {
      var got = draw(n);
      stage.classList.remove("is-on");
      renderResult(got);
      updateHint();
      busy = false;
    }, 1150);
  }

  /* ------------------------------ 绑定 ------------------------------ */

  Array.prototype.forEach.call(document.querySelectorAll("[data-recruit]"), function (b) {
    b.addEventListener("click", function () {
      var n = parseInt(b.getAttribute("data-recruit"), 10) || 1;
      open();
      run(n);
    });
  });

  Array.prototype.forEach.call(document.querySelectorAll("[data-recruit-close]"), function (el) {
    el.addEventListener("click", close);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && overlay.classList.contains("is-open")) close();
  });

  $("#recruit-reset").addEventListener("click", function () {
    store.ids = [];
    saveStore();
    result.classList.remove("is-on");
    result.innerHTML = "";
    updateHint();
  });

  document.addEventListener("ag:ready", function () { syncDate(); updateHint(); });
  loadStore();
})();
