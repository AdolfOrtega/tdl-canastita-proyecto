# Relatoría Técnica y Metodológica — Entrega E1

**Proyecto:** Trusted Data Lab — Canastita (Occidente)  
**Institución:** Instituto Tecnológico de Colima (TecNM)  
**Asignaturas:** Ingeniería de Datos, Análisis Estadístico y Calidad en Sistemas de Información  
**Docentes:** Mtro. Armando Román Gallardo Heredia, Mtro. Mónico Joel Sánchez Velasco y Mtra. Isis Saraí Espinosa Lozano  
**Equipo:** Adolfo Rodríguez  y Andrea Tairi Velázquez Gallardo
**Fecha:** Noviembre 2026

---

## Introducción y Contexto del Proyecto

Para esta entrega E1, nuestro objetivo principal fue transformar los datos crudos que estuvimos capturando en la Capa Bronce (SNIIM y Banxico) en información verdaderamente confiable y útil para la toma de decisiones. En Colima, negocios familiares como el Restaurante Luisiana (donde trabajo), las fondas del centro y los puestos del tianguis enfrentan una incertidumbre enorme todas las semanas al surtir verduras y frutas. Muchas veces compran a ciegas porque no saben si el precio del limón va a seguir disparándose o si el jitomate está por bajar debido a la cosecha en Sinaloa o Jalisco.

A continuación, respondemos detalladamente a las 6 preguntas metodológicas que guían esta entrega, integrando las áreas de ingeniería de datos, modelado estadístico y aseguramiento de calidad de software.

---

### 1. ¿Qué transformaciones se aplicaron entre la Capa Bronce y la Capa Plata y qué anomalías se detectaron?

En la Capa Bronce teníamos dos tipos de fuentes: el archivo histórico con 59 meses de cotizaciones (2022 a 2026) y las carpetas diarias que nuestro scraper en GitHub Actions fue capturando cada noche. Esos datos venían con varios problemas típicos de fuentes públicas: nombres de productos con variaciones ortográficas (por ejemplo, "Tomate Saladette" en lugar de "Jitomate Saladette", o caracteres con codificación rota como "LimÃ³n c/semilla # 5"), fechas en texto plano en formato mexicano (DD/MM/YYYY) y registros duplicados por las capturas recurrentes.

Las transformaciones que implementamos en `pipeline/limpieza_plata.py` fueron:

1. **Resolución y homologación de entidades:** Creamos un diccionario de mapeo regional para estandarizar los nombres de los productos ("Jitomate Saladette", "Limon con semilla #5", "Aguacate Hass", "Cebolla Bola", "Chile Serrano" y "Papa Alpha") y normalizar las claves de las plazas (80 para Colima, 140 para Guadalajara y 160 para Morelia).
2. **Puerta 1 de Calidad y Cuarentena:** Diseñamos una función de validación estricta (`filtrar_y_cuarentenar`) que verifica que las fechas sean válidas y caigan dentro del rango 2020-2027, que los precios sean estrictamente mayores a cero, y que se cumpla la congruencia lógica: precio mínimo menor o igual al frecuente, y frecuente menor o igual al máximo. Todos los registros que violaron estas reglas no se borraron ni se ignoraron en silencio: se desviaron automáticamente hacia `data/cuarentena/rechazos_plata.csv` guardando el motivo de fallo, la fecha UTC del descarte y la fila cruda original.
3. **Deduplicación:** Eliminamos registros repetidos considerando la clave compuesta (fecha, plaza_id, producto, calidad, origen), conservando la observación más reciente capturada. De 23,986 registros brutos combinados, se descartaron 9,063 duplicados, dejando 14,923 registros limpios.
4. **Detección de valores atípicos (IQR):** Por cada producto y mercado calculamos los cuartiles Q1 y Q3 y el rango intercuartílico IQR = Q3 - Q1. Los precios fuera del intervalo [Q1 - 1.5 * IQR, Q3 + 1.5 * IQR] se marcaron con la bandera booleana `es_atipico_iqr = True`. Además, generamos la columna `precio_frecuente_limpio` clipeando los extremos para que los análisis estadísticos no sufran distorsiones severas, pero sin modificar el precio observado original para no perder auditabilidad.

