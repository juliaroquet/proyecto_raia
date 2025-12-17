# ===============================================
# PROYECTO ML – ACCIDENTES SEGÚN CAUSA CONDUCTOR
# CLASIFICACIÓN + CLUSTERING
# ===============================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)



# ===============================================
# 1. CARGAR DATASET (VARIOS CSV)
# ===============================================

from pathlib import Path
import pandas as pd

# Carpeta donde están tus CSV
carpeta = Path(__file__).parent.parent / "datasets"

# Obtener todos los CSV
csv_files = list(carpeta.glob("*.csv"))

if len(csv_files) == 0:
    print("❌ No se encontraron archivos CSV en:", carpeta)
    exit()

print("CSV encontrados:")
for f in csv_files:
    print(" -", f.name)

# Unir todos los CSV
df = pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)

print("\n✔ Dataset combinado correctamente.")
print("Total de filas:", len(df))
print("Columnas del dataset:")
print(df.columns)


# ===============================================
# 2. DEFINIR TARGET
# ===============================================

target = "Descripcio_causa_mediata"

if target not in df.columns:
    print("\n❌ ERROR: La columna objetivo no existe.")
    print("Columnas disponibles:", list(df.columns))
    exit()

# ===============================================
# 3. IMPUTAR NULOS
# ===============================================

df = df.fillna("NA")  # Reemplazar nulos por 'NA' (podría ser otra estrategia según el dataset)

# ===============================================
# 4. CODIFICAR VARIABLES
# ===============================================

df_encoded = df.copy()
# Convertir variables categóricas a números para Random Forest
df_encoded = df_encoded.apply(
    lambda col: col.astype("category").cat.codes if col.dtype == "object" else col
)

# ===============================================
# 5. SEPARAR X E Y
# ===============================================

X = df_encoded.drop(columns=[target])
y = df_encoded[target]

print("\nDataset preparado correctamente")
print("X shape:", X.shape)
print("y shape:", y.shape)

# ===============================================
# 6. SPLIT TRAIN/TEST
# ===============================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

# ===============================================
# 7. ENTRENAR MODELO RANDOM FOREST
# ===============================================

model = RandomForestClassifier(
    n_estimators=200,  # Número de árboles
    max_depth=12,      # Profundidad máxima de cada árbol
    random_state=42
)

model.fit(X_train, y_train)

# ===============================================
# 8. PREDICCIÓN
# ===============================================

y_pred = model.predict(X_test)

# ===============================================
# 9. MÉTRICAS
# ===============================================

print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# ===============================================
# 10. MATRIZ DE CONFUSIÓN MEJORADA
# ===============================================

cm = confusion_matrix(y_test, y_pred)
labels = df[target].astype("category").cat.categories  # Obtener etiquetas originales

plt.figure(figsize=(10, 8))
sns.heatmap(
    cm, 
    annot=True, 
    fmt='d', 
    cmap='Blues', 
    xticklabels=labels, 
    yticklabels=labels
)
plt.ylabel('Etiqueta Real')
plt.xlabel('Etiqueta Predicha')
plt.title("Matriz de Confusión – Random Forest")
plt.xticks(rotation=45)
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()


# ===============================================
# 11. IMPORTANCIA DE VARIABLES
# ===============================================

importances = model.feature_importances_
features = X.columns
feature_importance_df = pd.DataFrame({'feature': features, 'importance': importances})
feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)

plt.figure(figsize=(10, 6))
sns.barplot(x='importance', y='feature', data=feature_importance_df)
plt.title("Importancia de Variables – Random Forest")
plt.tight_layout()
plt.show()

# ==========================================================
# PROYECTO ML – PREDICCIÓN DE CAUSA SEGÚN NOMBRE DE CALLE
# MODELO + INPUT + PROBABILIDADES + GRIDSEARCH OPCIONAL
# ==========================================================

import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

TARGET = "Descripcio_causa_mediata"
COLUMNA_CALLE = "Nom_carrer"   # Ajustar si tu dataset usa otra columna


# ==========================================================
# 1. CARGAR CSVs
# ==========================================================

def cargar_csvs():
    carpeta = Path(__file__).parent.parent / "datasets"
    csv_files = list(carpeta.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError("No se encontraron CSV en /datasets")

    df = pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)
    return df


# ==========================================================
# 2. IMPUTAR Y CODIFICAR
# ==========================================================

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


