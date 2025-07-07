# handlers_csv_excel.py
# (v2.2 - Versión final y completa.
#  Implementa toda la lógica de creación de instituciones, grupos y miembros.)

import collections, traceback, csv, io, re, unicodedata, datetime
from sociograma_data import schools_data, classes_data, members_data, questionnaire_responses_data, get_class_question_definitions
import pdf_generator

# --- Funciones de Utilidad (sin cambios) ---

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

def handle_csv_import_stage1(csv_content_string, import_options, ui_context=None):
    """
    VERSIÓN CORREGIDA: Asegura que la validación se ejecute SIEMPRE antes
    de cualquier otra decisión lógica.
    """
    try:
        reader = csv.DictReader(io.StringIO(csv_content_string))
        csv_data = list(reader)
        if not csv_data:
            return {'status': 'error', 'message': "El archivo CSV está vacío o tiene un formato no válido."}
    except Exception as e:
        return {'status': 'error', 'message': f"Error crítico al leer el contenido del CSV: {e}"}

    # 1. Iniciar sesión y parsear cabeceras
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
        parser = re.compile(r"^(.*?)\s*\[(?:Opcion|Opción|Eleccion|Elección)\s*(\d+)\s*\]$", re.IGNORECASE)
        for col in question_columns:
            match = parser.match(col)
            if match:
                question_text = match.group(1).strip()
                _import_session['parsed_questions'][question_text].append({'col_header': col, 'option_num': int(match.group(2))})
            else:
                _log(f"El encabezado de columna '{col}' no sigue el formato de pregunta y será ignorado.", 'warning')

    # 2. --- VALIDACIÓN PREVIA (SE EJECUTA SIEMPRE PRIMERO) ---
    is_valid, error_message = _validate_import_request()
    if not is_valid:
        # Si la validación falla, nos detenemos aquí y devolvemos el error.
        return {'status': 'error', 'message': error_message}
    # Si la validación pasa, continuamos.

    # 3. Detección de preguntas nuevas para confirmación de polaridad
    # (Este código es el mismo, pero ahora se ejecuta DESPUÉS de la validación)
    if import_options.get('import_defs_preguntas', False) and _import_session['parsed_questions']:
        first_row = csv_data[0]
        inst_csv = first_row.get("Institucion", "").strip()
        grp_csv = first_row.get("Grupo", "").strip()
        target_inst = inst_csv if import_options.get('import_escuelas', False) else (ui_context.get('school') if ui_context else None)
        
        if target_inst:
            defs_grupo_ref = get_class_question_definitions(target_inst, grp_csv)
            for preg_base, _ in _import_session['parsed_questions'].items():
                data_key = generar_data_key_desde_texto(preg_base)
                if data_key not in defs_grupo_ref:
                    _import_session['questions_needing_polarity'][preg_base] = {'data_key': data_key}

    # 4. Decisión final de la Etapa 1
    if _import_session['questions_needing_polarity']:
        # Hay preguntas nuevas, se necesita intervención del usuario
        return {
            'status': 'needs_polarity_confirmation',
            'message': 'Se necesita definir la polaridad de las nuevas preguntas.',
            'data_for_confirmation': _import_session['questions_needing_polarity']
        }
    else:
        # No hay preguntas nuevas o no se están importando defs.
        # Como la validación ya pasó, es seguro llamar a finalize_import.
        return finalize_import({})

