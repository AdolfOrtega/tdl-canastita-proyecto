"""
tests/test_e2_geo_iso.py
Pruebas automatizadas para fuente geoespacial DENUE-INEGI, sanitizacion LFPDPPP,
union espacial, linaje en Capa Oro y reglas de seguridad ISO/IEC 25010 y 25012.
Autor: Adolfo Rodriguez (Data Engineer & ISO Lead)
"""

import json
from pathlib import Path
import pandas as pd
import pytest

from extractores.denue_geo import (
    PLAZAS_GEO,
    construir_url_denue,
    sanitizar_registro_denue,
    sanitizar_url_token,
)
from pipeline.enriquecer_geo import (
    _punto_en_geometria,
    calcular_haversine_km,
    clasificar_categoria_y_anillo,
    ejecutar_union_espacial,
    filtrar_puerta_geoespacial,
    procesar_capa_plata_geo,
)
from pipeline.construir_oro import agregar_linaje_oro, integrar_geoespacial_oro
from calidad.evaluar_iso_25010_25012 import (
    analizar_fiabilidad_bitacora,
    analizar_mantenibilidad_codigo,
    auditar_seguridad_y_portabilidad,
    evaluar_iso_25010,
    evaluar_iso_25012,
    generar_reporte_iso_markdown,
)
from calidad.auditor_tdl import auditar_repositorio

RAIZ = Path(__file__).resolve().parent.parent


def test_url_denue_precision_6_decimales_y_sanitizacion_token():
    """Valida que la URL DENUE conserve >=4 decimales (evitando error Morelia) y redacte el token."""
    url = construir_url_denue("frutas", 19.7060, -101.1950, 2500, "TOKEN_SECRETO_XYZ")
    assert "19.706000,-101.195000" in url
    limpia = sanitizar_url_token(url, "TOKEN_SECRETO_XYZ")
    assert "TOKEN_SECRETO_XYZ" not in limpia
    assert "[REDACTED_TOKEN]" in limpia


def test_sanitizacion_lfpdppp_elimina_pii_denue():
    """Garantiza que campos personales (telefono, correo, calle) se descarten antes de Bronce."""
    crudo = {
        "Id": "999001",
        "Nombre": "FRUTERIA LA HUERTA",
        "Clase_actividad": "Comercio al por menor de frutas y verduras frescas",
        "Estrato": "0 a 5 personas",
        "Colonia": "CENTRO",
        "Latitud": "19.2433",
        "Longitud": "-103.7250",
        "Telefono": "3120000000",
        "Correo_e": "dueno@correo.mx",
        "Calle": "AV MADERO",
        "Num_Exterior": "123",
    }
    reg = sanitizar_registro_denue(
        crudo, PLAZAS_GEO[80], "frutas", "https://inegi.org.mx/.../[REDACTED_TOKEN]", "2026-11-20T00:00:00Z"
    )
    for prohibido in ["Telefono", "Correo_e", "Calle", "Num_Exterior", "telefono", "correo_e"]:
        assert prohibido not in reg
    assert reg["id_denue"] == "999001"


def test_puerta_geo_y_union_espacial_within():
    """Verifica rechazo de coordenadas fuera de Mexico y union espacial con GeoJSON."""
    df_pts = pd.DataFrame([
        {
            "id_denue": "1",
            "nombre_comercial": "A",
            "clase_actividad": "Comercio al por menor de frutas y verduras frescas",
            "giro_consulta": "frutas",
            "plaza_id": 80,
            "latitud": "19.2400",
            "longitud": "-103.7250",
        },
        {
            "id_denue": "2",
            "nombre_comercial": "B_FUERA",
            "clase_actividad": "Restaurantes",
            "giro_consulta": "restaurante",
            "plaza_id": 80,
            "latitud": "60.0000",
            "longitud": "10.0000",
        },
    ])
    validos, rechazados = filtrar_puerta_geoespacial(df_pts)
    assert len(validos) == 1
    assert len(rechazados) == 1
    assert rechazados.iloc[0]["motivo_rechazo"] == "coordenada_fuera_mexico"

    geojson_mock = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"cvegeo": "06002", "nom_agem": "Colima"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-103.80, 19.18],
                        [-103.65, 19.18],
                        [-103.65, 19.32],
                        [-103.80, 19.32],
                        [-103.80, 19.18],
                    ]],
                },
            }
        ],
    }
    joined = ejecutar_union_espacial(validos, geojson_mock)
    assert joined.iloc[0]["cvegeo_mun"] == "06002"
    assert joined.iloc[0]["nombre_municipio_geo"] == "Colima"

    enriq = clasificar_categoria_y_anillo(joined)
    assert enriq.iloc[0]["categoria_canastita"] == "Fruteria / Mercado"
    assert enriq.iloc[0]["distancia_central_abasto_km"] >= 0.0
    assert calcular_haversine_km(19.24, -103.72, 19.24, -103.72) == 0.0


