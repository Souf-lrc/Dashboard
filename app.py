import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# Configuration de la page
st.set_page_config(page_title="Inflation en Europe", layout="wide")
st.title("Dashboard Inflation en Europe")

# Fonction pour récupérer les données d'Eurostat
@st.cache_data(ttl=3600)  # Cache pour 1 heure
def get_inflation_data():
    try:
        # URL de l'API Eurostat pour l'inflation HICP mensuelle
        url = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/PRC_HICP_MANR"
        
        headers = {
            'Accept': 'application/json'
        }
        
        params = {
            'startPeriod': '2020',  # Données depuis 2020
            'format': 'JSON'
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Extraire les données du JSON
        observations = data['dataSets'][0]['series']
        
        # Créer une liste pour stocker les données
        records = []
        
        # Parcourir les observations
        for series_key, series_data in observations.items():
            # Décomposer la clé pour obtenir le pays
            keys = series_key.split(':')
            if len(keys) >= 5:  # Vérifier que nous avons assez d'éléments
                country = keys[4]
                
                # Parcourir les valeurs temporelles
                for time_idx, value in series_data['observations'].items():
                    time_period = data['structure']['dimensions']['observation'][0]['values'][int(time_idx)]['id']
                    records.append({
                        'date': pd.to_datetime(time_period),
                        'country': country,
                        'value': value[0]
                    })
        
        # Créer un DataFrame
        df = pd.DataFrame(records)
        
        # Pivoter le DataFrame
        df_pivot = df.pivot(index='date', columns='country', values='value')
        
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
                labels={"value": "Inflation (%)", "date": "Date"},
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
                ).round(1)
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
