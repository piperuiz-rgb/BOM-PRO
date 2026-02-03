import streamlit as st
import pandas as pd
import io
import os
import pickle
import time
from datetime import datetime

# --- 1. ESTÉTICA "ZARA" ---
st.set_page_config(page_title="GEXTIA FACTORY PRO", layout="wide")

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 1px solid #E0E0E0; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; color: #999 !important; font-weight: 300 !important;
        text-transform: uppercase; letter-spacing: 1px;
    }
    .stTabs [aria-selected="true"] { color: #000 !important; border-bottom: 2px solid #000 !important; }
    div.stButton > button {
        border-radius: 0px !important; border: 1px solid #000 !important;
        background-color: #FFF !important; color: #000 !important;
        text-transform: uppercase; letter-spacing: 1px; font-size: 11px !important;
    }
    div.stButton > button:hover { background-color: #000 !important; color: #FFF !important; }
    [data-testid="stSidebar"] { background-color: #F9F9F9 !important; border-right: 1px solid #EDEDED; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ESTADOS ---
if 'mesa' not in st.session_state: st.session_state.mesa = pd.DataFrame()
if 'bom' not in st.session_state: st.session_state.bom = pd.DataFrame()
if 'ultima_tanda' not in st.session_state: st.session_state.ultima_tanda = None

# --- 3. DATOS ---
@st.cache_data
def load_data(file):
    if os.path.exists(file):
        df = pd.read_excel(file, engine='openpyxl')
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        for col in df.columns:
            df[col] = df[col].astype(str).apply(lambda x: x.replace('.0', '').strip()).replace('nan', '')
        return df
    return None

df_prendas = load_data('prendas.xlsx')
df_comp = load_data('componentes.xlsx')

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='font-weight: 200; letter-spacing: 2px;'>GEXTIA PRO</h2>", unsafe_allow_html=True)
    if not st.session_state.mesa.empty:
        total = st.session_state.mesa['Cant. a fabricar'].astype(int).sum()
        st.metric("TOTAL PIEZAS", f"{total}")
    
    st.write("---")
    if st.button("LIMPIAR TODO"):
        st.session_state.mesa = pd.DataFrame()
        st.session_state.bom = pd.DataFrame()
        st.rerun()

# --- 5. TABS ---
t1, t2, t3, t4 = st.tabs(["MESA DE CORTE", "ASIGNACIÓN", "GEXTIA IMPORT", "COMPRAS"])

# --- TAB 1: MESA DE CORTE (Versión Data Editor) ---
with t1:
    if df_prendas is not None:
        c_sel, c_btn = st.columns([3, 1])
        with c_sel: refs = st.multiselect("BUSCAR:", sorted(df_prendas['Referencia'].unique()))
        with c_btn:
            st.write(" ")
            if st.button("CARGAR A MESA", use_container_width=True):
                nuevos = df_prendas[df_prendas['Referencia'].isin(refs)].copy()
                nuevos['Sel'] = False
                nuevos['Cant. a fabricar'] = 0
                st.session_state.mesa = pd.concat([st.session_state.mesa, nuevos]).drop_duplicates(subset=['Ean'])
                st.rerun()

    if not st.session_state.mesa.empty:
        st.write("### Planificación")
        # Operaciones masivas
        c_ops, c_val = st.columns([2, 2])
        with c_ops:
            op = st.selectbox("Acción masiva (filas marcadas):", ["---", "+5 Unidades", "+10 Unidades", "Eliminar"])
            if st.button("Ejecutar Acción"):
                mask = st.session_state.mesa['Sel'] == True
                if op == "+5 Unidades": st.session_state.mesa.loc[mask, 'Cant. a fabricar'] = st.session_state.mesa.loc[mask, 'Cant. a fabricar'].astype(int) + 5
                elif op == "+10 Unidades": st.session_state.mesa.loc[mask, 'Cant. a fabricar'] = st.session_state.mesa.loc[mask, 'Cant. a fabricar'].astype(int) + 10
                elif op == "Eliminar": st.session_state.mesa = st.session_state.mesa[~mask]
                st.toast(f"Proceso {op} finalizado")
                st.rerun()

        # LA TABLA (Data Editor)
        # El data editor permite marcar todas las filas con un solo click en el encabezado
        df_mesa_edit = st.data_editor(
            st.session_state.mesa,
            column_order=['Sel', 'Referencia', 'Nombre', 'Color', 'Talla', 'Cant. a fabricar'],
            column_config={
                "Sel": st.column_config.CheckboxColumn("Selección", default=False),
                "Cant. a fabricar": st.column_config.NumberColumn("Cantidad", min_value=0, step=1),
                "Referencia": st.column_config.Column(disabled=True),
                "Nombre": st.column_config.Column(disabled=True),
                "Color": st.column_config.Column(disabled=True),
                "Talla": st.column_config.Column(disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            key="editor_mesa"
        )
        
        # Sincronizamos cambios del editor al estado
        if not df_mesa_edit.equals(st.session_state.mesa):
            st.session_state.mesa = df_mesa_edit
            st.rerun()

# --- TAB 2: ASIGNACIÓN ---
with t2:
    if not st.session_state.mesa.empty:
        df_comp['Display'] = df_comp['Referencia'] + " | " + df_comp['Nombre']
        col_a, col_b = st.columns([3, 1])
        with col_a: 
            comp_sel = st.selectbox("MATERIAL:", df_comp['Display'].unique())
            r_c = df_comp[df_comp['Display'] == comp_sel].iloc[0]
        with col_b: 
            cons = st.number_input("CONSUMO:", min_value=0.0, value=1.0, format="%.3f")
        
        st.write("---")
        g1, g2, g3 = st.columns(3)
        with g1: f_ref = st.multiselect("FILTRAR REF:", sorted(st.session_state.mesa['Referencia'].unique()))
        with g2:
            d_aux = st.session_state.mesa if not f_ref else st.session_state.mesa[st.session_state.mesa['Referencia'].isin(f_ref)]
            f_col = st.multiselect("FILTRAR COLOR:", sorted(d_aux['Color'].unique()))
        with g3:
            d_aux2 = d_aux if not f_col else d_aux[d_aux['Color'].isin(f_col)]
            f_tal = st.multiselect("FILTRAR TALLA:", sorted(d_aux2['Talla'].unique()))
        
        target = d_aux2 if not f_tal else d_aux2[d_aux2['Talla'].isin(f_tal)]
        st.info(f"Variantes destino: {len(target)}")
        
        if st.button("INYECTAR MATERIAL", use_container_width=True):
            t_id = datetime.now().strftime('%H%M%S')
            nuevas = pd.DataFrame({
                'Nombre de producto': target['Nombre'], 'Cod Barras Variante': target['Ean'],
                'Ref Prenda': target['Referencia'], 'Col Prenda': target['Color'], 'Tal Prenda': target['Talla'],
                'Cantidad producto final': 1, 'Ref Comp': r_c['Referencia'], 'Nom Comp': r_c['Nombre'],
                'Col Comp': r_c.get('Color','-'), 'EAN Componente': r_c['Ean'],
                'Cantidad': cons, 'Ud': r_c.get('Unidad de medida','Un'),
                'Tipo de lista de material': 'Fabricación', 'Subcontratista': '', 'Tanda': t_id
            })
            st.session_state.bom = pd.concat([st.session_state.bom, nuevas]).drop_duplicates()
            st.session_state.ultima_tanda = t_id
            with st.status("Asignando...") as s:
                time.sleep(0.4)
                s.update(label="Material asignado", state="complete")
            st.rerun()

# --- TAB 3: GEXTIA ---
with t3:
    if not st.session_state.bom.empty:
        c_h, c_u = st.columns([4, 1])
        with c_h: st.write("### Escandallo Final")
        with c_u:
            if st.session_state.ultima_tanda and st.button("DESHACER"):
                st.session_state.bom = st.session_state.bom[st.session_state.bom['Tanda'] != st.session_state.ultima_tanda]
                st.session_state.ultima_tanda = None
                st.rerun()

        df_bom_edit = st.data_editor(st.session_state.bom, 
                                     column_order=['Ref Prenda', 'Col Prenda', 'Tal Prenda', 'Nom Comp', 'Cantidad', 'Ud'],
                                     use_container_width=True, hide_index=True)
        
        st.write("---")
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            df_bom_edit.drop(columns=['Tanda'], errors='ignore').to_excel(w, index=False)
        st.download_button("DESCARGAR GEXTIA EXCEL", out.getvalue(), "Gextia_BOM.xlsx", use_container_width=True)

# --- TAB 4: COMPRAS ---
with t4:
    if not st.session_state.bom.empty:
        st.write("### Necesidades Totales")
        calc = st.session_state.bom.copy()
        mesa_v = st.session_state.mesa[['Ean', 'Cant. a fabricar']]
        calc = calc.merge(mesa_v, left_on='Cod Barras Variante', right_on='Ean', how='left')
        calc['Total'] = calc['Cantidad'].astype(float) * calc['Cant. a fabricar'].astype(float)
        res = calc.groupby(['Ref Comp', 'Nom Comp', 'Ud'])['Total'].sum().reset_index()
        st.dataframe(res[res['Total'] > 0], use_container_width=True, hide_index=True)
        
