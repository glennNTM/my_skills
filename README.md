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

### [`architecture-systeme`](skills/architecture-systeme/SKILL.md)

Un **architecte logiciel senior** : il cadre les exigences par des questions, challenge la demande, raisonne en compromis, puis définit l'architecture d'un projet existant, d'un produit connu (Twitch, Discord…) ou d'un nouveau système. Livrables dans `docs/architecture/` :

- **diagrammes Excalidraw** éditables avec les logos officiels, et `ARCHITECTURE.md` (état actuel, cible, vue de déploiement) ;
- **`DONNEES.md`** : modèle de données, SGBD et hébergement justifiés à partir des patterns d'accès, backend applicatif par défaut, BaaS (Supabase, Firebase, Convex, Appwrite) seulement si le projet s'y prête ;
- **`API.md`** : style par frontière (REST, GraphQL, gRPC, WebSocket/SSE, webhooks), ressources, endpoints, conventions (auth, erreurs, pagination, idempotence, versioning) et index requis ;
- **`DEPLOIEMENT.md`** : estimation de charge, load balancing, scaling vertical ou horizontal, autoscaling, cache, réplicas, haute disponibilité, mise en production.

Il orchestre 7 agents embarqués ([`agents/`](skills/architecture-systeme/agents/)). Chacun traite **un seul problème**, avec uniquement les outils nécessaires et des règles non négociables :

| Agent | Problème | Outils |
|---|---|---|
| `codebase-explorer` | Qu'est-ce qui existe dans ce code ? (lecture seule, preuves `fichier:ligne`) | Read, Grep, Glob |
| `product-researcher` | Comment ce produit connu est-il construit ? | WebSearch, WebFetch |
| `best-practices-researcher` | Que font les équipes sérieuses à cette échelle ? | WebSearch, WebFetch |
| `data-architect` | Quel modèle de données, quel SGBD ? (BaaS seulement si le projet s'y prête) | Read, Write |
| `system-architect` | Quelles briques et quels flux ? | Read, Write |
| `api-designer` | Quel contrat d'API ? | Read, Write |
| `deployment-architect` | Comment ça tourne en prod et tient la charge ? | Read, Write |

Le script `build_excalidraw.py` met en page automatiquement (colonnes par catégorie, flèches orthogonales, ordre des nœuds qui minimise les croisements). `check_layout.py` vérifie la lisibilité sans navigateur. Avec `--open`, le diagramme s'ouvre dans VS Code (extension `pomdtr.excalidraw-editor`).

### [`landing-page-builder`](skills/landing-page-builder/SKILL.md)

Guide la création d'une landing page one-page codée directement dans la codebase, via un wizard en 5 étapes (contexte, objectif, direction visuelle, sections, technique) validé par un récapitulatif avant toute écriture de code. Produit un composant par section, les tokens de design, le SEO de base, l'accessibilité WCAG 2.2 AA, des pages légales en stub et une checklist finale. Recherche et intègre des images libres de droit (Unsplash, Pexels, Pixabay, Openverse…) pour les sections qui s'y prêtent, avec licences vérifiées et crédits tracés. Inclut un script de vérification des contrastes et un script de recherche d'images Openverse.

## Licence

MIT — voir [LICENSE](LICENSE).
