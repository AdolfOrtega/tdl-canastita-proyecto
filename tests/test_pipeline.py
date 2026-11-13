"""
tests/test_pipeline.py
Suite de pruebas automatizadas para el pipeline Medallion (Capa Plata y Capa Oro).
Atiende la retroalimentación de E0: 'Robustecer la suite tests/ antes de procesar
las transformaciones de la capa Plata'.
"""

import os
import shutil
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from pipeline.limpieza_plata import (
    normalizar_productos_y_plazas,
    filtrar_y_cuarentenar,
    detectar_atipicos_iqr,
    procesar_capa_plata,
)
from pipeline.construir_oro import (
    agregar_mensual_sniim,
    integrar_macro_oro,
    calcular_metricas_oro,
    procesar_capa_oro,
)

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def datos_bronce_sinteticos():
    """Genera datos sintéticos con casos válidos y casos límite corruptos."""
    return pd.DataFrame([
        {
            "fecha_observacion_raw": "05/01/2024",
            "anio_mes": "2024-01",
            "plaza_id": 80,
            "estado": "Colima",
            "ciudad": "Colima",
            "nombre_plaza": "Colima: Centros de distribucion de Colima",
            "producto": "Tomate Saladette",
            "calidad": "Primera",
            "presentacion": "Kilogramo",
            "origen": "Sinaloa",
            "precio_min_mxn": 20.0,
            "precio_max_mxn": 24.0,
            "precio_frecuente_mxn": 22.0,
            "observaciones": "",
            "_fuente": "SNIIM",
            "_url_origen": "http://ejemplo.com",
            "_capturado_en_utc": "2024-01-05T10:00:00Z",
        },
        {
            "fecha_observacion_raw": "10/01/2024",
            "anio_mes": "2024-01",
            "plaza_id": 80,
            "estado": "Colima",
            "ciudad": "Colima",
            "nombre_plaza": "Colima: Centros de distribucion de Colima",
            "producto": "Limon c/semilla # 5",
            "calidad": "Primera",
            "presentacion": "Kilogramo",
            "origen": "Michoacan",
            "precio_min_mxn": 28.0,
            "precio_max_mxn": 32.0,
            "precio_frecuente_mxn": 30.0,
            "observaciones": "",
            "_fuente": "SNIIM",
            "_url_origen": "http://ejemplo.com",
            "_capturado_en_utc": "2024-01-10T10:00:00Z",
        },
        # Registro corrupto 1: precio negativo
        {
            "fecha_observacion_raw": "15/01/2024",
            "anio_mes": "2024-01",
            "plaza_id": 80,
            "estado": "Colima",
            "ciudad": "Colima",
            "nombre_plaza": "Colima: Centros de distribucion de Colima",
            "producto": "Aguacate Hass",
            "calidad": "Primera",
            "presentacion": "Kilogramo",
            "origen": "Michoacan",
            "precio_min_mxn": -10.0,
            "precio_max_mxn": 50.0,
            "precio_frecuente_mxn": 45.0,
            "observaciones": "Corrupto",
            "_fuente": "SNIIM",
            "_url_origen": "http://ejemplo.com",
            "_capturado_en_utc": "2024-01-15T10:00:00Z",
        },
        # Registro corrupto 2: max < min
        {
            "fecha_observacion_raw": "16/01/2024",
            "anio_mes": "2024-01",
            "plaza_id": 140,
            "estado": "Jalisco",
            "ciudad": "Guadalajara",
            "nombre_plaza": "Jalisco: Mercado de Abasto de Guadalajara",
            "producto": "Cebolla Bola",
            "calidad": "Primera",
            "presentacion": "Kilogramo",
            "origen": "Guanajuato",
            "precio_min_mxn": 30.0,
            "precio_max_mxn": 15.0,
            "precio_frecuente_mxn": 20.0,
            "observaciones": "Invertido",
            "_fuente": "SNIIM",
            "_url_origen": "http://ejemplo.com",
            "_capturado_en_utc": "2024-01-16T10:00:00Z",
        },
        # Registro corrupto 3: fecha no parseable
        {
            "fecha_observacion_raw": "99/99/9999",
            "anio_mes": "invalido",
            "plaza_id": 160,
            "estado": "Michoacan",
            "ciudad": "Morelia",
            "nombre_plaza": "Michoacan: Mercado de Abasto de Morelia",
            "producto": "Papa Alpha",
            "calidad": "Primera",
            "presentacion": "Kilogramo",
            "origen": "Puebla",
            "precio_min_mxn": 18.0,
            "precio_max_mxn": 22.0,
            "precio_frecuente_mxn": 20.0,
            "observaciones": "Fecha rota",
            "_fuente": "SNIIM",
            "_url_origen": "http://ejemplo.com",
            "_capturado_en_utc": "2024-01-17T10:00:00Z",
        },
    ])


def test_normalizacion_nombres_productos():
    """Valida la resolución de entidades y homologación de nombres a estándar regional."""
    df_raw = pd.DataFrame({
        "producto": ["Tomate Saladette", "Limon c/semilla # 5", "Aguacate Hass", "Cebolla Bola"],
        "ciudad": ["Colima", "Guadalajara", "Morelia", "Colima"],
    })
    df_norm = normalizar_productos_y_plazas(df_raw)
    nombres_result = df_norm["producto"].tolist()
    assert "Jitomate Saladette" in nombres_result
    assert "Limon con semilla #5" in nombres_result
    assert "Aguacate Hass" in nombres_result
    assert "Tomate Saladette" not in nombres_result


