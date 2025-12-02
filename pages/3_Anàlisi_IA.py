import streamlit as st
import pandas as pd
import os
import re
from collections import Counter

# --- Configuració de la Pàgina ---
# S'ha eliminat el paràmetre 'color' ja que no és vàlid per a st.set_page_config
st.set_page_config(page_title="Analista de Dades d'Accidents", layout="wide")

# 💅 Estil més "Professional/Analític" amb contrast millorat
st.markdown("""
    <style>
    /* Fons clar per anàlisi */
    [data-testid="stAppViewContainer"] {
        background-color: #f0f2f6; 
    }
    
    /* --- Estil de Títols (Color Rosa Lluent Forçat) --- */
    .analyst-title {
        font-family: sans-serif;
        text-align: center;
        font-size: 40px;
        color: #FF007F !important; /* TORNA AL ROSA INTENS I LLUENT, FORÇAT AMB !important */
        text-shadow: 0px 0px 8px rgba(255, 0, 127, 0.7); /* Ombra per simular "lluentor" */
        margin-bottom: 5px;
    }
    .analyst-subtitle {
        text-align: center;
        font-size: 18px;
        color: #333333; /* Gris fosc per a major contrast */
        margin-bottom: 30px;
    }
    
    /* --- Estil per al Chatbot (Bombolla de l'assistent) --- */
    [data-testid="stChatMessageContent"] {
        background-color: #e0f7fa; /* Còmic de bombolla clar */
        border-left: 5px solid #00bcd4;
        color: #1a5276; /* TEXT MÉS FOSC per millorar la llegibilitat sobre el fons clar */
        padding: 10px;
        border-radius: 8px;
        font-size: 16px;
    }
    
    /* Estil per a l'entrada de text */
    .stTextInput > div > div > input {
        border-radius: 15px;
        border: 1px solid #00bcd4;
        color: #333;
    }
    
    /* Estil per al text de l'usuari (per defecte de streamlit, però assegurem contrast) */
    [data-testid="stChatMessage"] .stMarkdown {
        color: #333333; 
    }
    
    </style>
""", unsafe_allow_html=True)

# --- Títol i subtítol ---
st.markdown('<h1 class="analyst-title">🤖 Analista de Dades de Trànsit</h1>', unsafe_allow_html=True)
st.markdown('<p class="analyst-subtitle">Fes preguntes concretes sobre els accidents de trànsit a Barcelona basades en les dades que has pujat.</p>', unsafe_allow_html=True)


# --- 1. Càrrega i Pre-processament de Dades (Funció de Doble Codificació) ---
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

@st.cache_data
def carregar_csv_desde_carpeta():
    """Carrega tots els CSV amb doble codificació (UTF-8 i Latin-1)."""
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
        except Exception as e:
            st.error(f"❌ Error carregant {arxiu}: {e}")
            
    return dfs

# Carregar i combinar les dades
dfs = carregar_csv_desde_carpeta()
if dfs:
    df_accidents = pd.concat(dfs.values(), ignore_index=True)
else:
    df_accidents = pd.DataFrame()


# --- 2. Inicialitzar Historial de Conversa ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Sóc l'analista de dades. Pots preguntar-me sobre districtes, causes, anys, i tipus d'accidents. Per exemple: 'Quin és el districte amb més accidents?' o 'Quina és la causa més freqüent?'"
        }
    ]


# --- 3. Funció de Lògica de Resposta ---

