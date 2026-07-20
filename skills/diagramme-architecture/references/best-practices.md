# Best practices de diagramme d'architecture

Deux objectifs : un **découpage juste** et un **rendu lisible**. Applique ces principes avant de traduire en Mermaid (voir `figma-generate-diagram/references/architecture.md` pour la syntaxe et les contraintes exactes de l'outil).

## Principes de découpage

- **Choisir un niveau d'abstraction et s'y tenir.** Modèle C4 : *Context* (le système vu de l'extérieur + acteurs), *Container* (applis/services/bases déployables), *Component* (l'intérieur d'un service). Pour un diagramme de design system, le niveau **Container** est le bon défaut. Ne mélange pas les niveaux dans un même diagramme.
- **Regrouper par responsabilité.** Le vocabulaire Figma impose 6 catégories : `client` → `gateway` (CDN, load balancer, reverse proxy) → `service` (microservices, monolithes, workers) → `datastore` (bases, cache, stockage), avec `external` (tiers) et `async` (files/bus d'événements) en périphérie. Adapte le contenu de chaque catégorie à la stack réelle, mais ne t'écarte pas de ces 6 IDs.
- **Rendre visibles les composants d'infrastructure souvent oubliés** : cache (Redis), file d'attente / bus d'événements (Kafka, SQS, RabbitMQ), CDN, load balancer, reverse proxy, secrets manager, observabilité. S'ils font partie de l'archi, ils doivent apparaître.
- **Limiter la densité.** ~7 composants max par catégorie. Au-delà, monte d'un cran d'abstraction ou découpe en plusieurs diagrammes.
- **Granularité stricte** : un nœud = une unité déployable indépendamment. Voir la section dédiée dans `SKILL.md` (étape 3) — c'est la règle la plus facile à violer par excès de zèle (vouloir montrer chaque librairie).

## Principes de lisibilité

- **`flowchart LR` uniquement** — c'est une contrainte dure de l'outil, pas une préférence.
- **Étiqueter chaque flux inter-catégories** avec le protocole ou la donnée : `REST`, `gRPC`, `SQL`, `event`. Une flèche nue n'apprend rien. 1 à 4 mots max.
- **Distinguer synchrone et asynchrone** : arêtes pleines pour le flux normal, pointillées (`-.->`) pour tout ce qui touche `async` ou `external`. C'est également une contrainte dure du renderer, pas juste une convention visuelle.
- **Couleurs et formes sont auto-assignées** par FigJam selon la catégorie du sous-graphe — inutile d'en discuter avec l'utilisateur ou d'essayer de les piloter via `classDef`/`style`.

## Comment rechercher sur le web (étape 2 du workflow)

Le but est de **confronter le découpage à des architectures de référence réelles** pour la stack décrite, pas de recopier un template générique. Lance 2-4 recherches `WebSearch` ciblées, par exemple :

- `"<stack principale> reference architecture"` (ex: `Next.js Postgres reference architecture`)
- `"<techno> architecture best practices"` (ex: `event-driven microservices best practices`)
- `"<cloud> well-architected <domaine>"` (ex: `AWS well-architected serverless`)
- Le pattern pertinent s'il est nommé : `CQRS`, `event sourcing`, `BFF`, `hexagonal`, `saga`, `outbox`.

Puis **synthétise 3-5 recommandations concrètes** et applique-les au découpage (ajout de composants, réorganisation des catégories, correction des flux). Dis à l'utilisateur ce que tu changes et pourquoi — c'est la valeur ajoutée de cette étape.

## Anti-patterns à éviter

- Le « big ball de mud » : tout au même niveau, sans catégories.
- Des flèches sans étiquette qui partent dans tous les sens.
- Mélanger vue logique (composants) et vue physique (serveurs, zones réseau) dans un seul diagramme.
- Ajouter des composants juste pour « faire riche » alors qu'ils ne sont pas dans la stack.
- Créer un nœud pour chaque librairie utilisée par un service (ORM, middleware, SDK d'auth) — seul le service compte, sauf s'il s'agit d'un vrai appel réseau externe.
- Forcer une relation réelle dans une arête que le schéma n'autorise pas (ex: relier un fournisseur de certificats TLS directement à la gateway). Mieux vaut omettre le nœud et le signaler que produire un diagramme structurellement faux.
