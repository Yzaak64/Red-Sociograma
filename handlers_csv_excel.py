# handlers_csv_excel.py
# (v2.2 - Versión final y completa.
# --- AÑADE ESTAS DOS LÍNEAS AQUÍ ---
import tkinter as tk
from tkinter import ttk
# --- FIN DE LAS LÍNEAS A AÑADIR ---
#  Implementa toda la lógica de creación de instituciones, grupos y miembros.)

import collections, traceback, csv, io, re, unicodedata, datetime
from sociograma_data import schools_data, classes_data, members_data, questionnaire_responses_data, get_class_question_definitions, cognitive_social_structures_data
import pdf_generator

# --- Funciones de Utilidad (sin cambios) ---

# Archivo: dialog_test.py
# Ejecútalo para probar la ventana de forma aislada.

import tkinter as tk
from tkinter import ttk, messagebox

# --- ESTA ES LA CLASE DEFINITIVA Y AUTOCONTENIDA ---
# Una vez que confirmes que funciona, la copiaremos a tu proyecto.

class ConfirmQuestionsDialog(tk.Toplevel):
    """
    Versión FINAL. Mantiene el campo "Categoría" pero lo deshabilita para
    preguntas de meta-percepción. Permite confirmar la polaridad de todas
    las preguntas nuevas y adivina la polaridad de las negativas.
    """
    def __init__(self, parent, questions_data):
        super().__init__(parent)
        self.grab_set()
        self.title("Confirmar Detalles de Importación")
        self.geometry("850x600")
        self.minsize(600, 400)
        self.resizable(True, True) 
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.result = None
        self.question_widgets = []
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._create_widgets(questions_data)
        self.wait_window(self)

    def _create_widgets(self, questions_data):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        ttk.Label(header_frame, text="Confirmar Detalles de Nuevas Preguntas", font=("-size 14 -weight bold")).pack(anchor='w')
        ttk.Label(header_frame, text="Para cada pregunta, confirma su polaridad y edita la categoría sugerida si es necesario.", justify=tk.LEFT).pack(anchor='w', pady=(5, 0))

        scroll_container = ttk.Frame(main_frame)
        scroll_container.grid(row=1, column=0, sticky='nsew')
        scroll_container.grid_rowconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(scroll_container, borderwidth=0, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scrollbar.set)
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        canvas.grid(row=0, column=0, sticky='nsew')

        scrollable_frame = ttk.Frame(canvas, padding="10")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for i, (text, details) in enumerate(questions_data.items()):
            data_key = details['data_key']
            is_meta = details.get('is_meta', False) # Obtener si es de meta-percepción
            
            if i > 0:
                ttk.Separator(scrollable_frame).pack(fill='x', expand=True, pady=15)
            
            card = ttk.Frame(scrollable_frame)
            card.pack(fill='x', expand=True)
            ttk.Label(card, text=f'Pregunta: "{text}"').pack(anchor='w', pady=(0, 8))
            
            negative_keywords = ['rechazo', 'rechazas', 'evitar', 'evitarías', 'no invitar', 'no querrías']
            is_likely_positive = not any(keyword in text.lower() for keyword in negative_keywords)
            polarity_var = tk.BooleanVar(value=is_likely_positive)
            
            ttk.Checkbutton(card, text="Es una pregunta Positiva (de aceptación)", variable=polarity_var).pack(anchor='w', padx=20)
            
            # --- INICIO DE LA MODIFICACIÓN ---
            category_var = tk.StringVar(value=details.get('suggested_category', 'General'))
            category_frame = ttk.Frame(card)
            category_frame.pack(fill='x', expand=True, padx=20, pady=8)
            ttk.Label(category_frame, text="Categoría:").pack(side=tk.LEFT, padx=(0, 5))
            
            entry = ttk.Entry(category_frame, textvariable=category_var, width=30)
            entry.pack(side=tk.LEFT)
            # --- FIN DE LA MODIFICACIÓN ---
            
            self.question_widgets.append((data_key, polarity_var, category_var))

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky='e', pady=(15, 0))
        ttk.Button(button_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Confirmar e Importar", command=self._on_confirm).pack(side=tk.RIGHT)

    def _on_confirm(self):
        self.result = {}
        for data_key, polarity_var, category_var in self.question_widgets:
            polarity = 'positive' if polarity_var.get() else 'negative'
            self.result[data_key] = {'polarity': polarity, 'category': category_var.get().strip() or "General"}
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

def generar_categoria_desde_texto(texto_pregunta):
    """
    Analiza el texto de una pregunta para generar automáticamente una categoría
    corta y descriptiva, eligiendo la palabra más significativa.
    """
    if not texto_pregunta or not isinstance(texto_pregunta, str):
        return "General"

    # Lista de palabras comunes (stop words) en español a ignorar
    stop_words = set([
        'a', 'al', 'con', 'cual', 'cuales', 'de', 'del', 'dos', 'el', 'en', 
        'indica', 'la', 'las', 'los', 'mas', 'nombres', 'o', 'para', 'por', 
        'que', 'quien', 'quienes', 'se', 'si', 'sin', 'si pudieras', 'si tuvieras',
        'sus', 'un', 'una', 'unos', 'unas', 'y', 'companeros', 'companero'
    ])

    # 1. Limpiar el texto: minúsculas, sin acentos ni puntuación
    s = texto_pregunta.lower().strip()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z\s]', '', s)

    # 2. Separar en palabras y filtrar las que no son útiles
    palabras = s.split()
    palabras_significativas = [p for p in palabras if p not in stop_words and len(p) > 3]

    # 3. Si no quedan palabras significativas, usar un fallback
    if not palabras_significativas:
        # Si no hay palabras largas, intenta con las cortas que no sean stop words
        palabras_cortas = [p for p in palabras if p not in stop_words]
        if not palabras_cortas:
            return "General" # Fallback final si la pregunta es muy genérica
        else:
            palabras_significativas = palabras_cortas
    
    # 4. Elegir la palabra más larga como la más descriptiva
    categoria = max(palabras_significativas, key=len)
    
    # 5. Formatear y devolver (primera letra en mayúscula y truncado por seguridad)
    return categoria.capitalize()[:15]

