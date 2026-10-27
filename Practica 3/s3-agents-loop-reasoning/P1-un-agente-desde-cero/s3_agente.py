"""Sesión 3. Un agente desde cero: bucle, límite de pasos, trazas y aprobación humana.

Proveedor: Claude (Messages API). El patrón es idéntico con OpenAI o Gemini."""
import json
import os
from dataclasses import dataclass
from typing import Callable

import anthropic
from dotenv import load_dotenv

from herramientas import DEFINICIONES, FUNCIONES

load_dotenv()


@dataclass
class Herramienta:
    """Agrupa la información que el agente necesita para ofrecer y ejecutar una herramienta."""

    # El nombre debe coincidir con el que recibirá el modelo cuando solicite la herramienta.
    nombre: str
    # El modelo lee esta descripción para decidir cuándo le conviene usarla.
    descripcion: str
    # Esquema JSON que indica al modelo los argumentos esperados y sus tipos.
    esquema: dict
    # Función Python real que se ejecuta al aceptar la llamada del modelo.
    funcion: Callable
    # Las acciones con efectos importantes pueden requerir confirmación de una persona.
    requiere_aprobacion: bool = False


class Agente:
    """Coordina el modelo, las herramientas y el ciclo de ejecución del agente."""

    def __init__(self, sistema: str, herramientas: list[Herramienta], max_pasos: int = 8):
        # El cliente usa la clave de API configurada en el entorno.
        self.llm = anthropic.Anthropic()
        # El nombre del modelo se configura fuera del código, en la variable de entorno.
        self.modelo = os.environ["ANTHROPIC_MODEL"]
        # El mensaje de sistema define el rol y las reglas; max_pasos evita un bucle infinito.
        self.sistema, self.max_pasos = sistema, max_pasos
        # Un diccionario permite encontrar rápidamente una herramienta por su nombre.
        self.herramientas = {h.nombre: h for h in herramientas}

    def _definiciones(self) -> list[dict]:
        """Convierte las herramientas al formato que espera la API de Claude."""
        return [{"name": h.nombre, "description": h.descripcion, "input_schema": h.esquema}
                for h in self.herramientas.values()]

    def _ejecutar(self, nombre: str, args: dict) -> tuple[object, bool]:
        """Ejecuta una herramienta y devuelve (resultado, es_error).

        El indicador de error permite devolver fallos al modelo como resultados de herramienta,
        para que pueda corregir los argumentos o explicar que no pudo completar la acción.
        """
        # El nombre viene de la respuesta del modelo; se comprueba antes de buscar la función.
        h = self.herramientas.get(nombre)
        if h is None:
            return f"La herramienta {nombre} no existe.", True
        # Se pide autorización antes de ejecutar acciones marcadas como sensibles.
        if h.requiere_aprobacion:
            if input(f"  ¿Aprobar {nombre}({args})? [s/N] ").strip().lower() != "s":
                return "Un operador humano ha rechazado esta acción. No la repitas.", True
        # Los argumentos proceden del modelo y la función puede fallar; el error se devuelve
        # como dato al modelo en vez de interrumpir todo el ciclo.
        try:
            return h.funcion(**args), False
        except Exception as e:  # argumentos inventados, fallo de BD...
            return f"Error al ejecutar {nombre}: {e}", True

    def ejecutar(self, objetivo: str) -> str:
        """Resuelve un objetivo conversando con el modelo y ejecutando sus llamadas a herramientas."""
        # Messages API espera una lista de mensajes con roles; el objetivo inicia la conversación.
        mensajes: list = [{"role": "user", "content": objetivo}]
        # Cada vuelta permite al modelo responder o solicitar herramientas; el límite evita
        # que llamadas repetidas consuman recursos indefinidamente.
        for paso in range(1, self.max_pasos + 1):
            r = self.llm.messages.create(
                model=self.modelo,  # Modelo de Claude elegido mediante configuración.
                max_tokens=2048,  # Máximo de tokens que puede generar en esta respuesta.
                system=self.sistema,  # Instrucciones permanentes del agente.
                tools=self._definiciones(),  # Herramientas disponibles y sus esquemas.
                messages=mensajes,  # Historial necesario para que el modelo tenga contexto.
            )
            # Se conserva la respuesta completa: Claude puede devolver texto, llamadas a
            # herramientas o una combinación de ambos.
            mensajes.append({"role": "assistant", "content": r.content})
            # Si Claude no se detuvo para pedir una herramienta, se considera respuesta final.
            if r.stop_reason != "tool_use":
                return "".join(b.text for b in r.content if b.type == "text")
            resultados = []
            for bloque in r.content:
                # Puede haber texto explicativo junto a las llamadas a herramientas.
                if bloque.type == "text" and bloque.text.strip():
                    print(f"[paso {paso}] razonamiento visible: {bloque.text.strip()[:100]}")
                if bloque.type != "tool_use":
                    continue
                # Ejecuta la función local solicitada y registra la llamada para mostrar la traza.
                salida, es_error = self._ejecutar(bloque.name, bloque.input)
                print(f"[paso {paso}] {bloque.name}({bloque.input}) -> {str(salida)[:90]}")
                resultados.append({
                    "type": "tool_result",  # Tipo de bloque requerido por Messages API.
                    "tool_use_id": bloque.id,  # Vincula el resultado con la llamada concreta.
                    "is_error": es_error,  # Informa a Claude si la ejecución falló.
                    # El resultado se serializa porque la API espera contenido textual;
                    # default=str permite representar objetos no serializables directamente.
                    "content": json.dumps(salida, ensure_ascii=False, default=str),
                })
            # Los resultados se envían como mensaje de usuario para que Claude los procese
            # en la siguiente vuelta y decida si necesita otra herramienta o ya puede responder.
            mensajes.append({"role": "user", "content": resultados})
        # Si se agotan las vueltas, se deriva a una persona en vez de seguir indefinidamente.
        return "He alcanzado el límite de pasos sin terminar. Paso el caso a una persona."


# Estas instrucciones guían las decisiones del modelo y limitan cómo debe atender el correo.
SISTEMA = """Eres el agente de atención técnica de Tostadero Retiro S.L.
Objetivo: resolver correos de clientes usando las herramientas.
Procedimiento:
1. Identifica al cliente con buscar_cliente antes de usar su id.
2. Si hay una avería, registra una incidencia con la prioridad adecuada
   (alta si el local no puede servir café).
3. Si preguntan por pedidos, consulta los datos reales; no inventes cifras.
4. Termina con una respuesta breve al cliente, en español y con tono cordial."""

if __name__ == "__main__":
    # Las definiciones (para el modelo) y las funciones (para Python) se emparejan por nombre.
    herramientas = [
        Herramienta(d["name"], d["description"], d["parameters"], FUNCIONES[d["name"]],
                    # Crear incidencias modifica datos, así que requiere aprobación humana.
                    requiere_aprobacion=(d["name"] == "crear_incidencia"))
        for d in DEFINICIONES
    ]
    # Se crea el agente con las instrucciones anteriores y el conjunto de herramientas.
    agente = Agente(SISTEMA, herramientas)
    # Ejemplo de correo que se entrega como objetivo al agente.
    correo = ("Buenas, os escribo del Restaurante Lumbre. La cafetera de dos grupos no "
              "calienta y hoy no podemos servir cafés. ¿Además, cuándo llega el pedido pendiente?")
    # Inicia el bucle y muestra la respuesta final del agente.
    print(agente.ejecutar(correo))
