# Architecture de l'entreprise mère

L'entreprise mère n'est pas un nouvel agent. C'est une **couche de lecture et de rapprochement** au-dessus des
modules existants. Elle lit ce que chacun publie, rapproche les déclarations de la source qui fait foi, et dit, pour
chaque opportunité, quelle étape de la chaîne est prouvée. Aucun module n'importe le code d'un autre, et aucun ne
dépend de la mère : si elle disparaît, chacun continue de fonctionner.

```
                         PROPRIÉTAIRE : décide, envoie, encaisse, valide toute action externe
                                                  ▲
                 TABLEAU.md (public) · prive/TABLEAU_PRIVE.md · conflits · alertes · priorités
                                                  │
 ┌──────────────────────────────── ENTREPRISE MÈRE (.1 / mere) ─────────────────────────────────┐
 │  adaptateurs en lecture seule → faits (contrat commun) → consolidation → rapprochement →       │
 │  chaîne en 8 étapes → critères d'arrêt → priorités ; garde anti-fuite avant toute sortie       │
 └──────▲──────────────▲───────────────▲───────────────▲────────────────▲──────────────▲──────────┘
        │ prévisions,  │ portail,      │ registre      │ suites de      │ paiements,   │ envois et
        │ registre des │ actifs        │ d'envois      │ tests rejouées │ factures     │ réponses
        │ projets      │               │               │                │ (GET seul)   │ (pipeline privé)
   Poste business    NOVARYS          VELYX     SOVEREIGN · HIVE · Tr    Prestataire     Messagerie
   (Strat-ge-business)                                                 de paiement
```

## Les sept fonctions, et qui les tient

| Fonction | Module responsable | Ce qui existe et sert | Ce que la mère mesure |
|---|---|---|---|
| Recherche de marchés | VELYX ; poste business (`references/recherche.md`, `generer_fichier.py`) | Demande publiée, registre SIRENE, oppositions | Critère « demande réelle » : mesuré ou non |
| Invention | SOVEREIGN (Skills innovation et développement commercial) ; CORTEX, GALILÉE, LAVOISIER en expertise | Classement d'opportunités, matrice d'Ansoff, plans de lancement | Les six critères de chaque opportunité, étiquetés |
| Direction commerciale | NOVARYS (REACHER) avec la méthode du businessman (poste business) | Méthode, kits de vente, 13 skills de vente audités | Prospects contactés, réponses, qualifiés, conversions |
| Production | Poste business (Obligato, vérificateur de fichiers) ; VELYX (échantillons) ; HIVE (Studio) | Générateurs testés | Étape « produit » : suite de tests rejouée sur le commit actuel |
| Distribution | Prestataire de paiement, messagerie, portail NOVARYS | Produits et prix, envois | Étape « offre » : un prix actif existe |
| Finance | SOVEREIGN (registre, règle des 10 %) ; prestataire de paiement (source qui fait foi) | Calculateurs du poste business | Encaissé net, remboursements, frais, coûts, bénéfice net |
| Amélioration continue | Poste business (journal, prévisions, calibration, banc) ; NOVARYS Ω (preuves) | Prévisions datées | Verdicts dus et rendus ; une prévision échue sans résultat est un ÉCHEC |

**Gouvernance.**
- SOVEREIGN **dirige**. Ses règles tranchent la dépense : 10 % de l'encaissé réel, soit 0 € aujourd'hui. Son
  classement arbitre le portefeuille.
- HIVE **coordonne** les tâches et les validations humaines.
- NOVARYS Ω **contrôle** les preuves ; ce partage du contrôle avec HIVE est un écart à la mission, signalé en
  CONFLIT C5 de l'audit.
- NOVARYS **porte** les compétences commerciales.
- Les moteurs de recherche **apportent leur expertise** sur demande.
- La mère **rapproche**. Elle ne décide rien : elle rend visibles les faits, les conflits et les verdicts dus.

## Le contrat commun : un fait

Chaque module partage ses résultats sous une forme unique (`mere/faits.py`). Il peut l'écrire lui-même en JSONL,
ou laisser un adaptateur la lire dans ses fichiers.

