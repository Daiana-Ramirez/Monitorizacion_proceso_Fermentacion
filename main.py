from fastapi import FastAPI
from fermentacion import get_hongo_id, get_registros_fermentacion, get_detalles_por_fermentacion

from dotenv import load_dotenv
import os
from twilio.rest import Client

app = FastAPI()

# Cargar variables del archivo .env
load_dotenv()

@app.get("/")
def root():
    return {"estado": "ok", "mensaje": "API de fermentación funcionando"}

@app.get("/fermentacion/{nombre_hongo}")
def obtener_datos(nombre_hongo: str):
    hongo_id = get_hongo_id(nombre_hongo)
    if not hongo_id:
        return {"error": "Hongo no encontrado"}

    registros = get_registros_fermentacion(hongo_id)
    resultados = []

    for r in registros:
        id_f = r["id_registro_fermentacion"]
        detalles = get_detalles_por_fermentacion(id_f)
        resultados.append({
            "id_proceso": id_f,
            "detalles": detalles
        })

    return {
        "hongo": nombre_hongo,
        "procesos": resultados
    }

@app.post("/enviar-whatsapp/")
def enviar_whatsapp(mensaje: str):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_whatsapp = os.getenv("TWILIO_PHONE_NUMBER")
    to_whatsapp = os.getenv("DESTINO_WHATSAPP")

    if not all([account_sid, auth_token, from_whatsapp, to_whatsapp]):
        return {"error": "Faltan variables en el archivo .env"}

    client = Client(account_sid, auth_token)

    try:
        message = client.messages.create(
            from_=from_whatsapp,
            body=mensaje,
            to=to_whatsapp
        )
        return {"estado": "Mensaje enviado", "sid": message.sid}
    except Exception as e:
        return {"error": str(e)}
