# Bibliothèque de sections

À lire à l'étape 4 (choix des sections) et avant d'écrire les composants. Chaque section = un composant.

## Sommaire
- Présélections par objectif
- Détail des sections
- Règle des témoignages
- Sections spécifiques à l'objectif

## Présélections par objectif

| Objectif | Sections présélectionnées (dans l'ordre) |
|---|---|
| Générer des leads | navbar, hero, problème/solution, comment ça marche, preuve sociale, FAQ, formulaire, CTA final, footer |
| Essai gratuit / vente SaaS | structure complète : navbar, hero, problème/solution, comment ça marche, CTA intermédiaire, démo vidéo, fonctionnalités, storytelling fondateur, tarifs, FAQ, wall of love, CTA final, footer |
| Notoriété | navbar, hero, storytelling, valeurs, réalisations, preuve sociale, contact, footer |
| E-commerce / vendre | navbar, hero, produits phares, bénéfices, preuve sociale, garanties et livraison, FAQ, CTA final, footer |
| Rendez-vous | navbar, hero, bénéfices, comment ça marche, preuve sociale, calendrier, FAQ, CTA final, footer |
| Informer | navbar, hero, bénéfices/points clés, comment ça marche, FAQ, contact, footer |

Le socle (navbar, hero, preuve sociale, CTA final, footer) est toujours présent, même si une présélection ci-dessus ne le liste pas explicitement (ex. ajoute un CTA final aux présélections Notoriété et Informer).

## Détail des sections (ordre de référence)

1. **Navbar sticky** — logo, 3 à 4 ancres maximum, CTA en bouton. Menu repliable en mobile (bouton avec `aria-expanded`, accessible au clavier). Hauteur fixe pour éviter les sauts ; `scroll-margin-top` sur les sections ancrées.
2. **Hero** — H1 = le résultat désiré pour la cible. Sous-titre en mots simples qui explique. 3 bénéfices (pas des fonctionnalités). CTA principal (+ secondaire éventuel). Preuve sociale immédiate : rangée d'avatars + « X utilisateurs » (placeholders marqués si pas de vrais chiffres). Visuel : placeholder dimensionné, jamais en lazy-load (c'est le LCP).
3. **Problème / solution** — 5 points douloureux vécus sans le produit, face à 5 bénéfices correspondants, alignés deux à deux. Écris les problèmes du point de vue de la cible, avec ses mots.
4. **Comment ça marche** — 3 étapes illustrées maximum, liste ordonnée `<ol>`. Verbes d'action courts.
5. **CTA intermédiaire** — le même CTA principal + une levée d'objection (« pas d'expérience requise », « sans carte bancaire », « annulable à tout moment »). Choisis l'objection la plus probable pour la cible.
6. **Démo vidéo (~3 min)** — conteneur à ratio fixe (16:9), poster en placeholder, lecture à la demande (pas d'autoplay avec son), sous-titres/transcription à prévoir. Ne produit aucune vidéo ; ne charge pas d'iframe tierce sans demander (cookies/traceurs) — préfère un facade « cliquer pour lire ».
7. **Fonctionnalités détaillées** — en visuel plutôt qu'en texte long : cartes ou alternance visuel/texte, chaque fonctionnalité formulée par son bénéfice.
8. **Storytelling fondateur** — qui tu es, le problème que tu as vécu, comment tu l'as résolu. Première personne. Photo en placeholder dimensionné. Ne rien inventer sur le fondateur : demande ou laisse des champs marqués.
9. **Tarifs** — 2 ou 3 offres, une mise en avant visuellement (et sémantiquement : « Recommandé », pas seulement la couleur). Prix barré si promotion (`<del>` + texte accessible « ancien prix »). Option accès à vie si lancement. Prix **toujours visibles**. N'invente pas de prix : placeholders marqués si non fournis.
10. **FAQ** — objections courantes (prix, difficulté, délai, annulation, support, données). Utilise `<details>/<summary>` ou un accordéon accessible (boutons avec `aria-expanded`). 5 à 8 questions.
11. **Wall of love** — grille de témoignages. Placeholders marqués « à remplacer par de vrais témoignages » ; jamais de faux témoignages présentés comme réels.
12. **CTA final** — rappelle le résultat désiré + CTA principal + levée d'objection. Dernier moment de décision : une seule action.
13. **Footer** — logo, liens de navigation (ancres), liens légaux (pages distinctes), réseaux sociaux (liens avec nom accessible, pas icône seule sans `aria-label`), copyright avec l'année courante, identification de l'éditeur/contact.

## Règle des témoignages

Des témoignages isolés (1 citation courte + nom/rôle) sont **répartis entre les sections** : un dans/sous le hero, un après « comment ça marche », un près des tarifs ou du CTA final. Le wall of love, s'il est retenu, ne remplace pas cette répartition. Chaque témoignage placé près d'un CTA répond à l'objection que ce CTA soulève.

## Sections spécifiques à l'objectif

- **Formulaire (leads)** — le minimum de champs (idéalement email seul, + nom si vraiment utile). Chaque champ a un `<label>` visible, `autocomplete` adapté, erreurs en texte associé (`aria-describedby`), pas uniquement par la couleur. CTA orienté résultat (« Recevoir mon guide »). Mention de consentement/lien vers la politique de confidentialité. L'envoi réel dépend d'un backend (hors périmètre) : `action` configurable ou `TODO` explicite.
- **Calendrier (rendez-vous)** — emplacement pour un embed de prise de rendez-vous (Calendly, Cal.com…) : demande avant d'intégrer un script tiers ; sinon bouton vers l'URL de réservation.
- **Produits phares (e-commerce)** — 3 à 6 produits, prix visibles, images placeholders dimensionnées. Pas de panier ni de paiement (hors périmètre) : lien vers la fiche/boutique.
- **Garanties et livraison** — délais, retours, paiement sécurisé, support ; CGV requises dans le footer.
- **Valeurs / Réalisations (notoriété)** — 3 à 4 valeurs avec une preuve concrète chacune ; réalisations en grille avec visuels placeholders.
- **Contact** — coordonnées réelles (email, téléphone, adresse) fournies par l'utilisateur, formulaire court optionnel.
