# ==========================================
# MÓDULO: GESTIÓN DE USUARIOS (modulos/m_usuarios.py)
# VERSIÓN: SUPABASE CLOUD - INTEGRAL
# ==========================================
import streamlit as st
import pandas as pd
import time

def mostrar(conectar):
    st.header("🔐 Configuración de Accesos y Roles")
    supabase = conectar()

    # Solo el Administrador puede gestionar usuarios
    if st.session_state.user_rol != "Administrador":
        st.warning("Acceso restringido. Solo el Administrador puede gestionar cuentas.")
        return

    t1, t2 = st.tabs(["👥 Lista de Usuarios", "➕ Crear/Editar Usuario"])

    # 1. Obtener lista de usuarios desde la nube
    res = supabase.table("usuarios").select("id, usuario, nombre, rol, password").execute()
    df_usuarios = pd.DataFrame(res.data) if res.data else pd.DataFrame()

    # --- PESTAÑA 1: LISTA DE USUARIOS ---
    with t1:
        if not df_usuarios.empty:
            # Mostramos la tabla sin la contraseña por seguridad
            st.dataframe(df_usuarios[['id', 'usuario', 'nombre', 'rol']], 
                         use_container_width=True, hide_index=True)
            
            # Opción de eliminación rápida
            id_borrar = st.number_input("ID de usuario a eliminar:", min_value=1, step=1, key="del_user")
            if st.button("🗑️ Eliminar Usuario"):
                if id_borrar == 1:
                    st.error("No se puede eliminar al administrador principal.")
                else:
                    supabase.table("usuarios").delete().eq("id", id_borrar).execute()
                    st.success("Usuario eliminado.")
                    time.sleep(1); st.rerun()
        else:
            st.info("No hay usuarios registrados.")

    # --- PESTAÑA 2: CREAR / EDITAR USUARIO ---
    with t2:
        modo = st.radio("Acción:", ["Nuevo", "Editar"], horizontal=True)
        
        id_u, u_user, u_nom, u_rol, u_pass = None, "", "", "Vendedor", ""

        if modo == "Editar" and not df_usuarios.empty:
            sel = st.selectbox("Seleccione usuario:", df_usuarios['usuario'].tolist())
            u_data = df_usuarios[df_usuarios['usuario'] == sel].iloc[0]
            id_u, u_user, u_nom, u_rol, u_pass = u_data['id'], u_data['usuario'], u_data['nombre'], u_data['rol'], u_data['password']

        with st.form("form_usuarios"):
            c1, c2 = st.columns(2)
            new_user = c1.text_input("Usuario (Login)", value=u_user)
            new_pass = c2.text_input("Contraseña", value=u_pass, type="password")
            
            c3, c4 = st.columns(2)
            new_nom = c3.text_input("Nombre Completo", value=u_nom).upper()
            new_rol = c4.selectbox("Rol en el Sistema", ["Vendedor", "Gerente", "Administrador"], 
                                  index=["Vendedor", "Gerente", "Administrador"].index(u_rol))
            
            if st.form_submit_button("💾 Guardar Usuario"):
                if new_user and new_pass and new_nom:
                    datos = {
                        "usuario": new_user,
                        "password": new_pass,
                        "nombre": new_nom,
                        "rol": new_rol
                    }
                    try:
                        if id_u:
                            supabase.table("usuarios").update(datos).eq("id", id_u).execute()
                        else:
                            supabase.table("usuarios").insert(datos).execute()
                        st.success("✅ Usuario sincronizado en la nube.")
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Error: El nombre de usuario ya podría existir.")
                else:
                    st.error("Por favor complete todos los campos.")