| Champ | Sens |
|---|---|
| `module` | Qui a produit le fait (`stripe`, `pipeline`, `strat-ge-business`, `rejeu:sovereign`…) |
| `indicateur` | Un nom de la liste fermée `INDICATEURS` (21 indicateurs, chacun rattaché à une étape) |
| `valeur` | Nombre, texte ou booléen ; **montants en centimes entiers**, jamais de flottant |
| `statut` | PROUVÉ, INCONNU, CONFLIT ou ÉCHEC |
| `source`, `preuve` | Où le lire, et la référence qui le vérifie. **PROUVÉ sans preuve est refusé** |
| `opportunite` | L'identifiant du portefeuille, `*` pour toute l'entreprise, `module:<nom>`, `declaration:<module>` |
| `date`, `note` | Date de la mesure ; limites ou motifs |
| `prive` | Vrai pour tout montant : jamais dans une sortie publique |

Sorties partagées : `etat/faits_publics.jsonl` (faits non privés, publics) et `prive/faits.jsonl` (tous les faits,
à importer par exemple dans le registre financier de SOVEREIGN).

## La chaîne et ses statuts

`opportunité → produit → offre → acheteur → vente → encaissé → amélioration → croissance`

| Étape | Franchie (PROUVÉ) quand | Source qui fait foi |
|---|---|---|
| Opportunité | La demande réelle est notée « mesuré » et sa source est confirmée par la page publique ou les données | Source citée |
| Produit | La suite du module, rejouée deux fois dans un clone neuf, est verte et concordante, sur le commit actuel | La mère (clone propre) |
| Offre | Au moins un prix actif chez le prestataire | Prestataire de paiement |
| Acheteur | Au moins un prospect qualifié **et vérifié réel**, chaque ligne du pipeline ayant sa preuve | Pipeline et web public |
| Vente | Au moins un paiement réussi, capturé, non contesté, en mode réel, rapproché du grand livre | Prestataire de paiement et son grand livre |
| Encaissé | Encaissé net supérieur à zéro **et** retrouvé au crédit du relevé bancaire (net des frais) | Banque |
| Amélioration | Au moins un verdict rendu ; un verdict échu non rendu donne ÉCHEC | Prévisions du poste business |
| Croissance | Au moins deux ventes payées | Prestataire de paiement |

Une étape passe en **ÉCHEC** quand un critère d'arrêt qui la concerne est manqué à sa date. Elle passe en
**CONFLIT** quand des sources se contredisent. Sinon elle reste **INCONNU** tant qu'elle n'est pas prouvée. La
**distance** compte les étapes non prouvées avant l'argent encaissé.

## Les règles adversariales (chacune a son test dans `tests/`)

1. Seul un paiement **réussi, en mode réel, dans la devise de l'entreprise, net de ses remboursements** compte. Une
   carte de test, un paiement en mode test, une autre devise, une facture ouverte (CA annoncé) ou un potentiel ne
   comptent jamais. Une autorisation non capturée, un paiement contesté ou un paiement non attribué non plus.
2. Une source illisible donne INCONNU, **jamais zéro**. Un coût inconnu n'est pas un coût nul : le bénéfice reste
   INCONNU.
3. L'accès au prestataire est **en lecture seule par construction** : uniquement des GET, sur cinq listes nommées.
4. Une déclaration d'encaissé ou d'envois qui diffère de la source qui fait foi **à la même date** est un CONFLIT.
   Le conflit est rangé sous `declaration:<module>` : c'est la déclaration qui est fausse, et l'argent prouvé reste
   prouvé. Un registre qui n'a pas enregistré les envois postérieurs à sa date est signalé « en retard ».
5. Un registre qui déclare gelée, arrêtée ou en préparation une offre qui envoie des messages est en CONFLIT : un
   prospect pourrait répondre sans que personne ne soit chargé de lui répondre.
6. Un critère d'arrêt échu et manqué donne ÉCHEC. Échu sans mesure, il donne une alerte « verdict dû sans mesure ».
   Une prévision échue sans résultat écrit est un ÉCHEC de la boucle d'apprentissage.
7. Le classement ne compte que les notes **mesurées** : une hypothèse ne fait jamais monter une opportunité. Les
   tests en attente de verdict passent après les opportunités actives.
8. Un rejeu ne prouve que son commit. Il tourne sans aucune variable d'environnement évoquant un secret, et s'il
   écrit dans le dépôt du module, il ne prouve rien.
9. Avant d'écrire une sortie publique, la garde refuse les adresses e-mail, les numéros de téléphone, les SIREN et
   SIRET, les identifiants du prestataire, les clés, les identifiants de message, et tout montant qui n'est pas un
   prix public déclaré.

## La boucle de vérification obligatoire

