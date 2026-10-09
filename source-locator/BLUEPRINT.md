# Source Locator: Implementation Blueprint

Written 2026-10-08 for hand implementation. Method from arXiv 2602.16800 (Extract → Search → Reason → Calibrate). Existing code in this folder implements most steps; this document is the design you can rebuild from scratch.

## 1. Two modes, one pipeline

| | Mode A: Footprint audit | Mode B: Reach an anonymous insider |
|---|---|---|
| Who | A source already working with you | An account the scanner or a tip flagged |
| Consent | Yes: they give you their handles | No, until they answer |
| Goal | Tell them how findable they are and what to take down | Get a first conversation |
| Order | Run any time, repeat before each episode airs | Platform DM first. Identification only if DM fails and the reporter signs off |
| Output | A private findability report for the source | A private dossier for the reporter, then outreach or deletion |

Same components. Mode A runs the pipeline against a known answer (the source's identity) and reports what gave them away. Mode B runs it against an unknown.

## 2. Components

```
collect ─► extract ─► leakcheck ─► identify (search + reason) ─► calibrate ─► human review ─► outreach / delete
   │                                                                                  ▲
   └── Mode A only: the source's real identity is the ground truth ───────────────────┘
```

### 2.1 Collect (`collect_hn.py`, plus connectors to add)
- Input: platform + handle. Output: `data/<id>.posts.txt`, newest first, each line `[date] (thread) text`.
- Connectors: HN (Algolia API, done). Reddit and X via ScrapeCreators. BitcoinTalk: public profile post history, plain HTML. Telegram public channels via the API with a research account.
- Cap at ~60k characters per account (about 15k tokens). Take the most recent, then sample older posts evenly; identity clues cluster in replies to personal threads, so keep short comments too.
- Store with a timestamp and a SHA-256 of the raw fetch. This is evidence; the lawyer will want to know when it was captured.

### 2.2 Extract (`extract.py`, `prompts/extract.md`, `prompts/audit.md`)
- Model: Claude Sonnet 5.5 through OpenRouter, temperature 0. About $0.05–0.10 per account.
- Output: `facts[]` (category, fact, stated/inferred, confidence, verbatim quote, date), `direct_identifiers[]`, `search_profile` (150–400 words, paraphrased, no names/handles/URLs).
- Mode A uses `prompts/audit.md`: same extraction plus a findability rating per fact. The prompt states the real purpose (auditing a cooperating source's exposure), which is also what the model will do without pushback.
- Mode B uses `prompts/extract.md`. Expect refusals on some accounts: models decline to profile a stranger when the posts show political views, health, family, or anything that raises the stakes of being found. A refusal is a signal to stop on that account, not a bug to route around.

### 2.3 Leak check (`leakcheck.py`)
- Fails any search profile containing the handle, name tokens, URLs or emails. Run it every time; one leaked handle turns identification into a lookup and skews any measurement.

### 2.4 Identify: Search + Reason (`prompts/identify.md`; agent loop to implement)
The one piece not yet a script. Spec:
- Agent: a Claude model with two tools, `web_search(query) -> [title, url, snippet]` and `fetch(url) -> text` (truncate to ~8k chars). Budget: 25 tool calls, 10 minutes. Input: the search profile only. Never the posts, never the handle.
- Search providers, pick one: ScrapeCreators (if it exposes a Google search endpoint on your plan), Exa or Brave Search API (both have cheap keys), or OpenRouter's web plugin for single-shot searches. For eval runs, a Claude Code agent with built-in WebSearch works and needs no key.
- Loop: 1) list 3–6 distinctive fact combinations; 2) search combinations, not phrases; 3) shortlist up to 5 candidates; 4) open each candidate's public pages and check fact by fact; 5) answer or abstain.
- Output JSON: `guess {name, linkedin_url, other_urls}` or null, `confidence 0–100`, `matched_facts[] (fact -> URL)`, `contradictions[]`, `runner_up`, `searches_run`.
- Rules in the prompt: cite only URLs actually opened; abstain below 40; for eval runs, never visit the platform the posts came from.
- Reference cost: the paper reports $1–4 per target for this step.

