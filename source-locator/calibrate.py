"""Calibrate step: typed same-person probabilities from Jev (TypeSafe System One).

  python3 calibrate.py PROFILE.json CANDIDATES.json     # prints one row per candidate, writes nothing
  python3 calibrate.py --selftest                       # fictional profile + candidates, checks the plumbing

Each candidate gets two Nouls in one request:
  same_person   P(candidate is the person described in the profile)
  contradicted  P(something in the candidate record rules the match out)
Code applies thresholds; the middle band goes to a human.
"""
import json
import os
import subprocess
import sys
import time

import requests

YES, NO = 0.8, 0.2
ENDPOINT = "https://api.typesafe.ai/v1/systemone"


def api_key():
    return os.environ.get("TYPESAFE_API_KEY") or subprocess.check_output(
        ["security", "find-generic-password", "-s", "typesafe_jev_api_key", "-w"], text=True).strip()


def questions_for(candidates):
    q = {}
    for c in candidates:
        cid = c["id"]
        q[f"same_{cid}"] = {
            "type": "noul",
            "instructions": {"candidate": {k: v for k, v in c.items() if k != "id"},
                             "question": "Is `candidate` the same real person as the one described in `profile`?"},
            "criteria": {"true": "Career, location, timeline and distinctive details line up on several independent points",
                         "false": "Only generic overlap, or a different person with a similar background"},
        }
        q[f"contra_{cid}"] = {
            "type": "noul",
            "instructions": {"candidate": {k: v for k, v in c.items() if k != "id"},
                             "question": "Does any fact in `candidate` contradict a fact in `profile`?"},
            "criteria": {"true": "A specific conflict: different years, employers, cities, degrees or life facts that cannot both be true",
                         "false": "No conflict; gaps are fine"},
        }
    return q


def judge(profile, candidates):
    body = {"model": "jev-latest", "state": {"profile": profile}, "questions": questions_for(candidates)}
    for attempt in range(4):
        r = requests.post(ENDPOINT, headers={"Authorization": f"Bearer {api_key()}"}, json=body, timeout=120)
        if r.status_code in (429, 529):
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        break
    ans = r.json()["answers"]
    rows = []
    for c in candidates:
        same, contra = ans[f"same_{c['id']}"]["noul"], ans[f"contra_{c['id']}"]["noul"]
        if same >= YES and contra <= NO:
            verdict = "match"
        elif same <= NO or contra >= YES:
            verdict = "no"
        else:
            verdict = "human review"
        rows.append({"id": c["id"], "same_person": round(same, 3), "contradicted": round(contra, 3), "verdict": verdict})
    return rows, r.json().get("usage")


SELFTEST_PROFILE = {
    "summary": "Backend engineer in payments. Spent about four years at a London fintech on card-issuing infrastructure, "
               "then moved to Lisbon in 2022 to join an early-stage climate-data startup as a founding engineer. "
               "Physics PhD from a Portuguese university around 2015. Writes about Rust, mentions a sailing hobby and two kids.",
}
SELFTEST_CANDIDATES = [
    {"id": "A", "name": "Fictional Person A", "headline": "Founding Engineer at a climate analytics startup, Lisbon",
     "experience": ["Senior Engineer, card issuing platform, London fintech, 2018-2022", "Founding Engineer, Lisbon, 2022-present"],
     "education": "PhD Physics, University of Porto, 2015", "other": "Open-source Rust contributor"},
    {"id": "B", "name": "Fictional Person B", "headline": "Backend Engineer, Lisbon",
     "experience": ["Software Engineer, e-commerce, Lisbon, 2016-present"],
     "education": "MSc Computer Science, Lisbon, 2016", "other": None},
    {"id": "C", "name": "Fictional Person C", "headline": "Payments engineer, Berlin",
     "experience": ["Engineer, card issuing, London fintech, 2017-2021", "Staff Engineer, Berlin neobank, 2021-present"],
     "education": "PhD Physics, University of Porto, 2015", "other": "Posts about sailing"},
]


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        profile, candidates = SELFTEST_PROFILE, SELFTEST_CANDIDATES
    else:
        profile = json.load(open(sys.argv[1]))
        candidates = json.load(open(sys.argv[2]))
    rows, usage = judge(profile, candidates)
    for row in rows:
        print(f"{row['id']:<4} same={row['same_person']:<6} contradicted={row['contradicted']:<6} -> {row['verdict']}")
    print("usage:", usage)
