---
name: diagramme-architecture
description: Crée un diagramme d'architecture / de design system dans Figma (FigJam) à partir d'une description de projet. Recherche les best practices sur le web et les applique au découpage, puis génère le diagramme via le MCP Figma (generate_diagram, layout architecture). Déclenche ce skill dès que l'utilisateur dit "/diagramme", "fais un diagramme d'architecture", "schéma de mon système", "diagramme de design system", "représente/dessine mon archi dans Figma", ou décrit une stack/un système et veut une représentation visuelle de l'architecture — même s'il ne mentionne pas explicitement Figma.
---

# Diagramme d'architecture

Transforme une description de système en un diagramme d'architecture dans **FigJam**, via le MCP Figma. Le skill fait le travail de fond : chercher les bonnes pratiques pour la stack décrite, traduire l'architecture dans le vocabulaire strict qu'attend l'outil, puis générer.

## Pourquoi ce skill existe

Faire un bon diagramme d'archi demande deux choses que l'on bâcle souvent : **un découpage juste** (les bonnes couches, les composants qui manquent — cache, file d'attente, CDN, load balancer) et **une granularité correcte** (un nœud = une unité déployable indépendamment, pas un module interne). Ce skill impose une étape de recherche des best practices avant de dessiner, et applique les règles strictes du renderer Figma pour éviter un diagramme qui rend mal ou qui ment sur l'architecture réelle.

## Workflow — 4 étapes

### Étape 1 — Comprendre le système

Pars de la description fournie. Si des éléments essentiels manquent, demande-les **groupés en une fois** (ne noie pas l'utilisateur sous les questions) :

- **Le but** du système en une phrase (ce que fait l'appli).
- **La stack** : langages, frameworks, bases de données, services managés, tiers externes.
- **Le niveau de détail voulu** : par défaut, vise le niveau « conteneurs » du modèle C4 (services/bases déployables), pas le détail des modules internes — c'est le plus utile pour un diagramme de design system.

Si le projet est un vrai codebase, explore-le (package.json, docker-compose, routes, config de déploiement) plutôt que de deviner. Une archi extraite du code réel vaut toujours mieux qu'une archi reconstruite de mémoire.

### Étape 2 — Rechercher les best practices et les appliquer

Avant de figer le découpage, utilise `WebSearch` pour le confronter à des architectures de référence **pour la stack décrite**, pas dans l'abstrait. Lis `references/best-practices.md` pour les principes de découpage et les requêtes de recherche à lancer.

Applique ensuite 3-5 recommandations concrètes : ajouter les composants classiques oubliés (cache, message queue, CDN, load balancer), corriger le regroupement, clarifier les flux synchrones vs asynchrones. Dis à l'utilisateur ce que tu as ajouté ou réorganisé, et pourquoi.

### Étape 3 — Traduire en Mermaid selon le vocabulaire Figma

**Avant tout appel à `generate_diagram`, charge le skill Figma correspondant** — c'est obligatoire, pas optionnel :

```
mcp__<figma>__get_figma_skill  uri: "skill://figma/figma-generate-diagram/SKILL.md"
puis                            uri: "skill://figma/figma-generate-diagram/references/architecture.md"
```

Ce guide impose un vocabulaire fermé de sous-graphes (`client`, `gateway`, `service`, `datastore`, `external`, `async`) et des règles strictes (DAG, arêtes autorisées uniquement entre certaines catégories, `flowchart LR` obligatoire). Suis-le à la lettre — c'est lui qui fait autorité sur la syntaxe Mermaid et les contraintes de layout, pas ce fichier.

Deux règles de granularité, apprises en testant ce skill sur un vrai projet, à appliquer **avant** d'écrire le Mermaid :

- **Un nœud = une unité déployable indépendamment.** Une librairie ou un SDK intégré dans un service (ORM, middleware d'auth, middleware de sécurité) n'a **pas** son propre nœud — il reste invisible ou se mentionne dans le libellé d'une arête existante. Exemple : Better Auth monté dans une API Express fait partie du nœud `service` de l'API, pas un nœud séparé.
- **Sauf si ce module fait de vrais appels réseau sortants vers un tiers.** Dans ce cas il devient un nœud `external`, relié au service par une arête pointillée. Exemple : le SDK Arcjet appelle le cloud Arcjet pour ses décisions de rate-limiting → nœud `external`, pas un module invisible.

**Si une relation réelle ne correspond à aucune arête autorisée par le schéma** (ex: un fournisseur de certificats TLS relié à la gateway — aucune ligne `external → gateway` n'existe dans la table), **n'invente pas de contournement** : omets ce nœud et explique pourquoi à l'utilisateur plutôt que de forcer un diagramme structurellement faux.

### Étape 4 — Générer le diagramme

Appelle `generate_diagram` avec :
- `mermaidSyntax` : le Mermaid construit à l'étape 3
- `useArchitectureLayoutCode: "FIGMA_DIAGRAM_2026"`
- `planKey` : récupéré via `whoami` si pas déjà connu (un seul plan → l'utiliser directement ; plusieurs → demander lequel)

L'outil crée son propre fichier FigJam — n'appelle pas `create_new_file` avant.

## Livrer à l'utilisateur

La réponse de l'outil contient `claimFileUrl` (le lien à ouvrir) et `imageUrl` (une miniature). Donne les deux :

- Le lien en markdown, clairement identifié comme à ouvrir dans **le navigateur de l'utilisateur** (il doit déjà être connecté à son compte Figma — ce n'est pas un lien que je peux visiter à sa place).
- La miniature en image markdown pour un aperçu immédiat dans la conversation.

Si des nœuds ont été omis (étape 3), rappelle-le explicitement à ce moment — c'est le meilleur endroit pour que l'utilisateur voie l'écart entre l'archi réelle et ce qui est diagrammé.

## Itérer

Si l'utilisateur veut changer quelque chose sur un diagramme déjà généré :
- **Contenu** (ajouter/retirer un nœud, changer un libellé) → régénère avec `fileKey` pointant vers le fichier existant, pour rester dans le même fichier plutôt que d'en créer un nouveau à chaque itération.
- **Position, police, édition nœud par nœud** → `generate_diagram` ne sait pas faire ça ; oriente l'utilisateur vers l'édition manuelle dans FigJam.
- Après 2 tentatives infructueuses sur le même diagramme, arrête de régénérer à l'aveugle — demande précisément ce qui cloche.

## Ce que ce skill ne fait PAS

- ❌ Il ne génère plus de fichiers Excalidraw ou PowerPoint — le projet a tranché pour Figma/FigJam uniquement après comparaison des trois.
- ❌ Il n'appelle jamais `generate_diagram` sans avoir chargé `figma-generate-diagram` (et `architecture.md`) juste avant.
- ❌ Il ne force pas une relation dans le Mermaid quand elle ne correspond à aucune arête autorisée — il omet et explique.
- ❌ Il ne crée pas de nœud pour une librairie/un module interne qui n'est pas indépendamment déployable.
- ❌ Il n'invente pas de composants qui ne correspondent pas à la stack juste pour « faire riche ».

## Points d'attention

- **Trop de nœuds dans une catégorie** : au-delà de ~7 composants, le diagramme devient illisible — monte d'un cran d'abstraction ou découpe en plusieurs diagrammes.
- **Accès Figma** : vérifie que le compte a bien un accès (siège "Edit", pas seulement "View") avant de promettre un fichier éditable ; `whoami` renvoie le `seat` par plan.
- **Réseau restreint** : la recherche web peut échouer selon l'environnement — continue quand même, ne bloque pas le diagramme dessus.
