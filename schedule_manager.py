import json
import os
import uuid
import streamlit as st

DAYS_OF_WEEK = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- Detección y Configuración de Nube (Google Sheets) ---

def is_cloud_configured():
    """Verifica si las credenciales de Google Sheets están configuradas en los Secrets."""
    try:
        # En Streamlit local, si no existe el archivo secrets.toml, 
        # acceder a st.secrets lanza un StreamlitSecretNotFoundError.
        return "gcp_service_account" in st.secrets and "spreadsheet_url" in st.secrets
    except Exception:
        return False

def get_sheets_client():
    """Inicializa y retorna el cliente de gspread usando las credenciales secretas."""
    import gspread
    try:
        # Obtener una copia de las credenciales de secrets
        creds = {k: v for k, v in st.secrets["gcp_service_account"].items()}
        
        # Limpieza de comillas accidentales
        for key in creds:
            if isinstance(creds[key], str):
                val = creds[key].strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1].strip()
                creds[key] = val
                
        # Limpiar clave privada
        if "private_key" in creds:
            pk = creds["private_key"]
            pk = pk.replace("\\n", "\n")
            creds["private_key"] = pk
            
        return gspread.service_account_from_dict(creds)
    except Exception as e:
        # Diagnóstico visual seguro para el usuario en caso de error
        pk_info = "No encontrada"
        if "gcp_service_account" in st.secrets and "private_key" in st.secrets["gcp_service_account"]:
            raw_pk = st.secrets["gcp_service_account"]["private_key"]
            starts_ok = raw_pk.startswith("-----BEGIN PRIVATE KEY-----")
            ends_ok = raw_pk.strip().endswith("-----END PRIVATE KEY-----")
            has_escaped_n = "\\n" in raw_pk
            has_real_newline = "\n" in raw_pk
            length = len(raw_pk)
            pk_info = f"Largo: {length} chars | Inicia cabecera ok: {starts_ok} | Termina pie ok: {ends_ok} | Contiene '\\n' texto: {has_escaped_n} | Contiene enter real: {has_real_newline}"
        
        st.error(f"⚙️ Diagnóstico de tu Secreto en Streamlit:\n{pk_info}")
        raise e

def get_worksheet(sheet_name):
    """Obtiene una pestaña de la hoja de cálculo de Google. Si no existe, la crea con su cabecera."""
    client = get_sheets_client()
    sh = client.open_by_url(st.secrets["spreadsheet_url"])
    try:
        return sh.worksheet(sheet_name)
    except Exception:
        # Si no existe la pestaña, la creamos con las columnas correctas incluyendo 'username'
        if sheet_name == "Clases":
            ws = sh.add_worksheet(title="Clases", rows="1000", cols="9")
            ws.append_row(["username", "id", "name", "professor", "classroom", "day", "start_time", "end_time", "color"])
            return ws
        elif sheet_name == "Notas":
            ws = sh.add_worksheet(title="Notas", rows="1000", cols="5")
            ws.append_row(["username", "subject", "name", "weight", "grade"])
            return ws
        elif sheet_name == "Usuarios":
            ws = sh.add_worksheet(title="Usuarios", rows="1000", cols="2")
            ws.append_row(["username", "password_hash"])
            return ws

# --- Gestión de Cuentas de Usuario ---

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users():
    """Carga los usuarios y sus hashes de contraseña."""
    if is_cloud_configured():
        try:
            ws = get_worksheet("Usuarios")
            records = ws.get_all_records()
            return {str(r["username"]).strip().lower(): str(r["password_hash"]) for r in records if "username" in r and "password_hash" in r}
        except Exception as e:
            st.error(f"Error cargando usuarios desde Google Sheets: {e}")
            return {}
    else:
        if not os.path.exists(USERS_FILE):
            return {}
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

def save_users(users_data):
    """Guarda los usuarios y sus hashes de contraseña."""
    if is_cloud_configured():
        try:
            ws = get_worksheet("Usuarios")
            ws.clear()
            ws.append_row(["username", "password_hash"])
            rows = []
            for user, phash in users_data.items():
                rows.append([user.strip().lower(), phash])
            if rows:
                ws.append_rows(rows)
            return True
        except Exception as e:
            st.error(f"Error al guardar usuarios en Google Sheets: {e}")
            return False
    else:
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

def register_user(username, password):
    """Registra un nuevo usuario con su contraseña hashed."""
    users = load_users()
    user_lower = username.strip().lower()
    if user_lower in users:
        return False
    import hashlib
    phash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    users[user_lower] = phash
    return save_users(users)

def verify_user(username, password):
    """Verifica si el usuario y la contraseña coinciden."""
    users = load_users()
    user_lower = username.strip().lower()
    if user_lower not in users:
        return False
    import hashlib
    phash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return users[user_lower] == phash

