# PROPUESTA DEL OBSERVATORIO - ENTREGA E0 (ARRANQUE)
## TDL Canastita: Observatorio de Precios de la Canasta Básica e Inflación en el Occidente

**Materias del Proyecto Integrador:**
* **Ingeniería de Datos (CMD-2602):** ARMANDO ROMAN GALLARDO HEREDIA
* **Análisis Estadístico para Ciencia de Datos:** MONICO JOEL SANCHEZ VELASCO
* **Calidad en los Sistemas de Información (IFC-1008):** ISIS SARAI ESPINOSA LOZANO

**Integrantes del Equipo:**
* **Adolfo Rodríguez** (23460528@colima.tecnm.mx) - Data Engineer (Captura, almacén por capas, limpieza y puertas de calidad)
* **Andrea Tairi Velázquez Gallardo** (23460539@colima.tecnm.mx) - Data Statistician (Series de tiempo, experimento factorial, análisis multivariado y Quality Lead en E0)

**Fecha de Entrega:** 6 de noviembre de 2026 - **Etiqueta en repositorio:** e0

## 1. Ficha del Observatorio
Cuando nos sentamos a elegir el tema del observatorio, quisimos agarrar un problema real que tenemos literalmente en nuestro trabajo y en nuestra cuadra aquí en Colima: por un lado, uno de nosotros Adolfo trabaja en el restaurante **Luisiana**, donde en cocina se ve cada semana cómo pega en los costos cuando se disparan los insumos frescos; y por otro lado, Andrea ha trabajado en "Tienditas de la esquina", en la tienda de la esquina tenemos trato directo con la dueña de la abarrotera y con su hermano, que se dedica a la venta de frutas y verduras en el tianguis. Tanto en la cocina del restaurante como en la abarrotera y en el puesto del tianguis pasa lo mismo: surten varias veces por semana casi a ciegas, y cuando el limón, el jitomate, la papa o el aguacate suben de golpe en la bodega o con los proveedores, se enteran hasta que ya están pagando el producto.

Además, para poder comparar al menos tres grupos en la Unidad 5 de Estadística (E3), decidimos no quedarnos solo con la plaza de Colima, sino abarcar las tres plazas principales de abasto de nuestra región (**Corredor Occidente: Colima, Guadalajara y Morelia**), que son justo las referencias de donde entra mucha de la mercancía que se mueve en los tianguis y restaurantes de Colima.

