import streamlit as st
import pandas as pd
import os
import time

# --- 1. CONFIGURACIÓN E INYECCIÓN DE ESTILO "GEXTIA FACTORY" ---
st.set_page_config(page_title="Gextia Factory Pro", layout="wide")

st.markdown("""
    <style>
    /* Fondo general */
    [data-testid="stAppViewContainer"] { background-color: #F8F9FB; }
    
    /* Barra lateral Oscura */
    [data-testid="stSidebar"] {
        background-color: #1E2533 !important;
        color: white;
    }
    
    /* Estilo de Tarjetas (Cards) */
    .product-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #EAECEF;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 20px;
        height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .badge-ref { background-color: #F1F3F5; padding: 4px 8px; border-radius: 4px; font-size: 11px; color: #666; }
    .badge-color { background-color: #E7F0FF; padding: 4px 8px; border-radius: 4px; font-size: 11px; color: #0052CC; float: right; }
    .product-title { font-weight: 600; font-size: 18px; margin-top: 10px; color: #1E2533; }
    .product-sub { color: #888; font-size: 13px; }
    .product-meta { font-size: 13px; margin-top: 5px; color: #444; }
    
    /* Botones estilo SaaS */
    div.stButton > button {
        width: 100%;
        border-radius: 8px !important;
        background-color: #1E3A8A !important;
        color: white !important;
        border: none !important;
        font-weight: 500;
        transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #111827 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGICA DE ESTADO ---
if 'mesa' not in st.session_state: st.session_state.mesa = []

# --- 3. BARRA LATERAL (Sidebar como la imagen) ---
with st.sidebar:
    st.markdown("<h2 style='color:white; font-size:24px;'>Gextia</h2><p style='color:#888; margin-top:-15px;'>Factory Pro</p>", unsafe_allow_html=True)
    st.write(" ")
    st.button("📋 Prendas") # Este sería el active
    st.button("📂 Mesa de Trabajo")
    st.button("📊 Bill of Materials")
    st.button("⚙️ Componentes")
    
    st.markdown("<div style='position: fixed; bottom: 20px; width: 260px;'>", unsafe_allow_html=True)
    st.write("---")
    st.button("📤 Subir Archivo")
    if st.button("🗑️ Limpiar Todo"):
        st.session_state.mesa = []
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 4. CONTENIDO PRINCIPAL ---
st.markdown("### Catálogo de Prendas")
st.markdown("Selecciona prendas para agregar a la mesa de trabajo")

# Buscador y Filtro
c_search, c_filter = st.columns([3, 1])
with c_search:
    query = st.text_input("Buscar referencia...", label_visibility="collapsed", placeholder="🔍 Buscar...")
with c_filter:
    st.selectbox("Filtrar", ["Todas las categorías", "Camisas", "Pantalones", "Faldas"], label_visibility="collapsed")

# Simulación de datos (Esto vendría de tu Excel)
datos_prendas = [
    {"ref": "CAM-001", "nombre": "Camisa Oxford", "cat": "Camisas", "talla": "M", "color": "Azul"},
    {"ref": "CAM-002", "nombre": "Camisa Slim Fit", "cat": "Camisas", "talla": "L", "color": "Blanco"},
    {"ref": "PAN-001", "nombre": "Pantalón Chino", "cat": "Pantalones", "talla": "32", "color": "Beige"},
    {"ref": "PAN-002", "nombre": "Pantalón Cargo", "cat": "Pantalones", "talla": "34", "color": "Verde"},
    {"ref": "VES-001", "nombre": "Vestido Verano", "cat": "Vestidos", "talla": "S", "color": "Floral"},
    {"ref": "FAL-001", "nombre": "Falda Plisada", "cat": "Faldas", "talla": "M", "color": "Negro"},
]

# --- 5. GRID DE TARJETAS (CARDS) ---
cols = st.columns(3) # Tres tarjetas por fila como en la imagen

for i, p in enumerate(datos_prendas):
    with cols[i % 3]:
        st.markdown(f"""
            <div class="product-card">
                <div>
                    <span class="badge-ref">{p['ref']}</span>
                    <span class="badge-color">{p['color']}</span>
                    <div class="product-title">{p['nombre']}</div>
                    <div class="product-sub">{p['cat']}</div>
                    <div class="product-meta">Talla: <b>{p['talla']}</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        # El botón debe estar fuera del HTML pero visualmente pegado
        if st.button(f"+ Agregar a Mesa", key=f"btn_{p['ref']}"):
            st.session_state.mesa.append(p)
            st.toast(f"{p['nombre']} añadido")

# --- 6. FOOTER / STATUS ---
if st.session_state.mesa:
    st.success(f"Artículos en mesa: {len(st.session_state.mesa)}")
    