def test_puerta_calidad_rechazo_y_cuarentena(datos_bronce_sinteticos):
    """Verifica que Puerta 1 separe registros limpios de corruptos hacia cuarentena."""
    df_validos, df_rechazados = filtrar_y_cuarentenar(datos_bronce_sinteticos)

    # De los 5 sintéticos, 2 son válidos y 3 son corruptos
    assert len(df_validos) == 2
    assert len(df_rechazados) == 3

    # Motivos de rechazo esperados
    motivos = df_rechazados["motivo_rechazo"].tolist()
    assert any("precio_negativo_o_cero" in m for m in motivos)
    assert any("precio_max_menor_min" in m for m in motivos)
    assert any("fecha_invalida" in m for m in motivos)


def test_deteccion_atipicos_iqr():
    """Valida que la regla de IQR identifique y etiquete outliers estadísticos."""
    precios = [20.0, 21.0, 20.5, 22.0, 21.5, 20.0, 21.0, 19.5, 20.5, 95.0]  # 95 es atípico extremo
    fechas = pd.date_range("2024-01-01", periods=len(precios), freq="D")
    df = pd.DataFrame({
        "producto": ["Jitomate Saladette"] * len(precios),
        "plaza_id": [80] * len(precios),
        "fecha": fechas,
        "precio_frecuente_mxn": precios,
    })

    df_proc = detectar_atipicos_iqr(df)
    assert "es_atipico_iqr" in df_proc.columns
    assert "precio_frecuente_limpio" in df_proc.columns

    # El último valor (95.0) debe estar marcado como atípico
    assert df_proc.iloc[-1]["es_atipico_iqr"] == True
    # Y los primeros valores normales deben ser False
    assert df_proc.iloc[0]["es_atipico_iqr"] == False
    # El precio limpio debe estar acotado
    assert df_proc.iloc[-1]["precio_frecuente_limpio"] < 95.0


def test_integracion_macro_oro():
    """Valida el cruce correcto de SNIIM mensual con tipo de cambio FIX e INPC."""
    df_sniim_mensual = pd.DataFrame({
        "anio_mes": ["2024-01", "2024-02"],
        "plaza_id": [80, 80],
        "ciudad": ["Colima", "Colima"],
        "producto": ["Jitomate Saladette", "Jitomate Saladette"],
        "precio_promedio_mxn": [20.0, 25.0],
        "precio_min_mes": [18.0, 22.0],
        "precio_max_mes": [22.0, 28.0],
        "precio_mediana_mxn": [20.0, 25.0],
        "volatilidad_precio_std": [1.4, 2.1],
        "num_observaciones": [15, 14],
    })

    df_fx = pd.DataFrame({
        "fecha_iso": ["2024-01-15", "2024-02-15"],
        "anio_mes": ["2024-01", "2024-02"],
        "tipo_cambio_fix": [17.0, 17.5],
    })

    df_inpc = pd.DataFrame({
        "anio_mes": ["2024-01", "2024-02"],
        "valor": [133.5, 134.1],
    })

    df_oro = integrar_macro_oro(df_sniim_mensual, df_fx, df_inpc)

    assert "tipo_cambio_fix_promedio" in df_oro.columns
    assert "inpc_mensual" in df_oro.columns
    assert "precio_usd" in df_oro.columns

    # Verificar cálculo en USD (20 / 17 ~ 1.176)
    assert pytest.approx(df_oro.loc[0, "precio_usd"], rel=1e-2) == 20.0 / 17.0


def test_calculo_metricas_variacion_oro():
    """Valida las métricas de variación intermensual (MoM) y anual (YoY)."""
    df = pd.DataFrame({
        "anio_mes": ["2024-01", "2024-02", "2024-03"],
        "producto": ["Limón con semilla #5"] * 3,
        "plaza_id": [80] * 3,
        "precio_promedio_mxn": [20.0, 25.0, 30.0],
        "inpc_mensual": [130.0, 131.3, 132.613],
    })

    df_calc = calcular_metricas_oro(df)

    assert "variacion_mom_pct" in df_calc.columns
    assert "inflacion_mensual_pct" in df_calc.columns

    # Para el segundo mes, la variación de 20 a 25 es +25%
    assert pytest.approx(df_calc.loc[1, "variacion_mom_pct"], rel=1e-2) == 25.0
    # La inflación de 130 a 131.3 es +1.0%
    assert pytest.approx(df_calc.loc[1, "inflacion_mensual_pct"], rel=1e-2) == 1.0


def test_pipeline_completo_genera_archivos():
    """Ejecuta el procesamiento en capas Plata y Oro y verifica artefactos generados."""
    df_plata = procesar_capa_plata()
    assert df_plata is not None
    assert len(df_plata) > 0
    assert (RAIZ / "data" / "plata" / "canasta_occidente_plata.csv").exists()
    assert (RAIZ / "data" / "plata" / "canasta_occidente_plata.meta.json").exists()

    df_oro = procesar_capa_oro()
    assert df_oro is not None
    assert len(df_oro) > 0
    assert (RAIZ / "data" / "oro" / "canasta_occidente_oro.csv").exists()
    assert (RAIZ / "data" / "oro" / "canasta_occidente_oro.meta.json").exists()

    # Verificar que la serie temporal mensual tenga >= 36 periodos
    periodos_colima_jitomate = df_oro[
        (df_oro["plaza_id"] == 80) & (df_oro["producto"] == "Jitomate Saladette")
    ]["anio_mes"].nunique()
    assert periodos_colima_jitomate >= 36
