# BOM-generator

Generador automatizado de listas de materiales (BOM), compatible con importación directa en ERP Gextia.

## Cómo funciona

1. Coloca tus Excels `prendas.xlsx` y `componentes.xlsx` en la raíz del proyecto.  
   Ambos deben incluir la columna **Tarifa Proveedor** (sin IVA).  
2. Ejecuta la app con:
   ```
   streamlit run main.py
   ```
3. Usa los tabs para planificar cortes, editar cantidades, exportar para Gextia y calcular el coste total de la colección.
4. Puedes respaldar/restaurar tu avance con backups `.json`.

## Exportación a Gextia

En la pestaña de auditoría/export puedes descargar el archivo `importardor.xlsx` ya listo para importar en tu ERP, con el formato exacto requerido.

## Nota sobre costes
Si algún Excel no tiene la columna “Tarifa Proveedor”, la app lo avisará y pondrá coste 0 € para esos casos.
