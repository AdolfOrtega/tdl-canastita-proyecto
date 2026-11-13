# Plan de Aseguramiento de Calidad de Software (SQA) — IEEE Std 730

**Proyecto:** Trusted Data Lab — Canastita (Occidente)  
**Asignatura:** Calidad en Sistemas de Información  
**Docente:** Mtra. Isis Saraí Espinosa Lozano  
**Equipo de Trabajo:**
- **Adolfo Rodríguez** (`23460528@colima.tecnm.mx`) — *Data Engineer & SQA Implementation Lead*
- **Andrea Tairi Velázquez Gallardo** (`23460539@colima.tecnm.mx`) — *Data Statistician & Verification Lead*

**Versión del Documento:** 1.0 (Entrega E1)  
**Fecha:** Noviembre 2026  
**Estándar Aplicado:** IEEE Std 730-2014 (Standard for Software Quality Assurance Processes)

---

## 1. Propósito y Alcance del Plan SQA

El presente Plan de Aseguramiento de Calidad de Software (Software Quality Assurance Plan, SQAP) establece las directrices, estándares, métricas y mecanismos de control aplicados en el observatorio **TDL Canastita**. Su alcance cubre todo el ciclo de vida del dato: desde la ingestión ética en Capa Bronce, el saneamiento y cuarentena en Capa Plata, la integración dimensional en Capa Oro, hasta el modelado estadístico predictivo y la visualización interactiva.

El objetivo central es garantizar que la información entregada a comerciantes de tianguis, abarroteras y cocinas económicas (como el *Restaurante Luisiana* en Colima) posea los más altos estándares de veracidad, trazabilidad, reproducibilidad y disponibilidad.

---

## 2. Estructura Organizacional, Roles y Responsabilidades

| Rol SQA | Integrante Asignado | Responsabilidades Principales |
| :--- | :--- | :--- |
| **SQA Implementation Lead & Data Engineer** | Adolfo Rodríguez | Implementación de pipelines de datos en capas Bronce, Plata y Oro; diseño y ejecución de la suite de pruebas automatizadas (`tests/`); configuración de CI/CD en GitHub Actions; gestión del almacén de cuarentena; registro de defectos y tiempos PSP. |
| **Verification Lead & Data Statistician** | Andrea Tairi Velázquez Gallardo | Auditoría de calidad cruzada; diseño del protocolo de validación estadística (pruebas ADF, descomposición, métricas MAPE/RMSE); supervisión de cumplimiento de directrices IEEE 730; verificación de diccionarios de datos y trazabilidad de requerimientos. |

---

## 3. Documentos de Referencia y Normatividad

1. **IEEE Std 730-2014:** Standard for Software Quality Assurance Processes.
2. **IEEE Std 829-2008:** Standard for Software and System Test Documentation.
3. **PEP 8:** Style Guide for Python Code.
4. **Lineamientos de Datos Abiertos de México:** Portal SNIIM (Secretaría de Economía) y API SIE de Banco de México.
5. **Guía Integrada del Proyecto:** Instituto Tecnológico de Colima (TecNM), Semestre Agosto-Diciembre 2026.

---

## 4. Estándares y Directrices Técnicas del Proyecto

### 4.1 Estándar de Codificación y Calidad de Código
- **Lenguaje:** Python 3.12+.
- **Estilo:** Apego estricto a PEP 8.
- **Tipado Defensivo:** Coerción de tipos con `errors="coerce"` en lecturas de datos externos para evitar detenciones no controladas del pipeline.
- **Manejo de Errores y Registro:** Bitácoras estructuradas utilizando el módulo estándar `logging` con marcas temporales UTC y niveles `INFO`, `WARNING` y `ERROR`.

### 4.2 Control de Versiones y Gestión de Configuración (SCM)
- Repositorio oficial en GitHub: `tdl-canastita-proyecto`.
- Estrategia de ramas: Rama principal `main` protegida contra modificaciones directas no validadas; etiquetado semántico formal para entregables (`tag e0`, `tag e1`).
- Los datos intermedios y finales poseen archivos de metadatos `.meta.json` con firma criptográfica SHA-256 para detectar cualquier alteración no autorizada del contenido.

---

## 5. Arquitectura de Puertas de Calidad (Quality Gates)

