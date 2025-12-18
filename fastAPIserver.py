# =======================================================
# FITXER: api.py (API Unificada: ML Predictiu + Dades Unity)
# =======================================================

from fastapi import FastAPI, HTTPException, File, UploadFile, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from difflib import get_close_matches
from ml_service import cargar_csvs, cargar_modelo, filtrar_calle, codificar_df
from typing import List, Dict, Any, Optional
import unicodedata
import pandas as pd
import os
import time

# --- Configuració de l'API ---
app = FastAPI(
    title="API Unificada: ML i Dades per a Unity",
    version="1.1.0"
)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Configuració de Directoris ---
DATA_FOLDER = "data"
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =======================================================
# PART 1: Models Pydantic
# =======================================================

class Accident(BaseModel):
    id: int
    Nk_Any: Optional[int] = None
    Nom_districte: Optional[str] = None
    Nom_carrer: Optional[str] = None
    Latitud: float
    Longitud: float
    
class NouAccident(BaseModel):
    Nom_districte: str
    Nom_carrer: str
    Latitud: float
    Longitud: float

class CalleInput(BaseModel):
    nombre: str

# =======================================================
# PART 2: Càrrega Global del Model i Dades
# =======================================================

# Cargamos los datos y el modelo una sola vez al iniciar el servidor
df = cargar_csvs()
model, codificadores, columns = cargar_modelo()

def carregar_dades_accidents_per_api(df_total_ml):
    """ Prepara los datos de coordenadas para Unity """
    if df_total_ml.empty:
        return []
    
    # Unificar nombres de columnas de coordenadas
    if 'Latitud_WGS84' in df_total_ml.columns and 'Longitud_WGS84' in df_total_ml.columns:
        df_servei = df_total_ml.reindex(columns=['Nk_Any', 'Nom_districte', 'Nom_carrer', 'Latitud_WGS84', 'Longitud_WGS84']).dropna()
        df_servei.rename(columns={'Latitud_WGS84': 'Latitud', 'Longitud_WGS84': 'Longitud'}, inplace=True)
    elif 'Latitud' in df_total_ml.columns and 'Longitud' in df_total_ml.columns:
         df_servei = df_total_ml.reindex(columns=['Nk_Any', 'Nom_districte', 'Nom_carrer', 'Latitud', 'Longitud']).dropna()
    else:
        return []
    
    df_servei['id'] = range(1, len(df_servei) + 1)
    return df_servei.head(1000).to_dict('records')

db_accidents_llista = carregar_dades_accidents_per_api(df)

# =======================================================
# PART 3: Funcions de Suport ML
# =======================================================

def normalize_text_advanced(text):
    if not isinstance(text, str): return ""
    text = text.lower().strip()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = text.replace('.', ' ').replace('-', ' ').replace("'", ' ')
    tokens_a_ignorar = ["carrer", "c", "avinguda", "av", "passeig", "pg", "ronda", "placa", "pl", "via", "rambla", "travessera", "ctra", "de les", "del", "de la", "de l", "dels", "de", "la", "el", "els", "les", "i"]
    return ' '.join([t for t in text.split() if t not in tokens_a_ignorar]).strip()

def fuzzy_find_street(df, calle):
    if "Nom_carrer" not in df.columns: return None
    calle_norm = normalize_text_advanced(calle)
    if not calle_norm: return None
    carrers_originals = df["Nom_carrer"].dropna().unique().tolist()
    carrers_norm = [normalize_text_advanced(c) for c in carrers_originals]
    match = get_close_matches(calle_norm, carrers_norm, n=1, cutoff=0.7)
    return carrers_originals[carrers_norm.index(match[0])] if match else None

# =======================================================
# PART 4: Endpoints de Dades de Unity (Router 'data')
# =======================================================

data_router = APIRouter(prefix="/data", tags=["Unity-Data"])

@data_router.get("/accidents", response_model=List[Accident])
def obtenir_accidents():
    return db_accidents_llista

@data_router.post("/afegirAccident", status_code=201)
def afegir_accident(nou_accident: NouAccident):
    global db_accidents_llista
    registre = {
        "id": int(time.time() * 1000),
        "Nk_Any": pd.Timestamp.now().year, 
        "Nom_districte": nou_accident.Nom_districte,
        "Nom_carrer": nou_accident.Nom_carrer,
        "Latitud": nou_accident.Latitud,
        "Longitud": nou_accident.Longitud,
    }
    db_accidents_llista.append(registre)
    return {"missatge": "Accident afegit", "accident": registre}

@data_router.post("/upload_imatge")
async def upload_imatge(file: UploadFile = File(...)):
    try:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        content = await file.read()
        if len(content) == 0:
             raise HTTPException(status_code=400, detail="L'arxiu rebut és buit.")
        with open(file_location, "wb") as buffer:
            buffer.write(content) 
        return {"missatge": f"Arxiu '{file.filename}' carregat.", "mida": len(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =======================================================
# PART 5: Endpoint Machine Learning (TOP 3 CAUSES)
# =======================================================

@app.post("/predict_calle", tags=["Machine Learning"])
def predict_calle(data: CalleInput):
    calle_final = data.nombre
    df_calle = filtrar_calle(df, calle_final)

    # Fuzzy Matching si no hay registros exactos
    if df_calle.empty:
        calle_encontrada = fuzzy_find_street(df, data.nombre)
        if not calle_encontrada:
            raise HTTPException(status_code=404, detail=f"No hay datos para '{data.nombre}'")
        calle_final = calle_encontrada
        df_calle = filtrar_calle(df, calle_final)
    
    # Proceso de predicción
    df_encoded = codificar_df(df_calle, codificadores)
    X_input = df_encoded[columns]
    probas = model.predict_proba(X_input)

    # Cálculo de Top 3
    etiquetas = codificadores["Descripcio_causa_mediata"]
    proba_media = probas.mean(axis=0)
    proba_dict = {etiquetas[i]: float(round(proba_media[i] * 100, 2)) for i in range(len(etiquetas))}
    
    top_3_list = sorted(proba_dict.items(), key=lambda x: x[1], reverse=True)[:3]
    top_3_formatted = [{"causa": c, "probabilitat": p} for c, p in top_3_list]

    return {
        "calle": calle_final,
        "top_3": top_3_formatted,
        "probabilitats_completes": proba_dict
    }

# =======================================================
# PART 6: Inicialització
# =======================================================

app.include_router(data_router)

@app.get("/")
def root():
    return {"status": "API Unificada ONLINE", "mode": "ML + Unity Data"}