---
name: landing-page-builder
description: Guide la création d'une landing page one-page codée directement dans la codebase du projet, via un wizard en 5 étapes (contexte, objectif, direction visuelle, sections, technique) avant toute écriture de code. Produit du code fonctionnel (un composant par section, tokens de design, SEO de base, WCAG 2.2 AA, pages légales en stub, images libres de droit recherchées et créditées quand une section s'y prête), pas une maquette. Utilise ce skill dès que l'utilisateur dit "/landing-page-builder", "crée une landing page", "page d'atterrissage", "page de vente", "one-page", "site vitrine une page", "page de capture de leads", "page d'inscription à un essai", "hero + pricing + FAQ", même s'il ne dit pas "wizard" ni ne précise la stack.
---

# Landing Page Builder

Guide l'utilisateur, étape par étape, jusqu'à une landing page **codée et fonctionnelle** dans le projet en cours, à la manière du wizard de création de site d'Odoo Website : chaque étape préremplit intelligemment la suivante, et rien n'est écrit avant la validation d'un récapitulatif.

## Pourquoi ce fonctionnement

Une landing page se joue sur un seul objectif et une cible précise. Si on code avant de les avoir figés, on produit une page générique qui convertit mal et qu'il faut refaire. Le wizard force ces décisions tôt, une à la fois, avec des valeurs par défaut pour que l'utilisateur avance vite.

## Périmètre

**Inclus** : une seule page (one-page, sections ancrées) ; composants de section, layout, responsive, styles ; design system local (tokens couleur, typo, spacing) ; textes générés comme première version à valider ; pages légales en stub si absentes, avec liens corrects dans le footer ; SEO de base (title, meta description, Open Graph, HTML sémantique) ; accessibilité WCAG 2.2 AA ; recherche, sélection et intégration d'images libres de droit (Unsplash, Pexels, Pixabay, Openverse…) pour les sections où une image sert la conversion, avec licences vérifiées et crédits tracés.

**Exclus — à annoncer clairement si l'utilisateur le demande, puis proposer de s'en tenir au périmètre** : reste du site (pages intérieures, blog, app) ; backend, base de données, auth, paiement ; intégration CMS ; déploiement et DNS ; rédaction juridique réelle (mentions légales, CGV) ; production d'images, logos, vidéos (on cherche des images libres, on n'en crée pas) ; tracking analytics au-delà d'un emplacement prévu (un commentaire / composant vide `<Analytics />`).

Un formulaire est inclus côté front (champs, labels, validation, états), mais son envoi réel dépend d'un backend exclu : brancher une `action`/handler configurable ou un `TODO` explicite, jamais un faux succès silencieux.

## Règles du wizard

- **Une étape par message.** Ne pose jamais deux étapes à la fois.
- **Options numérotées, défaut recommandé en premier**, marqué « (défaut) ». L'utilisateur peut répondre « défaut » pour accepter et avancer, ou donner un numéro, ou répondre librement.
- **Préremplis** à partir des réponses précédentes et de ce que tu détectes dans la codebase (README, package.json, tokens existants, textes déjà présents). Propose, ne demande pas ce que tu peux déduire.
- Commence par une exploration rapide et silencieuse de la codebase (voir étape 5) pour que les propositions des étapes 1 à 4 soient réalistes. Si le répertoire est vide, dis-le et passe au défaut.
- Affiche une ligne de progression : `Étape 2/5 — Objectif`.
- Réponds dans la langue de l'utilisateur.

## Étape 1 — Contexte

Demande, avec préremplissage si le projet donne des indices :
1. Type de page : (1) SaaS, (2) e-commerce, (3) site institutionnel/vitrine, (4) événement, (5) portfolio, (6) autre. Défaut déduit du projet, sinon SaaS.
2. Nom du produit ou de l'entreprise.
3. En une phrase : ce que ça fait et pour qui.
4. Cible (ICP) en une ligne.

## Étape 2 — Objectif principal

Un seul, il pilote toute la structure : (1) générer des leads, (2) faire connaître la marque, (3) vendre / convertir en client payant, (4) inscrire à un essai gratuit, (5) informer, (6) prendre des rendez-vous. Recommande-en un selon l'étape 1 (SaaS → essai gratuit, vitrine → leads ou rendez-vous, portfolio → notoriété, e-commerce → vendre).

Puis le **libellé du CTA principal** — oriente résultat, pas action (« Obtenir mon audit gratuit » plutôt que « Envoyer »). Propose 3 libellés. Puis l'**action secondaire** éventuelle (ex. « Voir la démo »), défaut : aucune. Si l'utilisateur veut deux objectifs, explique qu'un deuxième objectif dilue le premier et fais-en un lien secondaire.

## Étape 3 — Direction visuelle

**a) Inspiration** : 1 à 3 sites de référence (nom ou lien), ou aucune (défaut). Pour les liens, consulte-les (WebFetch, ou outil navigateur si disponible) et extrais la **structure, le registre visuel et le ton** — jamais le contenu ni le code. Résume ce que tu en retiens en 3 lignes.

