# Étape 3 : une année réelle, nuages compris, et l'état des matériaux (25/11/2026)

**Statut :**
- **DÉMONTRÉ dans les données**, pour le calcul : 21 tests, et les sorties sont reproductibles.
- **INCONNU dans le monde réel** pour les valeurs absolues : la sensibilité est forte, voir le tableau 8.

## Ce qu'on a fait
Pour 8 villes, chaque heure de 2024 a été prise dans les données de la NASA (POWER) : température, point de rosée,
soleil, et rayonnement infrarouge du ciel, avec les nuages réels ou sans nuages. Les villes sont :
- **cinq humides** : Singapour, Jakarta, Lagos, Bangkok, Bombay ;
- **trois de référence** : Séville, Riyad, Phoenix.

Pour une surface blanche ordinaire (émissivité 0,95), le bilan se calcule directement à partir de ces données, sans
modèle de ciel. Les données sont dans `donnees/nasa_power_2024.csv.gz` ; le programme est `annuel.py`, ses tests
sont dans `test_annuel.py`, et les tableaux complets dans `sortie_annuel.md`.

## Les résultats

**1. Le modèle des étapes 1 et 2 tient** (tableau 5). Son ciel clair s'écarte de celui de la NASA de −3,4 % à
+2,1 % en moyenne selon la ville, y compris à Singapour (−0,1 %), alors que 94 % des heures y sont hors du domaine de
calage de la formule. Ce contrôle oppose deux modèles, pas un modèle et une mesure, mais ils sont indépendants et ils
concordent.

**2. Les villes humides disposent d'environ un tiers du froid des déserts** (tableau 6, nuages compris, 3 % du soleil
absorbé) :

| Kilowattheures par mètre carré et par an | Valeur |
|---|---|
| Singapour | 246 |
| Jakarta | 323 |
| Riyad | 786 |
| Phoenix | 794 |

Les nuages retirent environ 28 % du froid à Singapour : 340 sans nuages, 246 avec.

**3. La blancheur décide de tout pendant les heures de soleil** (tableau 7). C'est le résultat central. Voici la part
des heures ensoleillées où une surface peut rester sous la température de l'air, selon la part du soleil qu'elle
absorbe :

| Ville | 10 % absorbé (peinture blanche ordinaire) | 5 % | 3 % (97 % de réflexion) |
|---|---|---|---|
| Singapour | 8 % | 71 % | 100 % |
| Lagos | 14 % | 69 % | 99 % |
| Jakarta | 20 % | 97 % | 100 % |
| Bangkok | 35 % | 93 % | 100 % |

Passer de 90 % à 97 % de réflexion solaire, c'est passer de « presque jamais » à « toujours ».

**4. La nuit offre un froid indépendant de la blancheur** : 150 à 185 kWh/m²/an dans les villes humides, quelle que
soit la surface. C'est une voie de repli robuste : récolter le froid la nuit et le stocker pour la journée.

**5. Les valeurs absolues sont fragiles** (tableau 8). Si le rayonnement du ciel estimé par la NASA est faux de
±10 W/m², soit environ ±2 %, le froid annuel varie de ±21 à ±34 % dans les villes humides, contre ±11 à ±14 % ailleurs.
Le froid disponible est en effet une petite différence entre deux grands flux. Les comparaisons tiennent, mais les
kilowattheures absolus restent INCONNUS à ±30 % près tant qu'on n'a pas mesuré.

## Ce que dit la littérature sur les matériaux
- **Le meilleur blanc de laboratoire** : 98,1 % de réflexion solaire, avec une peinture au sulfate de baryum (Purdue,
  2021 : [communiqué](https://www.purdue.edu/newsroom/releases/2021/Q2/the-whitest-paint-is-here-and-its-the-coolest.-literally..HTML),
  [article](https://arxiv.org/pdf/2011.01161.pdf)). Les auteurs eux-mêmes disaient que la durabilité à long terme
  restait à établir. Une version à l'eau de 2025 annonce 95,4 %
  ([Purdue, 2025](https://engineering.purdue.edu/NANOENERGY/publications/Aljwirah_ACS%20AMI_2025.pdf)).
- **Le vieillissement** : une peinture blanche classique au dioxyde de titane perd environ 9 points de réflexion après
  l'équivalent de 3 ans de salissures, et 5,4 points après l'équivalent d'un an de soleil de Floride
  ([Purdue, 2025](https://engineering.purdue.edu/NANOENERGY/publications/Barber_ACS%20Appl%20Opt%20Mater_2025.pdf)).
- **Une piste contre le vieillissement** : un revêtement sans liant, conçu pour résister à la saleté et aux UV, a tenu
  plus de 6 mois dehors ([Nature Communications, 2022](https://www.nature.com/articles/s41467-022-32409-7)).
- **Ce qui manque** : je n'ai trouvé aucune étude pluriannuelle en climat tropical réel qui mesure ensemble la saleté,
  les micro-organismes et les UV. C'est INCONNU, et l'absence dans ma recherche ne prouve pas l'absence dans la
  littérature.

## La conclusion de l'étape 3
**Le verrou est précis et chiffré** (statut : PLAUSIBLE, appuyé sur les données). Pour refroidir de jour sous les
tropiques humides, une surface doit **garder au moins 97 % de réflexion solaire pendant des années** sous la chaleur,
l'humidité, la saleté, les micro-organismes et les UV. Or :
- le meilleur blanc de laboratoire est à 98 % lorsqu'il est neuf ;
- les peintures courantes perdent 5 à 9 points en un à trois ans.

**Aucun matériau connu de nous ne tient ce cahier des charges dans la durée sous les tropiques.**

**Décision (règle 7 : un seul front)** : la voie A, une **blancheur durable d'au moins 97 % sous les tropiques**.
C'est elle qui transforme « presque jamais » en « toujours ». La voie B, la récolte nocturne avec stockage, reste en
réserve : robuste, mais c'est de l'ingénierie déjà explorée, avec un gain plus modeste.

## L'étape suivante
1. **Antériorité.** Chercher les brevets et les produits de revêtements ultra-blancs autonettoyants ou anti-salissures
   pour les tropiques : ce qui existe, ce qui a échoué, et pourquoi.
2. **Concepts.** Proposer au plus trois concepts, chacun avec son bilan : réflexion, coût et mécanisme de durabilité.
3. **Expérience à bas coût.** Exposer dehors pendant plusieurs semaines quelques échantillons blancs et mesurer leur
   température face à l'air. Une dépense de quelques dizaines d'euros (thermomètres, peintures) sera proposée, et
   **soumise à l'accord du propriétaire**.

**Limites propres à cette étape.**
- Les données NASA sont des estimations, pas des mesures de station.
- Une seule année (2024) a été étudiée.
- Le froid est calculé à la température de l'air, pour une surface sans charge. Le service rendu à un bâtiment réel
  sera plus faible.

*Données : NASA Langley Research Center (LaRC) POWER Project, financé par le programme NASA Earth Science/Applied
Science.*
