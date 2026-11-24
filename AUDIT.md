# Audit de l'écosystème (24/11/2026)

**Verdict.** L'écosystème a construit cinq fois la même usine et n'a encore rien vendu. On compte cinq boucles de
décision, quatre registres chaînés en SHA-256, six tableaux de bord et sept produits avec un prix actif chez le
prestataire de paiement. L'argent encaissé, lui, est nul (PROUVÉ). Le goulot n'est pas une fonction manquante :
ce sont les conversations avec des acheteurs, un moyen de payer sur l'offre la plus avancée, et une source de
vérité unique. Ce dépôt apporte cette source de vérité. Il n'ajoute aucun agent.

Tout chiffre ci-dessous porte son statut : PROUVÉ (relu dans la source qui fait foi, commande ou relevé cité),
INCONNU, CONFLIT ou ÉCHEC. Les montants et les noms restent hors de ce dépôt public.

## 1. Les faits mesurés pendant l'audit

| Fait | Valeur | Statut | Source |
|---|---|---|---|
| Argent encaissé, tous produits | aucun | PROUVÉ | Prestataire de paiement, lecture seule (paiements, factures, remboursements, virements) |
| Clients enregistrés chez le prestataire | 0 | PROUVÉ | idem |
| Tentatives de paiement | 2, toutes en échec : une carte de test utilisée en mode réel (essai interne), un refus bancaire d'origine inconnue | ÉCHEC | idem |
| Produits avec un prix actif | 7 (13 prix), répartis sur 5 offres, dont 3 déclarées remplacées ou gelées | PROUVÉ | idem |
| Prix actif pour Obligato, l'offre qui a le plus de prospects | aucun | PROUVÉ | idem : un « oui » ne peut pas payer aujourd'hui |
| E-mails de prospection envoyés depuis le 21/11 | 26, sur 4 offres différentes (10, 8, 7 et 1) | PROUVÉ | Messagerie, dossier Envoyés, lecture seule |
| Réponses humaines | 0 | PROUVÉ | Messagerie (trois jours après les premiers envois, ce qui est encore tôt) |
| Message retenu par un filtre anti-spam à défi | 1 | PROUVÉ | Messagerie : il attend un clic du propriétaire |
| Envois de Novarys Conformité (lots J1 à J3 prévus du 24 au 26/11) | 0 retrouvé | INCONNU | Messagerie : passés peut-être par formulaire ou LinkedIn, sans trace |
| Visiteurs des pages d'offre | aucun compteur | INCONNU | Aucun outil de mesure activé |
| Coûts et heures du fondateur | aucun journal | INCONNU | — |
| Suite de SOVEREIGN | 292 tests, lint, format, types | PROUVÉ | rejouée, commit 7cddfbd53ae6 |
| Suite de HIVE | 54 tests | PROUVÉ | rejouée, commit 8b552da54e4a |
| Registre de NOVARYS | 35 preuves chaînées, 28 capacités ; 77 tests | PROUVÉ | `omega check`, commit e16b00ed355a |
| Suite de Tr (GALILÉE, CORTEX, LAVOISIER) | 51 tests | PROUVÉ | rejouée, commit 67a043cfd198 |
| Suite de VELYX | 229 réussis, 1 en échec | ÉCHEC | rejouée, commit 8879058e3b91 (cause en § 4) |
| Suite du poste business | 15 tests | PROUVÉ | rejouée, commit 292e9ccc17f6 |

## 2. Les modules nommés par la mission

