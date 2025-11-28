import streamlit as st
import pandas as pd
import os
import plotly.express as px

# --- Configuració de la Pàgina ---
st.set_page_config(page_title="Distribució de Causes", layout="wide")

# 💅 Estil CSS MILLORAT
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


st.markdown('<h1 class="main-header">📊 Causes dels Accidents: Interacció i Distribució💖</h1>', unsafe_allow_html=True)
st.markdown("Selecciona l'any (o 'Tots els Anys') de manera independent per a cada mètrica per analitzar la distribució de causes, els factors del conductor i els patrons temporals.")

# --- Variables Globals i Funció de Càrrega CORREGIDA ---
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
            # En un entorn real, millor loguejar l'error
            st.error(f"❌ Error carregant {arxiu} amb ambdues codificacions (UTF-8 i Latin-1).")
            
    return dfs

# --- UI de Càrrega d'Arxius ---
# Recarregar les dades un cop s'han pujat arxius nous
dfs = carregar_csv_desde_carpeta()

uploaded_files = st.file_uploader("Afegeix nous CSV", type="csv", accept_multiple_files=True)
if uploaded_files:
    for arxiu in uploaded_files:
        # Guardar l'arxiu pujat localment
        with open(os.path.join(DATA_FOLDER, arxiu.name), "wb") as f:
            f.write(arxiu.getbuffer())
    st.success(f"S'han guardat {len(uploaded_files)} arxius CSV.")
    # Forçar la recàrrega de les dades amb la nova funció
    st.cache_data.clear()
    dfs = carregar_csv_desde_carpeta() 

# --- Funció de Filtratge General ---
def get_filtered_df(df_total, selected_year, column_name='Nk_Any'):
    """Retorna el DataFrame filtrat per l'any seleccionat o el total si es tria 'Tots els Anys'."""
    if selected_year == 'Tots els Anys':
        return df_total
    try:
        # Assegurar que el tipus de l'any coincideix
        return df_total[df_total[column_name].astype(str) == str(selected_year)].copy()
    except Exception:
        return pd.DataFrame()


