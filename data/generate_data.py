"""Génère un jeu de données FICTIF : programme de modernisation du SI
d'un transporteur routier imaginaire ("TRANSLOG").

Aucune donnée réelle : lots, montants, applications et chiffres d'usage sont inventés
pour illustrer des méthodes de pilotage (budget, météo, décommissionnement, adoption).

Usage : python data/generate_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
OUT = Path(__file__).resolve().parent
rng = np.random.default_rng(SEED)

LOTS = [
    ("L1", "ERP Finance & facturation", 1_600_000),
    ("L2", "TMS – planification des tournées", 1_250_000),
    ("L3", "Plateforme data & reporting", 820_000),
    ("L4", "Application mobile conducteurs", 540_000),
    ("L5", "Conduite du changement & formation", 310_000),
    ("L6", "Décommissionnement de l'ancien SI", 450_000),
]
MOIS = pd.period_range("2026-01", "2026-12", freq="M")
DERNIER_MOIS_REEL = pd.Period("2026-10", "M")


def budget() -> pd.DataFrame:
    """Budget mensuel par lot : prévu, engagé (bons de commande), consommé (factures)."""
    rows = []
    derive = {"L1": 1.03, "L2": 1.11, "L3": 0.96, "L4": 1.17, "L5": 1.00, "L6": 0.92}
    for code, nom, bac in LOTS:
        profil = np.linspace(0.6, 1.4, len(MOIS))
        profil = profil / profil.sum()
        for i, m in enumerate(MOIS):
            prevu = bac * profil[i]
            reel = m <= DERNIER_MOIS_REEL
            conso = prevu * derive[code] * rng.normal(1, 0.05) if reel else np.nan
            engage = conso * rng.uniform(1.05, 1.20) if reel else np.nan
            rows.append(dict(lot=code, libelle=nom, mois=str(m), prevu=round(prevu),
                             engage=None if np.isnan(engage) else round(engage),
                             consomme=None if np.isnan(conso) else round(conso)))
    return pd.DataFrame(rows)


def jalons() -> pd.DataFrame:
    data = [
        ("J1", "L1", "Paramétrage ERP validé", "2026-03-31", "2026-04-02", "Terminé"),
        ("J2", "L2", "Pilote TMS sur l'agence de Lyon", "2026-06-30", "2026-08-04", "Terminé"),
        ("J3", "L3", "Entrepôt de données en production", "2026-07-15", "2026-07-15", "Terminé"),
        ("J4", "L4", "Bêta appli conducteurs", "2026-05-31", "2026-06-06", "Terminé"),
        ("J5", "L1", "Bascule facturation sur l'ERP", "2026-11-15", None, "En cours"),
        ("J6", "L2", "Généralisation TMS (toutes agences)", "2026-12-01", None, "En cours"),
        ("J7", "L6", "Arrêt de l'ancien logiciel d'exploitation", "2026-12-15", None, "À risque"),
        ("J8", "L3", "Tableaux de bord direction", "2027-01-15", None, "À venir"),
    ]
    return pd.DataFrame(data, columns=["id", "lot", "jalon", "date_prevue", "date_reelle", "statut"])


def risques() -> pd.DataFrame:
    data = [
        ("R1", "L2", "Disponibilité des exploitants pour la recette TMS", 4, 3, "Créneaux de recette réservés par agence"),
        ("R2", "L6", "Flux non documentés vers l'ancien logiciel", 4, 3, "Cartographie des interfaces + entretiens équipes"),
        ("R3", "L4", "Faible couverture réseau sur certaines tournées", 3, 3, "Mode hors-ligne de l'application"),
        ("R4", "L1", "Qualité des données clients reprises", 3, 2, "Contrôles automatisés avant migration"),
        ("R5", "L5", "Résistance au changement des équipes terrain", 2, 3, "Référents par agence + formations courtes"),
    ]
    return pd.DataFrame(data, columns=["id", "lot", "risque", "probabilite", "impact", "plan_action"])


def applications() -> pd.DataFrame:
    """Applications remplacées à décommissionner, avec leur coût de run annuel."""
    data = [
        ("APP-01", "EXPLOIT-2009 (ancien logiciel d'exploitation)", "L2", 280_000, "2026-12-15", "Migration données", 6, 4),
        ("APP-02", "FACTU-ACCESS (base de facturation)", "L1", 95_000, "2026-09-30", "Arrêté", 3, 3),
        ("APP-03", "Tableurs de planification partagés", "L2", 40_000, "2027-02-28", "Analyse dépendances", 5, 1),
        ("APP-04", "Ancien serveur de reporting", "L3", 110_000, "2026-11-30", "Gel fonctionnel", 4, 3),
        ("APP-05", "Boîtiers GPS ancienne génération", "L4", 72_000, "2026-08-31", "Arrêté", 2, 2),
        ("APP-06", "Outil RH local", "L1", 58_000, "2027-03-31", "Identifié", 4, 0),
    ]
    return pd.DataFrame(data, columns=["id", "application", "lot", "cout_run_annuel", "date_cible",
                                       "etape", "nb_dependances", "dependances_traitees"])


def adoption() -> pd.DataFrame:
    """Utilisateurs actifs par module et par mois, depuis la mise en service."""
    modules = [("ERP Finance", 120, "2026-04"), ("TMS", 260, "2026-08"),
               ("Reporting", 90, "2026-07"), ("Appli conducteurs", 410, "2026-06")]
    rows = []
    for nom, cible, debut in modules:
        for m in pd.period_range(debut, DERNIER_MOIS_REEL, freq="M"):
            age = (m - pd.Period(debut, "M")).n + 1
            taux = min(0.97, 0.25 + 0.16 * age + rng.normal(0, 0.03))
            rows.append(dict(module=nom, mois=str(m), utilisateurs_cibles=cible,
                             utilisateurs_actifs=int(cible * taux)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    for name, fn in {"budget": budget, "jalons": jalons, "risques": risques,
                     "applications": applications, "adoption": adoption}.items():
        df = fn()
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"{name}.csv : {len(df)} lignes")
