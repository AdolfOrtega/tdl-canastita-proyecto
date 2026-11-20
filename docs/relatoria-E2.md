# Relatoría E2 - TDL Canastita (Occidente)

**Equipo:** Adolfo Rodríguez (`23460528@colima.tecnm.mx`) y Andrea Tairi Velázquez Gallardo (`23460539@colima.tecnm.mx`)  
**Periodo:** 17 de noviembre de 2026 al 19 de noviembre de 2026

---

## 1. Qué nos propusimos
Ampliar el observatorio integrando la tercera fuente especializada geoespacial (DENUE-INEGI y Marco Geoestadístico) con cero datos personales (LFPDPPP) y linaje completo en Capa Oro; demostrar experimentalmente mediante un diseño factorial $2^3$ real qué configuración del extractor minimiza tiempo y errores; y certificar el producto de software y datos por encima del `95%` bajo ISO/IEC 25010 e ISO/IEC 25012, dejando operativo el protocolo de auditoría cruzada.

---

## 2. Qué hicimos (cronología con fechas, responsable y horas reales PSP)

| Fecha | Responsable | Horas Netas | Actividad y Entregable |
| :--- | :--- | :---: | :--- |
| **17 nov 2026** | Adolfo Rodríguez | 2.25 h | Análisis de `robots.txt` de INEGI (`Allow: /app`), diseño de sanitización LFPDPPP para API DENUE v1 y definición geométrica del diseño factorial $2^3$ junto con Andrea. |
| **17 nov 2026** | Andrea Tairi Velázquez | 2.08 h | Diseño formal de factores/bloques del experimento $2^3$ (Ruta Ingeniería), experimento de 2 vías 3×3 y construcción teórica $2^4$ vs $2^{4-1}$ (`I = ABCD`). |
| **18 nov 2026** | Adolfo Rodríguez | 2.75 h | Implementación de `extractores/denue_geo.py`, descarga de 9,650 comercios (Colima, Guadalajara y Morelia) + 4 polígonos INEGI, unión espacial `within` en `pipeline/enriquecer_geo.py` e inyección de `_linaje_*` y `linaje_oro.json` en `construir_oro.py`. |
| **18 nov 2026** | Andrea Tairi Velázquez | 2.50 h | Captura única de 6 páginas HTML reales del SNIIM en `extractores/snapshot_html_sniim.py` y programación del laboratorio experimental `experimento_factorial_2k.py` + `tests/test_experimento_e2.py`. |
| **19 nov 2026** | Andrea Tairi Velázquez | 5.25 h | Corridas experimentales (24 del $2^3$, 10 de confirmación, 27 del 3×3), análisis ANOVA, verificación Puerta 3 de residuos, `informe_experimento.md`, `auditor_tdl.py`, auditoría interna sobre `e1`, verificación QA visual de gráficas, limpieza de warnings en `adfuller` (`28/28` pruebas `pytest` con `0` warnings) y cierre documental. |
| **19 nov 2026** | Adolfo Rodríguez | 5.00 h | Evaluador cuantitativo `evaluar_iso_25010_25012.py`, workflow CI Puerta 2 (`.github/workflows/ci_calidad.yml`), pestañas Mapa `pydeck` y Experimento/ISO en `tablero/app.py`, pruebas `test_e2_geo_iso.py`, auditoría QA full-stack, pruebas E2E headless (`tests/test_tablero_e2e.py`) y verificación en verde de GitHub Actions CI. |

*Total invertido en E2 según bitácoras PSP (`calidad/tiempo-*.csv`):* **Adolfo 10.00 h (600 min) · Andrea 9.83 h (590 min) · Total equipo: 19.83 horas netas.**

---

## 3. Qué decidimos y por qué (alternativas descartadas)
1. **Fuente geoespacial INEGI DENUE + Marco Geoestadístico en lugar de OpenStreetMap Overpass:** Descartamos Overpass porque las pruebas devolvieron respuestas HTTP 406 en `robots.txt` y *timeouts* frecuentes (`ReadTimeout` / `504`). DENUE API v1 combinada con `WSCatGeo` ofreció 9,650 registros reales y polígonos municipales oficiales bajo Licencia Libre Uso MX (`100.0%` unión espacial `within`).
2. **Ruta Ingeniería sobre copia HTML congelada en lugar de consultar SNIIM en vivo:** Evitamos disparar 61 descargas repetidas al servidor federal (descartado por ética de scraping y sesgo por latencia de red), garantizando repetibilidad exacta del lote de 12 páginas (4,846 filas por corrida).
3. **Configuración óptima adoptada tras ANOVA (`1 hilo + lxml + Parquet`) en lugar de paralelismo por hilos:** Contrario a nuestra intuición inicial, el experimento demostró que 4 hilos en `BeautifulSoup` sufren contención del GIL de Python y alargan el tiempo; trabajar con `1 hilo + lxml + Parquet` confirmó `1.1996 s` vs `1.4426 s` de base E1 (`16.84%` más rápido) con **`99.03%` menos peso en disco**.

