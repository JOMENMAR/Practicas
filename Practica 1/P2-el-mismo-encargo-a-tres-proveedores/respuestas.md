# P2. Respuestas a las preguntas

Ejecuté `s1_hola_tres.py` dos veces. Los tiempos y tokens observados fueron:

| Ejecución | Proveedor | Segundos | Tokens de entrada/salida |
|---|---|---:|---:|
| 1 | OpenAI | 2,78 | 93/52 |
| 1 | Claude | 2,64 | 131/76 |
| 1 | Gemini | 14,72 | 85/758 |
| 2 | OpenAI | 2,24 | 93/44 |
| 2 | Claude | 2,01 | 131/85 |
| 2 | Gemini | 6,80 | 85/568 |

## ¿Qué proveedor responde antes? ¿La diferencia se mantiene?

Claude fue el más rápido en las dos ejecuciones (2,64 s y 2,01 s). El orden de rapidez se mantuvo, pero no los tiempos: todos variaron, y Gemini pasó de 14,72 s a 6,80 s. Son solo dos medidas, así que no bastan para establecer latencias estables.

## ¿Por qué no coinciden los tokens de entrada para el mismo texto?

Cada proveedor emplea un tokenizador y una representación de la petición distintos. El mismo correo y las mismas instrucciones no tienen por qué producir el mismo número de tokens; en estas ejecuciones OpenAI contó 93, Claude 131 y Gemini 85 tokens de entrada.

## El correo es mixto: ¿lo clasifican bien los tres?

Sí. En ambas respuestas los tres lo clasificaron como mixto: incluye la incidencia de la cafetera y la consulta sobre el pedido pendiente.

## ¿Cambia la redacción entre la primera y la segunda ejecución?

Sí. Cambiaron las palabras y la estructura de las tres respuestas, aunque mantuvieron la clasificación. En la primera ejecución Claude prometió una llamada en una hora y Gemini dijo que ya había avisado al servicio técnico; en la segunda cambiaron esos detalles. No conviene presentar como hechos confirmados una entrega, una llamada o una visita técnica si el sistema no tiene acceso para verificarlas o gestionarlas.
