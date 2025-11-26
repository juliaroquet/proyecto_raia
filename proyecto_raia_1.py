import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Estadístiques d'Accidents", layout="wide")
st.title("📊 Accidents a Barcelona: distribució per causa")

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# Funció per carregar CSVs
@st.cache_data
def carregar_csv_desde_carpeta():
    arxius = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    dfs = {}
    for arxiu in arxius:
        dfs[arxiu] = pd.read_csv(os.path.join(DATA_FOLDER, arxiu))
    return dfs

dfs = carregar_csv_desde_carpeta()

# File uploader
uploaded_files = st.file_uploader("Afegeix nous CSV", type="csv", accept_multiple_files=True)
if uploaded_files:
    for arxiu in uploaded_files:
        with open(os.path.join(DATA_FOLDER, arxiu.name), "wb") as f:
            f.write(arxiu.getbuffer())
    st.success(f"S'han guardat {len(uploaded_files)} arxius CSV.")
    dfs = carregar_csv_desde_carpeta()

if dfs:
    # Afegir opció per veure tots els CSV combinats
    opcions = ["Tots els CSV"] + list(dfs.keys())
    arxiu_sel = st.selectbox("Selecciona el CSV o 'Tots els CSV'", opcions)

    # Filtrar dataframe segons la selecció
    if arxiu_sel == "Tots els CSV":
        df_total = pd.concat(dfs.values(), ignore_index=True)
    else:
        df_total = dfs[arxiu_sel]

    # Comprovar que hi ha la columna necessària
    if 'Descripcio_causa_mediata' in df_total.columns:
        df_agg = df_total['Descripcio_causa_mediata'].value_counts().reset_index()
        df_agg.columns = ['Causa', 'Total_accidents']

        st.subheader(f"Distribució d'accidents per causa ({arxiu_sel})")
        fig = px.pie(df_agg, names='Causa', values='Total_accidents',
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("El CSV ha de tenir la columna 'Descripcio_causa_mediata'.")
else:
    st.info("👆 Puja un o més arxius CSV per començar.")
