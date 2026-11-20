"""
tests/test_experimento_e2.py
Suite de pruebas estadisticas para el modulo de Diseno de Experimentos (Entrega E2).
Autora: Andrea Tairi Velazquez Gallardo (Data Statistician & Quality Auditor)
"""

import json
from pathlib import Path
import numpy as np
import pytest

from laboratorio.experimento_factorial_2k import (
    construir_diseno_2_3,
    construir_matrices_2_4,
    ejecutar_corrida_extractor,
)
from extractores.sniim_canasta import PLAZAS_OCCIDENTE

RAIZ = Path(__file__).resolve().parent.parent


def test_diseno_2_3_ortogonalidad_y_balance():
    """Valida balanceo exacto, aleatorizacion y ortogonalidad de la matriz 2^3 con 3 bloques."""
    df = construir_diseno_2_3(n_bloques=3, seed=20261123)
    assert len(df) == 24
    assert df["bloque"].nunique() == 3

    # Suma cero en cada factor (diseno balanceado)
    for col in ["A", "B", "C"]:
        assert int(df[col].sum()) == 0
        assert set(df[col].unique()) == {-1, 1}

    # Ortogonalidad entre todos los pares de factores principales e interaccion triple
    assert int((df["A"] * df["B"]).sum()) == 0
    assert int((df["A"] * df["C"]).sum()) == 0
    assert int((df["B"] * df["C"]).sum()) == 0
    assert int((df["A"] * df["B"] * df["C"]).sum()) == 0


def test_matriz_2_4_fraccionada_alias_resolucion_iv():
    """Verifica ahorro del 50% y relaciones exactas de alias I=ABCD en el diseno 2^(4-1)."""
    df_comp, df_frac, info = construir_matrices_2_4()

    assert len(df_comp) == 16
    assert len(df_frac) == 8
    assert info["ahorro_pct"] == 50.0
    assert info["relacion_definidora"] == "I = ABCD"
    assert info["resolucion"] == "IV"
    assert all(info["verificacion_algebraica"].values())


def test_paridad_html_parser_vs_lxml():
    """Valida que ambos parsers de BeautifulSoup extraigan exactamente el mismo conteo de filas."""
    html_muestra = """
    <table>
      <tr>
        <td>10/11/2026</td><td>Jitomate Saladette</td><td>Primera</td><td>Kilogramo</td>
        <td>Sinaloa</td><td>18.00</td><td>24.00</td><td>21.00</td><td></td>
      </tr>
      <tr>
        <td>10/11/2026</td><td>Aguacate Hass</td><td>Primera</td><td>Kilogramo</td>
        <td>Michoacan</td><td>45.00</td><td>52.00</td><td>48.00</td><td></td>
      </tr>
    </table>
    """
    paginas = [(html_muestra, PLAZAS_OCCIDENTE[80], "http://ejemplo.local")]
    _, err_hp, _, n_hp = ejecutar_corrida_extractor(paginas, 2, ciclos=1, hilos=1, parser="html.parser", formato="CSV")
    _, err_lx, _, n_lx = ejecutar_corrida_extractor(paginas, 2, ciclos=1, hilos=1, parser="lxml", formato="Parquet")

    assert err_hp == 0.0
    assert err_lx == 0.0
    assert n_hp == 2
    assert n_lx == 2


def test_artefactos_experimento_e2_generados():
    """Valida la existencia y estructura cuantitativa del archivo resultados_experimento_e2.json."""
    ruta_res = RAIZ / "laboratorio" / "resultados_experimento_e2.json"
    assert ruta_res.exists(), "Debe existir laboratorio/resultados_experimento_e2.json"

    res = json.loads(ruta_res.read_text(encoding="utf-8"))
    assert res["experimento_2_3"]["total_corridas"] == 24
    assert res["experimento_2_3"]["tasa_error_global_pct"] == 0.0
    assert res["experimento_2vias"]["total_corridas"] == 27
    assert res["comparativa_2_4_fraccionado"]["ahorro_pct"] == 50.0

    # Validar p-valores dentro de [0, 1]
    for fila in res["experimento_2_3"]["anova_original"]:
        if fila["p_valor"] is not None:
            assert 0.0 <= fila["p_valor"] <= 1.0
