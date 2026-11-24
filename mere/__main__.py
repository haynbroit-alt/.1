"""Ligne de commande de l'entreprise mère.

  python3 -m mere tableau [--stripe] [--rejouer] [--jour AAAA-MM-JJ]
      Lit toutes les sources, écrit TABLEAU.md (public, vérifié par la garde), prive/TABLEAU_PRIVE.md,
      prive/faits.jsonl (tous les faits) et etat/faits_publics.jsonl (le contrat partagé).
      --stripe  : relève le prestataire de paiement en lecture seule (sinon : dernier relevé privé daté).
      --rejouer : rejoue deux fois les suites des modules dans un clone propre (sinon : dernier état).
      --controler : relance les contrôles réseau (citations, prospects) ; sinon, derniers résultats datés.
  python3 -m mere verifier
      Portefeuille et configuration valides, sorties publiques sans fuite. Code 1 sinon. Utilisé par la CI.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .garde import fuites
from .portefeuille import charger
from .tableau import construire, faits_publics, rendre

RACINE = Path(__file__).resolve().parent.parent
PUBLICS = ("TABLEAU.md", "etat/faits_publics.jsonl", "etat/rejeux.json", "etat/controles.json")


def _montants_publics() -> set[str]:
    _, reglages, _ = charger(RACINE / "donnees/portefeuille.toml")
    return {str(m) for m in reglages.get("montants_publics", [])}


def tableau(args: argparse.Namespace) -> int:
    jour = date.fromisoformat(args.jour) if args.jour else date.today()
    r = construire(RACINE, jour, lire_stripe=args.stripe, rejouer=args.rejouer, controler=args.controler)
    public, prive = rendre(r, prive=False), rendre(r, prive=True)
    lignes_publiques = "".join(json.dumps(f, ensure_ascii=False) + "\n" for f in faits_publics(r))
    rejeux = (json.dumps(r.rejeux_a_ecrire, ensure_ascii=False, indent=1) + "\n") if r.rejeux_a_ecrire is not None \
        else None
    ctrl = (json.dumps([c.to_dict() for c in r.controles_a_ecrire], ensure_ascii=False, indent=1) + "\n") \
        if r.controles_a_ecrire is not None else None
    # La garde passe sur TOUT ce qui sera public, avant toute écriture publique.
    trouvees = [t for texte in (public, lignes_publiques, rejeux or "", ctrl or "")
                for t in fuites(texte, r.montants_publics)]
    (RACINE / "prive").mkdir(exist_ok=True)
    (RACINE / "prive/TABLEAU_PRIVE.md").write_text(prive, encoding="utf-8")
    (RACINE / "prive/faits.jsonl").write_text(
        "".join(json.dumps(f.to_dict(), ensure_ascii=False) + "\n" for f in r.faits), encoding="utf-8")
    if trouvees:
        print("REFUS : la sortie publique contient des données à ne pas publier ; rien de public n'est écrit.")
        print("\n".join(f"  - {t}" for t in trouvees[:20]))
        return 1
    (RACINE / "TABLEAU.md").write_text(public, encoding="utf-8")
    (RACINE / "etat").mkdir(exist_ok=True)
    (RACINE / "etat/faits_publics.jsonl").write_text(lignes_publiques, encoding="utf-8")
    if rejeux is not None:
        (RACINE / "etat/rejeux.json").write_text(rejeux, encoding="utf-8")
    if ctrl is not None:
        (RACINE / "etat/controles.json").write_text(ctrl, encoding="utf-8")
    print(public.split("\n## Indicateurs")[0].strip())
    print(f"\n{len(r.faits)} faits · {len(r.conflits)} conflit(s) · {len(r.alertes)} alerte(s) · "
          f"{len(r.erreurs)} erreur(s) de lecture. Tableaux : TABLEAU.md, prive/TABLEAU_PRIVE.md")
    return 0


def verifier(_: argparse.Namespace) -> int:
    problemes: list[str] = []
    opportunites, _, erreurs = charger(RACINE / "donnees/portefeuille.toml")
    problemes += [f"portefeuille : {e}" for e in erreurs]
    if not opportunites:
        problemes.append("portefeuille vide")
    publics = _montants_publics()
    for nom in PUBLICS:
        chemin = RACINE / nom
        if chemin.is_file():
            problemes += [f"{nom} : {t}" for t in fuites(chemin.read_text(encoding="utf-8"), publics)]
    for p in problemes:
        print(f"ÉCHEC : {p}")
    print(f"{'OK' if not problemes else 'ÉCHEC'} : {len(opportunites)} opportunité(s), "
          f"{len(problemes)} problème(s), sorties publiques vérifiées : {', '.join(PUBLICS)}")
    return 1 if problemes else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mere", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sous = ap.add_subparsers(dest="commande", required=True)
    t = sous.add_parser("tableau", help="consolider et écrire le tableau de bord")
    t.add_argument("--stripe", action="store_true", help="relever le prestataire de paiement (lecture seule)")
    t.add_argument("--rejouer", action="store_true", help="rejouer les suites de tests des modules")
    t.add_argument("--controler", action="store_true",
                   help="relancer les contrôles réseau : citations (pages publiques) et prospects (web public)")
    t.add_argument("--jour", help="jour évalué (AAAA-MM-JJ), par défaut aujourd'hui")
    t.set_defaults(f=tableau)
    sous.add_parser("verifier", help="valider la configuration et les sorties publiques").set_defaults(f=verifier)
    args = ap.parse_args(argv)
    return int(args.f(args))


if __name__ == "__main__":
    sys.exit(main())
