# L'entreprise mère : notes pour les agents de code

## Reprise : par où commencer chaque session
1. `python3 -m mere tableau --stripe --rejouer`, puis lire dans `TABLEAU.md` les conflits, les alertes et les
   verdicts dus. Un verdict dû passe avant tout le reste.
2. Ne revendiquer aucun chiffre qui n'est pas un fait PROUVÉ du tableau. Potentiel, CA annoncé et encaissé ne se
   confondent jamais.
3. Pour toute décision business, charger le skill `businessman` du poste business (dépôt Strat-ge-business) et
   consigner la décision dans son journal (`memoire/JOURNAL_DECISIONS.md`).

## Règles du dépôt
- Python 3.11 ou plus, **bibliothèque standard seule**. Vérification avant commit :
  `.claude/bin/journal verif bash -o pipefail -c 'pipx run ruff check mere tests && python3 -m unittest discover -s tests && python3 -m mere verifier'`
- Identifiants en français, comme le reste du dépôt ; montants en centimes entiers, jamais de flottant.
- **Dépôt public.** Rien de nominatif, de financier réel ni de secret. `prive/` est ignoré par git. La garde
  (`mere/garde.py`) doit accepter toute sortie publique : ne jamais l'assouplir pour faire passer une sortie.
- **Lecture seule partout.** Le client du prestataire de paiement n'envoie que des GET, sur cinq listes nommées.
  Aucun adaptateur n'écrit dans un module. Un rejeu qui modifie un dépôt ne prouve rien.
- **Aucun nouvel agent, aucun nouveau registre chaîné, aucun nouveau tableau de bord** (voir `AUDIT.md`, § 3).
  Une capacité nouvelle s'ajoute dans le module existant qui la porte.
- Une opportunité active a ses six critères étiquetés et au moins un critère d'arrêt daté, fixé avant d'agir.
- Envoi, publication, dépense, création de prix, création de compte : décisions du propriétaire.

## Fiabilité avant sobriété : la preuve prime sur le plafond de sortie
- Le plafond est de 15 000 caractères, et il ne doit jamais coûter une preuve. Une sortie d'échec trop longue est
  coupée en tête et en fin, sans fichier ni code garanti. Toute vérification (tests, lint, rejeux) passe donc par
  `.claude/bin/journal <étiquette> <commande>`. Il garde le journal complet sur disque et affiche un résumé de
  moins de 8 000 caractères, jamais tronqué. Il écrit le code de sortie exact en première et en dernière ligne, et
  renvoie ce même code.
- Jamais `vérification | tail/head/grep` sans `pipefail` : le crochet `.claude/hooks/garde_pipe.py` refuse ces
  commandes.
- « Réussi » exige un code 0 **et** la ligne de bilan de l'outil (« OK », « All checks passed! »). Sinon, écrire
  « non vérifié » et pourquoi.
- Fusionner une PR seulement si **tous** les contrôles de la tête actuelle sont `success` (SHA vérifié) et si les
  vérifications locales ont rendu le code 0.

## Sobriété : chaque session, sans exception
- Lire de façon ciblée : Grep d'abord, puis Read avec `offset` et `limit`. Ne jamais lire `prive/faits.jsonl` en
  entier.
- Code minimal : le plus petit diff qui résout le problème.
- Carte du dépôt :
  - `mere/statuts.py` : les 4 statuts et leur combinaison.
  - `mere/faits.py` : le contrat commun et les 21 indicateurs.
  - `mere/stripe.py` : la lecture seule de l'argent.
  - `mere/sources.py` : les adaptateurs (prévisions, registres, déclarations, pipeline, coûts, rejeux).
  - `mere/portefeuille.py` : les six critères.
  - `mere/chaine.py` : consolidation, rapprochement, étapes, critères d'arrêt, priorités.
  - `mere/tableau.py` : assemblage et rendu.
  - `mere/garde.py` : la garde anti-fuite.
  - `donnees/` : le portefeuille et les sources.
  - `etat/` : les rejeux et les faits publics.
  - `tests/` : les attaques.
