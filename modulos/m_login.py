# =========================================================
# SECCIÓN 1: IMPORTACIONES Y CONFIGURACIÓN
# =========================================================
import streamlit as st
import time
import os

def inicializar_usuarios(conectar):
    """Inicializa variables de sesión si no existen."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'user_rol' not in st.session_state:
        st.session_state.user_rol = None

# =========================================================
# SECCIÓN 2: IDENTIDAD VISUAL (Logo y Branding)
# =========================================================
def login_form(conectar):
    # CSS para forzar que el contenido suba al borde superior de la pantalla
    st.markdown("""
        <style>
            .block-container {padding-top: 1rem !important;}
        </style>
    """, unsafe_allow_html=True)

    # --- EL LOGO: Pegado arriba a la izquierda ---
    col_logo, _ = st.columns([0.15, 0.9])
    with col_logo:
        try:
            # Envolvemos en un div para subirlo más que el margen de Streamlit
            st.markdown('<div style="margin-top: -45px; margin-left: -10px;">', unsafe_allow_html=True)
            st.image("logo_crm.png", width=60)
            st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.write("🌸")

    # --- EL NOMBRE: Centrado absoluto y pegado al divider ---
    st.markdown(
        """
        <div style='text-align: center; margin-top: -75px; margin-bottom: -15px;'>
            <h1 style='margin: 0; padding: 0; color: #1E1E1E; font-size: 2.8rem; font-weight: bold; line-height: 1;'>
                BRUDER PERU
            </h1>
            <p style='margin: 0; padding: 0; color: #5E5E5E; font-size: 1.2rem; letter-spacing: 1px;'>
                CRM Lubricantes
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    st.divider()

# =========================================================
# SECCIÓN 3: ESTILOS DEL FORMULARIO
# =========================================================
    st.markdown("""
        <style>
        .login-box {
            background-color: #f0f2f6;
            padding: 2rem;
            border-radius: 10px;
            border: 1px solid #d1d3d4;
        }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# SECCIÓN 4: LÓGICA DE ACCESO (Supabase Cloud)
# =========================================================
    with st.container():
        st.markdown("<h3 style='text-align: center;'>🔐 Acceso al Sistema</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Ingrese sus credenciales para continuar</p>", unsafe_allow_html=True)
        
        # Centramos el formulario usando columnas
        _, col_central, _ = st.columns([0.2, 0.6, 0.2])
        
        with col_central:
            with st.form("login_form_bruder"):
                # Agregamos KEY únicas para bloquear el autollenado molesto
                user_input = st.text_input("Usuario", key="user_bruder_2026")
                pass_input = st.text_input("Contraseña", type="password", key="pass_bruder_2026")
                submit = st.form_submit_button("Ingresar al Sistema", use_container_width=True)

                if submit:
                    supabase = conectar()
                    try:
                        res = supabase.table("usuarios")\
                            .select("usuario, rol, nombre")\
                            .eq("usuario", user_input)\
                            .eq("password", pass_input)\
                            .execute()

                        if res.data and len(res.data) > 0:
                            usuario_db = res.data[0]
                            st.session_state.logged_in = True
                            st.session_state.user_name = usuario_db['nombre']
                            st.session_state.user_rol = usuario_db['rol']
                            
                            st.success(f"✅ Bienvenido/a {usuario_db['nombre']}")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Usuario o contraseña incorrectos")
                    
                    except Exception as e:
                        st.error(f"⚠️ Error de conexión: {str(e)}")

# =========================================================
# SECCIÓN 5: CIERRE DE SESIÓN
# =========================================================
def logout():
    """Finaliza la sesión del usuario."""
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_name = None
        st.session_state.user_rol = None
        st.rerun()