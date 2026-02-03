# ==========================================
# MÓDULO: ESTADÍSTICAS E INTELIGENCIA (modulos/m_estadisticas.py)
# VERSIÓN: SUPABASE CLOUD - FUNCIONALIDAD INTEGRAL CERTIFICADA
# ==========================================
import streamlit as st
import pandas as pd
import plotly.express as px
import io
from datetime import datetime

def mostrar(conectar):
    st.header("📊 Estadísticas e Inteligencia de Negocio")
    supabase = conectar()

    t1, t2, t3 = st.tabs(["📦 Productos", "🤝 Gestión de Cobranza", "🥇 Desempeño Vendedores"])

    # --- 1. CARGA DE DATOS MAESTROS ---
    res_p = supabase.table("productos").select("*").execute()
    res_v = supabase.table("ventas").select("*, clientes(nombre_comercial)").execute()
    res_dv = supabase.table("detalle_ventas").select("*, productos(nombre, marca, costo)").execute()
    res_pag = supabase.table("pagos").select("*").execute()
    res_suc = supabase.table("sucursales").select("vendedor_asignado").execute()

    df_p_raw = pd.DataFrame(res_p.data) if res_p.data else pd.DataFrame()
    df_v_raw = pd.DataFrame(res_v.data) if res_v.data else pd.DataFrame()
    df_dv_raw = pd.DataFrame(res_dv.data) if res_dv.data else pd.DataFrame()
    df_suc_raw = pd.DataFrame(res_suc.data) if res_suc.data else pd.DataFrame()
    df_pag_raw = pd.DataFrame(res_pag.data) if res_pag.data else pd.DataFrame(columns=['venta_id', 'monto_pagado'])

    # --- TAB 1: PRODUCTOS (Rentabilidad + Filtros + Gráficos) ---
    with t1:
        st.subheader("📈 Análisis de Rentabilidad")
        if not df_dv_raw.empty:
            df_p = df_dv_raw.copy()
            df_p['Producto'] = df_p['productos'].apply(lambda x: f"{x['nombre']} {x['marca']}")
            df_p['Costo_U'] = df_p['productos'].apply(lambda x: x['costo'])
            
            # Agregación de métricas
            df_p_grp = df_p.groupby('Producto').agg({'cantidad': 'sum'}).reset_index()
            df_p_val = df_p.groupby('Producto').apply(lambda x: (x['cantidad'] * x['precio_unitario']).sum()).reset_index(name='Ventas')
            df_p_grp = df_p_grp.merge(df_p_val, on='Producto')
            df_p_grp = df_p_grp.merge(df_p[['Producto', 'Costo_U']].drop_duplicates(), on='Producto')
            
            df_p_grp['Inversion'] = (df_p_grp['cantidad'] * df_p_grp['Costo_U']).round(2)
            df_p_grp['Ventas'] = df_p_grp['Ventas'].round(2)
            df_p_grp['Utilidad_Bruta'] = (df_p_grp['Ventas'] - df_p_grp['Inversion']).round(2)
            df_p_grp['Margen_Pct'] = ((df_p_grp['Utilidad_Bruta'] / df_p_grp['Ventas']) * 100).round(2)

            # Filtro Dinámico
            lista_p = sorted(df_p_grp['Producto'].unique().tolist())
            sel_p = st.multiselect("🔍 Filtrar Productos:", lista_p, default=lista_p[:7] if len(lista_p)>7 else lista_p)
            df_p_f = df_p_grp[df_p_grp['Producto'].isin(sel_p)]

            if not df_p_f.empty:
                st.dataframe(df_p_f[['Producto', 'cantidad', 'Ventas', 'Inversion', 'Utilidad_Bruta', 'Margen_Pct']].style.format({
                    'Ventas': 'S/ {:.2f}', 'Inversion': 'S/ {:.2f}', 'Utilidad_Bruta': 'S/ {:.2f}', 'Margen_Pct': '{:.2f}%'
                }), use_container_width=True, hide_index=True)

                fig_p = px.bar(df_p_f, x='Producto', y='Utilidad_Bruta', color='Margen_Pct', 
                              title="Utilidad por Producto (S/)", color_continuous_scale='Viridis')
                st.plotly_chart(fig_p, use_container_width=True)

    # --- TAB 2: COBRANZA (Demora + Filtros + Scatter) ---
    with t2:
        st.subheader("🤝 Estado de Cobranza y Riesgo")
        if not df_v_raw.empty:
            df_c = df_v_raw.copy()
            df_c['Cliente_Nom'] = df_c['clientes'].apply(lambda x: x['nombre_comercial'])
            
            pagos_clean = df_pag_raw.groupby('venta_id')['monto_pagado'].sum().reset_index(name='Total_Pagado')
            df_c = df_c.merge(pagos_clean, left_on='id', right_on='venta_id', how='left').fillna(0)
            df_c['fecha'] = pd.to_datetime(df_c['fecha']).dt.tz_localize(None)
            df_c['Demora'] = (datetime.now() - df_c['fecha']).dt.days
            
            df_c_grp = df_c.groupby('Cliente_Nom').agg({'total': 'sum', 'Total_Pagado': 'sum', 'Demora': 'max'}).reset_index()
            df_c_grp['Deuda_Valor'] = (df_c_grp['total'] - df_c_grp['Total_Pagado']).round(2)
            df_c_grp['Deuda_Pct'] = ((df_c_grp['Deuda_Valor'] / df_c_grp['total']) * 100).round(2)

            # Filtro Dinámico
            lista_c = sorted(df_c_grp['Cliente_Nom'].unique().tolist())
            sel_c = st.multiselect("🔍 Filtrar Clientes:", lista_c, default=lista_c)
            df_c_f = df_c_grp[df_c_grp['Cliente_Nom'].isin(sel_c)]

            if not df_c_f.empty:
                st.dataframe(df_c_f.style.format({
                    'total': 'S/ {:.2f}', 'Total_Pagado': 'S/ {:.2f}', 'Deuda_Valor': 'S/ {:.2f}', 
                    'Deuda_Pct': '{:.2f}%', 'Demora': '{:.0f} días'
                }), use_container_width=True, hide_index=True)

                fig_c = px.scatter(df_c_f, x='Demora', y='Deuda_Valor', size='total', color='Deuda_Pct',
                                  hover_name='Cliente_Nom', title="Riesgo: Demora (Días) vs Deuda (S/)", color_continuous_scale='Reds')
                st.plotly_chart(fig_c, use_container_width=True)

    # --- TAB 3: VENDEDORES (Rendimiento + Margen %) ---
    with t3:
        st.subheader("🥇 Ranking de Vendedores")
        if not df_v_raw.empty:
            df_v_base = df_v_raw.copy()
            df_det_v = df_dv_raw.copy()
            df_det_v['costo_t'] = df_det_v['cantidad'] * df_det_v['productos'].apply(lambda x: x['costo'])
            costos_tick = df_det_v.groupby('venta_id')['costo_t'].sum().reset_index(name='Costo_Ticket')
            df_v_base = df_v_base.merge(costos_tick, left_on='id', right_on='venta_id', how='left').fillna(0)
            
            v_stats = df_v_base.groupby('vendedor').agg({'total': 'sum', 'Costo_Ticket': 'sum', 'cliente_id': 'nunique'}).reset_index()
            v_stats.columns = ['Vendedor', 'Ventas', 'Costo_Total', 'Clientes_Atendidos']
            v_stats['Utilidad_Bruta'] = (v_stats['Ventas'] - v_stats['Costo_Total']).round(2)
            v_stats['Margen_Pct'] = ((v_stats['Utilidad_Bruta'] / v_stats['Ventas']) * 100).round(2)

            # Filtro Dinámico
            lista_v = sorted(v_stats['Vendedor'].unique().tolist())
            sel_v = st.multiselect("🔍 Filtrar Vendedores:", lista_v, default=lista_v)
            v_f = v_stats[v_stats['Vendedor'].isin(sel_v)]

            if not v_f.empty:
                st.dataframe(v_f[['Vendedor', 'Ventas', 'Utilidad_Bruta', 'Margen_Pct', 'Clientes_Atendidos']].style.format({
                    'Ventas': 'S/ {:.2f}', 'Utilidad_Bruta': 'S/ {:.2f}', 'Margen_Pct': '{:.2f}%'
                }), use_container_width=True, hide_index=True)

                fig_v = px.bar(v_f, x='Vendedor', y='Ventas', text='Utilidad_Bruta', color='Margen_Pct', title="Ventas y Utilidad por Vendedor")
                st.plotly_chart(fig_v, use_container_width=True)

    # --- EXPORTACIÓN MAESTRA ---
    st.sidebar.divider()
    if not df_p_raw.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_p_raw.to_excel(writer, index=False, sheet_name='STOCK')
            if 'df_c_grp' in locals(): df_c_grp.to_excel(writer, index=False, sheet_name='COBRANZA')
            if 'v_stats' in locals(): v_stats.to_excel(writer, index=False, sheet_name='DESEMPEÑO')
            for s in writer.sheets: writer.sheets[s].set_column('A:Z', 22)
        st.sidebar.download_button("💾 Descargar Todo en Excel", output.getvalue(), f"Reporte_{datetime.now().strftime('%Y%m%d')}.xlsx")