# --- Gestión del Horario (Schedule) ---

def get_local_schedule_path(username):
    """Genera la ruta del archivo JSON local para el usuario específico."""
    safe_user = "".join([c for c in username if c.isalnum() or c in ("-", "_")]).strip().lower()
    if not safe_user:
        safe_user = "default"
    return os.path.join(os.path.dirname(__file__), f"schedule_{safe_user}.json")

def load_schedule(username):
    """Carga el horario de un usuario. En la nube filtra por su columna; en local lee su JSON."""
    if not username:
        return []
    
    if is_cloud_configured():
        try:
            ws = get_worksheet("Clases")
            all_records = ws.get_all_records()
            # Filtrar solo los registros que corresponden al usuario
            user_records = [r for r in all_records if str(r.get("username", "")).strip().lower() == username.strip().lower()]
            return user_records
        except Exception as e:
            st.error(f"Error cargando horario desde Google Sheets: {e}")
            return []
    else:
        # Fallback local
        local_file = get_local_schedule_path(username)
        if not os.path.exists(local_file):
            return []
        try:
            with open(local_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar el archivo local: {e}")
            return []

def save_schedule(username, schedule):
    """Guarda el horario de un usuario. En la nube actualiza sus filas; en local escribe su JSON."""
    if not username:
        return False
        
    if is_cloud_configured():
        try:
            ws = get_worksheet("Clases")
            all_records = ws.get_all_records()
            
            # Filtrar y MANTENER los registros de otros usuarios
            other_users_records = [
                r for r in all_records 
                if str(r.get("username", "")).strip().lower() != username.strip().lower()
            ]
            
            # Limpiar la hoja y reescribir todo
            ws.clear()
            ws.append_row(["username", "id", "name", "professor", "classroom", "day", "start_time", "end_time", "color"])
            
            rows_to_write = []
            # Agregar los de otros usuarios
            for r in other_users_records:
                rows_to_write.append([
                    r["username"], r["id"], r["name"], r["professor"], 
                    r["classroom"], r["day"], r["start_time"], r["end_time"], r["color"]
                ])
                
            # Agregar los nuevos del usuario actual
            for c in schedule:
                rows_to_write.append([
                    username.strip().lower(), c["id"], c["name"], c["professor"],
                    c["classroom"], c["day"], c["start_time"], c["end_time"], c["color"]
                ])
                
            if rows_to_write:
                ws.append_rows(rows_to_write)
            return True
        except Exception as e:
            st.error(f"Error al guardar en Google Sheets: {e}")
            return False
    else:
        # Guardado local
        local_file = get_local_schedule_path(username)
        try:
            with open(local_file, "w", encoding="utf-8") as f:
                json.dump(schedule, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Error al guardar archivo local: {e}")
            return False

def add_class(username, name, professor, classroom, day, start_time, end_time, color="#1f77b4"):
    """Agrega una nueva clase al horario de un usuario."""
    schedule = load_schedule(username)
    new_class = {
        "id": str(uuid.uuid4()),
        "name": name,
        "professor": professor,
        "classroom": classroom,
        "day": day,
        "start_time": start_time,
        "end_time": end_time,
        "color": color
    }
    schedule.append(new_class)
    if save_schedule(username, schedule):
        return new_class
    return None

def delete_class(username, class_id):
    """Elimina una clase por su ID para un usuario específico."""
    schedule = load_schedule(username)
    initial_length = len(schedule)
    schedule = [c for c in schedule if c["id"] != class_id]
    
    if len(schedule) < initial_length:
        return save_schedule(username, schedule)
    return False

def update_class(username, class_id, updated_data):
    """Actualiza los datos de una clase existente por su ID para un usuario específico."""
    schedule = load_schedule(username)
    for c in schedule:
        if c["id"] == class_id:
            c.update(updated_data)
            return save_schedule(username, schedule)
    return False

# --- Gestión de Notas (Grades) ---

def get_local_grades_path(username):
    """Genera la ruta del archivo JSON local de notas para el usuario específico."""
    safe_user = "".join([c for c in username if c.isalnum() or c in ("-", "_")]).strip().lower()
    if not safe_user:
        safe_user = "default"
    return os.path.join(os.path.dirname(__file__), f"grades_{safe_user}.json")

def load_grades(username):
    """Carga las notas de un usuario."""
    if not username:
        return {}
        
    if is_cloud_configured():
        try:
            ws = get_worksheet("Notas")
            all_records = ws.get_all_records()
            
            # Filtrar solo las notas del usuario actual
            user_records = [r for r in all_records if str(r.get("username", "")).strip().lower() == username.strip().lower()]
            
            grades = {}
            for r in user_records:
                subj = r["subject"]
                if subj not in grades:
                    grades[subj] = []
                grades[subj].append({
                    "name": r["name"],
                    "weight": float(r["weight"]),
                    "grade": float(r["grade"])
                })
            return grades
        except Exception as e:
            st.error(f"Error cargando notas desde Google Sheets: {e}")
            return {}
    else:
        # Fallback local
        local_file = get_local_grades_path(username)
        if not os.path.exists(local_file):
            return {}
        try:
            with open(local_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar notas locales: {e}")
            return {}

def save_grades(username, grades_data):
    """Guarda las notas de un usuario."""
    if not username:
        return False
        
    if is_cloud_configured():
        try:
            ws = get_worksheet("Notas")
            all_records = ws.get_all_records()
            
            # Filtrar y MANTENER las notas de otros usuarios
            other_users_records = [
                r for r in all_records 
                if str(r.get("username", "")).strip().lower() != username.strip().lower()
            ]
            
            ws.clear()
            ws.append_row(["username", "subject", "name", "weight", "grade"])
            
            rows_to_write = []
            # Agregar los de otros usuarios
            for r in other_users_records:
                rows_to_write.append([
                    r["username"], r["subject"], r["name"], r["weight"], r["grade"]
                ])
                
            # Agregar las nuevas notas del usuario actual
            for subj, items in grades_data.items():
                for item in items:
                    rows_to_write.append([
                        username.strip().lower(), subj, item["name"], item["weight"], item["grade"]
                    ])
                    
            if rows_to_write:
                ws.append_rows(rows_to_write)
            return True
        except Exception as e:
            st.error(f"Error al guardar notas en Google Sheets: {e}")
            return False
    else:
        # Guardado local
        local_file = get_local_grades_path(username)
        try:
            with open(local_file, "w", encoding="utf-8") as f:
                json.dump(grades_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Error al guardar notas locales: {e}")
            return False

# --- Cuadrículas y Formateo ---

def get_empty_calendar_grid():
    """Crea una estructura de cuadrícula vacía para los días de la semana y horas."""
    hours = [f"{h:02d}:00" for h in range(6, 23)]
    grid = {day: {hour: [] for hour in hours} for day in DAYS_OF_WEEK}
    return grid

def populate_calendar_grid(classes):
    """Llena la cuadrícula de calendario con las clases cargadas."""
    grid = get_empty_calendar_grid()
    for c in classes:
        day = c["day"]
        start_hour = int(c["start_time"].split(":")[0])
        end_hour = int(c["end_time"].split(":")[0])
        
        # Llenar cada bloque de hora correspondiente
        for h in range(start_hour, end_hour):
            hour_str = f"{h:02d}:00"
            if day in grid and hour_str in grid[day]:
                grid[day][hour_str].append(c)
    return grid

# --- Generador de PDF (ReportLab) ---

def generate_pdf_schedule(username, schedule):
    """Genera un archivo PDF binario en orientación horizontal (Landscape A4) con el horario del usuario."""
    import io
    import datetime
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors as pdf_colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    
    # Documento A4 Horizontal con márgenes de 0.4 pulgadas para maximizar espacio
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=0.4*inch,
        leftMargin=0.4*inch,
        topMargin=0.4*inch,
        bottomMargin=0.4*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos de párrafos
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=pdf_colors.HexColor('#1E293B'),
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        textColor=pdf_colors.HexColor('#64748B'),
        spaceAfter=10
    )
    cell_header_style = ParagraphStyle(
        'CellHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        alignment=1, # Centrado
        textColor=pdf_colors.HexColor('#FFFFFF')
    )
    cell_time_style = ParagraphStyle(
        'CellTime',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        alignment=1, # Centrado
        textColor=pdf_colors.HexColor('#334155')
    )
    cell_class_name_style = ParagraphStyle(
        'CellClassName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        alignment=1,
        textColor=pdf_colors.HexColor('#1E293B'),
        spaceAfter=1
    )
    cell_class_detail_style = ParagraphStyle(
        'CellClassDetail',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        alignment=1,
        textColor=pdf_colors.HexColor('#334155')
    )
    
    # Encabezado del documento
    now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"📅 Horario Universitario de Clases", title_style))
    elements.append(Paragraph(f"Usuario / Estudiante: <b>{username}</b> &nbsp;&nbsp;|&nbsp;&nbsp; Fecha de emisión: {now_str}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=pdf_colors.HexColor('#CBD5E1'), spaceAfter=8))
    
    if not schedule:
        elements.append(Paragraph("No hay clases registradas en el horario.", styles['Normal']))
    else:
        # Calcular rango de horas
        start_hours = [int(c["start_time"].split(":")[0]) for c in schedule]
        end_hours = [int(c["end_time"].split(":")[0]) for c in schedule]
        min_hour = max(6, min(start_hours) - 1)
        max_hour = min(22, max(end_hours) + 1)
        hours_range = [f"{h:02d}:00" for h in range(min_hour, max_hour)]
        
        has_sunday = any(c["day"] == "Domingo" for c in schedule)
        active_days = DAYS_OF_WEEK if has_sunday else DAYS_OF_WEEK[:-1]
        
        # Mapear matriz [día][hora]
        grid = {d: {h: [] for h in hours_range} for d in active_days}
        for c in schedule:
            c_day = c["day"]
            if c_day not in grid:
                continue
            c_start = int(c["start_time"].split(":")[0])
            c_end = int(c["end_time"].split(":")[0])
            for h in range(c_start, c_end):
                h_str = f"{h:02d}:00"
                if h_str in grid[c_day]:
                    grid[c_day][h_str].append(c)
                    
        # Construir datos de la tabla ReportLab
        table_data = []
        header_row = [Paragraph("Hora", cell_header_style)]
        for d in active_days:
            header_row.append(Paragraph(d, cell_header_style))
        table_data.append(header_row)
        
        table_cell_styles = [
            ('BACKGROUND', (0,0), (-1,0), pdf_colors.HexColor('#1E293B')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, pdf_colors.HexColor('#CBD5E1')),
            ('BACKGROUND', (0,1), (0,-1), pdf_colors.HexColor('#F1F5F9')),
        ]
        
        for r_idx, h_str in enumerate(hours_range, start=1):
            row = [Paragraph(h_str, cell_time_style)]
            for c_idx, d in enumerate(active_days, start=1):
                classes_in_cell = grid[d][h_str]
                if not classes_in_cell:
                    row.append("")
                else:
                    cell_elements = []
                    cell_bg = None
                    for cls in classes_in_cell:
                        cell_elements.append(Paragraph(cls['name'], cell_class_name_style))
                        cell_elements.append(Paragraph(f"📍 {cls['classroom']} | 👤 {cls['professor']}", cell_class_detail_style))
                        raw_color = cls.get('color', '#A2C4C9')
                        try:
                            cell_bg = pdf_colors.HexColor(raw_color)
                        except Exception:
                            cell_bg = pdf_colors.HexColor('#A2C4C9')
                    
                    row.append(cell_elements)
                    if cell_bg:
                        table_cell_styles.append(('BACKGROUND', (c_idx, r_idx), (c_idx, r_idx), cell_bg))
                        
            table_data.append(row)
            
        # Anchos de columna
        available_width = 10.8 * inch # A4 Landscape printable width
        time_col_w = 0.8 * inch
        day_col_w = (available_width - time_col_w) / len(active_days)
        col_widths = [time_col_w] + [day_col_w] * len(active_days)
        
        t_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        t_table.setStyle(TableStyle(table_cell_styles))
        elements.append(t_table)
        
        # Pie de página / Métricas
        elements.append(Spacer(1, 8))
        total_hours = sum(int(c["end_time"].split(":")[0]) - int(c["start_time"].split(":")[0]) for c in schedule)
        unique_mats = len(set(c["name"].lower().strip() for c in schedule))
        metrics_p = Paragraph(f"<b>Total Asignaturas:</b> {unique_mats} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Total Horas Semanales:</b> {total_hours} hrs", subtitle_style)
        elements.append(metrics_p)
        
    doc.build(elements)
    pdf_val = buffer.getvalue()
    buffer.close()
    return pdf_val

# --- Gestión de Banners Personalizados ---

def get_user_banner_path(username):
    """Genera la ruta del archivo de configuración del banner personalizado para un usuario."""
    safe_user = "".join([c for c in username if c.isalnum() or c in ("-", "_")]).strip().lower()
    if not safe_user:
        safe_user = "default"
    return os.path.join(os.path.dirname(__file__), f"banner_{safe_user}.txt")

def load_user_banner(username):
    """Carga la URL o ruta del banner personalizado para el usuario actual."""
    if not username:
        return None
    banner_file = get_user_banner_path(username)
    if os.path.exists(banner_file):
        try:
            with open(banner_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return content if content else None
        except Exception:
            return None
    return None

def save_user_banner(username, banner_val):
    """Guarda o limpia la URL del banner personalizado para el usuario actual."""
    if not username:
        return False
    banner_file = get_user_banner_path(username)
    try:
        with open(banner_file, "w", encoding="utf-8") as f:
            f.write(banner_val.strip() if banner_val else "")
        return True
    except Exception as e:
        print(f"Error al guardar banner: {e}")
        return False
