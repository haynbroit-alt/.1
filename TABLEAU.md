# Tableau de bord commercial de l'entreprise mère (public)

> Généré par `python3 -m mere tableau` le 2026-11-25T17:07+00:00 (jour évalué : 2026-11-25). Ne pas modifier à la main.
> Version publique : les montants sont dans `prive/TABLEAU_PRIVE.md`, jamais versionnés.

## Verdict

**Premier euro : non atteint (PROUVÉ : aucun paiement réussi chez le prestataire)**. Conflits ouverts : 0. Alertes : 2.

Niveaux de l'argent : paiement réussi → 0 vente(s) · rapprochement grand livre → PROUVÉ · versé vers la banque → PROUVÉ · crédité en banque → PROUVÉ (aucun virement versé : rien à créditer).

## Trois réussites à ne pas confondre

Seule la réussite commerciale fait avancer une opportunité vers l'argent. L'activité ne prouve rien ; la réussite technique prouve qu'un outil marche, pas qu'il se vend.

| Niveau | Mesure | Valeur |
|---|---|---|
| Activité | Prospects contactés | — (INCONNU) |
| Activité | Offres avec un prix actif | 7 (PROUVÉ) |
| Activité | Contrôles exécutés dans ce passage | 19 |
| Technique | Suites rejouées deux fois en clone propre et vertes | 0/6 |
| Technique | Notes « mesuré » dont la source est confirmée | 0/6 |
| Technique | La mère contrôlée par NOVARYS Ω | INCONNU |
| Commercial | Prospects réels vérifiés | — (INCONNU) |
| Commercial | Réponses | — (INCONNU) |
| Commercial | Qualifiés et vérifiés réels | — (INCONNU) |
| Commercial | Ventes payées | 0 (PROUVÉ) |
| Commercial | Crédité en banque | [privé] (PROUVÉ) |

## Indicateurs obligatoires (toute l'entreprise)

| Indicateur | Valeur | Statut | Sources | Note |
|---|---:|---|---|---|
| Visiteurs | — | INCONNU | compteur | à activer sur les pages d'offre avant toute campagne |
| Prospects contactés | — | INCONNU | pipeline | aucun pipeline lisible |
| Prospects réels (vérifiés par le web public) | — | INCONNU | web-public |  |
| Envois bloqués par un filtre | — | INCONNU | — |  |
| Réponses | — | INCONNU | pipeline | aucun pipeline lisible |
| Prospects qualifiés | — | INCONNU | pipeline | aucun pipeline lisible |
| Qualifiés et vérifiés réels | — | INCONNU | — |  |
| Conversions (proposition acceptée) | — | INCONNU | pipeline | aucun pipeline lisible |
| Ventes payées | 0 | PROUVÉ | stripe |  |
| Paiements échoués | 2 | ÉCHEC | stripe | carte de test en mode réel; generic_decline |
| Remboursements | [privé] | PROUVÉ | stripe |  |
| Litiges de paiement ouverts | 0 | PROUVÉ | stripe |  |
| Coûts directs | — | INCONNU | couts | aucun journal des coûts |
| Frais de paiement | [privé] | PROUVÉ | stripe |  |
| Bénéfice net (hors temps) | — | INCONNU | mere | une composante n'est pas prouvée |
| CA annoncé (factures non payées) | [privé] | PROUVÉ | stripe | annoncé, non encaissé |
| Argent encaissé net | [privé] | PROUVÉ | stripe |  |
| Versé vers la banque (selon le prestataire) | [privé] | PROUVÉ | stripe |  |
| Crédité en banque (vérifié sur le relevé) | [privé] | PROUVÉ | banque |  |
| Abonnements actifs | 0 | PROUVÉ | stripe |  |
| Offres avec un prix actif | 7 | PROUVÉ | stripe |  |

## La chaîne, opportunité par opportunité

PROUVÉ = étape franchie avec preuve · INCONNU = pas encore prouvé · ÉCHEC = critère d'arrêt manqué · CONFLIT = sources contradictoires. Distance = étapes non prouvées avant l'argent encaissé.

