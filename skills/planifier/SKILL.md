---
name: planifier
description: Planifie l'exécution d'une tâche de développement (feature, refactoring, migration, bugfix, ajout d'API, etc.) en explorant le projet et en produisant un plan structuré, validé par l'utilisateur, qui servira de base à `/coder`. Ce skill ne fonctionne qu'en plan mode — s'il est invoqué hors plan mode, il demande d'abord à y entrer (EnterPlanMode) et ne fait rien d'autre tant que ce n'est pas le cas. Déclenche ce skill dès que l'utilisateur dit "/planifier", "planifier", "préparer une feature", "structurer un refactoring", "analyser une migration", "fais-moi un plan", ou demande explicitement à réfléchir avant de coder. À utiliser même si l'utilisateur ne dit pas "plan" mais formule clairement une intention de cadrer un travail avant de l'implémenter.
---

# Planifier

Analyse le contexte d'une tâche de développement et produit un plan clair, structuré, validé avant tout développement.

## Prérequis obligatoire : être en plan mode

Ce skill ne s'utilise **qu'en plan mode**. C'est la première chose à vérifier, avant toute exploration ou question.

- **Déjà en plan mode** (le système l'indique par un message « Plan mode is active ») → continue normalement.
- **Pas en plan mode** → appelle immédiatement l'outil `EnterPlanMode` (à charger via `ToolSearch` s'il est différé). Ne lis aucun fichier, ne pose aucune question de cadrage avant.
- **L'utilisateur refuse l'entrée en plan mode** (ou l'outil est indisponible) → arrête-toi. Réponds simplement : *« Le skill /planifier s'utilise en plan mode. Active-le avec Shift+Tab (ou `/plan`) puis relance `/planifier`. »* Ne produis pas de plan hors plan mode.

Une fois en plan mode, respecte ses règles :
- Exploration **en lecture seule** uniquement (Read, Glob, Grep, commandes non modifiantes). Aucune modification de code, aucune commande Git qui écrit.
- Le plan est **écrit dans le fichier de plan** indiqué par le système (seul fichier modifiable), au format décrit plus bas.
- Les questions de cadrage passent par `AskUserQuestion`.
- La validation finale passe par `ExitPlanMode` (voir « Validation avec l'utilisateur »).

## Pourquoi ce skill existe

Coder sans plan sur une tâche non-triviale mène à des allers-retours, du code qu'il faut jeter, et des oublis (tests, edge cases, migrations). Ce skill force une étape de cadrage rapide pour aligner sur le **quoi**, le **comment** et le **où** avant le **faire**.

## Calibrer la profondeur du plan

Toutes les tâches ne méritent pas le même niveau de détail. Évalue rapidement la complexité avant de plonger :

- **Tâche triviale** (1-3 lignes, fix typo, renommage local, ajout de log) → **pas de plan formel**. Écris dans le fichier de plan la modification en 2-3 lignes et appelle directement `ExitPlanMode`. Forcer un plan complet ici fait perdre du temps à tout le monde.
- **Tâche moyenne** (1-5 fichiers, fonctionnalité circonscrite) → plan complet selon le format ci-dessous, mais reste concis (pas besoin d'épiloguer).
- **Tâche large** (migration, refactor multi-modules, nouvelle feature avec UI + back + DB) → plan détaillé, et si vraiment énorme, **propose de la découper en sous-tâches** avant de planifier chacune.

Si tu hésites sur la catégorie, demande à l'utilisateur via `AskUserQuestion` : *"Tâche rapide ou je fais un plan complet ?"*

## Ce dont tu as besoin

Pour une tâche moyenne ou large, trois choses minimum doivent être présentes dans la conversation. Si elles manquent, demande-les **en une seule fois groupée** (un seul appel `AskUserQuestion`) :

1. **Titre** de la tâche *(court, explicite — ex: "Ajout de l'authentification OAuth Google")*
2. **Description** *(le quoi et le pourquoi — ex: "Permettre aux utilisateurs de se connecter via Google. Réduit la friction d'inscription.")*
3. **Critères d'acceptation** *(comment savoir que c'est terminé — ex: "Bouton 'Se connecter avec Google' sur /login, callback fonctionnel, utilisateur créé en base avec email vérifié, tests d'intégration verts")*

Si ces infos sont déjà claires dans la conversation, ne redemande pas — confirme rapidement ta compréhension à la place.

## Exploration du projet (avant de produire le plan)

Plonge dans le code pour comprendre les contraintes réelles. **Parallélise les explorations** (lance plusieurs Glob/Grep/Read en même temps) — l'exploration séquentielle est lente sans raison :

- **Structure générale** : arborescence, conventions de nommage des fichiers et dossiers
- **Fichiers directement concernés** : ceux que la tâche va modifier ou qui contiennent la logique adjacente
- **Dépendances existantes** : librairies déjà installées qui peuvent servir, services internes liés
- **Patterns en place** : style de code, architecture (couches, modules), gestion d'erreurs, logging — **lis au moins 1-2 fichiers similaires en entier** pour saisir le style réel, pas une vague idée
- **Tests existants** dans la zone : framework utilisé, conventions, niveau de couverture
- **Configuration** : variables d'env utilisées, fichiers de config impactés

L'objectif est de planifier avec les **vraies** contraintes du projet, pas avec un plan abstrait qui ignore l'existant.

## Quand la tâche est ambiguë : proposer 2 approches

Si plusieurs designs raisonnables existent (ex: "implémenter une side-car vs intégrer dans le service existant", "REST vs WebSocket", "champ JSON vs table dédiée"), **ne tranche pas seul**. Présente brièvement 2 options avec leurs trade-offs via `AskUserQuestion` (option recommandée en premier), laisse l'utilisateur choisir, puis détaille le plan complet pour l'option retenue.

C'est mieux qu'un plan unique imposé qu'il faudra refaire.

## Format du plan à produire

Écris le plan dans le fichier de plan (en français), exactement avec cette structure :

---

### 📋 [Titre de la tâche]

**Résumé**
*Une phrase qui explique ce que la tâche accomplit et pourquoi.*

**Fichiers à créer ou modifier**
- `chemin/vers/fichier.ext` — *à créer / à modifier*, *ce qui change en une ligne*
- ...

**Étapes de développement**
1. Première étape concrète et actionnable
2. Deuxième étape (...)
3. ...

**Tests à prévoir**
- Type de test (unitaire / intégration / E2E) + ce qu'il vérifie
- ...

**Points d'attention**
- ⚠️ Risque, edge case, ou contrainte critique
- 🔗 Dépendance externe (API, service, librairie à installer)
- 🔒 Aspect sécurité ou permissions
- 🔄 Stratégie de rollback / migration (si changement risqué : migration de DB, suppression de champ, refactor large)
- ...

---

## Quand prévoir un rollback

Pour les changements à risque, ajoute une ligne explicite dans **Points d'attention** :

- **Migration de schéma DB** : indiquer si réversible (down migration), ou si destructive (drop column) — dans ce cas, prévoir un backup ou une phase d'archivage
- **Suppression de fonctionnalité utilisée** : feature flag pour un rollback rapide
- **Refactor large** : possibilité de PR par sous-étape plutôt qu'un gros bloc
- **Changement d'API publique** : période de deprecation, double-écriture, etc.

Si le changement est local et facilement réversible (un nouveau fichier, un nouveau composant), pas besoin de section rollback.

## Exemple de plan rendu

Pour donner une idée concrète, voici à quoi un plan correctement rempli ressemble :

> ### 📋 Ajout de l'authentification OAuth Google
>
> **Résumé**
> *Permet aux utilisateurs de se connecter via leur compte Google pour réduire la friction d'inscription et éliminer la gestion de mots de passe.*
>
> **Fichiers à créer ou modifier**
> - `src/auth/providers/google.ts` — à créer, configuration du provider OAuth Google (client ID, scopes)
> - `src/auth/callback.ts` — à modifier, ajout du handler `/auth/google/callback`
> - `src/components/LoginButtons.tsx` — à modifier, ajout du bouton "Continuer avec Google"
> - `prisma/schema.prisma` — à modifier, ajout du champ `googleId` sur le modèle User
> - `tests/auth/google.test.ts` — à créer, tests d'intégration du flow OAuth
> - `.env.example` — à modifier, documentation des variables `GOOGLE_CLIENT_ID` et `GOOGLE_CLIENT_SECRET`
>
> **Étapes de développement**
> 1. Créer un projet OAuth dans Google Cloud Console et récupérer client ID + secret (action utilisateur)
> 2. Ajouter les variables d'env et les charger dans la config existante
> 3. Implémenter le provider Google en suivant le pattern de `src/auth/providers/github.ts`
> 4. Ajouter la migration Prisma pour `googleId` (nullable, unique)
> 5. Implémenter le callback : créer ou lier l'utilisateur, générer la session
> 6. Ajouter le bouton dans le composant de login
> 7. Écrire les tests d'intégration (mock du token Google)
>
> **Tests à prévoir**
> - Intégration : flow complet OAuth avec token mocké → utilisateur créé + session valide
> - Intégration : utilisateur existant avec même email → liaison du `googleId` au compte existant
> - Unitaire : validation des champs retournés par Google (email vérifié, etc.)
>
> **Points d'attention**
> - ⚠️ Vérifier que `email_verified` est `true` dans le token Google avant de lier à un compte existant (sinon risque de takeover)
> - 🔗 Nécessite que l'URL de callback soit whitelistée dans la console Google Cloud avant la mise en prod
> - 🔒 Stocker `GOOGLE_CLIENT_SECRET` uniquement côté serveur, jamais exposé au front
> - 🔄 La migration `googleId` est nullable et additive — rollback facile (drop column si besoin, aucune perte de données existantes)

## Validation avec l'utilisateur

Une fois le plan écrit dans le fichier de plan, appelle `ExitPlanMode` : c'est cet outil qui présente le plan à l'utilisateur et lui demande de l'approuver. Ne demande **pas** la validation en texte libre ni via `AskUserQuestion` (« Le plan te va ? »).

- **Plan refusé / ajustements demandés** → reste en plan mode, mets à jour le fichier de plan, puis rappelle `ExitPlanMode`.
- **Plan approuvé** → le rôle du skill s'arrête là. Indique en une ligne que l'utilisateur peut lancer `/coder` pour démarrer l'implémentation.

## Ce que ce skill ne fait PAS

- Il ne s'exécute jamais hors plan mode — pas d'exploration, pas de plan tant que le plan mode n'est pas actif
- Il ne code rien — son rôle s'arrête à la validation du plan par l'utilisateur (`ExitPlanMode`)
- Il ne crée pas de branche, ne commit pas, ne touche pas à Git
- Il ne lance pas `/coder` automatiquement — l'utilisateur déclenche la suite quand il est prêt
- Il n'impose pas un plan formel pour une modif triviale — bon sens avant tout
