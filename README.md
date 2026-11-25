# Programme de découverte

Un seul front à la fois. Chaque affirmation porte son statut : **imaginé**, **plausible**, **démontré** ou **réalisé**.

| Document | Contenu |
|---|---|
| [CHARTE.md](CHARTE.md) | Les règles du programme |
| [01_CHOIX_DU_PROBLEME.md](01_CHOIX_DU_PROBLEME.md) | Étape 0 : pourquoi le refroidissement passif en climat chaud et humide |
| [refroidissement/RESULTATS.md](refroidissement/RESULTATS.md) | Étapes 1 et 2 : le modèle physique, le levier qui domine, les limites |
| [refroidissement/ETAPE3.md](refroidissement/ETAPE3.md) | Étape 3 : une année réelle (NASA, 8 villes, nuages compris) et l'état des matériaux |
| [refroidissement/ETAPE4.md](refroidissement/ETAPE4.md) | Étape 4 : antériorité, concept retenu (un blanc à la chaux renouvelable), protocole d'expérience et prédiction enregistrée |

## Reproduire les résultats
Python 3.11 ou plus récent, bibliothèque standard seule :

```bash
cd refroidissement
python3 -m unittest test_modele test_annuel   # 22 tests
python3 experience.py                         # les tableaux de RESULTATS.md
python3 annuel.py                             # les tableaux de ETAPE3.md (--telecharger pour reprendre les données)
python3 prediction_experience.py              # la prédiction enregistrée de l'étape 4
```

**Front actuel** : en attente de l'accord du propriétaire pour la dépense de l'expérience de l'étape 4 (environ 67 à 125 €, plus la chaux). Aucun achat n'est fait.
