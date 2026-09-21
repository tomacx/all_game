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
| `data/index.json` | 归档日索引（脚本自动维护） |
| `data/daily/<日期>.json` | 当日数据：`highlights`（人工精读）+ `radar`（自动收录）+ `trends`（趋势小结） |
| `data/learning/curriculum.json` | 「理论学习 · 主线剧情」课程（6 幕 / 24 章） |
| `data/runs.json` | 最近 40 次抓取运行记录（成功/失败、各来源命中数） |
| `digests/<日期>.md` | 当日清单 Markdown，供本地精读使用 |
| `logs/<日期>.log` | 当日运行日志（Actions 里同时上传为 artifact，保留 30 天） |
| `scripts/fetch_daily.py` | **主抓取脚本**：arXiv + OpenAlex + Crossref 三路来源（纯标准库） |
| `scripts/fetch_arxiv.py` | 仅 arXiv 的抓取实现，被 `fetch_daily.py` 复用 |
| `scripts/resolve_ids.py` | 按标题反查 arXiv 编号，用于精读条目补链接 |
| `tools/seed_briefing.py` | 精读回填（把人工解读写入当日 JSON） |
| `tools/build_curriculum.py` | 生成理论学习课程 JSON |
| `.github/workflows/daily-update.yml` | 每日 3 个时段冗余触发 + 幂等 + 重试 + 日志 + 失败告警 |

## 数据是怎么来的

### 三路来源

| 来源 | 覆盖 | 检索规则 |
|---|---|---|
| **arXiv** | 预印本，时效最快 | 六路检索式：`cs.MA`、`cs.GT`、`MARL`、`Nash equilibrium`、`机制设计`、`LLM × multi-agent`；按提交时间窗过滤（默认 7 天，用于对冲 arXiv 索引 1–3 天的滞后） |
| **OpenAlex** | CCF-A 顶会顶刊 | ① 按 6 个主题词做 `title_and_abstract.search`；② 对领域顶刊按 **ISSN 精确检索**：`Games and Economic Behavior`、`Journal of Economic Theory`、`Econometrica`、`Operations Research`、`Mathematics of Operations Research`、`Management Science`、`Theoretical Economics`、`JMLR`、`TPAMI`、`Artificial Intelligence`（默认回溯 90 天，顶刊出版慢） |
| **Crossref** | Nature / Science 及其子刊 | 按 **ISSN 逐个精确检索**：Nature、Science、Nature Machine Intelligence、Nature Communications、Nature Human Behaviour、Nature Computational Science、Science Advances、PNAS、Nature Reviews Physics；另有 6 路期刊主题检索兜底 |

### 去重逻辑

三级去重，命中任意一级即视为同一工作：

1. **DOI**（小写归一化）
2. **arXiv ID / 记录 ID**
3. **规范化标题**（小写、只保留字母数字，截断 120 字符）

同一工作同时存在预印本与正式发表版本时，**保留影响力更高的一份**，另一份降级记入 `alt` 字段（不重复展示）。

### 影响力标注与排序

每条都会标注 `venue`（来源名）、`impact`（档位）、`impact_label`、`provider`（数据接口）：

| 档位 | 含义 | 权重 |
|---|---|---|
| `top` 顶刊 | Nature / Science 及其子刊、PNAS | 105–130 |
| `ccf_a` CCF-A | 顶会（NeurIPS / ICML / ICLR / AAAI / IJCAI / AAMAS / EC / WINE …）与领域顶刊 | 72–100 |
| `journal` 期刊 | 其他同行评审期刊 | 55 |
| `preprint` 预印本 | arXiv / Zenodo 等 | 30 |

venue 判定采用 **精确匹配优先 + 特征子串兜底**（先规范化：小写、去标点、去年份、去 `Proceedings of the …` 前缀）。
这样 `Management Science` 不会被误判成 `Science`，而 `Proceedings of the 42nd ICML` 仍能正确归到 ICML。

排序公式：`rank = 影响力权重 + 相关度得分 + 时效加成`，时效加成对 3 天内的新条目额外加权，
保证「今日新动向」排在旧的顶刊之前。页面上可按影响力排序、按档位筛选（顶刊 / CCF-A / 期刊 / 预印本）。

> 档次只说明**发表载体**，不构成对论文本身的评价。

### 其它

1. **新增判定**：抓取时读取 `data/daily/` 下往期所有已收录的 ID / DOI / 标题做比对，给每篇打上 `is_new`。
   页面上带 `NEW` 徽章的就是**往期没出现过的新条目**；控制条上的「仅看新增」默认开启，关掉即可连往期一起看。
2. **人工精读**：从 `digests/<日期>.md` 挑出值得细读的论文，写成博客式长文写入 `highlights`：引入段 → 若干分节 → 小结。
3. 已精读的条目会在「全站雷达」里标上 `精读` 徽章，且不会重复出现两次。

### 干员寻访

