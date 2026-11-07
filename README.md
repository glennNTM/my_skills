# claude-skills

Skills personnels pour [Claude Code](https://claude.com/claude-code), écrits par Glenn Ntoutoume.

## Installation

Copie le dossier du skill voulu dans `~/.claude/skills/` (global) ou `.claude/skills/` à la racine d'un projet (local au projet) :

```bash
cp -r skills/<nom-du-skill> ~/.claude/skills/
```

## Skills

### [`planifier`](skills/planifier/SKILL.md)

Planifie l'exécution d'une tâche de développement (feature, refactoring, migration, bugfix) en explorant le projet et en produisant un plan structuré, validé par l'utilisateur avant tout développement. S'utilise uniquement en plan mode (entre en plan mode si besoin) et se valide via `ExitPlanMode`.

### [`coder`](skills/coder/SKILL.md)

Démarre le développement d'une feature à partir d'un plan validé par `planifier` : création de branche, implémentation étape par étape, lint/typecheck/tests, puis pause pour validation manuelle. Conçu pour s'enchaîner avec `planifier`.

### [`diagramme-architecture`](skills/diagramme-architecture/SKILL.md)

Crée un diagramme d'architecture / de design system dans Excalidraw (fichier `.excalidraw` éditable) à partir d'une description de projet : recherche les best practices pour la stack décrite, cherche sur le web le logo officiel de chaque techno, puis génère le diagramme avec les logos intégrés via `scripts/build_excalidraw.py`.

### [`landing-page-builder`](skills/landing-page-builder/SKILL.md)

Guide la création d'une landing page one-page codée directement dans la codebase, via un wizard en 5 étapes (contexte, objectif, direction visuelle, sections, technique) validé par un récapitulatif avant toute écriture de code. Produit un composant par section, les tokens de design, le SEO de base, l'accessibilité WCAG 2.2 AA, des pages légales en stub et une checklist finale. Recherche et intègre des images libres de droit (Unsplash, Pexels, Pixabay, Openverse…) pour les sections qui s'y prêtent, avec licences vérifiées et crédits tracés. Inclut un script de vérification des contrastes et un script de recherche d'images Openverse.

## Licence

MIT — voir [LICENSE](LICENSE).