| Opportunité | Statut mère | Opportunité | Produit | Offre | Acheteur | Vente | Encaissé | Amélioration | Croissance | Distance |
|---|---|---|---|---|---|---|---|---|---|---:|
| **Obligato, affichages obligatoires remplis pour vous** (`obligato`, strat-ge-business) | actif | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 6 |
| **Novarys Conformité, vérification de fichiers de prospection** (`novarys-conformite`, strat-ge-business) | gele | INCONNU | INCONNU | PROUVÉ | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 5 |
| **VELYX, nouvelles entreprises du BTP pour courtiers en décennale** (`velyx-btp`, velyx) | test | INCONNU | INCONNU | PROUVÉ | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 5 |
| **Créations d'entreprises par département pour experts-comptables** (`creations-ec`, non déclaré) | test | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 6 |
| **Pilote de conformité Google Merchant Center** (`conformite-gmc`, non déclaré) | test | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 6 |
| **Alll, livret « L'histoire de votre maison »** (`alll-livret`, alll) | gele | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | INCONNU | 6 |

Détail des étapes :

- `obligato` : Opportunité : demande mesurée : Service Public F23106 : affichages obligatoires pour tout employeur, mais source non confirmée : PROUVÉ au passage du 2026-11-24, non refait dans ce passage · Produit : dépôt modifié depuis le rejeu : le code présent n'est pas celui qui a été testé · Offre : 0 prix actif(s) · Acheteur : contactés ? (dont réels vérifiés ?), réponses ?, qualifiés ? (vérifiés ?) · Vente : 0 vente(s) payée(s) · Encaissé : aucun argent reçu · Amélioration : 0 verdict(s) rendu(s), aucun confirmé par la mesure · Croissance : au moins 2 ventes payées
- `novarys-conformite` : Opportunité : demande mesurée : novarys/echantillons/novarys_btp_FR_7j_stats.json : 79,6 % des créations BTP vérifiées ont fait opposition, mais source non confirmée : 0.796 conforme aux données internes ; ce n'est pas une source indépendante · Produit : dépôt modifié depuis le rejeu : le code présent n'est pas celui qui a été testé · Offre : 2 prix actif(s) · Acheteur : contactés ? (dont réels vérifiés ?), réponses ?, qualifiés ? (vérifiés ?) · Vente : 0 vente(s) payée(s) · Encaissé : aucun argent reçu · Amélioration : 0 verdict(s) rendu(s), aucun confirmé par la mesure · Croissance : au moins 2 ventes payées
- `velyx-btp` : Opportunité : demande mesurée : Code des assurances, art. L241-1 (décennale obligatoire), mais source non confirmée : relancer avec --controler (note modifiée ou jamais contrôlée) · Produit : rejeu ancien ou unique, hors clone propre : à refaire avec --rejouer · Offre : 1 prix actif(s) · Acheteur : contactés ? (dont réels vérifiés ?), réponses ?, qualifiés ? (vérifiés ?) · Vente : 0 vente(s) payée(s) · Encaissé : aucun argent reçu · Amélioration : aucune prévision chiffrée rattachée : rien à apprendre · Croissance : au moins 2 ventes payées
- `creations-ec` : Opportunité : demande non mesurée · Produit : aucun rejeu sur le commit actuel · Offre : ? prix actif(s) · Acheteur : contactés ? (dont réels vérifiés ?), réponses ?, qualifiés ? (vérifiés ?) · Vente : 0 vente(s) payée(s) · Encaissé : aucun argent reçu · Amélioration : aucune prévision chiffrée rattachée : rien à apprendre · Croissance : au moins 2 ventes payées
- `conformite-gmc` : Opportunité : demande non mesurée · Produit : aucun rejeu sur le commit actuel · Offre : ? prix actif(s) · Acheteur : contactés ? (dont réels vérifiés ?), réponses ?, qualifiés ? (vérifiés ?) · Vente : 0 vente(s) payée(s) · Encaissé : aucun argent reçu · Amélioration : aucune prévision chiffrée rattachée : rien à apprendre · Croissance : au moins 2 ventes payées
- `alll-livret` : Opportunité : demande non mesurée · Produit : aucun rejeu sur le commit actuel · Offre : ? prix actif(s) · Acheteur : contactés ? (dont réels vérifiés ?), réponses ?, qualifiés ? (vérifiés ?) · Vente : 0 vente(s) payée(s) · Encaissé : aucun argent reçu · Amélioration : aucune prévision chiffrée rattachée : rien à apprendre · Croissance : au moins 2 ventes payées

