# Declaracion de Etica, Legalidad y Privacidad de Datos (TDL Canastita)

**Proyecto:** Trusted Data Lab — Canastita (Occidente: Colima, Guadalajara y Morelia)  
**Institucion:** Instituto Tecnologico de Colima (TecNM)  
**Integrantes:** Adolfo Rodriguez (`23460528@colima.tecnm.mx`) y Andrea Tairi Velazquez Gallardo (`23460539@colima.tecnm.mx`)  
**Alcance:** Cobertura integral de las tres fuentes del observatorio (E0–E2)

---

## 1. Marco Legal, Licencias y Politica de Extraccion Etica

El observatorio opera exclusivamente con datos publicos gubernamentales de costo `$0` y codigo abierto, aplicando tres reglas invariables en el modulo base [extractores/base.py](../extractores/base.py):
1. **Identificacion honesta:** Todas las peticiones HTTP declaran el encabezado `User-Agent: TDL-Observatorio/1.0 (proyecto academico; contacto: 23460528@colima.tecnm.mx)`.
2. **Respeto automatico a `robots.txt`:** Antes de cualquier peticion de red, `ExtractorEtico` consulta `urllib.robotparser`. Si un dominio prohibe la ruta, el extractor lanza `PermissionError` y se sustituye la fuente.
3. **Respeto a servidores publicos:** Pausa minima entre peticiones al mismo dominio (`>= 1.5 s` en SNIIM/Banxico y `>= 4.0 s` en INEGI DENUE) con retroceso exponencial ante codigos 429 o 5xx. En evaluaciones de rendimiento (experimento factorial $2^3$ de E2) las pruebas repetidas corren exclusivamente sobre una copia local congelada ([data/bronce/sniim_html_snapshot/](../data/bronce/sniim_html_snapshot/)), evitando trafico automatizado innecesario contra portales del gobierno.

