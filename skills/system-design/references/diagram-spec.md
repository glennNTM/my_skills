# Diagram — spec format, logos, generation, checks

Skill folder: `~/.claude/skills/system-design/`. Agents write specs; the orchestrator fetches logos, generates and checks.

## 1. Spec format
```json
{
  "title": "Demo Shop — architecture",
  "subtitle": "Next.js · Node · PostgreSQL · RabbitMQ",
  "decisions": ["Choice + why + rejected alternative + revisit signal"],
  "evolutions": ["What comes later + the measured signal that triggers it"],
  "nodes": [
    {"id": "web", "label": "Next.js Web", "sublabel": "SSR",   "category": "client",    "logo": "logos/nextdotjs.svg"},
    {"id": "lb",  "label": "Nginx",       "sublabel": "LB · TLS", "category": "gateway", "logo": "logos/nginx.svg"},
    {"id": "api", "label": "Node API",    "sublabel": "×3",    "category": "service",   "logo": "logos/nodedotjs.svg"},
    {"id": "mq",  "label": "RabbitMQ",    "category": "async",     "logo": "logos/rabbitmq.svg"},
    {"id": "db",  "label": "PostgreSQL",  "category": "datastore", "logo": "logos/postgresql.svg"},
    {"id": "pay", "label": "Stripe",      "category": "external",  "logo": "logos/stripe.svg"}
  ],
  "edges": [
    {"from": "web", "to": "lb",  "label": "HTTPS"},
    {"from": "lb",  "to": "api", "label": "HTTP"},
    {"from": "api", "to": "db",  "label": "SQL"},
    {"from": "api", "to": "mq",  "label": "event"},
    {"from": "api", "to": "pay", "label": "payment"}
  ],
  "platform": {"label": "VPS · Docker", "categories": ["gateway", "service", "async", "datastore"]}
}
```
- **Categories** (columns, left to right): `client`, `gateway` (CDN, LB, reverse proxy, API gateway), `api` (optional: BFF, GraphQL gateway, SSR), `service`, `async` (queues, event logs), `datastore` (databases, cache, search, object storage), `external` (third parties). `async` and `datastore` share a column by default; `"columns"` changes the grouping.
- **Granularity**: C4 *container* level — one node = one independently deployable unit. A library is not a node, except an SDK calling a third party over the network (→ `external`). The same code run as separately deployed processes = several nodes.
- **Platform**: Kubernetes, AWS, a VPS, Dokploy… is a `platform` frame around the categories it hosts, not a node.
- **Labels**: `label` 2–3 words, details in `sublabel` (instance count `×3`, role). Edge labels 1–4 words (protocol or data).
- **Edges**: those touching `async` or `external` are dashed automatically; `"dashed": true` forces it (indirect or unverified flow); `"both": true` draws both arrowheads (WebSocket, long polling).
- **Limits**: ~7 nodes per category, **15 edges per view**. Beyond that, split into views: `spec-<view>.json`.
- `decisions` and `evolutions` are mandatory. For a current-state view, `decisions` holds only **observed** choices (with evidence) and `evolutions` stays empty.
- Logo paths are relative to the spec file.

### File names
| View | Spec | Diagram | Doc |
|---|---|---|---|
| Current state / new system | `spec.json` | `architecture.excalidraw` | `ARCHITECTURE.md` |
| Target | `spec-target.json` | `architecture-target.excalidraw` | `ARCHITECTURE-target.md` |
| Infrastructure (physical) | `spec-infrastructure.json` | `architecture-infrastructure.excalidraw` | `ARCHITECTURE-infrastructure.md` |

## 2. Readability
- Left-to-right reading: from the client to the data. A worker consuming from a queue: the edge goes from the queue to the worker.
- Label every edge between categories; an unlabelled arrow teaches nothing.
- Make often-forgotten infrastructure visible when it exists: cache, queue, CDN, load balancer, search, object storage.
- Do not mix levels (C4 context / container / component) or logical and physical views in one diagram: the infrastructure view is a separate spec.
- Anti-patterns: everything at one level without categories; unlabelled arrows everywhere; components added "to look complete"; one node per library; approximate or wrong logos.

## 3. Logos (diagram only — never in the design-doc PDF)
For each named technology, fetch its official logo into `logos/` next to the spec; reuse existing files.
1. **Simple Icons**: `curl -sfL https://cdn.simpleicons.org/<slug> -o logos/<slug>.svg`. Slug = lowercase, no spaces, `.` → `dot`, `+` → `plus` (`nextdotjs`, `nodedotjs`, `postgresql`, `redis`, `fastapi`, `traefikproxy`, `apachekafka`).
2. **Devicon** if missing: `https://cdn.jsdelivr.net/gh/devicons/devicon/icons/<name>/<name>-original.svg`.
3. Otherwise the vendor's official press kit or Wikimedia Commons; cloud services: the vendor's official architecture icons. Simple Icons no longer ships AWS logos.
4. Check each file starts with `<svg` / `<?xml` or is a real PNG/JPEG (the script re-checks and skips invalid files).
5. Not found → node without a logo, reported. Never an invented or look-alike logo.

## 4. Generate
```bash
py ~/.claude/skills/system-design/scripts/build_excalidraw.py docs/architecture/spec.json -o docs/architecture/architecture.excalidraw --lang <en|fr> [--open]
```
(`python` instead of `py` outside Windows.) The script lays out zones, nodes with logos, orthogonal arrows and labels, a legend, and writes `ARCHITECTURE.md` next to the spec (only the generated block is rewritten; hand-written notes are kept). Options: `--open` (VS Code, extension `pomdtr.excalidraw-editor`), `--doc-only` (keeps manual edits of the `.excalidraw`), `--no-doc`, `--doc <path>`. Large specs can take 15–20 s (crossing minimisation).

## 5. Check
```bash
py ~/.claude/skills/system-design/scripts/check_layout.py docs/architecture/architecture.excalidraw
```
Expected: 0 overlaps, 0 hidden labels, 0 arrows through a node (exit code 1 otherwise). ≤ 5 crossings is acceptable. Otherwise: split into views, reduce column-skipping edges (move entry points to `api`, event-driven workers to `async`), shorten sublabels. Two attempts, then deliver and report the defect.

Known limit: two arrows of neighbouring columns crossing in an X onto nodes on the same row can overlap; move one of the four nodes to another category and regenerate.

## 6. Static SVG (for the PDF)
```bash
py ~/.claude/skills/system-design/scripts/excalidraw_to_svg.py docs/architecture/architecture.excalidraw -o docs/architecture/design-doc/architecture.svg --no-logos --no-header
```
It reads the `.excalidraw` file, so manual edits made in Excalidraw are kept.