---

## 4. Qué salió mal y cómo lo corregimos (registros PSP)
* **Defecto Adolfo #9 (Interfaz DENUE):** La API DENUE devolvía `"No hay resultados."` en Morelia al interpolar flotantes (`19.706` con 3 decimales). Se corrigió formateando a 6 decimales fijos (`19.706000,-101.195000`) en `construir_url_denue()`, recuperando 3,490 comercios en Morelia (`20 min`).
* **Defecto Adolfo #10 (Datos DENUE):** Buscar `"fruteria"` omitía fruterías en Guadalajara por la nomenclatura SCIAN; se ajustó a `"frutas"` y se actualizó el clasificador de `enriquecer_geo.py` (`15 min`).
* **Defecto Adolfo #11 (Entorno WDAC/GDAL):** `gpd.read_file` fallaba en Windows por ausencia de DLL externa de `pyogrio`; se resolvió leyendo el GeoJSON estándar con `json.loads` -> `GeoDataFrame.from_features(..., crs="EPSG:4326")` más respaldo puro Python *ray-casting* (`20 min`).
* **Defecto Adolfo #12 (Falsos positivos de seguridad):** El escáner inicial confundía hashes SHA-256 de 64 caracteres con secretos; se refinó con expresiones regulares específicas de tokens y UUIDs en URLs (`10 min`).
* **Defecto Andrea #8 (Sintaxis `patsy` en ANOVA):** La fórmula `ols("tiempo_seg ~ C(bloque) + A * B * C")` fallaba con `TypeError: 'Series' object is not callable` porque existía la columna `C` del formato; se resolvió usando columnas categóricas explícitas `bloque_cat` y `lote_cat` (`15 min`).
* **Defecto Adolfo #13 (CI Puerta 2 / Cobertura y Portabilidad):** La primera corrida de CI Puerta 2 falló por cobertura inicial de `46.32%` (`< 60%`) y un falso positivo del escáner sobre texto literal en documentación; se ampliaron pruebas en `tests/test_e2_geo_iso.py` (`82.60%` cobertura total) y se generalizó la expresión regular de rutas locales (`15 min`).
* **Defecto Adolfo #14 (QA Tablero / Interfaz):** La auditoría QA detectó un logo externo de Wikimedia con HTTP 400 y 12 llamadas deprecadas `use_container_width` en Streamlit 1.67; se reemplazó por un distintivo institucional HTML/CSS offline del TecNM Colima y `width="stretch"` (`streamlit>=1.50.0`, `20 min`).
* **Defecto Adolfo #15 (QA Memoria y Mantenibilidad):** En `tablero/app.py` tres figuras de Matplotlib no liberaban memoria tras `st.pyplot()` y faltaban *docstrings* en auxiliares; se agregó `plt.close()` y *docstrings*, subiendo cobertura documental a `94.05%` e ISO/IEC 25010 a `97.88%` (`10 min`).
* **Defecto Adolfo #16 (Pruebas E2E `tests/test_tablero_e2e.py`):** Al ejecutar `AppTest.from_file` se resolvía una ruta relativa al directorio `tests/`; se corrigió derivando la ruta desde `Path(__file__).resolve().parent.parent`, logrando `2/2` pruebas E2E en verde (`10 min`).
* **Defecto Andrea #10 (QA Visual Gráficas):** La inspección visual detectó ligero empalme de etiquetas en `confirmacion_optimo_vs_base.png` y `efectos_principales_2_3.png`; se reubicaron con fondo blanco (`bbox`) y se regeneraron ambas figuras desde los CSV guardados (`20 min`).
* **Defecto Andrea #11 (QA Warnings Estadísticos):** La suite `pytest` arrojaba 2 `FutureWarning` de `statsmodels` en `adfuller` dentro de `laboratorio/pronostico_series_tiempo.py`; se pasó condicionalmente `result_object=False` vía `inspect.signature`, dejando `28/28` pruebas con `0` warnings (`15 min`).
* **Incidencia organizacional (Auditoría cruzada externa):** Al 19 de noviembre de 2026 no habíamos recibido asignación de equipo par ni issues previos en GitHub; para no dejar incompleto el criterio, Andrea implementó `calidad/auditor_tdl.py` y ejecutó la auditoría completa sobre nuestro propio corte `tag: e1` dejando lista la sección de equipo par.

