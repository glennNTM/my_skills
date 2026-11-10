# Référence : modéliser une API

Repères tirés des guides de référence : [Google AIP](https://google.aip.dev), [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/), [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines). En cas de conflit, ce sont les conventions déjà en place dans le projet qui l'emportent : la cohérence compte plus que la mode.

## Style par frontière
| Besoin | Style |
|---|---|
| API publique, CRUD, clients variés | REST (niveau de maturité 2 : ressources et verbes HTTP) |
| Plusieurs fronts avec des besoins de lecture très différents | GraphQL (ou un BFF par front) |
| Appels internes service à service, forte charge, contrat strict | gRPC |
| Push serveur → client | SSE (sens unique) ou WebSocket (bidirectionnel) |
| Notifier un tiers | Webhooks signés (HMAC) avec retries |
| Découpler des services | Événements sur une file ou un bus (voir Asynchrone) |

## Ressources et nommage
- Des noms au pluriel, pas de verbes : `/orders/{id}/items`. Une imbrication de 2 niveaux au maximum.
- Ressources issues du **domaine**, pas des tables. Identifiants opaques et stables (UUID/ULID), jamais d'auto-incrément exposé.
- Une action qui n'est pas du CRUD : sous-ressource ou méthode personnalisée (`POST /orders/{id}:cancel`, selon le style des AIP).
- Une seule casse pour les champs JSON (`snake_case` ou `camelCase`), dates en RFC 3339 UTC, montants en entiers dans l'unité mineure, avec la devise.

## Conventions transverses (à fixer une fois pour toutes)
- **Auth** : OAuth 2.1 / OIDC pour les utilisateurs, avec des scopes par ressource et action. mTLS ou JWT de service entre services internes. Jamais de secret dans l'URL.
- **Erreurs** : `application/problem+json` (RFC 9457), avec `type`, `title`, `status`, `detail` et un code métier stable. 400 validation · 401 · 403 · 404 · 409 conflit · 422 règle métier · 429 · 5xx.
- **Pagination** : par curseur (`page_size`, `page_token`, `next_page_token`) par défaut. L'offset est réservé aux petits volumes administratifs. Une taille maximale est imposée.
- **Filtres et tri** : paramètres explicites (`?status=paid&sort=-created_at`), documentés et bornés.
- **Idempotence** : en-tête `Idempotency-Key` sur les `POST` qui créent ou paient, avec stockage de la réponse pendant 24 h environ. `PUT` et `DELETE` sont idempotents par nature.
- **Concurrence** : `ETag` + `If-Match` sur les mises à jour concurrentes (réponse 412).
- **Rate limiting** : 429 + `Retry-After` et des en-têtes de quota. Limites par client et par route coûteuse.
- **Opérations longues** : `202 Accepted` + une ressource d'opération à interroger, ou un webhook.
- **Versioning** : on évolue de façon compatible (ajouter des champs optionnels ; ne jamais retirer ni renommer). Une version majeure (`/v2` ou en-tête) seulement pour une rupture, avec une date de dépréciation (`Deprecation`/`Sunset`).
- **Compatibilité** : les clients doivent tolérer les champs inconnus (Zalando : « be conservative in what you send, liberal in what you accept »).

## Asynchrone
- Un événement = un fait passé (`order.paid`), avec `id`, `type`, `occurred_at`, une version de schéma et un payload minimal ou complet (à choisir et à écrire).
- Livraison « au moins une fois » → les consommateurs sont idempotents (dédoublonnage sur `id`).
- Écrire en base et publier sans perdre l'un des deux → pattern **outbox**.

## Gabarit de la table des endpoints
| Méthode | Chemin | Rôle | Auth (scope) | Idempotent |
|---|---|---|---|---|
| POST | `/v1/orders` | Créer une commande | `orders:write` | via `Idempotency-Key` |
