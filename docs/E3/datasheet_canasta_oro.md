# Ficha Técnica del Conjunto de Datos (*Datasheet*): TDL Canastita (Occidente)

Siguiendo la metodología **Datasheets for Datasets** (Gebru et al., 2021) y la norma **ISO/IEC 25012**, esta ficha documenta la motivación, composición, recolección, limpieza, usos apropiados y distribución del dataset certificado en Capa Oro.

---

## 1. Motivación
- **¿Por qué se creó el conjunto de datos?** Para ofrecer a comercios locales, abarroteras, fondas y cocinas económicas del Occidente de México (como el caso piloto *Restaurante Luisiana* en Colima) una fuente única, limpia, auditada y actualizada diariamente de precios mayoristas agropecuarios comparados contra inflación, tipo de cambio y densidad comercial municipal.
- **Creadores y responsables:** Adolfo Rodríguez (`23460528@colima.tecnm.mx`) y Andrea Tairi Velázquez Gallardo (`23460539@colima.tecnm.mx`), laboratorio académico *Trusted Data Lab (TDL)* del TecNM Campus Colima.
- **Financiamiento:** `$0` (infraestructura 100% abierta y fuentes públicas gubernamentales).

---

## 2. Composición
- **Archivos principales:**
  - `data/oro/canasta_occidente_oro.csv` y `data/oro/canasta_occidente_oro.parquet` (**967+ observaciones mensuales**, grano `anio_mes x plaza_id x producto`, `34` columnas tipadas, periodo continuo `2022-01` a `2026-11`, `59` meses).
  - `data/plata/denue_occidente_geo.csv` y `.geojson` (**9,650 establecimientos comerciales** en `Colima`, `Guadalajara` y `Morelia`, grano `id_denue`, `14` columnas).
  - `data/oro/linaje_oro.json` (grafo de trazabilidad y hashes SHA-256) y `pipeline/diccionario_datos.md` (documentación 100% de las 34 columnas).
- **Cobertura geográfica y de productos:**
  - **Plazas mayoristas SNIIM:** Colima (`plaza_id=80`), Guadalajara (`plaza_id=140`) y Morelia (`plaza_id=160`).
  - **6 productos base continuos (2022–2026):** `Aguacate Hass`, `Cebolla Bola`, `Chile Serrano`, `Jitomate Saladette`, `Limon con semilla #5` y `Papa Alpha`, más series complementarias captadas en ventana diaria reciente.
- **Datos faltantes conocidos:**
  - Las columnas de variación temporal (`variacion_mom_pct`, `inflacion_mensual_pct`) son estructuralmente nulas en el primer mes de cada serie (`t = 1`), y `variacion_yoy_pct` es nula en los primeros 12 meses (`t = 1..12`).
  - Todas las demás columnas obligatorias presentan **`100.0%` de completitud** (medido por `ISO/IEC 25012`).
- **Privacidad (LFPDPPP):** Cero datos personales identificables (PII). No se almacenan nombres de personas físicas, teléfonos, correos ni direcciones de calle/número.

---

## 3. Proceso de Captura
- **SNIIM (Secretaría de Economía):** Scraping ético diario (`extractores/sniim_canasta.py`) mediante `ExtractorEtico` (`robots.txt` verificado, `User-Agent` institucional y pausa `>= 1.5 s`), optimizado tras experimento $2^3$ a `1 hilo + parser lxml + escritura dual CSV/Parquet`.
- **Banco de México (API SIE):** Descarga automática vía REST API (`extractores/macro_api.py`) de las series `SF43718` (Tipo de cambio FIX promedio mensual) y `SP1` (INPC nacional mensual).
- **INEGI (DENUE v1 + Marco Geoestadístico WSCatGeo):** Captura geoespacial sanitizada (`extractores/denue_geo.py`) con radio `2,500 m` alrededor de cada Central de Abasto y polígonos municipales oficiales (`06002`, `06010`, `14039`, `16053`) en CRS `EPSG:4326`.
- **Automatización:** Ejecución diaria programada en `.github/workflows/captura_diaria.yml` (13:00 UTC / 07:00 CST), registrando latencia y estado en `calidad/bitacora_captura.csv` (`100.0%` disponibilidad operativa).

---

## 4. Preprocesamiento, Puertas de Calidad y Linaje
1. **Puerta 1 (`pipeline/limpieza_plata.py`):** Valida formato de fechas (`2020–2027`), positividad de precios (`> 0`), coherencia lógica ($P_{\min} \le P_{\text{frecuente}} \le P_{\max}$), homologa entidades regionales (`"Tomate Saladette"` -> `"Jitomate Saladette"`) y deduplica por observación diaria. Cualquier registro inválido **se envía a `data/cuarentena/rechazos_plata.csv`** con motivo explícito (nunca borrado silencioso).
2. **Tratamiento de atípicos:** Etiquetado por rango intercuartílico (**IQR**) por grupo `(producto, plaza_id)`, generando `precio_frecuente_limpio` sin alterar el valor bruto auditado `precio_frecuente_mxn`.
3. **Unión espacial (`pipeline/enriquecer_geo.py`):** Validación geográfica dentro de México (`14°–33° N`, `86°–119° W`), `within` punto-en-polígono (`100.0%` de emparejamiento) y distancia Haversine a la Central de Abasto.
4. **Linaje por registro (`pipeline/construir_oro.py`):** Cada fila incluye `_linaje_fuente_precios`, `_linaje_fuente_macro`, `_linaje_fuente_geo`, `_linaje_fecha_captura_sniim`, `_linaje_fecha_proceso_oro_utc` y `_linaje_version_pipeline`.

---

## 5. Usos Recomendados y Usos NO Recomendados
- **Usos recomendados:**
  - Planeación de compras, cobertura de inventario y comparación regional mayorista para cocinas económicas, restaurantes, tianguis y abarroteras.
  - Modelado de series de tiempo agroalimentarias, análisis multivariado regional (PCA/MANOVA) y estudios académicos reproducibles sobre inflación alimentaria.
- **Usos NO recomendados:**
  - **No inferir precios minoristas de mostrador al consumidor final** (los datos reflejan cotizaciones **mayoristas** por caja, arpilla o kilogramo en Centrales de Abasto).
  - **No utilizar como prospección telefónica o de domicilio** (PII suprimida deliberadamente bajo LFPDPPP).
  - **No extrapolar densidad DENUE fuera del radio de 2.5 km** ni comparar en bruto productos agregados que solo cuentan con ventana reciente frente a los 6 productos base históricos de 59 meses.

---

## 6. Distribución y Mantenimiento
- **Licencia:** `CC BY 4.0` compatible con Libre Uso MX (ver [LICENSE-DATA.md](../../LICENSE-DATA.md)).
- **Acceso público:** Repositorio oficial en GitHub (`AdolfOrtega/tdl-canastita-proyecto`), tablero interactivo Streamlit con botón de descarga directa y scripts reproducibles con verificación `pytest` y `Puerta 2 CI`.
- **Mantenimiento:** Actualización diaria automatizada vía GitHub Actions y verificación continua de integridad ISO/IEC 25012 (`>= 95%` completitud obligatoria, `0` secretos, `0` PII).
