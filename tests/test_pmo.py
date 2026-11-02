import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pmo import adoption, budget, decommissionnement, meteo  # noqa: E402
from pmo.indicateurs import calculer  # noqa: E402


@pytest.fixture
def budget_simple():
    return pd.DataFrame({
        "lot": ["A", "A", "B", "B"], "libelle": ["a", "a", "b", "b"],
        "mois": ["2026-01", "2026-02", "2026-01", "2026-02"],
        "prevu": [100, 100, 200, 200], "engage": [120, None, 210, None],
        "consomme": [110, None, 180, None],
    })


def test_atterrissage_par_lot(budget_simple):
    s = budget.synthese_par_lot(budget_simple, "2026-01").set_index("lot")
    assert s.loc["A", "bac"] == 200
    assert s.loc["A", "indice_perf"] == pytest.approx(1.10)
    assert s.loc["A", "atterrissage"] == pytest.approx(220)
    assert s.loc["B", "ecart_pct"] == pytest.approx(-0.10)


def test_lots_en_alerte(budget_simple):
    s = budget.synthese_par_lot(budget_simple, "2026-01")
    assert list(budget.lots_en_alerte(s)["lot"]) == ["A"]


@pytest.mark.parametrize("ecart,attendu", [(0.01, "Soleil"), (0.04, "Nuageux"),
                                           (0.08, "Pluie"), (0.20, "Orage")])
def test_meteo_budget(ecart, attendu):
    assert meteo.meteo_budget(ecart).niveau == attendu


def test_meteo_globale_ne_cache_pas_un_orage():
    axes = [meteo.Meteo("a", "Soleil", "", ""), meteo.Meteo("b", "Soleil", "", ""),
            meteo.Meteo("c", "Soleil", "", ""), meteo.Meteo("d", "Orage", "", "")]
    assert meteo.meteo_globale(axes).niveau == "Pluie"


def test_economies_decommissionnement():
    apps = pd.DataFrame({
        "id": [1, 2], "application": ["X", "Y"], "lot": ["L", "L"],
        "cout_run_annuel": [100, 300], "date_cible": ["2026-11-15", "2026-01-01"],
        "etape": ["Arrêté", "Gel fonctionnel"], "nb_dependances": [2, 4],
        "dependances_traitees": [2, 1],
    })
    e = decommissionnement.enrichir(apps, "2026-10-31")
    assert decommissionnement.economies(e)["taux"] == pytest.approx(0.25)
    assert e.loc[1, "statut_pilotage"] == "En retard"
    assert decommissionnement.nb_alertes(e) == 1


def test_taux_adoption_pondere():
    d = pd.DataFrame({"module": ["A", "A", "B"], "mois": ["2026-09", "2026-10", "2026-10"],
                      "utilisateurs_cibles": [100, 100, 300],
                      "utilisateurs_actifs": [10, 80, 150]})
    assert adoption.taux_global(d) == pytest.approx(230 / 400)


def test_pipeline_complet():
    ind = calculer()
    assert ind["meteo_globale"].niveau in meteo.NIVEAUX
    assert len(ind["meteo_axes"]) == 5
    assert ind["programme"]["bac"] > 0
