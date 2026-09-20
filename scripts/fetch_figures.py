#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取论文主图与图注。

从 arXiv 的 HTML 渲染版（https://arxiv.org/html/<id>）里挑出「主图」——
优先 Fig.1 / Figure 1（通常是整体框架图或总览图），其次取第一条有实质长度图注的图；
跳过 "(a)"、"(b)" 这类子图切片。图片下载到 assets/figures/。

用法：
    python3 scripts/fetch_figures.py                 # 处理 data/daily/ 里所有含 id 的条目
    python3 scripts/fetch_figures.py 2609.15361 ...  # 指定 arXiv 编号
    python3 scripts/fetch_figures.py --dry-run

输出：assets/figures/manifest.json
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "daily")
FIG_DIR = os.path.join(ROOT, "assets", "figures")
MANIFEST = os.path.join(FIG_DIR, "manifest.json")
UA = "all-game-radar/1.0 (figure fetcher)"

TAG_STRIP = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def log(m: str) -> None:
    print(f"[fig] {m}", file=sys.stderr)


def get(url: str, timeout: int = 60) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as exc:  # noqa: BLE001
        log(f"  下载失败 {url}: {exc}")
        return None


def clean(t: str) -> str:
    return WS.sub(" ", TAG_STRIP.sub("", t)).strip()


def parse_figures(html: str) -> list[dict]:
    out = []
    for block in re.findall(r"<figure[^>]*>(.*?)</figure>", html, re.S):
        img = re.search(r'<img[^>]+src="([^"]+)"', block)
        if not img:
            continue
        src = img.group(1)
        # 只接受位图，跳过 SVG 图标 / data URI
        if src.startswith("data:") or src.lower().endswith(".svg"):
            continue
        cap_m = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", block, re.S)
        cap = clean(cap_m.group(1)) if cap_m else ""
        out.append({"src": src, "caption": cap})
    return out


def pick_main(figs: list[dict]) -> dict | None:
    """挑主图：Fig.1 > Figure 1 > 第一条有实质图注的 > 第一条。"""
    if not figs:
        return None
    for f in figs:
        c = f["caption"]
        if re.match(r"^\s*(fig(?:ure)?\.?\s*1)\b", c, re.I):
            return f
    for f in figs:
        if len(f["caption"]) >= 55 and not re.match(r"^\s*\(?[a-d]\)", f["caption"]):
            return f
    return figs[0]


def abs_url(arxiv_id: str, src: str) -> str:
    if src.startswith("http"):
        return src
    # src 形如 2609.15361v1/resources/x.jpg，相对 https://arxiv.org/html/
    return "https://arxiv.org/html/" + src.lstrip("/")


def ext_of(url: str) -> str:
    m = re.search(r"\.(png|jpe?g|gif|webp)(\?|$)", url, re.I)
    return ("." + m.group(1).lower().replace("jpeg", "jpg")) if m else ".png"


def fetch_one(arxiv_id: str, dry: bool = False) -> dict | None:
    html_raw = get(f"https://arxiv.org/html/{arxiv_id}")
    if not html_raw:
        return None
    html = html_raw.decode("utf-8", "ignore")
    figs = parse_figures(html)
    if not figs:
        log(f"  {arxiv_id}: 无可用 figure")
        return None
    main = pick_main(figs)
    url = abs_url(arxiv_id, main["src"])
    local = f"figures/{arxiv_id}{ext_of(url)}"

    if not dry:
        data = get(url)
        if not data:
            return None
        os.makedirs(FIG_DIR, exist_ok=True)
        with open(os.path.join(FIG_DIR, f"{arxiv_id}{ext_of(url)}"), "wb") as f:
            f.write(data)
        log(f"  {arxiv_id}: 保存 {local}（{len(data) // 1024} KB）")

    return {
        "id": arxiv_id,
        "local": local,
        "source_url": url,
        "caption": main["caption"],
        "figure_count": len(figs),
    }


def collect_ids() -> list[str]:
    ids = []
    for fn in sorted(os.listdir(DATA_DIR), reverse=True):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(DATA_DIR, fn), encoding="utf-8") as f:
            data = json.load(f)
        for h in data.get("highlights", []):
            if h.get("id") and h["id"] not in ids:
                ids.append(h["id"])
    return ids


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    ids = args or collect_ids()
    log(f"待处理 {len(ids)} 篇")

    man = {}
    if os.path.exists(MANIFEST):
        try:
            with open(MANIFEST, encoding="utf-8") as f:
                man = json.load(f)
        except (json.JSONDecodeError, OSError):
            man = {}

    for i, aid in enumerate(ids, 1):
        log(f"[{i}/{len(ids)}] {aid}")
        got = fetch_one(aid, dry)
        if got:
            man[aid] = got
        time.sleep(2)

    if not dry:
        os.makedirs(FIG_DIR, exist_ok=True)
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(man, f, ensure_ascii=False, indent=2)
            f.write("\n")
        log(f"写入 {MANIFEST}（{len(man)} 条）")
    else:
        print(json.dumps(man, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
