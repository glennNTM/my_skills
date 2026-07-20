---
name: coder
description: Démarre le développement d'une feature en s'appuyant sur le plan validé par `/planifier` (ou un plan fourni explicitement). Crée la branche feature en convention `feat/`, implémente étape par étape en suivant le plan, lance lint + typecheck + tests du projet, puis attend la validation manuelle de l'utilisateur avant de s'arrêter. Déclenche ce skill quand l'utilisateur dit "/coder", "implémente le plan", "démarre le développement", "code-le", "vas-y, lance-toi", ou tout signal clair de passage du plan à l'implémentation.
---

# Coder

Démarre le développement d'une feature à partir d'un plan validé. Ne fait pas plus que nécessaire : pas de commit auto, pas de push, pas de PR — laisse ces décisions à l'utilisateur.

## Pourquoi ce skill existe

Une fois le plan validé, l'utilisateur veut un démarrage propre : bonne branche, bon point de départ Git, implémentation cohérente avec le plan, qualité vérifiée (lint, types, tests), et une pause claire pour valider avant d'avancer plus loin.

## Prérequis

Un plan doit exister dans la conversation (issu de `/planifier` ou fourni explicitement). Si aucun plan n'est présent, demande à l'utilisateur de lancer `/planifier` d'abord — ne plonge pas dans le code sans cadrage.

Exception : pour une tâche **vraiment triviale** (1-3 lignes, typo, renommage), tu peux implémenter directement sans plan formel.

## Étapes

### 1. Vérifier l'état du working tree

Avant tout `git pull`, vérifie l'état du repo :

```bash
git status --short
git branch --show-current
```

- **Working tree non propre** (modifications non commitées) : **stoppe** et demande à l'utilisateur s'il veut commiter, stasher (`git stash`), ou abandonner ces changements. Ne jamais écraser silencieusement.
- **Branche actuelle déjà une branche feature** : signale-le à l'utilisateur et confirme qu'il veut bien repartir de la branche de référence (étape suivante).

### 2. Synchroniser avec la branche de référence

Demande sur quelle branche baser la nouvelle feature :

> "Sur quelle branche dois-je baser la nouvelle feature ? (`main`, `develop`, `staging`…)"

Une fois la réponse obtenue, **checkout d'abord, pull ensuite** :

```bash
git checkout <branche-de-reference>
git pull origin <branche-de-reference>
```

Cet ordre garantit que le pull se fait sur la bonne branche locale. Si conflit ou erreur de pull → stoppe et préviens l'utilisateur.

### 3. Déduire le nom de la feature

Déduis le nom depuis le titre du plan :

- Convertis en **kebab-case** : minuscules, tirets, sans accents, sans caractères spéciaux
- Reste concis : 2 à 5 mots max

Exemples :
- "Ajout de l'authentification OAuth" → `ajout-authentification-oauth`
- "Refactoring du module paiement" → `refactoring-module-paiement`
- "Fix bug calcul TVA" → `fix-bug-calcul-tva`

Si le nom paraît ambigu ou trop long, propose-le à l'utilisateur pour validation rapide.

### 4. Créer et checkout la branche feature

Convention : **`feat/<nom-feature>`** (Conventional Branches, cohérent avec Conventional Commits)

```bash
git checkout -b feat/<nom-feature>
```

Adapte le préfixe à la nature réelle de la tâche :
- `feat/` — nouvelle fonctionnalité
- `fix/` — bugfix
- `refactor/` — refactoring sans changement de comportement
- `chore/` — config, dépendances, outillage
- `docs/` — documentation uniquement
- `perf/` — optimisation de perf

Confirme à l'utilisateur la branche créée.

### 5. Lire 1-2 fichiers similaires avant d'écrire

