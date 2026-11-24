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
| Opportunité | La demande réelle est notée « mesuré » avec sa source | Portefeuille |
| Produit | La suite de tests du module est verte, ligne de bilan vue, **sur le commit actuel**, dépôt non modifié par le rejeu | Rejeu |
| Offre | Au moins un prix actif chez le prestataire | Prestataire de paiement |
| Acheteur | Au moins un prospect qualifié, chaque ligne du pipeline ayant sa preuve | Pipeline privé |
| Vente | Au moins un paiement réussi en mode réel, non remboursé en totalité | Prestataire de paiement |
| Encaissé | Encaissé net supérieur à zéro | Prestataire de paiement |
| Amélioration | Au moins un verdict rendu ; un verdict échu non rendu donne ÉCHEC | Prévisions du poste business |
| Croissance | Au moins deux ventes payées | Prestataire de paiement |

Une étape passe en **ÉCHEC** quand un critère d'arrêt qui la concerne est manqué à sa date. Elle passe en
**CONFLIT** quand des sources se contredisent. Sinon elle reste **INCONNU** tant qu'elle n'est pas prouvée. La
**distance** compte les étapes non prouvées avant l'argent encaissé.

## Les règles adversariales (chacune a son test dans `tests/`)

1. Seul un paiement **réussi, en mode réel, dans la devise de l'entreprise, net de ses remboursements** compte. Une
   carte de test, un paiement en mode test, une autre devise, une facture ouverte (CA annoncé) ou un potentiel ne
   comptent jamais.
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

## Ajouter un module ou une opportunité

- **Une opportunité** : une entrée dans `donnees/portefeuille.toml`, avec ses six critères étiquetés et au moins un
  critère d'arrêt daté. `python3 -m mere verifier` refuse le reste.
- **Une source** : un chemin dans `donnees/sources.toml`. Si le format est nouveau, un adaptateur de lecture seule
  dans `mere/sources.py`, avec ses tests.
- **Une suite à rejouer** : une entrée `[[rejeu]]` avec sa commande et sa ligne de bilan. Elle ne doit rien écrire
  dans le dépôt du module.