Para asegurar la confiabilidad del dato a lo largo de la arquitectura Medallion, se definieron cuatro puertas de inspección rigurosa:

```
[Fuentes Externas: SNIIM / Banxico]
                │
         (Puerta 0: Extracción Ética & Trazabilidad)
                ▼
        [data/bronce/] (Raw Data + .meta.json + SHA-256)
                │
         (Puerta 1: Validación de Esquema & Reglas de Negocio)
                ├─── Rechazados ──► [data/cuarentena/rechazos_plata.csv]
                │
                ▼
        [data/plata/] (Limpieza + Deduplicación + IQR Clipping)
                │
         (Puerta 2: Integridad Referencial & Cruce Multifuente)
                ▼
        [data/oro/] (Agregación Mensual + FIX + INPC + Métricas Derivadas)
                │
         (Puerta 3: Validación Estadística & Fuera de Muestra)
                ▼
     [laboratorio/ & tablero/] (Modelos ARIMA/Holt-Winters + Streamlit)
```

### Detalle de Puertas de Calidad:

1. **Puerta 0 (Extracción Ética y Auditoría):**
   - Validación previa de `robots.txt` del dominio objetivo.
   - Inclusión obligatoria del User-Agent identificativo con correo institucional (`23460528@colima.tecnm.mx`).
   - Tiempos de espera adaptativos ($>1.0$ s) para no saturar servidores públicos.
   - Registro de toda extracción en `calidad/bitacora_captura.csv`.

2. **Puerta 1 (Bronce a Plata — Sanidad y Cuarentena):**
   - **Regla 1 (Fechas):** Fechas obligatorias, formato válido (`DD/MM/YYYY` o ISO), acotadas entre 2020 y 2027.
   - **Regla 2 (Positividad):** Precios estrictamente positivos ($P_{\min} > 0, P_{\max} > 0, P_{\text{frecuente}} > 0$).
   - **Regla 3 (Consistencia Lógica):** $P_{\min} \le P_{\text{frecuente}} \le P_{\max}$. Si $P_{\max} < P_{\min}$, se rechaza inmediatamente.
   - **Manejo de Cuarentena:** Todo registro que viole alguna regla se aísla en `data/cuarentena/rechazos_plata.csv` preservando la fecha de descarte, motivo del rechazo y el registro original sin alterar.
   - **Regla 4 (Atípicos IQR):** Detección estadística mediante $[Q1 - 1.5 \times IQR, Q3 + 1.5 \times IQR]$. Los valores extremos son etiquetados con bandera booleana (`es_atipico_iqr`) y suavizados en `precio_frecuente_limpio` sin perder el precio original observado.

3. **Puerta 2 (Plata a Oro — Integración y Trazabilidad):**
   - Agregación mensual consistente.
   - Integridad referencial con series macroeconómicas de Banco de México (tipo de cambio FIX e INPC). No se admiten pérdidas de observaciones por diferencias de clave temporal (`anio_mes`).
   - Verificación de continuidad temporal ($\ge 36$ períodos mensuales continuos para cada producto prioritario).

4. **Puerta 3 (Oro a Modelado Predictivo — Validez Estadística):**
   - Validación cruzada en ventana temporal fuera de muestra (Train: 51 meses, Test: 8 meses).
   - Umbral de aceptación de error: Modelo seleccionado debe minimizar el MAPE (buscando $\le 20\%$ en insumos no sujetos a crisis climáticas severas).
   - Cálculo de bandas de confianza al 95% para advertir al usuario del margen de incertidumbre.

---

## 6. Métrica de Disponibilidad y Confiabilidad en Producción

Con base en la bitácora de captura real generada por el pipeline en producción (`calidad/bitacora_captura.csv`) y los flujos automatizados de GitHub Actions ejecutados diariamente:

### 6.1 Datos Observados en Operación
- **Período de Monitoreo:** Noviembre 6 a Noviembre 12 de 2026.
- **Total de ejecuciones registradas:** 30 corridas.
- **Ejecuciones programadas de producción (GitHub Actions Cron):** 27 corridas.
- **Ejecuciones exitosas en producción:** 27 de 27.
- **Tasa de fallos en producción:** 0 fallos.

