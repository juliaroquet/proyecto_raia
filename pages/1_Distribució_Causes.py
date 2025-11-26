import streamlit as st
import pandas as pd
import os
import plotly.express as px

# --- Configuració de la Pàgina ---
st.set_page_config(page_title="Distribució de Causes", layout="wide")
st.title("📊 Causes dels Accidents: Pie Charts💖")
st.markdown("Aquesta pàgina mostra la distribució percentual dels accidents segons la seva causa mediata.")

# --- Variables Globals i Funció de Càrrega CORREGIDA ---
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
            continue # Si funciona, saltem al següent fitxer
        except UnicodeDecodeError:
            pass # Continuem amb el segon intent si falla
            
        # Intent 2: Utilitzar la codificació per a Europa Occidental (Latin-1)
        try:
            df = pd.read_csv(ruta_arxiu, sep=',', encoding='latin-1')
            dfs[arxiu] = df
        except Exception as e:
            st.error(f"❌ Error carregant {arxiu} amb ambdues codificacions (UTF-8 i Latin-1).: {e}")
            
    return dfs

# --- UI de Càrrega d'Arxius ---
# Recarregar les dades un cop s'han pujat arxius nous
dfs = carregar_csv_desde_carpeta()

uploaded_files = st.file_uploader("Afegeix nous CSV", type="csv", accept_multiple_files=True)
if uploaded_files:
    for arxiu in uploaded_files:
        with open(os.path.join(DATA_FOLDER, arxiu.name), "wb") as f:
            f.write(arxiu.getbuffer())
    st.success(f"S'han guardat {len(uploaded_files)} arxius CSV.")
    # Recarregar les dades un cop s'han pujat arxius nous
    dfs = carregar_csv_desde_carpeta() 

# --- Generació dels Gràfics ---
if dfs:
    # ----------------------------------------
    # Secció 1: Gràfics individuals (en columnes)
    # ----------------------------------------
    st.header("📌 Distribució Individual per Any")
    
    num_cols = 2
    cols = st.columns(num_cols)
    
    for i, (nom_csv, df) in enumerate(dfs.items()):
        any_file = nom_csv.split('_')[0] if nom_csv[0].isdigit() else nom_csv.replace('.csv', '')
        
        with cols[i % num_cols]:
            if 'Descripcio_causa_mediata' in df.columns:
                # 1. Agregació de dades
                df_agg = df['Descripcio_causa_mediata'].value_counts().reset_index()
                df_agg.columns = ['Causa', 'Total_accidents']

                # 2. Creació del Pie Chart
                fig = px.pie(
                    df_agg, 
                    names='Causa', 
                    values='Total_accidents',
                    title=f"Causes: {any_file}",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                
                # Millora de la visualització
                fig.update_traces(textposition='inside', textinfo='percent')
                fig.update_layout(showlegend=False)
                
                # 3. Mostrar el Gràfic
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"El CSV {nom_csv} no té la columna 'Descripcio_causa_mediata'.")

    st.markdown("---")
    
    # ----------------------------------------
    # Secció 2: Gràfic Combinat de Tots els Anys
    # ----------------------------------------
    st.header("📌 Distribució Combinada de Totes les Dades")
    df_total = pd.concat(dfs.values(), ignore_index=True)
    
    if 'Descripcio_causa_mediata' in df_total.columns:
        df_agg_total = df_total['Descripcio_causa_mediata'].value_counts().reset_index()
        df_agg_total.columns = ['Causa', 'Total_accidents']

        fig_total = px.pie(
            df_agg_total, 
            names='Causa', 
            values='Total_accidents',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        # Personalització per al gràfic principal
        fig_total.update_traces(textposition='outside', textinfo='percent+label')
        fig_total.update_layout(title="Total d'Accidents per Causa", font=dict(size=14))
        
        st.plotly_chart(fig_total, use_container_width=True)
    else:
        st.warning("El CSV combinat no té la columna 'Descripcio_causa_mediata'.")
else:
    st.info("👆 Puja un o més arxius CSV per començar a veure els gràfics.")