## Priorités vers le premier euro

Ordre : opportunités actives avant les tests en attente de verdict, puis distance à l'argent, échéance la plus proche, score prouvé (seules les notes mesurées comptent).

1. **Obligato, affichages obligatoires remplis pour vous** : distance 6, score prouvé 0/30, score avec hypothèses 17/30, confiance 0 %. Prochaine action : D-20261125-1 : créer le lien de paiement (propriétaire), 30 conversations directes du 27/11 au 03/12, appeler les 10 cabinets le 28/11 au lieu de les relancer par e-mail (responsable : propriétaire (envois, relances) ; businessman (préparation)).
2. **VELYX, nouvelles entreprises du BTP pour courtiers en décennale** : distance 5, score prouvé 0/30, score avec hypothèses 14/30, confiance 0 %. Prochaine action : Abandon décidé le 25/11 (D-20261125-1) : répondre à tout retour jusqu'au 05/12, puis arrêt (responsable : propriétaire (réponses) ; VELYX (échantillons)).
3. **Créations d'entreprises par département pour experts-comptables** : distance 6, score prouvé 0/30, score avec hypothèses 8/30, confiance 0 %. Prochaine action : Abandon décidé le 25/11 (D-20261125-1) : répondre à tout retour jusqu'au 05/12, puis arrêt (responsable : propriétaire (réponses)).
4. **Pilote de conformité Google Merchant Center** : distance 6, score prouvé 0/30, score avec hypothèses 7/30, confiance 0 %. Prochaine action : Rattacher l'offre à un module ; attendre la réponse du seul prospect contacté jusqu'au 06/12 (responsable : propriétaire (réponse)).

Hors priorité (gelé ou arrêté par la mère) : Novarys Conformité, vérification de fichiers de prospection (gele), Alll, livret « L'histoire de votre maison » (gele).

## Les six critères de chaque opportunité

Nature : m = mesuré (source citée), c = calcul, h = hypothèse.

| Opportunité | Demande réelle | Concurrence | Marge | Coût d'acquisition | Vitesse de vente | Potentiel | Prouvé | Total |
|---|---|---|---|---|---|---|---:|---:|
| Obligato, affichages obligatoires remplis pour vous | 4 m | 3 m | 4 c | 2 h | 1 h | 3 h | 0 | 17 |
| Novarys Conformité, vérification de fichiers de prospection | 2 m | 3 h | 4 c | 2 h | 1 h | 3 h | 0 | 15 |
| VELYX, nouvelles entreprises du BTP pour courtiers en décennale | 3 m | 3 h | 4 c | 2 h | 1 h | 1 m | 0 | 14 |
| Créations d'entreprises par département pour experts-comptables | 0 h | 0 h | 4 c | 1 h | 1 h | 2 m | 0 | 8 |
| Pilote de conformité Google Merchant Center | 0 h | 0 h | 3 h | 1 h | 1 h | 2 h | 0 | 7 |
| Alll, livret « L'histoire de votre maison » | 0 h | 2 h | 4 c | 1 h | 1 h | 2 h | 0 | 10 |

## Critères d'arrêt et verdicts

