#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
博弈智能 · 每日动向「多来源」抓取脚本
========================================

来源覆盖（不只是 arXiv）：
  1. arXiv        —— 预印本，时效最快（cs.MA / cs.GT / MARL / Nash / 机制设计 / LLM×多智能体）
  2. OpenAlex     —— CCF-A 顶会顶刊（NeurIPS / ICML / ICLR / AAAI / IJCAI / AAMAS / EC / WINE …）
                    与领域顶刊（GEB / JET / Econometrica / Operations Research …）
  3. Crossref     —— Nature / Science 及其子刊（按 ISSN 精确检索）+ 其他期刊

检索 → 分类 → 去重 → 影响力排序：
  · 检索：每个来源按主题词检索，arXiv 用短窗口（时效），期刊会议用长窗口（出版慢）
  · 分类：命中的 venue 名与「影响力规则表」比对，得到 impact（顶刊 / CCF-A / 期刊 / 预印本）
  · 去重：DOI → arXiv ID → 规范化标题，三级；同一工作同时有预印本与正式版时保留正式版
  · 排序：rank = 影响力权重 + 相关度 + 时效加成

输出：
    data/daily/<YYYY-MM-DD>.json   当日数据（供网站读取）
    digests/<YYYY-MM-DD>.md        当日清单（供本地精读 / 人工回填）
    logs/<YYYY-MM-DD>.log          本次运行日志
    data/runs.json                 最近 N 次运行记录（便于在仓库里直接查）

设计要点：
  1. 纯标准库，无第三方依赖，GitHub Actions 上可直接跑。
  2. 单来源失败不影响整体：某个来源挂掉只记 warning，其余照常入库。
  3. 幂等：当日文件已存在且非空时默认跳过（--force 可强制重跑）。
  4. 人工字段（highlights / trends / note / learning）永远保留，不会被自动任务冲掉。

用法：
    python3 scripts/fetch_daily.py                     # 抓取今天
    python3 scripts/fetch_daily.py --date 2026-09-21
    python3 scripts/fetch_daily.py --force             # 强制重跑当日
    python3 scripts/fetch_daily.py --dry-run           # 只打印，不写文件
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_arxiv import (  # noqa: E402  —— 复用既有 arXiv 逻辑
    ARXIV_API,
    KEYWORDS,
    SECTION_RULES,
    UA,
    clean_ws,
    http_get,
    load_existing,
    log,
    section_of,
    summarize,
    update_index,
    write_json,
)

# --------------------------------------------------------------------------- #
# 路径
# --------------------------------------------------------------------------- #

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "daily")
DIGEST_DIR = os.path.join(ROOT, "digests")
LOG_DIR = os.path.join(ROOT, "logs")
RUNS_PATH = os.path.join(ROOT, "data", "runs.json")
INDEX_PATH = os.path.join(ROOT, "data", "index.json")

CONTACT = "all-game-radar/1.0 (mailto:maintainer@example.com)"

# --------------------------------------------------------------------------- #
# 主题检索式（三路来源共用，arXiv 走其专用语法）
# --------------------------------------------------------------------------- #

TOPIC_TERMS = [
    ("multi-agent reinforcement learning", "主题·MARL"),
    ("Nash equilibrium", "主题·纳什均衡"),
    ("mechanism design", "主题·机制设计"),
    ("game theory", "主题·博弈理论"),
    ("auction theory", "主题·拍卖"),
    ("multi-agent system large language model", "主题·LLM多智能体"),
]

# Nature / Science 及其子刊（按 ISSN 精确检索）
NATURE_SCIENCE_ISSN = {
    "0028-0836": "Nature",
    "0036-8075": "Science",
    "2522-5839": "Nature Machine Intelligence",
    "2041-1723": "Nature Communications",
    "2375-2548": "Science Advances",
    "2397-3374": "Nature Human Behaviour",
    "2662-8457": "Nature Computational Science",
    "0027-8424": "PNAS",
    "2058-8437": "Nature Reviews Physics",
    "1548-8403": "AAMAS",  # Adaptive Agents and Multi-Agent Systems（会议论文集 ISSN）
}

# 领域顶刊（按 ISSN-L 在 OpenAlex 精确检索）
TOP_JOURNAL_ISSN_L = {
    "0899-8256": "Games and Economic Behavior",
    "0022-0531": "Journal of Economic Theory",
    "0012-9682": "Econometrica",
    "0030-364X": "Operations Research",
    "0364-765X": "Mathematics of Operations Research",
    "0025-1909": "Management Science",
    "1555-7561": "Theoretical Economics",
    "1532-4435": "JMLR",
    "0162-8828": "IEEE TPAMI",
    "0004-3702": "Artificial Intelligence",
}

# Crossref 主题词：必须是「短」词串，长短语串会让 Crossref 的相关性检索返回 0
CR_TOPIC_QUERY = "multi-agent OR \"game theory\" OR auction OR equilibrium OR strategic OR bargaining"

