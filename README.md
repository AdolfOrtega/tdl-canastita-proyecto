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

## Enlaces Rápidos de la Entrega E1

* **Ficha Ejecutiva E1 (con atención a issues de E0):** [docs/E1/ENTREGA.md](docs/E1/ENTREGA.md)
* **Relatoría Metodológica (6 preguntas guía):** [docs/relatoria-E1.md](docs/relatoria-E1.md)
* **Plan SQA según estándar IEEE 730:** [docs/E1/plan_sqa_ieee730.md](docs/E1/plan_sqa_ieee730.md)
* **Diccionario de Datos (Capas Plata y Oro):** [pipeline/diccionario_datos.md](pipeline/diccionario_datos.md)
* **Informe Técnico de Series de Tiempo:** [laboratorio/informe_estadistico.md](laboratorio/informe_estadistico.md)
* **Pronósticos a 4 Meses (Dic 2026 - Mar 2027):** [laboratorio/pronosticos_futuro.csv](laboratorio/pronosticos_futuro.csv)
* **Métricas de Modelos (MAPE, RMSE, MAE):** [laboratorio/metricas_modelos.csv](laboratorio/metricas_modelos.csv)
* **Tablero Interactivo Streamlit:** [tablero/app.py](tablero/app.py)
* **Suite de Pruebas (91% cobertura):** [tests/test_pipeline.py](tests/test_pipeline.py) y [tests/test_extractores.py](tests/test_extractores.py)
* **Evidencias de la Entrega E0 previa:** [docs/E0/ENTREGA.md](docs/E0/ENTREGA.md) y [docs/E0/propuesta.md](docs/E0/propuesta.md)

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

2. **Ejecutar la suite de pruebas unitarias y cobertura (91%):**
   ```powershell
   pytest -v --cov=pipeline
   ```

3. **Ejecutar el pipeline de datos (Capa Plata y Capa Oro):**
   ```powershell
   python pipeline/limpieza_plata.py
   python pipeline/construir_oro.py
   ```

4. **Ejecutar el laboratorio estadístico de series de tiempo:**
   ```powershell
   python laboratorio/pronostico_series_tiempo.py
   ```

5. **Lanzar el tablero interactivo de control (Streamlit):**
   ```powershell
   streamlit run tablero/app.py
   ```

---

## Estructura de Carpetas

```text
tdl-canastita-proyecto/
├── README.md                      # Descripción general y guía de ejecución
├── requirements.txt               # Dependencias del proyecto
├── pytest.ini                     # Configuración de pythonpath para pytest
├── docs/
│   ├── E0/                        # Entregables E0 (propuesta.md, ENTREGA.md)
│   ├── E1/                        # Entregables E1 (ENTREGA.md, plan_sqa_ieee730.md)
│   └── relatoria-E1.md            # Relatoría reflexiva y metodológica de E1
├── calidad/                       # Bitácora de capturas y registros PSP de tiempo/defectos
│   ├── bitacora_captura.csv       # Historial de 27 corridas exitosas en producción (100% disponibilidad)
│   ├── defectos-adolfo.csv        # Registro de defectos PSP Adolfo
│   ├── tiempo-adolfo.csv          # Registro de tiempos PSP Adolfo
│   ├── defectos-andrea.csv        # Registro de defectos PSP Andrea
│   └── tiempo-andrea.csv          # Registro de tiempos PSP Andrea
├── extractores/                   # Extractores éticos de Capa Bronce (SNIIM y Banxico)
├── pipeline/                      # Transformaciones Medallion y calidad
│   ├── limpieza_plata.py          # Puerta 1, cuarentena, deduplicación e IQR
│   ├── construir_oro.py           # Agregación mensual, join macro y métricas derivadas
│   └── diccionario_datos.md       # Diccionario dimensional de esquemas
├── data/
│   ├── bronce/                    # Datos crudos CSV + metadatos (.meta.json)
│   ├── plata/                     # Datos limpios y normalizados (canasta_occidente_plata.csv)
│   ├── oro/                       # Tabla analítica dimensional (canasta_occidente_oro.csv)
│   └── cuarentena/                # Registros rechazados por Puerta 1 (rechazos_plata.csv)
├── laboratorio/                   # Laboratorio estadístico de pronósticos
│   ├── pronostico_series_tiempo.py# Modelos SES, Holt, Holt-Winters, ARIMA
│   ├── informe_estadistico.md     # Reporte técnico detallado
│   ├── metricas_modelos.csv       # Comparativa MAPE / RMSE / MAE
│   ├── pronosticos_futuro.csv     # Proyecciones a 4 meses con IC 95%
│   ├── correlaciones_macro.csv    # Correlaciones con TC FIX e INPC
│   └── graficos/                  # Gráficos de descomposición y pronóstico
├── tablero/                       # Dashboard interactivo con Streamlit
│   └── app.py                     # Visor de mercado, pronósticos y panel SQA
├── tests/                         # Suite automatizada (11 pruebas, 91% cobertura)
│   ├── test_extractores.py        # Pruebas de extracción ética y metadatos
│   └── test_pipeline.py           # Pruebas de Plata, Oro, Cuarentena e IQR
└── .github/workflows/             # Flujos CI/CD programados en GitHub Actions
```