| Opportunité | Critère | Date | Mesure | Statut | Détail | Si échec |
|---|---|---|---:|---|---|---|
| obligato | Au moins une réponse des cabinets contactés (alerte J+7 de la mère) (seuil ≥ 1) | 2026-12-01 | — | INCONNU | en attente, J-6 | Revoir l'objet et le canal avant toute relance groupée ; ne pas élargir la liste |
| obligato | Au moins 3 paiements dans les 30 jours suivant le premier envoi (D-20261124-1) (seuil ≥ 3) | 2026-12-24 | 0 | INCONNU | en attente, J-29 | Pas de réactivation de la boutique ; pivot si moins de 3 personnes prêtes à payer sur 30 conversations |
| obligato | Au moins 1 paiement après 30 conversations directes (D-20261125-1) (seuil ≥ 1) | 2026-12-09 | 0 | INCONNU | en attente, J-14 | Arrêt d'Obligato en direct ; on garde le générateur et l'on ne construit rien de nouveau |
| obligato | P-20261124-1 : Obligato : paiements Stripe reçus en prévente, si l'étape 2 démarre avant le 10/12 (D-20261124-1) | 2027-01-15 | — | INCONNU | en attente |  |
| obligato | P-20261124-2 : Obligato : testeurs prêts à payer au moins 39 € HT, sur 20 packs gratuits envoyés (D-20261124-1) | 2027-01-15 | — | INCONNU | en attente |  |
| obligato | P-20261125-1 : Obligato remplis pour vous : paiements reçus après 30 conversations directes (D-20261125-1) | 2026-12-09 | — | INCONNU | en attente |  |
| novarys-conformite | Au moins une réponse sur les 20 cibles prioritaires (D-20261123-2 exige une réponse positive : à qualifier) (seuil ≥ 1) | 2026-11-30 | — | INCONNU | en attente, J-5 | Revoir l'angle de la loi du 30/06/2025 |
| novarys-conformite | Au moins 2 clients payants (D-20261123-1) (seuil ≥ 2) | 2026-12-04 | 0 | INCONNU | en attente, J-9 | Moins de 3 diagnostics : arrêt et plan B ; des diagnostics sans vente : repositionnement en audit pour le DPO |
| novarys-conformite | P-20261123-1 : Novarys : diagnostics demandés (D-20261123-1) | 2026-12-04 | — | INCONNU | en attente |  |
| novarys-conformite | P-20261123-2 : Novarys : clients payants (D-20261123-1) | 2026-12-04 | — | INCONNU | en attente |  |
| novarys-conformite | P-20261123-3 : Novarys : réponses positives (diagnostic demandé) sur les 20 e-mails prioritaires (angle loi du 30/06/2025) | 2026-11-30 | — | INCONNU | en attente |  |
| velyx-btp | Au moins une réponse 14 jours après les envois (ADR 0002 de NOVARYS) (seuil ≥ 1) | 2026-12-05 | — | INCONNU | en attente, J-10 | Arrêt de l'offre BTP aux courtiers ; ne pas insister sur la même cible |
| creations-ec | Au moins une réponse 14 jours après les envois (seuil ≥ 1) | 2026-12-05 | — | INCONNU | en attente, J-10 | Clore sans relance ; l'offre n'a ni registre ni étude |
| conformite-gmc | Une réponse 14 jours après l'envoi (seuil ≥ 1) | 2026-12-06 | — | INCONNU | en attente, J-11 | Clore |

## Contrôles indépendants de ce passage

Aucun producteur ne se contrôle lui-même : chaque ligne nomme qui affirme et qui vérifie.

