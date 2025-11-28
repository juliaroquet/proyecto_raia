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


