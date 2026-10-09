"""Import Apollo people records (JSON) as employment edges.

  python3 import_apollo.py FILE.json

Accepts one person object, a list of them, or an object with "person", "people" or "matches".
Uses: name (or first_name + last_name), linkedin_url, title, organization.name,
employment_history[{organization_name, title, start_date, end_date, current}].
Save the output of an Apollo lookup (connector or REST API) to a file, then import it. Untested against live data as of 2026-10-08.
"""
import json
import sys

from db import add_edge, connect, get_or_create_node


def people(j):
    if isinstance(j, list):
        return j
    for k in ("people", "matches", "contacts"):
        if isinstance(j.get(k), list):
            return j[k]
    return [j.get("person", j)]


def main(path):
    con = connect()
    n = 0
    with con:
        for p in people(json.load(open(path))):
            name = p.get("name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
            if not name:
                continue
            notes = " · ".join(x for x in (p.get("headline"), p.get("linkedin_url")) if x)
            pid = get_or_create_node(con, "person", name, "", notes)
            jobs = p.get("employment_history") or []
            if not jobs and p.get("organization"):
                jobs = [{"organization_name": p["organization"].get("name"), "title": p.get("title"), "current": True}]
            for job in jobs:
                org = job.get("organization_name")
                if not org:
                    continue
                oid = get_or_create_node(con, "org", org)
                add_edge(con, pid, oid, "employed_at", job.get("title") or "", (job.get("start_date") or "")[:10] or None,
                         None if job.get("current") else (job.get("end_date") or "")[:10] or None,
                         p.get("linkedin_url") or "apollo", "", 70, "apollo")
                n += 1
    print(f"{n} employment edges")


if __name__ == "__main__":
    main(sys.argv[1])
