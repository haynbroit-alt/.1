"""Contrôles indépendants : aucun module ne valide seul son propre travail.

Un contrôle porte un producteur (qui affirme) et un contrôleur (qui vérifie). Ils doivent être différents :
un contrôle où le producteur se vérifie lui-même est refusé à la construction. Est indépendant un contrôleur que
le producteur ne maîtrise pas : une autorité externe (prestataire de paiement, banque, page publique, registre),
un autre module, ou une copie propre du dépôt rejouée hors de son poste de travail.

Les contrôles réseau (citations, prospects) ne tournent qu'avec `--controler` ; sinon le dernier résultat daté
est relu. Un réseau indisponible donne INCONNU, jamais un succès ni un échec.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from .sources import Evenement, _git, environnement_propre, euros_en_centimes
from .statuts import CONFLIT, ECHEC, INCONNU, PROUVE

AGENT = "Mozilla/5.0 (compatible; verification-entreprise-mere)"
FICHIERS_DE_DONNEES = (".json", ".csv")
# Une page ne prouve une note que si elle vient d'une autorité publique, ou d'un tiers nommé dans le portefeuille
# (réglage « sources_tierces »), et jamais d'un hébergeur où le producteur peut publier lui-même.
# Hôtes exacts (pas des suffixes : un sous-domaine public peut accueillir des textes déposés par n'importe qui).
AUTORITES = ("entreprendre.service-public.gouv.fr", "www.service-public.fr", "www.legifrance.gouv.fr",
             "code.travail.gouv.fr", "travail-emploi.gouv.fr", "www.economie.gouv.fr", "www.insee.fr", "www.urssaf.fr",
             "www.cnil.fr", "www.inpi.fr", "www.infogreffe.fr", "annuaire-entreprises.data.gouv.fr",
             "recherche-entreprises.api.gouv.fr", "eur-lex.europa.eu")
# Tiers reconnus : la liste vit dans le code, pas dans le portefeuille du producteur. L'allonger est un changement de
# code, donc relu par un autre agent et prouvé par NOVARYS Ω avant de compter.
TIERS_RECONNUS = ("centre-national-droit-du-travail.fr",)
HOTES_REFUSES = ("data.gouv.fr", "github.com", "githubusercontent.com", "gitlab.com", "gist.", "pastebin.",
                 "bitbucket.org",
                 "github.io", "pages.dev", "workers.dev", "notion.site", "docs.google.com", "sites.google.com",
                 "jsdelivr.net", "netlify.app", "vercel.app", "onrender.com", "herokuapp.com", "glitch.me",
                 "replit.", "wixsite.com", "webflow.io", "framer.", "carrd.co", "canva.site", "myshopify.com",
                 "blogspot.", "wordpress.com", "medium.com", "substack.com", "velyx.org")
# Messageries grand public : un domaine de ce type n'identifie pas une entreprise.
MESSAGERIES = ("gmail.com", "googlemail.com", "hotmail.", "outlook.", "live.", "yahoo.", "icloud.com", "me.com",
               "orange.fr", "wanadoo.fr", "free.fr", "sfr.fr", "laposte.net", "gmx.", "proton", "aol.", "neuf.fr")
DEPOT_DU_PRODUCTEUR = "mere"  # le portefeuille vit dans ce dépôt : ses propres fichiers ne prouvent pas ses notes


class AutoValidation(ValueError):
    """Un producteur ne peut pas être son propre contrôleur."""


@dataclass(frozen=True)
class Controle:
    id: str
    objet: str
    producteur: str
    controleur: str
    methode: str
    statut: str
    detail: str
    date: str
    reference: str = ""
    opportunite: str = "*"

    def __post_init__(self) -> None:
        if _racine(self.producteur) == _racine(self.controleur):
            raise AutoValidation(f"{self.id} : {self.producteur} ne peut pas se contrôler lui-même")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _racine(module: str) -> str:
    """« rejeu:sovereign » et « sovereign » sont le même acteur ; « mere:clone-propre » et « sovereign » non."""
    return module.split(":", 1)[-1] if module.startswith("rejeu:") else module.split(":", 1)[0]


def _maintenant() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def texte_normalise(brut: str) -> str:
    """Texte visible d'une page, sans balises, accents conservés, espaces réduits, apostrophes unifiées."""
    sans_code = re.sub(r"<script.*?</script>|<style.*?</style>", " ", brut, flags=re.S | re.I)
    texte = html.unescape(re.sub(r"<[^>]+>", " ", sans_code))
    texte = unicodedata.normalize("NFC", texte).replace("’", "'").replace("\xa0", " ")
    return re.sub(r"\s+", " ", texte).strip()


