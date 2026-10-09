"""Redact eval inputs and check search profiles for identity leaks.

  python3 leakcheck.py prep              # data/<user>.json -> data/<id>.posts.txt (redacted, eval only)
  python3 leakcheck.py check <id> FILE   # fail if a search profile leaks handle/name/URL
"""
import hashlib
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).parent / "data"
URL = re.compile(r"https?://\S+|www\.\S+|\b\S+\.(com|io|org|net|dev|me|ai|co)(/\S*)?\b", re.I)
EMAIL = re.compile(r"\S+@\S+\.\S+")
MAX_CHARS = 60000


def eval_id(user):
    return hashlib.sha256(user.encode()).hexdigest()[:10]


def name_tokens(slug):
    return [t for t in re.split(r"[-_]", slug) if t.isalpha() and len(t) >= 3]


def forbidden(entry):
    toks = name_tokens(entry["linkedin_slug"])
    return [entry["user"].lower(), entry["linkedin_slug"]] + [t for t in toks if len(t) >= 4][-1:]


def prep():
    truth = json.loads((DATA / "truth.json").read_text())
    for e in truth:
        comments = json.loads((DATA / f"{e['user']}.json").read_text())
        toks = name_tokens(e["linkedin_slug"])
        full = re.compile(r"\b" + r"\s+".join(map(re.escape, toks[:2])) + r"\b", re.I) if len(toks) >= 2 else None
        user = re.compile(re.escape(e["user"]), re.I)
        lines, total = [], 0
        for c in comments:
            t = URL.sub("[url]", EMAIL.sub("[email]", c["text"]))
            t = user.sub("[user]", t)
            if full:
                t = full.sub("[name]", t)
            line = f"[{c['date']}] ({c['thread']}) {t}"
            if total + len(line) > MAX_CHARS:
                break
            lines.append(line)
            total += len(line)
        (DATA / f"{eval_id(e['user'])}.posts.txt").write_text("\n\n".join(lines))
        print(eval_id(e["user"]), len(lines), "comments")


def check(eid, path):
    truth = {eval_id(e["user"]): e for e in json.loads((DATA / "truth.json").read_text())}
    text = Path(path).read_text().lower()
    leaks = [w for w in forbidden(truth[eid]) if re.search(r"\b" + re.escape(w) + r"\b", text)]
    leaks += [m.group(0) for m in URL.finditer(text)] + [m.group(0) for m in EMAIL.finditer(text)]
    print("LEAK: " + ", ".join(leaks) if leaks else "clean")
    return not leaks


if __name__ == "__main__":
    if sys.argv[1] == "prep":
        prep()
    else:
        sys.exit(0 if check(sys.argv[2], sys.argv[3]) else 1)
