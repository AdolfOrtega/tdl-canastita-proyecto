# Relatoría E3 - TDL Canastita (Occidente)

**Equipo:** Adolfo Rodríguez (`23460528@colima.tecnm.mx`) y Andrea Tairi Velázquez Gallardo (`23460539@colima.tecnm.mx`)  
**Periodo:** 25 de noviembre de 2026 al 27 de noviembre de 2026

---

## 1. Qué nos propusimos
Consolidar la etapa multivariada y de certificación final (**Sello TDL**): construir la matriz de 7 variables numéricas de Capa Oro con pruebas de normalidad multivariada (Mardia y Henze-Zirkler + Q-Q Mahalanobis), extraer componentes principales estandarizados (PCA) y comparar nuestras 3 plazas (`Colima`, `Guadalajara`, `Morelia`) vía **MANOVA**; aplicar en producción la optimización ganadora de E2 (`1 hilo + lxml + Parquet`) midiendo antes vs. después y publicar el dataset abierto (`CC BY 4.0`) con su *datasheet*; y cerrar el ciclo de calidad con retrospectiva PSP E0–E3, autoevaluación MoProSoft/CMMI, DataOps y cumplimiento `6/6` del Sello TDL.

---

## 2. Qué hicimos (cronología con fechas, responsable y horas reales PSP)

| Fecha | Responsable | Horas Netas | Actividad y Entregable |
| :--- | :--- | :---: | :--- |
| **25 nov 2026** | Adolfo Rodríguez | 2.58 h | Implementación de `parser="lxml"` con fallback y escritura/lectura `.parquet` en `sniim_canasta.py`, `ejecutar_captura.py`, `limpieza_plata.py` y `construir_oro.py` (`3.0-E3`), más desarrollo de `pipeline/benchmark_optimizacion_e3.py`. |
| **25 nov 2026** | Andrea Tairi Velázquez | 2.75 h | Diseño de matriz multivariada (`N = 619`, 7 variables continuas), pruebas Mardia y Henze-Zirkler, tratamiento Yeo-Johnson y distancias Q-Q de Mahalanobis en `laboratorio/analisis_multivariado_e3.py`. |
| **26 nov 2026** | Adolfo Rodríguez | 2.33 h | Redacción de licencia abierta `CC BY 4.0` ([LICENSE-DATA.md](../LICENSE-DATA.md)), ficha técnica completa [docs/E3/datasheet_canasta_oro.md](E3/datasheet_canasta_oro.md) y reporte cuantitativo [docs/E3/optimizacion_pipeline_e3.md](E3/optimizacion_pipeline_e3.md). |
| **26 nov 2026** | Andrea Tairi Velázquez | 3.25 h | Implementación de PCA estandarizado, gráfica de sedimentación, biplot PC1–PC2, MANOVA (`Wilks`, `Pillai`), PERMANOVA y redacción de [laboratorio/informe_multivariado_e3.md](../laboratorio/informe_multivariado_e3.md). |
| **27 nov 2026** | Andrea Tairi Velázquez | 5.08 h | Desarrollo de `calidad/retrospectiva_psp.py`, evaluación MoProSoft/CMMI, tendencias DataOps, cierre de auditoría post-E3, verificador del Sello TDL (`6/6`), `test_e3_multivariado_sello.py`, `relatoria-E3.md` y `ENTREGA.md`. |
| **27 nov 2026** | Adolfo Rodríguez | 4.42 h | Pestaña 6 (`Mapa Multivariado & Sello TDL`) y descarga abierta en `tablero/app.py`, pruebas E2E (`test_tablero_e2e.py`), CI Puerta 2, corrección de *mojibake* (`reparar_mojibake`) y clave `SF43718` en diccionario. |

*Total invertido en E3 según bitácoras PSP (`calidad/tiempo-*.csv`):* **Adolfo 9.33 h (560 min) · Andrea 11.08 h (665 min) · Total E3: 20.42 h netas · Acumulado E0–E3: 79.75 horas netas.**

---

