# Evaluacion Cuantitativa de Calidad bajo ISO/IEC 25010, ISO/IEC 25012 y Antecedentes Normativos

**Proyecto:** TDL Canastita (Occidente)  
**Responsable de Calidad e ISO:** Adolfo Rodriguez (`23460528@colima.tecnm.mx`)  
**Verificacion Estadistica y Auditoria:** Andrea Tairi Velazquez Gallardo (`23460539@colima.tecnm.mx`)  
**Fecha de medicion:** Noviembre 2026 (Entrega E2)

---

## 1. Evaluacion del Producto Software bajo ISO/IEC 25010

Todas las metricas provienen de ejecuciones reales de codigo ([calidad/evaluar_iso_25010_25012.py](../../calidad/evaluar_iso_25010_25012.py)), del laboratorio factorial ([laboratorio/resultados_experimento_e2.json](../../laboratorio/resultados_experimento_e2.json)) y de la bitacora diaria de GitHub Actions ([calidad/bitacora_captura.csv](../../calidad/bitacora_captura.csv)).

| # | Caracteristica ISO/IEC 25010 | Metrica Evaluada | Valor Medido en el Sistema | Umbral Objetivo | Calificacion |
| :---: | :--- | :--- | :--- | :--- | :---: |
| 1 | **Adecuacion funcional** | Fuentes activas integradas, capas Medallion (Bronce/Plata/Oro/Cuarentena/Geo) y tablero operativo | 3/3 fuentes (SNIIM, Banxico, DENUE+MGEM) y 9,650 puntos espaciales | 3 fuentes + 4 capas | **100.0%** |
| 2 | **Eficiencia de desempeno** | Tiempo confirmado del punto optimo 2^3 y ahorro de disco con Parquet | 1.200s vs 1.443s (16.8% menos tiempo); 99.03% menos peso en Parquet | Mejora >= 10% y 0% error | **96.0%** |
| 3 | **Compatibilidad** | Interoperabilidad de formatos heterogeneos integrados al modelo comun | HTML latin-1 + REST JSON + GeoJSON ITRF2008/WGS84 -> UTF-8 CSV/Parquet/GeoJSON | 100% integracion sin perdida | **95.0%** |
| 4 | **Capacidad de interaccion (Usabilidad)** | Cobertura funcional en Streamlit con semaforo de compra, filtros, mapa pydeck e incertidumbre 95% | 5 pestanas interactivas y semaforo comprensible para el cliente (Restaurante Luisiana) | >= 4 vistas ejecutivas | **95.0%** |
| 5 | **Fiabilidad** | Disponibilidad operativa medida A = MTBF/(MTBF+MTTR) y Puerta 1 con cuarentena | 100.0% (48/48 corridas diarias en 307.2h; MTTR=0h) | >= 95.0% | **100.0%** |
| 6 | **Seguridad** | Secretos expuestos en codigo/datos y cumplimiento LFPDPPP (cero PII) | 0 secretos expuestos y 0 columnas PII en 99 archivos | 0 secretos y 0 PII | **100.0%** |
| 7 | **Mantenibilidad** | Complejidad ciclomatica promedio de McCabe y tasa de docstrings en funciones | CC promedio = 4.71, docstrings = 77.38% (84 funciones) | CC promedio <= 6 y doc >= 80% | **82.0%** |
| 8 | **Portabilidad** | Ausencia de rutas locales absolutas y compatibilidad Windows + Linux CI | 0 rutas locales absolutas; fallback puro Python + PyArrow/CSV | 0 rutas locales absolutas | **100.0%** |

* **Indice global medido ISO/IEC 25010:** **`96.00%`** (Escala TecNM: Excelente).
* **Resultado de Seguridad y Privacidad:** `0` secretos expuestos, `0` columnas PII en datos geoespaciales, `.env` protegido en `.gitignore` y no rastreado por Git.

---

## 2. Evaluacion de la Calidad de Datos bajo ISO/IEC 25012 (Capa Oro)

Medida ejecutada directamente sobre los **963 registros analiticos** de [data/oro/canasta_occidente_oro.csv](../../data/oro/canasta_occidente_oro.csv) y su manifiesto de linaje ([data/oro/linaje_oro.json](../../data/oro/linaje_oro.json)):

