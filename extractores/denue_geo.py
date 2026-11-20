"""
extractores/denue_geo.py
Proyecto Integrador - Trusted Data Lab (tdl-canastita-proyecto)
Autor: Adolfo Rodriguez (Data Engineer & ISO Lead)

Fuente 3 (Especializada Geoespacial - Entrega E2):
1. Consulta la API oficial del DENUE (INEGI) alrededor de las 3 plazas
   mayoristas (Colima, Guadalajara y Morelia) para localizar fruterias,
   tiendas de abarrotes y cocinas economicas/restaurantes.
2. Descarga los poligonos municipales oficiales del Marco Geoestadistico
   Nacional de INEGI (WSCatGeo) para union espacial.
3. Aplica sanitizacion LFPDPPP antes de escribir en Capa Bronce: elimina
   telefono, correo electronico, sitio web, domicilio exacto y redacta
   el token en los metadatos de trazabilidad.
"""

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from extractores.base import ExtractorEtico, UA, cargar_env

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
DIR_BRONZE_DENUE = RAIZ_PROYECTO / "data" / "bronce" / "denue_inegi"

# Campos personales o sensibles excluidos por cumplimiento LFPDPPP antes de Capa Bronce
CAMPOS_PII_EXCLUIDOS = [
    "Telefono",
    "Correo_e",
    "Sitio_internet",
    "Calle",
    "Num_Exterior",
    "Num_Interior",
    "Tipo_vialidad",
    "CP",
    "Razon_social",
]

# Plazas de abasto del observatorio: centro de busqueda urbano DENUE + coordenada real de Central de Abasto
PLAZAS_GEO = {
    80: {
        "plaza_id": 80,
        "ciudad_plaza": "Colima",
        "estado_plaza": "Colima",
        "nombre_central": "Central de Abasto de Colima",
        "lat_central": 19.2248,
        "lon_central": -103.7325,
        "lat_busqueda": 19.2433,
        "lon_busqueda": -103.7250,
        "radio_m": 4000,
    },
    140: {
        "plaza_id": 140,
        "ciudad_plaza": "Guadalajara",
        "estado_plaza": "Jalisco",
        "nombre_central": "Mercado de Abasto de Guadalajara",
        "lat_central": 20.6540,
        "lon_central": -103.3830,
        "lat_busqueda": 20.6767,
        "lon_busqueda": -103.3475,
        "radio_m": 2500,
    },
    160: {
        "plaza_id": 160,
        "ciudad_plaza": "Morelia",
        "estado_plaza": "Michoacan",
        "nombre_central": "Mercado de Abasto de Morelia",
        "lat_central": 19.7230,
        "lon_central": -101.1780,
        "lat_busqueda": 19.7060,
        "lon_busqueda": -101.1950,
        "radio_m": 2500,
    },
}

GIROS_CANASTITA = ["frutas", "abarrotes", "restaurante"]

MUNICIPIOS_MGEM = [
    ("06", "002", "Colima"),
    ("06", "010", "Villa de Alvarez"),
    ("14", "039", "Guadalajara"),
    ("16", "053", "Morelia"),
]


def calcular_sha256(ruta: Path) -> str:
    """Calcula el digest SHA-256 hexadecimal de un archivo en disco."""
    hasher = hashlib.sha256()
    hasher.update(ruta.read_bytes())
    return hasher.hexdigest()


def sanitizar_url_token(url: str, token: str) -> str:
    """Reemplaza cualquier ocurrencia del token en la URL por [REDACTED_TOKEN]."""
    if not token:
        return url
    return url.replace(token, "[REDACTED_TOKEN]")


