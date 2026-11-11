# Infrastructure — load balancing, CDN, scalability, latency, reliability, deployment, observability

Grounded in [AWS Well-Architected — Reliability](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html) (incl. [REL05-BP06 stateless](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_stateless.html)), [Google Cloud Architecture Framework — horizontal scalability](https://docs.cloud.google.com/architecture/framework/reliability/horizontal-scalability) and [The Twelve-Factor App](https://12factor.net). Golden rule: **move up a step only when a measured signal justifies it.**

## 1. Vertical vs horizontal scaling
- **Vertical** (bigger machine): simple, no code change; has a ceiling and stays a single point of failure. A fine default for the database at first.
- **Horizontal** (more instances): for **stateless** components. Move state out of the instance first: sessions → Redis or signed tokens; files → object storage; local caches → shared cache; scheduled jobs → a single runner (lock or leader election).
- At least 2 instances per critical component, across 2 availability zones, as soon as downtime is expensive.

## 2. Load balancing
- **L7** (HTTP: Nginx, Traefik, Envoy, HAProxy HTTP, cloud ALB): path/host routing, TLS termination, headers. Default for web APIs. **L4** (TCP/UDP: NLB, HAProxy TCP): non-HTTP protocols, very high throughput.
- Algorithms: round-robin by default; least-connections for variable request durations and WebSockets; consistent hashing when data affinity matters.
- **Health checks**: separate *liveness* (process alive) and *readiness* (ready for traffic). **Connection draining** on deploy.
- Avoid sticky sessions; if unavoidable (WebSockets), say so and design reconnection.
- The load balancer itself must not be a SPOF (managed LB, or a redundant pair).

## 3. Edge: CDN, WAF, rate limiting
- **CDN** for static assets and cacheable responses: `Cache-Control`, `ETag`, versioned asset URLs, explicit purge strategy. It cuts latency for distant users and load on the origin.
- Cache only what is safe to share (never per-user responses without proper `Vary`/private headers).
- WAF and rate limiting at the edge when the API is public; per-client limits at the gateway (see `api-design.md`).

## 4. Autoscaling
- Signals: CPU (~60–70 %), p95 latency, queue depth/age for workers, connection count. Explicit min/max bounds and cooldown.
- What scales with replicas can break elsewhere: database connections (→ pooler), third-party API quotas, licences.
- Workers scale on **queue depth**, not CPU.

## 5. Latency in production
- Measure p50/p95/p99, not averages. Track the latency budget defined in `fundamentals.md` §3 per hop.
- Levers by cost: indexes and query fixes → cache → fewer sequential calls → async processing → CDN → regional deployment.
- Multi-region only if global latency or the RTO requires it: data replication and consistency get much harder.

## 6. Reliability
- Timeouts on every network call. Retries with exponential backoff and jitter, only on idempotent operations. Circuit breaker towards fragile dependencies. Bulkheads (separate pools) so one slow dependency cannot exhaust everything.
- Graceful degradation: decide what still works when the cache, the search engine or a third party is down.
- Backups automated **and restore-tested**. State RPO and RTO.
- List every SPOF: removed, or accepted in writing with its RTO.

## 7. Deployment
- Rolling update by default; blue/green when instant rollback is needed; canary for risky changes at high traffic.
- Database migrations compatible with old and new code (expand → migrate → contract).
- Configuration via environment variables, secrets in a secret manager, immutable images, CI/CD pipeline, infrastructure as code when there is more than one environment.

## 8. Observability
- **Logs**: structured (JSON), with a correlation/trace id, no secrets or personal data.
- **Metrics**: RED per endpoint (rate, errors, duration), USE per resource (utilisation, saturation, errors), queue depth/age, cache hit ratio, replication lag.
- **Traces**: distributed tracing (OpenTelemetry) as soon as a request crosses 3+ components.
- **Alerts** on SLO burn (user-visible symptoms), not on CPU alone. A dashboard per critical flow.

## 9. `INFRASTRUCTURE.md` template
1. **Load assumptions**: calculations and retained numbers.
2. **Topology**: environments, hosting, regions/zones, public/private network; link to the infrastructure diagram.
3. **Per component** (table, one row per component; columns: stateful or stateless, scaling mode, min–max instances, autoscaling signal, health check).
4. **Load balancing and edge**: LB type (L4/L7), algorithm, TLS, CDN, WAF, rate limiting.
5. **Latency**: budget per hop of the critical path, main levers.
6. **Reliability**: SPOFs removed or accepted, timeouts/retries, degraded modes, RPO/RTO.
7. **Deployment** and **observability**.
8. **Next steps**: what to add, at which measured signal.
