# -*- coding: utf-8 -*-
"""本机 git push 走 github.com:443 不通，用 Git Data API 推单个提交。

用法：
    python3 tools/push_via_api.py "<commit message>" <rel_path> [<rel_path> ...]

凭据取 `gh auth token`，所以运行前需 gh 已登录。
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "tomacx/all_game"
API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def gh_token():
    return subprocess.check_output(["gh", "auth", "token"], text=True).strip()


def api(method, path, payload=None, token=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "all-game-backfill",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:800])
        raise


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    message, paths = sys.argv[1], sys.argv[2:]
    token = gh_token()

    ref = api("GET", f"/repos/{REPO}/git/ref/heads/master", token=token)
    base = ref["object"]["sha"]
    commit = api("GET", f"/repos/{REPO}/git/commits/{base}", token=token)
    base_tree = commit["tree"]["sha"]
    print("base commit:", base[:8], "tree:", base_tree[:8])

    tree = []
    for rel in paths:
        full = os.path.join(ROOT, rel)
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
        blob = api("POST", f"/repos/{REPO}/git/blobs",
                   {"content": content, "encoding": "utf-8"}, token)
        tree.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"  blob {rel} -> {blob['sha'][:8]}")

    new_tree = api("POST", f"/repos/{REPO}/git/trees",
                   {"base_tree": base_tree, "tree": tree}, token)
    print("new tree:", new_tree["sha"][:8])

    new_commit = api("POST", f"/repos/{REPO}/git/commits",
                     {"message": message, "tree": new_tree["sha"], "parents": [base]}, token)
    print("new commit:", new_commit["sha"][:8])

    api("PATCH", f"/repos/{REPO}/git/refs/heads/master",
        {"sha": new_commit["sha"]}, token)
    print("refs/heads/master ->", new_commit["sha"][:8])
    return 0


if __name__ == "__main__":
    sys.exit(main())
