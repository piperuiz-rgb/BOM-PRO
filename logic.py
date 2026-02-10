import pandas as pd
import io
import streamlit as st

TARIFA_COL = "Tarifa Proveedor"
EAN_COL = "EAN"

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
            if 'Cant. a fabricar' not in nuevos.columns:
                nuevos['Cant. a fabricar'] = 0
            mesa = pd.concat([mesa, nuevos]).drop_duplicates(subset=[EAN_COL])
            st.session_state['mesa'] = mesa.reset_index(drop=True)

    if mesa.empty:
        st.info("Añade referencias para empezar la planificación.")
        return

    st.divider()

    st.markdown("### Edición masiva")
    col_sel, col_talla = st.columns([2, 2])
    seleccion_todos = col_sel.checkbox("Seleccionar todos")
    tallas_disponibles = sorted(mesa['Talla'].unique())
    talla_filtro = col_talla.selectbox("Filtrar por talla:", ["Todas"] + tallas_disponibles)

    # Obtener índices seleccionados
    if seleccion_todos:
        seleccionadas = mesa.index
    elif talla_filtro != "Todas":
        seleccionadas = mesa[mesa['Talla'] == talla_filtro].index
    else:
        seleccionadas = []

    cols_mass = st.columns(4)
    if cols_mass[0].button("➕ Sumar 5"):
        mesa.loc[seleccionadas, 'Cant. a fabricar'] += 5
    if cols_mass[1].button("➕ Sumar 10"):
        mesa.loc[seleccionadas, 'Cant. a fabricar'] += 10
    if cols_mass[2].button("➖ Restar 5"):
        mesa.loc[seleccionadas, 'Cant. a fabricar'] -= 5
        mesa.loc[mesa['Cant. a fabricar'] < 0, 'Cant. a fabricar'] = 0
    if cols_mass[3].button("➖ Restar 10"):
        mesa.loc[seleccionadas, 'Cant. a fabricar'] -= 10
        mesa.loc[mesa['Cant. a fabricar'] < 0, 'Cant. a fabricar'] = 0
    st.session_state['mesa'] = mesa

    st.write("### Modificar cantidades por variante:")
    for idx, row in mesa.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([1.3, 2, 1, 1, 1, 1])
        c1.markdown(f"**Ref:** {row['Referencia']}")
        c2.write(f"{row['Nombre']} ({row['Color']}, Talla {row['Talla']})\nEAN: {row[EAN_COL]}")
        unidades = int(row['Cant. a fabricar'])
        if c3.button(f"+5", key=f"plus5_{idx}"):
            mesa.at[idx, 'Cant. a fabricar'] = unidades + 5
            st.session_state['mesa'] = mesa
        if c4.button(f"+10", key=f"plus10_{idx}"):
            mesa.at[idx, 'Cant. a fabricar'] = unidades + 10
            st.session_state['mesa'] = mesa
        if c5.button(f"-5", key=f"minus5_{idx}"):
            mesa.at[idx, 'Cant. a fabricar'] = max(0, unidades - 5)
            st.session_state['mesa'] = mesa
        if c6.button(f"-10", key=f"minus10_{idx}"):
            mesa.at[idx, 'Cant. a fabricar'] = max(0, unidades - 10)
            st.session_state['mesa'] = mesa
        st.write(f"Cantidad actual: {unidades}")

    st.session_state['mesa'] = mesa.reset_index(drop=True)

    # Selección de variantes para asignación de componentes
    st.divider()
    st.markdown("### Selecciona variantes para mesa de asignación de componentes")
    seleccion_asignacion = st.multiselect(
        "Elige variantes (EAN) para asignar componentes:",
        options=mesa[EAN_COL].tolist(),
        default=[]
    )
    if st.button("➡️ Pasar a mesa de asignación de componentes"):
        st.session_state['mesa_asignacion'] = mesa[mesa[EAN_COL].isin(seleccion_asignacion)].copy()
        st.success(f"¡{len(seleccion_asignacion)} variantes transferidas a la mesa de asignación de componentes!")

def calcular_lista_compra(bom, mesa, df_comp):
    df_m = mesa[['Referencia', 'Color', 'Talla', 'Cant. a fabricar', EAN_COL]]
    df = bom.merge(df_m, left_on=[EAN_COL], right_on=[EAN_COL], how='left')
    df['Total Compra'] = df['Cantidad'].astype(float) * df['Cant. a fabricar'].astype(float)
    df = df.merge(
        df_comp[['Referencia', TARIFA_COL]],
        left_on='Ref Comp',
        right_on='Referencia',
        how='left',
        suffixes=('', '_comp')
    )
    df[TARIFA_COL] = df[TARIFA_COL].fillna(0.0)
    df['Coste componente'] = df['Total Compra'] * df[TARIFA_COL]
    coste_total = df['Coste componente'].sum()
    cols_out = ['Ref Comp', 'Nom Comp', 'Col Comp', 'Ud', 'Total Compra', TARIFA_COL, 'Coste componente']
    st.subheader("📊 Necesidades Totales y Costes")
    st.dataframe(df[cols_out], use_container_width=True)
    st.info(f"**Coste total de la colección (sin IVA): {coste_total:.2f} €**")
    return df[cols_out], coste_total

def exportar_importador_gextia(mesa, bom):
    columnas_gextia = [
        'Nombre',
        EAN_COL,
        'Cant. a fabricar',
        'Tipo de lista de material',  # Añade en bom si lo necesitas
        'Subcontratista',
        'EAN Componente',
        'Cantidad',
        'Ud'
    ]
    bom_export = bom.copy()
    mesa_export = mesa.copy()
    for col in columnas_gextia:
        if col not in bom_export.columns:
            bom_export[col] = ''
    for col in ['Nombre', EAN_COL, 'Cant. a fabricar']:
        if col not in mesa_export.columns:
            mesa_export[col] = ''
    export_df = bom_export.copy()
    export_df['Nombre'] = export_df['Nombre'].fillna('')
    export_df[EAN_COL] = export_df[EAN_COL].fillna('')
    export_df['Cant. a fabricar'] = mesa_export.set_index(EAN_COL).loc[export_df[EAN_COL], 'Cant. a fabricar'].values
    export_df = export_df[columnas_gextia]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False)
    return output.getvalue()

def ui_tab_exportar_importador(st):
    mesa = st.session_state['mesa']
    bom = st.session_state['bom']
    if mesa.empty or bom.empty:
        st.info("Debes tener mesa y BOM generados antes de exportar.")
        return
    st.subheader("📋 Exportar para Importador Gextia")
    if st.button("Descargar importardor.xlsx"):
        data = exportar_importador_gextia(mesa, bom)
        st.download_button(
            "Descargar archivo importardor.xlsx",
            data,
            file_name="importardor.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
