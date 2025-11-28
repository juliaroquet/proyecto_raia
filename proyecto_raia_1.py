import streamlit as st
import pandas as pd
import os
import plotly.express as px

# --- Configuració de la Pàgina ---
st.set_page_config(page_title="Accidents a Barcelona", layout="wide")

# 💅 Estil CSS Personalitzat (Estètica Professional amb Contrast millorat)
st.markdown("""
    <style>
    /* 1. Fons de Pàgina i Color de Text Global */
    [data-testid="stAppViewContainer"] {
        background-color: #f5f7fa; /* Blanc trencat, molt net */
        color: #333333; /* Força el text global a ser gris */
    }

    /* 2. Estil del Títol Principal */
    .main-header {
        font-family: 'Verdana', Tahoma, Geneva, Segoe UI, sans-serif;
        text-align: center;
        color: #1A5276; /* Blau Corporatiu Fosc */
        font-size: 3em;
        padding-top: 15px;
        padding-bottom: 5px;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 30px;
    }

    /* 3. Estil dels KPIs (st.metric containers) */
    [data-testid="stMetric"] {
        background-color: white; 
        padding: 20px;
        border-radius: 10px; /* Cantonades arrodonides */
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05); /* Ombra subtil */
        border-left: 5px solid #4682B4; /* Barra lateral per destacar */
        /* Assegura que el text llarg es talli dins de la caixa */
        overflow: hidden; 
        text-overflow: ellipsis; 
    }
    
    /* Regles específiques per a les mètriques per assegurar-ne el contrast */
    [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] {
        color: #333333 !important; /* Assegura que les lletres del KPI siguin visibles */
    }
    
    /* Més petit: Font dels VALORS dels KPIs per encabir el text llarg de la Causa */
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.5rem; /* Reduït a 1.5rem */
        color: #333333 !important; /* CORRECCIÓ: Força el color a ser fosc per visibilitat */
    }
    
    /* 4. Estil de la Guia de Navegació i Headers */
    .stMarkdown h2 {
        color: #1A5276; 
        border-left: 5px solid #4682B4;
        padding-left: 10px;
    }

    /* 5. Estil de l'avís de dades buides */
    .stAlert {
        border-left: 5px solid #FF9900;
        color: #333333;
    }
    
    /* 6. Assegura que el text general de Streamlit tingui un bon color */
    .stMarkdown {
        color: #333333;
    }
    
    /* 7. Estil de la barra lateral (encara utilitzada per la navegació) */
    .sidebar .sidebar-content {
        background-color: #e0e6f0; /* Un blau molt clar per diferenciar */
    }

    /* 8. Estil per a l'expansor/resum del gràfic */
    .summary-expander {
        margin-bottom: 20px;
        padding: 10px;
        background-color: #e6eef5; /* Fons clar per a destacar */
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
    """Carrega tots els CSV amb doble codificació (UTF-8 i Latin-1)."""
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
        except Exception:
            # En un entorn real, millor loguejar l'error
            pass
            
    return dfs

# Carregar dades
dfs = carregar_csv_desde_carpeta()
df_total = pd.concat(dfs.values(), ignore_index=True) if dfs else pd.DataFrame()


# --- FILTRES GLOBALS A LA BARRA LATERAL (NOU) ---
anys_seleccionats = df_total['Nk_Any'].unique().tolist() # Default: tots els anys
df_filtrat = df_total.copy()

if 'Nk_Any' in df_total.columns and not df_total.empty:
    st.sidebar.header("Opcions ⚙️")
    
    # Utilitzem st.sidebar.expander per al desplegable 'Filtres:'
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
        # Si se desselecciona tot, s'ha de mostrar un df_filtrat buit
        df_filtrat = df_total.iloc[0:0] 
        anys_seleccionats = [] 


# --- Contingut de la Pàgina Principal ---

st.markdown('<h1 class="main-header">🚦 Dashboard d\'Accidents de Trànsit a Barcelona 🏙️</h1>', unsafe_allow_html=True)

if df_total.empty:
    st.warning("No s'ha pogut carregar cap dada. Puja fitxers a la pàgina '1 Distribució Causes'.")
else:
    
    # NOU: Resum de l'aplicació
    st.markdown("""
        Aquesta aplicació interactiva us permet **analitzar i visualitzar** les dades d'accidents de trànsit registrats a la ciutat de Barcelona. Utilitzeu els filtres a la barra lateral per enfocar l'anàlisi per any i exploreu les mètriques clau, les tendències temporals i la distribució geogràfica dels sinistres.
    """)
    
    # ----------------------------------------------------
    # Ajust de Columnes: [3, 2.5, 3] 
    # ----------------------------------------------------
    st.markdown("---") # Afegim un separador abans dels KPIs
    
    
    # 1. Càlcul de Mètriques Clau (KPIs) - UTILTIZA df_filtrat
    total_accidents = len(df_filtrat)
    
    # Nou KPI: Total Lesionats (no es mostra, només el deixem preparat)
    total_lesionats = df_filtrat['Num_lesionats'].sum() if 'Num_lesionats' in df_filtrat.columns else 0
    total_lesionats = int(total_lesionats) 
    
    anys_coberts = df_filtrat['Nk_Any'].nunique() if 'Nk_Any' in df_filtrat.columns else 0
    # Aquesta línia utilitza el df_filtrat, reflectint els anys seleccionats
    anys_min_max = f"{df_filtrat['Nk_Any'].min()} - {df_filtrat['Nk_Any'].max()}" if anys_coberts > 0 else "N/A"
    
    # 2. Creació de 3 Columnes per als KPIs amb proporcions ajustades
    col1, col2, col3 = st.columns([3, 2.5, 3]) 

    with col1:
        st.metric(label="Total d'Accidents (Filtre Actual)", value=f"{total_accidents:,}")
    
    with col2:
        st.metric(label="Anys en l'Anàlisi", value=anys_coberts, delta=anys_min_max)
        
    with col3:
        # Calcular la causa més freqüent
        causa_mes_freq = "No Disponible"
        if 'Descripcio_causa_mediata' in df_filtrat.columns:
            data_filtrada = df_filtrat[df_filtrat['Descripcio_causa_mediata'].astype(str).str.strip() != '']
            if not data_filtrada.empty:
                causa_mes_freq = data_filtrada['Descripcio_causa_mediata'].mode()[0]
            
        st.metric(label="Causa Més Freqüent", value=causa_mes_freq)
        
    
    st.markdown("---")
    
    # 3. Gràfic de Tendència Temporal
    if 'Nk_Any' in df_total.columns:
        st.header("Anàlisi de Tendència Temporal")
        
        # Botó de resum (Expander)
        with st.expander("ℹ️ Clic per a un Resum d'Interpretació", expanded=False):
            st.markdown("""
                Aquest gràfic de línies mostra el nombre total d'accidents de trànsit a Barcelona **cada any**, utilitzant la totalitat de les dades disponibles (sense el filtre d'any aplicat).
                
                **Objectiu:** Identificar patrons a llarg termini, com ara si la xifra d'accidents està augmentant, disminuint o es manté estable.
                
                * **Si la línia baixa:** Indica que les mesures de seguretat o els canvis en el comportament dels conductors estan sent efectius.
                * **Si la línia puja:** Suggerix que s'ha d'investigar l'impacte de factors nous (p. ex., canvis en la mobilitat, augment de la població de vehicles).
            """)
        
        # Utilitzem el df_total sencer per donar el context històric complet
        df_anual = df_total.groupby('Nk_Any').size().reset_index(name='Total_Accidents')
        
        fig_trend = px.line(
            df_anual,
            x='Nk_Any',
            y='Total_Accidents',
            title='Evolució Anual d\'Accidents de Trànsit (Totes les Dades)',
            markers=True,
            line_shape='linear',
            color_discrete_sequence=['#4682B4'] # Color de línia
        )
        fig_trend.update_layout(
            height=400,
            plot_bgcolor='#f5f7fa', 
            paper_bgcolor='#f5f7fa',
            title_font=dict(color='#000000'), 
            xaxis=dict(
                title="Any",
                tickfont=dict(color='#000000'), 
                title_font=dict(color='#000000'),
                tickmode='linear' 
            ),
            yaxis=dict(
                title="Total Accidents",
                tickfont=dict(color='#000000'), 
                title_font=dict(color='#000000')
            )
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # 4. Resum Gràfic: Accidents per Districte (UTILTIZA df_filtrat)
    st.header("Resum Ràpid: Distribució Geogràfica")
    
    if 'Nom_districte' in df_filtrat.columns:
        
        # Botó de resum (Expander)
        with st.expander("ℹ️ Clic per a un Resum d'Interpretació", expanded=False):
            # Assegurem que el missatge reflecteixi que el filtre és al sidebar
            anys_msg = ', '.join(map(str, anys_seleccionats)) if anys_seleccionats else "Cap Any Seleccionat"
            st.markdown(f"""
                Aquest gràfic de barres mostra els **10 districtes de Barcelona amb el major nombre d'accidents** registrats.
                
                **Dades:** Les dades mostrades aquí estan filtrades pels anys seleccionats al filtre lateral, a la secció **Filtres:** (Actualment: **{anys_msg}**).
                
                **Objectiu:** Identificar les zones geogràfiques de major risc o "punts calents" que requereixen atenció especial o campanyes de seguretat viària focalitzades.
            """)
        
        # Filtrar per districtes vàlids i usar df_filtrat
        df_districte = df_filtrat[df_filtrat['Nom_districte'].astype(str).str.strip() != '']
        df_districte = df_districte['Nom_districte'].value_counts().reset_index()
        df_districte.columns = ['Districte', 'Total_accidents']
        
        # Gràfic de barres senzill amb el nou color corporatiu
        fig_districte = px.bar(
            df_districte.head(10), 
            x='Districte',
            y='Total_accidents',
            title='Top 10 Districtes amb Més Accidents',
            color_discrete_sequence=['#1A5276'] # Blau Corporatiu
        )
        # Ajustos estètics de Plotly
        fig_districte.update_layout(
            height=400,
            plot_bgcolor='#f5f7fa', 
            paper_bgcolor='#f5f7fa',
            title_font=dict(color='#000000'), 
            xaxis=dict(
                categoryorder='total descending', 
                tickfont=dict(color='#000000'), 
                title_font=dict(color='#000000'),
                title="Districte"
            ),
            yaxis=dict(
                tickfont=dict(color='#000000'), 
                title_font=dict(color='#000000'),
                title="Total Accidents"
            )
        )
        st.plotly_chart(fig_districte, use_container_width=True)
        

    st.markdown("---")