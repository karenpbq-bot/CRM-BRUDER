# ==========================================
# MÓDULO: HOJA DE RUTA / AGENDA (modulos/m_agenda.py)
# VERSIÓN: SUPABASE CLOUD - VINCULACIÓN TOTAL Y VALIDACIÓN
# ==========================================
import streamlit as st
import pandas as pd
from datetime import datetime
import time

def mostrar(conectar):
    st.header("🗺️ Hoja de Ruta Estratégica")
    supabase = conectar()

    # 1. VINCULACIÓN CON USUARIOS: Traemos a todos (Gerente y Vendedores) excepto Admin
    res_u = supabase.table("usuarios").select("nombre").neq("rol", "Administrador").execute()
    lista_usuarios = sorted([u['nombre'] for u in res_u.data]) if res_u.data else []
    
    v_sel = st.selectbox("👤 Seleccione Responsable (Vendedor/Gerente):", ["--"] + lista_usuarios)

    if v_sel != "--":
        # 2. CARGA DE DATOS: Consulta a sucursales con join a clientes y agenda
        # Agregamos un st.spinner para que el usuario sepa que se están trayendo datos frescos
        with st.spinner("Actualizando hoja de ruta..."):
            res_data = supabase.table("sucursales").select(
                "id, nombre_sede, distrito, zona, cliente_id, "
                "clientes(nombre_comercial), "
                "agenda(fecha_visita, tipo_contacto, color)"
            ).execute()

        # Validación de errores de conexión
        if not res_data.data:
            st.warning("No se encontraron sedes vinculadas a este usuario.")
            return

        # 3. VALIDACIÓN DE CARTERA: Mensaje si no hay clientes asignados
        if not res_data.data:
            st.warning(f"⚠️ El usuario **{v_sel}** aún no tiene clientes o sedes asignadas bajo su responsabilidad.")
            return

       
        # 4. PROCESAMIENTO: Mapeo de datos inicial
        filas = []
        for r in res_data.data:
            ag = r.get('agenda') if r.get('agenda') else {}
            if isinstance(ag, list): ag = ag[0] if len(ag) > 0 else {}

            filas.append({
                "Cliente": r['clientes']['nombre_comercial'] if r.get('clientes') else "Sin Nombre",
                "Sede": r['nombre_sede'],
                "Distrito": r['distrito'],
                "Zona": r['zona'],
                "Fecha": ag.get('fecha_visita'),
                "Contacto": ag.get('tipo_contacto', "Llamada"),
                "Color": ag.get('color', "Celeste"),
                "ID_SEDE": r['id'],
                "CLIENTE_ID": r['cliente_id']
            })
        
        df_base = pd.DataFrame(filas)
        df_base['Fecha'] = pd.to_datetime(df_base['Fecha'], errors='coerce')

        # 5. PANEL DE FILTROS: (Variables inicializadas aquí para evitar NameError)
        st.info("💡 **Tip:** Selecciona 'Sin fecha' para ver clientes pendientes de programar.")
        
        with st.expander("🔍 Filtros de Cartera (Multiselección)", expanded=True):
            f_col1, f_col2 = st.columns(2)
            
            # Selector de estado de fecha
            estado_fec = f_col1.radio("Estado de fecha:", ["Todas", "Con fecha", "Sin fecha"], horizontal=True, key="rad_fec")
            
            # Inicializamos f_fecha como None por defecto para que siempre exista
            f_fecha = None
            if estado_fec == "Con fecha":
                f_fecha = f_col1.date_input("Día específico:", value=None, key="input_fec")
            
            f_colores = f_col2.multiselect("Filtrar por Colores:", ["Verde", "Amarillo", "Naranja", "Celeste", "Melón"], key="ms_col")
            
            f_col3, f_col4 = st.columns(2)
            f_zonas = f_col3.multiselect("Filtrar por Zonas:", sorted(df_base['Zona'].dropna().unique().tolist()), key="ms_zon")
            f_distritos = f_col4.multiselect("Filtrar por Distritos:", sorted(df_base['Distrito'].dropna().unique().tolist()), key="ms_dis")

       # 5.1 LÓGICA DE FILTRADO DINÁMICO (Segura contra NameError)
        df_filtrado = df_base.copy()
        
        if estado_fec == "Sin fecha":
            df_filtrado = df_filtrado[df_filtrado['Fecha'].isna()]
        elif estado_fec == "Con fecha" and f_fecha:
            df_filtrado = df_filtrado[df_filtrado['Fecha'].dt.date == f_fecha]
            
        if f_colores:
            df_filtrado = df_filtrado[df_filtrado['Color'].isin(f_colores)]
        if f_zonas:
            df_filtrado = df_filtrado[df_filtrado['Zona'].isin(f_zonas)]
        if f_distritos:
            df_filtrado = df_filtrado[df_filtrado['Distrito'].isin(f_distritos)]

        # 6. DÍA, ICONO Y REORDENAMIENTO FINAL
        def obtener_dia_semana(f):
            if pd.isna(f): return "Pendiente"
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            return dias[f.weekday()]
        
        df_filtrado['Día'] = df_filtrado['Fecha'].apply(obtener_dia_semana)
        df_filtrado = df_filtrado.rename(columns={"Color": "🎨"})

        # NUEVO ORDEN: Zona ahora se ubica después de la paleta 🎨
        columnas_orden = [
            "Cliente", "Sede", "Distrito", "Día", "Fecha", 
            "Contacto", "🎨", "Zona", "ID_SEDE", "CLIENTE_ID"
        ]
        df_filtrado = df_filtrado.reindex(columns=columnas_orden)

        # 7. CONFIGURACIÓN DE TABLA (Ajustado al nuevo orden)
        column_config = {
            "ID_SEDE": None, "CLIENTE_ID": None,
            "Cliente": st.column_config.TextColumn("🏢 Cliente", disabled=True),
            "Sede": st.column_config.TextColumn("📍 Sede", disabled=True),
            "Distrito": st.column_config.TextColumn("🏘️ Distrito", disabled=True),
            "Día": st.column_config.TextColumn("🗓️ Día", disabled=True),
            "Fecha": st.column_config.DateColumn("📅 Fecha", format="DD/MM/YYYY"),
            "Contacto": st.column_config.SelectboxColumn("📞 Contacto", options=["Visita", "Llamada"]),
            "🎨": st.column_config.SelectboxColumn("🎨", options=["Verde", "Amarillo", "Naranja", "Celeste", "Melón"]),
            "Zona": st.column_config.TextColumn("🚩 Zona", disabled=True)
        }

        # 8. SEMAFIZACIÓN
        def highlight_rows(row):
            color_map = {
                "Verde": "background-color: #d4edda", "Amarillo": "background-color: #fff3cd",
                "Naranja": "background-color: #ffe5d0", "Celeste": "background-color: #d1ecf1",
                "Melón": "background-color: #ffd1dc"
            }
            return [color_map.get(row['🎨'], "")] * len(row)

        st.subheader(f"📋 Registros en Hoja de Ruta: {len(df_filtrado)}")
        
        # Uso de width='stretch' para eliminar el Warning de 2026
        df_editado = st.data_editor(
            df_filtrado.style.apply(highlight_rows, axis=1),
            column_config=column_config,
            width="stretch",
            hide_index=True,
            key="agenda_v2026_final_fix"
        )

       # 9. GUARDADO (UPSERT) CORREGIDO PARA ACTUALIZAR VISTA
        if st.button("💾 Guardar Cambios en Agenda"):
            try:
                for _, row in df_editado.iterrows():
                    # Convertimos la fecha a string para Supabase
                    f_val = row['Fecha']
                    f_str = f_val.strftime('%Y-%m-%d') if pd.notna(f_val) else None
                    
                    obj_upsert = {
                        "sede_id": int(row['ID_SEDE']),
                        "cliente_id": int(row['CLIENTE_ID']),
                        "fecha_visita": f_str,
                        "tipo_contacto": row['Contacto'],
                        "color": row['🎨'],
                        "zona": row['Zona']
                    }
                    # Ejecutamos el guardado
                    supabase.table("agenda").upsert(obj_upsert, on_conflict="sede_id").execute()
                
                # --- EL TRUCO PARA ACTUALIZAR LA VISTA ---
                st.success("✨ ¡Sincronización exitosa!")
                time.sleep(1) # Damos tiempo a la base de datos para procesar
                
                # Limpiamos el estado del editor para que cargue los nuevos valores
                if "agenda_cloud_editor_final" in st.session_state:
                    del st.session_state["agenda_cloud_editor_final"]
                
                st.rerun() # Forzamos el refresco total de la página
                
            except Exception as e:
                st.error(f"Error al sincronizar: {e}")