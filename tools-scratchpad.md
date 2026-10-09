# Investigation Tools Scratchpad

Started 2026-10-07. A working list of the investigation tools for Confessions / CC. Rough notes, not a spec.

## Decisions so far (Q&A, 2026-10-07)
| Question | Answer |
|---|---|
| Where do the connections come from? | **Social/forum activity**: who replies to, mentions, quotes, follows, or posts in threads with whom |
| Which platforms first? | **Crypto forums** (BitcoinTalk, crypto subreddits, Discord/Telegram), **Reddit / X / 4chan**, **finance insider boards** (Wall Street Oasis, Blind, Glassdoor) |
| Why identify a poster? | **To reach them as a source**: find an anonymous insider so the reporter can contact them. Not to expose or publish them. |
| Build or buy? | **Custom build with Claude** |

## Goal: 15–20 whistleblowers (owner, 2026-10-07)
The tools exist to find and reach insiders. Tactics others have used to get inside elite worlds:

| Tactic | Who did it | How it applies here |
|---|---|---|
| **Work inside, in a service role** | Lawrence Otis Graham (busboy at Greenwich Country Club, NY mag 1992; owner's cousin), Barbara Ehrenreich, Günter Wallraff, Shane Bauer | Staff see everything and are invisible: drivers, assistants, event staff, IT, compliance juniors, conference crew |
| **Get the credential** | Brooke Harrington trained and certified as a wealth manager to study offshore wealth | Reporter attends industry courses/certs, conferences (Sibos, Money20/20, BIS/central-bank events) |
| **Anonymous mass interviews** | Joris Luyendijk (Guardian banking blog): ~200 anonymous City of London insiders, one referred the next | Closest model to the show: anonymity promised, published as Q&A. Ask each source "who else should I talk to?" |
| **Court records → names → door-knocking** | Julie K. Brown (Miami Herald, Epstein): ~80 identified, ~60 located, 8 talked | Retaliation/wrongful-termination suits, SOX whistleblower cases, FINRA BrokerCheck "discharged" notes, SEC actions. These people have already blown the whistle; their names are in public dockets |
| **Secure inbox for leaks** | Panama Papers (anonymous source contacted Süddeutsche Zeitung), LuxLeaks, HSBC/Falciani | Signal number + SecureDrop-style tip line before episode 1 airs |
| **Public callouts** | ProPublica "Do you work at X?" callouts; Greg Smith's Goldman op-ed showed people will go public | Every episode ends with "If you were in the room, talk to us." The silhouette format is the promise of anonymity, so **the show recruits episodes 9–20** |
| **Go through whistleblower lawyers and groups** | SEC/CFTC/IRS/AML reward programs pay 10–30% of sanctions; lawyers and nonprofits (Government Accountability Project, Whistleblower Aid, The Signals Network) work with these people | Lawyers already represent finance whistleblowers; build relationships with a few firms |
| **Target the recently departed** | Common newsroom practice | LinkedIn: people who left right after a scandal, layoff/WARN notices, angry Glassdoor/Blind posts. Ex-employees talk more freely |
| **Be in the room** | Kevin Roose crashed the Kappa Beta Phi dinner; Michael Wolff (*Fire and Fury*) | Galas, alumni events, side events at summits |

**Funnel math (rough):** Brown got ~10% of identified people talking; Luyendijk needed ~200 interviews. For 15–20 on-camera sources, plan on **200–400 identified, ~150 contacted, 40–60 conversations**.

**Risks to clear with the lawyer:**
- Undercover employment: ABC was sued for trespass and breach of loyalty after its reporters took jobs at Food Lion to film undercover (Food Lion v. ABC, 1999).
- NDAs and employment contracts: SEC rules protect talking *to regulators*, not to press.
- Swiss bank secrecy law (Banking Act Art. 47) penalizes disclosing bank client data, and since 2015 also third parties who pass it on. Relevant to Basel/Swiss sources.
- Source exposure: metadata, filming locations, voice. Use voice altering plus an actor recreation.

## Core thesis (owner, 2026-10-07)
There is a temporary information gap. Sworn testimony, unredacted files on .gov sites, library and archive collections, old forums and archived websites still hold material that powerful people haven't scrubbed yet. Right now AI gives the person *pulling* information the advantage: one person can read and cross-reference what used to take a newsroom. The window won't stay open, so move fast and keep copies.

**Stress-test:**
- Most of this isn't hidden, it's *unread*. The edge is reading thousands of pages and **connecting** them (a LinkedIn job + a deposition + a 2017 forum post), not getting access.
- The window is closing from several sides: platforms closing APIs (Reddit, X), sites blocking AI crawlers, link rot, reputation firms filing takedowns. The other side has AI too.
- So **preservation is part of the tool**. Everything found gets saved locally with a timestamp + hash and pushed to the Wayback Machine, so it stays usable as evidence (lawyer will want this).
- Accidentally unredacted files can contain private data of bystanders. Reading them is fine; publishing needs the lawyer.

## Added scope (owner, 2026-10-07; details pending)
- **Go "way more internal"**: meaning still to confirm (rank-and-file staff? org charts and project teams? ex-employees? internal docs?).
- **LinkedIn work-history map**: who worked where, when; career moves between institutions (revolving door). LinkedIn bans scraping and has sued over it; possible routes: Apollo connector (already in this app, returns employment history), manual browse + Claude structures it, or a paid people-data vendor.
- **Archive Miner (4th tool)**: sworn testimony and court records (CourtListener/RECAP), congressional hearings (govinfo.gov), FOIA reading rooms, SEC EDGAR full-text search, Wayback Machine snapshots of sites as they used to be, library/digital archives, historical Reddit dumps. Feeds names and entities into the same database as everything else.

## Services on hand (checked 2026-10-08)
| Service | What it is | Where it fits |
|---|---|---|
| **OpenRouter** (key in Keychain as `openrouter_api_key`) | One API for many models; has Claude Sonnet/Opus/Haiku 5.5 | Runs the Extract step now; any script step later |
| **ScrapeCreators** (owner has an account; key not on this Mac yet) | Social scraping API: Reddit, X, LinkedIn, YouTube, TikTok, IG etc. MCP endpoint + CLI. 100 free credits, then $47 / 25k | Collector connectors for the **forum scanner** (Reddit, X) and candidate lookups in the Source Locator Search step |
| **Jev** (TypeSafe) | A "decision model": returns a typed answer with a probability (Choice / Score / yes-no) instead of prose. Fast and cheap. Via OpenRouter | **Calibrate step**: "same person? yes/no + probability" on each shortlist candidate; also the scanner's insider filter ("does this post read like an insider?"). Needs a shadow test against Claude before trusting it |
| **Jev Social** (socai-io/jev-social, MIT) | Jev + a local CLI that drives the owner's *own logged-in Chrome* to read Instagram/TikTok/LinkedIn, read-only, every finding cited | Possible **LinkedIn reader** for one candidate at a time (experience, education). Uses a real account, so LinkedIn can restrict it; use a research account, never the owner's main one |
| **Superwarm** (key in Keychain as `superwarm_api_key`) | Creates and warms TikTok/Instagram accounts for automation | Not an investigation tool. Belongs to the **rollout** (seeding host clips from many accounts). Flag: coordinated accounts break platform rules and read as astroturfing if exposed; decide with eyes open |

## The original three tools

These are one pipeline, not three separate apps. The scanner collects posts into one database, the mapper draws connections from that same database, and the source locator works on the posters the other two flag.

```
Forum Scanner  ──►  shared post DB  ──►  Connection Mapper
                         │
                         └──►  Source Locator (flagged posters only)  ──►  reporter outreach
```

### 1. Forum Scanner (build first)
- **Job:** watch the target platforms for keywords and topics (BIS, mBridge, Agora, CBDC, specific banks, names from the research), save matching posts with author, timestamp, thread, and links, then rank by "sounds like an insider".
- **Insider signals to score:** claims of employment or access, jargon specific to one institution, specific dates or figures, "throwaway" accounts, posts that were later deleted.
- **Access notes per platform** (check ToS before building each connector):
  - BitcoinTalk: public HTML, full post history on profiles. Easiest start.
  - Reddit: official API (paid for commercial use); historical dumps exist for older data.
  - 4chan: read-only JSON API for live threads; third-party archives for older ones. Mostly anonymous, so limited author data.
  - X: API is expensive; scope carefully.
  - Telegram: public channels readable via the API with a user account.
  - Discord: scraping with a user account breaks ToS. Only join and read manually, or use a bot where a server admin allows it.
  - Wall Street Oasis / Blind / Glassdoor: login walls, and their ToS forbid scraping. Likely manual monitoring plus saved searches/alerts instead of a scraper.
- **Storage:** SQLite to start.

### 2. Connection Mapper
- **Built 2026-10-08, v0 in `graph/`** (see its README): SQLite store, document extractor (people/orgs/relationships with verbatim quotes, via OpenRouter), query commands (who / path / roster / moves / overlap), interactive map (`graph.html`). First run on `BIS_Founders_Report.md`: 45 nodes, 72 edges, $0.16. Apollo importer written for LinkedIn work histories, untested.
- **Nodes:** accounts (later also people, companies, institutions).
- **Edges:** replied-to, mentioned, quoted, same-thread, follows, shared links, cross-platform same handle.
- **Output:** an interactive graph (web page) to filter by topic, platform, date range; clusters show who talks to whom about what.
- **Later:** merge with public records (board seats, filings) so forum accounts can sit next to institutions on the same map.

### 3. Source Locator (reframed from "who posted this")
- **Job:** for a flagged poster, put together a confidence-scored profile so the reporter can decide whether and how to reach out.
- **Methods:** same handle on other platforms, full post history (role, location, and timeline clues the person has posted publicly), activity hours → likely timezone, writing-style comparison across accounts (link alts).
- **Output:** a short private note for the reporter: likely role/access, confidence level, and the best channel to contact them (prefer the platform's own DM first).
- **Build status (2026-10-08):** pipeline code in `source-locator/` (see its README). First test on 12 non-consenting HN users was refused by the model on every profile and then dropped on reflection; verification will use consenting accounts instead. Identification is the last resort after platform DM fails, not the first step.
- **Method reference (2026-10-08):** arXiv 2602.16800, "Large-scale online deanonymization with LLMs" (notes in `papers/2602.16800-notes.md`). Pipeline: extract profile from posts → search candidates → LLM reasons over shortlist → confidence threshold. ~67% identified at 90% precision, $1–4 per person. We build the **targeted** version only (one flagged poster at a time, human-verified), not bulk matching of whole forums.

## Guardrails (source-finding)
The series protects its own whistleblowers in silhouette. A tool that unmasks forum insiders can burn sources the same way, so:
- Locator results are **never published** and never shared outside the reporter + owner.
- First contact goes through the poster's own channel (platform DM), not their employer, family, or a personal email they never gave out.
- If they decline, stop and delete the profile.
- Keep profiles encrypted, not in synced cloud folders or chat logs.
- Run the outreach protocol past the media lawyer (already on the hiring list) and the reporter.
- Our own opsec: separate research accounts, no scraping from personal IPs/accounts tied to the show.

## Open questions (for later)
- Seed list: which keywords, subreddits, BitcoinTalk boards, Telegram channels to start with?
- How far back: live monitoring only, or historical (years of posts)?
- Alerts: how should hits reach you (email digest, Slack, a dashboard)?
- Budget for paid APIs (X, Reddit) and residential proxies, if any?
- Where does it run: this Mac, or a small cloud server that runs 24/7?
- Does the reporter hire need access, and at what point?

## Suggested next step
Build **Scanner v0** on BitcoinTalk + Reddit (cheapest, most open access) with 10–20 seed keywords, saving to SQLite, plus a daily digest of the top-scored posts. Needs from you: the seed keyword list and 3–5 starting subreddits/boards.
