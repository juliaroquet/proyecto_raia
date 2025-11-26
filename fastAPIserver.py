from fastapi import FastAPI
from pydantic import BaseModel
from cryptography.fernet import Fernet

app = FastAPI()

key = Fernet.generate_key()
fernet = Fernet(key)

class Missatge(BaseModel):
    text: str

@app.post("/mensaje")
def rebre_missatge(missatge: Missatge):
    text_original = missatge.text.encode()
    text_encriptat = fernet.encrypt(text_original)
    return {
        "resposta": f"Missatge encriptat: {text_encriptat.decode()}",
        "clau": key.decode()
    }