# --- Generació dels Gràfics ---
if dfs:
    
    # Concatenar totes les dades per a anàlisis totals
    # Cal assegurar que la columna 'Nk_Any' existeix i és numèrica per a l'ordenació
    df_total = pd.concat(dfs.values(), ignore_index=True)
    
    # Intentem convertir l'any a enter, si falla, el tractem com a string
    try:
        if 'Nk_Any' in df_total.columns:
             # Convertir a Int64 (amb NA) per a neteja i després a string per consistència en el filtrat
             df_total['Nk_Any'] = pd.to_numeric(df_total['Nk_Any'], errors='coerce').astype('Int64').astype(str).str.replace('<NA>', 'NaN')
    except Exception:
        pass # Si falla la conversió inicial, mantenim els anys com a strings purs

    # Preparació d'anys per a desplegables
    if 'Nk_Any' in df_total.columns:
        # Netejar i ordenar valors únics
        anys_disponibles = sorted([a for a in df_total['Nk_Any'].dropna().unique().tolist() if a.isdigit()], key=int)
        anys_opcions = ['Tots els Anys'] + anys_disponibles
    else:
        st.warning("No s'ha trobat la columna 'Nk_Any' per a filtrar per anys.")
        anys_disponibles = []
        anys_opcions = ['Tots els Anys']

    # ----------------------------------------
    # Secció 2: Distribució de Causes (Per Any Seleccionat)
    # ----------------------------------------
    st.header("📌 Distribució de Causes Mediate")
    
    # RESUM DE LA SECCIÓ 2
    with st.expander("ℹ️ Què veig en aquest gràfic?"):
        st.markdown("""
            Aquest gràfic de pastís (Pie Chart) mostra el percentatge de cada **Causa Mediate** (la causa original o subjacent de l'accident) en el període seleccionat. 
            Permet identificar ràpidament quins són els factors primaris i sistèmics que contribueixen al major nombre d'accidents.
        """)

    if 'Descripcio_causa_mediata' in df_total.columns:
        
        # Selector d'any per a aquesta mètrica
        any_causa_mediate = st.selectbox(
            "Selecciona l'any per a la distribució de causes:",
            options=anys_opcions,
            key='any_causa_mediate',
            index=0 # Default a 'Tots els Anys'
        )
        
        df_seccio_2 = get_filtered_df(df_total, any_causa_mediate)
        
        if not df_seccio_2.empty:
            
            # 1. Gràfic de Causes (Combinat dels anys seleccionats)
            st.subheader(f"Distribució de Causes Mediate per a {any_causa_mediate}")
            
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
            
            # Forcem text de l'etiqueta fora del gràfic a color fosc
            fig_filtrat.update_traces(
                textposition='outside', 
                textinfo='percent+label', 
                marker=dict(line=dict(color='#333333', width=1)),
                textfont=dict(color='#000000') # <-- Font de les etiquetes exteriors a negre absolut
            )
            
            # Configuració del fons del gràfic a blanc i text a fosc
            fig_filtrat.update_layout(
                height=600, 
                font=dict(size=14, color='#000000'), # Títol i llegenda de la gràfica en NEGRE
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
    # Secció 3: Anàlisi de Causes Directes del Conductor (Per Any Seleccionat)
    # ----------------------------------------
    st.header("🔝 Top 10 Causes Directes del Conductor")
    
    # RESUM DE LA SECCIÓ 3
    with st.expander("ℹ️ Què veig en aquest gràfic?"):
        st.markdown("""
            Aquest gràfic de barres horitzontal mostra les 10 causes d'accident més freqüents directament atribuïdes al conductor. 
            És útil per destacar els comportaments de conducció o les faltes immediates que desencadenen un major nombre de sinistres.
        """)
    
    COL_CAUSA_DIRECTA = 'Descripcio_causa_conductor'

    if COL_CAUSA_DIRECTA in df_total.columns:
        
        # Selector d'any per a aquesta mètrica
        any_causa_conductor = st.selectbox(
            "Selecciona l'any per veure el Top 10 de causes del conductor:",
            options=anys_opcions,
            key='any_causa_conductor',
            index=0 # Default a 'Tots els Anys'
        )

        df_seccio_3 = get_filtered_df(df_total, any_causa_conductor)

        if not df_seccio_3.empty:
            # Filtrem valors nuls o no especificats com 'No consta'
            df_causes_directes = df_seccio_3[df_seccio_3[COL_CAUSA_DIRECTA].astype(str).str.strip() != 'No consta'].copy()
            
            if not df_causes_directes.empty:
                # 1. Agregació (Top 10)
                df_agg_causes = df_causes_directes[COL_CAUSA_DIRECTA].value_counts().nlargest(10).reset_index()
                df_agg_causes.columns = ['Causa Directa', 'Total_Accidents']

                # 2. Creació del Bar Chart
                fig_directes = px.bar(
                    df_agg_causes, 
                    x='Total_Accidents', 
                    y='Causa Directa',
                    orientation='h',
                    title=f"Les 10 Causes Més Comunes Atribuïdes al Conductor ({any_causa_conductor})",
                    color='Total_Accidents', 
                    text='Total_Accidents',
                    color_continuous_scale=px.colors.sequential.Plasma
                )
                
                # Configuració explícita per al text de les barres (Total d'accidents)
                fig_directes.update_traces(
                    texttemplate='%{text}',
                    textposition='outside',
                    marker_line_color='#333333',
                    marker_line_width=1,
                    textfont=dict(color='#000000') # <-- Forcem color NEGRE ABSOLUT pel text dels valors
                )
                
                # Configuració del fons del gràfic a blanc i text a fosc
                fig_directes.update_layout(
                    height=500, 
                    # Configuració Eix Y (Categoría)
                    yaxis={
                        'categoryorder':'total ascending', 
                        'title': '', 
                        'showgrid': True,                       
                        'gridcolor': '#cccccc',                 
                        'tickfont': {'color': '#000000'}, # NEGRE
                        'title_font': {'color': '#000000'} # NEGRE
                    }, 
                    # Configuració Eix X (Valor)
                    xaxis={
                        'title': 'Nombre d\'Accidents',
                        'showgrid': True,                       
                        'gridcolor': '#cccccc',                 
                        'tickfont': {'color': '#000000'}, # NEGRE
                        'title_font': {'color': '#000000'} # NEGRE
                    },
                    font=dict(color='#000000'), # Títol principal de la gràfica en NEGRE
                    coloraxis_showscale=False, # <-- Amaguem la barra de color
                    plot_bgcolor='white', 
                    paper_bgcolor='white'
                )
                
                st.plotly_chart(fig_directes, use_container_width=True)
            else:
                 st.info(f"No hi ha dades de causa directa (sense 'No consta') per a l'any {any_causa_conductor}.")
        else:
            st.info(f"No hi ha dades d'accidents per a l'any {any_causa_conductor}.")

    else:
        st.warning(f"El CSV combinat no té la columna '{COL_CAUSA_DIRECTA}' per a l'anàlisi de causes directes.")

    # ----------------------------------------
    # Secció 4: Anàlisi Temporal (Heatmap - Per Any Seleccionat)
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
        
        # Selector d'any per a aquesta mètrica
        any_heatmap = st.selectbox(
            "Selecciona l'any per veure el patró horari i diari:",
            options=anys_opcions,
            key='any_heatmap',
            index=0 # Default a 'Tots els Anys'
        )
        
        df_seccio_4 = get_filtered_df(df_total, any_heatmap)

        if not df_seccio_4.empty:
            
            # Ordre correcte dels dies de la setmana per al gràfic
            DIES_ORDRE = ['Dilluns', 'Dimarts', 'Dimecres', 'Dijous', 'Divendres', 'Dissabte', 'Diumenge']

            # 1. Agregació de dades
            # Cal assegurar-se que la columna 'Hora_dia' és numèrica per a l'eix X
            df_seccio_4[COL_HORA] = pd.to_numeric(df_seccio_4[COL_HORA], errors='coerce').fillna(-1).astype(int).astype(str)
            df_temporal = df_seccio_4.groupby([COL_DIA, COL_HORA]).size().reset_index(name='Total_Accidents')

            # Eliminar la fila on l'hora era NaN (convertida a -1 i ara a string '-1')
            df_temporal = df_temporal[df_temporal[COL_HORA] != '-1']


            # 2. Assegurar l'ordre dels dies
            df_temporal[COL_DIA] = pd.Categorical(df_temporal[COL_DIA], categories=DIES_ORDRE, ordered=True)
            df_temporal = df_temporal.sort_values(COL_DIA)
            
            # 3. Creació del Heatmap
            fig_temps = px.density_heatmap(
                df_temporal, 
                x=COL_HORA, 
                y=COL_DIA, 
                z='Total_Accidents',
                title=f"Accidents per Hora del Dia i Dia de la Setmana ({any_heatmap})",
                text_auto=True,
                category_orders={COL_DIA: DIES_ORDRE}, 
                color_continuous_scale=px.colors.sequential.Magenta # <-- MODIFICAT: Ús de la paleta 'Magenta'
            )
            
            # Configuració del fons del gràfic a blanc, text a fosc i línies dels eixos a fosc
            fig_temps.update_layout(
                height=600, 
                # Forcem el color dels valors (ticks) i el TÍTOL de l'eix X a fosc
                xaxis={
                    'title': 'Hora del Dia (0-23)', 
                    'tickmode': 'linear', 
                    'showgrid': False, 
                    'linecolor': '#333333',
                    'tickfont': {'color': '#000000'}, # NEGRE
                    'title_font': {'color': '#000000'} # NEGRE
                },
                # Forcem el color dels valors (ticks) i el TÍTOL de l'eix Y a fosc
                yaxis={
                    'title': 'Dia de la Setmana', 
                    'showgrid': False, 
                    'linecolor': '#333333',
                    'tickfont': {'color': '#000000'}, # NEGRE
                    'title_font': {'color': '#000000'} # NEGRE
                },
                # CORRECCIÓ FINAL DE LA LLEGIBILITAT DE LA BARRA DE COLOR
                coloraxis_colorbar=dict(
                    title=dict(
                        text="Total d'Accidents", 
                        font={'color': '#000000'} # <-- Forcem el títol a negre absolut
                    ),
                    tickfont={'color': '#000000'}   # <-- Forcem els números de l'escala de colors a negre absolut
                ),
                font=dict(color='#000000'), # Títol principal del gràfic i text general en NEGRE
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