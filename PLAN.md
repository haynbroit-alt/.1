# Plan d'exécution priorisé

**Décision.** On ne construit plus rien jusqu'au premier euro. Toute l'énergie va à trois gestes :
- rendre l'offre la plus avancée payable ;
- répondre et relancer à temps ;
- rendre les verdicts aux dates déjà fixées.

L'écosystème a l'outillage. Il lui manque des acheteurs et un moyen de les faire payer.

Chaque chiffre est étiqueté : [mesuré] avec sa source, [hypothèse] ou [calcul].

## Étape 0 : les gestes du propriétaire (cette semaine, 0 €)

| # | Geste | Pourquoi | Débloque | Durée |
|---|---|---|---|---|
| 1 | Valider le défi anti-spam en attente dans la messagerie | 1 des 10 cabinets Obligato ne reçoit rien tant que ce n'est pas fait [mesuré] | 10 % du test Obligato | 1 min |
| 2 | Confirmer le statut pour facturer (D2 de NOVARYS) : numéro d'entreprise existant ou non | Sans lui, aucune facture légale, quelle que soit l'offre | Toutes les ventes | 2 min si le statut existe, 30 min sinon |
| 3 | Autoriser la création du prix Obligato chez le prestataire : pack TPE à 39 € HT, licence cabinet à 49 € HT par mois (prix de `boutique/STRATEGIE_COMMERCIALE.md`) | L'offre qui a le plus de prospects n'a aucun prix actif [mesuré] : un « oui » ne peut pas payer | L'étape « offre » d'Obligato | 5 min, à faire avec l'agent |
| 4 | Dire si les lots J1 à J3 de Novarys Conformité sont partis, et par quel canal | Aucun envoi retrouvé dans la messagerie [mesuré] ; le verdict du 30/11 échouera par défaut | Le verdict de D-20261123-2 | 2 min |
| 5 | Accepter ou refuser les propositions de l'audit : C1 (VELYX en test sans nouvel envoi), C4 (deux offres orphelines en test), C5 (partage du contrôle) | Une seule vérité par offre | La fin des priorités contradictoires | 2 min |
| 6 | Activer un compteur de visites gratuit sur le portail et les pages d'offre | Visiteurs INCONNU partout [mesuré] | Le haut de l'entonnoir | 10 min |
| 7 | Dès le premier virement du prestataire : déposer l'export du relevé bancaire dans `.1/prive/banque.csv` (date;libelle;montant) | La banque est le seul contrôleur indépendant de l'encaissement : sans relevé, « encaissé » reste INCONNU | La preuve du premier euro | 2 min par mois |
| 8 | Dire oui ou non à une relecture par un autre modèle (Codex, compte OpenAI requis) | Aujourd'hui, le relecteur indépendant est du même modèle que l'auteur | Une indépendance plus forte du contrôle du code | 5 min |
| 9 | Autoriser l'écriture dans le dépôt VELYX, ou corriger soi-même son test daté | Sa suite est rouge depuis le 23/11 (audit, § 4) | Le produit VELYX de nouveau PROUVÉ | 10 min |

## Étape 1 : jusqu'aux verdicts (25/11 au 06/12)

| Date | Action | Responsable | Indicateur | Critère d'arrêt |
|---|---|---|---|---|
| Chaque jour | `python3 -m mere tableau --stripe --rejouer --controler`, puis lire les conflits, les alertes et les contrôles en échec | Agent | Conflits ouverts, verdicts dus, contrôles non PROUVÉS | Un verdict dû sans mesure se traite le jour même |
| Chaque semaine | Second relevé indépendant de la messagerie (`prive/recomptage_messagerie.json`), par un autre lecteur que celui qui tient le pipeline | Un agent distinct, ou le propriétaire | Concordance envois, réponses, rebonds, domaines | Tout écart est un CONFLIT à résoudre avant la revue |
| Chaque jour | Répondre dans la journée à tout retour, **y compris** sur VELYX, les créations d'entreprises et le pilote Google Merchant Center | Propriétaire, avec un brouillon de l'agent | Réponses dans la journée | Aucune réponse laissée plus de 24 h |
| 28/11 | Relance Obligato des 10 cabinets : un seul message, leur propre pack en pièce jointe, une question fermée | Propriétaire | Réponses | Moins d'une réponse au 01/12 : revoir l'objet et le canal |
| 30/11 | Verdict de D-20261123-2 (angle de la loi du 30/06/2025) | Agent | Réponses positives sur 20 | Moins d'une : revoir l'angle |
| 04/12 | Verdict de D-20261123-1 (Novarys Conformité) | Agent | Diagnostics, clients payants | Moins de 3 diagnostics : arrêt |
| 05/12 | Verdict de VELYX BTP et des créations d'entreprises (14 jours) | Agent | Réponses | Aucune réponse : arrêt de l'offre, sans relance |
| 06/12 | Verdict du pilote Google Merchant Center | Agent | Réponse | Aucune : clore |

