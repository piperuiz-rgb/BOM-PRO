import streamlit as st
import pandas as pd
import io
import os
import time
from datetime import datetime

# --- 1. ESTÉTICA "SaaS MODERN" (Basada en la imagen) ---
st.set_page_config(page_title="Gextia Factory Pro", layout="wide")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #F8F9FB; }
    [data-testid="stSidebar"] { background-color: #1E2533 !important; color: white; }
    
    /* Estilo de Tarjetas */
    .product-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #EAECEF;
        margin-bottom: 10px;
        min-height: 180px;
    }
    .badge-ref { background-color: #F1F3F5; padding: 4px 8px; border-radius: 4px; font-size: 11px; color: #666; font-family: monospace; }
    .product-title { font-weight: 600; font-size: 16px; margin-top: 10px; color: #1E2533; display: block; }
    .product-sub { color: #888; font-size: 12px; margin-bottom: 10px; }
    
    /* Botones SaaS */
    div.stButton > button {
        border-radius: 8px !important;
        background-color: #FFF !important;
        color: #1E2533 !important;
        border: 1px solid #EAECEF !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div.stButton > button:hover { background-color: #1E2533 !important; color: white !important; }
    
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { font-weight: 500; color: #666; }
    .stTabs [aria-selected="true"] { color: #1E2533 !important; border-bottom-color: #1E2533 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE DATOS ORIGINAL ---
if 'mesa' not in st.session_state: st.session_state.mesa = pd.DataFrame()
if 'bom' not in st.session_state: st.session_state.bom = pd.DataFrame()

@st.cache_data
def load_data(file):
    if os.path.exists(file):
        df = pd.read_excel(file, engine='openpyxl')
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        return df
    return None

df_prendas = load_data('prendas.xlsx')
df_comp = load_data('componentes.xlsx')

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='color:white;'>Gextia</h2><p style='color:#888; margin-top:-15px;'>Factory Pro</p>", unsafe_allow_html=True)
    st.write("---")
    if not st.session_state.mesa.empty:
        total_unidades = st.session_state.mesa['Cant. a fabricar'].sum()
        st.metric("UNIDADES EN MESA", int(total_unidades))
    
    st.write(" ")
    if st.button("🗑️ LIMPIAR SESIÓN"):
        st.session_state.mesa = pd.DataFrame()
        st.session_state.bom = pd.DataFrame()
        st.rerun()

# --- 4. CUERPO PRINCIPAL (TABS) ---
t1, t2, t3, t4 = st.tabs(["🛍️ CATÁLOGO / MESA", "🔗 ASIGNACIÓN", "📦 GEXTIA IMPORT", "🛒 COMPRAS"])

# --- TAB 1: MESA DE CORTE (VISUAL DE TARJETAS) ---
with t1:
    if df_prendas is not None:
        c_tit, c_search = st.columns([2, 2])
        with c_tit: st.subheader("Catálogo de Prendas")
        with c_search: 
            search = st.text_input("Buscar referencia o nombre...", label_visibility="collapsed", placeholder="🔍 Buscar...")
        
        # Filtro de búsqueda
        display_df = df_prendas.copy()
        if search:
            display_df = display_df[display_df['Referencia'].str.contains(search, case=False) | display_df['Nombre'].str.contains(search, case=False)]

        # Grid de Tarjetas para el catálogo
        st.write("### Disponibles en Maestro")
        cols = st.columns(4)
        for idx, row in display_df.head(20).iterrows(): # Limitamos a 20 para fluidez
            with cols[idx % 4]:
                st.markdown(f"""
                    <div class="product-card">
                        <span class="badge-ref">{row['Referencia']}</span>
                        <div class="product-title">{row['Nombre']}</div>
                        <div class="product-sub">{row['Color']} / Talla {row['Talla']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"Añadir", key=f"add_{row['Ean']}"):
                    nueva_fila = pd.DataFrame([row])
                    nueva_fila['Sel'] = False
                    nueva_fila['Cant. a fabricar'] = 0
                    st.session_state.mesa = pd.concat([st.session_state.mesa, nueva_fila]).drop_duplicates(subset=['Ean'])
                    st.toast(f"{row['Referencia']} en mesa")
                    st.rerun()

    if not st.session_state.mesa.empty:
        st.write("---")
        st.write("### 📋 Artículos en Mesa de Trabajo")
        
        # Acciones en bloque para la mesa
        m1, m2, m3, m4 = st.columns([1, 1, 1, 1])
        if m1.button("Seleccionar Todo"): st.session_state.mesa['Sel'] = True; st.rerun()
        if m2.button("Deseleccionar"): st.session_state.mesa['Sel'] = False; st.rer
            
