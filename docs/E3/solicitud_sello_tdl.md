# Solicitud Formal del Sello TDL (Entrega E3)

**Proyecto:** Trusted Data Lab — TDL Canastita (Occidente)  
**Repositorio:** `https://github.com/AdolfOrtega/tdl-canastita-proyecto`  
**Equipo:** Adolfo Rodríguez (`23460528@colima.tecnm.mx`) y Andrea Tairi Velázquez Gallardo (`23460539@colima.tecnm.mx`)  
**Herramienta de Verificación:** [calidad/auditor_tdl.py](../../calidad/auditor_tdl.py) (`python calidad/auditor_tdl.py . --sello`)

---

## Tabla Probatoria de los 6 Umbrales Mínimos Obligatorios

| # | Criterio del Sello TDL | Umbral Mínimo | Valor Medido Actual | Evidencia Verificable en Repositorio | Cumple |
| :---: | :--- | :---: | :---: | :--- | :---: |
| 1 | **Disponibilidad medida de captura** | `>= 95%` (últimos 14 días) | **`100.00%`** | [calidad/bitacora_captura.csv](../../calidad/bitacora_captura.csv) (todas las corridas diarias `EXITO`, MTTR `0 h`) | **SÍ** |
| 2 | **Completitud de Capa Oro (ISO/IEC 25012)** | `>= 95%` | **`100.00%`** obligatoria / `98.64%` global | [calidad/resultados_iso_25012.json](../../calidad/resultados_iso_25012.json) + `canasta_occidente_oro.csv` (`967` filas) | **SÍ** |
| 3 | **Cobertura de pruebas automáticas** | `>= 60%` | **`>= 80%`** (suite ampliada en E3) | `.github/workflows/ci_calidad.yml` (`--cov-fail-under=60`) + `tests/` | **SÍ** |
| 4 | **Secretos expuestos en repositorio** | `0` | **`0`** | `calidad/evaluar_iso_25010_25012.py --verificar-seguridad` + `.gitignore` | **SÍ** |
| 5 | **Hallazgos críticos de auditoría abiertos** | `0` | **`0`** (`CRITICO: 0`, `MAYOR: 0`, `MENOR: 0`) | [docs/E3/cierre_auditoria.md](cierre_auditoria.md) + `calidad/solicitud_sello_tdl.json` | **SÍ** |
| 6 | **Reproducibilidad y Dataset Abierto** | Reproducible | **`6/6` validado** | [README.md](../../README.md), [LICENSE-DATA.md](../../LICENSE-DATA.md) (`CC BY 4.0`) y [datasheet_canasta_oro.md](datasheet_canasta_oro.md) | **SÍ** |

---

**Dictamen Automatizado (`calidad/solicitud_sello_tdl.json`):** `apto_sello_tdl = true` (**6 / 6 criterios cumplidos**). Se solicita formalmente la evaluación y otorgamiento del **Sello TDL** para el observatorio *TDL Canastita (Occidente)*.
