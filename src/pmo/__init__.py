"""Boîte à outils de pilotage PMO d'un programme de transformation SI (données fictives)."""
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MOIS_COURANT = "2026-10"
DATE_REF = "2026-10-31"


def charger(nom: str) -> pd.DataFrame:
    """Charge un CSV du dossier data/ (le régénère si absent)."""
    chemin = DATA_DIR / f"{nom}.csv"
    if not chemin.exists():
        import runpy
        runpy.run_path(str(DATA_DIR / "generate_data.py"), run_name="__main__")
    return pd.read_csv(chemin)
