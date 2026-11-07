---
name: diagramme-architecture
description: Crée un diagramme d'architecture / de design system dans Excalidraw (fichier .excalidraw) à partir d'une description de projet. Recherche les best practices sur le web et les applique au découpage, cherche sur le net le logo officiel de chaque techno mentionnée, puis génère un fichier .excalidraw éditable avec les logos intégrés. Déclenche ce skill dès que l'utilisateur dit "/diagramme", "fais un diagramme d'architecture", "schéma de mon système", "diagramme de design system", "représente/dessine mon archi dans Excalidraw", ou décrit une stack/un système et veut une représentation visuelle de l'architecture — même s'il ne mentionne pas explicitement Excalidraw.
---

# Diagramme d'architecture (Excalidraw)

Transforme une description de système en un diagramme d'architecture **Excalidraw** (`.excalidraw`), avec le **logo officiel de chaque techno** dans son nœud. Le skill fait le travail de fond : chercher les bonnes pratiques pour la stack décrite, récupérer les logos sur le web, puis générer le fichier via le script `scripts/build_excalidraw.py`.

## Pourquoi ce skill existe

Faire un bon diagramme d'archi demande deux choses que l'on bâcle souvent : **un découpage juste** (les bonnes couches, les composants qui manquent — cache, file d'attente, CDN, load balancer) et **une granularité correcte** (un nœud = une unité déployable indépendamment, pas un module interne). Les logos des technos rendent le schéma lisible au premier coup d'œil. Le script garantit un JSON Excalidraw valide et une mise en page propre, sans écrire des centaines de lignes de JSON à la main.

## Workflow — 5 étapes

### Étape 1 — Comprendre le système

Pars de la description fournie. Si des éléments essentiels manquent, demande-les **groupés en une fois** :

- **Le but** du système en une phrase.
- **La stack** : langages, frameworks, bases de données, services managés, tiers externes.
- **Le niveau de détail voulu** : par défaut, niveau « conteneurs » du modèle C4 (services/bases déployables), pas les modules internes.

Si le projet est un vrai codebase, explore-le (package.json, docker-compose, routes, config de déploiement) plutôt que de deviner.

### Étape 2 — Rechercher les best practices et les appliquer

Avant de figer le découpage, utilise `WebSearch` pour le confronter à des architectures de référence **pour la stack décrite**. Lis `references/best-practices.md` pour les principes de découpage et les requêtes à lancer.

Applique 3-5 recommandations concrètes (composants oubliés, regroupement, flux sync vs async). Dis à l'utilisateur ce que tu as ajouté ou réorganisé, et pourquoi.

Puis range chaque nœud dans une des 6 catégories (colonnes de gauche à droite) : `client`, `gateway`, `service`, `async`, `datastore`, `external`.

Règles de granularité :
- **Un nœud = une unité déployable indépendamment.** Une librairie intégrée dans un service (ORM, middleware d'auth, SDK) n'a **pas** son propre nœud. Ex : Better Auth monté dans une API Express fait partie du nœud de l'API.
- **Sauf si ce module fait de vrais appels réseau vers un tiers** → nœud `external`. Ex : le SDK Arcjet appelle le cloud Arcjet → nœud `external`.

### Étape 3 — Chercher les logos des technos sur le net

Pour **chaque techno nommée** dans un nœud (Next.js, PostgreSQL, Redis, Nginx, Stripe, AWS S3…), récupère son logo officiel. Travaille dans un dossier dédié, ex. `docs/architecture/logos/`.

1. **Simple Icons** (logos de marque en SVG, couleur officielle) : `curl -sfL https://cdn.simpleicons.org/<slug> -o logos/<slug>.svg`. Le slug est le nom en minuscules sans espaces, avec `.` → `dot`, `+` → `plus` (ex. `nextdotjs`, `nodedotjs`, `postgresql`, `redis`, `rabbitmq`, `stripe`). En cas de doute sur le slug, `WebSearch "simple icons <techno>"`.
2. **Devicon** si absent de Simple Icons : `https://cdn.jsdelivr.net/gh/devicons/devicon/icons/<nom>/<nom>-original.svg`.
3. **Sinon, `WebSearch "<techno> official logo svg"`** et prends le logo du kit presse / brand assets officiel de l'éditeur (ou Wikimedia Commons). Pour les services cloud (AWS, GCP, Azure), cherche l'icône officielle du service dans les « architecture icons » de l'éditeur.
4. **Vérifie** chaque fichier téléchargé : il doit commencer par `<svg` / `<?xml` (SVG) ou être un PNG/JPEG réel — pas une page HTML d'erreur. Le script le revérifie et ignore les fichiers invalides.
5. **Introuvable** → laisse le nœud sans logo et signale-le à l'utilisateur. N'invente pas de logo et n'en dessine pas un approximatif.

Les nœuds génériques sans techno précise (« Worker », « Admin ») n'ont pas besoin de logo, sauf si leur runtime est connu (ex. worker Node.js → logo Node.js).

### Étape 4 — Écrire la spec et générer le `.excalidraw`

Écris une spec JSON (ex. `docs/architecture/spec.json`) :

```json
{
  "title": "Demo Shop — architecture",
  "nodes": [
    {"id": "web",   "label": "Next.js Web", "category": "client",    "logo": "logos/nextdotjs.svg"},
    {"id": "lb",    "label": "Nginx",       "category": "gateway",   "logo": "logos/nginx.svg"},
    {"id": "api",   "label": "API Node.js", "category": "service",   "logo": "logos/nodedotjs.svg"},
    {"id": "mq",    "label": "RabbitMQ",    "category": "async",     "logo": "logos/rabbitmq.svg"},
    {"id": "db",    "label": "PostgreSQL",  "category": "datastore", "logo": "logos/postgresql.svg"},
    {"id": "pay",   "label": "Stripe",      "category": "external",  "logo": "logos/stripe.svg"}
  ],
  "edges": [
    {"from": "web", "to": "lb",  "label": "HTTPS"},
    {"from": "lb",  "to": "api", "label": "REST"},
    {"from": "api", "to": "db",  "label": "SQL"},
    {"from": "api", "to": "mq",  "label": "event"},
    {"from": "api", "to": "pay", "label": "paiement"}
  ]
}
```

- Chemins de logos **relatifs au fichier spec**.
- Chaque arête a un libellé court (1-4 mots : protocole ou donnée).
- Les arêtes touchant `async` ou `external` sont automatiquement pointillées ; `"dashed": true` force le pointillé ailleurs.

Puis génère :

```bash
python <dossier-du-skill>/scripts/build_excalidraw.py docs/architecture/spec.json -o docs/architecture/architecture.excalidraw
```

(Sous Windows, si `python` n'existe pas, utiliser `py`.) Le script place chaque catégorie dans une zone colorée, met logo + libellé dans chaque nœud (groupés), relie les nœuds par des flèches liées avec étiquette, et embarque les logos en base64 dans le fichier — il est donc autonome.

### Étape 5 — Livrer à l'utilisateur

Donne :
- Le **chemin du fichier** `.excalidraw` généré.
- Comment l'ouvrir : glisser-déposer le fichier sur **https://excalidraw.com** (ou menu ☰ → Ouvrir), ou l'ouvrir dans VS Code avec l'extension **Excalidraw** (`pomdtr.excalidraw-editor`). Tout reste éditable : déplacer, recolorer, ajouter des nœuds.
- La liste des **logos utilisés et leur source**, et ceux **introuvables**.
- Les nœuds ou relations omis, s'il y en a, avec la raison.

## Itérer

- **Contenu** (ajouter/retirer un nœud, changer un libellé, une arête) → modifie `spec.json` et relance le script. Préviens que ça écrase les retouches manuelles faites dans Excalidraw ; si l'utilisateur a déjà retouché le fichier à la main, propose plutôt d'écrire dans un nouveau fichier.
- **Position fine, styles, annotations** → à faire directement dans Excalidraw.
- Après 2 tentatives infructueuses sur le même diagramme, arrête de régénérer à l'aveugle — demande précisément ce qui cloche.

## Ce que ce skill ne fait PAS

- ❌ Il n'utilise plus Figma/FigJam — le diagramme se fait dans Excalidraw.
- ❌ Il n'invente pas de logo et ne dessine pas de logo approximatif — logo officiel trouvé sur le web ou rien.
- ❌ Il ne crée pas de nœud pour une librairie/un module interne qui n'est pas indépendamment déployable.
- ❌ Il n'invente pas de composants qui ne correspondent pas à la stack juste pour « faire riche ».
- ❌ Il n'écrit pas le JSON Excalidraw à la main — il passe par `scripts/build_excalidraw.py`.

## Points d'attention

- **Trop de nœuds dans une catégorie** : au-delà de ~7, le diagramme devient illisible — monte d'un cran d'abstraction ou découpe en plusieurs diagrammes.
- **Logos de marque** : utilisés à titre d'identification de la techno, sans les modifier (couleurs, proportions).
- **Réseau restreint** : si la recherche web ou le téléchargement des logos échoue, génère quand même le diagramme sans logos et dis-le, ne bloque pas dessus.
