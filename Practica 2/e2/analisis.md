# Análisis de P3: bucle de herramientas con OpenAI

## 1) ¿Qué pedidos pendientes tiene el Bar La Esquina y cuánto suman?

Secuencia de llamadas:

1. `buscar_cliente({"texto": "Bar La Esquina"})`
   - Resultado: `[{'id': 1, 'nombre': 'Bar La Esquina', 'tipo': 'bar', 'distrito': 'Retiro'}]`
2. `consultar_pedidos({"cliente_id": 1})`
   - Resultado: lista de pedidos del cliente 1, entre ellos el 1004 en estado `pendiente` con total `98.0`

Respuesta final del asistente:

> Bar La Esquina tiene 1 pedido pendiente:
>
> - Pedido 1004 — fecha: 2026-09-30 — total: 98,00 €
>
> Total pendiente: 98,00 €

Observación: el modelo encadena dos herramientas para localizar el cliente y luego consultar sus pedidos. El total se calcula sumando los pedidos pendientes.

## 2) ¿Cuánto stock queda de descafeinado?

Secuencia de llamadas:

1. `stock_producto({"texto": "descafeinado"})`
   - Resultado: `[{'sku': 'CAF-003', 'nombre': 'Café descafeinado 1 kg', 'precio': 19.8, 'stock': 45}]`

Respuesta final del asistente:

> Quedan 45 unidades de Café descafeinado 1 kg (SKU CAF-003).

Observación: una sola llamada basta porque el producto se identifica directamente por nombre/SKU.

## 3) ¿Qué pedidos tiene el Bar Inexistente?

Secuencia de llamadas:

1. `buscar_cliente({"texto": "Bar Inexistente"})`
   - Resultado: `[]`

Respuesta final del asistente:

> No he encontrado ningún cliente llamado "Bar Inexistente" en el sistema, así que no puedo consultar sus pedidos.

Observación: cuando la búsqueda devuelve vacío, el asistente no intenta otra herramienta y responde con una respuesta de “no encontrado” clara y sin inventar datos.

## 4) Borra el pedido 1003

Secuencia de llamadas:

- No se llama a ninguna herramienta.

Respuesta final del asistente:

> No puedo borrar pedidos con las herramientas disponibles. Si quieres, puedo ayudarte a consultar los pedidos del cliente asociado al pedido 1003 para revisar alternativas.

Observación: como no existe una función `borrar_pedido`, el modelo responde de forma segura diciendo que no puede hacerlo con las herramientas disponibles. No intenta inventar una operación que no existe.

## Conclusión

El patrón del bucle es el siguiente:

1. El modelo decide qué herramienta usar.
2. Nuestro código ejecuta la función real sobre la base de datos.
3. El resultado vuelve al modelo como salida de función.
4. El modelo interpreta ese resultado y genera la respuesta final.

Los casos más útiles son los encadenados (cliente → pedidos) y los vacíos (cliente no encontrado), porque muestran cómo se gestiona la lectura de datos reales y cómo se evita inventar información.

# P4. Comparación entre OpenAI y Claude

Se ejecutó el mismo bucle con los cuatro prompts de P3 usando `s2_chat_herramientas.py` y `s2_chat_claude.py`. La tabla siguiente resume número de llamadas, tokens y calidad de la respuesta final.

| Pregunta | OpenAI llamadas | OpenAI input/output | Claude llamadas | Claude input/output | Calidad |
|---|---:|---:|---:|---:|---|
| ¿Qué pedidos pendientes tiene el Bar La Esquina y cuánto suman? | 2 | 1056 / 99 | 2 | 3497 / 231 | Correcta y precisa |
| ¿Cuánto stock queda de descafeinado? | 1 | 603 / 49 | 1 | 2153 / 105 | Correcta |
| ¿Qué pedidos tiene el Bar Inexistente? | 1 | 567 / 63 | 1 | 2139 / 145 | Correcta: responde que no existe |
| Borra el pedido 1003 | 0 | 263 / 58 | 0 | 1015 / 133 | Correcta y segura: no hay herramienta de borrado |

Conclusión de la comparación:

- Ambos proveedores usan el mismo patrón de llamadas a herramientas y toman la misma decisión de negocio.
- OpenAI usa menos tokens en todas las consultas y responde con una longitud más compacta.
- Claude produce respuestas más verbosas, pero igualmente correctas y seguras.
- En las cuatro preguntas la calidad final es buena en ambos modelos, y la diferencia principal está en el consumo de tokens y el estilo de respuesta.

Se adjunta además la implementación del bucle para Claude en `e2/s2_chat_claude.py`.
