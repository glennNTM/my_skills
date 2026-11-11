# API design

Grounded in [Google AIP](https://google.aip.dev), [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) and [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines). When they conflict with conventions already used in the project, the project's conventions win: consistency matters more than fashion.

## 1. Style per boundary
| Need | Style |
|---|---|
| Public API, CRUD, varied clients | REST (maturity level 2: resources + HTTP verbs) |
| Several front-ends with very different read needs | GraphQL, or one BFF per front-end |
| Internal service-to-service, high throughput, strict contract | gRPC |
| Server push to clients | SSE (one-way) or WebSocket (two-way) |
| Notify third parties | Signed webhooks (HMAC) with retries |
| Decouple services | Events on a queue or log (see `fundamentals.md` §5) |

## 2. Resources and naming
- Plural nouns, no verbs: `/orders/{id}/items`. Nest at most two levels.
- Resources come from the **domain**, not from tables. Opaque, stable ids (UUID/ULID); never expose auto-increment ids.
- Non-CRUD actions: a sub-resource or a custom method (`POST /orders/{id}:cancel`, AIP style).
- One casing for JSON fields (`snake_case` or `camelCase`), RFC 3339 UTC timestamps, money as integer minor units + currency.

## 3. Cross-cutting conventions (decide once)
- **Auth**: OAuth 2.1 / OIDC for users, scopes per resource and action; mTLS or service tokens between internal services; never secrets in URLs.
- **Errors**: `application/problem+json` (RFC 9457) with `type`, `title`, `status`, `detail` and a stable business code. 400 validation · 401 · 403 · 404 · 409 conflict · 422 business rule · 429 · 5xx.
- **Pagination**: cursor-based by default (`page_size`, `page_token` → `next_page_token`), with a maximum page size. Offset only for small admin lists.
- **Filtering and sorting**: explicit, documented, bounded parameters (`?status=paid&sort=-created_at`).
- **Idempotency**: `Idempotency-Key` header on `POST`s that create or charge, response stored ~24 h. `PUT`/`DELETE` are idempotent by design.
- **Concurrency**: `ETag` + `If-Match` on concurrent updates (412 on mismatch).
- **Rate limiting**: per client (API key/user/IP) and per expensive route; token bucket or sliding window, enforced at the gateway or in a shared store (Redis); `429` + `Retry-After` + quota headers. Document the limits.
- **Long-running operations**: `202 Accepted` + an operation resource to poll, or a webhook.
- **Versioning**: evolve compatibly (add optional fields; never remove or rename). A new major version (`/v2` or header) only for a breaking change, with `Deprecation`/`Sunset` dates.
- **Compatibility**: clients must tolerate unknown fields ("be conservative in what you send, liberal in what you accept").

## 4. Queries → indexes
Every list endpoint that filters, sorts or paginates needs a matching index. Example: `GET /restaurants/{id}/orders?status=…` sorted by date → index `(restaurant_id, status, created_at DESC)`. The cursor is built from the sorted, indexed columns (+ id as tie-breaker).

## 5. Events and webhooks
- An event is a past fact (`order.paid`) with `id`, `type`, `occurred_at`, a schema version and a payload (thin or full — decide and write it down).
- At-least-once delivery → idempotent consumers (dedupe on `id`).
- Webhooks: HMAC signature, timestamp to prevent replay, retries with backoff, a way to replay missed deliveries.

## 6. Endpoint table template
The table lists one row per endpoint; columns give the HTTP method, the path, what it does, the required auth scope, and whether a retry is safe.

| Method | Path | Purpose | Auth (scope) | Idempotent |
|---|---|---|---|---|
| POST | `/v1/orders` | Create an order | `orders:write` | via `Idempotency-Key` |
| GET | `/v1/orders?status=&page_token=` | List orders | `orders:read` | yes |
