"""
pipeline/enriquecer_geo.py
Modulo de enriquecimiento geoespacial y union espacial (Capa Plata Geo - Entrega E2).
Autor: Adolfo Rodriguez (Data Engineer & ISO Lead)

1. Aplica Puerta 1 Geoespacial sobre datos crudos del DENUE (validacion de rango
   geografico en Mexico, unicidad y verificacion de cero PII).
2. Ejecuta union espacial (point-in-polygon / within) entre establecimientos
   y los poligonos municipales oficiales del Marco Geoestadistico INEGI usando
   GeoPandas (con respaldo geometrico puro Python ray-casting).
3. Calcula distancia Haversine a la Central de Abasto correspondiente y asigna
   anillo logistico y categoria comercial Canastita.
4. Exporta CSV, GeoJSON RFC 7946 y archivo .meta.json con SHA-256.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

try:
    import geopandas as gpd
    from shapely.geometry import Point

    TIENE_GEOPANDAS = True
except Exception:
    TIENE_GEOPANDAS = False

from extractores.denue_geo import PLAZAS_GEO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("enriquecer_geo")

DIR_BRONCE_GEO = RAIZ / "data" / "bronce" / "denue_inegi"
DIR_PLATA = RAIZ / "data" / "plata"
DIR_CUARENTENA = RAIZ / "data" / "cuarentena"

COLUMNAS_PII_PROHIBIDAS = {
    "telefono",
    "correo",
    "correo_e",
    "email",
    "sitio_internet",
    "calle",
    "num_exterior",
    "num_interior",
}


def calcular_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia ortodromica en kilometros entre dos pares (lat, lon)."""
    r_tierra_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return r_tierra_km * c


def _punto_en_anillo(lon: float, lat: float, anillo: List[List[float]]) -> bool:
    """Algoritmo ray-casting 2D para probar si (lon, lat) esta dentro de un anillo cerrado."""
    n = len(anillo)
    if n < 3:
        return False
    dentro = False
    j = n - 1
    for i in range(n):
        xi, yi = anillo[i][0], anillo[i][1]
        xj, yj = anillo[j][0], anillo[j][1]
        cruza_y = (yi > lat) != (yj > lat)
        if cruza_y:
            x_inter = (xj - xi) * (lat - yi) / ((yj - yi) if (yj - yi) != 0 else 1e-12) + xi
            if lon < x_inter:
                dentro = not dentro
        j = i
    return dentro


def _punto_en_geometria(lon: float, lat: float, geom: Dict[str, Any]) -> bool:
    """Evalua Polygon o MultiPolygon GeoJSON en coordenadas geograficas."""
    gtype = geom.get("type")
    coords = geom.get("coordinates", [])
    if gtype == "Polygon":
        poligonos = [coords]
    elif gtype == "MultiPolygon":
        poligonos = coords
    else:
        return False

    for poly in poligonos:
        if not poly:
            continue
        if _punto_en_anillo(lon, lat, poly[0]):
            en_hueco = any(_punto_en_anillo(lon, lat, hueco) for hueco in poly[1:])
            if not en_hueco:
                return True
    return False


