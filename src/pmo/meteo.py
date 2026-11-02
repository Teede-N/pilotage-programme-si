"""Météo synthétique du programme à destination des sponsors.

Chaque axe (budget, délais, risques, décommissionnement, adoption) reçoit une
météo sur une échelle à 4 niveaux. Les règles sont explicites et paramétrables pour
que la météo soit objective, reproductible et discutable en comité.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

NIVEAUX = ["Soleil", "Nuageux", "Pluie", "Orage"]
ICONES = {"Soleil": "☀️", "Nuageux": "⛅", "Pluie": "🌧️", "Orage": "⛈️"}
COULEURS = {"Soleil": "#2e9e5b", "Nuageux": "#d9a400", "Pluie": "#e0702d", "Orage": "#c62f3a"}


@dataclass
class Meteo:
    axe: str
    niveau: str
    indicateur: str
    commentaire: str

    @property
    def icone(self) -> str:
        return ICONES[self.niveau]

    @property
    def couleur(self) -> str:
        return COULEURS[self.niveau]


def _par_seuils(valeur: float, seuils: tuple[float, float, float]) -> str:
    """Retourne le niveau selon 3 seuils croissants (valeur élevée = mauvais)."""
    for niveau, s in zip(NIVEAUX[:3], seuils):
        if valeur <= s:
            return niveau
    return NIVEAUX[3]


def meteo_budget(ecart_pct: float) -> Meteo:
    niveau = _par_seuils(ecart_pct, (0.02, 0.05, 0.10))
    return Meteo("Budget", niveau, f"Atterrissage {ecart_pct:+.1%} vs budget",
                 "Écart projeté à terminaison sur l'ensemble des lots.")


def meteo_delais(jalons: pd.DataFrame, date_ref: str) -> Meteo:
    j = jalons.copy()
    j["date_prevue"] = pd.to_datetime(j["date_prevue"])
    j["date_reelle"] = pd.to_datetime(j["date_reelle"])
    ref = pd.Timestamp(date_ref)
    passes = j[j["date_prevue"] <= ref]
    retard = ((passes["date_reelle"].isna()) |
              (passes["date_reelle"] > passes["date_prevue"] + pd.Timedelta(days=7)))
    a_risque = (j["statut"] == "À risque").sum()
    taux = (retard.sum() + a_risque) / max(len(j), 1)
    niveau = _par_seuils(taux, (0.10, 0.25, 0.40))
    return Meteo("Délais", niveau, f"{int(retard.sum())} jalon(s) en retard, {a_risque} à risque",
                 "Retard = jalon échu non livré ou livré > 7 jours après la date prévue.")


def meteo_risques(risques: pd.DataFrame) -> Meteo:
    crit = risques["probabilite"] * risques["impact"]
    niveau = _par_seuils(float(crit.max()), (6, 9, 12))
    top = risques.loc[crit.idxmax(), "risque"]
    return Meteo("Risques", niveau, f"Criticité max {int(crit.max())}/16",
                 f"Risque principal : {top}.")


def meteo_decommissionnement(taux_economies: float, nb_retards: int) -> Meteo:
    manque = 1 - taux_economies
    niveau = _par_seuils(manque + 0.10 * nb_retards, (0.40, 0.70, 1.00))
    return Meteo("Décommissionnement", niveau,
                 f"{taux_economies:.0%} des économies de run sécurisées",
                 f"{nb_retards} arrêt(s) d'applicatif en retard ou à risque.")


def meteo_adoption(taux_adoption: float, cible: float = 0.75) -> Meteo:
    ecart = cible - taux_adoption
    niveau = _par_seuils(ecart, (0.0, 0.05, 0.15))
    return Meteo("Adoption", niveau, f"{taux_adoption:.0%} d'utilisateurs actifs (cible {cible:.0%})",
                 "Part des utilisateurs cibles actifs sur les nouveaux outils.")


def meteo_globale(meteos: list[Meteo]) -> Meteo:
    """Météo globale : moyenne des niveaux arrondie vers le pessimiste,
    jamais meilleure que le pire axe moins un cran (un orage ne se cache pas)."""
    idx = [NIVEAUX.index(m.niveau) for m in meteos]
    moyenne = -(-sum(idx) // len(idx))  # arrondi supérieur
    niveau = NIVEAUX[max(moyenne, max(idx) - 1)]
    alertes = [m.axe for m in meteos if NIVEAUX.index(m.niveau) >= 2]
    com = "Points d'attention : " + ", ".join(alertes) if alertes else "Programme sous contrôle."
    return Meteo("Programme", niveau, f"{len(alertes)} axe(s) en alerte", com)
