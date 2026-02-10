import pandas as pd
import json
import io
import streamlit as st

TARIFA_COL = "Tarifa Proveedor"

def cargar_excel_estatico(path, entidad):
    df = pd.read_excel(path)
    if TARIFA_COL not in df.columns:
        st.warning(
            f"⚠️ Atención: El archivo de {entidad} no contiene la columna '{TARIFA_COL}'. "
            f"Los costes serán 0 € por defecto.", icon="⚠️"
        )
        df[TARIFA_COL] = 0.0
    df[TARIFA_COL] = pd.to_numeric(df[TARIFA_COL], errors='coerce').fillna(0.0)
    return df

def guardar_backup_json(mesa, bom, ultima_tanda):
    data = {
        "mesa": mesa.to_dict(orient="records"),
        "bom": bom.to_dict(orient="records"),
        "ultima_tanda": ultima_tanda,
    }
    return io.BytesIO(json.dumps(data, indent=2, default=str).encode())

def cargar_backup_json(json_file):
    data = json.load(json_file)
    mesa = pd.DataFrame(data["mesa"])
    bom = pd.DataFrame(data["bom"])
    ultima_tanda = data.get("ultima_tanda", None)
    return mesa, bom, ultima_tanda