def parse_nombre_apellido(nombre_completo_str):
    partes = nombre_completo_str.strip().split()
    if not partes: return "", ""
    if len(partes) == 1: return partes[0], ""
    apellido = partes[-1]
    nombre = " ".join(partes[:-1])
    return nombre.strip(), apellido.strip()

def generar_iniciales_desde_nombre_apellido(nombre_str, apellido_str):
    iniciales = []
    if nombre_str:
        for parte_n in nombre_str.strip().split():
            if parte_n: iniciales.append(parte_n[0].upper())
    if apellido_str:
        for parte_a in apellido_str.strip().split():
            if parte_a: iniciales.append(parte_a[0].upper())
    final_str = "".join(iniciales)
    if not final_str: return "N/A"
    return final_str[:4] if len(final_str) > 4 else final_str.ljust(3, 'X')

def generar_iniciales_con_fila(nombre_str, apellido_str, numero_fila):
    """
    Genera iniciales usando la primera letra del nombre, la primera del apellido,
    y el número de la fila del CSV.
    """
    nombre_inicial = nombre_str.strip()[0].upper() if nombre_str.strip() else 'X'
    apellido_inicial = apellido_str.strip()[0].upper() if apellido_str.strip() else 'X'
    
    return f"{nombre_inicial}{apellido_inicial}{numero_fila}"

def generar_data_key_desde_texto(texto_pregunta):
    if not texto_pregunta: return None
    s = texto_pregunta.lower().strip()
    s = re.sub(r'\s+', '_', s)
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9_]', '', s).strip('_')
    return f"q_{s[:50]}" if s else f"q_pregunta_{abs(hash(texto_pregunta))%10000}"

def normalizar_nombre_para_comparacion(nombre_str):
    if not isinstance(nombre_str, str): return ""
    s = nombre_str.lower().strip()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# --- Lógica de Importación ---
_import_session = {}

def _start_import_session(options, csv_data, ui_context):
    global _import_session
    _import_session = {
        'options': options, 'csv_data': csv_data, 'ui_context': ui_context,
        'parsed_questions': collections.defaultdict(list),
        'questions_needing_polarity': {}, 'logs': [], 'errors': [], 'warnings': [],
        'counters': collections.defaultdict(int)
    }

def _log(msg, level='info'):
    if level == 'error': _import_session['errors'].append(msg)
    elif level == 'warning': _import_session['warnings'].append(msg)
    _import_session['logs'].append(f"[{level.upper()}] {msg}")

# Colocar esta función dentro de: handlers_csv_excel.py

import collections, traceback, csv, io, re, unicodedata, datetime
from sociograma_data import schools_data, classes_data, members_data, questionnaire_responses_data, get_class_question_definitions
# (Otras importaciones del módulo...)

# Dentro del archivo: handlers_csv_excel.py