| Contrôle | Producteur → contrôleur | Méthode | Statut | Détail |
|---|---|---|---|---|
| La source de la note « demande » de obligato dit ce que la note affirme | portefeuille → page-publique | la phrase citée figure dans la page | INCONNU | PROUVÉ au passage du 2026-11-24, non refait dans ce passage |
| La source de la note « concurrence » de obligato dit ce que la note affirme | portefeuille → page-publique | la phrase citée figure dans la page | INCONNU | PROUVÉ au passage du 2026-11-24, non refait dans ce passage |
| La source de la note « demande » de novarys-conformite dit ce que la note affirme | portefeuille → donnees | taux_opposition_btp relu dans le fichier versionné | INCONNU | 0.796 conforme aux données internes ; ce n'est pas une source indépendante |
| La source de la note « demande » de velyx-btp dit ce que la note affirme | portefeuille → page-publique | non relancé | INCONNU | relancer avec --controler (note modifiée ou jamais contrôlée) |
| La source de la note « potentiel » de velyx-btp dit ce que la note affirme | portefeuille → donnees | btp_gardes relu dans le fichier versionné | INCONNU | 38 conforme aux données internes ; ce n'est pas une source indépendante |
| La source de la note « potentiel » de creations-ec dit ce que la note affirme | portefeuille → donnees | secteur_gardes relu dans le fichier versionné | INCONNU | 59 conforme aux données internes ; ce n'est pas une source indépendante |
| Le pipeline contient tous les envois de la messagerie | pipeline → recomptage-independant | second relevé de la messagerie | INCONNU | aucun second relevé |
| Chaque paiement réussi figure au grand livre du prestataire, même montant | mere:releve-paiements → stripe:grand-livre | contrôle croisé /v1/charges contre /v1/balance_transactions | PROUVÉ | 0 paiement(s) réussi(s) rapproché(s) |
| L'argent versé par le prestataire est crédité en banque | stripe → banque | rapprochement montant exact et date ± 4 jours | PROUVÉ | aucun virement versé : rien à créditer |
| La suite de tests de strat-ge-business passe | strat-ge-business → mere:clone-propre | 2 exécution(s) dans un clone neuf du commit, bilans comparés | INCONNU | dépôt modifié depuis le rejeu : le code présent n'est pas celui qui a été testé |
| La suite de tests de sovereign passe | sovereign → mere:clone-propre | 0 exécution(s) dans un clone neuf du commit, bilans comparés | INCONNU | rejeu ancien ou unique, hors clone propre : à refaire avec --rejouer |
| La suite de tests de novarys passe | novarys → mere:clone-propre | 0 exécution(s) dans un clone neuf du commit, bilans comparés | INCONNU | rejeu ancien ou unique, hors clone propre : à refaire avec --rejouer |
| La suite de tests de hive passe | hive → mere:clone-propre | 0 exécution(s) dans un clone neuf du commit, bilans comparés | INCONNU | rejeu ancien ou unique, hors clone propre : à refaire avec --rejouer |
| La suite de tests de velyx passe | velyx → mere:clone-propre | 0 exécution(s) dans un clone neuf du commit, bilans comparés | INCONNU | rejeu ancien ou unique, hors clone propre : à refaire avec --rejouer |
| La suite de tests de tr passe | tr → mere:clone-propre | 0 exécution(s) dans un clone neuf du commit, bilans comparés | INCONNU | rejeu ancien ou unique, hors clone propre : à refaire avec --rejouer |
| La mère est contrôlée par un autre module | mere → novarys | protocole de preuve Ω | INCONNU | registre de NOVARYS absent de cette machine |
| Le registre de strat-ge-business décrit obligato comme il est | strat-ge-business → pipeline | statut déclaré contre envois des 14 derniers jours | INCONNU | déclaré « actif », 0 envoi(s) récent(s) |
| Le registre de strat-ge-business décrit novarys-conformite comme il est | strat-ge-business → pipeline | statut déclaré contre envois des 14 derniers jours | INCONNU | déclaré « gele », 0 envoi(s) récent(s) |
| Le registre de strat-ge-business décrit velyx-btp comme il est | strat-ge-business → pipeline | statut déclaré contre envois des 14 derniers jours | INCONNU | déclaré « test », 0 envoi(s) récent(s) |

## Conflits à résoudre

Aucun.

## Alertes

- creations-ec : aucun registre de module ne déclare cette offre (responsable : non déclaré)
- conformite-gmc : aucun registre de module ne déclare cette offre (responsable : non déclaré)

Statuts déclarés par les registres des modules : `novarys-conformite` : gele, `obligato` : actif, `velyx-btp` : test.

## Sources lues dans ce passage

| Source | État | Détail |
|---|---|---|
| dépôt strat-ge-business | trouvé |  |
| dépôt novarys | absent |  |
| dépôt sovereign | absent |  |
| dépôt hive | absent |  |
| dépôt velyx | absent |  |
| dépôt tr | absent |  |
| prévisions (poste business) | lu | 7 prévision(s) |
| pipeline commercial (privé) | absent | 0 événement(s) |
| journal des coûts (privé) | absent |  |
| prestataire de paiement | lu en direct |  |
| suites de tests | rejouées en clone propre | 6 suite(s) |
| tableau novarys | absent ou vide |  |
| kpi velyx | absent ou vide |  |