def lire_url(url: str, delai: int = 20) -> tuple[int, str]:
    """GET d'une page publique. Renvoie (code HTTP, texte). Lève OSError si le réseau ne répond pas."""
    requete = urllib.request.Request(url, headers={"User-Agent": AGENT}, method="GET")
    try:
        with urllib.request.urlopen(requete, timeout=delai) as r:  # noqa: S310
            return r.status, r.read(3_000_000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, ""


# -- Citations : la source citée dit-elle vraiment ce que la note affirme ? -------------------------------

def _hote_autorise(hote: str, tiers: tuple[str, ...] = ()) -> bool:
    """`tiers` n'élargit rien : seuls les tiers déjà reconnus par le code sont retenus (le portefeuille ne peut pas
    déclarer sa propre page comme source)."""
    def couvre(domaine: str) -> bool:
        return hote in (domaine, "www." + domaine)
    if hote in AUTORITES:  # hôte exact d'une autorité (annuaire-entreprises.data.gouv.fr compris)
        return True
    if any(r in hote for r in HOTES_REFUSES):  # data.gouv.fr : tout compte peut y publier
        return False
    return any(couvre(t) for t in TIERS_RECONNUS if t in tiers or not tiers)


def empreinte(texte: str) -> str:
    """Empreinte SHA-256 de 12 lettres (chiffres hexadécimaux traduits en g à p) : sans chiffre, elle ne peut pas
    ressembler à un SIREN, un téléphone ou un identifiant de message, et la garde n'a pas à l'excuser."""
    return hashlib.sha256(texte.encode()).hexdigest()[:12].translate(str.maketrans("0123456789", "ghijklmnop"))


def signature(verif: dict[str, Any]) -> str:
    """Empreinte de la façon de vérifier une note : un contrôle relu n'est valable que pour la même vérification."""
    return empreinte(json.dumps(verif, sort_keys=True, ensure_ascii=False))


def controler_citation(oid: str, critere: str, verif: dict[str, Any], depots: dict[str, Path | None],
                       lire: Callable[[str], tuple[int, str]] = lire_url, tiers: tuple[str, ...] = ()) -> Controle:
    """Une note « mesuré » cite une source ; un autre acteur (la page publique ou un fichier de données) confirme.

    Un document rédigé (Markdown) ne prouve rien : seules une page publique ou des données brutes comptent.
    """
    objet = f"{oid}/{critere}"
    quand = _maintenant()
    base = dict(id=f"citation:{objet}", objet=f"La source de la note « {critere} » de {oid} dit ce que la note "
                f"affirme", producteur="portefeuille", opportunite=oid, date=quand)
    sig = f" · signature {signature(verif)}" if verif else ""
    if "url" in verif:
        url, attendu = str(verif["url"]), texte_normalise(str(verif.get("contient", "")))
        hote = urllib.parse.urlparse(url).hostname or ""
        if len(attendu) < 12 or len(attendu.split()) < 2:
            return Controle(**base, controleur="page-publique", methode="lecture de la page", statut=ECHEC,
                            detail="phrase attendue trop courte pour prouver quoi que ce soit (12 caractères et "
                            "2 mots au moins)", reference=url)
        if not url.startswith("https://") or not _hote_autorise(hote, tiers):
            return Controle(**base, controleur="page-publique", methode="lecture de la page", statut=ECHEC,
                            detail="ni autorité publique ni tiers déclaré, ou hébergeur où le producteur peut "
                            "publier : ce n'est pas une source indépendante", reference=url + sig)
        try:
            code, page = lire(url)
        except OSError as exc:
            return Controle(**base, controleur="page-publique", methode="lecture de la page", statut=INCONNU,
                            detail=f"page injoignable ({type(exc).__name__})", reference=url)
        if code != 200:
            return Controle(**base, controleur="page-publique", methode="lecture de la page", statut=INCONNU,
                            detail=f"HTTP {code} : accès refusé ou page absente", reference=url)
        texte = texte_normalise(page)
        trouve = attendu.lower() in texte.lower()
        trace = empreinte(texte)
        return Controle(**base, controleur="page-publique", methode="la phrase citée figure dans la page",
                        statut=PROUVE if trouve else ECHEC,
                        detail=("phrase trouvée" if trouve else "phrase absente de la page : note à revoir")
                        + f" (empreinte du texte {trace})", reference=url + sig)
    if "fichier" in verif:
        chemin_rel = str(verif["fichier"])
        if str(verif.get("depot", "")) in ("", DEPOT_DU_PRODUCTEUR):
            return Controle(**base, controleur="donnees", methode="relecture des données", statut=ECHEC,
                            detail="données du dépôt du portefeuille lui-même : le producteur ne se cite pas",
                            reference=chemin_rel)
        if verif.get("valeur") is None and verif.get("min") is None and verif.get("max") is None:
            return Controle(**base, controleur="donnees", methode="relecture des données", statut=ECHEC,
                            detail="aucune valeur, ni minimum, ni maximum attendu : rien à vérifier",
                            reference=chemin_rel)
        base_depot = depots.get(str(verif.get("depot", "")))
        if not chemin_rel.endswith(FICHIERS_DE_DONNEES):
            return Controle(**base, controleur="donnees", methode="relecture des données", statut=ECHEC,
                            detail="un document rédigé n'est pas une preuve : citer des données brutes",
                            reference=chemin_rel)
        if base_depot is None or not (base_depot / chemin_rel).is_file():
            return Controle(**base, controleur="donnees", methode="relecture des données", statut=INCONNU,
                            detail="fichier de données absent de cette machine", reference=chemin_rel + sig)
        suivi = _git(base_depot, "ls-files", "--", chemin_rel) == chemin_rel
        modifie = _git(base_depot, "status", "--porcelain", "--", chemin_rel) != ""
        if not suivi or modifie:
            return Controle(**base, controleur="donnees", methode="relecture des données", statut=INCONNU,
                            detail="fichier de données non versionné ou modifié localement : non opposable",
                            reference=chemin_rel + sig)
        try:
            donnees = json.loads((base_depot / chemin_rel).read_text(encoding="utf-8"))
            valeur: Any = donnees
            for morceau in str(verif["cle"]).split("."):
                valeur = valeur[morceau]
        except (ValueError, KeyError, TypeError) as exc:
            return Controle(**base, controleur="donnees", methode="relecture des données", statut=ECHEC,
                            detail=f"clé {verif.get('cle')!r} illisible ({type(exc).__name__})", reference=chemin_rel)
        attendu_v = verif.get("valeur")
        if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
            return Controle(**base, controleur="donnees", methode="relecture des données", statut=ECHEC,
                            detail="la valeur citée n'est pas un nombre (contenu non recopié)", reference=chemin_rel)
        try:
            ok = (valeur == attendu_v) if attendu_v is not None else (
                (verif.get("min") is None or valeur >= verif["min"])
                and (verif.get("max") is None or valeur <= verif["max"]))
        except TypeError:
            ok = False
        commit = _git(base_depot, "rev-parse", "HEAD")[:12]
        # Le nombre lu n'est publié que si la note le déclare public (statistique agrégée) : il pourrait être privé.
        lu = f"{valeur!r}" if verif.get("public") is True else "valeur en privé"
        # Un fichier d'un autre dépôt de l'écosystème a été écrit par la même lignée d'acteurs : il peut contredire
        # une note (CONFLIT), jamais la prouver seul. Il faut une source externe pour PROUVÉ.
        return Controle(**base, controleur="donnees", methode=f"{verif['cle']} relu dans le fichier versionné",
                        statut=INCONNU if ok else CONFLIT,
                        detail=(f"{lu} conforme aux données internes ; ce n'est pas une source indépendante" if ok
                                else f"le fichier dit {lu}, la note suppose autre chose"),
                        reference=f"{verif.get('depot')}@{commit}:{chemin_rel}{sig}")
    return Controle(**base, controleur="aucun", methode="aucune", statut=INCONNU,
                    detail="note « mesuré » sans source vérifiable : comptée comme une hypothèse")


# -- Argent : le paiement est-il rapproché, versé, crédité en banque ? -------------------------------------

def lire_releve_bancaire(chemin: Path | None) -> tuple[list[tuple[str, int, str]] | None, list[str]]:
    """Relevé bancaire exporté par le propriétaire (privé) : date;libelle;montant;reference. Crédits seulement."""
    if chemin is None or not chemin.is_file():
        return None, []
    lignes, erreurs = [], []
    brut = chemin.read_bytes()
    try:
        texte = brut.decode("utf-8-sig")
    except UnicodeDecodeError:
        texte = brut.decode("cp1252", errors="replace")  # export bancaire Windows, courant en France
    for n, ligne in enumerate(csv.DictReader(io.StringIO(texte), delimiter=";"), 2):
        try:
            jour = (ligne.get("date") or "").strip()
            date.fromisoformat(jour)
            montant = euros_en_centimes(ligne.get("montant") or "")
        except ValueError:
            erreurs.append(f"relevé ligne {n} : date ou montant illisible")
            continue
        if montant > 0:
            lignes.append((jour, montant, (ligne.get("libelle") or "").strip()))
    return lignes, erreurs


def rapprocher_virements(virements: list[dict[str, Any]], releve: list[tuple[str, int, str]] | None,
                         jour: date, tolerance_jours: int = 4) -> Controle:
    """Chaque virement versé par le prestataire doit apparaître au crédit du relevé (montant exact, ± 4 jours).

    Producteur : le prestataire (il affirme avoir versé). Contrôleur : la banque, via le relevé du propriétaire.
    """
    payes = [v for v in virements if v.get("status") == "paid" and v.get("livemode")]
    base = dict(id="argent:credite-en-banque", objet="L'argent versé par le prestataire est crédité en banque",
                producteur="stripe", controleur="banque", methode="rapprochement montant exact et date ± 4 jours",
                date=_maintenant())
    if not payes:
        return Controle(**base, statut=PROUVE, detail="aucun virement versé : rien à créditer",
                        reference="/v1/payouts")
    if releve is None:
        return Controle(**base, statut=INCONNU, detail=f"{len(payes)} virement(s) versé(s), aucun relevé bancaire "
                        "fourni (prive/banque.csv)", reference="/v1/payouts")
    restants = list(releve)
    manquants = 0
    for v in payes:
        arrivee = datetime.fromtimestamp(int(v.get("arrival_date") or 0), UTC).date()
        trouve = next((r for r in restants if r[1] == int(v.get("amount") or 0)
                       and abs((date.fromisoformat(r[0]) - arrivee).days) <= tolerance_jours), None)
        if trouve:
            restants.remove(trouve)
        else:
            manquants += 1
    if manquants:
        return Controle(**base, statut=CONFLIT, detail=f"{manquants} virement(s) versé(s) sans crédit correspondant "
                        "sur le relevé", reference="/v1/payouts + relevé")
    return Controle(**base, statut=PROUVE, detail=f"{len(payes)} virement(s) retrouvé(s) au crédit",
                    reference="/v1/payouts + relevé")


# -- Prospects : existent-ils vraiment ? ------------------------------------------------------------------

@dataclass(frozen=True)
class Prospect:
    opportunite: str
    ref: str
    domaine: str
    rebond: bool


def prospects_contactes(evenements: list[Evenement] | None, domaines: dict[tuple[str, str], str]) -> list[Prospect]:
    if not evenements:
        return []
    rebonds = {(e.opportunite, e.ref) for e in evenements if e.etape == "rebond"}
    vus: dict[tuple[str, str], Prospect] = {}
    for e in evenements:
        cle = (e.opportunite, e.ref)
        if e.etape in ("envoi", "relance") and cle not in vus:
            vus[cle] = Prospect(e.opportunite, e.ref, domaines.get(cle, ""), cle in rebonds)
    return list(vus.values())


def controler_prospect(p: Prospect, lire: Callable[[str], tuple[int, str]] = lire_url,
                       domaines_messagerie: set[str] | None = None, opposable: bool = False) -> Controle:
    # `domaines_messagerie` : domaines relevés pour CETTE opportunité par le second lecteur.
    """Un prospect est réel si son adresse n'a pas rebondi ET si le site de son domaine répond (2xx ou 3xx). Le
    domaine écrit dans le pipeline doit figurer dans le second relevé de la messagerie quand il existe.

    Producteur : le pipeline (qui a envoyé). Contrôleur : le web public. Un rebond est un ÉCHEC ; un site qui ne
    répond pas reste INCONNU (le réseau ou un pare-feu peut en être la cause), jamais un succès.
    """
    base = dict(id=f"prospect:{p.opportunite}:{p.ref}", objet="Le prospect contacté existe", producteur="pipeline",
                controleur="web-public", methode="absence de rebond et site du domaine joignable",
                date=_maintenant(), opportunite=p.opportunite)
    if p.rebond:
        return Controle(**base, statut=ECHEC, detail="adresse rejetée par le serveur du destinataire")
    if not p.domaine or "." not in p.domaine or "/" in p.domaine:
        return Controle(**base, statut=INCONNU, detail="domaine absent du pipeline")
    if any(m in p.domaine for m in MESSAGERIES):
        return Controle(**base, statut=INCONNU, detail="messagerie grand public : n'identifie pas une entreprise")
    if domaines_messagerie is None:
        return Controle(**base, statut=INCONNU, detail="aucun second relevé de la messagerie : le domaine, écrit par "
                        "l'auteur du pipeline, n'est pas confirmé")
    if p.domaine not in domaines_messagerie:
        return Controle(**base, statut=ECHEC, detail="domaine absent du second relevé de la messagerie : le pipeline "
                        "ne dit pas à qui le message est parti")
    codes = []
    for url in (f"https://{p.domaine}/", f"https://www.{p.domaine}/"):
        try:
            code, _ = lire(url)
        except OSError:
            continue
        codes.append(code)
        if 200 <= code < 400:
            if not opposable:
                # Le site existe, mais que le message soit parti à ce domaine n'est attesté que par des fichiers
                # écrits hors de la mère : pas de PROUVÉ.
                return Controle(**base, statut=INCONNU, detail=f"site joignable (HTTP {code}) ; destinataire confirmé "
                                "par un relevé non opposable")
            return Controle(**base, statut=PROUVE, detail=f"site joignable (HTTP {code})")
    detail = f"site sans réponse exploitable (HTTP {', '.join(map(str, codes))})" if codes else \
        "site injoignable depuis cette machine"
    return Controle(**base, statut=INCONNU, detail=detail)


# -- Suites de tests : rejouées deux fois dans une copie propre ---------------------------------------------

def _compte(bilan: str) -> str:
    """« 292 passed in 8.10s » -> « 292 passed » : la durée n'entre pas dans la concordance."""
    return re.sub(r"\s+in\s+[\d.]+s\b.*$", "", bilan).strip()


def rejouer_propre(nom: str, depot: Path | None, commande: list[str], bilan: str, essais: int = 2,
                   delai: int = 900) -> dict[str, Any]:
    """Clone le commit courant du module dans un dossier neuf (rien d'ignoré, rien de local), y rejoue la suite
    `essais` fois. PROUVÉ = toutes les exécutions réussies, ligne de bilan vue, bilans concordants.
    Le dépôt d'origine ne doit pas changer pendant le contrôle."""
    quand = _maintenant()
    resultat: dict[str, Any] = {"nom": nom, "date": quand, "controleur": "mere:clone-propre", "essais": [],
                                "commit": "", "statut": INCONNU, "bilan": "", "note": ""}
    if depot is None or not depot.is_dir():
        resultat["note"] = "dépôt absent de cette machine"
        return resultat
    commit = _git(depot, "rev-parse", "HEAD")
    resultat["commit"] = commit[:12]
    avant = _git(depot, "status", "--porcelain", "--ignored")
    if avant:
        resultat["note"] = "dépôt d'origine modifié : seul le commit est rejoué, les modifications locales non"
    for _ in range(essais):
        dossier = Path(tempfile.mkdtemp(prefix=f"rejeu-{nom}-"))
        try:
            clone = subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(depot), str(dossier / "d")],
                                   capture_output=True, text=True, timeout=300, check=False)
            if clone.returncode != 0:
                resultat["essais"].append({"code": -3, "bilan": "", "note": "clonage impossible"})
                continue
            subprocess.run(["git", "-C", str(dossier / "d"), "checkout", "-q", commit], capture_output=True,
                           timeout=60, check=False)
            try:
                fini = subprocess.run(commande, cwd=dossier / "d", env=environnement_propre(), capture_output=True,
                                      text=True, timeout=delai, check=False)
                sortie, code = (fini.stdout or "") + (fini.stderr or ""), fini.returncode
            except subprocess.TimeoutExpired:
                sortie, code = "", -1
            except OSError as exc:
                sortie, code = str(exc), -2
            vus = [ligne.strip() for ligne in sortie.splitlines() if re.search(bilan, ligne)]
            essai = {"code": code, "bilan": vus[-1][:200] if vus else ""}
            lances = re.findall(r"^Ran (\d+) tests?", sortie, flags=re.M)
            sautes = re.findall(r"skipped=(\d+)", sortie)
            if lances and int(lances[-1]) - (int(sautes[-1]) if sautes else 0) <= 0:
                essai["bilan"] = ""  # unittest : tous les tests sautés, rien n'a été exécuté
            resultat["essais"].append(essai)
        finally:
            shutil.rmtree(dossier, ignore_errors=True)
    essais_faits = resultat["essais"]
    codes = {e["code"] for e in essais_faits}
    comptes = {_compte(e["bilan"]) for e in essais_faits}
    # Un bilan « 0 passed » ou « # pass 0 » ne prouve rien : aucun test n'a tourné.
    if any(re.match(r"^\D*0\b", e["bilan"]) for e in essais_faits if e["bilan"]):
        comptes.add("")
    if (_git(depot, "status", "--porcelain", "--ignored") != avant
            or _git(depot, "rev-parse", "HEAD") != commit):
        resultat["statut"], resultat["note"] = INCONNU, "le dépôt d'origine a changé pendant le contrôle"
    elif not commit or codes & {-1, -2, -3}:
        # Clonage impossible, outil absent ou délai dépassé : l'environnement est en cause, pas encore la suite.
        resultat["statut"], resultat["note"] = INCONNU, "dépôt non clonable, outil absent ou délai dépassé"
    elif len(essais_faits) < essais:
        resultat["statut"] = INCONNU
    elif codes == {0} and "" not in comptes and len(comptes) == 1:
        resultat["statut"], resultat["bilan"] = PROUVE, essais_faits[-1]["bilan"]
    elif 0 not in codes:
        resultat["statut"], resultat["bilan"] = ECHEC, essais_faits[-1]["bilan"]
    elif codes == {0} and "" in comptes:
        resultat["statut"], resultat["note"] = INCONNU, "code 0 sans ligne de bilan : non vérifié"
    else:
        resultat["statut"], resultat["note"] = CONFLIT, "exécutions discordantes : suite instable"
    return resultat