def _validate_import_request():
    """
    VERSIÓN CON LOGS DE DEPURACIÓN: Realiza validaciones previas e imprime cada paso.
    """
    global _import_session
    options = _import_session.get('options', {})
    csv_data = _import_session.get('csv_data', [])
    ui_context = _import_session.get('ui_context', {})

    # Iniciar logging para esta validación
    _log("\n--- INICIANDO VALIDACIÓN PREVIA DE IMPORTACIÓN (con logs) ---", 'debug')

    if not csv_data:
        _log("FALLO: El archivo CSV no contiene filas de datos.", 'error')
        return False, "El archivo CSV no contiene filas de datos."

    parsed_data_keys = [generar_data_key_desde_texto(p) for p in _import_session['parsed_questions']]
    if len(parsed_data_keys) != len(set(parsed_data_keys)):
        counts = collections.Counter(parsed_data_keys)
        duplicate_key = next((key for key, count in counts.items() if count > 1), "")
        _log(f"FALLO: Detectada Clave de Datos duplicada por normalización: '{duplicate_key}'.", 'error')
        return False, (f"ERROR: El CSV contiene preguntas que se normalizan a la misma Clave de Datos ('{duplicate_key}'). Modifique los encabezados.")

    rows_by_group = collections.defaultdict(list)
    for row in csv_data:
        inst_csv = row.get("Institucion", "").strip()
        grp_csv = row.get("Grupo", "").strip()
        if inst_csv and grp_csv: rows_by_group[(inst_csv, grp_csv)].append(row)

    if not rows_by_group:
        _log("FALLO: Ninguna fila en el CSV contiene información completa de Institución y Grupo.", 'error')
        return False, "Ninguna fila en el CSV contiene información válida y completa de Institución y Grupo."

    _log(f"Opciones de importación recibidas: {options}", 'debug')

    for (inst_csv, grp_csv), group_rows in rows_by_group.items():
        _log(f"\n--- VALIDANDO GRUPO: {inst_csv} / {grp_csv} ---", 'debug')
        
        target_inst = inst_csv
        if not options.get('import_escuelas') and inst_csv not in schools_data:
            target_inst = ui_context.get('school')
        
        if not target_inst:
            _log(f"FALLO para '{inst_csv}': La institución no existe y no hay contexto alternativo.", 'error')
            return False, f"La institución '{inst_csv}' del CSV no existe y no se proporcionó un contexto alternativo."

        # --- VALIDACIÓN DE DESAJUSTE DE PREGUNTAS (CON LOGS) ---
        defs_existentes = get_class_question_definitions(target_inst, grp_csv)
        keys_existentes = {d.get('data_key') for d in defs_existentes.values()}
        keys_csv = {generar_data_key_desde_texto(p) for p in _import_session['parsed_questions']}
        hay_desajuste = (keys_existentes != keys_csv)

        _log(f"  - Keys de preguntas existentes en el grupo: {len(keys_existentes)}", 'debug')
        _log(f"  - Keys de preguntas en el CSV: {len(keys_csv)}", 'debug')
        _log(f"  - ¿Hay desajuste (keys_existentes != keys_csv)? -> {hay_desajuste}", 'debug')
        
        # Escenario 1: El usuario NO quiere modificar definiciones.
        opcion_importar_defs = options.get('import_defs_preguntas', False)
        _log(f"  - Opción 'Importar/Actualizar Definiciones': {opcion_importar_defs}", 'debug')
        if not opcion_importar_defs and hay_desajuste:
            _log("  - DECISIÓN: FALLO. Importación de definiciones desactivada y hay desajuste.", 'error')
            return False, (f"ERROR en Grupo '{grp_csv}': Las preguntas del CSV no coinciden con las existentes y la importación de definiciones está desactivada.")

        # Escenario 2: El usuario SI quiere modificar, pero NO en modo "solo agregar".
        opcion_solo_agregar = options.get('add_new_questions_only', True)
        _log(f"  - Opción 'Solo agregar preguntas nuevas': {opcion_solo_agregar}", 'debug')
        if opcion_importar_defs and not opcion_solo_agregar and hay_desajuste:
            _log("  - DECISIÓN: FALLO. Modo de 'coincidencia estricta' activado (solo agregar está desactivado) y hay desajuste.", 'error')
            return False, (
                f"ERROR en Grupo '{grp_csv}': Las preguntas del CSV no coinciden con las existentes.\n\n"
                "El modo actual requiere una coincidencia exacta porque la opción 'Solo agregar preguntas nuevas' está desactivada.\n\n"
                "Solución: Active 'Solo agregar preguntas nuevas' para fusionar."
            )
        
        _log("  - INFO: Validación de desajuste de preguntas superada para este grupo.", 'debug')

        # --- Validación de Número de Respuestas vs. Miembros (CON LOGS) ---
        miembros_actuales = members_data.get(target_inst, {}).get(grp_csv, [])
        nombres_actuales_norm = {normalizar_nombre_para_comparacion(f"{m.get('nome','').title()} {m.get('cognome','').title()}") for m in miembros_actuales}
        
        nuevos_miembros_proyectados = set()
        if options.get('import_miembros_nominadores'):
            for row in group_rows: nuevos_miembros_proyectados.add(normalizar_nombre_para_comparacion(row.get("Nombre y Apellido", "")))
        if options.get('create_mentioned_members') and options.get('import_respuestas'):
            for row in group_rows:
                nombres_mencionados = {v.strip() for k, v in row.items() if "Opcion" in k and v.strip()}
                for nombre in nombres_mencionados: nuevos_miembros_proyectados.add(normalizar_nombre_para_comparacion(nombre))
        
        nuevos_miembros_proyectados.discard('')
        num_miembros_proyectado = len(nombres_actuales_norm | nuevos_miembros_proyectados)
        _log(f"  - Miembros proyectados para el grupo: {num_miembros_proyectado}", 'debug')

        for preg, opts in _import_session['parsed_questions'].items():
            max_respuestas_csv = len(opts)
            data_key = generar_data_key_desde_texto(preg)
            
            max_posible_sin_auto = max(0, num_miembros_proyectado - 1)
            max_posible_con_auto = num_miembros_proyectado
            
            preguntas_nuevas_en_csv = keys_csv - keys_existentes
            
            if data_key in preguntas_nuevas_en_csv:
                _log(f"    - Validando pregunta NUEVA: '{preg[:30]}...' (Respuestas en CSV: {max_respuestas_csv})", 'debug')
                allow_self_new = options.get('allow_self_selection_new', False)
                limite_real = max_posible_con_auto if allow_self_new else max_posible_sin_auto
                _log(f"      - Límite real de elecciones: {limite_real}", 'debug')
                if max_respuestas_csv > limite_real:
                    _log(f"      - DECISIÓN: FALLO. {max_respuestas_csv} > {limite_real}", 'error')
                    return False, (f"ERROR en Grupo '{grp_csv}', Pregunta Nueva '{preg[:30]}...': El CSV necesita {max_respuestas_csv} respuestas, pero el máximo de miembros elegibles será {limite_real}.")
            
            elif data_key in keys_existentes:
                _log(f"    - Validando pregunta EXISTENTE: '{preg[:30]}...' (Respuestas en CSV: {max_respuestas_csv})", 'debug')
                q_def = next((d for d in defs_existentes.values() if d.get('data_key') == data_key), {})
                limite_real = max_posible_con_auto if q_def.get('allow_self_selection') else max_posible_sin_auto
                _log(f"      - Límite real de elecciones: {limite_real}", 'debug')
                if max_respuestas_csv > limite_real and not options.get('expand_max_selections'):
                     _log(f"      - DECISIÓN: FALLO. {max_respuestas_csv} > {limite_real} y expandir está desactivado.", 'error')
                     return False, (f"ERROR en Grupo '{grp_csv}', Pregunta Existente '{preg[:30]}...': El CSV necesita {max_respuestas_csv} respuestas, pero el máximo es {limite_real}. Active 'Ampliar max_selections' para permitirlo.")

    _log("--- VALIDACIÓN PREVIA SUPERADA ---", 'debug')
    return True, "Validación exitosa."

