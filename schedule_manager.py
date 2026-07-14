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
    # Obtener una copia editable de las credenciales de secrets
    creds = {k: v for k, v in st.secrets["gcp_service_account"].items()}
    
    # Limpieza robusta: eliminar comillas accidentales que el usuario pudiera copiar del JSON original
    for key in creds:
        if isinstance(creds[key], str):
            val = creds[key].strip()
            # Si tiene comillas dobles o simples al inicio y al final, las removemos
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1].strip()
            creds[key] = val
            
    # Limpiar saltos de línea en la clave privada si vienen escapados como texto \n o \\n
    if "private_key" in creds:
        creds["private_key"] = creds["private_key"].replace("\\n", "\n").replace("\n", "\n")
        
    return gspread.service_account_from_dict(creds)

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
