from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from difflib import get_close_matches
from ml_service import cargar_csvs, cargar_modelo, filtrar_calle, codificar_df
import unicodedata

app = FastAPI()

# === CORS (OBLIGATORIO para conectar con Streamlit) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    
    allow_methods=["*"],
    allow_headers=["*"]
)

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

def fuzzy_find_street(df, calle):
    """
    Troba el nom de carrer més proper al dataset utilitzant la normalització avançada.
    """
    if "Nom_carrer" not in df.columns:
        return None

    # Normalitzem el nom de la carrer a buscar que ve de Streamlit
    calle_normalitzada = normalize_text_advanced(calle)

    if not calle_normalitzada:
        return None
    
    # Obtenim la llista de noms ORIGINALS del dataset
    carrers_originals = df["Nom_carrer"].dropna().unique().tolist()
    
    # Generem la llista de noms NORMALITZATS del dataset per a la comparació
    carrers_normalitzats = [normalize_text_advanced(c) for c in carrers_originals]

    # Buscar coincidències properes amb els textos normalitzats
    match = get_close_matches(calle_normalitzada, carrers_normalitzats, n=1, cutoff=0.7)

    if match:
        index = carrers_normalitzats.index(match[0])
        # Retornem el nom ORIGINAL i correcte del dataset (Ex: "AVINGUDA DIAGONAL")
        return carrers_originals[index]

    return None

# NO cal canviar el teu endpoint /predict_calle ja que ja feia servir 'fuzzy_find_street',
# només calia actualitzar la definició de la funció en si.


# === Endpoint base de prueba ===
@app.get("/")
def root():
    return {"status": "FastAPI funcionando"}

# === Carga del modelo una vez ===
df = cargar_csvs()
model, codificadores, columns = cargar_modelo()

# === Input del endpoint predict_calle ===
class CalleInput(BaseModel):
    nombre: str

from fastapi import APIRouter
# ... otros imports y la definición de la clase CalleInput ...

@app.post("/predict_calle")
def predict_calle(data: CalleInput):
    # 1. Definimos el nombre de calle inicial, que asumimos será el final si no hay fuzzy match
    calle_final = data.nombre
    
    # 2. Intento EXACTO
    df_calle = filtrar_calle(df, calle_final)

    # 3. Si no hay coincidencias exactas, intentamos fuzzy matching
    if df_calle.empty:
        # Intentamos encontrar el nombre real usando fuzzy matching
        calle_encontrada = fuzzy_find_street(df, data.nombre)
        
        # Si el fuzzy matching tampoco encuentra nada, retornamos el error
        if not calle_encontrada:
            return {"error": f"No hay registros para '{data.nombre}'"}
        
        # Si encontramos el nombre real (fuzzy match), actualizamos el nombre final
        calle_final = calle_encontrada
        
        # Volvemos a buscar en el DataFrame con el nombre real encontrado
        df_calle = filtrar_calle(df, calle_final)
    
    # Después de este punto, df_calle contiene datos O ya hemos retornado un error.
    # Usamos calle_final como el nombre final de la calle.
    
    # 4. Actualizamos el Pydantic Model (opcional, pero útil para el JSON de retorno)
    data.nombre = calle_final
    
    # 5. Lógica del Modelo de Machine Learning (tu código original)
    df_encoded = codificar_df(df_calle, codificadores)
    X_input = df_encoded[columns]

    pred = model.predict(X_input)
    proba = model.predict_proba(X_input)

    etiquetas = codificadores["Descripcio_causa_mediata"]
    proba_media = proba.mean(axis=0)
    proba_dict = {etiquetas[i]: float(proba_media[i]) for i in range(len(etiquetas))}
    top = max(proba_dict, key=proba_dict.get)

    return {
        "calle": data.nombre,
        "prediccion": top,
        "probabilidades": proba_dict
    }
