# Análisis comparativo

## 1. Puntuación de calidad (1 a 5)

He puntuado cada respuesta atendiendo a su utilidad, claridad y prudencia: 5 indica una respuesta útil y bien calibrada; 3, una respuesta aprovechable pero con una suposición u omisión importante; 1, una respuesta que no resuelve la consulta. Las notas están en `calidad_1a5` del CSV. Como el ejercicio no aporta datos reales de entregas, facturas ni catálogo, resto puntos cuando una respuesta presenta esos detalles como hechos.

## 2. ¿Por qué un modelo gasta más tokens para respuestas igual de cortas?

Los proveedores usan tokenizadores y formatos de entrada distintos, por lo que no cuentan igual el mismo texto. Además, `tokens_salida` es el uso que informa la API, no un recuento de las palabras visibles: puede incluir tokens internos de razonamiento además de la respuesta final. Se ve especialmente en Gemini: en esta muestra, sus respuestas visibles son breves, pero la tabla registra entre 437 y 555 tokens de salida. Por eso no se debe comparar la longitud visible como si fuera el uso total de tokens.

## 3. ¿Qué modelo elegiría para 2.000 correos al mes?

Con los cinco correos de la muestra, elegiría **OpenAI** como opción inicial:

| Proveedor | Latencia media | Coste medio por correo | Estimación para 2.000 correos/mes | Calidad media |
|---|---:|---:|---:|---:|
| OpenAI | 1,19 s | $0,0002754 | **$0,55/mes** | 3,6/5 |
| Claude | 1,79 s | $0,0004500 | $0,90/mes | 3,6/5 |
| Gemini | 5,05 s | $0,0020866 | $4,17/mes | 2,0/5 |

OpenAI y Claude empatan en calidad media en esta valoración, pero OpenAI fue más rápido en promedio y cuesta menos: aproximadamente un 39 % menos que Claude y un 87 % menos que Gemini para el volumen estimado. Gemini es claramente más lento y caro en estos datos, sin una mejora de calidad que lo compense. Antes de desplegar cualquier proveedor, probaría más correos y evitaría que el asistente confirme entregas, reparaciones o datos de facturación que no puede verificar.

La estimación multiplica el coste medio de los cinco correos por 2.000. Usa los costes calculados en el CSV y los precios configurados en `llm_client.py`; no contempla reintentos ni cambios en tarifas. Las latencias y puntuaciones proceden de una muestra pequeña y no garantizan el rendimiento futuro.
