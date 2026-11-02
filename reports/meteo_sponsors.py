"""Génère la météo synthétique du programme (one-pager HTML pour les sponsors).

Usage : python reports/meteo_sponsors.py  ->  reports/meteo_sponsors_<mois>.html
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pmo.indicateurs import calculer  # noqa: E402


def euros(x: float) -> str:
    return f"{x / 1000:,.0f} k€".replace(",", " ")


def generer(ind: dict) -> str:
    g, p, eco = ind["meteo_globale"], ind["programme"], ind["economies"]
    cartes = "".join(
        f"""<div class="carte" style="border-top:6px solid {m.couleur}">
              <div class="ico">{m.icone}</div><h3>{m.axe}</h3>
              <p class="ind">{m.indicateur}</p><p class="com">{m.commentaire}</p></div>"""
        for m in ind["meteo_axes"]
    )
    alertes = ind["lots_alerte"]
    lignes_alerte = "".join(
        f"<li><b>{r.lot} – {r.libelle}</b> : atterrissage {r.ecart_pct:+.1%} "
        f"({euros(r.ecart_atterrissage)})</li>" for r in alertes.itertuples()
    ) or "<li>Aucun lot en dépassement significatif.</li>"
    apps = ind["applications"]
    lignes_apps = "".join(
        f"<li><b>{r.application}</b> – {r.etape}, cible {r.date_cible:%d/%m/%Y} "
        f"({r.statut_pilotage})</li>"
        for r in apps[apps["statut_pilotage"].isin(["À risque", "En retard"])].itertuples()
    ) or "<li>Aucun arrêt en alerte.</li>"
    risques = ind["risques"].assign(crit=lambda d: d.probabilite * d.impact).nlargest(3, "crit")
    lignes_risques = "".join(
        f"<li><b>{r.risque}</b> (criticité {r.crit}) → {r.plan_action}</li>"
        for r in risques.itertuples()
    )
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Météo programme – {ind['mois_courant']}</title>
<style>
 body{{font-family:Segoe UI,Arial,sans-serif;margin:32px;color:#1d2733;background:#fff}}
 header{{display:flex;align-items:center;gap:20px;border-bottom:2px solid #e6e9ee;padding-bottom:16px}}
 .big{{font-size:64px}} h1{{margin:0;font-size:24px}} .sub{{color:#5b6775}}
 .kpis{{display:flex;gap:16px;margin:20px 0}}
 .kpi{{flex:1;background:#f5f7fa;border-radius:8px;padding:12px 16px}}
 .kpi b{{display:block;font-size:22px}}
 .grille{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}
 .carte{{background:#fafbfc;border-radius:8px;padding:12px}} .ico{{font-size:32px}}
 .carte h3{{margin:4px 0}} .ind{{font-weight:600;margin:4px 0}} .com{{font-size:13px;color:#5b6775}}
 .cols{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:20px}}
 h2{{font-size:16px;border-left:4px solid #1d4ed8;padding-left:8px}} li{{margin-bottom:6px;font-size:14px}}
 footer{{margin-top:24px;font-size:12px;color:#8a95a3}}
</style></head><body>
<header><div class="big">{g.icone}</div><div>
<h1>Météo du programme de modernisation SI – {g.niveau}</h1>
<div class="sub">Arrêté au {ind['date_ref']} · {g.commentaire}</div></div></header>
<div class="kpis">
 <div class="kpi">Budget total<b>{euros(p['bac'])}</b></div>
 <div class="kpi">Consommé à date<b>{euros(p['consomme_cumule'])}</b></div>
 <div class="kpi">Atterrissage<b>{euros(p['atterrissage'])} ({p['ecart_pct']:+.1%})</b></div>
 <div class="kpi">Économies de run sécurisées<b>{euros(eco['securise'])} / {euros(eco['potentiel'])}</b></div>
</div>
<div class="grille">{cartes}</div>
<div class="cols">
 <div><h2>Lots en dépassement</h2><ul>{lignes_alerte}</ul></div>
 <div><h2>Décommissionnements en alerte</h2><ul>{lignes_apps}</ul></div>
 <div><h2>Top 3 risques & plans d'action</h2><ul>{lignes_risques}</ul></div>
</div>
<footer>Généré automatiquement par pilotage-programme-si · données fictives</footer>
</body></html>"""


if __name__ == "__main__":
    ind = calculer()
    sortie = ROOT / "reports" / f"meteo_sponsors_{ind['mois_courant']}.html"
    sortie.write_text(generer(ind), encoding="utf-8")
    print(f"Météo générée : {sortie}")
