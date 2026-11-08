---
name: diagramme-architecture
description: Crée un diagramme d'architecture / de system design dans Excalidraw (fichier .excalidraw + ARCHITECTURE.md) avec les logos officiels des technos. Trois modes, chacun orchestré avec des agents spécialisés — (1) dans une codebase, il scanne le projet et dessine l'état actuel, puis propose une architecture cible améliorée ; (2) pour un produit existant (Twitch, Spotify…), il recherche sa stack réelle sur le web ; (3) à partir d'une description, il conçoit l'architecture en s'appuyant sur les bonnes pratiques. Déclenche ce skill dès que l'utilisateur dit "/diagramme", "fais un diagramme d'architecture", "system design de…", "schéma de mon système", "dessine l'archi de ce projet / de cette codebase", "architecture de <produit>", ou décrit une stack et veut une représentation visuelle — même s'il ne mentionne pas Excalidraw.
---

# Diagramme d'architecture (Excalidraw) — orchestrateur

Ce skill transforme un système (une codebase, un produit existant ou une description) en un **diagramme Excalidraw** éditable avec les **logos officiels** des technos, plus un **`ARCHITECTURE.md`** lisible par les devs et les agents IA (briques, flux, décisions, évolutions).

Le travail est réparti entre **4 agents spécialisés** (définis dans `~/.claude/agents/`) et la conversation principale, qui les orchestre et parle à l'utilisateur :

| Agent (`subagent_type`) | Rôle |
|---|---|
| `archi-explorateur-code` | Lit la codebase en lecture seule ; rend l'inventaire de l'existant, chaque élément avec sa preuve `fichier:ligne`, et une spec « état actuel » |
| `archi-chercheur-produit` | Recherche sur le web la stack réelle d'un produit existant, avec sources et niveau de confiance |
| `archi-chercheur-bonnes-pratiques` | Recherche les architectures de référence et rend des recommandations adaptées à l'échelle, priorisées et sourcées |
| `archi-expert-senior` | Expert senior en system design : conçoit l'architecture cible ou nouvelle, écrit la spec, génère et vérifie le diagramme |

La référence technique commune (format de la spec, logos, script, vérification) est dans **`references/spec-et-generation.md`** : lis-la avant de générer toi-même un diagramme. Les principes de découpage sont dans `references/best-practices.md`.

**Les agents ne peuvent ni se lancer entre eux ni parler à l'utilisateur** : c'est toi qui les lances (outil Agent, avec le `subagent_type` ci-dessus), qui leur transmets le contexte (chemins, contraintes, rapports des autres agents) et qui poses les questions. Si un agent n'est pas disponible dans la session, lis son fichier dans `~/.claude/agents/<nom>.md` et applique ses instructions toi-même.

## Étape 0 — Choisir le mode

| Situation | Mode |
|---|---|
| L'utilisateur parle de « ce projet », « cette codebase », « mon API », ou le dossier courant contient du code (manifeste de dépendances, `docker-compose`, sources) | **A. Codebase** |
| Il nomme un produit existant qui n'est pas le sien (« architecture de Twitch ») | **B. Produit existant** |
| Il décrit un système à concevoir (« une app qui… avec FastAPI, Redis… ») | **C. Conception** |

En cas de doute (par ex. une description fournie *dans* une codebase), demande-le en une question.

## Mode A — Codebase : l'existant d'abord, la cible ensuite

1. **Explorer.** Lance `archi-explorateur-code` avec le chemin du projet (et le sous-dossier si c'est un monorepo ou si l'utilisateur vise un service précis).
2. **Dessiner l'état actuel.** Toi-même, à partir de la spec brouillon de l'explorateur :
   - écris `docs/architecture/spec.json` (relis les catégories et la granularité ; `decisions` = choix **constatés** avec leur preuve, `evolutions` vide) ;
   - récupère les logos dans `docs/architecture/logos/` ;
   - génère `architecture.excalidraw` + `ARCHITECTURE.md`, vérifie avec `check_layout.py`, ouvre avec `--open`.
   - **N'ajoute rien qui n'est pas dans le code.** Les incertitudes de l'explorateur restent des incertitudes : signale-les.
