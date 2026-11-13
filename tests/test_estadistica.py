"""
tests/test_estadistica.py
Suite de pruebas estadísticas automatizadas para el laboratorio de series de tiempo.
Autora: Andrea Tairi Velázquez Gallardo (Data Statistician & Verification Lead)
Proyecto: TDL Canastita - Entrega E1
"""

import numpy as np
import pandas as pd
import pytest

from laboratorio.pronostico_series_tiempo import (
    calcular_metricas_error,
    descomponer_clasica,
    ejecutar_prueba_adf,
    analizar_correlacion_macro,
)


def test_calculo_metricas_error_exactitud():
    """Valida las fórmulas matemáticas de MAE, RMSE y MAPE."""
    y_real = np.array([20.0, 25.0, 30.0, 35.0])
    y_pred = np.array([22.0, 24.0, 33.0, 35.0])

    # Errores absolutos: [2, 1, 3, 0] -> MAE = 6 / 4 = 1.5
    # Errores cuadráticos: [4, 1, 9, 0] -> RMSE = sqrt(14 / 4) = sqrt(3.5) ~ 1.8708
    # Errores relativos: [2/20, 1/25, 3/30, 0] = [0.10, 0.04, 0.10, 0.0] -> MAPE = 24% / 4 = 6.0%

    metricas = calcular_metricas_error(y_real, y_pred)
    assert metricas["mae"] == 1.5
    assert pytest.approx(metricas["rmse"], rel=1e-2) == 1.87
    assert pytest.approx(metricas["mape"], rel=1e-2) == 6.0


def test_descomposicion_clasica_identidad():
    """Verifica que la descomposición aditiva cumpla estrictamente Y_t = Tendencia + Estacionalidad + Residuo."""
    fechas = pd.date_range("2022-01-01", periods=36, freq="MS")
    # Serie sintética con tendencia lineal y ciclo anual
    t_base = np.linspace(20, 50, 36)
    est_base = np.tile([2.0, 4.0, -1.0, -3.0, -2.0, 0.0, 1.0, 3.0, 2.0, -2.0, -3.0, -1.0], 3)
    ruido = np.random.normal(0, 0.5, 36)
    serie = pd.Series(t_base + est_base + ruido, index=fechas)

    tendencia, estacional, residuo = descomponer_clasica(serie, periodo=12)

    # Reconstrucción: Y_reconstruida = T + S + R
    reconstruccion = tendencia + estacional + residuo

    # La diferencia entre la serie original y la suma de sus componentes debe ser numéricamente cero
    np.testing.assert_allclose(serie.values, reconstruccion.values, rtol=1e-5, atol=1e-5)


def test_test_adf_formato_y_orden_integracion():
    """Valida que la prueba Augmented Dickey-Fuller reporte estadísticos, p-valores y orden d."""
    fechas = pd.date_range("2022-01-01", periods=48, freq="MS")
    # Serie no estacionaria con caminata aleatoria (random walk con drift)
    np.random.seed(42)
    pasos = np.random.normal(1.0, 2.0, 48)
    serie_rw = pd.Series(np.cumsum(pasos) + 30.0, index=fechas)

    res = ejecutar_prueba_adf(serie_rw, "Serie Random Walk")

    assert res["producto"] == "Serie Random Walk"
    assert "niveles" in res and "primera_diferencia" in res
    assert "p_valor" in res["niveles"]
    assert "estadistico_adf" in res["niveles"]
    # El orden de integración debe ser 0, 1 o 2
    assert res["orden_integracion_d"] in [0, 1, 2]


def test_analisis_correlacion_macro_limites():
    """Verifica que los coeficientes de correlación estén acotados en [-1, 1]."""
    fechas = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06", "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"]
    n = len(fechas)
    df_sintetico = pd.DataFrame({
        "anio_mes": fechas,
        "plaza_id": [80] * n,
        "producto": ["Jitomate Saladette"] * n,
        "precio_promedio_mxn": [20.0 + i * 0.5 for i in range(n)],
        "tipo_cambio_fix_promedio": [17.0 + i * 0.1 for i in range(n)],
        "inpc_mensual": [130.0 + i * 0.3 for i in range(n)],
    })

    df_corr = analizar_correlacion_macro(df_sintetico, plaza_id=80)
    assert not df_corr.empty
    row = df_corr.iloc[0]

    # Coeficientes entre -1.0 y 1.0
    assert -1.0 <= row["corr_pearson_tc_fix"] <= 1.0
    assert -1.0 <= row["corr_spearman_tc_fix"] <= 1.0
    assert -1.0 <= row["corr_pearson_inpc"] <= 1.0
    # p-valores entre 0.0 y 1.0
    assert 0.0 <= row["p_valor_tc_fix"] <= 1.0
    assert 0.0 <= row["p_valor_inpc"] <= 1.0
