# Design doc — principles and templates

A design doc is a **technical design document**: an internal contract between the people involved in the project and a communication tool that explains the core of the system. It is written **before development starts** — it is the map of the software, and changing a document is cheap while changing code is expensive.

## Principles
1. **Just enough.** Neither too much nor too little: every section must help someone build, operate or change the system.
2. **Optimise the reader's investment.** The most important information first; short sentences; one idea per paragraph; plain words over jargon (define unavoidable terms in the glossary).
3. **Document what is least likely to change**: goals, constraints, boundaries, data ownership, contracts, decisions and their reasons. Leave volatile details (class names, exact config values) to the code.
4. **Describe what is good to know**: the things a newcomer would otherwise get wrong or spend a day discovering.
5. **Logical, progressive organisation**: context → goals → requirements → overview → details → risks. Each section can be read after the previous ones only.
6. **Cover a concept completely or not at all.** No half-explained mechanism: if retries are mentioned, say which calls, how many times, with which backoff, and what happens after.
7. **Include examples**: a sample request/response, a sample event, a worked load calculation.
8. **Avoid complex diagrams.** One overview diagram, plus at most one diagram per detailed view. No technology logos. Every figure has a caption and is referenced in the text.
9. **Explain every table**: one sentence before it saying what a row is and what each column means.
10. **Explain every chart**: say what the X axis and the Y axis represent, with units.
11. **Professional tone, no addressees.** Do not name or describe the readers; write in the impersonal or the "we" of the project.
12. **Decisions are traceable**: each one gives the choice, the reason, the rejected alternative and the signal that would make us revisit it.

## Two phases, two templates

### A. Project proposal — general architecture
Goal: agree on *what* we build and the *big choices* before investing. 4–8 pages.
1. **Context and scope** — the problem, who has it, what is in and out of scope.
2. **Goals and non-goals** — measurable goals; explicit non-goals.
3. **Requirements and estimates** — functional requirements; non-functional (latency, availability, consistency, security, cost); load estimates with their calculation.
4. **Architecture overview** — the overview diagram and one paragraph per component group.
5. **Key decisions and alternatives** — the structuring choices (service boundaries, data stores, sync/async, API style, hosting).
6. **Risks** — what could make the design fail, likelihood, mitigation.
7. **Open questions.**

### B. Project implementation — detailed technical documentation
Goal: let the team build and operate the system without guessing. Everything in A, plus:
1. **Data** — model and ownership, stores and why, schema overview and indexes, replication, caching (keys, TTL, invalidation), search, file storage, retention.
2. **API** — style per boundary, resources, main endpoints table, conventions (auth, errors, pagination, idempotency, rate limiting, versioning), events and webhooks, with one request/response example.
3. **Infrastructure, scalability and reliability** — topology, load balancing, CDN, scaling per component, latency budget, failure modes and degraded behaviour, RPO/RTO.
4. **Observability** — logs, metrics, traces, alerts, dashboards.
5. **Security** — authentication, authorisation, secrets, personal data, threat surface.
6. **Rollout and migration plan** — steps, feature flags, data migration, rollback.
7. **Glossary.**

## Markdown conventions for `build_pdf.py`
- First line `# <Title>`, then an optional `> <subtitle>` line (e.g. "Architecture proposal · <product>").
- `##` / `###` headings are numbered automatically: do not number them by hand.
- Figures on their own line: `![Caption](architecture.svg)` — use the `--no-logos --no-header` SVG.
- Tables, lists, code blocks, `> notes`, links and **bold** are supported. No raw HTML.
