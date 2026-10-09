"""Graph store for the Connection Mapper (SQLite, one file: graph.db).

  python3 db.py init
  python3 db.py add-node TYPE "Name" [--alias "Alt|Alt2"] [--notes "..."]
  python3 db.py add-edge SRC_TYPE "Src" EDGE_TYPE DST_TYPE "Dst" [--role R] [--start Y] [--end Y] [--source S] [--quote Q] [--confidence N]
  python3 db.py import-csv FILE.csv     # columns: src_type,src,type,dst_type,dst,role,start,end,source,quote,confidence
  python3 db.py merge KEEP_ID DROP_ID   # fold a duplicate node into another
  python3 db.py stats
"""
import argparse
import csv
import re
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "graph.db"
NODE_TYPES = ("person", "org", "project", "account", "place", "event", "document")
EDGE_TYPES = ("employed_at", "led", "board_of", "founded", "member_of", "worked_on", "attended",
              "met_with", "corresponded_with", "family_of", "succeeded", "advised",
              "funded", "owned", "affiliated_with", "replied_to", "mentioned", "cited_in")
AFFILIATION = ("employed_at", "led", "board_of", "founded", "member_of")
HONORIFICS = re.compile(r"^(sir|dr|mr|mrs|ms|prof|professor|lord|baron|count|herr|monsieur)\.?\s+", re.I)

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
  id INTEGER PRIMARY KEY,
  type TEXT NOT NULL,
  name TEXT NOT NULL,
  norm TEXT NOT NULL,
  aliases TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(type, norm)
);
CREATE TABLE IF NOT EXISTS edges (
  id INTEGER PRIMARY KEY,
  src INTEGER NOT NULL REFERENCES nodes(id),
  dst INTEGER NOT NULL REFERENCES nodes(id),
  type TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT '',
  start TEXT,
  end TEXT,
  source TEXT NOT NULL DEFAULT '',
  quote TEXT NOT NULL DEFAULT '',
  confidence INTEGER NOT NULL DEFAULT 80,
  added_by TEXT NOT NULL DEFAULT 'manual',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS edges_src ON edges(src);
CREATE INDEX IF NOT EXISTS edges_dst ON edges(dst);
"""


def norm(name):
    n = HONORIFICS.sub("", (name or "").strip().lower())
    n = re.sub(r"[^\w\s]", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def connect(path=DB):
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def find_node(con, name, type_=None):
    """Exact match on the normalized name, then on aliases. Returns a row or None."""
    n = norm(name)
    if not n:
        return None
    rows = con.execute("SELECT * FROM nodes" + (" WHERE type=?" if type_ else ""), (type_,) if type_ else ()).fetchall()
    for r in rows:
        if r["norm"] == n:
            return r
    for r in rows:
        if n in [norm(a) for a in r["aliases"].split("|") if a.strip()]:
            return r
    return None


def get_or_create_node(con, type_, name, aliases="", notes=""):
    if type_ not in NODE_TYPES:
        raise ValueError(f"node type {type_!r}; use one of {NODE_TYPES}")
    row = find_node(con, name, type_)
    if row:
        known = {row["norm"]} | {norm(a) for a in row["aliases"].split("|") if a.strip()}
        new = [a.strip() for a in aliases.split("|") if a.strip() and norm(a) not in known]
        if new or (notes and not row["notes"]):
            merged = "|".join([a for a in row["aliases"].split("|") if a] + new)
            con.execute("UPDATE nodes SET aliases=?, notes=? WHERE id=?", (merged, row["notes"] or notes, row["id"]))
        return row["id"]
    cur = con.execute("INSERT INTO nodes(type, name, norm, aliases, notes) VALUES (?,?,?,?,?)",
                      (type_, name.strip(), norm(name), aliases, notes))
    return cur.lastrowid


def add_edge(con, src, dst, type_, role="", start=None, end=None, source="", quote="", confidence=80, added_by="manual"):
    if type_ not in EDGE_TYPES:
        raise ValueError(f"edge type {type_!r}; use one of {EDGE_TYPES}")
    dup = con.execute("SELECT id, quote, source FROM edges WHERE src=? AND dst=? AND type=? AND role=? AND IFNULL(start,'')=?",
                      (src, dst, type_, role or "", start or "")).fetchone()
    if dup:
        if not dup["quote"] and quote:
            con.execute("UPDATE edges SET quote=?, source=? WHERE id=?", (quote, source or dup["source"], dup["id"]))
        return dup["id"]
    cur = con.execute(
        "INSERT INTO edges(src, dst, type, role, start, end, source, quote, confidence, added_by) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (src, dst, type_, role or "", start or None, end or None, source or "", quote or "", int(confidence or 80), added_by))
    return cur.lastrowid


def merge(con, keep, drop):
    k = con.execute("SELECT * FROM nodes WHERE id=?", (keep,)).fetchone()
    d = con.execute("SELECT * FROM nodes WHERE id=?", (drop,)).fetchone()
    if not k or not d:
        raise SystemExit("unknown node id")
    con.execute("UPDATE edges SET src=? WHERE src=?", (keep, drop))
    con.execute("UPDATE edges SET dst=? WHERE dst=?", (keep, drop))
    aliases = [a for a in k["aliases"].split("|") if a] + [d["name"]] + [a for a in d["aliases"].split("|") if a]
    con.execute("UPDATE nodes SET aliases=?, notes=? WHERE id=?", ("|".join(dict.fromkeys(aliases)), k["notes"] or d["notes"], keep))
    con.execute("DELETE FROM nodes WHERE id=?", (drop,))


def import_csv(con, path):
    n = 0
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            s = get_or_create_node(con, row["src_type"], row["src"])
            d = get_or_create_node(con, row["dst_type"], row["dst"])
            add_edge(con, s, d, row["type"], row.get("role", ""), row.get("start") or None, row.get("end") or None,
                     row.get("source", ""), row.get("quote", ""), row.get("confidence") or 80, "csv")
            n += 1
    return n


def stats(con):
    for t, c in con.execute("SELECT type, COUNT(*) FROM nodes GROUP BY type ORDER BY 2 DESC"):
        print(f"{c:5d} {t} nodes")
    for t, c in con.execute("SELECT type, COUNT(*) FROM edges GROUP BY type ORDER BY 2 DESC"):
        print(f"{c:5d} {t} edges")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("add-node")
    p.add_argument("type"); p.add_argument("name"); p.add_argument("--alias", default=""); p.add_argument("--notes", default="")
    p = sub.add_parser("add-edge")
    for a in ("src_type", "src", "type", "dst_type", "dst"):
        p.add_argument(a)
    for a in ("--role", "--start", "--end", "--source", "--quote"):
        p.add_argument(a, default="")
    p.add_argument("--confidence", type=int, default=80)
    p = sub.add_parser("import-csv"); p.add_argument("file")
    p = sub.add_parser("merge"); p.add_argument("keep", type=int); p.add_argument("drop", type=int)
    sub.add_parser("stats")
    a = ap.parse_args()
    con = connect()
    with con:
        if a.cmd == "init":
            print(f"ready: {DB}")
        elif a.cmd == "add-node":
            print(get_or_create_node(con, a.type, a.name, a.alias, a.notes))
        elif a.cmd == "add-edge":
            s = get_or_create_node(con, a.src_type, a.src)
            d = get_or_create_node(con, a.dst_type, a.dst)
            print(add_edge(con, s, d, a.type, a.role, a.start or None, a.end or None, a.source, a.quote, a.confidence))
        elif a.cmd == "import-csv":
            print(f"{import_csv(con, a.file)} edges")
        elif a.cmd == "merge":
            merge(con, a.keep, a.drop); print("merged")
        elif a.cmd == "stats":
            stats(con)


if __name__ == "__main__":
    main()
