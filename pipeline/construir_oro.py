"""
pipeline/construir_oro.py
Módulo de la Capa Oro (Medallion Architecture) para TDL Canastita.
Agrega mensualmente los precios de Capa Plata, integra indicadores macroeconómicos
de Banxico (Tipo de cambio FIX e INPC) y calcula métricas financieras de variación
intermensual (MoM), anual (YoY), spreads y precios convertidos a dólares.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("oro")

DIR_BRONCE = RAIZ / "data" / "bronce"
DIR_PLATA = RAIZ / "data" / "plata"
DIR_ORO = RAIZ / "data" / "oro"


def agregar_mensual_sniim(df_plata: pd.DataFrame) -> pd.DataFrame:
    """Agrega precios diarios a frecuencia mensual por plaza y producto."""
    cols_grupo = ["anio_mes", "plaza_id", "ciudad", "nombre_plaza", "producto"]
    # Asegurar que existan las columnas requeridas
    cols_validas = [c for c in cols_grupo if c in df_plata.columns]

    agregados = (
        df_plata.groupby(cols_validas)
        .agg(
            precio_promedio_mxn=("precio_frecuente_mxn", "mean"),
            precio_limpio_promedio_mxn=("precio_frecuente_limpio", "mean"),
            precio_mediana_mxn=("precio_frecuente_mxn", "median"),
            precio_min_mes=("precio_min_mxn", "min"),
            precio_max_mes=("precio_max_mxn", "max"),
            volatilidad_precio_std=("precio_frecuente_mxn", "std"),
            num_observaciones=("precio_frecuente_mxn", "count"),
            conteo_atipicos_iqr=("es_atipico_iqr", "sum"),
        )
        .reset_index()
    )

    agregados["volatilidad_precio_std"] = agregados["volatilidad_precio_std"].fillna(0.0)
    agregados["spread_mensual_mxn"] = agregados["precio_max_mes"] - agregados["precio_min_mes"]
    agregados["spread_pct"] = (
        (agregados["spread_mensual_mxn"] / agregados["precio_promedio_mxn"]) * 100.0
    ).round(2)

    if "_capturado_en_utc" in df_plata.columns:
        cap_max = (
            df_plata.groupby(cols_validas)["_capturado_en_utc"]
            .max()
            .reset_index()
            .rename(columns={"_capturado_en_utc": "_linaje_fecha_captura_sniim"})
        )
        agregados = agregados.merge(cap_max, on=cols_validas, how="left")

    return agregados


def integrar_macro_oro(
    df_sniim_mensual: pd.DataFrame, df_fx: pd.DataFrame, df_inpc: pd.DataFrame
) -> pd.DataFrame:
    """
    Realiza el join analítico entre los precios mensuales de SNIIM y los
    indicadores macroeconómicos de Banxico (Tipo de cambio FIX e Inflación INPC).
    """
    df_out = df_sniim_mensual.copy()

    # 1. Procesar Tipo de Cambio FIX mensual promedio
    df_fx_copy = df_fx.copy()
    if "tipo_cambio_fix" in df_fx_copy.columns:
        df_fx_copy["tipo_cambio_fix"] = pd.to_numeric(df_fx_copy["tipo_cambio_fix"], errors="coerce")
        fx_mensual = (
            df_fx_copy.groupby("anio_mes")["tipo_cambio_fix"]
            .mean()
            .reset_index()
            .rename(columns={"tipo_cambio_fix": "tipo_cambio_fix_promedio"})
        )
        df_out = df_out.merge(fx_mensual, on="anio_mes", how="left")
    else:
        df_out["tipo_cambio_fix_promedio"] = np.nan

    # 2. Procesar INPC
    df_inpc_copy = df_inpc.copy()
    if "valor" in df_inpc_copy.columns:
        df_inpc_copy["valor"] = pd.to_numeric(df_inpc_copy["valor"], errors="coerce")
        inpc_mensual = df_inpc_copy[["anio_mes", "valor"]].drop_duplicates(subset=["anio_mes"]).rename(
            columns={"valor": "inpc_mensual"}
        )
        df_out = df_out.merge(inpc_mensual, on="anio_mes", how="left")
    else:
        df_out["inpc_mensual"] = np.nan

    # Imputar si hay algún mes reciente que Banxico aún no publica (usar forward-fill por serie temporal)
    df_out["tipo_cambio_fix_promedio"] = df_out["tipo_cambio_fix_promedio"].ffill().bfill()
    df_out["inpc_mensual"] = df_out["inpc_mensual"].ffill().bfill()

    # 3. Calcular precio en USD
    df_out["precio_usd"] = (
        df_out["precio_promedio_mxn"] / df_out["tipo_cambio_fix_promedio"]
    ).round(4)

    return df_out


def calcular_metricas_oro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula variaciones mensuales (MoM), anuales (YoY), inflación y medias móviles.
    """
    df_out = df.sort_values(by=["plaza_id", "producto", "anio_mes"]).reset_index(drop=True)

    # Variación MoM y YoY de precios por serie (plaza, producto)
    grupos = df_out.groupby(["plaza_id", "producto"])

    df_out["variacion_mom_pct"] = (
        grupos["precio_promedio_mxn"].pct_change(1) * 100.0
    ).round(2)
    df_out["variacion_yoy_pct"] = (
        grupos["precio_promedio_mxn"].pct_change(12) * 100.0
    ).round(2)
    df_out["media_movil_3m"] = (
        grupos["precio_promedio_mxn"].rolling(3, min_periods=1).mean().round(2)
    ).values

    # Inflación mensual a partir del INPC
    # El INPC es nacional, así que calculamos la inflación mensual del INPC mapeada por mes
    inpc_tabla = (
        df_out[["anio_mes", "inpc_mensual"]]
        .drop_duplicates()
        .sort_values("anio_mes")
        .reset_index(drop=True)
    )
    inpc_tabla["inflacion_mensual_pct"] = (
        inpc_tabla["inpc_mensual"].pct_change(1) * 100.0
    ).round(2)

    df_out = df_out.merge(
        inpc_tabla[["anio_mes", "inflacion_mensual_pct"]], on="anio_mes", how="left"
    )

    # Redondeos cosméticos para presentación ejecutiva
    cols_redondeo_2 = [
        "precio_promedio_mxn",
        "precio_limpio_promedio_mxn",
        "precio_mediana_mxn",
        "volatilidad_precio_std",
    ]
    for c in cols_redondeo_2:
        if c in df_out.columns:
            df_out[c] = df_out[c].round(2)

    if "tipo_cambio_fix_promedio" in df_out.columns:
        df_out["tipo_cambio_fix_promedio"] = df_out["tipo_cambio_fix_promedio"].round(4)
    if "inpc_mensual" in df_out.columns:
        df_out["inpc_mensual"] = df_out["inpc_mensual"].round(3)

    return df_out


