# Étape 4 : antériorité, concepts et protocole d'expérience (25/11/2026)

**Rappel du verrou** (étape 3) : sous les tropiques humides, une surface doit **garder au moins 97 % de réflexion
solaire pendant des années**. Les meilleurs blancs neufs y arrivent, mais rien ne prouve qu'ils y restent.

## 1. Ce qui existe déjà (antériorité)

| Piste | Ce qu'on trouve | Ce qui manque | Source |
|---|---|---|---|
| Blancs à pigment très diffusant | Le carbonate de calcium atteint 95,5 %, le sulfate de baryum 98,1 % et le nitrure de bore 97,9 % (peintures acryliques de laboratoire). Une peinture à l'eau au phosphate de calcium atteint 98 %. Les peintures du commerce sont à 80–90 % | La durabilité dehors sur plusieurs années | [Purdue 2025](https://engineering.purdue.edu/NANOENERGY/publications/Aljwirah_ACS%20AMI_2025.pdf), [arXiv 2011.01161](https://arxiv.org/pdf/2011.01161.pdf) |
| Surfaces autonettoyantes et superhydrophobes (l'eau perle et emporte la saleté) | Un **brevet** de 2019, d'origine chinoise, sur un film refroidissant superhydrophobe et autonettoyant. Des articles de 2022 à 2025 ; un film de 2025 atteint 94,2 % de réflexion | Des données de longue durée en extérieur. La plupart des essais sont courts ou faits en laboratoire | [brevet (USPTO)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10927244), [J. Mater. Chem. A 2025](https://pubs.rsc.org/en/content/articlehtml/2025/ta/d5ta01065a), [PubMed 36320188](https://www.pubmed.gov/36320188/) |
| Peintures hydrophobes contre la saleté | Une peinture à liant silicone, conçue pour mieux résister à la salissure qu'une peinture au dioxyde de titane | Des données tropicales | [Purdue 2025](https://engineering.purdue.edu/NANOENERGY/publications/Barber_ACS%20Appl%20Opt%20Mater_2025.pdf) |
| Revêtement sans liant résistant à la saleté et aux UV | Bon refroidissement après vieillissement accéléré et 6 mois dehors | Plusieurs années, sous les tropiques | [Nature Communications 2022](https://www.nature.com/articles/s41467-022-32409-7) |
| Badigeon de chaux (pratique traditionnelle) | Un toit blanchi à la chaux rafraîchit depuis longtemps. Un pilote à Ahmedabad (Inde) en 2017 a blanchi plus de 3 000 toits, selon une source informelle | Le badigeon n'est pas optimisé pour les meilleures réflexions. Je n'ai trouvé aucune mesure fiable de sa réflexion ni de son effet contre les micro-organismes (INCONNU) | [Wikipedia](https://en.wikipedia.org/wiki/Limewash), [source informelle](https://denutrients.substack.com/p/white-roofs-traditionally-cooling) |
| Films avec couche d'argent | Ils existent dans le commerce, y compris à Singapour | Ils sont chers, et leur aspect est peu accepté | [IPI Singapore](https://www.ipi-singapore.org/tech-offer/download-pdf/175501), [revue PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11656601) |

**Ce que j'en conclus.** Chaque piste « matériau qui ne se salit pas » est déjà explorée, et souvent brevetée. Une
invention de matériau de plus dans cette course serait faible face aux laboratoires. En revanche, une question reste
ouverte, et elle est peu chère à attaquer : **plutôt que d'empêcher le blanc de vieillir, peut-on le renouveler pour
presque rien ?**

## 2. Les concepts (au plus trois)

| Concept | Idée | Mécanisme de durabilité | Bilan attendu | Statut | Antériorité |
|---|---|---|---|---|---|
| **C1. Blanc renouvelable à la chaux** (retenu) | Un badigeon de chaux (hydroxyde de calcium) chargé d'un pigment très diffusant (sulfate de baryum ou carbonate de calcium fin), passé au rouleau, puis **renouvelé chaque année** | On accepte la salissure, et on rend la remise à neuf presque gratuite. La chaux durcit en calcaire au contact de l'air. Son alcalinité pourrait gêner les moisissures (hypothèse non vérifiée) | Réflexion visée : au moins 97 % (INCONNU, à mesurer). Coût visé : quelques centimes à quelques dizaines de centimes par m² et par an (hypothèse, prix non relevés). Matériaux locaux, applicables par n'importe qui | **IMAGINÉ** | Le badigeon de chaux est ancien. La nouveauté serait seulement une formule optimisée pour au moins 97 %, prouvée par la mesure. C'est peu brevetable, mais très diffusable : un impact fort, une protection faible |
| C2. Sous-couche ultra-blanche et couche autonettoyante | Une base au sulfate de baryum, recouverte d'une fine couche superhydrophobe que la pluie lave | L'eau emporte la saleté | Plus de 94 % mesuré en laboratoire par d'autres | PLAUSIBLE | **Déjà brevetée et publiée.** Notre seul apport serait de la tester sous les tropiques, pas de l'inventer |
| *(écarté)* Films avec argent ou polymères poreux | — | — | Chers ou difficiles à produire | — | Déjà industrialisés ou publiés |

**Choix : C1.** C'est le seul concept qui peut se tester pour quelques dizaines d'euros, qui ne dépend d'aucune
usine, et qui transforme le problème de durabilité, que personne n'a résolu, en un geste d'entretien annuel que des
millions de gens font déjà avec la chaux. Le risque est clair : un badigeon n'atteindra peut-être pas 97 %. C'est
justement la première chose à mesurer.

## 3. Le protocole d'expérience (rien n'est acheté)

**Objectif.** Mesurer trois choses :
- si un blanc à la chaux chargé reste plus froid qu'une peinture blanche ordinaire au soleil ;
- s'il descend sous la température de l'air ;
- comment il vieillit, semaine après semaine.

**Montage.**
- **Trois échantillons** de 10 × 10 cm, sur des plaques (chutes d'aluminium ou de contreplaqué) :
  - (1) une peinture blanche ordinaire, comme témoin ;
  - (2) un badigeon de chaux seul ;
  - (3) un badigeon de chaux chargé (concept C1).
- **L'installation.** Chaque plaque est posée sur une boîte en polystyrène de récupération, qui l'isole par dessous,
  et recouverte d'un film alimentaire tendu. Le polyéthylène est transparent à l'infrarouge et coupe le vent.
- **La mesure.** Une sonde de température est collée sous chaque plaque. Une quatrième sonde, à l'ombre sous un
  gobelet blanc retourné et ventilé, mesure l'air.
- **L'emplacement.** Le tout est posé sur un toit ou un balcon dégagé, face au ciel, loin des murs.

**Mesures.**
- La température de chaque sonde toutes les 5 à 10 minutes, pendant 4 à 8 semaines.
- Une photo par semaine, toujours au même endroit, pour suivre la salissure.
- Les données sont récupérées par l'application du téléphone ; l'analyse est faite par l'agent.

**Prédiction enregistrée avant l'expérience** (`prediction_experience.py`). Les conditions supposées sont un midi
d'hiver ensoleillé dans le sud de la France : air 12 °C, rosée 4 °C, soleil 500 W/m², avec le film.

| Échantillon | Écart à l'air à midi | Écart la nuit |
|---|---|---|
| Peinture blanche ordinaire (environ 10 % du soleil absorbé) | −5,0 °C | −10,8 °C |
| Blanc à 97 % (3 % absorbé) | −9,1 °C | −10,8 °C |

Ce qui compte, ce sont les **écarts entre échantillons**, pas les valeurs absolues :
- **à midi**, le plus blanc doit être 3 à 4 °C plus froid que le témoin ; sans film, l'écart attendu est d'environ
  2,7 °C ;
- **la nuit**, tous les échantillons doivent être à la même température, à ±0,5 °C près. La blancheur ne joue plus,
  donc ce point sert de contrôle des capteurs.

Deux réserves. La nuit, la rosée réchauffera les plaques vers le point de rosée, donc les −10,8 °C sont surestimés.
Et le vent réel est inconnu.

**Critères, fixés d'avance.**
- **Concept C1 confirmé** si le badigeon chargé est au moins 2 °C plus froid que le témoin à midi ensoleillé (moyenne
  sur 5 jours clairs ou plus) et s'il reste sous l'air à midi.
- **Concept C1 réfuté** s'il n'est pas plus froid que le témoin. On passe alors à C2, ou à la voie B (récolte
  nocturne).
- **Expérience invalide** si les échantillons diffèrent de plus de 1 °C la nuit. Il faut alors recaler les sondes.

**Ce que cet essai ne prouvera pas.** La durabilité sous les tropiques : il aura lieu en France, en hiver. Il prouve la
méthode, le classement des blancs et un premier vieillissement. L'essai tropical viendra ensuite, avec un partenaire
sur place.

**Sécurité.** La chaux est caustique : gants, lunettes, et ni contact avec la peau ni inhalation de la poudre.

## 4. Le matériel à faire approuver (estimation, rien n'est commandé)

| Article | Quantité | Prix relevé | Statut du prix |
|---|---|---|---|
| Enregistreur de température Bluetooth avec sonde externe (exemple : [Pearl FWS-350.bt, reconditionné](https://www.pearl.fr/article/NX5826R/enregistreur-de-donnees-thermometrique-hygrometrique-connecte-fws-350-bt-1)) | 4 | 22,46 € pièce, soit environ 90 € | Vu le 25/11 dans un résultat de recherche ; disponibilité non vérifiée |
| Sulfate de baryum en poudre, plus petit conditionnement ([Fisher, qualité laboratoire](https://fishersci.fr/shop/products/barium-sulfate-97-thermo-scientific/p-3256913)) | 1 | à partir de 34,57 € | Fourchette vue dans un résultat de recherche. Un pigment « blanc fixe » de peintre est probablement moins cher (non vérifié) |
| Chaux aérienne en poudre | 1 petit sac | **non relevé** | À chiffrer avant l'achat |
| Peinture blanche ordinaire (témoin) | un fond de pot | **non relevé** | Un reste de peinture suffit |
| Boîtes en polystyrène, plaques, film alimentaire, gobelet, colle | — | 0 € (récupération) | — |

**Les deux options.**
- **Option complète**, avec 4 sondes et le sulfate de baryum : environ 125 € pour les articles chiffrés, plus la
  chaux.
- **Option minimale**, avec 3 sondes et un badigeon de chaux seul face au témoin : environ 67 €, plus la chaux. Elle
  teste moins (pas de pigment ajouté).

**Aucun achat n'est fait. La décision et la dépense appartiennent au propriétaire.**