| Module | Ce qu'il est | Ce qui est prouvé | Ce qui manque ou échoue | Rôle dans l'entreprise mère |
|---|---|---|---|---|
| **SOVEREIGN** | Le moteur : base SQLite en ajout seul, registre financier (règle des 10 %), mémoire, conseil, simulation, 10 Skills, CLI, API, MCP | Suite verte. La boucle du directeur tourne sur le jeu de démonstration. L'observation des dépôts est opérationnelle (NOVARYS, preuve n° 17) | Aucune donnée d'entreprise chargée, aucun encaissement enregistré. Cycle quotidien arrêté depuis le 18/11 (D5 de NOVARYS) | **Direction** : règles de décision, enveloppe de dépense (10 % de l'encaissé réel, donc 0 € aujourd'hui), arbitrage du portefeuille |
| **HIVE** | Colonie d'agents coordonnés par traces, validations depuis le téléphone, Studio vidéo | Suite verte, vidéo réelle produite par la démo selon le dépôt | Aucun modèle de langage branché (jour 2 de sa feuille de route). Aucune offre | **Coordination et contrôle des tâches** : file de validations humaines et missions de production. Le contrôle des *preuves* reste à NOVARYS Ω (voir CONFLIT C5) |
| **NOVARYS** | Poste de pilotage : protocole de preuves Ω, référentiel des capacités, registre des actifs, portail public, méthode commerciale REACHER | Registre intact (35 preuves). Portail en ligne selon son journal | 16 fonctions sur 28 sous le niveau TESTÉ. REACHER ne lit qu'un compte sur sept | **Compétences commerciales** (REACHER, avec la méthode du poste business) et **protocole de preuve** |
| **CORTEX** (dépôt 1, repris dans Tr) | Boucle cognitive bayésienne qui pilote une activité inconnue | Suite de Tr verte (51 tests) | Recherche sur simulation : ni offre ni utilisateur. Quatre copies du même code | **Expertise** : choisir quel levier commercial tester en premier, une fois qu'il y aura des données de vente |
| **GALILÉE** (dépôt All, repris dans Tr) | Agent qui retrouve une loi cachée dans des données | idem | idem | **Expertise** : relier les taux de conversion à leurs causes, au-delà de 30 conversations |
| **LAVOISIER** (dépôt A, repris dans Tr) | Reconstruire les comptes d'une entreprise opaque par conservation | Premier organe seulement (selon Tr) | Organes 2 à 8 non écrits | **Expertise** : à terme, contrôle de cohérence des comptes (encaissé, coûts) |
| **VELYX** (Velyx-prospection-) | Agent de prospection par la preuve : demande publiée, registre SIRENE, échantillons, file de revue | 229 tests sur 230 ; 7 envois réels le 21/11 | Son registre déclare 0 envoi au 21/11 à 8 h 22 : les 7 envois de l'après-midi n'y sont pas. 1 test rouge | **Recherche de marchés et production d'échantillons** |
| *Poste business* (Strat-ge-business, non nommé) | Le businessman (méthode, 7 règles, mémoire, banc d'évaluation), Obligato, Novarys Conformité | Suite verte ; banc à environ 95/100 ; 10 envois Obligato | 0 € ; registre des projets en retard sur la réalité (CONFLIT C2) | **Direction commerciale** (méthode), **production** des offres actives, **amélioration continue** (journal, prévisions, calibration) |

Les autres dépôts, décrits dans le registre des actifs de NOVARYS (Alll, Ref, Paie-juste, Clip-preuve, Jeun,
Toon-o-Matic, Logiciel- (OMNIA), MONDO, Artiste-), restent hors de la chaîne tant qu'ils n'ont pas d'offre testée.
Alll y figure gelé : sa mise en vente demande une dépense, refusée par le budget de 0 €.

## 3. Les doublons

| Fonction | Construite dans | Ce qu'il faut garder |
|---|---|---|
| Boucle de décision (observer → apprendre) | SOVEREIGN (directeur), VELYX (même 13 phases), HIVE (profil « analyse »), CORTEX, businessman | La boucle du businessman pour décider, les règles de SOVEREIGN pour la dépense. Plus aucune nouvelle boucle |
| Registre chaîné en ajout seul | NOVARYS Ω, Tr, VELYX, HIVE (et l'audit de SOVEREIGN) | Chacun garde le sien : la mère ne crée **pas** de cinquième registre, elle lit les sources |
| Tableau de bord | Portail NOVARYS, VELYX, OMNIA, poste business, REACHER (privé), HIVE (application) | `TABLEAU.md` de la mère pour la chaîne commerciale ; les autres renvoient vers lui |
| Fichier de créations d'entreprises du BTP | VELYX (courtiers) et `novarys/generer_fichier.py` (plan B de D-20261123-1) | VELYX pour la production ; une seule offre commerciale |
| Code de recherche | Tr, 1, A, All (recouvrement d'environ 90 %) | Tr comme référence ; archiver les trois copies (décision du propriétaire) |
| Le nom « Novarys » | Le dépôt de pilotage, une offre du poste business, le paquet Python de Ref, et 8 entreprises homonymes au registre | Un nom par chose (décision du propriétaire, D8 de NOVARYS) |
| Offres en vente | 7 produits actifs chez le prestataire, dont Velyx, Velyx Pro, Velyx Business et Textes alternatifs, déclarés gelés ou remplacés | Archiver les produits zombies (geste d'écriture : accord du propriétaire) |

## 4. Les conflits

| N° | Conflit | Sources | Proposition | Qui tranche |
|---|---|---|---|---|
| C1 | VELYX est la mission n° 1 pour NOVARYS (ADR 0002, 21/11), mais « gelé » pour le poste business ; or 7 envois sont partis le 21/11 | ADR 0002 de NOVARYS, `memoire/PROJETS.md`, messagerie | Statut **test** : on laisse courir les 7 envois jusqu'au verdict du 05/12 et on répond à tout retour, sans nouvel envoi. Registre du poste business corrigé | Proposé ; le propriétaire peut le renverser |
| C2 | Obligato est déclaré « préparé hors ligne, validation en attente », alors que 10 cabinets ont reçu leur pack le 24/11 | `memoire/PROJETS.md` contre le journal D-20261124-1 et la messagerie | Registre corrigé : actif | Fait dans cette session |
| C3 | Le registre de VELYX annonce 0 envoi au 21/11 à 8 h 22 ; 7 envois partent le même après-midi et n'y sont pas | `etat/kpi.json` de VELYX, messagerie | Enregistrer les envois dans VELYX (commande `geste` de son dépôt) ; tant que ce n'est pas fait, ses taux de réponse seront faux | Le propriétaire (accès en écriture à VELYX) |
| C4 | Deux offres sont parties sans qu'aucun registre ne les déclare : créations d'entreprises pour experts-comptables (8 envois) et pilote de conformité Google Merchant Center (1 envoi) | Messagerie ; aucun dépôt lisible | Statut test, rattachement à un module, aucun nouvel envoi | Le propriétaire |
| C5 | La mission confie le contrôle à HIVE ; dans les faits, c'est NOVARYS Ω qui contrôle les preuves (35 preuves chaînées), et HIVE n'a aucun modèle de langage branché | Mission, dépôts | HIVE coordonne les tâches et les validations, NOVARYS Ω contrôle les preuves, la mère rapproche les chiffres. Changer ce partage demanderait de réécrire Ω dans HIVE, sans gain mesuré | Le propriétaire |
| C6 | Le `CLAUDE.md` du poste business dit « dépôt public » ; GitHub le classe privé | `CLAUDE.md`, liste des dépôts | Garder la règle la plus prudente (rien de réel versionné) | Aucun changement |
| C7 | Le poste business arrête la vente de fichiers de créations (D-20261123-1, 23/11) ; NOVARYS en fait sa première mission (21/11) ; Stripe garde actif un abonnement « Fichier mensuel des nouvelles entreprises du bâtiment » | Les deux journaux, le prestataire | Une seule décision, au verdict du 05/12 (C1) | Au verdict |

**Le test rouge de VELYX** (« opposition reçue après l'échantillon → revue caduque ») : le scénario crée une revue
datée du 16/11, valable 7 jours, puis appelle la ligne de commande, qui lit l'horloge réelle. Depuis le 23/11, la
revue est déjà expirée : elle n'est donc plus « rendue caduque ». La cause est PROUVÉE par lecture du code
(`test/cycle.test.js` l. 262 à 288, `src/risque.js` l. 27 et 343) ; le comportement du produit est correct. La
correction consiste à injecter l'horloge dans la ligne de commande ou à dater le scénario à partir d'aujourd'hui.
Elle relève du dépôt VELYX, que cette session ne peut que lire.

## 5. Les compétences réellement manquantes

1. **Un moyen de payer sur l'offre la plus avancée** : Obligato n'a aucun prix chez le prestataire.
2. **La mesure du haut de l'entonnoir** : aucun compteur de visites ; les envois ne sont tenus dans aucun registre
   à jour.
3. **Un seul compteur d'argent rapproché** : les modules déclaraient l'encaissé chacun de leur côté, sans
   rapprochement avec le prestataire. C'est fait ici (`mere/chaine.py`, `rapprocher`).
4. **Le statut pour facturer** (D2 de NOVARYS) : INCONNU. Le compte du prestataire de paiement fonctionne en mode
   réel, ce qui suggère qu'une identité d'entreprise y a été déclarée, mais rien ne le prouve dans les dépôts.
5. **Le suivi des réponses** : aucun processus ne garantit qu'un prospect qui répond sur une offre « gelée »
   reçoive une réponse.

Rien d'autre ne manque pour encaisser le premier euro : les fonctions d'invention, de recherche, de production
et de décision existent toutes, souvent en plusieurs exemplaires.

## 6. Les synergies utilisables tout de suite

- **Obligato et les experts-comptables.** Deux offres visent la même cible : 10 cabinets pour Obligato, 8 pour les
  créations d'entreprises. Un cabinet qui reçoit les affichages de ses clients est un canal, pas un client
  final. La licence pour cabinet est la seule offre dont le rapport LTV/CAC dépasse 1 sous hypothèses prudentes
  (1,41, D-20261124-1).
- **VELYX et Novarys Conformité.** Le même croisement entre registre et oppositions sert d'échantillon à VELYX et
  de diagnostic à Novarys Conformité. On garde un seul moteur de vérification, celui de `novarys/verifier_fichier.py`.
- **SOVEREIGN et la mère.** Le registre financier de SOVEREIGN sait importer des encaissements depuis un CSV. Les
  faits PROUVÉS de la mère (`prive/faits.jsonl`) peuvent l'alimenter dès le premier euro. Sa règle des 10 %
  devient alors la seule porte de dépense.

## 7. Limites de cet audit

- La messagerie ne montre que les envois par e-mail. Les formulaires et LinkedIn ne laissent aucune trace
  lisible : les envois de Novarys Conformité y sont peut-être.
- L'attribution d'un paiement à une opportunité repose sur la métadonnée `opportunite`, sur le produit de la
  facture ou sur la description. Un paiement sans aucun de ces trois repères est compté au total, mais pas
  attribué.
- Les dépôts privés (Alll, velyx-sauvegardes) et les actifs hors GitHub n'ont pas été lus.
- Les notes des six critères sont, pour la plupart, des hypothèses étiquetées. Seul le score prouvé sert au
  classement.

## 8. Les outils tiers proposés le 24/11 : audit et verdict

Les sept dépôts ont été clonés à part et lus comme des données non fiables : aucun code n'a été exécuté. Le critère
de choix : l'outil sert-il la boucle de vérification ou la chaîne jusqu'à l'argent, sans dépense ni compte nouveau ?

| Outil | Ce qu'il est (lu dans le dépôt) | Licence | Verdict | Pourquoi |
|---|---|---|---|---|
| Playwright MCP (microsoft/playwright-mcp) | Navigateur piloté par MCP | Apache-2.0 | **Retenu pour les vérifications de pages** | Il vérifie de façon indépendante qu'une page d'offre ou le portail est en ligne et fonctionne. Le navigateur est déjà installé dans l'environnement. À brancher en `.mcp.json`, en version épinglée, au moment de vérifier une page d'offre |
| agent-fender (K-Carb/agent-fender) | Grille de 7 garde-fous pour le code d'agents, plus une bibliothèque Python sans dépendance | MIT | **Retenu comme grille de contrôle externe**, sans installation | Ses 7 critères (délai sur chaque appel au modèle, limite de boucle, délai des outils, validation des actions dangereuses, détection d'injection, journal structuré, budget de jetons) sont une grille indépendante pour auditer SOVEREIGN, HIVE et VELYX. Son installateur écrit dans `~/.claude/skills` : à ne pas lancer sans accord |
| Codex pour Claude Code (openai/codex-plugin-cc) | Relecture et délégation à Codex depuis Claude Code | Apache-2.0 | **Utile, mais bloqué : décision du propriétaire** | Une relecture par un autre modèle est la forme la plus forte du « aucun agent ne valide seul ». Il exige un compte ChatGPT ou une clé OpenAI : souscription et identité, donc accord explicite |
| Remotion (remotion-dev/claude-code-plugin) | Création de vidéos en code | (voir le dépôt) | Non retenu maintenant | Production vidéo, déjà couverte par le Studio de HIVE. Aucune offre active n'en a besoin avant le premier euro |
| last30days (mvanhorn/last30days-skill) | Recherche des discussions récentes (Reddit, HN, X, YouTube…) | MIT | Non retenu pour les marchés actuels | Signal anglophone et grand public ; les offres actives visent des TPE et des cabinets français, pour lesquels les registres publics sont la source fiable. Plusieurs sources exigent des clés. À réévaluer pour une offre grand public |
| Impeccable (pbakaus/impeccable) | Vocabulaire de design et détecteur déterministe de « design générique » | Apache-2.0 | Non retenu maintenant | Améliore des pages, mais aucune page d'offre n'a de trafic mesuré. À reprendre quand une page reçoit des visiteurs |
| feder-skills (federbenjamin/feder-skills) | Cinq skills de raisonnement et de présentation | MIT | Non retenu | Recouvre la boucle de décision du businessman (options, explication) : un doublon de plus |

## 9. La revue indépendante du code de la mère

Un agent relecteur, sans le contexte de l'auteur, a attaqué `mere/` par des scripts reproductibles. Les 62 tests
de l'auteur passaient tous. La revue a pourtant trouvé :
- **1ʳᵉ revue : 19 défauts**, dont 6 critiques. Une autorisation non capturée comptait comme vente. Des valeurs
  privées atteignaient le tableau public. La garde laissait passer des SIREN, des téléphones et des clés.
  Un fichier public était écrit avant la garde.
- **2ᵉ revue : 18 défauts corrigés sur 19**, et 10 nouveaux, dont 3 critiques :
  - un prospect qualifié dans une offre en validait une autre ;
  - une page en 403 ou 404 « prouvait » un prospect ;
  - une valeur citée pouvait être recopiée dans le public.
- **3ᵉ revue : les 10 corrigés**, et 7 nouveaux, dont aucun ne touche l'argent ni les ventes. Un hébergeur où le
  producteur peut publier passait pour une source. Une donnée non versionnée était acceptée. Un contrôle en
  cache était réutilisé après un changement de la note. Ils sont corrigés ; une liste d'autorités autorisées
  remplace la liste de refus.
- **4ᵉ revue : 3 corrigés, 4 brèches résiduelles reproduites**, corrigées depuis.
  - Le producteur pouvait déclarer sa propre page comme tiers de confiance.
  - data.gouv.fr publie les jeux de n'importe quel compte.
  - Un fichier de données écrit dans l'écosystème prouvait une note.
  - Un contrôle en cache, forgeable, restait PROUVÉ.

  La règle qui en sort est stricte : une donnée interne peut révéler un CONFLIT, jamais prouver. Un contrôle ne vaut
  que dans le passage qui l'a fait.
- **5ᵉ revue : A1 à A4 corrigés**, mais six étapes sur huit pouvaient encore être PROUVÉES par la seule mémoire de
  la mère (rejeux enregistrés, instantané du prestataire) ou par des fichiers de l'auteur (verdict saisi, domaine
  tapé). Une lecture ne vaut désormais que dans le passage qui l'a faite. Un verdict saisi doit concorder avec la
  mesure. Un domaine doit être confirmé par le second relevé de la messagerie.
- **6ᵉ revue : 5 chemins sur 6 fermés.** Deux chemins restaient ouverts : un verdict « confirmé » par un compte du
  pipeline, et un second relevé de la messagerie fourni comme fichier. Ils sont fermés à leur tour. En
  conséquence, l'étape « acheteur » reste INCONNUE tant que la mère ne lit pas elle-même la messagerie.
- **7ᵉ revue : « amélioration » fermé.** Un dernier chemin restait : l'identifiant de passage, prévisible, laissait
  un fichier se faire passer pour une lecture directe de la messagerie. Il est fermé : aucun fichier ne rend un
  relevé opposable. Le script d'attaque du relecteur, rejoué sur le code corrigé, ne passe plus. Le relecteur n'a
  trouvé aucune autre étape PROUVÉE sur des preuves écrites par la mère ou par l'auteur.

Chaque défaut a son test de non-régression (`tests/test_revue_independante.py`, f01 à f19, n01 à n10, t1 à t7, a1 à a4, b1 à b5, c1, c2 et d1 : 128 tests).
Ces tests ont été rejoués contre le code d'avant correction : ils y échouent bien. Le détail des erreurs, de leurs causes et
des corrections est dans `journal/C-0002.md`.

## 10. Le code des moteurs, contrôlé avec une grille externe (agent-fender)

La grille vient de agent-fender (MIT), pas de l'auteur de cet audit. Chaque verdict cite la ligne qui le fonde.

| Garde-fou | SOVEREIGN (`core/llm.py`) | HIVE (`core/llm.py`, `core/governance.py`) |
|---|---|---|
| 1. Délai sur l'appel au modèle, erreurs classées | ✗ : `anthropic.Anthropic()` sans délai explicite (l. 121), délai par défaut du SDK ; `except Exception` générique (l. 176) | ✓ partiel : `timeout_s = 120` pour les fournisseurs HTTP (l. 64, 150, 194) ; ✗ appel Anthropic sans délai explicite |
| 2. Limite de boucle | ✓ : boucle du directeur en phases bornées ; le `while True` de `interfaces/cli.py` l. 113 est l'invite interactive | ✓ : `max_steps_per_mission = 120` (`governance.py` l. 53) |
| 3. Délai des outils | non applicable : aucun outil externe exécuté par le modèle | ✓ : disjoncteurs par mission |
| 4. Validation des actions dangereuses | ✓ : revue humaine des risques élevés, jamais via MCP (`ARCHITECTURE.md` de SOVEREIGN) | ✓ : `request_approval` (`governance.py` l. 195) |
| 5. Détection d'injection | ✗ : aucune trouvée ; risque limité, car l'IA n'y décide pas (ADR 0004) | ✗ : aucune trouvée |
| 6. Journal structuré | ✓ : registre en ajout seul et journalisation | ✓ : registre chaîné |
| 7. Budget de jetons | ✓ : enveloppe de 10 % vérifiée avant l'appel, `max_tokens` (l. 134 à 160) | ✓ : budget par mission (`governance.py` l. 74 à 125) |

À corriger, dans les dépôts concernés, au moment où un modèle y sera réellement branché : un délai explicite sur
chaque client Anthropic (`timeout=60`), et le classement des erreurs (délai, connexion, réponse). La mère n'appelle
aucun modèle : les garde-fous 1, 5 et 7 ne la concernent pas.
