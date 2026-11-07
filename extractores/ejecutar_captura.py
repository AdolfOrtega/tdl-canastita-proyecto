"""
extractores/ejecutar_captura.py
Proyecto Integrador - Trusted Data Lab (tdl-canastita-proyecto)
Alumnos: Adolfo Rodriguez y Andrea Tairi Velazquez Gallardo

Script principal que ejecuta las 2 fuentes de E0 (Scraper SNIIM y API Banxico),
guarda los archivos CSV crudos con sus metadatos (.meta.json) en data/bronce/
y registra cada corrida en calidad/bitacora_captura.csv.
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from extractores.base import ExtractorEtico, UA, cargar_env
from extractores.macro_api import (
    extraer_inflacion_mexico_api,
    extraer_tipo_cambio_historico,
)
from extractores.sniim_canasta import (
    extraer_sniim_historico,
    extraer_sniim_reciente,
)

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
DIR_BRONCE = RAIZ_PROYECTO / "data" / "bronce"
ARCHIVO_BITACORA = RAIZ_PROYECTO / "calidad" / "bitacora_captura.csv"


def guardar_csv_y_metadatos(registros, subcarpeta, nombre_base, descripcion):
    """Guarda los registros en data/bronce/<subcarpeta>/ y crea su archivo .meta.json."""
    destino_dir = DIR_BRONCE / subcarpeta
    destino_dir.mkdir(parents=True, exist_ok=True)
    ruta_csv = destino_dir / f"{nombre_base}.csv"
    ruta_meta = destino_dir / f"{nombre_base}.meta.json"

    if not registros:
        raise ValueError(f"No se obtuvieron registros para {subcarpeta}/{nombre_base}")

    columnas = list(registros[0].keys())
    with ruta_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(registros)

    periodos_unicos = sorted({r.get("anio_mes", "") for r in registros if r.get("anio_mes")})
    fuentes_unicas = sorted({r.get("_fuente", "") for r in registros if r.get("_fuente")})

    meta = {
        "nombre_archivo": ruta_csv.name,
        "descripcion": descripcion,
        "fuente_subcarpeta": subcarpeta,
        "fuentes_origen": fuentes_unicas,
        "fecha_captura_utc": datetime.now(timezone.utc).isoformat(),
        "user_agent": UA,
        "total_registros": len(registros),
        "total_periodos_mensuales": len(periodos_unicos),
        "primer_periodo": periodos_unicos[0] if periodos_unicos else None,
        "ultimo_periodo": periodos_unicos[-1] if periodos_unicos else None,
        "columnas": columnas,
    }
    with ruta_meta.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    return ruta_csv


def registrar_bitacora(fuente, modo, inicio_utc, fin_utc, duracion_seg, estado, registros_capturados, archivo_salida, mensaje_error=""):
    """Agrega un renglon a calidad/bitacora_captura.csv para medir MTBF, MTTR y disponibilidad."""
    ARCHIVO_BITACORA.parent.mkdir(parents=True, exist_ok=True)
    existe = ARCHIVO_BITACORA.exists()
    encabezados = [
        "timestamp_inicio_utc",
        "timestamp_fin_utc",
        "fuente",
        "modo",
        "duracion_seg",
        "estado",
        "registros_capturados",
        "archivo_bronce",
        "mensaje_error",
    ]
    with ARCHIVO_BITACORA.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(encabezados)
        writer.writerow([
            inicio_utc,
            fin_utc,
            fuente,
            modo,
            round(duracion_seg, 3),
            estado,
            registros_capturados,
            archivo_salida,
            mensaje_error,
        ])


def ejecutar(modo="diario"):
    print(f"--- Iniciando captura en capa bronce (modo: {modo}) ---")

    cargar_env()
    extractor = ExtractorEtico(pausa=1.5)
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    fallos = 0

    # Fuente 1: Scraping reciente de SNIIM (Colima, Guadalajara y Morelia)
    t0 = time.time()
    ini_utc = datetime.now(timezone.utc).isoformat()
    try:
        datos_sniim_dia = extraer_sniim_reciente(extractor=extractor, dias_ventana=35)
        ruta_sniim_dia = guardar_csv_y_metadatos(
            datos_sniim_dia,
            subcarpeta=f"sniim_canasta/fecha={hoy_str}",
            nombre_base=f"sniim_reciente_{hoy_str}",
            descripcion="Captura programada de precios mayoristas SNIIM en Colima, Guadalajara y Morelia",
        )
        registrar_bitacora(
            fuente="SNIIM_SCRAPER_REC",
            modo=modo,
            inicio_utc=ini_utc,
            fin_utc=datetime.now(timezone.utc).isoformat(),
            duracion_seg=time.time() - t0,
            estado="EXITO",
            registros_capturados=len(datos_sniim_dia),
            archivo_salida=str(ruta_sniim_dia.relative_to(RAIZ_PROYECTO)),
        )
        print(f"OK - SNIIM reciente: {len(datos_sniim_dia)} registros guardados")
    except Exception as e:
        fallos += 1
        registrar_bitacora(
            fuente="SNIIM_SCRAPER_REC",
            modo=modo,
            inicio_utc=ini_utc,
            fin_utc=datetime.now(timezone.utc).isoformat(),
            duracion_seg=time.time() - t0,
            estado="FALLA",
            registros_capturados=0,
            archivo_salida="",
            mensaje_error=str(e),
        )
        print(f"Error en SNIIM reciente: {e}")

    # Fuente 2: API Banxico SIE (Tipo de Cambio FIX USD/MXN e INPC SP1)
    t1 = time.time()
    ini_fx = datetime.now(timezone.utc).isoformat()
    try:
        datos_fx = extraer_tipo_cambio_historico(extractor=extractor)
        ruta_fx = guardar_csv_y_metadatos(
            datos_fx,
            subcarpeta="macro_api/tipo_cambio",
            nombre_base="usd_mxn_historico_2022_2026",
            descripcion="Serie historica y actual de tipo de cambio FIX USD/MXN (Banxico SIE SF43718, 2022-2026)",
        )
        registrar_bitacora(
            fuente="BANXICO_SIE_SF43718_USDMXN",
            modo=modo,
            inicio_utc=ini_fx,
            fin_utc=datetime.now(timezone.utc).isoformat(),
            duracion_seg=time.time() - t1,
            estado="EXITO",
            registros_capturados=len(datos_fx),
            archivo_salida=str(ruta_fx.relative_to(RAIZ_PROYECTO)),
        )
        print(f"OK - Banxico Tipo de Cambio: {len(datos_fx)} registros guardados")
    except Exception as e:
        fallos += 1
        registrar_bitacora(
            fuente="BANXICO_SIE_SF43718_USDMXN",
            modo=modo,
            inicio_utc=ini_fx,
            fin_utc=datetime.now(timezone.utc).isoformat(),
            duracion_seg=time.time() - t1,
            estado="FALLA",
            registros_capturados=0,
            archivo_salida="",
            mensaje_error=str(e),
        )
        print(f"Error en Banxico Tipo de Cambio: {e}")

    t3 = time.time()
    ini_inf = datetime.now(timezone.utc).isoformat()
    try:
        datos_inf = extraer_inflacion_mexico_api(extractor=extractor)
        ruta_inf = guardar_csv_y_metadatos(
            datos_inf,
            subcarpeta="macro_api/inflacion",
            nombre_base="inpc_inflacion_mexico_historico",
            descripcion="Serie historica mensual del INPC Nacional (Banxico SIE SP1, 2022-2026)",
        )
        registrar_bitacora(
            fuente="BANXICO_SIE_SP1_INPC",
            modo=modo,
            inicio_utc=ini_inf,
            fin_utc=datetime.now(timezone.utc).isoformat(),
            duracion_seg=time.time() - t3,
            estado="EXITO",
            registros_capturados=len(datos_inf),
            archivo_salida=str(ruta_inf.relative_to(RAIZ_PROYECTO)),
        )
        print(f"OK - Banxico INPC: {len(datos_inf)} registros guardados")
    except Exception as e:
        fallos += 1
        registrar_bitacora(
            fuente="BANXICO_SIE_SP1_INPC",
            modo=modo,
            inicio_utc=ini_inf,
            fin_utc=datetime.now(timezone.utc).isoformat(),
            duracion_seg=time.time() - t3,
            estado="FALLA",
            registros_capturados=0,
            archivo_salida="",
            mensaje_error=str(e),
        )
        print(f"Error en Banxico INPC: {e}")

    if modo == "completo":
        t2 = time.time()
        ini_hist = datetime.now(timezone.utc).isoformat()
        try:
            datos_sniim_hist = extraer_sniim_historico(extractor=extractor)
            ruta_sniim_hist = guardar_csv_y_metadatos(
                datos_sniim_hist,
                subcarpeta="sniim_canasta/historico",
                nombre_base="sniim_occidente_historico_2022_2026",
                descripcion="Serie historica 2022-2026 de canasta basica en Colima, Guadalajara y Morelia",
            )
            registrar_bitacora(
                fuente="SNIIM_SCRAPER_HIST_36M",
                modo=modo,
                inicio_utc=ini_hist,
                fin_utc=datetime.now(timezone.utc).isoformat(),
                duracion_seg=time.time() - t2,
                estado="EXITO",
                registros_capturados=len(datos_sniim_hist),
                archivo_salida=str(ruta_sniim_hist.relative_to(RAIZ_PROYECTO)),
            )
            print(f"OK - SNIIM historico: {len(datos_sniim_hist)} registros guardados")
        except Exception as e:
            fallos += 1
            registrar_bitacora(
                fuente="SNIIM_SCRAPER_HIST_36M",
                modo=modo,
                inicio_utc=ini_hist,
                fin_utc=datetime.now(timezone.utc).isoformat(),
                duracion_seg=time.time() - t2,
                estado="FALLA",
                registros_capturados=0,
                archivo_salida="",
                mensaje_error=str(e),
            )
            print(f"Error en SNIIM historico: {e}")

    return 0 if fallos == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Ejecuta la captura de datos en la capa bronce.")
    parser.add_argument(
        "--modo",
        choices=["diario", "completo"],
        default="diario",
        help="diario (para GitHub Actions) o completo (descarga tambien el historico 2022-2026).",
    )
    args = parser.parse_args()
    sys.exit(ejecutar(modo=args.modo))


if __name__ == "__main__":
    main()
