#En aquest arxiu definirem el visualitzador que en aquest cas es tracta de Streamlits on podrem veure l'informació d'una manera senzilla

#Definirem les llibreries en qüestió de streamlit i requests
import streamlit as st
import requests


#Crearem el titol de la página
st.title("Client API - Register & Login")


API_URL = "http://127.0.0.1:8000"

def mostrar_missatge(url):
    resposta = requests.get(url)
    if resposta.status_code == 200:
        st.success(resposta.json()["resposta"])
    else:
        st.error("Error al conectar con la API")


if st.button("obtenir missatge genèric"):
     mostrar_missatge(f"{API_URL}/mensaje")

st.header("Registrar nou usuari")

new_username = st.text_input("Nom d'usuari nou")
new_password = st.text_input("Contrasenya nova", type="password")

if st.button("Registrar"):
    if new_username and new_password:
        payload = {"username": new_username, "password": new_password}
        resposta = requests.post(f"{API_URL}/register", json=payload)
        if resposta.status_code == 200:
            st.success(resposta.json()["resposta"])
        else:
            st.error(resposta.json().get("detail", "Error en el registre"))
    else:
        st.warning("Introdueix usuari i contrasenya")

st.header("Inici de sessió")

username = st.text_input("Usuari")
password = st.text_input("Contrasenya", type="password")

if st.button("Login"):
    if username and password:
        payload = {"username": username, "password": password}
        resposta = requests.post(f"{API_URL}/login", json=payload)
        if resposta.status_code == 200:
            st.success(resposta.json()["resposta"])
        else:
            st.error(resposta.json().get("detail", "Error d'inici de sessió"))
    else:
        st.warning("Introdueix usuari i contrasenya")



#Per poder visualitzar el missatge fem servir 'streamlit run serverStreamlit.py'