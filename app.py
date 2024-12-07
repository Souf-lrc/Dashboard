import streamlit as st
import pandas as pd
import plotly.express as px
import eurostat

# Configuration de la page
st.set_page_config(page_title="Inflation en Europe", layout="wide")
st.title("Dashboard Inflation en Europe")

# Fonction pour récupérer les données d'Eurostat
@st.cache_data  # Cache les données pour éviter de recharger à chaque interaction
def get_inflation_data():
    # Code Eurostat pour l'indice HICP (Harmonised Index of Consumer Prices)
    code = 'prc_hicp_manr'
    
    # Récupération des données via l'API Eurostat
    data = eurostat.get_data_df(code)
    
    # Nettoyage et préparation des données
    data = data[data['unit'] == 'RCH_A']  # Taux annuel de changement
    data = data[data['coicop'] == 'CP00']  # Tous items
    
    # Pivot de la table pour avoir les pays en colonnes
    data_clean = data.pivot(index='time', columns='geo', values='values')
    
    return data_clean

try:
    # Chargement des données
    df = get_inflation_data()

    # Sélection des pays
    pays_disponibles = sorted(df.columns)
    pays_selectionnes = st.multiselect(
        "Sélectionnez les pays à afficher",
        pays_disponibles,
        default=['EA', 'FR', 'DE', 'IT', 'ES']  # Zone Euro et quelques pays majeurs
    )

    # Période
    periode = st.slider(
        "Sélectionnez la période",
        min_value=df.index.min(),
        max_value=df.index.max(),
        value=(df.index.max() - pd.DateOffset(years=2), df.index.max())
    )

    # Filtrage des données selon la sélection
    df_filtered = df.loc[periode[0]:periode[1]][pays_selectionnes]

    # Création de deux colonnes
    col1, col2 = st.columns([2, 1])

    with col1:
        # Graphique d'évolution
        fig = px.line(
            df_filtered,
            title="Évolution de l'inflation",
            labels={"value": "Inflation (%)", "time": "Date"},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Tableau des dernières valeurs
        st.subheader("Dernières valeurs")
        latest_data = df_filtered.iloc[-1].sort_values(ascending=False)
        st.dataframe(
            latest_data.reset_index().rename(
                columns={'index': 'Pays', latest_data.name: 'Inflation (%)'}
            )
        )

        # Statistiques
        st.subheader("Statistiques")
        stats = df_filtered.describe().round(2)
        st.dataframe(stats)

except Exception as e:
    st.error(f"Erreur lors de la récupération des données : {str(e)}")
    st.info("Vérifiez votre connexion Internet et l'accès à l'API Eurostat")

# Ajout d'informations sur les données
st.markdown("---")
st.caption("""
    Source : Eurostat - HICP (Harmonised Index of Consumer Prices)
    Mise à jour : Mensuelle
    Note : EA = Zone Euro
""")
