# Entrega E2 - TDL Canastita (Occidente)

**Equipo:** Adolfo Rodríguez (`23460528@colima.tecnm.mx`) y Andrea Tairi Velázquez Gallardo (`23460539@colima.tecnm.mx`)  
**Etiqueta:** `e2` (Rama `main`)  
**Tablero interactivo:** [tablero/app.py](../../tablero/app.py) (`streamlit run tablero/app.py`)  
**Repositorio:** `https://github.com/AdolfOrtega/tdl-canastita-proyecto`

---

## Resumen en tres líneas
En E2 ampliamos el observatorio integrando la tercera fuente especializada geoespacial (**9,650 comercios DENUE-INEGI** y 4 polígonos municipales con unión espacial `within` del `100.0%` y cero PII) junto con trazabilidad a nivel registro (`_linaje_*`) en Capa Oro y declaración de ética y legalidad. Demostramos experimentalmente mediante un **diseño factorial $2^3$ real (24 corridas), ANOVA de 2 vías (3×3) y matriz fraccionada $2^{4-1}$ (`I = ABCD`)** que `1 hilo + lxml + Parquet` reduce `16.84%` el tiempo frente a E1 (`1.1996 s` vs `1.4426 s`) y ahorra **`99.03%`** en almacenamiento con `0%` de error. Certificamos el producto de software y datos con **`96.00%` en ISO/IEC 25010** y **`99.67%` en ISO/IEC 25012**, disponibilidad real del **`100.0%`** en producción (`48/48` corridas diarias), integración continua en cada `push` y auditoría técnica automatizada.

---

## Ingeniería de Datos

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| :--- | :--- | :--- |
| **Fuente especializada integrada y visible en tablero (Cero PII)** | [extractores/denue_geo.py](../../extractores/denue_geo.py) · [pipeline/enriquecer_geo.py](../../pipeline/enriquecer_geo.py) · [tablero/app.py](../../tablero/app.py) | Integración INEGI DENUE v1 + Marco Geoestadístico en Colima (2,881), Guadalajara (3,279) y Morelia (3,490); `100.0%` unión espacial `within` (EPSG:4326) y mapa interactivo `pydeck` sin datos personales (LFPDPPP). |
| **Declaración de ética y legalidad de datos** | [docs/etica-datos.md](../etica-datos.md) | Análisis por fuente (SNIIM, Banxico SIE, INEGI DENUE/MGEM), licencia Libre Uso MX, `robots.txt` (incluyendo precedente de rechazo `open-meteo`), exclusión PII y sesgos con mitigación. |
| **Linaje de datos en Capa Oro** | [pipeline/construir_oro.py](../../pipeline/construir_oro.py) · [data/oro/linaje_oro.json](../../data/oro/linaje_oro.json) · [pipeline/diccionario_datos.md](../../pipeline/diccionario_datos.md) | Cada fila de `canasta_occidente_oro.csv` (963 registros) contiene `_linaje_fuente_*`, `_linaje_fecha_captura_sniim` y `_linaje_version_pipeline`, respaldado por grafo SHA-256 en JSON y diccionario v2.0. |

---

## Análisis Estadístico

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| :--- | :--- | :--- |
| **Diseño $2^3$ con aleatorización, réplicas y bloqueo** | [laboratorio/experimento_factorial_2k.py](../../laboratorio/experimento_factorial_2k.py) · [experimento_2_3_corridas.csv](../../laboratorio/experimento_2_3_corridas.csv) · [extractores/snapshot_html_sniim.py](../../extractores/snapshot_html_sniim.py) | Ruta Ingeniería sobre copia local congelada de 6 HTML reales del SNIIM (lote de 12 páginas = 4,846 filas/corrida), 3 bloques aleatorizados (24 corridas), tasa de error `0.0%`. |
| **Diseño de dos factores ($\ge 3$ niveles) con interacción** | [laboratorio/experimento_2vias_corridas.csv](../../laboratorio/experimento_2vias_corridas.csv) · [interaccion_2vias_lote_formato.png](../../laboratorio/graficos/interaccion_2vias_lote_formato.png) | Diseño 3×3 (`lote_paginas`: 6, 12, 24 × `formato_salida`: CSV, CSV_GZIP, Parquet; 27 corridas) con ANOVA Tipo II e interacción + Tukey HSD. |
| **Completo $2^4$ vs Fraccionado $2^{4-1}$** | [laboratorio/matriz_2_4_completo.csv](../../laboratorio/matriz_2_4_completo.csv) · [laboratorio/matriz_2_4_fraccionado.csv](../../laboratorio/matriz_2_4_fraccionado.csv) · [tests/test_experimento_e2.py](../../tests/test_experimento_e2.py) | Construcción y verificación algebraica del generador `D = ABC` (`I = ABCD`, Resolución IV, alias de efectos e interacciones) logrando **50% de ahorro** (16 a 8 tratamientos). |
| **ANOVA, supuestos y corrida de confirmación** | [laboratorio/informe_experimento.md](../../laboratorio/informe_experimento.md) · [confirmacion_optimo.csv](../../laboratorio/confirmacion_optimo.csv) · [residuos_anova_2_3.png](../../laboratorio/graficos/residuos_anova_2_3.png) | Puerta 3 aprobada en escala original (Shapiro-Wilk `p = 0.5647`, Levene `p = 0.6385`, DW = `2.0205`). Confirmación de `1 hilo + lxml + Parquet` en `1.1996 s` (dentro IC 95% `[0.9948, 1.2123] s`, `-16.84%` vs base E1). |

