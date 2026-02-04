import streamlit as st
import pandas as pd
import io
import os
import pickle
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTÉTICA "ZARA STYLE" ---
st.set_page_config(page_title="Gextia Factory | Atelier", layout="wide", page_icon="🖤")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1a1a1a;
    }

    /* Fondo de la App */
    [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF;
    }
    
    /* Sidebar Minimalista */
    [data-testid="stSidebar"] {
        background-color: #f4f4f4 !important;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Tarjetas de Producto Estilo Zara */
    .product-card {
        background-color: #ffffff;
        border: 1px solid #eeeeee;
        padding: 20px;
        border-radius: 0px; /* Zara usa bordes rectos o muy sutiles */
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }
    .product-card:hover {
        border-color: #1a1a1a;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .badge-ref {
        font-size: 10px;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #888;
        margin-bottom: 8px;
        display: block;
    }
    .product-title {
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        margin-bottom: 4px;
        color: #1a1a1a;
    }
    .product-sub {
        color: #666;
        font-size: 12px;
        margin-bottom: 12px;
    }

    /* Botones Estilo Botique */
    div.stButton > button {
        border-radius: 0px !important;
        border: 1px solid #1a1a1a !important;
        background-color: white !important;
        color: #1a1a1a !important;
        font-size: 11px !important;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        padding: 8px 20px !important;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #1a1a1a !important;
        color: white !important;
    }
    
    /* Input Fields */
    input {
        border-radius: 0px !important;
        border: 1px solid #e0e0e0 !important;
    }

    /* Tabs Personalizados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #eee;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 12px;
        font-weight: 400;
        letter-spacing: 1px;
        color: #999;
        text-transform: uppercase;
    }
    .stTabs [aria-selected="true"] {
        color: #1a1a1a !important;
        border-bottom: 2px solid #1a1a1a !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES DE PERSISTENCIA (Manteniendo tu lógica) ---
def guardar_progreso():
    datos = {'mesa': st.session_state.mesa, 'bom': st.session_state.bom, 'ultima_tanda': st.session_state.ultima_tanda}
    return pickle.dumps(datos)

def cargar_progreso(archivo_bytes):
    datos = pickle.loads(archivo_bytes)
    st.session_state.mesa = datos['mesa']
    st.session_state.bom = datos['bom']
    st.session_state.ultima_tanda = datos.get('ultima_tanda')

@st.cache_data
def load_data(file):
    if os.path.exists(file):
        df = pd.read_excel(file, engine='openpyxl')
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        for col in df.columns:
            df[col] = df[col].astype(str).apply(lambda x: x.replace('.0', '').strip()).replace('nan', '')
        return df
    return None

# --- 3. INICIALIZACIÓN ---
df_prendas = load_data('prendas.xlsx')
df_comp = load_data('componentes.xlsx')

if 'mesa' not in st.session_state: st.session_state.mesa = pd.DataFrame()
if 'bom' not in st.session_state: st.session_state.bom = pd.DataFrame()
if 'ultima_tanda' not in st.session_state: st.session_state.ultima_tanda = None

# --- 4. SIDEBAR (Elegante) ---
with st.sidebar:
    st.markdown("<h2 style='letter-spacing: 4px; font-weight: 300;'>GEXTIA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 10px; color: #888;'>FACTORY MANAGEMENT SYSTEM</p>", unsafe_allow_html=True)
    st.write("---")
    
    if not st.session_state.mesa.empty:
        total_m = int(st.session_state.mesa['Cant. a fabricar'].astype(float).sum())
        st.metric("PIEZAS EN PRODUCCIÓN", total_m)

    st.write("---")
    if not st.session_state.mesa.empty or not st.session_state.bom.empty:
        st.download_button("EXPORTAR BACKUP", data=guardar_progreso(), 
                           file_name=f"Gextia_{datetime.now().strftime('%d%m')}.pkt", use_container_width=True)
    
    archivo_subido = st.file_uploader("Restaurar .pkt", type=["pkt"], label_visibility="collapsed")
    if archivo_subido and st.button("RESTAURAR SESIÓN", use_container_width=True):
        cargar_progreso(archivo_subido.read())
        st.rerun()
    
    if st.button("LIMPIAR MESA DE TRABAJO", use_container_width=True):
        st.session_state.mesa = pd.DataFrame(); st.session_state.bom = pd.DataFrame(); st.rerun()

# --- 5. TABS ---
t1, t2, t3, t4 = st.tabs(["01 Catálogo", "02 Inyección", "03 Escandallo", "04 Suministros"])

# --- TAB 1: MESA DE CORTE (Visual Grid) ---
with t1:
    if df_prendas is not None:
        c_tit, c_search = st.columns([2, 2])
        with c_tit: st.markdown("<h3 style='font-weight: 300; letter-spacing: 1px;'>COLECCIÓN ACTUAL</h3>", unsafe_allow_html=True)
        with c_search: search = st.text_input("Buscador", label_visibility="collapsed", placeholder="Buscar prenda o referencia...")
        
        display_df = df_prendas.copy()
        if search:
            display_df = display_df[display_df['Referencia'].str.contains(search, case=False) | display_df['Nombre'].str.contains(search, case=False)]
        
        # Grid de Tarjetas Estilo eCommerce
        cols = st.columns(4)
        for idx, row in display_df.head(16).iterrows():
            with cols[idx % 4]:
                st.markdown(f"""
                    <div class="product-card">
                        <span class="badge-ref">REF: {row['Referencia']}</span>
                        <div class="product-title">{row['Nombre']}</div>
                        <div class="product-sub">{row['Color']} | Talla {row['Talla']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("Añadir a Mesa", key=f"cat_{row['Ean']}", use_container_width=True):
                    nuevos = pd.DataFrame([row])
                    nuevos['Sel'], nuevos['Cant. a fabricar'] = False, 0
                    st.session_state.mesa = pd.concat([st.session_state.mesa, nuevos]).drop_duplicates(subset=['Ean'])
                    st.toast(f"Añadido: {row['Referencia']}")
                    st.rerun()

    # Mesa de producción (Tabla de edición)
    if not st.session_state.mesa.empty:
        st.write("---")
        st.markdown("<h3 style='font-weight: 300; letter-spacing: 1px;'>ORDEN DE PRODUCCIÓN</h3>", unsafe_allow_html=True)
        
        # Header de acciones masivas
        c_all, c_ops = st.columns([1, 4])
        with c_all: 
            if st.checkbox("TODOS", key="master_sel") != st.session_state.get('p_sel', False):
                st.session_state.mesa['Sel'] = st.session_state.master_sel
                st.session_state['p_sel'] = st.session_state.master_sel
                st.rerun()
        with c_ops:
            mask = st.session_state.mesa['Sel'] == True
            b1, b2, b3 = st.columns(3)
            if b1.button("+ 10 UNIDADES"): st.session_state.mesa.loc[mask, 'Cant. a fabricar'] += 10; st.rerun()
            if b2.button("+ 50 UNIDADES"): st.session_state.mesa.loc[mask, 'Cant. a fabricar'] += 50; st.rerun()
            if b3.button("ELIMINAR SELECCIÓN"): st.session_state.mesa = st.session_state.mesa[~mask].reset_index(drop=True); st.rerun()

        # Filas de la mesa con diseño minimalista
        for idx, row in st.session_state.mesa.iterrows():
            with st.container():
                f1, f2, f3, f4 = st.columns([0.3, 1.5, 4, 1.5])
                if f1.checkbox(" ", value=row['Sel'], key=f"ch_{idx}_{row['Ean']}", label_visibility="collapsed") != row['Sel']:
                    st.session_state.mesa.at[idx, 'Sel'] = not row['Sel']; st.rerun()
                f2.markdown(f"<span style='font-family: monospace; font-size: 12px; color: #888;'>{row['Referencia']}</span>", unsafe_allow_html=True)
                f3.markdown(f"<span style='font-size: 13px;'>{row['Nombre']} — <b>{row['Color']} / {row['Talla']}</b></span>", unsafe_allow_html=True)
                nv = f4.number_input("Cant", min_value=0, value=int(row['Cant. a fabricar']), key=f"v_{idx}_{row['Ean']}", label_visibility="collapsed")
                if nv != row['Cant. a fabricar']: st.session_state.mesa.at[idx, 'Cant. a fabricar'] = nv; st.rerun()
                st.markdown("<hr style='margin: 5px 0; border: 0.1px solid #f9f9f9;'>", unsafe_allow_html=True)

# --- TAB 2: ASIGNACIÓN ---
with t2:
    if not st.session_state.mesa.empty:
        st.markdown("<h3 style='font-weight: 300;'>ASIGNACIÓN DE COMPONENTES</h3>", unsafe_allow_html=True)
        df_comp['Display'] = df_comp['Referencia'] + " - " + df_comp['Nombre']
        
        col_a, col_b = st.columns([3, 1])
        with col_a: 
            comp_sel = st.selectbox("MATERIAL / AVÍO:", df_comp['Display'].unique())
            row_c = df_comp[df_comp['Display'] == comp_sel].iloc[0]
        with col_b: 
            cons_inj = st.number_input("CONSUMO UNITARIO:", min_value=0.0, value=1.0, format="%.3f")
        
        st.write("---")
        st.markdown("<p style='font-size: 11px; letter-spacing: 1px; color: #888;'>FILTRAR DESTINO POR PROPIEDADES</p>", unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        with f1: r_ts = st.multiselect("Por Referencia:", sorted(st.session_state.mesa['Referencia'].unique()))
        with f2:
            d_t = st.session_state.mesa if not r_ts else st.session_state.mesa[st.session_state.mesa['Referencia'].isin(r_ts)]
            c_ts = st.multiselect("Por Color:", sorted(d_t['Color'].unique()))
        with f3:
            d_t2 = d_t if not c_ts else d_t[d_t['Color'].isin(c_ts)]
            t_ts = st.multiselect("Por Talla:", sorted(d_t2['Talla'].unique()))
            
        final_df = d_t2 if not t_ts else d_t2[d_t2['Talla'].isin(t_ts)]
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 15px; border-left: 3px solid black; font-size: 12px;'>Impacto: <b>{len(final_df)}</b> variantes serán actualizadas.</div>", unsafe_allow_html=True)
        
        st.write(" ")
        cb1, cb2 = st.columns([3, 1])
        with cb1:
            if st.button("CONFIRMAR ASIGNACIÓN A SELECCIÓN", use_container_width=True):
                t_id = datetime.now().strftime('%H%M%S')
                nuevas = pd.DataFrame({
                    'Nombre de producto': final_df['Nombre'], 'Cod Barras Variante': final_df['Ean'],
                    'Ref Prenda': final_df['Referencia'], 'Col Prenda': final_df['Color'], 'Tal Prenda': final_df['Talla'],
                    'Ref Comp': row_c.get('Referencia',''), 'Nom Comp': row_c.get('Nombre',''),
                    'Col Comp': row_c.get('Color',''), 'EAN Componente': row_c.get('Ean',''),
                    'Cantidad': cons_inj, 'Ud': row_c.get('Unidad de medida','Un'), 'Tanda': t_id
                })
                st.session_state.bom = pd.concat([st.session_state.bom, nuevas]).drop_duplicates()
                st.session_state.ultima_tanda = t_id
                st.toast("Componentes inyectados con éxito")
        with cb2:
            if st.session_state.ultima_tanda and st.button("DESHACER ÚLTIMO"):
                st.session_state.bom = st.session_state.bom[st.session_state.bom['Tanda'] != st.session_state.ultima_tanda]
                st.rerun()

# --- TAB 3: GEXTIA EXPORT ---
with t3:
    if not st.session_state.bom.empty:
        st.markdown("<h3 style='font-weight: 300;'>AUDITORÍA DE ESCANDALLO</h3>", unsafe_allow_html=True)
        df_edit = st.data_editor(st.session_state.bom, 
                                 column_order=['Ref Prenda', 'Col Prenda', 'Tal Prenda', 'Nom Comp', 'Cantidad', 'Ud'],
                                 use_container_width=True, hide_index=False)
        
        if st.button("GUARDAR EDICIÓN"):
            st.session_state.bom = df_edit
            st.success("BOM actualizado")
            
        st.write("---")
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            st.session_state.bom.to_excel(w, index=False)
        st.download_button("DESCARGAR EXCEL PARA GEXTIA", out.getvalue(), "Gextia_BOM.xlsx", use_container_width=True)

# --- TAB 4: COMPRAS ---
with t4:
    if not st.session_state.bom.empty:
        st.markdown("<h3 style='font-weight: 300;'>CÁLCULO DE SUMINISTROS</h3>", unsafe_allow_html=True)
        df_calc = st.session_state.bom.copy()
        df_m = st.session_state.mesa[['Ean', 'Cant. a fabricar']]
        df_calc = df_calc.merge(df_m, left_on='Cod Barras Variante', right_on='Ean', how='left')
        df_calc['Total Compra'] = df_calc['Cantidad'].astype(float) * df_calc['Cant. a fabricar'].astype(float)
        
        res = df_calc.groupby(['Ref Comp', 'Nom Comp', 'Col Comp', 'Ud'])['Total Compra'].sum().reset_index()
        st.dataframe(res[res['Total Compra'] > 0], use_container_width=True, hide_index=True)
        
