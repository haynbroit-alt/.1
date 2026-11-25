"""Bilan thermique d'une surface qui se refroidit en rayonnant vers le ciel (refroidissement radiatif passif).

Modèle volontairement simple, mais physiquement cohérent et entièrement vérifiable :

1. Rayonnement de corps noir (loi de Planck), intégré numériquement par bandes de longueur d'onde.
2. Ciel à deux bandes :
   - hors de la « fenêtre atmosphérique » 8–13 µm, l'atmosphère est supposée opaque (émissivité 1) ;
   - dans la fenêtre, elle est grise, de transmittance zénithale t0, et son émissivité dépend de l'angle :
     eps(theta) = 1 - t0 ** (1 / cos theta).
   t0 est calé pour que l'émissivité hémisphérique totale du ciel égale la corrélation de Berdahl et Martin
   (1984) : eps = 0,711 + 0,56 x + 0,73 x², avec x = point de rosée en °C / 100 (moyenne sur 24 h, ciel clair,
   calée sur des points de rosée de -13 à 24 °C).
3. Surface plane tournée vers le ciel : émissivité par bande, éventuellement limitée à un cône autour du zénith
   (écran angulaire idéal : hors du cône, la surface ne voit qu'un miroir et n'échange rien).
4. Bilan : rayonnement net, soleil absorbé, apports de l'air par convection et conduction (coefficient h).

Limites (voir RESULTATS.md) : ciel clair seulement ; fenêtre grise ; bande 16–25 µm ignorée ; aucun nuage ;
corrélation calée hors des climats équatoriaux les plus humides.

Bibliothèque standard seule. Unités SI, températures en kelvins sauf mention contraire.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

H = 6.62607015e-34        # constante de Planck (J s)
C = 2.99792458e8          # vitesse de la lumière (m/s)
KB = 1.380649e-23         # constante de Boltzmann (J/K)
SIGMA = 5.670374419e-8    # constante de Stefan-Boltzmann (W/m²/K⁴)
FENETRE = (8.0, 13.0)     # fenêtre atmosphérique principale (µm)


def _simpson(f, a: float, b: float, n: int = 2000) -> float:
    """Intégrale de f sur [a, b] par la méthode de Simpson (n pair)."""
    if n % 2:
        n += 1
    pas = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * f(a + i * pas)
    return s * pas / 3


def exitance_spectrale(lambda_um: float, t: float) -> float:
    """Émittance spectrale hémisphérique d'un corps noir (W/m²/µm), loi de Planck."""
    lam = lambda_um * 1e-6
    x = H * C / (lam * KB * t)
    if x > 700:
        return 0.0
    return 2 * math.pi * H * C ** 2 / lam ** 5 / math.expm1(x) * 1e-6


def fraction_bande(t: float, debut_um: float, fin_um: float) -> float:
    """Part de l'émission totale d'un corps noir à la température t comprise entre debut_um et fin_um."""
    return _simpson(lambda l: exitance_spectrale(l, t), debut_um, fin_um, 4000) / (SIGMA * t ** 4)


def emissivite_berdahl_martin(point_rosee_c: float) -> float:
    """Émissivité hémisphérique du ciel clair, moyenne sur 24 h (Berdahl et Martin, 1984)."""
    x = point_rosee_c / 100
    return 0.711 + 0.56 * x + 0.73 * x * x


def emissivite_fenetre_cone(t0: float, demi_angle_deg: float = 90.0) -> float:
    """Émissivité du ciel dans la fenêtre, pondérée par cos θ, intégrée de 0 au demi-angle (fraction de π).

    Vaut 1 - t0 au zénith seul et décroît avec t0. Pour un cône complet (90°), c'est l'émissivité hémisphérique.
    """
    tc = math.radians(demi_angle_deg)

    def f(th: float) -> float:
        c = math.cos(th)
        if c <= 1e-9:
            return 0.0  # à l'horizon, le poids cos θ est nul
        return (1 - t0 ** (1 / c)) * c * math.sin(th) * 2

    return _simpson(f, 0.0, tc, 400)


