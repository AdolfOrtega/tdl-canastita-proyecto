# TDL Canastita (tdl-canastita-proyecto)

**Observatorio de Precios de la Canasta Básica, Inflación y Pronósticos Mayoristas en el Occidente (Colima, Guadalajara y Morelia)**  
Proyecto Integrador — Tecnológico Nacional de México (Campus Colima) — Semestre Ago-Dic 2026

## Integrantes y Roles

* **Adolfo Rodríguez** (`23460528@colima.tecnm.mx`) — **Data Engineer & SQA Implementation Lead**  
  Encargado de los extractores éticos, arquitectura Medallion (Bronce, Plata, Oro), Puerta 1 de calidad, cuarentena de datos, suite de pruebas automatizadas y CI/CD.
* **Andrea Tairi Velázquez Gallardo** (`23460539@colima.tecnm.mx`) — **Data Statistician & Verification Lead**  
  Encargada del laboratorio de series de tiempo (E1: SES, Holt, Holt-Winters, ARIMA), diseño del experimento factorial 2^3 (E2), análisis multivariado PCA/MANOVA (E3) y auditoría SQA (IEEE 730).

**Materias vinculadas:**
* **Ingeniería de Datos (CMD-2602):** MTRO. ARMANDO ROMAN GALLARDO HEREDIA
* **Análisis Estadístico para Ciencia de Datos:** MTRO. MONICO JOEL SANCHEZ VELASCO
* **Calidad en los Sistemas de Información (IFC-1008):** MTRA. ISIS SARAI ESPINOSA LOZANO

---

## Qué hace nuestro observatorio