Au 06/12, il reste **une ou deux offres actives**, jamais quatre.

## Étape 2 : du premier euro à une offre rentable (décembre)

- Le premier paiement passe par le prestataire, avec la métadonnée `opportunite`. La mère le prouve et
  l'attribue. Le registre financier de SOVEREIGN l'importe ; sa règle des 10 % ouvre alors la première enveloppe
  de dépense.
- L'offre qui a obtenu des réponses reçoit tout le temps disponible. On mesure les taux réels (réponse, essai,
  achat) et l'on remplace les hypothèses du calculateur.
- **Seuil de rentabilité d'une offre** : LTV/CAC d'au moins 1, temps compris, sur au moins 10 clients mesurés. En
  dessous, on corrige une seule chose (cible, canal ou prix), puis on remesure.

## Le chemin vers 1 000 € par jour, chiffré

1 000 € de chiffre d'affaires par jour, c'est environ 30 000 € HT par mois [calcul]. Les hypothèses du
calculateur du poste business (`economie_unitaire.py`) :
- 10 minutes par contact et 40 € par heure de temps du fondateur ;
- des taux de conversion **supposés** [hypothèse] : 10 % de réponses, 50 % d'essais, 25 à 30 % d'achats.

| Offre | Prix HT | Clients nécessaires | Contacts par mois | Heures d'acquisition par mois | LTV/CAC | Verdict |
|---|---|---|---|---|---|---|
| Pack Obligato à l'unité, prospection directe | 39 € | 770 ventes par mois | environ 51 000 | environ 9 300 | 0,08 | Impossible par prospection directe |
| Licence cabinet Obligato | 49 € par mois, churn 5 % | 613 licences actives, 31 nouvelles par mois en régime établi | environ 2 100 | environ 380 | 1,48 | Rentable mais fragile ; intenable en solo |
| Abonnement Novarys Conformité | 290 € par mois, churn 8 % | 104 abonnés actifs ; 14 nouveaux par mois pour les atteindre en 12 mois | environ 1 100 | environ 200 | 4,64 | Le seul profil compatible, **si** les taux supposés se vérifient |

Le LTV/CAC vient du calculateur. Les volumes sont des calculs posés à partir de ses valeurs par client : 67 à 80
contacts et 12 à 14 heures par client signé.

Ce que cela veut dire :
1. **1 000 € par jour ne s'atteignent pas avec des ventes ponctuelles à bas prix en prospection directe.** Il faut
   un abonnement B2B de quelques centaines d'euros par mois, ou un canal qui démultiplie la vente : les cabinets
   d'expertise comptable pour Obligato, des partenaires pour la conformité.
2. Même dans le meilleur cas, il faut une centaine d'abonnés actifs et environ 200 heures d'acquisition par mois
   pendant un an [calcul]. C'est plus que le temps d'une personne seule : la vente doit passer par du contenu ou des
   partenaires. L'objectif s'atteint par étapes, pas en quelques semaines.
3. Toutes ces lignes reposent sur des taux **supposés**. Les premiers taux mesurés, attendus aux verdicts du 30/11
   au 06/12, remplaceront ce tableau.

## Étape 3 : plusieurs activités rentables et indépendantes (2027)

On n'ouvre une deuxième activité que lorsque la première vérifie trois conditions, mesurées sur trois mois :
- LTV/CAC d'au moins 3 ;
- un canal qui ne dépend pas du temps du fondateur ;
- au moins 30 % du revenu récurrent.

Chaque activité garde son module, son registre et ses critères d'arrêt. La mère les rapproche, et la règle des
10 % de SOVEREIGN répartit la dépense.

## Ce qu'on ne fait pas

- Aucun nouvel agent, aucune nouvelle boucle de décision, aucun nouveau registre chaîné, aucun nouveau tableau de
  bord. L'écosystème en compte déjà cinq, quatre et six.
- Aucune nouvelle offre avant les verdicts du 30/11 au 06/12.
- Aucune dépense : le budget supplémentaire est de 0 €, et l'enveloppe de SOVEREIGN vaut 10 % de 0 €.
- Aucun envoi, aucune publication et aucune création de prix sans l'accord du propriétaire.

## Décisions à prendre plus tard, sans urgence

- Archiver chez le prestataire les produits zombies (Velyx, Velyx Pro, Velyx Business, Textes alternatifs) : un
  acheteur pourrait payer une offre abandonnée.
- Archiver les dépôts 1, A et All, repris dans Tr (proposition déjà faite par NOVARYS).
- Choisir un nom par chose (D8 de NOVARYS) : « Novarys » désigne aujourd'hui trois choses internes et huit
  entreprises homonymes.
- Corriger le test daté de VELYX (audit, § 4), dans le dépôt VELYX.
