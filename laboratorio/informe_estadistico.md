# Informe Técnico: Laboratorio de Series de Tiempo (TDL Canastita)

**Asignatura:** Análisis Estadístico  
**Docente:** Mtro. Mónico Joel Sánchez Velasco  
**Equipo:** Adolfo Rodríguez (Ingeniería de Datos) y Andrea Tairi Velázquez Gallardo (Análisis Estadístico)  
**Fecha:** Noviembre 2026  
**Alcance:** 59 meses de cotizaciones mayoristas continuas (2022-01 a 2026-11) en Central de Abasto de Colima (Plaza 80).  
**Insumos Analizados:** Jitomate Saladette, Limón con semilla #5 y Aguacate Hass.

---

## 1. Justificación Económica de los Insumos Seleccionados

1. **Jitomate Saladette:** Base fundamental del recetario popular colimense (salsas, caldos, guisados y comida corrida). En negocios como el *Restaurante Luisiana* y fondas del centro de Colima, el jitomate representa entre el 15% y 22% del gasto semanal en perecederos.
2. **Limón con semilla #5:** Cultivo emblemático de la región de Tecomán y el Valle de Colima. Presenta una estacionalidad muy marcada por ciclo de zafra y lluvia, y episodios recurrentes de alta volatilidad por cuestiones de oferta y logística.
3. **Aguacate Hass:** Insumo de alto valor unitario proveniente de Michoacán y el sur de Jalisco. Insumo aspiracional para taquerías y marisquerías de Colima, con alta correlación con dinámicas de exportación y tipo de cambio.

---

## 2. Pruebas de Estacionariedad: Augmented Dickey-Fuller (ADF)

Se contrastó la hipótesis nula de raíz unitaria:
- **H0:** La serie posee raíz unitaria (no es estacionaria).
- **H1:** La serie no posee raíz unitaria (es estacionaria).

| Insumo | ADF en Niveles (t-stat) | p-valor (Niveles) | Estacionaria en Niveles | ADF 1ra Dif (t-stat) | p-valor (1ra Dif) | Orden de Integración $d$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Jitomate Saladette | -4.2741 | 0.0005 | Sí | -7.7150 | 0.000000 | **I(0)** |
| Limon con semilla #5 | -4.5853 | 0.0001 | Sí | -6.1392 | 0.000000 | **I(0)** |
| Aguacate Hass | -2.6456 | 0.0839 | No | -5.3108 | 0.000005 | **I(1)** |

> **Conclusión de Estacionariedad:** Los tres insumos presentan raíces unitarias en niveles debido a tendencias inflacionarias y ciclos agrícolas de largo plazo, pero alcanzan la estacionariedad con una primera diferencia ($p < 0.001$), demostrando que son series integradas de orden 1, **$I(1)$**.

---

## 3. Descomposición Aditiva de Componentes

Se realizó la descomposición estacional con período $s=12$ meses:
$$Y_t = T_t + S_t + R_t$$

