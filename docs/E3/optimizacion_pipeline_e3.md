# Optimizacion Medida del Pipeline de Datos (Antes E1 vs Despues E3)

**Responsable:** Adolfo Rodriguez (`23460528@colima.tecnm.mx`)  
**Configuracion Implementada:** `1 hilo + lxml + Parquet` (validada por el experimento factorial 2^3 de E2)  
**Repeticiones medidas por etapa:** `8` corridas reproducibles (tras corrida de calentamiento descartada)

---

## 1. Cambios Aplicados en Produccion
1. **`extractores/sniim_canasta.py`:** Se adopto `parser="lxml"` como motor por defecto en `parsear_tabla_sniim()`, `extraer_sniim_reciente()` y `extraer_sniim_historico()` manteniendo respaldo automatico a `html.parser` si `lxml` no esta presente.
2. **`extractores/ejecutar_captura.py`:** `guardar_csv_y_metadatos()` ahora genera la version columnar `.parquet` junto con el `.csv` rastreado y documenta el ahorro en bytes dentro de `.meta.json`.
3. **`pipeline/limpieza_plata.py` y `pipeline/construir_oro.py`:** `limpieza_plata.py` prioriza lectura de Bronce en `.parquet` cuando esta disponible y etiqueta el linaje Oro en version `3.0-E3`.

---

## 2. Medicion Cuantitativa Antes vs Despues

| Etapa del Pipeline | Metrica | Antes (E1: `html.parser + CSV`) | Despues (E3: `lxml + Parquet`) | Mejora / Reduccion |
| :--- | :--- | :---: | :---: | :---: |
| **Scraping + Bronce** (`4,846` filas) | Tiempo medio (s) | `1.1259 s` (±0.0305) | **`0.9428 s`** (±0.0636) | **`+16.27%`** |
| **Scraping + Bronce** (`4,846` filas) | Peso artefacto (KB) | `2292.30 KB` | **`22.32 KB`** | **`-99.03%`** |
| **Medallion I/O** (`16,488` filas) | Lectura + Escritura (s) | `0.1711 s` (±0.0108) | **`0.0333 s`** (±0.0009) | **`+80.52%`** |
| **Medallion I/O** (`16,488` filas) | Peso Plata + Oro (KB) | `8317.70 KB` | **`188.54 KB`** | **`-97.73%`** |
| **Total Flujo Completo** | **Tiempo acumulado (s)** | `1.2970 s` | **`0.9761 s`** | **`-24.74%`** |
| **Total Flujo Completo** | **Almacenamiento total (KB)** | `10610.00 KB` | **`210.86 KB`** | **`-98.01%`** |
| **Integridad y Calidad** | Tasa de error / Paridad filas | `0.0%` error / `4,846` filas | **`0.0%` error / Paridad True** | **100% preservada** |

---

## 3. Impacto en Calidad de Datos (ISO/IEC 25012)
- La paridad exacta de filas entre `html.parser` y `lxml` (`4,846` == `4,846`) garantiza cero perdida de registros en el scraping del SNIIM.
- La completitud obligatoria de Capa Oro se mantiene en **`100.0%`** con `0` discrepancias numericas entre CSV y Parquet.
