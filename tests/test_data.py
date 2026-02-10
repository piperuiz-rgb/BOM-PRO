import pandas as pd
from data import cargar_excel_estatico

def test_cargar_excel_estatico(tmp_path):
    # Crear Excel de prueba
    df = pd.DataFrame({
        "Referencia": ["R1"],
        "Nombre": ["Camiseta"],
        "Color": ["Rojo"],
        "Talla": ["M"],
        "Tarifa Proveedor": [5.0]
    })
    fichero = tmp_path / "prendas.xlsx"
    df.to_excel(fichero, index=False)
    df_cargado = cargar_excel_estatico(fichero, "prendas")
    assert "Tarifa Proveedor" in df_cargado.columns
    assert float(df_cargado["Tarifa Proveedor"][0]) == 5.0