@dataclass(frozen=True)
class Ciel:
    """Ciel clair caractérisé par la température de l'air et le point de rosée."""
    t_air: float            # K
    point_rosee_c: float    # °C

    @property
    def emissivite_totale(self) -> float:
        return emissivite_berdahl_martin(self.point_rosee_c)

    @property
    def fraction_fenetre(self) -> float:
        return fraction_bande(self.t_air, *FENETRE)

    @property
    def t0(self) -> float:
        """Transmittance zénithale de la fenêtre qui reproduit l'émissivité totale de Berdahl et Martin."""
        cible = self.emissivite_totale
        fw = self.fraction_fenetre

        def eps_total(t0: float) -> float:
            return (1 - fw) + fw * emissivite_fenetre_cone(t0)

        if cible >= 1:
            return 0.0
        if cible <= eps_total(1.0):
            return 1.0  # ciel plus sec que ce que le modèle à deux bandes peut représenter
        bas, haut = 0.0, 1.0
        for _ in range(60):
            milieu = (bas + haut) / 2
            if eps_total(milieu) > cible:
                bas = milieu
            else:
                haut = milieu
        return (bas + haut) / 2

    @property
    def calage_exact(self) -> bool:
        """Faux quand le ciel est trop sec pour le modèle à deux bandes (bande 16–25 µm ignorée) : t0 est alors
        plafonné à 1 et le ciel du modèle est plus émissif, donc moins favorable, que le ciel réel."""
        fw = self.fraction_fenetre
        return self.emissivite_totale >= (1 - fw) + fw * emissivite_fenetre_cone(1.0)

    @property
    def dans_le_domaine_valide(self) -> bool:
        """Vrai si le point de rosée est dans la plage de calage de Berdahl et Martin et si le calage est exact."""
        return -13 <= self.point_rosee_c <= 24 and self.calage_exact


@dataclass(frozen=True)
class Surface:
    """Surface tournée vers le ciel."""
    nom: str
    eps_fenetre: float = 0.95       # émissivité dans 8–13 µm
    eps_hors_fenetre: float = 0.95  # émissivité ailleurs dans l'infrarouge thermique
    absorption_solaire: float = 0.05
    demi_angle_deg: float = 90.0    # cône d'échange avec le ciel (90 = sans écran angulaire)


def puissance_radiative_nette(s: Surface, ciel: Ciel, t_surface: float) -> float:
    """Puissance rayonnée nette vers le ciel (W/m²) ; positive = la surface perd de la chaleur."""
    cone = math.sin(math.radians(s.demi_angle_deg)) ** 2   # part de l'émission cos θ dans le cône
    t0 = ciel.t0
    fw_s = fraction_bande(t_surface, *FENETRE)
    fw_a = ciel.fraction_fenetre
    m_s = SIGMA * t_surface ** 4
    m_a = SIGMA * ciel.t_air ** 4
    fenetre = s.eps_fenetre * (fw_s * m_s * cone - fw_a * m_a * emissivite_fenetre_cone(t0, s.demi_angle_deg))
    ailleurs = s.eps_hors_fenetre * ((1 - fw_s) * m_s - (1 - fw_a) * m_a) * cone
    return fenetre + ailleurs


def bilan(s: Surface, ciel: Ciel, t_surface: float, soleil: float, h: float) -> float:
    """Flux net sortant (W/m²) : rayonnement net − soleil absorbé − apports de l'air."""
    return (puissance_radiative_nette(s, ciel, t_surface)
            - s.absorption_solaire * soleil
            - h * (ciel.t_air - t_surface))


def temperature_equilibre(s: Surface, ciel: Ciel, soleil: float, h: float) -> float:
    """Température de la surface sans charge à refroidir (K), par dichotomie sur le bilan."""
    bas, haut = ciel.t_air - 80, ciel.t_air + 80
    for _ in range(80):
        milieu = (bas + haut) / 2
        if bilan(s, ciel, milieu, soleil, h) > 0:
            haut = milieu   # perd encore de la chaleur : l'équilibre est plus froid
        else:
            bas = milieu
    return (bas + haut) / 2
