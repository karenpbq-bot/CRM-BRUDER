# ==========================================
# MÓDULO: CLIENTES (modulos/m_clientes.py)
# VERSIÓN: PROTECCIÓN CONTRA DUPLICADOS Y NULOS
# ==========================================
import streamlit as st
import pandas as pd
import time

def mostrar(conectar):
    st.header("👥 Gestión Estratégica de Clientes")
    supabase = conectar()
    
    t1, t2, t3 = st.tabs(["🆕 Maestro de Clientes", "📍 Gestión de Sedes", "🔍 Buscador de Cartera"])

    # --- PESTAÑA 1: MAESTRO DE CLIENTES (REGISTRO Y EDICIÓN) ---
    with t1:
        st.subheader("Catálogo de Clientes")
        # Carga de datos actuales
        res_c = supabase.table("clientes").select("id, nombre_comercial, ruc_dni, rubro, contacto_nombre").execute()
        df_c = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()
        
        col_m1, col_m2 = st.columns([1, 2])
        modo_c = col_m1.radio("Acción Cliente:", ["Registrar Nuevo", "Editar Existente"], horizontal=True, key="m_cli_opt")
        
        id_c, v_nom, v_ruc, v_rub, v_con = None, "", "", "", ""

        if modo_c == "Editar Existente" and not df_c.empty:
            sel_c = st.selectbox("🔍 CLIENTE EXISTENTE:", 
                                ["-- SELECCIONE --"] + 
                                df_c.apply(lambda r: f"ID {r['id']} | {r['nombre_comercial']}", axis=1).tolist())
            if sel_c != "-- SELECCIONE --":
                id_c = int(sel_c.split(" | ")[0].replace("ID ", ""))
                c_data = df_c[df_c['id'] == id_c].iloc[0]
                v_nom, v_ruc, v_rub, v_con = c_data['nombre_comercial'], c_data['ruc_dni'], c_data['rubro'], c_data['contacto_nombre']

        with st.form("form_maestro_cliente"):
            st.write(f"### {'📝 Editando: ' + str(v_nom) if id_c else '✨ Nuevo Registro'}")
            c1, c2 = st.columns(2)
            nom_f = c1.text_input("Razón Social / Nombre Comercial", value=v_nom).upper().strip()
            ruc_f = c2.text_input("RUC / DNI (Obligatorio)", value=v_ruc).strip()
            
            c3, c4 = st.columns(2)
            rub_f = c3.text_input("Rubro (ej. Taller, Lubricentro)", value=v_rub).upper().strip()
            con_f = c4.text_input("Nombre de Contacto Principal", value=v_con).upper().strip()

            if st.form_submit_button("💾 Guardar Cambios"):
                if not ruc_f:
                    st.error("❌ El RUC o DNI es obligatorio.")
                elif not nom_f:
                    st.error("❌ El nombre comercial es obligatorio.")
                else:
                    datos = {"nombre_comercial": nom_f, "ruc_dni": ruc_f, "rubro": rub_f, "contacto_nombre": con_f}
                    try:
                        if id_c:
                            supabase.table("clientes").update(datos).eq("id", id_c).execute()
                            st.success(f"✅ Cliente {nom_f} actualizado.")
                        else:
                            supabase.table("clientes").insert(datos).execute()
                            st.success(f"✅ Cliente {nom_f} registrado con éxito.")
                        
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        if "23505" in str(e):
                            st.error(f"⚠️ El RUC/DNI '{ruc_f}' ya está registrado con otro cliente.")
                        else:
                            st.error(f"❌ Error: {e}")

    # --- PESTAÑA 2: GESTIÓN DE SEDES ---
    with t2:
        st.subheader("Sedes y Puntos de Entrega")
        res_list = supabase.table("clientes").select("id, nombre_comercial").execute()
        c_list = pd.DataFrame(res_list.data) if res_list.data else pd.DataFrame()
        
        if not c_list.empty:
            target_c = st.selectbox("Seleccione Cliente para sus sedes:", ["--"] + sorted(c_list['nombre_comercial'].tolist()))
            
            if target_c != "--":
                id_target = int(c_list[c_list['nombre_comercial'] == target_c]['id'].iloc[0])
                res_s = supabase.table("sucursales").select("*").eq("cliente_id", id_target).execute()
                sedes_actuales = pd.DataFrame(res_s.data) if res_s.data else pd.DataFrame()
                
                modo_s = st.radio("Acción Sede:", ["Añadir Nueva Sede", "Editar Sede Existente"], horizontal=True)
                id_s, s_nom, s_dir, s_dis, s_prv, s_zon, s_ven, s_tel, s_con = None, "", "", "", "AREQUIPA", "", "", "", ""

                if modo_s == "Editar Sede Existente" and not sedes_actuales.empty:
                    sel_s = st.selectbox("Seleccione Sede:", sedes_actuales['nombre_sede'].tolist())
                    s_data = sedes_actuales[sedes_actuales['nombre_sede'] == sel_s].iloc[0]
                    id_s = s_data['id']
                    s_nom, s_dir, s_dis, s_prv = s_data['nombre_sede'], s_data['direccion'], s_data['distrito'], s_data['provincia']
                    s_zon, s_ven, s_tel, s_con = s_data['zona'], s_data['vendedor_asignado'], s_data['telefono1'], s_data['contacto_sede']

                res_u = supabase.table("usuarios").select("nombre").neq("rol", "Administrador").execute()
                lista_responsables = sorted([u['nombre'] for u in res_u.data]) if res_u.data else []

                with st.form("form_sede_final"):
                    c_sd1, c_sd2 = st.columns(2)
                    sn_f = c_sd1.text_input("Nombre de Sede", value=s_nom).upper().strip()
                    sd_f = c_sd2.text_input("Dirección", value=s_dir).upper().strip()
                    
                    f1, f2, f3 = st.columns(3)
                    pr_f = f1.text_input("Provincia", value=s_prv).upper()
                    di_f = f2.text_input("Distrito", value=s_dis).upper()
                    zo_f = f3.text_input("Zona", value=s_zon).upper()
                    
                    v1, v2, v3 = st.columns(3)
                    idx_v = lista_responsables.index(s_ven) + 1 if s_ven in lista_responsables else 0
                    ven_f = v1.selectbox("Vendedor Asignado", ["-- SIN ASIGNAR --"] + lista_responsables, index=idx_v)
                    tel_f = v2.text_input("Teléfono", value=s_tel)
                    cs_f = v3.text_input("Contacto Sede", value=s_con).upper().strip()

                    if st.form_submit_button("💾 Guardar Sede"):
                        if sn_f and sd_f:
                            datos_s = {
                                "cliente_id": id_target, "nombre_sede": sn_f, "direccion": sd_f,
                                "distrito": di_f, "provincia": pr_f, "zona": zo_f,
                                "vendedor_asignado": ven_f if ven_f != "-- SIN ASIGNAR --" else "", 
                                "telefono1": tel_f, "contacto_sede": cs_f
                            }
                            if id_s:
                                supabase.table("sucursales").update(datos_s).eq("id", id_s).execute()
                            else:
                                supabase.table("sucursales").insert(datos_s).execute()
                            st.success("✅ Sede guardada."); time.sleep(1); st.rerun()
                        else:
                            st.error("Nombre y dirección son obligatorios.")

    # --- PESTAÑA 3: BUSCADOR ---
    with t3:
        st.subheader("🔍 Buscador de Cartera Detallado")
        res_full = supabase.table("sucursales").select("nombre_sede, distrito, vendedor_asignado, clientes(nombre_comercial, contacto_nombre, rubro)").execute()
        if res_full.data:
            df_full = pd.DataFrame([ {
                "Cliente": r['clientes']['nombre_comercial'], "Rubro": r['clientes']['rubro'],
                "Contacto": r['clientes']['contacto_nombre'], "Sede": r['nombre_sede'],
                "Distrito": r['distrito'], "Responsable": r['vendedor_asignado']
            } for r in res_full.data ])
            
            b_text = st.text_input("Buscar por Nombre o Sede:").upper()
            if b_text:
                df_full = df_full[df_full.apply(lambda row: b_text in str(row['Cliente']) or b_text in str(row['Sede']), axis=1)]
            st.dataframe(df_full, use_container_width=True, hide_index=True)