### 6.2 Fórmulas de Confiabilidad y Disponibilidad (IEEE 730)
- **MTBF (Mean Time Between Failures):**
  $$\text{MTBF} = \frac{\text{Tiempo Total de Operación}}{\text{Número de Fallas}} = \frac{144 \text{ horas}}{0 \text{ fallas}} \rightarrow \infty$$
- **MTTR (Mean Time To Repair):**
  $$\text{MTTR} = \frac{\text{Tiempo Total de Inactividad por Reparación}}{\text{Número de Fallas}} = \frac{0 \text{ horas}}{0} = 0 \text{ horas}$$
- **Disponibilidad Operativa ($A$):**
  $$A = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}} \times 100\% = \frac{144}{144 + 0} \times 100\% = 100.0\%$$

> **Evaluación SQA:** El observatorio supera ampliamente la meta comprometida de disponibilidad ($\ge 95\%$), manteniendo una disponibilidad del **100%** durante su primera semana completa de captura autónoma programada.

---

## 7. Estrategia de Pruebas y Cobertura de Código

En atención directa a la recomendación docente de la Entrega E0 (*"Robustecer la suite tests/ antes de procesar las transformaciones de la capa Plata"*), se diseñó e implementó una suite integral de 11 pruebas automatizadas con `pytest` y `pytest-cov`:

| Módulo de Pruebas | Casos de Prueba Implementados | Objetivo Verificado |
| :--- | :--- | :--- |
| `tests/test_extractores.py` | 5 pruebas unitarias | Extracción ética con User-Agent institucional; scraping de tablas HTML de SNIIM; manejo de tablas vacías; serie histórica $\ge 36$ meses; integridad y cálculo de SHA-256. |
| `tests/test_pipeline.py` | 6 pruebas de integración | Resolución y homologación de entidades; Puerta 1 con separación de registros corruptos a cuarentena; detección de atípicos IQR y clipeo; join multifuente de Capa Oro con Banxico; cálculo de métricas de variación MoM y YoY; generación de artefactos finales Oro y Plata. |

### Resultado de Cobertura de Código:
```text
Name                         Stmts   Miss  Cover
------------------------------------------------
pipeline\__init__.py             0      0   100%
pipeline\construir_oro.py      105     12    89%
pipeline\limpieza_plata.py     133      9    93%
------------------------------------------------
TOTAL                          238     21    91%
```
- **Meta establecida:** $\ge 60\%$ de cobertura de pruebas.
- **Resultado obtenido:** **91% de cobertura**, certificando que toda la lógica de negocio, validación, cuarentena y transformaciones analíticas está cubierta por pruebas automatizadas.

---

## 8. Gestión de Defectos y Personal Software Process (PSP)

Cada integrante del equipo mantuvo un registro diario riguroso de defectos encontrados y tiempos dedicados en `calidad/`:

1. **Clasificación de Defectos:** Documentación, Entorno, Sistema, Datos, Lógica.
2. **Ciclo de Defecto:** Registro de la fase donde se introdujo (Planeación, Diseño, Código) vs la fase donde fue eliminado (Pruebas, Revisión) y los minutos requeridos para su corrección.
3. **Archivos de Auditoría PSP:**
   - [defectos-adolfo.csv](../../calidad/defectos-adolfo.csv) (8 defectos gestionados y resueltos).
   - [tiempo-adolfo.csv](../../calidad/tiempo-adolfo.csv) (10 sesiones de trabajo registradas).
   - [defectos-andrea.csv](../../calidad/defectos-andrea.csv) (6 defectos gestionados y resueltos).
   - [tiempo-andrea.csv](../../calidad/tiempo-andrea.csv) (10 sesiones de trabajo registradas).

---

## 9. Conclusiones y Estado de Calidad en E1

El plan SQA ejecutado demuestra que el observatorio **TDL Canastita** opera bajo controles de calidad de nivel profesional:
1. Las anomalías de datos crudos no contaminan las capas analíticas gracias al aislamiento activo en **cuarentena**.
2. Los modelos de pronóstico se alimentan exclusivamente de datos validados y certificados en **Capa Oro**.
3. La suite de pruebas robustecida con **91% de cobertura** garantiza que cualquier cambio o integración futura en GitHub Actions mantendrá la integridad del sistema.
