# L'entreprise mère

Une chaîne mesurée, de l'opportunité à l'argent encaissé, posée au-dessus des modules existants : SOVEREIGN,
NOVARYS, HIVE, VELYX, GALILÉE, CORTEX, LAVOISIER et le poste business. Elle n'ajoute aucun agent. Elle lit chaque
module en lecture seule, rapproche ce qu'ils déclarent de la source qui fait foi, et dit, opportunité par
opportunité, ce qui est **PROUVÉ**, **INCONNU**, en **CONFLIT** ou en **ÉCHEC**.

| Question | Où lire la réponse |
|---|---|
| Où en est l'argent, et quelle est la prochaine action ? | [`TABLEAU.md`](TABLEAU.md), régénéré à chaque passage. Les montants vivent dans `prive/`, jamais versionné |
| Qu'est-ce qui existe, en double, en conflit, ou manque ? | [`AUDIT.md`](AUDIT.md) |
| Qui fait quoi, et comment les modules se parlent-ils ? | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Que faire, dans quel ordre, et quand arrêter ? | [`PLAN.md`](PLAN.md) |
| Quelles opportunités, notées sur quels critères ? | [`donnees/portefeuille.toml`](donnees/portefeuille.toml) |

## État au 24/11/2026

Premier euro : **non atteint** (PROUVÉ par le prestataire de paiement, en lecture seule). 26 prospects contactés
sur 4 offres, 0 réponse à ce jour. Deux registres contredisaient la réalité : Velyx était déclaré gelé, et Obligato
en préparation, alors que des envois étaient partis. Ils ont été corrigés. Les conflits qui attendent une décision
du propriétaire sont listés dans `AUDIT.md`, § 4, et les alertes dans `TABLEAU.md`.

## La boucle de vérification

Rien n'est PROUVÉ sur la seule parole de celui qui l'a produit. Chaque affirmation (un paiement, un prospect, une
suite de tests, une note du portefeuille, un registre) est contrôlée par un acteur que son producteur ne maîtrise
pas : le grand livre du prestataire, la banque, le web public, un second lecteur de la messagerie, une copie propre
du dépôt, NOVARYS Ω, un relecteur indépendant. La matrice est dans `ARCHITECTURE.md` ; l'historique des erreurs
et des corrections, dans `journal/`.

## Utilisation

```bash
python3 -m mere tableau --stripe --rejouer --controler   # relève, rejoue en clone propre, contrôle, écrit les tableaux
python3 -m mere tableau                      # même chose avec le dernier relevé privé et les derniers rejeux
python3 -m mere verifier                     # portefeuille valide, sorties publiques sans fuite (CI)
python3 -m unittest discover -s tests        # tests adversariaux, dont les non-régressions des revues indépendantes
```

Python 3.11 ou plus, bibliothèque standard seule. Les modules sont cherchés à côté de ce dépôt (voir
`donnees/sources.toml`). Le prestataire de paiement se lit avec une clé **restreinte en lecture**, placée dans
`STRIPE_CLE_LECTURE` ; dans l'environnement cloud, c'est le mandataire réseau qui l'injecte. Le pipeline commercial
(`prive/pipeline.csv`) et le journal des coûts (`prive/couts.csv`) restent privés ; leurs colonnes sont décrites
dans `mere/sources.py`.

## Ce que la mère ne fait jamais

Envoyer un message, publier, dépenser, créer ou modifier un prix, écrire chez un prestataire ou dans un autre
module. Ces gestes restent au propriétaire. La mère les prépare et les rend visibles, rien de plus.
