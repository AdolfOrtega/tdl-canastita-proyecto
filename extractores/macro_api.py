"""
extractores/macro_api.py
Proyecto Integrador - Trusted Data Lab (tdl-canastita-proyecto)
Alumnos: Adolfo Rodriguez y Andrea Tairi Velazquez Gallardo

Fuente 2 (API del SIE de Banxico):
- Serie SF43718: Tipo de cambio FIX (USD/MXN) diario desde 2022.
- Serie SP1: Indice Nacional de Precios al Consumidor (INPC mensual desde 2022).
"""

import os
from datetime import datetime, timezone
from extractores.base import ExtractorEtico, cargar_env


def extraer_tipo_cambio_historico(extractor=None, fecha_inicio="2022-01-01", fecha_final="2026-11-05"):
    """Consulta la serie SF43718 (Tipo de cambio FIX) en la API de Banxico."""
    cargar_env()
    ext = extractor or ExtractorEtico(pausa=1.0)
    captura_ts = datetime.now(timezone.utc).isoformat()
    banxico_token = os.getenv("BANXICO_TOKEN", "").strip()

    if banxico_token:
        url_banxico = (
            f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/"
            f"datos/{fecha_inicio}/{fecha_final}"
        )
        try:
            resp = ext.get(url_banxico, headers={"Bmx-Token": banxico_token})
            datos = resp.json().get("bmx", {}).get("series", [{}])[0].get("datos", [])
            registros = []
            for item in datos:
                fecha_raw = item.get("fecha", "")
                dato_raw = item.get("dato", "").replace(",", "")
                try:
                    tc = float(dato_raw)
                except ValueError:
                    continue

                partes = fecha_raw.split("/")
                anio_mes = f"{partes[2]}-{partes[1]}" if len(partes) == 3 else ""
                fecha_iso = f"{partes[2]}-{partes[1]}-{partes[0]}" if len(partes) == 3 else fecha_raw

                registros.append({
                    "fecha_iso": fecha_iso,
                    "anio_mes": anio_mes,
                    "moneda_base": "USD",
                    "moneda_destino": "MXN",
                    "tipo_cambio_fix": tc,
                    "_fuente": "BANXICO_SIE_SF43718",
                    "_url_origen": url_banxico,
                    "_capturado_en_utc": captura_ts,
                })
            if registros:
                return registros
        except Exception as e:
            print(f"Aviso: fallo la consulta con token de Banxico ({e}), intentando respaldo...")

    # Si alguien corre el script en otra compu sin archivo .env, usamos este respaldo publico
    url_fx = f"https://api.frankfurter.app/{fecha_inicio}..{fecha_final}?from=USD&to=MXN"
    resp = ext.get(url_fx)
    rates = resp.json().get("rates", {})
    registros = []
    for fecha_iso in sorted(rates.keys()):
        mxn_val = rates[fecha_iso].get("MXN")
        if mxn_val is None:
            continue
        registros.append({
            "fecha_iso": fecha_iso,
            "anio_mes": fecha_iso[:7],
            "moneda_base": "USD",
            "moneda_destino": "MXN",
            "tipo_cambio_fix": float(mxn_val),
            "_fuente": "FRANKFURTER_FX_API",
            "_url_origen": url_fx,
            "_capturado_en_utc": captura_ts,
        })
    return registros


def extraer_inflacion_mexico_api(extractor=None, fecha_inicio="2022-01-01", fecha_final="2026-11-05"):
    """Consulta la serie SP1 (INPC mensual) en la API de Banxico."""
    cargar_env()
    ext = extractor or ExtractorEtico(pausa=1.0)
    captura_ts = datetime.now(timezone.utc).isoformat()
    banxico_token = os.getenv("BANXICO_TOKEN", "").strip()

    if banxico_token:
        url_sp1 = (
            f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/SP1/"
            f"datos/{fecha_inicio}/{fecha_final}"
        )
        try:
            resp = ext.get(url_sp1, headers={"Bmx-Token": banxico_token})
            series = resp.json().get("bmx", {}).get("series", [])
            if series:
                datos = series[0].get("datos", [])
                registros = []
                for item in datos:
                    fecha_raw = item.get("fecha", "")
                    dato_raw = item.get("dato", "").replace(",", "")
                    try:
                        val = float(dato_raw)
                    except ValueError:
                        continue
                    partes = fecha_raw.split("/")
                    anio_mes = f"{partes[2]}-{partes[1]}" if len(partes) == 3 else ""
                    fecha_iso = f"{partes[2]}-{partes[1]}-{partes[0]}" if len(partes) == 3 else fecha_raw
                    registros.append({
                        "fecha_iso": fecha_iso,
                        "anio_mes": anio_mes,
                        "codigo_indicador": "SP1",
                        "nombre_indicador": "INPC_GENERAL_MENSUAL_BANXICO_INEGI",
                        "valor": val,
                        "pais": "MEX",
                        "_fuente": "BANXICO_SIE_SP1",
                        "_url_origen": url_sp1,
                        "_capturado_en_utc": captura_ts,
                    })
                if registros:
                    return registros
        except Exception as e:
            print(f"Aviso: fallo la lectura de SP1 en Banxico ({e}), intentando respaldo...")

    url_wb = (
        "https://api.worldbank.org/v2/country/MEX/indicator/FP.CPI.TOTL"
        "?date=1985:2025&per_page=100&format=json"
    )
    resp = ext.get(url_wb)
    payload = resp.json()
    registros = []
    if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list):
        for item in payload[1]:
            val = item.get("value")
            anio = item.get("date")
            if val is None or not anio:
                continue
            registros.append({
                "fecha_iso": f"{anio}-12-31",
                "anio_mes": f"{anio}-12",
                "codigo_indicador": "FP.CPI.TOTL",
                "nombre_indicador": "INDICE_PRECIOS_CONSUMIDOR_BASE2010",
                "valor": float(val),
                "pais": "MEX",
                "_fuente": "WORLD_BANK_OPEN_API",
                "_url_origen": url_wb,
                "_capturado_en_utc": captura_ts,
            })
    registros.sort(key=lambda r: r["anio_mes"])
    return registros