# --------------------------------------------------------------------------- #
# 影响力判定
#   1) 精确匹配（规范化后的 venue 名）—— 解决 "Management Science" 被误判成 "Science" 这类问题
#   2) 特征子串兜底（按模式长度降序，长的优先）—— 解决 "Proceedings of the 42nd ICML" 这类前缀
#   档位：top（Nature/Science 系顶刊）> ccf_a > journal > preprint
# --------------------------------------------------------------------------- #

def norm_venue(name: str) -> str:
    v = (name or "").lower()
    v = re.sub(r"[^a-z0-9]+", " ", v)
    v = re.sub(r"\b(19|20)\d{2}\b", " ", v)
    v = re.sub(r"\b(proceedings of the|proceedings|ieee|acm|cvf|acm sigsac|springer|elsevier|wiley|annual)\b", " ", v)
    return re.sub(r"\s+", " ", v).strip()


# 规范化名 -> (规范名, 类别, 档位, 权重)
EXACT_VENUES: dict[str, tuple[str, str, str, int]] = {
    # Nature / Science 系
    "nature": ("Nature", "顶刊", "top", 130),
    "science": ("Science", "顶刊", "top", 130),
    "nature machine intelligence": ("Nature Machine Intelligence", "顶刊", "top", 120),
    "nature communications": ("Nature Communications", "顶刊", "top", 115),
    "science advances": ("Science Advances", "顶刊", "top", 115),
    "science robotics": ("Science Robotics", "顶刊", "top", 115),
    "nature human behaviour": ("Nature Human Behaviour", "顶刊", "top", 115),
    "nature human behavior": ("Nature Human Behaviour", "顶刊", "top", 115),
    "nature computational science": ("Nature Computational Science", "顶刊", "top", 115),
    "nature methods": ("Nature Methods", "顶刊", "top", 112),
    "nature physics": ("Nature Physics", "顶刊", "top", 112),
    "nature reviews physics": ("Nature Reviews Physics", "顶刊", "top", 112),
    "nature biotechnology": ("Nature Biotechnology", "顶刊", "top", 112),
    "pnas": ("PNAS", "顶刊", "top", 105),
    "proceedings of the national academy of sciences": ("PNAS", "顶刊", "top", 105),
    "national academy of sciences": ("PNAS", "顶刊", "top", 105),
    # 经济 / 博弈顶刊
    "econometrica": ("Econometrica", "CCF-A", "ccf_a", 100),
    "games and economic behavior": ("Games and Economic Behavior", "CCF-A", "ccf_a", 95),
    "journal of economic theory": ("Journal of Economic Theory", "CCF-A", "ccf_a", 95),
    "american economic review": ("American Economic Review", "CCF-A", "ccf_a", 95),
    "quarterly journal of economics": ("Quarterly Journal of Economics", "CCF-A", "ccf_a", 95),
    "theoretical economics": ("Theoretical Economics", "CCF-A", "ccf_a", 92),
    "journal of political economy": ("Journal of Political Economy", "CCF-A", "ccf_a", 92),
    "review of economic studies": ("Review of Economic Studies", "CCF-A", "ccf_a", 92),
    "mathematics of operations research": ("Mathematics of Operations Research", "CCF-A", "ccf_a", 92),
    "operations research": ("Operations Research", "CCF-A", "ccf_a", 92),
    "management science": ("Management Science", "CCF-A", "ccf_a", 88),
    "rand journal of economics": ("RAND Journal of Economics", "CCF-A", "ccf_a", 88),
    "journal of the european economic association": ("JEEA", "期刊", "journal", 80),
    "experimental economics": ("Experimental Economics", "期刊", "journal", 72),
    "international journal of game theory": ("Int. J. Game Theory", "期刊", "journal", 75),
    "dynamic games and applications": ("Dynamic Games and Applications", "期刊", "journal", 65),
    "acm transactions on economics and computation": ("ACM TEAC", "期刊", "journal", 78),
    # AI / ML 期刊
    "artificial intelligence": ("Artificial Intelligence", "CCF-A", "ccf_a", 78),
    "journal of artificial intelligence research": ("JAIR", "期刊", "journal", 68),
    "journal of machine learning research": ("JMLR", "CCF-A", "ccf_a", 80),
    "machine learning": ("Machine Learning", "期刊", "journal", 65),
    "transactions on machine learning research": ("TMLR", "期刊", "journal", 65),
    "ieee transactions on pattern analysis and machine intelligence": ("IEEE TPAMI", "CCF-A", "ccf_a", 80),
    "acm computing surveys": ("ACM CSUR", "CCF-A", "ccf_a", 75),
    "ieee transactions on automatic control": ("IEEE TAC", "期刊", "journal", 68),
    "automatica": ("Automatica", "期刊", "journal", 68),
    "autonomous agents and multi agent systems": ("JAAMAS", "期刊", "journal", 68),
    "journal of autonomous agents and multi agent systems": ("JAAMAS", "期刊", "journal", 68),
}

