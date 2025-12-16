# =======================================================
# FITXER: api.py (API Unificada: ML Predictiu + Dades Unity)
# =======================================================

from fastapi import FastAPI, HTTPException, File, UploadFile, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from difflib import get_close_matches
from ml_service import cargar_csvs, cargar_modelo, filtrar_calle, codificar_df
from typing import List, Dict, Any, Optional # Necessari per als models de dades de Unity
import unicodedata
import pandas as pd # Necessari per processar les dades de Unity
import os
import time

# --- Configuració de l'API i Global ---
app = FastAPI(
    title="API Unificada: ML i Dades per a Unity",
    version="1.0.0"
)

# === CORS (OBLIGATORI) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Configuració de Dades per a Unity ---
DATA_FOLDER = "data"
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True) # Assegura que la carpeta d'uploads existeix

# =======================================================
# PART 1: Models Pydantic i Funcions de Càrrega (PER A UNITY)
# =======================================================

class Accident(BaseModel):
    """Model per a l'estructura d'un registre d'accident (sortida GET)."""
    id: int
    Nk_Any: Optional[int] = None
    Nom_districte: Optional[str] = None
    Nom_carrer: Optional[str] = None
    Latitud: float
    Longitud: float
    
class NouAccident(BaseModel):
    """Model per rebre un nou accident (entrada POST de dades estructurades)."""
    Nom_districte: str
    Nom_carrer: str
    Latitud: float
    Longitud: float

def carregar_dades_accidents_per_api(df_total_ml):
    """Prepara les dades bàsiques (coords) per a ser servides a Unity."""
    if df_total_ml.empty:
        return []

    # Unificar noms de coordenades si cal
    if 'Latitud_WGS84' in df_total_ml.columns and 'Longitud_WGS84' in df_total_ml.columns:
        df_servei = df_total_ml.reindex(columns=['Nk_Any', 'Nom_districte', 'Nom_carrer', 'Latitud_WGS84', 'Longitud_WGS84']).dropna()
        df_servei.rename(columns={'Latitud_WGS84': 'Latitud', 'Longitud_WGS84': 'Longitud'}, inplace=True)
    elif 'Latitud' in df_total_ml.columns and 'Longitud' in df_total_ml.columns:
         df_servei = df_total_ml.reindex(columns=['Nk_Any', 'Nom_districte', 'Nom_carrer', 'Latitud', 'Longitud']).dropna()
    else:
        print("ADVERTÈNCIA: Columnes de coordenades no trobades.")
        return []
    
    # Crear un ID seqüencial
    df_servei['id'] = range(1, len(df_servei) + 1)
    
    # Limitem a 1000 registres (per una càrrega ràpida a Unity)
    return df_servei.head(1000).to_dict('records')


# =======================================================
# PART 2: Càrrega Global del Model i Dades
# =======================================================

# === Carga del modelo una vez (ML) ===
df = cargar_csvs()
model, codificadores, columns = cargar_modelo()

# === Preparació de la DB de dades per Unity ===
db_accidents_llista = carregar_dades_accidents_per_api(df)
if not db_accidents_llista:
    print(f"ADVERTÈNCIA: La llista de dades per a Unity està buida.")


# =======================================================
# PART 3: Funcions de Suport (PER A ML) (El teu codi original)
# =======================================================

def normalize_text_advanced(text):
    """ Normalitza i neteja el text d'entrada. """
    # ... El codi de la funció normalize_text_advanced és el teu codi original
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.replace('.', ' ').replace('-', ' ').replace("'", ' ')
    tokens_a_ignorar = [
        "carrer", "c", "avinguda", "av", "passeig", "pg", "ronda", "placa", "pl",
        "via", "rambla", "travessera", "ctra",
        "de les", "del", "de la", "de l", "dels", "de", "la", "el", "els", "les", "i"
    ]
    tokens = []
    for token in text.split():
        if token not in tokens_a_ignorar:
            tokens.append(token)
    return ' '.join(tokens).strip()

