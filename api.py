from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/obtener_ruta_predicha', methods=['GET'])
def home():
    # AQUÍ IRÍA TU CÓDIGO DE PREDICCIÓN REAL
    # Por ahora devolvemos datos falsos para probar que Unity los recibe
    
    datos = {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [2.1685, 41.3879] # Longitud, Latitud (BCN)
          }
        },
        {
          "type": "Feature",
          "geometry": {
             "type": "Point",
             "coordinates": [2.1700, 41.3885] 
          }
        }
      ]
    }
    
    print("¡Unity me ha pedido datos!")
    return jsonify(datos)

if __name__ == '__main__':
    # host='0.0.0.0' permite que se conecten desde fuera si hace falta
    app.run(host='0.0.0.0', port=5000)