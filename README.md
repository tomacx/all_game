# 博弈智能 · 每日动向 | Game Intelligence Radar

> 追踪**博弈智能**领域每天的新动向与新方法：多智能体强化学习（MARL）、博弈理论与均衡求解、
> LLM 多智能体博弈、机制设计与拍卖、对抗安全与鲁棒性。

🌐 站点：<https://tomacx.github.io/all_game/>

界面以**明日方舟**风格手工还原（六边形源石徽章、斜切角面板、HUD 状态条、干员职业配色）。
默认**罗德岛日间模式（浅色）**，右上角按钮可切到夜间模式（暗色），选择会记在本地。

**不做内容评级**：站点没有任何星级、稀有度或分数展示。唯一的分色来自「干员职业」
（近卫 / 术师 / 重装 / 辅助 / 特种 / 狙击），它只标识研究方向，不代表等级或质量。

---

## 站点结构

| 路径 | 说明 |
|---|---|
| `index.html` | 单页站点入口 |
| `assets/css/ak.css` | 明日方舟风格样式（浅色 / 暗色双主题，CSS 变量驱动） |
| `assets/js/app.js` | 读取 JSON 并渲染：搜索、标签筛选、分区归类、干员职业、视图切换 |
| `assets/js/recruit.js` | 「干员寻访」：随机抽取当日条目，作为进入解读 / 雷达的入口 |
| `assets/figures/` | 论文主图与 `manifest.json`（由 `scripts/fetch_figures.py` 抓取） |
| `data/index.json` | 归档日索引（脚本自动维护） |
| `data/daily/<日期>.json` | 当日数据：`highlights`（人工精读）+ `radar`（自动收录）+ `trends`（趋势小结） |
| `digests/<日期>.md` | 当日清单 Markdown，供本地精读使用 |
| `scripts/fetch_arxiv.py` | 每日抓取脚本（纯标准库） |
| `scripts/resolve_ids.py` | 按标题反查 arXiv 编号，用于精读条目补链接 |
| `tools/seed_highlights.py` | 精读回填示例（把人工解读写入当日 JSON） |
| `.github/workflows/daily-update.yml` | 每日 UTC 01:00（北京 09:00）自动抓取并提交 |

## 数据是怎么来的

1. **自动雷达**：脚本按六路检索式查询 arXiv API
   （`cs.MA`、`cs.GT`、`multi-agent reinforcement learning`、`Nash equilibrium`、
   `mechanism design`、`LLM × multi-agent`），按提交时间窗过滤、按 arXiv ID 去重，
   再用关键词词典打分、自动打标签、归入分区。这个分数只用于内部决定「哪些进雷达」，
   **页面上不作任何展示**，也没有星级 / 稀有度之类的评级。
2. **新增判定**：抓取时会读取 `data/daily/` 下往期所有已收录 ID 做比对，给每篇打上 `is_new`。
   页面上带 `NEW` 徽章的就是**往期没出现过的新论文**；控制条上的「仅看新增」默认开启，
   所以「全站雷达」默认只显示今天的新动向，关掉即可连往期一起看。
   检索窗口刻意开到 7 天，是为了对冲 arXiv 索引滞后（新提交的论文通常晚 1–3 天才进索引）。
3. **人工精读**：从 `digests/<日期>.md` 挑出值得细读的论文，写成博客式图文长文写入 `highlights`：
   引入段 → 若干分节（配论文主图）→ 小结。
4. 已精读的条目会在「全站雷达」里标上 `精读` 徽章，且不会重复出现两次。

### 干员寻访

首页顶部有「干员寻访 · 单次 / 十连」。点击后进入寻访界面：源石六边形脉动 → 抽取 → 展示结果卡片。

- 抽的是当日档案里的条目（精读 + 雷达），**已抽到的不会重复**，记录在 localStorage，换天自动重置。
- 抽到精读条目 →「查看完整解读」直接跳到该条并展开图文长文。
- 抽到雷达条目 →「在雷达中定位」切到雷达视图并搜索该标题。
- 「重置寻访记录」可以清空已抽记录再来一轮。

### 论文主图

```bash
python3 scripts/fetch_figures.py                 # 抓取所有精读条目的主图
python3 scripts/fetch_figures.py 2609.15361      # 只抓指定编号
```

从 arXiv 的 HTML 渲染版提取主图（优先 `Fig. 1`，跳过 `(a)`、`(b)` 子图切片），
下载到 `assets/figures/` 并记录原文图注到 `manifest.json`。纯理论论文没有位图时会跳过，
对应的解读就只有文字。

### 每日自动更新

GitHub Actions 每天北京时间 09:00 自动跑一次抓取并提交；若当天没有新内容则不产生提交。
也可以在仓库 **Actions → 每日抓取 · 博弈智能新动向 → Run workflow** 手动触发（可指定回溯天数）。

## 本地预览

```bash
cd all_game
python3 -m http.server 8000
# 打开 http://127.0.0.1:8000
```

> 站点通过 `fetch` 读取 `data/*.json`，直接双击打开 `index.html`（`file://`）会被浏览器拦下，
> 必须走本地 HTTP 服务。

## 手动跑一次抓取

```bash
python3 scripts/fetch_arxiv.py --days 3 --per-query 150 --top 40
python3 scripts/fetch_arxiv.py --dry-run --days 7        # 只看统计，不写文件
```

可选参数：`--date`（指定归档日期）、`--days`（回溯天数）、`--per-query`（每路检索式拉取条数）、
`--top`（最多入库条数）、`--dry-run`。

## 回填一篇精读

编辑 `data/daily/<日期>.json`，往 `highlights` 数组里加一条：

```jsonc
{
  "idx": 17,
  "id": "2609.12345",                       // arXiv 编号，可留空
  "title": "中文标题",
  "title_en": "English Title",
  "authors": ["A", "B"],
  "primary_category": "cs.GT",
  "abs_url": "https://arxiv.org/abs/2609.12345",
  "section": "博弈求解与理论",               // 决定首页归到哪个分区
  "klass": "caster",                         // 干员职业：guard/caster/supporter/specialist/defender/sniper
  "tags": ["博弈理论", "均衡选择"],
  "glance": "一句话看点",
  "essay": [
    { "t": "lead",  "v": "引入段落：这篇在解决什么问题、为什么现在值得看" },
    { "t": "h",     "v": "分节标题" },
    { "t": "p",     "v": "叙述段落…" },
    { "t": "fig",   "src": "figures/2609.12345.png", "cap": "中文图注", "cap_en": "原文图注" },
    { "t": "quote", "v": "值得摘出来的一句话" },
    { "t": "close", "v": "小结：可迁移的做法、要注意的坑" }
  ]
}
```

`essay` 按顺序渲染为博客正文：`lead` 作引入段，`h` 是分节标题，`p` 是正文段落，
`fig` 插入论文主图并附中英双行图注，`quote` 是摘录，`close` 是小结。
块类型可以自由增删，图放在哪一段后面，就出现在哪一段后面。

写进 `trends` 数组的是本期趋势小结（字符串数组）。`note` 字段会显示在页面顶部说明栏。
脚本重跑时这三个字段会被保留，不会被 radar 覆盖。

## 说明

- 站内没有任何星级、稀有度或分数展示；关键词打分只用于内部决定哪些条目进雷达。
- 明日方舟风格 UI 为本项目手工绘制（SVG / CSS），未使用任何官方素材文件。
- 论文主图来自 arXiv 的 HTML 渲染版，版权归各论文作者所有，仅作评注性引用。
