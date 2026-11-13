# Diccionario de Datos — Capas Plata y Oro (TDL Canastita)

**Proyecto:** Trusted Data Lab — Canastita (Occidente)  
**Institución:** Instituto Tecnológico de Colima (TecNM)  
**Equipo:** Adolfo Rodríguez (Ingeniería de Datos) y Andrea Tairi Velázquez Gallardo (Análisis Estadístico)  
**Fecha:** Noviembre 2026  
**Versión:** 1.0 (Entrega E1)

---

## 1. Arquitectura Medallion del Proyecto

El observatorio sigue el patrón de arquitectura Medallion para garantizar el linaje, la auditabilidad y la confianza de los datos:

1. **Capa Bronce (`data/bronce/`):** Almacén de ingestión cruda en formatos nativos (CSV) con metadatos JSON y bitácora de extracción.
2. **Capa Plata (`data/plata/`):** Almacén limpio, deduplicado, tipado, estandarizado a nivel regional, con tratamiento y etiquetado de anomalías (IQR) y filtrado por Puerta 1.
3. **Capa Oro (`data/oro/`):** Tabla dimensional analítica mensual integrada con indicadores macroeconómicos de Banco de México (tipo de cambio FIX e INPC) y métricas derivadas (variaciones intermensuales MoM, anuales YoY, precios en USD y spreads).
4. **Almacén de Cuarentena (`data/cuarentena/`):** Repositorio de auditoría de registros rechazados por Puerta 1 con motivo de fallo y marca temporal.

---

## 2. Diccionario de Datos — Capa Plata

* **Archivo:** `data/plata/canasta_occidente_plata.csv` (y `.parquet` en entornos con soporte).
* **Grano:** Una cotización mayorista diaria por mercado, producto, variedad/calidad y origen.
* **Total registros:** ~14,923 observaciones limpias (2022-01 a 2026-11).

| Nombre de Columna | Tipo de Dato | Nulos Permitidos | Descripción de Negocio | Rango o Valores Válidos | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `fecha_observacion_raw` | String | No | Fecha original registrada en la fuente SNIIM. | Formato `DD/MM/YYYY` | `"05/01/2024"` |
| `fecha` | Date / String | No | Fecha normalizada de la cotización mayorista. | `2022-01-01` a `2026-11-30` | `"2024-01-05"` |
| `fecha_iso` | String | No | Fecha en formato ISO 8601 (`YYYY-MM-DD`). | `YYYY-MM-DD` | `"2024-01-05"` |
| `anio_mes` | String | No | Período mensual de la cotización. | Formato `YYYY-MM` | `"2024-01"` |
| `plaza_id` | Integer | No | Identificador numérico oficial de la plaza según SNIIM. | 80, 140, 160 | `80` |
| `estado` | String | No | Entidad federativa donde se ubica el centro mayorista. | Colima, Jalisco, Michoacán | `"Colima"` |
| `ciudad` | String | No | Ciudad sede del mercado de abasto. | Colima, Guadalajara, Morelia | `"Colima"` |
| `nombre_plaza` | String | No | Nombre descriptivo del centro de distribución o abasto. | Texto descriptivo | `"Colima: Centros de distribucion de Colima"` |
| `producto` | String | No | Nombre homologado del producto agropecuario de la canasta. | Jitomate Saladette, Limon con semilla #5, Aguacate Hass, etc. | `"Jitomate Saladette"` |
| `calidad` | String | Sí | Clasificación de calidad comercial según el mayorista. | Primera, Segunda, S/C | `"Primera"` |
| `presentacion` | String | Sí | Unidad de comercialización mayorista. | Kilogramo, Caja, Arpilla | `"Kilogramo"` |
| `origen` | String | Sí | Estado de la República de procedencia del cultivo. | Michoacán, Sinaloa, Colima, etc. | `"Sinaloa"` |
| `precio_min_mxn` | Float | No | Precio mínimo observado por kilogramo en el día (MXN). | `> 0`, `<= precio_frecuente` | `20.0` |
| `precio_max_mxn` | Float | No | Precio máximo observado por kilogramo en el día (MXN). | `>= precio_frecuente` | `25.0` |
| `precio_frecuente_mxn` | Float | No | Precio modal o más común de transacción comercial (MXN). | `precio_min <= P <= precio_max` | `22.0` |
| `precio_frecuente_limpio` | Float | No | Precio frecuente acotado a los límites del método IQR para estabilidad en modelado estadístico. | `> 0` | `22.0` |
| `es_atipico_iqr` | Boolean | No | Bandera que indica si el precio observado se clasifica como outlier estadístico ($> Q3 + 1.5 \times IQR$ o $< Q1 - 1.5 \times IQR$). | `True`, `False` | `False` |
| `observaciones` | String | Sí | Notas adicionales registradas por el analista de mercado. | Texto libre | `""` |
| `_fuente` | String | No | Identificador del sistema de origen. | `"SNIIM_SE"` | `"SNIIM_SE"` |
| `_url_origen` | String | No | URL del portal gubernamental de donde se extrajo. | URL válida | `"http://www.economia-sniim.gob.mx/..."` |
| `_capturado_en_utc` | String | No | Marca temporal UTC en la que el observatorio extrajo el registro. | Formato ISO 8601 UTC | `"2026-11-12T20:40:28+00:00"` |

---

## 3. Diccionario de Datos — Capa Oro

