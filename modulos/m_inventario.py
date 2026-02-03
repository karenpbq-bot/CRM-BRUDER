# ==========================================
# MÓDULO: INVENTARIO (modulos/m_inventario.py)
# VERSIÓN: SUPABASE CLOUD - INTEGRAL
# ==========================================
import streamlit as st
import pandas as pd
from datetime import datetime
import time

def mostrar(conectar):
    st.header("📦 Gestión de Almacén e Inventario")
    
    # 1. DEFINICIÓN DE PESTAÑAS SEGÚN ROL (Funcionalidad Conservada)
    if st.session_state.user_rol == "Vendedor":
        titulos_tabs = ["📋 Stock Actual"]
    else:
        titulos_tabs = ["📋 Stock Actual", "🆕 Definir Producto", "📥 Registrar Ingreso", "📅 Historial"]
    
    tabs = st.tabs(titulos_tabs)
    supabase = conectar()

    # --- PESTAÑA 0: STOCK ACTUAL (Visible para todos) ---
    with tabs[0]:
        st.subheader("Estado Físico de Almacén")
        res = supabase.table("productos").select("id, nombre, marca, unidad, stock, stock_minimo, precio_venta").order("nombre").execute()
        
        if res.data:
            df_stock = pd.DataFrame(res.data)
            # Renombrar para que coincida con tu vista original
            df_stock = df_stock.rename(columns={
                'nombre': 'Producto', 'marca': 'Marca', 'unidad': 'Unidad',
                'stock': 'Stock Actual', 'stock_minimo': 'S. Mínimo', 'precio_venta': 'Precio Venta'
            })

            # Resaltado de Stock Bajo (Lógica de colores conservada)
            def resaltar_bajo_stock(s):
                is_low = s['Stock Actual'] <= s['S. Mínimo']
                return ['background-color: #ffcccc' if is_low else '' for _ in s]

            st.dataframe(
                df_stock.style.apply(resaltar_bajo_stock, axis=1), 
                use_container_width=True, 
                hide_index=True
            )
        
        if st.session_state.user_rol == "Vendedor":
            st.info("💡 Modo Lectura: Puedes consultar la disponibilidad, pero no editar los registros.")

    # --- BLOQUE DE SEGURIDAD: Solo Admin y Gerente ---
    if st.session_state.user_rol in ["Administrador", "Gerente"]:
        
        # --- PESTAÑA 1: DEFINIR PRODUCTO ---
        with tabs[1]:
            st.subheader("Maestro de Catálogo")
            # Traemos todos los productos para el buscador de edición
            res_m = supabase.table("productos").select("*").execute()
            df_m = pd.DataFrame(res_m.data) if res_m.data else pd.DataFrame()
            
            modo = st.radio("Acción a realizar:", ["Crear Nuevo Producto", "Editar Producto Existente"], horizontal=True, key="inv_modo")
            id_p, v_nom, v_mar, v_uni, v_min, v_stock = None, "", "", "Botella", 5.0, 0.0

            if modo == "Editar Producto Existente" and not df_m.empty:
                busqueda_edit = st.selectbox("🔍 Seleccione el PRODUCTO EXISTENTE:", 
                                            ["-- SELECCIONE --"] + 
                                            df_m.apply(lambda r: f"ID {r['id']} | {r['nombre']} {r['marca']}", axis=1).tolist())
                
                if busqueda_edit != "-- SELECCIONE --":
                    id_p = int(busqueda_edit.split(" | ")[0].replace("ID ", ""))
                    data = df_m[df_m['id'] == id_p].iloc[0]
                    v_nom, v_mar, v_uni, v_min, v_stock = data['nombre'], data['marca'], data['unidad'], float(data['stock_minimo']), float(data['stock'])

            with st.form("form_maestro_final", clear_on_submit=(modo == "Crear Nuevo Producto")):
                st.write(f"### {'📝 Editando ID: ' + str(id_p) if id_p else '✨ Nuevo Registro'}")
                en = st.text_input("Nombre del Producto", value=v_nom).upper()
                em = st.text_input("Marca", value=v_mar).upper()
                
                c1, c2, c3 = st.columns(3)
                unidades = ["Botella", "Caja", "Balde", "Cilindro"]
                idx_uni = unidades.index(v_uni) if v_uni in unidades else 0
                eu = c1.selectbox("Unidad", unidades, index=idx_uni)
                esm = c2.number_input("Stock Mínimo (Alerta)", value=v_min)
                est = c3.number_input("Stock Físico Actual", value=v_stock)

                if st.form_submit_button("💾 Guardar Cambios en Sistema"):
                    if en and em:
                        datos = {"nombre": en, "marca": em, "unidad": eu, "stock_minimo": esm, "stock": est}
                        if id_p:
                            supabase.table("productos").update(datos).eq("id", id_p).execute()
                            st.success("✅ Datos maestros actualizados en la nube.")
                        else:
                            supabase.table("productos").insert(datos).execute()
                            st.success("✅ Producto creado exitosamente en la nube.")
                        time.sleep(1); st.rerun()
                    else:
                        st.error("⚠️ El Nombre y la Marca son obligatorios.")

        # --- PESTAÑA 2: REGISTRAR INGRESO ---
        with tabs[2]:
            st.subheader("Entrada de Mercadería")
            res_marcas = supabase.table("productos").select("marca").execute()
            marcas_disp = sorted(list(set([r['marca'] for r in res_marcas.data]))) if res_marcas.data else []
            
            m_filtro = st.selectbox("1. Filtrar por Marca:", ["TODAS"] + marcas_disp)
            
            query = supabase.table("productos").select("id, nombre, marca, precio_venta")
            if m_filtro != "TODAS":
                query = query.eq("marca", m_filtro)
            
            prods_list = pd.DataFrame(query.execute().data)
            
            if not prods_list.empty:
                p_sel_name = st.selectbox("2. Seleccione Producto:", ["-- SELECCIONE --"] + prods_list['nombre'].tolist())
                
                if p_sel_name != "-- SELECCIONE --":
                    p_data = prods_list[prods_list['nombre'] == p_sel_name].iloc[0]
                    id_sel = int(p_data['id'])

                    with st.form("form_ingreso_agil"):
                        st.info(f"Ingresando stock para: **{p_data['nombre']} {p_data['marca']}**")
                        c1, c2 = st.columns(2)
                        cant = c1.number_input("Cantidad", min_value=0.1)
                        costo = c2.number_input("Costo Unitario S/", min_value=0.0)
                        
                        c3, c4 = st.columns(2)
                        p_venta = c3.number_input("Precio de Venta Sugerido S/", value=float(p_data['precio_venta']))
                        fec = c4.date_input("Fecha de Ingreso", value=datetime.now())
                        
                        if st.form_submit_button("📥 Registrar Ingreso"):
                            # Obtener stock actual para sumar
                            p_curr = supabase.table("productos").select("stock").eq("id", id_sel).single().execute()
                            nuevo_stock = p_curr.data['stock'] + cant
                            
                            # Actualizar Producto
                            supabase.table("productos").update({
                                "stock": nuevo_stock, "costo": costo, "precio_venta": p_venta
                            }).eq("id", id_sel).execute()
                            
                            # Registrar Movimiento
                            supabase.table("movimientos").insert({
                                "producto_id": id_sel, "fecha": str(fec), 
                                "tipo": 'INGRESO', "cantidad": cant, "costo_historico": costo
                            }).execute()
                            
                            st.success("✅ Inventario sincronizado.")
                            time.sleep(1); st.rerun()

        # --- PESTAÑA 3: HISTORIAL (Buscador y Editor de Historial) ---
        with tabs[3]:
            st.subheader("🔍 Buscador de Movimientos")
            res_h = supabase.table("movimientos").select("id, fecha, cantidad, costo_historico, tipo, productos(nombre, marca)").order("id", desc=True).execute()
            
            if res_h.data:
                # Aplanamos los datos para el DataFrame
                df_h_raw = pd.DataFrame([{
                    'id': r['id'], 'fecha': r['fecha'], 'nombre': r['productos']['nombre'],
                    'marca': r['productos']['marca'], 'cantidad': r['cantidad'], 'Costo': r['costo_historico']
                } for r in res_h.data])
                
                c1, c2, c3 = st.columns(3)
                f_nom = c1.multiselect("Filtrar por Nombre:", sorted(df_h_raw['nombre'].unique()))
                f_mar = c2.multiselect("Filtrar por Marca:", sorted(df_h_raw['marca'].unique()))
                f_fec = c3.date_input("Filtrar por Fecha:", value=None)

                df_f = df_h_raw.copy()
                if f_nom: df_f = df_f[df_f['nombre'].isin(f_nom)]
                if f_mar: df_f = df_f[df_f['marca'].isin(f_mar)]
                if f_fec: df_f = df_f[df_f['fecha'] == str(f_fec)]

                st.dataframe(df_f, use_container_width=True, hide_index=True)

                if not df_f.empty:
                    with st.expander("✏️ Editar Registro de Ingreso Seleccionado"):
                        id_edit_h = st.selectbox("ID de registro:", df_f['id'].tolist())
                        reg = df_f[df_f['id'] == id_edit_h].iloc[0]
                        with st.form("form_edit_hist_final"):
                            ce1, ce2 = st.columns(2)
                            nq = ce1.number_input("Corregir Cantidad", value=float(reg['cantidad']))
                            nc = ce2.number_input("Corregir Costo", value=float(reg['Costo']))
                            
                            if st.form_submit_button("✅ Aplicar Corrección"):
                                diff = nq - reg['cantidad']
                                # 1. Actualizar Stock en tabla productos
                                # Primero buscamos el producto asociado a este movimiento
                                mov_data = supabase.table("movimientos").select("producto_id").eq("id", id_edit_h).single().execute()
                                p_id = mov_data.data['producto_id']
                                
                                p_stock_res = supabase.table("productos").select("stock").eq("id", p_id).single().execute()
                                nuevo_st = p_stock_res.data['stock'] + diff
                                
                                supabase.table("productos").update({"stock": nuevo_st}).eq("id", p_id).execute()
                                
                                # 2. Actualizar el movimiento
                                supabase.table("movimientos").update({"cantidad": nq, "costo_historico": nc}).eq("id", id_edit_h).execute()
                                st.success("Corrección aplicada en la nube."); time.sleep(1); st.rerun()
            else:
                st.info("No hay movimientos registrados.")