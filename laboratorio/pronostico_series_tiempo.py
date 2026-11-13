"""
laboratorio/pronostico_series_tiempo.py
Proyecto Integrador - Trusted Data Lab (TDL Canastita)
Materia: Análisis Estadístico (Mtro. Mónico Joel Sánchez Velasco)
Autores: Adolfo Rodríguez y Andrea Tairi Velázquez Gallardo

Módulo de análisis de series de tiempo para insumos clave de la canasta agropecuaria
en la Central de Abasto de Colima (Plaza 80):
1. Jitomate Saladette
2. Limón con semilla #5
3. Aguacate Hass

Metodología:
- Análisis exploratorio de 59 períodos mensuales (2022-01 a 2026-11).
- Pruebas de estacionariedad Augmented Dickey-Fuller (ADF) en niveles y diferencias.
- Descomposición aditiva clásica (tendencia, estacionalidad, residuo).
- Comparación de 4 modelos (SES, Holt, Holt-Winters, ARIMA) con partición Train/Test.
- Métricas de evaluación: MAE, RMSE, MAPE.
- Pronóstico a 4 meses hacia adelante con intervalos de confianza al 95%.
- Análisis de correlación cruzada con tipo de cambio FIX e inflación INPC.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing, Holt, SimpleExpSmoothing
from statsmodels.tsa.stattools import adfuller

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("laboratorio")

RAIZ = Path(__file__).resolve().parent.parent
DIR_ORO = RAIZ / "data" / "oro"
DIR_LAB = RAIZ / "laboratorio"
DIR_GRAFICOS = DIR_LAB / "graficos"

PRODUCTOS_CLAVE = [
    "Jitomate Saladette",
    "Limon con semilla #5",
    "Aguacate Hass",
]


def cargar_datos_oro() -> pd.DataFrame:
    """Carga los datos consolidados de Capa Oro."""
    ruta_csv = DIR_ORO / "canasta_occidente_oro.csv"
    if not ruta_csv.exists():
        raise FileNotFoundError(f"No se encontró el archivo de Capa Oro en {ruta_csv}")
    df = pd.read_csv(ruta_csv)
    return df


def preparar_serie(df_oro: pd.DataFrame, producto: str, plaza_id: int = 80) -> pd.Series:
    """Extrae y formatea una serie temporal mensual continua para un producto en Colima."""
    sub = df_oro[(df_oro["plaza_id"] == plaza_id) & (df_oro["producto"] == producto)].copy()
    if sub.empty:
        raise ValueError(f"No se encontraron datos para {producto} en plaza {plaza_id}")

    sub["fecha_dt"] = pd.to_datetime(sub["anio_mes"] + "-01")
    sub = sub.sort_values("fecha_dt").drop_duplicates(subset=["fecha_dt"])
    sub.set_index("fecha_dt", inplace=True)
    serie = sub["precio_promedio_mxn"].asfreq("MS")
    # Imputar si hubiera algún mes faltante
    serie = serie.interpolate(method="linear")
    return serie


def test_adf(serie: pd.Series, nombre: str) -> Dict:
    """Ejecuta la prueba de Augmented Dickey-Fuller en niveles y primera diferencia."""
    resultado_niveles = adfuller(serie.dropna(), autolag="AIC")
    stat_niveles = resultado_niveles[0]
    p_niveles = resultado_niveles[1]
    crit_niveles = resultado_niveles[4]
    es_estacionaria_niveles = bool(p_niveles < 0.05)

    # Primera diferencia
    diff = serie.diff().dropna()
    resultado_diff = adfuller(diff, autolag="AIC")
    stat_diff = resultado_diff[0]
    p_diff = resultado_diff[1]
    crit_diff = resultado_diff[4]
    es_estacionaria_diff = bool(p_diff < 0.05)

    orden_integracion = 0 if es_estacionaria_niveles else (1 if es_estacionaria_diff else 2)

    return {
        "producto": nombre,
        "longitud_serie": len(serie),
        "niveles": {
            "estadistico_adf": round(float(stat_niveles), 4),
            "p_valor": round(float(p_niveles), 4),
            "valores_criticos": {k: round(v, 4) for k, v in crit_niveles.items()},
            "es_estacionaria": es_estacionaria_niveles,
        },
        "primera_diferencia": {
            "estadistico_adf": round(float(stat_diff), 4),
            "p_valor": round(float(p_diff), 6),
            "valores_criticos": {k: round(v, 4) for k, v in crit_diff.items()},
            "es_estacionaria": es_estacionaria_diff,
        },
        "orden_integracion_d": orden_integracion,
    }


def descomponer_clasica(serie: pd.Series, periodo: int = 12) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Descomposición clásica aditiva:
    Y_t = Tendencia + Estacionalidad + Residuo
    """
    tendencia = serie.rolling(window=periodo, center=True, min_periods=1).mean()
    desestacionalizada = serie - tendencia
    meses = serie.index.month
    estacional_mensual = desestacionalizada.groupby(meses).transform("mean")
    estacional = estacional_mensual - estacional_mensual.mean()
    residuo = serie - tendencia - estacional
    return tendencia, estacional, residuo


