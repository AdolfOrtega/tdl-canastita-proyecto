# Cierre de Auditoria y Trazabilidad de Hallazgos (Entrega E3)

**Proyecto:** Trusted Data Lab — TDL Canastita (Occidente)  
**Auditora Responsable:** Andrea Tairi Velazquez Gallardo (`23460539@colima.tecnm.mx`)  
**Responsable Tecnico de Correccion:** Adolfo Rodriguez (`23460528@colima.tecnm.mx`)

---

## 1. Verificacion de Issues Externos y Auditoria Cruzada
- **Consulta automatizada a la API de GitHub (`repos/AdolfOrtega/tdl-canastita-proyecto/issues?state=all`):** `0` issues abiertos y `0` cerrados por docentes o equipos pares al 27 de noviembre de 2026 (`open_issues_count = 0`).
- **Estado de asignacion par:** Como complemento proactivo a la auditoria interna sobre `tag: e1` ([docs/E2/auditoria_cruzada.md](../E2/auditoria_cruzada.md)), durante E3 se mantuvieron vigiladas tanto las 4 acciones previas (`INT-01`..`INT-04`) como 2 hallazgos adicionales identificados en la revision pre-E3, dejando **`0` hallazgos criticos, `0` mayores y `0` menores abiertos**.

---

## 2. Matriz Completa de Hallazgos Cerrados (Linea Base E1 -> E3)

| ID | Severidad | Origen | Hallazgo Detectado | Accion Correctiva y Commit | Estado Final |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **INT-01** | **MAYOR** | Auditoria interna `e1` | Falta de integracion continua automatica (`pytest` + seguridad) en cada `push` a `main`. | Creacion de `.github/workflows/ci_calidad.yml` (commit `c25d23e`, ampliado en E3 para modulos multivariados y benchmark). | **Cerrado** |
| **INT-02** | **MAYOR** | Auditoria interna `e1` | Ausencia de columnas de linaje a nivel fila (`_linaje_*`) y grafo SHA-256 en Capa Oro. | Implementacion en `pipeline/construir_oro.py` + `data/oro/linaje_oro.json` (commit `7931e51`, actualizado a `3.0-E3`). | **Cerrado** |
| **INT-03** | **MENOR** | Auditoria interna `e1` | KPIs estaticos en la Pestana 3 del tablero Streamlit desfasados de la bitacora real. | Lectura dinamica desde `calidad/bitacora_captura.csv` y JSONs ISO (commit `c25d23e`). | **Cerrado** |
| **INT-04** | **MENOR** | Auditoria interna `e1` | Posibles rutas locales absolutas en documentacion Markdown y advertencias UI. | Eliminacion total + regex bloqueante en Puerta 2 CI (commit `7b114e9` y `4e1e367`). | **Cerrado** |
| **E3-AUD-01** | **MENOR** | Revision pre-E3 | Descripciones `#5` y `#9` en `defectos-andrea.csv` contenian comas sin comillas generando `ParserError` en `pandas`. | Entrecomillado estandar RFC-4180 verificado con `csv.reader` y `pandas.read_csv` (commit `37ef180`). | **Cerrado** |
| **E3-AUD-02** | **MAYOR** | Revision arquitectura E3 | La configuracion ganadora del experimento $2^3$ (`1 hilo + lxml + Parquet`) seguia solo en laboratorio y faltaba aplicarla en el extractor y pipeline real con benchmark. | Implementado `parser="lxml"` con fallback y escritura/lectura `.parquet` en Bronce + benchmark `benchmark_optimizacion_e3.py`. | **Cerrado** |

---

## 3. Verificacion de Ejecucion de Auditoria Automatizada (`calidad/auditor_tdl.py .`)
- **Hallazgos CRITICOS:** `0`
- **Hallazgos MAYORES:** `0`
- **Hallazgos MENORES:** `0`
- **Veredicto:** Apto para obtener el **Sello TDL**.
