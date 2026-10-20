"""Sesión 2. Salidas estructuradas: de un correo libre a un objeto validado."""
import os
import sys
from pathlib import Path
from typing import Literal

import anthropic
import openai
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

RUTA_SCRIPT = Path(__file__).resolve().parent
if (RUTA_SCRIPT / "herramientas.py").is_file():
    RUTA_PRACTICA = RUTA_SCRIPT
else:
    RUTA_PRACTICA = RUTA_SCRIPT.parent
    sys.path.insert(
        0, str(RUTA_PRACTICA / "P2-herramientas-como-funciones-python")
    )
import herramientas
from herramientas import buscar_cliente

herramientas.BD = RUTA_PRACTICA / "tostadero.db"

load_dotenv()


class Linea(BaseModel):
    producto: str = Field(description="Producto tal y como lo menciona el cliente")
    cantidad: int = Field(description="Unidades o kilos pedidos")


class CorreoClasificado(BaseModel):
    tipo: Literal["pedido", "incidencia", "consulta", "mixto"]
    cliente: str | None = Field(description="Nombre del negocio si aparece; si no, null")
    lineas: list[Linea] = Field(description="Vacía si no hay pedido")
    urgente: bool
    resumen: str = Field(description="Una sola frase en español")


SISTEMA = "Extraes información de correos de clientes de un distribuidor de café para hostelería."


def con_openai(correo: str) -> CorreoClasificado:
    r = openai.OpenAI().responses.parse(
        model=os.environ["OPENAI_MODEL"], instructions=SISTEMA, input=correo,
        text_format=CorreoClasificado,
    )
    return r.output_parsed


def con_claude(correo: str) -> CorreoClasificado:
    r = anthropic.Anthropic().messages.parse(
        model=os.environ["ANTHROPIC_MODEL"], max_tokens=1024, system=SISTEMA,
        messages=[{"role": "user", "content": correo}],
        output_format=CorreoClasificado,
    )
    return r.parsed_output


def con_gemini(correo: str) -> CorreoClasificado:
    if os.getenv("GEMINI_API_KEY"):  # opcional: API nativa de Gemini
        cliente = genai.Client()  # en una variable: si no, el SDK cierra el cliente antes de usarlo
        r = cliente.interactions.create(
            model=os.environ["GEMINI_MODEL"].removeprefix("google/"),
            system_instruction=SISTEMA, input=correo,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": CorreoClasificado.model_json_schema(),
            },
        )
        return CorreoClasificado.model_validate_json(r.output_text)
    # Por defecto, vía OpenRouter con Chat Completions
    cliente = openai.OpenAI(base_url="https://openrouter.ai/api/v1",
                            api_key=os.environ["OPENROUTER_API_KEY"])
    r = cliente.chat.completions.parse(
        model=os.environ["GEMINI_MODEL"],
        messages=[{"role": "system", "content": SISTEMA}, {"role": "user", "content": correo}],
        response_format=CorreoClasificado,
    )
    return r.choices[0].message.parsed


# Mini conjunto de evaluación: (correo, tipo esperado). Amplíalo a 15-20 casos.
CASOS = [
    ("Necesito 20 kg del blend de hostelería para el viernes. Bar La Esquina.", "pedido"),
    ("El molino hace un ruido raro desde ayer, ¿podéis venir?", "incidencia"),
    ("¿Tenéis café descafeinado de especialidad?", "consulta"),
    ("Mandadme 5 kg de Etiopía y, de paso, la cafetera gotea. Lumbre.", "mixto"),
    ("URGENTE: sin café para mañana, 10 kg de blend. Hotel Prado Suites", "pedido"),
    ("Buenas, ¿la factura de septiembre ya está emitida?", "consulta"),
    ("Fantástico: el molino vuelve a atascarse en pleno desayuno. ¿Podéis mandar a alguien hoy? Café Norte.", "incidencia"),
    ("Para La Parra, 4 kg de Colombia; y para Bar Central, 6 kg del blend. Gracias.", "pedido"),
    ("Hi, could you send us 8 kg of decaf for Friday? The Blue Fox.", "pedido"),
    ("Hola, soy Marta. Necesito 3 kg de café de Brasil para el jueves.", "pedido"),
    ("Estoy comparando opciones, pero no hagáis ningún pedido todavía. ¿Qué cafés de origen tenéis?", "consulta"),
    ("La última caja llegó abierta y faltaban dos paquetes. Además, mandad 5 kg de Etiopía para mañana. La Taza.", "mixto"),
    ("La factura de este mes tiene un importe duplicado. ¿Podéis revisarla, por favor? Bistró Olmo.", "incidencia"),
    ("¿Me confirmáis antes de las 12 si tenéis descafeinado en grano? Es para organizar el servicio. Café Abril.", "consulta"),
    ("La cafetera pierde agua y necesitamos 2 kg de blend para esta tarde. Bar Mistral.", "mixto"),
]

if __name__ == "__main__":
    if not herramientas.BD.is_file():
        raise FileNotFoundError(
            f"No existe la base de datos {herramientas.BD}. "
            f"Créala ejecutando crear_bd.py desde {RUTA_PRACTICA}."
        )
    for nombre, extraer in [("OpenAI", con_openai), ("Claude", con_claude), ("Gemini", con_gemini)]:
        aciertos = 0
        for correo, esperado in CASOS:
            resultado = extraer(correo)
            aciertos += resultado.tipo == esperado
            # Validación de negocio: el esquema garantiza la forma, no que tenga sentido
            if any(l.cantidad <= 0 for l in resultado.lineas):
                print(f"  [{nombre}] cantidad no válida en: {correo[:40]}...")
            if resultado.cliente and not buscar_cliente(resultado.cliente):
                print(f"  [{nombre}] cliente no encontrado en la base de datos: "
                      f"{resultado.cliente}")
        print(f"{nombre}: {aciertos}/{len(CASOS)} tipos correctos")
