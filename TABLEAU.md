# Tableau de bord commercial de l'entreprise mère (public)

> Généré par `python3 -m mere tableau` le 2026-11-24T20:01+00:00 (jour évalué : 2026-11-24). Ne pas modifier à la main.
> Version publique : les montants sont dans `prive/TABLEAU_PRIVE.md`, jamais versionnés.

## Verdict

**Premier euro : non atteint** (PROUVÉ par le prestataire de paiement). Conflits ouverts : 0. Alertes : 4.

## Indicateurs obligatoires (toute l'entreprise)

| Indicateur | Valeur | Statut | Sources | Note |
|---|---:|---|---|---|
| Visiteurs | — | INCONNU | compteur | à activer sur les pages d'offre avant toute campagne |
| Prospects contactés | 26 | PROUVÉ | pipeline |  |
| Envois bloqués par un filtre | 1 | PROUVÉ | pipeline |  |
| Réponses | 0 | PROUVÉ | pipeline |  |
| Prospects qualifiés | 0 | PROUVÉ | pipeline |  |
| Conversions (proposition acceptée) | 0 | PROUVÉ | pipeline |  |
| Ventes payées | 0 | PROUVÉ | stripe |  |
| Paiements échoués | 2 | ÉCHEC | stripe | carte de test en mode réel; generic_decline |
| Remboursements | [privé] | PROUVÉ | stripe |  |
| Coûts directs | — | INCONNU | couts | aucun journal des coûts |
| Frais de paiement | [privé] | PROUVÉ | stripe |  |
| Bénéfice net (hors temps) | — | INCONNU | mere | une composante n'est pas prouvée |
| CA annoncé (factures non payées) | [privé] | PROUVÉ | stripe | annoncé, non encaissé |
| Argent encaissé net | [privé] | PROUVÉ | stripe |  |
| Abonnements actifs | 0 | PROUVÉ | stripe |  |
| Offres avec un prix actif | 7 | PROUVÉ | stripe |  |

## La chaîne, opportunité par opportunité

PROUVÉ = étape franchie avec preuve · INCONNU = pas encore prouvé · ÉCHEC = critère d'arrêt manqué · CONFLIT = sources contradictoires. Distance = étapes non prouvées avant l'argent encaissé.

| Opportunité | Statut mère | Opportunité | Produit | Offre | Acheteur | Vente | Encaissé | Amélioration | Croissance | Distance |
|---|---|---|---|---|---|---|---|---|---|---:|
| **Obligato, affichages obligatoires pré-remplis par SIRET** (`obligato`, strat-ge-business) | actif | PROUVÉ | PROUVÉ | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 4 |
| **Novarys Conformité, vérification de fichiers de prospection** (`novarys-conformite`, strat-ge-business) | actif | PROUVÉ | PROUVÉ | PROUVÉ | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 3 |
| **VELYX, nouvelles entreprises du BTP pour courtiers en décennale** (`velyx-btp`, velyx) | test | PROUVÉ | ÉCHEC | PROUVÉ | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 4 |
| **Créations d'entreprises par département pour experts-comptables** (`creations-ec`, non déclaré) | test | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 6 |
| **Pilote de conformité Google Merchant Center** (`conformite-gmc`, non déclaré) | test | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 6 |
| **Alll, livret « L'histoire de votre maison »** (`alll-livret`, alll) | gele | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 6 |

Détail des étapes :

