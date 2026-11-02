"""Suivi de l'adoption des nouveaux outils par les utilisateurs."""
from __future__ import annotations

import pandas as pd


def taux_par_module(adoption: pd.DataFrame) -> pd.DataFrame:
    """Taux d'adoption (actifs / cibles) par module et par mois."""
    d = adoption.copy()
    d["taux_adoption"] = d["utilisateurs_actifs"] / d["utilisateurs_cibles"]
    return d


def dernier_etat(adoption: pd.DataFrame) -> pd.DataFrame:
    """Dernier taux connu de chaque module."""
    d = taux_par_module(adoption)
    return d.sort_values("mois").groupby("module").tail(1).sort_values("taux_adoption")


def taux_global(adoption: pd.DataFrame) -> float:
    """Taux d'adoption global, pondéré par le nombre d'utilisateurs cibles."""
    d = dernier_etat(adoption)
    return float(d["utilisateurs_actifs"].sum() / d["utilisateurs_cibles"].sum())
