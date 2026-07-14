import streamlit as st
import pandas as pd
import schedule_manager as sm
import importlib
importlib.reload(sm)

# Configuración de página
st.set_page_config(
    page_title="Mi Horario Universitario",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Función de Cálculo de Contraste Dinámico (W3C Standard) ---
def get_contrast_text_color(hex_color):
    """Calcula el color de texto (oscuro o claro) de alto contraste según la luminancia del fondo."""
    if not hex_color or not isinstance(hex_color, str):
        return "#1E293B"
    clean_hex = hex_color.lstrip('#')
    if len(clean_hex) == 6:
        try:
            r, g, b = int(clean_hex[0:2], 16), int(clean_hex[2:4], 16), int(clean_hex[4:6], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#1E293B" if luminance > 0.55 else "#FFFFFF"
        except ValueError:
            return "#1E293B"
    return "#1E293B"

# --- Función de Temas Personalizados Dinámicos ---
def apply_custom_theme(theme_name):
    themes = {
        "Tema Claro ☀️": {
            "bg": "#F8F9FA",
            "sidebar_bg": "#E9ECEF",
            "text": "#1E293B",
            "primary": "#2A6F97",
            "input_bg": "#FFFFFF",
            "input_text": "#1E293B",
            "input_border": "#CED4DA",
            "table_th_bg": "#E2E8F0",
            "table_th_text": "#1E293B",
            "table_td_bg": "#FFFFFF",
            "table_td_border": "#E2E8F0",
            "time_col_bg": "#F1F5F9",
            "time_col_text": "#475569"
        },
        "Tema Oscuro 🌙": {
            "bg": "#0B0F19",
            "sidebar_bg": "#111827",
            "text": "#F8FAFC",
            "primary": "#00F5D4",
            "input_bg": "#1F2937",
            "input_text": "#F8FAFC",
            "input_border": "#374151",
            "table_th_bg": "#1F2937",
            "table_th_text": "#F8FAFC",
            "table_td_bg": "#111827",
            "table_td_border": "#374151",
            "time_col_bg": "#1F2937",
            "time_col_text": "#9CA3AF"
        }
    }
    t = themes.get(theme_name, themes["Tema Claro ☀️"])
    
    st.markdown(f"""
        <style>
        :root {{
            --primary-color: {t['primary']} !important;
            --background-color: {t['bg']} !important;
            --secondary-background-color: {t['sidebar_bg']} !important;
            --text-color: {t['text']} !important;
        }}
        .stApp {{
            background-color: {t['bg']} !important;
            color: {t['text']} !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: {t['sidebar_bg']} !important;
        }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {{
            color: {t['text']} !important;
        }}
        /* Entradas de texto, números y selectores */
        input, select, textarea, div[data-baseweb="select"] > div {{
            background-color: {t['input_bg']} !important;
            color: {t['input_text']} !important;
            border-color: {t['input_border']} !important;
        }}
        input::placeholder, textarea::placeholder {{
            color: {t['input_text']} !important;
            opacity: 0.65 !important;
        }}
        /* Menús desplegables y opciones */
        ul[data-baseweb="menu"], div[data-baseweb="popover"], div[role="listbox"] {{
            background-color: {t['input_bg']} !important;
            color: {t['input_text']} !important;
        }}
        ul[data-baseweb="menu"] *, div[data-baseweb="popover"] *, div[role="listbox"] * {{
            color: {t['input_text']} !important;
        }}
        li[data-baseweb="option"], div[role="option"] {{
            color: {t['input_text']} !important;
            background-color: {t['input_bg']} !important;
        }}
        li[data-baseweb="option"]:hover, div[role="option"]:hover {{
            background-color: {t['sidebar_bg']} !important;
        }}
        /* Botones secundarios (como Restablecer o Cerrar Sesión) */
        div[data-testid="stButton"] button {{
            background-color: {t['input_bg']} !important;
            color: {t['input_text']} !important;
            border: 1px solid {t['input_border']} !important;
            font-weight: 600 !important;
        }}
        div[data-testid="stButton"] button p, div[data-testid="stButton"] button span {{
            color: {t['input_text']} !important;
        }}
        /* Botones primarios (Guardar, Iniciar Sesión, etc.) */
        div[data-testid="stButton"] button[kind="primary"], button[data-testid="baseButton-primary"] {{
            background-color: {t['primary']} !important;
            color: #FFFFFF !important;
            border: none !important;
        }}
        div[data-testid="stButton"] button[kind="primary"] p, button[data-testid="baseButton-primary"] p {{
            color: #FFFFFF !important;
        }}
        /* Archivos subidos (File Uploader preview y zona de arrastre) */
        [data-testid="stFileUploader"] section {{
            background-color: {t['input_bg']} !important;
            border: 1px dashed {t['input_border']} !important;
        }}
        [data-testid="stFileUploader"] section * {{
            color: {t['input_text']} !important;
        }}
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {{
            background-color: {t['sidebar_bg']} !important;
            border: 1px solid {t['input_border']} !important;
        }}
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] * {{
            color: {t['text']} !important;
        }}
        /* Expanders (Acordeones) */
        details[data-testid="stExpander"] {{
            background-color: {t['sidebar_bg']} !important;
            border: 1px solid {t['input_border']} !important;
            border-radius: 8px !important;
        }}
        details[data-testid="stExpander"] summary {{
            background-color: {t['sidebar_bg']} !important;
        }}
        details[data-testid="stExpander"] summary * {{
            color: {t['text']} !important;
        }}
        /* Párrafos, Títulos y Etiquetas */
        .stMarkdown, h1, h2, h3, h4, h5, h6, label, p, span {{
            color: {t['text']};
        }}
        .main .block-container {{
            padding-top: 2rem;
        }}
        /* Pestañas */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 16px;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 48px;
            background-color: {t['sidebar_bg']};
            border-radius: 6px 6px 0px 0px;
            font-weight: 600;
            color: {t['text']} !important;
            border: 1px solid {t['input_border']};
            border-bottom: none;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {t['bg']} !important;
            color: {t['primary']} !important;
            border-bottom: 3px solid {t['primary']} !important;
        }}
        /* Contenedores st.metric */
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
            color: {t['text']} !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    return t

# Selector de Temas en el Panel Lateral
st.sidebar.header("🎨 Apariencia y Tema")
theme_options = ["Tema Claro ☀️", "Tema Oscuro 🌙"]
selected_theme_name = st.sidebar.selectbox("Selecciona un tema visual", theme_options, key="active_theme_select")
active_theme = apply_custom_theme(selected_theme_name)

# --- Personalización de Banner ---
active_user = st.session_state.get("username", "")
current_user_banner = sm.load_user_banner(active_user) if active_user else None

with st.sidebar.expander("🖼️ Personalizar mi Banner"):
    if st.session_state.get("authenticated", False):
        st.caption("Pega el enlace (URL) de una imagen o sube un archivo.")
        banner_url_input = st.text_input("URL de Imagen", value=current_user_banner if current_user_banner and not current_user_banner.startswith("data:") else "", placeholder="https://ejemplo.com/mi_banner.jpg", key="banner_url_input")
        uploaded_banner = st.file_uploader("O sube una imagen (.jpg, .png)", type=["jpg", "png", "jpeg", "webp"], key="user_banner_upload")
        
        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            if st.button("Guardar Banner", key="save_banner_btn", type="primary"):
                val_to_save = ""
                if uploaded_banner is not None:
                    import base64
                    bytes_data = uploaded_banner.getvalue()
                    b64_str = base64.b64encode(bytes_data).decode("utf-8")
                    mime_type = uploaded_banner.type
                    val_to_save = f"data:{mime_type};base64,{b64_str}"
                elif banner_url_input.strip():
                    val_to_save = banner_url_input.strip()
                
                if val_to_save:
                    sm.save_user_banner(st.session_state.username, val_to_save)
                    st.success("¡Banner guardado!")
                    st.rerun()
                else:
                    st.error("Ingresa una URL o sube una imagen.")
        with col_b2:
            if st.button("Restablecer", key="reset_banner_btn"):
                sm.save_user_banner(st.session_state.username, "")
                st.info("Banner restablecido.")
                st.rerun()
    else:
        st.info("Ingresa a tu sesión para personalizar tu banner personal.")

# --- Renderizado de Banner y Título ---
import os
if current_user_banner:
    st.image(current_user_banner, use_container_width=True)
else:
    banner_path = os.path.join(os.path.dirname(__file__), "app_banner.jpg")
    if os.path.exists(banner_path):
        st.image(banner_path, use_container_width=True)

st.title("📅 Horario Universitario Interactivo")
st.markdown("Gestiona tus asignaturas, profesores, aulas y visualiza tu semana académica de manera sencilla y moderna.")

# --- Gestión de Sesión de Usuario ---
st.sidebar.header("🔑 Sesión de Usuario")

# Inicializar sesión
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Botón de Cerrar Sesión si ya está autenticado
if st.session_state.authenticated:
    st.sidebar.write(f"Sesión activa: **{st.session_state.username}**")
    if st.sidebar.button("Cerrar Sesión", type="secondary"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        if "classes" in st.session_state:
            del st.session_state["classes"]
        if "grades_data" in st.session_state:
            del st.session_state["grades_data"]
        st.session_state.needs_reload_classes = True
        st.session_state.needs_reload_grades = True
        st.rerun()
else:
    # Ingresar el nombre del usuario
    username_input = st.sidebar.text_input(
        "Ingresa tu Usuario / Código*",
        value="",
        placeholder="Ej. santiago123",
        help="Escribe un identificador único."
    ).strip().lower()
    
    if username_input:
        users = sm.load_users()
        if username_input in users:
            # El usuario existe, pedimos contraseña
            st.sidebar.info("Este usuario ya existe. Ingresa tu contraseña:")
            password = st.sidebar.text_input("Contraseña*", type="password", key="login_pass")
            if st.sidebar.button("Iniciar Sesión", type="primary"):
                if sm.verify_user(username_input, password):
                    st.session_state.username = username_input
                    st.session_state.authenticated = True
                    st.session_state.needs_reload_classes = True
                    st.session_state.needs_reload_grades = True
                    st.success("¡Sesión iniciada con éxito!")
                    st.rerun()
                else:
                    st.sidebar.error("Contraseña incorrecta.")
        else:
            # El usuario es nuevo, pedimos definir contraseña
            st.sidebar.warning("¡Usuario nuevo detectado! Define tu contraseña para proteger tu horario:")
            password = st.sidebar.text_input("Define tu contraseña*", type="password", key="reg_pass")
            if st.sidebar.button("Registrar y Entrar", type="primary"):
                if not password:
                    st.sidebar.error("Por favor, define una contraseña.")
                else:
                    if sm.register_user(username_input, password):
                        st.session_state.username = username_input
                        st.session_state.authenticated = True
                        st.session_state.needs_reload_classes = True
                        st.session_state.needs_reload_grades = True
                        st.sidebar.success("¡Usuario registrado y autenticado!")
                        st.rerun()
                    else:
                        st.sidebar.error("Error al registrar el usuario.")

# Si no está autenticado, mostramos pantalla de bienvenida
if not st.session_state.authenticated:
    st.info("👋 ¡Bienvenido! Ingresa tu usuario en la barra lateral para ver o crear tu horario.")
    st.markdown("""
    ### ¿Cómo empezar?
    Esta aplicación es **multiusuario y segura**. Para gestionar tu propio horario de clases y calificaciones de forma privada:
    
    1. Ve a la sección **🔑 Sesión de Usuario** en el panel izquierdo.
    2. Escribe tu nombre de usuario, alias o código (ej. `santiago123`).
    3. Si eres nuevo, el sistema te pedirá **definir una contraseña**.
    4. Si ya te registraste, te pedirá **ingresar tu contraseña** para desbloquear tus datos.
    
    *Tu información se almacenará de manera totalmente independiente y protegida, nadie más podrá ver tus clases a menos que conozca tu contraseña.*
    """)
    st.stop()

# Cargar clases existentes para el usuario activo (usando caché en session_state)
if "classes" not in st.session_state or st.session_state.get("needs_reload_classes", True):
    st.session_state.classes = sm.load_schedule(st.session_state.username)
    st.session_state.needs_reload_classes = False

classes = st.session_state.classes

# Sidebar: Acciones de gestión (Agregar / Eliminar clases)
st.sidebar.header("🛠️ Gestión de Clases")

# Formulario para agregar una clase
with st.sidebar.expander("➕ Agregar Nueva Clase", expanded=True):
    # Selector de asignatura con autocompletado
    existing_names = sorted(list(set(c["name"] for c in classes))) if classes else []
    name_options = ["[Escribir nueva...]"] + existing_names
    name_choice = st.selectbox("Asignatura*", name_options, key="add_name_choice")
    if name_choice == "[Escribir nueva...]":
        name = st.text_input("Escribe el nombre de la Asignatura*", placeholder="Ej. Cálculo Multivariable", key="add_name_new")
    else:
        name = name_choice
    
    # Selector de profesor con autocompletado
    existing_professors = sorted(list(set(c["professor"] for c in classes))) if classes else []
    prof_options = ["[Escribir nuevo...]"] + existing_professors
    prof_choice = st.selectbox("Profesor*", prof_options, key="add_prof_choice")
    if prof_choice == "[Escribir nuevo...]":
        professor = st.text_input("Escribe el nombre del Profesor*", placeholder="Ej. Ing. Carlos Gómez", key="add_prof_new")
    else:
        professor = prof_choice
        
    # Selector de aula con autocompletado
    existing_classrooms = sorted(list(set(c["classroom"] for c in classes))) if classes else []
    room_options = ["[Escribir nuevo...]"] + existing_classrooms
    room_choice = st.selectbox("Lugar / Aula*", room_options, key="add_room_choice")
    if room_choice == "[Escribir nuevo...]":
        classroom = st.text_input("Escribe el Lugar / Aula*", placeholder="Ej. Edificio C - Aula 204", key="add_room_new")
    else:
        classroom = room_choice

    day = st.selectbox("Día de la semana", sm.DAYS_OF_WEEK, key="add_day")
    
    # Opciones de horario en intervalos de horas completas
    hours_options = [f"{h:02d}:00" for h in range(6, 23)]
    start_time = st.selectbox("Hora de Inicio", hours_options[:-1], index=2, key="add_start")
    end_time = st.selectbox("Hora de Fin", hours_options[1:], index=3, key="add_end")
    
    # Paleta de colores predefinida (Pasteles Femeninos y Modernos)
    colors = {
        "Rosa Pastel 🌸": "#FFB7B2",
        "Azul Menta 🌊": "#A2C4C9",
        "Verde Menta 🌿": "#B5EAD7",
        "Lavanda Pastel 🪻": "#C7CEEA",
        "Durazno Pastel 🍑": "#FFDAC1",
        "Amarillo Pastel ☀️": "#FFF5BA",
        "Rosa Chicle 💖": "#FF9AA2",
        "Malva Soft 🪷": "#E8AEB7"
    }
    color_name = st.selectbox("Color de la tarjeta", list(colors.keys()), key="add_color")
    selected_color = colors[color_name]
    
    if st.button("Agregar al Horario", key="add_submit_btn", type="primary"):
        if not name or not professor or not classroom:
            st.error("Por favor completa los campos obligatorios (*).")
        else:
            start_hour = int(start_time.split(":")[0])
            end_hour = int(end_time.split(":")[0])
            
            if end_hour <= start_hour:
                st.error("La hora de fin debe ser posterior a la de inicio.")
            else:
                # -- IDEA 1: Sistema Anti-Choques --
                has_collision = False
                for c in classes:
                    if c["day"] == day:
                        c_start = int(c["start_time"].split(":")[0])
                        c_end = int(c["end_time"].split(":")[0])
                        # Dos intervalos chocan si max(inicio1, inicio2) < min(fin1, fin2)
                        if max(c_start, start_hour) < min(c_end, end_hour):
                            has_collision = True
                            st.error(f"🚨 Choque de horario: Esta clase coincide con '{c['name']}' de {c['start_time']} a {c['end_time']}.")
                            break
                
                if not has_collision:
                    new_cls = sm.add_class(st.session_state.username, name, professor, classroom, day, start_time, end_time, selected_color)
                    if new_cls:
                        st.session_state.needs_reload_classes = True
                        st.success(f"¡{name} agregada correctamente!")
                        st.rerun()
                    else:
                        st.error("No se pudo guardar la clase.")

# Opción para editar clases
if classes:
    with st.sidebar.expander("✏️ Editar una Clase"):
        class_to_edit = st.selectbox(
            "Selecciona la clase a editar",
            options=classes,
            format_func=lambda x: f"{x['name']} - {x['day']} ({x['start_time']} a {x['end_time']})",
            key="edit_select"
        )
        cls_id = class_to_edit["id"]
        
        # Asignatura con autocompletado en edición
        existing_names = sorted(list(set(c["name"] for c in classes))) if classes else []
        name_options = ["[Escribir nueva...]"] + existing_names
        try:
            name_index = name_options.index(class_to_edit["name"])
        except ValueError:
            name_index = 0
            
        edit_name_choice = st.selectbox("Nombre de la Asignatura*", name_options, index=name_index, key=f"edit_name_choice_{cls_id}")
        if edit_name_choice == "[Escribir nueva...]":
            edit_name = st.text_input("Escribe el nombre de la Asignatura*", value=class_to_edit["name"], key=f"edit_name_new_{cls_id}")
        else:
            edit_name = edit_name_choice
        
        # Profesor con autocompletado
        existing_professors = sorted(list(set(c["professor"] for c in classes))) if classes else []
        prof_options = ["[Escribir nuevo...]"] + existing_professors
        
        try:
            prof_index = prof_options.index(class_to_edit["professor"])
        except ValueError:
            prof_index = 0
            
        edit_prof_choice = st.selectbox("Profesor*", prof_options, index=prof_index, key=f"edit_prof_choice_{cls_id}")
        if edit_prof_choice == "[Escribir nuevo...]":
            edit_professor = st.text_input("Escribe el nombre del Profesor*", value=class_to_edit["professor"], key=f"edit_prof_new_{cls_id}")
        else:
            edit_professor = edit_prof_choice
            
        # Aula con autocompletado
        existing_classrooms = sorted(list(set(c["classroom"] for c in classes))) if classes else []
        room_options = ["[Escribir nuevo...]"] + existing_classrooms
        
        try:
            room_index = room_options.index(class_to_edit["classroom"])
        except ValueError:
            room_index = 0
            
        edit_room_choice = st.selectbox("Lugar / Aula*", room_options, index=room_index, key=f"edit_room_choice_{cls_id}")
        if edit_room_choice == "[Escribir nuevo...]":
            edit_classroom = st.text_input("Escribe el Lugar / Aula*", value=class_to_edit["classroom"], key=f"edit_room_new_{cls_id}")
        else:
            edit_classroom = edit_room_choice
            
        day_index = sm.DAYS_OF_WEEK.index(class_to_edit["day"]) if class_to_edit["day"] in sm.DAYS_OF_WEEK else 0
        edit_day = st.selectbox("Día de la semana", sm.DAYS_OF_WEEK, index=day_index, key=f"edit_day_{cls_id}")
        
        # Horas
        hours_options = [f"{h:02d}:00" for h in range(6, 23)]
        try:
            start_index = hours_options.index(class_to_edit["start_time"])
        except ValueError:
            start_index = 2
            
        try:
            end_index = hours_options.index(class_to_edit["end_time"])
        except ValueError:
            end_index = 3
            
        edit_start_time = st.selectbox("Hora de Inicio", hours_options[:-1], index=min(start_index, len(hours_options)-2), key=f"edit_start_{cls_id}")
        edit_end_time = st.selectbox("Hora de Fin", hours_options[1:], index=min(max(0, end_index-1), len(hours_options)-2), key=f"edit_end_{cls_id}")
        
        edit_color = st.color_picker("Color de la tarjeta", value=class_to_edit["color"], key=f"edit_color_{cls_id}")
        
        if st.button("Guardar Cambios", key=f"edit_save_btn_{cls_id}", type="primary"):
            if not edit_name or not edit_professor or not edit_classroom:
                st.error("Por favor completa los campos obligatorios (*).")
            else:
                start_hour = int(edit_start_time.split(":")[0])
                end_hour = int(edit_end_time.split(":")[0])
                
                if end_hour <= start_hour:
                    st.error("La hora de fin debe ser posterior a la de inicio.")
                else:
                    updated_data = {
                        "name": edit_name,
                        "professor": edit_professor,
                        "classroom": edit_classroom,
                        "day": edit_day,
                        "start_time": edit_start_time,
                        "end_time": edit_end_time,
                        "color": edit_color
                    }
                    if sm.update_class(st.session_state.username, cls_id, updated_data):
                        st.session_state.needs_reload_classes = True
                        st.success("¡Clase actualizada correctamente!")
                        st.rerun()
                    else:
                        st.error("No se pudo actualizar la clase.")

# Opción para eliminar clases
if classes:
    with st.sidebar.expander("❌ Eliminar una Clase"):
        class_to_delete = st.selectbox(
            "Selecciona la clase a eliminar",
            options=classes,
            format_func=lambda x: f"{x['name']} - {x['day']} ({x['start_time']} a {x['end_time']})",
            key="delete_select"
        )
        if st.button("Eliminar Seleccionada", type="secondary", key="delete_submit_btn"):
            if sm.delete_class(st.session_state.username, class_to_delete["id"]):
                st.session_state.needs_reload_classes = True
                st.success(f"Clase '{class_to_delete['name']}' eliminada.")
                st.rerun()
            else:
                st.error("Error al eliminar la clase.")
else:
    st.sidebar.info("Agrega clases para habilitar opciones de edición/eliminación.")


# Pestañas principales
tab_calendar, tab_list, tab_stats, tab_grades = st.tabs([
    "📅 Vista Semanal", 
    "📋 Lista Detallada", 
    "📊 Estadísticas y Utilidades",
    "🧮 Simulador de Notas"
])

# pestaña 1: Vista Semanal (Calendario interactivo en HTML)
with tab_calendar:
    st.subheader("📅 Horario de la Semana")
    
    def generate_html_schedule(classes_list, t):
        if not classes_list:
            return """
            <div style='text-align: center; padding: 40px; border: 2px dashed #ccc; border-radius: 8px; margin-top: 20px;'>
                <h3 style='color: #6c757d;'>Tu horario está vacío</h3>
                <p style='color: #8c969e;'>Utiliza el panel de la izquierda para agregar tus asignaturas, profesores y aulas.</p>
            </div>
            """
        
        # Encontrar el rango de horas activo de todas las clases para no mostrar celdas vacías innecesarias
        start_hours = [int(c["start_time"].split(":")[0]) for c in classes_list]
        end_hours = [int(c["end_time"].split(":")[0]) for c in classes_list]
        
        min_hour = max(6, min(start_hours) - 1)
        max_hour = min(22, max(end_hours) + 1)
        
        hours_range = [f"{h:02d}:00" for h in range(min_hour, max_hour)]
        
        # Días a mostrar (se excluye el domingo si no hay clases en ese día para optimizar espacio)
        has_sunday = any(c["day"] == "Domingo" for c in classes_list)
        active_days = sm.DAYS_OF_WEEK if has_sunday else sm.DAYS_OF_WEEK[:-1]
        
        # Mapear clases en una estructura de consulta rápida [día][hora]
        grid = {d: {h: [] for h in hours_range} for d in active_days}
        for c in classes_list:
            c_day = c["day"]
            if c_day not in grid:
                continue
            c_start = int(c["start_time"].split(":")[0])
            c_end = int(c["end_time"].split(":")[0])
            for h in range(c_start, c_end):
                h_str = f"{h:02d}:00"
                if h_str in grid[c_day]:
                    grid[c_day][h_str].append(c)
        
        # Estilos y encabezado dinámicos según el tema activo
        html = f"""
        <style>
            .schedule-container {{
                overflow-x: auto;
                margin-top: 15px;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            }}
            .schedule-table {{
                width: 100%;
                border-collapse: collapse;
                font-family: 'Inter', -apple-system, sans-serif;
                overflow: hidden;
            }}
            .schedule-table th {{
                background-color: {t['table_th_bg']};
                color: {t['table_th_text']};
                text-align: center;
                padding: 16px;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                border-bottom: 3px solid {t['primary']};
            }}
            .schedule-table td {{
                border: 1px solid {t['table_td_border']};
                padding: 6px;
                text-align: center;
                height: 80px;
                vertical-align: middle;
                font-size: 13px;
                background-color: {t['table_td_bg']};
            }}
            .time-col {{
                background-color: {t['time_col_bg']} !important;
                font-weight: 700;
                width: 110px;
                color: {t['time_col_text']} !important;
                font-size: 12px;
                border-right: 2px solid {t['table_td_border']} !important;
            }}
            .class-card {{
                border-radius: 8px;
                padding: 10px;
                color: #1E293B;
                font-weight: 600;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: flex-start;
                text-align: left;
                height: 100%;
                min-height: 60px;
                transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
                border-left: 4px solid rgba(0, 0, 0, 0.2);
            }}
            .class-card:hover {{
                transform: translateY(-3px) scale(1.02);
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.25);
                filter: brightness(1.08);
            }}
            .class-name {{
                font-size: 13px;
                font-weight: 700;
                margin-bottom: 4px;
                word-wrap: break-word;
                letter-spacing: 0.3px;
                line-height: 1.2;
            }}
            .class-details {{
                font-size: 11px;
                opacity: 0.9;
                line-height: 1.3;
                margin-top: 1px;
                font-weight: 400;
            }}
        </style>

        <div class="schedule-container">
            <table class="schedule-table">
                <thead>
                    <tr>
                        <th>Hora</th>
        """
        for d in active_days:
            html += f"<th>{d}</th>"
        html += "</tr></thead><tbody>"
        
        # Renderizar filas
        for h_str in hours_range:
            h_val = int(h_str.split(":")[0])
            time_label = f"{h_str} - {h_val+1:02d}:00"
            html += f"<tr><td class='time-col'>{time_label}</td>"
            
            for d in active_days:
                classes_in_slot = grid[d][h_str]
                if classes_in_slot:
                    # En caso de que coincidan materias (cruce), las apilamos
                    html += "<td style='padding: 4px;'>"
                    for c_slot in classes_in_slot:
                        card_bg = c_slot.get('color', '#A2C4C9')
                        text_color = get_contrast_text_color(card_bg)
                        html += f"""
                        <div class="class-card" style="background-color: {card_bg}; color: {text_color} !important; margin-bottom: 2px;">
                            <div class="class-name" style="color: {text_color} !important;">{c_slot['name']}</div>
                            <div class="class-details" style="color: {text_color} !important;">👤 {c_slot['professor']}</div>
                            <div class="class-details" style="color: {text_color} !important;">📍 {c_slot['classroom']}</div>
                        </div>
                        """
                    html += "</td>"
                else:
                    html += "<td></td>"
            html += "</tr>"
            
        html += "</tbody></table></div>"
        return html

    st.markdown(generate_html_schedule(classes, active_theme), unsafe_allow_html=True)
    
    if classes:
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        col_pdf1, col_pdf2 = st.columns([1, 1])
        with col_pdf1:
            try:
                pdf_bytes = sm.generate_pdf_schedule(st.session_state.username, classes)
                st.download_button(
                    label="📄 Descargar Horario en PDF (A4 Horizontal)",
                    data=pdf_bytes,
                    file_name=f"horario_{st.session_state.username}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error al generar PDF: {e}")
        with col_pdf2:
            st.markdown("""
                <button onclick="window.print()" style="
                    width: 100%;
                    background-color: #475569;
                    color: white;
                    border: none;
                    padding: 9px 16px;
                    font-size: 14px;
                    font-weight: 600;
                    border-radius: 6px;
                    cursor: pointer;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                ">
                    🖨️ Imprimir / Guardar en Navegador
                </button>
            """, unsafe_allow_html=True)

# pestaña 2: Lista Detallada
with tab_list:
    st.subheader("📋 Listado de Clases Registradas")
    if classes:
        df_classes = pd.DataFrame(classes)
        # Renombrar columnas para una presentación más amigable
        df_display = df_classes[["name", "professor", "classroom", "day", "start_time", "end_time"]].copy()
        df_display.columns = ["Asignatura", "Profesor", "Lugar / Aula", "Día", "Inicio", "Fin"]
        
        # Filtros de búsqueda rápidos
        search_query = st.text_input("🔍 Buscar por asignatura, profesor o aula", "").lower()
        if search_query:
            filtered_df = df_display[
                df_display["Asignatura"].str.lower().str.contains(search_query) |
                df_display["Profesor"].str.lower().str.contains(search_query) |
                df_display["Lugar / Aula"].str.lower().str.contains(search_query)
            ]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.dataframe(df_display, use_container_width=True)
            
        # Opción para exportar a CSV
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Horario a CSV",
            data=csv_data,
            file_name="mi_horario_universitario.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay asignaturas para mostrar en la lista. Agrega algunas desde el panel lateral.")

# pestaña 3: Estadísticas e Utilidades
with tab_stats:
    st.subheader("📊 Resumen Académico")
    if classes:
        # Calcular horas totales de clase por semana
        total_hours = 0
        for c in classes:
            start_h = int(c["start_time"].split(":")[0])
            end_h = int(c["end_time"].split(":")[0])
            total_hours += (end_h - start_h)
            
        col1, col2, col3 = st.columns(3)
        with col1:
            # Contar de forma insensible a mayúsculas/minúsculas y espacios
            unique_subjects_count = len(set(c["name"].strip().lower() for c in classes))
            st.metric(label="Total Asignaturas", value=unique_subjects_count)
        with col2:
            st.metric(label="Total Horas de Clase a la Semana", value=f"{total_hours} hrs")
        with col3:
            st.metric(label="Días con Clases", value=len(set(c["day"] for c in classes)))
            
        # Listado rápido de profesores y sus aulas (agrupado de forma insensible a mayúsculas/minúsculas)
        st.markdown("### 📍 Directorio de Clases Rápido")
        prof_map = {}
        for c in classes:
            # Buscar el nombre exacto de la primera ocurrencia registrada para conservar la estética
            canonical_name = next(x["name"] for x in classes if x["name"].lower().strip() == c["name"].lower().strip())
            
            if canonical_name not in prof_map:
                prof_map[canonical_name] = {
                    "Profesor": c["professor"],
                    "Ubicación": c["classroom"]
                }
            else:
                # Si la ubicación del mismo ramo es diferente, las consolidamos visualmente
                curr_loc = prof_map[canonical_name]["Ubicación"]
                if c["classroom"] not in curr_loc.split(" / "):
                    prof_map[canonical_name]["Ubicación"] = f"{curr_loc} / {c['classroom']}"
                    
        st.json(prof_map)
        
        # --- IDEA 1: Gráficos Visuales de Carga Horaria ---
        st.markdown("---")
        st.subheader("📈 Análisis de Carga Horaria")
        
        daily_hours = {d: 0 for d in sm.DAYS_OF_WEEK}
        subject_hours = {}
        
        for c in classes:
            start_h = int(c["start_time"].split(":")[0])
            end_h = int(c["end_time"].split(":")[0])
            duration = end_h - start_h
            
            daily_hours[c["day"]] += duration
            
            canon_name = next(x["name"] for x in classes if x["name"].lower().strip() == c["name"].lower().strip())
            subject_hours[canon_name] = subject_hours.get(canon_name, 0) + duration
            
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("**Horas de clase por día**")
            df_daily = pd.DataFrame(list(daily_hours.items()), columns=["Día", "Horas"])
            df_daily = df_daily[df_daily["Horas"] > 0]
            st.bar_chart(df_daily.set_index("Día"))
            
        with col_chart2:
            st.markdown("**Distribución por Asignatura**")
            import altair as alt
            df_subj = pd.DataFrame(list(subject_hours.items()), columns=["Asignatura", "Horas"])
            chart = alt.Chart(df_subj).mark_arc(innerRadius=50).encode(
                theta="Horas:Q",
                color="Asignatura:N",
                tooltip=["Asignatura", "Horas"]
            ).properties(height=350)
            st.altair_chart(chart, use_container_width=True)
            
        # --- IDEA 2: Detector Automático de Huecos ---
        st.markdown("---")
        st.subheader("☕ Detector de Huecos (Tiempos Libres)")
        st.markdown("Estos son tus mejores momentos para estudiar, almorzar o descansar entre clases:")
        
        gaps_found = False
        
        for day in sm.DAYS_OF_WEEK:
            day_classes = [c for c in classes if c["day"] == day]
            if len(day_classes) > 1:
                # Ordenar por hora de inicio
                day_classes.sort(key=lambda x: int(x["start_time"].split(":")[0]))
                
                day_gaps = []
                for i in range(len(day_classes) - 1):
                    end_current = int(day_classes[i]["end_time"].split(":")[0])
                    start_next = int(day_classes[i+1]["start_time"].split(":")[0])
                    
                    if start_next > end_current:
                        gap_duration = start_next - end_current
                        day_gaps.append({
                            "start": f"{end_current:02d}:00",
                            "end": f"{start_next:02d}:00",
                            "duration": gap_duration,
                            "between": f"{day_classes[i]['name']} y {day_classes[i+1]['name']}"
                        })
                
                if day_gaps:
                    gaps_found = True
                    st.markdown(f"**{day}**")
                    for gap in day_gaps:
                        st.info(f"⏳ **{gap['duration']} hora(s)** libre(s) de **{gap['start']} a {gap['end']}** (Entre {gap['between']})")
                        
        if not gaps_found:
            st.success("¡Tu horario está súper compacto! No tienes huecos muertos entre clases.")

    else:
        st.info("Agrega clases para poder ver estadísticas y métricas de tu horario.")

# pestaña 4: Simulador de Notas
with tab_grades:
    st.subheader("🧮 Simulador de Notas")
    st.markdown("Calcula tu nota actual y descubre cuánto necesitas para aprobar. Tus notas se guardan localmente.")
    
    if not classes:
        st.info("Agrega clases en 'Gestionar Clases' primero.")
    else:
        # Extraer materias únicas, agrupando por nombre canónico
        unique_subjects = sorted(list(set(next(x["name"] for x in classes if x["name"].lower().strip() == c["name"].lower().strip()) for c in classes)))
        
        selected_subject = st.selectbox("Selecciona una materia", unique_subjects)
        
        # Carga optimizada con caché para evitar agotar la cuota de lectura del API de Google Sheets
        if "grades_data" not in st.session_state or st.session_state.get("needs_reload_grades", True):
            st.session_state.grades_data = sm.load_grades(st.session_state.username)
            st.session_state.needs_reload_grades = False
            
        grades_data = st.session_state.grades_data
        if selected_subject not in grades_data:
            grades_data[selected_subject] = []
            
        st.markdown(f"### Notas de {selected_subject}")
        
        with st.form("add_grade_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                eval_name = st.text_input("Evaluación (ej. Parcial 1)")
            with col2:
                eval_weight = st.number_input("Porcentaje (%)", min_value=1.0, max_value=100.0, step=1.0, value=30.0)
            with col3:
                eval_grade = st.number_input("Nota obtenida", min_value=0.0, max_value=5.0, step=0.1, value=0.0)
                
            submit_grade = st.form_submit_button("Agregar Nota")
            if submit_grade and eval_name:
                grades_data[selected_subject].append({
                    "name": eval_name,
                    "weight": eval_weight,
                    "grade": eval_grade
                })
                sm.save_grades(st.session_state.username, grades_data)
                st.session_state.needs_reload_grades = True
                st.success("Nota agregada correctamente.")
                st.rerun()
                
        if grades_data[selected_subject]:
            df_grades = pd.DataFrame(grades_data[selected_subject])
            df_grades["Aporte"] = (df_grades["grade"] * df_grades["weight"]) / 100
            
            # Mostrar tabla
            df_display_grades = df_grades.copy()
            df_display_grades.columns = ["Evaluación", "Peso (%)", "Nota", "Aporte a Definitiva"]
            st.dataframe(df_display_grades, use_container_width=True)
            
            current_sum = df_grades["Aporte"].sum()
            total_weight = df_grades["weight"].sum()
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Porcentaje Evaluado", f"{total_weight}%")
                st.metric("Nota Acumulada", f"{current_sum:.2f}")
                
            with col_b:
                if total_weight < 100:
                    needed_weight = 100 - total_weight
                    passing_grade = 3.0 # Nota mínima aprobatoria estándar
                    missing_points = passing_grade - current_sum
                    
                    if missing_points <= 0:
                        st.success("¡Felicidades! Ya tienes lo necesario para aprobar la materia. 🎉")
                    else:
                        needed_grade = (missing_points * 100) / needed_weight
                        if needed_grade > 5.0:
                            st.error(f"Necesitas sacar **{needed_grade:.2f}** en el {needed_weight}% restante. Matemáticamente no te alcanza. 💔")
                        else:
                            st.warning(f"Necesitas sacar al menos **{needed_grade:.2f}** en el {needed_weight}% restante para pasar (con 3.0).")
                else:
                    if current_sum >= 3.0:
                        st.success(f"¡Materia aprobada con {current_sum:.2f}! 🎉")
                    else:
                        st.error(f"Materia reprobada con {current_sum:.2f}. 💔")
                        
            # Sección para eliminar notas
            st.markdown("---")
            st.markdown("##### 🗑️ Gestionar Notas Registradas")
            col_del1, col_del2 = st.columns(2)
            
            with col_del1:
                # Armar opciones legibles para borrar notas individuales
                eval_options = [f"{i}: {item['name']} (Nota: {item['grade']}, Peso: {item['weight']}%)" for i, item in enumerate(grades_data[selected_subject])]
                selected_eval_to_delete = st.selectbox("Selecciona una nota para eliminar", eval_options, key="delete_eval_selectbox")
                if st.button("🗑️ Eliminar Nota Seleccionada", type="secondary", key="delete_single_eval_btn", use_container_width=True):
                    # Obtener el índice numérico
                    idx = int(selected_eval_to_delete.split(":")[0])
                    # Remover el elemento de la lista
                    grades_data[selected_subject].pop(idx)
                    sm.save_grades(st.session_state.username, grades_data)
                    st.session_state.needs_reload_grades = True
                    st.success("Nota eliminada correctamente.")
                    st.rerun()
                    
            with col_del2:
                # Espacio vacío para balancear el diseño y botón de limpiar todo
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🚨 Limpiar todas las notas", type="secondary", key="clear_all_grades_btn", use_container_width=True):
                    grades_data[selected_subject] = []
                    sm.save_grades(st.session_state.username, grades_data)
                    st.session_state.needs_reload_grades = True
                    st.success("Se eliminaron todas las notas de esta asignatura.")
                    st.rerun()