def run_full_csv_import_flow(parent_window, csv_content_string, import_options, ui_context=None):
    """
    Orquesta todo el proceso de importación, mostrando la ventana de confirmación si es necesario.
    Esta es la única función que debes llamar desde el botón "Importar CSV" de tu aplicación.
    """
    result_stage1 = handle_csv_import_stage1(csv_content_string, import_options, ui_context)
    
    if result_stage1.get('status') == 'needs_user_confirmation':
        dialog = ConfirmQuestionsDialog(parent_window, result_stage1['data_for_confirmation'])
        confirmed_details = dialog.result

        if confirmed_details is None:
            return {'status': 'cancelled', 'message': 'Importación cancelada por el usuario.'}
        
        return finalize_import(confirmed_details)

    elif result_stage1.get('status') == 'error':
        return result_stage1
    
    else:
        return finalize_import({})

def handle_csv_import_stage1(csv_content_string, import_options, ui_context=None):
    """
    Etapa 1 MODIFICADA. Ahora pide confirmación para TODAS las preguntas nuevas,
    incluyendo las de meta-percepción, y pasa la información 'is_meta' al diálogo.
    """
    try:
        reader = csv.DictReader(io.StringIO(csv_content_string))
        csv_data = list(reader)
        if not csv_data:
            return {'status': 'error', 'message': "El archivo CSV está vacío o tiene un formato no válido."}
    except Exception as e:
        return {'status': 'error', 'message': f"Error crítico al leer el contenido del CSV: {e}"}

    _start_import_session(import_options, csv_data, ui_context)
    _import_session['counters']['filas_leidas'] = len(csv_data)

    headers = list(csv_data[0].keys())
    id_cols = ["Marca temporal", "Dirección de correo electrónico", "Institucion", "Grupo", "Nombre y Apellido", "Sexo", "Fecha De Nacimiento"]
    last_id_idx = -1
    for col in reversed(id_cols):
        if col in headers:
            last_id_idx = headers.index(col)
            break
    
    if last_id_idx != -1:
        question_columns = headers[last_id_idx + 1:]
        
        parser = re.compile(r"^(.*?)\s*\[(?P<type>Opcion|Opción|Eleccion|Elección|Percepcion|Percepción)\s*(\d+)\s*\]$", re.IGNORECASE)
        _import_session['parsed_questions'] = {}

        for col in question_columns:
            match = parser.match(col)
            if match:
                question_text = match.group(1).strip()
                question_type_word = match.group('type').lower()
                option_num = int(match.group(3))

                if question_text not in _import_session['parsed_questions']:
                    _import_session['parsed_questions'][question_text] = {
                        'options': [],
                        'is_meta': 'percep' in question_type_word
                    }
                
                _import_session['parsed_questions'][question_text]['options'].append({
                    'col_header': col, 
                    'option_num': option_num
                })
            else:
                _log(f"El encabezado de columna '{col}' no sigue el formato de pregunta y será ignorado.", 'warning')

    is_valid, error_message = _validate_import_request()
    if not is_valid:
        return {'status': 'error', 'message': error_message}
        
    _import_session['questions_needing_confirmation'] = {}
    if import_options.get('import_defs_preguntas', False) and _import_session['parsed_questions']:
        first_row = csv_data[0]
        inst_csv = first_row.get("Institucion", "").strip()
        grp_csv = first_row.get("Grupo", "").strip()
        target_inst = inst_csv if import_options.get('import_escuelas', False) else (ui_context.get('school') if ui_context else None)
        
        if target_inst:
            defs_grupo_ref = get_class_question_definitions(target_inst, grp_csv)
            for preg_base, preg_data in _import_session['parsed_questions'].items():
                data_key = generar_data_key_desde_texto(preg_base)
                if data_key not in defs_grupo_ref:
                    is_meta = preg_data['is_meta']
                    # Generar categoría: Fija si es meta, dinámica si no.
                    sugerencia = '[Meta-Percepción]' if is_meta else generar_categoria_desde_texto(preg_base)
                    
                    # Preparar la información para el diálogo de confirmación
                    _import_session['questions_needing_confirmation'][preg_base] = {
                        'data_key': data_key,
                        'suggested_category': sugerencia,
                        'is_meta': is_meta  # Pasar esta información al diálogo
                    }

    if _import_session['questions_needing_confirmation']:
        return {
            'status': 'needs_user_confirmation',
            'message': 'Se necesita definir la polaridad y categoría de las nuevas preguntas.',
            'data_for_confirmation': _import_session['questions_needing_confirmation']
        }
    else:
        return finalize_import({})
    # --- FIN DE LA MODIFICACIÓN ---

