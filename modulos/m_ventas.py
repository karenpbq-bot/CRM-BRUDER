# ==============================================================================
# MÓDULO: VENTAS (modulos/m_ventas.py) - VERSIÓN INTEGRAL CON SECCIONES
# ==============================================================================
import streamlit as st
import pandas as pd
from datetime import datetime
import time

def mostrar(conectar):
    st.header("💰 Gestión de Ventas y Pedidos")
    supabase = conectar()
    
    # --------------------------------------------------------------------------
    # SECCIÓN 0: CARGA DE DATOS MAESTROS (Inventario y Vendedores)
    # --------------------------------------------------------------------------
    try:
        res_v = supabase.table("usuarios").select("nombre").neq("rol", "Administrador").execute()
        vendedores = sorted([r['nombre'] for r in res_v.data]) if res_v.data else []
        
        # Productos registrados en Inventario (Solo con stock para nuevas ventas)
        res_p = supabase.table("productos").select("*").execute()
        df_p_inv = pd.DataFrame(res_p.data) if res_p.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return

    t1, t2, t3 = st.tabs(["🛒 Registrar Venta", "📜 Historial Detallado", "✏️ Editar Operación"])

    # --------------------------------------------------------------------------
    # SECCIÓN 1: PESTAÑA REGISTRAR VENTA (Multiproducto + Buscador Multi-Cliente)
    # --------------------------------------------------------------------------
    with t1:
        st.subheader("Registrar Nuevo Pedido")
        c1, c2 = st.columns(2)
        v_reg = c1.selectbox("👤 Vendedor:", ["--"] + vendedores, key="v_reg_s_v11")
        f_reg = c2.date_input("📅 Fecha:", value=datetime.now(), key="f_reg_s_v11")

        if v_reg != "--":
            st.divider()
            res_c = supabase.table("sucursales").select("id, nombre_sede, cliente_id, clientes(nombre_comercial)").eq("vendedor_asignado", v_reg).execute()
            
            if res_c.data:
                # --- NUEVA SUB-SECCIÓN: BUSCADOR MULTISELECCIÓN ---
                if "v_cli_v11" not in st.session_state:
                    # Mapeamos la cartera para el buscador
                    cartera_opciones = {f"{r['clientes']['nombre_comercial']} | {r['nombre_sede']}": r for r in res_c.data}
                    
                    clientes_buscados = st.multiselect(
                        "🔍 Ubicar Cliente(s):", 
                        options=list(cartera_opciones.keys()),
                        help="Escriba el nombre del cliente o la sede para filtrar."
                    )

                    if not clientes_buscados:
                        st.info("Seleccione uno o más clientes del buscador para iniciar pedidos.")
                    
                    # Iteramos solo sobre los seleccionados
                    for seleccion in clientes_buscados:
                        row = cartera_opciones[seleccion]
                        col1, col2, col3 = st.columns([4, 3, 2])
                        nom_cli = row['clientes']['nombre_comercial']
                        col1.write(f"**{nom_cli}**")
                        col2.write(row['nombre_sede'])
                        if col3.button("🛒 Pedido", key=f"btn_v11_{row['id']}"):
                            st.session_state.v_cli_v11 = {'id_c': row['cliente_id'], 'id_s': row['id'], 'nom': nom_cli}
                            st.session_state.v_carro_v11 = []
                            st.rerun()
                
                # --- SUB-SECCIÓN: CARRITO DE COMPRAS (Mantenida intacta) ---
                else:
                    sel = st.session_state.v_cli_v11
                    st.success(f"📦 Cliente: {sel['nom']}")
                    with st.container(border=True):
                        cp, cq, cb = st.columns([3, 1, 1])
                        opts = ["--"] + df_p_inv[df_p_inv['stock']>0].apply(lambda r: f"{r['nombre']} {r['marca']}", axis=1).tolist()
                        p_sel = cp.selectbox("Producto:", opts, key="p_v11")
                        cant = cq.number_input("Cant:", min_value=0.1, key="q_v11")
                        if cb.button("➕ Añadir", key="add_v11"):
                            if p_sel != "--":
                                info = df_p_inv[df_p_inv.apply(lambda r: f"{r['nombre']} {r['marca']}", axis=1) == p_sel].iloc[0]
                                st.session_state.v_carro_v11.append({
                                    'id': int(info['id']), 'Producto': p_sel, 
                                    'Cant': float(cant), 'Precio': float(info['precio_venta']), 
                                    'Subtotal': round(float(cant)*float(info['precio_venta']), 2)
                                })
                                st.rerun()

                    if st.session_state.get("v_carro_v11"):
                        df_car = pd.DataFrame(st.session_state.v_carro_v11)
                        st.table(df_car[['Producto', 'Cant', 'Precio', 'Subtotal']].style.format({'Precio': '{:.2f}', 'Subtotal': '{:.2f}'}))
                        total_v = round(df_car['Subtotal'].sum(), 2)
                        pago_v = st.number_input("Monto Cancelado:", value=total_v, format="%.2f", key="p_v11_val")
                        
                        cf1, cf2 = st.columns(2)
                        if cf1.button("🚀 Confirmar Venta", type="primary", use_container_width=True):
                            ins = supabase.table("ventas").insert({"cliente_id": int(sel['id_c']), "sede_id": int(sel['id_s']), "fecha": str(f_reg), "total": float(total_v), "vendedor": v_reg}).execute()
                            v_id = ins.data[0]['id']
                            for i in st.session_state.v_carro_v11:
                                supabase.table("detalle_ventas").insert({"venta_id": v_id, "producto_id": i['id'], "cantidad": i['Cant'], "precio_unitario": i['Precio']}).execute()
                                supabase.rpc("disminuir_stock", {"p_id": i['id'], "cant": i['Cant']}).execute()
                            if pago_v > 0:
                                supabase.table("pagos").insert({"venta_id": v_id, "fecha_pago": str(f_reg), "monto_pagado": float(pago_v)}).execute()
                            st.success("✅ Guardada"); del st.session_state.v_cli_v11; st.session_state.v_carro_v11 = []; st.rerun()

                        if cf2.button("🗑️ Cancelar", type="secondary", use_container_width=True):
                            del st.session_state.v_cli_v11; st.session_state.v_carro_v11 = []; st.rerun()

    # --------------------------------------------------------------------------
    # SECCIÓN 2: PESTAÑA HISTORIAL (Con 5 Filtros y Columna de Productos)
    # --------------------------------------------------------------------------
    with t2:
        st.subheader("📜 Historial Detallado")
        with st.container(border=True):
            h1, h2, h3 = st.columns([1, 2, 2])
            fh_t = h1.number_input("Ticket #:", min_value=0, key="h_t_v11")
            fh_f = h2.date_input("Fecha:", value=None, key="h_f_v11")
            fh_v = h3.selectbox("Vendedor:", ["TODOS"] + vendedores, key="h_v_v11")
            h4, h5 = st.columns(2)
            fh_c = h4.text_input("Cliente:", key="h_c_v11").upper()
            fh_p = h5.text_input("Filtrar por Producto:", key="h_p_v11").upper()

        q_hist = supabase.table("ventas").select("id, fecha, total, vendedor, clientes(nombre_comercial), detalle_ventas(cantidad, precio_unitario, productos(nombre, marca))").order("id", desc=True)
        if fh_t > 0: q_hist = q_hist.eq("id", int(fh_t))
        if fh_f: q_hist = q_hist.eq("fecha", str(fh_f))
        if fh_v != "TODOS": q_hist = q_hist.eq("vendedor", str(fh_v))
        
        res_h = q_hist.execute()
        if res_h.data:
            data_h = []
            for r in res_h.data:
                prods_txt = ", ".join([f"{d['productos']['nombre']} {d['productos']['marca']}" for d in r['detalle_ventas']])
                if fh_c and fh_c not in r['clientes']['nombre_comercial'].upper(): continue
                if fh_p and fh_p not in prods_txt.upper(): continue
                
                rp = supabase.table("pagos").select("monto_pagado").eq("venta_id", r['id']).execute()
                pag = round(sum(p['monto_pagado'] for p in rp.data), 2)
                pend = round(r['total'] - pag, 2)
                
                data_h.append({
                    "Ticket": r['id'], "Fecha": r['fecha'], "Cliente": r['clientes']['nombre_comercial'], 
                    "Productos": prods_txt, "Total": r['total'], "Pagado": pag, "Pendiente": pend, "Vendedor": r['vendedor']
                })
            
            if data_h:
                df_h = pd.DataFrame(data_h)
                st.dataframe(df_h.style.format({'Total': '{:.2f}', 'Pagado': '{:.2f}', 'Pendiente': '{:.2f}'}).apply(lambda x: ['background-color: #ffcccc' if x.Pendiente > 0 else 'background-color: #ccffcc' for i in x], axis=1), use_container_width=True, hide_index=True)

    # ==============================================================================
