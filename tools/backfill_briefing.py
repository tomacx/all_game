# -*- coding: utf-8 -*-
"""
把人工精读长文回填进当日 JSON（可复用版）。

内容写在  tools/briefs/<日期>.json，结构与示例：
    {
      "items": [{"id": "<radar 中的 id 或 doi>", "title": "中文标题",
                 "title_en": "英文原题", "section": "分区", "klass": "职业",
                 "tags": [...], "glance": "一句话亮点", "essay": [{"t": "...", "v": "..."}]}],
      "trends": ["..."],
      "note": "..."
    }

本脚本负责：按 id 从当日 radar 取元数据 → 与人工字段合并 → 追加进 highlights
（已有精读不会被覆盖）→ 更新 trends/note/curated → 同步 digests 的趋势小结。

运行：
    python3 tools/backfill_briefing.py 2026-09-21
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "daily")
BRIEF_DIR = os.path.join(ROOT, "tools", "briefs")
DIGEST_DIR = os.path.join(ROOT, "digests")

ARXIV_ID = re.compile(r"^\d{4}\.\d{4,5}$")


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def find_in_radar(radar, key):
    key = str(key)
    for it in radar:
        if str(it.get("id", "")) == key or str(it.get("doi", "")) == key:
            return it
    low = key.lower()
    for it in radar:
        if str(it.get("doi", "")).lower() == low or str(it.get("id", "")).lower() == low:
            return it
    return None


def build(brief_item, radar_item, idx):
    """雷达元数据打底，人工字段覆盖。"""
    r = radar_item or {}
    out = {
        "idx": idx,
        "id": r.get("id") or brief_item.get("id", ""),
        "doi": r.get("doi", ""),
        "title": brief_item["title"],
        "title_en": brief_item.get("title_en") or r.get("title", ""),
        "authors": r.get("authors", []),
        "published": r.get("published", ""),
        "venue": r.get("venue", ""),
        "venue_raw": r.get("venue_raw", ""),
        "impact": r.get("impact", ""),
        "impact_label": r.get("impact_label", ""),
        "primary_category": r.get("primary_category", ""),
        "url": r.get("url", ""),
        "summary": r.get("summary", ""),
        "summary_short": r.get("summary_short", ""),
        "is_new": r.get("is_new", True),
        "sources": r.get("sources", []),
    }
    aid = out["id"]
    if ARXIV_ID.match(str(aid)):
        out["abs_url"] = f"https://arxiv.org/abs/{aid}"
    else:
        out["abs_url"] = r.get("url", "")

    for k in ("title", "title_en", "section", "klass", "tags", "glance", "essay"):
        if k in brief_item:
            out[k] = brief_item[k]
    out["curated"] = True
    return out


def sync_digest(date, trends, n_highlights):
    path = os.path.join(DIGEST_DIR, f"{date}.md")
    if not os.path.isfile(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    text = re.sub(r"- 精读条目：\d+", f"- 精读条目：{n_highlights}", text, count=1)

    block = "## 本期趋势小结\n\n" + "\n".join(f"{i}. {t}" for i, t in enumerate(trends, 1)) + "\n"
    if "## 本期趋势小结" in text:
        text = re.sub(r"## 本期趋势小结.*", block.rstrip("\n"), text, flags=re.S)
    else:
        text = text.rstrip("\n") + "\n\n" + block
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return True


def main():
    if len(sys.argv) < 2:
        print("用法: python3 tools/backfill_briefing.py <YYYY-MM-DD>")
        return 1
    date = sys.argv[1]

    brief_path = os.path.join(BRIEF_DIR, f"{date}.json")
    day_path = os.path.join(DATA_DIR, f"{date}.json")
    if not os.path.isfile(brief_path):
        print(f"缺少精读内容文件：{brief_path}")
        return 1
    if not os.path.isfile(day_path):
        print(f"缺少当日数据：{day_path}")
        return 1

    brief = load(brief_path)
    day = load(day_path)
    radar = day.get("radar", [])
    highlights = day.get("highlights", []) or []

    known = {str(h.get("id", "")).lower() for h in highlights}
    known |= {str(h.get("doi", "")).lower() for h in highlights if h.get("doi")}
    known |= {h.get("title", "") for h in highlights}

    added, missing = [], []
    idx = len(highlights)
    for b in brief.get("items", []):
        key = b.get("id", "")
        if str(key).lower() in known or b.get("title") in known:
            continue
        r = find_in_radar(radar, key)
        if r is None:
            missing.append(key)
            continue
        idx += 1
        known.add(str(key).lower())
        known.add(b.get("title", ""))
        added.append(build(b, r, idx))

    if not added:
        print("没有新增精读条目（可能已全部回填过）。")
        if missing:
            print("未能在 radar 中匹配到：", missing)
        return 0

    day["highlights"] = highlights + added
    if brief.get("trends"):
        day["trends"] = brief["trends"]
    if brief.get("note"):
        day["note"] = brief["note"]
    day["curated"] = True

    save(day_path, day)
    load(day_path)  # 校验可解析

    ok = sync_digest(date, day.get("trends", []), len(day["highlights"]))
    print(f"新增精读 {len(added)} 篇 -> {day_path}（累计 {len(day['highlights'])} 篇）")
    for h in added:
        print(f"  [{h['idx']}] {h['title']} · {h.get('venue', '')} ({h.get('impact_label', '')})")
    if ok:
        print(f"已同步 {os.path.join('digests', date + '.md')} 的趋势小结")
    if missing:
        print("未能在 radar 中匹配到：", missing)
    return 0


if __name__ == "__main__":
    sys.exit(main())
