# Entrega E3 - TDL Canastita (Occidente)

**Equipo:** Adolfo Rodríguez (`23460528@colima.tecnm.mx`) y Andrea Tairi Velázquez Gallardo (`23460539@colima.tecnm.mx`)  
**Etiqueta:** `e3` (Rama `main`)  
**Tablero interactivo:** [tablero/app.py](../../tablero/app.py) (`streamlit run tablero/app.py` — 6 pestañas)  
**Repositorio:** `https://github.com/AdolfOrtega/tdl-canastita-proyecto`

---

## Resumen en tres líneas
En **E3** completamos el análisis estadístico multivariado sobre Capa Oro (**PCA** estandarizado con `63.19%` de varianza en `PC1+PC2`, pruebas de normalidad **Mardia y Henze-Zirkler**, Q-Q de **Mahalanobis**, **MANOVA** `Wilks=0.1339 / Pillai=1.0301, p < 0.001` y **PERMANOVA** `p = 0.001`) y publicamos su mapa interactivo **PC1 vs PC2** en el tablero Streamlit. Aplicamos en producción la combinación ganadora del experimento (`1 hilo + lxml + Parquet`), midiendo una reducción real de **`-24.74%` en tiempo** y **`-98.01%` en almacenamiento** con `0.0%` de error, y publicamos el dataset bajo licencia **`CC BY 4.0`** con su *datasheet* completo. Cerramos el ciclo de calidad con retrospectiva PSP E0–E3 (`79.75 h`, `34` defectos, exactitud `93.52%`, *Review Yield* E3 `57.14%`), autoevaluación **MoProSoft / CMMI / SPICE**, tendencia **DataOps**, **`0` hallazgos abiertos** y cumplimiento **`6/6` para el Sello TDL**.

---

## Análisis Estadístico

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| :--- | :--- | :--- |
| **Matriz y normalidad multivariada (15 pts)** | [laboratorio/analisis_multivariado_e3.py](../../laboratorio/analisis_multivariado_e3.py) · [matriz_correlaciones_e3.csv](../../laboratorio/matriz_correlaciones_e3.csv) · [qq_mahalanobis_e3.png](../../laboratorio/graficos/qq_mahalanobis_e3.png) | Matriz `7x7` de rango completo (`N = 619`, `2023-01` a `2026-11`), Mardia (`b1,7=68.83`, `b2,7=168.99`), Henze-Zirkler (`HZ=24.41`), Yeo-Johnson, Q-Q Mahalanobis (`r = 0.7755`) y Puerta 3 PERMANOVA. |
| **Componentes principales — PCA (35 pts)** | [pca_cargas_y_varianza_e3.csv](../../laboratorio/pca_cargas_y_varianza_e3.csv) · [pca_sedimentacion_e3.png](../../laboratorio/graficos/pca_sedimentacion_e3.png) · [pca_biplot_plazas_productos_e3.png](../../laboratorio/graficos/pca_biplot_plazas_productos_e3.png) | Estandarizado sobre matriz de correlaciones, ortogonalidad verificada (`error = 0.0`), 2 componentes Kaiser (`63.19%`), 3 componentes (`77.24%`), biplot con centroides y nombres de negocio. |
| **MANOVA (25 pts)** | [manova_resultados_e3.csv](../../laboratorio/manova_resultados_e3.csv) · [laboratorio/informe_multivariado_e3.md](../../laboratorio/informe_multivariado_e3.md) | Comparativa de **Colima, Guadalajara y Morelia** (`Wilks = 0.13393`, `Pillai = 1.03008`, `p = 0.0`) y por producto (`Wilks = 0.78464`, `p = 0.0`), contrastada con 7 ANOVAs y riesgo de error Tipo I (`30.17%`). |
| **Mapa proyectado en tablero (15 pts)** | [tablero/app.py](../../tablero/app.py) · [pca_proyeccion_oro_e3.csv](../../laboratorio/pca_proyeccion_oro_e3.csv) · [tests/test_tablero_e2e.py](../../tests/test_tablero_e2e.py) | Pestaña 6 interactiva (**PC1 vs PC2** coloreable por plaza o producto y filtrable por insumo) con explicación ejecutiva para *Restaurante Luisiana* validada en pruebas E2E. |

---