Monitoreamos, limpiamos, certificamos y proyectamos los precios mayoristas de insumos frescos de cocina (**Jitomate Saladette, Limón con semilla #5, Aguacate Hass, Cebolla Bola, Chile Serrano y Papa Alpha**) en tres centros mayoristas del Occidente (**Colima, Guadalajara y Morelia**) desde el portal oficial del **SNIIM (Secretaría de Economía)**, y los integramos analíticamente con el **Tipo de Cambio FIX (USD/MXN)** y el **Índice Nacional de Precios al Consumidor (INPC)** de la API SIE de **Banco de México**.

El objetivo es darle a los encargados de compras de **cocinas económicas y restaurantes de Colima (como el Restaurante Luisiana)**, así como a **abarroteras locales y comerciantes de tianguis**, herramientas predictivas y semáforos de compra basados en datos para decidir cuándo abastecer volumen o comprar justo a tiempo.

---

## Enlaces Rápidos de la Entrega E3 (Mapa Multivariado, Optimización y Sello TDL)

* **Ficha Ejecutiva E3:** [docs/E3/ENTREGA.md](docs/E3/ENTREGA.md)
* **Relatoría Metodológica E3:** [docs/relatoria-E3.md](docs/relatoria-E3.md)
* **Informe Multivariado (PCA, Mardia/Henze-Zirkler y MANOVA):** [laboratorio/informe_multivariado_e3.md](laboratorio/informe_multivariado_e3.md)
* **Optimización Medida del Pipeline (Antes vs. Después):** [docs/E3/optimizacion_pipeline_e3.md](docs/E3/optimizacion_pipeline_e3.md)
* **Dataset Abierto y Ficha Técnica (*Datasheet*):** [LICENSE-DATA.md](LICENSE-DATA.md) · [docs/E3/datasheet_canasta_oro.md](docs/E3/datasheet_canasta_oro.md)
* **Retrospectiva PSP (E0–E3) y Modelos de Proceso:** [docs/E3/retrospectiva_psp.md](docs/E3/retrospectiva_psp.md) · [docs/E3/modelos_proceso_moprosoft_cmmi.md](docs/E3/modelos_proceso_moprosoft_cmmi.md)
* **Tendencias DataOps, Cierre de Auditoría y Sello TDL:** [docs/E3/tendencias_dataops_observabilidad.md](docs/E3/tendencias_dataops_observabilidad.md) · [docs/E3/cierre_auditoria.md](docs/E3/cierre_auditoria.md) · [docs/E3/solicitud_sello_tdl.md](docs/E3/solicitud_sello_tdl.md)
* **Evidencias Previas (E2, E1 y E0):** [docs/E2/ENTREGA.md](docs/E2/ENTREGA.md) · [docs/relatoria-E2.md](docs/relatoria-E2.md) · [docs/E1/ENTREGA.md](docs/E1/ENTREGA.md) · [docs/E0/ENTREGA.md](docs/E0/ENTREGA.md)

---

## Enlaces de la Entrega E2 (Experimento, Geodatos y Calidad ISO)

* **Ficha Ejecutiva E2:** [docs/E2/ENTREGA.md](docs/E2/ENTREGA.md)
* **Relatoría Metodológica E2:** [docs/relatoria-E2.md](docs/relatoria-E2.md)
* **Declaración de Ética y Legalidad de Datos:** [docs/etica-datos.md](docs/etica-datos.md)
* **Informe del Experimento Factorial 2³, 2 Vías y 2^(4-1):** [laboratorio/informe_experimento.md](laboratorio/informe_experimento.md)
* **Evaluación ISO/IEC 25010, ISO/IEC 25012 y Antecedentes:** [docs/E2/evaluacion_iso_25010_25012.md](docs/E2/evaluacion_iso_25010_25012.md)
* **Auditoría Técnica y Protocolo Cruzado:** [docs/E2/auditoria_cruzada.md](docs/E2/auditoria_cruzada.md)
* **Manifiesto de Linaje de Capa Oro:** [data/oro/linaje_oro.json](data/oro/linaje_oro.json)
* **Evidencias Previas (E1 y E0):** [docs/E1/ENTREGA.md](docs/E1/ENTREGA.md) · [docs/relatoria-E1.md](docs/relatoria-E1.md) · [docs/E0/ENTREGA.md](docs/E0/ENTREGA.md)

---

## Cómo correr el proyecto en local

1. **Clonar y preparar el entorno virtual:**
   ```powershell
   git clone https://github.com/AdolfOrtega/tdl-canastita-proyecto.git
   cd tdl-canastita-proyecto
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

2. **Ejecutar la suite completa de pruebas automatizadas y cobertura:**
   ```powershell
   pytest -v --cov=pipeline --cov=calidad tests/
   ```

3. **Ejecutar el pipeline de datos optimizado (`1 hilo + lxml + Parquet`) y benchmark E3:**
   ```powershell
   python pipeline/enriquecer_geo.py
   python pipeline/limpieza_plata.py
   python pipeline/construir_oro.py
   python pipeline/benchmark_optimizacion_e3.py
   ```
   *(Para actualizar la fuente DENUE en Capa Bronce requiere `INEGI_TOKEN` en `.env`: `python -m extractores.ejecutar_captura --modo geo`)*.

4. **Ejecutar los laboratorios estadísticos (Series E1, Experimento E2 y Multivariado PCA/MANOVA E3):**
   ```powershell
   python laboratorio/pronostico_series_tiempo.py
   python laboratorio/experimento_factorial_2k.py
   python laboratorio/analisis_multivariado_e3.py
   ```

5. **Ejecutar evaluaciones ISO 25010/25012, retrospectiva PSP y auditoría Sello TDL:**
   ```powershell
   python calidad/evaluar_iso_25010_25012.py
   python calidad/evaluar_iso_25010_25012.py --verificar-seguridad
   python calidad/retrospectiva_psp.py
   python calidad/auditor_tdl.py . --sello
   ```

6. **Lanzar el tablero interactivo de control (Streamlit — 6 pestañas):**
   ```powershell
   streamlit run tablero/app.py
   ```

---

## Estructura de Carpetas

```text
tdl-canastita-proyecto/
├── README.md                      # Descripción general y guía de ejecución
├── LICENSE-DATA.md                # Licencia de datos abiertos CC BY 4.0 / Libre Uso MX
├── requirements.txt               # Dependencias del proyecto
├── pytest.ini                     # Configuración de pythonpath para pytest
├── docs/
│   ├── E0/                        # Entregables E0 (propuesta.md, ENTREGA.md)
│   ├── E1/                        # Entregables E1 (ENTREGA.md, plan_sqa_ieee730.md)
│   ├── E2/                        # Entregables E2 (ENTREGA.md, evaluacion_iso, auditoria_cruzada)
│   ├── E3/                        # Entregables E3 (ENTREGA.md, datasheet, MoProSoft/CMMI, PSP, Sello TDL)
│   ├── etica-datos.md             # Declaración ética, licencias y LFPDPPP de las 3 fuentes
│   ├── relatoria-E1.md            # Relatoría reflexiva de E1
│   ├── relatoria-E2.md            # Relatoría reflexiva de E2
│   └── relatoria-E3.md            # Relatoría reflexiva de E3
├── calidad/                       # Bitácora, evaluador ISO 25010/25012, retrospectiva PSP, auditor TDL
├── extractores/                   # Extractores éticos optimizados (lxml + Parquet)
├── pipeline/                      # Transformaciones Medallion, union espacial, linaje Oro y benchmark E3
├── data/
│   ├── bronce/                    # Datos crudos (SNIIM, Banxico, DENUE-MGEM, snapshot HTML)
│   ├── plata/                     # Datos limpios, normalizados y capa geo enriquecida
│   ├── oro/                       # Tabla analítica dimensional, linaje por fila, linaje_oro.json y benchmark E3
│   └── cuarentena/                # Registros rechazados por Puerta 1 (rechazos_plata.csv)
├── laboratorio/                   # Pronósticos (E1) + Experimento 2^3 (E2) + PCA/MANOVA/Mahalanobis (E3)
├── tablero/                       # Dashboard Streamlit (6 pestañas incluyendo Mapa DENUE y Mapa Multivariado)
├── tests/                         # Suite automatizada pytest (extractores, pipeline, estadística, E2, E3, E2E)
└── .github/workflows/             # Captura programada (cron) e Integración Continua Puerta 2 (push)
```