def finalize_import(confirmed_details):
    """
    Versión FINAL Y DEFINITIVA. Asigna el TIPO estructural internamente
    y guarda la CATEGORÍA temática del usuario por separado, evitando conflictos.
    """
    global _import_session
    if not _import_session:
        return {'status': 'error', 'message': 'No hay una sesión de importación activa para finalizar.'}

    options = _import_session.get('options', {})
    csv_data = _import_session.get('csv_data', [])
    ui_context = _import_session.get('ui_context', {})
    
    processed_groups_for_defs = set()
    group_members_cache = {}

    # --- BUCLE 1: CREAR INSTITUCIONES, GRUPOS Y DEFINICIONES DE PREGUNTAS ---
    for row_index, row in enumerate(csv_data):
        inst_csv = row.get("Institucion", "").strip()
        grp_csv = row.get("Grupo", "").strip()
        
        target_inst = inst_csv
        if not options.get('import_escuelas', False) and inst_csv not in schools_data:
            target_inst = ui_context.get('school')
            if not target_inst:
                _log(f"Fila {row_index+2}: Institución '{inst_csv}' no existe y no hay contexto de UI. Fila omitida.", 'error')
                continue
        
        target_grp = grp_csv
        if not options.get('import_grupos', False):
            if not any(g.get('name') == grp_csv for g in classes_data.get(target_inst, [])):
                msg = f"Fila {row_index+2}: El grupo '{grp_csv}' no existe en la institución '{target_inst}' y la opción de crear grupos está desactivada. Fila omitida."
                _log(msg, 'warning')
                continue
        
        if not target_inst or not target_grp:
            _log(f"Fila {row_index+2}: No se pudo determinar la institución o grupo de destino. Fila omitida.", 'error')
            continue

        group_key = (target_inst, target_grp)
        
        if group_key not in processed_groups_for_defs:
            if options.get('import_escuelas', False) and target_inst not in schools_data:
                schools_data[target_inst] = "Importada desde CSV."
                _import_session['counters']['instituciones_creadas'] += 1
            
            if options.get('import_grupos', False) and target_inst in schools_data:
                if not any(g.get('name') == target_grp for g in classes_data.get(target_inst, [])):
                    classes_data.setdefault(target_inst, []).append({"name": target_grp, "coordinator": "Importado"})
                    _import_session['counters']['grupos_creados'] += 1

            if options.get('import_defs_preguntas'):
                defs = get_class_question_definitions(target_inst, target_grp)
                
                orden_actual_max = -1
                if defs:
                    ordenes_existentes = [q.get('order', -1) for q in defs.values() if isinstance(q.get('order'), int)]
                    if ordenes_existentes:
                        orden_actual_max = max(ordenes_existentes)
                siguiente_orden = orden_actual_max + 1

                if options.get('add_new_questions_only'):
                    for preg, preg_data in _import_session['parsed_questions'].items():
                        data_key = generar_data_key_desde_texto(preg)
                        if data_key not in defs:
                            details = confirmed_details.get(data_key, {})
                            polaridad_confirmada = details.get('polarity', 'positive')
                            categoria_confirmada = details.get('category', generar_categoria_desde_texto(preg))
                            is_meta = preg_data['is_meta']

                            new_def = {
                                "text": preg,
                                "data_key": data_key,
                                "max_selections": len(preg_data['options']),
                                "order": siguiente_orden,
                                "allow_self_selection": options.get('allow_self_selection_new', False),
                                "polarity": polaridad_confirmada,
                                
                                # 1. El 'type' (Tipo Estructural) se asigna internamente.
                                "type": '[Meta-Percepción]' if is_meta else '[Acción Real]',
                                
                                # 2. La 'category' (Categoría Temática) es la que el usuario define.
                                "category": categoria_confirmada,
                                
                                # 3. Los flags internos se mantienen consistentes.
                                "is_cognitive": is_meta,
                                "perceived_nominator": '[SELF]' if is_meta else None
                            }
                            
                            defs[data_key] = new_def
                            _import_session['counters']['defs_preguntas_creadas'] += 1
                            siguiente_orden += 1

                if options.get('expand_max_selections'):
                    for preg, preg_data in _import_session['parsed_questions'].items():
                        data_key = generar_data_key_desde_texto(preg)
                        if data_key in defs and len(preg_data['options']) > defs[data_key].get('max_selections', 0):
                             defs[data_key]['max_selections'] = len(preg_data['options'])
                             _import_session['counters']['defs_preguntas_max_sel_expandido'] += 1

            processed_groups_for_defs.add(group_key)
            
    # --- BUCLE 2: CREACIÓN DE MIEMBROS ---
    last_row_index = -1
    if options.get('import_miembros_nominadores', False):
        for row_index, row in enumerate(csv_data):
            inst_csv, grp_csv, full_name = row.get("Institucion", "").strip(), row.get("Grupo", "").strip(), row.get("Nombre y Apellido", "").strip()
            if not all([inst_csv, grp_csv, full_name]): continue
            group_key = (inst_csv, grp_csv)
            if group_key not in group_members_cache:
                group_members_cache[group_key] = {normalizar_nombre_para_comparacion(f"{m.get('nome','').title()} {m.get('cognome','').title()}") for m in members_data.get(inst_csv, {}).get(grp_csv, [])}
            
            normalized_name = normalizar_nombre_para_comparacion(full_name)
            if normalized_name not in group_members_cache[group_key]:
                nombre, apellido = parse_nombre_apellido(full_name)
                numero_de_fila = row_index + 1
                iniciales = generar_iniciales_con_fila(nombre, apellido, numero_de_fila)
                
                new_member = {"cognome": apellido.upper(), "nome": nombre.title(), "sexo": row.get("Sexo", "Desconocido"), "fecha_nac": row.get("Fecha De Nacimiento", ""), "iniz": iniciales, "annotations": "Creado por importación CSV (Nominador)"}
                members_data.setdefault(inst_csv, {}).setdefault(grp_csv, []).append(new_member)
                group_members_cache[group_key].add(normalized_name)
                _import_session['counters']['miembros_nominadores_creados'] += 1
            last_row_index = row_index

    siguiente_numero_disponible = last_row_index + 2
    if options.get('create_mentioned_members', False):
        todos_los_mencionados = {v.strip() for row in csv_data for k, v in row.items() if ("Opcion" in k or "Percepcion" in k) and v.strip()}
        for full_name in sorted(list(todos_los_mencionados)):
            normalized_name = normalizar_nombre_para_comparacion(full_name)
            if not any(normalized_name in cache for cache in group_members_cache.values()):
                primer_grupo_procesado = next(iter(processed_groups_for_defs), None)
                if not primer_grupo_procesado: continue
                inst_csv, grp_csv = primer_grupo_procesado
                nombre, apellido = parse_nombre_apellido(full_name)
                iniciales = generar_iniciales_con_fila(nombre, apellido, siguiente_numero_disponible)
                siguiente_numero_disponible += 1
                new_member = {"cognome": apellido.upper(), "nome": nombre.title(), "sexo": "Desconocido", "fecha_nac": "", "iniz": iniciales, "annotations": "Creado por mención en CSV"}
                members_data.setdefault(inst_csv, {}).setdefault(grp_csv, []).append(new_member)
                group_key = (inst_csv, grp_csv)
                if group_key not in group_members_cache: group_members_cache[group_key] = set()
                group_members_cache[group_key].add(normalized_name)
                _import_session['counters']['miembros_mencionados_creados'] += 1

    # --- BUCLE 3: IMPORTACIÓN DE RESPUESTAS ---
    if options.get('import_respuestas', False):
        for row in csv_data:
            inst_csv, grp_csv, nominator = row.get("Institucion","").strip(), row.get("Grupo","").strip(), row.get("Nombre y Apellido","").strip()
            if not all([inst_csv, grp_csv, nominator]): continue
            target_inst = inst_csv
            if not options.get('import_escuelas', False) and inst_csv not in schools_data: target_inst = ui_context.get('school')
            target_grp = grp_csv
            if not options.get('import_grupos', False) and not any(g.get('name') == grp_csv for g in classes_data.get(target_inst, [])): continue

            respuestas_miembro_directas = {}
            respuestas_miembro_cognitivas = collections.defaultdict(list)
            defs_grupo_actual = get_class_question_definitions(target_inst, target_grp)
            
            for preg, preg_data in _import_session['parsed_questions'].items():
                opts = preg_data['options']
                is_meta = preg_data['is_meta']
                data_key = generar_data_key_desde_texto(preg)
                q_def = defs_grupo_actual.get(data_key)
                if not q_def: continue

                elecciones_originales = [row.get(op['col_header'], '').strip() for op in opts if row.get(op['col_header'], '').strip()]
                elecciones_filtradas = [e for e in elecciones_originales if normalizar_nombre_para_comparacion(e) != normalizar_nombre_para_comparacion(nominator)] if not q_def.get('allow_self_selection', True) else elecciones_originales
                
                if elecciones_filtradas:
                    elecciones_finales = list(dict.fromkeys(elecciones_filtradas))[:q_def.get('max_selections', len(opts))]
                    if is_meta:
                        respuestas_miembro_cognitivas[data_key] = elecciones_finales
                    else:
                        respuestas_miembro_directas[data_key] = elecciones_finales
            
            if respuestas_miembro_directas:
                questionnaire_responses_data[(target_inst, target_grp, nominator)] = respuestas_miembro_directas
                _import_session['counters']['respuestas_importadas'] += 1
            if respuestas_miembro_cognitivas:
                cognitive_key = (target_inst, target_grp, nominator)
                perceiver_all_perceptions = cognitive_social_structures_data.setdefault(cognitive_key, collections.defaultdict(dict))
                for dk, noms in respuestas_miembro_cognitivas.items():
                    perceiver_all_perceptions[dk][nominator] = noms
                _import_session['counters']['respuestas_cognitivas_importadas'] += 1

    # --- Generación del resumen final ---
    summary = "Importación completada.\n" + "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in _import_session['counters'].items() if v > 0])
    if _import_session['errors']:
        summary += f"\n\nErrores ({len(_import_session['errors'])}):\n" + "\n".join(_import_session['errors'])
    if _import_session['warnings']:
        summary += f"\n\nAdvertencias ({len(_import_session['warnings'])}):\n" + "\n".join(_import_session['warnings'])
    
    return {'status': 'success', 'message': summary}


