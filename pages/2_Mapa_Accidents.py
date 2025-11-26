import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Mapa d'Accidents", layout="wide")
st.title("📍 Mapa d'Accidents a Barcelona")

# --- Funcions de Càrrega de Dades CORREGIDA ---
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

@st.cache_data
def carregar_csv_desde_carpeta():
    arxius = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    dfs = {}
    for arxiu in arxius:
        ruta_arxiu = os.path.join(DATA_FOLDER, arxiu)
        
        # Intent 1: Utilitzar la codificació universal (UTF-8)
        try:
            df = pd.read_csv(ruta_arxiu, sep=',', encoding='utf-8')
            dfs[arxiu] = df
            continue
        except UnicodeDecodeError:
            pass
            
        # Intent 2: Utilitzar la codificació per a Europa Occidental (Latin-1)
        try:
            df = pd.read_csv(ruta_arxiu, sep=',', encoding='latin-1')
            dfs[arxiu] = df
        except Exception as e:
            st.error(f"❌ Error carregant {arxiu} amb ambdues codificacions (UTF-8 i Latin-1).: {e}")
            
    return dfs

# Carregar i combinar totes les dades
dfs = carregar_csv_desde_carpeta()

if not dfs:
    st.info("👆 Primer, puja un o més arxius CSV a la pàgina 'Distribució Causes'.")
    st.stop() 

# Combinar totes les dades
df_total = pd.concat(dfs.values(), ignore_index=True)

# Assegurem que les columnes de coordenades tinguin el nom correcte
if 'Latitud' not in df_total.columns and 'Latitud_WGS84' in df_total.columns:
    df_total.rename(columns={'Latitud_WGS84': 'Latitud', 'Longitud_WGS84': 'Longitud'}, inplace=True)


# --- 1. APLICACIÓ DELS FILTRES A LA BARRA LATERAL ---

st.sidebar.header("Opcions de Filtre 🔍")

# 1.1 FILTRE PER ANY
df_filtrat = df_total.copy()
if 'Nk_Any' in df_total.columns:
    anys_disponibles = sorted(df_total['Nk_Any'].dropna().astype(str).unique())
    anys_seleccionats = st.sidebar.multiselect(
        "Selecciona l'Any:",
        options=anys_disponibles,
        default=anys_disponibles
    )
    df_filtrat = df_filtrat[df_filtrat['Nk_Any'].astype(str).isin(anys_seleccionats)]
else:
    st.sidebar.warning("Columna 'Nk_Any' no trobada per filtrar.")


# 1.2 FILTRE PER DISTRICTE
if 'Nom_districte' in df_filtrat.columns:
    districtes_disponibles = sorted(df_filtrat['Nom_districte'].dropna().unique())
    districtes_disponibles = [d for d in districtes_disponibles if d.strip() != '' and d.strip() != 'Desconegut']
    
    districtes_seleccionats = st.sidebar.multiselect(
        "Selecciona el Districte:",
        options=districtes_disponibles,
        default=districtes_disponibles
    )
    df_filtrat = df_filtrat[df_filtrat['Nom_districte'].isin(districtes_seleccionats)]
else:
    st.sidebar.warning("Columna 'Nom_districte' no trobada per filtrar.")


# --- 2. Creació del Mapa Interactiu amb Dades Filtrades ---

st.header("Visualització Interactiva dels Accidents")

columnes_coordenades = ['Latitud', 'Longitud']
columnes_present = all(col in df_filtrat.columns for col in columnes_coordenades)

if columnes_present and not df_filtrat.empty:
    df_mapa = df_filtrat.copy()
    
    try:
        # Assegurem que les coordenades són números flotants i netegem
        df_mapa['Latitud'] = pd.to_numeric(df_mapa['Latitud'], errors='coerce')
        df_mapa['Longitud'] = pd.to_numeric(df_mapa['Longitud'], errors='coerce')

        df_mapa = df_mapa[(df_mapa['Latitud'].notna()) & (df_mapa['Longitud'].notna())]
        df_mapa = df_mapa[(df_mapa['Latitud'] != 0) & (df_mapa['Longitud'] != 0)]
        
    except Exception as e:
        st.error(f"Error en processar coordenades: {e}")
        st.stop()
        
    # Mida de la mostra per millorar el rendiment
    if len(df_mapa) > 50000:
        df_mapa = df_mapa.sample(50000, random_state=42)
        st.info(f"Mostrant {len(df_mapa):,} accidents (mostra aleatòria de 50k punts).")
    else:
        st.info(f"Mostrant {len(df_mapa):,} accidents.")

    # Crear el mapa amb Plotly Express
    fig_mapa = px.scatter_mapbox(
        df_mapa, 
        lat="Latitud",           
        lon="Longitud",          
        hover_name="Nom_carrer", 
        color="Nom_districte",   
        zoom=10,                 
        center={"lat": 41.3851, "lon": 2.1734},
        mapbox_style="open-street-map", # Estil gratuït
        opacity=0.6,             
        title="Ubicació dels Accidents Filtrats"
    )
    
    # Actualitzar el layout (sense la clau de Mapbox)
    fig_mapa.update_layout(
        margin={"r":0,"t":50,"l":0,"b":0}
    )

    st.plotly_chart(fig_mapa, use_container_width=True)

elif df_filtrat.empty:
    st.warning("No hi ha dades per als filtres seleccionats.")

else:
    st.warning("Per generar el mapa, les dades combinades han de contenir les columnes 'Latitud' i 'Longitud'.")