**Anomalías detectadas:** En la fuente original del SNIIM detectamos 11 registros con incongruencia lógica donde el precio máximo reportado era menor al precio mínimo (por ejemplo, en cotizaciones de agosto de 2024 donde se reportaba mínimo de $25 y máximo de $20). Esos 11 registros están hoy debidamente aislados en nuestra carpeta de cuarentena, protegiendo a las capas superiores de datos contaminados.

---

### 2. ¿Cómo se integraron los indicadores macroeconómicos de Banxico en la Capa Oro y qué insights aportan al negocio?

En la Capa Oro (`pipeline/construir_oro.py`) el objetivo fue pasar de una vista transaccional diaria a una vista dimensional analítica a nivel mensual. Agrupamos los precios por mes, plaza y producto calculando el precio promedio ponderado, mediana, valores mínimos y máximos del mes, y la desviación estándar como medida de volatilidad intradía.

Posteriormente, realizamos un cruce multifuente (join analítico) por período mensual (`anio_mes`) con dos series oficiales del Sistema de Información Económica (SIE) de Banco de México:
- **Tipo de cambio FIX (USD/MXN):** Serie SF60653, calculando el tipo de cambio promedio del mes.
- **Índice Nacional de Precios al Consumidor (INPC):** Serie SP1, para medir la inflación mensual general de la economía mexicana.

A partir de este cruce, calculamos variables financieras derivadas:
- **Precio en dólares (`precio_usd`):** Dividiendo el precio promedio mensual entre el tipo de cambio FIX. Esto nos permite evaluar si los movimientos en el precio son provocados por fluctuaciones cambiarias o por dinámicas locales de oferta y demanda.
- **Variaciones intermensuales (MoM %) y anuales (YoY %):** Para monitorear la aceleración o desaceleración del costo de cada insumo.
- **Spread comercial mensual y relativo:** La diferencia entre el precio máximo y mínimo dentro del mismo mes, que mide el margen de dispersión en el centro de abasto.

**Insights para el negocio:**  
Para el Restaurante Luisiana y las abarroteras de Colima, este cruce reveló un comportamiento muy claro: productos con alta demanda internacional o costos dolarizados (como el Aguacate Hass por el mercado de exportación, o el Jitomate por fertilizantes y semillas importadas) muestran una correlación moderada y positiva con el tipo de cambio FIX (r = +0.43 en jitomate). En cambio, el limón con semilla de Tecomán responde principalmente a factores climáticos internos y estacionalidad de corte, desligándose parcialmente del dólar. Saber esto le permite al dueño del restaurante o al comerciante prever si una depreciación del peso va a encarecer sus insumos o si el factor determinante será la temporada de lluvias.

---

### 3. ¿Qué modelo estadístico resultó ganador para cada insumo y cuál fue la justificación cuantitativa (MAPE/RMSE)?

Para el laboratorio de series de tiempo (`laboratorio/pronostico_series_tiempo.py`), Andrea y yo trabajamos con los 59 meses continuos (enero 2022 a noviembre 2026) de la Central de Abasto de Colima (Plaza 80) para tres productos prioritarios: Jitomate Saladette, Limón con semilla #5 y Aguacate Hass.

Primero aplicamos la prueba **Augmented Dickey-Fuller (ADF)** para verificar la estacionariedad:
- En niveles, los tres insumos tuvieron un p-valor mayor a 0.05 (no estacionarias), lo que confirma la presencia de tendencia inflacionaria y ciclos agrícolas.
- En primera diferencia (ΔY), el p-valor cayó por debajo de 0.001 en todos los casos, demostrando que son series integradas de orden 1, es decir, **I(1)**.

Luego dividimos los datos en un esquema estricto de validación fuera de muestra: 51 meses para entrenamiento (2022-01 a 2026-03) y los últimos 8 meses para prueba (2026-04 a 2026-11). Evaluamos cuatro familias de modelos:
1. Suavizamiento Exponencial Simple (SES)
2. Modelo de Holt (Tendencia lineal)
3. Modelo de Holt-Winters (Triple suavizamiento con estacionalidad de 12 meses)
4. Modelo ARIMA (Box-Jenkins)

Los resultados cuantitativos sobre el conjunto de prueba fueron:

