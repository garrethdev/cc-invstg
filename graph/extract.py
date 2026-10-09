"""Extract people, organizations and relationships from a document into the graph.

  python3 extract.py DOC [--import]        # writes review/<doc>.json; --import also loads it into graph.db
  python3 extract.py --load review/X.json  # load a reviewed or hand-edited JSON

Reads .md/.txt, and .pdf when pypdf is installed. Long documents are split into chunks.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

from db import EDGE_TYPES, NODE_TYPES, add_edge, connect, get_or_create_node

HERE = Path(__file__).parent
REVIEW = HERE / "review"
MODEL = os.environ.get("CM_MODEL", "anthropic/claude-sonnet-5.5")
CHUNK = 60000


def api_key():
    return os.environ.get("OPENROUTER_API_KEY") or subprocess.check_output(
        ["security", "find-generic-password", "-s", "openrouter_api_key", "-w"], text=True).strip()


def chat(system, user, max_tokens=16000):
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key()}", "X-Title": "connection-mapper"},
        json={"model": MODEL, "max_tokens": max_tokens, "temperature": 0,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        timeout=900,
    )
    r.raise_for_status()
    body = r.json()
    return body["choices"][0]["message"]["content"], body.get("usage", {})


def parse_json(text):
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < 0:
        raise ValueError("no JSON in model reply:\n" + text[:600])
    return json.loads(text[a:b + 1])


def read_doc(path):
    if path.suffix.lower() == ".pdf":
        import pypdf
        return "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(path)).pages)
    return path.read_text(errors="replace")


def chunks(text):
    if len(text) <= CHUNK:
        return [text]
    out, cur = [], ""
    for para in re.split(r"\n(?=#{1,3} )|\n\n", text):
        if len(cur) + len(para) > CHUNK and cur:
            out.append(cur)
            cur = ""
        cur += para + "\n\n"
    if cur.strip():
        out.append(cur)
    return out


def extract(path):
    system = (HERE / "prompts" / "extract.md").read_text()
    nodes, edges = [], []
    for i, ch in enumerate(chunks(read_doc(path))):
        out, usage = chat(system, f"SOURCE FILE: {path.name}\n\nDOCUMENT:\n\n{ch}")
        j = parse_json(out)
        nodes += j.get("nodes", [])
        edges += j.get("edges", [])
        print(f"chunk {i + 1}: {len(j.get('nodes', []))} nodes, {len(j.get('edges', []))} edges, "
              f"tokens {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}, cost ${usage.get('cost', 0):.3f}")
    REVIEW.mkdir(exist_ok=True)
    out = REVIEW / (path.stem + ".json")
    out.write_text(json.dumps({"source": str(path), "model": MODEL, "nodes": nodes, "edges": edges}, indent=1, ensure_ascii=False))
    print(f"review file: {out}")
    return out


def load(review_path):
    j = json.loads(Path(review_path).read_text())
    con = connect()
    skipped, count = [], 0
    with con:
        for n in j.get("nodes", []):
            if n.get("type") in NODE_TYPES and n.get("name"):
                get_or_create_node(con, n["type"], n["name"], "|".join(n.get("aliases") or []), n.get("description") or "")
        for e in j.get("edges", []):
            if e.get("type") not in EDGE_TYPES or e.get("src_type") not in NODE_TYPES or e.get("dst_type") not in NODE_TYPES \
                    or not e.get("src") or not e.get("dst"):
                skipped.append(e)
                continue
            s = get_or_create_node(con, e["src_type"], e["src"])
            d = get_or_create_node(con, e["dst_type"], e["dst"])
            add_edge(con, s, d, e["type"], e.get("role") or "", e.get("start"), e.get("end"), j.get("source", ""),
                     e.get("quote") or "", e.get("confidence") or 80, f"extract:{j.get('model', '?')}")
            count += 1
    print(f"loaded {count} edges, skipped {len(skipped)}")
    for b in skipped[:5]:
        print("  skipped:", {k: b.get(k) for k in ("src", "type", "dst", "src_type", "dst_type")})


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--load"]:
        load(args[1])
    else:
        rp = extract(Path(args[0]))
        if "--import" in args:
            load(rp)
