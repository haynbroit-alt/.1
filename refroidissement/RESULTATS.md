# Étapes 1 et 2 : le modèle physique et le levier qui domine (25/11/2026)

**Statut : DÉMONTRÉ dans le modèle (calcul vérifié par 11 tests), NON VÉRIFIÉ dans le monde réel.**
Aucune découverte à ce stade. Ce travail donne une base chiffrée et désigne l'endroit exact où une invention aurait
de l'effet.

## Le résultat en trois phrases
1. **En climat tropical humide, le ciel clair n'offre qu'environ 53 W/m² de « froid » rayonné**, contre 140 au désert.
   L'humidité ferme à moitié la fenêtre par laquelle la chaleur s'échappe vers l'espace (transmittance au zénith
   de 0,51 contre 0,91).
2. **Ce budget équivaut à environ 6 % du soleil de midi.** Une surface qui absorbe plus de 5,8 % du soleil ne peut donc
   pas rester plus fraîche que l'air à midi, quelles que soient ses propriétés infrarouges. Une bonne peinture
   blanche, qui absorbe environ 5 % du soleil, finit à −0,5 °C : presque rien.
3. **Le levier dominant est la réflexion du soleil, de très loin.** Passer de 5 % à 1 % d'absorption fait gagner
   2,6 °C. Les leviers « savants » apportent peu tant que le soleil n'est pas maîtrisé : la sélectivité spectrale
   donne −0,2 °C, l'isolation −0,6 °C, et un écran angulaire nuit même (+1,6 °C). Une fois la réflexion maîtrisée,
   en revanche, l'isolation et la sélectivité multiplient l'effet : tous les leviers réunis donnent −15 °C (idéal,
   ciel clair, sans charge à refroidir).

**Critère d'arrêt de l'étape 0 : franchi.** On visait au moins 2 °C sous l'air à midi en climat tropical humide avec
un levier réaliste. Le modèle donne −3,1 °C avec 1 % d'absorption solaire, ce qui est le niveau des meilleurs
matériaux de laboratoire selon la littérature (à vérifier à l'étape 3). **On continue.**

## Les tableaux
Ils sont générés par `python3 experience.py`. La sortie complète est dans `sortie_experience.md`.

**Tableau 1.** Peinture blanche « fraîche » (ε = 0,95, 5 % du soleil absorbé, convection h = 8 W/m²/K), soleil de
900 W/m² à midi.

| Climat | Air (°C) | Rosée (°C) | Émissivité du ciel | Transmittance zénithale 8–13 µm | Puissance de nuit à l'ambiante (W/m²) | Écart de nuit (°C) | Écart à midi (°C) |
|---|---|---|---|---|---|---|---|
| Désert sec | 38 | 2 | 0,722 | 0,91 | 140 | −9,9 | −6,7 |
| Tempéré, été | 26 | 12 | 0,789 | 0,78 | 91 | −6,7 | −3,4 |
| Méditerranéen, été | 32 | 16 | 0,819 | 0,70 | 84 | −6,1 | −2,8 |
| Tropical humide | 32 | 24 | 0,887 | 0,51 | 53 | −3,8 | −0,5 |
| Équatorial très humide (**hors domaine**, extrapolé) | 31 | 26 | 0,906 | 0,45 | 43 | −3,1 | +0,1 |

**Tableau 2.** Tropical humide (air 32 °C, rosée 24 °C), midi. Chaque levier est changé seul par rapport à la base.

| Levier | Puissance nette à l'ambiante (W/m²) | Écart à l'air (°C) | Gain sur la base (°C) |
|---|---|---|---|
| Base : peinture blanche (5 % absorbé, h = 8) | 8 | −0,5 | 0 |
| Soleil absorbé : 5 % → 1 % | 44 | −3,1 | **−2,6** |
| Émission limitée à la fenêtre 8–13 µm | 8 | −0,7 | −0,2 |
| Écran angulaire à 45° (avec sélectivité) | −10 | +1,1 | +1,6 (pénalise) |
| Écran contre l'air : h = 8 → 2 | 8 | −0,9 | −0,4 |
| Isolation très forte : h = 8 → 0,5 | 8 | −1,1 | −0,6 |
| Tout combiné : 1 %, sélectif, h = 0,5 | 44 | **−15,3** | −14,8 |
| Tout combiné, avec écran angulaire à 45° | 26 | −15,4 | −14,8 |

**Tableau 3.** Le seuil solaire : la part du soleil absorbé (900 W/m²) au-delà de laquelle aucune surface ne reste
sous l'air à midi.

| Climat | Absorption maximale | Réflexion minimale |
|---|---|---|
| Désert sec | 15,6 % | 84,4 % |
| Tempéré, été | 10,1 % | 89,9 % |
| Méditerranéen, été | 9,4 % | 90,6 % |
| **Tropical humide** | **5,8 %** | **94,2 %** |
| Équatorial très humide (extrapolé) | 4,8 % | 95,2 % |

**Tableau 4.** L'écran angulaire ne sert qu'une fois la surface très sous l'air (tropical humide, sélectif, 1 %
absorbé, h = 0,5). L'optimum se situe vers 60°, et il n'apporte alors que 1,7 °C.

