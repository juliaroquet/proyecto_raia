import streamlit as st
import pandas as pd
import os
import plotly.express as px

# --- Configuració de la Pàgina ---
st.set_page_config(page_title="Distribució de Causes", layout="wide")

# 💅 Estil CSS MILLORAT (Es manté el mateix estil)
st.markdown("""
    <style>
    /* Estil consistent amb el Dashboard: Nou fons no blanc (blau clar suau) */
    [data-testid="stAppViewContainer"] { 
        background-color: #ebf5fb; 
        color: #333333; /* Color de text general per defecte */
    }
    .main-header { 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        text-align: center; 
        color: #1A5276; 
        font-size: 3em; 
        padding: 15px 0 5px; 
        border-bottom: 2px solid #4682B4; 
        margin-bottom: 30px; 
    }
    .stMarkdown h2 { 
        color: #1A5276; 
        padding-left: 0; 
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .stAlert { border-left: 5px solid #FF9900; color: #333333; }
    .stMarkdown { color: #333333; }

    /* Forcem color de text fosc per a labels i inputs de Streamlit */
    label, [data-testid="stFileUploader"] {
        color: #333333 !important;
    }

    /* ********** CORRECCIÓ DE LLEGIBILITAT DEL SELECTBOX ********** */
    /* Forcem fons blanc i text fosc per al desplegable d'anys */
    div[data-testid="stSelectbox"] div[data-testid="stSingleSelectbox"] {
        background-color: white !important; /* Fons blanc per la caixa */
        border: 1px solid #ccc;
    }
    div[data-testid="stSelectbox"] div[data-testid="stSingleSelectbox"] div {
        color: #333333 !important; /* Text fosc dins de la caixa */
    }
    div[data-testid="stSelectbox"] {
        margin-bottom: 20px;
    }
    /* ************************************************************ */
    
    /* Estil per als expanders de resum */
    .summary-expander {
        border-radius: 8px;
        background-color: #f0f7f9; /* Un fons lleugerament diferent */
        padding: 10px;
        margin-top: 10px;
        margin-bottom: 20px;
        border: 1px solid #d0e8f0;
    }
    </style>
""", unsafe_allow_html=True)


st.markdown('<h1 class="main-header">📊 Causes dels Accidents: Interacció i Distribució</h1>', unsafe_allow_html=True)
st.markdown("Selecciona l'any (o 'Tots els Anys') de manera independent per a cada mètrica per analitzar la distribució de causes, els punts calents i els patrons temporals.")

# --- Variables Globals i Funció de Càrrega CORREGIDA (Es manté) ---
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

@st.cache_data
def carregar_csv_desde_carpeta():
    """Carrega tots els CSV amb doble codificació (UTF-8 i Latin-1) des de la carpeta 'data'."""
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
            df = df.astype(str) # Forcem a string per evitar errors de tipus amb dades brutes
            dfs[arxiu] = df
        except Exception as e:
            st.error(f"❌ Error carregant {arxiu} amb ambdues codificacions (UTF-8 i Latin-1).")
            
    return dfs

# --- UI de Càrrega d'Arxius i Preparació de Dades (Es manté) ---
dfs = carregar_csv_desde_carpeta()

uploaded_files = st.file_uploader("Afegeix nous CSV", type="csv", accept_multiple_files=True)
if uploaded_files:
    for arxiu in uploaded_files:
        with open(os.path.join(DATA_FOLDER, arxiu.name), "wb") as f:
            f.write(arxiu.getbuffer())
    st.success(f"S'han guardat {len(uploaded_files)} arxius CSV.")
    st.cache_data.clear()
    dfs = carregar_csv_desde_carpeta() 

# --- Funció de Filtratge General (Es manté) ---
def get_filtered_df(df_total, selected_year, column_name='Nk_Any'):
    """Retorna el DataFrame filtrat per l'any seleccionat o el total si es tria 'Tots els Anys'."""
    if selected_year == 'Tots els Anys':
        return df_total
    try:
        return df_total[df_total[column_name].astype(str) == str(selected_year)].copy()
    except Exception:
        return pd.DataFrame()


