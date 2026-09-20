#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按标题批量反查 arXiv 编号与作者，用于给人工精读条目补上可点击链接。

用法：
    python3 scripts/resolve_ids.py titles.txt   # 每行一个标题
    python3 scripts/resolve_ids.py --inline "Title One" "Title Two"

输出 JSON 到 stdout：
    [{"title": "...", "id": "2609.01234", "authors": [...], "primary_category": "cs.MA"}, ...]
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
UA = "all-game-radar/1.0 (title resolver)"


def norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def search(title: str) -> dict | None:
    q = urllib.parse.urlencode({"search_query": f'ti:"{title}"', "max_results": "5"})
    req = urllib.request.Request(f"{ARXIV_API}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    root = ET.fromstring(raw)
    want = norm(title)
    best = None
    for e in root.findall("a:entry", NS):
        t = " ".join((e.findtext("a:title", "", NS) or "").split())
        if norm(t) == want:
            best = e
            break
        if best is None and norm(t)[:40] == want[:40]:
            best = e
    if best is None:
        return None
    aid = " ".join((best.findtext("a:id", "", NS) or "").split()).rsplit("/abs/", 1)[-1]
    import re as _re

    aid = _re.sub(r"v\d+$", "", aid)
    authors = [
        " ".join((a.findtext("a:name", "", NS) or "").split())
        for a in best.findall("a:author", NS)
    ]
    prim = best.find("arxiv:primary_category", NS)
    return {
        "title": title,
        "id": aid,
        "authors": authors,
        "primary_category": prim.get("term", "") if prim is not None else "",
        "abs_url": f"https://arxiv.org/abs/{aid}",
    }


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--inline":
        titles = args[1:]
    elif args:
        with open(args[0], "r", encoding="utf-8") as f:
            titles = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    else:
        print("用法: resolve_ids.py titles.txt | --inline \"标题\" ...", file=sys.stderr)
        return 1

    out = []
    for t in titles:
        try:
            got = search(t)
        except Exception as exc:  # noqa: BLE001
            got = None
            print(f"[warn] {t}: {exc}", file=sys.stderr)
        if got is None:
            print(f"[miss] {t}", file=sys.stderr)
            out.append({"title": t, "id": "", "authors": [], "primary_category": "", "abs_url": ""})
        else:
            out.append(got)
        time.sleep(3)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
