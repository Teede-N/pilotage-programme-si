"""Pilotage du décommissionnement des applicatifs remplacés.

Objectif : concrétiser la baisse des coûts de run en suivant chaque arrêt
(étape, dépendances traitées, date cible) et les économies réellement sécurisées.
"""
from __future__ import annotations

import pandas as pd

ETAPES = ["Identifié", "Analyse dépendances", "Gel fonctionnel", "Migration données", "Arrêté"]


def enrichir(apps: pd.DataFrame, date_ref: str) -> pd.DataFrame:
    df = apps.copy()
    df["date_cible"] = pd.to_datetime(df["date_cible"])
    ref = pd.Timestamp(date_ref)
    df["avancement_etape"] = df["etape"].map(lambda e: ETAPES.index(e) / (len(ETAPES) - 1))
    df["avancement_dependances"] = (df["dependances_traitees"] / df["nb_dependances"]).fillna(1)
    df["jours_restants"] = (df["date_cible"] - ref).dt.days
    arrete = df["etape"] == "Arrêté"
    # À risque : non arrêté, échéance < 60 jours et dépendances traitées < 80 %
    df["statut_pilotage"] = "Dans les temps"
    df.loc[~arrete & (df["jours_restants"] < 60) & (df["avancement_dependances"] < 0.8),
           "statut_pilotage"] = "À risque"
    df.loc[~arrete & (df["jours_restants"] < 0), "statut_pilotage"] = "En retard"
    df.loc[arrete, "statut_pilotage"] = "Arrêté"
    return df


def economies(apps_enrichies: pd.DataFrame) -> dict:
    """Économies de run annuelles : potentiel total vs sécurisé (applicatifs arrêtés)."""
    total = float(apps_enrichies["cout_run_annuel"].sum())
    securise = float(apps_enrichies.loc[apps_enrichies["etape"] == "Arrêté",
                                        "cout_run_annuel"].sum())
    return {"potentiel": total, "securise": securise,
            "reste_a_securiser": total - securise,
            "taux": securise / total if total else 0.0}


def nb_alertes(apps_enrichies: pd.DataFrame) -> int:
    return int(apps_enrichies["statut_pilotage"].isin(["À risque", "En retard"]).sum())
