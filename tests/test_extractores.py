"""
tests/test_extractores.py
Pruebas básicas para verificar que el ExtractorEtico, el parser de SNIIM
y los archivos de la serie histórica en capa bronce funcionen bien.
"""

import json
from pathlib import Path
from extractores.base import ExtractorEtico, UA
from extractores.sniim_canasta import parsear_tabla_sniim, PLAZAS_OCCIDENTE

RAIZ = Path(__file__).resolve().parent.parent


def test_user_agent_identificado():
    ext = ExtractorEtico(pausa=1.0)
    assert "TDL-Observatorio/1.0" in UA
    assert "23460528@colima.tecnm.mx" in ext.sesion.headers["User-Agent"]


def test_parsear_tabla_sniim_muestra():
    html_ejemplo = """
    <table>
      <tr><td>Encabezado</td></tr>
      <tr>
        <td>03/10/2025</td>
        <td>Limon c/semilla # 5</td>
        <td>Primera</td>
        <td>Kilogramo</td>
        <td>Colima</td>
        <td>25.00</td>
        <td>28.00</td>
        <td>28.00</td>
        <td></td>
      </tr>
    </table>
    """
    filas = parsear_tabla_sniim(
        html_ejemplo,
        PLAZAS_OCCIDENTE[80],
        "2026-11-06T00:00:00+00:00",
        "http://www.economia-sniim.gob.mx/ejemplo",
    )
    assert len(filas) == 1
    assert filas[0]["anio_mes"] == "2025-10"
    assert filas[0]["ciudad"] == "Colima"
    assert filas[0]["precio_frecuente_mxn"] == 28.0


def test_serie_historica_minimo_36_periodos():
    meta_sniim = RAIZ / "data" / "bronce" / "sniim_canasta" / "historico" / "sniim_occidente_historico_2022_2026.meta.json"
    meta_fx = RAIZ / "data" / "bronce" / "macro_api" / "tipo_cambio" / "usd_mxn_historico_2022_2026.meta.json"

    if meta_sniim.exists():
        datos = json.loads(meta_sniim.read_text(encoding="utf-8"))
        assert datos["total_periodos_mensuales"] >= 36

    if meta_fx.exists():
        datos_fx = json.loads(meta_fx.read_text(encoding="utf-8"))
        assert datos_fx["total_periodos_mensuales"] >= 36
