# Fundamentals — requirements, estimates, latency, service boundaries, messaging, consistency

## 1. Requirements first
- **Functional**: what the system does (the 3–7 core use cases).
- **Non-functional**: scale (DAU, peak), latency targets (p95/p99), availability (SLO, e.g. 99.9 % ≈ 43 min/month of downtime), consistency needs, durability, security and compliance, cost, team size and skills, hosting constraints.
- Write every number down. A wrong number that is stated can be corrected; an implicit one cannot.

## 2. Back-of-the-envelope estimates
| Quantity | Formula |
|---|---|
| Average RPS | DAU × requests per user per day / 86 400 |
| Peak RPS | average × 2–5 (seasonality, launches) — state the factor |
| Storage per year | new objects per day × average size × 365 (× replicas, + backups) |
| Bandwidth | peak RPS × average response size |
| Read/write ratio | tells whether caching and read replicas will pay off |

Rounding is fine: the goal is the order of magnitude that decides the design (1 server vs 10 vs 1 000).

## 3. Latency budget
Reference orders of magnitude (approximate): memory access ~100 ns · SSD random read ~100 µs · round trip in the same datacenter ~0.5 ms · Redis GET over the network ~1 ms · simple indexed SQL query ~1–5 ms · cross-continent round trip ~100–150 ms.
- Split the p95 target across the hops of the critical path (edge → gateway → service → data → back). Each synchronous hop and each sequential call eats the budget.
- Levers: fewer sequential calls (parallelise, batch), cache, move work off the request path (queue), move data closer (CDN, region).

## 4. Service boundaries: monolith or microservices
- **Default: a modular monolith** (one deployable, clear internal modules). It is cheaper to build, test, deploy and debug.
- Split a service out when there is a concrete reason: independent scaling needs that differ by an order of magnitude, a different reliability or security level, a separate team that must deploy independently, or a different runtime. Rough signal: several teams of ~6–8 people blocking each other.
- Every network boundary adds latency, partial failure, versioning and observability cost. A service per entity ("user-service", "order-service" for a 3-person team) is an anti-pattern.

## 5. Synchronous vs asynchronous
- **Synchronous** (HTTP/gRPC): the caller needs the answer to continue. Set a timeout on every call.
- **Asynchronous** (queue or event bus): the work can happen later, is slow, must survive failures, or must fan out to several consumers.
- **Message queues** (point-to-point work: RabbitMQ, SQS, Redis streams, BullMQ/Celery) vs **event logs** (replayable streams, many consumers, ordering per partition: Kafka, Redpanda, Kinesis). Default to a simple queue; a log is justified by replay, high throughput, or many independent consumers.
- Delivery is **at-least-once** in practice: consumers must be **idempotent** (dedupe on a message id). Use **retries with backoff**, a **dead-letter queue**, and alerting on queue depth/age.
- Writing to the database *and* publishing an event without losing one of them → **transactional outbox**.
- Ordering is only guaranteed per queue/partition; design for it explicitly when it matters.

## 6. Consistency
- **Strong consistency**: reads see the latest write. Needed for money, stock, uniqueness, permissions.
- **Eventual consistency**: replicas converge later. Fine for feeds, counters, search indexes, analytics. State the acceptable staleness ("search results may lag by ≤ 5 s").
- **CAP / PACELC**: during a network partition you choose availability or consistency; otherwise you trade latency for consistency. Say which side each data flow is on.
- Across services there is no shared transaction: use a **saga** (sequence of local transactions + compensations) or keep the invariant inside one service/database.
- Read-your-own-writes after async replication: route the user's reads to the primary for a short window, or use version checks.
