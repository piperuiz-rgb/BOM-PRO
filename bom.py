import streamlit as st
import pandas as pd
import io
import os
import pickle
import time
from datetime import datetime

# --- 1. ESTÉTICA "ZARA" RESTAURADA ---
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

# --- 2. LÓGICA DE ESTADO ---
if 'mesa' not in st.session_state: st.session_state.mesa = pd.DataFrame()
if 'bom' not in st.session_state: st.session_state.bom = pd.DataFrame()
if 'master_sel' not in st.session_state: st.session_state.master_sel = False

def toggle_master():
    # Esta función fuerza el cambio en todas las filas
    st.session_state.mesa['Sel'] = st.session_state.master_sel

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
    st.markdown("<h2 style='font-weight: 200;'>SISTEMA</h2>", unsafe_allow_html=True)
    if not st.session_state.mesa.empty:
        total = st.session_state.mesa['Cant. a fabricar'].astype(int).sum()
        st.metric("TOTAL PLANIFICADO", f"{total} pzs")
    
    if st.button("LIMPIAR SESIÓN GLOBAL"):
        st.session_state.mesa = pd.DataFrame()
        st.session_state.bom = pd.DataFrame()
        st.rerun()

# --- 5. TABS ---
t1, t2, t3, t4 = st.tabs(["MESA DE CORTE", "ASIGNACIÓN", "GEXTIA IMPORT", "COMPRAS"])

# --- TAB 1: MESA DE CORTE (Diseño Visual Original) ---
with t1:
    if df_prendas is not None:
        c_sel, c_btn = st.columns([3, 1])
        with c_sel: refs = st.multiselect("AÑADIR REFERENCIAS:", sorted(df_prendas['Referencia'].unique()))
        with c_btn:
            st.write(" ")
            if st.button("CARGAR A MESA", use_container_width=True):
                nuevos = df_prendas[df_prendas['Referencia'].isin(refs)].copy()
                nuevos['Sel'] = False
                nuevos['Cant. a fabricar'] = 0
                st.session_state.mesa = pd.concat([st.session_state.mesa, nuevos]).drop_duplicates(subset=['Ean'])
                st.toast("Mesa actualizada")
                st.rerun()

    if not st.session_state.mesa.empty:
        st.write("---")
        c1, c2, c3 = st.columns([1, 1.5, 3])
        
        with c1:
            # CHECKBOX MAESTRO: Usa on_change para disparar la función toggle_master
            st.checkbox("SELECCIONAR TODO", key="master_sel", on_change=toggle_master)

        with c2:
            talla_f = st.selectbox("FILTRAR TALLA:", ["Todas"] + sorted(st.session_state.mesa['Talla'].unique().tolist()))
        
        with c3:
            mask = st.session_state.mesa['Sel'] == True
            if talla_f != "Todas": mask = mask & (st.session_state.mesa['Talla'] == talla_f)
            
            b_a, b_b, b_c = st.columns(3)
            if b_a.button("+ 5 UNID."):
                st.session_state.mesa.loc[mask, 'Cant. a fabricar'] = st.session_state.mesa.loc[mask, 'Cant. a fabricar'].astype(int) + 5
                st.toast("Añadidas 5 unidades a la selección", icon="📈")
                st.rerun()
            if b_b.button("+ 10 UNID."):
                st.session_state.mesa.loc[mask, 'Cant. a fabricar'] = st.session_state.mesa.loc[mask, 'Cant. a fabricar'].astype(int) + 10
                st.toast("Añadidas 10 unidades a la selección", icon="📈")
                st.rerun()
            if b_c.button("ELIMINAR"):
                st.session_state.mesa = st.session_state.mesa[~mask].reset_index(drop=True)
                st.rerun()

        st.write("---")
        # Listado de filas (Estilo Visual)
        for idx, row in st.session_state.mesa.iterrows():
            f1, f2, f3, f4 = st.columns([0.5, 2, 4, 1.5])
            
            # Checkbox individual. Importante: no usamos 'key' dinámico aquí para evitar desincronización
            if f1.checkbox(" ", value=row['Sel'], key=f"ch_{row['Ean']}_{idx}"):
                if not row['Sel']:
                    st.session_state.mesa.at[idx, 'Sel'] = True
                    st.rerun()
            else:
                if row['Sel']:
                    st.session_state.mesa.at[idx, 'Sel'] = False
                    st.rerun()
            
            f2.write(f"Ref: **{row['Referencia']}**")
            f3.write(f"{row['Nombre']} — {row['Color']} / Talla {row['Talla']}")
            
            new_val = f4.number_input("CANT", min_value=0, value=int(row['Cant. a fabricar']), key=f"n_{row['Ean']}_{idx}", label_visibility="collapsed")
            if new_val != row['Cant. a fabricar']:
                st.session_state.mesa.at[idx, 'Cant. a fabricar'] = new_val
                st.rerun()

# --- TAB 2: ASIGNACIÓN ---
with t2:
    if not st.session_state.mesa.empty:
        df_comp['Display'] = df_comp['Referencia'] + " | " + df_comp['Nombre']
        col_a, col_b = st.columns([3, 1])
        with col_a: 
            comp = st.selectbox("COMPONENTE:", df_comp['Display'].unique())
            r_c = df_comp[df_comp['Display'] == comp].iloc[0]
        with col_b: 
            cons = st.number_input("CONSUMO:", min_value=0.0, value=1.0, format="%.3f")
        
        st.write("---")
        if st.button("EJECUTAR ASIGNACIÓN A TODA LA MESA", use_container_width=True):
            with st.status("Asignando materiales...") as status:
                t_id = datetime.now().strftime('%H%M%S')
                target = st.session_state.mesa.copy()
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
                time.sleep(0.5)
                status.update(label="Asignación completada", state="complete")
            st.rerun()

# --- TAB 3: GEXTIA (Editor para revisión final) ---
with t3:
    if not st.session_state.bom.empty:
        c_h, c_u = st.columns([4, 1])
        with c_h: st.write("### Auditoría de Materiales")
        with c_u:
            if st.button("🔄 DESHACER"):
                st.session_state.bom = st.session_state.bom[st.session_state.bom['Tanda'] != st.session_state.ultima_tanda]
                st.toast("Acción revertida")
                st.rerun()

        df_final = st.data_editor(st.session_state.bom, 
                                 column_order=['Ref Prenda', 'Col Prenda', 'Tal Prenda', 'Nom Comp', 'Cantidad', 'Ud'],
                                 use_container_width=True, hide_index=True)
        
        st.write("---")
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            df_final.drop(columns=['Tanda'], errors='ignore').to_excel(w, index=False)
        st.download_button("DESCARGAR EXCEL GEXTIA", out.getvalue(), "Gextia_BOM.xlsx")

# --- TAB 4: COMPRAS ---
with t4:
    if not st.session_state.bom.empty:
        st.write("### Necesidades de Compra")
        calc = st.session_state.bom.copy()
        mesa_v = st.session_state.mesa[['Ean', 'Cant. a fabricar']]
        calc = calc.merge(mesa_v, left_on='Cod Barras Variante', right_on='Ean', how='left')
        calc['Total'] = calc['Cantidad'].astype(float) * calc['Cant. a fabricar'].astype(float)
        res = calc.groupby(['Ref Comp', 'Nom Comp', 'Ud'])['Total'].sum().reset_index()
        st.dataframe(res[res['Total'] > 0], use_container_width=True, hide_index=True)
        
