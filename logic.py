import pandas as pd
import io
import streamlit as st

TARIFA_COL = "Tarifa Proveedor"

def ui_tab_mesa_de_corte(st):
    mesa = st.session_state['mesa']
    df_prendas = st.session_state['df_prendas']

    st.subheader("🏗️ Planificación de Producción")
    c_sel, c_btn = st.columns([3, 1])
    refs_disponibles = sorted(df_prendas['Referencia'].unique())
    with c_sel:
        seleccion_refs = st.multiselect("Añadir referencias:", refs_disponibles)
    with c_btn:
        if st.button("➕ CARGAR", type="primary"):
            nuevos = df_prendas[df_prendas['Referencia'].isin(seleccion_refs)].copy()
            nuevos['Cant. a fabricar'] = 0
            mesa = pd.concat([mesa, nuevos]).drop_duplicates(subset=['Referencia', 'Color', 'Talla'])
            st.session_state['mesa'] = mesa.reset_index(drop=True)

    if mesa.empty:
        st.info("Añade referencias de prendas para empezar la planificación.")
        return

    st.divider()

    # --- EDICIÓN MASIVA ---
    with st.expander("🛠️ Edición masiva (sumar/restar a todos o a un grupo):"):
        columnas_filtrado = ['Talla', 'Color']
        col_filtro = st.selectbox("Filtrar por:", ['Todos'] + columnas_filtrado)
        valor_filtro = None
        if col_filtro != 'Todos':
            valores = mesa[col_filtro].unique()
            valor_filtro = st.selectbox(f"Valor para {col_filtro}:", valores)
        suma = st.number_input("Unidades a sumar/restar:", value=5, step=1)
        col1, col2 = st.columns(2)
        if col1.button("➕ Sumar a seleccionados"):
            idxs = mesa.index if col_filtro == 'Todos' else mesa[mesa[col_filtro] == valor_filtro].index
            mesa.loc[idxs, 'Cant. a fabricar'] += suma
            mesa.loc[mesa['Cant. a fabricar'] < 0, 'Cant. a fabricar'] = 0
            st.session_state['mesa'] = mesa
        if col2.button("➖ Restar a seleccionados"):
            idxs = mesa.index if col_filtro == 'Todos' else mesa[mesa[col_filtro] == valor_filtro].index
            mesa.loc[idxs, 'Cant. a fabricar'] -= suma
            mesa.loc[mesa['Cant. a fabricar'] < 0, 'Cant. a fabricar'] = 0
            st.session_state['mesa'] = mesa

    st.write("Modificar cantidades por prenda:")

    for idx, row in mesa.iterrows():
        c1, c2, c3, c4 = st.columns([1.3, 1.7, 1, 2])
        c1.markdown(f"**Ref:** {row['Referencia']}")
        c2.write(f"{row['Nombre']} ({row['Color']}, Talla {row['Talla']})")
        menos = c3.button("➖", key=f"menos_{idx}")
        mas = c3.button("➕", key=f"mas_{idx}")
        unidades = int(row['Cant. a fabricar'])
        nuevo_valor = c4.number_input(
            "Unidades", min_value=0, value=unidades,
            key=f"input_{idx}", step=1, label_visibility="collapsed"
        )
        # Actualización simple, sin rerun — refresca al tocar otro widget/acción
        if menos and unidades > 0:
            mesa.at[idx, 'Cant. a fabricar'] = unidades - 1
            st.session_state['mesa'] = mesa
            # st.experimental_rerun()  # solo si no da error
        if mas:
            mesa.at[idx, 'Cant. a fabricar'] = unidades + 1
            st.session_state['mesa'] = mesa
            # st.experimental_rerun()  # solo si no da error
        if nuevo_valor != unidades:
            mesa.at[idx, 'Cant. a fabricar'] = nuevo_valor
            st.session_state['mesa'] = mesa

    st.session_state['mesa'] = mesa.reset_index(drop=True)

def calcular_lista_compra(bom, mesa, df_comp):
    df_m = mesa[['Referencia', 'Color', 'Talla', 'Cant. a fabricar']]
    df = bom.merge(df_m, left_on=['Ref Prenda', 'Col Prenda', 'Tal Prenda'],
                   right_on=['Referencia', 'Color', 'Talla'], how='left')
    df['Total Compra'] = df['Cantidad'].astype(float) * df['Cant. a fabricar'].astype(float)
    df = df.merge(df_comp[['Referencia', TARIFA_COL]], left_on='Ref Comp', right_on='Referencia', how='left', suffixes=('', '_comp'))
    df[TARIFA_COL] = df[TARIFA_COL].fillna(0.0)
    df['Coste componente'] = df['Total Compra'] * df[TARIFA_COL]
    coste_total = df['Coste componente'].sum()
    cols_out = ['Ref Comp', 'Nom Comp', 'Col Comp', 'Ud', 'Total Compra', TARIFA_COL, 'Coste componente']
    st.subheader("📊 Necesidades Totales y Costes")
    st.dataframe(df[cols_out], use_container_width=True)
    st.info(f"**Coste total de la colección (sin IVA): {coste_total:.2f} €**")
    return df[cols_out], coste_total

def exportar_importador_gextia(bom):
    columnas_gextia = [
        'Nombre de producto',
        'Cod Barras Variante',
        'Cantidad producto final',
        'Tipo de lista de material',
        'Subcontratista',
        'EAN Componente',
        'Cantidad',
        'Ud'
    ]
    bom_export = bom.copy()
    for col in columnas_gextia:
        if col not in bom_export.columns:
            bom_export[col] = ''
    bom_export = bom_export[columnas_gextia]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        bom_export.to_excel(writer, index=False)
    return output.getvalue()

def ui_tab_exportar_importador(st):
    bom = st.session_state['bom']
    if bom.empty:
        st.info("Primero debes generar el BOM antes de poder exportar el archivo de importación para Gextia.")
        return
    st.subheader("📋 Exportar para Importador Gextia")
    if st.button("Descargar importardor.xlsx"):
        data = exportar_importador_gextia(bom)
        st.download_button(
            "Descargar archivo importardor.xlsx",
            data,
            file_name="importardor.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
