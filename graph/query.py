"""Ask the graph questions.

  python3 query.py who "Montagu Norman"                       # everything linked to one node, with evidence
  python3 query.py path "Montagu Norman" "Owen Young"          # shortest chain between two nodes
  python3 query.py roster "Bank of England" [1929]             # people affiliated with an org, optionally active in a year
  python3 query.py moves "Bank of England" "Bank for International Settlements"   # people linked to both orgs
  python3 query.py overlap "Hjalmar Schacht" "Montagu Norman"  # orgs/events both are linked to, with dates
  python3 query.py search young                                # find nodes by name fragment
"""
import re
import sys
from collections import deque

from db import AFFILIATION, connect, find_node, norm


def year(s):
    m = re.match(r"\d{4}", s or "")
    return int(m.group(0)) if m else None


def resolve(con, name):
    r = find_node(con, name)
    if r:
        return r
    toks = norm(name).split()  # "Owen Young" matches "Owen D. Young"
    rows = [r for r in con.execute("SELECT * FROM nodes")
            if all(t in (r["norm"] + " " + norm(r["aliases"].replace("|", " "))).split() for t in toks)]
    if not rows:
        rows = con.execute("SELECT * FROM nodes WHERE name LIKE ? OR aliases LIKE ?", (f"%{name}%", f"%{name}%")).fetchall()
    if len(rows) == 1:
        return rows[0]
    if not rows:
        raise SystemExit(f"no node matching {name!r}")
    raise SystemExit("ambiguous: " + ", ".join(f"{r['name']} ({r['type']}, id {r['id']})" for r in rows[:10]))


def edges_of(con, nid):
    return con.execute(
        "SELECT e.*, s.name AS sname, d.name AS dname FROM edges e JOIN nodes s ON s.id=e.src JOIN nodes d ON d.id=e.dst "
        "WHERE e.src=? OR e.dst=? ORDER BY IFNULL(e.start,'9999')", (nid, nid)).fetchall()


def fmt(e):
    when = f" [{e['start'] or '?'}–{e['end'] or '?'}]" if (e["start"] or e["end"]) else ""
    role = f" ({e['role']})" if e["role"] else ""
    line = f"{e['sname']} —{e['type']}{role}{when}→ {e['dname']}"
    if e["quote"]:
        line += f'\n        "{e["quote"][:200]}"'
    return line


def who(con, name):
    r = resolve(con, name)
    print(f"{r['name']} [{r['type']}]" + (f"  also: {r['aliases'].replace('|', ', ')}" if r["aliases"] else ""))
    if r["notes"]:
        print(f"  {r['notes']}")
    for e in edges_of(con, r["id"]):
        print("   ", fmt(e))


def path(con, a, b):
    s, t = resolve(con, a)["id"], resolve(con, b)["id"]
    prev, q = {s: None}, deque([s])
    while q and t not in prev:
        n = q.popleft()
        for e in edges_of(con, n):
            m = e["dst"] if e["src"] == n else e["src"]
            if m not in prev:
                prev[m] = (n, e)
                q.append(m)
    if t not in prev:
        print("no path")
        return
    chain = []
    n = t
    while prev[n]:
        n, e = prev[n]
        chain.append(e)
    print(f"{len(chain)} steps:")
    for e in reversed(chain):
        print("   ", fmt(e))


def active_in(e, yr):
    s, t = year(e["start"]), year(e["end"])
    if s is None and t is None:
        return True
    return (s or t) <= yr <= (t or s if t is not None else 9999)


def roster(con, org, yr=None):
    r = resolve(con, org)
    rows = [e for e in edges_of(con, r["id"]) if e["dst"] == r["id"] and e["type"] in AFFILIATION]
    if yr:
        rows = [e for e in rows if active_in(e, int(yr))]
    print(f"{r['name']}: {len(rows)} affiliations" + (f" active in {yr}" if yr else ""))
    for e in rows:
        print("   ", fmt(e).split("\n")[0])


def moves(con, a, b):
    ra, rb = resolve(con, a), resolve(con, b)
    pa = {e["src"]: e for e in edges_of(con, ra["id"]) if e["dst"] == ra["id"] and e["type"] in AFFILIATION}
    pb = {e["src"]: e for e in edges_of(con, rb["id"]) if e["dst"] == rb["id"] and e["type"] in AFFILIATION}
    both = set(pa) & set(pb)
    print(f"{len(both)} people linked to both {ra['name']} and {rb['name']}:")
    for pid in both:
        print("   ", fmt(pa[pid]).split("\n")[0])
        print("   ", fmt(pb[pid]).split("\n")[0])


def overlap(con, a, b):
    ra, rb = resolve(con, a), resolve(con, b)
    ea = {e["dst"]: e for e in edges_of(con, ra["id"]) if e["src"] == ra["id"]}
    eb = {e["dst"]: e for e in edges_of(con, rb["id"]) if e["src"] == rb["id"]}
    shared = set(ea) & set(eb)
    print(f"{len(shared)} shared links between {ra['name']} and {rb['name']}:")
    for nid in shared:
        print("   ", fmt(ea[nid]).split("\n")[0])
        print("   ", fmt(eb[nid]).split("\n")[0])


def search(con, text):
    for r in con.execute("SELECT * FROM nodes WHERE name LIKE ? OR aliases LIKE ? ORDER BY type, name", (f"%{text}%", f"%{text}%")):
        print(f"{r['id']:4d}  {r['type']:<9} {r['name']}" + (f"  ({r['aliases'].replace('|', ', ')})" if r["aliases"] else ""))


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    con = connect()
    {"who": who, "path": path, "roster": roster, "moves": moves, "overlap": overlap, "search": search}[cmd](con, *args)