# 特征子串 -> (规范名, 类别, 档位, 权重)；运行时按模式长度降序匹配
PATTERN_VENUES: list[tuple[str, str, str, str, int]] = [
    ("economics and computation", "ACM EC", "CCF-A", "ccf_a", 90),
    ("web and internet economics", "WINE", "CCF-A", "ccf_a", 88),
    ("autonomous agents and multiagent systems", "AAMAS", "CCF-A", "ccf_a", 88),
    ("autonomous agents and multi agent systems", "AAMAS", "CCF-A", "ccf_a", 88),
    ("neural information processing systems", "NeurIPS", "CCF-A", "ccf_a", 85),
    ("international conference on machine learning", "ICML", "CCF-A", "ccf_a", 85),
    ("international conference on learning representations", "ICLR", "CCF-A", "ccf_a", 85),
    ("conference on learning representations", "ICLR", "CCF-A", "ccf_a", 85),
    ("artificial intelligence and statistics", "AISTATS", "CCF-A", "ccf_a", 80),
    ("uncertainty in artificial intelligence", "UAI", "CCF-A", "ccf_a", 80),
    ("conference on learning theory", "COLT", "CCF-A", "ccf_a", 80),
    ("knowledge discovery and data mining", "KDD", "CCF-A", "ccf_a", 78),
    ("empirical methods in natural language processing", "EMNLP", "CCF-A", "ccf_a", 78),
    ("computational linguistics", "ACL", "CCF-A", "ccf_a", 78),
    ("conference on computer vision and pattern recognition", "CVPR", "CCF-A", "ccf_a", 75),
    ("international conference on computer vision", "ICCV", "CCF-A", "ccf_a", 75),
    ("european conference on computer vision", "ECCV", "CCF-A", "ccf_a", 75),
    ("computer and communications security", "CCS", "CCF-A", "ccf_a", 75),
    ("symposium on security and privacy", "IEEE S&P", "CCF-A", "ccf_a", 75),
    ("operating systems principles", "SOSP", "CCF-A", "ccf_a", 78),
    ("symposium on theory of computing", "STOC", "CCF-A", "ccf_a", 85),
    ("foundations of computer science", "FOCS", "CCF-A", "ccf_a", 85),
    ("symposium on discrete algorithms", "SODA", "CCF-A", "ccf_a", 80),
    ("web conference", "The Web Conference", "CCF-A", "ccf_a", 78),
    ("very large data bases", "VLDB", "CCF-A", "ccf_a", 75),
    ("international conference on data engineering", "ICDE", "CCF-A", "ccf_a", 72),
    ("journal of machine learning research", "JMLR", "CCF-A", "ccf_a", 80),
    ("pattern analysis and machine intelligence", "IEEE TPAMI", "CCF-A", "ccf_a", 80),
    ("neurips", "NeurIPS", "CCF-A", "ccf_a", 85),
    ("icml", "ICML", "CCF-A", "ccf_a", 85),
    ("iclr", "ICLR", "CCF-A", "ccf_a", 85),
    ("aaai", "AAAI", "CCF-A", "ccf_a", 82),
    ("ijcai", "IJCAI", "CCF-A", "ccf_a", 82),
    ("aistats", "AISTATS", "CCF-A", "ccf_a", 80),
    ("emnlp", "EMNLP", "CCF-A", "ccf_a", 78),
    ("naacl", "NAACL", "CCF-A", "ccf_a", 75),
    ("sigir", "SIGIR", "CCF-A", "ccf_a", 78),
    ("sigmod", "SIGMOD", "CCF-A", "ccf_a", 75),
    ("vldb", "VLDB", "CCF-A", "ccf_a", 75),
    ("sigcomm", "SIGCOMM", "CCF-A", "ccf_a", 75),
    ("infocom", "INFOCOM", "CCF-A", "ccf_a", 72),
    ("usenix security", "USENIX Security", "CCF-A", "ccf_a", 75),
    ("stoc", "STOC", "CCF-A", "ccf_a", 85),
    ("focs", "FOCS", "CCF-A", "ccf_a", 85),
    ("soda", "SODA", "CCF-A", "ccf_a", 80),
    ("jmlr", "JMLR", "CCF-A", "ccf_a", 80),
    ("aamas", "AAMAS", "CCF-A", "ccf_a", 88),
    ("wine", "WINE", "CCF-A", "ccf_a", 88),
]

_PATTERNS_SORTED = sorted(PATTERN_VENUES, key=lambda r: len(r[0]), reverse=True)

IMPACT_META = {
    "top": {"label": "顶刊", "weight": 1.0},
    "ccf_a": {"label": "CCF-A", "weight": 1.0},
    "journal": {"label": "期刊", "weight": 1.0},
    "preprint": {"label": "预印本", "weight": 1.0},
    "other": {"label": "其他", "weight": 1.0},
}