---

## 5. Qué aprendimos

### Ingeniería de Datos
Una unión espacial real (`within`) no termina al cruzar coordenadas: primero requiere sanitización LFPDPPP previa a Capa Bronce para no almacenar teléfonos o calles de micronegocios, validación de formato en APIs externas (como los 6 decimales obligatorios del DENUE) y linaje explícito por registro (`_linaje_*` + `linaje_oro.json`) para auditar el origen de cada cifra mostrada al cliente.

### Análisis Estadístico
El diseño factorial $2^3$ demostró con evidencia que la intuición técnica puede fallar sin experimentación: 4 hilos empeoraron el desempeño por contención del GIL en Python, mientras que `1 hilo + lxml + Parquet` logró menor varianza y tiempo confirmado dentro del IC 95% (`1.1996 s` dentro de `[0.9948, 1.2123] s`). En el diseño 3×3 corroboramos que Parquet ahorra más del 98% de almacenamiento sin penalización significativa de tiempo (`p = 0.3845`).

### Calidad en los Sistemas de Información
Medir ISO/IEC 25010 e ISO/IEC 25012 sobre código y datos reales evita calificaciones subjetivas: al conectar la bitácora diaria de GitHub Actions (`48/48` corridas exitosas en modo diario, `100.0%`), la complejidad ciclomática AST (`4.73`), los resultados del experimento $2^3$ y la completitud obligatoria de Capa Oro (`100.0%`), obtuvimos índices reales de `97.88%` y `99.67%` reforzados con Puerta 2 CI en cada `push`.

---

## 6. Evidencias
* **Commits principales E2:** `7931e51` (Ingeniería Geoespacial, Linaje y Ética · Adolfo), `3bdecb4` (Laboratorio Experimento Factorial 2³ · Andrea), `c25d23e` (ISO 25010/25012, CI Puerta 2 y Tablero · Adolfo), `03081c3` (Auditoría Cruzada, Relatoría E2 y Entrega · Andrea), `216644f` / `4e1e367` / `a15920c` (Endurecimiento CI, QA Full-Stack y E2E · Adolfo) y commits finales de cierre PSP.
* **Artefactos técnicos:** [docs/E2/ENTREGA.md](E2/ENTREGA.md), [docs/etica-datos.md](etica-datos.md), [pipeline/diccionario_datos.md](../pipeline/diccionario_datos.md), [data/oro/linaje_oro.json](../data/oro/linaje_oro.json), [laboratorio/informe_experimento.md](../laboratorio/informe_experimento.md), [docs/E2/evaluacion_iso_25010_25012.md](E2/evaluacion_iso_25010_25012.md), [docs/E2/auditoria_cruzada.md](E2/auditoria_cruzada.md), [tablero/app.py](../tablero/app.py) y [tests/test_tablero_e2e.py](../tests/test_tablero_e2e.py).
* **Bitácoras PSP actualizadas:** [tiempo-adolfo.csv](../calidad/tiempo-adolfo.csv), [defectos-adolfo.csv](../calidad/defectos-adolfo.csv), [tiempo-andrea.csv](../calidad/tiempo-andrea.csv) y [defectos-andrea.csv](../calidad/defectos-andrea.csv).
* **Gráficas experimentales:** [efectos_principales_2_3.png](../laboratorio/graficos/efectos_principales_2_3.png), [interacciones_2_3.png](../laboratorio/graficos/interacciones_2_3.png), [residuos_anova_2_3.png](../laboratorio/graficos/residuos_anova_2_3.png), [interaccion_2vias_lote_formato.png](../laboratorio/graficos/interaccion_2vias_lote_formato.png) y [confirmacion_optimo_vs_base.png](../laboratorio/graficos/confirmacion_optimo_vs_base.png).

---

## Uso de IA generativa
Durante la etapa E2 utilizamos asistencia de modelos de lenguaje dentro del entorno de desarrollo para estructurar el código de `GeoDataFrame.from_features` (superando la incompatibilidad DLL de `pyogrio` en Windows), depurar la colisión de nombres en fórmulas de `patsy`, redactar las pruebas unitarias de `tests/` y estructurar las vistas `pydeck` en Streamlit. Todas las corridas del experimento factorial, descargas de INEGI DENUE, evaluaciones ISO y pruebas `pytest` fueron ejecutadas y verificadas directamente sobre nuestros datos reales por ambos integrantes, quienes dominamos su fundamento técnico para defensa.
