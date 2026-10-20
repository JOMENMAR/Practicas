"""Sesión 1. Comparativa de proveedores sobre los mismos correos (genera comparativa.csv)."""
import csv
import sys
from pathlib import Path

try:
    from llm_client import LLM
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "P3-una-interfaz-comun"))
    from llm_client import LLM

SISTEMA = ("Eres el asistente de atención al cliente de Tostadero Retiro S.L. "
           "Responde en español y en dos frases como máximo.")
CORREOS = [
    "¿Hacéis entregas los sábados en Chamberí?",
    "La cafetera gotea por el grupo 1 desde esta mañana.",
    "Quiero 15 kg de blend y dos cajas de vasos para el jueves.",
    "¿Por qué la factura de septiembre es más alta que la de agosto?",
    "Somos un hotel nuevo en Centro: ¿qué café nos recomendáis para el desayuno?",
]

with open("comparativa.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["proveedor", "correo", "segundos", "tokens_entrada", "tokens_salida",
               "coste_usd", "calidad_1a5", "respuesta"])
    for proveedor in ["openai", "claude", "gemini"]:
        llm = LLM(proveedor)
        for correo in CORREOS:
           respuesta = llm.responder(SISTEMA, correo)
           w.writerow([
               proveedor,
               correo,
               f"{respuesta.segundos:.2f}",
               respuesta.tokens_entrada,
               respuesta.tokens_salida,
               respuesta.coste_usd,
               "",
               respuesta.texto,
           ])
           print(f"{proveedor:7} | {correo[:42]:42} | {respuesta.segundos:5.2f}s | "
                 f"{respuesta.tokens_entrada}/{respuesta.tokens_salida} tok")

print("Hecho: abre comparativa.csv y puntúa la columna calidad_1a5 en equipo.")