def integrar_geoespacial_oro(
    df_oro: pd.DataFrame, df_geo: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Cruza la Capa Oro mensual con el resumen por plaza de la fuente especializada
    DENUE-INEGI + Marco Geoestadistico (Capa Plata Geoespacial).
    """
    df_out = df_oro.copy()

    if df_geo is None:
        ruta_geo = DIR_PLATA / "denue_occidente_geo.csv"
        if not ruta_geo.exists():
            return df_out
        df_geo = pd.read_csv(ruta_geo)

    if df_geo.empty or "plaza_id" not in df_geo.columns:
        return df_out

    df_g = df_geo.copy()
    df_g["plaza_id"] = pd.to_numeric(df_g["plaza_id"], errors="coerce").fillna(0).astype(int)
    df_g["es_fruteria"] = (df_g.get("categoria_canastita", "") == "Fruteria / Mercado").astype(int)
    df_g["es_cocina"] = (df_g.get("categoria_canastita", "") == "Cocina economica / Restaurante").astype(int)
    df_g["es_abarrotes"] = (df_g.get("categoria_canastita", "") == "Abarrotes / Miscelanea").astype(int)

    def _moda_cvegeo(serie: pd.Series) -> Optional[str]:
        limpia = serie.dropna().astype(str)
        if limpia.empty:
            return None
        return str(limpia.mode().iloc[0])

    resumen_geo = (
        df_g.groupby("plaza_id")
        .agg(
            comercios_denue_radio=("id_denue", "count"),
            fruterias_mercados_cercanos=("es_fruteria", "sum"),
            cocinas_restaurantes_cercanos=("es_cocina", "sum"),
            abarrotes_cercanos=("es_abarrotes", "sum"),
            distancia_media_abasto_km=("distancia_central_abasto_km", "mean"),
            cvegeo_sede=("cvegeo_mun", _moda_cvegeo),
        )
        .reset_index()
    )
    resumen_geo["distancia_media_abasto_km"] = resumen_geo["distancia_media_abasto_km"].round(3)

    cols_existentes = [c for c in resumen_geo.columns if c != "plaza_id" and c in df_out.columns]
    if cols_existentes:
        df_out = df_out.drop(columns=cols_existentes)

    df_out["plaza_id"] = pd.to_numeric(df_out["plaza_id"], errors="coerce").fillna(0).astype(int)
    df_out = df_out.merge(resumen_geo, on="plaza_id", how="left")
    return df_out


def agregar_linaje_oro(
    df_oro: pd.DataFrame, fecha_proceso_utc: Optional[str] = None
) -> pd.DataFrame:
    """
    Agrega columnas explicitas de linaje a nivel registro para garantizar
    trazabilidad hasta la fuente de origen y su fecha de captura (Entrega E2).
    """
    df_out = df_oro.copy()
    ts_proceso = fecha_proceso_utc or datetime.now(timezone.utc).isoformat()

    df_out["_linaje_fuente_precios"] = "SNIIM_SE"
    df_out["_linaje_fuente_macro"] = "BANXICO_SIE_SF43718_SP1"
    df_out["_linaje_fuente_geo"] = (
        "INEGI_DENUE_v1_MGEM" if "comercios_denue_radio" in df_out.columns else "NO_INTEGRADA"
    )
    if "_linaje_fecha_captura_sniim" not in df_out.columns:
        df_out["_linaje_fecha_captura_sniim"] = ts_proceso
    else:
        df_out["_linaje_fecha_captura_sniim"] = df_out["_linaje_fecha_captura_sniim"].fillna(ts_proceso)

    df_out["_linaje_fecha_proceso_oro_utc"] = ts_proceso
    df_out["_linaje_version_pipeline"] = "2.0-E2"
    return df_out


def construir_manifiesto_linaje(
    df_oro: pd.DataFrame,
    sha_oro: str,
    fecha_proceso_utc: str,
) -> Dict[str, Any]:
    """Construye el grafo completo de linaje Bronce -> Plata -> Oro con SHA-256."""
    def _info_archivo(ruta: Path, ruta_meta: Optional[Path] = None) -> Dict[str, Any]:
        if not ruta.exists():
            return {"ruta": str(ruta.relative_to(RAIZ)), "existe": False}
        info: Dict[str, Any] = {
            "ruta": str(ruta.relative_to(RAIZ)).replace("\\", "/"),
            "existe": True,
            "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest(),
            "tamano_bytes": ruta.stat().st_size,
        }
        if ruta_meta and ruta_meta.exists():
            try:
                m = json.loads(ruta_meta.read_text(encoding="utf-8"))
                if "fecha_captura_utc" in m:
                    info["fecha_captura_utc"] = m["fecha_captura_utc"]
                elif "fecha_procesamiento_utc" in m:
                    info["fecha_procesamiento_utc"] = m["fecha_procesamiento_utc"]
            except Exception:
                pass
        return info

    lotes_diarios_sniim = sorted((DIR_BRONCE / "sniim_canasta").glob("fecha=*/*.csv"))
    ult_diario = lotes_diarios_sniim[-1] if lotes_diarios_sniim else None

    fuentes_bronce = [
        _info_archivo(
            DIR_BRONCE / "sniim_canasta" / "historico" / "sniim_occidente_historico_2022_2026.csv",
            DIR_BRONCE / "sniim_canasta" / "historico" / "sniim_occidente_historico_2022_2026.meta.json",
        ),
        _info_archivo(
            DIR_BRONCE / "macro_api" / "tipo_cambio" / "usd_mxn_historico_2022_2026.csv",
            DIR_BRONCE / "macro_api" / "tipo_cambio" / "usd_mxn_historico_2022_2026.meta.json",
        ),
        _info_archivo(
            DIR_BRONCE / "macro_api" / "inflacion" / "inpc_inflacion_mexico_historico.csv",
            DIR_BRONCE / "macro_api" / "inflacion" / "inpc_inflacion_mexico_historico.meta.json",
        ),
        _info_archivo(
            DIR_BRONCE / "denue_inegi" / "denue_occidente_raw.csv",
            DIR_BRONCE / "denue_inegi" / "denue_occidente_raw.meta.json",
        ),
        _info_archivo(
            DIR_BRONCE / "denue_inegi" / "municipios_occidente.geojson",
            DIR_BRONCE / "denue_inegi" / "municipios_occidente.meta.json",
        ),
    ]
    if ult_diario:
        fuentes_bronce.append(
            _info_archivo(ult_diario, ult_diario.with_suffix(".meta.json"))
        )

    capas_plata = [
        _info_archivo(
            DIR_PLATA / "canasta_occidente_plata.csv",
            DIR_PLATA / "canasta_occidente_plata.meta.json",
        ),
        _info_archivo(
            DIR_PLATA / "denue_occidente_geo.csv",
            DIR_PLATA / "denue_occidente_geo.meta.json",
        ),
    ]

    return {
        "esquema_linaje": "TDL-Canastita-Lineage-v2.0",
        "fecha_generacion_utc": fecha_proceso_utc,
        "destino_oro": {
            "ruta": "data/oro/canasta_occidente_oro.csv",
            "registros": len(df_oro),
            "sha256_artefacto_primario": sha_oro,
            "columnas_linaje_fila": [c for c in df_oro.columns if c.startswith("_linaje_")],
        },
        "grafo_transformacion": [
            {
                "etapa": "Bronce -> Plata (Precios SNIIM)",
                "script": "pipeline/limpieza_plata.py",
                "reglas": [
                    "Normalizacion regional de productos y plazas",
                    "Puerta 1 de calidad hacia data/cuarentena/rechazos_plata.csv",
                    "Deduplicacion por (fecha_iso, plaza_id, producto, origen, calidad)",
                    "Deteccion y acotamiento IQR por (producto, plaza_id)",
                ],
            },
            {
                "etapa": "Bronce -> Plata Geo (DENUE + Marco Geoestadistico)",
                "script": "pipeline/enriquecer_geo.py",
                "reglas": [
                    "Puerta 1 geoespacial: cero PII (LFPDPPP) y limites geograficos de Mexico",
                    "Union espacial point-in-polygon (EPSG:4326) con municipios INEGI",
                    "Calculo de distancia Haversine a Central de Abasto y anillos logisticos",
                ],
            },
            {
                "etapa": "Plata + Macro Banxico + Plata Geo -> Capa Oro",
                "script": "pipeline/construir_oro.py",
                "reglas": [
                    "Agregacion mensual por (anio_mes, plaza_id, producto)",
                    "Join analitico izquierdo con Banxico FIX (SF43718) e INPC (SP1)",
                    "Calculo de variaciones MoM%, YoY%, precio_usd, media movil 3M y spread",
                    "Join izquierdo con agregados comerciales geoespaciales por plaza_id",
                    "Inyeccion de trazabilidad _linaje_* por fila",
                ],
            },
        ],
        "entradas_bronce_principales": fuentes_bronce,
        "capturas_diarias_sniim_totales": len(lotes_diarios_sniim),
        "capas_plata_intermedias": capas_plata,
    }


def procesar_capa_oro() -> pd.DataFrame:
    """
    Función orquestadora principal de Capa Plata a Capa Oro:
    1. Carga Capa Plata (o la construye si no existe).
    2. Carga datos macro de Capa Bronce (FIX e INPC).
    3. Agrega SNIIM a frecuencia mensual.
    4. Realiza el join con macroeconomía.
    5. Calcula métricas derivadas (MoM, YoY, USD, Spreads).
    6. Exporta a Parquet y CSV en data/oro/ con metadatos SHA-256.
    """
    DIR_ORO.mkdir(parents=True, exist_ok=True)

    ruta_plata_parquet = DIR_PLATA / "canasta_occidente_plata.parquet"
    ruta_plata_csv = DIR_PLATA / "canasta_occidente_plata.csv"

    df_plata = None
    if ruta_plata_parquet.exists():
        try:
            df_plata = pd.read_parquet(ruta_plata_parquet)
        except Exception:
            df_plata = None

    if df_plata is None:
        if ruta_plata_csv.exists():
            df_plata = pd.read_csv(ruta_plata_csv)
        else:
            logger.info("Capa Plata no encontrada en disco. Ejecutando pipeline de Plata...")
            from pipeline.limpieza_plata import procesar_capa_plata
            df_plata = procesar_capa_plata()

    logger.info("Capa Plata cargada con %d observaciones.", len(df_plata))

    # Cargar fuentes macro
    ruta_fx = DIR_BRONCE / "macro_api" / "tipo_cambio" / "usd_mxn_historico_2022_2026.csv"
    ruta_inpc = DIR_BRONCE / "macro_api" / "inflacion" / "inpc_inflacion_mexico_historico.csv"

    if not ruta_fx.exists() or not ruta_inpc.exists():
        raise FileNotFoundError("No se encontraron los archivos macro de Banxico en Capa Bronce.")

    df_fx = pd.read_csv(ruta_fx)
    df_inpc = pd.read_csv(ruta_inpc)

    # 1. Agregación mensual
    df_mensual = agregar_mensual_sniim(df_plata)
    logger.info("Agregación mensual calculada: %d registros producto-plaza-mes.", len(df_mensual))

    # 2. Integración macro
    df_integrado = integrar_macro_oro(df_mensual, df_fx, df_inpc)

    # 3. Métricas derivadas
    df_oro = calcular_metricas_oro(df_integrado)

    # 3b. Integracion geoespacial DENUE + Linaje E2
    fecha_proceso_utc = datetime.now(timezone.utc).isoformat()
    df_oro = integrar_geoespacial_oro(df_oro)
    df_oro = agregar_linaje_oro(df_oro, fecha_proceso_utc=fecha_proceso_utc)

    # 4. Guardar artefactos Oro (CSV siempre garantizado, Parquet con fallback)
    ruta_parquet = DIR_ORO / "canasta_occidente_oro.parquet"
    ruta_csv = DIR_ORO / "canasta_occidente_oro.csv"
    ruta_meta = DIR_ORO / "canasta_occidente_oro.meta.json"
    ruta_linaje = DIR_ORO / "linaje_oro.json"

    df_oro.to_csv(ruta_csv, index=False, encoding="utf-8")

    parquet_guardado = False
    try:
        df_oro.to_parquet(ruta_parquet, index=False)
        parquet_guardado = True
    except Exception as e:
        logger.warning("No se pudo generar Parquet Oro localmente (%s). Se garantiza CSV.", e)

    # Hash SHA-256 sobre el artefacto CSV principal rastreado
    hasher = hashlib.sha256()
    hasher.update(ruta_csv.read_bytes())
    sha_csv = hasher.hexdigest()

    archivo_para_hash = ruta_parquet if parquet_guardado else ruta_csv
    sha_archivo = hashlib.sha256(archivo_para_hash.read_bytes()).hexdigest()

    manifiesto_linaje = construir_manifiesto_linaje(df_oro, sha_csv, fecha_proceso_utc)
    ruta_linaje.write_text(
        json.dumps(manifiesto_linaje, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    meta = {
        "capa": "Oro",
        "descripcion": "Tabla analítica dimensional mensual integrada con precios mayoristas SNIIM, indicadores macro Banxico y densidad comercial geoespacial DENUE-INEGI",
        "fecha_procesamiento_utc": fecha_proceso_utc,
        "total_registros_mensuales": len(df_oro),
        "total_meses_unicos": int(df_oro["anio_mes"].nunique()),
        "rango_periodos": {
            "min": str(df_oro["anio_mes"].min()),
            "max": str(df_oro["anio_mes"].max()),
        },
        "plazas": df_oro["ciudad"].unique().tolist(),
        "productos": df_oro["producto"].unique().tolist(),
        "fuente_geoespacial_integrada": "comercios_denue_radio" in df_oro.columns,
        "archivo_linaje": "data/oro/linaje_oro.json",
        "sha256_csv": sha_csv,
        "sha256_artefacto": sha_archivo,
        "formato_primario": "parquet" if parquet_guardado else "csv",
        "archivos_salida": {
            "parquet": str(ruta_parquet.relative_to(RAIZ)).replace("\\", "/") if parquet_guardado else None,
            "csv": str(ruta_csv.relative_to(RAIZ)).replace("\\", "/"),
            "linaje": "data/oro/linaje_oro.json",
        },
    }

    with open(ruta_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info("Capa Oro generada exitosamente: %d registros guardados en %s", len(df_oro), ruta_parquet)
    return df_oro


if __name__ == "__main__":
    procesar_capa_oro()
