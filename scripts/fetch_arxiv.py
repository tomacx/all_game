#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
博弈智能 · 每日动向抓取脚本
================================

从 arXiv 官方 API 拉取最近一个索引窗口内与「博弈智能」相关的新论文，
去重、按关键词打分、自动打标签，输出：

    data/daily/<YYYY-MM-DD>.json   当日数据（供网站读取）
    digests/<YYYY-MM-DD>.md        当日清单（供本地精读 / 人工回填）

设计要点：
  1. 纯标准库，无第三方依赖，GitHub Actions 上可直接跑。
  2. 已存在的当日 JSON 会被「保留人工字段」式合并：
     highlights / trends / note 这类人工精读内容不会被覆盖。
  3. 幂等：同一天重复运行只更新 radar 部分与统计信息。

用法：
    python3 scripts/fetch_arxiv.py                 # 抓取今天（默认回溯 5 天）
    python3 scripts/fetch_arxiv.py --days 7        # 回溯 7 天
    python3 scripts/fetch_arxiv.py --date 2026-09-20
    python3 scripts/fetch_arxiv.py --dry-run       # 只打印统计，不写文件
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}
ARXIV_NS = {"arxiv": "http://arxiv.org/schemas/atom"}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "daily")
DIGEST_DIR = os.path.join(ROOT, "digests")
INDEX_PATH = os.path.join(ROOT, "data", "index.json")

# 六路检索式：分类检索 + 主题检索
QUERIES = [
    ("cat:cs.MA", "分类·多智能体"),
    ("cat:cs.GT", "分类·博弈论"),
    ('abs:"multi-agent reinforcement learning"', "主题·MARL"),
    ('abs:"Nash equilibrium"', "主题·纳什均衡"),
    ('abs:"mechanism design"', "主题·机制设计"),
    ('abs:"large language model" AND abs:"multi-agent"', "主题·LLM多智能体"),
]

# 关键词 -> (权重, 标签)。权重用于相关度打分，标签用于站点筛选。
KEYWORDS: dict[str, tuple[int, str]] = {
    # MARL
    "multi-agent reinforcement learning": (10, "MARL"),
    "marl": (8, "MARL"),
    "multiagent": (6, "MARL"),
    "dec-pomdp": (7, "MARL"),
    "decentralized": (5, "MARL"),
    "cooperative": (4, "MARL"),
    "zero-sum": (6, "MARL"),
    "self-play": (6, "自博弈"),
    "mean field": (5, "平均场"),
    # 均衡与博弈理论
    "nash equilibrium": (10, "博弈理论"),
    "nash regret": (9, "博弈理论"),
    "correlated equilibrium": (8, "博弈理论"),
    "coarse correlated equilibrium": (8, "博弈理论"),
    "stackelberg": (8, "博弈理论"),
    "minimax": (6, "博弈理论"),
    "regret": (5, "博弈理论"),
    "no-regret": (7, "博弈理论"),
    "swap regret": (9, "博弈理论"),
    "potential game": (8, "博弈理论"),
    "equilibrium selection": (7, "均衡选择"),
    "imperfect information": (6, "不完美信息"),
    "extensive-form": (7, "不完美信息"),
    "counterfactual regret": (9, "不完美信息"),
    "poker": (5, "不完美信息"),
    "psro": (9, "PSRO"),
    "policy space response": (8, "PSRO"),
    # 机制设计
    "mechanism design": (10, "机制设计"),
    "auction": (8, "拍卖机制"),
    "incentive compatible": (8, "机制设计"),
    "truthful": (6, "机制设计"),
    "social welfare": (5, "机制设计"),
    "contract": (4, "机制设计"),
    "bidding": (6, "拍卖机制"),
    "matching market": (6, "机制设计"),
    # LLM 多智能体
    "large language model": (4, "LLM-Agent"),
    "llm agent": (8, "LLM-Agent"),
    "llm-agent": (8, "LLM-Agent"),
    "language model agent": (7, "LLM-Agent"),
    "agentic": (5, "LLM-Agent"),
    "multi-agent system": (5, "LLM-Agent"),
    "social simulation": (6, "社会模拟"),
    "emergent": (5, "涌现行为"),
    # 安全 / 对抗
    "adversarial": (4, "对抗安全"),
    "prompt injection": (6, "对抗安全"),
    "jailbreak": (4, "对抗安全"),
    "alignment": (4, "AI安全"),
    "safety": (2, "AI安全"),
    "poisoning": (5, "对抗安全"),
    "robustness": (3, "对抗安全"),
    # 应用域
    "autonomous driving": (4, "自动驾驶"),
    "trading": (4, "金融博弈"),
    "spectrum": (4, "资源博弈"),
    "congestion game": (7, "资源博弈"),
    "network game": (5, "资源博弈"),
    "cybersecurity": (5, "安全博弈"),
    "cyber security": (5, "安全博弈"),
    "swarm": (4, "群体智能"),
    "robotics": (2, "机器人"),
}

