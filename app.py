"""
Dashboard de monitoring de troupeau laitier — Smart Livestock
Lancement : streamlit run app.py
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Smart Livestock Dashboard", layout="wide")

# ---------- Chargement des données ----------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return df

DATA_PATH = "smart_livestock_dataset.csv"
df = load_data(DATA_PATH)

st.title("🐄 Smart Livestock — Dashboard de monitoring de troupeau")
st.caption(
    "Suivi de la santé, du comportement et de la production laitière du troupeau "
    "à partir de données de capteurs (température, activité, rumination, production)."
)

# ---------- Filtres (barre latérale) ----------
st.sidebar.header("Filtres")

min_date, max_date = df["date"].min(), df["date"].max()
date_range = st.sidebar.date_input(
    "Période", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

cow_options = ["Toutes"] + sorted(df["cow_id"].unique().tolist())
selected_cow = st.sidebar.selectbox("Vache", cow_options)

only_alerts = st.sidebar.checkbox("Afficher uniquement les jours avec alerte", value=False)

# application des filtres
mask = (df["date"] >= pd.Timestamp(date_range[0])) & (df["date"] <= pd.Timestamp(date_range[1]))
filtered = df.loc[mask].copy()

if selected_cow != "Toutes":
    filtered = filtered[filtered["cow_id"] == selected_cow]

if only_alerts:
    filtered = filtered[filtered["alert_flag"] == 1]

# ---------- KPIs ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Vaches suivies", filtered["cow_id"].nunique())
col2.metric("Alertes actives", int(filtered["alert_flag"].sum()))
col3.metric("Production moyenne (L/jour)", f"{filtered['milk_yield_l'].mean():.1f}")
col4.metric("Température moyenne (°C)", f"{filtered['body_temp_c'].mean():.2f}")

st.divider()

# ---------- Liste des vaches à surveiller ----------
st.subheader("🚨 Vaches à surveiller")

alert_summary = (
    df[df["alert_flag"] == 1]
    .groupby("cow_id")
    .agg(
        derniere_alerte=("date", "max"),
        nb_alertes=("alert_flag", "sum"),
        statut_le_plus_recent=("health_status", "last"),
    )
    .reset_index()
    .sort_values("nb_alertes", ascending=False)
)

if alert_summary.empty:
    st.success("Aucune alerte sur la période sélectionnée.")
else:
    st.dataframe(alert_summary, use_container_width=True, hide_index=True)

st.divider()

# ---------- Graphiques ----------
st.subheader("📈 Évolution dans le temps")

if selected_cow != "Toutes":
    chart_df = filtered.set_index("date")
    tab1, tab2, tab3 = st.tabs(["Température", "Activité & rumination", "Production laitière"])

    with tab1:
        st.line_chart(chart_df["body_temp_c"])
    with tab2:
        st.line_chart(chart_df[["activity_index", "rumination_min"]])
    with tab3:
        st.line_chart(chart_df["milk_yield_l"])
else:
    daily_avg = filtered.groupby("date")[
        ["body_temp_c", "activity_index", "rumination_min", "milk_yield_l", "thi"]
    ].mean()

    tab1, tab2, tab3 = st.tabs(["Température moyenne", "Confort thermique (THI)", "Production moyenne"])
    with tab1:
        st.line_chart(daily_avg["body_temp_c"])
    with tab2:
        st.line_chart(daily_avg["thi"])
    with tab3:
        st.line_chart(daily_avg["milk_yield_l"])

st.divider()

# ---------- Table détaillée ----------
with st.expander("Voir les données détaillées"):
    st.dataframe(filtered.sort_values(["date", "cow_id"]), use_container_width=True, hide_index=True)
