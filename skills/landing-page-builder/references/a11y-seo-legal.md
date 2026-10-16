# Accessibilité, SEO, Légal — référence

À lire avant d'écrire le code et avant de dresser la checklist finale.

## Sommaire
- Accessibilité WCAG 2.2 AA
- SEO de base
- Légal : pages et stubs
- Cookies

## Accessibilité WCAG 2.2 AA

**Structure**
- `<html lang="…">` correspondant à la langue de la page ; `lang` sur les passages dans une autre langue.
- Landmarks : `header`, `nav` (avec `aria-label` s'il y en a plusieurs), `main` (un seul), `footer`.
- Un seul `<h1>` (le hero). Sections avec un titre H2, sous-titres H3, sans saut de niveau.
- Lien d'évitement « Aller au contenu » en tout premier élément focusable.
- Chaque section ancrée : `id` + `scroll-margin-top` ≥ hauteur de la navbar sticky (WCAG 2.4.11 : le focus ne doit pas être masqué par la navbar).

**Couleurs et contraste** (SC 1.4.3, 1.4.11)
- Texte normal ≥ 4,5:1 ; grand texte (≥24px, ou ≥18,66px gras) ≥ 3:1 ; éléments d'interface (bordure de champ, icône porteuse de sens, état focus) ≥ 3:1 contre leur fond adjacent.
- Vérifie aussi : texte sur images/dégradés (pire cas), texte du bouton sur son fond, états hover/disabled, placeholders de champ, liens dans le texte courant (distincts autrement que par la couleur : soulignement).
- Ne jamais transmettre une information par la couleur seule (SC 1.4.1).
- Outil : `python scripts/contrast.py "#fff" "#1a1a1a"` (voir le script).

**Images et médias**
- Informative : `alt` descriptif de la fonction/du contenu. Décorative : `alt=""`. Logo-lien : `alt` = nom de l'entreprise (ou destination).
- SVG décoratif : `aria-hidden="true"`, `focusable="false"`. Icône-bouton : nom accessible (`aria-label`).
- Vidéo : sous-titres/transcription à prévoir ; pas d'autoplay avec son ; contrôles clavier.
- Texte superposé à une photo : voile (overlay) dont l'opacité est réglée pour que le texte atteigne 4,5:1 contre la zone la plus défavorable ; crédit d'image (`<figcaption>` ou footer) lisible et contrasté lui aussi.

**Clavier et focus** (SC 2.1.1, 2.4.3, 2.4.7, 2.4.11, 2.5.8)
- Tout est atteignable et actionnable au clavier ; ordre de tabulation = ordre visuel ; pas de `tabindex` positif.
- Focus **toujours visible**, contraste ≥ 3:1 (`:focus-visible` avec outline épais, ne jamais `outline: none` sans remplacement).
- Cibles tactiles ≥ 24×24 CSS px (SC 2.5.8), idéalement 44×44 pour les CTA et le menu mobile.
- Menu mobile et accordéons : `button` avec `aria-expanded` et `aria-controls`, `Échap` ferme le menu, pas de piège clavier.

**Formulaires** (SC 1.3.1, 3.3.x, 3.3.7, 3.3.8)
- Chaque champ : `<label for>` visible (le placeholder ne remplace pas le label), `autocomplete` pertinent, `type` adapté (`email`, `tel`).
- Erreurs : message textuel associé via `aria-describedby`, `aria-invalid`, annoncé (`role="alert"` ou zone live), suggestion de correction.
- Pas de re-saisie d'information déjà fournie ; pas de test cognitif (CAPTCHA à reconnaître) pour l'authentification.

**Mouvement**
- Toute animation/transition derrière `@media (prefers-reduced-motion: no-preference)` ou neutralisée dans `@media (prefers-reduced-motion: reduce)`. Pas de contenu clignotant (>3 fois/s). Pas de carrousel auto-défilant sans pause.

**Zoom et responsive** (SC 1.4.4, 1.4.10)
- Utilise `rem`/`em` pour les tailles de texte ; lisible à 200 % ; pas de défilement horizontal à 320px de large (reflow) ; testé à 375px.
- Ne bloque pas le zoom (`user-scalable=no` interdit).

## SEO de base

- `<title>` unique, ~50–60 caractères : bénéfice + marque.
- `<meta name="description">` ~140–160 caractères, orientée bénéfice et CTA.
- `<link rel="canonical">` (URL à confirmer par l'utilisateur).
- Open Graph : `og:title`, `og:description`, `og:type=website`, `og:url`, `og:image` (+ `og:image:alt`), `twitter:card=summary_large_image`. L'image OG n'est pas produite par le skill : placeholder signalé 1200×630, ou recadrage d'une image libre retenue (licence vérifiée, voir `images-libres.md`).
- `<meta name="viewport" content="width=device-width, initial-scale=1">`, `<meta charset="utf-8">`.
- Favicon : référencé, fichier à fournir.
- HTML sémantique et titres cohérents font office de SEO on-page ; texte réel dans le DOM (pas dans des images).
- Données structurées JSON-LD (`Organization`, `FAQPage`) : optionnel, à proposer s'il est pertinent ; seulement avec des données réelles.
- Dans un framework avec gestion de `<head>` (Next metadata, Astro, `react-helmet`…), utilise le mécanisme natif du projet.
- Hors périmètre : sitemap, robots.txt, indexation, analytics → à mentionner à l'utilisateur.

## Légal : pages et stubs

Pages **distinctes**, liées depuis le footer :
- Mentions légales (identification de l'éditeur, hébergeur, contact, directeur de la publication).
- Politique de confidentialité.
- Politique de cookies.
- CGV — si vente en ligne uniquement.

Si des images libres de droit sont utilisées : mentionner les crédits photos (footer ou mentions légales) et, si des images sont chargées depuis un CDN tiers (hotlink), le signaler dans la politique de confidentialité.

**Pour chaque page existante** : lie-la (ne l'écrase pas). **Si absente** : crée un stub, route ou fichier selon la stack, avec :
- un titre H1, une bannière claire « Page provisoire — contenu à faire rédiger par un professionnel du droit » ;
- la structure de sections attendues avec des champs `[À COMPLÉTER]` ;
- le même layout simple (header/footer) pour que la navigation reste cohérente ;
- `noindex` tant que le contenu n'est pas validé (à signaler à l'utilisateur).
Ne rédige pas de texte juridique réel : un stub n'a aucune valeur légale. Rappelle-le à l'utilisateur dans la checklist.

Éditeur et contact : demande la raison sociale / le nom, l'adresse, l'email de contact, le numéro d'immatriculation si applicable. Sans réponse, placeholders marqués — jamais de coordonnées inventées. Le copyright utilise l'année courante calculée à l'exécution/au build (`new Date().getFullYear()` ou équivalent).

## Cookies

- Aucun traceur non essentiel (analytics, pixels pub, embeds tiers qui déposent des cookies) → **pas de bandeau**, mais dis-le dans la checklist.
- Si des traceurs non essentiels sont prévus : bandeau avec « Accepter » et « Refuser » au même niveau de visibilité et d'accessibilité (même taille/style, même nombre de clics), option « Personnaliser », focus géré (dialogue non bloquant ou `role="dialog"` correctement géré), et **aucun traceur chargé avant consentement**. Pour une solution de consentement tierce, demande avant de l'ajouter.
- Emplacement analytics : composant/commentaire vide, activé uniquement après consentement si requis.