Avant la première modification, **ouvre 1-2 fichiers du projet qui ressemblent à ce que tu vas écrire** (composant similaire, route similaire, service similaire). Le but : aligner le style (imports, naming, gestion d'erreurs, logging) sur la réalité du projet plutôt que sur tes habitudes.

C'est une étape rapide (2-3 minutes) qui évite des allers-retours de review.

### 6. Développement étape par étape

Implémente la fonctionnalité **dans l'ordre du plan**. Utilise l'outil de suivi de tâches (TaskCreate/TaskUpdate) pour cocher chaque étape du plan au fur et à mesure — ça donne de la visibilité à l'utilisateur et évite d'oublier une étape.

- Crée ou modifie les fichiers listés
- Respecte les conventions observées (étape 5)
- **Pas d'over-engineering** : pas de helper "au cas où", pas d'abstraction prématurée pour un seul cas, pas de feature flag pour une feature non finie. Si trois lignes similaires se répètent, c'est encore OK — n'extrait pas un helper tant que ce n'est pas nécessaire.
- Si une étape révèle un problème non anticipé (dépendance manquante, incompatibilité, ambiguïté du plan, choix d'archi non trivial) → **stoppe** et informe l'utilisateur. Ne pars pas en improvisation silencieuse.
- N'ajoute pas de fonctionnalités hors du plan, même si elles semblent "logiques" — discute-les d'abord.

Avance méthodiquement, pas par grandes envolées.

### 7. Vérifications qualité : lint, typecheck, tests

Une fois l'implémentation faite, lance **dans cet ordre** les vérifications définies par le projet. Saute une étape uniquement si elle n'est clairement pas configurée.

#### 7a. Lint

Identifie la commande de lint dans cet ordre de priorité :

1. **`package.json`** (champ `scripts`) → `npm run lint` / `pnpm lint` / `yarn lint` selon le lockfile détecté
2. **`Makefile`** → cible `lint`
3. **`pyproject.toml`** / **`setup.cfg`** → Python : `ruff check`, `flake8`, `black --check`, etc.
4. **`composer.json`** (PHP) → champ `scripts`
5. **Fichiers de config seuls** (`.eslintrc*`, `.flake8`, `ruff.toml`, `.rubocop.yml`) — en dernier recours, utilise l'outil correspondant directement

#### 7b. Typecheck

Si le projet est typé, lance le typecheck :

- **TypeScript** : `npm run typecheck` / `tsc --noEmit`
- **Python avec types** : `mypy`, `pyright`, ou `pyre` si configuré dans `pyproject.toml` / `mypy.ini`
- **Go, Rust** : le build classique fait le typecheck (`go build ./...`, `cargo check`)

#### 7c. Tests

Lance les tests **ciblés sur la zone modifiée** d'abord, pas toute la suite (gain de temps) :

- **JS/TS** : `npm test -- <pattern>` / `vitest run <fichier>` / `jest <pattern>`
- **Python** : `pytest <chemin>` / `pytest -k <pattern>`
- **Odoo** : `odoo -d <db> -i <module> --test-enable --stop-after-init`
- **Go** : `go test ./<package>/...`

Si les tests ciblés passent et que la zone touchée est sensible, propose à l'utilisateur de lancer la suite complète.

#### Si une vérification échoue

- **Erreurs triviales** (formatage, imports inutilisés, types évidents) → corrige directement
- **Corrections non triviales** (renommer une API, désactiver une règle, changer une signature, casser un test existant) → informe l'utilisateur avant de toucher
- **Tests existants qui cassent** → **stoppe immédiatement**. Un test rouge signale soit un bug introduit, soit un test à mettre à jour intentionnellement. Discute avant de modifier le test.

⚠️ **Hooks pré-commit** : si le projet utilise Husky, lefthook, pre-commit ou équivalent, ces outils tourneront automatiquement au commit. Ne les contourne **jamais** (`--no-verify` interdit) — fais juste passer les vérifs manuellement.

### 8. Validation manuelle — PAUSE OBLIGATOIRE

⚠️ **Ne pas passer outre cette étape sans validation explicite de l'utilisateur.**

Le type de validation dépend de la nature du projet — adapte le message :

- **Projet web / app UI** : "Ouvre l'app dans le navigateur, teste le golden path et 1-2 cas limites du plan."
- **Backend / API REST** : "Voici une commande `curl` pour tester l'endpoint principal : `curl -X POST ...`. Vérifie la réponse et les logs."
- **CLI / outil** : "Lance la commande sur un cas réel et vérifie la sortie."
- **Librairie / module sans UI** : "Les tests automatisés couvrent le comportement, mais vérifie l'API publique (signatures, exports) si tu veux."
- **Module Odoo** : "Mets à jour le module (`-u <module>`) et vérifie le flow dans l'interface (vue, menu, action) + les logs serveur."
- **Cas mixte** : combine les vérifs pertinentes.

Format du message :

> "Le développement est terminé sur la branche `feat/<nom-feature>`.
>
> ✅ Lint : OK
> ✅ Typecheck : OK (ou "N/A — projet non typé")
> ✅ Tests : <N> tests passent
>
> 👉 Validation manuelle : <instruction adaptée au type de projet>
>
> Quand tu es prêt, dis-moi si tout est bon ou s'il y a des corrections à apporter."

Attends la réponse. Si l'utilisateur signale des problèmes → corrige et répète cette étape. Si tout est validé → l'utilisateur décide de la suite (commit, push, PR — pas ton job).

## Ce que ce skill ne fait PAS

- ❌ **Ne commit pas automatiquement** — l'utilisateur choisit le moment et le message
- ❌ **Ne push pas automatiquement**
- ❌ **Ne crée pas de Pull Request automatiquement**
- ❌ **N'ajoute pas de fonctionnalités hors plan** sans en discuter
- ❌ **Ne contourne pas les hooks** (jamais de `--no-verify`)
- ❌ **N'over-engineere pas** : pas d'abstraction prématurée, pas de helper "au cas où"
- ❌ **Ne modifie pas un test existant qui casse** sans en parler d'abord

## Points d'attention

- **Working tree dirty** : toujours diagnostiquer avant `git pull`. Stash, commit ou clarifier avec l'utilisateur.
- **Branche de référence introuvable** : si `git pull origin <branche>` échoue (branche inexistante côté remote), arrête-toi et demande la bonne référence.
- **Plan ambigu** : mieux vaut une clarification rapide qu'une implémentation qu'il faudra défaire.
- **Préfixe de branche** : adapte à la nature de la tâche (`feat/`, `fix/`, `refactor/`, `chore/`, `docs/`, `perf/`).
- **Suivi des étapes** : utilise TaskCreate/TaskUpdate pour rendre la progression visible — c'est utile à toi (rien d'oublié) et à l'utilisateur (transparence).
- **Test rouge surprise** : indicateur fort qu'il faut s'arrêter et comprendre, pas "ajuster" le test pour le faire passer.
