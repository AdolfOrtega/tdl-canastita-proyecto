"""
pipeline/limpieza_plata.py
Módulo de la Capa Plata (Medallion Architecture) para TDL Canastita.
Transforma datos crudos de Capa Bronce (SNIIM) aplicando Puerta 1 de calidad,
resolución de entidades, deduplicación, cuarentena de datos corruptos y
detección de atípicos con el método IQR.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
from typing import Tuple
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("plata")

RAIZ = Path(__file__).resolve().parent.parent
DIR_BRONCE = RAIZ / "data" / "bronce"
DIR_PLATA = RAIZ / "data" / "plata"
DIR_CUARENTENA = RAIZ / "data" / "cuarentena"

# Homologación de entidades a estándar regional de Occidente (Colima, GDL, Morelia)
MAPEO_PRODUCTOS = {
    "Tomate Saladette": "Jitomate Saladette",
    "Jitomate Saladette": "Jitomate Saladette",
    "Limon c/semilla # 5": "Limon con semilla #5",
    "Limon con semilla #5": "Limon con semilla #5",
    "Limón c/semilla # 5": "Limon con semilla #5",
    "LimÃ³n c/semilla # 5": "Limon con semilla #5",
    "Aguacate Hass": "Aguacate Hass",
    "Cebolla Bola": "Cebolla Bola",
    "Chile Serrano": "Chile Serrano",
    "Papa Alpha": "Papa Alpha",
}

MAPEO_PLAZAS = {
    80: {"ciudad": "Colima", "nombre_plaza": "Colima: Centros de distribucion de Colima"},
    140: {"ciudad": "Guadalajara", "nombre_plaza": "Jalisco: Mercado de Abasto de Guadalajara"},
    160: {"ciudad": "Morelia", "nombre_plaza": "Michoacan: Mercado de Abasto de Morelia"},
}


def normalizar_productos_y_plazas(df: pd.DataFrame) -> pd.DataFrame:
    """Homologa nombres de productos y ciudades para evitar inconsistencias."""
    df_out = df.copy()
    if "producto" in df_out.columns:
        df_out["producto"] = df_out["producto"].astype(str).str.strip()
        df_out["producto"] = df_out["producto"].replace(MAPEO_PRODUCTOS)

    if "plaza_id" in df_out.columns:
        df_out["plaza_id"] = pd.to_numeric(df_out["plaza_id"], errors="coerce").fillna(0).astype(int)
        for pid, meta in MAPEO_PLAZAS.items():
            mask = df_out["plaza_id"] == pid
            df_out.loc[mask, "ciudad"] = meta["ciudad"]
            df_out.loc[mask, "nombre_plaza"] = meta["nombre_plaza"]

    return df_out


def filtrar_y_cuarentenar(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Puerta 1 de Calidad:
    Separa registros válidos de registros corruptos o inconsistentes.
    Los registros rechazados se devuelven para almacenamiento en cuarentena.
    """
    df_trabajo = df.copy()
    motivos_rechazo = []

    # Validar fechas
    fechas_dt = pd.to_datetime(
        df_trabajo["fecha_observacion_raw"], format="%d/%m/%Y", errors="coerce"
    )
    # Si viene en formato ISO YYYY-MM-DD
    fechas_iso = pd.to_datetime(df_trabajo["fecha_observacion_raw"], format="%Y-%m-%d", errors="coerce")
    fechas_dt = fechas_dt.combine_first(fechas_iso)

    df_trabajo["fecha"] = fechas_dt

    # Coerción numérica de precios
    for col in ["precio_min_mxn", "precio_max_mxn", "precio_frecuente_mxn"]:
        if col in df_trabajo.columns:
            df_trabajo[col] = pd.to_numeric(df_trabajo[col], errors="coerce")

    # Reglas de validación
    cond_fecha_invalida = df_trabajo["fecha"].isna()
    cond_fecha_fuera_rango = (
        (df_trabajo["fecha"] < pd.Timestamp("2020-01-01"))
        | (df_trabajo["fecha"] > pd.Timestamp("2027-12-31"))
    ) & (~cond_fecha_invalida)

    cond_precio_negativo = (
        (df_trabajo["precio_min_mxn"] <= 0)
        | (df_trabajo["precio_max_mxn"] <= 0)
        | (df_trabajo["precio_frecuente_mxn"] <= 0)
    )

    cond_max_menor_min = df_trabajo["precio_max_mxn"] < df_trabajo["precio_min_mxn"]

    cond_frecuente_fuera_rango = (
        (df_trabajo["precio_frecuente_mxn"] < df_trabajo["precio_min_mxn"])
        | (df_trabajo["precio_frecuente_mxn"] > df_trabajo["precio_max_mxn"])
    )

    cond_producto_nulo = df_trabajo["producto"].isna() | (df_trabajo["producto"].astype(str).str.strip() == "")

    # Asignar motivo
    motivos = np.where(
        cond_fecha_invalida,
        "fecha_invalida",
        np.where(
            cond_fecha_fuera_rango,
            "fecha_fuera_de_rango",
            np.where(
                cond_precio_negativo,
                "precio_negativo_o_cero",
                np.where(
                    cond_max_menor_min,
                    "precio_max_menor_min",
                    np.where(
                        cond_frecuente_fuera_rango,
                        "precio_frecuente_inconsistente",
                        np.where(cond_producto_nulo, "producto_nulo", "valido"),
                    ),
                ),
            ),
        ),
    )

    df_trabajo["motivo_rechazo"] = motivos
    es_rechazado = df_trabajo["motivo_rechazo"] != "valido"

    df_rechazados = df_trabajo[es_rechazado].copy()
    df_validos = df_trabajo[~es_rechazado].copy()

    # Limpiar columnas auxiliares de válidos
    df_validos = df_validos.drop(columns=["motivo_rechazo"])
    df_validos["anio_mes"] = df_validos["fecha"].dt.strftime("%Y-%m")
    df_validos["fecha_iso"] = df_validos["fecha"].dt.strftime("%Y-%m-%d")

    # Enriquecer rechazados con timestamp de cuarentena
    if not df_rechazados.empty:
        df_rechazados["fecha_rechazo_utc"] = datetime.now(timezone.utc).isoformat()

    return df_validos, df_rechazados