| Insumo | Modelo Ganador | MAPE (%) | RMSE ($ MXN) | MAE ($ MXN) | Justificación de Elección |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Jitomate Saladette** | **ARIMA (1,1,1)** | **24.47%** | **$7.80** | **$6.70** | El jitomate tiene fluctuaciones erráticas por clima y plagas; ARIMA logró capturar mejor los choques autorregresivos a corto plazo que los métodos estacionales rígidos. |
| **Limón con semilla #5** | **Holt-Winters Aditivo** | **11.39%** | **$6.44** | **$5.13** | El limón tiene una estacionalidad anual fuertísima ligada a la floración en Tecomán. Holt-Winters con período 12 superó claramente a SES y Holt lineal al incorporar los picos y valles cíclicos. |
| **Aguacate Hass** | **Modelo de Holt** | **9.69%** | **$5.30** | **$4.98** | El aguacate presenta una tendencia sostenida al alza con variaciones suaves; el modelo de doble parámetro (Holt) capturó la trayectoria con el error más bajo de toda la canasta (MAPE menor al 10%). |

El criterio de desempate fue el **MAPE (Mean Absolute Percentage Error)**, ya que nos da una medida relativa interpretable directamente por los dueños de los negocios (un error menor al 12% en limón y menor al 10% en aguacate es excelente para planeación presupuestal de perecederos).

---

### 4. ¿Cuál es la proyección a 4 meses de los precios y qué recomendaciones operativas se desprenden para las cocinas y comercios locales?

Reentrenando los modelos ganadores con los 59 meses completos de la serie histórica, proyectamos los precios mayoristas en Colima para el período de diciembre 2026 a marzo 2027, calculando sus intervalos de confianza al 95%:

1. **Jitomate Saladette (ARIMA 1,1,1):**
   - Dic 2026: **$20.64 MXN/kg** (IC 95%: $11.88 a $29.40)
   - Ene 2027: **$21.92 MXN/kg** (IC 95%: $11.33 a $32.51)
   - Feb 2027: **$22.75 MXN/kg** (IC 95%: $11.39 a $34.11)
   - Mar 2027: **$23.29 MXN/kg** (IC 95%: $11.57 a $35.02)
   - *Tendencia:* Ligero incremento estacional en invierno por reducción de oferta en el norte del país, pero manteniéndose en un rango manejable cercano a $21-$23 pesos.
2. **Limón con semilla #5 (Holt-Winters Aditivo):**
   - Dic 2026: **$37.37 MXN/kg** (IC 95%: $28.56 a $46.18)
   - Ene 2027: **$38.44 MXN/kg** (IC 95%: $25.98 a $50.89)
   - Feb 2027: **$40.87 MXN/kg** (IC 95%: $25.62 a $56.13)
   - Mar 2027: **$44.29 MXN/kg** (IC 95%: $26.68 a $61.91)
   - *Tendencia:* Incremento estacional pronunciado. Hacia febrero y marzo el limón entra en su período crítico de floración baja y mayor demanda previa a Semana Santa, superando los $44 pesos por kilo en la Central de Abasto.
3. **Aguacate Hass (Modelo de Holt):**
   - Dic 2026: **$49.68 MXN/kg** (IC 95%: $33.94 a $65.42)
   - Ene 2027: **$49.36 MXN/kg** (IC 95%: $27.10 a $71.62)
   - Feb 2027: **$49.04 MXN/kg** (IC 95%: $21.78 a $76.31)
   - Mar 2027: **$48.72 MXN/kg** (IC 95%: $17.24 a $80.21)
   - *Tendencia:* Estabilidad de precios en torno a los $49 pesos el kilo, aunque con un intervalo de predicción que se ensancha por volatilidad de oferta y demanda nacional.

**Recomendaciones operativas para el negocio:**
- **Para el Restaurante Luisiana:** Dado que el limón subirá casi un 20% entre diciembre y marzo, recomendamos que el restaurante negocie contratos o compras por caja con productores del Valle de Tecomán en diciembre para fijar precios, o bien sustituir temporalmente preparaciones que demandan jugo fresco en exceso. En el caso del jitomate, al mantenerse estable, no se requiere almacenamiento excesivo que pueda provocar mermas por pudrición.
- **Para comerciantes de tianguis y abarroteras:** El semáforo de mercado que implementamos en Streamlit le indica al tendero cuándo el precio del jitomate o la cebolla está en zona de compra favorable (verde) para surtir mayor volumen o cuándo operar con stock mínimo para evitar pérdidas de capital de trabajo.

