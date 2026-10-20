# Ejecuta el script y anota los aciertos de cada proveedor.

> Todos son 6/6 aciertos aunque gemini tarda tres veces mas

![alt text]({E9885EE3-831E-44D5-A7D1-A2F1BC5F234E}.png)

# Amplía `CASOS` hasta al menos 15, con casos difíciles: ironía, dos clientes en el mismo correo, un correo en inglés, un correo sin nombre de negocio.

> Increiblemente son 15/15 aciertos por lo que no hay fallos que ver

![alt text]({D116E239-8ECD-4461-A70E-FC301B8407DA}.png)

# Añade una validación de negocio: si hay cliente, comprueba con `buscar_cliente` que existe en la base de datos.

> Una herramienta es una funcion reutilizable que realiza una tarea concreta, como buscar un cliente en la base de datos. Se define una vez para poder llamarla cuando haga falta, en lugar de repetir su logica en distintos lugares. En un asistente con herramientas, el modelo puede solicitar su uso y el programa ejecuta la funcion y le devuelve el resultado

![alt text]({FABA750F-1E81-47E5-B7BD-67006119E0D2}.png)

> Como se espera saca los clientes que no se encuentran en la base de datos, pero se han ido algunos saltando y otros metiendo, como por ejemplo OpenAI que segun los otros se salta Marta y La Parra y Bar Central

![alt text]({39715C3D-F581-4690-82A4-65E4D31C0235}.png)

