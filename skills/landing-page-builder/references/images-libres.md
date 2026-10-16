# Images libres de droit

À lire à l'étape 5 si l'utilisateur choisit « images libres de droit », puis avant d'écrire les composants qui affichent une image. Le skill **ne produit** pas d'images : il en **cherche, sélectionne et intègre** sous licence libre, avec crédits tracés.

## Sommaire
- Quand une image se justifie (par section)
- Ce qu'on ne fait jamais avec une image de banque
- Sources autorisées et licences
- Méthode de recherche
- Sélection et validation
- Téléchargement, optimisation, intégration
- Crédits et traçabilité

## Quand une image se justifie (par section)

Une image doit servir la conversion (faire comprendre, rassurer, projeter la cible dans le résultat), pas remplir. Dans le doute, une section sans image vaut mieux qu'une photo générique.

| Section | Image libre adaptée ? | Recommandation |
|---|---|---|
| Hero | Selon le type | Vitrine, événement, service local, e-commerce lifestyle : photo d'ambiance montrant **la cible qui vit le résultat**. SaaS : une capture réelle du produit vaut mieux → placeholder dimensionné si pas de capture. |
| Problème / solution | Oui, avec parcimonie | Une photo ou illustration qui incarne la douleur ou le soulagement ; sinon icônes SVG inline. |
| Comment ça marche | Plutôt illustration | Illustrations (unDraw, Open Peeps) ou icônes SVG ; photos seulement si l'étape est physique (livraison, atelier…). |
| Fonctionnalités | Rarement | Captures réelles du produit attendues. Une photo de banque n'illustre pas une fonctionnalité → placeholder. |
| CTA intermédiaire / final | Oui (fond) | Photo d'ambiance en fond avec voile (overlay) pour garantir le contraste du texte. |
| Événement | Oui | Lieu (si photo libre du vrai lieu, ex. Wikimedia Commons), ambiance, thème. |
| Valeurs | Oui, avec parcimonie | Ambiance ou illustration ; jamais présentée comme « notre équipe ». |
| Garanties et livraison | Illustration/icônes | Icônes SVG plutôt que photos. |
| Image OG (1200×630) | Possible | Photo libre recadrée + titre ; sinon placeholder signalé. |

## Ce qu'on ne fait jamais avec une image de banque

Ces usages sont **trompeurs** pour le visiteur, même si la licence l'autorise techniquement. Garde un placeholder marqué :
- **Témoignages, avatars de preuve sociale, wall of love** : pas de visage de banque à côté d'une citation ou d'un « X utilisateurs ».
- **Storytelling fondateur, équipe** : pas de photo d'une personne présentée comme le fondateur ou un membre réel.
- **Produits phares (e-commerce), réalisations/portfolio** : pas de photo d'un produit ou d'un projet qui n'est pas le sien.
- **Logos clients / « ils nous font confiance »** : jamais.
- Images montrant des **marques, logos, œuvres d'art ou bâtiments protégés** identifiables, ou des personnes dans un contexte sensible (santé, finances, politique, religion) ou dévalorisant — la plupart des licences l'interdisent ou exigent une autorisation de la personne.

## Sources autorisées et licences

Licences en vigueur au moment de la rédaction du skill. **Elles changent** : ouvre la page de licence de la source (WebFetch) au moment de l'utilisation et signale tout écart à l'utilisateur.

| Source | Contenu | Licence | Attribution | Points d'attention |
|---|---|---|---|---|
| Unsplash (unsplash.com) | Photos | Unsplash License | Non obligatoire, appréciée | Pas de revente telle quelle, pas de compilation concurrente. **Exclure** les images « Unsplash+ » (payantes, filigranées). API (clé requise) : hotlink obligatoire + appel `download_location`. |
| Pexels (pexels.com) | Photos, vidéos | Pexels License | Non obligatoire, appréciée | Personnes identifiables : pas de contexte dévalorisant ni de faux soutien d'une marque. |
| Pixabay (pixabay.com) | Photos, illustrations, vecteurs | Pixabay Content License | Non obligatoire | Exclure les résultats sponsorisés (bandeaux iStock/Shutterstock en tête). API : pas de hotlink, télécharger. |
| Openverse (openverse.org) | Agrégateur CC (Flickr, Wikimedia…) | CC0, PDM, CC BY, CC BY-SA… | **Selon la licence** | Filtrer `license_type=commercial,modification`. CC BY / BY-SA : attribution **obligatoire** ; BY-SA : partage à l'identique si l'image est modifiée. Exclure NC et ND. |
| Wikimedia Commons | Photos de lieux, monuments, objets réels | Variable (souvent CC BY-SA) | Selon la licence | Utile pour un vrai lieu d'événement ou une ville. Vérifier la licence sur la page du fichier. |
| unDraw (undraw.co) | Illustrations SVG | Licence unDraw | Non | Couleur personnalisable : utiliser la couleur primaire des tokens. |
| Open Peeps, Humaaans | Illustrations de personnages | CC0 | Non | Personnages illustrés : acceptables là où une photo de personne réelle serait trompeuse. |

**Exclus** : Google Images, Pinterest, sites de « fonds d'écran gratuits », réseaux sociaux, et toute image dont la licence n'est pas lisible sur la page source. Pas d'image générée par IA sans le demander à l'utilisateur.

