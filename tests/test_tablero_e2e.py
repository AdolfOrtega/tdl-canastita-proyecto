"""
tests/test_tablero_e2e.py
Pruebas funcionales End-to-End (E2E) del tablero interactivo Streamlit usando AppTest.
Valida renderizado sin excepciones de las 5 pestanas, filtros de mercado, pronosticos
y mapa geoespacial DENUE-INEGI.
"""

from pathlib import Path
from streamlit.testing.v1 import AppTest

RUTA_APP = Path(__file__).resolve().parent.parent / "tablero" / "app.py"


def test_tablero_renderiza_5_pestanas_sin_excepciones():
    """Verifica que el tablero cargue todas sus vistas, KPIs y selectores sin errores."""
    at = AppTest.from_file(str(RUTA_APP), default_timeout=30)
    at.run()

    assert len(at.exception) == 0, f"Excepciones en renderizado inicial: {at.exception}"
    assert len(at.tabs) == 5
    assert len(at.metric) >= 20


def test_tablero_interaccion_filtros_y_mapa():
    """Prueba cambios interactivos de moneda, plazas, productos y categorias DENUE."""
    at = AppTest.from_file(str(RUTA_APP), default_timeout=30)
    at.run()

    # Cambiar moneda a USD y verificar estabilidad
    at.sidebar.radio[0].set_value("Dólares Americanos (USD)").run()
    assert len(at.exception) == 0

    # Cambiar plaza en barra lateral
    for plaza in ["Todas las Plazas (Comparativo)", "Guadalajara", "Morelia", "Colima"]:
        at.sidebar.selectbox[0].set_value(plaza).run()
        assert len(at.exception) == 0

    # Probar los 3 insumos en Laboratorio de Pronosticos (Pestana 2)
    for prod in ["Jitomate Saladette", "Limon con semilla #5", "Aguacate Hass"]:
        at.selectbox[0].set_value(prod).run()
        assert len(at.exception) == 0

    # Probar ciudades y categorias en Mapa Geoespacial DENUE (Pestana 4)
    for ciudad_geo in ["Colima", "Guadalajara", "Morelia"]:
        at.selectbox[1].set_value(ciudad_geo).run()
        assert len(at.exception) == 0
        for cat in at.selectbox[2].options[:2]:
            at.selectbox[2].set_value(cat).run()
            assert len(at.exception) == 0