def sanitizar_registro_denue(
    item: Dict[str, Any],
    plaza_meta: Dict[str, Any],
    giro_consulta: str,
    url_sanitizada: str,
    captura_ts: str,
) -> Dict[str, Any]:
    """
    Extrae unicamente atributos comerciales y geograficos publicos del DENUE,
    descartando campos de contacto o identificacion personal (LFPDPPP).
    """
    return {
        "id_denue": str(item.get("Id", "")).strip(),
        "nombre_comercial": str(item.get("Nombre", "")).strip(),
        "clase_actividad": str(item.get("Clase_actividad", "")).strip(),
        "giro_consulta": giro_consulta,
        "estrato_personal": str(item.get("Estrato", "")).strip(),
        "plaza_id": plaza_meta["plaza_id"],
        "ciudad_plaza": plaza_meta["ciudad_plaza"],
        "estado_plaza": plaza_meta["estado_plaza"],
        "colonia": str(item.get("Colonia", "")).strip(),
        "latitud": str(item.get("Latitud", "")).strip(),
        "longitud": str(item.get("Longitud", "")).strip(),
        "_fuente": "INEGI_DENUE_v1",
        "_url_origen": url_sanitizada,
        "_capturado_en_utc": captura_ts,
    }


def construir_url_denue(giro: str, lat: float, lon: float, radio: int, token: str) -> str:
    """Construye la URL de consulta DENUE v1 con precision fija de 6 decimales."""
    return (
        f"https://www.inegi.org.mx/app/api/denue/v1/consulta/"
        f"Buscar/{giro}/{lat:.6f},{lon:.6f}/{radio}/{token}"
    )