IMPACT_ORDER = {"top": 0, "ccf_a": 1, "journal": 2, "preprint": 3, "other": 4}


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #

RUN_LOG: list[str] = []


def rlog(msg: str) -> None:
    """同时写 stderr 与内存日志（最后落盘 logs/<date>.log）。"""
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    RUN_LOG.append(line)
    print(f"[daily] {msg}", file=sys.stderr)


def norm_title(title: str) -> str:
    """标题规范化：小写 + 仅保留字母数字，用于跨来源去重。"""
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())[:120]


def classify_venue(venue: str) -> tuple[str, str, str, int]:
    """返回 (规范名, 类别, 影响力档位, 权重)。精确匹配优先，特征子串兜底。"""
    if not (venue or "").strip():
        return ("arXiv", "预印本", "preprint", 30)
    nv = norm_venue(venue)
    if not nv:
        return ("arXiv", "预印本", "preprint", 30)
    if nv in EXACT_VENUES:
        return EXACT_VENUES[nv]
    for pattern, canonical, kind, tier, weight in _PATTERNS_SORTED:
        if pattern in nv:
            return (canonical, kind, tier, weight)
    if "arxiv" in nv or "zenodo" in nv or "researchgate" in nv or "preprint" in nv:
        return ("预印本", "预印本", "preprint", 30)
    if any(k in nv for k in ("journal", "transactions", "review", "letters", "magazine")):
        return (venue[:80], "期刊", "journal", 55)
    return (venue[:80], "会议/其他", "other", 45)


def relevance(title: str, abstract: str) -> tuple[int, list[str]]:
    """关键词打分（与 arXiv 版一致），返回 (分数, 标签)。"""
    blob = f"{title}\n{abstract}".lower()
    score = 0
    tags: dict[str, int] = {}
    for kw, (weight, tag) in KEYWORDS.items():
        if kw in blob:
            score += weight
            tags[tag] = tags.get(tag, 0) + weight
    title_bonus = sum(w for kw, (w, _t) in KEYWORDS.items() if kw in title.lower())
    score += title_bonus
    ordered = sorted(tags.items(), key=lambda kv: kv[1], reverse=True)
    return score, [t for t, _ in ordered][:4]


def abstract_from_inverted_index(inv: dict | None) -> str:
    """OpenAlex 的摘要是倒排索引 {词: [位置...]}，还原成原文。"""
    if not inv:
        return ""
    slots: dict[int, str] = {}
    for word, positions in inv.items():
        for p in positions:
            slots[p] = word
    if not slots:
        return ""
    return clean_ws(" ".join(slots[i] for i in sorted(slots)))


def age_days(date_str: str, today: datetime) -> int:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return 999
    return max(0, (today - d).days)


# --------------------------------------------------------------------------- #
# 来源 1：arXiv（复用既有模块）
# --------------------------------------------------------------------------- #

def fetch_arxiv_items(days: int, per_query: int) -> tuple[list[dict], int]:
    from fetch_arxiv import QUERIES, collect, fetch_query, parse_entry

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    seen: dict[str, dict] = {}
    total_raw = 0
    for query, label in QUERIES:
        try:
            entries = fetch_query(query, per_query)
        except Exception as exc:  # noqa: BLE001
            rlog(f"arXiv 检索式 [{label}] 失败：{exc}（跳过）")
            continue
        total_raw += len(entries)
        kept = 0
        for e in entries:
            item = parse_entry(e, label)
            if item is None or item["published_dt"] < cutoff:
                continue
            if item["id"] in seen:
                if label not in seen[item["id"]]["sources"]:
                    seen[item["id"]]["sources"].append(label)
            else:
                seen[item["id"]] = item
            kept += 1
        rlog(f"arXiv [{label}] 返回 {len(entries)}，窗口内保留 {kept}")
        time.sleep(3)  # arXiv 官方建议 ≥3s

    out = []
    for it in seen.values():
        out.append({
            "key": "arxiv:" + it["id"],
            "raw_id": it["id"],
            "doi": "",
            "title": it["title"],
            "abstract": it["summary"],
            "authors": it["authors"],
            "published": it["published"],
            "venue": "arXiv",
            "venue_raw": "arXiv",
            "provider": "arXiv",
            "url": it["abs_url"],
            "primary_category": it["primary_category"],
            "sources": it["sources"],
        })
    return out, total_raw


# --------------------------------------------------------------------------- #
# 来源 2：OpenAlex（顶会顶刊）
# --------------------------------------------------------------------------- #

