import streamlit as st
import pandas as pd
import io
import os
import pickle
import time
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTÉTICA SaaS ---
st.set_page_config(page_title="Gextia Factory Pro", layout="wide", page_icon="✂️")

st.markdown("""
    <style>
    /* Fondo y Tipografía */
    [data-testid="stAppViewContainer"] { background-color: #F8F9FB; }
    
    /* Sidebar Estilo Nav-Dark */
    [data-testid="stSidebar"] { background-color: #1E2533 !important; color: white; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] p { color: white !important; }
    
    /* Tarjetas de Producto */
    .product-card {
        background-color: white;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #EAECEF;
        margin-bottom: 10px;
        transition: transform 0.2s;
    }
    .product-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .badge-ref { background-color: #F1F3F5; padding: 3px 8px; border-radius: 4px; font-size: 10px; color: #666; font-family: monospace; }
    .product-title { font-weight: 600; font-size: 15px; margin-top: 8px; color: #1E2533; }
    .product-sub { color: #888; font-size: 12px; }
    
    /* Botones y Inputs */
    div.stButton > button {
        border-radius: 8px !important;
        font-size: 12px !important;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        color: #666;
    }
    .stTabs [aria-selected="true"] { background-color: white !important; color: #1E2533 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES DE PERSISTENCIA (Tu Lógica original) ---
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

# --- 4. SIDEBAR (Navegación y Backup) ---
with st.sidebar:
    st.markdown("## Gextia Factory")
    st.markdown("<p style='opacity:0.7;'>v3.0 Professional Edition</p>", unsafe_allow_html=True)
    st.write("---")
    
    # Métricas rápidas
    if not st.session_state.mesa.empty:
        total_m = int(st.session_state.mesa['Cant. a fabricar'].astype(float).sum())
        st.metric("TOTAL PIEZAS MESA", total_m)

    st.write("---")
    # Exportar / Importar
    if not st.session_state.mesa.empty or not st.session_state.bom.empty:
        st.download_button("📥 DESCARGAR BACKUP", data=guardar_progreso(), 
                           file_name=f"Backup_Gextia_{datetime.now().strftime('%H%M')}.pkt", use_container_width=True)
    
    archivo_subido = st.file_uploader("Restaurar .pkt", type=["pkt"])
    if archivo_subido and st.button("🔄 RESTAURAR", use_container_width=True):
        cargar_progreso(archivo_subido.read())
        st.rerun()
    
    if st.button("🗑️ LIMPIAR TODO", use_container_width=True, type="secondary"):
        st.session_state.mesa = pd.DataFrame(); st.session_state.bom = pd.DataFrame(); st.rerun()

# --- 5. TABS ---
t1, t2, t3, t4 = st.tabs(["🏗️ MESA DE TRABAJO", "🧬 ASIGNACIÓN", "📋 GEXTIA EXPORT", "📊 COMPRAS"])

# --- TAB 1: MESA DE CORTE (Grid Visual) ---
with t1:
    # Catálogo (Grid de Tarjetas)
    if df_prendas is not None:
        c_tit, c_search = st.columns([2, 2])
        with c_tit: st.markdown("### 🛍️ Catálogo de Prendas")
        with c_search: search = st.text_input("Buscar...", label_visibility="collapsed", placeholder="🔍 Buscar por referencia o nombre...")
        
        display_df = df_prendas.copy()
        if search:
            display_df = display_df[display_df['Referencia'].str.contains(search, case=False) | display_df['Nombre'].str.contains(search, case=False)]
        
        # Grid de Tarjetas
        st.write("Muestra de catálogo:")
        cols = st.columns(4)
        for idx, row in display_df.head(12).iterrows():
            with cols[idx % 4]:
                st.markdown(f"""
                    <div class="product-card">
                        <span class="badge-ref">{row['Referencia']}</span>
                        <div class="product-title">{row['Nombre']}</div>
                        <div class="product-sub">{row['Color']} / {row['Talla']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("Seleccionar", key=f"cat_{row['Ean']}"):
                    nuevos = pd.DataFrame([row])
                    nuevos['Sel'], nuevos['Cant. a fabricar'] = False, 0
                    st.session_state.mesa = pd.concat([st.session_state.mesa, nuevos]).drop_duplicates(subset=['Ean'])
                    st.toast(f"{row['Referencia']} añadida")
                    st.rerun()

    # Mesa de trabajo (Lógica de edición masiva)
    if not st.session_state.mesa.empty:
        st.write("---")
        st.markdown("### 🏗️ Producción en Curso")
        
        c_all, c_ops = st.columns([1, 4])
        with c_all: 
            if st.checkbox("TODO", key="master_sel") != st.session_state.get('p_sel', False):
                st.session_state.mesa['Sel'] = st.session_state.master_sel
                st.session_state['p_sel'] = st.session_state.master_sel
                st.rerun()
        with c_ops:
            mask = st.session_state.mesa['Sel'] == True
            b1, b2, b3 = st.columns(3)
            if b1.button("➕5 Sel."): st.session_state.mesa.loc[mask, 'Cant. a fabricar'] += 5; st.rerun()
            if b2.button("➕10 Sel."): st.session_state.mesa.loc[mask, 'Cant. a fabricar'] += 10; st.rerun()
            if b3.button("🗑️ Quitar Sel."): st.session_state.mesa = st.session_state.mesa[~mask].reset_index(drop=True); st.rerun()

        # Filas de la mesa
        for idx, row in st.session_state.mesa.iterrows():
            f1, f2, f3, f4 = st.columns([0.5, 2, 4, 1.5])
            if f1.checkbox(" ", value=row['Sel'], key=f"ch_{idx}_{row['Ean']}", label_visibility="collapsed") != row['Sel']:
                st.session_state.mesa.at[idx, 'Sel'] = not row['Sel']; st.rerun()
            f2.write(f"`{row['Referencia']}`")
            f3.write(f"**{row['Nombre']}** ({row['Color']} / {row['Talla']})")
            nv = f4.number_input("n", min_value=0, value=int(row['Cant. a fabricar']), key=f"v_{idx}_{row['Ean']}", label_visibility="collapsed")
            if nv != row['Cant. a fabricar']: st.session_state.mesa.at[idx, 'Cant. a fabricar'] = nv; st.rerun()

# --- TAB 2: ASIGNACIÓN (Lógica original de inyección) ---
with t2:
    if not st.session_state.mesa.empty:
        st.markdown("### 🧬 Inyección de Materiales")
        df_comp['Display'] = df_comp['Referencia'] + " - " + df_comp['Nombre']
        
        c_m, c_c = st.columns([3, 1])
        with c_m: 
            comp_sel = st.selectbox("Seleccionar Componente:", df_comp['Display'].unique())
            row_c = df_comp[df_comp['Display'] == comp_sel].iloc[0]
        with c_c: 
            cons_inj = st.number_input("Consumo Unitario:", min_value=0.0, value=1.0, format="%.3f")
        
        st.write("---")
        st.markdown("#### 🎯 Filtros de Destino")
        f1, f2, f3 = st.columns(3)
        with f1: r_ts = st.multiselect("Por Ref:", sorted(st.session_state.mesa['Referencia'].unique()))
        with f2:
            d_t = st.session_state.mesa if not r_ts else st.session_state.mesa[st.session_state.mesa['Referencia'].isin(r_ts)]
            c_ts = st.multiselect("Por Color:", sorted(d_t['Color'].unique()))
        with f3:
            d_t2 = d_t if not c_ts else d_t[d_t['Color'].isin(c_ts)]
            t_ts = st.multiselect("Por Talla:", sorted(d_t2['Talla'].unique()))
            
        final_df = d_t2 if not t_ts else d_t2[d_t2['Talla'].isin(t_ts)]
        st.info(f"Se asignará a **{len(final_df)}** variantes seleccionadas.")
        
        cb1, cb2 = st.columns([3, 1])
        with cb1:
            if st.button("✂️ ASIGNAR MATERIAL A SELECCIÓN", type="primary", use_container_width=True):
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
                st.toast("Inyección completada"); st.balloons()
        with cb2:
            if st.session_state.ultima_tanda and st.button("🔄 DESHACER"):
                st.session_state.bom = st.session_state.bom[st.session_state.bom['Tanda'] != st.session_state.ultima_tanda]
                st.rerun()

# --- TAB 3: GEXTIA EXPORT (Auditoría original) ---
with t3:
    if not st.session_state.bom.empty:
        st.markdown("### 📋 Auditoría de Escandallo")
        df_edit = st.data_editor(st.session_state.bom, 
                                 column_order=['Ref Prenda', 'Col Prenda', 'Tal Prenda', 'Nom Comp', 'Cantidad', 'Ud'],
                                 use_container_width=True, hide_index=False)
        
        if st.button("💾 GUARDAR CAMBIOS EN CANTIDADES"):
            st.session_state.bom = df_edit
            st.success("Cambios guardados.")
            
        st.write("---")
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            st.session_state.bom.to_excel(w, index=False)
        st.download_button("📥 DESCARGAR EXCEL PARA GEXTIA", out.getvalue(), "Gextia_BOM.xlsx", use_container_width=True)

# --- TAB 4: COMPRAS (Cálculo original) ---
with t4:
    if not st.session_state.bom.empty:
        st.markdown("### 📊 Necesidades de Suministro")
        df_calc = st.session_state.bom.copy()
        df_m = st.session_state.mesa[['Ean', 'Cant. a fabricar']]
        df_calc = df_calc.merge(df_m, left_on='Cod Barras Variante', right_on='Ean', how='left')
        df_calc['Total Compra'] = df_calc['Cantidad'].astype(float) * df_calc['Cant. a fabricar'].astype(float)
        
        res = df_calc.groupby(['Ref Comp', 'Nom Comp', 'Col Comp', 'Ud'])['Total Compra'].sum().reset_index()
        st.dataframe(res[res['Total Compra'] > 0], use_container_width=True, hide_index=True)
            