def controle_suite(r: dict[str, Any], depot: Path | None, ce_passage: bool = True) -> Controle:
    """`ce_passage` : faux quand le résultat est relu d'un passage précédent (etat/rejeux.json). Il n'est alors
    jamais PROUVÉ : ce fichier est la mémoire de la mère, et il se modifie à la main."""
    actuel = _git(depot, "rev-parse", "HEAD")[:12] if depot else ""
    statut, detail = r["statut"], r.get("bilan") or r.get("note") or ""
    if not ce_passage and statut == PROUVE:
        statut, detail = INCONNU, f"PROUVÉ au rejeu du {str(r.get('date'))[:10]}, non rejoué dans ce passage"
    elif r.get("controleur") != "mere:clone-propre" or len(r.get("essais", [])) < 2:
        statut, detail = INCONNU, "rejeu ancien ou unique, hors clone propre : à refaire avec --rejouer"
    elif statut == PROUVE and depot is not None and _git(depot, "status", "--porcelain"):
        statut, detail = INCONNU, "dépôt modifié depuis le rejeu : le code présent n'est pas celui qui a été testé"
    elif statut == PROUVE and actuel != r.get("commit"):
        statut, detail = INCONNU, f"rejoué sur {r.get('commit')}, dépôt maintenant à {actuel or '?'}"
    return Controle(id=f"suite:{r['nom']}", objet=f"La suite de tests de {r['nom']} passe", producteur=r["nom"],
                    controleur="mere:clone-propre", methode=f"{len(r.get('essais', []))} exécution(s) dans un clone "
                    "neuf du commit, bilans comparés", statut=statut, detail=detail, date=r["date"],
                    reference=str(r.get("commit")))