def fetch_openalex(days: int, per_term: int) -> tuple[list[dict], int]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    out: list[dict] = []
    total = 0
    for term, label in TOPIC_TERMS:
        params = urllib.parse.urlencode({
            "filter": f"title_and_abstract.search:{term},from_publication_date:{since},type:article",
            "sort": "publication_date:desc",
            "per-page": str(min(per_term, 200)),
            "mailto": "all_game@example.com",
        })
        url = f"https://api.openalex.org/works?{params}"
        try:
            raw = http_get(url, retries=3, timeout=60)
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            rlog(f"OpenAlex [{label}] 失败：{exc}（跳过）")
            continue
        results = data.get("results", [])
        total += len(results)
        kept = 0
        for w in results:
            item = oa_work_to_item(w, label)
            if item:
                out.append(item)
                kept += 1
        rlog(f"OpenAlex [{label}] 返回 {len(results)}，纳入 {kept}")
        time.sleep(0.5)
    return out, total


def oa_work_to_item(w: dict, label: str) -> dict | None:
    """OpenAlex work -> 统一条目结构。"""
    title = clean_ws(w.get("title") or w.get("display_name") or "")
    if not title:
        return None
    abstract = abstract_from_inverted_index(w.get("abstract_inverted_index"))
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    venue = clean_ws(src.get("display_name") or "")
    doi = clean_ws(w.get("doi") or "").replace("https://doi.org/", "")
    authors = [
        clean_ws((a.get("author") or {}).get("display_name") or "")
        for a in (w.get("authorships") or [])
    ]
    authors = [a for a in authors if a][:12]
    return {
        "key": ("doi:" + doi.lower()) if doi else ("title:" + norm_title(title)),
        "raw_id": doi,
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "published": w.get("publication_date") or "",
        "venue": venue,
        "venue_raw": venue,
        "provider": "OpenAlex",
        "url": (loc.get("landing_page_url") or w.get("doi") or w.get("id") or ""),
        "primary_category": "",
        "sources": [label],
    }


def fetch_openalex_journals(days: int, per_page: int = 50) -> tuple[list[dict], int]:
    """按 ISSN-L 精确检索领域顶刊（GEB / JET / Econometrica / OR / MOR / MS / TE / JMLR / TPAMI / AI）。

    顶刊出版节奏慢，且通用主题检索容易被「最新但水」的期刊刷屏，因此单独走 ISSN-L 精确检索。
    """
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    out: list[dict] = []
    total = 0
    for issn, name in sorted(TOP_JOURNAL_ISSN_L.items()):
        params = urllib.parse.urlencode({
            "filter": f"primary_location.source.issn:{issn},from_publication_date:{since}",
            "sort": "publication_date:desc",
            "per-page": str(per_page),
            "mailto": "all_game@example.com",
        })
        try:
            raw = http_get(f"https://api.openalex.org/works?{params}", retries=3, timeout=60)
            results = json.loads(raw.decode("utf-8")).get("results", [])
        except Exception as exc:  # noqa: BLE001
            rlog(f"OpenAlex [顶刊 {name}] 失败：{exc}（跳过）")
            continue
        kept = 0
        for w in results:
            item = oa_work_to_item(w, f"ISSN-L·{name}")
            if item:
                out.append(item)
                kept += 1
        total += len(results)
        rlog(f"OpenAlex [顶刊 {name}] 返回 {len(results)}，纳入 {kept}")
        time.sleep(0.4)
    return out, total


# --------------------------------------------------------------------------- #
# 来源 3：Crossref（Nature / Science 系按 ISSN + 期刊主题检索）
# --------------------------------------------------------------------------- #

def fetch_crossref(days: int, per_term: int) -> tuple[list[dict], int]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    def parse_items(items, label):
        out = []
        for it in items:
            title_list = it.get("title") or []
            title = clean_ws(title_list[0] if title_list else "")
            if not title:
                continue
            venue_list = it.get("container-title") or []
            venue = clean_ws(venue_list[0] if venue_list else "")
            doi = clean_ws(it.get("DOI") or "")
            parts = ((it.get("issued") or {}).get("date-parts") or [[None]])[0]
            pub = "-".join(f"{p:02d}" for p in parts if isinstance(p, int)) if parts and parts[0] else ""
            authors = []
            for a in (it.get("author") or [])[:12]:
                name = clean_ws(f"{a.get('given', '')} {a.get('family', '')}".strip())
                if name:
                    authors.append(name)
            abstract = clean_ws(re.sub(r"<[^>]+>", " ", it.get("abstract") or ""))
            issn_hit = [i for i in (it.get("ISSN") or []) if i in NATURE_SCIENCE_ISSN]
            if issn_hit:
                venue = venue or NATURE_SCIENCE_ISSN.get(issn_hit[0], venue)
            out.append({
                "key": ("doi:" + doi.lower()) if doi else ("title:" + norm_title(title)),
                "raw_id": doi,
                "doi": doi,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": pub,
                "venue": venue,
                "venue_raw": venue,
                "provider": "Crossref",
                "url": it.get("URL") or (f"https://doi.org/{doi}" if doi else ""),
                "primary_category": "",
                "sources": [label],
            })
        return out

    out: list[dict] = []
    total = 0

    # (a) Nature / Science 系：逐个 ISSN 精确检索（Crossref 不支持多 ISSN 逗号 OR，会 400）
    topic_or = CR_TOPIC_QUERY
    for issn, name in sorted(NATURE_SCIENCE_ISSN.items()):
        params = urllib.parse.urlencode({
            "filter": f"from-pub-date:{since},issn:{issn},type:journal-article",
            "query.bibliographic": topic_or,
            "rows": str(min(per_term, 100)),
            "mailto": "all_game@example.com",
        })
        try:
            raw = http_get(f"https://api.crossref.org/works?{params}", retries=3, timeout=60)
            items = (json.loads(raw.decode("utf-8")).get("message") or {}).get("items") or []
            got = parse_items(items, f"ISSN·{name}")
            out += got
            total += len(items)
        except Exception as exc:  # noqa: BLE001
            rlog(f"Crossref [ISSN {name}] 失败：{exc}（跳过）")
        time.sleep(0.4)

    # (b) 期刊主题检索
    for term, label in TOPIC_TERMS:
        params = urllib.parse.urlencode({
            "query.bibliographic": term,
            "filter": f"from-pub-date:{since},type:journal-article",
            "rows": str(min(per_term, 200)),
            "mailto": "all_game@example.com",
        })
        try:
            raw = http_get(f"https://api.crossref.org/works?{params}", retries=3, timeout=60)
            items = (json.loads(raw.decode("utf-8")).get("message") or {}).get("items") or []
        except Exception as exc:  # noqa: BLE001
            rlog(f"Crossref [{label}] 失败：{exc}（跳过）")
            continue
        got = parse_items(items, label)
        out += got
        total += len(items)
        rlog(f"Crossref [{label}] 返回 {len(items)}，纳入 {len(got)}")
        time.sleep(0.5)

    return out, total


