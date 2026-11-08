# Référence technique : spec, logos, génération, vérification

Ce fichier est partagé par la conversation principale (qui génère le diagramme de l'**état actuel**) et par l'agent `archi-expert-senior` (qui génère les diagrammes **cible** ou **nouveaux**). Dossier du skill : `~/.claude/skills/diagramme-architecture/`.

## 1. Logos

Pour **chaque techno nommée** dans un nœud, récupère son logo officiel dans le dossier `logos/` à côté de la spec (ex. `docs/architecture/logos/`). Réutilise un logo déjà présent plutôt que de le retélécharger.

1. **Simple Icons** (SVG, couleur officielle) : `curl -sfL https://cdn.simpleicons.org/<slug> -o logos/<slug>.svg`. Slug = nom en minuscules sans espaces, `.` → `dot`, `+` → `plus` (`nextdotjs`, `nodedotjs`, `postgresql`, `redis`, `fastapi`, `traefikproxy`, `apachekafka`). En cas de doute : `WebSearch "simple icons <techno>"`.
2. **Devicon** si absent : `https://cdn.jsdelivr.net/gh/devicons/devicon/icons/<nom>/<nom>-original.svg`.
3. **Sinon** : `WebSearch "<techno> official logo svg"`, kit presse officiel de l'éditeur ou Wikimedia Commons. Services cloud : icônes d'architecture officielles de l'éditeur.
4. **Vérifie** chaque fichier : il doit commencer par `<svg` / `<?xml`, ou être un vrai PNG/JPEG, pas une page d'erreur HTML (le script le revérifie et ignore les fichiers invalides).
5. **Introuvable** → nœud sans logo, à signaler. Jamais de logo inventé ni approximatif. Simple Icons ne fournit plus les logos AWS.

Les nœuds génériques sans techno précise (« Worker », « Bases & caches ») n'ont pas de logo, sauf si leur runtime est connu (worker Node.js → `nodedotjs`).

## 2. La spec JSON

```json
{
  "title": "Demo Shop — architecture",
  "subtitle": "Next.js · Node · PostgreSQL · RabbitMQ",
  "decisions": ["Le choix + la raison + l'alternative écartée", "..."],
  "evolutions": ["Ce qui viendra plus tard + le signal qui le déclenchera"],
  "nodes": [
    {"id": "web", "label": "Next.js Web", "sublabel": "SSR", "category": "client",    "logo": "logos/nextdotjs.svg"},
    {"id": "lb",  "label": "Nginx",       "category": "gateway",   "logo": "logos/nginx.svg"},
    {"id": "api", "label": "API Node.js", "category": "service",   "logo": "logos/nodedotjs.svg"},
    {"id": "mq",  "label": "RabbitMQ",    "category": "async",     "logo": "logos/rabbitmq.svg"},
    {"id": "db",  "label": "PostgreSQL",  "category": "datastore", "logo": "logos/postgresql.svg"},
    {"id": "pay", "label": "Stripe",      "category": "external",  "logo": "logos/stripe.svg"}
  ],
  "edges": [
    {"from": "web", "to": "lb",  "label": "HTTPS"},
    {"from": "lb",  "to": "api", "label": "REST"},
    {"from": "api", "to": "db",  "label": "SQL"},
    {"from": "api", "to": "mq",  "label": "event"},
    {"from": "api", "to": "pay", "label": "paiement"}
  ],
  "platform": {"label": "Serveur Dokploy · conteneurs Docker", "logo": "logos/dokploy.svg",
               "categories": ["gateway", "service", "async", "datastore"]}
}
```

- **Catégories** (colonnes de gauche à droite) : `client`, `gateway`, `api` (facultative : BFF, gateway GraphQL, SSR — évite des flèches entre nœuds d'une même colonne), `service`, `async`, `datastore`, `external`. Par défaut `async` et `datastore` sont empilées dans la même colonne ; `"columns"` change ce regroupement.
- **Granularité** : un nœud = une unité déployable. Une librairie (ORM, middleware, SDK de logs) n'est pas un nœud, sauf un SDK qui appelle un tiers par le réseau (→ `external`). Le même code lancé en plusieurs processus déployés séparément = plusieurs nœuds.
- **Plateforme** : Dokploy, Kubernetes, AWS, Vercel, un VPS… ne sont pas des nœuds mais un cadre `platform` autour des catégories qu'ils hébergent.
- **Libellés** : `label` de 2-3 mots, détail dans `sublabel` (un libellé « Nom — détail » ou « Nom (détail) » est découpé automatiquement). Étiquettes de flèches de 1-4 mots.
- **Flèches** : celles qui touchent `async` ou `external` sont pointillées automatiquement ; `"dashed": true` force le pointillé ; `"both": true` met une pointe aux deux bouts (échange dans les deux sens sur la même connexion : long polling, WebSocket de chat).
- **Limites** : ~7 nœuds par catégorie, **15 flèches par vue**. Au-delà, plusieurs vues : `spec-<vue>.json`.
- **`decisions` et `evolutions`** sont obligatoires : ce sont eux qui donnent le *pourquoi* aux devs et aux agents IA. Une décision = choix + raison (+ alternative écartée). Une évolution = ce qui viendra + son signal de déclenchement. Pour un état actuel, `decisions` ne contient que des choix **constatés**, et `evolutions` reste vide.
- Chemins de logos **relatifs au fichier spec**.

## 3. Génération

```bash
py ~/.claude/skills/diagramme-architecture/scripts/build_excalidraw.py docs/architecture/spec.json -o docs/architecture/architecture.excalidraw
```

(`python` à la place de `py` hors Windows.) Le script :
- place les catégories en zones colorées, met logo + libellé dans chaque nœud, embarque les logos en base64 (fichier autonome) ;
- choisit l'ordre des nœuds qui minimise les croisements, trace des flèches orthogonales sur des voies distinctes, fait passer par des couloirs au-dessus ou en dessous des zones les flèches qui sautent une colonne, pose les étiquettes sur fond blanc, ajoute une légende ;
- écrit **`ARCHITECTURE.md`** à côté de la spec (`ARCHITECTURE-<vue>.md` pour `spec-<vue>.json`) : briques, hébergement, flux, décisions, évolutions. Seul le bloc `BEGIN GENERATED` / `END GENERATED` est réécrit ; les notes ajoutées à la main sont conservées.

Options : `--open` ouvre le résultat dans VS Code (extension `pomdtr.excalidraw-editor`) ou l'application par défaut ; `--doc-only` met à jour le document sans réécrire le `.excalidraw` (garde les retouches manuelles) ; `--no-doc` ; `--doc <chemin>`.

Avec beaucoup de nœuds, la génération peut prendre 15-20 secondes (recherche de l'ordre optimal) : c'est normal.

## 4. Vérification

```bash
py ~/.claude/skills/diagramme-architecture/scripts/check_layout.py docs/architecture/architecture.excalidraw
```

Attendu : 0 superposition, 0 étiquette masquée, 0 flèche à travers un nœud (sinon code de sortie 1). Quelques croisements (≤ 5) sont acceptables quand des flèches sautent des colonnes. Au-delà : découper en vues, réduire les flèches qui sautent des colonnes (catégorie `api`, regroupement), raccourcir les `sublabel`. Deux essais maximum, puis livrer en signalant le défaut.

Remèdes qui ont marché :
- **Beaucoup de croisements avec 5 nœuds ou plus dans la colonne `service`** qui s'appellent entre eux : répartis-les. Les points d'entrée (BFF, services qui reçoivent les requêtes de la gateway) vont en `api` ; les composants déclenchés par des événements (workers de push, consommateurs) peuvent aller en `async`.
- **Superposition entre deux flèches de colonnes voisines qui se croisent en X** (A en haut → B en bas, C en haut → D en bas, avec B et D sur la même ligne) : limite connue du script, l'ordre des voies ne peut pas l'éviter. Déplace l'un des quatre nœuds dans une autre catégorie (ex. une passerelle de push en `api`), puis régénère.

Si un navigateur est disponible, le rendu réel s'obtient avec une page locale qui charge `@excalidraw/excalidraw@0.17.6` (UMD, avec React 18.2.0) et appelle `ExcalidrawLib.exportToSvg` sur le contenu du fichier.
