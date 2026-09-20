# 博弈智能 · 每日动向 | Game Intelligence Radar

> 追踪**博弈智能**领域每天的新动向与新方法：多智能体强化学习（MARL）、博弈理论与均衡求解、
> LLM 多智能体博弈、机制设计与拍卖、对抗安全与鲁棒性。

🌐 站点：<https://tomacx.github.io/all_game/>

界面以**明日方舟**风格手工还原（六边形源石徽章、斜切角面板、HUD 状态条、★ 稀有度分级）。
默认**罗德岛日间模式（浅色）**，右上角按钮可切到夜间模式（暗色），选择会记在本地。

---

## 站点结构

| 路径 | 说明 |
|---|---|
| `index.html` | 单页站点入口 |
| `assets/css/ak.css` | 明日方舟风格样式（浅色 / 暗色双主题，CSS 变量驱动） |
| `assets/js/app.js` | 读取 JSON 并渲染：搜索、标签筛选、分区归类、稀有度分级、视图切换 |
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
   再用关键词词典打分、自动打标签、归入分区。★ 分级由分数映射而来，**仅用于快速筛选，不是学术评价**。
2. **新增判定**：抓取时会读取 `data/daily/` 下往期所有已收录 ID 做比对，给每篇打上 `is_new`。
   页面上带 `NEW` 徽章的就是**往期没出现过的新论文**；控制条上的「仅看新增」默认开启，
   所以「全站雷达」默认只显示今天的新动向，关掉即可连往期一起看。
   检索窗口刻意开到 7 天，是为了对冲 arXiv 索引滞后（新提交的论文通常晚 1–3 天才进索引）。
2. **人工精读**：从 `digests/<日期>.md` 挑出值得细读的论文，写入当日 JSON 的 `highlights`，
   每条包含「核心问题 / 方法与建模 / 实验与战绩 / 启示·可迁移点」四段。
3. 已精读的条目会在「全站雷达」里标上 `精读` 徽章，且不会重复出现两次。

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
  "tags": ["博弈理论", "均衡选择"],
  "tier": 6,                                 // 3~6，对应蓝/紫/金/橙红
  "glance": "一句话看点",
  "problem": "它到底解决了什么问题…",
  "method": ["建模 / 方法要点 1", "要点 2"],
  "result": "实验设置与关键数字…",
  "insight": "对我的启示、可迁移的做法…"
}
```

写进 `trends` 数组的是本期趋势小结（字符串数组）。`note` 字段会显示在页面顶部说明栏。
脚本重跑时这三个字段会被保留，不会被 radar 覆盖。

## 说明

- 排名与 ★ 分级来自关键词加权打分，只服务于「快速定位」，不构成对论文质量的判断。
- 明日方舟风格 UI 为本项目手工绘制（SVG / CSS），未使用任何官方素材文件。
