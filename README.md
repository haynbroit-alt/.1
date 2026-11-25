# Programme de découverte

Un seul front à la fois. Chaque affirmation porte son statut : **imaginé**, **plausible**, **démontré** ou **réalisé**.

| Document | Contenu |
|---|---|
| [CHARTE.md](CHARTE.md) | Les règles du programme |
| [01_CHOIX_DU_PROBLEME.md](01_CHOIX_DU_PROBLEME.md) | Étape 0 : pourquoi le refroidissement passif en climat chaud et humide |
| [refroidissement/RESULTATS.md](refroidissement/RESULTATS.md) | Étapes 1 et 2 : le modèle physique, le levier qui domine, les limites |

## Reproduire les résultats
Python 3.11 ou plus récent, bibliothèque standard seule :

```bash
cd refroidissement
python3 -m unittest test_modele   # 11 tests
python3 experience.py             # les tableaux de RESULTATS.md
```

**Front actuel** : étape 3. Matériaux à au moins 99 % de réflexion solaire, durables sous les tropiques ; froid annuel
réel avec les nuages ; recherche d'antériorité.