3. **Présenter et demander.** Montre l'état actuel en quelques lignes (briques, flux principaux, incertitudes), puis demande avec AskUserQuestion :
   - s'il veut des **suggestions d'amélioration** (oui / non) ;
   - si oui, ses **contraintes** dans la même série de questions : échelle visée (utilisateurs, trafic), taille de l'équipe, budget / hébergement, priorités (coût, fiabilité, temps réel, simplicité).
   S'il répond non, livre (étape « Livrer ») et arrête-toi là.
4. **Rechercher les bonnes pratiques.** Lance `archi-chercheur-bonnes-pratiques` avec : les chemins de `spec.json` et `ARCHITECTURE.md`, le résumé de l'explorateur, les contraintes de l'utilisateur.
5. **Concevoir la cible.** Lance `archi-expert-senior` en **mode amélioration** avec : les chemins de l'état actuel, le rapport de bonnes pratiques complet, les contraintes, le dossier `docs/architecture/`. Il écrit `spec-cible.json` → `architecture-cible.excalidraw` + `ARCHITECTURE-cible.md`, sans toucher à l'état actuel.
6. **Présenter la cible** : ce qui change (ajouts, retraits, modifications, avec leurs raisons), ce qui est reporté à plus tard, les questions ouvertes de l'expert. Ouvre `architecture-cible.excalidraw` (`code <fichier>`).

## Mode B — Produit existant

1. Lance `archi-chercheur-produit` avec le produit et l'angle demandé (« l'app mobile », « la vidéo »…).
2. Dessine toi-même le résultat à partir de sa ou ses specs, dans un dossier dédié (ex. `~/<produit>-architecture/`, ou là où l'utilisateur le demande) : logos, génération, `check_layout.py`, `--open`. Une vue par spec si le chercheur en propose plusieurs.
3. Livre en distinguant ce qui est **officiel**, **secondaire** et **non vérifié**, avec les sources en liens.

## Mode C — Conception d'un nouveau système

1. Si l'essentiel manque, demande-le **en une fois** : le but, la stack imposée, l'échelle visée, l'hébergement.
2. Lance `archi-chercheur-bonnes-pratiques` avec la description et les contraintes.
3. Lance `archi-expert-senior` en **mode conception** avec la description, les contraintes, le rapport de bonnes pratiques et le dossier cible (`docs/architecture/` du projet, ou un dossier dédié).
4. Présente les choix structurants et les questions ouvertes ; ouvre le diagramme.

## Livrer (tous les modes)

- Les chemins du ou des `.excalidraw` et `ARCHITECTURE*.md`, et le diagramme **ouvert dans VS Code** (`--open` ou `code <fichier>`). Si l'extension `pomdtr.excalidraw-editor` n'est pas installée, **propose** de l'installer. Autre option : glisser le fichier sur excalidraw.com (rien n'est envoyé sur leurs serveurs).
- Le résultat de `check_layout.py`.
- Les logos utilisés et ceux introuvables ; les nœuds ou flux omis et pourquoi.
- Si le projet a un `CLAUDE.md` ou un `AGENTS.md`, ajoute une ligne qui pointe vers `docs/architecture/ARCHITECTURE.md` (et la cible s'il y en a une). S'il n'en a pas, **propose** d'en créer un minimal ; n'en crée pas sans accord.

## Itérer

- **Contenu** (nœud, libellé, flux, décision) → modifie la spec et relance le script. Préviens que ça écrase les retouches manuelles du `.excalidraw` ; si l'utilisateur en a fait, utilise `--doc-only` pour ne mettre à jour que le document, ou écris dans un nouveau fichier.
- **Position fine, couleurs, annotations** → directement dans Excalidraw.
- **Le code a changé** (mode A) → relance l'explorateur et régénère l'état actuel ; la cible reste un fichier séparé.
- Après 2 tentatives infructueuses sur le même diagramme, arrête de régénérer à l'aveugle : demande précisément ce qui cloche.

## Ce que ce skill ne fait PAS

- ❌ Il ne mélange jamais l'état actuel et la cible dans le même fichier : l'existant ne montre que ce qui est dans le code.
- ❌ Il n'invente ni composant, ni techno, ni logo ; ce qui n'est pas vérifié est signalé.
- ❌ Il ne crée pas de nœud pour une librairie interne non déployable.
- ❌ Il n'écrit pas le JSON Excalidraw à la main : il passe par `scripts/build_excalidraw.py`.
- ❌ Il ne lit jamais la valeur des secrets d'un projet (`.env`, clés) : seulement les noms de variables.