# 站点显示的分区（用于首页归类）
SECTION_RULES: list[tuple[str, list[str]]] = [
    ("核心算法创新 · MARL", ["MARL", "自博弈", "平均场"]),
    ("博弈求解与理论", ["博弈理论", "均衡选择", "不完美信息", "PSRO"]),
    ("机制设计与市场", ["机制设计", "拍卖机制", "资源博弈"]),
    ("LLM 多智能体与社会模拟", ["LLM-Agent", "社会模拟", "涌现行为"]),
    ("对抗、安全与鲁棒", ["对抗安全", "AI安全", "安全博弈"]),
    ("应用与交叉", ["自动驾驶", "金融博弈", "群体智能", "机器人"]),
]

UA = "all-game-radar/1.0 (Game Intelligence Daily Radar; mailto:maintainer@example.com)"


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #


def log(msg: str) -> None:
    print(f"[fetch] {msg}", file=sys.stderr)


def http_get(url: str, retries: int = 3, timeout: int = 60) -> bytes:
    """带指数退避的 GET。arXiv 偶发 5xx / 限流，重试即可。"""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - 网络层异常种类太多
            last_err = exc
            wait = 3 * (attempt + 1)
            log(f"请求失败（第 {attempt + 1} 次）：{exc}，{wait}s 后重试")
            time.sleep(wait)
    raise RuntimeError(f"arXiv 请求持续失败：{last_err}")


def clean_ws(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def parse_arxiv_dt(raw: str) -> datetime | None:
    """arXiv 返回 '2026-09-17T09:41:22Z'。"""
    if not raw:
        return None
    try:
        dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        try:
            dt = datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None
    return dt.replace(tzinfo=timezone.utc)


def entry_id(entry: ET.Element) -> str:
    raw = clean_ws(entry.findtext("a:id", default="", namespaces=ATOM_NS))
    # http://arxiv.org/abs/2609.01234v1 -> 2609.01234v1
    return raw.rsplit("/abs/", 1)[-1]


def short_id(full_id: str) -> str:
    return re.sub(r"v\d+$", "", full_id)


# --------------------------------------------------------------------------- #
# 抓取
# --------------------------------------------------------------------------- #


def fetch_query(query: str, max_results: int = 120) -> list[ET.Element]:
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(max_results),
        }
    )
    url = f"{ARXIV_API}?{params}"
    raw = http_get(url)
    root = ET.fromstring(raw)
    return root.findall("a:entry", ATOM_NS)


def parse_entry(entry: ET.Element, source_query: str) -> dict | None:
    full_id = entry_id(entry)
    if not full_id:
        return None

    title = clean_ws(entry.findtext("a:title", default="", namespaces=ATOM_NS))
    summary = clean_ws(entry.findtext("a:summary", default="", namespaces=ATOM_NS))
    published = parse_arxiv_dt(entry.findtext("a:published", default="", namespaces=ATOM_NS))
    updated = parse_arxiv_dt(entry.findtext("a:updated", default="", namespaces=ATOM_NS))

    authors = [
        clean_ws(a.findtext("a:name", default="", namespaces=ATOM_NS))
        for a in entry.findall("a:author", ATOM_NS)
    ]
    authors = [a for a in authors if a]

    cats = [c.get("term", "") for c in entry.findall("a:category", ATOM_NS)]
    primary_el = entry.find("arxiv:primary_category", ARXIV_NS)
    primary = primary_el.get("term", "") if primary_el is not None else (cats[0] if cats else "")

    pdf = ""
    for link in entry.findall("a:link", ATOM_NS):
        if link.get("title") == "pdf":
            pdf = link.get("href", "")
    abs_url = f"https://arxiv.org/abs/{full_id}"

    if not published:
        return None

    return {
        "id": short_id(full_id),
        "version_id": full_id,
        "title": title,
        "title_lower": title.lower(),
        "summary": summary,
        "summary_lower": summary.lower(),
        "authors": authors,
        "published": published.strftime("%Y-%m-%d"),
        "published_dt": published,
        "updated": (updated or published).strftime("%Y-%m-%d"),
        "categories": cats,
        "primary_category": primary,
        "abs_url": abs_url,
        "pdf_url": pdf or abs_url.replace("/abs/", "/pdf/"),
        "sources": [source_query],
    }


