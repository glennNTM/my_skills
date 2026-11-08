# claude-skills

Skills personnels pour [Claude Code](https://claude.com/claude-code), écrits par Glenn Ntoutoume.

## Installation

Copie le dossier du skill voulu dans `~/.claude/skills/` (global) ou `.claude/skills/` à la racine d'un projet (local au projet) :

```bash
cp -r skills/<nom-du-skill> ~/.claude/skills/
```

Certains skills s'appuient sur des **agents** (sous-agents Claude Code, chacun avec son propre prompt système). Copie-les dans `~/.claude/agents/`, puis ouvre une nouvelle session pour qu'ils soient chargés :

```bash
cp agents/*.md ~/.claude/agents/
```

## Skills

### [`planifier`](skills/planifier/SKILL.md)

Planifie l'exécution d'une tâche de développement (feature, refactoring, migration, bugfix) en explorant le projet et en produisant un plan structuré, validé par l'utilisateur avant tout développement.

### [`coder`](skills/coder/SKILL.md)

Démarre le développement d'une feature à partir d'un plan validé par `planifier` : création de branche, implémentation étape par étape, lint/typecheck/tests, puis pause pour validation manuelle. Conçu pour s'enchaîner avec `planifier`.

### [`diagramme-architecture`](skills/diagramme-architecture/SKILL.md)

Crée un diagramme d'architecture / de system design dans **Excalidraw** (`.excalidraw` éditable, avec les logos officiels des technos) et un **`ARCHITECTURE.md`** lisible par les devs et les agents IA (briques, flux, décisions, évolutions). Trois modes, orchestrés avec 4 agents :

- **Codebase** : scanne le projet en lecture seule et dessine l'**état actuel** (chaque élément avec sa preuve `fichier:ligne`), puis, si l'utilisateur le veut, propose une **architecture cible** améliorée dans des fichiers séparés.
- **Produit existant** (Twitch, Spotify, Figma…) : reconstitue sa stack à partir de sources publiques, avec niveau de confiance et sources.
- **Conception** : conçoit un nouveau système à partir d'une description et des bonnes pratiques adaptées à l'échelle.

Le script `build_excalidraw.py` met en page automatiquement (colonnes par catégorie, flèches orthogonales, couloirs, ordre des nœuds qui minimise les croisements) ; `check_layout.py` vérifie la lisibilité sans navigateur. Avec `--open`, le diagramme s'ouvre dans VS Code (extension `pomdtr.excalidraw-editor`).

Nécessite les agents du dossier [`agents/`](agents/) :

| Agent | Rôle |
|---|---|
| [`archi-explorateur-code`](agents/archi-explorateur-code.md) | Lit une codebase en lecture seule et reconstitue l'architecture réelle, chaque élément avec sa preuve |
| [`archi-chercheur-produit`](agents/archi-chercheur-produit.md) | Recherche la stack réelle d'un produit existant, avec sources et niveau de confiance |
| [`archi-chercheur-bonnes-pratiques`](agents/archi-chercheur-bonnes-pratiques.md) | Recommandations d'architecture adaptées à l'échelle et à l'équipe, sourcées |
| [`archi-expert-senior`](agents/archi-expert-senior.md) | Expert senior en system design : conçoit la cible, génère et vérifie le diagramme |

### [`landing-page-builder`](skills/landing-page-builder/SKILL.md)

Guide la création d'une landing page one-page codée directement dans la codebase, via un wizard en 5 étapes (contexte, objectif, direction visuelle, sections, technique) validé par un récapitulatif avant toute écriture de code. Produit un composant par section, les tokens de design, le SEO de base, l'accessibilité WCAG 2.2 AA, des pages légales en stub et une checklist finale. Recherche et intègre des images libres de droit (Unsplash, Pexels, Pixabay, Openverse…) pour les sections qui s'y prêtent, avec licences vérifiées et crédits tracés. Inclut un script de vérification des contrastes et un script de recherche d'images Openverse.

## Licence

MIT — voir [LICENSE](LICENSE).
