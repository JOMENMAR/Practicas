"""Versión didáctica del agente de la práctica, construida paso a paso."""

import json
import os
from dataclasses import dataclass
from typing import Callable

import anthropic
from dotenv import load_dotenv

from herramientas import DEFINICIONES, FUNCIONES

# Carga en el entorno las variables definidas en el archivo .env.
load_dotenv()


@dataclass
class Herramienta:
    """Describe una herramienta que el agente podrá ofrecer al modelo."""

    nombre: str
    descripcion: str
    esquema: dict
    funcion: Callable
    requiere_aprobacion: bool = False


class Agente:
    """Guarda la configuración que se usará después para ejecutar el agente."""

    def __init__(
        self,
        sistema: str,
        herramientas: list[Herramienta],
        max_pasos: int = 8,
    ):
        # El cliente se conecta con Claude usando la configuración del entorno.
        self.llm = anthropic.Anthropic()

        # Se configura el modelo fuera del código para poder cambiarlo sin editarlo.
        self.modelo = os.environ["ANTHROPIC_MODEL"]

        # Se guardan las instrucciones y el límite para utilizarlos durante la ejecución.
        self.sistema = sistema
        self.max_pasos = max_pasos

        # El nombre de cada herramienta será la clave para encontrarla rápidamente.
        self.herramientas = {herramienta.nombre: herramienta for herramienta in herramientas}
        self.acciones_rechazadas: set[str] = set()

    def _definiciones(self) -> list[dict]:
        """Prepara las herramientas en el formato que Claude espera en su API."""
        return [
            {
                "name": herramienta.nombre,
                "description": herramienta.descripcion,
                "input_schema": herramienta.esquema,
            }
            for herramienta in self.herramientas.values()
        ]

    def _ejecutar(self, nombre: str, args: dict) -> tuple[object, bool, bool]:
        """Devuelve el resultado, si hubo un error y si la persona rechazó la acción."""
        herramienta = self.herramientas.get(nombre)
        if herramienta is None:
            return f"La herramienta {nombre} no existe.", True, False

        try:
            if nombre == "crear_incidencia":
                catalogo = self.herramientas.get("stock_producto")
                if catalogo is None:
                    return {
                        "estado": "error",
                        "mensaje": "No se pudo validar la máquina en el catálogo; no se registró la incidencia.",
                    }, True, False

                maquina = args.get("maquina", "")
                productos = catalogo.funcion(texto=maquina)
                if not any(
                    isinstance(producto, dict) and producto.get("sku") == maquina
                    for producto in productos
                ):
                    return {
                        "estado": "error",
                        "mensaje": (
                            f"El código {maquina!r} no aparece en el catálogo; "
                            "no se registró la incidencia."
                        ),
                    }, True, False

            if nombre in self.acciones_rechazadas:
                return {
                    "estado": "rechazada",
                    "mensaje": "Acción no ejecutada: el operador ya rechazó esta acción.",
                }, False, True

            if herramienta.requiere_aprobacion:
                aprobada = input(
                    f"  ¿Aprobar {nombre}({args})? [s/N] "
                ).strip().lower() == "s"
                if not aprobada:
                    self.acciones_rechazadas.add(nombre)
                    return {
                        "estado": "rechazada",
                        "mensaje": (
                            "Acción no ejecutada: el operador rechazó la aprobación. "
                            "No fue un error técnico."
                        ),
                    }, False, True

            return herramienta.funcion(**args), False, False
        except Exception as error:
            return f"Error al ejecutar {nombre}: {error}", True, False

    def ejecutar(self, objetivo: str) -> str:
        """Pide al modelo resolver el objetivo, ejecutando herramientas cuando las solicite."""
        # La conversación empieza con el objetivo del usuario.
        mensajes: list = [{"role": "user", "content": objetivo}]
        self.acciones_rechazadas.clear()
        resultados_confirmados = []

        # Cada iteración es un paso del agente; max_pasos limita el ciclo.
        for paso in range(1, self.max_pasos + 1):
            respuesta = self.llm.messages.create(
                model=self.modelo,
                max_tokens=2048,
                system=self.sistema,
                tools=self._definiciones(),
                messages=mensajes,
            )

            # Se guarda la respuesta de Claude para mantener el contexto de la conversación.
            mensajes.append({"role": "assistant", "content": respuesta.content})

            # Si Claude no pidió herramientas, su texto es la respuesta final.
            if respuesta.stop_reason != "tool_use":
                if self.acciones_rechazadas:
                    return (
                        "No se registró la incidencia: el operador rechazó la aprobación. "
                        "No fue un error técnico. "
                        "Resultados de otras herramientas: "
                        f"{json.dumps(resultados_confirmados, ensure_ascii=False, default=str)}"
                    )
                return "".join(
                    bloque.text for bloque in respuesta.content if bloque.type == "text"
                )

            resultados = []
            for bloque in respuesta.content:
                if bloque.type == "text" and bloque.text.strip():
                    print(f"[paso {paso}] texto: {bloque.text.strip()[:100]}")

                if bloque.type != "tool_use":
                    continue

                # Ejecuta la función Python correspondiente a la solicitud de Claude.
                salida, es_error, rechazada = self._ejecutar(bloque.name, bloque.input)
                print(f"[paso {paso}] {bloque.name}({bloque.input}) -> {str(salida)[:90]}")
                if rechazada:
                    self.acciones_rechazadas.add(bloque.name)
                elif not es_error:
                    resultados_confirmados.append({"herramienta": bloque.name, "resultado": salida})

                # Claude necesita el id de la llamada para asociarle el resultado correcto.
                resultados.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": bloque.id,
                        "is_error": es_error,
                        "content": json.dumps(salida, ensure_ascii=False, default=str),
                    }
                )

            # Se devuelven los resultados al modelo para que decida qué hacer a continuación.
            mensajes.append({"role": "user", "content": resultados})

        # Si se alcanza el límite, se detiene el ciclo y se deriva el caso a una persona.
        if self.acciones_rechazadas:
            return (
                "No se registró la incidencia: el operador rechazó la aprobación. "
                "No fue un error técnico. "
                "Resultados de otras herramientas: "
                f"{json.dumps(resultados_confirmados, ensure_ascii=False, default=str)}"
            )
        return "He alcanzado el límite de pasos sin terminar. Paso el caso a una persona."