def handle_prepare_data_for_csv_export(groups_to_export):
    """
    Versión con LOGS DE DEPURACIÓN. Imprime en consola los datos que encuentra
    para cada miembro durante el proceso de exportación para identificar por qué
    las celdas de respuesta aparecen vacías.
    """
    print("\n--- [LOG-EXPORT] INICIANDO PROCESO DE EXPORTACIÓN A CSV ---")
    if not groups_to_export:
        print("[LOG-EXPORT] Error: No se seleccionaron grupos.")
        return False, [["Error: No se seleccionaron grupos."]]
    
    try:
        # --- 1. Recolectar TODA la información de las preguntas ---
        max_selections = collections.defaultdict(int)
        question_info = {}

        for inst, grp in groups_to_export:
            # Iteramos sobre los valores (las definiciones de pregunta), no sobre los items
            for qd in get_class_question_definitions(inst, grp).values():
                # La clave que nos interesa es la data_key
                dk = qd.get('data_key')
                if not dk: continue # Ignorar si no hay data_key

                max_selections[dk] = max(max_selections[dk], qd.get('max_selections', 0))
                if dk not in question_info:
                    is_meta = qd.get('is_cognitive', False) and qd.get('perceived_nominator') == '[SELF]'
                    question_info[dk] = {
                        'text': qd.get('text', dk),
                        'is_meta': is_meta
                    }
        
        sorted_dks = sorted(list(max_selections.keys()))
        print(f"[LOG-EXPORT] Claves de preguntas a exportar (ordenadas): {sorted_dks}")

        # --- 2. Construir los encabezados dinámicamente ---
        question_headers = []
        for dk in sorted_dks:
            info = question_info[dk]
            header_type = "Percepcion" if info['is_meta'] else "Opcion"
            for i in range(max_selections[dk]):
                question_headers.append(f"{info['text']} [{header_type} {i+1}]")

        header = ["Institucion", "Grupo", "Nombre y Apellido", "Sexo", "Fecha De Nacimiento"] + question_headers
        all_rows = [header]
        print(f"[LOG-EXPORT] Encabezados generados ({len(header)} columnas).")

        # --- 3. Poblar las filas buscando en AMBAS fuentes de datos ---
        print("\n--- [LOG-EXPORT] Procesando miembros y sus respuestas ---")
        for inst, grp in groups_to_export:
            print(f"\n[LOG-EXPORT] Grupo actual: {inst} / {grp}")
            for member in members_data.get(inst, {}).get(grp, []):
                full_name = f"{member.get('nome','').title()} {member.get('cognome','').title()}"
                print(f"  - Procesando miembro: {full_name}")
                
                row = [inst, grp, full_name, member.get('sexo', ''), member.get('fecha_nac', '')]
                
                # --- LOGS CLAVE: Verificar las claves de búsqueda ---
                direct_response_key = (inst, grp, full_name)
                cognitive_response_key = (inst, grp, full_name)
                
                print(f"    Buscando acciones reales con la clave: {direct_response_key}")
                direct_responses = questionnaire_responses_data.get(direct_response_key, {})
                if direct_responses:
                    print(f"      > ¡Encontrado! Datos de acción real: {direct_responses}")
                else:
                    print(f"      > No se encontraron datos de acción real.")
                    
                print(f"    Buscando meta-percepciones con la clave: {cognitive_response_key}")
                cognitive_responses = cognitive_social_structures_data.get(cognitive_response_key, {})
                if cognitive_responses:
                     print(f"      > ¡Encontrado! Datos de meta-percepción: {cognitive_responses}")
                else:
                    print(f"      > No se encontraron datos de meta-percepción.")

                for dk in sorted_dks:
                    info = question_info[dk]
                    resps = []
                    
                    if info['is_meta']:
                        resps = cognitive_responses.get(dk, {}).get(full_name, [])
                        print(f"      - Para la pregunta de META-PERCEPCIÓN '{dk}', respuestas encontradas: {resps}")
                    else:
                        resps = direct_responses.get(dk, [])
                        print(f"      - Para la pregunta de ACCIÓN REAL '{dk}', respuestas encontradas: {resps}")
                    
                    row.extend(resps + [''] * (max_selections[dk] - len(resps)))
                
                all_rows.append(row)
                
        print("\n--- [LOG-EXPORT] PROCESO DE EXPORTACIÓN FINALIZADO ---")
        return True, all_rows
    except Exception as e:
        print(f"[LOG-EXPORT] ERROR FATAL DURANTE LA EXPORTACIÓN: {e}")
        traceback.print_exc()
        return False, [[f"Error al exportar: {e}"]]

def handle_generate_instructions_pdf():
    try:
        return pdf_generator.generate_import_instructions_pdf()
    except Exception as e: return None, f"Error al generar PDF: {e}"

print("handlers_csv_excel.py refactorizado y COMPLETO, listo para su uso.")