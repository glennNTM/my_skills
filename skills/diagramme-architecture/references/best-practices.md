# Best practices de diagramme d'architecture

Deux objectifs : un **découpage juste** et un **rendu lisible**. Applique ces principes avant d'écrire la spec JSON passée à `scripts/build_excalidraw.py`.

## Principes de découpage

- **Choisir un niveau d'abstraction et s'y tenir.** Modèle C4 : *Context* (le système vu de l'extérieur + acteurs), *Container* (applis/services/bases déployables), *Component* (l'intérieur d'un service). Pour un diagramme de design system, le niveau **Container** est le bon défaut. Ne mélange pas les niveaux dans un même diagramme.
- **Regrouper par responsabilité.** Le script attend 6 catégories, rendues en colonnes de gauche à droite : `client` → `gateway` (CDN, load balancer, reverse proxy) → `service` (microservices, monolithes, workers) → `async` (files/bus d'événements) → `datastore` (bases, cache, stockage) → `external` (tiers). Adapte le contenu de chaque catégorie à la stack réelle, mais ne t'écarte pas de ces 6 IDs.
- **Rendre visibles les composants d'infrastructure souvent oubliés** : cache (Redis), file d'attente / bus d'événements (Kafka, SQS, RabbitMQ), CDN, load balancer, reverse proxy, secrets manager, observabilité. S'ils font partie de l'archi, ils doivent apparaître.
- **Limiter la densité.** ~7 composants max par catégorie. Au-delà, monte d'un cran d'abstraction ou découpe en plusieurs diagrammes.
- **Granularité stricte** : un nœud = une unité déployable indépendamment. Voir la section dédiée dans `SKILL.md` (étape 3) — c'est la règle la plus facile à violer par excès de zèle (vouloir montrer chaque librairie).

## Principes de lisibilité

- **Lecture de gauche à droite** : le flux principal part du client et va vers les données. Évite les arêtes qui reviennent vers la gauche quand une autre formulation est possible (ex. `worker` consomme depuis `async` : l'arête part de la file vers le worker).
- **Un logo officiel par techno** : chaque nœud qui correspond à une techno nommée porte son logo (Simple Icons, devicon, ou kit presse officiel). Les logos accélèrent la lecture ; un logo faux ou approximatif fait plus de mal que pas de logo.
- **Étiqueter chaque flux inter-catégories** avec le protocole ou la donnée : `REST`, `gRPC`, `SQL`, `event`. Une flèche nue n'apprend rien. 1 à 4 mots max.
- **Distinguer synchrone et asynchrone** : arêtes pleines pour le flux normal, pointillées pour tout ce qui touche `async` ou `external` (le script le fait automatiquement ; `"dashed": true` pour forcer).
- **Couleurs par catégorie** (assignées par le script, retouchables ensuite dans Excalidraw) : client bleu, gateway violet, service vert, async orange, datastore jaune, external gris.

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
- Mettre un logo approximatif ou d'une autre techno « qui ressemble » faute d'avoir trouvé le bon.
