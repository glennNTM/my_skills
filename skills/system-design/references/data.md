# Data — databases, replication, sharding, consistency, caching, search, storage

**Golden rule:** choose from **access patterns** (how data is read and written), consistency needs and volumes — not from the apparent shape of the data. Relational databases forgive questions you did not plan for; NoSQL rewards access patterns known in advance.

## 1. Data model → database
| Model | Choose it when | Common engines | Avoid when |
|---|---|---|---|
| **Relational** (default) | ACID transactions, relations, joins, ad-hoc queries, reporting | PostgreSQL (default: JSONB, full-text, PostGIS, pgvector, TimescaleDB), MySQL/MariaDB, SQLite (embedded, single node) | Massive distributed writes beyond one large server |
| **Document** | Nested aggregates read as a whole, varying schema, per-entity access | MongoDB, Couchbase | Many cross-entity relations and joins |
| **Key-value** | Access by a known key: cache, sessions, counters, rate limits | Redis / Valkey, DynamoDB | Queries on anything other than the key |
| **Wide-column** | Huge write volumes with known, partitionable query paths (messages, events, IoT) | Cassandra, ScyllaDB, Bigtable | Ad-hoc queries, multi-row transactions |
| **Search** | Full-text, relevance, facets, typo tolerance | OpenSearch / Elasticsearch, Meilisearch, Typesense; PostgreSQL full-text for simple needs | As the source of truth (it is a secondary index) |
| **Time series** | Timestamped measurements, retention, window aggregates | TimescaleDB, InfluxDB, ClickHouse | Transactional business data |
| **Analytics (OLAP)** | Large scans and aggregates, dashboards | ClickHouse, BigQuery, DuckDB (local) | Frequent small transactional writes |
| **Graph** | Deep, variable-depth relationship traversals (fraud, recommendations) | Neo4j, Memgraph | 1–2 levels of relations (SQL is enough) |
| **Vector** | Semantic search, RAG | pgvector (if PostgreSQL is already there), Qdrant, Weaviate | Up to a few million vectors already in Postgres → pgvector |
| **Object storage** | Files, media, exports, backups | S3, R2, GCS, MinIO | Queryable data |

**Default: one relational database.** Each extra store is a new thing to operate, back up, secure and keep consistent; it needs an access pattern or a volume the default cannot serve.

**Managed vs self-hosted:** a small team without ops expertise takes a managed service (backups, point-in-time recovery, upgrades, failover). Self-host for cost at large scale, sovereignty, or a hosting constraint (VPS, Dokploy), and own tested backups and restores.

## 2. Scaling the database — in this order
1. Fix queries and **indexes** (check the query plan of the dominant queries).
2. **Vertical** scaling (bigger instance).
3. **Connection pooler** (PgBouncer / RDS Proxy) when app replicas × pool size approaches the connection limit.
4. **Cache** hot reads (section 4).
5. **Read replicas** for read-heavy workloads (section 3).
6. **Partitioning** inside one database (by date or tenant) for very large tables.
7. **Sharding** across databases — last resort.

## 3. Replication
- **Primary–replica (leader–follower)**: writes go to the primary, reads can go to replicas. Asynchronous replication → **replication lag**: a replica can serve stale data. Synchronous replication → no loss on failover but higher write latency.
- Uses: read scaling, high availability (automatic failover to a replica), backups and analytics off the primary.
- Handle lag explicitly: critical reads (just after a write, money, permissions) go to the primary.
- **Multi-primary / multi-region writes** only with a strong reason: conflict resolution is hard.
- State the **RPO** (data loss tolerated) and **RTO** (downtime tolerated) the setup delivers.

## 4. Caching (application/data cache)
- **Cache-aside** (default): read cache → on miss read DB and populate with a **TTL**. Invalidate or update on write.
- **Write-through**: write cache and DB together (fresher, more write latency). **Write-behind**: write cache first, flush later (fast, risk of loss — rarely justified).
- Decide per item: key format, TTL, invalidation trigger, acceptable staleness, behaviour when the cache is down (fall back to the DB, with a limit).
- Risks: **stampede** on a hot key expiry (request coalescing, jittered TTL), unbounded memory (eviction policy, max size), caching per-user data under a shared key.
- Edge/CDN caching of HTTP responses belongs to the infrastructure side (see `infrastructure.md`).

## 5. Sharding
- Splits data across several databases by a **shard key**. Justified only when one primary cannot hold the writes or the data size after steps 1–6.
- Shard key: high cardinality, even distribution, present in almost every query (tenant id, user id). Avoid monotonically increasing keys (hot shard) unless hashed.
- Strategies: **hash** (even spread, range queries hard), **range** (range queries easy, hotspots), **directory/lookup** (flexible, extra component). Consistent hashing eases resharding.
- Costs: cross-shard queries and transactions, rebalancing, operational complexity. Distributed SQL (CockroachDB, YugabyteDB, Vitess, Citus) can absorb part of it — it is still a big step.

## 6. Search
- Start with the database's own full-text search when needs are simple (PostgreSQL `tsvector`, trigram).
- A dedicated engine when you need relevance tuning, facets, typo tolerance, large volumes or many languages.
- It is a **secondary index**: fed from the source of truth (change-data-capture, outbox events or periodic sync), with stated indexing lag and a full reindex procedure.

## 7. Storage (files and blobs)
- Files go to **object storage**, never to the database or the local disk of an app server (it blocks horizontal scaling).
- Uploads: **pre-signed URLs** so clients upload directly; downloads through a CDN with signed URLs when private.
- Define lifecycle rules (expiry, colder storage classes), encryption, and backups/versioning for critical files.

## 8. Schema and lifecycle
- High-level schema: main tables/collections, keys, relations, and the **indexes required by the dominant queries**.
- Migrations compatible with old and new code (*expand → migrate → contract*).
- Retention and deletion of personal data; encryption at rest; least-privilege database users.