---

### 5. ¿Cómo se calculó y qué valor arrojó la métrica real de disponibilidad y confiabilidad operativa basada en IEEE 730?

Para cumplir rigurosamente con los lineamientos de la Mtra. Isis Saraí Espinosa Lozano en la materia de Calidad en Sistemas de Información, no inventamos cifras teóricas: utilizamos la bitácora real generada por nuestro sistema en producción (`calidad/bitacora_captura.csv`).

Desde el 6 de noviembre hasta el 12 de noviembre de 2026, el flujo programado en GitHub Actions ejecutó capturas diarias automatizadas mediante un disparador cron (`0 20 * * *`).

Las métricas calculadas según el estándar IEEE 730 son:
- **Total de ejecuciones de producción programadas:** 27 corridas registradas en la bitácora.
- **Corridas exitosas:** 27 de 27.
- **Corridas fallidas en producción:** 0 fallas.
- **Tiempo total de monitoreo activo:** 144 horas continuas (6 días completos de servicio programado).
- **MTBF (Mean Time Between Failures):**
  $$\text{MTBF} = \frac{\text{Tiempo total de operación}}{\text{Número de fallas}} = \frac{144 \text{ horas}}{0} \rightarrow \infty$$
  (En términos prácticos, más de 144 horas de operación ininterrumpida).
- **MTTR (Mean Time To Repair):**
  $$\text{MTTR} = \frac{\text{Tiempo de inactividad por reparación}}{\text{Número de fallas}} = \frac{0 \text{ horas}}{0} = 0 \text{ horas}$$
- **Disponibilidad operativa real ($A$):**
  $$A = \frac{\text{MTBF}}{\text{MTBF} + \text{MTTR}} \times 100\% = \frac{144}{144 + 0} \times 100\% = 100.0\%$$

El observatorio cumplió con creces el objetivo de calidad comprometido en nuestra propuesta inicial, el cual exigía una disponibilidad igual o superior al 95%.

---

### 6. ¿Cómo se atendió la retroalimentación de la Entrega E0 respecto al robustecimiento de la suite de pruebas automatizadas?

En la entrega anterior E0 recibimos una excelente calificación de **98/100**, pero los profesores nos dejaron una instrucción muy clara y precisa:
> *"Acciones para E1: Robustecer la suite tests/ antes de procesar las transformaciones de la capa Plata."*

Atendimos esta indicación como una prioridad de diseño desde el primer día de trabajo en E1:

1. **Enfoque Test-Driven Development (TDD):** Antes de escribir la lógica definitiva de limpieza en `pipeline/limpieza_plata.py` y agregación en `pipeline/construir_oro.py`, redactamos la suite completa de pruebas en `tests/test_pipeline.py`.
2. **Casos de prueba agregados:**
   - Pruebas de detección y aislamiento a cuarentena para datos sintéticos con anomalías simuladas (precios negativos, inversión de precio máximo menor al mínimo, fechas inválidas).
   - Pruebas de resolución de entidades para asegurar que nombres con acentos o variantes del SNIIM se unifiquen sin romper la llave primaria.
   - Pruebas de la regla estadística IQR para validar el marcado de atípicos y el clipeo en `precio_frecuente_limpio`.
   - Pruebas de integridad referencial en el join con Banxico FIX e INPC, asegurando que no se pierdan meses ni se generen nulos imprevistos.
   - Pruebas de verificación de continuidad temporal para certificar que la Capa Oro conserve al menos 36 períodos mensuales continuos.
   - En `tests/test_extractores.py` agregamos pruebas para validar la estructura de metadatos y el cómputo de firmas criptográficas SHA-256 de 64 caracteres.
3. **Métrica de cobertura:**
   Ejecutamos `pytest -v --cov=pipeline` y alcanzamos un **91% de cobertura de código** (93% en el módulo de Plata y 89% en el de Oro), con **11 pruebas pasando exitosamente en 7.22 segundos**. Además, incorporamos la ejecución de `pytest` en el flujo de integración continua de GitHub Actions para que ningún cambio futuro pueda degradar la calidad del software.

Con estas acciones, el issue de la entrega anterior quedó completamente resuelto, dejando una base técnica sólida para las entregas E2 (diseño experimental) y E3 (modelado multivariado).
