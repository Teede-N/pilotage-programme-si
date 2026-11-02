"""Tableau de bord PMO – programme de modernisation SI (données fictives).

Lancer : streamlit run app.py
"""
import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from pmo.indicateurs import calculer  # noqa: E402
from pmo.meteo import COULEURS  # noqa: E402

st.set_page_config(page_title="Pilotage programme SI", page_icon="📊", layout="wide")


@st.cache_data
def indicateurs():
    return calculer()


def keur(x):
    return f"{x / 1000:,.0f} k€".replace(",", " ")


ind = indicateurs()
g = ind["meteo_globale"]

st.title("📊 Pilotage du programme de modernisation SI")
st.caption(f"Arrêté au {ind['date_ref']} · transporteur fictif TRANSLOG · données fictives")

onglets = st.tabs(["🌤️ Météo sponsors", "💶 Budget", "🗓️ Jalons & risques",
                   "🧹 Décommissionnement", "👥 Adoption"])

# --- Météo ---------------------------------------------------------------
with onglets[0]:
    st.markdown(
        f"<div style='padding:16px;border-radius:10px;background:{g.couleur}22;"
        f"border-left:8px solid {g.couleur}'><span style='font-size:40px'>{g.icone}</span> "
        f"<b style='font-size:22px'>Météo globale : {g.niveau}</b><br>{g.commentaire}</div>",
        unsafe_allow_html=True)
    st.write("")
    cols = st.columns(len(ind["meteo_axes"]))
    for c, m in zip(cols, ind["meteo_axes"]):
        c.markdown(
            f"<div style='border-top:6px solid {m.couleur};background:#f6f8fa;padding:10px;"
            f"border-radius:8px;min-height:170px'><div style='font-size:30px'>{m.icone}</div>"
            f"<b>{m.axe}</b> – {m.niveau}<br><small><b>{m.indicateur}</b><br>{m.commentaire}"
            f"</small></div>", unsafe_allow_html=True)
    p = ind["programme"]
    st.write("")
    k = st.columns(4)
    k[0].metric("Budget total", keur(p["bac"]))
    k[1].metric("Consommé à date", keur(p["consomme_cumule"]))
    k[2].metric("Atterrissage", keur(p["atterrissage"]), f"{p['ecart_pct']:+.1%}",
                delta_color="inverse")
    k[3].metric("Économies de run sécurisées", keur(ind["economies"]["securise"]),
                f"{ind['economies']['taux']:.0%} du potentiel")

# --- Budget --------------------------------------------------------------
with onglets[1]:
    t = ind["trajectoire"]
    fig = go.Figure()
    for col, nom, dash in [("prevu", "Prévu", "dot"), ("engage", "Engagé", None),
                           ("consomme", "Consommé", None)]:
        fig.add_scatter(x=t["mois"], y=t[col], name=nom, mode="lines+markers",
                        line=dict(dash=dash))
    fig.update_layout(title="Trajectoire budgétaire cumulée (programme)", yaxis_title="€",
                      height=380, legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

    lots = ind["lots"].copy()
    fig2 = px.bar(lots, x="lot", y="ecart_pct", text_auto=".1%",
                  color=lots["ecart_pct"].gt(0.05).map({True: "Dépassement > 5 %",
                                                        False: "Sous contrôle"}),
                  color_discrete_map={"Dépassement > 5 %": COULEURS["Orage"],
                                      "Sous contrôle": COULEURS["Soleil"]},
                  hover_data=["libelle"], title="Écart d'atterrissage par lot")
    fig2.update_layout(yaxis_tickformat=".0%", height=340, legend_title="",
                       yaxis_title="Écart vs budget", xaxis_title="Lot",
                       xaxis={"categoryorder": "category ascending"})
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(
        lots[["lot", "libelle", "bac", "consomme_cumule", "engage_cumule", "atterrissage",
              "ecart_pct", "taux_consommation"]].style.format(
            {"bac": keur, "consomme_cumule": keur, "engage_cumule": keur,
             "atterrissage": keur, "ecart_pct": "{:+.1%}", "taux_consommation": "{:.0%}"}),
        use_container_width=True, hide_index=True)

# --- Jalons & risques ----------------------------------------------------
with onglets[2]:
    c1, c2 = st.columns([3, 2])
    c1.subheader("Jalons")
    c1.dataframe(ind["jalons"], use_container_width=True, hide_index=True)
    r = ind["risques"].assign(criticite=lambda d: d.probabilite * d.impact)
    fig3 = px.scatter(r, x="probabilite", y="impact", size="criticite", text="id",
                      hover_data=["risque", "plan_action"], range_x=[0.5, 4.5],
                      range_y=[0.5, 4.5], title="Matrice des risques")
    fig3.update_traces(textposition="middle center", marker_color=COULEURS["Pluie"])
    c2.plotly_chart(fig3, use_container_width=True)
    st.dataframe(r.sort_values("criticite", ascending=False), use_container_width=True,
                 hide_index=True)

# --- Décommissionnement --------------------------------------------------
with onglets[3]:
    eco = ind["economies"]
    k = st.columns(3)
    k[0].metric("Potentiel d'économies de run / an", keur(eco["potentiel"]))
    k[1].metric("Sécurisé (applicatifs arrêtés)", keur(eco["securise"]))
    k[2].metric("Reste à sécuriser", keur(eco["reste_a_securiser"]))
    a = ind["applications"]
    fig4 = px.bar(a.sort_values("cout_run_annuel"), x="cout_run_annuel", y="application",
                  color="statut_pilotage", orientation="h",
                  color_discrete_map={"Arrêté": COULEURS["Soleil"],
                                      "Dans les temps": "#5b8def",
                                      "À risque": COULEURS["Pluie"],
                                      "En retard": COULEURS["Orage"]},
                  title="Coût de run annuel par applicatif à décommissionner")
    fig4.update_layout(height=340, xaxis_title="€ / an", legend_title="")
    st.plotly_chart(fig4, use_container_width=True)
    st.dataframe(
        a[["application", "lot", "etape", "date_cible", "avancement_dependances",
           "jours_restants", "statut_pilotage"]].style.format(
            {"avancement_dependances": "{:.0%}", "date_cible": "{:%d/%m/%Y}"}),
        use_container_width=True, hide_index=True)

# --- Adoption -----------------------------------------------------------
with onglets[4]:
    st.metric("Taux d'adoption global (pondéré)", f"{ind['taux_adoption']:.0%}", "cible 75 %",
              delta_color="off")
    c1, c2 = st.columns(2)
    fig5 = px.line(ind["adoption"], x="mois", y="taux_adoption", color="module", markers=True,
                   title="Montée en charge des nouveaux outils")
    fig5.add_hline(y=0.75, line_dash="dot", annotation_text="Cible 75 %")
    fig5.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 1], legend_title="")
    c1.plotly_chart(fig5, use_container_width=True)
    der = ind["adoption_dernier"]
    fig6 = px.bar(der, x="taux_adoption", y="module", orientation="h", text_auto=".0%",
                  title="Dernier taux d'adoption par module")
    fig6.update_layout(xaxis_tickformat=".0%", xaxis_range=[0, 1])
    c2.plotly_chart(fig6, use_container_width=True)