def test_oro_linaje_y_geoespacial_completo():
    """Valida presencia de columnas _linaje_* y KPIs geoespaciales en Capa Oro real."""
    ruta_oro = RAIZ / "data" / "oro" / "canasta_occidente_oro.csv"
    ruta_linaje = RAIZ / "data" / "oro" / "linaje_oro.json"
    assert ruta_oro.exists()
    assert ruta_linaje.exists()

    df_oro = pd.read_csv(ruta_oro)
    for col in [
        "comercios_denue_radio",
        "cvegeo_sede",
        "_linaje_fuente_precios",
        "_linaje_fuente_macro",
        "_linaje_fuente_geo",
        "_linaje_fecha_captura_sniim",
        "_linaje_fecha_proceso_oro_utc",
        "_linaje_version_pipeline",
    ]:
        assert col in df_oro.columns
        assert int(df_oro[col].isna().sum()) == 0

    lin = json.loads(ruta_linaje.read_text(encoding="utf-8"))
    assert lin["esquema_linaje"] == "TDL-Canastita-Lineage-v2.0"
    assert len(lin["entradas_bronce_principales"]) >= 5


def test_evaluacion_iso_25010_25012_umbrales():
    """Ejecuta y valida el evaluador cuantitativo ISO/IEC 25010 y 25012."""
    seg = auditar_seguridad_y_portabilidad()
    mant = analizar_mantenibilidad_codigo()
    fiab = analizar_fiabilidad_bitacora()
    r10 = evaluar_iso_25010(seg, mant, fiab)
    r12 = evaluar_iso_25012(seg, fiab)
    md = generar_reporte_iso_markdown(r10, r12, seg)

    assert len(r10["caracteristicas"]) == 8
    assert r10["seguridad_hallazgos_secretos"] == 0
    assert r10["seguridad_hallazgos_pii"] == 0
    assert r10["portabilidad_rutas_locales"] == 0
    assert r12["completitud_obligatoria_pct"] >= 95.0
    assert r12["trazabilidad_pct"] == 100.0
    assert "ISO/IEC 9126" in md and "SQuaRE" in md


def test_punto_en_geometria_multipolygon_y_pipeline_geo():
    """Verifica motor ray-casting sobre MultiPolygon y flujo end-to-end geoespacial."""
    mp = {
        "type": "MultiPolygon",
        "coordinates": [[[[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 2.0], [0.0, 0.0]]]],
    }
    assert _punto_en_geometria(1.0, 1.0, mp) is True
    assert _punto_en_geometria(5.0, 5.0, mp) is False

    df_geo = procesar_capa_plata_geo()
    assert len(df_geo) > 0
    assert int(df_geo["cvegeo_mun"].isna().sum()) == 0


def test_auditor_tdl_repo_propio_y_vacio(tmp_path):
    """Valida que auditor_tdl apruebe el repositorio propio y detecte criticos en uno incompleto."""
    res_propio = auditar_repositorio(RAIZ)
    assert res_propio["conteos_severidad"]["CRITICO"] == 0
    assert res_propio["disponibilidad_medida_pct"] >= 95.0

    res_vacio = auditar_repositorio(tmp_path)
    assert res_vacio["conteos_severidad"]["CRITICO"] >= 3
    assert res_vacio["conteos_severidad"]["MAYOR"] >= 1
