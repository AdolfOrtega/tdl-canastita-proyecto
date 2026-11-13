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
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("oro")

RAIZ = Path(__file__).resolve().parent.parent
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

    # 4. Guardar artefactos Oro (CSV siempre garantizado, Parquet con fallback)
    ruta_parquet = DIR_ORO / "canasta_occidente_oro.parquet"
    ruta_csv = DIR_ORO / "canasta_occidente_oro.csv"
    ruta_meta = DIR_ORO / "canasta_occidente_oro.meta.json"

    df_oro.to_csv(ruta_csv, index=False, encoding="utf-8")

    parquet_guardado = False
    try:
        df_oro.to_parquet(ruta_parquet, index=False)
        parquet_guardado = True
    except Exception as e:
        logger.warning("No se pudo generar Parquet Oro localmente (%s). Se garantiza CSV.", e)

    # Hash SHA-256
    hasher = hashlib.sha256()
    archivo_para_hash = ruta_parquet if parquet_guardado else ruta_csv
    hasher.update(archivo_para_hash.read_bytes())
    sha_archivo = hasher.hexdigest()

    meta = {
        "capa": "Oro",
        "descripcion": "Tabla analítica dimensional mensual integrada con precios mayoristas SNIIM e indicadores macro Banxico",
        "fecha_procesamiento_utc": datetime.now(timezone.utc).isoformat(),
        "total_registros_mensuales": len(df_oro),
        "total_meses_unicos": int(df_oro["anio_mes"].nunique()),
        "rango_periodos": {
            "min": str(df_oro["anio_mes"].min()),
            "max": str(df_oro["anio_mes"].max()),
        },
        "plazas": df_oro["ciudad"].unique().tolist(),
        "productos": df_oro["producto"].unique().tolist(),
        "sha256_artefacto": sha_archivo,
        "formato_primario": "parquet" if parquet_guardado else "csv",
        "archivos_salida": {
            "parquet": str(ruta_parquet.relative_to(RAIZ)) if parquet_guardado else None,
            "csv": str(ruta_csv.relative_to(RAIZ)),
        },
    }

    with open(ruta_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info("Capa Oro generada exitosamente: %d registros guardados en %s", len(df_oro), ruta_parquet)
    return df_oro


if __name__ == "__main__":
    procesar_capa_oro()
