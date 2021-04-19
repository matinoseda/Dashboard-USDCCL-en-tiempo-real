# Dashboard-USDCCL-en-tiempo-real
Este dashboard grafica en tiempo real el valor del dólar CCL de varios Cedears simultáneamente.

## Qué se necesita:
+ Para usar FinnHub se necesita un token (línea 110). Se puede obtener gratis en la página de FinnHub.
+ Para usar Pyrofex se necesita tener una cuenta en un bróker que utilice la plataforma Talaris v3 (línea 41, no sé si Pyrofex puede funcionar con Talaris v4).
+ Es necesario tener python 3 e instalar las siguientes librerías:
 -pandas
 -websocket
 -threading
 -requests
 -dash
 -plotly
 
## Cómo funciona el script:

+ se creó una hoja de cálculo en Excel en la cual se indica y elige que cedears van a estar en el dashboard real time. En este Excel se cargaran algunos datos de los cedears, tales como si ticker, ratio.
+  se creó una conexión websocket con FinnHub para traer datos de mercado (último precio, volumen, timestamp) de varias acciones del mercado estadounidense en tiempo real.
+  se creó una conexión websocket con Pyrofex para traer datos de mercado (caja de puntas, volumen, timestamp) de varios Cedears en tiempo real.
+  se creó una web app simple que contiene un gráfico interactivo con las librerías Dash y Plotly.
+  se crearon 3 threads para que todo pouede funcionar simultáneamente.

![](Panel%20Cedears.png)

Este código se puede adaptar fácilmente para que muestre el tipo de cambio USDCCL de ADRs, bonos, letras del tesoro
