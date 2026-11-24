"""Les quatre statuts de l'entreprise mère et la règle qui les combine.

PROUVÉ   : valeur lue dans la source qui fait foi, avec une référence vérifiable.
INCONNU  : rien de lisible, une déclaration non vérifiable, ou une hypothèse.
CONFLIT  : deux sources disent des choses incompatibles sur le même point.
ÉCHEC    : mesuré, et en dessous du critère d'arrêt à sa date ; ou l'événement a échoué.

Règle de combinaison : un CONFLIT l'emporte sur tout (on ne sait pas ce qui est vrai), puis un ÉCHEC,
puis l'INCONNU ; PROUVÉ exige que tout soit PROUVÉ. Une absence de preuve ne vaut jamais PROUVÉ.
"""

from __future__ import annotations

from collections.abc import Iterable

PROUVE = "PROUVÉ"
INCONNU = "INCONNU"
CONFLIT = "CONFLIT"
ECHEC = "ÉCHEC"
STATUTS = (PROUVE, INCONNU, CONFLIT, ECHEC)


def combiner(statuts: Iterable[str]) -> str:
    """Statut d'un ensemble : CONFLIT > ÉCHEC > INCONNU > PROUVÉ ; un ensemble vide est INCONNU."""
    vus = set(statuts)
    inconnus = vus - set(STATUTS)
    if inconnus:
        raise ValueError(f"statut inconnu : {sorted(inconnus)}")
    if not vus:
        return INCONNU
    if CONFLIT in vus:
        return CONFLIT
    if ECHEC in vus:
        return ECHEC
    if vus == {PROUVE}:
        return PROUVE
    return INCONNU
