# claude-skills

Skills personnels pour [Claude Code](https://claude.com/claude-code), écrits par Glenn Ntoutoume.

## Installation

Copie le dossier du skill voulu dans `~/.claude/skills/` (global) ou `.claude/skills/` à la racine d'un projet (local au projet) :

```bash
cp -r skills/<nom-du-skill> ~/.claude/skills/
```

Les skills qui orchestrent des **agents** les embarquent dans leur propre dossier (`<skill>/agents/`) : rien n'est installé dans `~/.claude/agents/`. Leur dossier contient un `.claude-plugin/plugin.json`, ce qui fait charger les agents par Claude Code (sous le nom `<skill>:<agent>`). Après l'installation, lance `/reload-plugins` ou ouvre une nouvelle session.

Pour tout installer d'un coup :

```bash
cp -r skills/* ~/.claude/skills/
```

## Skills

### [`planifier`](skills/planifier/SKILL.md)

Planifie l'exécution d'une tâche de développement (feature, refactoring, migration, bugfix) en explorant le projet et en produisant un plan structuré, validé par l'utilisateur avant tout développement.

### [`coder`](skills/coder/SKILL.md)

Démarre le développement d'une feature à partir d'un plan validé par `planifier` : création de branche, implémentation étape par étape, lint/typecheck/tests, puis pause pour validation manuelle. Conçu pour s'enchaîner avec `planifier`.

### [`system-design`](skills/system-design/SKILL.md)

A **senior software architect**: it frames requirements with questions, challenges the request, reasons in trade-offs, then designs the architecture of an existing codebase, a well-known product (Twitch, Discord…) or a new system. Covers system design, scalability, latency, caching, load balancing, databases, replication, sharding, consistency, message queues, rate limiting, CDNs, search, storage, microservices and observability.

Deliverables in `docs/architecture/`, written in the user's language:

- **always** — an editable **Excalidraw diagram** with official logos and `ARCHITECTURE.md` (current state, target, infrastructure view);
- **in scope** — `DATA.md` (stores, replication, sharding, consistency, caching, search, storage), `API.md` (style per boundary, endpoints, conventions, rate limiting, required indexes) and `INFRASTRUCTURE.md` (load balancing, CDN, scaling, latency, reliability, deployment, observability);
- **on request** — a professional **design-doc PDF** (project proposal or implementation phase), without logos.

It orchestrates 8 embedded agents ([`agents/`](skills/system-design/agents/)), each solving **one problem** with only the tools it needs, under shared rules ([`rules.md`](skills/system-design/rules.md)):

| Agent | Problem | Tools |
|---|---|---|
| `codebase-explorer` | What actually exists in the code? (read-only, `path:line` evidence) | Read, Grep, Glob |
| `product-researcher` | How is this known product built? | WebSearch, WebFetch |
| `best-practices-researcher` | What do serious teams do at this scale? | WebSearch, WebFetch |
| `data-architect` | Where and how does the data live? | Read, Write |
| `system-architect` | Which components, boundaries and flows? | Read, Write |
| `api-designer` | What is the API contract? | Read, Write |
| `infrastructure-architect` | How does it run and hold the load in production? | Read, Write |
| `technical-writer` | Turn the design into a design doc (PDF on request) | Read, Write |

Scripts (standard library only): `build_excalidraw.py` (automatic layout, `--lang en|fr`), `check_layout.py` (readability check without a browser), `excalidraw_to_svg.py` (static SVG, `--no-logos`), `build_pdf.py` (Markdown → PDF through headless Chrome/Edge). With `--open`, the diagram opens in VS Code (extension `pomdtr.excalidraw-editor`).

### [`landing-page-builder`](skills/landing-page-builder/SKILL.md)

Guide la création d'une landing page one-page codée directement dans la codebase, via un wizard en 5 étapes (contexte, objectif, direction visuelle, sections, technique) validé par un récapitulatif avant toute écriture de code. Produit un composant par section, les tokens de design, le SEO de base, l'accessibilité WCAG 2.2 AA, des pages légales en stub et une checklist finale. Recherche et intègre des images libres de droit (Unsplash, Pexels, Pixabay, Openverse…) pour les sections qui s'y prêtent, avec licences vérifiées et crédits tracés. Inclut un script de vérification des contrastes et un script de recherche d'images Openverse.

## Licence

MIT — voir [LICENSE](LICENSE).
