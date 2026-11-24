"""Outils communs aux tests : un faux prestataire de paiement qui enregistre chaque requête."""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.parse
from typing import Any

from mere.stripe import ClientLecture


class Reponse(io.BytesIO):
    def __enter__(self) -> Reponse:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class FauxStripe:
    """Sert des listes paginées par chemin ; `refus` : chemins qui répondent HTTP 403."""

    def __init__(self, donnees: dict[str, list[dict[str, Any]]], refus: set[str] | None = None, page: int = 100):
        self.donnees, self.refus, self.page = donnees, refus or set(), page
        self.requetes: list[tuple[str, str]] = []

    def __call__(self, requete: Any) -> Reponse:
        self.requetes.append((requete.get_method(), requete.full_url))
        url = urllib.parse.urlparse(requete.full_url)
        chemin = url.path.removeprefix("/v1/")
        if chemin in self.refus:
            raise urllib.error.HTTPError(requete.full_url, 403, "refus", {}, None)  # type: ignore[arg-type]
        params = dict(urllib.parse.parse_qsl(url.query))
        elements = self.donnees.get(chemin, [])
        debut = 0
        if "starting_after" in params:
            debut = next(i for i, e in enumerate(elements) if e["id"] == params["starting_after"]) + 1
        tranche = elements[debut:debut + self.page]
        corps = {"object": "list", "data": tranche, "has_more": debut + self.page < len(elements)}
        return Reponse(json.dumps(corps).encode())

    def client(self) -> ClientLecture:
        return ClientLecture(ouvrir=self, cle="rk_test_factice")


def paiement(id_: str, montant: int, *, statut: str = "succeeded", reel: bool = True, rembourse: int = 0,
             devise: str = "eur", cree: int = 1_790_000_000, **extra: Any) -> dict[str, Any]:
    return {"id": id_, "amount": montant, "amount_refunded": rembourse, "currency": devise, "status": statut,
            "paid": statut == "succeeded", "livemode": reel, "created": cree, **extra}
