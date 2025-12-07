# ================================
# ENTRENAR Y GUARDAR EL MODELO ML
# ================================

from ml_service import entrenar_modelo

if __name__ == "__main__":
    print("🔧 Entrenant el model IA... (pot tardar uns segons)")
    entrenar_modelo()
    print("✔ Model entrenat i guardat correctament a la carpeta /model")
