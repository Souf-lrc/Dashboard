import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests

# Configuration de la page
st.set_page_config(page_title="Inflation en Europe", layout="wide")
st.title("Dashboard Inflation en Europe")

# Fonction pour récupérer les données d'Eurostat via leur API REST
@st.cache_data
def get_inflation_data():
    # URL de l'API Eurostat pour HICP
    url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr"
    
    # Paramètres de la requête
    params = {
        'format': 'JSON',
        'lang': 'en',
        'freq': 'M',  # Mensuel
        'unit': 'RCH_A',  # Taux annuel de changement
        'coicop': 'CP00'  # Tous items
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Vérifie si la requête a réussi
        data = response.json()
        
        # Transformation en DataFrame
        values = data['value']
        dimensions = data['dimension']
        
        # Création d'une liste de données
        records = []
        for time_key in dimensions['time']['category']['index'].keys():
            for geo_key in dimensions['geo']['category']['index'].keys():
                value_key = f"{time_key},{geo_key}"
                if value_key in values:
                    records.append({
                        'time': time_key,
                        'geo': geo_key,
                        'value': values[value_key]
                    })
        
        df = pd.DataFrame(records)
        
        # Conversion de la colonne time en datetime
        df['time'] = pd.to_datetime(df['time'], format='%Y-%m')
        
        # Pivot de la table
        df_pivot = df.pivot(index='time', columns='geo', values='value')
        
        return df_pivot
        
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {str(e)}")
        return None

# Chargement des données
df = get_inflation_data()

if df is not None:
    # Sélection des pays
    pays_disponibles = sorted(df.columns)
    pays_selectionnes = st.multiselect(
        "Sélectionnez les pays à afficher",
        pays_disponibles,
        default=['EA', 'FR', 'DE', 'IT', 'ES'] if all(pays in pays_disponibles for pays in ['EA', 'FR', 'DE', 'IT', 'ES']) else pays_disponibles[:5]
    )

    if pays_selectionnes:
        # Période
        dates_disponibles = df.index.sort_values()
        date_debut = dates_disponibles[0]
        date_fin = dates_disponibles[-1]
        
        default_start = date_fin - timedelta(days=365*2)  # 2 ans par défaut
        default_start = max(date_debut, default_start)
        
        periode = st.slider(
            "Sélectionnez la période",
            min_value=date_debut,
            max_value=date_fin,
            value=(default_start, date_fin)
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

# Ajout d'informations sur les données
st.markdown("---")
st.caption("""
    Source : Eurostat - HICP (Harmonised Index of Consumer Prices)
    Mise à jour : Mensuelle
    Note : EA = Zone Euro
""")
