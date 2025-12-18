import streamlit as st
import pandas as pd
import os
import plotly.express as px

# --- 1. CONFIGURACIÓ DE LA PÀGINA (Sempre la primera línia) ---
st.set_page_config(page_title="Accidents a Barcelona", layout="wide")

# 2. IMPLEMENTACIÓ CRITERI: CONTROL D'USUARI
if "usuari_nom" not in st.session_state:

    st.markdown("""
        <style>
        /* Fons igual que el dashboard */
        [data-testid="stAppViewContainer"] {
            background-color: #f5f7fa;
        }
        /* Eliminem la caixa blanca */
        .login-box {
            text-align: center;
            padding: 40px;
            background-color: transparent;
            border-radius: 0;
            box-shadow: none;
            margin-top: 60px;
        }
        /* Títol login */
        .login-header {
            color: #1A5276 !important;
            font-family: 'Verdana', sans-serif;
            font-weight: 700;
        }
        /* Label del text input */
        label {
            color: #333333 !important;
            font-weight: 500;
        }
        /* Text que escriu l'usuari */
        input {
            color: #f5f7fa !important;
        }
        </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<h1 class="login-header">🔐 Accés</h1>', unsafe_allow_html=True)
        nom = st.text_input("Introdueix el teu nom per accedir al Dashboard:")
        if st.button("Iniciar Sessió"):
            if nom:
                st.session_state.usuari_nom = nom
                st.rerun()
            else:
                st.error("Si us plau, introdueix un nom.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 💅 Estil CSS Personalitzat (Estètica Professional amb Contrast millorat)

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #f5f7fa;
        color: #1A5276;
    }

    .main-header {
        font-family: 'Verdana', Tahoma, Geneva, Segoe UI, sans-serif;
        text-align: center;
        color: #1A5276;
        font-size: 3em;
        padding-top: 15px;
        padding-bottom: 5px;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 30px;
    }



    [data-testid="stMetric"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #4682B4;
        overflow: hidden;
    }

   
    [data-testid="stMetricLabel"],
    [data-testid="stMetricDelta"],
    [data-testid="stMetricValue"] {
        color: #333333 !important;
    }
    .stMarkdown h2 {
        color: #1A5276;
        border-left: 5px solid #4682B4;
        padding-left: 10px;
    }

    .stAlert {
        border-left: 5px solid #FF9900;
        color: #333333;
    }

       .stMarkdown {
        color: #333333;
    }

    .sidebar .sidebar-content {
        background-color: #e0e6f0;
    }

    .summary-expander {
        margin-bottom: 20px;
        padding: 10px;
        background-color: #e6eef5;
        border-radius: 5px;
        border-left: 3px solid #1A5276;
    }

    </style>
""", unsafe_allow_html=True)

# --- Funcions de Càrrega ---
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)
@st.cache_data
def carregar_csv_desde_carpeta():
    arxius = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    dfs = {}
    for arxiu in arxius:
        ruta_arxiu = os.path.join(DATA_FOLDER, arxiu)
        try:
            df = pd.read_csv(ruta_arxiu, sep=',', encoding='utf-8')
            dfs[arxiu] = df
            continue
        except UnicodeDecodeError:
            pass
        try:
            df = pd.read_csv(ruta_arxiu, sep=',', encoding='latin-1')
            dfs[arxiu] = df
        except Exception:
            pass
    return dfs

dfs = carregar_csv_desde_carpeta()
df_total = pd.concat(dfs.values(), ignore_index=True) if dfs else pd.DataFrame()
# --- FILTRES GLOBALS ---

st.sidebar.title(f"👤 {st.session_state.usuari_nom}")

if st.sidebar.button("Tancar Sessió"):

    del st.session_state.usuari_nom

    st.rerun()

anys_seleccionats = df_total['Nk_Any'].unique().tolist() if not df_total.empty else []

df_filtrat = df_total.copy()



if 'Nk_Any' in df_total.columns and not df_total.empty:

    st.sidebar.header("Opcions")

    with st.sidebar.expander("Filtres:", expanded=True):

        anys_disponibles = sorted(df_total['Nk_Any'].unique().tolist())

        anys_seleccionats = st.multiselect(

            "Selecciona l'Any(s) (Afecta Mètriques i Gràfics):",

            options=anys_disponibles,

            default=anys_disponibles

        )



    if anys_seleccionats:

        df_filtrat = df_total[df_total['Nk_Any'].isin(anys_seleccionats)]

    else:

        df_filtrat = df_total.iloc[0:0]

        anys_seleccionats = []



# --- Contingut de la Pàgina Principal ---



# Títol personalitzat amb el nom de l'analista

st.markdown(f'<h1 class="main-header"> Dashboard d\'Accidents | {st.session_state.usuari_nom} </h1>', unsafe_allow_html=True)
if df_total.empty:
    st.warning("No s'ha pogut carregar cap dada. Puja fitxers a la pàgina '1 Distribució Causes'.")
