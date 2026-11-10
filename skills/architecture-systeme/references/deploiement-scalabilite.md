# Référence : déploiement et scalabilité

Repères : [AWS Well-Architected — Reliability](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html) (dont [REL05-BP06 stateless](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_stateless.html)), [Google Cloud Architecture Framework — horizontal scalability](https://docs.cloud.google.com/architecture/framework/reliability/horizontal-scalability), [The Twelve-Factor App](https://12factor.net). Règle d'or : **on monte d'un cran seulement quand un signal chiffré le justifie.**

## Estimer la charge (ordres de grandeur)
- RPS moyen ≈ utilisateurs actifs par jour × requêtes par utilisateur et par jour / 86 400. Pic ≈ 2 à 5 × la moyenne, selon la saisonnalité.
- Stockage par an ≈ objets créés par jour × taille moyenne × 365 (+ réplicas et sauvegardes).
- Ratio lecture/écriture → dit si le cache et les réplicas de lecture sont utiles.
- Écris les hypothèses. Un chiffre faux mais déclaré se corrige ; un chiffre implicite, non.

## Vertical ou horizontal
- **Vertical** (machine plus grosse) : simple, pas de changement de code, mais il a un plafond et reste un SPOF. Bon défaut pour la base de données au départ.
- **Horizontal** (plus d'instances) : pour les briques **sans état**. Il faut sortir l'état de l'instance : sessions → Redis ou JWT, fichiers → stockage objet, caches locaux → cache partagé, tâches planifiées → un seul exécuteur (verrou ou leader).
- Un minimum de 2 instances par brique critique, sur 2 zones de disponibilité, dès qu'une indisponibilité coûte cher.

## Load balancing
- **L7** (HTTP : Nginx, Traefik, Envoy, ALB) : routage par chemin ou hôte, terminaison TLS, en-têtes. C'est le défaut pour les API web. **L4** (TCP/UDP : NLB, HAProxy en mode TCP) : protocoles non HTTP, très gros débit.
- Algorithmes : round-robin par défaut. *Least connections* pour des requêtes de durée variable ou des WebSockets. Hash cohérent quand l'affinité de données compte.
- **Health checks** séparés : *liveness* (le processus vit) et *readiness* (prêt à recevoir du trafic). *Connection draining* au déploiement.
- Éviter les sessions collantes. Si elles sont inévitables (WebSocket), le dire et prévoir la reconnexion.
- Devant le LB : CDN pour le statique et le cacheable, WAF et rate limiting à l'edge si l'API est exposée.

## Autoscaling
- Signal : CPU (~60-70 %), latence p95, profondeur de file pour les workers, nombre de connexions. Bornes min et max explicites, cooldown.
- Ce qui scale avec les réplicas peut casser ailleurs : connexions à la base (→ pooler type PgBouncer), quotas d'API tierces, limites de licences.

## Données : l'échelle de montée en charge (dans l'ordre)
1. Index et requêtes corrigés → 2. base plus grosse (vertical) → 3. pooler de connexions → 4. cache (cache-aside + TTL + invalidation à l'écriture) → 5. réplicas de lecture (attention au retard de réplication) → 6. partitionnement par table ou par date → 7. sharding par clé (en dernier recours, coût élevé) ou base spécialisée pour un usage précis.
- Travail lourd hors de la requête : file + workers, avec retries, backoff et file des messages en échec (DLQ).

## Fiabilité
- Timeouts sur tout appel réseau. Retries avec backoff exponentiel et jitter, uniquement sur des opérations idempotentes. Disjoncteur vers les dépendances fragiles.
- Sauvegardes automatiques **testées** (restauration). RPO (perte tolérée) et RTO (durée d'indisponibilité tolérée) écrits.
- Multi-région seulement si le RTO ou la latence mondiale l'exigent : son coût et sa complexité sont élevés.

## Mise en production
- Rolling update par défaut. Blue/green quand il faut pouvoir revenir en arrière instantanément. Canary pour les changements risqués à fort trafic.
- Migrations de base compatibles avec l'ancienne et la nouvelle version (*expand* → déploiement → *contract*).
- Config par variables d'environnement, secrets dans un gestionnaire de secrets, images immuables, CI/CD.

## Observabilité minimale
Logs structurés avec un identifiant de corrélation, métriques RED (rate, errors, duration) par endpoint, traces distribuées dès qu'il y a 3 services ou plus, alertes sur les SLO (pas sur le CPU seul).

## Gabarit de `DEPLOIEMENT.md`
1. **Hypothèses de charge** : calculs et chiffres retenus.
2. **Topologie** : environnements, hébergement, régions/zones, réseau (public/privé), lien vers `architecture-deploiement.excalidraw`.
3. **Par brique** (tableau) : brique · avec ou sans état · scaling (vertical/horizontal, min-max) · signal d'autoscaling · health check.
4. **Load balancing et edge** : LB (L4/L7), algorithme, TLS, CDN, WAF, rate limiting.
5. **Données** : stratégie de montée en charge, cache, sauvegardes, RPO/RTO.
6. **Fiabilité** : SPOF assumés, timeouts/retries, dégradation acceptable.
7. **Mise en production et observabilité.**
8. **Paliers suivants** : quoi ajouter, à partir de quel signal chiffré.