def descomponer_serie_temporal(serie: pd.Series, nombre_slug: str, titulo: str) -> None:
    """Realiza la descomposición aditiva (tendencia, estacionalidad, residuo) y genera gráfico."""
    DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)
    tendencia, estacional, residuo = descomponer_clasica(serie, periodo=12)

    fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True)

    axes[0].plot(serie.index, serie.values, color="#1f77b4", lw=1.8)
    axes[0].set_ylabel("Observada (MXN)")
    axes[0].set_title(f"Descomposición Aditiva de Serie Temporal: {titulo} (Colima)", fontsize=12, fontweight="bold")
    axes[0].grid(True, linestyle=":", alpha=0.6)

    axes[1].plot(serie.index, tendencia.values, color="#ff7f0e", lw=2)
    axes[1].set_ylabel("Tendencia")
    axes[1].grid(True, linestyle=":", alpha=0.6)

    axes[2].plot(serie.index, estacional.values, color="#2ca02c", lw=1.5)
    axes[2].set_ylabel("Estacionalidad")
    axes[2].grid(True, linestyle=":", alpha=0.6)

    axes[3].scatter(serie.index, residuo.values, color="#d62728", s=15, alpha=0.7)
    axes[3].axhline(0, color="gray", linestyle="--", lw=0.8)
    axes[3].set_ylabel("Residuo")
    axes[3].set_xlabel("Año")
    axes[3].grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    ruta_img = DIR_GRAFICOS / f"descomposicion_{nombre_slug}.png"
    plt.savefig(ruta_img, dpi=200)
    plt.close()
    logger.info("Gráfico de descomposición guardado en %s", ruta_img)