Chaque résultat suit le même cycle : **action → preuve → vérification indépendante → détection des erreurs →
correction → nouveau test**. La règle fondamentale est inscrite dans le code : un `Controle` dont le contrôleur est
le producteur est refusé à la construction (`AutoValidation`). Un contrôleur est indépendant quand le producteur ne
le maîtrise pas : une autorité externe, un autre module, une copie propre du dépôt, un autre lecteur ou le
propriétaire.

| Ce qui est affirmé | Producteur | Contrôleur indépendant | Méthode reproductible | Sinon |
|---|---|---|---|---|
| Un client a payé | lecture des paiements par la mère | grand livre du prestataire | `/v1/charges` contre `/v1/balance_transactions` : même paiement, même montant | CONFLIT |
| L'argent est encaissé | prestataire (virement « versé ») | banque | virement retrouvé au crédit du relevé du propriétaire (`prive/banque.csv`), montant exact, ± 4 jours | INCONNU sans relevé, CONFLIT si absent |
| Le paiement est acquis | prestataire | fiches de litige | litige ouvert : INCONNU ; perdu : retiré de l'encaissé | INCONNU |
| Un prospect existe | pipeline | web public | aucun rebond, et le site de son domaine répond | ÉCHEC si rebond, INCONNU sinon |
| Le pipeline est complet | agent qui l'a rempli | second lecteur de la messagerie | recomptage des envois, réponses, rebonds et défis anti-spam | CONFLIT |
| Une note « mesuré » est vraie | auteur du portefeuille | page d'une autorité publique, ou d'un tiers reconnu dans le code (pas dans le portefeuille) | la phrase citée figure dans la page, relue dans ce passage. Un texte rédigé ne prouve rien ; un fichier de données de l'écosystème peut révéler un CONFLIT, jamais prouver | ÉCHEC, CONFLIT ou INCONNU |
| La suite d'un module passe | le module | la mère, dans un clone neuf | deux exécutions du commit hors poste de travail, bilans concordants, au moins un test exécuté, dépôt d'origine inchangé | ÉCHEC, CONFLIT si discordant |
| Un registre dit vrai | le module (NOVARYS, VELYX, poste business) | prestataire et pipeline | rapprochement à la même date, en instants UTC, sur le périmètre de la déclaration | CONFLIT |
| La mère calcule juste | la mère | NOVARYS Ω | deux exécutions concordantes de la suite et attaques par mutation, au registre chaîné de NOVARYS | INCONNU tant que non prouvé |
| Le code de la mère est correct | l'agent qui l'a écrit | relecteur indépendant (autre agent, sans le contexte de l'auteur) | attaques reproduites par scripts, puis contre-vérification des corrections | — |

Ce qui reste hors de portée est affiché INCONNU, jamais deviné : visiteurs, coûts, crédit en banque sans relevé,
sources qui refusent la lecture automatisée. **Un contrôle ne vaut que dans le passage qui l'a fait.** Les résultats
d'un passage précédent sont relus pour mémoire. Ils ne sont jamais PROUVÉS, car la mère ne se fie pas à sa propre
mémoire. Seuls un CONFLIT ou un ÉCHEC déjà connus restent affichés.

**Trois réussites à ne pas confondre.** Le tableau les sépare :
- **l'activité** (envois, prix créés, contrôles lancés) ne prouve rien ;
- **la réussite technique** (suites reproduites, sources confirmées) prouve qu'un outil marche ;
- **la réussite commerciale** (prospects réels qui répondent, paiements rapprochés, argent crédité en banque) est
  la seule qui fasse avancer une opportunité vers l'argent.

**Historique.** Les preuves de la mère sont au registre chaîné de NOVARYS Ω ; les décisions, au journal du poste
business. Les erreurs et leurs corrections sont tenues cycle par cycle dans `journal/`. Les échecs y restent.

## Ajouter un module ou une opportunité

- **Une opportunité** : une entrée dans `donnees/portefeuille.toml`, avec ses six critères étiquetés et au moins un
  critère d'arrêt daté. `python3 -m mere verifier` refuse le reste.
- **Une source** : un chemin dans `donnees/sources.toml`. Si le format est nouveau, un adaptateur de lecture seule
  dans `mere/sources.py`, avec ses tests.
- **Une suite à rejouer** : une entrée `[[rejeu]]` avec sa commande et sa ligne de bilan. Elle ne doit rien écrire
  dans le dépôt du module.
