"""
extractores/sniim_canasta.py
Proyecto Integrador - Trusted Data Lab (tdl-canastita-proyecto)
Alumnos: Adolfo Rodriguez y Andrea Tairi Velazquez Gallardo

Fuente 1 (Web Scraping):
Descarga los precios mayoristas de frutas y hortalizas desde el portal del SNIIM
(Secretaria de Economia) en las 3 plazas que comparamos: Colima, Guadalajara y Morelia.
"""

import re
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from extractores.base import ExtractorEtico

URL_SNIIM = (
    "http://www.economia-sniim.gob.mx/nuevo/Consultas/MercadosNacionales/"
    "PreciosDeMercado/Agricolas/ResultadosConsultaFechaFrutasYHortalizas.aspx"
)

# Las 3 plazas de abasto para comparar en el proyecto
PLAZAS_OCCIDENTE = {
    80: {
        "plaza_id": 80,
        "estado": "Colima",
        "ciudad": "Colima",
        "nombre_plaza": "Colima: Centros de distribucion de Colima",
    },
    140: {
        "plaza_id": 140,
        "estado": "Jalisco",
        "ciudad": "Guadalajara",
        "nombre_plaza": "Jalisco: Mercado de Abasto de Guadalajara",
    },
    160: {
        "plaza_id": 160,
        "estado": "Michoacan",
        "ciudad": "Morelia",
        "nombre_plaza": "Michoacan: Mercado de Abasto de Morelia",
    },
}

# IDs de los 6 insumos en el SNIIM para armar la serie historica desde 2022
PRODUCTOS_CANASTA = {
    133: ("Aguacate Hass", "Primera"),
    421: ("Limon c/semilla # 5", "Primera"),
    839: ("Tomate Saladette", "Primera"),
    183: ("Cebolla Bola", "Primera"),
    246: ("Chile Serrano", "Primera"),
    740: ("Papa Alpha", "Primera"),
}

PATRON_FECHA = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def limpiar_precio(texto):
    """Quita signos de pesos o comas y convierte el texto a float."""
    limpio = texto.replace("$", "").replace(",", "").strip()
    try:
        return float(limpio)
    except ValueError:
        return None


def parsear_tabla_sniim(html, plaza_info, captura_ts, url_origen, producto_fijo=None, calidad_fija="Primera"):
    """
    Lee las filas <tr> de la tabla del SNIIM y regresa una lista de diccionarios.
    Nota: cuando se pide ProductoId=-1 la tabla trae 9 columnas, pero cuando se
    consulta un solo producto el SNIIM quita Producto y Calidad y deja 7 columnas.
    """
    soup = BeautifulSoup(html, "html.parser")
    registros = []

    for fila in soup.find_all("tr"):
        celdas = [td.get_text(" ", strip=True) for td in fila.find_all("td")]
        if len(celdas) < 6:
            continue

        fecha_str = celdas[0].strip()
        if not PATRON_FECHA.match(fecha_str):
            continue

        if len(celdas) >= 8 and producto_fijo is None:
            producto = celdas[1].strip()
            calidad = celdas[2].strip()
            presentacion = celdas[3].strip()
            origen = celdas[4].strip()
            p_min = limpiar_precio(celdas[5])
            p_max = limpiar_precio(celdas[6])
            p_frec = limpiar_precio(celdas[7])
            obs = celdas[8].strip() if len(celdas) > 8 else ""
        else:
            producto = producto_fijo or "Producto Canasta"
            calidad = calidad_fija
            presentacion = celdas[1].strip()
            origen = celdas[2].strip()
            p_min = limpiar_precio(celdas[3])
            p_max = limpiar_precio(celdas[4])
            p_frec = limpiar_precio(celdas[5])
            obs = celdas[6].strip() if len(celdas) > 6 else ""

        if p_frec is None and p_min is None:
            continue

        registros.append({
            "fecha_observacion_raw": fecha_str,
            "anio_mes": f"{fecha_str[6:10]}-{fecha_str[3:5]}",
            "plaza_id": plaza_info["plaza_id"],
            "estado": plaza_info["estado"],
            "ciudad": plaza_info["ciudad"],
            "nombre_plaza": plaza_info["nombre_plaza"],
            "producto": producto,
            "calidad": calidad,
            "presentacion": presentacion,
            "origen": origen,
            "precio_min_mxn": p_min,
            "precio_max_mxn": p_max,
            "precio_frecuente_mxn": p_frec,
            "observaciones": obs,
            "_fuente": "SNIIM_SE",
            "_url_origen": url_origen,
            "_capturado_en_utc": captura_ts,
        })

    return registros


def extraer_sniim_reciente(extractor=None, dias_ventana=35):
    """Descarga los registros recientes de las 3 plazas para la corrida diaria."""
    ext = extractor or ExtractorEtico(pausa=1.5)
    captura_ts = datetime.now(timezone.utc).isoformat()

    fecha_fin = datetime.now()
    fecha_ini = fecha_fin - timedelta(days=dias_ventana)
    f_ini_str = fecha_ini.strftime("%d/%m/%Y")
    f_fin_str = fecha_fin.strftime("%d/%m/%Y")

    todos = []
    for dest_id, info in PLAZAS_OCCIDENTE.items():
        params = {
            "fechaInicio": f_ini_str,
            "fechaFinal": f_fin_str,
            "ProductoId": "-1",
            "OrigenId": "-1",
            "Origen": "Todos",
            "DestinoId": str(dest_id),
            "Destino": info["ciudad"],
            "PreciosPorId": "1",
            "RegistrosPorPagina": "500",
        }
        resp = ext.get(URL_SNIIM, params=params)
        # El HTML del SNIIM viene en latin-1
        html = resp.content.decode("latin-1", errors="replace")
        filas = parsear_tabla_sniim(html, info, captura_ts, resp.url)
        todos.extend(filas)

    return todos


def extraer_sniim_historico(extractor=None, fecha_inicio="01/01/2022", fecha_final="05/11/2026"):
    """Descarga la serie historica desde 2022 (>= 36 meses) para los 6 productos base."""
    ext = extractor or ExtractorEtico(pausa=1.5)
    captura_ts = datetime.now(timezone.utc).isoformat()
    todos = []

    for dest_id, info in PLAZAS_OCCIDENTE.items():
        for prod_id, (nombre_prod, calidad_prod) in PRODUCTOS_CANASTA.items():
            params = {
                "fechaInicio": fecha_inicio,
                "fechaFinal": fecha_final,
                "ProductoId": str(prod_id),
                "OrigenId": "-1",
                "Origen": "Todos",
                "DestinoId": str(dest_id),
                "Destino": info["ciudad"],
                "PreciosPorId": "1",
                "RegistrosPorPagina": "1000",
            }
            resp = ext.get(URL_SNIIM, params=params)
            html = resp.content.decode("latin-1", errors="replace")
            filas = parsear_tabla_sniim(
                html,
                info,
                captura_ts,
                resp.url,
                producto_fijo=nombre_prod,
                calidad_fija=calidad_prod,
            )
            todos.extend(filas)

    return todos
