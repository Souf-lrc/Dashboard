import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Inflation en Europe",
    page_icon="📈",
    layout="wide"
)

# Titre
st.title("🌍 Dashboard Inflation en Europe")

@st.cache_data(ttl=3600)  # Cache les données pendant 1 heure
def get_inflation_data():
    # URL et paramètres
    url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr"
    params = {
        'format': 'JSON',
        'lang': 'fr',
        'freq': 'M',
        'unit': 'RCH_A',
        'coicop': 'CP00'
    }
    
    try:
        # Récupération des données
        response = requests.get(url, params=params)
        data = response.json()

        # Création des dictionnaires inversés
        time_indices = {v: k for k, v in data['dimension']['time']['category']['index'].items()}
        geo_indices = {v: k for k, v in data['dimension']['geo']['category']['index'].items()}

        # Extraire les valeurs
        values = []
        for key, value in data['value'].items():
            position = int(key)
            n_times = len(time_indices)
            time_idx = position % n_times
            geo_idx = position // n_times
            
            time = time_indices.get(time_idx)
            geo = geo_indices.get(geo_idx)
            
            if geo in ['EU27_2020', 'FR', 'DE', 'US'] and time is not None:
                values.append({
                    'date': pd.to_datetime(time),
                    'pays': geo,
                    'inflation': value
                })

        # Créer un DataFrame
        df = pd.DataFrame(values)
        return df
        
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {str(e)}")
        return None

# Chargement des données
df = get_inflation_data()

if df is not None:
    # Création des colonnes pour le layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sélection de la période
        df = df.sort_values('date')
        latest_date = df['date'].max()
        earliest_date = df['date'].min()
        
        periode = st.slider(
            "Sélectionnez la période",
            min_value=earliest_date,
            max_value=latest_date,
            value=(latest_date - pd.DateOffset(months=12), latest_date)
        )
        
        # Filtrer les données selon la période
        mask = (df['date'] >= periode[0]) & (df['date'] <= periode[1])
        df_filtered = df[mask]
        
        # Pivoter pour avoir les pays en colonnes
        df_pivot = df_filtered.pivot(index='date', columns='pays', values='inflation')
        
        # Créer le graphique
        fig = px.line(
            df_pivot,
            title="Évolution de l'inflation",
            labels={'date': 'Date', 
                   'value': "Taux d'inflation (%)",
                   'pays': 'Pays'},
            height=500
        )
        
        fig.update_layout(
            legend_title_text='Pays',
            xaxis_title="Date",
            yaxis_title="Inflation (%)",
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            hovermode='x unified'
        )
        
        # Afficher le graphique
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Tableau des dernières valeurs
        st.subheader("Dernières valeurs")
        latest_data = df_pivot.iloc[-1].sort_values(ascending=False)
        st.dataframe(
            latest_data.reset_index().rename(
                columns={'index': 'Pays', latest_data.name: 'Inflation (%)'}
            ).round(1)
        )
        
        # Statistiques
        st.subheader("Statistiques")
        stats = df_pivot.describe().round(1)
        st.dataframe(stats)

# Informations sur les données
st.markdown("---")
st.caption("""
    Source : Eurostat - HICP (Harmonised Index of Consumer Prices)
    Mise à jour : Mensuelle
    Note : 
    - EU27_2020 = Union Européenne (27 pays)
    - FR = France
    - DE = Allemagne
    - US = États-Unis
""")