# -- La mère contrôlée par NOVARYS Ω --------------------------------------------------------------------

PERIMETRE_PROUVE = ("mere", "tests", "donnees", "pyproject.toml")


def meme_code(racine: Path | None, commit: str, chemins: tuple[str, ...] = PERIMETRE_PROUVE) -> bool:
    """Le code revendiqué (`chemins`) est-il identique, au commit `commit` et maintenant (index et copie de travail) ?
    Un tableau régénéré ne change pas le code prouvé ; une ligne de `mere/` modifiée, si."""
    if racine is None or not commit:
        return False
    try:
        r = subprocess.run(["git", "-C", str(racine), "diff", "--quiet", commit, "--", *chemins],
                           capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def controle_par_novarys(preuves: Path | None, prefixe: str, head_mere: str,
                         racine: Path | None = None) -> list[Controle]:
    """Dernière preuve NOVARYS Ω de chaque capacité de la mère. Valable seulement si le code prouvé est
    identique à celui d'aujourd'hui (même commit, ou commit différent sans changement dans le périmètre prouvé)."""
    if preuves is None or not preuves.is_file():
        return [Controle(id="novarys:mere", objet="La mère est contrôlée par un autre module", producteur="mere",
                         controleur="novarys", methode="protocole de preuve Ω", statut=INCONNU,
                         detail="registre de NOVARYS absent de cette machine", date=_maintenant())]
    dernieres: dict[str, dict[str, Any]] = {}
    with preuves.open(encoding="utf-8") as f:
        for ligne in f:
            if f'"claim":"{prefixe}' not in ligne.replace(" ", ""):
                continue
            try:
                p = json.loads(ligne)
            except ValueError:
                continue
            if str(p.get("claim", "")).startswith(prefixe):
                dernieres[p["claim"]] = p
    if not dernieres:
        return [Controle(id="novarys:mere", objet="La mère est contrôlée par un autre module", producteur="mere",
                         controleur="novarys", methode="protocole de preuve Ω", statut=INCONNU,
                         detail="aucune capacité de la mère au registre de NOVARYS", date=_maintenant())]
    sortie = []
    for claim, p in sorted(dernieres.items()):
        sujet = p.get("subject") or {}
        statut = {"PROUVE": PROUVE, "ECHEC": ECHEC, "CONFLIT": CONFLIT}.get(str(p.get("status")), INCONNU)
        detail = f"preuve n° {p.get('seq')} du {str(p.get('at'))[:10]}, statut {p.get('status')}"
        prouve_sur = str(sujet.get("commit", ""))
        identique = prouve_sur[:12] == head_mere[:12] or meme_code(racine, prouve_sur)
        if statut == PROUVE and (sujet.get("dirty") or not identique):
            statut, detail = INCONNU, detail + f", sur le commit {prouve_sur[:12]} : le code a changé depuis"
        elif statut == PROUVE and prouve_sur[:12] != head_mere[:12]:
            detail += f", commit {prouve_sur[:12]}, code identique à l'actuel"
        sortie.append(Controle(id=f"novarys:{claim}", objet=str(p.get("capability", claim)), producteur="mere",
                               controleur="novarys", methode="protocole Ω : 2 exécutions concordantes et attaque",
                               statut=statut, detail=detail, date=str(p.get("at", "")),
                               reference=f"registre/preuves.jsonl n° {p.get('seq')}"))
    return sortie


def instantane(controles: list[Controle], chemin: Path) -> None:
    chemin.parent.mkdir(exist_ok=True)
    chemin.write_text(json.dumps([c.to_dict() for c in controles], ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")


def relire(chemin: Path, ids_prefixes: tuple[str, ...]) -> list[Controle]:
    """Relit les contrôles d'un passage précédent, pour mémoire seulement : un contrôle relu n'est jamais PROUVÉ.
    Le fichier est la mémoire de la mère, modifiable : s'y fier serait se valider soi-même. Un CONFLIT ou un ÉCHEC
    relu reste affiché (une contradiction connue ne s'efface pas en ne relançant pas le contrôle)."""
    if not chemin.is_file():
        return []
    sortie = []
    try:
        entrees = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    champs = set(Controle.__dataclass_fields__)
    for d in entrees if isinstance(entrees, list) else []:
        if not isinstance(d, dict) or not str(d.get("id", "")).startswith(ids_prefixes):
            continue
        try:
            c = Controle(**{k: v for k, v in d.items() if k in champs})
            if c.statut == PROUVE:
                c = Controle(**{**c.to_dict(), "statut": INCONNU,
                                "detail": f"PROUVÉ au passage du {str(c.date)[:10]}, non refait dans ce passage"})
        except (TypeError, ValueError):
            continue  # entrée illisible ou auto-validée : ignorée, le contrôle sera refait
        sortie.append(c)
    return sortie
