"""Point d'entrée unique : calcule tous les indicateurs du programme à une date d'arrêté."""
from __future__ import annotations

from . import DATE_REF, MOIS_COURANT, adoption, budget, charger, decommissionnement, meteo


def calculer(mois_courant: str = MOIS_COURANT, date_ref: str = DATE_REF) -> dict:
    bud = charger("budget")
    jal = charger("jalons")
    ris = charger("risques")
    apps = charger("applications")
    ado = charger("adoption")

    lots = budget.synthese_par_lot(bud, mois_courant)
    prog = budget.synthese_programme(lots)
    apps_e = decommissionnement.enrichir(apps, date_ref)
    eco = decommissionnement.economies(apps_e)
    taux_ado = adoption.taux_global(ado)

    axes = [
        meteo.meteo_budget(prog["ecart_pct"]),
        meteo.meteo_delais(jal, date_ref),
        meteo.meteo_risques(ris),
        meteo.meteo_decommissionnement(eco["taux"], decommissionnement.nb_alertes(apps_e)),
        meteo.meteo_adoption(taux_ado),
    ]
    return {
        "mois_courant": mois_courant, "date_ref": date_ref,
        "budget_brut": bud, "lots": lots, "programme": prog,
        "trajectoire": budget.trajectoire(bud),
        "lots_alerte": budget.lots_en_alerte(lots),
        "jalons": jal, "risques": ris,
        "applications": apps_e, "economies": eco,
        "adoption": adoption.taux_par_module(ado),
        "adoption_dernier": adoption.dernier_etat(ado),
        "taux_adoption": taux_ado,
        "meteo_axes": axes, "meteo_globale": meteo.meteo_globale(axes),
    }