# --------------------------------------------------------------------------- #
# 合并、去重、打分、排序
# --------------------------------------------------------------------------- #

def merge(items: list[dict], today: datetime) -> list[dict]:
    """三级去重：DOI → arXiv ID → 规范化标题；同题保留影响力更高的一份。"""
    by_doi: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    merged: list[dict] = []

    def tier_rank(it: dict) -> tuple:
        _c, _k, tier, weight = classify_venue(it.get("venue", ""))
        return (IMPACT_ORDER.get(tier, 9), -weight)

    for it in items:
        it["_impact"] = classify_venue(it.get("venue", ""))
        # 同一工作：先按 DOI，再按标题
        key = it.get("key") or ""
        dup = None
        if key.startswith("doi:") and key in by_doi:
            dup = by_doi[key]
        elif norm_title(it["title"]) in by_title:
            dup = by_title[norm_title(it["title"])]
        if dup is None:
            merged.append(it)
            if key.startswith("doi:"):
                by_doi[key] = it
            by_title[norm_title(it["title"])] = it
        else:
            # 保留影响力更高者，另一份降级为 alt（记录但不重复展示）
            if tier_rank(it) < tier_rank(dup):
                keep, drop = it, dup
                if keep.get("key", "").startswith("doi:"):
                    by_doi[keep["key"]] = keep
                by_title[norm_title(keep["title"])] = keep
            else:
                keep, drop = dup, it
            alt_desc = f"{drop['provider']}:{drop.get('venue_raw') or drop.get('raw_id')}"
            keep.setdefault("alt", [])
            if alt_desc not in keep["alt"]:
                keep["alt"].append(alt_desc)

    for it in merged:
        canonical, kind, tier, weight = it["_impact"]
        score, tags = relevance(it.get("title", ""), it.get("abstract", "") or it.get("title", ""))
        age = age_days(it.get("published", ""), today)
        recency = max(0, 60 - age)
        if age <= 3:
            recency += 20  # 48 小时内的新东西额外加权，保证「今日新动向」靠前
        it.update({
            "venue": canonical or it.get("venue_raw") or "—",
            "kind": kind,
            "impact": tier,
            "impact_label": IMPACT_META.get(tier, {}).get("label", tier),
            "impact_weight": weight,
            "score": score,
            "tags": tags,
            "section": section_of(tags),
            "rank": weight + score + recency,
            "summary_short": summarize(it.get("abstract") or "", 300),
            "age_days": age,
        })
    merged.sort(key=lambda x: (-x["rank"], x.get("published", "")))
    return merged


# 顶刊专用的宽松词：顶刊里真正的博弈智能研究往往标题不含多词短语，
# 只靠 KEYWORDS 会漏掉，因此顶刊档位额外接受这些单词级信号。
TOP_TOKENS = (
    "auction", "equilibrium", "strategic", "bargaining", "multi-agent", "multiagent",
    "mechanism design", "incentive", "bidding", "negotiat", "voting", "coalition",
    "prisoner", "payoff", "nash", "stackelberg", "game-theoretic", "game theory",
)

# 明显不是研究论文的条目（更正、撤稿、社论、新闻）
NOISE_TITLE = (
    "author correction", "correction:", "erratum", "retraction", "editorial",
    "publisher correction", "expression of concern", "comment on", "reply to",
    "book review", "meeting report", "news & views", "obituary",
)