* **Archivo:** `data/oro/canasta_occidente_oro.csv` (y `.parquet` en entornos con soporte).
* **Grano:** Una observación mensual agregada por mercado (`plaza_id`) y producto agropecuario (`producto`).
* **Total registros:** ~961 registros mensuales consolidados (2022-01 a 2026-11).

| Nombre de Columna | Tipo de Dato | Nulos Permitidos | Fórmula o Método de Derivación | Descripción de Negocio | Ejemplo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `anio_mes` | String | No | Extracción de período (`YYYY-MM`). | Mes de referencia de la canasta. | `"2024-03"` |
| `plaza_id` | Integer | No | Clave oficial de la plaza. | Identificador del centro de abasto. | `80` |
| `ciudad` | String | No | Homologación regional. | Ciudad sede del mercado mayorista. | `"Colima"` |
| `nombre_plaza` | String | No | Catálogo de plazas. | Nombre oficial del centro de distribución. | `"Colima: Centros de distribucion de Colima"` |
| `producto` | String | No | Homologación regional. | Insumo agropecuario clave. | `"Limon con semilla #5"` |
| `precio_promedio_mxn` | Float | No | $\frac{1}{N} \sum P_{\text{frecuente}}$ | Precio promedio mensual observado (pesos/kg). | `28.50` |
| `precio_limpio_promedio_mxn` | Float | No | $\frac{1}{N} \sum P_{\text{limpio}}$ | Precio promedio mensual mitigando distorsiones extremas IQR. | `28.20` |
| `precio_mediana_mxn` | Float | No | $\text{Mediana}(P_{\text{frecuente}})$ | Mediana mensual de cotizaciones (pesos/kg). | `28.00` |
| `precio_min_mes` | Float | No | $\min(P_{\text{min}})$ | Precio piso observado en el mes. | `24.00` |
| `precio_max_mes` | Float | No | $\max(P_{\text{max}})$ | Precio techo observado en el mes. | `34.00` |
| `volatilidad_precio_std` | Float | No | $\sigma(P_{\text{frecuente}})$ | Desviación estándar de los precios en el mes. | `2.45` |
| `num_observaciones` | Integer | No | $\text{Count}(*)$ | Número de cotizaciones registradas en el mes. | `22` |
| `conteo_atipicos_iqr` | Integer | No | $\sum \text{es\_atipico\_iqr}$ | Cantidad de días del mes con precios atípicos. | `1` |
| `spread_mensual_mxn` | Float | No | $P_{\max} - P_{\min}$ | Amplitud o brecha de precios en el mercado local. | `10.00` |
| `spread_pct` | Float | No | $\frac{\text{spread}}{P_{\text{promedio}}} \times 100$ | Porcentaje del spread respecto al precio promedio. | `35.09` |
| `tipo_cambio_fix_promedio` | Float | No | Join mensual con Banxico (SF60653). | Tipo de cambio FIX promedio del mes (USD/MXN). | `16.8520` |
| `inpc_mensual` | Float | No | Join mensual con Banxico (SP1). | Índice Nacional de Precios al Consumidor. | `134.120` |
| `precio_usd` | Float | No | $\frac{P_{\text{promedio}}}{\text{TC\_FIX}}$ | Precio mayorista equivalente en dólares por kilogramo. | `1.6912` |
| `variacion_mom_pct` | Float | Sí (1er mes) | $\frac{P_t - P_{t-1}}{P_{t-1}} \times 100$ | Tasa de variación porcentual intermensual. | `+12.40` |
| `variacion_yoy_pct` | Float | Sí (<12 meses)| $\frac{P_t - P_{t-12}}{P_{t-12}} \times 100$ | Tasa de variación porcentual anualizada. | `-8.50` |
| `media_movil_3m` | Float | No | Rolling 3 meses de $P_{\text{promedio}}$ | Tendencia suavizada trimestral del insumo. | `26.80` |
| `inflacion_mensual_pct` | Float | Sí (1er mes) | $\frac{\text{INPC}_t - \text{INPC}_{t-1}}{\text{INPC}_{t-1}} \times 100$ | Tasa de inflación mensual general de la economía. | `+0.45` |

---

## 4. Almacén de Cuarentena (`data/cuarentena/rechazos_plata.csv`)

Los registros que no satisfacen las reglas de la Puerta 1 son desviados a cuarentena con trazabilidad completa.

| Nombre de Columna | Tipo de Dato | Motivo y Regla de Rechazo |
| :--- | :--- | :--- |
| `fecha_rechazo_utc` | String | Fecha y hora UTC en que el registro fue rechazado por el pipeline. |
| `motivo_rechazo` | String | `precio_negativo_o_cero`: Cotización menor o igual a cero.<br>`precio_max_menor_min`: Inversión lógica ($P_{\max} < P_{\min}$).<br>`precio_frecuente_inconsistente`: $P_{\text{frecuente}} < P_{\min}$ o $P_{\text{frecuente}} > P_{\max}$.<br>`fecha_invalida`: Fecha con formato corrupto.<br>`fecha_fuera_de_rango`: Fechas anteriores a 2020 o posteriores a 2027. |
| `fecha_observacion_raw` | String | Cadena original de fecha en la fuente. |
| `producto` | String | Nombre del producto en el registro corrupto. |
| `precio_min_mxn` | Float | Valor de precio mínimo detectado. |
| `precio_max_mxn` | Float | Valor de precio máximo detectado. |
| `precio_frecuente_mxn` | Float | Valor de precio frecuente detectado. |
