# ==========================================
# SECCIÓN: IMPORTACIONES Y ARQUITECTURA (NUBE)
# ==========================================
import streamlit as st
from supabase import create_client, Client
import sys
import os
import time # Añadido para los retardos de éxito

# Asegura la detección del paquete modulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importación de módulos
from modulos import m_dashboard, m_inventario, m_clientes, m_ventas, m_agenda, m_estadisticas, m_login, m_usuarios

# Asegúrate de que el archivo 'logo_crm.png' esté en la misma carpeta que app.py
st.set_page_config(
    page_title="CRM Lubricantes", 
    page_icon="logo_crm.png", # <--- Aquí cambiamos el emoji por tu archivo
    layout="wide"
)

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = "https://amazezckxnvsglkoaygl.supabase.co"
SUPABASE_KEY = "sb_publishable_tFgB3zR46aRobZPDBZ1wiQ_XxVfgg3t" 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def conectar():
    return supabase

m_login.inicializar_usuarios(conectar)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_rol = None
    st.session_state.user_name = None

# GESTIÓN DE NAVEGACIÓN (Para evitar borrado accidental de estados)
if 'menu_previo' not in st.session_state:
    st.session_state.menu_previo = None

if not st.session_state.logged_in:
    m_login.login_form(conectar)
else:
    with st.sidebar:
        # --- SECCIÓN DE LOGO PERSONALIZADO ---
        # Asegúrate de que el archivo se llame 'logo_crm.png' y esté en la raíz
        try:
            # Usamos columnas para centrar el logo ligeramente
            col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
            with col2:
                st.image("logo_crm.png", use_container_width=True)
        except Exception:
            st.write("🌸") # Respaldo si no encuentra el archivo

        # --- ACTUALIZACIÓN DE NOMBRE ---
        st.title("CRM Lubricantes") 
        st.write(f"👤 **Usuario:** {st.session_state.user_name}")
        st.caption(f"Rol: {st.session_state.user_rol}")
        st.divider()

        # --- MENÚ DE OPCIONES ---
        if st.session_state.user_rol == "Administrador":
            opciones_finales = ["📊 Dashboard", "📦 Inventario", "👥 Clientes", "💰 Ventas", "🗓️ Agenda", "📈 Estadísticas", "👤 Usuarios"]
        elif st.session_state.user_rol == "Gerente":
            opciones_finales = ["📊 Dashboard", "📦 Inventario", "👥 Clientes", "💰 Ventas", "🗓️ Agenda", "📈 Estadísticas"]
        elif st.session_state.user_rol == "Vendedor":
            opciones_finales = ["📦 Inventario", "💰 Ventas", "🗓️ Agenda"]

        opcion = st.radio("Menú Principal", opciones_finales)
        st.divider()
        m_login.logout()

    # --- LÓGICA DE ENRUTAMIENTO ---
    # Limpiar estados de ventas SOLO si venimos de otro menú
    if opcion == "💰 Ventas" and st.session_state.menu_previo != "💰 Ventas":
        claves_v = ['cli_sel', 'carrito', 'edit_id', 'id_ed_final', 'id_ed_maestro']
        for k in claves_v:
            if k in st.session_state: del st.session_state[k]
    
    # Actualizar rastro de navegación
    st.session_state.menu_previo = opcion

    if opcion == "📊 Dashboard":
        m_dashboard.mostrar(conectar)
    elif opcion == "📦 Inventario":
        m_inventario.mostrar(conectar)
    elif opcion == "👥 Clientes":
        m_clientes.mostrar(conectar)
    elif opcion == "💰 Ventas":
        m_ventas.mostrar(conectar)
    elif opcion == "🗓️ Agenda":
        m_agenda.mostrar(conectar)
    elif opcion == "📈 Estadísticas":
        m_estadisticas.mostrar(conectar)
    elif opcion == "👤 Usuarios":
        m_usuarios.mostrar(conectar)