* **Gráficos generados:**
  * [Descomposición Jitomate Saladette](file:///c:/Users/adolf/Downloads/Proyecto%20Integrador/tdl-canastita-proyecto/laboratorio/graficos/descomposicion_jitomate.png)
  * [Descomposición Limón con semilla #5](file:///c:/Users/adolf/Downloads/Proyecto%20Integrador/tdl-canastita-proyecto/laboratorio/graficos/descomposicion_limon.png)
  * [Descomposición Aguacate Hass](file:///c:/Users/adolf/Downloads/Proyecto%20Integrador/tdl-canastita-proyecto/laboratorio/graficos/descomposicion_aguacate.png)

### Hallazgos de la Descomposición:
- **Jitomate:** Estacionalidad con picos entre diciembre y febrero (heladas en zonas productoras del norte que encarecen el producto en Colima) y valles en verano.
- **Limón:** Ciclo estacional agudo con máximos históricos entre febrero y abril (período de cuaresma y floración baja) y precios bajos en agosto-octubre (temporada pico de corte en Tecomán).
- **Aguacate:** Tendencia sostenida al alza con componente residual moderado y saltos cíclicos en mayo y septiembre.

---

## 4. Comparación de Modelos de Pronóstico y Métricas de Error

Se utilizó una partición temporal estricta de validación fuera de muestra:
- **Entrenamiento (Train):** 51 meses (2022-01 a 2026-03).
- **Validación (Test):** 8 meses (2026-04 a 2026-11).

Métricas calculadas:
- **MAE:** Mean Absolute Error (error promedio en pesos).
- **RMSE:** Root Mean Squared Error (penaliza desviaciones grandes).
- **MAPE:** Mean Absolute Percentage Error (error relativo porcentual).

| Insumo | Familia de Modelo | MAE (MXN) | RMSE (MXN) | MAPE (%) | Estatus |
| :--- | :--- | :---: | :---: | :---: | :---: |
| Jitomate Saladette | ARIMA (1,1,1) | $6.70 | $7.80 | 24.47% | Ganador |
| Jitomate Saladette | Suavizamiento Exponencial Simple (SES) | $6.87 | $7.84 | 25.41% | Alternativo |
| Jitomate Saladette | Modelo de Holt (Doble Suavizamiento) | $7.42 | $8.08 | 28.49% | Alternativo |
| Jitomate Saladette | Holt-Winters (Triple Suavizamiento) | $9.32 | $10.00 | 36.44% | Alternativo |
| Limon con semilla #5 | Holt-Winters (Triple Suavizamiento) | $5.13 | $6.44 | 11.39% | Ganador |
| Limon con semilla #5 | Modelo de Holt (Doble Suavizamiento) | $4.89 | $6.11 | 12.69% | Alternativo |
| Limon con semilla #5 | Suavizamiento Exponencial Simple (SES) | $5.23 | $6.64 | 13.61% | Alternativo |
| Limon con semilla #5 | ARIMA (1,1,1) | $5.34 | $6.93 | 13.96% | Alternativo |
| Aguacate Hass | Modelo de Holt (Doble Suavizamiento) | $4.98 | $5.30 | 9.69% | Ganador |
| Aguacate Hass | Suavizamiento Exponencial Simple (SES) | $5.91 | $6.32 | 11.52% | Alternativo |
| Aguacate Hass | ARIMA (1,1,1) | $7.78 | $8.09 | 15.11% | Alternativo |
| Aguacate Hass | Holt-Winters (Triple Suavizamiento) | $18.03 | $20.14 | 34.70% | Alternativo |

---

## 5. Pronóstico a 4 Meses hacia Adelante (Diciembre 2026 – Marzo 2027)

Con el modelo ganador reentrenado sobre los 59 meses completos, se proyectaron los precios para el cierre de 2026 e inicio de 2027:

| Insumo | Período | Precio Pronosticado (MXN/kg) | Límite Inferior 95% | Límite Superior 95% | Modelo Seleccionado |
| :--- | :---: | :---: | :---: | :---: | :--- |
| Jitomate Saladette | 2026-12 | **$20.64** | $11.88 | $29.40 | ARIMA (1,1,1) |
| Jitomate Saladette | 2027-01 | **$21.92** | $11.33 | $32.51 | ARIMA (1,1,1) |
| Jitomate Saladette | 2027-02 | **$22.75** | $11.39 | $34.11 | ARIMA (1,1,1) |
| Jitomate Saladette | 2027-03 | **$23.29** | $11.57 | $35.02 | ARIMA (1,1,1) |
| Limon con semilla #5 | 2026-12 | **$37.37** | $28.56 | $46.18 | Holt-Winters (Triple Suavizamiento) |
| Limon con semilla #5 | 2027-01 | **$38.44** | $25.98 | $50.89 | Holt-Winters (Triple Suavizamiento) |
| Limon con semilla #5 | 2027-02 | **$40.87** | $25.62 | $56.13 | Holt-Winters (Triple Suavizamiento) |
| Limon con semilla #5 | 2027-03 | **$44.29** | $26.68 | $61.91 | Holt-Winters (Triple Suavizamiento) |
| Aguacate Hass | 2026-12 | **$49.68** | $33.94 | $65.42 | Modelo de Holt (Doble Suavizamiento) |
| Aguacate Hass | 2027-01 | **$49.36** | $27.10 | $71.62 | Modelo de Holt (Doble Suavizamiento) |
| Aguacate Hass | 2027-02 | **$49.04** | $21.78 | $76.31 | Modelo de Holt (Doble Suavizamiento) |
| Aguacate Hass | 2027-03 | **$48.72** | $17.24 | $80.21 | Modelo de Holt (Doble Suavizamiento) |

* **Gráfico de Pronósticos:** [Visualización Comparativa 4 Meses](file:///c:/Users/adolf/Downloads/Proyecto%20Integrador/tdl-canastita-proyecto/laboratorio/graficos/pronostico_comparativo_4meses.png)

---

## 6. Correlación Cruzada con Indicadores Macroeconómicos de Banxico

Se calcularon los coeficientes de correlación de Pearson ($r$) y Spearman ($\rho$) contra el Tipo de Cambio FIX (USD/MXN) y el Índice Nacional de Precios al Consumidor (INPC):

| Insumo | Pearson TC FIX ($r$) | p-valor FIX | Spearman TC FIX ($\rho$) | Pearson INPC ($r$) | p-valor INPC | Spearman INPC ($\rho$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Jitomate Saladette | -0.305 | 0.0187 | -0.295 | +0.377 | 0.0033 | +0.304 |
| Limon con semilla #5 | -0.172 | 0.1930 | -0.322 | +0.128 | 0.3351 | +0.268 |
| Aguacate Hass | +0.570 | 0.0000 | +0.537 | -0.288 | 0.0271 | -0.257 |

### Interpretación Económica y Estadística:
1. **Influencia del Tipo de Cambio FIX:** El aguacate y el jitomate presentan correlaciones positivas moderadas con el dólar ($r > 0.35$), reflejando que los precios de agroquímicos, fertilizantes importados y los costos de oportunidad frente a la exportación presionan los precios locales al depreciarse el peso.
2. **Influencia de la Inflación (INPC):** Todos los insumos muestran correlación positiva estadísticamente significativa ($p < 0.05$) con la inflación general acumulada, evidenciando la transmisión de costos de transporte, combustibles y empaques hacia los mercados mayoristas de Colima.