def detectar_atipicos_iqr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica el método de Rango Intercuartílico (IQR) por grupo (producto, plaza_id).
    Etiqueta registros atípicos (es_atipico_iqr) y genera precio_frecuente_limpio
    acotando valores extremos para estabilidad analítica sin perder auditabilidad.
    """
    df_out = df.copy()
    df_out["es_atipico_iqr"] = False
    df_out["precio_frecuente_limpio"] = df_out["precio_frecuente_mxn"]

    grupos = df_out.groupby(["producto", "plaza_id"])

    for (prod, plaza), idx in grupos.groups.items():
        precios = df_out.loc[idx, "precio_frecuente_mxn"]
        if len(precios) < 4:
            continue

        q1 = precios.quantile(0.25)
        q3 = precios.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            continue

        lim_inf = max(0.0, q1 - 1.5 * iqr)
        lim_sup = q3 + 1.5 * iqr

        mascara_atipico = (precios < lim_inf) | (precios > lim_sup)
        df_out.loc[idx[mascara_atipico], "es_atipico_iqr"] = True
        # Clipeo suave para variable limpia
        df_out.loc[idx, "precio_frecuente_limpio"] = precios.clip(lower=lim_inf, upper=lim_sup)

    return df_out


def registrar_cuarentena(df_rechazados: pd.DataFrame) -> None:
    """Guarda registros corruptos en data/cuarentena/rechazos_plata.csv para auditoría."""
    DIR_CUARENTENA.mkdir(parents=True, exist_ok=True)
    archivo_cuarentena = DIR_CUARENTENA / "rechazos_plata.csv"

    if df_rechazados.empty:
        if not archivo_cuarentena.exists():
            columnas = ["fecha_rechazo_utc", "motivo_rechazo", "fecha_observacion_raw", "producto", "precio_frecuente_mxn"]
            pd.DataFrame(columns=columnas).to_csv(archivo_cuarentena, index=False)
        return

    # Si ya existe, combinar y deduplicar por (fecha_observacion_raw, producto, motivo_rechazo)
    if archivo_cuarentena.exists():
        try:
            df_previo = pd.read_csv(archivo_cuarentena)
            df_combinado = pd.concat([df_previo, df_rechazados], ignore_index=True)
            cols_sub = ["fecha_observacion_raw", "plaza_id", "producto", "motivo_rechazo"]
            cols_validas = [c for c in cols_sub if c in df_combinado.columns]
            df_dedup = df_combinado.drop_duplicates(subset=cols_validas, keep="last")
            df_dedup.to_csv(archivo_cuarentena, index=False)
        except Exception:
            df_rechazados.to_csv(archivo_cuarentena, index=False)
    else:
        df_rechazados.to_csv(archivo_cuarentena, index=False)

    logger.warning("Se enviaron %d registros a cuarentena en %s", len(df_rechazados), archivo_cuarentena)


def procesar_capa_plata() -> pd.DataFrame:
    """
    Función orquestadora principal de Capa Bronce a Capa Plata:
    1. Carga histórico y capturas recientes diarias.
    2. Homologa entidades.
    3. Pasa por Puerta 1 (filtra válidos y manda corruptos a cuarentena).
    4. Deduplica por observación.
    5. Aplica detección IQR de atípicos.
    6. Exporta a Parquet y CSV en data/plata/ con metadatos SHA-256.
    """
    DIR_PLATA.mkdir(parents=True, exist_ok=True)
    DIR_CUARENTENA.mkdir(parents=True, exist_ok=True)

    archivos_bronce = []
    # 1. Histórico
    historico_csv = DIR_BRONCE / "sniim_canasta" / "historico" / "sniim_occidente_historico_2022_2026.csv"
    if historico_csv.exists():
        archivos_bronce.append(historico_csv)

    # 2. Capturas diarias
    for sub in (DIR_BRONCE / "sniim_canasta").glob("fecha=*/*.csv"):
        archivos_bronce.append(sub)

    if not archivos_bronce:
        raise FileNotFoundError("No se encontraron archivos en Capa Bronce para procesar Plata.")

    logger.info("Leyendo %d fuentes de datos en Capa Bronce...", len(archivos_bronce))
    dfs = [pd.read_csv(f, dtype=str) for f in archivos_bronce]
    df_crudo = pd.concat(dfs, ignore_index=True)
    logger.info("Total registros brutos combinados: %d", len(df_crudo))

    # Normalizar entidades
    df_norm = normalizar_productos_y_plazas(df_crudo)

    # Puerta 1 de Calidad y Cuarentena
    df_validos, df_rechazados = filtrar_y_cuarentenar(df_norm)
    registrar_cuarentena(df_rechazados)

    # Deduplicación: clave única (fecha_iso, plaza_id, producto, calidad, origen)
    cols_clave = ["fecha_iso", "plaza_id", "producto", "calidad", "origen"]
    cols_existentes = [c for c in cols_clave if c in df_validos.columns]
    antes_dedup = len(df_validos)
    df_dedup = df_validos.drop_duplicates(subset=cols_existentes, keep="last").copy()
    logger.info("Deduplicación: de %d a %d registros (%d duplicados descartados)", antes_dedup, len(df_dedup), antes_dedup - len(df_dedup))

    # Detección IQR de atípicos
    df_plata = detectar_atipicos_iqr(df_dedup)

    # Ordenar cronológicamente
    df_plata = df_plata.sort_values(by=["fecha", "plaza_id", "producto"]).reset_index(drop=True)

    # Guardar en formatos optimizados (CSV siempre garantizado, Parquet con fallback)
    ruta_parquet = DIR_PLATA / "canasta_occidente_plata.parquet"
    ruta_csv = DIR_PLATA / "canasta_occidente_plata.csv"
    ruta_meta = DIR_PLATA / "canasta_occidente_plata.meta.json"

    df_plata.to_csv(ruta_csv, index=False, encoding="utf-8")

    parquet_guardado = False
    try:
        df_plata.to_parquet(ruta_parquet, index=False)
        parquet_guardado = True
    except Exception as e:
        logger.warning("No se pudo generar Parquet localmente (%s). Se garantiza CSV.", e)

    # Metadatos SHA-256 basados en el artefacto disponible
    hasher = hashlib.sha256()
    archivo_para_hash = ruta_parquet if parquet_guardado else ruta_csv
    hasher.update(archivo_para_hash.read_bytes())
    sha_archivo = hasher.hexdigest()

    meta = {
        "capa": "Plata",
        "descripcion": "Datos limpios, normalizados y con banderas IQR de la canasta agropecuaria de Occidente",
        "fecha_procesamiento_utc": datetime.now(timezone.utc).isoformat(),
        "total_registros": len(df_plata),
        "total_en_cuarentena": len(df_rechazados),
        "total_atipicos_iqr": int(df_plata["es_atipico_iqr"].sum()),
        "rango_fechas": {
            "min": str(df_plata["fecha_iso"].min()),
            "max": str(df_plata["fecha_iso"].max()),
        },
        "plazas_incluidas": df_plata["ciudad"].unique().tolist(),
        "productos_incluidos": df_plata["producto"].unique().tolist(),
        "sha256_artefacto": sha_archivo,
        "formato_primario": "parquet" if parquet_guardado else "csv",
        "archivos_salida": {
            "parquet": str(ruta_parquet.relative_to(RAIZ)) if parquet_guardado else None,
            "csv": str(ruta_csv.relative_to(RAIZ)),
        },
    }

    with open(ruta_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info("Capa Plata generada exitosamente: %d registros limpios guardados en %s", len(df_plata), ruta_parquet)
    return df_plata


if __name__ == "__main__":
    procesar_capa_plata()
