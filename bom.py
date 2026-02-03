import streamlit as st
import pandas as pd
import io
import os
import pickle
import time
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTÉTICA "ZARA" ---
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
    
    /* Botones Estilo Industrial */
    div.stButton > button {
        border-radius: 0px !important; border: 1px solid #000 !important;
        background-color: #FFF !important; color: #000 !important;
        text-transform: uppercase; letter-spacing: 1px; font-size: 11px !important;
        padding: 8px 20px !important;
    }
    div.stButton > button:hover { background-color: #000 !important; color: #FFF !important; }
    
    /* Notificaciones sutiles */
    .stStatusWidget { border-radius: 0px !important; border: 1px solid #E0E0E0 !important; }
    [data-testid="stSidebar"] { background-color: #F9F9F9 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. PERSISTENCIA ---
def guardar_progreso():
    return pickle.dumps({'mesa': st.session_state.mesa, 'bom': st.session_state.bom, 'ultima_tanda': st.session_state.ultima_tanda})

def cargar_progreso(archivo_bytes):
    datos = pickle.loads(archivo_bytes)
    st.session_state.mesa = datos['mesa']
    st.session_state.bom = datos['bom']
    st.session_state.ultima_tanda = datos.get('ultima_tanda')

# --- 3. INICIALIZACIÓN ---
if 'mesa' not in st.session_state: st.session_state.mesa = pd.DataFrame()
if 'bom' not in st.session_state: st.session_state.bom = pd.DataFrame()
if 'ultima_tanda' not in st.session_state: st.session_state.ultima_tanda = None

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
        st.download_button("EXPORTAR BACKUP", data=guardar_progreso(), file_name=f"Sesion_{datetime.now().strftime('%H%M')}.pkt")
    
    st.write("---")
    archivo = st.file_uploader("CARGAR AVANCE", type=["pkt"])
    if archivo and st.button("RESTAURAR"):
        cargar_progreso(archivo.read())
        st.toast("SESIÓN RESTAURADA", icon="📋")
        st.rerun()
    
    if st.button("LIMPIAR SESIÓN"):
        st.session_state.mesa = pd.DataFrame()
        st.session_state.bom = pd.DataFrame()
        st.rerun()

# --- 5. TABS ---
t1, t2, t3, t4 = st.tabs(["MESA DE CORTE", "ASIGNACIÓN", "GEXTIA IMPORT", "COMPRAS"])

# --- TAB 1: MESA DE CORTE ---
with t1:
    if df_prendas is not None:
        c_sel, c_btn = st.columns([3, 1])
        with c_sel: 
            refs = st.multiselect("SELECCIONAR REFERENCIAS:", sorted(df_prendas['Referencia'].unique()))
        with c_btn:
            st.write(" ")
            if st.button("AÑADIR A MESA"):
                nuevos = df_prendas[df_prendas['Referencia'].isin(refs)].copy()
                nuevos['Sel'] = False
                nuevos['Cant. a fabricar'] = 0
                st.session_state.mesa = pd.concat([st.session_state.mesa, nuevos]).drop_duplicates(subset=['Ean'])
                with st.status("Procesando...", expanded=False) as s:
                    time.sleep(0.5)
                    s.update(label="Mesa actualizada con éxito", state="complete", expanded=False)
                st.rerun()

    if not st.session_state.mesa.empty:
        st.write("---")
        c1, c2, c3 = st.columns([1, 1.5, 3])
        
        with c1:
            m_sel = st.checkbox("SELECCIONAR TODO", key="master_check")
            if m_sel != st.session_state.get('prev_master', False):
                st.session_state.mesa['Sel'] = m_sel
                st.session_state['prev_master'] = m_sel
                st.rerun()

        with c2:
            talla_f = st.selectbox("FILTRAR TALLA:", ["Todas"] + sorted(st.session_state.mesa['Talla'].unique().tolist()))
        
        with c3:
            mask = st.session_state.mesa['Sel'] == True
            if talla_f != "Todas": mask = mask & (st.session_state.mesa['Talla'] == talla_f)
            
            b_a, b_b, b_c = st.columns(3)
            if b_a.button("+ 5 UNID."):
                st.session_state.mesa.loc[mask, 'Cant. a fabricar'] = st.session_state.mesa.loc[mask, 'Cant. a fabricar'].astype(int) + 5
                st.toast("Cantidades actualizadas", icon="📈")
                st.rerun()
            if b_b.button("+ 10 UNID."):
                st.session_state.mesa.loc[mask, 'Cant. a fabricar'] = st.session_state.mesa.loc[mask, 'Cant. a fabricar'].astype(int) + 10
                st.toast("Cantidades actualizadas", icon="📈")
                st.rerun()
            if b_c.button("ELIMINAR"):
                st.session_state.mesa = st.session_state.mesa[~mask].reset_index(drop=True)
                st.rerun()

        st.write("---")
        for idx, row in st.session_state.mesa.iterrows():
            f1, f2, f3, f4 = st.columns([0.5, 2, 4, 1.5])
            new_sel = f1.checkbox(" ", value=row['Sel'], key=f"check_{idx}_{row['Ean']}")
            if new_sel != row['Sel']:
                st.session_state.mesa.at[idx, 'Sel'] = new_sel
                st.rerun()
            
            f2.write(f"Ref: **{row['Referencia']}**")
            f3.write(f"{row['Nombre']} — {row['Color']} / Talla {row['Talla']}")
            
            new_val = f4.number_input("CANT", min_value=0, value=int(row['Cant. a fabricar']), key=f"num_{idx}_{row['Ean']}", label_visibility="collapsed")
            if new_val != row['Cant. a fabricar']:
                st.session_state.mesa.at[idx, 'Cant. a fabricar'] = new_val
                st.rerun()

# --- TAB 2: ASIGNACIÓN ---
with t2:
    if not st.session_state.mesa.empty:
        df_comp['Display'] = df_comp['Referencia'] + " | " + df_comp['Nombre']
        col_a, col_b = st.columns([3, 1])
        with col_a: 
            comp = st.selectbox("MATERIAL A ASIGNAR:", df_comp['Display'].unique())
            r_c = df_comp[df_comp['Display'] == comp].iloc[0]
        with col_b: 
            cons = st.number_input("CONSUMO UNIT:", min_value=0.0, value=1.0, format="%.3f")
        
        st.write("---")
        g1, g2, g3 = st.columns(3)
        with g1: f_ref = st.multiselect("FILTRAR REF PRENDA:", sorted(st.session_state.mesa['Referencia'].unique()))
        with g2:
            d_aux = st.session_state.mesa if not f_ref else st.session_state.mesa[st.session_state.mesa['Referencia'].isin(f_ref)]
            f_col = st.multiselect("FILTRAR COLOR PRENDA:", sorted(d_aux['Color'].unique()))
        with g3:
            d_aux2 = d_aux if not f_col else d_aux[d_aux['Color'].isin(f_col)]
            f_tal = st.multiselect("FILTRAR TALLA PRENDA:", sorted(d_aux2['Talla'].unique()))
        
        target = d_aux2 if not f_tal else d_aux2[d_aux2['Talla'].isin(f_tal)]
        st.info(f"Variantes destino: {len(target)}")
        
        if st.button("EJECUTAR ASIGNACIÓN", use_container_width=True):
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
            with st.status("Generando escandallo...") as s:
                time.sleep(0.6)
                s.update(label="Material inyectado correctamente", state="complete")
            st.rerun()

# --- TAB 3: GEXTIA ---
with t3:
    if not st.session_state.bom.empty:
        c_title, c_undo = st.columns([4, 1])
        with c_title: st.subheader("REVISIÓN DE ESCANDALLO")
        with c_undo:
            if st.session_state.ultima_tanda:
                if st.button("🔄 DESHACER", use_container_width=True):
                    st.session_state.bom = st.session_state.bom[st.session_state.bom['Tanda'] != st.session_state.ultima_tanda]
                    st.session_state.ultima_tanda = None
                    st.toast("Última acción revertida")
                    st.rerun()

        df_e = st.data_editor(st.session_state.bom, 
                              column_order=['Ref Prenda', 'Col Prenda', 'Tal Prenda', 'Nom Comp', 'Cantidad', 'Ud'],
                              use_container_width=True, hide_index=True)
        
        if st.button("GUARDAR CAMBIOS MANUALES"):
            st.session_state.bom = df_e
            st.toast("Cambios guardados", icon="💾")
            
        st.write("---")
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            st.session_state.bom.drop(columns=['Tanda'], errors='ignore').to_excel(w, index=False)
        st.download_button("DESCARGAR EXCEL GEXTIA", out.getvalue(), "Gextia_BOM.xlsx")

# --- TAB 4: COMPRAS ---
with t4:
    if not st.session_state.bom.empty:
        st.subheader("REQUERIMIENTOS DE COMPRA")
        calc = st.session_state.bom.copy()
        mesa_v = st.session_state.mesa[['Ean', 'Cant. a fabricar']]
        calc = calc.merge(mesa_v, left_on='Cod Barras Variante', right_on='Ean', how='left')
        calc['Total'] = calc['Cantidad'].astype(float) * calc['Cant. a fabricar'].astype(float)
        
        res = calc.groupby(['Ref Comp', 'Nom Comp', 'Ud'])['Total'].sum().reset_index()
        st.dataframe(res[res['Total'] > 0], use_container_width=True, hide_index=True)
                
