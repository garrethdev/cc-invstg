"""Render graph.db to an interactive map (graph.html).

  python3 render.py [OUT.html]

Open the file in a browser. Cytoscape loads from cdnjs; the data is embedded. The file holds the investigation data, so keep it local.
"""
import json
import sys
from pathlib import Path

from db import connect

HERE = Path(__file__).parent


def export(con):
    nodes = [dict(r) for r in con.execute("SELECT id, type, name, aliases, notes FROM nodes")]
    edges = [dict(r) for r in con.execute("SELECT id, src, dst, type, role, start, end, source, quote, confidence FROM edges")]
    return {"nodes": nodes, "edges": edges}


def main(out):
    data = export(connect())
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (HERE / "template.html").read_text().replace("__DATA__", payload)
    Path(out).write_text(html)
    print(f"{len(data['nodes'])} nodes, {len(data['edges'])} edges -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE / "graph.html")