def fuzzy_find_street(df, calle):
    """ Troba el nom de carrer més proper al dataset utilitzant la normalització avançada. """
    # ... El codi de la funció fuzzy_find_street és el teu codi original
    if "Nom_carrer" not in df.columns:
        return None
    calle_normalitzada = normalize_text_advanced(calle)
    if not calle_normalitzada:
        return None
    carrers_originals = df["Nom_carrer"].dropna().unique().tolist()
    carrers_normalitzats = [normalize_text_advanced(c) for c in carrers_originals]
    match = get_close_matches(calle_normalitzada, carrers_normalitzats, n=1, cutoff=0.7)
    if match:
        index = carrers_normalitzats.index(match[0])
        return carrers_originals[index]
    return None

# =======================================================
# PART 4: Endpoints de Dades de Unity (Router 'data')
# =======================================================

data_router = APIRouter(
    prefix="/data",
    tags=["Unity-Data (GET/POST)"]
)

@data_router.get("/accidents", response_model=List[Accident])
def obtenir_accidents():
    """
    [GET] Retorna la llista de registres d'accidents (max. 1000) per a Unity.
    """
    return db_accidents_llista

@data_router.post("/afegirAccident", response_model=Dict[str, Any], status_code=201)
def afegir_accident(nou_accident: NouAccident):
    """
    [POST] Simula l'addició d'un nou registre d'accident (s'afegeix a la llista en memòria).
    """
    global db_accidents_llista
    
    nou_id = int(time.time() * 1000) # ID ràpid i únic
    
    nou_registre = {
        "id": nou_id,
        "Nk_Any": pd.Timestamp.now().year, 
        "Nom_districte": nou_accident.Nom_districte,
        "Nom_carrer": nou_accident.Nom_carrer,
        "Latitud": nou_accident.Latitud,
        "Longitud": nou_accident.Longitud,
    }
    
    db_accidents_llista.append(nou_registre)
    
    return {
        "missatge": "Nou accident afegit correctament.",
        "nou_accident": nou_registre
    }

@data_router.post("/upload_imatge")
async def upload_imatge(file: UploadFile = File(...)):
    """
    [POST] Rep i guarda un arxiu (imatge) carregat pel client de Unity al directori 'uploaded_files/'.
    """
    try:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        
        content = await file.read()
        
        if len(content) == 0:
             raise HTTPException(status_code=400, detail="L'arxiu rebut és buit.")

        with open(file_location, "wb") as buffer:
            buffer.write(content) 

        return {
            "missatge": f"Arxiu '{file.filename}' carregat correctament.",
            "path_guardat": file_location,
            "mida_bytes": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hi ha hagut un error en la càrrega de l'arxiu: {e}")

# =======================================================
# PART 5: Endpoints de Machine Learning (Sense Router)
# =======================================================

class CalleInput(BaseModel):
    nombre: str

@app.post("/predict_calle", tags=["Machine Learning (Predicció)"])
def predict_calle(data: CalleInput):
    """
    [POST] Prediu la causa més probable d'un accident en un carrer (Endpoint ML existent).
    """
    calle_final = data.nombre
    df_calle = filtrar_calle(df, calle_final)

    if df_calle.empty:
        calle_encontrada = fuzzy_find_street(df, data.nombre)
        
        if not calle_encontrada:
            return {"error": f"No hi ha registres per a '{data.nombre}' ni coincidències properes."}
        
        calle_final = calle_encontrada
        df_calle = filtrar_calle(df, calle_final)
    
    data.nombre = calle_final
    
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

# =======================================================
# PART 6: Inclusió de Routers i Endpoint Base
# =======================================================

app.include_router(data_router)

@app.get("/", tags=["Base"])
def root():
    """Endpoint base de prova."""
    return {"status": "FastAPI unificada per a ML i Dades Unity funcionant"}