## 3. Qué decidimos y por qué (alternativas descartadas)
1. **Excluir variables geográficas constantes de la matriz de MANOVA en lugar de forzar todas las columnas de Capa Oro:** Incluir `comercios_denue_radio` o `distancia_media_abasto_km` (constantes dentro de cada plaza) habría hecho singular la matriz intra-grupos $\mathbf{E}$; seleccionamos 7 variables económicas linealmente independientes (`rango = 7`) sobre los 6 insumos base continuos (`N = 619`, `2023-01` a `2026-11`).
2. **Respaldar el MANOVA con Traza de Pillai y PERMANOVA no paramétrico en lugar de depender solo de Lambda de Wilks:** Dado que las pruebas Mardia y Henze-Zirkler detectaron no normalidad multivariada por picos reales agropecuarios ($47$ meses $> \chi^2_{7,0.99}$), aplicamos Puerta 3 confirmando el efecto regional tanto por Pillai (`1.03008`, `p = 0.0`) como por PERMANOVA (`pseudo-F = 141.7209`, `p = 0.001`).
3. **Implementar Yeo-Johnson con `scipy.stats.yeojohnson` en lugar de añadir `scikit-learn` a `requirements.txt`:** Mantuvo el entorno ligero y reproducible en CI usando una librería ya probada en E1/E2.

---

## 4. Qué salió mal y cómo lo corregimos (registros PSP)
* **Defecto Adolfo #17 (Entorno / Datos desfasados):** Al reubicar localmente el repositorio y correr la actualización, un archivo `.parquet` previo (`15,189` filas) coexistía con el `.csv` diario de GitHub Actions (`15,521` filas). Se encadenó explícitamente `limpieza_plata.py -> construir_oro.py` con verificación de código de salida, regenerando los `967` registros vigentes (`15 min`).
* **Defecto Adolfo #18 (Datos / Parser):** Al establecer `parser="lxml"` por defecto en `parsear_tabla_sniim()`, se añadió captura de `FeatureNotFound` con respaldo automático a `html.parser` (`10 min`).
* **Defecto Andrea #12 (Lógica / Diseño MANOVA):** Se detectó en revisión previa el riesgo de singularidad intra-grupo y se fijaron 7 variables con varianza intra-plaza positiva verificando rango completo `7` (`15 min`).
* **Defecto Andrea #13 (Sintaxis Python 3.12):** Las cadenas f-string con LaTeX emitieron `SyntaxWarning` en `analisis_multivariado_e3.py`; se convirtió la plantilla a raw f-string (`rf"""`), dejando `0` advertencias (`10 min`).
* **Defecto Andrea #14 (Entorno / Dependencias):** Se sustituyó `PowerTransformer` por `scipy.stats.yeojohnson` para mantener `requirements.txt` mínimo y evitar fallos en CI (`10 min`).
* **Defecto Adolfo #19 (Datos / Codificación):** La auditoría post-E3 detectó `19` nombres de productos secundarios SNIIM con doble codificación UTF-8/latin-1 (*mojibake*) en Plata y Oro; se implementó `reparar_mojibake()` en `pipeline/limpieza_plata.py` con prueba unitaria dejando `0` caracteres corruptos (`15 min`).
* **Defecto Andrea #15 (Documentación / Trazabilidad):** La auditoría de calidad detectó referencia heredada a serie Banxico `SF60653` en `pipeline/diccionario_datos.md` frente a `SF43718` usada en `macro_api.py`; se homologó a `SF43718` y se actualizó `cierre_auditoria.md` (`10 min`).

---

## 5. Qué aprendimos

### Análisis Estadístico
Comprendimos con datos reales por qué **MANOVA no equivale a correr 7 ANOVAs separados** (que inflarían el error Tipo I global al `30.17%`): aunque las tasas `MoM %` y `YoY %` no muestran diferencias univariadas aisladas (`p > 0.50`), al analizarse junto con nivel de precio, volatilidad, spread y liquidez de plaza el perfil multivariado separa nítidamente a Colima (cotizaciones por kg, `spread 24.1%`) de Guadalajara (`23.1` obs/mes, lotes por caja, `spread 58.9%`), mientras el PCA condensa `63.19%` de varianza en dos ejes interpretables.

### Ingeniería de Datos
Medimos el impacto real de pasar la optimización del laboratorio a producción: cambiar a `1 hilo + lxml + Parquet` redujo el tiempo combinado (`Scraping+Bronce + Medallion I/O`) en **`24.74%`** (`1.2970 s` -> `0.9761 s`) y el almacenamiento en **`98.01%`** (`10,610.00 KB` -> `210.86 KB`) manteniendo `0.0%` de error y `100.0%` de completitud obligatoria en Oro, listo para consumo público bajo licencia `CC BY 4.0` y *datasheet* completo.

