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

    # Seleccionar todos, filtro por talla, suma/resta masiva
    st.markdown("### Edición masiva")
    col_sel, col_talla, col_step = st.columns([2, 2, 1])
    seleccion_todos = col_sel.checkbox("Seleccionar todos")
    tallas_disponibles = sorted(mesa['Talla'].unique())
    talla_filtro = col_talla.selectbox("Filtrar por talla:", ["Todas"] + tallas_disponibles)
    step = col_step.selectbox("Cantidad a modificar", [1, 5, 10])

    if seleccion_todos:
        seleccionadas = mesa.index
    elif talla_filtro != "Todas":
        seleccionadas = mesa[mesa['Talla'] == talla_filtro].index
    else:
        seleccionadas = []

    col_sum, col_rest = st.columns(2)
    if col_sum.button(f"➕ Sumar {step} a seleccionados"):
        mesa.loc[seleccionadas, 'Cant. a fabricar'] += step
        mesa.loc[mesa['Cant. a fabricar'] < 0, 'Cant. a fabricar'] = 0
        st.session_state['mesa'] = mesa
    if col_rest.button(f"➖ Restar {step} a seleccionados"):
        mesa.loc[seleccionadas, 'Cant. a fabricar'] -= step
        mesa.loc[mesa['Cant. a fabricar'] < 0, 'Cant. a fabricar'] = 0
        st.session_state['mesa'] = mesa

    st.write("### Modificar cantidades por variante:")

    for idx, row in mesa.iterrows():
        c1, c2, c3, c4 = st.columns([1.3, 2, 1, 2])
        c1.markdown(f"**Ref:** {row['Referencia']}")
        c2.write(
            f"{row['Nombre']} ({row['Color']}, Talla {row['Talla']})\nEAN: {row[EAN_COL]}"
        )
        menos = c3.button("➖", key=f"menos_{idx}")
        mas = c3.button("➕", key=f"mas_{idx}")
        unidades = int(row['Cant. a fabricar'])
        nuevo_valor = c4.number_input(
            "Unidades", min_value=0, value=unidades,
            key=f"input_{idx}", step=1, label_visibility="collapsed"
        )
        if menos and unidades > 0:
            mesa.at[idx, 'Cant. a fabricar'] = unidades - 1
            st.session_state['mesa'] = mesa
        if mas:
            mesa.at[idx, 'Cant. a fabricar'] = unidades + 1
            st.session_state['mesa'] = mesa
        if nuevo_valor != unidades:
            mesa.at[idx, 'Cant. a fabricar'] = nuevo_valor
            st.session_state['mesa'] = mesa

    st.session_state['mesa'] = mesa.reset_index(drop=True)

def calcular_lista_compra(bom, mesa, df_comp):
    # Aquí assumes que el BOM conecta prendas por EAN (o por Referencia, Talla, Color)
    df_m = mesa[['Referencia', 'Color', 'Talla', 'Cant. a fabricar', EAN_COL]]
    # Ajusta el merge a tus columnas reales en BOM
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
    # Exporta usando EAN como identificador de variante
    columnas_gextia = [
        'Nombre',            # Nombre de producto
        EAN_COL,             # Cod Barras Variante
        'Cant. a fabricar',  # Cantidad producto final
        'Tipo de lista de material',  # Puedes añadir esta columna en el BOM
        'Subcontratista',             # Puedes añadir esta columna en el BOM
        'EAN Componente',             # La EAN del componente
        'Cantidad',                   # Cantidad del componente
        'Ud'                         # Unidad del componente
    ]

    bom_export = bom.copy()
    mesa_export = mesa.copy()
    # Si alguna columna no existe, se crea vac��a
    for col in columnas_gextia:
        if col not in bom_export.columns:
            bom_export[col] = ''
    for col in ['Nombre', EAN_COL, 'Cant. a fabricar']:
        if col not in mesa_export.columns:
            mesa_export[col] = ''
    # Ejemplo: unir mesa y bom para el export, ajusta según tu BOM
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
