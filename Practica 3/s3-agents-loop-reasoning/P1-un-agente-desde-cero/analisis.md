# Análisis de P1: un agente desde cero

## Objetivo

Construir y probar un agente de atención técnica que use Claude y herramientas Python para
identificar clientes, consultar pedidos y productos, y registrar incidencias con aprobación humana.
El trabajo se hizo de forma incremental en `s3_agente_paso_a_paso.py`, conservando sin cambios
el script original `s3_agente.py`.

## Qué hemos construido

La versión didáctica reúne estas piezas:

- `Herramienta` guarda el nombre, la descripción, el esquema de argumentos, la función Python y
  si requiere aprobación humana.
- `Agente.__init__` prepara el cliente de Anthropic, el modelo configurado en el entorno, las
  instrucciones del sistema, el límite de pasos y el diccionario de herramientas.
- `_definiciones()` traduce las herramientas al formato Messages API de Claude.
- `_ejecutar()` valida y ejecuta las llamadas a las herramientas. Para crear una incidencia,
  comprueba primero que el SKU exista en el catálogo y pide aprobación antes de escribir en la BD.
- `ejecutar()` mantiene el historial, llama al modelo, procesa las llamadas de herramientas y
  devuelve sus resultados al modelo, con un límite para evitar un ciclo indefinido.

## Pruebas y aprendizajes

### Preparación y primera ejecución

Se creó la base de datos de ejemplo en `P2-experimentos-con-el-agente/tostadero.db`. La primera
consulta real identificó a Restaurante Lumbre y recuperó el pedido 1003, fechado el 28 de
septiembre de 2026, con estado `pendiente` e importe de 496,40 €.

### Rechazo de una acción y respuestas incorrectas del modelo

En las primeras ejecuciones, Claude propuso códigos de máquina que no estaban en el catálogo
(`MAQ-001` y `MAQ-002`). Aunque el operador rechazó la creación de la incidencia, el modelo llegó
a afirmar que se había registrado o atribuyó el rechazo a un error técnico. Esto mostró que la
aprobación por sí sola no garantiza que la respuesta final sea fiel a lo ocurrido.

Se actualizó únicamente `s3_agente_paso_a_paso.py` para:

1. Verificar el SKU exacto contra `stock_producto` antes de permitir crear una incidencia.
2. No pedir aprobación ni guardar la incidencia cuando el código no existe en el catálogo.
3. Distinguir un rechazo humano de un error técnico.
4. Devolver una respuesta determinista después de un rechazo, indicando que la incidencia no se
   registró, sin dejar que el texto final del modelo contradiga ese resultado.
5. Instruir al modelo para que pruebe términos de búsqueda cortos y no invente códigos.

Las pruebas locales confirmaron que un SKU desconocido se bloquea y que un rechazo no puede
producir una respuesta de éxito. También se hizo una ejecución real que encontró `MAQ-010` y,
tras responder `N`, confirmó que no se guardaba la incidencia.

### Aprobación de una incidencia

En otra ejecución se comprobó el camino de aprobación: la herramienta encontró la cafetera
espresso de dos grupos con SKU `MAQ-010`, solicitó confirmación y el operador respondió `s`.
La base de datos confirmó la creación de la incidencia número 3, con prioridad `alta` y estado
`abierta`. La creación fue una escritura real autorizada por el operador.

## Resultado y limitación pendiente

Las pruebas comprobaron el ciclo de llamadas a herramientas, la consulta del pedido, la búsqueda
del SKU, el rechazo seguro y la creación aprobada de una incidencia.

Queda un problema en la respuesta redactada por el modelo: en la prueba final describió el pedido
como “en preparación”, aunque la herramienta y la base de datos indican `pendiente`. Por tanto, el
agente aún puede inventar o reinterpretar datos al redactar la respuesta final. La aplicación
debería basar esa parte de la respuesta en los resultados reales de las herramientas y no afirmar
un estado distinto.

## Capturas

Se resumen las pruebas en cuatro intentos, con una captura para cada uno:

| Captura | Evidencia y explicación | Archivo |
|---|---|---|
| 1. Primer intento: ejecución y rechazo | Claude propuso `MAQ-001`, un código incorrecto, y después afirmó que había registrado la incidencia pese al rechazo. | ![Primer intento: propuesta de SKU incorrecto y respuesta errónea](image.png) |
| 2. Segundo intento: otro código inventado | Claude propuso `MAQ-002`. Tras rechazar la acción, lo describió como un problema técnico, aunque el operador simplemente no había aprobado el registro. | ![Segundo intento: código inventado y rechazo mal explicado](image-1.png) |
| 3. Tercer intento: rechazo gestionado correctamente | Tras actualizar el agente, este consultó el catálogo y encontró `MAQ-010`. Al responder `N`, confirmó que la incidencia no se registró y que no hubo un error técnico. | ![Tercer intento: SKU correcto y rechazo seguro](image-2.png) |
| 4. Cuarto intento: creación aprobada y dato pendiente | Al responder `s`, se creó la incidencia número 3 con prioridad alta y estado abierta. La captura también muestra el problema pendiente: Claude dijo que el pedido estaba “en preparación”, aunque la herramienta devolvió el estado `pendiente`. | ![Cuarto intento: incidencia creada y discrepancia en el pedido](image-3.png) |

## Conclusión

La práctica permitió ver que un agente es un ciclo de modelo, herramientas y resultados, no solo una
petición de texto a un LLM. También mostró la importancia de validar los argumentos antes de
ejecutar escrituras, pedir aprobación humana y comprobar que la respuesta final no contradice los
datos obtenidos.