| Demi-angle du cône | 90° | 75° | 60° | 45° | 30° |
|---|---|---|---|---|---|
| Écart à l'air à midi (°C) | −15,3 | −16,1 | −17,0 | −15,4 | −8,6 |

## Contrôles effectués
- **11 tests** (`python3 -m unittest test_modele`) vérifient trois familles de propriétés :
  - les lois physiques : Planck redonne Stefan-Boltzmann à 0,5 % près, et la loi de Wien est respectée ;
  - le calage exact du ciel sur Berdahl et Martin ;
  - les cas limites et le sens des variations.
- **Un défaut de domaine trouvé par les tests** : par ciel très sec (rosée −10 °C), le modèle à deux bandes ne peut
  pas reproduire l'émissivité mesurée. Il le signale désormais (`calage_exact = False`) au lieu de produire un faux
  calage.
- **Un défaut de mon script trouvé à la relecture** : le tableau 4 calculait le mauvais climat. Corrigé, et
  recoupé avec le tableau 2 (−15,3 °C à 90° dans les deux).
- **Ordre de grandeur face à la littérature** : à Singapour, avec une forte isolation, on mesure jusqu'à 8 °C sous
  l'air ([2024](https://doaj.org/article/a5096ee788d545d79675ad38f7cb800d)). Avec une isolation forte et 2 à 3 %
  d'absorption, le modèle donne −4 à −5 °C. Même ordre de grandeur, mais ce n'est pas une validation : les
  dispositifs et les conditions diffèrent.

## Les limites, à lire avant d'utiliser un chiffre
1. **Ciel clair seulement.** Sous les nuages, fréquents sous les tropiques, le refroidissement radiatif s'effondre.
   Le gain annuel réel sera nettement plus faible que ces chiffres de midi par ciel clair.
2. **La corrélation du ciel** ([Berdahl et Martin, 1984](https://escholarship.org/content/qt3d17x714/qt3d17x714.pdf?t=p0fuh4))
   est une moyenne sur 24 h, calée sur des points de rosée de −13 à 24 °C. Le climat tropical humide étudié est à la
   limite de ce domaine, et le climat équatorial le dépasse.
3. **Un ciel simplifié** : la fenêtre 8–13 µm est supposée grise, la bande 16–25 µm est ignorée (ce qui sous-estime
   les performances par temps sec), et il n'y a ni aérosols ni pollution.
4. **Des surfaces idéalisées** : l'écran angulaire est un miroir parfait, l'écran contre l'air est parfaitement
   transparent à l'infrarouge, et les propriétés ne vieillissent pas.
5. **Pas de charge** : la surface ne refroidit rien. Sur un vrai toit, une partie de la puissance sert à absorber la
   chaleur du bâtiment, ce qui réduit l'écart de température.

## Ce que cela désigne comme invention à chercher (étape 3)
**Statut : IMAGINÉ, à vérifier.** La cible n'est pas un principe physique nouveau. C'est une surface qui garde au
moins 99 % de réflexion solaire pendant des années, en climat chaud, humide, pollué et très ensoleillé, pour un coût
de peinture. Elle serait couplée à un écran contre l'air transparent à l'infrarouge.

Les questions de l'étape 3, dans l'ordre :
1. Quels matériaux atteignent 99 % aujourd'hui, à quel coût, et combien de temps tiennent-ils dehors sous les
   tropiques (salissures, micro-organismes, UV, humidité) ? C'est une recherche documentaire sourcée.
2. Combien de froid utile par an, avec les vraies données horaires d'une ville tropicale (nuages compris) ? Des
   données météo publiques et gratuites existent ; il faudra un modèle de ciel nuageux.
3. Existe-t-il un concept qui garde sa blancheur dans ces conditions, et qui ne figure pas déjà dans les brevets ?
4. Une expérience à bas coût sur un toit : deux échantillons, deux thermomètres, quelques dizaines d'euros, avec
   l'accord du propriétaire.