---

## Calidad en los Sistemas de Información

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| :--- | :--- | :--- |
| **Evaluación del producto con ISO/IEC 25010** | [calidad/evaluar_iso_25010_25012.py](../../calidad/evaluar_iso_25010_25012.py) · [docs/E2/evaluacion_iso_25010_25012.md](evaluacion_iso_25010_25012.md) · [.github/workflows/ci_calidad.yml](../../.github/workflows/ci_calidad.yml) | Las 8 características medidas con código real: índice global **`96.00%`** (`100.0%` disponibilidad en `48/48` corridas diarias, `0` secretos, `0` PII, CC promedio `4.71`, eficiencia confirmada por $2^3$). |
| **Evaluación de datos con ISO/IEC 25012** | [calidad/resultados_iso_25012.json](../../calidad/resultados_iso_25012.json) · [docs/E2/evaluacion_iso_25010_25012.md](evaluacion_iso_25010_25012.md) | Las 15 características medidas sobre los 963 registros de Capa Oro: **`99.67%`** global, **`100.0%` de completitud obligatoria** (`98.63%` global con rezagos MoM/YoY) y `100.0%` de trazabilidad y diccionario. |
| **Antecedentes normativos (9126 -> SQuaRE / ISO 9001)** | [docs/E2/evaluacion_iso_25010_25012.md](evaluacion_iso_25010_25012.md) | Cuadro comparativo técnico articulando ISO/IEC 9126, la familia ISO/IEC 25000 SQuaRE (25010/25012) y el enfoque a procesos PHVA de ISO 9001:2015. |
| **Auditoría cruzada y PSP** | [calidad/auditor_tdl.py](../../calidad/auditor_tdl.py) · [docs/E2/auditoria_cruzada.md](auditoria_cruzada.md) · [tiempo-adolfo.csv](../../calidad/tiempo-adolfo.csv) · [tiempo-andrea.csv](../../calidad/tiempo-andrea.csv) | Herramienta CLI de auditoría lista; auditoría interna de línea base ejecutada sobre corte `e1` (`INT-01`..`INT-04` cerrados, `0` hallazgos abiertos hoy). Sección par lista en espera de asignación docente. |

---

## Relatoría de etapa
* Documento completo con las 6 preguntas obligatorias, horas PSP reales y declaración de IA generativa: [docs/relatoria-E2.md](../relatoria-E2.md).

---

## Issues de la entrega anterior
* Al cierre de esta entrega (19 de noviembre de 2026), **no se registraron issues abiertos ni cerrados por parte de los docentes** en el repositorio de GitHub (`AdolfOrtega/tdl-canastita-proyecto`, verificado vía API de GitHub: `open_issues_count = 0`).
* Adicionalmente, la *Quality Auditor* ejecutó una auditoría interna sobre el corte `tag: e1` ([docs/E2/auditoria_cruzada.md](auditoria_cruzada.md)), resolviendo los 4 hallazgos detectados mediante commits trazables antes de cerrar E2:
  * `INT-01`: Flujo automático CI Puerta 2 en cada `push` -> cerrado en commit `c25d23e` ([.github/workflows/ci_calidad.yml](../../.github/workflows/ci_calidad.yml)).
  * `INT-02`: Columnas de linaje `_linaje_*` y grafo en Capa Oro -> cerrado en commit `7931e51` ([pipeline/construir_oro.py](../../pipeline/construir_oro.py)).
  * `INT-03`: KPIs dinámicos en Pestaña 3 del tablero -> cerrado en commit `c25d23e` ([tablero/app.py](../../tablero/app.py)).
  * `INT-04`: Vigilancia continua de 0 rutas locales absolutas -> cerrado y automatizado en Puerta 2 CI (`calidad/evaluar_iso_25010_25012.py`).