else:
    st.markdown("""
        Aquesta aplicació interactiva us permet **analitzar i visualitzar** les dades d'accidents de trànsit registrats a la ciutat de Barcelona.
    """)   
    st.markdown("---")

   

    # 1. Càlcul de Mètriques Clau (KPIs)

    total_accidents = len(df_filtrat)
    anys_coberts = df_filtrat['Nk_Any'].nunique() if 'Nk_Any' in df_filtrat.columns else 0
    anys_min_max = f"{df_filtrat['Nk_Any'].min()} - {df_filtrat['Nk_Any'].max()}" if anys_coberts > 0 else "N/A"

    # 2. Creació de 3 Columnes per als KPIs
    col1, col2, col3 = st.columns([3, 2.5, 3])

    with col1:
       st.markdown(f"""
            <div style="font-size: 14px; color: gray; margin-bottom: 5px;">
                Total d'Accidents (Filtre Actual)
            </div>
            <div style="font-size: 24px; font-weight: bold;">
                {total_accidents:,}
            </div>
        """, unsafe_allow_html=True)
       
    with col2:
        # Aquí simulem el "delta" posant el rang d'anys en petit i color verd o gris a sota
        st.markdown(f"""
            <div style="font-size: 14px; color: gray; margin-bottom: 5px;">
                Anys en l'Anàlisi
            </div>
            <div style="font-size: 24px; font-weight: bold;">
                {anys_coberts}
            </div>
            <div style="font-size: 12px; color: #2E8B57; margin-top: -2px;">
                📅 {anys_min_max}
            </div>
        """, unsafe_allow_html=True)

    with col3:
        # 1. Definimos la variable inicial para evitar el NameError
        text_causa = "No Disponible"

        # 2. Calculamos el dato si existe la columna
        if 'Descripcio_causa_mediata' in df_filtrat.columns:
            data_filtrada = df_filtrat[df_filtrat['Descripcio_causa_mediata'].astype(str).str.strip() != '']
            if not data_filtrada.empty:
                # Obtenemos solo la causa número 1 (.idxmax devuelve el índice del valor máximo)
                text_causa = data_filtrada['Descripcio_causa_mediata'].value_counts().idxmax()

        # 3. Mostramos el resultado con HTML personalizado para que NO se corte el texto
        st.markdown(f"""
            <div style="font-size: 14px; color: gray; margin-bottom: 5px;">
                Causa Més Freqüent
            </div>
            <div style="font-size: 16px; font-weight: bold; line-height: 1.4;">
                {text_causa}
            </div>

        """, unsafe_allow_html=True)

    st.markdown("---")

   

    # 3. Gràfic de Tendència Temporal

    if 'Nk_Any' in df_total.columns:

        st.header("Anàlisi de Tendència Temporal")

        with st.expander("ℹ️ Clic per a un Resum d'Interpretació", expanded=False):

            st.markdown("Aquest gràfic mostra el total d'accidents anuals per identificar patrons a llarg termini.")

       

        df_anual = df_total.groupby('Nk_Any').size().reset_index(name='Total_Accidents')

        fig_trend = px.line(

            df_anual,

            x='Nk_Any',

            y='Total_Accidents',

            title="Evolució Anual d'Accidents",

            markers=True,

            color_discrete_sequence=px.colors.qualitative.Pastel,

            )

       

        fig_trend.update_layout(

            # Título personalizado y centrado

            title={

                'text': "Evolució Anual d'Accidents",

                'y': 0.95,

                'x': 0.5,

                'xanchor': 'center',

                'yanchor': 'top',

                'font': dict(size=20, color='black')

            },

            # Márgenes

            margin=dict(t=50, b=40, l=40, r=40),

           

            # Fondos transparentes y texto negro

            plot_bgcolor='rgba(0,0,0,0)',

            paper_bgcolor='rgba(0,0,0,0)',

            showlegend=False,

            font_color="black"

        )



        fig_trend.update_xaxes(

            title=None,

            type='category',         # <--- IMPORTANTE: Trata los años como categorías (sin comas ni decimales)

            showgrid=False,          # Generalmente en líneas temporales queda más limpio sin grid vertical

            showline=True,

            linecolor='black',

            tickfont=dict(color='black')

        )

        fig_trend.update_yaxes(

            title="Total Accidents",

            showgrid=True,

            gridcolor='rgba(0,0,0,0.1)', # Cuadrícula sutil

            zeroline=True,

            zerolinecolor='black',

            tickfont=dict(color='black'),

            title_font=dict(color='black')

        )

        fig_trend.update_traces(

            line=dict(width=3),      # Línea un poco más gruesa

            marker=dict(size=8, line=dict(width=1, color='black')) # Puntos con borde negro para resaltar

        )

        st.plotly_chart(fig_trend, use_container_width=True)



    st.markdown("---")



    # 4. Resum Gràfic: Accidents per Districte

    st.header("Distribució Geogràfica: top 10 districtes")

    if 'Nom_districte' in df_filtrat.columns:

        with st.expander("ℹ️ Clic per a un Resum d'Interpretació", expanded=False):

            st.markdown("Mostra els 10 districtes amb més sinistralitat segons el filtre seleccionat.")

       

        df_districte = df_filtrat[df_filtrat['Nom_districte'].astype(str).str.strip() != '']

        df_districte = df_districte['Nom_districte'].value_counts().reset_index()

        df_districte.columns = ['Districte', 'Total_accidents']
        
        fig_districte = px.bar(
    df_districte.head(10),
    x='Districte',
    y='Total_accidents',
    color='Districte',
    color_discrete_sequence=px.colors.qualitative.Pastel,)
        fig_districte.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',  # Fondo del gráfico transparente
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            font_color="white",
            title_font_size=20
        )
        fig_districte.update_xaxes(
            title=None,
            showgrid=False,          # Quitamos la cuadrícula vertical (suele ensuciar)
            showline=True,           # Mostramos la línea del eje
            linecolor='white',       # Color de la línea del eje
            tickfont=dict(color='black'))

        fig_districte.update_yaxes(
            title="Total Accidents",
            showgrid=True,           # Dejamos la cuadrícula horizontal para referencia
            gridcolor='rgba(0,0,0,0.1)', # Cuadrícula blanca semitransparente
            zeroline=True,
            zerolinecolor='black',
            tickfont=dict(color='black'),
            title_font=dict(color='black'),
        )
        fig_districte.update_traces(
            marker=dict(line=dict(color='#333333', width=1))
        )
        st.plotly_chart(fig_districte, use_container_width=True)
    st.markdown("---")