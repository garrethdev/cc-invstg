"""Extract step: posts -> evidence profile + anonymized search profile (via OpenRouter).

  python3 extract.py <id> [<id> ...]      # reads data/<id>.posts.txt, writes data/<id>.profile.json + data/<id>.search.txt
  python3 extract.py all                  # every data/*.posts.txt without a profile yet
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

HERE = Path(__file__).parent
DATA = HERE / "data"
MODEL = os.environ.get("SL_MODEL", "anthropic/claude-sonnet-5.5")


def api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    return subprocess.check_output(["security", "find-generic-password", "-s", "openrouter_api_key", "-w"], text=True).strip()


def chat(system, user, max_tokens=8000):
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key()}", "HTTP-Referer": "https://localhost/source-locator", "X-Title": "source-locator"},
        json={"model": MODEL, "max_tokens": max_tokens, "temperature": 0,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        timeout=600,
    )
    r.raise_for_status()
    body = r.json()
    return body["choices"][0]["message"]["content"], body.get("usage", {})


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def run(eid):
    posts = (DATA / f"{eid}.posts.txt").read_text()
    system = (HERE / "prompts" / "extract.md").read_text()
    out, usage = chat(system, f"POSTING HISTORY (newest first):\n\n{posts}")
    prof = parse_json(out)
    (DATA / f"{eid}.profile.json").write_text(json.dumps(prof, indent=1))
    (DATA / f"{eid}.search.txt").write_text(prof["search_profile"].strip() + "\n")
    print(f"{eid}: {len(prof['facts'])} facts, {len(prof['direct_identifiers'])} direct identifiers, tokens {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}")


if __name__ == "__main__":
    ids = sys.argv[1:]
    if ids == ["all"]:
        ids = [p.name.split(".")[0] for p in DATA.glob("*.posts.txt") if not (DATA / f"{p.name.split('.')[0]}.profile.json").exists()]
    for eid in ids:
        run(eid)