### Calidad en los Sistemas de Información
La retrospectiva cuantitativa PSP (`79.75 h` acumuladas y `34` defectos gestionados de E0 a E3) evidenció cómo el error de estimación se estabilizó en **`+4.70%` en E3** (`93.52%` de exactitud media) y el *Review Yield* temprano subió de `0.0%` (E2) a **`57.14%` (E3)** tras cazar defectos preventivos en revisión de auditoría; al integrar MoProSoft, CMMI, prácticas DataOps y el auditor automatizado logramos **`0` hallazgos abiertos** y **`6/6` umbrales del Sello TDL**.

---

## 6. Evidencias
* **Commits principales E3:** `4815b20` (Optimización `lxml + Parquet`, Benchmark y Dataset Abierto · Adolfo), `5a978a9` (Matriz Multivariada, Mardia/Henze-Zirkler y Q-Q Mahalanobis · Andrea), `a67e7d9` (PCA Estandarizado, Sedimentación y Biplot · Andrea), `7754247` (MANOVA `Wilks/Pillai`, PERMANOVA e Informe · Andrea), `d145a9e` (Retrospectiva PSP E0–E3 · Andrea), `ecba18c` (MoProSoft, CMMI, SPICE y DataOps · Andrea), `b949a3b` (Cierre Auditoría y Verificador Sello TDL · Andrea), `e989dfd` (Pestaña 6 Tablero, E2E y CI Puerta 2 · Adolfo) y commit final de cierre (`test_e3_multivariado_sello.py`, `ENTREGA.md`, `relatoria-E3.md` · Andrea).
* **Artefactos técnicos:** [docs/E3/ENTREGA.md](E3/ENTREGA.md), [laboratorio/analisis_multivariado_e3.py](../laboratorio/analisis_multivariado_e3.py), [laboratorio/informe_multivariado_e3.md](../laboratorio/informe_multivariado_e3.md), [pipeline/benchmark_optimizacion_e3.py](../pipeline/benchmark_optimizacion_e3.py), [docs/E3/optimizacion_pipeline_e3.md](E3/optimizacion_pipeline_e3.md), [LICENSE-DATA.md](../LICENSE-DATA.md), [docs/E3/datasheet_canasta_oro.md](E3/datasheet_canasta_oro.md), [calidad/retrospectiva_psp.py](../calidad/retrospectiva_psp.py), [docs/E3/retrospectiva_psp.md](E3/retrospectiva_psp.md), [docs/E3/modelos_proceso_moprosoft_cmmi.md](E3/modelos_proceso_moprosoft_cmmi.md), [docs/E3/tendencias_dataops_observabilidad.md](E3/tendencias_dataops_observabilidad.md), [docs/E3/cierre_auditoria.md](E3/cierre_auditoria.md), [docs/E3/solicitud_sello_tdl.md](E3/solicitud_sello_tdl.md) y [tablero/app.py](../tablero/app.py).
* **Gráficas E3:** [correlaciones_multivariadas_e3.png](../laboratorio/graficos/correlaciones_multivariadas_e3.png), [qq_mahalanobis_e3.png](../laboratorio/graficos/qq_mahalanobis_e3.png), [pca_sedimentacion_e3.png](../laboratorio/graficos/pca_sedimentacion_e3.png), [pca_biplot_plazas_productos_e3.png](../laboratorio/graficos/pca_biplot_plazas_productos_e3.png) y [retrospectiva_psp_e0_e3.png](../laboratorio/graficos/retrospectiva_psp_e0_e3.png).

---

## Uso de IA generativa
Durante E3 utilizamos asistencia de modelos de lenguaje dentro del editor para estructurar las funciones vectorizadas de Mardia, Henze-Zirkler y PERMANOVA en NumPy/SciPy, automatizar el cálculo de métricas PSP por etapa y maquetar la Pestaña 6 en Streamlit. Todas las ejecuciones sobre Capa Oro real (`967` filas), mediciones de benchmark (`8` repeticiones), pruebas estadísticas (`pytest`) y auditorías ISO/TDL fueron corridas, inspeccionadas y validadas directamente por ambos integrantes.
