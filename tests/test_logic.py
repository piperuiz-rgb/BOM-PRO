import pandas as pd
from logic import calcular_lista_compra

def test_calculo_lista_compra_basico():
    mesa = pd.DataFrame({
        "Referencia": ["R1"],
        "Color": ["Rojo"],
        "Talla": ["M"],
        "Cant. a fabricar": [10]
    })
    bom = pd.DataFrame({
        "Ref Prenda": ["R1"],
        "Col Prenda": ["Rojo"],
        "Tal Prenda": ["M"],
        "Ref Comp": ["C1"],
        "Nom Comp": ["Botón"],
        "Col Comp": ["Blanco"],
        "Cantidad": [2],
        "Ud": ["ud"]
    })
    df_comp = pd.DataFrame({
        "Referencia": ["C1"],
        "Tarifa Proveedor": [0.5]
    })
    out, total = calcular_lista_compra(bom, mesa, df_comp)
    assert total == 10 * 2 * 0.5  # 10 camisetas * 2 botones * 0.5 €/botón = 10 €