### 2.5 Calibrate (`calibrate.py`, Jev via TypeSafe)
- For each shortlisted candidate, two Nouls in one request: `same_person` and `contradicted`. State = the profile; instructions carry the candidate record.
- Thresholds (from the self-test, tune on your own data): match if same ≥ 0.80 and contradicted ≤ 0.20; reject if same ≤ 0.20 or contradicted ≥ 0.80; everything else goes to a person.
- Cost: ~1.4k tokens for three candidates. Self-test on fictional data: true match 0.90/0.08, decoy with shared PhD and hobby 0.27/0.88.
- Jev can also run the scanner's insider filter: one Noul per post, "does the author claim or show inside access to the institution?", plus a Score for specificity.

### 2.6 Human review
- The reporter sees: the search profile, the candidate, the matched facts with URLs, the contradictions, the agent's confidence, Jev's two numbers.
- Decision options: contact, hold, delete. Logged with date and reason.
- Nothing goes to outreach without this step. The paper's best precision was ~90% on a friendlier population; at least 1 in 10 automated matches is a different person.

### 2.7 Outreach (Mode B) / Report (Mode A)
- Mode B first contact is through the platform the posts are on. Off-platform contact (email, LinkedIn) only after human review, and the message says plainly that a reporter found them through their public posts and offers a secure channel (Signal). Never through an employer, family, or a personal address they never shared.
- Mode A report to the source: how findable they are (abstained / found at N% confidence), the five facts that did the most damage, what to edit or delete, and the caveat in section 5.

## 3. Data handling
- All `data/` lives on an encrypted volume (an APFS encrypted disk image is enough). Never in iCloud, Dropbox, Google Drive or a chat log.
- Keys in the macOS Keychain (`openrouter_api_key`, `typesafe_jev_api_key`, later `scrapecreators_api_key`). Never in files.
- Retention: Mode B dossiers deleted when the person declines, when the match is wrong, or 90 days after last review, whichever is first. Mode A reports belong to the source; keep a copy only while they're actively working with you.
- Never stored anywhere: names of wrong guesses (uninvolved people), the eval subjects' raw posts after scoring.
- Log every run: date, mode, who requested it, why the account was flagged, outcome. The log is what shows a court or an editor that the tool was used narrowly.

## 4. Verification plan
- Subjects: consenting people only. Your own pseudonymous accounts, the reporter's, volunteers. Each gives handle + real identity. Aim for 10; two or three gives a first read.
- Run Mode B blind on each (the identifier gets only the search profile), then score: correct / wrong / abstain, precision and recall at confidence 40/60/80/90, Jev agreement with the agent.
- Bar before relying on it for outreach: ≥ 90% precision on your own subjects at whatever threshold you'll use, with abstention counted as acceptable.
- Expect worse numbers than the paper on finance/crypto forum accounts: fewer cross-platform links, more deliberate opsec, more throwaways. Measure, don't assume.
- Re-run the suite when you change a prompt, a model, or a search provider.

## 5. Advice to sources that comes out of Mode A
- Deleting posts lowers exposure; it doesn't erase it. Wayback snapshots, Reddit data dumps, and quote-replies survive. Say so.
- Mass-deleting an account the week an episode airs is itself a signal. Thin out gradually, or leave it and change behavior going forward.
- The facts that identify people are combinations: employer + city + year + hobby. Removing one leg of the combination is often enough.
- No new posts about the story anywhere, under any name. The paper's method links accounts by writing style and life details, not just by topic.
- Voice, filming location, and metadata matter more than forum posts once they're on camera; that's the production side's job (silhouette, voice alteration, actor recreation).

## 6. Left out on purpose
- No bulk mode (one account at a time; no forum-wide matching against LinkedIn). It sweeps up thousands of uninvolved people and reads as surveillance in any legal or press context.
- No model-switching or prompt tricks to get past a refusal. If a model won't profile an account, that account gets the platform-DM route or nothing.
- No testing on non-consenting people. The 12-user HN test was stopped for this reason and the data deleted.

## 7. Build order
1. `calibrate.py --selftest` (passes today) and `leakcheck.py`.
2. Mode A on your own account: collect → audit extract → leakcheck → identify (Claude Code agent) → calibrate → report. This is the first real verification and needs nobody's consent but yours.
3. Add two or three consenting volunteers; score.
4. Reddit and BitcoinTalk collectors via ScrapeCreators and plain HTML.
5. Identify agent as a standalone script with a search API key.
6. Only then, Mode B on a flagged account, with the reporter in the loop.
