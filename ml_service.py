# ml_service.py
import pickle
import pandas as pd
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

TARGET = "Descripcio_causa_mediata"
COLUMNA_CALLE = "Nom_carrer"

MODEL_PATH = Path("model/random_forest.pkl")
CODIFICADORES_PATH = Path("model/codificadores.pkl")
COLUMNS_PATH = Path("model/columns.pkl")

def cargar_csvs():
    carpeta = Path(__file__).parent / "data"
    csv_files = list(carpeta.glob("*.csv"))
    if not csv_files:
        raise RuntimeError("No se encontraron CSV en /data")
    return pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)

def preparar_dataset(df):
    df = df.fillna("NA")
    codificadores = {}
    df_encoded = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            df_encoded[col] = df[col].astype("category")
            codificadores[col] = df_encoded[col].cat.categories
            df_encoded[col] = df_encoded[col].cat.codes

    X = df_encoded.drop(columns=[TARGET])
    y = df_encoded[TARGET]

    return X, y, codificadores

def entrenar_modelo():
    df = cargar_csvs()
    X, y, codificadores = preparar_dataset(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=300, max_depth=16, random_state=42)
    model.fit(X_train, y_train)

    # guardar
    MODEL_PATH.parent.mkdir(exist_ok=True)
    pickle.dump(model, open(MODEL_PATH, "wb"))
    pickle.dump(codificadores, open(CODIFICADORES_PATH, "wb"))
    pickle.dump(list(X.columns), open(COLUMNS_PATH, "wb"))

    print("Modelo guardado correctamente")

def cargar_modelo():
    model = pickle.load(open(MODEL_PATH, "rb"))
    codificadores = pickle.load(open(CODIFICADORES_PATH, "rb"))
    columns = pickle.load(open(COLUMNS_PATH, "rb"))
    return model, codificadores, columns

def filtrar_calle(df, calle):
    return df[df[COLUMNA_CALLE].str.contains(calle, case=False, na=False)]

def codificar_df(df, codificadores):
    df_encoded = df.copy()
    for col in df.columns:
        if col in codificadores:
            cats = codificadores[col].tolist()
            df_encoded[col] = df[col].apply(lambda x: cats.index(x) if x in cats else -1)
    return df_encoded
