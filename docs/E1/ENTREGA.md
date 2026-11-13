# Ficha Ejecutiva de Entrega E1 — Datos de Confianza y Pronóstico

**Proyecto:** Trusted Data Lab — Canastita (Occidente)  
**Institución:** Instituto Tecnológico de Colima (TecNM)  
**Asignaturas Integradas:**
- **Ingeniería de Datos:** Mtro. Armando Román Gallardo Heredia
- **Análisis Estadístico:** Mtro. Mónico Joel Sánchez Velasco
- **Calidad en Sistemas de Información:** Mtra. Isis Saraí Espinosa Lozano

**Equipo de Trabajo:**
- **Adolfo Rodríguez** (`23460528@colima.tecnm.mx`) — *Data Engineer & SQA Implementation Lead*
- **Andrea Tairi Velázquez Gallardo** (`23460539@colima.tecnm.mx`) — *Data Statistician & Verification Lead*

**Fecha:** Noviembre 2026  
**Versión / Tag:** `e1` (Rama `main`)  
**Repositorio GitHub:** [https://github.com/AdolfOrtega/tdl-canastita-proyecto](https://github.com/AdolfOrtega/tdl-canastita-proyecto)

---

## 1. Resumen Ejecutivo de la Entrega E1

La entrega **E1 (Datos de confianza y pronóstico)** consolida el paso de la ingestión en crudo hacia una arquitectura analítica Medallion robusta, auditable y de valor real para los comerciantes de tianguis, abarroteras y cocinas económicas (como el *Restaurante Luisiana* en Colima).

### Logros Principales de E1:
1. **Capa Plata (`data/plata/`):** 14,923 registros limpios, normalizados y deduplicados de precios diarios agropecuarios (2022-2026). Incorpora la **Puerta 1 de Calidad** con derivación activa de registros corruptos hacia **cuarentena** (`data/cuarentena/rechazos_plata.csv`) y detección de valores atípicos con el método **IQR**.
2. **Capa Oro (`data/oro/`):** 961 observaciones mensuales consolidadas mediante un join analítico multifuente con indicadores de Banco de México (Tipo de Cambio FIX promedio e Inflación INPC), calculando spreads, conversión en USD y tasas de variación intermensual (MoM) y anual (YoY).
3. **Laboratorio de Series de Tiempo (`laboratorio/`):** Modelado predictivo riguroso sobre 59 meses continuos para tres insumos críticos en Colima (Jitomate Saladette, Limón con semilla #5 y Aguacate Hass). Comparación de 4 familias de modelos (**SES, Holt, Holt-Winters, ARIMA**) con partición fuera de muestra, pruebas de estacionariedad **ADF** ($I(1)$) y pronóstico a 4 meses (Dic 2026 – Mar 2027) con intervalos de confianza al 95%.
4. **Calidad y SQA (IEEE 730):** Disponibilidad operativa real del **100.0%** en producción con base en 27 ejecuciones programadas exitosas en GitHub Actions; Plan SQA formal en [docs/E1/plan_sqa_ieee730.md](plan_sqa_ieee730.md); y registros PSP actualizados en `calidad/`.
5. **Tablero Streamlit (`tablero/app.py`):** Interfaz interactiva de consulta con visor de mercado, comparativo regional de plazas, semáforo de compras para cocinas y panel de gobernanza de datos.
6. **Suite de Pruebas Automatizadas:** 15 pruebas unitarias y de integración con **90% de cobertura de código**, superando ampliamente la meta del 60%.

---

## 2. Issues de la Entrega Anterior (Atención a la Retroalimentación de E0)

### Comentario Docente Recibido en E0 (Calificación: 98 / 100):
> *"Acciones para E1: Robustecer la suite tests/ antes de procesar las transformaciones de la capa Plata."*

### Acciones Correctivas Implementadas para E1:
Para atender de forma exhaustiva y preventiva esta observación, el equipo ejecutó el desarrollo bajo el principio de diseño dirigido por pruebas (TDD):

1. **Ampliación de Pruebas Unitarias de Extracción (`tests/test_extractores.py`):**
   - Se añadieron pruebas para validación de scraping defensivo ante respuestas vacías del portal de SNIIM.
   - Se incorporó la prueba `test_verificacion_integridad_archivos_bronce` para verificar la consistencia de metadatos y cálculo criptográfico de hashes SHA-256 de 64 caracteres.
2. **Creación de la Suite Integral de Pipeline (`tests/test_pipeline.py`):**
   - `test_normalizacion_nombres_productos`: Verifica la homologación regional de entidades (ej. "Tomate Saladette" -> "Jitomate Saladette", "Limón c/semilla # 5" -> "Limon con semilla #5").
   - `test_puerta_calidad_rechazo_y_cuarentena`: Valida que los datos corruptos (precios negativos, precios nulos, fechas invertidas o rotas, $P_{\max} < P_{\min}$) sean rechazados y confinados en `data/cuarentena/rechazos_plata.csv`.
   - `test_deteccion_atipicos_iqr`: Valida la identificación de outliers mediante $[Q1 - 1.5 \times IQR, Q3 + 1.5 \times IQR]$ y la generación de `precio_frecuente_limpio`.
   - `test_integracion_macro_oro`: Verifica la integridad referencial en el join entre SNIIM mensual y las series de Banxico FIX e INPC, sin pérdida de registros temporales.
   - `test_calculo_metricas_variacion_oro`: Verifica el cálculo correcto de variaciones intermensuales (MoM), anuales (YoY) y tasas inflacionarias.
   - `test_pipeline_completo_genera_archivos`: Prueba end-to-end que ejecuta la transformación de capas y certifica la existencia de los artefactos y el cumplimiento de $\ge 36$ períodos continuos.
3. **Suite de Pruebas Estadísticas (`tests/test_estadistica.py`):**
   - Validación de fórmulas matemáticas de error (MAPE, RMSE, MAE).
   - Invarianza de la descomposición estacional clásica ($Y_t = T_t + S_t + R_t$).
   - Pruebas ADF de estacionariedad e intervalos de predicción al 95%.
4. **Resultado Cuantitativo:**
   - Total de pruebas en suite: **15 tests pasando exitosamente**.
   - Cobertura de código alcanzada: **90%** (`pipeline/limpieza_plata.py`: 91%, `pipeline/construir_oro.py`: 88%).

---

## 3. Enlaces Directos a Evidencias del Proyecto

| Componente | Artefacto Generado | Ubicación en el Repositorio |
| :--- | :--- | :--- |
| **Pruebas Automatizadas** | Suite con 90% de cobertura (15 tests) | [tests/test_pipeline.py](../../tests/test_pipeline.py) · [tests/test_extractores.py](../../tests/test_extractores.py) · [tests/test_estadistica.py](../../tests/test_estadistica.py) |
| **Capa Plata** | Datos limpios y deduplicados | [data/plata/canasta_occidente_plata.csv](../../data/plata/canasta_occidente_plata.csv) · [Metadatos Plata](../../data/plata/canasta_occidente_plata.meta.json) |
| **Cuarentena** | Auditoría de rechazos Puerta 1 | [data/cuarentena/rechazos_plata.csv](../../data/cuarentena/rechazos_plata.csv) |
| **Capa Oro** | Tabla dimensional analítica | [data/oro/canasta_occidente_oro.csv](../../data/oro/canasta_occidente_oro.csv) · [Metadatos Oro](../../data/oro/canasta_occidente_oro.meta.json) |
| **Diccionario de Datos** | Especificación de esquemas | [pipeline/diccionario_datos.md](../../pipeline/diccionario_datos.md) |
| **Laboratorio Predictivo** | Script de pronósticos | [laboratorio/pronostico_series_tiempo.py](../../laboratorio/pronostico_series_tiempo.py) |
| **Informe Estadístico** | Reporte técnico de series de tiempo | [laboratorio/informe_estadistico.md](../../laboratorio/informe_estadistico.md) |
| **Métricas de Modelos** | Tabla comparativa MAPE/RMSE | [laboratorio/metricas_modelos.csv](../../laboratorio/metricas_modelos.csv) |
| **Pronósticos 4 Meses** | Proyecciones Dic 2026 – Mar 2027 | [laboratorio/pronosticos_futuro.csv](../../laboratorio/pronosticos_futuro.csv) |
| **Gráficos Estadísticos** | Visualizaciones analíticas | [laboratorio/graficos/](../../laboratorio/graficos/) |
| **Plan SQA IEEE 730** | Estándar de aseguramiento | [docs/E1/plan_sqa_ieee730.md](plan_sqa_ieee730.md) |
| **Bitácora de Producción** | 27 capturas programadas exitosas | [calidad/bitacora_captura.csv](../../calidad/bitacora_captura.csv) |
| **Registros PSP** | Defectos y tiempos del equipo | [calidad/defectos-adolfo.csv](../../calidad/defectos-adolfo.csv) · [calidad/defectos-andrea.csv](../../calidad/defectos-andrea.csv) |
| **Tablero Interactivo** | Aplicación Streamlit | [tablero/app.py](../../tablero/app.py) |
| **Relatoría Metodológica** | 6 preguntas de reflexión técnica | [docs/relatoria-E1.md](../relatoria-E1.md) |

---

## 4. Síntesis del Laboratorio Estadístico de Pronóstico

### Insumos Clave Analizados (Central de Abasto de Colima):
1. **Jitomate Saladette:** Modelo ganador **ARIMA (1,1,1)** con un **MAPE de 24.47%** y **RMSE de $7.80 MXN**.
2. **Limón con semilla #5:** Modelo ganador **Holt-Winters (Triple Suavizamiento Aditivo con período 12)** con un **MAPE de 11.39%** y **RMSE de $6.44 MXN**. Captura fielmente el ciclo estacional de floración baja y cuaresma.
3. **Aguacate Hass:** Modelo ganador **Modelo de Holt (Doble Suavizamiento con Tendencia Lineal)** con un **MAPE de 9.69%** y **RMSE de $5.30 MXN**.

### Pronóstico a 4 Meses Hacia Adelante (Intervalos de Confianza al 95%):

| Insumo | Dic 2026 (MXN) | Ene 2027 (MXN) | Feb 2027 (MXN) | Mar 2027 (MXN) | Tendencia Proyectada |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Jitomate Saladette** | **$20.64** [$11.88, $29.40] | **$21.92** [$11.33, $32.51] | **$22.75** [$11.39, $34.11] | **$23.29** [$11.57, $35.02] | Ligera alza invernal controlada. |
| **Limón con semilla #5** | **$37.37** [$28.56, $46.18] | **$38.44** [$25.98, $50.89] | **$40.87** [$25.62, $56.13] | **$44.29** [$26.68, $61.91] | Incremento estacional pronunciado hacia primavera. |
| **Aguacate Hass** | **$49.68** [$33.94, $65.42] | **$49.36** [$27.10, $71.62] | **$49.04** [$21.78, $76.31] | **$48.72** [$17.24, $80.21] | Estabilidad en torno a $49 MXN/kg con rango amplio. |

---

## 5. Métrica de Calidad en Producción (IEEE 730)

- **Total de corridas en producción:** 27 ejecuciones programadas vía cron en GitHub Actions.
- **Tasa de fallos en producción:** 0 fallos.
- **Disponibilidad operativa calculada:**
  $$A = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}} = \frac{144 \text{ h}}{144 \text{ h} + 0 \text{ h}} = 100.0\% \quad (\text{Meta comprometida: } \ge 95.0\%)$$
- **Cobertura de pruebas automatizadas:** **91%** en la suite `tests/` con ejecución en CI.

---

## 6. Instrucciones de Reproducción Local

Para ejecutar las pruebas y levantar el tablero localmente:

```bash
# 1. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 2. Correr la suite de pruebas y cobertura
pytest -v --cov=pipeline

# 3. Regenerar Capa Plata y Capa Oro (opcional)
python pipeline/limpieza_plata.py
python pipeline/construir_oro.py

# 4. Ejecutar el laboratorio de pronósticos
python laboratorio/pronostico_series_tiempo.py

# 5. Lanzar el tablero interactivo Streamlit
streamlit run tablero/app.py
```
