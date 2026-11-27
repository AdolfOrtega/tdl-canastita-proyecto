# Evaluacion del Proceso frente a MoProSoft, CMMI, SPICE e ISO 9001 (E3)

**Proyecto:** Trusted Data Lab — TDL Canastita (Occidente)  
**Autora:** Andrea Tairi Velazquez Gallardo (`23460539@colima.tecnm.mx`)  
**Revision ISO:** Adolfo Rodriguez (`23460528@colima.tecnm.mx`)  

---

## 1. Autoevaluacion frente a MoProSoft (`NMX-I-059-NYCE`)

MoProSoft esta disenado especificamente para equipos y organizaciones pequenas de software en Mexico, estructurado en tres categorias de procesos. Evaluamos nuestra operacion real de E0 a E3:

| Categoria | Proceso MoProSoft | Nivel de Capacidad Alcanzado | Evidencia Concreta en el Repositorio | Brecha Identificada (Que falta para Nivel 3–4) |
| :--- | :--- | :---: | :--- | :--- |
| **Alta Direccion** | Gestion de Negocio (`GN`) | **Nivel 2 (Gestionado)** | Definicion de valor comercial en `docs/E0/propuesta.md` y cliente piloto (*Restaurante Luisiana*). | Falta formalizar indicadores financieros trimestrales de costo operativo vs suscripcion (meta E4). |
| **Gerencia** | Gestion de Proyectos (`GP`) | **Nivel 2 (Gestionado)** | Entregables por hitos (`e0`..`e3`), bitacoras PSP de tiempo y plan de riesgos en `docs/E1/plan_sqa_ieee730.md`. | Estimaciones iniciales sin linea base parametrica formal entre sprints. |
| **Gerencia** | Gestion de Recursos (`GR`) | **Nivel 1 (Realizado)** | Roles cruzados documentados y entorno `.venv` reproducible con `requirements.txt`. | Falta registro automatizado de horas de capacitacion y matriz formal de competencias. |
| **Operacion** | Administracion de Proyectos Especificos (`APE`) | **Nivel 2 (Gestionado)** | Relatorias cronologicas (`relatoria-E1..E3.md`), trazabilidad de commits por integrante y gestion de issues. | Automatizar tableros de valor ganado o burndown por etapa. |
| **Operacion** | Desarrollo y Mantenimiento de Software (`DMS`) | **Nivel 3 (Establecido)** | Arquitectura Medallion documentada, Puerta 1 cuarentena, Puerta 2 CI en GitHub Actions (`pytest >= 80%`) y verificacion ISO 25010/25012. | Incorporar analisis estatico de estilo (`ruff` / `mypy`) bloqueante en CI junto con pruebas unitarias. |

**Diagnostico MoProSoft Global:** **Nivel de Madurez 2 (Gestionado)** consolidado en Gerencia y Operacion, con practicas estandarizadas de **Nivel 3** en verificacion, validacion y control de configuracion (`DMS`).

---

## 2. Autoevaluacion frente a CMMI (Areas de Practica Aplicables)

| Area de Practica CMMI | Nivel Alcanzado | Evidencia en TDL Canastita | Brecha Concreta para Siguiente Nivel |
| :--- | :---: | :--- | :--- |
| **Planning (`PLAN`)** | Nivel 2 | Cronograma E0–E4, estimacion previa por etapa y seguimiento en `calidad/tiempo-*.csv`. | Integrar estimaciones con banda de confianza basada en varianza historica PROBE. |
| **Requirements Management (`RDM`)** | Nivel 2 | Requerimientos verificables en `docs/E1/plan_sqa_ieee730.md` trazados a pruebas `pytest`. | Matriz bidireccional automatica entre cada requisito y su caso de prueba. |
| **Technical Solution (`TS`)** | Nivel 3 | Arquitectura Medallion desacoplada (`extractores -> pipeline -> laboratorio -> tablero`) + fallback multiplataforma. | Contenedorizacion (Docker) para eliminar diferencias residuales de sistema operativo local. |
| **Verification & Validation (`VV`)** | Nivel 3 | Puerta 1 (cuarentena), Puerta 2 (CI `pytest` + seguridad), Puerta 3 (supuestos ANOVA/MANOVA), pruebas E2E `AppTest`. | Pruebas de carga continua sobre volumen de datos 10x superior al actual. |
| **Process Quality Assurance (`PQA`)** | Nivel 3 | Evaluacion objetiva con `evaluar_iso_25010_25012.py`, auditoria con `auditor_tdl.py` y roles alternos de *Quality Lead*. | Auditorias externas periodicas automatizadas sobre el repositorio de otros equipos pares. |
| **Configuration Management (`CM`)** | Nivel 3 | Git con etiquetas inmutables `e0`, `e1`, `e2`, `e3`, proteccion `.env` en `.gitignore` y hashes SHA-256 en `linaje_oro.json`. | Uso obligatorio de ramas `feature/*` con Pull Requests revisados antes de integrar a `main`. |
| **Managing Performance & Measurement (`MPM`)** | Nivel 2 | Medicion continua de disponibilidad (bitacora `100%`), benchmark $2^3$ (`lxml+Parquet`) y retrospectiva PSP E0–E3. | Graficas de control estadistico de procesos (SPC / X-barra) continuas en produccion (Nivel 4). |

---

## 3. Cuadro Comparativo de Marcos y Estandares de Calidad de Proceso

| Estandar / Modelo | Alcance Principal | Estructura | Nivel de Granularidad | Complemento en TDL Canastita |
| :--- | :--- | :--- | :--- | :--- |
| **ISO 9001:2015** | Sistema de Gestion de Calidad (SGC) generico para cualquier organizacion. | Requisitos auditables basados en ciclo **PHVA** y enfoque a procesos/riesgos. | Organizacional (politicas, no conformidades, acciones correctivas). | Marca el marco de mejora continua y cierre formal de hallazgos de auditoria (`docs/E3/cierre_auditoria.md`). |
| **MoProSoft (`NMX-I-059-NYCE`)** | Norma mexicana para PyMEs y grupos pequenos de desarrollo de software. | 3 categorias (`Alta Direccion`, `Gerencia`, `Operacion`) y niveles de capacidad `0–5`. | Equipo pequeno / proyecto especifico (`APE`, `DMS`). | Guia nuestra autoevaluacion realista de equipo de 2 personas con roles cruzados. |
| **SPICE (`ISO/IEC 15504` -> `ISO/IEC 33000`)** | Evaluacion estandarizada de capacidad de procesos de software y sistemas. | Dimension de proceso + dimension de capacidad (`Niveles 0 a 5`: Incompleto a Optimizado). | Evaluacion objetiva por atributos de proceso (`PA`). | Da el criterio riguroso de evidencia objetiva (bitacoras, reportes CI, metricas) para calificar capacidades. |
| **CMMI v2.0** | Modelo integral de madurez organizacional para ingenieria de sistemas y software. | Niveles de madurez `1–5` y areas de practica (Ingenieria, Gestion, Soporte). | Institucional / empresarial. | Estructura nuestras areas de verificacion (`VV`), configuracion (`CM`) y aseguramiento (`PQA`). |
| **PSP / TSP** | Disciplina individual (`PSP`) y de equipo autodirigido (`TSP`) en ingenieria de software. | Bitacoras personales de tiempo, 10 tipos de defectos, revisiones y retrospectivas metricas. | **Individual y de pareja** (minuto a minuto y defecto a defecto). | Alimenta los CSV `calidad/tiempo-*.csv` y `defectos-*.csv` para calcular nuestro *Review Yield* real. |