> **Precedente real de cumplimiento (`open-meteo.com`):** Durante las primeras pruebas de E0 (Defecto #4 en [calidad/defectos-adolfo.csv](../calidad/defectos-adolfo.csv)), al consultar `https://archive-api.open-meteo.com`, `ExtractorEtico` detecto `Disallow: /` para `User-Agent: *` en su `robots.txt` y detuvo la extraccion de inmediato. En estricto apego a la etica del proyecto, dicha fuente fue descartada sin evadir el bloqueo.

---

## 2. Analisis por Fuente de Datos

| Fuente | Organismo y Metodo de Acceso | Licencia y Base Legal | Estado `robots.txt` y Politica de Frecuencia |
| :--- | :--- | :--- | :--- |
| **1. SNIIM Frutas y Hortalizas** | Secretaria de Economia (`economia-sniim.gob.mx`) · Scraping HTML (`latin-1`) | Informacion publica federal mexicana orientada a transparencia de mercados agropecuarios (sin restricciones de reproduccion con atribucion). | Permite la ruta `/nuevo/Consultas/...`; restringe `/Analisis/`, `/*.xls$`, `/2010/`, `/Sicia*`. Pausa minima `1.5 s`, captura 1 vez al dia en ventana controlada. |
| **2. API SIE de Banxico** (`SF43718` y `SP1`) | Banco de Mexico (`banxico.org.mx/SieAPIRest`) · API REST JSON con `Bmx-Token` | Terminos de Uso de Datos Abiertos del SIE de Banco de Mexico para fines academicos y analiticos con cita de fuente. | Consumo via web service autenticado; credencial aislada en `.env` local (ignorado en `.gitignore`) y en GitHub Secrets en produccion. |
| **3. INEGI DENUE v1 + Marco Geoestadistico** | INEGI (`inegi.org.mx/app/api/denue/v1/` y `gaia.inegi.org.mx/wscatgeo/`) · API REST JSON y GeoJSON | **Terminos de Libre Uso MX** (Datos Abiertos del Gobierno de Mexico / INEGI): permite copiar, redistribuir y transformar citando la fuente oficial. | `www.inegi.org.mx/robots.txt` incluye `Allow: /app`. Pausa ajustada a `4.0 s` tras detectar throttling suave de DENUE; token redactado en logs como `[REDACTED_TOKEN]`. |

---

## 3. Privacidad y Cumplimiento LFPDPPP (Cero Datos Personales)

En cumplimiento estricto de la **Ley Federal de Proteccion de Datos Personales en Posesion de los Particulares (LFPDPPP)**, el observatorio prohibe almacenar nombres de personas fisicas, telefonos, correos electronicos o domicilios particulares en cualquier capa de almacenamiento (incluida la Capa Bronce):

1. **SNIIM y Banxico:** Contienen unicamente precios mayoristas de referencia en centrales de abasto y series macroeconomicas agregadas nacionales. No contienen atributos de personas fisicas.
2. **Sanitizacion previa en INEGI DENUE ([extractores/denue_geo.py](../extractores/denue_geo.py)):** Aunque los establecimientos en el DENUE son unidades economicas censadas, la respuesta cruda del servicio incluye telefonos comerciales, correos de contacto y domicilio exacto con numero interior/exterior que pueden pertenecer a micronegocios familiares en domicilios particulares. Por ello, **antes de escribir el archivo en Capa Bronce**, el extractor excluye de raiz los campos:
   `Telefono`, `Correo_e`, `Sitio_internet`, `Calle`, `Num_Exterior`, `Num_Interior`, `Tipo_vialidad`, `CP` y `Razon_social`.
3. **Verificacion automatica:** La Puerta 1 geoespacial ([pipeline/enriquecer_geo.py](../pipeline/enriquecer_geo.py)) y la suite de integracion continua ([.github/workflows/ci_calidad.yml](../.github/workflows/ci_calidad.yml)) verifican programaticamente que ninguna columna PII prohibida y ningun token secreto existan en los archivos rastreados del repositorio.

---

## 4. Sesgos Conocidos y Estrategias de Mitigacion

| Fuente | Sesgo Conocido | Impacto en la Toma de Decisiones | Mitigacion Aplicada en el Observatorio |
| :--- | :--- | :--- | :--- |
| **SNIIM** | Reporta cotizaciones **mayoristas** de puerta de central de abasto en bulto/kg, no el precio final al consumidor en tianguis o tiendas de esquina. Ademas puede contener errores humanos de captura (p. ej. precio max < min). | Un comerciante o cocina economica podria confundir el precio mayorista con el precio de venta al publico. | Puerta 1 aisla inversiones logicas a `data/cuarentena/rechazos_plata.csv`; el tablero etiqueta explicitamente los valores como *precio mayorista en central de abasto* e incluye bandas de incertidumbre al 95% en pronosticos. |
| **Banxico SIE** | El INPC (`SP1`) se publica con frecuencia mensual y rezago de cierre frente a cotizaciones diarias del mes en curso. | El ultimo mes abierto en tiempo real podria quedar nulo tras el join mensual. | Imputacion causal hacia adelante (`ffill`) documentada en Capa Oro ([pipeline/construir_oro.py](../pipeline/construir_oro.py)) sin usar informacion futura (*no data leakage*). |
| **INEGI DENUE** | **Subregistro del sector informal:** capta unidades economicas establecidas y registradas en censos economicos o actualizaciones del directorio, subestimando puestos rotativos de tianguis y vendedores ambulantes temporales. | Sobrestimar la ausencia de competencia o concentracion en colonias con fuerte actividad informal. | Se explicita al cliente (Restaurante Luisiana y comerciantes de Colima) que el conteo DENUE representa un *piso formal minimo* de fruterias, abarrotes y cocinas dentro del poligono municipal, complementado por analisis de distancia logistica a la Central de Abasto. |

---

## 5. Uso Secundario, Atribucion y Transparencia

Los datos generados por *TDL Canastita* se publican unicamente con fines academicos y de inteligencia comercial regional citando en cada vista del tablero y ficha tecnica a las instituciones emisoras (**Secretaria de Economia - SNIIM**, **Banco de Mexico - SIE** e **INEGI - DENUE y Marco Geoestadistico 2025**). Queda prohibido utilizar los datos para perfilamiento de propietarios individuales o contacto comercial no solicitado.
