import streamlit as st
import pandas as pd
import os
import plotly.express as px

# --- Configuració de la Pàgina ---
st.set_page_config(page_title="Accidents a Barcelona💖", layout="wide")

# --- Funcions de Càrrega (Copiades dels fitxers de pages/) ---
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

@st.cache_data
def carregar_csv_desde_carpeta():
    arxius = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    dfs = {}
    for arxiu in arxius:
        ruta_arxiu = os.path.join(DATA_FOLDER, arxiu)
        
        # Mètode de la Doble Codificació per als accents
        try:
            df = pd.read_csv(ruta_arxiu, sep=',', encoding='utf-8')
            dfs[arxiu] = df
            continue
        except UnicodeDecodeError:
            pass
            
        try:
            df = pd.read_csv(ruta_arxiu, sep=',', encoding='latin-1')
            dfs[arxiu] = df
        except Exception as e:
            st.error(f"❌ Error carregant {arxiu} amb ambdues codificacions.")
            
    return dfs

# Carregar dades
dfs = carregar_csv_desde_carpeta()
df_total = pd.concat(dfs.values(), ignore_index=True) if dfs else pd.DataFrame()


# --- Contingut de la Pàgina Principal ---

st.title("🚦 Dashboard d'Accidents de Trànsit a Barcelona")
st.markdown("---")

if df_total.empty:
    st.warning("No s'ha pogut carregar cap dada. Puja fitxers a la pàgina '1 Distribució Causes'.")
else:
    # 1. Càlcul de Mètriques Clau (KPIs)
    total_accidents = len(df_total)
    anys_coberts = df_total['Nk_Any'].nunique() if 'Nk_Any' in df_total.columns else 0
    anys_min_max = f"{df_total['Nk_Any'].min()} - {df_total['Nk_Any'].max()}" if anys_coberts > 0 else "N/A"
    
    # 2. Creació de Columnes per als KPIs
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Total d'Accidents Registrats", value=f"{total_accidents:,}", delta="Base de Dades Total")
    
    with col2:
        st.metric(label="Anys Coberts", value=anys_coberts, delta=anys_min_max)
    
    with col3:
        # Calcular la causa més freqüent
        causa_mes_freq = "No Disponible"
        if 'Descripcio_causa_mediata' in df_total.columns:
            causa_mes_freq = df_total['Descripcio_causa_mediata'].mode()[0]
            # Si hi ha valors nuls o estranys, els ignorem
            if causa_mes_freq.strip() == '':
                causa_mes_freq = df_total['Descripcio_causa_mediata'].value_counts().index[1] if len(df_total['Descripcio_causa_mediata'].value_counts()) > 1 else "Altres"
                
        st.metric(label="Causa Més Freqüent", value=causa_mes_freq, delta="Revisa la secció 'Causes'")

    st.markdown("---")

    # 3. Resum Gràfic: Accidents per Districte
    st.header("Resum Ràpid: Distribució Geogràfica")
    
    if 'Nom_districte' in df_total.columns:
        df_districte = df_total['Nom_districte'].value_counts().reset_index()
        df_districte.columns = ['Districte', 'Total_accidents']
        df_districte = df_districte[df_districte['Districte'].str.strip() != '']
        
        # Gràfic de barres senzill
        fig_districte = px.bar(
            df_districte.head(10), # Només els 10 primers districtes
            x='Districte',
            y='Total_accidents',
            title='Top 10 Districtes amb Més Accidents',
            color_discrete_sequence=['#4682B4']
        )
        fig_districte.update_layout(xaxis={'categoryorder':'total descending'}, height=400)
        st.plotly_chart(fig_districte, use_container_width=True)
        

    st.markdown("---")

    # 4. Guia de Navegació
    st.header("Explora l'Anàlisi Completa")
    st.markdown("""
    Utilitza la barra lateral per aprofundir en les estadístiques:

    * **1 Distribució Causes:** Analitza les proporcions dels tipus de causa.
    * **2 Mapa Accidents:** Visualitza els punts calents a Barcelona amb filtres per any i districte.
    * **3 Analista de Dades:** Fes preguntes directes per obtenir estadístiques concretes mitjançant el nostre chatbot.
    """)