# ==========================================================
# 3. ENTRENAR RANDOM FOREST
# ==========================================================

def entrenar_random_forest(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300, max_depth=16, random_state=42
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("\n=== MÉTRICAS RANDOM FOREST ===")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    return model


# ==========================================================
# 4. FILTRAR CALLE
# ==========================================================

def filtrar_calle(df, calle):
    return df[df[COLUMNA_CALLE].str.contains(calle, case=False, na=False)]


# ==========================================================
# 5. CODIFICAR SEGÚN CODIFICADORES ORIGINALES
# ==========================================================

def codificar_df(df, codificadores):
    df_encoded = df.copy()

    for col in df.columns:
        if col in codificadores:
            cats = codificadores[col].tolist()
            df_encoded[col] = df[col].apply(lambda x: cats.index(x) if x in cats else -1)

    return df_encoded


# ==========================================================
# 6. PREDICCIÓN + PROBABILIDAD
# ==========================================================

def predecir_calle(modelo, df_calle, X_columns, codificadores):

    df_encoded = codificar_df(df_calle, codificadores)
    X_input = df_encoded[X_columns]

    y_pred = modelo.predict(X_input)
    probas = modelo.predict_proba(X_input)

    etiquetas = codificadores[TARGET]
    pred_texto = [etiquetas[p] for p in y_pred]

    print("\n=== PREDICCIONES PARA LA CALLE (primeros 15) ===")
    for i, p in enumerate(pred_texto[:15]):
        print(f"{i+1}. {p}")

    proba_media = probas.mean(axis=0)
    proba_dict = {etiquetas[i]: round(proba_media[i] * 100, 2)
                  for i in range(len(etiquetas))}

    print("\n=== PROBABILIDAD PROMEDIO POR CLASE ===")
    for clase, pct in proba_dict.items():
        print(f"- {clase}: {pct}%")

   # TOP 3 causas más probables
    top_3 = sorted(
        proba_dict.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    print("\n TOP 3 causas más probables:")
    for i, (causa, prob) in enumerate(top_3, start=1):
        print(f"{i}. {causa} ({prob}%)")


# ==========================================================
# 7. GRIDSEARCH (OPCIONAL)
# ==========================================================

def ejecutar_gridsearch(X, y):
    print("\nEjecutando GridSearchCV...")

    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [8, 12, 16, None],
        "min_samples_split": [2, 5, 10],
    }

    grid = GridSearchCV(
        RandomForestClassifier(random_state=42),
        param_grid,
        cv=5,
        n_jobs=-1,
        verbose=1
    )

    grid.fit(X, y)

    print("\nMejores parámetros encontrados:")
    print(grid.best_params_)

    return grid.best_estimator_


# ==========================================================
# 8. COMPARAR VARIOS MODELOS
# ==========================================================

def comparar_modelos(X_train, X_test, y_train, y_test, X, y):

    modelos = {
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "Decision Tree": DecisionTreeClassifier(max_depth=6),
        "Naive Bayes": GaussianNB(),
        "Linear SVM": SVC(kernel="linear", probability=True),
        "RBF SVM": SVC(gamma=2, C=1, probability=True),
        "Neural Net": MLPClassifier(alpha=1, max_iter=1000),
        "Random Forest": RandomForestClassifier(n_estimators=200, max_depth=12)
    }

    print("\n===== COMPARACION DE MODELOS =====")

    for nombre, modelo in modelos.items():
        modelo.fit(X_train, y_train)
        acc = modelo.score(X_test, y_test)
        cv = cross_val_score(modelo, X, y, cv=10).mean()

        print(f"{nombre.ljust(15)}  Test Acc = {acc:.3f} | CV Acc = {cv:.3f}")


# ==========================================================
# MAIN
# ==========================================================

def main():

    df = cargar_csvs()
    print(f"✔ Dataset cargado ({len(df)} filas)")

    X, y, codificadores = preparar_dataset(df)
    modelo = entrenar_random_forest(X, y)

    calle = input("\nIngresa la calle a analizar: ").strip()
    df_calle = filtrar_calle(df, calle)

    if df_calle.empty:
        print(f"No hay registros para '{calle}'")
        return

    print(f"✔ {len(df_calle)} registros encontrados en '{calle}'")

    predecir_calle(modelo, df_calle, X.columns, codificadores)

if __name__ == "__main__":
    main()