def keep_filter(it: dict, min_score_other: int = 30) -> bool:
    """非预印本、非顶会顶刊的来源要求「强相关」才入库，避免被水文刷屏。"""
    tier = it.get("impact")
    score = it.get("score", 0)
    title = (it.get("title") or "").lower()
    if any(n in title for n in NOISE_TITLE):
        return False
    if tier == "top":
        # 顶刊：多词命中或单词级信号任一即可（顶刊本身已是强过滤）
        return score >= 6 or any(tok in title for tok in TOP_TOKENS)
    if tier == "ccf_a":
        return score >= 6
    if tier in ("journal", "other"):
        return score >= min_score_other
    return True  # arXiv 预印本已在检索式层面过滤


# --------------------------------------------------------------------------- #
# 读写
# --------------------------------------------------------------------------- #

def load_seen(exclude_date: str) -> tuple[set[str], set[str]]:
    """往期已收录的 id / doi / 标题，用于判定「今日新增」。"""
    ids: set[str] = set()
    titles: set[str] = set()
    if not os.path.isdir(DATA_DIR):
        return ids, titles
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith(".json") or fn[:-5] == exclude_date:
            continue
        data = load_existing(os.path.join(DATA_DIR, fn))
        for group in ("highlights", "radar"):
            for it in data.get(group, []):
                if it.get("id"):
                    ids.add(str(it["id"]).lower())
                if it.get("doi"):
                    ids.add("doi:" + str(it["doi"]).lower())
                if it.get("title"):
                    titles.add(norm_title(it["title"]))
    return ids, titles


def render_digest(date: str, payload: dict) -> str:
    src = payload["source"]
    lines = [
        f"# 博弈智能 · 每日动向 · {date}",
        "",
        f"- 检索窗口：arXiv {src['arxiv_days']} 天 / 期刊会议 {src['venue_days']} 天（截至 {date}）",
        f"- 命中总数：{src['total_raw']}，去重后 {src['unique']}，入库 {len(payload['radar'])}",
        f"- **今日新增：{src['new_count']} 篇**（往期已收录 {src['seen_before']} 条用于比对）",
        f"- 来源构成：{json.dumps(src['by_source'], ensure_ascii=False)}",
        f"- 影响力构成：{json.dumps(src['by_impact'], ensure_ascii=False)}",
        f"- 精读条目：{len(payload['highlights'])}",
        "",
        "## 待精读清单（仅列今日新增）",
        "",
    ]
    fresh = [it for it in payload["radar"] if it.get("is_new")] or payload["radar"]
    for i, it in enumerate(fresh, 1):
        lines.append(f"### {i}. {it['title']}")
        lines.append("")
        lines.append(f"- **来源**：{it.get('venue')} · {it.get('impact_label')}（{it.get('provider')}）")
        lines.append(f"- **链接**：{it.get('url')}")
        lines.append(f"- **标签**：{' / '.join(it.get('tags', [])) or '—'} · 分区：{it.get('section')}")
        lines.append(f"- **作者**：{', '.join((it.get('authors') or [])[:6])}")
        lines.append("")
        if it.get("summary_short"):
            lines.append(f"> {it['summary_short']}")
            lines.append("")
    lines += ["## 本期趋势小结", "", "1. ", ""]
    return "\n".join(lines)


def write_run_log(date: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, f"{date}.log")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"===== run @ {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} =====\n")
        f.write("\n".join(RUN_LOG) + "\n")