**b) Design system**, quatre options :
1. Fournir le sien (palette, typo, ou fichier de tokens). **Détecte d'abord** dans la codebase : `tailwind.config.*`, `@theme` dans le CSS, `tokens.*`, `theme.*`, variables CSS `:root`, `design-tokens.json`. Si trouvé, propose de le réutiliser en priorité, et fais-en l'option par défaut.
2. Fournir un logo : dérive les couleurs (lis l'image si elle est dans le projet).
3. Proposer 3 palettes cohérentes avec le secteur et l'inspiration ; l'utilisateur choisit.
4. Défaut neutre moderne.

**Dans tous les cas, valide les contrastes avant de retenir une palette** : lance `python scripts/contrast.py` (voir `scripts/contrast.py`, usage en tête de fichier) sur les paires texte/fond, bouton/texte du bouton, bordure de champ/fond. Seuils : 4,5:1 texte normal, 3:1 texte large (≥24px, ou ≥18,66px gras) et éléments d'interface. Ajuste une couleur qui échoue plutôt que d'abandonner la palette, et dis à l'utilisateur ce que tu as corrigé. Montre les ratios dans le récapitulatif.

**c) Ton** : (1) sobre et corporate, (2) direct et punchy, (3) chaleureux, (4) technique. Défaut déduit du type de page et de la cible.

## Étape 4 — Sections

Affiche une liste ordonnée **déjà cochée** (`[x]` / `[ ]`), déduite des étapes 1 et 2. L'utilisateur coche, décoche, réordonne, ajoute. Lis `references/sections.md` pour le détail de chaque section, les présélections par objectif et les règles de contenu.

**Socle non négociable** : navbar sticky simple, hero, preuve sociale, CTA final, footer. Si l'utilisateur en décoche un, explique brièvement pourquoi il est requis et remets-le.

Ordre de référence (haute conversion) : navbar → hero → problème/solution → comment ça marche → CTA intermédiaire → démo vidéo → fonctionnalités → storytelling fondateur → tarifs → FAQ → wall of love → CTA final → footer. Les sections spécifiques à un objectif (formulaire, calendrier, produits phares, garanties et livraison, valeurs, réalisations, contact) s'insèrent là où l'objectif le demande (voir `references/sections.md`).

Règle transversale : **répartis des témoignages isolés entre les sections** (hero, après « comment ça marche », près des tarifs…) au lieu de les regrouper en un seul bloc ; le wall of love, s'il est retenu, vient en complément.

## Étape 5 — Technique

Détecte la stack dans la codebase **avant de poser la question**, puis fais confirmer : framework (Next, Astro, Vite/React, Vue, Svelte, HTML pur…), moteur de styles (Tailwind, CSS Modules, styled-components, CSS pur), librairie de composants (shadcn, MUI…), i18n déjà en place, TypeScript ou non, structure de dossiers, pages légales existantes (`/mentions-legales`, `/privacy`, etc.).

- **Ne jamais introduire une dépendance sans demander.** Si une police, une icône ou un composant exige un paquet, propose d'abord l'alternative sans dépendance (police système, SVG inline).
- **Langue** : propose celle de l'utilisateur. Plusieurs langues seulement si l'i18n est déjà en place — alors passe par ses clés de traduction.
- **Contenu** : réel (fourni par l'utilisateur) ou textes générés. Les textes générés sont une **première version à valider** : marque-les clairement (commentaire `TODO(contenu à valider)` et liste dans la checklist finale). N'invente jamais de chiffres, témoignages, logos clients ou noms de clients présentés comme réels : utilise des placeholders évidents (« Témoignage client à venir », « [X] utilisateurs »).
- **Images** : liste d'abord les emplacements où une image servirait la page, d'après les sections retenues et le tableau « Quand une image se justifie » de `references/images-libres.md` (ex. hero d'un site vitrine, fond du CTA final) — et ceux où une image de banque serait trompeuse (témoignages, fondateur, équipe, produits, réalisations). Puis propose : (1) images libres de droit recherchées par toi pour les emplacements adaptés, placeholders ailleurs (défaut si au moins un emplacement s'y prête) ; (2) images fournies par l'utilisateur ; (3) placeholders partout (défaut si aucun emplacement ne s'y prête, ex. SaaS dont toutes les images sont des captures produit). Option 1 : lis `references/images-libres.md` et fais la recherche **avant le récapitulatif** (2 à 3 candidats par emplacement, vérifiés visuellement et côté licence). Les placeholders restent dimensionnés (largeur/hauteur explicites, `aspect-ratio`) ; jamais d'images inventées.
- **Pages légales** : lie celles qui existent ; crée des stubs pour les autres (voir « Légal »).
- Si le projet n'a pas de stack (dossier vide), propose HTML/CSS/JS pur (défaut, zéro dépendance) ou demande quel framework initialiser — ne lance pas d'installation sans accord.

## Récapitulatif avant écriture

Après l'étape 5, présente un récapitulatif compact : contexte, objectif + CTA, direction visuelle (palette avec ratios de contraste, typo, ton), liste finale des sections, stack, langue, images (tableau des candidats : section, lien source, auteur, licence, attribution requise — ou « placeholder »), fichiers qui seront créés/modifiés (y compris le fichier de tokens, les images et le fichier de crédits). **Attends la validation explicite** avant d'écrire du code. Les modifications demandées à ce stade se font sur le récapitulatif, pas dans le code.

