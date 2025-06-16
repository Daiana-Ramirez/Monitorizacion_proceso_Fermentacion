from dotenv import load_dotenv
import os
import requests
import pandas as pd

# Cargar variables de entorno desde .env
load_dotenv()

HASURA_URL = os.getenv("HASURA_URL")
HASURA_SECRET = os.getenv("HASURA_SECRET")

HEADERS = {
    "Content-Type": "application/json",
    "x-hasura-admin-secret": HASURA_SECRET
}

def get_hongo_id(nombre_hongo):
    query = {
        "query": """
        query ($nombre: String!) {
          Hongo(where: {nombre_Hongo: {_ilike: $nombre}}) {
            id_Hongo
          }
        }
        """,
        "variables": {"nombre": nombre_hongo}
    }
    response = requests.post(HASURA_URL, headers=HEADERS, json=query)
    data = response.json()

    if "errors" in data:
        print("❌ Error al obtener ID del hongo:", data["errors"])
        return None

    return data["data"]["Hongo"][0]["id_Hongo"] if data["data"]["Hongo"] else None

def get_registros_fermentacion(hongo_id):
    query = {
        "query": """
        query ($id: Int!) {
          Registro_Fermentacion(where: {id_hongo: {_eq: $id}}) {
            id_registro_fermentacion
          }
        }
        """,
        "variables": {"id": hongo_id}
    }
    response = requests.post(HASURA_URL, headers=HEADERS, json=query)
    data = response.json()

    if "errors" in data:
        print("❌ Error al obtener registros de fermentación:", data["errors"])
        return []

    return data["data"]["Registro_Fermentacion"]

def get_detalles_por_fermentacion(id_registro_fermentacion):
    query = {
        "query": """
        query ($id: Int!) {
          Registro_detalle(
            where: {id_registro_fermentacion: {_eq: $id}},
            order_by: {fechaHoraRegistroDetalle: asc}
          ) {
            fechaHoraRegistroDetalle
            temperaturaByIdTemperaturaTempeh {
              temp
            }
            temperaturaByIdTemperaturaAmbiente {
              temp
            }
            Humedad {
              humed
            }
            AireAcondicionadoTemperatura {
              Temperatura {
                temp
              }
            }
            EstufaTemperatura {
              Temperatura {
                temp
              }
            }
            Alarma {
              nombreAlarma
            }
          }
        }
        """,
        "variables": {"id": id_registro_fermentacion}
    }

    response = requests.post(HASURA_URL, headers=HEADERS, json=query)
    data = response.json()

    if "errors" in data:
        print(f"❌ Error al obtener detalles para ID {id_registro_fermentacion}:", data["errors"])
        return []

    return data["data"]["Registro_detalle"]

if __name__ == "__main__":
    print("🔄 URL cargada:", HASURA_URL)
    print("🔐 Secreto cargado:", "Sí" if HASURA_SECRET else "No")

    hongo_id = get_hongo_id("tempeh")
    if not hongo_id:
        exit()

    print(f"\n🔵 ID del hongo 'tempeh': {hongo_id}\n")

    registros = get_registros_fermentacion(hongo_id)

    procesos_historicos = {}

    for r in registros:
        id_f = r["id_registro_fermentacion"]
        print(f"\n🌱 Proceso de Fermentación ID: {id_f}")
        detalles = get_detalles_por_fermentacion(id_f)

        if not detalles:
            print("⚠️ Sin datos de detalle para este proceso.")
            continue

        tabla = []
        for d in detalles:
            fila = {
                "fecha": d['fechaHoraRegistroDetalle'],
                "temp_tempeh": float(d['temperaturaByIdTemperaturaTempeh']['temp']) if d['temperaturaByIdTemperaturaTempeh'] else None,
                "temp_ambiente": float(d['temperaturaByIdTemperaturaAmbiente']['temp']) if d['temperaturaByIdTemperaturaAmbiente'] else None,
                "humedad": float(d['Humedad']['humed']) if d['Humedad'] else None,
                "aire": float(d['AireAcondicionadoTemperatura']['Temperatura']['temp']) if d['AireAcondicionadoTemperatura'] and d['AireAcondicionadoTemperatura']['Temperatura'] else None,
                "estufa": float(d['EstufaTemperatura']['Temperatura']['temp']) if d['EstufaTemperatura'] and d['EstufaTemperatura']['Temperatura'] else None,
                "alarma": d['Alarma']['nombreAlarma'] if d['Alarma'] else "Sin alarma"
            }
            tabla.append(fila)

        df = pd.DataFrame(tabla)
        procesos_historicos[id_f] = df
        print(df.to_string(index=True))
