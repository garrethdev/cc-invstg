"""Collect public Hacker News comment histories.

  python3 collect_hn.py build N      # eval set: users who self-posted LinkedIn in "Who wants to be hired"
  python3 collect_hn.py user NAME    # one flagged target (real use)
"""
import html
import json
import re
import sys
import time
from pathlib import Path

import requests

API = "https://hn.algolia.com/api/v1"
DATA = Path(__file__).parent / "data"
HIRING = re.compile(r"who (wants to be|is) hired|who is hiring|freelancer\? seeking", re.I)
LINKEDIN = re.compile(r"linkedin\.com/in/([A-Za-z0-9\-_%]+)", re.I)
MIN_COMMENTS = 40


def get(path, **params):
    for attempt in range(3):
        r = requests.get(f"{API}/{path}", params=params, timeout=30)
        if r.ok:
            return r.json()
        time.sleep(2 * (attempt + 1))
    r.raise_for_status()


def clean(text):
    text = re.sub(r"<p>", "\n", text or "")
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def user_comments(user, limit=300):
    out, page = [], 0
    while len(out) < limit:
        res = get("search_by_date", tags=f"comment,author_{user}", hitsPerPage=100, page=page)
        for h in res["hits"]:
            if HIRING.search(h.get("story_title") or ""):
                continue
            text = clean(h.get("comment_text"))
            if len(text) > 40:
                out.append({"date": h["created_at"][:10], "thread": h.get("story_title"), "text": text})
        page += 1
        if page >= res["nbPages"]:
            break
    return out[:limit]


def hiring_threads(n_months):
    res = get("search_by_date", tags="story,author_whoishiring", query="who wants to be hired", hitsPerPage=50)
    return [h["objectID"] for h in res["hits"] if "wants to be hired" in h["title"].lower()][:n_months]


def build(target_n):
    DATA.mkdir(exist_ok=True)
    seen, truth = set(), []
    for tid in hiring_threads(12):
        for c in get(f"items/{tid}")["children"]:
            user, m = c.get("author"), LINKEDIN.search(html.unescape(c.get("text") or ""))
            if not user or not m or user in seen:
                continue
            seen.add(user)
            slug = m.group(1).strip("-_/").lower()
            if not re.search(r"[a-z]{3,}-[a-z]{3,}", slug):  # skip slugs that aren't name-like
                continue
            comments = user_comments(user)
            if len(comments) < MIN_COMMENTS:
                continue
            truth.append({"user": user, "linkedin_slug": slug})
            (DATA / f"{user}.json").write_text(json.dumps(comments, indent=1))
            print(f"[{len(truth)}/{target_n}] {user}: {len(comments)} comments")
            if len(truth) >= target_n:
                (DATA / "truth.json").write_text(json.dumps(truth, indent=1))
                return
            time.sleep(0.5)
    (DATA / "truth.json").write_text(json.dumps(truth, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build(int(sys.argv[2]))
    elif cmd == "user":
        DATA.mkdir(exist_ok=True)
        comments = user_comments(sys.argv[2])
        (DATA / f"{sys.argv[2]}.json").write_text(json.dumps(comments, indent=1))
        print(f"{len(comments)} comments")
