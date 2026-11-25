# Programme de découverte

Un seul front à la fois. Chaque affirmation porte son statut : **imaginé**, **plausible**, **démontré** ou **réalisé**.

| Document | Contenu |
|---|---|
| [CHARTE.md](CHARTE.md) | Les règles du programme |
| [01_CHOIX_DU_PROBLEME.md](01_CHOIX_DU_PROBLEME.md) | Étape 0 : pourquoi le refroidissement passif en climat chaud et humide |
| [refroidissement/RESULTATS.md](refroidissement/RESULTATS.md) | Étapes 1 et 2 : le modèle physique, le levier qui domine, les limites |
| [refroidissement/ETAPE3.md](refroidissement/ETAPE3.md) | Étape 3 : une année réelle (NASA, 8 villes, nuages compris) et l'état des matériaux |

## Reproduire les résultats
Python 3.11 ou plus récent, bibliothèque standard seule :

```bash
cd refroidissement
python3 -m unittest test_modele test_annuel   # 21 tests
python3 experience.py                         # les tableaux de RESULTATS.md
python3 annuel.py                             # les tableaux de ETAPE3.md (--telecharger pour reprendre les données)
```

**Front actuel** : voie A, une blancheur d'au moins 97 % qui dure sous les tropiques. Prochaines tâches : recherche d'antériorité, au plus trois concepts, une expérience à bas coût (soumise à l'accord du propriétaire).
