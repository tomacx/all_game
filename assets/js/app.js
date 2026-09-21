/* ==========================================================================
   博弈智能雷达 · 前端逻辑
   纯静态：读取 data/index.json 与 data/daily/<date>.json 渲染
   ========================================================================== */
(function () {
  "use strict";

  var $ = function (sel) { return document.querySelector(sel); };

  var state = {
    index: { days: [] },
    day: null,        // 当日数据
    date: null,       // 当前归档日期
    view: "brief",    // brief | radar | trends
    q: "",
    tags: [],         // 已选标签
    sort: "default",  // default | date | title
    onlyNew: true,
    openAll: false
  };

  /* 干员职业：只用于标识研究方向，不做任何等级评价 */
  var KLASS = {
    guard:     { cn: "近卫",  en: "GUARD",      path: "M8 2 14 8v10H2V8Z" },
    caster:    { cn: "术师",  en: "CASTER",     path: "M8 1.5 13.5 6 11 15H5L2.5 6Z" },
    supporter: { cn: "辅助",  en: "SUPPORTER",  path: "M8 2 14 5.5v7L8 16 2 12.5v-7Z" },
    specialist:{ cn: "特种",  en: "SPECIALIST", path: "M8 1.5 14.5 8 8 14.5 1.5 8Z" },
    defender:  { cn: "重装",  en: "DEFENDER",   path: "M8 2 14 5v6.5L8 15 2 11.5V5Z" },
    sniper:    { cn: "狙击",  en: "SNIPER",     path: "M8 2 13 9l-5 6-5-6Z" }
  };

  function klassOf(item) {
    var k = item && item.klass;
    if (!k && item && item.section) {
      var map = {
        "核心算法创新 · MARL": "guard",
        "博弈求解与理论": "caster",
        "机制设计与市场": "supporter",
        "LLM 多智能体与社会模拟": "specialist",
        "对抗、安全与鲁棒": "defender"
      };
      k = map[item.section] || "sniper";
    }
    return KLASS[k] ? k : "sniper";
  }

  function klassChip(item, withEn) {
    var k = klassOf(item);
    var d = KLASS[k];
    return '<span class="klass__chip" data-klass="' + k + '">' +
      '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="' + d.path +
      '" fill="currentColor"/></svg><span>' + d.cn + "</span></span>" +
      (withEn ? '<span class="klass__en micro">' + d.en + "</span>" : "");
  }

  /* ------------------------------ 工具 ------------------------------ */

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function hexSvg() {
    return '<svg class="sect__hex" viewBox="0 0 16 18" aria-hidden="true">' +
      '<path d="M8 0 16 4.5v9L8 18 0 13.5v-9Z" fill="var(--accent)"/></svg>';
  }

  function authorLine(authors, max) {
    if (!authors || !authors.length) return "";
    max = max || 4;
    var a = authors.slice(0, max);
    var out = a.join(", ");
    if (authors.length > max) out += " 等 " + authors.length + " 人";
    return out;
  }

  function getJSON(url) {
    return fetch(url, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error(url + " -> HTTP " + r.status);
      return r.json();
    });
  }

  /* ------------------------------ 主题 ------------------------------ */

  var THEME_KEY = "all_game_theme";

  function applyTheme(t) {
    document.documentElement.setAttribute("data-theme", t);
    try { localStorage.setItem(THEME_KEY, t); } catch (e) {}
    // 徽记与分区图标的主色随主题切换
    var mark = document.querySelector(".brand__mark");
    if (mark) {
      var c = t === "night" ? "#ffb13b" : "#e0742a";
      Array.prototype.forEach.call(mark.querySelectorAll("path"), function (p) {
        if (p.getAttribute("stroke")) p.setAttribute("stroke", c);
        if (p.getAttribute("fill") && p.getAttribute("fill") !== "none") p.setAttribute("fill", c);
      });
    }
  }

  function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (e) {}
    if (!saved) {
      saved = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "night" : "day";
    }
    applyTheme(saved);
    $("#theme-btn").addEventListener("click", function () {
      var cur = document.documentElement.getAttribute("data-theme");
      applyTheme(cur === "night" ? "day" : "night");
    });
  }

  /* ------------------------------ 数据加载 ------------------------------ */

  function currentDate() {
    var m = /[?&]d=(\d{4}-\d{2}-\d{2})/.exec(location.search);
    if (m) return m[1];
    if (state.index.days && state.index.days.length) return state.index.days[0].date;
    return null;
  }

  function load() {
    return getJSON("data/index.json")
      .then(function (idx) {
        state.index = idx;
        var d = currentDate();
        if (!d) throw new Error("暂无归档数据");
        state.date = d;
        renderArchive();
        return getJSON("data/daily/" + d + ".json");
      })
      .then(function (day) {
        state.day = day;
        renderHUD();
        renderHero();
        renderTagbar();
        render();
        document.dispatchEvent(new CustomEvent("ag:ready", { detail: { date: state.date } }));
      })
      .catch(function (err) {
        $("#view").innerHTML =
          '<div class="empty"><div style="font-size:15px;color:var(--danger)">档案载入失败</div>' +
          '<div style="margin-top:8px;font-family:var(--mono);font-size:12px">' +
          esc(err.message) + "</div></div>";
      });
  }

  /* ------------------------------ 渲染：HUD / Hero / 归档 ------------------------------ */

  function renderHUD() {
    var d = state.day || {};
    $("#hud-date").textContent = (d.date || "—").slice(5);
    $("#hud-brief").textContent = (d.highlights || []).length;
    $("#hud-radar").textContent = (d.radar || []).length;
    $("#hud-new").textContent = (d.source && d.source.new_count) || 0;
    $("#hud-scan").textContent = (d.source && d.source.total_raw) || 0;
  }

  function renderHero() {
    var d = state.day || {};
    var src = d.source || {};
    $("#hero-title").textContent = "博弈智能科研剪报 · " + (d.date || "");
    $("#hero-desc").innerHTML =
      "本期检索窗口 <strong>" + esc(src.window || "—") + "</strong>，" +
      "六路检索式共命中 <strong>" + (src.total_raw || 0) + "</strong> 篇，去重后 <strong>" +
      (src.unique || 0) + "</strong> 篇；其中人工精读 <strong>" +
      (d.highlights || []).length + "</strong> 篇，雷达收录 <strong>" +
      (d.radar || []).length + "</strong> 篇，<strong style=\"color:var(--accent)\">今日新增 " +
      (src.new_count || 0) + " 篇</strong>（已与往期 " + (src.seen_before || 0) + " 篇比对去重）。";
    var note = $("#hero-note");
    if (d.note) { note.hidden = false; note.textContent = d.note; } else { note.hidden = true; }
  }

  function renderArchive() {
    var box = $("#archive");
    var days = state.index.days || [];
    box.innerHTML = '<span class="micro" style="margin-right:4px">Archive</span>';
    days.slice(0, 14).forEach(function (d) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "archive__day";
      b.textContent = d.date;
      b.setAttribute("aria-pressed", String(d.date === state.date));
      b.addEventListener("click", function () {
        if (d.date === state.date) return;
        location.search = "?d=" + d.date;
      });
      box.appendChild(b);
    });
  }

  /* ------------------------------ 过滤逻辑 ------------------------------ */

  function radarList() {
    var ids = {};
    (state.day.highlights || []).forEach(function (h) { if (h.id) ids[h.id] = 1; });
    return (state.day.radar || []).filter(function (r) { return !ids[r.id]; });
  }

  function allItems() {
    // 精读条目补足雷达视图需要的字段，避免摘要为空
    var hs = (state.day.highlights || []).map(function (h) {
      return Object.assign({}, h, {
        curated: true,
        summary_short: h.summary_short || h.glance || ""
      });
    });
    return hs.concat(radarList());
  }

  function matchQ(item, q) {
    if (!q) return true;
    q = q.toLowerCase();
    var pool = [
      item.title, item.title_en, item.summary, item.summary_short, item.glance,
      item.problem, item.result, item.insight, item.id,
      (item.authors || []).join(" "), (item.tags || []).join(" ")
    ].join(" ").toLowerCase();
    return pool.indexOf(q) !== -1;
  }

  function filter(items) {
    return items.filter(function (it) {
      // 「仅看新增」只在雷达视图生效，且不影响当日精读条目
      if (state.onlyNew && state.view === "radar" && !it.curated && !it.is_new) return false;
      if (state.tags.length) {
        var own = it.tags || [];
        var hit = state.tags.some(function (t) { return own.indexOf(t) !== -1; });
        if (!hit) return false;
      }
      return matchQ(it, state.q);
    });
  }

  function sorted(items) {
    var arr = items.slice();
    if (state.sort === "date") {
      arr.sort(function (a, b) { return String(b.published || "").localeCompare(String(a.published || "")); });
    } else if (state.sort === "title") {
      arr.sort(function (a, b) { return String(a.title || "").localeCompare(String(b.title || ""), "zh"); });
    }
    return arr; // default：保持分区归类后的原始顺序
  }

  /* ------------------------------ 渲染：标签栏 ------------------------------ */

  function renderTagbar() {
    var counts = {};
    allItems().forEach(function (it) {
      (it.tags || []).forEach(function (t) { counts[t] = (counts[t] || 0) + 1; });
    });
    var keys = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; }).slice(0, 26);
    var box = $("#tagbar");
    box.innerHTML = "";
    keys.forEach(function (t) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "tagchip";
      b.textContent = t + " · " + counts[t];
      b.setAttribute("aria-pressed", String(state.tags.indexOf(t) !== -1));
      b.addEventListener("click", function () {
        var i = state.tags.indexOf(t);
        if (i === -1) state.tags.push(t); else state.tags.splice(i, 1);
        renderTagbar();
        render();
      });
      box.appendChild(b);
    });
    if (state.tags.length) {
      var clr = document.createElement("button");
      clr.type = "button";
      clr.className = "tagchip";
      clr.style.borderColor = "var(--danger)";
      clr.style.color = "var(--danger)";
      clr.textContent = "清除筛选 ×";
      clr.addEventListener("click", function () { state.tags = []; renderTagbar(); render(); });
      box.appendChild(clr);
    }
  }

  /* ------------------------------ 渲染：精读卡片 ------------------------------ */

  function cardHTML(h, i) {
    var meta = [];
    if (h.authors && h.authors.length) meta.push(esc(authorLine(h.authors, 3)));
    if (h.primary_category) meta.push(esc(h.primary_category));
    if (h.id) meta.push('arXiv:' + esc(h.id));
    if (h.published) meta.push(esc(h.published));

    return '' +
      '<article class="card' + (state.openAll ? " is-open" : "") + '"' +
        ' data-klass="' + klassOf(h) + '" id="op-' + esc(h.id || i) + '">' +
        '<div class="card__bar"></div>' +
        '<div class="card__head">' +
          '<div class="hex">' + String(i + 1).padStart(2, "0") + "</div>" +
          '<div class="card__ttl">' +
            "<h3>" + esc(h.title) + "</h3>" +
            (h.title_en ? '<p class="card__en">' + esc(h.title_en) + "</p>" : "") +
            '<div class="card__meta">' + meta.join(" · ") + "</div>" +
          "</div>" +
          '<div class="klass">' + klassChip(h, true) + "</div>" +
        "</div>" +
        (h.glance ? '<div class="glance">' + esc(h.glance) + "</div>" : "") +
        ((h.tags && h.tags.length)
          ? '<div class="tags">' + h.tags.map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("") + "</div>"
          : "") +
        '<div class="card__toggle">' +
          '<button class="btn btn--solid" data-toggle="1" type="button">' +
            (state.openAll ? "收起解读" : "展开解读") + "</button>" +
          (h.abs_url ? '<a class="btn" href="' + esc(h.abs_url) + '" target="_blank" rel="noopener">原文 →</a>' : "") +
        "</div>" +
        '<div class="mods">' + essayHTML(h) + "</div>" +
      "</article>";
  }

  /* 博客式解读：引入 → 分节叙述（穿插论文主图）→ 总结 */
  function essayHTML(h) {
    var blocks = h.essay;
    if (!blocks || !blocks.length) {
      // 兼容旧数据结构（problem/method/result/insight）
      var old = "";
      if (h.problem) old += '<div class="mod"><h4>核心问题</h4><p>' + esc(h.problem) + "</p></div>";
      if (h.method && h.method.length) {
        old += '<div class="mod"><h4>方法与建模</h4><ol>' +
          h.method.map(function (m) { return "<li>" + esc(m) + "</li>"; }).join("") + "</ol></div>";
      }
      if (h.result) old += '<div class="mod"><h4>实验与战绩</h4><p>' + esc(h.result) + "</p></div>";
      if (h.insight) old += '<div class="mod mod--insight"><h4>启示 · 可迁移点</h4><p>' + esc(h.insight) + "</p></div>";
      return old;
    }

    return '<div class="essay">' + blocks.map(function (b) {
      if (!b) return "";
      switch (b.t) {
        case "lead":
          return '<p class="essay__lead">' + esc(b.v) + "</p>";
        case "h":
          return "<h4>" + esc(b.v) + "</h4>";
        case "p":
          return "<p>" + esc(b.v) + "</p>";
        case "quote":
          return '<blockquote class="essay__quote">' + esc(b.v) + "</blockquote>";
        case "close":
          return '<p class="essay__close"><strong>小结 · </strong>' + esc(b.v) + "</p>";
        default:
          return b.v ? "<p>" + esc(b.v) + "</p>" : "";
      }
    }).join("") + "</div>";
  }

  function renderBrief(items) {
    var hs = items.filter(function (it) { return (it.essay && it.essay.length) || it.problem || it.insight; });
    if (!hs.length) {
      return '<div class="empty">当日暂无精读条目——运行 <code>scripts/fetch_arxiv.py</code> 后由本地精读回填。</div>';
    }
    var bySect = {};
    var order = [];
    hs.forEach(function (h) {
      var s = h.section || "其他交叉方向";
      if (!bySect[s]) { bySect[s] = []; order.push(s); }
      bySect[s].push(h);
    });
    var html = "";
    order.forEach(function (s) {
      var list = sorted(bySect[s]);
      html += '<div class="sect">' + hexSvg() + "<h2>" + esc(s) + "</h2>" +
        '<span class="sect__line"></span><span class="sect__count">' + list.length + " 篇</span></div>";
      html += list.map(function (h, i) { return cardHTML(h, i); }).join("");
    });
    return html;
  }

  /* ------------------------------ 渲染：雷达 ------------------------------ */

  function renderRadar(items) {
    var list = sorted(items);
    if (!list.length) return '<div class="empty">没有符合条件的条目。</div>';
    var rows = list.map(function (r) {
      return '<div class="radar__row" data-klass="' + klassOf(r) + '">' +
        '<div class="radar__dot"></div>' +
        '<div class="radar__body">' +
          '<a class="radar__title" href="' + esc(r.abs_url) + '" target="_blank" rel="noopener">' +
            esc(r.title) + "</a>" +
          '<p class="radar__abs">' + esc(r.summary_short || "") + "</p>" +
          '<div class="radar__meta">' +
            "<span>" + esc(r.primary_category || "") + "</span>" +
            "<span>" + esc(r.published || "") + "</span>" +
            "<span>" + esc(authorLine(r.authors, 3)) + "</span>" +
            (r.curated
              ? '<span class="tag" style="border-color:var(--accent);color:var(--accent)">精读</span>'
              : "") +
            (r.is_new ? '<span class="tag tag--new">NEW</span>' : "") +
            (r.tags || []).map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("") +
          "</div>" +
        "</div>" +
        '<div class="radar__when">' + esc(r.published || "") + "</div>" +
        "</div>";
    }).join("");
    return '<div class="radar">' + rows + "</div>";
  }

  /* ------------------------------ 渲染：趋势 ------------------------------ */

  function renderTrends() {
    var ts = state.day.trends || [];
    if (!ts.length) return '<div class="empty">当日暂无趋势小结。</div>';
    return '<ul class="trends">' + ts.map(function (t, i) {
      return "<li><span class=\"trends__n\">" + (i + 1) + "</span><span>" + esc(t) + "</span></li>";
    }).join("") + "</ul>";
  }

  /* ------------------------------ 主渲染 ------------------------------ */

  function render() {
    if (!state.day) return;
    var box = $("#view");
    if (state.view === "trends") {
      box.innerHTML = renderTrends();
      return;
    }
    var pool = state.view === "radar" ? allItems() : (state.day.highlights || []);
    var items = filter(pool);
    box.innerHTML = state.view === "radar" ? renderRadar(items) : renderBrief(items);
    if (!items.length && state.view === "brief") {
      box.innerHTML = '<div class="empty">没有符合条件的精读条目，试试放宽筛选或切换到「全站雷达」。</div>';
    }
    bindCards();
  }

  function bindCards() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-toggle]"), function (btn) {
      btn.addEventListener("click", function () {
        var card = btn.closest(".card");
        var open = card.classList.toggle("is-open");
        btn.textContent = open ? "收起解读" : "展开解读";
      });
    });
  }

  /* ------------------------------ 事件绑定 ------------------------------ */

  function bind() {
    var q = $("#q"), timer = null;
    q.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(function () { state.q = q.value.trim(); render(); }, 160);
    });

    Array.prototype.forEach.call(document.querySelectorAll("#view-seg button"), function (b) {
      b.addEventListener("click", function () {
        state.view = b.getAttribute("data-view");
        Array.prototype.forEach.call(document.querySelectorAll("#view-seg button"), function (x) {
          x.setAttribute("aria-pressed", String(x === b));
        });
        render();
      });
    });

    $("#sort").addEventListener("change", function (e) { state.sort = e.target.value; render(); });

    $("#only-new").addEventListener("click", function () {
      state.onlyNew = !state.onlyNew;
      this.setAttribute("aria-pressed", String(state.onlyNew));
      this.textContent = state.onlyNew ? "仅看新增 ✓" : "含往期收录";
      render();
    });

    $("#expand-all").addEventListener("click", function () {
      state.openAll = !state.openAll;
      this.textContent = state.openAll ? "收起全部" : "展开全部";
      render();
    });
  }

  /* ------------------------------ 对寻访模块暴露接口 ------------------------------ */

  window.AG = {
    /** 当前可用于寻访的条目（精读 + 雷达，按 id 去重） */
    items: function () {
      if (!state.day) return [];
      var seen = {};
      return allItems().filter(function (it) {
        var k = it.id || it.title;
        if (!k || seen[k]) return false;
        seen[k] = 1;
        return true;
      });
    },
    klassChip: klassChip,
    klassOf: klassOf,
    /** 在雷达视图中定位某条目标题 */
    find: function (title) {
      if (!title) return;
      state.view = "radar";
      state.q = title;
      state.onlyNew = false;
      state.tags = [];
      var q = $("#q"); if (q) q.value = title;
      var onb = $("#only-new");
      if (onb) { onb.setAttribute("aria-pressed", "false"); onb.textContent = "含往期收录"; }
      Array.prototype.forEach.call(document.querySelectorAll("#view-seg button"), function (x) {
        x.setAttribute("aria-pressed", String(x.getAttribute("data-view") === "radar"));
      });
      renderTagbar();
      render();
      if (typeof window.scrollTo === "function") window.scrollTo({ top: 0, behavior: "smooth" });
    },
    date: function () { return state.date; },
    /** 跳到某条目的解读并展开 */
    focus: function (id) {
      if (!id) return;
      state.view = "brief";
      state.q = "";
      state.tags = [];
      var q = $("#q"); if (q) q.value = "";
      Array.prototype.forEach.call(document.querySelectorAll("#view-seg button"), function (x) {
        x.setAttribute("aria-pressed", String(x.getAttribute("data-view") === "brief"));
      });
      render();
      var el = document.getElementById("op-" + id);
      if (!el) return;
      el.classList.add("is-open");
      var btn = el.querySelector("[data-toggle]");
      if (btn) btn.textContent = "收起解读";
      if (typeof el.scrollIntoView === "function") {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  };

  /* ------------------------------ 启动 ------------------------------ */

  initTheme();
  bind();
  load();
})();