## Calidad en los Sistemas de Información

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| :--- | :--- | :--- |
| **Cierre de auditoría (30 pts)** | [docs/E3/cierre_auditoria.md](cierre_auditoria.md) · [calidad/auditor_tdl.py](../../calidad/auditor_tdl.py) | `0` issues externos en GitHub y cierre verificable de los hallazgos internos/pre-E3 (`CRITICO: 0`, `MAYOR: 0`, `MENOR: 0`). |
| **Modelos de proceso (25 pts)** | [docs/E3/modelos_proceso_moprosoft_cmmi.md](modelos_proceso_moprosoft_cmmi.md) | Autoevaluación aplicada en **MoProSoft (`NMX-I-059-NYCE`)** y **CMMI** con nivel y brechas concretas, más tabla comparativa (**ISO 9001, MoProSoft, SPICE/ISO 33000, CMMI, PSP/TSP**). |
| **Retrospectiva PSP E0–E3 (25 pts)** | [calidad/retrospectiva_psp.py](../../calidad/retrospectiva_psp.py) · [docs/E3/retrospectiva_psp.md](retrospectiva_psp.md) · [retrospectiva_psp_e0_e3.png](../../laboratorio/graficos/retrospectiva_psp_e0_e3.png) | Análisis automático de las 4 bitácoras PSP (`79.75 h`, `34` defectos): exactitud global `93.52%`, error E3 `+4.70%` y mejora de *Review Yield* temprano (`0.0%` en E2 -> `57.14%` en E3). |
| **Tendencias aplicadas (10 pts)** | [docs/E3/tendencias_dataops_observabilidad.md](tendencias_dataops_observabilidad.md) | Documento de 1 página mapeando **DataOps, Observabilidad de Datos y DevSecOps** sobre nuestra arquitectura diaria en producción. |
| **Solicitud formal del Sello TDL** | [docs/E3/solicitud_sello_tdl.md](solicitud_sello_tdl.md) · [calidad/solicitud_sello_tdl.json](../../calidad/solicitud_sello_tdl.json) | **`6 / 6` criterios cumplidos** (`100.0%` disponibilidad últimos 14 días, `100.0%` completitud Oro obligatoria, `>= 80%` cobertura `pytest`, `0` secretos, `0` críticos, reproducible + abierto). |

---

## Ingeniería de Datos

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| :--- | :--- | :--- |
| **Optimización medida (50 pts)** | [extractores/sniim_canasta.py](../../extractores/sniim_canasta.py) · [pipeline/benchmark_optimizacion_e3.py](../../pipeline/benchmark_optimizacion_e3.py) · [docs/E3/optimizacion_pipeline_e3.md](optimizacion_pipeline_e3.md) | Adopción real de **`1 hilo + lxml + Parquet`** en Bronce/Plata/Oro (`3.0-E3`): **`-24.74%` tiempo total** (`1.2970 s -> 0.9761 s`) y **`-98.01%` peso en disco** (`10,610 KB -> 210.86 KB`), `0.0%` error y `100%` paridad de filas. |
| **Dataset publicado con licencia abierta y *datasheet* (40 pts)** | [LICENSE-DATA.md](../../LICENSE-DATA.md) · [docs/E3/datasheet_canasta_oro.md](datasheet_canasta_oro.md) · [pipeline/diccionario_datos.md](../../pipeline/diccionario_datos.md) | Licencia **`CC BY 4.0`** / Libre Uso MX, descarga directa en Pestaña 6 del tablero, diccionario v3.0 y *Datasheet* completo (motivación, composición de `967` filas, captura, Puerta 1, usos recomendados y no recomendados). |

---

## Relatoría de etapa
* Documento completo con las 6 preguntas obligatorias, horas PSP reales y uso de IA generativa: [docs/relatoria-E3.md](../relatoria-E3.md).

---

## Issues de la entrega anterior
* Al cierre de E3 (`27 de noviembre de 2026`), la API de GitHub confirma **`0` issues abiertos ni cerrados por docentes o equipos pares** (`open_issues_count = 0`).
* Todos los hallazgos internos y de revisión pre-E3 quedaron formalmente cerrados con trazabilidad (`c25d23e`, `7931e51`, `37ef180`, `4815b20`, `b949a3b`) en [docs/E3/cierre_auditoria.md](cierre_auditoria.md).