# SECCIÓN 3: PESTAÑA EDITAR OPERACIÓN (Corregida y Blindada)
# ==============================================================================
    with t3:
        st.subheader("✏️ Edición Integral de Operaciones")
        # --- Buscador Espejo (Ticket, Fecha, Vendedor, Cliente, Producto) ---
        with st.container(border=True):
            e1, e2, e3 = st.columns([1, 2, 2])
            fe_t = e1.number_input("Ticket #:", min_value=0, key="e_t_v16")
            fe_f = e2.date_input("Fecha:", value=None, key="e_f_v16")
            fe_v = e3.selectbox("Vendedor:", ["TODOS"] + vendedores, key="e_v_v16")
            e4, e5 = st.columns(2)
            fe_c = e4.text_input("Cliente:", key="e_c_v16").upper()
            fe_p = e5.text_input("Producto:", key="e_p_v16").upper()

        res_e = q_hist.execute()
        if res_e.data:
            opts_e = []
            for r in res_e.data:
                ps_e = ", ".join([f"{d['productos']['nombre']} {d['productos']['marca']}" for d in r['detalle_ventas']]).upper()
                if fe_c and fe_c not in r['clientes']['nombre_comercial'].upper(): continue
                if fe_p and fe_p not in ps_e: continue
                opts_e.append(f"Ticket #{r['id']} | {r['clientes']['nombre_comercial']} | S/ {r['total']:.2f}")

            if opts_e:
                sel_e = st.selectbox("Seleccione registro:", opts_e, key="sel_e_v16")
                id_ed = int(sel_e.split('#')[1].split(' |')[0])
                if st.button("🔓 Abrir para Edición Maestra", key="btn_ed_v16"):
                    st.session_state.v_id_edit_v16 = id_ed
                    st.rerun()

        # --- PANEL DE EDICIÓN ACTIVO ---
        if "v_id_edit_v16" in st.session_state:
            id_a = st.session_state.v_id_edit_v16
            v_m = supabase.table("ventas").select("*, clientes(nombre_comercial)").eq("id", id_a).single().execute().data
            d_m = supabase.table("detalle_ventas").select("id, cantidad, precio_unitario, producto_id, productos(nombre, marca)").eq("venta_id", id_a).execute().data
            sum_p = sum(p['monto_pagado'] for p in supabase.table("pagos").select("monto_pagado").eq("venta_id", id_a).execute().data)

            st.warning(f"⚠️ Editando Ticket #{id_a} - {v_m['clientes']['nombre_comercial']}")

            # --- SUB-SECCIÓN A: AÑADIR NUEVOS PRODUCTOS A ESTA VENTA ---
            with st.expander("➕ Añadir Producto Faltante a esta Venta", expanded=False):
                col_add1, col_add2, col_add3 = st.columns([3, 1, 1])
                opts_inv = ["--"] + df_p_inv[df_p_inv['stock']>0].apply(lambda r: f"{r['nombre']} {r['marca']}", axis=1).tolist()
                p_new = col_add1.selectbox("Elegir de Inventario:", opts_inv, key="p_new_edit")
                q_new = col_add2.number_input("Cant:", min_value=0.1, key="q_new_edit")
                if col_add3.button("Añadir", key="btn_add_edit"):
                    if p_new != "--":
                        info_p = df_p_inv[df_p_inv.apply(lambda r: f"{r['nombre']} {r['marca']}", axis=1) == p_new].iloc[0]
                        # Insertar directamente en la base de datos
                        supabase.table("detalle_ventas").insert({
                            "venta_id": id_a, "producto_id": int(info_p['id']), 
                            "cantidad": float(q_new), "precio_unitario": float(info_p['precio_venta'])
                        }).execute()
                        # Descontar Stock
                        supabase.rpc("disminuir_stock", {"p_id": int(info_p['id']), "cant": float(q_new)}).execute()
                        st.success("Producto añadido"); time.sleep(0.5); st.rerun()

            # --- SUB-SECCIÓN B: LISTA DE PRODUCTOS ACTUALES (Con opción de eliminar) ---
            st.write("### 🛒 Productos Registrados")
            for d in d_m:
                col_i1, col_i2, col_i3, col_i4 = st.columns([4, 2, 2, 1])
                col_i1.write(f"**{d['productos']['nombre']} {d['productos']['marca']}**")
                n_q = col_i2.number_input("Cant:", value=float(d['cantidad']), key=f"q_edit_{d['id']}")
                n_pr = col_i3.number_input("Precio S/:", value=float(d['precio_unitario']), key=f"pr_edit_{d['id']}")
                if col_i4.button("🗑️", key=f"del_edit_{d['id']}"):
                    # Devolver stock antes de borrar
                    supabase.rpc("aumentar_stock", {"p_id": int(d['producto_id']), "cant": float(d['cantidad'])}).execute()
                    supabase.table("detalle_ventas").delete().eq("id", d['id']).execute()
                    st.rerun()
                # Actualización silenciosa de cambios en fila
                if n_q != d['cantidad'] or n_pr != d['precio_unitario']:
                    supabase.table("detalle_ventas").update({"cantidad": n_q, "precio_unitario": n_pr}).eq("id", d['id']).execute()

            # --- SUB-SECCIÓN C: CABECERA Y PAGOS ---
            with st.form("f_ed_final_v16"):
                st.write("### 📝 Datos de Venta y Cobranza")
                ce1, ce2 = st.columns(2)
                ne_f = ce1.date_input("Fecha:", value=datetime.strptime(v_m['fecha'], '%Y-%m-%d'))
                ne_v = ce2.selectbox("Vendedor:", vendedores, index=vendedores.index(v_m['vendedor']) if v_m['vendedor'] in vendedores else 0)
                
                # Recalcular total real de la base de datos
                d_m_updated = supabase.table("detalle_ventas").select("cantidad, precio_unitario").eq("venta_id", id_a).execute().data
                total_real = round(sum(i['cantidad'] * i['precio_unitario'] for i in d_m_updated), 2)
                
                ce3, ce4 = st.columns(2)
                ne_t = ce3.number_input("Total Final S/:", value=float(total_real), format="%.2f")
                ne_p = ce4.number_input("Monto Cobrado S/:", value=float(sum_p), format="%.2f")

                if st.form_submit_button("💾 Finalizar y Guardar Todo"):
                    supabase.table("ventas").update({"fecha": str(ne_f), "vendedor": ne_v, "total": float(ne_t)}).eq("id", id_a).execute()
                    supabase.table("pagos").delete().eq("venta_id", id_a).execute()
                    if ne_p > 0:
                        supabase.table("pagos").insert({"venta_id": id_a, "fecha_pago": str(ne_f), "monto_pagado": float(ne_p)}).execute()
                    st.success("✅ Ticket sincronizado"); del st.session_state.v_id_edit_v16; time.sleep(1); st.rerun()
            
            if st.button("❌ Cerrar Sin Guardar Cabecera"):
                del st.session_state.v_id_edit_v16
                st.rerun()