def filtrar_puerta_geoespacial(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Puerta 1 Geoespacial:
    Verifica ausencia de columnas PII, coordenadas dentro de Mexico y unicidad id_denue.
    """
    cols_lower = {c.lower() for c in df.columns}
    cols_violadas = sorted(cols_lower.intersection(COLUMNAS_PII_PROHIBIDAS))
    if cols_violadas:
        raise ValueError(f"Violacion LFPDPPP: se detectaron columnas PII prohibidas: {cols_violadas}")

    df_t = df.copy()
    df_t["latitud"] = pd.to_numeric(df_t.get("latitud"), errors="coerce")
    df_t["longitud"] = pd.to_numeric(df_t.get("longitud"), errors="coerce")
    df_t["plaza_id"] = pd.to_numeric(df_t.get("plaza_id"), errors="coerce").fillna(0).astype(int)

    cond_id_invalido = df_t["id_denue"].isna() | (df_t["id_denue"].astype(str).str.strip() == "")
    cond_coord_nula = df_t["latitud"].isna() | df_t["longitud"].isna()
    cond_fuera_mexico = (
        (df_t["latitud"] < 14.0)
        | (df_t["latitud"] > 33.0)
        | (df_t["longitud"] < -118.0)
        | (df_t["longitud"] > -86.0)
    ) & (~cond_coord_nula)

    motivos = np.where(
        cond_id_invalido,
        "id_denue_nulo",
        np.where(
            cond_coord_nula,
            "coordenada_nula",
            np.where(cond_fuera_mexico, "coordenada_fuera_mexico", "valido"),
        ),
    )

    df_t["motivo_rechazo"] = motivos
    rechazados = df_t[df_t["motivo_rechazo"] != "valido"].copy()
    validos = df_t[df_t["motivo_rechazo"] == "valido"].drop(columns=["motivo_rechazo"]).copy()
    validos = validos.drop_duplicates(subset=["id_denue"], keep="first").reset_index(drop=True)

    if not rechazados.empty:
        rechazados["fecha_rechazo_utc"] = datetime.now(timezone.utc).isoformat()

    return validos, rechazados


def ejecutar_union_espacial(
    df_puntos: pd.DataFrame, geojson_municipios: Dict[str, Any]
) -> pd.DataFrame:
    """
    Asigna clave y nombre de municipio oficial (cvegeo_mun, nombre_municipio_geo)
    mediante union espacial point-in-polygon (GeoPandas sjoin o fallback ray-casting).
    """
    df_out = df_puntos.copy().reset_index(drop=True)
    features = geojson_municipios.get("features", [])

    if df_out.empty or not features:
        df_out["cvegeo_mun"] = None
        df_out["nombre_municipio_geo"] = None
        return df_out

    if TIENE_GEOPANDAS:
        try:
            gdf_muns = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
            cols_mun = ["geometry"]
            if "cvegeo" in gdf_muns.columns:
                cols_mun.append("cvegeo")
            if "nom_agem" in gdf_muns.columns:
                cols_mun.append("nom_agem")

            geoms_pts = [Point(lon, lat) for lon, lat in zip(df_out["longitud"], df_out["latitud"])]
            gdf_pts = gpd.GeoDataFrame(df_out[["id_denue"]], geometry=geoms_pts, crs="EPSG:4326")
            joined = gpd.sjoin(gdf_pts, gdf_muns[cols_mun], how="left", predicate="within")
            joined = joined[~joined.index.duplicated(keep="first")].sort_index()

            df_out["cvegeo_mun"] = joined["cvegeo"].values if "cvegeo" in joined.columns else None
            df_out["nombre_municipio_geo"] = joined["nom_agem"].values if "nom_agem" in joined.columns else None
            return df_out
        except Exception as e:
            logger.warning("GeoPandas fallback activado por excepcion (%s). Usando ray-casting.", e)

    # Respaldo puro en Python sobre GeoJSON
    cves: List[Optional[str]] = []
    nombres: List[Optional[str]] = []
    for lon, lat in zip(df_out["longitud"], df_out["latitud"]):
        cve_match = None
        nom_match = None
        for feat in features:
            if _punto_en_geometria(float(lon), float(lat), feat.get("geometry", {})):
                props = feat.get("properties", {})
                cve_match = props.get("cvegeo")
                nom_match = props.get("nom_agem")
                break
        cves.append(cve_match)
        nombres.append(nom_match)

    df_out["cvegeo_mun"] = cves
    df_out["nombre_municipio_geo"] = nombres
    return df_out


def clasificar_categoria_y_anillo(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula distancia a Central de Abasto, anillo logistico y categoria Canastita."""
    df_out = df.copy()

    distancias = []
    for plaza_id, lat, lon in zip(df_out["plaza_id"], df_out["latitud"], df_out["longitud"]):
        meta = PLAZAS_GEO.get(int(plaza_id))
        if meta:
            d = calcular_haversine_km(float(lat), float(lon), meta["lat_central"], meta["lon_central"])
            distancias.append(round(d, 3))
        else:
            distancias.append(np.nan)
    df_out["distancia_central_abasto_km"] = distancias

    df_out["anillo_logistico"] = np.where(
        df_out["distancia_central_abasto_km"] < 2.0,
        "< 2 km (Zona nucleo)",
        np.where(
            df_out["distancia_central_abasto_km"] <= 4.0,
            "2 - 4 km (Anillo intermedio)",
            "> 4 km (Periferia)",
        ),
    )

    clase_lower = df_out["clase_actividad"].astype(str).str.lower()
    giro_lower = df_out["giro_consulta"].astype(str).str.lower()

    es_fruteria = clase_lower.str.contains("frutas y verduras", na=False) | giro_lower.isin(["fruteria", "frutas"])
    es_abarrotes = clase_lower.str.contains("abarrotes", na=False) | (giro_lower == "abarrotes")

    df_out["categoria_canastita"] = np.where(
        es_fruteria,
        "Fruteria / Mercado",
        np.where(
            es_abarrotes,
            "Abarrotes / Miscelanea",
            "Cocina economica / Restaurante",
        ),
    )
    return df_out


def exportar_geojson_puntos(df_geo: pd.DataFrame, ruta_salida: Path) -> None:
    """Serializa el DataFrame geoespacial como FeatureCollection RFC 7946."""
    features = []
    cols_props = [c for c in df_geo.columns if c not in ("latitud", "longitud")]
    for _, row in df_geo.iterrows():
        props = {}
        for col in cols_props:
            val = row[col]
            if pd.isna(val):
                props[col] = None
            elif isinstance(val, (np.integer, int)):
                props[col] = int(val)
            elif isinstance(val, (np.floating, float)):
                props[col] = float(val)
            else:
                props[col] = str(val)
        features.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["longitud"]), float(row["latitud"])],
                },
            }
        )

    fc = {
        "type": "FeatureCollection",
        "name": "denue_occidente_geo",
        "features": features,
    }
    ruta_salida.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")


