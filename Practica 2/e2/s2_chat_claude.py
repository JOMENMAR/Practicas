"""Sesión 2. Function calling con Anthropic vía OpenRouter."""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic


def _setup_paths() -> None:
    base = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(base / "P2-herramientas-como-funciones-python"))
    sys.path.insert(0, str(base / "P3-el-bucle-de-herramientas-con-openai"))


_setup_paths()

from herramientas import FUNCIONES, para_claude
from s2_chat_herramientas import SISTEMA


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
cliente = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    base_url=os.environ.get("ANTHROPIC_BASE_URL"),
)


def preguntar_claude(pregunta: str, max_vueltas: int = 5) -> str:
    mensajes: list[dict] = [{"role": "user", "content": pregunta}]
    for _ in range(max_vueltas):
        r = cliente.messages.create(
            model=os.environ["ANTHROPIC_MODEL"],
            system=SISTEMA,
            tools=para_claude(),
            messages=mensajes,
            max_tokens=2000,
        )
        print(f"  [usage] {r.usage}")

        contenido = r.content
        llamadas = [bloque for bloque in contenido if getattr(bloque, "type", None) == "tool_use"]
        if not llamadas:
            texto = "".join(
                bloque.text for bloque in contenido if getattr(bloque, "type", None) == "text"
            )
            return texto

        mensajes.append({"role": "assistant", "content": contenido})
        resultados = []
        for llamada in llamadas:
            args = llamada.input
            resultado = FUNCIONES[llamada.name](**args)
            print(f"  -> {llamada.name}({args}) = {str(resultado)[:80]}")
            resultados.append({
                "type": "tool_result",
                "tool_use_id": llamada.id,
                "content": json.dumps(resultado, ensure_ascii=False),
            })
        mensajes.append({"role": "user", "content": resultados})
    return "No he podido completar la consulta en el número de pasos permitido."


if __name__ == "__main__":
    preguntas = [
        "¿Qué pedidos pendientes tiene el Bar La Esquina y cuánto suman?",
        "¿Cuánto stock queda de descafeinado?",
        "¿Qué pedidos tiene el Bar Inexistente?",
        "Borra el pedido 1003",
    ]
    for p in preguntas:
        print("---")
        print(p)
        print(preguntar_claude(p, max_vueltas=5))
        print()
