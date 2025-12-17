import streamlit as st
import pandas as pd
import os
import re
from collections import Counter
import requests
from difflib import get_close_matches
import unicodedata

FASTAPI_URL = "http://localhost:8000"   # o la URL donde tengas FastAPI corriendo

def normalize_text_advanced(text):
    """
    Normalitza i neteja el text d'entrada:
    1. Minúscules i eliminació d'espais.
    2. Eliminació d'accents (diacrítics).
    3. Eliminació de signes de puntuació.
    4. Eliminació de tipus de via i preposicions comunes.
    """
    if not isinstance(text, str):
        return ""

    text = text.lower().strip()

    # 1. Normalització d'Unicode (treu accents i diacrítics: 'aragó' -> 'arago')
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

    # 2. Neteja de caràcters i signes
    text = text.replace('.', ' ').replace('-', ' ').replace("'", ' ')
    
    # Llista de tokens de tipus de via i preposicions a ignorar
    tokens_a_ignorar = [
        "carrer", "c", "avinguda", "av", "passeig", "pg", "ronda", "placa", "pl",
        "via", "rambla", "travessera", "ctra",
        "de les", "del", "de la", "de l", "dels", "de", "la", "el", "els", "les", "i"
    ]
    
    # 3. Eliminació de tokens
    tokens = []
    for token in text.split():
        if token not in tokens_a_ignorar:
            tokens.append(token)

    return ' '.join(tokens).strip()

# Exemple: 'Prediu la causa per Av. Aragó' -> 'prediu causa arago'
# Exemple: 'AVINGUDA DE SARRIÀ' -> 'sarria'

def predict_calle_via_api(calle: str):
    """Llama al endpoint FastAPI /predict_calle."""
    try:
        resp = requests.post(
            f"{FASTAPI_URL}/predict_calle",
            json={"nombre": calle}
        )
        return resp.json()
    except Exception as e:
        return {"error": f"Error connectant amb el servidor FastAPI: {e}"}


# --- Configuració de la Pàgina ---
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

def detectar_carrer_ontologic(text, df):
    """
    Detecta noms de carrer usant la normalització avançada i fuzzy matching.
    Ara aïlla el nom del carrer del soroll de la pregunta.
    """
    if "Nom_carrer" not in df.columns:
        return None

    # 1. Normalitzem el text de l'usuari (retorna 'prediu causa problable a arago')
    text_normalitzat_complet = normalize_text_advanced(text)

    if not text_normalitzat_complet:
        return None
        
    # NOU PAS CLAU: Aïllem només la part final del text (els últims 4 mots) per a la comparació fuzzy.
    text_a_comparar = ' '.join(text_normalitzat_complet.split()[-4:])


    # Obtenim la llista de noms ORIGINALS i NORMALITZATS del dataset
    carrers_originals = df["Nom_carrer"].dropna().unique().tolist()
    # Aquesta llista idealment només s'hauria de calcular una vegada, fora de la funció.
    carrers_normalitzats = [normalize_text_advanced(c) for c in carrers_originals] 
    
    # 1. Intent de Coincidència amb les últimes 4 paraules
    match = get_close_matches(text_a_comparar, carrers_normalitzats, n=1, cutoff=0.7)

    if match:
        # Trobem l'índex del nom normalitzat que ha coincidit
        index = carrers_normalitzats.index(match[0])
        # Retornem el nom ORIGINAL i correcte del dataset
        return carrers_originals[index]

    # 2. Intent de Coincidència de paraula única (per si només es diu "Diagonal")
    # Si la primera cerca falla, intentem buscar un match només amb el darrer mot
    if len(text_a_comparar.split()) > 1:
        text_darrer_mot = text_a_comparar.split()[-1]
        
        match_ultim = get_close_matches(text_darrer_mot, carrers_normalitzats, n=1, cutoff=0.7)
        if match_ultim:
            index = carrers_normalitzats.index(match_ultim[0])
            return carrers_originals[index]

    return None


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
    elif any(keyword in user_text for keyword in ["causa més", "causa mes", "motiu principal", "causes mes frequents"]):
        if COL_CAUSA not in df.columns:
            resposta = f"No s'ha trobat la columna '{COL_CAUSA}' per analitzar les causes."
        else:
            data = df[df[COL_CAUSA].notna() & (df[COL_CAUSA].str.strip() != '')]

        if data.empty:
            resposta = "No hi ha dades de causes vàlides per a l'anàlisi."
        else:
            comptatge = data[COL_CAUSA].value_counts().head(3)
            total = len(data)

            linies = []
            for i, (causa, count) in enumerate(comptatge.items(), start=1):
                percentatge = (count / total) * 100
                linies.append(
                    f"**{i}. {causa}** → {count:,} casos ({percentatge:.2f}%)"
                )

            resposta = (
                "Les **3 causes mediates més freqüents** dels accidents són:\n\n"
                + "\n".join(linies)
            )
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
    
    # 3.5 Predicció IA segons una calle (integració FastAPI)
    if any(word in user_text for word in ["prediu", "predicció", "causa probable", "prediccio"]):
        
        # 1) Intent simple amb regex: carrer X
        match = re.search(r"(carrer|avinguda|av\.?|passeig|pg\.?|via|ronda|plaça|travessera)\s+([\w\s\-]+)", user_text)
        
        if match:
            carrer_detectat = match.group(0)
        else:
            # 2) Mètode robust: fuzzy matching contra tota la llista de carrers
            carrer_detectat = detectar_carrer_ontologic(user_text, df)
        
        if not carrer_detectat:
            return "No he pogut identificar cap carrer a la teva pregunta. Prova amb: 'Prediu la causa probable a Avinguda Diagonal'."

        # Cridar a FastAPI
        result = predict_calle_via_api(carrer_detectat)

        if "error" in result:
            return f"⚠️ Error en la predicció: {result['error']}"

        pred = result.get("prediccion")
        probas = result.get("probabilidades", {})

        resposta = (
            f"🔍 **Predicció IA per a _{carrer_detectat}_:**\n\n"
            f"📌 **Causa més probable:** *{pred}*\n\n"
            f"📊 **Probabilitats:**\n"
        )

        for causa, pct in probas.items():
            resposta += f"- {causa}: {pct:.2%}\n"

        return resposta



    # 3.6 Resposta per Defecte
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