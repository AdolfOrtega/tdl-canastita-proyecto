"""
tests/test_e3_multivariado_sello.py
Suite de pruebas automatizadas para Entrega E3:
- Matriz multivariada, normalidad (Mardia/Henze-Zirkler/Mahalanobis), PCA y MANOVA/PERMANOVA.
- Optimizacion del pipeline (lxml + Parquet) y artefactos de publicacion abierta.
- Retrospectiva PSP E0-E3 y criterios del Sello TDL.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd

from laboratorio.analisis_multivariado_e3 import (
    VARIABLES_E3,
    calcular_mahalanobis,
    cargar_matriz_multivariada,
    ejecutar_pca,
    ejecutar_permanova,
    prueba_henze_zirkler,
    prueba_mardia,
)
from pipeline.benchmark_optimizacion_e3 import ejecutar_benchmark_optimizacion
from calidad.auditor_tdl import evaluar_criterios_sello_tdl
from calidad.retrospectiva_psp import cargar_defectos_psp, cargar_tiempos_psp, calcular_resumen_psp

RAIZ = Path(__file__).resolve().parent.parent


def test_matriz_multivariada_rango_completo_y_sin_nulos():
    """Valida >=5 variables continuas sin nulos y matriz de covarianzas no singular."""
    df_comp, info = cargar_matriz_multivariada()
    assert len(VARIABLES_E3) >= 5
    assert info["registros_completos_e3"] >= 500
    assert set(df_comp["ciudad"].unique()) == {"Colima", "Guadalajara", "Morelia"}
    assert int(df_comp[VARIABLES_E3].isna().sum().sum()) == 0

    X = df_comp[VARIABLES_E3].to_numpy(dtype=float)
    _, diag = calcular_mahalanobis(X)
    assert diag["rango_matriz_cov"] == len(VARIABLES_E3)
    assert np.isfinite(diag["num_condicion_cov"])
    assert diag["d2_media"] > 0


def test_normalidad_multivariada_mardia_y_henze_zirkler():
    """Verifica que Mardia y Henze-Zirkler acepten muestra normal sintetica y rechacen sesgo fuerte."""
    rng = np.random.default_rng(42)
    X_norm = rng.normal(loc=0.0, scale=1.0, size=(250, 4))
    m_n = prueba_mardia(X_norm)
    hz_n = prueba_henze_zirkler(X_norm)
    assert m_n["p_asimetria"] > 0.05
    assert hz_n["p_valor"] > 0.05

    X_sesg = np.exp(X_norm * 1.4)
    m_s = prueba_mardia(X_sesg)
    hz_s = prueba_henze_zirkler(X_sesg)
    assert m_s["p_asimetria"] < 0.01
    assert hz_s["p_valor"] < 0.01


def test_pca_propiedades_espectrales_y_permanova():
    """Valida suma de eigenvalores=p, varianza acumulada 100%, ortonormalidad y PERMANOVA."""
    df_comp, _ = cargar_matriz_multivariada()
    df_meta, df_proj, res_pca = ejecutar_pca(df_comp)

    assert len(df_meta) == len(VARIABLES_E3)
    assert abs(sum(res_pca["eigenvalores"]) - len(VARIABLES_E3)) < 1e-2
    assert abs(float(df_meta["varianza_acumulada_pct"].iloc[-1]) - 100.0) < 0.1
    assert res_pca["ortonormalidad_max_error"] < 1e-8
    assert {"PC1", "PC2", "PC3"}.issubset(df_proj.columns)

    X = df_comp[VARIABLES_E3].to_numpy(dtype=float)
    Z = (X - X.mean(axis=0)) / X.std(axis=0, ddof=1)
    perm = ejecutar_permanova(Z, df_comp["ciudad"].to_numpy(), n_perm=99, seed=123)
    assert perm["pseudo_f"] > 10.0
    assert perm["p_valor_permutacion"] <= 0.02


def test_artefactos_multivariados_y_benchmark_e3():
    """Verifica existencia y coherencia de JSON/CSV multivariados y mejora Parquet/lxml."""
    ruta_mv = RAIZ / "laboratorio" / "resultados_multivariado_e3.json"
    ruta_bench = RAIZ / "data" / "oro" / "benchmark_optimizacion_e3.json"
    assert ruta_mv.exists() and ruta_bench.exists()

    mv = json.loads(ruta_mv.read_text(encoding="utf-8"))
    assert mv["manova"]["manova_plazas_wilks"]["p_valor"] < 0.05
    assert mv["manova"]["manova_plazas_pillai"]["p_valor"] < 0.05

    bench_rapido = ejecutar_benchmark_optimizacion(n_repeticiones=2)
    assert bench_rapido["scraping_bronce"]["filas_paridad_exacta"] is True
    assert bench_rapido["total_end_to_end"]["ahorro_espacio_pct"] > 90.0
    assert (RAIZ / "LICENSE-DATA.md").exists()
    assert (RAIZ / "docs" / "E3" / "datasheet_canasta_oro.md").exists()


def test_retrospectiva_psp_y_sello_tdl_6_de_6():
    """Valida calculos PSP E0-E3 y cumplimiento completo de los 6 criterios del Sello TDL."""
    df_t = cargar_tiempos_psp()
    df_d = cargar_defectos_psp()
    res_psp = calcular_resumen_psp(df_t, df_d)

    etapas = {r["etapa"] for r in res_psp["evolucion_etapas"]}
    assert etapas == {"E0", "E1", "E2", "E3"}
    assert res_psp["totales_acumulados"]["horas_equipo"] > 40.0
    assert res_psp["totales_acumulados"]["defectos_totales"] >= 30

    sello = evaluar_criterios_sello_tdl(RAIZ)
    assert sello["total_criterios"] == 6
    assert sello["criterios_cumplidos"] == 6
    assert sello["apto_sello_tdl"] is True