def extraer_denue_occidente(
    extractor: ExtractorEtico | None = None,
    token: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Consulta la API oficial del DENUE para los 3 giros en las 3 plazas
    y devuelve los registros sanitizados y deduplicados por id_denue.
    """
    cargar_env()
    tok = token or os.getenv("INEGI_TOKEN", "").strip()
    if not tok:
        raise RuntimeError(
            "Falta INEGI_TOKEN en .env o variables de entorno para consultar DENUE."
        )

    ext = extractor or ExtractorEtico(pausa=1.5)
    captura_ts = datetime.now(timezone.utc).isoformat()
    por_id: Dict[str, Dict[str, Any]] = {}

    for _, plaza_meta in PLAZAS_GEO.items():
        lat = plaza_meta.get("lat_busqueda", plaza_meta["lat_central"])
        lon = plaza_meta.get("lon_busqueda", plaza_meta["lon_central"])
        radio = plaza_meta["radio_m"]

        for giro in GIROS_CANASTITA:
            url = construir_url_denue(giro, lat, lon, radio, tok)
            url_limpia = sanitizar_url_token(url, tok)
            payload = None
            for intento in range(2):
                resp = ext.get(url)
                try:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        payload = data
                        break
                except ValueError:
                    pass
                if intento == 0:
                    import time
                    time.sleep(2.0)

            if not isinstance(payload, list):
                print(f"  [AVISO] Sin resultados para {plaza_meta['ciudad_plaza']} / {giro}")
                continue
            print(f"  DENUE {plaza_meta['ciudad_plaza']} / {giro}: {len(payload)} registros")

            for item in payload:
                if not isinstance(item, dict):
                    continue
                reg = sanitizar_registro_denue(
                    item, plaza_meta, giro, url_limpia, captura_ts
                )
                id_d = reg["id_denue"]
                if id_d and id_d not in por_id:
                    por_id[id_d] = reg

    return list(por_id.values())


def extraer_municipios_geojson(
    extractor: ExtractorEtico | None = None,
) -> Dict[str, Any]:
    """
    Descarga los limites municipales oficiales del Marco Geoestadistico
    Nacional de INEGI (WSCatGeo) para las 3 areas metropolitanas del proyecto.
    """
    ext = extractor or ExtractorEtico(pausa=1.5)
    features = []
    fuentes_urls = []

    for cve_ent, cve_mun, _ in MUNICIPIOS_MGEM:
        url = f"https://gaia.inegi.org.mx/wscatgeo/geo/mgem/{cve_ent}/{cve_mun}"
        fuentes_urls.append(url)
        resp = ext.get(url)
        data = resp.json()
        for feat in data.get("features", []):
            props = dict(feat.get("properties", {}))
            props["_url_origen"] = url
            features.append(
                {
                    "type": "Feature",
                    "properties": props,
                    "geometry": feat.get("geometry"),
                }
            )

    return {
        "type": "FeatureCollection",
        "name": "municipios_occidente_mgem",
        "metadata": {
            "crs_documentado": "EPSG:4326 (WGS84 / compatible con EPSG:6365 ITRF2008 origen INEGI)",
            "fuente": "INEGI Marco Geoestadistico (WSCatGeo)",
            "urls_origen": fuentes_urls,
            "capturado_en_utc": datetime.now(timezone.utc).isoformat(),
        },
        "features": features,
    }


def guardar_bronce_geoespacial(
    registros_denue: List[Dict[str, Any]],
    geojson_municipios: Dict[str, Any],
) -> Dict[str, Path]:
    """Guarda puntos DENUE y poligonos municipales en data/bronce/denue_inegi/ con SHA-256."""
    DIR_BRONZE_DENUE.mkdir(parents=True, exist_ok=True)
    if not registros_denue:
        raise ValueError("No se obtuvieron registros DENUE para guardar en Capa Bronce.")

    ruta_csv = DIR_BRONZE_DENUE / "denue_occidente_raw.csv"
    ruta_meta_csv = DIR_BRONZE_DENUE / "denue_occidente_raw.meta.json"
    columnas = list(registros_denue[0].keys())

    with ruta_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(registros_denue)

    meta_csv = {
        "nombre_archivo": ruta_csv.name,
        "descripcion": "Establecimientos DENUE-INEGI alrededor de centrales de abasto de Colima, Guadalajara y Morelia (sin PII)",
        "fuente": "INEGI DENUE API v1",
        "fecha_captura_utc": datetime.now(timezone.utc).isoformat(),
        "user_agent": UA,
        "total_registros": len(registros_denue),
        "plazas_incluidas": sorted({int(r["plaza_id"]) for r in registros_denue}),
        "giros_consultados": GIROS_CANASTITA,
        "campos_pii_excluidos_lfpdppp": CAMPOS_PII_EXCLUIDOS,
        "sha256_archivo": calcular_sha256(ruta_csv),
        "columnas": columnas,
    }
    ruta_meta_csv.write_text(
        json.dumps(meta_csv, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    ruta_geo = DIR_BRONZE_DENUE / "municipios_occidente.geojson"
    ruta_meta_geo = DIR_BRONZE_DENUE / "municipios_occidente.meta.json"
    ruta_geo.write_text(
        json.dumps(geojson_municipios, ensure_ascii=False), encoding="utf-8"
    )

    meta_geo = {
        "nombre_archivo": ruta_geo.name,
        "descripcion": "Poligonos municipales oficiales del Marco Geoestadistico Nacional INEGI (Colima, Villa de Alvarez, Guadalajara, Morelia)",
        "fuente": "INEGI Marco Geoestadistico WSCatGeo",
        "crs": "EPSG:4326",
        "fecha_captura_utc": datetime.now(timezone.utc).isoformat(),
        "total_poligonos": len(geojson_municipios.get("features", [])),
        "cvegeo_municipios": [
            f.get("properties", {}).get("cvegeo")
            for f in geojson_municipios.get("features", [])
        ],
        "sha256_archivo": calcular_sha256(ruta_geo),
    }
    ruta_meta_geo.write_text(
        json.dumps(meta_geo, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return {
        "denue_csv": ruta_csv,
        "denue_meta": ruta_meta_csv,
        "municipios_geojson": ruta_geo,
        "municipios_meta": ruta_meta_geo,
    }


def main() -> None:
    ext = ExtractorEtico(pausa=1.5)
    print("--- Descargando establecimientos DENUE-INEGI (sin PII) ---")
    registros = extraer_denue_occidente(extractor=ext)
    print(f"OK - DENUE deduplicado: {len(registros)} establecimientos")

    print("--- Descargando poligonos municipales Marco Geoestadistico INEGI ---")
    geojson = extraer_municipios_geojson(extractor=ext)
    print(f"OK - Marco Geoestadistico: {len(geojson['features'])} municipios")

    salidas = guardar_bronce_geoespacial(registros, geojson)
    for k, v in salidas.items():
        print(f"  Guardado {k}: {v.relative_to(RAIZ_PROYECTO)}")


if __name__ == "__main__":
    main()
