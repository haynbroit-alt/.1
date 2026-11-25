# Étape 0 : le choix du problème (25/11/2026)

## Les candidats
Les notes vont de 1 à 5. Ce sont des **jugements argumentés, pas des mesures** : la colonne « pourquoi » dit sur quoi
chacun repose.

| Problème | Importance | Angle d'attaque avec nos moyens | Vérifiable vite | Ouverture pour un nouvel entrant | Pourquoi |
|---|---|---|---|---|---|
| **Se rafraîchir sans électricité dans les pays chauds et humides** | 5 | 5 | 5 | 4 | Besoin énorme et croissant (ci-dessous). La physique est connue, rien de nouveau à inventer en physique. Un calcul se fait sur ordinateur, et une expérience coûte quelques dizaines d'euros. Le verrou (l'humidité) est documenté et non résolu |
| Eau potable tirée de l'air ou dessalement à bas coût | 5 | 3 | 3 | 3 | Le bilan énergétique de l'eau limite fortement les rendements. Les expériences sont plus lentes et plus chères |
| Diagnostic médical à très bas coût | 5 | 2 | 2 | 3 | Il faut des laboratoires, des échantillons et des autorisations sanitaires |
| Stockage d'énergie de longue durée, bon marché | 5 | 2 | 2 | 2 | Des industriels puissants s'y consacrent déjà. Les essais sont lents et coûteux |
| Découverte de matériaux par l'IA | 4 | 3 | 2 | 1 | De très grands laboratoires y travaillent, et une découverte doit ensuite être fabriquée et mesurée |
| Vérification automatique des affirmations (fiabilité de l'information) | 4 | 4 | 4 | 2 | Très utile, mais il s'agit surtout de logiciel et d'usage, où l'apport d'une découverte est difficile à prouver |

**Choix : le refroidissement passif en climat chaud et humide.**

## Pourquoi ce problème mérite qu'on s'y consacre
Ce sont des faits sourcés, pas des estimations à nous.
- **L'énergie de la climatisation.** Sans politique d'efficacité, la demande d'énergie pour rafraîchir les bâtiments
  ferait plus que tripler d'ici 2050, autant que toute l'électricité de la Chine et de l'Inde aujourd'hui (AIE,
  [The Future of Cooling](https://www.iea.org/reports/the-future-of-cooling), 2018).
- **Où se trouve la demande.** Plus de 80 % de la demande d'électricité pour le froid projetée en 2050 viendrait des
  pays émergents et en développement. En Indonésie, la part de la population équipée d'un climatiseur passerait de
  14 % en 2023 à 85 % en 2050 (AIE,
  [commentaire de 2025](https://www.iea.org/commentaries/staying-cool-without-overheating-the-energy-system)).
- **Le verrou.** Le refroidissement radiatif, c'est-à-dire une surface qui se refroidit seule en rayonnant sa chaleur
  vers le ciel, fonctionne bien en climat sec. Il est documenté comme décevant en climat chaud et humide, car la
  vapeur d'eau rend le ciel moins transparent à ce rayonnement :
  - [Okayama, 2018](https://doaj.org/article/395e3bd27e534211baf5727998c8db9c) : un dispositif restait 2,8 °C au-dessus
    de l'air, à 35 °C ;
  - [Hong Kong](https://scholars.cityu.edu.hk/en/publications/passive-radiative-cooling-under-a-humid-subtropical-climate-devel/) :
    le refroidissement de jour reste à améliorer ;
  - [Singapour, 2024](https://doaj.org/article/a5096ee788d545d79675ad38f7cb800d) : jusqu'à 8 °C sous l'air, mais avec
    une forte isolation.

Ce sont précisément les régions où la demande explose qui en profitent le moins. Résoudre ce verrou à un coût de
peinture aurait un marché mondial naturel : toitures, peintures, revêtements.

## Critère d'arrêt de ce choix
Si l'étape 2 montre qu'aucun levier réaliste ne peut donner au moins 2 °C sous l'air à midi en climat tropical humide,
on abandonne ce problème et l'on passe au candidat suivant.