# --- FUNCIÓN FINALIZE_IMPORT COMPLETA Y ROBUSTA ---
def finalize_import(confirmed_polarities):
    """
    Finaliza la importación, asignando un orden secuencial a las preguntas nuevas.
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

            # --- LÓGICA DE PREGUNTAS CON ORDEN SECUENCIAL ---
            if options.get('import_defs_preguntas'):
                defs = get_class_question_definitions(target_inst, target_grp)
                
                # Calcular el siguiente número de orden disponible
                orden_actual_max = -1
                if defs:
                    ordenes_existentes = [q.get('order', -1) for q in defs.values() if isinstance(q.get('order'), int)]
                    if ordenes_existentes:
                        orden_actual_max = max(ordenes_existentes)
                
                siguiente_orden = orden_actual_max + 1

                if options.get('add_new_questions_only'):
                    for preg, opts in _import_session['parsed_questions'].items():
                        data_key = generar_data_key_desde_texto(preg)
                        if data_key not in defs:
                            polaridad = confirmed_polarities.get(data_key, 'positive')
                            defs[data_key] = {
                                "text": preg, "type": "Importado", "polarity": polaridad,
                                "data_key": data_key, "max_selections": len(opts),
                                "order": siguiente_orden, # Asignar orden secuencial
                                "allow_self_selection": options.get('allow_self_selection_new', False)
                            }
                            _import_session['counters']['defs_preguntas_creadas'] += 1
                            siguiente_orden += 1 # Incrementar para la siguiente
                else:
                    _log(f"Procesando grupo '{target_grp}' con preguntas coincidentes (modo no-agregar).", 'info')

                if options.get('expand_max_selections'):
                    for preg, opts in _import_session['parsed_questions'].items():
                        data_key = generar_data_key_desde_texto(preg)
                        if data_key in defs and len(opts) > defs[data_key].get('max_selections', 0):
                             defs[data_key]['max_selections'] = len(opts)
                             _import_session['counters']['defs_preguntas_max_sel_expandido'] += 1

            processed_groups_for_defs.add(group_key)
            
    # --- BUCLE 2: CREACIÓN DE MIEMBROS (CON LÓGICA DE NUMERACIÓN SECUENCIAL) ---
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
        todos_los_mencionados = set()
        for row in csv_data:
            mentioned_names = {v.strip() for k, v in row.items() if "Opcion" in k and v.strip()}
            todos_los_mencionados.update(mentioned_names)

        for full_name in sorted(list(todos_los_mencionados)):
            normalized_name = normalizar_nombre_para_comparacion(full_name)
            
            ya_existe = any(normalized_name in cache for cache in group_members_cache.values())
            
            if not ya_existe:
                primer_grupo_procesado = next(iter(processed_groups_for_defs), None)
                if not primer_grupo_procesado: continue
                inst_csv, grp_csv = primer_grupo_procesado

                nombre, apellido = parse_nombre_apellido(full_name)
                
                iniciales = generar_iniciales_con_fila(nombre, apellido, siguiente_numero_disponible)
                siguiente_numero_disponible += 1

                new_member = {"cognome": apellido.upper(), "nome": nombre.title(), "sexo": "Desconocido", "fecha_nac": "", "iniz": iniciales, "annotations": "Creado por mención en CSV"}
                members_data.setdefault(inst_csv, {}).setdefault(grp_csv, []).append(new_member)
                
                group_key = (inst_csv, grp_csv)
                if group_key not in group_members_cache:
                     group_members_cache[group_key] = set()
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

            respuestas_miembro = {}
            defs_grupo_actual = get_class_question_definitions(target_inst, target_grp)
            
            for preg, opts in _import_session['parsed_questions'].items():
                data_key = generar_data_key_desde_texto(preg)
                q_def = defs_grupo_actual.get(data_key)
                if not q_def: continue

                elecciones_originales = [row.get(op['col_header'], '').strip() for op in opts if row.get(op['col_header'], '').strip()]
                
                elecciones_filtradas = []
                if q_def.get('allow_self_selection', True):
                    elecciones_filtradas = elecciones_originales
                else:
                    nominator_normalizado = normalizar_nombre_para_comparacion(nominator)
                    for eleccion in elecciones_originales:
                        if normalizar_nombre_para_comparacion(eleccion) != nominator_normalizado:
                            elecciones_filtradas.append(eleccion)
                        else:
                            _log(f"Auto-elección de '{nominator}' omitida para pregunta '{preg}' (no permitida).", 'warning')
                
                if elecciones_filtradas:
                    respuestas_miembro[data_key] = list(dict.fromkeys(elecciones_filtradas))[:q_def.get('max_selections', len(opts))]
            
            if respuestas_miembro:
                questionnaire_responses_data[(target_inst, target_grp, nominator)] = respuestas_miembro
                _import_session['counters']['respuestas_importadas'] += 1

    # --- Generación del resumen final ---
    summary = f"Importación completada.\n" + "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in _import_session['counters'].items()])
    if _import_session['errors']:
        summary += f"\n\nErrores ({len(_import_session['errors'])}):\n" + "\n".join(_import_session['errors'])
    if _import_session['warnings']:
        summary += f"\n\nAdvertencias ({len(_import_session['warnings'])}):\n" + "\n".join(_import_session['warnings'])
    
    return {'status': 'success', 'message': summary}


def handle_prepare_data_for_csv_export(groups_to_export):
    if not groups_to_export: return False, [["Error: No se seleccionaron grupos."]]
    try:
        max_selections, question_texts = collections.defaultdict(int), {}
        for inst, grp in groups_to_export:
            for dk, qd in get_class_question_definitions(inst, grp).items():
                max_selections[dk] = max(max_selections[dk], qd.get('max_selections', 0))
                if dk not in question_texts: question_texts[dk] = qd.get('text', dk)
        
        sorted_dks = sorted(list(max_selections.keys()))
        question_headers = [f"{question_texts.get(dk, dk)} [Opcion {i+1}]" for dk in sorted_dks for i in range(max_selections[dk])]
        header = ["Institucion", "Grupo", "Nombre y Apellido", "Sexo", "Fecha De Nacimiento"] + question_headers
        all_rows = [header]

        for inst, grp in groups_to_export:
            for member in members_data.get(inst, {}).get(grp, []):
                full_name = f"{member.get('nome','').title()} {member.get('cognome','').title()}"
                row = [inst, grp, full_name, member.get('sexo', ''), member.get('fecha_nac', '')]
                responses = questionnaire_responses_data.get((inst, grp, full_name), {})
                for dk in sorted_dks:
                    resps = responses.get(dk, [])
                    row.extend(resps + [''] * (max_selections[dk] - len(resps)))
                all_rows.append(row)
        return True, all_rows
    except Exception as e: return False, [[f"Error al exportar: {e}"]]

def handle_generate_instructions_pdf():
    try:
        return pdf_generator.generate_import_instructions_pdf()
    except Exception as e: return None, f"Error al generar PDF: {e}"

print("handlers_csv_excel.py refactorizado y COMPLETO, listo para su uso.")