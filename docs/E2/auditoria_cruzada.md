# Protocolo de Auditoria de Calidad e Informe de Auditoria Cruzada (Entrega E2)

**Proyecto:** Trusted Data Lab — TDL Canastita (Occidente)  
**Auditora Responsable:** Andrea Tairi Velazquez Gallardo (`23460539@colima.tecnm.mx`)  
**Herramienta Automatizada:** [calidad/auditor_tdl.py](../../calidad/auditor_tdl.py)  
**Marcos Normativos:** ISO/IEC 25010 (Software), ISO/IEC 25012 (Datos) e ISO 19011 (Directrices para la auditoria de sistemas de gestion)

---

## 1. Criterios de Clasificacion de Hallazgos

| Severidad | Definicion Operativa | Impacto en Sello TDL / Entrega |
| :--- | :--- | :--- |
| **CRITICO** | Exposicion de credenciales/secretos reales o PII (LFPDPPP), ausencia de pruebas automatizadas o captura rota (< 70% disponibilidad), o borrado silencioso sin cuarentena. | Bloquea la obtencion del Sello TDL; exige cierre inmediato antes de E3. |
| **MAYOR** | Incumplimiento parcial de normas ISO 25010/25012 o arquitectura TDL (ej. falta de CI automatico en cada `push`, ausencia de trazabilidad/linaje por fila o cobertura < 60%). | Debe atenderse con accion correctiva y commit verificable antes de E3. |
| **MENOR** | Desviacion cosmetica, inconsistencia menor en UI o documentacion no critica (ej. metricas fijas en tablero o ausencia de descripcion en repositorio). | Recomendado corregir en ciclo de mejora continua. |

---

## 2. Seccion 1 — Auditoria Interna de Linea Base sobre Corte `tag: e1` (`tdl-canastita-proyecto`)

Con el fin de validar el instrumento [calidad/auditor_tdl.py](../../calidad/auditor_tdl.py) antes de recibir el repositorio asignado para auditoria cruzada, la *Quality Auditor* inspecciono formalmente el estado congelado de nuestro propio repositorio en la etiqueta **`e1`** (commit `7b114e9`):

| ID | Severidad | Area / Norma | Evidencia Detectada en Corte `e1` | Recomendacion Emitida | Estado al Cierre de E2 |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **INT-01** | **MAYOR** | Puerta 2 CI / ISO 25010 Mantenibilidad | En el corte `e1` solo existia [.github/workflows/captura_diaria.yml](../../.github/workflows/captura_diaria.yml) con disparador `schedule`, sin flujo automatico de CI que corriera `pytest` y verificacion de seguridad en cada `push`. | Crear workflow en `.github/workflows/` disparado en `push` y `pull_request` sobre `main`. | **Cerrado** (commit `c25d23e`, [.github/workflows/ci_calidad.yml](../../.github/workflows/ci_calidad.yml)). |
| **INT-02** | **MAYOR** | Trazabilidad / ISO 25012 | `data/oro/canasta_occidente_oro.csv` en `e1` incluia metadatos agregados pero carecia de columnas de linaje a nivel registro (`_linaje_*`) y de manifiesto de grafo completo. | Inyectar columnas `_linaje_fuente_*` y `_linaje_fecha_captura_sniim` por fila + `data/oro/linaje_oro.json`. | **Cerrado** (commit `7931e51`, [pipeline/construir_oro.py](../../pipeline/construir_oro.py)). |
| **INT-03** | **MENOR** | Tablero / Precision | En `tablero/app.py` (pestana 3 del corte `e1`), los KPIs de disponibilidad (`100.0%`) y cobertura (`91.0%` / `11 / 11`) estaban declarados como texto estatico y desfasados de los 15 tests reales. | Leer dinamicamente `calidad/bitacora_captura.csv` y los JSON de ISO/pytest. | **Cerrado** (commit `c25d23e`, [tablero/app.py](../../tablero/app.py)). |
| **INT-04** | **MENOR** | Portabilidad | Durante la revision previa al cierre `e1` se detectaron enlaces `file:///c:/Users/...` en markdown (corregidos en el ultimo commit de `e1`: `7b114e9`). | Mantener verificacion automatica de 0 rutas locales en Puerta 2 CI. | **Cerrado y monitoreado** (`evaluar_iso_25010_25012.py --verificar-seguridad`). |

**Resultado de ejecucion actual de `python calidad/auditor_tdl.py .`:**
`CRITICO: 0 | MAYOR: 0 | MENOR: 0` (Disponibilidad diaria medida: `100.0%`).

---

## 3. Seccion 2 — Auditoria Cruzada al Equipo Par (Estado: Pendiente de Asignacion Docente)

> **Constancia de estado a la fecha de entrega E2 (19–20 de noviembre de 2026):**  
> Hasta este momento, los docentes de la asignatura aun no han publicado la matriz oficial de asignacion de equipos pares ni el enlace al repositorio externo a auditar, ni han registrado issues previos de E1 en nuestro repositorio.  
> El equipo deja **completamente listo el instrumento automatizado y el formato consultivo de auditoria** para ejecutar la inspeccion en cuanto se notifique el repositorio par asignado y anexar el dictamen mediante commit previo a E3.

### Instrumento y Lista de Cotejo Preparada para el Equipo Par

Comando reproducible de inspeccion inicial sobre el clon del equipo par en su etiqueta `e1`:

```bash
git clone <URL_REPO_EQUIPO_PAR> repo_par
cd repo_par && git checkout e1 && cd ..
python calidad/auditor_tdl.py repo_par
```

| ID | Severidad | Criterio (ISO 25010 / 25012) | Evidencia Verificada en Repo Par (`e1`) | Recomendacion Accionable |
| :---: | :---: | :--- | :--- | :--- |
| **PAR-01** | *Pendiente* | Seguridad y LFPDPPP | *En espera de asignacion de repositorio par.* | — |
| **PAR-02** | *Pendiente* | Disponibilidad y Bitacora >= 95% | *En espera de asignacion de repositorio par.* | — |
| **PAR-03** | *Pendiente* | Completitud Capa Oro >= 95% y Cuarentena | *En espera de asignacion de repositorio par.* | — |
| **PAR-04** | *Pendiente* | Cobertura `pytest` >= 60% y Reproducibilidad | *En espera de asignacion de repositorio par.* | — |