def collect(days: int, per_query: int) -> tuple[list[dict], int]:
    """拉取并去重，返回 (条目列表, 抓取到的总条数)。"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    seen: dict[str, dict] = {}
    total_raw = 0

    for query, label in QUERIES:
        try:
            entries = fetch_query(query, per_query)
        except Exception as exc:  # noqa: BLE001
            log(f"检索式 [{label}] 失败：{exc}，跳过")
            continue
        total_raw += len(entries)
        kept = 0
        for e in entries:
            item = parse_entry(e, label)
            if item is None:
                continue
            if item["published_dt"] < cutoff:
                continue
            key = item["id"]
            if key in seen:
                if label not in seen[key]["sources"]:
                    seen[key]["sources"].append(label)
            else:
                seen[key] = item
            kept += 1
        log(f"检索式 [{label}]：返回 {len(entries)}，窗口内保留 {kept}")
        time.sleep(3)  # arXiv 官方建议请求间隔 ≥ 3s

    return list(seen.values()), total_raw


# --------------------------------------------------------------------------- #
# 打分与标签
# --------------------------------------------------------------------------- #


def score_and_tag(item: dict) -> dict:
    blob = f"{item['title_lower']} {item['summary_lower']}"
    score = 0
    tags: dict[str, int] = {}

    for kw, (weight, tag) in KEYWORDS.items():
        if kw in blob:
            score += weight
            tags[tag] = tags.get(tag, 0) + weight

    # 分类本身给一点基础分
    cats = " ".join(item["categories"]).lower()
    if "cs.ma" in cats:
        score += 8
    if "cs.gt" in cats:
        score += 8
    if "econ.th" in cats:
        score += 6

    # 标题命中权重更高（标题比摘要更能说明主线）
    title_bonus = sum(w for kw, (w, _t) in KEYWORDS.items() if kw in item["title_lower"])
    score += title_bonus

    ordered = sorted(tags.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "score": score,
        "tags": [t for t, _ in ordered][:4],
    }


def section_of(tags: list[str]) -> str:
    for section, keys in SECTION_RULES:
        if any(t in tags for t in keys):
            return section
    return "其他交叉方向"


def tier_of(score: int) -> int:
    """明日方舟式稀有度：3★ / 4★ / 5★ / 6★，仅用于视觉分级。"""
    if score >= 60:
        return 6
    if score >= 40:
        return 5
    if score >= 24:
        return 4
    return 3


def summarize(text: str, limit: int = 320) -> str:
    text = clean_ws(text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    # 尽量在句末/词末断开
    for sep in ("。 ", ". "):
        idx = cut.rfind(sep)
        if idx > limit * 0.6:
            return cut[: idx + 1].strip()
    return cut.rstrip() + "…"


# --------------------------------------------------------------------------- #
# 读写
# --------------------------------------------------------------------------- #


def load_existing(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        log(f"读取已有 {path} 失败（{exc}），按空数据处理")
        return {}


def load_seen_ids(exclude_date: str) -> set[str]:
    """汇总往期已收录过的 arXiv ID，用于标记「今日新增」。"""
    seen: set[str] = set()
    if not os.path.isdir(DATA_DIR):
        return seen
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith(".json"):
            continue
        if fn[:-5] == exclude_date:
            continue
        data = load_existing(os.path.join(DATA_DIR, fn))
        for h in data.get("highlights", []):
            if h.get("id"):
                seen.add(h["id"])
        for r in data.get("radar", []):
            if r.get("id"):
                seen.add(r["id"])
    return seen


def write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def update_index(date: str, payload: dict) -> None:
    index = load_existing(INDEX_PATH)
    days = index.get("days", [])
    entry = {
        "date": date,
        "radar_count": len(payload.get("radar", [])),
        "highlight_count": len(payload.get("highlights", [])),
        "new_count": payload.get("source", {}).get("new_count", 0),
        "total_hits": payload.get("source", {}).get("total_raw", 0),
    }
    days = [d for d in days if d.get("date") != date]
    days.append(entry)
    days.sort(key=lambda d: d["date"], reverse=True)
    index["days"] = days
    index["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_json(INDEX_PATH, index)


def render_digest(date: str, payload: dict) -> str:
    lines = [
        f"# 博弈智能 · 每日动向 · {date}",
        "",
        f"- 检索窗口：{payload['source']['window']}",
        f"- 命中总数：{payload['source']['total_raw']}，去重后：{payload['source']['unique']}，入库：{len(payload['radar'])}",
        f"- **今日新增：{payload['source'].get('new_count', 0)} 篇**（往期已收录 {payload['source'].get('seen_before', 0)} 篇用于去重比对）",
        f"- 精读条目：{len(payload['highlights'])}",
        "",
        "## 待精读清单（仅列今日新增）",
        "",
    ]
    fresh = [it for it in payload["radar"] if it["is_new"]] or payload["radar"]
    for i, it in enumerate(fresh, 1):
        lines.append(f"### {i}. {it['title']}")
        lines.append("")
        lines.append(f"- **arXiv**：{it['id']} · {it['primary_category']}")
        lines.append(f"- **链接**：{it['abs_url']}")
        lines.append(f"- **标签**：{' / '.join(it['tags']) or '—'}")
        lines.append(f"- **相关度**：{it['score']}（{it['tier']}★）")
        lines.append(f"- **作者**：{', '.join(it['authors'][:6])}{' 等' if len(it['authors']) > 6 else ''}")
        lines.append("")
        lines.append(f"> {it['summary_short']}")
        lines.append("")
    lines += [
        "## 精读模板",
        "",
        "| # | 标题 | 标签 | 一句话看点 |",
        "|---|---|---|---|",
        "",
        "## 本期趋势小结",
        "",
        "1. ",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #


def main() -> int:
    ap = argparse.ArgumentParser(description="抓取博弈智能领域每日 arXiv 新动向")
    ap.add_argument("--date", default=None, help="归档日期，默认今天（UTC）")
    ap.add_argument("--days", type=int, default=5, help="回溯天数，默认 5")
    ap.add_argument("--per-query", type=int, default=120, help="每条检索式最多拉取条数")
    ap.add_argument("--top", type=int, default=40, help="最多入库条数")
    ap.add_argument("--dry-run", action="store_true", help="只打印统计，不写文件")
    args = ap.parse_args()

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log(f"目标日期 {date} · 回溯 {args.days} 天")

    items, total_raw = collect(args.days, args.per_query)
    log(f"去重后 {len(items)} 篇（原始命中 {total_raw}）")

    for it in items:
        st = score_and_tag(it)
        it["score"] = st["score"]
        it["tags"] = st["tags"]
        it["section"] = section_of(st["tags"])
        it["tier"] = tier_of(st["score"])
        it["summary_short"] = summarize(it["summary"])

    items.sort(key=lambda x: (-x["score"], x["published_dt"]), reverse=False)
    items = items[: args.top]

    seen_ids = load_seen_ids(date)
    radar = [
        {
            "id": it["id"],
            "is_new": it["id"] not in seen_ids,
            "title": it["title"],
            "authors": it["authors"],
            "published": it["published"],
            "updated": it["updated"],
            "categories": it["categories"],
            "primary_category": it["primary_category"],
            "abs_url": it["abs_url"],
            "pdf_url": it["pdf_url"],
            "summary": it["summary"],
            "summary_short": it["summary_short"],
            "tags": it["tags"],
            "section": it["section"],
            "score": it["score"],
            "tier": it["tier"],
            "sources": it["sources"],
        }
        for it in items
    ]

    existing = load_existing(os.path.join(DATA_DIR, f"{date}.json"))
    payload = {
        "date": date,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "window": f"{(datetime.now(timezone.utc) - timedelta(days=args.days)).strftime('%Y-%m-%d')} ~ {date}",
            "queries": [q for q, _ in QUERIES],
            "total_raw": total_raw,
            "unique": len(items),
            "days": args.days,
            "new_count": sum(1 for r in radar if r["is_new"]),
            "seen_before": len(seen_ids),
        },
        # 人工精读内容：合并时保留
        "highlights": existing.get("highlights", []),
        "trends": existing.get("trends", []),
        "note": existing.get("note", ""),
        "radar": radar,
    }

    if args.dry_run:
        print(json.dumps(payload["source"], ensure_ascii=False, indent=2))
        for it in radar[:10]:
            print(f"  [{it['tier']}★ {it['score']:>3}] {it['tags']} {it['title'][:80]}")
        return 0

    write_json(os.path.join(DATA_DIR, f"{date}.json"), payload)

    os.makedirs(DIGEST_DIR, exist_ok=True)
    with open(os.path.join(DIGEST_DIR, f"{date}.md"), "w", encoding="utf-8") as f:
        f.write(render_digest(date, payload))

    update_index(date, payload)

    log(f"写入 data/daily/{date}.json（radar {len(radar)} 条，精读 {len(payload['highlights'])} 条）")
    log(f"写入 digests/{date}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