def analitzar_pregunta(user_text, df):
    """Analitza el text de l'usuari i retorna una resposta basada en les dades."""
    if df.empty:
        return "No s'han trobat dades per analitzar. Assegura't de pujar els arxius CSV a la pàgina '1 Distribució Causes'."

    user_text = user_text.lower()
    
    # Estandaritzar noms de columnes per a la lògica d'anàlisi
    COL_DISTRICTE = 'Nom_districte'
    COL_CAUSA = 'Descripcio_causa_mediata'
    COL_ANY = 'Nk_Any'
    
    resposta = ""
    
    # --- Detecció de Preguntes Clau ---
    
    # 3.1 Preguntes Generals (Total, Anys)
    if any(keyword in user_text for keyword in ["total accidents", "quants accidents", "nombre total"]):
        total = len(df)
        resposta = f"El nombre total d'accidents registrats a totes les dades combinades és de **{total:,}**."

    elif any(keyword in user_text for keyword in ["quants anys", "període", "quin rang"]):
        if COL_ANY in df.columns:
            anys = df[COL_ANY].dropna().astype(int).unique()
            if len(anys) > 0:
                min_any, max_any = min(anys), max(anys)
                num_anys = len(anys)
                resposta = f"Les dades cobreixen un total de **{num_anys}** anys, des de **{min_any}** fins a **{max_any}**."
            else:
                resposta = "No s'ha trobat informació d'any (columna 'Nk_Any')."
        else:
            resposta = f"No s'ha trobat la columna '{COL_ANY}' per analitzar els anys."
            
    # 3.2 Preguntes sobre Districte
    elif any(keyword in user_text for keyword in ["districte amb més", "districte mes", "districte amb menys"]):
        if COL_DISTRICTE in df.columns:
            # Neteja de dades: Ignorar valors buits o 'Desconegut'
            data = df[df[COL_DISTRICTE].notna() & (df[COL_DISTRICTE].str.strip() != '') & (df[COL_DISTRICTE].str.strip() != 'Desconegut')]
            
            if data.empty:
                resposta = "No hi ha dades de districte vàlides per a l'anàlisi."
            else:
                comptatge = data[COL_DISTRICTE].value_counts()
                
                if "menys" in user_text:
                    districte_clau = comptatge.index[-1]
                    total_clau = comptatge.iloc[-1]
                    resposta = f"El districte amb **menys** accidents és **{districte_clau}** amb un total de {total_clau:,} accidents."
                else:
                    districte_clau = comptatge.index[0]
                    total_clau = comptatge.iloc[0]
                    resposta = f"El districte amb **més** accidents registrats és **{districte_clau}** amb un total de {total_clau:,} accidents."
        else:
            resposta = f"No s'ha trobat la columna '{COL_DISTRICTE}' per analitzar per districte."

    # 3.3 Preguntes sobre Causes
    elif any(keyword in user_text for keyword in ["causa més", "causa mes", "motiu principal"]):
        if COL_CAUSA in df.columns:
            # Neteja de dades: Ignorar valors buits
            data = df[df[COL_CAUSA].notna() & (df[COL_CAUSA].str.strip() != '')]
            
            if data.empty:
                resposta = "No hi ha dades de causes vàlides per a l'anàlisi."
            else:
                comptatge = data[COL_CAUSA].value_counts()
                causa_clau = comptatge.index[0]
                total_clau = comptatge.iloc[0]
                percentatge = (total_clau / len(data)) * 100
                
                resposta = f"La **causa mediata més freqüent** dels accidents és: **'{causa_clau}'**, representant un **{percentatge:.2f}%** del total ({total_clau:,} casos)."
        else:
            resposta = f"No s'ha trobat la columna '{COL_CAUSA}' per analitzar les causes."

    # 3.4 Anàlisi Específica (e.g., Accidents en un any concret)
    elif (any(c in user_text for c in ['accidents', 'casos', 'sinistres']) and 
          re.search(r'\b\d{4}\b', user_text)):
        
        any_trobat = re.search(r'\b\d{4}\b', user_text).group(0)
        
        if COL_ANY in df.columns:
            df_any = df[df[COL_ANY].astype(str) == any_trobat]
            total_any = len(df_any)
            
            if total_any > 0:
                resposta = f"L'any **{any_trobat}** es van registrar **{total_any:,}** accidents. Pots comprovar la distribució de causes per a aquest any a la pàgina 'Distribució Causes'."
            else:
                resposta = f"No es van trobar accidents registrats per a l'any **{any_trobat}** en les dades disponibles."
        else:
            resposta = f"No puc filtrar per any perquè falta la columna '{COL_ANY}'."


    # 3.5 Resposta per Defecte
    else:
        # Utilitzar algunes paraules clau per donar una resposta útil
        if any(keyword in user_text for keyword in ["hola", "saluda", "bon dia"]):
            resposta = "Hola! Estic preparat per analitzar els accidents de trànsit. Fes-me una pregunta sobre districtes, causes o anys."
        else:
            resposta = "Ho sento, no he entès la teva pregunta. Pots provar amb preguntes més concretes com: 'Quin districte té més accidents?' o 'Quina és la causa principal?'"
            
    return resposta


# --- 4. Mostrar Missatges i Processar l'Entrada de l'Usuari ---

# Mostrar missatges previs
for msg in st.session_state.messages:
    avatar = "🕵️" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Entrada de l'usuari
if prompt := st.chat_input("Fes la teva pregunta d'anàlisi aquí..."):
    # Afegir missatge de l'usuari a l'historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Obtenir la resposta de l'analista
    with st.spinner("Analitzant les dades..."):
        response = analitzar_pregunta(prompt, df_accidents)
        
    # Afegir missatge de l'assistent a l'historial
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Mostrar la resposta de l'assistent
    with st.chat_message("assistant", avatar="🕵️"):
        st.markdown(response)

# --- 5. Missatge d'Estat de les Dades ---
if df_accidents.empty:
    st.warning("Estat de les dades: No hi ha dades carregades. Sisplau, puja CSVs a la primera pàgina.")
else:
    st.sidebar.success(f"Dades carregades correctament: {len(df_accidents):,} registres.")