| Caracteristica ISO/IEC 25012 | Categoria | Evidencia Medida sobre Capa Oro / Geo | Cumplimiento |
| :--- | :--- | :--- | :---: |
| **Exactitud sintactica** | Inherente | 100.0% formatos YYYY-MM validos | **100.0%** |
| **Exactitud semantica** | Inherente | 100.0% coherencia min <= promedio <= max (>0) | **100.0%** |
| **Completitud** | Inherente | 100.0% obligatoria / 98.63% global en 963 filas | **100.0%** |
| **Consistencia** | Inherente | 100.0% coherencia spread y conversion USD | **100.0%** |
| **Credibilidad** | Inherente | 100.0% respaldo oficial SNIIM + Banxico + INEGI | **100.0%** |
| **Actualidad** | Inherente / Sist. | Ultimo periodo 2026-11 al dia con captura diaria (2026-11) | **100.0%** |
| **Accesibilidad** | Inherente / Sist. | Tablero Streamlit + CSV/GeoJSON/Parquet abiertos | **100.0%** |
| **Conformidad** | Inherente / Sist. | ISO 8601 + EPSG:4326 (union espacial 100.0%) + UTF-8 | **100.0%** |
| **Confidencialidad** | Inherente / Sist. | 0 PII (LFPDPPP) y 0 secretos | **100.0%** |
| **Eficiencia** | Inherente / Sist. | Oro Parquet reduce 76.31% frente a CSV (73.1 vs 308.5 KB) | **95.0%** |
| **Precision** | Inherente / Sist. | Decimales homologados (2 MXN, 4 USD/FIX, 3 INPC) | **100.0%** |
| **Trazabilidad** | Inherente / Sist. | 100.0% filas con columnas _linaje_* + linaje_oro.json | **100.0%** |
| **Comprensibilidad** | Inherente / Sist. | 100.0% de columnas (34/34) documentadas en diccionario | **100.0%** |
| **Disponibilidad** | Dependiente Sist. | 100.0% de disponibilidad operativa real | **100.0%** |
| **Portabilidad y Recuperabilidad** | Dependiente Sist. | Versionado Git + hashes SHA-256 + dualidad CSV/Parquet | **100.0%** |

* **Completitud en columnas obligatorias (sin rezagos matematicos MoM/YoY):** **`100.00%`** (supera el umbral del Sello TDL de `>= 95%`).
* **Completitud global en toda la tabla:** **`98.63%`**.
* **Indice global medido ISO/IEC 25012:** **`99.67%`**.

---

## 3. Antecedentes Normativos: Evolucion de ISO/IEC 9126 a SQuaRE (ISO/IEC 25000) e ISO 9001

| Norma / Estandar | Rol Historico y Enfoque Principal | Caracteristicas Clave | Relacion y Aplicacion Directa en TDL Canastita |
| :--- | :--- | :--- | :--- |
| **ISO/IEC 9126** (1991 / rev. 2001) | Primer estandar internacional consolidado para calidad del producto software (antecedente directo del temario). | Definio 6 caracteristicas (Funcionalidad, Fiabilidad, Usabilidad, Eficiencia, Mantenibilidad, Portabilidad) mas calidad en uso. No incluia seguridad ni compatibilidad como pilares propios, ni evaluaba calidad de datos. | Sirvio como base conceptual inicial, pero resultaba insuficiente para un observatorio multifuente donde el dato y la seguridad de tokens son criticos. |
| **Familia ISO/IEC 25000 (SQuaRE)** | **Sucesora oficial** de ISO/IEC 9126 e ISO/IEC 14598 (*Software Product Quality Requirements and Evaluation*). | Organiza la calidad en divisiones: **25010** (modelo del producto con 8 caracteristicas, elevando Seguridad y Compatibilidad) y **25012** (primer modelo dedicado al **producto de datos** con 15 caracteristicas inherentes y dependientes). | Constituye el marco directo de medicion de E2: ISO/IEC 25010 audita el codigo, tablero Streamlit y experimento de eficiencia; ISO/IEC 25012 certifica la Capa Oro, su linaje y completitud >= 95%. |
| **ISO 9001:2015** | Norma internacional de **Sistemas de Gestion de Calidad (SGC)** con enfoque basado en procesos y mejora continua (**ciclo PHVA**). | No evalua un producto tecnologico concreto sino la madurez y control del **proceso** que lo produce (documentacion, auditorias, acciones correctivas, gestion de riesgos). | Complementa a SQuaRE en nuestro observatorio mediante el Plan SQA ([docs/E1/plan_sqa_ieee730.md](../E1/plan_sqa_ieee730.md)), las Puertas de Calidad 1–3, los registros PSP de defectos y las auditorias cruzadas con acciones correctivas cerradas. |
