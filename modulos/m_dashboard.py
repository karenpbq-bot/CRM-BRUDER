# ==========================================
# MÓDULO: DASHBOARD (modulos/m_dashboard.py)
# VERSIÓN: SUPABASE CLOUD (PostgreSQL)
# ==========================================
import streamlit as st
import pandas as pd

def mostrar(conectar):
    st.header("📊 Panel de Control y Estado Financiero")
    supabase = conectar()

    try:
        # 1. --- CÁLCULO DE KPIs PRINCIPALES ---
        # Obtenemos datos de ventas, pagos y productos simultáneamente
        res_ventas = supabase.table("ventas").select("total").execute()
        res_pagos = supabase.table("pagos").select("monto_pagado").execute()
        res_prods = supabase.table("productos").select("stock, costo, nombre, marca, unidad, stock_minimo").execute()

        # Procesar Totales
        total_ventas = sum(v['total'] for v in res_ventas.data) if res_ventas.data else 0.0
        total_pagos = sum(p['monto_pagado'] for p in res_pagos.data) if res_pagos.data else 0.0
        valor_almacen = sum((p['stock'] or 0) * (p['costo'] or 0) for p in res_prods.data) if res_prods.data else 0.0

        # Mostrar KPIs
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        col_kpi1.metric("💰 Por Cobrar Total", f"S/ {total_ventas - total_pagos:,.2f}")
        col_kpi2.metric("📈 Ventas Acumuladas", f"S/ {total_ventas:,.2f}")
        col_kpi3.metric("📦 Valor en Almacén", f"S/ {valor_almacen:,.2f}")

        st.divider()

        # 2. --- SECCIÓN: CUENTAS POR COBRAR (DETALLE) ---
        st.subheader("👥 Estado de Cuentas por Cliente")
        
        # En Supabase/Postgres, la lógica de saldos se maneja mejor trayendo las tablas relacionadas
        # Nota: Esta consulta asume que ya creaste las tablas 'clientes', 'ventas' y 'pagos'
        res_deudas = supabase.table("clientes").select("""
            nombre_comercial, 
            ruc_dni,
            ventas (id, total, pagos (monto_pagado))
        """).execute()

        datos_saldos = []
        if res_deudas.data:
            for c in res_deudas.data:
                t_ventas = sum(v['total'] for v in c['ventas'])
                t_pagos = sum(sum(p['monto_pagado'] for p in v['pagos']) for v in c['ventas'])
                saldo = t_ventas - t_pagos
                
                if saldo > 0.01:
                    datos_saldos.append({
                        "Cliente": c['nombre_comercial'],
                        "Identificación": c['ruc_dni'],
                        "Total Ventas": t_ventas,
                        "Total Pagado": t_pagos,
                        "Saldo Pendiente": saldo
                    })

        if datos_saldos:
            df_saldos = pd.DataFrame(datos_saldos)
            st.dataframe(df_saldos.sort_values(by="Saldo Pendiente", ascending=False), 
                         use_container_width=True, hide_index=True)
        else:
            st.info("No hay deudas pendientes registradas en la nube.")

        # 3. --- SECCIÓN: ALERTAS DE STOCK BAJO ---
        st.divider()
        st.subheader("⚠️ Alertas de Inventario")
        
        if res_prods.data:
            # Filtramos localmente para mayor velocidad
            df_prods = pd.DataFrame(res_prods.data)
            df_stock_bajo = df_prods[df_prods['stock'] < df_prods['stock_minimo']]
            
            if not df_stock_bajo.empty:
                st.warning("Los siguientes productos requieren reposición:")
                st.table(df_stock_bajo[['nombre', 'marca', 'stock', 'unidad']].rename(columns={
                    'nombre': 'Producto', 'marca': 'Marca', 'stock': 'Stock', 'unidad': 'Unidad'
                }))
            else:
                st.success("El stock de todos los productos es óptimo.")
        else:
            st.info("Catálogo vacío.")

    except Exception as e:
        st.error(f"Error al cargar Dashboard: {str(e)}")
        st.info("Asegúrese de haber creado las tablas 'pagos', 'ventas' y 'clientes' en Supabase.")