SISTEMA = """Eres el agente de atención técnica de Tostadero Retiro S.L.
Objetivo: resolver correos de clientes usando las herramientas.
Procedimiento:
1. Identifica al cliente con buscar_cliente antes de usar su id.
2. Si hay una avería de una máquina, consulta stock_producto para verificar su SKU exacto.
   La búsqueda es por texto literal: empieza con un término corto del modelo, como "espresso",
   y si no hay resultados prueba otro término corto relevante. No inventes códigos.
   Si el catálogo sigue sin identificar la máquina, no registres la incidencia y explica
   que necesitas confirmar el modelo.
3. Registra una incidencia con la prioridad adecuada (alta si el local no puede servir café).
   La herramienta comprobará el SKU y pedirá aprobación antes de guardarla.
4. Si el resultado indica que la acción fue rechazada, di claramente que no se registró;
   no lo describas como un error técnico ni vuelvas a intentarlo.
5. Si preguntan por pedidos, consulta los datos reales; no inventes cifras.
6. Termina con una respuesta breve al cliente, en español y con tono cordial."""


if __name__ == "__main__":
    # Las definiciones describen las herramientas al modelo; FUNCIONES aporta las funciones Python.
    herramientas = [
        Herramienta(
            definicion["name"],
            definicion["description"],
            definicion["parameters"],
            FUNCIONES[definicion["name"]],
            requiere_aprobacion=(definicion["name"] == "crear_incidencia"),
        )
        for definicion in DEFINICIONES
    ]

    agente = Agente(SISTEMA, herramientas)
    correo = (
        "Buenas, os escribo del Restaurante Lumbre. La cafetera de dos grupos no "
        "calienta y hoy no podemos servir cafés. ¿Además, cuándo llega el pedido pendiente?"
    )
    print(agente.ejecutar(correo))