def update_runs(date: str, ok: bool, stats: dict) -> None:
    data = load_existing(RUNS_PATH)
    runs = data.get("runs", [])
    runs.append({
        "date": date,
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": ok,
        **stats,
    })
    data["runs"] = runs[-40:]
    write_json(RUNS_PATH, data)


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description="多来源抓取博弈智能领域每日新动向")
    ap.add_argument("--date", default=None, help="归档日期，默认今天（UTC）")
    ap.add_argument("--arxiv-days", type=int, default=7, help="arXiv 回溯天数")
    ap.add_argument("--venue-days", type=int, default=60, help="期刊/会议回溯天数")
    ap.add_argument("--per-query", type=int, default=120, help="arXiv 每条检索式拉取条数")
    ap.add_argument("--per-term", type=int, default=100, help="OpenAlex/Crossref 每个主题词拉取条数")
    ap.add_argument("--top", type=int, default=60, help="最多入库条数")
    ap.add_argument("--force", action="store_true", help="当日已有数据也强制重跑")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    args = ap.parse_args()

    today = datetime.now(timezone.utc)
    date = args.date or today.strftime("%Y-%m-%d")
    rlog(f"目标日期 {date} · arXiv {args.arxiv_days} 天 / 期刊会议 {args.venue_days} 天")

    path = os.path.join(DATA_DIR, f"{date}.json")
    if os.path.exists(path) and not args.force and not args.dry_run:
        existing = load_existing(path)
        if len(existing.get("radar", [])) > 0:
            rlog(f"data/daily/{date}.json 已存在 {len(existing['radar'])} 条，跳过（--force 可强制重跑）")
            write_run_log(date)
            return 0

    all_items: list[dict] = []
    counts: dict[str, int] = {}
    total_raw = 0

    ax_items, ax_raw = fetch_arxiv_items(args.arxiv_days, args.per_query)
    all_items += ax_items
    counts["arXiv"] = len(ax_items)
    total_raw += ax_raw

    oa_items, oa_raw = fetch_openalex(args.venue_days, args.per_term)
    ja_items, ja_raw = fetch_openalex_journals(args.venue_days)
    oa_items += ja_items
    all_items += oa_items
    counts["OpenAlex"] = len(oa_items)
    total_raw += oa_raw + ja_raw

    cr_items, cr_raw = fetch_crossref(args.venue_days, args.per_term)
    all_items += cr_items
    counts["Crossref"] = len(cr_items)
    total_raw += cr_raw

    rlog(f"各来源纳入：{json.dumps(counts, ensure_ascii=False)}")

    merged = merge(all_items, today)
    kept = [it for it in merged if keep_filter(it)]
    rlog(f"去重后 {len(merged)} 篇，按相关性过滤后 {len(kept)} 篇")
    kept = kept[: args.top]

    seen_ids, seen_titles = load_seen(date)
    radar = []
    for it in kept:
        key_id = it.get("raw_id") or ""
        is_new = True
        if (it.get("doi") and ("doi:" + it["doi"].lower()) in seen_ids) or \
           (key_id and key_id.lower() in seen_ids) or \
           (norm_title(it["title"]) in seen_titles):
            is_new = False
        radar.append({
            "id": key_id,
            "doi": it.get("doi", ""),
            "is_new": is_new,
            "title": it.get("title", ""),
            "authors": it.get("authors", []),
            "published": it.get("published", ""),
            "venue": it.get("venue", ""),
            "venue_raw": it.get("venue_raw", ""),
            "provider": it.get("provider", ""),
            "kind": it.get("kind", ""),
            "impact": it.get("impact", ""),
            "impact_label": it.get("impact_label", ""),
            "impact_weight": it.get("impact_weight", 0),
            "primary_category": it.get("primary_category", ""),
            "url": it.get("url", ""),
            "summary": it.get("abstract", ""),
            "summary_short": it.get("summary_short", ""),
            "tags": it.get("tags", []),
            "section": it.get("section", ""),
            "score": it.get("score", 0),
            "rank": it.get("rank", 0),
            "sources": it.get("sources", []),
            "alt": it.get("alt", []),
        })

    by_impact: dict[str, int] = {}
    for r in radar:
        by_impact[r["impact_label"]] = by_impact.get(r["impact_label"], 0) + 1

    existing = load_existing(path)
    payload = {
        "date": date,
        "generated_at": today.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "window": f"arXiv {(today - timedelta(days=args.arxiv_days)).strftime('%Y-%m-%d')} ~ {date}"
                      f" ／ 期刊会议 {(today - timedelta(days=args.venue_days)).strftime('%Y-%m-%d')} ~ {date}",
            "arxiv_days": args.arxiv_days,
            "venue_days": args.venue_days,
            "total_raw": total_raw,
            "unique": len(merged),
            "by_source": counts,
            "by_impact": by_impact,
            "new_count": sum(1 for r in radar if r["is_new"]),
            "seen_before": len(seen_ids) + len(seen_titles),
        },
        "highlights": existing.get("highlights", []),
        "trends": existing.get("trends", []),
        "note": existing.get("note", ""),
        "learning": existing.get("learning", {}),
        "radar": radar,
    }

    stats = {
        "total_raw": total_raw,
        "unique": len(merged),
        "kept": len(radar),
        "new_count": payload["source"]["new_count"],
        "by_source": counts,
        "by_impact": by_impact,
    }

    if args.dry_run:
        print(json.dumps(payload["source"], ensure_ascii=False, indent=2))
        for it in radar[:15]:
            print(f"  [{it['impact_label']:>5} rank{it['rank']:>4}] {it['venue'][:26]:28s} {it['title'][:60]}")
        return 0

    write_json(path, payload)
    os.makedirs(DIGEST_DIR, exist_ok=True)
    with open(os.path.join(DIGEST_DIR, f"{date}.md"), "w", encoding="utf-8") as f:
        f.write(render_digest(date, payload))
    update_index(date, payload)
    update_runs(date, True, stats)
    write_run_log(date)

    rlog(f"写入 data/daily/{date}.json（radar {len(radar)} 条，精读 {len(payload['highlights'])} 条）")
    rlog(f"写入 digests/{date}.md、logs/{date}.log、data/runs.json")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        rlog(f"运行失败：{exc}")
        write_run_log(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        raise
