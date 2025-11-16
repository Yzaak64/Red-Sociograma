# handlers_utils.py
# (v1.9 - Lógica de 'cs' en get_aggregated_network actualizada para funcionar solo con percepción)

import re
import unicodedata
import collections
import math # <-- Se añade esta importación para la nueva lógica de CS

# No se importan widgets aquí, este módulo debe ser independiente de la UI.

# --- Funciones de Utilidad Reutilizables ---

def normalizar_nombre_para_comparacion(nombre_str):
    """
    Normaliza un nombre para comparación: lo convierte a minúsculas,
    elimina tildes y caracteres especiales, y estandariza los espacios.
    Esencial para que "José Pérez" coincida con "jose perez".
    """
    if not isinstance(nombre_str, str): 
        return ""
    # Convertir a minúsculas y quitar espacios al inicio/final
    s = str(nombre_str).lower().strip()
    # Reemplazar tildes y diacríticos (ej. á -> a)
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    # Eliminar cualquier caracter que no sea letra, número o espacio
    s = re.sub(r'[^a-z0-9\s]', '', s)
    # Reemplazar múltiples espacios por uno solo
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def get_member_options_for_dropdown(school_name, class_name,
                                     app_data_ref,
                                     order_by='Apellido',
                                     exclude_member_display_name=None,
                                     include_all_option=False):
    """
    CORREGIDO: Obtiene una lista de tuplas para poblar un desplegable de miembros,
    asegurando que la etiqueta de visualización sea siempre el NOMBRE COMPLETO.
    """
    if not app_data_ref or not hasattr(app_data_ref, 'members_data'):
        print("ERROR en get_member_options: app_data_ref no es válido.")
        return [('Error: Datos no disponibles', None)]

    options = []
    if include_all_option:
        # Para el filtro del sociograma, la opción "Todos" es la primera
        options.append(('Todos (Grafo Completo)', None))
    else:
        # Para el cuestionario, "Seleccionar" es la opción por defecto
        options.append(('Seleccionar', ''))

    local_members_data = app_data_ref.members_data
    members_list_all = local_members_data.get(school_name, {}).get(class_name, [])
    if not members_list_all:
        return options

    members_to_process = list(members_list_all)

    if exclude_member_display_name:
        normalized_exclude_name = normalizar_nombre_para_comparacion(exclude_member_display_name)
        members_to_process = [
            m for m in members_to_process
            if normalizar_nombre_para_comparacion(f"{m.get('nome', '')} {m.get('cognome', '')}") != normalized_exclude_name
        ]

    # Ordenar la lista para una visualización consistente en el dropdown
    if order_by == 'Nombre':
        key_func = lambda s: (str(s.get('nome', '')).strip().upper(), str(s.get('cognome', '')).strip().upper())
    else:  # Por defecto, ordenar por Apellido
        key_func = lambda s: (str(s.get('cognome', '')).strip().upper(), str(s.get('nome', '')).strip().upper())

    try:
        sorted_members = sorted(members_to_process, key=key_func)
    except Exception as e:
        print(f"ERROR al ordenar miembros en get_member_options: {e}")
        sorted_members = members_to_process
    
    for member_dict in sorted_members:
        nombre_titulo = str(member_dict.get('nome', '')).strip().title()
        cognome_titulo = str(member_dict.get('cognome', '')).strip().title()
        
        display_label = f"{nombre_titulo} {cognome_titulo}".strip()
        internal_value = display_label

        if internal_value:
            options.append((display_label, internal_value))

    return options

def generar_opciones_dropdown_miembros_main_select(lista_miembros):
    """
    Función específica para el `sg.Listbox` principal de la vista de miembros.
    Toma una lista de diccionarios de miembros y devuelve una lista de strings ordenada.
    """
    if not lista_miembros:
        return []
        
    sorted_list = sorted(lista_miembros, key=lambda m: (str(m.get('nome','')).strip().title(), str(m.get('cognome','')).strip().title()))

    options = []
    for m in sorted_list:
        nome = m.get('nome', '').strip().title()
        cognome = m.get('cognome', '').strip().title()
        display_text = f"{nome} {cognome}".strip()
        if display_text:
            options.append(display_text)
    return options

def get_aggregated_network(institution_name, group_name, aggregation_mode, app_data_ref, perceiver_name=None, selected_keys=None, consensus_threshold=50):
    """
    Función central para obtener una red basada en diferentes modos de agregación.
    v4.0 - Versión final y limpia. Solo procesa 'real_actions' y 'meta_perceptions'.
           Los modos matriciales (CIVSOC, Accuracy) se calculan en sus propios manejadores.
    """
    members_list = app_data_ref.members_data.get(institution_name, {}).get(group_name, [])
    if not members_list:
        return {}

    member_names = [f"{m.get('nome','').title()} {m.get('cognome','').title()}" for m in members_list]
    
    output_network = collections.defaultdict(lambda: collections.defaultdict(list))
    all_question_defs_by_id = app_data_ref.get_class_question_definitions(institution_name, group_name)
    all_question_defs = {v['data_key']: v for k, v in all_question_defs_by_id.items()}
    cognitive_data = app_data_ref.cognitive_social_structures_data

    if not selected_keys:
        selected_keys = list(all_question_defs.keys())

    # --- MODO 1: Acciones Reales (Estándar) ---
    if aggregation_mode == 'real_actions':
        real_actions_data = {}
        for key, responses in app_data_ref.questionnaire_responses_data.items():
            if key[0] == institution_name and key[1] == group_name:
                filtered_responses = {q_key: nominees for q_key, nominees in responses.items() if q_key in selected_keys}
                if filtered_responses:
                    real_actions_data[key] = filtered_responses
        return real_actions_data
        
    # --- MODO 2: Meta-Percepción (GLOBAL - SIN FOCO) ---
    elif aggregation_mode == 'meta_perceptions':
        for ego_name in member_names:
            ego_perceptions = cognitive_data.get((institution_name, group_name, ego_name), {})
            for meta_key in selected_keys:
                q_def = all_question_defs.get(meta_key)
                if not q_def or q_def.get('perceived_nominator') != '[SELF]':
                    continue

                if meta_key in ego_perceptions:
                    believed_nominators = ego_perceptions[meta_key].get(ego_name, [])
                    for alter_name in believed_nominators:
                        response_key = (institution_name, group_name, alter_name)
                        output_network[response_key][meta_key].append(ego_name)
        return dict(output_network)

    # Para los modos 'accuracy_analysis' y 'civsoc_matrix', esta función no necesita
    # hacer nada. El cálculo de la matriz se realiza directamente en `window_sociomatrix`
    # usando funciones de `handlers_groups`. Devolver una red vacía es el
    # comportamiento correcto.
    return dict(output_network)
    
print("handlers_utils.py refactorizado y listo para su uso en la aplicación de escritorio.")