- `obligato` : Opportunité : demande mesurée : Service Public F23106 (obligation pour tout employeur) ; packs déjà vendus sur le marché (boutique/ETUDE_MARCHE.md) · Produit : suite de tests rejouée · Offre : 0 prix actif(s) · Acheteur : contactés 10, réponses 0, qualifiés 0 · Vente : 0 vente(s) payée(s) · Encaissé : montant en privé · Amélioration : 0 verdict(s) rendu(s) · Croissance : au moins 2 ventes payées
- `novarys-conformite` : Opportunité : demande mesurée : novarys/echantillons/*_stats.json : 77 % d'oppositions sur 736 sociétés · Produit : suite de tests rejouée · Offre : 2 prix actif(s) · Acheteur : contactés 0, réponses 0, qualifiés 0 · Vente : 0 vente(s) payée(s) · Encaissé : montant en privé · Amélioration : 0 verdict(s) rendu(s) · Croissance : au moins 2 ventes payées
- `velyx-btp` : Opportunité : demande mesurée : Code des assurances L241-1 (décennale obligatoire) ; prix de leads relevés par le dépôt VELYX (reports/) · Produit : suite en échec · Offre : 1 prix actif(s) · Acheteur : contactés 7, réponses 0, qualifiés 0 · Vente : 0 vente(s) payée(s) · Encaissé : montant en privé · Amélioration : aucune prévision chiffrée rattachée : rien à apprendre · Croissance : au moins 2 ventes payées
- `creations-ec` : Opportunité : demande non mesurée · Produit : aucun rejeu sur le commit actuel · Offre : ? prix actif(s) · Acheteur : contactés 8, réponses 0, qualifiés 0 · Vente : 0 vente(s) payée(s) · Encaissé : montant en privé · Amélioration : aucune prévision chiffrée rattachée : rien à apprendre · Croissance : au moins 2 ventes payées
- `conformite-gmc` : Opportunité : demande non mesurée · Produit : aucun rejeu sur le commit actuel · Offre : ? prix actif(s) · Acheteur : contactés 1, réponses 0, qualifiés 0 · Vente : 0 vente(s) payée(s) · Encaissé : montant en privé · Amélioration : aucune prévision chiffrée rattachée : rien à apprendre · Croissance : au moins 2 ventes payées
- `alll-livret` : Opportunité : demande non mesurée · Produit : aucun rejeu sur le commit actuel · Offre : ? prix actif(s) · Acheteur : contactés 0, réponses 0, qualifiés 0 · Vente : 0 vente(s) payée(s) · Encaissé : montant en privé · Amélioration : aucune prévision chiffrée rattachée : rien à apprendre · Croissance : au moins 2 ventes payées

## Priorités vers le premier euro

Ordre : opportunités actives avant les tests en attente de verdict, puis distance à l'argent, échéance la plus proche, score prouvé (seules les notes mesurées comptent).

1. **Novarys Conformité, vérification de fichiers de prospection** : distance 3, score prouvé 2/30, score avec hypothèses 15/30, confiance 17 %. Prochaine action : Constater et dater les envois des lots J1 à J3 dans le pipeline : aucun n'est retrouvé dans la messagerie (responsable : propriétaire (envois) ; businessman (diagnostics)).
2. **Obligato, affichages obligatoires pré-remplis par SIRET** : distance 4, score prouvé 7/30, score avec hypothèses 17/30, confiance 33 %. Prochaine action : Valider le défi anti-spam en attente, relancer les 10 cabinets le 28/11, créer le prix Stripe avant la première réponse positive (responsable : propriétaire (envois, relances) ; businessman (préparation)).
3. **VELYX, nouvelles entreprises du BTP pour courtiers en décennale** : distance 4, score prouvé 4/30, score avec hypothèses 14/30, confiance 33 %. Prochaine action : Laisser courir les 7 envois du 21/11 jusqu'au verdict du 05/12, répondre à tout retour, aucun nouvel envoi (responsable : propriétaire (réponses) ; VELYX (échantillons)).
4. **Créations d'entreprises par département pour experts-comptables** : distance 6, score prouvé 1/30, score avec hypothèses 7/30, confiance 17 %. Prochaine action : Rattacher cette offre à un module et à un registre ; laisser courir les 8 envois jusqu'au 05/12 sans nouvel envoi (responsable : propriétaire (réponses)).
5. **Pilote de conformité Google Merchant Center** : distance 6, score prouvé 0/30, score avec hypothèses 7/30, confiance 0 %. Prochaine action : Rattacher l'offre à un module ; attendre la réponse du seul prospect contacté jusqu'au 06/12 (responsable : propriétaire (réponse)).

Hors priorité (gelé ou arrêté par la mère) : Alll, livret « L'histoire de votre maison » (gele).

## Les six critères de chaque opportunité

Nature : m = mesuré (source citée), c = calcul, h = hypothèse.

| Opportunité | Demande réelle | Concurrence | Marge | Coût d'acquisition | Vitesse de vente | Potentiel | Prouvé | Total |
|---|---|---|---|---|---|---|---:|---:|
| Obligato, affichages obligatoires pré-remplis par SIRET | 4 m | 3 m | 4 c | 2 h | 1 h | 3 h | 7 | 17 |
| Novarys Conformité, vérification de fichiers de prospection | 2 m | 3 h | 4 c | 2 h | 1 h | 3 h | 2 | 15 |
| VELYX, nouvelles entreprises du BTP pour courtiers en décennale | 3 m | 3 h | 4 c | 2 h | 1 h | 1 m | 4 | 14 |
| Créations d'entreprises par département pour experts-comptables | 0 h | 0 h | 4 c | 1 h | 1 h | 1 m | 1 | 7 |
| Pilote de conformité Google Merchant Center | 0 h | 0 h | 3 h | 1 h | 1 h | 2 h | 0 | 7 |
| Alll, livret « L'histoire de votre maison » | 0 h | 2 h | 4 c | 1 h | 1 h | 2 h | 0 | 10 |

## Critères d'arrêt et verdicts

| Opportunité | Critère | Date | Mesure | Statut | Détail | Si échec |
|---|---|---|---:|---|---|---|
| obligato | Au moins une réponse des cabinets contactés (alerte J+7 de la mère) (seuil ≥ 1) | 2026-12-01 | 0 | INCONNU | en attente, J-7 | Revoir l'objet et le canal avant toute relance groupée ; ne pas élargir la liste |
| obligato | Au moins 3 paiements dans les 30 jours suivant le premier envoi (D-20261124-1) (seuil ≥ 3) | 2026-12-24 | 0 | INCONNU | en attente, J-30 | Pas de réactivation de la boutique ; pivot si moins de 3 personnes prêtes à payer sur 30 conversations |
| obligato | P-20261124-1 : Obligato : paiements Stripe reçus en prévente, si l'étape 2 démarre avant le 10/12 (D-20261124-1) | 2027-01-15 | — | INCONNU | en attente |  |
| obligato | P-20261124-2 : Obligato : testeurs prêts à payer au moins 39 € HT, sur 20 packs gratuits envoyés (D-20261124-1) | 2027-01-15 | — | INCONNU | en attente |  |
| novarys-conformite | Au moins une réponse sur les 20 cibles prioritaires (D-20261123-2 exige une réponse positive : à qualifier) (seuil ≥ 1) | 2026-11-30 | 0 | INCONNU | en attente, J-6 | Revoir l'angle de la loi du 30/06/2025 |
| novarys-conformite | Au moins 2 clients payants (D-20261123-1) (seuil ≥ 2) | 2026-12-04 | 0 | INCONNU | en attente, J-10 | Moins de 3 diagnostics : arrêt et plan B ; des diagnostics sans vente : repositionnement en audit pour le DPO |
| novarys-conformite | P-20261123-1 : Novarys : diagnostics demandés (D-20261123-1) | 2026-12-04 | — | INCONNU | en attente |  |
| novarys-conformite | P-20261123-2 : Novarys : clients payants (D-20261123-1) | 2026-12-04 | — | INCONNU | en attente |  |
| novarys-conformite | P-20261123-3 : Novarys : réponses positives (diagnostic demandé) sur les 20 e-mails prioritaires (angle loi du 30/06/2025) | 2026-11-30 | — | INCONNU | en attente |  |
| velyx-btp | Au moins une réponse 14 jours après les envois (ADR 0002 de NOVARYS) (seuil ≥ 1) | 2026-12-05 | 0 | INCONNU | en attente, J-11 | Arrêt de l'offre BTP aux courtiers ; ne pas insister sur la même cible |
| creations-ec | Au moins une réponse 14 jours après les envois (seuil ≥ 1) | 2026-12-05 | 0 | INCONNU | en attente, J-11 | Clore sans relance ; l'offre n'a ni registre ni étude |
| conformite-gmc | Une réponse 14 jours après l'envoi (seuil ≥ 1) | 2026-12-06 | 0 | INCONNU | en attente, J-12 | Clore |

## Conflits à résoudre

Aucun.

## Alertes

- registre de velyx en retard : 0 envoi(s) déclaré(s) au 2026-11-21, 7 prospect(s) contacté(s) depuis, non enregistré(s)
- creations-ec : aucun registre de module ne déclare cette offre (responsable : non déclaré)
- conformite-gmc : aucun registre de module ne déclare cette offre (responsable : non déclaré)
- novarys-conformite : active, mais aucun envoi ces 14 derniers jours

Statuts déclarés par les registres des modules : `novarys-conformite` : actif, `obligato` : actif, `velyx-btp` : test.

## Sources lues dans ce passage

| Source | État | Détail |
|---|---|---|
| dépôt strat-ge-business | trouvé |  |
| dépôt novarys | trouvé |  |
| dépôt sovereign | trouvé |  |
| dépôt hive | trouvé |  |
| dépôt velyx | trouvé |  |
| dépôt tr | trouvé |  |
| prévisions (poste business) | lu | 6 prévision(s) |
| pipeline commercial (privé) | lu | 27 événement(s) |
| journal des coûts (privé) | absent |  |
| prestataire de paiement | relevé privé du 2026-11-24 | relancer avec --stripe |
| rejeux des suites de tests | dernier état | 6 suite(s) |
| tableau novarys | lu |  |
| kpi velyx | lu |  |