def procesar_capa_plata_geo() -> pd.DataFrame:
    """Orquestador principal de Capa Bronce Geo -> Capa Plata Geo."""
    DIR_PLATA.mkdir(parents=True, exist_ok=True)
    DIR_CUARENTENA.mkdir(parents=True, exist_ok=True)

    ruta_raw = DIR_BRONCE_GEO / "denue_occidente_raw.csv"
    ruta_muns = DIR_BRONCE_GEO / "municipios_occidente.geojson"

    if not ruta_raw.exists() or not ruta_muns.exists():
        raise FileNotFoundError(
            "No se encontraron los artefactos de Bronce DENUE. Ejecuta `python -m extractores.denue_geo`."
        )

    df_raw = pd.read_csv(ruta_raw, dtype=str)
    geojson_muns = json.loads(ruta_muns.read_text(encoding="utf-8"))

    df_validos, df_rechazados = filtrar_puerta_geoespacial(df_raw)
    if not df_rechazados.empty:
        df_rechazados.to_csv(DIR_CUARENTENA / "rechazos_geo.csv", index=False, encoding="utf-8")
        logger.warning("Puerta 1 Geo envio %d registros a cuarentena.", len(df_rechazados))

    df_joined = ejecutar_union_espacial(df_validos, geojson_muns)
    df_geo = clasificar_categoria_y_anillo(df_joined)

    ruta_csv = DIR_PLATA / "denue_occidente_geo.csv"
    ruta_geojson = DIR_PLATA / "denue_occidente_geo.geojson"
    ruta_meta = DIR_PLATA / "denue_occidente_geo.meta.json"

    df_geo.to_csv(ruta_csv, index=False, encoding="utf-8")
    exportar_geojson_puntos(df_geo, ruta_geojson)

    sha_csv = hashlib.sha256(ruta_csv.read_bytes()).hexdigest()
    sha_geojson = hashlib.sha256(ruta_geojson.read_bytes()).hexdigest()
    emparejados = int(df_geo["cvegeo_mun"].notna().sum())

    meta = {
        "capa": "Plata Geoespacial",
        "descripcion": "Comercios DENUE integrados mediante union espacial con poligonos municipales INEGI",
        "fecha_procesamiento_utc": datetime.now(timezone.utc).isoformat(),
        "motor_union_espacial": "geopandas_shapely" if TIENE_GEOPANDAS else "python_raycasting",
        "crs": "EPSG:4326",
        "total_establecimientos": len(df_geo),
        "rechazados_cuarentena": len(df_rechazados),
        "emparejados_dentro_poligono": emparejados,
        "tasa_emparejamiento_pct": round((emparejados / len(df_geo)) * 100.0, 2) if len(df_geo) else 0.0,
        "conteo_por_plaza": {str(k): int(v) for k, v in df_geo["ciudad_plaza"].value_counts().to_dict().items()},
        "conteo_por_categoria": {str(k): int(v) for k, v in df_geo["categoria_canastita"].value_counts().to_dict().items()},
        "sha256_csv": sha_csv,
        "sha256_geojson": sha_geojson,
    }
    ruta_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(
        "Capa Plata Geo generada: %d comercios (%d dentro de poligono municipal).",
        len(df_geo),
        emparejados,
    )
    return df_geo


if __name__ == "__main__":
    procesar_capa_plata_geo()