## Écriture du code

1. **Tokens de design** dans le fichier de configuration du projet (thème Tailwind / `@theme`, variables CSS `:root`, fichier de tokens existant) : couleurs (+ états hover/focus/disabled), typo (famille, échelle, interlignes), spacing, rayons, ombres. Étends l'existant, n'écrase rien.
2. **Un fichier par section** (une section = un composant) plus **la page qui les assemble**. Props typées si TypeScript. Suis les conventions de nommage et de dossiers du projet.
3. **Contenu centralisé** (un objet/fichier de contenu ou les clés i18n) pour que l'utilisateur remplace les textes sans toucher aux composants.
4. **Images** retenues (si option images libres) : téléchargées dans le dossier d'assets du projet, au bon format et à la bonne taille, référencées dans le contenu centralisé, fichier `CREDITS.md` à côté, attribution affichée quand la licence l'exige (voir `references/images-libres.md`).
5. **Pages légales** (stubs) + **liens du footer**.
6. Vérifie que ça tourne : lance le build/lint/typecheck du projet s'il existe, et si possible le serveur de dev. Vérifie le rendu à **375px** et au-dessus (navigateur si disponible). Dis ce que tu as vraiment vérifié et ce que tu n'as pas pu vérifier.

## Règles de qualité (appliquées sans demander)

**Conversion**
- Un seul objectif, un seul CTA principal, répété (navbar, hero, intermédiaire, final), même libellé, orienté résultat.
- Le H1 porte le résultat désiré pour la cible nommée, pas une catégorie produit (« Publiez vos factures en 2 minutes » plutôt que « Logiciel de facturation »).
- Bénéfices avant fonctionnalités.
- Tarifs visibles dans la page, jamais derrière un formulaire.
- Formulaires courts : le minimum de champs (email seul si possible).

**Technique**
- Mobile-first ; point de rupture testé à 375px, aucun défilement horizontal.
- HTML sémantique (`header`, `nav`, `main`, `section` avec titre, `footer`), **un seul H1**, hiérarchie H2/H3 sans saut.
- Images optimisées (formats modernes si le projet le permet), `loading="lazy"` hors du viewport initial, `width`/`height` explicites.
- **Pas de CLS sur le hero** : dimensions et `aspect-ratio` réservés, pas de police qui fait sauter la mise en page (`font-display: swap` + fallback proche).
- Pas de JS superflu : la page doit rester utilisable sans animation.

**Accessibilité WCAG 2.2 AA** — checklist détaillée dans `references/a11y-seo-legal.md`. Essentiel : contraste 4,5:1 (3:1 pour grand texte et éléments d'interface) ; `alt` descriptif sur images informatives, `alt=""` sur décoratives ; navigation clavier complète, focus visible, ordre de tabulation logique ; cibles tactiles ≥ 24×24px ; `lang` sur `<html>` ; labels associés aux champs ; `prefers-reduced-motion` respecté ; lien d'évitement « Aller au contenu » ; ancres avec `scroll-margin-top` pour que la navbar sticky ne masque pas le titre (WCAG 2.2 « focus not obscured »).

**SEO de base** : `<title>` unique, meta description, balises Open Graph (image OG en placeholder signalé), `canonical`, balisage sémantique. Détail dans `references/a11y-seo-legal.md`.

**Légal et confiance**
- Footer avec liens vers mentions légales, politique de confidentialité, politique de cookies, et CGV si vente en ligne — **en pages distinctes**.
- Copyright avec **l'année courante** (calculée, pas écrite en dur).
- Bandeau cookies **uniquement si des cookies non essentiels existent** ; alors « Refuser » aussi accessible que « Accepter » (même niveau, même visibilité). Sans traceur, pas de bandeau.
- Coordonnées de contact réelles et identification de l'éditeur : demande-les, ne les invente pas ; placeholders marqués sinon.
- **Images de tiers** : uniquement sous licence vérifiée sur la page source au moment de l'utilisation, crédits tracés dans `CREDITS.md`, attribution affichée quand la licence l'exige ; jamais une photo de banque présentée comme un client, un membre de l'équipe ou un produit réel.
- **Rappelle que la rédaction juridique relève d'un professionnel** : les stubs ne sont pas des textes juridiques.

## Sortie finale

1. Le récapitulatif validé (déjà présenté).
2. Le code : un fichier par section + la page d'assemblage.
3. Les tokens dans le fichier de configuration du projet.
4. **Checklist finale** en quatre blocs — Conversion, Accessibilité, SEO, Légal — chaque point marqué ✅ fait / ⚠️ à ta charge. Liste explicitement ce qui reste à l'utilisateur : textes à valider, vrais témoignages et chiffres, images (remplacer les photos de banque par de vraies photos de la marque quand c'est possible) et image OG, crédits photos à conserver, coordonnées et éditeur, rédaction juridique par un professionnel, branchement du formulaire, analytics, déploiement. Ne coche ✅ que ce que tu as réellement vérifié.