首页顶部有「干员寻访 · 单次 / 十连」。点击后进入寻访界面：源石六边形脉动 → 抽取 → 展示结果卡片。

- 抽的是当日档案里的条目（精读 + 雷达），**已抽到的不会重复**，记录在 localStorage，换天自动重置。
- 抽到精读条目 →「查看完整解读」直接跳到该条并展开图文长文。
- 抽到雷达条目 →「在雷达中定位」切到雷达视图并搜索该标题。
- 「重置寻访记录」可以清空已抽记录再来一轮。

### 理论学习 · 主线剧情

控制条上新增「理论学习」视图，以**关卡 / 章节**形式组织经典博弈论知识点：

- 6 幕 24 章：序章（均衡的起点）→ 静态博弈 → 动态与重复 → 不完全信息 → 演化与学习 → 前沿
- 每章含：引入段、分节正文、摘录、小结，以及一道**思考题**
- 解锁规则：序章默认解锁 3 章，之后**每过一天自动解锁 1 章**；同时**每完成 1 章会额外提前解锁 1 章**
- 顶部面板显示已完成 / 已解锁数量、双段进度条（解锁进度 + 完成进度）与「今日关卡」快捷入口
- 完成状态记在 localStorage（`all_game_learned`），可反复标记 / 取消

课程数据由 `tools/build_curriculum.py` 生成：

```bash
python3 tools/build_curriculum.py      # -> data/learning/curriculum.json
```

## 每日自动更新

工作流：`.github/workflows/daily-update.yml`

| 机制 | 做法 |
|---|---|
| **触发** | 一天 **3 个时段冗余触发**：UTC 01:00 / 05:00 / 09:00（北京 09:00 / 13:00 / 17:00）。GitHub 的 cron 偶尔会延迟或漏跑，多留两个补跑窗口 |
| **幂等** | 先判断当日文件是否已存在且非空：已存在 → 直接跳过；当日 0 条 → 判定为需要补跑；手动触发可勾选 `force` 强制重跑 |
| **重试** | 抓取最多 3 次，指数退避（20s / 40s / 60s）；单次网络请求内部还有 3 次带退避的重试 |
| **日志** | 每次运行写 `logs/<日期>.log`，并更新 `data/runs.json`（最近 40 次）；同时上传为 Actions artifact，保留 30 天；关键输出写入 `$GITHUB_STEP_SUMMARY` |
| **失败告警** | 连续失败会开一个带 `daily-failure` 标签的 issue（同名未关闭 issue 不会重复创建），避免静默失败 |
| **并发** | `concurrency.group: daily-fetch`，`cancel-in-progress: false`，同一时间只有一个任务排队、不中断进行中的 |
| **推送** | 提交后 push 也带 3 次重试，避免瞬时网络抖动导致丢失 |

也可以手动触发：**Actions → 每日抓取 · 博弈智能新动向 → Run workflow**（可指定 `force` / arXiv 回溯天数 / 期刊回溯天数 / 入库条数）。

> 注意：GitHub 对「60 天无任何活动」的仓库会自动停用定时任务。本仓库每天都有自动提交，不会出现这种情况。

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
python3 scripts/fetch_daily.py                      # 抓取今天（arXiv 7 天 + 期刊会议 90 天）
python3 scripts/fetch_daily.py --force              # 当日已有数据也强制重跑
python3 scripts/fetch_daily.py --dry-run            # 只看统计，不写文件
python3 scripts/fetch_daily.py --date 2026-09-21    # 指定归档日期
python3 scripts/fetch_arxiv.py --days 3 --top 40    # 只用 arXiv 的旧脚本
```

`fetch_daily.py` 可选参数：`--date`、`--arxiv-days`（arXiv 回溯天数）、`--venue-days`（期刊会议回溯天数）、
`--per-query`（arXiv 每路检索式条数）、`--per-term`（OpenAlex / Crossref 每主题词条数）、
`--top`（最多入库条数）、`--force`、`--dry-run`。

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
    { "t": "quote", "v": "值得摘出来的一句话" },
    { "t": "close", "v": "小结：可迁移的做法、要注意的坑" }
  ]
}
```

`essay` 按顺序渲染为博客正文：`lead` 作引入段，`h` 是分节标题，`p` 是正文段落，
`quote` 是摘录，`close` 是小结。块类型可以自由增删，顺序即呈现顺序。

写进 `trends` 数组的是本期趋势小结（字符串数组）。`note` 字段会显示在页面顶部说明栏。
脚本重跑时这三个字段会被保留，不会被 radar 覆盖。

## 说明

- 站内没有任何星级、稀有度或分数展示；关键词打分只用于内部决定哪些条目进雷达。
- 「影响力档位」只标识**发表载体**（顶刊 / CCF-A / 期刊 / 预印本），不代表对论文质量的评价。
- 明日方舟风格 UI 为本项目手工绘制（SVG / CSS），未使用任何官方素材文件。
