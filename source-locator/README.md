# Source Locator

Finds the likely real-world identity behind **one flagged pseudonymous account**, so the reporter can decide whether to reach out. Method adapted from arXiv 2602.16800 (see `../papers/2602.16800-notes.md`).

## Pipeline (paper's Extract → Search → Reason → Calibrate)
| Step | Paper | Here |
|---|---|---|
| Collect | pseudonymous profile + posts | `collect_hn.py` pulls a user's public comment history (HN first; Reddit/BitcoinTalk connectors later) |
| **Extract** | LLM summarizes posts into stated + inferred facts | Extractor agent (no web access) reads posts → profile with a quote for every fact (`prompts/extract.md`) |
| Anonymize | strip names, handles, URLs, repos; keep institutions, demographics, interests | Extractor also writes a *search profile* under the same rules; `leakcheck.py` confirms no handle/name/URL survived |
| **Search + Reason** | agent with web search finds and cross-checks candidates | Identifier agent (web access) gets only the search profile → shortlist → picks one or abstains (`prompts/identify.md`) |
| **Calibrate** | confidence score sets the precision threshold | Identifier outputs 0–100 confidence; `score.py` reports precision/recall at each threshold so we pick the cut-off |

## Guardrails (built into how it runs)
- **One target at a time.** No bulk mode, no "match the whole forum against LinkedIn".
- Targets come only from the scanner or a tip, logged with the reason they were flagged.
- Every fact in the output needs a source (a quote or a URL). No evidence, no claim.
- Below the threshold, the answer is "unknown". Abstaining is a valid result.
- Output goes to the reporter only. A human verifies before any outreach; first contact goes through the poster's own channel.
- Dossiers are deleted if the person declines or the match is wrong.

## Status (2026-10-08)
Built: `collect_hn.py` (collector), `leakcheck.py` (redaction + leak check), `prompts/extract.md`, `prompts/identify.md`, `extract.py` (via OpenRouter), `calibrate.py` (Jev same-person probabilities), `score.py`.

**First verification attempt, and why it stopped.** The eval set was 12 HN users who had posted their own LinkedIn in "Who wants to be hired?" threads (the paper's own ground-truth trick). Claude Sonnet 5.5 refused the Extract step on all 12, each time on the same grounds: compiling a pseudonymous stranger's scattered self-disclosures into a profile whose purpose is to find them is unmasking, whoever is asking. On reflection that holds for a *test*: those 12 people did not agree to be subjects, and the paper's authors (one at Anthropic) withheld their agent for exactly this reason. Their post histories and the refusal output were deleted. No model-shopping to get around the refusal: that is the thing the paper's authors were trying to prevent, and the wrong fix for a safety refusal.

## Verification protocol (revised)
Ground truth comes from **consenting people only**: the owner's own pseudonymous accounts, the reporter's, team members', or volunteers who hand over a handle plus their real identity.
1. `collect_hn.py user NAME` (or a Reddit/BitcoinTalk collector later) pulls the account's public posts.
2. `extract.py` builds the evidence profile and anonymized search profile; `leakcheck.py check` must pass.
3. The identifier (a Claude Code agent with web search, `prompts/identify.md`) gets only the search profile.
4. `calibrate.py` scores the shortlist with Jev; `score.py` reports correct / wrong / abstain by threshold.
5. Results keep hashed IDs and outcomes only; wrong guesses (uninvolved people) are never stored.

`calibrate.py --selftest` checks the Jev plumbing on fictional data and needs no real person.

## Where this sits in the workflow
Identification is the **last resort**, not the first step. Scanner flags an account → reporter messages it through the platform → if they answer, verification happens with their cooperation (prove employment privately) and no unmasking is needed. The Locator runs only when the platform route fails, one account at a time, with the reporter deciding.

**Known gap:** HN is tech people; our real targets are finance/crypto insiders on Reddit and BitcoinTalk. Any success rate measured on consenting HN-style accounts will not transfer directly.