# --- Generació dels Gràfics ---
if dfs:
    
    df_total = pd.concat(dfs.values(), ignore_index=True)
    
    # Conversió d'anys per a desplegables (es manté)
    try:
        if 'Nk_Any' in df_total.columns:
              df_total['Nk_Any'] = pd.to_numeric(df_total['Nk_Any'], errors='coerce').astype('Int64').astype(str).str.replace('<NA>', 'NaN')
    except Exception:
        pass 

    if 'Nk_Any' in df_total.columns:
        anys_disponibles = sorted([a for a in df_total['Nk_Any'].dropna().unique().tolist() if a.isdigit()], key=int)
        anys_opcions = ['Tots els Anys'] + anys_disponibles
    else:
        st.warning("No s'ha trobat la columna 'Nk_Any' per a filtrar per anys.")
        anys_disponibles = []
        anys_opcions = ['Tots els Anys']

    # ----------------------------------------
    # Secció 2: Distribució de Causes (Es manté)
    # ----------------------------------------
    st.header("Distribució de Causes")
    
    # RESUM DE LA SECCIÓ 2
    with st.expander("ℹ️ Què veig en aquest gràfic?"):
        st.markdown("""
            Aquest gràfic de pastís (Pie Chart) mostra el percentatge de cada **Causa** (la causa original o subjacent de l'accident) en el període seleccionat. 
            Permet identificar ràpidament quins són els factors primaris i sistèmics que contribueixen al major nombre d'accidents.
        """)

    if 'Descripcio_causa_mediata' in df_total.columns:
        
        any_causa_mediate = st.selectbox(
            "Selecciona l'any per a la distribució de causes:",
            options=anys_opcions,
            key='any_causa_mediate_s2',
            index=0 
        )
        
        df_seccio_2 = get_filtered_df(df_total, any_causa_mediate)
        
        if not df_seccio_2.empty:
            
            st.subheader(f"Distribució de Causes per a {any_causa_mediate}")
            
            df_agg_filtrat = df_seccio_2['Descripcio_causa_mediata'].value_counts().reset_index()
            df_agg_filtrat.columns = ['Causa', 'Total_accidents']

            fig_filtrat = px.pie(
                df_agg_filtrat, 
                names='Causa', 
                values='Total_accidents',
                title=f"Distribució de Causes Mediate ({any_causa_mediate})",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            # Configuració del gràfic de pastís (es manté)
            fig_filtrat.update_traces(
                textposition='outside', 
                textinfo='percent+label', 
                marker=dict(line=dict(color='#333333', width=1)),
                textfont=dict(color='#000000') 
            )
            
            fig_filtrat.update_layout(
                height=600, 
                font=dict(size=14, color='#000000'), 
                title_x=0.5,
                plot_bgcolor='white', 
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig_filtrat, use_container_width=True)
        else:
            st.info(f"No hi ha dades de causa mediata per a l'any {any_causa_mediate}.")

    else:
        st.warning("El CSV combinat no té la columna 'Descripcio_causa_mediata' necessària per a aquesta anàlisi.")


    # ----------------------------------------
    # Secció 3 (NOVA): Punts Calents de Sinistralitat (Top 10 Carrers)
    # ----------------------------------------
    st.header("🔥 Top 10 Punts Calents de Sinistralitat (Carrers)")
    
    # RESUM DE LA SECCIÓ 3
    with st.expander("ℹ️ Què veig en aquest gràfic?"):
        st.markdown("""
            Aquesta és la mètrica més important per a l'acció. Mostra els **10 carrers o vies amb major concentració d'accidents** en el període seleccionat. 
            Aquests són els punts calents on cal prioritzar les inversions en seguretat viària i campanyes de conscienciació.
        """)
    
    COL_CARRER = 'Nom_carrer'

    if COL_CARRER in df_total.columns:
        
        # Selector d'any per a aquesta mètrica
        any_carrer = st.selectbox(
            "Selecciona l'any per veure el Top 10 de carrers:",
            options=anys_opcions,
            key='any_carrer',
            index=0 # Default a 'Tots els Anys'
        )

        df_seccio_3 = get_filtered_df(df_total, any_carrer)
        
        # Filtrem valors nuls o no especificats
        EXCLUSIONS_CARRER = ['Desconegut', 'NULL', 'No consta', '', 'N/A', 'NO IDENTIFICADA']
        df_carrers = df_seccio_3[
            ~df_seccio_3[COL_CARRER].astype(str).str.strip().isin(EXCLUSIONS_CARRER)
        ].copy()


        if not df_carrers.empty:
            
            # 1. Agregació (Top 10)
            df_agg_carrers = df_carrers[COL_CARRER].value_counts().nlargest(10).reset_index()
            df_agg_carrers.columns = ['Carrer', 'Total_Accidents']

            # 2. Creació del Bar Chart (Horitzontal)
            fig_carrers = px.bar(
                df_agg_carrers, 
                x='Total_Accidents', 
                y='Carrer',
                orientation='h',
                title=f"Top 10 Carrers amb Més Accidents ({any_carrer})",
                color='Total_Accidents', 
                text='Total_Accidents',
                color_continuous_scale=px.colors.sequential.Sunset # Escala que va de clar (baix) a fosc/vermell (alt)
            )
            
            fig_carrers.update_traces(
                texttemplate='%{text}',
                textposition='outside',
                marker_line_color='#333333',
                marker_line_width=1,
                textfont=dict(color='#000000') 
            )
            
            fig_carrers.update_layout(
                height=500, 
                yaxis={'categoryorder':'total ascending', 'title': '', 'tickfont': {'color': '#000000'}, 'title_font': {'color': '#000000'}}, 
                xaxis={'title': 'Nombre d\'Accidents', 'showgrid': True, 'gridcolor': '#cccccc', 'tickfont': {'color': '#000000'}, 'title_font': {'color': '#000000'}},
                font=dict(color='#000000'), 
                coloraxis_showscale=False, 
                plot_bgcolor='white', 
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig_carrers, use_container_width=True)
        else:
            st.info(f"No hi ha dades de carrers vàlides per a l'anàlisi per a l'any {any_carrer}.")

    else:
        st.warning(f"El CSV combinat no té la columna '{COL_CARRER}' per a l'anàlisi de punts calents.")
    
    # ----------------------------------------
    # Secció 4: Anàlisi Temporal (Heatmap - Es manté)
    # ----------------------------------------
    st.header("⏳ Distribució Temporal d'Accidents (Hora i Dia)")
    
    # RESUM DE LA SECCIÓ 4
    with st.expander("ℹ️ Què veig en aquest gràfic?"):
        st.markdown("""
            Aquest mapa de calor (Heatmap) mostra la concentració d'accidents en funció de l'**Hora del Dia** (eix X, 0 a 23) i el **Dia de la Setmana** (eix Y). 
            Els colors més intensos (**més propers al magenta/rosa intens**) indiquen els moments de major sinistralitat, permetent identificar els patrons horaris i diaris de risc màxim.
        """)
    
    COL_DIA = 'Descripcio_dia_setmana'
    COL_HORA = 'Hora_dia'

    if COL_DIA in df_total.columns and COL_HORA in df_total.columns:
        
        any_heatmap = st.selectbox(
            "Selecciona l'any per veure el patró horari i diari:",
            options=anys_opcions,
            key='any_heatmap',
            index=0 # Default a 'Tots els Anys'
        )
        
        df_seccio_4 = get_filtered_df(df_total, any_heatmap)

        if not df_seccio_4.empty:
            
            DIES_ORDRE = ['Dilluns', 'Dimarts', 'Dimecres', 'Dijous', 'Divendres', 'Dissabte', 'Diumenge']

            df_seccio_4[COL_HORA] = pd.to_numeric(df_seccio_4[COL_HORA], errors='coerce').fillna(-1).astype(int).astype(str)
            df_temporal = df_seccio_4.groupby([COL_DIA, COL_HORA]).size().reset_index(name='Total_Accidents')
            df_temporal = df_temporal[df_temporal[COL_HORA] != '-1']

            df_temporal[COL_DIA] = pd.Categorical(df_temporal[COL_DIA], categories=DIES_ORDRE, ordered=True)
            df_temporal = df_temporal.sort_values(COL_DIA)
            
            fig_temps = px.density_heatmap(
                df_temporal, 
                x=COL_HORA, 
                y=COL_DIA, 
                z='Total_Accidents',
                title=f"Accidents per Hora del Dia i Dia de la Setmana ({any_heatmap})",
                text_auto=True,
                category_orders={COL_DIA: DIES_ORDRE}, 
                color_continuous_scale=px.colors.sequential.Magenta 
            )
            
            fig_temps.update_layout(
                height=600, 
                xaxis={'title': 'Hora del Dia (0-23)', 'tickmode': 'linear', 'showgrid': False, 'linecolor': '#333333', 'tickfont': {'color': '#000000'}, 'title_font': {'color': '#000000'}},
                yaxis={'title': 'Dia de la Setmana', 'showgrid': False, 'linecolor': '#333333', 'tickfont': {'color': '#000000'}, 'title_font': {'color': '#000000'}},
                coloraxis_colorbar=dict(
                    title=dict(
                        text="Total d'Accidents", 
                        font={'color': '#000000'}
                    ),
                    tickfont={'color': '#000000'}
                ),
                font=dict(color='#000000'),
                plot_bgcolor='white', 
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig_temps, use_container_width=True)
        else:
            st.info(f"No hi ha dades temporals per a l'any {any_heatmap}.")
            
    else:
        st.warning(f"El CSV combinat no té les columnes '{COL_DIA}' o '{COL_HORA}' per a l'anàlisi temporal.")
    
else:
    st.info("👆 Puja un o més arxius CSV a la secció superior per començar a veure els gràfics.")