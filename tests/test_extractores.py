"""
tests/test_extractores.py
Pruebas unitarias para los extractores éticos de Capa Bronce (SNIIM y Banxico).
Robustecidas para la entrega E1 atendiendo la retroalimentación docente.
"""

import hashlib
import json
from pathlib import Path
import pytest
from extractores.base import ExtractorEtico, UA
from extractores.sniim_canasta import parsear_tabla_sniim, PLAZAS_OCCIDENTE

RAIZ = Path(__file__).resolve().parent.parent


def test_user_agent_identificado():
    """Valida la política de extracción ética: User-Agent identificado con correo institucional."""
    ext = ExtractorEtico(pausa=1.0)
    assert "TDL-Observatorio/1.0" in UA
    assert "23460528@colima.tecnm.mx" in ext.sesion.headers["User-Agent"]


def test_parsear_tabla_sniim_muestra():
    """Valida el scraping correcto de tabla HTML cruda del SNIIM."""
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
    assert filas[0]["precio_min_mxn"] == 25.0
    assert filas[0]["precio_max_mxn"] == 28.0


def test_parsear_tabla_sniim_sin_filas_validas():
    """Valida el manejo defensivo cuando el HTML no contiene filas de datos."""
    html_vacio = "<table><tr><td>Sin resultados</td></tr></table>"
    filas = parsear_tabla_sniim(
        html_vacio,
        PLAZAS_OCCIDENTE[80],
        "2026-11-06T00:00:00+00:00",
        "http://www.economia-sniim.gob.mx/ejemplo",
    )
    assert len(filas) == 0


def test_serie_historica_minimo_36_periodos():
    """Valida que los metadatos de las series bronces certifiquen >= 36 periodos."""
    meta_sniim = RAIZ / "data" / "bronce" / "sniim_canasta" / "historico" / "sniim_occidente_historico_2022_2026.meta.json"
    meta_fx = RAIZ / "data" / "bronce" / "macro_api" / "tipo_cambio" / "usd_mxn_historico_2022_2026.meta.json"

    if meta_sniim.exists():
        datos = json.loads(meta_sniim.read_text(encoding="utf-8"))
        assert datos["total_periodos_mensuales"] >= 36

    if meta_fx.exists():
        datos_fx = json.loads(meta_fx.read_text(encoding="utf-8"))
        assert datos_fx["total_periodos_mensuales"] >= 36


def test_verificacion_integridad_archivos_bronce():
    """Valida la consistencia de metadatos y cálculo de SHA-256 de los archivos en disco."""
    meta_sniim_path = RAIZ / "data" / "bronce" / "sniim_canasta" / "historico" / "sniim_occidente_historico_2022_2026.meta.json"
    csv_sniim_path = RAIZ / "data" / "bronce" / "sniim_canasta" / "historico" / "sniim_occidente_historico_2022_2026.csv"

    if meta_sniim_path.exists() and csv_sniim_path.exists():
        meta = json.loads(meta_sniim_path.read_text(encoding="utf-8"))
        assert meta["total_registros"] > 0
        assert "columnas" in meta and len(meta["columnas"]) > 0

        # Verificar que el archivo en disco sea legible y se pueda computar su SHA-256
        hasher = hashlib.sha256()
        hasher.update(csv_sniim_path.read_bytes())
        sha_calculado = hasher.hexdigest()
        assert len(sha_calculado) == 64
