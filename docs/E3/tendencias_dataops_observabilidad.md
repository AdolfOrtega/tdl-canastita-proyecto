# Tendencia Aplicada: DataOps, Observabilidad de Datos y DevSecOps en TDL Canastita

**Proyecto:** Trusted Data Lab — TDL Canastita (Occidente)  
**Autora:** Andrea Tairi Velazquez Gallardo (`23460539@colima.tecnm.mx`)  
**Alcance:** Aplicacion directa de practicas modernas de DataOps y Observabilidad sobre el observatorio en produccion.

---

## 1. Por que DataOps y Observabilidad en un Observatorio de Datos
Los pipelines tradicionales fallan en silencio: el codigo corre sin lanzar excepciones, pero entrega tablas vacias, fechas congeladas o precios corruptos. Para un observatorio publico orientado a decisiones comerciales reales (cocinas y comercios de Colima), el enfoque **DataOps + Observabilidad de Datos** convierte la calidad en controles automatizados en tiempo de ejecucion, inspirados en los cinco pilares de observabilidad moderna (**Frescura, Volumen, Esquema, Distribucion y Linaje**).

---

## 2. Mapeo de los Pilares de Observabilidad sobre Nuestra Arquitectura

| Pilar de Observabilidad / DataOps | Mecanismo Implementado Hoy en `tdl-canastita-proyecto` | Evidencia Verificable |
| :--- | :--- | :--- |
| **1. Frescura (*Freshness*)** | Ejecucion diaria automatizada a las `13:00 UTC` via GitHub Actions (`captura_diaria.yml`) y comparacion del ultimo periodo `anio_mes` en `evaluar_iso_25010_25012.py`. | `calidad/bitacora_captura.csv` (`100.0%` disponibilidad en corridas diarias hasta `2026-11-26`). |
| **2. Volumen y Completitud** | Registro de `registros_capturados` en bitacora y conteo obligatorio de no-nulos por columna bajo **ISO/IEC 25012** en Capa Oro. | `15,521` registros Plata y `967` filas Oro con `100.0%` completitud obligatoria. |
| **3. Esquema y Puerta 1** | Validacion de tipos, fechas y reglas de negocio ($P_{\min} \le P_{\text{frec}} \le P_{\max}$) con desvio determinista hacia cuarentena. | `data/cuarentena/rechazos_plata.csv` (`13` registros corruptos aislados sin contaminar Oro). |
| **4. Distribucion Estadistica (Drift)** | Deteccion univariada por rango intercuartilico (**IQR**) en Capa Plata y monitoreo multivariado de anomalias mediante distancia de **Mahalanobis ($D^2$ vs $\chi^2_7$)** en E3. | `831` banderas IQR en Plata + `laboratorio/pca_proyeccion_oro_e3.csv`. |
| **5. Linaje (*Lineage*)** | Columnas `_linaje_fuente_*` y `_linaje_fecha_*` en cada fila de Capa Oro mas grafo criptografico SHA-256 de punta a punta. | `data/oro/linaje_oro.json` (`TDL-Canastita-Lineage-v2.0`, pipeline `3.0-E3`). |
| **6. DevSecOps (Puerta 2 CI)** | Validacion automatica en cada `push`/`pull_request` verificando `py_compile`, pruebas `pytest >= 60%`, `0` secretos, `0` PII (LFPDPPP) y `0` rutas locales. | `.github/workflows/ci_calidad.yml` + `calidad/evaluar_iso_25010_25012.py --verificar-seguridad`. |

---

## 3. Siguiente Paso Evolutivo hacia E4 y Produccion Continua
1. **Alertas activas de deriva (*Data Drift*):** Activar aviso automatico cuando un lote semanal supere el percentil 99 de distancia de Mahalanobis o caiga la tasa de filas capturadas por central de abasto.
2. **Gobierno de IA (ISO/IEC 42001) como trazabilidad metodologica:** Documentar en cada entrega que porcion de codigo asistido por IA fue validada con pruebas deterministas y supuestos estadisticos auditables por el equipo antes de integrarse a `main`.
