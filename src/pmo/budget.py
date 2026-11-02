"""Suivi budgétaire du programme : réalisé vs prévu, atterrissage et écarts."""
from __future__ import annotations

import pandas as pd


def synthese_par_lot(budget: pd.DataFrame, mois_courant: str) -> pd.DataFrame:
    """Synthèse par lot à une date d'arrêté.

    - BAC : budget total alloué au lot (Budget At Completion)
    - prevu_cumule / consomme_cumule / engage_cumule : cumuls à date
    - indice_perf : consommé / prévu à date (>1 = surconsommation)
    - atterrissage : projection du coût final = BAC x indice_perf
    - ecart_atterrissage : atterrissage - BAC (positif = dépassement)
    """
    df = budget.copy()
    a_date = df[df["mois"] <= mois_courant]
    bac = df.groupby(["lot", "libelle"])["prevu"].sum().rename("bac")
    cumuls = a_date.groupby(["lot", "libelle"])[["prevu", "engage", "consomme"]].sum()
    cumuls.columns = ["prevu_cumule", "engage_cumule", "consomme_cumule"]
    out = pd.concat([bac, cumuls], axis=1).reset_index()
    out["indice_perf"] = out["consomme_cumule"] / out["prevu_cumule"]
    out["atterrissage"] = out["bac"] * out["indice_perf"]
    out["ecart_atterrissage"] = out["atterrissage"] - out["bac"]
    out["ecart_pct"] = out["ecart_atterrissage"] / out["bac"]
    out["taux_consommation"] = out["consomme_cumule"] / out["bac"]
    return out.round({"indice_perf": 3, "atterrissage": 0, "ecart_atterrissage": 0,
                      "ecart_pct": 4, "taux_consommation": 4})


def synthese_programme(synthese_lots: pd.DataFrame) -> dict:
    """Agrège la synthèse par lot au niveau programme."""
    tot = synthese_lots[["bac", "prevu_cumule", "engage_cumule", "consomme_cumule",
                         "atterrissage"]].sum()
    ecart = tot["atterrissage"] - tot["bac"]
    return {
        "bac": float(tot["bac"]),
        "prevu_cumule": float(tot["prevu_cumule"]),
        "engage_cumule": float(tot["engage_cumule"]),
        "consomme_cumule": float(tot["consomme_cumule"]),
        "atterrissage": float(tot["atterrissage"]),
        "ecart_atterrissage": float(ecart),
        "ecart_pct": float(ecart / tot["bac"]),
    }


def trajectoire(budget: pd.DataFrame) -> pd.DataFrame:
    """Courbes cumulées mensuelles (prévu / engagé / consommé) au niveau programme."""
    mensuel = budget.groupby("mois")[["prevu", "engage", "consomme"]].sum(min_count=1)
    cumul = mensuel.cumsum()
    # On ne prolonge pas le réalisé au-delà du dernier mois connu
    cumul.loc[mensuel["consomme"].isna(), ["engage", "consomme"]] = None
    return cumul.reset_index()


def lots_en_alerte(synthese_lots: pd.DataFrame, seuil: float = 0.05) -> pd.DataFrame:
    """Lots dont l'atterrissage dépasse le budget de plus de `seuil` (5 % par défaut)."""
    return synthese_lots[synthese_lots["ecart_pct"] > seuil].sort_values(
        "ecart_pct", ascending=False)
