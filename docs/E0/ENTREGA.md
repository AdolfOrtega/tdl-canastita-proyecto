# Entrega E0 - TDL Canastita
Equipo: Adolfo Rodríguez (23460528@colima.tecnm.mx) y Andrea Tairi Velázquez Gallardo (23460539@colima.tecnm.mx) - Etiqueta: e0 - Tablero: (Pendiente para E1 en Streamlit)

## Resumen en tres líneas
En esta primera entrega arrancamos **TDL Canastita**, un observatorio pensado para **cocinas y tiendas (Abarroteras) en Colima** (partiendo de la experiencia de Adolfo trabajando en el restaurante **Luisiana** y Andrea en abarroteras), así como para **abarroteras de barrio y comerciantes de fruta y verdura en tianguis**, que necesitan saber dónde y cuándo surtir insumos frescos antes de que suban por la inflación o el dólar en el corredor **Colima, Guadalajara y Morelia**. Dejamos corriendo nuestras dos fuentes en Python (el scraper ético del SNIIM de la Secretaría de Economía y la API oficial del SIE de Banxico) programadas diariamente en GitHub Actions, con **59 meses de serie histórica (2022-2026)** ya descargados en la capa bronce. Además, abrimos nuestros registros individuales de tiempo y defectos (PSP), la bitácora automática de ejecuciones y fijamos tres objetivos medibles de calidad para el Plan SQA de E1.

## Ingeniería de Datos
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| :--- | :--- | :--- |
| **Plan de recopilación** (20 pts): Fuentes con estructura, formato, frecuencia y análisis de robots.txt y términos de uso | [docs/E0/propuesta.md](propuesta.md) / [extractores/base.py](../../extractores/base.py) | Revisamos el robots.txt real del SNIIM y de las APIs; documentamos cómo ExtractorEtico bloqueó un primer servidor que tenía Disallow: / y lo cambiamos por la API oficial de Banxico |
| **Captura y serie histórica** (25 pts): Dos fuentes funcionando, una programada; serie de 36 periodos o más en la capa bronce | [extractores/sniim_canasta.py](../../extractores/sniim_canasta.py) / [extractores/macro_api.py](../../extractores/macro_api.py) / [.github/workflows/captura_diaria.yml](../../.github/workflows/captura_diaria.yml) / [data/bronce/](../../data/bronce/) | Descargamos 59 meses continuos (2022-01 a 2026-11) en data/bronce/: 13,647 precios históricos del SNIIM en las 3 plazas + 1,218 días de tipo de cambio FIX (Banxico SF43718) + 57 meses de INPC (Banxico SP1) |

## Análisis Estadístico
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| :--- | :--- | :--- |
| **Pregunta y cliente** (20 pts): Pregunta concreta con evidencia de la entrevista; cliente identificado y con motivo para pagar | [docs/E0/propuesta.md](propuesta.md) | Incluye el sondeo directo en cocina/compras del restaurante Luisiana en Colima y con comerciantes locales (la dueña de la abarrotera de la esquina y su hermano que vende fruta y verdura en el tianguis) |
| **Preguntas analíticas** (20 pts): Tres preguntas medibles: variable a pronosticar, factores del experimento y grupos a comparar | [docs/E0/propuesta.md](propuesta.md) | Definimos la variable a pronosticar en E1, el diseño factorial 2^3 por ruta ingeniería sobre nuestro propio extractor para E2, y la comparación de las 3 plazas (Colima, Guadalajara y Morelia) en 6 variables numéricas para el PCA y MANOVA de E3 |

## Calidad en los Sistemas de Información
| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
| :--- | :--- | :--- |
| **Arranque de calidad** (15 pts): Registros individuales de defectos y tiempo, bitácora de captura activa y tres objetivos medibles | [calidad/defectos-adolfo.csv](../../calidad/defectos-adolfo.csv) / [calidad/tiempo-adolfo.csv](../../calidad/tiempo-adolfo.csv) / [calidad/defectos-andrea.csv](../../calidad/defectos-andrea.csv) / [calidad/tiempo-andrea.csv](../../calidad/tiempo-andrea.csv) / [calidad/bitacora_captura.csv](../../calidad/bitacora_captura.csv) | Registros individuales abiertos usando los 10 tipos de defectos de PSP, bitácora real donde ya quedaron registradas las corridas exitosas y los errores corregidos en las pruebas, y los 3 objetivos medibles (Disponibilidad >= 95%, Completitud >= 95% y Cobertura >= 60% con 0 secretos) |

## Relatoría de etapa
En E0 el entregable principal es la propuesta en [docs/E0/propuesta.md](propuesta.md) (incluyendo en su sección 7 la declaración de uso de IA y lo que corregimos en esta semana). Las relatorías por etapa inician en E1 (`docs/relatoria-E1.md`).

## Issues de la entrega anterior
No aplica (es el arranque del proyecto en E0).
