# Référence : choisir la base de données, le SGBD et le BaaS

**Règle d'or :** on choisit à partir des **patterns d'accès** (comment les données sont lues et écrites), des besoins de cohérence et des volumes, pas à partir de la forme apparente des données. Le relationnel pardonne les questions qu'on n'avait pas prévues ; le NoSQL récompense des patterns d'accès connus d'avance.

## 1. Modèle → SGBD

| Modèle | Quand le choisir | SGBD courants | Quand l'éviter |
|---|---|---|---|
| **Relationnel** (défaut) | Transactions ACID, relations, jointures, requêtes imprévues, reporting | PostgreSQL (défaut : JSONB, plein texte, extensions PostGIS, pgvector, TimescaleDB), MySQL/MariaDB, SQLite (embarqué, mono-serveur) | Écritures massives distribuées au-delà d'un gros serveur |
| **Document** | Agrégats imbriqués lus d'un bloc, schéma qui varie, accès par entité | MongoDB, Firestore, Couchbase | Beaucoup de relations croisées et de jointures |
| **Clé-valeur** | Accès par clé connue : cache, sessions, compteurs, rate limiting, files légères | Redis / Valkey, DynamoDB | Requêtes par d'autres champs que la clé |
| **Colonnes larges** | Écritures massives, chemins de requête connus et partitionnables (messages, événements, IoT) | Cassandra, ScyllaDB, Bigtable | Requêtes ad hoc, transactions multi-lignes |
| **Recherche** | Plein texte avancé, facettes, tolérance aux fautes | OpenSearch / Elasticsearch, Meilisearch, Typesense | Source de vérité (c'est un index secondaire) |
| **Séries temporelles** | Métriques, mesures horodatées, rétention, agrégats par fenêtre | TimescaleDB, InfluxDB, ClickHouse | Données métier transactionnelles |
| **Analytique (OLAP)** | Gros scans et agrégats, tableaux de bord | ClickHouse, BigQuery, DuckDB (local) | Petites écritures transactionnelles fréquentes |
| **Graphe** | Parcours de relations profonds et variables (recommandations, fraude, réseau social) | Neo4j, Memgraph | Relations simples sur 1-2 niveaux (le SQL suffit) |
| **Vecteurs** | Recherche sémantique, RAG | pgvector (si PostgreSQL est déjà là), Qdrant, Weaviate | Moins de quelques millions de vecteurs déjà dans Postgres → pgvector suffit |
| **Stockage objet** | Fichiers, médias, exports | S3, R2, GCS, MinIO | Données requêtables |

**Ordre de montée en charge** avant de changer de SGBD : index et requêtes corrigés → plus grosse machine → pooler de connexions → cache → réplicas de lecture → partitionnement → sharding (dernier recours). Voir `deploiement-scalabilite.md`.

**Managé ou auto-hébergé :** une petite équipe sans compétence d'exploitation prend un service managé (sauvegardes, PITR, mises à jour, haute disponibilité). On auto-héberge pour le coût à grande échelle, la souveraineté ou une contrainte d'hébergement (VPS, Dokploy), en assumant sauvegardes et restauration **testées**.

## 2. BaaS : oui, non ou hybride

**Le défaut reste un backend applicatif** (API maison + sa base). Un BaaS fournit base + auth + stockage + temps réel + fonctions, et remplace tout ou partie de ce backend. On ne le retient que si le projet s'y prête : au moins un critère « plutôt oui » et aucun « plutôt non ».

**Plutôt oui** : MVP ou time-to-market prioritaire ; petite équipe sans profil backend ou ops ; besoins essentiellement CRUD + auth + fichiers + temps réel ; app mobile qui a besoin de synchronisation ou de mode hors ligne.

**Plutôt non** : logique métier complexe (workflows, calculs, intégrations nombreuses) qui ne rentre pas dans les abstractions du BaaS ; contraintes de conformité ou de résidence des données que l'offre ne garantit pas ; très gros volume, où la facturation à l'usage dépasse le coût d'un backend ; backend existant qui fonctionne ; besoin fort de portabilité.

**Hybride** (fréquent) : le BaaS pour l'auth, le stockage et la base, plus un service maison pour la logique métier lourde.

**Limiter le lock-in** : préférer un BaaS dont les données restent portables (PostgreSQL standard) ou qui est auto-hébergeable ; isoler les appels au BaaS derrière une couche de service ; plafonds de dépenses et alertes de coût.

| BaaS | Base de données | Points forts | Limites et risques |
|---|---|---|---|
| **Supabase** | PostgreSQL complet | SQL et extensions, Row Level Security, auth, stockage, temps réel, edge functions ; open source et auto-hébergeable ; données portables (`pg_dump`) | L'auto-hébergement a plusieurs composants à opérer ; la sécurité repose sur des politiques RLS correctes |
| **Firebase** | Firestore (documents, NoSQL) ; offre PostgreSQL managée via Cloud SQL (Data Connect / SQL Connect) | Synchronisation temps réel et hors ligne mobile, auth, notifications push, écosystème Google | Propriétaire, non auto-hébergeable ; jointures à faire côté application avec Firestore ; facturation à l'opération et sans plafond par défaut sur le plan à l'usage |
| **Convex** | Base documentaire transactionnelle avec schéma, intégrée au runtime | Backend réactif en TypeScript (requêtes, mutations, actions), temps réel par défaut, typage de bout en bout | Logique couplée à son runtime ; licence FSL (passe en Apache 2.0 au bout de 2 ans ; on ne peut pas monter un service concurrent) ; écosystème plus jeune |
| **Appwrite** | Base gérée par la plateforme (moteur selon la version : à vérifier) | Open source, auto-hébergeable avec les mêmes fonctionnalités que le cloud ; auth, bases, stockage, fonctions, temps réel, messagerie | Scaling manuel en auto-hébergement ; requêtes moins riches que du SQL direct |

Les prix et quotas changent souvent : vérifie-les toujours sur la page officielle et cite-la. Ne les recopie jamais de mémoire.

Sources : [Convex — self-hosting](https://docs.convex.dev/self-hosting), [Appwrite — self-hosting](https://appwrite.io/docs/advanced/self-hosting), [Firebase — SQL Connect / Data Connect](https://firebase.google.com/docs/data-connect), [Supabase docs](https://supabase.com/docs), comparatifs secondaires ([dev.to 2026](https://dev.to/_6638a39c349d7e9c85ee20/best-backend-as-a-service-platforms-2026-supabase-vs-appwrite-vs-convex-vs-firebase-3j7b), [Appwrite — when a custom backend stops being worth it](https://appwrite.io/blog/post/when-custom-backend-stops-being-worth-it), à lire comme des sources d'éditeur).