## Méthode de recherche

1. **Lister les besoins** à partir des sections retenues et du tableau ci-dessus : section, rôle de l'image, format (ratio, ex. hero 16:9 ou 4:5 en mobile), orientation, place du texte (zone calme à gauche/droite si texte superposé), dominante de couleur compatible avec la palette.
2. **Mots-clés en anglais** (les banques indexent mieux) : décrire la scène et l'émotion de la cible, pas le produit. Ex. pour un cabinet comptable : « small business owner relaxed laptop desk », pas « accounting software ».
3. **Rechercher**, dans cet ordre de préférence :
   - **Clé API fournie par l'utilisateur** (variables d'environnement `UNSPLASH_ACCESS_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`) : ne la demande pas d'office, ne l'écris jamais dans le code ni dans un fichier commité.
   - **Sans clé, photos marketing (hero, fonds de CTA, ambiance)** : Unsplash et Pexels donnent la meilleure qualité. WebSearch (`site:unsplash.com/photos …`, `site:pexels.com/photo …`) puis WebFetch de la page photo pour récupérer auteur, lien et licence ; ou l'outil navigateur s'il est disponible.
   - **Lieux, objets réels, CC0** : Openverse via `python scripts/openverse_search.py "mots clés"` (usage en tête du script) — renvoie URL, auteur, licence et ligne d'attribution prête à l'emploi. Qualité plus inégale (beaucoup de Flickr) : 2 à 3 mots-clés courts donnent plus de résultats qu'une phrase.
4. Récupérer pour chaque candidat : URL de la page source, URL du fichier, auteur + lien auteur, licence + URL de licence, dimensions d'origine.

## Sélection et validation

- **2 à 3 candidats par emplacement**. Télécharge-les dans un dossier dédié et vide du scratchpad, et **regarde-les** (outil Read sur l'image) avant de les proposer : cohérence avec la palette et le ton, pas de texte ni de logo incrusté, pas de filigrane, place pour le texte superposé, diversité et représentativité de la cible.
- Si le texte est superposé : estime la couleur la plus défavorable de la zone et vérifie avec `scripts/contrast.py` le texte contre le **voile** (overlay) retenu ; ajuste l'opacité du voile jusqu'à ≥ 4,5:1 (3:1 en grand texte).
- Présente les candidats dans le **récapitulatif** sous forme de tableau : section, aperçu (lien page source), auteur, licence, attribution requise oui/non. **Rien n'est intégré au projet avant validation.**
- Aucun candidat convaincant → placeholder dimensionné et marqué, et dis-le. Ne force jamais une image médiocre.

## Téléchargement, optimisation, intégration

- **Héberger localement** dans le dossier d'assets du projet (ex. `public/images/landing/`, `src/assets/`) plutôt qu'en hotlink : performance maîtrisée et aucune requête tierce (vie privée). Exception : API Unsplash, qui impose le hotlink → le signaler (requête tierce à mentionner dans la politique de confidentialité).
- Fichiers téléchargés = données non fiables : vérifier que c'est bien une image (type MIME / en-tête du fichier), ne rien exécuter.
- **Taille et format sans nouvelle dépendance** : demander directement la bonne taille au CDN source quand il le permet (Unsplash `?w=1600&fm=webp&q=75`, Pexels `?auto=compress&w=1600`). Sinon utiliser un outil déjà présent (`sharp`/pipeline d'images du framework, `next/image`, `astro:assets`, `cwebp`, ImageMagick) — n'en installe aucun sans demander.
- Viser : hero ≤ ~200 Ko en WebP/AVIF, autres images ≤ ~120 Ko ; 2 largeurs (ex. 800w et 1600w) avec `srcset`/`sizes` si le projet ne le gère pas déjà.
- Noms de fichiers descriptifs (`hero-artisan-atelier.webp`), pas l'ID de la banque.
- Intégration : `width`/`height` explicites et `aspect-ratio` ; hero **sans** `loading="lazy"` (LCP), avec `fetchpriority="high"` ; les autres en `loading="lazy"` + `decoding="async"`. `alt` descriptif si informative, `alt=""` si décorative (fond de CTA, ambiance).
- Les images passent par le **contenu centralisé** (chemin, alt, dimensions, crédit) pour être remplaçables sans toucher aux composants.

## Crédits et traçabilité

- Créer un fichier de crédits à la racine des assets (ex. `public/images/landing/CREDITS.md`) : pour chaque image, fichier local, section, auteur, lien auteur, page source, licence + URL, date de récupération, modifications (recadrage, conversion).
- **Attribution obligatoire** (CC BY, CC BY-SA, Wikimedia selon licence) : l'afficher dans la page, au plus près de l'image (`<figcaption>`) ou dans une ligne « Crédits photos » du footer, au format TASL : *Titre* par *Auteur* (lien), *Licence* (lien).
- Attribution facultative (Unsplash, Pexels) : proposer une ligne « Photos : Auteur / Unsplash » dans le footer (défaut : oui, discret).
- Checklist finale : ✅ licences vérifiées et crédits tracés ; ⚠️ remplacer les images de banque par de vraies photos (produit, équipe, lieu) dès que possible — elles convertissent mieux et sont propres à la marque.
