import streamlit as st
import pandas as pd
from data import cargar_excel_estatico, guardar_backup_json, cargar_backup_json
from logic import (
    ui_tab_mesa_de_corte,
    calcular_lista_compra,
    ui_tab_exportar_importador
)

st.set_page_config(page_title="BOM Generator", layout="wide")

# ====== CARGA DE DATOS ======
st.sidebar.header("📁 Excels de catálogo (estructura fija)")
if 'df_prendas' not in st.session_state:
    st.session_state['df_prendas'] = cargar_excel_estatico("prendas.xlsx", "prendas")
if 'df_comp' not in st.session_state:
    st.session_state['df_comp'] = cargar_excel_estatico("componentes.xlsx", "componentes")

# ====== ESTADO DE SESIÓN ======
for k in ['mesa', 'bom', 'ultima_tanda']:
    if k not in st.session_state:
        st.session_state[k] = pd.DataFrame() if k != 'ultima_tanda' else None

# ====== PANEL LATERAL DE BACKUP ======
st.sidebar.header("💾 Backup de sesión")
if st.sidebar.button("Guardar backup"):
    st.sidebar.download_button(
        "Descargar backup (.json)",
        guardar_backup_json(
            st.session_state['mesa'],
            st.session_state['bom'],
            st.session_state['ultima_tanda']
        ),
        file_name="backup_gextia.json"
    )

archivo_backup = st.sidebar.file_uploader("Restaurar backup (.json)", type=["json"])
if archivo_backup and st.sidebar.button("Restaurar backup"):
    mesa, bom, ultima_tanda = cargar_backup_json(archivo_backup)
    st.session_state['mesa'], st.session_state['bom'], st.session_state['ultima_tanda'] = mesa, bom, ultima_tanda
    st.experimental_rerun()

# ====== UI PRINCIPAL ======
tabs = st.tabs([
    "🏗️ MESA DE CORTE",
    "🧬 ASIGNACIÓN",
    "📋 AUDITORÍA/EXPORT",
    "📊 LISTA DE COMPRA"
])

with tabs[0]:
    ui_tab_mesa_de_corte(st)

# Tab de auditoría/exportación Gextia (usa tu lógica de generación de BOM antes)
with tabs[2]:
    ui_tab_exportar_importador(st)

with tabs[3]:
    if not st.session_state['bom'].empty:
        calcular_lista_compra(
            st.session_state['bom'],
            st.session_state['mesa'],
            st.session_state['df_comp']
        )
    else:
        st.info("Primero genera el BOM para poder calcular la lista y el coste total.")