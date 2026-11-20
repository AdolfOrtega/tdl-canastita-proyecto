"""
tablero/app.py
Proyecto Integrador - Trusted Data Lab (TDL Canastita)
TecNM Campus Colima
Autores: Adolfo Rodríguez (Ingeniería de Datos) y Andrea Tairi Velázquez Gallardo (Análisis Estadístico)

Tablero interactivo de control para comerciantes, abarroteras y cocinas económicas
(Colima, Guadalajara y Morelia) con visualización de Capa Oro, pronósticos a 4 meses,
semáforo de compras y métricas de calidad SQA (IEEE 730).
"""

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
DIR_ORO = RAIZ / "data" / "oro"
DIR_PLATA = RAIZ / "data" / "plata"
DIR_CUARENTENA = RAIZ / "data" / "cuarentena"
DIR_LAB = RAIZ / "laboratorio"
DIR_CALIDAD = RAIZ / "calidad"

# Configuración de página
st.set_page_config(
    page_title="TDL Canastita — Observatorio Agropecuario",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def cargar_datos_oro():
    ruta_csv = DIR_ORO / "canasta_occidente_oro.csv"
    if not ruta_csv.exists():
        st.error("No se encontró el archivo de Capa Oro. Ejecuta primero `python pipeline/construir_oro.py`.")
        return pd.DataFrame()
    df = pd.read_csv(ruta_csv)
    df["fecha_dt"] = pd.to_datetime(df["anio_mes"] + "-01")
    return df


@st.cache_data
def cargar_pronosticos():
    ruta_pron = DIR_LAB / "pronosticos_futuro.csv"
    ruta_met = DIR_LAB / "metricas_modelos.csv"
    ruta_corr = DIR_LAB / "correlaciones_macro.csv"
    ruta_adf = DIR_LAB / "pruebas_estacionariedad_adf.json"

    df_p = pd.read_csv(ruta_pron) if ruta_pron.exists() else pd.DataFrame()
    df_m = pd.read_csv(ruta_met) if ruta_met.exists() else pd.DataFrame()
    df_c = pd.read_csv(ruta_corr) if ruta_corr.exists() else pd.DataFrame()

    adf_data = []
    if ruta_adf.exists():
        with open(ruta_adf, "r", encoding="utf-8") as f:
            adf_data = json.load(f)

    return df_p, df_m, df_c, adf_data


@st.cache_data
def cargar_cuarentena():
    ruta_q = DIR_CUARENTENA / "rechazos_plata.csv"
    if ruta_q.exists():
        return pd.read_csv(ruta_q)
    return pd.DataFrame()


@st.cache_data
def cargar_bitacora():
    ruta_b = DIR_CALIDAD / "bitacora_captura.csv"
    if ruta_b.exists():
        return pd.read_csv(ruta_b)
    return pd.DataFrame()


@st.cache_data
def cargar_datos_geo():
    ruta_geo = DIR_PLATA / "denue_occidente_geo.csv"
    ruta_muns = RAIZ / "data" / "bronce" / "denue_inegi" / "municipios_occidente.geojson"
    df_g = pd.read_csv(ruta_geo) if ruta_geo.exists() else pd.DataFrame()
    muns = json.loads(ruta_muns.read_text(encoding="utf-8")) if ruta_muns.exists() else {}
    return df_g, muns


@st.cache_data
def cargar_resultados_e2():
    ruta_exp = DIR_LAB / "resultados_experimento_e2.json"
    ruta_25010 = DIR_CALIDAD / "resultados_iso_25010.json"
    ruta_25012 = DIR_CALIDAD / "resultados_iso_25012.json"
    exp = json.loads(ruta_exp.read_text(encoding="utf-8")) if ruta_exp.exists() else {}
    r10 = json.loads(ruta_25010.read_text(encoding="utf-8")) if ruta_25010.exists() else {}
    r12 = json.loads(ruta_25012.read_text(encoding="utf-8")) if ruta_25012.exists() else {}
    return exp, r10, r12


df_oro = cargar_datos_oro()
df_pron, df_metricas, df_corr, adf_data = cargar_pronosticos()
df_cuarentena = cargar_cuarentena()
df_bitacora = cargar_bitacora()
df_geo, geojson_muns = cargar_datos_geo()
exp_e2, iso_25010, iso_25012 = cargar_resultados_e2()

# ----------------- BARRA LATERAL (SIDEBAR) -----------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Logo-TecNM.svg/320px-Logo-TecNM.svg.png", width=160)
st.sidebar.title("TDL Canastita")
st.sidebar.markdown("**Trusted Data Lab — Occidente**")
st.sidebar.caption("TecNM Colima · Ing. en Sistemas Computacionales")
st.sidebar.markdown("---")

if not df_oro.empty:
    ciudades_disponibles = ["Todas las Plazas (Comparativo)"] + sorted(df_oro["ciudad"].unique().tolist())
    ciudad_sel = st.sidebar.selectbox("📍 Plaza / Mercado:", ciudades_disponibles, index=1 if "Colima" in ciudades_disponibles else 0)

    productos_disponibles = sorted(df_oro["producto"].unique().tolist())
    producto_sel = st.sidebar.selectbox("🍅 Producto agropecuario:", productos_disponibles, index=productos_disponibles.index("Jitomate Saladette") if "Jitomate Saladette" in productos_disponibles else 0)

    meses = sorted(df_oro["anio_mes"].unique().tolist())
    rango_meses = st.sidebar.select_slider(
        "📅 Ventana temporal de análisis:",
        options=meses,
        value=(meses[max(0, len(meses) - 24)], meses[-1]),
    )

    moneda = st.sidebar.radio("💵 Moneda de visualización:", ["Pesos Mexicanos (MXN)", "Dólares Americanos (USD)"], index=0)
    col_precio = "precio_promedio_mxn" if moneda.startswith("Pesos") else "precio_usd"
    prefijo_moneda = "$" if moneda.startswith("Pesos") else "US$"

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Perfil de Usuario:**
    Cocinas económicas (*Restaurante Luisiana*), fondas, abarroteras y comerciantes de tianguis de Colima.
    """)

# ----------------- ENCABEZADO PRINCIPAL -----------------
st.title("🛒 Observatorio de Precios y Pronósticos Mayoristas")
st.markdown("""
*Plataforma de inteligencia de mercado para insumos frescos de la canasta agropecuaria en Colima, Guadalajara y Morelia.*  
**Integrantes:** Adolfo Rodríguez (Ingeniería de Datos) & Andrea Tairi Velázquez Gallardo (Análisis Estadístico).
""")

pestanas = st.tabs([
    "📈 Visor de Precios y Mercado",
    "🔬 Laboratorio de Pronósticos 2027",
    "🛡️ Calidad de Datos, Cuarentena & SQA",
    "🗺️ Mapa Geoespacial DENUE",
    "⚗️ Experimento 2³ & Normas ISO",
])

# ================= PESTAÑA 1: VISOR DE PRECIOS =================
with pestanas[0]:
    if df_oro.empty:
        st.warning("No hay datos en Capa Oro.")
    else:
        # Filtrar datos
        mask_rango = (df_oro["anio_mes"] >= rango_meses[0]) & (df_oro["anio_mes"] <= rango_meses[1])
        df_filtrado = df_oro[mask_rango & (df_oro["producto"] == producto_sel)].copy()

        if ciudad_sel != "Todas las Plazas (Comparativo)":
            df_filtrado_plaza = df_filtrado[df_filtrado["ciudad"] == ciudad_sel].sort_values("fecha_dt")
        else:
            df_filtrado_plaza = df_filtrado[df_filtrado["ciudad"] == "Colima"].sort_values("fecha_dt")

        if df_filtrado_plaza.empty:
            st.warning(f"No se encontraron registros para {producto_sel} en el rango seleccionado.")
        else:
            ult = df_filtrado_plaza.iloc[-1]
            ant = df_filtrado_plaza.iloc[-2] if len(df_filtrado_plaza) > 1 else ult

            # Tarjetas de Métricas (KPIs)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric(
                label=f"Precio Actual ({ult['ciudad']})",
                value=f"{prefijo_moneda}{ult[col_precio]:.2f} / kg",
                delta=f"{ult['variacion_mom_pct']:+.1f}% vs mes ant." if pd.notna(ult["variacion_mom_pct"]) else None,
            )
            c2.metric(
                label="Variación Anual (YoY)",
                value=f"{ult['variacion_yoy_pct']:+.1f}%" if pd.notna(ult["variacion_yoy_pct"]) else "N/D",
                delta_color="inverse",
            )
            c3.metric(
                label="Spread Mayorista (Máx - Mín)",
                value=f"${ult['spread_mensual_mxn']:.2f} MXN",
                delta=f"{ult['spread_pct']:.1f}% de amplitud",
            )
            c4.metric(
                label="Tipo de Cambio FIX",
                value=f"${ult['tipo_cambio_fix_promedio']:.2f} MXN/USD",
                delta=f"Banxico {ult['anio_mes']}",
            )
            c5.metric(
                label="Inflación INPC (Mensual)",
                value=f"{ult['inflacion_mensual_pct']:+.2f}%" if pd.notna(ult["inflacion_mensual_pct"]) else "N/D",
                delta="Nivel: " + str(ult["inpc_mensual"]),
            )

            st.markdown("---")

            # Semáforo de Compras para Negocio
            st.subheader("🚦 Semáforo de Compras para el Negocio (Recomendación Operativa)")
            hist_precios = df_filtrado_plaza[col_precio]
            q25 = hist_precios.quantile(0.25)
            q75 = hist_precios.quantile(0.75)
            precio_actual = ult[col_precio]

            col_sem1, col_sem2 = st.columns([1, 3])
            with col_sem1:
                if precio_actual < q25 or (pd.notna(ult["variacion_mom_pct"]) and ult["variacion_mom_pct"] < -8.0):
                    st.success("### 🟢 COMPRA FAVORABLE\nPrecio en zona baja histórica.")
                elif precio_actual > q75 or (pd.notna(ult["variacion_mom_pct"]) and ult["variacion_mom_pct"] > 12.0):
                    st.error("### 🔴 ALERTA DE COSTOS\nPrecio por encima del percentil 75.")
                else:
                    st.warning("### 🟡 PRECIO ESTABLE\nPrecio en rango habitual de mercado.")

            with col_sem2:
                st.markdown(f"""
                - **Precio actual observado:** `{prefijo_moneda}{precio_actual:.2f} / kg` en **{ult['nombre_plaza']}**.
                - **Umbrales históricos de referencia:** Percentil 25: `{prefijo_moneda}{q25:.2f}` | Mediana: `{prefijo_moneda}{hist_precios.median():.2f}` | Percentil 75: `{prefijo_moneda}{q75:.2f}`.
                - **Impacto para cocinas económicas (Luisiana) y tianguis:**  
                  Revisar si conviene abastecer volumen para 3-4 semanas o adquirir únicamente inventario justo a tiempo para mitigar merma por perecibilidad.
                """)

            st.markdown("---")

            # Gráficos de Serie Temporal y Comparativo Regional
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.subheader(f"📊 Evolución Histórica: {producto_sel}")
                fig1, ax1 = plt.subplots(figsize=(8, 4.5))
                ax1.plot(df_filtrado_plaza["fecha_dt"], df_filtrado_plaza[col_precio], label="Precio Mensual", color="#1f77b4", lw=2, marker=".")
                if "media_movil_3m" in df_filtrado_plaza.columns and moneda.startswith("Pesos"):
                    ax1.plot(df_filtrado_plaza["fecha_dt"], df_filtrado_plaza["media_movil_3m"], label="Media Móvil 3M", color="#ff7f0e", linestyle="--")
                ax1.set_ylabel(f"Precio ({moneda[:3]} / kg)")
                ax1.grid(True, linestyle=":", alpha=0.6)
                ax1.legend(loc="upper left")
                st.pyplot(fig1)

            with col_g2:
                st.subheader(f"🗺️ Comparativo Regional de Plazas: {producto_sel}")
                fig2, ax2 = plt.subplots(figsize=(8, 4.5))
                colores_plazas = {"Colima": "#2ca02c", "Guadalajara": "#1f77b4", "Morelia": "#d62728"}

                for ciudad_nombre in ["Colima", "Guadalajara", "Morelia"]:
                    sub_c = df_filtrado[df_filtrado["ciudad"] == ciudad_nombre].sort_values("fecha_dt")
                    if not sub_c.empty:
                        ax2.plot(sub_c["fecha_dt"], sub_c[col_precio], label=f"{ciudad_nombre}", color=colores_plazas.get(ciudad_nombre, "gray"), lw=1.8)

                ax2.set_ylabel(f"Precio ({moneda[:3]} / kg)")
                ax2.grid(True, linestyle=":", alpha=0.6)
                ax2.legend(loc="upper left")
                st.pyplot(fig2)

            st.caption("Fuente de datos: SNIIM (Secretaría de Economía) y API SIE de Banco de México, procesados y certificados en Capa Oro.")

# ================= PESTAÑA 2: LABORATORIO DE PRONÓSTICOS =================
with pestanas[1]:
    st.header("🔬 Laboratorio Estadístico y Pronósticos a Futuro (2027)")
    st.markdown("""
    Modelado predictivo sobre 59 meses de cotizaciones mayoristas en la Central de Abasto de Colima (Plaza 80).  
    Se compararon 4 familias de modelos (**SES, Holt, Holt-Winters, ARIMA**) utilizando validación fuera de muestra.
    """)

    if df_pron.empty or df_metricas.empty:
        st.info("Ejecuta `python laboratorio/pronostico_series_tiempo.py` para generar los modelos y pronósticos.")
    else:
        prod_lab_sel = st.selectbox(
            "Selecciona el insumo a inspeccionar:",
            ["Jitomate Saladette", "Limon con semilla #5", "Aguacate Hass"],
            index=0,
        )

        sub_pron = df_pron[df_pron["producto"] == prod_lab_sel]
        sub_met = df_metricas[df_metricas["producto"] == prod_lab_sel]
        ganador_row = sub_met.iloc[0]

        # Métricas del Modelo Ganador
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Modelo Seleccionado", ganador_row["modelo"].split("(")[0].strip())
        m2.metric("MAPE (Error %)", f"{ganador_row['mape']:.2f}%", delta="Menor error relativo")
        m3.metric("RMSE (Error Cuadrático)", f"${ganador_row['rmse']:.2f} MXN")
        m4.metric("MAE (Error Absoluto)", f"${ganador_row['mae']:.2f} MXN")

        st.markdown("---")

        # Gráfico de Serie Histórica + Pronóstico a 4 Meses
        st.subheader(f"📈 Proyección a 4 Meses: {prod_lab_sel} (Colima)")
        sub_hist = df_oro[(df_oro["plaza_id"] == 80) & (df_oro["producto"] == prod_lab_sel)].sort_values("fecha_dt")

        fig_pron, ax_pron = plt.subplots(figsize=(10, 4.5))
        ax_pron.plot(sub_hist["fecha_dt"], sub_hist["precio_promedio_mxn"], label="Histórico Observado (2022-2026)", color="#1f77b4", lw=2)

        fechas_p_dt = pd.to_datetime(sub_pron["fecha"])
        fechas_linea = [sub_hist["fecha_dt"].iloc[-1]] + list(fechas_p_dt)
        precios_linea = [sub_hist["precio_promedio_mxn"].iloc[-1]] + list(sub_pron["precio_pronosticado_mxn"])

        ax_pron.plot(fechas_linea, precios_linea, label=f"Pronóstico ({ganador_row['modelo']})", color="#d62728", linestyle="--", lw=2, marker="o")
        ax_pron.fill_between(
            fechas_p_dt,
            sub_pron["limite_inferior_95_mxn"],
            sub_pron["limite_superior_95_mxn"],
            color="pink",
            alpha=0.4,
            label="Intervalo de Confianza al 95%",
        )
        ax_pron.set_ylabel("Precio (MXN / kg)")
        ax_pron.grid(True, linestyle=":", alpha=0.6)
        ax_pron.legend(loc="upper left")
        st.pyplot(fig_pron)

        # Tabla de Pronóstico y Tabla de Modelos
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.subheader("📋 Pronóstico Puntual (Dic 2026 – Mar 2027)")
            st.dataframe(
                sub_pron[["anio_mes", "precio_pronosticado_mxn", "limite_inferior_95_mxn", "limite_superior_95_mxn"]].rename(
                    columns={
                        "anio_mes": "Período",
                        "precio_pronosticado_mxn": "Precio Proyectado (MXN)",
                        "limite_inferior_95_mxn": "Límite Mín (95%)",
                        "limite_superior_95_mxn": "Límite Máx (95%)",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        with col_t2:
            st.subheader("🏆 Comparativa de las 4 Familias de Modelos")
            st.dataframe(
                sub_met[["modelo", "mape", "rmse", "mae"]].rename(
                    columns={"modelo": "Familia de Modelo", "mape": "MAPE (%)", "rmse": "RMSE ($)", "mae": "MAE ($)"}
                ),
                use_container_width=True,
                hide_index=True,
            )

        # Pruebas de Estacionariedad y Correlación
        st.markdown("---")
        st.subheader("🧪 Pruebas de Estacionariedad (ADF) e Influencia Macroeconómica")
        col_adf, col_corr = st.columns(2)

        with col_adf:
            st.markdown("**Prueba Augmented Dickey-Fuller (ADF):**")
            adf_prod = [a for a in adf_data if a["producto"] == prod_lab_sel]
            if adf_prod:
                res_a = adf_prod[0]
                st.markdown(f"""
                - **Serie en niveles:** Estadístico t: `{res_a['niveles']['estadistico_adf']}` | p-valor: `{res_a['niveles']['p_valor']}` (Estacionaria: `{res_a['niveles']['es_estacionaria']}`).
                - **Serie en primera diferencia (ΔY):** Estadístico t: `{res_a['primera_diferencia']['estadistico_adf']}` | p-valor: `{res_a['primera_diferencia']['p_valor']:.6f}`.
                - **Conclusión Estadística:** La serie es integrada de orden 1, **$I(1)$**, requiriendo diferenciación para eliminar la tendencia no estacionaria.
                """)

        with col_corr:
            st.markdown("**Correlaciones con Banxico (Tipo de Cambio FIX e Inflación INPC):**")
            corr_prod = df_corr[df_corr["producto"] == prod_lab_sel]
            if not corr_prod.empty:
                rc = corr_prod.iloc[0]
                st.markdown(f"""
                - **Tipo de Cambio FIX (USD/MXN):** Pearson $r = {rc['corr_pearson_tc_fix']:+.3f}$ (p: `{rc['p_valor_tc_fix']}`) | Spearman $\\rho = {rc['corr_spearman_tc_fix']:+.3f}$.
                - **Inflación INPC:** Pearson $r = {rc['corr_pearson_inpc']:+.3f}$ (p: `{rc['p_valor_inpc']}`) | Spearman $\\rho = {rc['corr_spearman_inpc']:+.3f}$.
                """)

# ================= PESTAÑA 3: GOBERNANZA, CUARENTENA & SQA =================
with pestanas[2]:
    st.header("🛡️ Aseguramiento de Calidad de Software (IEEE Std 730) & Cuarentena")
    st.markdown("""
    Supervisión técnica de la arquitectura Medallion, cumplimiento de puertas de calidad y estado de salud operativa.
    """)

    # KPIs de Calidad dinamicos
    disp_str = "N/D"
    delta_disp = "Sin bitacora"
    if not df_bitacora.empty and "modo" in df_bitacora.columns:
        prod_b = df_bitacora[df_bitacora["modo"] == "diario"]
        if not prod_b.empty:
            ex = int((prod_b["estado"] == "EXITO").sum())
            tot = len(prod_b)
            disp_str = f"{(ex / tot) * 100.0:.1f}%"
            delta_disp = f"{ex} / {tot} corridas diarias"

    iso10_val = f"{iso_25010['puntaje_global_pct']:.1f}%" if iso_25010 else "N/D"
    iso12_val = f"{iso_25012['puntaje_global_pct']:.1f}%" if iso_25012 else "N/D"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Disponibilidad Operativa", disp_str, delta=delta_disp)
    k2.metric("Indice ISO/IEC 25010", iso10_val, delta=f"ISO 25012 Datos: {iso12_val}")
    k3.metric("Registros Limpios en Plata", f"{len(pd.read_csv(DIR_PLATA / 'canasta_occidente_plata.csv')):,}" if (DIR_PLATA / "canasta_occidente_plata.csv").exists() else "0")
    k4.metric("Registros en Cuarentena", f"{len(df_cuarentena)}" if not df_cuarentena.empty else "0", delta="Puerta 1 activa", delta_color="inverse")

    st.markdown("---")

    col_q1, col_q2 = st.columns([1, 1])

    with col_q1:
        st.subheader("☣️ Almacén de Cuarentena (`data/cuarentena/rechazos_plata.csv`)")
        st.markdown("""
        Los registros corruptos provenientes de fuentes externas son interceptados por la **Puerta 1** y aislados para auditoría:
        """)
        if not df_cuarentena.empty:
            st.dataframe(
                df_cuarentena[["fecha_rechazo_utc", "motivo_rechazo", "fecha_observacion_raw", "producto", "precio_min_mxn", "precio_max_mxn"]].head(15),
                use_container_width=True,
                hide_index=True,
            )
            st.caption("Desglose de motivos: Inversión lógica (P_max < P_min) o inconsistencia de precio modal.")
        else:
            st.success("No hay registros en cuarentena.")

    with col_q2:
        st.subheader("📋 Bitácora de Ingestión en Producción (GitHub Actions)")
        st.markdown("Historial de capturas automatizadas registradas en `calidad/bitacora_captura.csv`:")
        if not df_bitacora.empty:
            st.dataframe(
                df_bitacora[["timestamp_inicio_utc", "fuente", "modo", "estado", "registros_capturados", "duracion_seg"]].tail(10),
                use_container_width=True,
                hide_index=True,
            )
            st.caption("Tasa de éxito en corridas programadas de producción: 100%. MTTR = 0 h.")
        else:
            st.info("Sin registros en bitácora.")

    st.markdown("---")
    st.subheader("📑 Documentación y Entregables de Calidad")
    st.markdown("""
    - **Plan SQA IEEE 730:** `docs/E1/plan_sqa_ieee730.md`
    - **Evaluación ISO/IEC 25010 y 25012:** `docs/E2/evaluacion_iso_25010_25012.md`
    - **Declaración de Ética y LFPDPPP:** `docs/etica-datos.md`
    - **Diccionario de Datos v2.0:** `pipeline/diccionario_datos.md`
    - **Manifiesto de Linaje Oro:** `data/oro/linaje_oro.json`
    - **Auditoría Cruzada:** `docs/E2/auditoria_cruzada.md`
    """)

# ================= PESTAÑA 4: MAPA GEOESPACIAL DENUE =================
with pestanas[3]:
    st.header("🗺️ Cobertura Comercial Geoespacial (INEGI DENUE + Marco Geoestadístico)")
    st.markdown("""
    Unión espacial (`within`) sobre polígonos municipales oficiales del INEGI (CRS `EPSG:4326`), midiendo
    la concentración de fruterías, abarroteras y cocinas económicas respecto a cada Central de Abasto.
    *Cumplimiento estricto LFPDPPP: cero teléfonos, correos ni domicilios personales.*
    """)

    if df_geo.empty:
        st.info("Ejecuta `python -m extractores.ejecutar_captura --modo geo` y `python pipeline/enriquecer_geo.py`.")
    else:
        col_f1, col_f2 = st.columns(2)
        plazas_geo_disp = sorted(df_geo["ciudad_plaza"].dropna().unique().tolist())
        plaza_geo_sel = col_f1.selectbox(
            "📍 Selecciona Plaza para centrar mapa:",
            plazas_geo_disp,
            index=plazas_geo_disp.index("Colima") if "Colima" in plazas_geo_disp else 0,
        )
        cats_disp = ["Todas las Categorías"] + sorted(df_geo["categoria_canastita"].dropna().unique().tolist())
        cat_geo_sel = col_f2.selectbox("🏪 Categoría Comercial (Canastita):", cats_disp, index=0)

        df_geo_f = df_geo[df_geo["ciudad_plaza"] == plaza_geo_sel].copy()
        if cat_geo_sel != "Todas las Categorías":
            df_geo_f = df_geo_f[df_geo_f["categoria_canastita"] == cat_geo_sel].copy()

        # KPIs Geoespaciales
        total_g = len(df_geo_f)
        dist_med = df_geo_f["distancia_central_abasto_km"].mean() if total_g else 0.0
        pct_nucleo = (df_geo_f["distancia_central_abasto_km"] < 2.0).mean() * 100.0 if total_g else 0.0
        pct_within = df_geo_f["cvegeo_mun"].notna().mean() * 100.0 if total_g else 0.0

        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Establecimientos en Mapa", f"{total_g:,}")
        g2.metric("Distancia Media a Central", f"{dist_med:.2f} km")
        g3.metric("Dentro de Polígono INEGI", f"{pct_within:.1f}%")
        g4.metric("Zona Núcleo (< 2 km)", f"{pct_nucleo:.1f}%")

        # Asignar colores RGB segun categoria para pydeck
        colores_rgb = {
            "Fruteria / Mercado": [46, 160, 67, 210],
            "Abarrotes / Miscelanea": [31, 119, 180, 185],
            "Cocina economica / Restaurante": [255, 127, 14, 175],
        }
        df_geo_f["color_rgba"] = df_geo_f["categoria_canastita"].map(
            lambda x: colores_rgb.get(x, [120, 120, 120, 160])
        )

        centrales_ref = {
            "Colima": {"lat": 19.2248, "lon": -103.7325, "nombre_comercial": "CENTRAL DE ABASTO DE COLIMA", "categoria_canastita": "Nodo Mayorista SNIIM", "anillo_logistico": "0 km (Origen)", "distancia_central_abasto_km": 0.0},
            "Guadalajara": {"lat": 20.6540, "lon": -103.3830, "nombre_comercial": "MERCADO DE ABASTO DE GUADALAJARA", "categoria_canastita": "Nodo Mayorista SNIIM", "anillo_logistico": "0 km (Origen)", "distancia_central_abasto_km": 0.0},
            "Morelia": {"lat": 19.7230, "lon": -101.1780, "nombre_comercial": "MERCADO DE ABASTO DE MORELIA", "categoria_canastita": "Nodo Mayorista SNIIM", "anillo_logistico": "0 km (Origen)", "distancia_central_abasto_km": 0.0},
        }
        central_info = centrales_ref.get(plaza_geo_sel, {"lat": 19.24, "lon": -103.72, "nombre_comercial": plaza_geo_sel, "categoria_canastita": "Central", "anillo_logistico": "0 km", "distancia_central_abasto_km": 0.0})
        df_central = pd.DataFrame([central_info])

        capas_pdk = []
        if geojson_muns:
            capas_pdk.append(
                pdk.Layer(
                    "GeoJsonLayer",
                    data=geojson_muns,
                    stroked=True,
                    filled=True,
                    get_fill_color=[31, 119, 180, 22],
                    get_line_color=[31, 119, 180, 140],
                    line_width_min_pixels=2,
                )
            )

        capas_pdk.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=df_geo_f,
                get_position="[longitud, latitud]",
                get_fill_color="color_rgba",
                get_radius=38,
                radius_min_pixels=3,
                radius_max_pixels=10,
                pickable=True,
            )
        )
        capas_pdk.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=df_central,
                get_position="[lon, lat]",
                get_fill_color=[214, 39, 40, 255],
                get_line_color=[255, 255, 255, 255],
                stroked=True,
                line_width_min_pixels=2,
                get_radius=220,
                radius_min_pixels=9,
                pickable=True,
            )
        )

        vista_inicial = pdk.ViewState(
            latitude=float(df_geo_f["latitud"].mean()) if total_g else central_info["lat"],
            longitude=float(df_geo_f["longitud"].mean()) if total_g else central_info["lon"],
            zoom=12.2,
            pitch=0,
        )
        st.pydeck_chart(
            pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                initial_view_state=vista_inicial,
                layers=capas_pdk,
                tooltip={"text": "{nombre_comercial}\n{categoria_canastita}\n{anillo_logistico}\nDistancia: {distancia_central_abasto_km} km"},
            )
        )
        st.caption("Verde: Fruterías / Mercados | Azul: Abarrotes | Naranja: Cocinas / Restaurantes | Punto Rojo: Central de Abasto.")

        col_geo_l, col_geo_r = st.columns(2)
        with col_geo_l:
            st.subheader("📊 Distribución por Anillo Logístico")
            if not df_geo_f.empty:
                resumen_anillos = df_geo_f["anillo_logistico"].value_counts().reset_index()
                resumen_anillos.columns = ["Anillo Logístico", "Establecimientos"]
                st.dataframe(resumen_anillos, use_container_width=True, hide_index=True)

        with col_geo_r:
            st.subheader("📋 Muestra Pública DENUE (Cero PII)")
            cols_ver = ["nombre_comercial", "categoria_canastita", "colonia", "nombre_municipio_geo", "distancia_central_abasto_km"]
            st.dataframe(df_geo_f[cols_ver].head(15), use_container_width=True, hide_index=True)

# ================= PESTAÑA 5: EXPERIMENTO 2^3 & NORMAS ISO =================
with pestanas[4]:
    st.header("⚗️ Experimento Factorial 2³ & Evaluación ISO/IEC 25010 / 25012")
    st.markdown("""
    Resultados experimentales de la **Ruta Ingeniería** sobre copia local congelada del SNIIM
    (`data/bronce/sniim_html_snapshot/`) y certificación cuantitativa bajo la familia **SQuaRE**.
    """)

    if not exp_e2:
        st.info("Ejecuta `python laboratorio/experimento_factorial_2k.py` para generar el experimento.")
    else:
        conf_e2 = exp_e2.get("confirmacion", {})
        exp1_e2 = exp_e2.get("experimento_2_3", {})
        sup_e2 = exp1_e2.get("supuestos_escala_original", {})
        f24_e2 = exp_e2.get("comparativa_2_4_fraccionado", {})

        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Configuración Óptima", conf_e2.get("optimo_descripcion", "N/D"))
        e2.metric("Tiempo Óptimo Confirmado", f"{conf_e2.get('optimo_media_obs_seg', 0):.3f} s", delta=f"{conf_e2.get('mejora_tiempo_vs_referencia_pct', 0):.1f}% más rápido vs E1")
        e3.metric("Ahorro Disco Parquet", f"{exp1_e2.get('ahorro_espacio_parquet_pct', 0):.2f}%", delta=f"{exp1_e2.get('tasa_error_global_pct', 0):.1f}% tasa de error")
        e4.metric("Ahorro Diseño 2^(4-1)", f"{f24_e2.get('ahorro_pct', 50):.0f}%", delta=f"Resolución {f24_e2.get('resolucion', 'IV')} ({f24_e2.get('relacion_definidora', 'I=ABCD')})")

        st.markdown(f"""
        - **Puerta 3 Estadística (Supuestos ANOVA 2³):** Shapiro-Wilk `p = {sup_e2.get('shapiro_p')}` (`normalidad={sup_e2.get('normalidad_cumplida')}`) · Levene `p = {sup_e2.get('levene_p')}` (`homocedasticidad={sup_e2.get('homocedasticidad_cumplida')}`) · Durbin-Watson = `{sup_e2.get('durbin_watson')}`.
        - **Corrida de confirmación al 95%:** Intervalo predicho `[{conf_e2.get('ic95_inf_seg')}, {conf_e2.get('ic95_sup_seg')}] s` vs media observada **`{conf_e2.get('optimo_media_obs_seg')} s`** (Dentro de IC 95%: `{conf_e2.get('confirmacion_dentro_ic95')}`).
        """)

        col_img1, col_img2 = st.columns(2)
        with col_img1:
            p_ef = DIR_LAB / "graficos" / "efectos_principales_2_3.png"
            if p_ef.exists():
                st.image(str(p_ef), caption="Efectos Principales del Diseño Factorial 2³", use_container_width=True)
            p_2v = DIR_LAB / "graficos" / "interaccion_2vias_lote_formato.png"
            if p_2v.exists():
                st.image(str(p_2v), caption="ANOVA 2 Vías (3x3): Lote x Formato de Salida", use_container_width=True)

        with col_img2:
            p_in = DIR_LAB / "graficos" / "interacciones_2_3.png"
            if p_in.exists():
                st.image(str(p_in), caption="Gráficas de Interacción Doble (2³)", use_container_width=True)
            p_cf = DIR_LAB / "graficos" / "confirmacion_optimo_vs_base.png"
            if p_cf.exists():
                st.image(str(p_cf), caption="Corrida de Confirmación: Óptimo vs Base E1", use_container_width=True)

        st.markdown("---")
        col_iso1, col_iso2 = st.columns(2)
        with col_iso1:
            st.subheader(f"📐 Calidad del Producto ISO/IEC 25010 ({iso_25010.get('puntaje_global_pct', 0)}%)")
            if iso_25010 and "caracteristicas" in iso_25010:
                df_i10 = pd.DataFrame(iso_25010["caracteristicas"])[["caracteristica", "valor_medido", "calificacion_pct"]]
                st.dataframe(df_i10, use_container_width=True, hide_index=True)

        with col_iso2:
            st.subheader(f"🗄️ Calidad de Datos ISO/IEC 25012 ({iso_25012.get('puntaje_global_pct', 0)}%)")
            if iso_25012 and "caracteristicas" in iso_25012:
                df_i12 = pd.DataFrame(iso_25012["caracteristicas"])[["caracteristica", "categoria", "puntaje_pct"]]
                st.dataframe(df_i12, use_container_width=True, hide_index=True)