| Elemento | Definición de nuestro proyecto |
| :--- | :--- |
| **Nombre del proyecto** | TDL Canastita (tdl-canastita-proyecto) |
| **Sector / Vertical** | Precios de abasto de insumos para cocinas/restaurantes, abarroteras y comerciantes de tianguis |
| **Región que observa** | Región Occidente (3 plazas): Colima (Centros de distribución de Colima), Guadalajara, Jalisco (Mercado de Abasto de Guadalajara) y Morelia, Michoacán (Mercado de Abasto de Morelia) |
| **Pregunta central** | ¿En qué plaza del Occidente (Colima, Guadalajara o Morelia) y en qué momento conviene surtir los insumos básicos frescos (aguacate Hass, limón #5, jitomate saladette, cebolla bola, chile serrano y papa alpha) y cómo les pegan las subidas del dólar (USD/MXN) y la inflación (INPC)? |
| **Quién pagaría por la respuesta (Cliente)** | Encargados de compras de cocinas y restaurantes de Colima (como el restaurante Luisiana), dueños de abarroteras locales y comerciantes de frutas y verduras en tianguis |
| **Por qué pagaría** | Tanto en la cocina de un restaurante como en un puesto de tianguis o abarrotera, comprar cajas o arpillas en la semana más cara o sin comparar contra lo que cuesta en Guadalajara o Morelia les hace perder entre $2,500 y $6,000 pesos al mes en sobrecostos y merma. Pagar una herramienta accesible ($150 a $300 MXN al mes) se recupera en un solo viaje o pedido bien negociado |

## 2. Entrevista con Alguien del Sector
Para validar el problema desde los dos lados (quien compra para cocina de restaurante y quien vende en abarrotera/tianguis), platicamos tanto en el área de cocina/compras del restaurante **Luisiana** donde trabaja Adolfo, como con la **dueña de la abarrotera de la esquina y su hermano, que vende frutas y verduras en el tianguis** donde trabajaba Andrea, aquí en Colima *(por la regla de cero datos personales de la LFPDPPP no incluimos sus nombres completos ni teléfonos personales en el repositorio)*.

### Las 5 preguntas y lo que nos respondieron
1. **¿Cuáles son los insumos frescos cuyas subidas de precio más les desacomodan la semana (tanto en el restaurante como en la abarrotera y el tianguis)?**
   * **Respuesta:** *"Los que más nos mueven la jugada semana tras semana son el aguacate, el jitomate, la cebolla blanca, el limón, el chile serrano y la papa. En el restaurante (Luisiana) no puedes cambiar los precios del menú cada martes porque subió la caja de aguacate o jitomate; y en la abarrotera y en el tianguis, si la arpilla o la reja sube al doble en la bodega, la gente se queja y compra menos, así que nos toca bajarle a nuestra ganancia para que no se quede y se eche a perder."*
2. **¿Cómo deciden hoy con qué proveedor, bodega o mercado surtir cada semana (comparan contra otras plazas como Guadalajara o Michoacán antes de comprar)?**
   * **Respuesta:** *"Casi siempre surtimos con los mismos bodegueros aquí en Colima por falta de tiempo en la madrugada. El hermano de la dueña de la abarrotera, que anda en el tianguis, comenta que muchas veces los mayoristas locales dicen 'subió porque viene caro desde Guadalajara o desde Michoacán y por el dólar', pero a las 6 de la mañana nadie tiene a la mano una tabla confiable para ver en cuánto amaneció realmente el kilo en el Abasto de Guadalajara o de Morelia."*
3. **¿Con cuánta anticipación se enteran de que un producto básico viene al alza, o normalmente se dan cuenta hasta que ya están surtiendo?**
   * **Respuesta:** *"Nos damos cuenta hasta que llegamos a la bodega o cuando llega el proveedor con la nota. Cero anticipación. Si supiéramos unos días antes que la próxima semana viene subida fuerte en la papa, la cebolla o el limón, adelantaríamos compra de lo que aguanta más días sin dañarse o ajustaríamos qué tanta mercancía meter."*
4. **Si existiera un tablero sencillo que les avisara cada semana cómo está el precio en Colima frente a Guadalajara y Morelia y qué productos van a subir las siguientes semanas, ¿qué decisión cambiarían?**
   * **Respuesta:** *"En el restaurante nos serviría para negociar con el proveedor enseñándole el precio real de abasto y para planear compras de cocina. Y para la abarrotera y el puesto del tianguis serviría para decidir si conviene encargar mercancía con alguien que va a Guadalajara o comprar más volumen antes de que pegue el brinco de precio."*
5. **¿Cuánto calculan que pierden o gastan de más en un mes malo cuando se disparan estos productos sin aviso previo, y cuánto estarían dispuestos a pagar por tener ese monitoreo?**
   * **Respuesta:** *"En un mes pesado donde se disparan dos o tres verduras básicas se van fácil de $2,500 a $4,000 pesos en la abarrotera/tianguis y hasta $5,000 o $6,000 en cocina del restaurante. Si la página trae datos reales y no falla, sí pagaríamos entre $150 y $300 pesos al mes porque en una sola surtida buena se recupera."*

### Qué aprendimos de la entrevista
Lo más importante que sacamos de platicar en el restaurante **Luisiana** y con la dueña de la abarrotera y su hermano del tianguis es que ninguno de ellos tiene tiempo en la mañana para meterse a buscar tablas viejas del gobierno ni interpretar fórmulas de un ARIMA. Lo que necesitan ver en menos de un minuto en su celular o compu es:
1. En cuánto anda hoy el precio mínimo, frecuente y máximo de cada producto en Colima comparado con Guadalajara y Morelia.
2. Si para las próximas semanas se espera que suba o baje (con su margen de error explicado en palabras sencillas).
3. Si el aumento que les quiere cobrar el bodeguero se justifica por la inflación (INPC) o el dólar (USD/MXN), o si es un sobreprecio local.

## 3. Las Tres Preguntas Analíticas del Proyecto
Aterrizamos una pregunta medible para cada una de las tres técnicas que vamos a ver en Análisis Estadístico (E1, E2 y E3):

1. **Pregunta de Pronóstico (E1 - Series de Tiempo, Unidad 3):**
   * **Pregunta:** ¿Cuál será el precio mayorista frecuente (MXN/kg) del jitomate, el limón #5 y el aguacate Hass en Colima durante los próximos 4 periodos, y qué relación o rezago muestra su correlación cruzada frente al tipo de cambio FIX USD/MXN y al INPC?
   * **Con qué datos se responde:** Con la serie histórica de 59 meses continuos (2022-01 a 2026-11, con 13,647 registros) descargada del SNIIM en `data/bronce/sniim_canasta/historico/` cruzada con los 1,218 registros diarios del tipo de cambio FIX (SF43718) y los 57 meses del INPC (SP1) de la API de Banxico, comparando Suavizamiento Exponencial Simple, Holt, Holt-Winters y ARIMA por su error (MAE, RMSE y MAPE).
2. **Pregunta de Experimento Factorial (E2 - Diseño de Experimentos, Unidad 4):**
   * **Pregunta (Ruta Ingeniería sobre nuestro propio sistema):** ¿Qué combinación de factores en nuestro extractor (Factor A: 1 hilo vs 4 hilos; Factor B: parser html.parser vs lxml; Factor C: formato CSV vs Parquet) logra el menor tiempo de ejecución en segundos y la menor tasa de error al procesar un lote local de páginas del SNIIM?
   * **Por qué elegimos esta ruta:** Porque así no dependemos de que un tercero corra una campaña externa en una sola semana, no saturamos el servidor del gobierno (se corre contra copias locales descargadas) y además el resultado nos sirve directamente como evidencia medida de Eficiencia de Desempeño para la evaluación ISO/IEC 25010 en la materia de Calidad.
3. **Pregunta de Análisis Multivariado (E3 - PCA y MANOVA, Unidad 5):**
   * **Pregunta:** ¿Existen diferencias estadísticamente significativas (con alfa = 0.05) en el comportamiento conjunto de precios y volatilidad entre los 3 mercados del Occidente (Colima, Guadalajara y Morelia), y qué perfiles de productos/plazas aparecen al proyectar los datos en sus dos primeros componentes principales?
   * **Grupos y variables:** Comparamos los 3 grupos (Colima ID 80, Guadalajara ID 140 y Morelia ID 160) midiendo simultáneamente 6 variables numéricas por observación/mes: `precio_min_mxn`, `precio_max_mxn`, `precio_frecuente_mxn`, `rango_precio_mxn` (max - min), `dispersion_porcentual` y `tipo_cambio_fix` (USD/MXN).

## 4. Plan de Recopilación y Análisis de robots.txt y Términos de Uso
Desde este arranque (E0) dejamos funcionando nuestras dos fuentes obligatorias (un scraper ético y una API REST):

| Fuente | Qué extraemos y formato | Frecuencia | Método de acceso |
| :--- | :--- | :--- | :--- |
| **1. SNIIM - Secretaría de Economía** (economia-sniim.gob.mx) | Precios mayoristas (precio_min_mxn, precio_max_mxn, precio_frecuente_mxn, origen, calidad, presentacion) de canasta básica en Colima, Guadalajara y Morelia. Formato HTML (latin-1) guardado como CSV + .meta.json en `data/bronce/sniim_canasta/` | Días hábiles (el flujo en GitHub Actions corre diario a las 7:00 a.m. hora del centro) | Web Scraping ético con ExtractorEtico (requests + BeautifulSoup) y pausa de 1.5 s |
| **2. API del SIE de Banxico** (banxico.org.mx/SieAPIRest) | Tipo de cambio diario FIX USD/MXN (serie SF43718, 1,218 días) e Índice Nacional de Precios al Consumidor INPC mensual (serie SP1, 57 meses). Formato JSON guardado en CSV + .meta.json en `data/bronce/macro_api/` | Diaria (Tipo de cambio) y Mensual (INPC); consultada en la corrida diaria de GitHub Actions | API REST oficial usando token en encabezado Bmx-Token (con respaldo abierto en Frankfurter y World Bank API si se corre sin .env) |

### Revisión de robots.txt, Términos de Uso y Privacidad (LFPDPPP)
1. **Revisión de http://www.economia-sniim.gob.mx/robots.txt:**
   Antes de programar el scraper descargamos el `robots.txt` del SNIIM y encontramos estas reglas:
   ```text
   User-agent: *
   Disallow: /Analisis/
   Disallow: /*.xls$
   Disallow: /2010/
   Disallow: /Sicia/
   Disallow: /Sicia2/
   Disallow: /SiciaAnt/
   # Allow: /
   ```
   Nuestra consulta entra por `/nuevo/Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/ResultadosConsultaFechaFrutasYHortalizas.aspx`, que está permitida (`Allow: /`) y no baja archivos `.xls` ni toca las carpetas restringidas. Además, `ExtractorEtico` lo comprueba automáticamente con `urllib.robotparser` antes de cada petición.
2. **Caso real donde ExtractorEtico bloqueó una fuente y cambiamos de servidor:**
   En nuestras primeras pruebas (documentado en la bitácora `calidad/bitacora_captura.csv` y en el defecto #4 de Adolfo) intentamos descargar datos históricos de `archive-api.open-meteo.com`, pero su archivo `robots.txt` tiene `Disallow: /` para cualquier `User-Agent: *`. Nuestro `ExtractorEtico` lanzó `PermissionError` y detuvo la descarga. Siguiendo la regla del proyecto ("Si un sitio lo prohíbe, se busca otra fuente. No se negocia"), quitamos ese servidor y usamos las series oficiales SF43718 y SP1 de la API de Banxico, cuyos términos de Datos Abiertos permiten el acceso automatizado.
3. **Cero Datos Personales y Cero Secretos Expuestos:**
   * Ni las tablas de precios del SNIIM ni las series económicas de Banxico contienen nombres, teléfonos, correos ni perfiles de personas físicas, cumpliendo con la LFPDPPP.
   * Nuestro token de Banxico se lee desde `.env` (en local) y desde GitHub Secrets (`BANXICO_TOKEN`) en GitHub Actions, manteniendo 0 secretos expuestos en el repositorio.

## 5. Máquina de Captura y Serie Histórica en Capa Bronce
Todo el código de captura ya corre solo y deja evidencia verificable:
* **Código base y módulos:** `extractores/base.py` (ExtractorEtico), `extractores/sniim_canasta.py`, `extractores/macro_api.py` y el orquestador `extractores/ejecutar_captura.py`.
* **Ejecución programada en GitHub Actions:** El archivo `.github/workflows/captura_diaria.yml` está programado con `cron: "0 13 * * *"` (7:00 a.m. hora local) y también tiene `workflow_dispatch` para poder dispararlo manualmente desde la pestaña Actions. En cada corrida descarga los datos nuevos, corre `pytest` y hace commit automático de la capa bronce y de la bitácora.
* **Archivos ya descargados en `data/bronce/` (superando los 36 periodos mínimos):**
  1. `data/bronce/sniim_canasta/historico/sniim_occidente_historico_2022_2026.csv`: 13,647 registros a lo largo de 59 meses continuos (2022-01 a 2026-11) en Colima, Guadalajara y Morelia.
  2. `data/bronce/sniim_canasta/fecha=2026-11-06/sniim_reciente_2026-11-06.csv`: 1,500 registros de la captura reciente en las 3 plazas.
  3. `data/bronce/macro_api/tipo_cambio/usd_mxn_historico_2022_2026.csv`: 1,218 registros diarios (59 meses) del tipo de cambio FIX oficial de Banxico (SF43718).
  4. `data/bronce/macro_api/inflacion/inpc_inflacion_mexico_historico.csv`: 57 meses continuos (2022-01 a 2026-09) del INPC Nacional (SP1 de Banxico).

## 6. Arranque del Sistema de Calidad (PSP y Objetivos Medibles)
Para no dejar la calidad al final, abrimos desde el primer día nuestros registros individuales de PSP y la bitácora automática del sistema:
* **Registros de Adolfo Rodríguez (Data Engineer):** `calidad/defectos-adolfo.csv` y `calidad/tiempo-adolfo.csv`.
* **Registros de Andrea Tairi Velázquez Gallardo (Data Statistician y Quality Lead en E0):** `calidad/defectos-andrea.csv` y `calidad/tiempo-andrea.csv`.
* **Bitácora de ejecuciones de captura:** `calidad/bitacora_captura.csv` guarda automáticamente la hora de inicio y fin de cada corrida, cuánto tardó en segundos, cuántos registros bajó y si terminó en EXITO o FALLA.

### Nuestros 3 Objetivos de Calidad Medibles (que revisaremos en E1 y E3)
1. **Disponibilidad real de la captura automática >= 95%:**
   Con los registros de `calidad/bitacora_captura.csv` entre el 6 y el 13 de noviembre calcularemos el Tiempo Medio Entre Fallas (MTBF) y el Tiempo Medio de Reparación (MTTR) usando la fórmula vista en clase: `A = MTBF / (MTBF + MTTR) >= 0.95`.
2. **Completitud y validez de datos hacia capa plata/oro >= 95% (ISO/IEC 25012):**
   Al menos el 95% de las filas capturadas deben pasar las validaciones automáticas de esquema y reglas de negocio (por ejemplo, que `precio_min_mxn <= precio_frecuente_mxn <= precio_max_mxn` y que no haya precios negativos o vacíos). Todo registro que falle se irá a `data/cuarentena/` con su motivo de rechazo, sin borrar nada en silencio.
3. **Cobertura de pruebas >= 60% y 0 secretos expuestos:**
   Mantener una cobertura mínima del 60% en nuestras pruebas automáticas con `pytest` y garantizar 0 llaves o tokens expuestos en el repositorio al auditar con `gitleaks`.

## 7. Reflexión y Declaración de Uso de IA Generativa
Durante el armado de esta entrega E0 nos apoyamos en ChatGPT / Gemini únicamente para resolver dudas puntuales del scraping y de la configuración de GitHub Actions. Al principio tuvimos un detalle importante con la tabla HTML del SNIIM: cuando consultábamos todos los productos (`ProductoId=-1`) la tabla traía 9 columnas, pero al consultar un producto específico para armar el histórico de 5 años el servidor quitaba las columnas de Producto y Calidad y nos dejaba solo 7 columnas, por lo que el parser devolvía una lista vacía. Revisando el HTML crudo adaptamos la función `parsear_tabla_sniim` para que detecte ambos formatos sin perder filas.

*Prompts principales que usamos como apoyo:*
* *"Como reviso por código si la ruta de consulta de frutas y hortalizas del SNIIM pasa el robots.txt con urllib.robotparser?"*
* *"Por qué al consultar un solo ProductoId en el SNIIM mi función de BeautifulSoup no encuentra las 9 celdas td que salían cuando pedía todos los productos?"*
* *"Como configuro el archivo YAML de GitHub Actions para que corra el script de captura todos los días con cron y guarde el CSV actualizado en el repo?"*
* *"Como leo mi token de Banxico desde un archivo .env sin que se suba al repositorio ni salga en los archivos de metadatos?"*
* *"Como puedo subir el repositorio a GitHub?"*
