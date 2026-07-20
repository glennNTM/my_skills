# claude-skills

Skills personnels pour [Claude Code](https://claude.com/claude-code), écrits par Glenn Ntoutoume.

## Installation

Copie le dossier du skill voulu dans `~/.claude/skills/` (global) ou `.claude/skills/` à la racine d'un projet (local au projet) :

```bash
cp -r skills/<nom-du-skill> ~/.claude/skills/
```

## Skills

### [`planifier`](skills/planifier/SKILL.md)

Planifie l'exécution d'une tâche de développement (feature, refactoring, migration, bugfix) en explorant le projet et en produisant un plan structuré, validé par l'utilisateur avant tout développement.

### [`coder`](skills/coder/SKILL.md)

Démarre le développement d'une feature à partir d'un plan validé par `planifier` : création de branche, implémentation étape par étape, lint/typecheck/tests, puis pause pour validation manuelle. Conçu pour s'enchaîner avec `planifier`.

### [`diagramme-architecture`](skills/diagramme-architecture/SKILL.md)

Crée un diagramme d'architecture / de design system dans Figma (FigJam) à partir d'une description de projet : recherche les best practices pour la stack décrite, traduit l'architecture dans le vocabulaire strict qu'attend le renderer Figma, puis génère le diagramme.

## Licence

MIT — voir [LICENSE](LICENSE).