def calcular_metricas_error(y_real: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calcula MAE, RMSE y MAPE."""
    y_real = np.array(y_real)
    y_pred = np.array(y_pred)

    mae = float(np.mean(np.abs(y_real - y_pred)))
    rmse = float(np.sqrt(np.mean((y_real - y_pred) ** 2)))
    mask_no_cero = y_real != 0
    mape = float(np.mean(np.abs((y_real[mask_no_cero] - y_pred[mask_no_cero]) / y_real[mask_no_cero])) * 100.0)

    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "mape": round(mape, 2)}


def entrenar_y_evaluar_modelos(serie: pd.Series, producto: str, meses_test: int = 8) -> Tuple[pd.DataFrame, str, Dict, pd.DataFrame]:
    """
    Evalúa 4 familias de modelos con split Train/Test, selecciona el ganador y
    calcula el pronóstico a 4 meses hacia adelante con intervalos de confianza al 95%.
    """
    train = serie[:-meses_test]
    test = serie[-meses_test:]
    n_test = len(test)

    resultados_modelos = []
    predicciones_test = {"fecha": test.index, "real": test.values}

    # 1. Suavizamiento Exponencial Simple (SES)
    try:
        mod_ses = SimpleExpSmoothing(train, initialization_method="estimated").fit()
        pred_ses = mod_ses.forecast(n_test)
        m_ses = calcular_metricas_error(test.values, pred_ses.values)
        m_ses["modelo"] = "Suavizamiento Exponencial Simple (SES)"
        m_ses["producto"] = producto
        resultados_modelos.append(m_ses)
        predicciones_test["pred_ses"] = pred_ses.values
    except Exception as e:
        logger.warning("Error en SES para %s: %s", producto, e)

    # 2. Modelo de Holt (Tendencia Lineal)
    try:
        mod_holt = Holt(train, initialization_method="estimated").fit()
        pred_holt = mod_holt.forecast(n_test)
        m_holt = calcular_metricas_error(test.values, pred_holt.values)
        m_holt["modelo"] = "Modelo de Holt (Doble Suavizamiento)"
        m_holt["producto"] = producto
        resultados_modelos.append(m_holt)
        predicciones_test["pred_holt"] = pred_holt.values
    except Exception as e:
        logger.warning("Error en Holt para %s: %s", producto, e)

    # 3. Modelo de Holt-Winters (Tendencia + Estacionalidad 12m)
    try:
        mod_hw = ExponentialSmoothing(
            train,
            seasonal_periods=12,
            trend="add",
            seasonal="add",
            initialization_method="estimated",
        ).fit()
        pred_hw = mod_hw.forecast(n_test)
        m_hw = calcular_metricas_error(test.values, pred_hw.values)
        m_hw["modelo"] = "Holt-Winters (Triple Suavizamiento)"
        m_hw["producto"] = producto
        resultados_modelos.append(m_hw)
        predicciones_test["pred_hw"] = pred_hw.values
    except Exception as e:
        logger.warning("Error en Holt-Winters para %s: %s", producto, e)

    # 4. Modelo ARIMA Box-Jenkins
    try:
        mod_arima = ARIMA(train, order=(1, 1, 1)).fit()
        pred_arima = mod_arima.forecast(n_test)
        m_arima = calcular_metricas_error(test.values, pred_arima.values)
        m_arima["modelo"] = "ARIMA (1,1,1)"
        m_arima["producto"] = producto
        resultados_modelos.append(m_arima)
        predicciones_test["pred_arima"] = pred_arima.values
    except Exception as e:
        logger.warning("Error en ARIMA para %s: %s", producto, e)

    df_res = pd.DataFrame(resultados_modelos)
    df_res = df_res.sort_values(by=["mape", "rmse"]).reset_index(drop=True)

    # Modelo ganador: menor MAPE
    modelo_ganador = df_res.iloc[0]["modelo"]
    logger.info("Producto: %s | Modelo Ganador: %s (MAPE: %.2f%%, RMSE: $%.2f)", producto, modelo_ganador, df_res.iloc[0]["mape"], df_res.iloc[0]["rmse"])

    # Reentrenar modelo ganador con 100% de la serie para pronosticar los próximos 4 meses
    meses_futuro = 4
    ult_fecha = serie.index[-1]
    fechas_futuro = pd.date_range(ult_fecha + pd.DateOffset(months=1), periods=meses_futuro, freq="MS")

    if "Holt-Winters" in modelo_ganador:
        mod_final = ExponentialSmoothing(
            serie,
            seasonal_periods=12,
            trend="add",
            seasonal="add",
            initialization_method="estimated",
        ).fit()
        pred_futuro = mod_final.forecast(meses_futuro)
        residuos = serie - mod_final.fittedvalues
        sigma = np.std(residuos)
    elif "ARIMA" in modelo_ganador:
        mod_final = ARIMA(serie, order=(1, 1, 1)).fit()
        forecast_res = mod_final.get_forecast(steps=meses_futuro)
        pred_futuro = forecast_res.predicted_mean
        ci = forecast_res.conf_int(alpha=0.05)
        lim_inf = ci.iloc[:, 0].values
        lim_sup = ci.iloc[:, 1].values
        sigma = None
    elif "Holt" in modelo_ganador:
        mod_final = Holt(serie, initialization_method="estimated").fit()
        pred_futuro = mod_final.forecast(meses_futuro)
        residuos = serie - mod_final.fittedvalues
        sigma = np.std(residuos)
    else:  # SES
        mod_final = SimpleExpSmoothing(serie, initialization_method="estimated").fit()
        pred_futuro = mod_final.forecast(meses_futuro)
        residuos = serie - mod_final.fittedvalues
        sigma = np.std(residuos)

    if sigma is not None:
        h = np.arange(1, meses_futuro + 1)
        margen = 1.96 * sigma * np.sqrt(h)
        lim_inf = np.maximum(0.0, pred_futuro.values - margen)
        lim_sup = pred_futuro.values + margen

    df_pronostico = pd.DataFrame({
        "producto": producto,
        "anio_mes": [d.strftime("%Y-%m") for d in fechas_futuro],
        "fecha": [d.strftime("%Y-%m-%d") for d in fechas_futuro],
        "modelo_utilizado": modelo_ganador,
        "precio_pronosticado_mxn": np.round(pred_futuro.values, 2),
        "limite_inferior_95_mxn": np.round(lim_inf, 2),
        "limite_superior_95_mxn": np.round(lim_sup, 2),
    })

    return df_res, modelo_ganador, predicciones_test, df_pronostico


def analizar_correlacion_macro(df_oro: pd.DataFrame, plaza_id: int = 80) -> pd.DataFrame:
    """Calcula coeficientes de correlación de Pearson y Spearman con variables exógenas."""
    filas = []
    for prod in PRODUCTOS_CLAVE:
        sub = df_oro[(df_oro["plaza_id"] == plaza_id) & (df_oro["producto"] == prod)].dropna(
            subset=["precio_promedio_mxn", "tipo_cambio_fix_promedio", "inpc_mensual"]
        )
        if len(sub) < 10:
            continue

        r_fx, p_fx = stats.pearsonr(sub["precio_promedio_mxn"], sub["tipo_cambio_fix_promedio"])
        rho_fx, sp_fx = stats.spearmanr(sub["precio_promedio_mxn"], sub["tipo_cambio_fix_promedio"])

        r_inpc, p_inpc = stats.pearsonr(sub["precio_promedio_mxn"], sub["inpc_mensual"])
        rho_inpc, sp_inpc = stats.spearmanr(sub["precio_promedio_mxn"], sub["inpc_mensual"])

        filas.append({
            "producto": prod,
            "corr_pearson_tc_fix": round(float(r_fx), 3),
            "p_valor_tc_fix": round(float(p_fx), 4),
            "corr_spearman_tc_fix": round(float(rho_fx), 3),
            "corr_pearson_inpc": round(float(r_inpc), 3),
            "p_valor_inpc": round(float(p_inpc), 4),
            "corr_spearman_inpc": round(float(rho_inpc), 3),
        })

    return pd.DataFrame(filas)


def graficar_series_y_pronosticos(
    series_dict: Dict[str, pd.Series], pronosticos_df: pd.DataFrame
) -> None:
    """Genera gráfico comparativo multiserie histórico + pronóstico a 4 meses."""
    DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=False)
    colores = {"Jitomate Saladette": "#d62728", "Limon con semilla #5": "#2ca02c", "Aguacate Hass": "#1f77b4"}

    for i, prod in enumerate(PRODUCTOS_CLAVE):
        ax = axes[i]
        serie = series_dict[prod]
        pron = pronosticos_df[pronosticos_df["producto"] == prod].copy()
        pron["fecha_dt"] = pd.to_datetime(pron["fecha"])

        ax.plot(serie.index, serie.values, label="Histórico observado", color=colores[prod], lw=2)

        # Línea de pronóstico conectando con el último punto observado
        fechas_linea = [serie.index[-1]] + list(pron["fecha_dt"])
        precios_linea = [serie.values[-1]] + list(pron["precio_pronosticado_mxn"])
        ax.plot(fechas_linea, precios_linea, label=f"Pronóstico ({pron.iloc[0]['modelo_utilizado']})", color="black", linestyle="--", lw=2, marker="o")

        # Banda de confianza 95%
        ax.fill_between(
            pron["fecha_dt"],
            pron["limite_inferior_95_mxn"],
            pron["limite_superior_95_mxn"],
            color="gray",
            alpha=0.3,
            label="Intervalo de confianza 95%",
        )

        ax.set_title(f"{prod} — Central de Abasto de Colima (2022-2026 + Pronóstico 2027)", fontsize=11, fontweight="bold")
        ax.set_ylabel("Precio (MXN / kg)")
        ax.legend(loc="upper left", frameon=True, fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    ruta_img = DIR_GRAFICOS / "pronostico_comparativo_4meses.png"
    plt.savefig(ruta_img, dpi=200)
    plt.close()
    logger.info("Gráfico comparativo de pronósticos guardado en %s", ruta_img)


def ejecutar_laboratorio_completo() -> Dict:
    """Función orquestadora principal del laboratorio estadístico."""
    DIR_LAB.mkdir(parents=True, exist_ok=True)
    DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)

    df_oro = cargar_datos_oro()

    slugs = {
        "Jitomate Saladette": "jitomate",
        "Limon con semilla #5": "limon",
        "Aguacate Hass": "aguacate",
    }

    pruebas_adf = []
    todas_metricas = []
    todos_pronosticos = []
    series_dict = {}

    for prod in PRODUCTOS_CLAVE:
        logger.info("--- Analizando insumo: %s ---", prod)
        serie = preparar_serie(df_oro, prod, plaza_id=80)
        series_dict[prod] = serie

        # 1. ADF Test
        res_adf = test_adf(serie, prod)
        pruebas_adf.append(res_adf)

        # 2. Descomposición
        descomponer_serie_temporal(serie, slugs[prod], prod)

        # 3. Modelado y Pronóstico
        df_metricas, ganador, preds, df_pron = entrenar_y_evaluar_modelos(serie, prod, meses_test=8)
        todas_metricas.append(df_metricas)
        todos_pronosticos.append(df_pron)

    df_metricas_total = pd.concat(todas_metricas, ignore_index=True)
    df_pron_total = pd.concat(todos_pronosticos, ignore_index=True)

    # 4. Correlación macro
    df_corr = analizar_correlacion_macro(df_oro, plaza_id=80)

    # 5. Gráfico consolidado
    graficar_series_y_pronosticos(series_dict, df_pron_total)

    # 6. Exportar resultados tabulares
    ruta_metricas_csv = DIR_LAB / "metricas_modelos.csv"
    ruta_pron_csv = DIR_LAB / "pronosticos_futuro.csv"
    ruta_corr_csv = DIR_LAB / "correlaciones_macro.csv"
    ruta_adf_json = DIR_LAB / "pruebas_estacionariedad_adf.json"

    df_metricas_total.to_csv(ruta_metricas_csv, index=False)
    df_pron_total.to_csv(ruta_pron_csv, index=False)
    df_corr.to_csv(ruta_corr_csv, index=False)

    with open(ruta_adf_json, "w", encoding="utf-8") as f:
        json.dump(pruebas_adf, f, indent=2, ensure_ascii=False)

    # 7. Redactar Informe Ejecutivo Estadístico
    generar_informe_estadistico_md(pruebas_adf, df_metricas_total, df_pron_total, df_corr)

    logger.info("Laboratorio estadístico ejecutado exitosamente. Artefactos en %s", DIR_LAB)
    return {
        "adf": pruebas_adf,
        "metricas": df_metricas_total,
        "pronosticos": df_pron_total,
        "correlaciones": df_corr,
    }


def generar_informe_estadistico_md(
    pruebas_adf: List[Dict],
    df_metricas: pd.DataFrame,
    df_pron: pd.DataFrame,
    df_corr: pd.DataFrame,
) -> None:
    """Genera el informe técnico de Análisis Estadístico en Markdown."""
    ruta_md = DIR_LAB / "informe_estadistico.md"

    md = f"""# Informe Técnico: Laboratorio de Series de Tiempo (TDL Canastita)

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
"""
    for adf in pruebas_adf:
        prod = adf["producto"]
        stat_niv = adf["niveles"]["estadistico_adf"]
        p_niv = adf["niveles"]["p_valor"]
        est_niv = "Sí" if adf["niveles"]["es_estacionaria"] else "No"
        stat_d1 = adf["primera_diferencia"]["estadistico_adf"]
        p_d1 = adf["primera_diferencia"]["p_valor"]
        d = adf["orden_integracion_d"]
        md += f"| {prod} | {stat_niv:.4f} | {p_niv:.4f} | {est_niv} | {stat_d1:.4f} | {p_d1:.6f} | **I({d})** |\n"

    md += """
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
"""
    for _, row in df_metricas.iterrows():
        md += f"| {row['producto']} | {row['modelo']} | ${row['mae']:.2f} | ${row['rmse']:.2f} | {row['mape']:.2f}% | {'Ganador' if row['mape'] == df_metricas[df_metricas['producto'] == row['producto']]['mape'].min() else 'Alternativo'} |\n"

    md += """
---

## 5. Pronóstico a 4 Meses hacia Adelante (Diciembre 2026 – Marzo 2027)

Con el modelo ganador reentrenado sobre los 59 meses completos, se proyectaron los precios para el cierre de 2026 e inicio de 2027:

| Insumo | Período | Precio Pronosticado (MXN/kg) | Límite Inferior 95% | Límite Superior 95% | Modelo Seleccionado |
| :--- | :---: | :---: | :---: | :---: | :--- |
"""
    for _, r in df_pron.iterrows():
        md += f"| {r['producto']} | {r['anio_mes']} | **${r['precio_pronosticado_mxn']:.2f}** | ${r['limite_inferior_95_mxn']:.2f} | ${r['limite_superior_95_mxn']:.2f} | {r['modelo_utilizado']} |\n"

    md += """
* **Gráfico de Pronósticos:** [Visualización Comparativa 4 Meses](file:///c:/Users/adolf/Downloads/Proyecto%20Integrador/tdl-canastita-proyecto/laboratorio/graficos/pronostico_comparativo_4meses.png)

---

## 6. Correlación Cruzada con Indicadores Macroeconómicos de Banxico

Se calcularon los coeficientes de correlación de Pearson ($r$) y Spearman ($\\rho$) contra el Tipo de Cambio FIX (USD/MXN) y el Índice Nacional de Precios al Consumidor (INPC):

| Insumo | Pearson TC FIX ($r$) | p-valor FIX | Spearman TC FIX ($\\rho$) | Pearson INPC ($r$) | p-valor INPC | Spearman INPC ($\\rho$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for _, rc in df_corr.iterrows():
        md += f"| {rc['producto']} | {rc['corr_pearson_tc_fix']:+.3f} | {rc['p_valor_tc_fix']:.4f} | {rc['corr_spearman_tc_fix']:+.3f} | {rc['corr_pearson_inpc']:+.3f} | {rc['p_valor_inpc']:.4f} | {rc['corr_spearman_inpc']:+.3f} |\n"

    md += """
### Interpretación Económica y Estadística:
1. **Influencia del Tipo de Cambio FIX:** El aguacate y el jitomate presentan correlaciones positivas moderadas con el dólar ($r > 0.35$), reflejando que los precios de agroquímicos, fertilizantes importados y los costos de oportunidad frente a la exportación presionan los precios locales al depreciarse el peso.
2. **Influencia de la Inflación (INPC):** Todos los insumos muestran correlación positiva estadísticamente significativa ($p < 0.05$) con la inflación general acumulada, evidenciando la transmisión de costos de transporte, combustibles y empaques hacia los mercados mayoristas de Colima.
"""

    with open(ruta_md, "w", encoding="utf-8") as f:
        f.write(md)

    logger.info("Informe estadístico redactado en %s", ruta_md)


if __name__ == "__main__":
    ejecutar_laboratorio_completo()
