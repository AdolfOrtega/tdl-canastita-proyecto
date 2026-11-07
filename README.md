# TDL Canastita (tdl-canastita-proyecto)

**Observatorio de Precios de la Canasta Básica e Inflación en el Occidente (Colima, Guadalajara y Morelia)**  
Proyecto Integrador - Tecnológico Nacional de México (Campus Colima) - Semestre Ago-Dic 2026

## Integrantes y Roles

* **Adolfo Rodríguez** (23460528@colima.tecnm.mx) - **Data Engineer**  
  Encargado de los extractores, la estructura del almacén por capas (bronce, plata y oro), la limpieza y las puertas de calidad.
* **Andrea Tairi Velázquez Gallardo** (23460539@colima.tecnm.mx) - **Data Statistician**  
  Encargada del análisis de series de tiempo y pronósticos (E1), el diseño del experimento factorial 2^3 (E2), el análisis multivariado PCA/MANOVA (E3) y la revisión de Quality Lead en E0.

**Materias vinculadas:**
* **Ingeniería de Datos (CMD-2602):** ARMANDO ROMAN GALLARDO HEREDIA
* **Análisis Estadístico para Ciencia de Datos:** MONICO JOEL SANCHEZ VELASCO
* **Calidad en los Sistemas de Información (IFC-1008):** ISIS SARAI ESPINOSA LOZANO

## Qué hace nuestro observatorio

Monitoreamos y comparamos los precios mayoristas de insumos frescos de cocina (aguacate Hass, limón con semilla #5, jitomate saladette, cebolla bola, chile serrano y papa alpha) en tres plazas de abasto del Occidente (**Colima, Guadalajara y Morelia**) desde el portal del **SNIIM (Secretaría de Economía)**, y los cruzamos con el **tipo de cambio diario FIX USD/MXN** y el **Índice Nacional de Precios al Consumidor (INPC)** de la API oficial del **SIE de Banxico**.

El objetivo es darle a los encargados de compras de **cocinas y restaurantes de Colima (como el restaurante Luisiana)**, así como a **abarroteras locales y comerciantes de frutas y verduras en tianguis**, información clara y respaldada con estadística para decidir qué insumos surtir antes de una subida fuerte y comparar si el proveedor o bodega local en Colima está dando más caro respecto a Guadalajara o Morelia.

## Enlaces Rápidos de la Entrega E0

* **Ficha de entrega para los 3 docentes:** [docs/E0/ENTREGA.md](docs/E0/ENTREGA.md)
* **Propuesta completa del observatorio:** [docs/E0/propuesta.md](docs/E0/propuesta.md)
* **Bitácora de ejecuciones de captura:** [calidad/bitacora_captura.csv](calidad/bitacora_captura.csv)
* **Registros PSP de tiempo y defectos:** [calidad/](calidad/)

## Cómo correr el proyecto en local

1. **Crear y activar el entorno virtual (Python 3.11 o 3.12):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Configurar el token de Banxico (opcional en local, ya incluye respaldos abiertos):**
   Copia el archivo `.env.example` a `.env` y coloca tu token gratuito del SIE de Banxico:
   ```text
   BANXICO_TOKEN=tu_token_banxico
   ```

3. **Ejecutar los extractores hacia `data/bronce/`:**
   ```powershell
   # Corrida diaria (la misma que ejecuta GitHub Actions):
   python -m extractores.ejecutar_captura --modo diario

   # Corrida completa (incluye también los 59 meses históricos del SNIIM 2022-2026):
   python -m extractores.ejecutar_captura --modo completo
   ```

4. **Correr las pruebas con `pytest`:**
   ```powershell
   pytest -v
   ```

## Estructura de Carpetas

```text
tdl-canastita-proyecto/
├── README.md                 # Descripción general y guía de ejecución
├── requirements.txt          # Librerías necesarias
├── pytest.ini                # Configuración de ruta para pytest
├── docs/                     # Fichas ENTREGA.md, propuesta.md y relatorías por etapa
├── calidad/                  # Registros PSP de defectos/tiempo por integrante y bitacora_captura.csv
├── extractores/              # base.py (ExtractorEtico), sniim_canasta.py, macro_api.py, ejecutar_captura.py
├── pipeline/                 # Transformaciones bronce -> plata -> oro y puertas de calidad (E1-E3)
├── data/
│   ├── bronce/               # Datos crudos CSV + metadatos (.meta.json)
│   ├── plata/                # Datos limpios e integrados (E1)
│   ├── oro/                  # Datos listos para análisis y diccionario (E1-E3)
│   └── cuarentena/           # Registros que no pasen la puerta de calidad con su motivo (E1)
├── laboratorio/              # Notebooks de series de tiempo, experimento y multivariado
├── tablero/                  # Aplicación en Streamlit
├── tests/                    # Pruebas automáticas con pytest
└── .github/workflows/        # Captura diaria programada e integración continua
```
