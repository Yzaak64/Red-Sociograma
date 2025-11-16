# handlers_groups.py
# (v16.3 - Refactorizado para incluir tanto el cálculo de CIVSOC como el de Precisión de Meta-Percepción)

import traceback
import collections
import numpy as np
from sociograma_data import (
    classes_data,
    members_data,
    questionnaire_responses_data,
    get_class_question_definitions,
    question_definitions,
    cognitive_social_structures_data
)
import pdf_generator
from handlers_utils import normalizar_nombre_para_comparacion

# --- Funciones Lógicas de la Vista de Grupos ---

def handle_add_group(institution_name, group_details):
    """
    Lógica para añadir un nuevo grupo a una institución.
    group_details es un diccionario con 'name', 'coordinator', etc.
    Devuelve (éxito, mensaje).
    """
    group_name = group_details.get('name', '').strip()
    if not group_name:
        return False, "El nombre del grupo no puede estar vacío."
    
    if institution_name not in classes_data:
        return False, f"La institución '{institution_name}' no existe."
    
    existing_groups_in_institution = classes_data.get(institution_name, [])
    if any(g.get('name', '').lower() == group_name.lower() for g in existing_groups_in_institution):
        return False, f"El grupo '{group_name}' ya existe en esta institución."

    try:
        # Asegurarse de que las estructuras de datos dependientes existan
        classes_data.setdefault(institution_name, []).append(group_details)
        members_data.setdefault(institution_name, collections.OrderedDict()).setdefault(group_name, [])
        get_class_question_definitions(institution_name, group_name) # Crea el espacio para las preguntas

        return True, f"Grupo '{group_name}' añadido correctamente a la institución '{institution_name}'."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al añadir el grupo: {e}"

def handle_modify_group(institution_name, original_group_name, updated_group_details):
    """
    Lógica para modificar un grupo existente.
    Devuelve (éxito, mensaje).
    """
    new_group_name = updated_group_details.get('name', '').strip()
    if not new_group_name:
        return False, "El nombre del grupo no puede estar vacío."

    if institution_name not in classes_data:
        return False, f"La institución '{institution_name}' no existe."

    institution_groups = classes_data[institution_name]
    
    # Verificar si el nuevo nombre ya existe en otro grupo
    if new_group_name.lower() != original_group_name.lower():
        if any(g.get('name', '').lower() == new_group_name.lower() for g in institution_groups):
            return False, f"Un grupo con el nombre '{new_group_name}' ya existe."

    # Encontrar y actualizar el grupo
    group_found = False
    for i, group in enumerate(institution_groups):
        if group.get('name', '').lower() == original_group_name.lower():
            # Actualizar el diccionario del grupo en su lugar
            institution_groups[i].update(updated_group_details)
            group_found = True
            
            # Si el nombre del grupo cambió, hay que migrar los datos dependientes
            if new_group_name.lower() != original_group_name.lower():
                # Migrar miembros
                if institution_name in members_data and original_group_name in members_data[institution_name]:
                    members_data[institution_name][new_group_name] = members_data[institution_name].pop(original_group_name)
                
                # Migrar respuestas de cuestionario
                for key in list(questionnaire_responses_data.keys()):
                    if key[0] == institution_name and key[1] == original_group_name:
                        responses = questionnaire_responses_data.pop(key)
                        new_key = (institution_name, new_group_name, key[2])
                        questionnaire_responses_data[new_key] = responses
                
                # Migrar definiciones de preguntas
                old_q_key = (institution_name, original_group_name)
                if old_q_key in question_definitions:
                    defs = question_definitions.pop(old_q_key)
                    question_definitions[(institution_name, new_group_name)] = defs
            
            break
            
    if not group_found:
        return False, f"No se encontró el grupo original '{original_group_name}' para modificar."
        
    return True, f"Grupo '{new_group_name}' actualizado correctamente."
    
def handle_delete_group(institution_name, group_name_to_delete):
    """
    Lógica para eliminar un grupo y todos sus datos asociados.
    Devuelve (éxito, mensaje).
    """
    if not all([institution_name, group_name_to_delete]):
        return False, "Faltan datos (institución o grupo) para la eliminación."

    try:
        deleted_items_count = 0
        
        # Eliminar de classes_data
        if institution_name in classes_data:
            original_len = len(classes_data[institution_name])
            classes_data[institution_name] = [g for g in classes_data[institution_name] if g.get('name') != group_name_to_delete]
            if len(classes_data[institution_name]) < original_len:
                deleted_items_count += 1
        
        # Eliminar de members_data
        if institution_name in members_data and group_name_to_delete in members_data.get(institution_name, {}):
            del members_data[institution_name][group_name_to_delete]
            deleted_items_count += 1

        # Eliminar respuestas asociadas
        keys_to_delete = [k for k in questionnaire_responses_data if k[0] == institution_name and k[1] == group_name_to_delete]
        if keys_to_delete:
            for key in keys_to_delete:
                del questionnaire_responses_data[key]
            deleted_items_count += len(keys_to_delete)

        # Eliminar definiciones de preguntas
        q_def_key = (institution_name, group_name_to_delete)
        if q_def_key in question_definitions:
            del question_definitions[q_def_key]
            deleted_items_count += 1

        if deleted_items_count > 0:
            return True, f"Grupo '{group_name_to_delete}' y sus datos asociados eliminados."
        else:
            return False, f"Grupo '{group_name_to_delete}' no encontrado para eliminar."

    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al eliminar el grupo: {e}"
def prepare_context_for_view(institution_name, group_name, target_view):
    """
    Valida y prepara un diccionario de contexto para navegar a otra vista.
    target_view puede ser 'members', 'sociogram', etc.
    Devuelve un diccionario de contexto o None si hay error.
    """
    if not all([institution_name, group_name]):
        print(f"Error: Faltan datos para preparar la vista '{target_view}'.")
        return None
    
    context = {
        'school': institution_name,
        'class_name': group_name
    }
    return context

def handle_generate_diana_data(institution_name, group_name, selected_question_keys, network_data_override=None):
    """
    Calcula los datos de popularidad (elecciones recibidas) para la Diana de Afinidad.
    Devuelve una lista de diccionarios de miembros con su puntaje.
    """
    class_members_raw = members_data.get(institution_name, {}).get(group_name, [])
    if not class_members_raw:
        return None

    member_info_map = { f"{m.get('nome','').strip().title()} {m.get('cognome','').strip().title()}": m for m in class_members_raw }
    members_in_class_set = set(member_info_map.keys())
    
    source_responses = network_data_override if network_data_override is not None else questionnaire_responses_data

    affinity_scores = collections.defaultdict(lambda: {'total_recibido': 0})
    edges_data = []

    for (resp_inst, resp_grp, nominator_key), resp_dict in source_responses.items():
        if resp_inst == institution_name and resp_grp == group_name and nominator_key in members_in_class_set:
            for q_key, nominees_list in resp_dict.items():
                if q_key not in selected_question_keys: continue
                for nominee_key in nominees_list:
                    if nominee_key in members_in_class_set:
                        affinity_scores[nominee_key]['total_recibido'] += 1
                        edges_data.append((nominator_key, nominee_key))
    
    members_data_list_final = []
    for name, info in member_info_map.items():
        member_dict = {
            'nombre_completo': name,
            'id_corto': info.get('iniz', 'N/A'),
            'sexo': info.get('sexo', 'Desconocido'),
            **affinity_scores.get(name, {'total_recibido': 0})
        }
        members_data_list_final.append(member_dict)
    
    # Devuelve tanto los datos de los nodos como los de las aristas
    return members_data_list_final, edges_data

def calculate_civsoc_distance_data(institution_name, group_name, focus_member_name, question_keys):
    """
    Calcula los datos para un Gráfico de Distancia Sociométrica estilo CIVSOC.
    Devuelve una lista de diccionarios con los datos de los miembros para el gráfico.
    VERSIÓN CORREGIDA: Usa normalización de nombres para identificar correctamente al foco.
    """
    members_list = members_data.get(institution_name, {}).get(group_name, [])
    
    q_e, q_r, q_pe, q_pr = question_keys.get('accion_pos'), question_keys.get('accion_neg'), question_keys.get('meta_pos'), question_keys.get('meta_neg')
    if not all([q_e, q_r, q_pe, q_pr]): return None

    members_data_list_detailed = []
    focus_member_dict = next((m for m in members_list if f"{m.get('nome','').title()} {m.get('cognome','').title()}" == focus_member_name), None)
    if not focus_member_dict: return None
    
    # El miembro foco siempre se añade primero con distancia 0
    members_data_list_detailed.append({
        'nombre_completo': focus_member_name, 'id_corto': focus_member_dict.get('iniz', 'N/A'),
        'sexo': focus_member_dict.get('sexo', 'Desconocido'), 'distancia_sociometrica': 0
    })

    # Normalizar el nombre del foco UNA VEZ para eficiencia
    normalized_focus_name = normalizar_nombre_para_comparacion(focus_member_name)

    for other_member_dict in members_list:
        other_member_name = f"{other_member_dict.get('nome','').title()} {other_member_dict.get('cognome','').title()}"
        
        # --- LÍNEA CORREGIDA ---
        # Usar la comparación normalizada para saltar el foco de forma segura
        if normalizar_nombre_para_comparacion(other_member_name) == normalized_focus_name:
            continue
        # --- FIN DE LA CORRECCIÓN ---

        # Implementación de la fórmula de Barrasa y Gil (2004)
        foco_actions = questionnaire_responses_data.get((institution_name, group_name, focus_member_name), {})
        e_ij = 1 if other_member_name in foco_actions.get(q_e, []) else 0
        r_ij = 1 if other_member_name in foco_actions.get(q_r, []) else 0
        otro_actions = questionnaire_responses_data.get((institution_name, group_name, other_member_name), {})
        e_ji = 1 if focus_member_name in otro_actions.get(q_e, []) else 0
        r_ji = 1 if focus_member_name in otro_actions.get(q_r, []) else 0
        foco_perceptions = cognitive_social_structures_data.get((institution_name, group_name, focus_member_name), {})
        pe_ij = 1 if other_member_name in foco_perceptions.get(q_pe, {}).get(focus_member_name, []) else 0
        pr_ij = 1 if other_member_name in foco_perceptions.get(q_pr, {}).get(focus_member_name, []) else 0
        otro_perceptions = cognitive_social_structures_data.get((institution_name, group_name, other_member_name), {})
        pe_ji = 1 if focus_member_name in otro_perceptions.get(q_pe, {}).get(other_member_name, []) else 0
        pr_ji = 1 if focus_member_name in otro_perceptions.get(q_pr, {}).get(other_member_name, []) else 0
        distancia = (e_ij - r_ij + pe_ji - pr_ji) + (e_ji - r_ji + pe_ij - pr_ij)
        
        members_data_list_detailed.append({
            'nombre_completo': other_member_name, 'id_corto': other_member_dict.get('iniz', 'N/A'),
            'sexo': other_member_dict.get('sexo', 'Desconocido'), 'distancia_sociometrica': int(round(distancia))
        })
        
    return members_data_list_detailed

def calculate_civsoc_matrix(institution_name, group_name, question_keys, allow_self_on_diagonal=False):
    """
    Calcula la Matriz de Relaciones Completas (CIVSOC) de forma FLEXIBLE.
    
    Usa las claves de pregunta proporcionadas y trata las que faltan como no disponibles.
    Si allow_self_on_diagonal es True, calcula un código simplificado (0, 1 o 2) para la diagonal.
    
    Devuelve una tupla con:
    1. Una matriz de Python con los códigos de relación.
    2. La lista de miembros ordenada que corresponde a las filas/columnas.
    3. Un diccionario para la leyenda dinámica.
    """
    # 1. Obtener datos base: definiciones de preguntas y lista de miembros ordenada.
    all_defs = get_class_question_definitions(institution_name, group_name)
    members_list = sorted(
        members_data.get(institution_name, {}).get(group_name, []),
        key=lambda m: (m.get('cognome', '').upper(), m.get('nome', '').upper())
    )
    member_names = [f"{m.get('nome','').title()} {m.get('cognome','').title()}" for m in members_list]
    num_members = len(member_names)

    # Mapear las claves de pregunta a sus roles para el cálculo
    accion_pos_key = question_keys.get('accion_pos')
    accion_neg_key = question_keys.get('accion_neg')
    meta_pos_key = question_keys.get('meta_pos')
    meta_neg_key = question_keys.get('meta_neg')

    # 2. Construir una matriz numérica temporal con NumPy para los cálculos.
    # Se inicializa con 0 (código para "Indiferencia").
    civsoc_matrix_np = np.full((num_members, num_members), 0, dtype=int)

    # 3. Iterar sobre cada par de miembros (Actor -> Objeto) para calcular el código de relación.
    for i, actor_name in enumerate(member_names): # 'i' es el Actor (fila)
        actor_actions = questionnaire_responses_data.get((institution_name, group_name, actor_name), {})
        actor_perceptions = cognitive_social_structures_data.get((institution_name, group_name, actor_name), {})

        for j, target_name in enumerate(member_names): # 'j' es el Objeto (columna)
            
            # --- INICIO DEL BLOQUE PARA MANEJAR LA DIAGONAL (i == j) ---
            if i == j: 
                if allow_self_on_diagonal:
                    # Lógica simplificada para la diagonal: solo se consideran acciones reales.
                    i_elige_i = actor_name in actor_actions.get(accion_pos_key, [])
                    i_rechaza_i = actor_name in actor_actions.get(accion_neg_key, [])
                    
                    code = 0 # Indiferencia por defecto
                    if i_elige_i: code = 1
                    elif i_rechaza_i: code = 2
                    civsoc_matrix_np[i, j] = code
                else:
                    # Si no se permite, el valor se deja en 0.
                    # El bucle de conversión final lo cambiará por 'X'.
                    pass 
                continue # Pasa al siguiente miembro en la fila
            # --- FIN DEL BLOQUE PARA MANEJAR LA DIAGONAL ---

            # Lógica para las relaciones interpersonales (i != j)
            # Determinar las 4 condiciones booleanas para la relación i -> j
            i_elige_j = target_name in actor_actions.get(accion_pos_key, []) if accion_pos_key else False
            i_rechaza_j = target_name in actor_actions.get(accion_neg_key, []) if accion_neg_key else False
            # La percepción es sobre uno mismo (SELF), por eso el target es 'actor_name'
            i_cree_que_j_le_elige = target_name in actor_perceptions.get(meta_pos_key, {}).get(actor_name, []) if meta_pos_key else False
            i_cree_que_j_le_rechaza = target_name in actor_perceptions.get(meta_neg_key, {}).get(actor_name, []) if meta_neg_key else False

            # Asignar el código de relación según la tabla de verdad de CIVSOC
            code = 0 # Indiferencia por defecto
            if i_elige_j and i_cree_que_j_le_elige: code = 5
            elif i_rechaza_j and i_cree_que_j_le_rechaza: code = 8
            elif i_elige_j and i_cree_que_j_le_rechaza: code = 6
            elif i_rechaza_j and i_cree_que_j_le_elige: code = 7
            elif i_elige_j: code = 1
            elif i_rechaza_j: code = 2
            elif i_cree_que_j_le_elige: code = 3
            elif i_cree_que_j_le_rechaza: code = 4

            civsoc_matrix_np[i, j] = code
            
    # 4. Convertir la matriz NumPy a una lista de Python, manejando la diagonal según la opción.
    final_matrix_python = []
    for i, row in enumerate(civsoc_matrix_np):
        new_row = []
        for j, value in enumerate(row):
            # Si la opción NO está activada Y es una celda diagonal, poner 'X'.
            if not allow_self_on_diagonal and i == j:
                new_row.append('X')
            else:
                new_row.append(value)
        final_matrix_python.append(new_row)
            
    # 5. Construir una Leyenda Dinámica basada en las preguntas seleccionadas.
    full_legend = {
        "1": "Elección", "2": "Rechazo", "3": "Percepción de Elección", "4": "Percepción de Rechazo",
        "5": "Elección y Percepción de Elección", "6": "Elección y Percepción de Rechazo",
        "7": "Rechazo y Percepción de Elección", "8": "Rechazo y Percepción de Rechazo",
        "0": "Indiferencia"
    }
    
    possible_codes = {0} # La indiferencia siempre es posible
    if accion_pos_key: possible_codes.add(1)
    if accion_neg_key: possible_codes.add(2)
    if meta_pos_key: possible_codes.add(3)
    if meta_neg_key: possible_codes.add(4)
    if accion_pos_key and meta_pos_key: possible_codes.add(5)
    if accion_pos_key and meta_neg_key: possible_codes.add(6)
    if accion_neg_key and meta_pos_key: possible_codes.add(7)
    if accion_neg_key and meta_neg_key: possible_codes.add(8)

    dynamic_legend = {str(k): v for k, v in full_legend.items() if int(k) in possible_codes}
    
    # 6. Devolver los resultados.
    return (final_matrix_python, members_list, dynamic_legend)

def calculate_accuracy_matrix(institution_name, group_name, action_q_key, meta_q_key, allow_self_on_diagonal=False):
    """
    Calcula una matriz de precisión para TODOS los miembros del grupo.
    Cada fila 'i' representa la precisión de las creencias del miembro 'i'.
    Si allow_self_on_diagonal es True, la diagonal (i, i) muestra la precisión
    de las creencias del miembro 'i' sobre sus propias acciones hacia sí mismo.
    """
    members_list = sorted(
        members_data.get(institution_name, {}).get(group_name, []),
        key=lambda m: (m.get('cognome', '').upper(), m.get('nome', '').upper())
    )
    member_names = [f"{m.get('nome','').title()} {m.get('cognome','').title()}" for m in members_list]
    num_members = len(member_names)

    # 1. Preparar la matriz y la leyenda
    # Usamos dtype=object para poder mezclar números y la letra 'X'
    accuracy_matrix = np.full((num_members, num_members), '', dtype=object)
    legend = {
        "1": "Acierto (Creyó y Ocurrió)",
        "2": "Error / Falso Positivo (Creyó y NO Ocurrió)",
        "3": "Omisión / Falso Negativo (NO Creyó y SÍ Ocurrió)",
        "0": "Indiferencia Correcta (NO Creyó y NO Ocurrió)"
    }

    # 2. Iterar sobre cada miembro, tratándolo como el 'Ego' de su propia fila
    for i, ego_name in enumerate(member_names):
        # Obtener las creencias de este Ego
        ego_perceptions = cognitive_social_structures_data.get((institution_name, group_name, ego_name), {})
        ego_beliefs = set(ego_perceptions.get(meta_q_key, {}).get(ego_name, []))

        # Iterar sobre todos los 'Alters' para llenar la fila del Ego
        for j, alter_name in enumerate(member_names):
            
            # --- INICIO DEL BLOQUE PARA MANEJAR LA DIAGONAL (i == j) ---
            if i == j:
                if allow_self_on_diagonal:
                    # Lógica para "auto-precisión": ¿Son correctas las creencias del Ego sobre sí mismo?
                    ego_actions = questionnaire_responses_data.get((institution_name, group_name, ego_name), {})
                    
                    # Acción real: ¿El Ego se eligió/rechazó a sí mismo?
                    ego_did_action_towards_self = ego_name in ego_actions.get(action_q_key, [])
                    # Creencia: ¿El Ego creía que se elegiría/rechazaría a sí mismo?
                    ego_believed_self_would_act = ego_name in ego_beliefs

                    # Asignar código de precisión basado en la comparación
                    code = 0  # Indiferencia Correcta por defecto
                    if ego_believed_self_would_act and ego_did_action_towards_self:
                        code = 1  # Acierto
                    elif ego_believed_self_would_act and not ego_did_action_towards_self:
                        code = 2  # Error
                    elif not ego_believed_self_would_act and ego_did_action_towards_self:
                        code = 3  # Omisión
                    
                    accuracy_matrix[i, j] = code
                else:
                    # Comportamiento original si la opción no está marcada
                    accuracy_matrix[i, j] = 'X'
                
                continue # Pasa al siguiente miembro en la fila
            # --- FIN DEL BLOQUE PARA MANEJAR LA DIAGONAL ---

            # Lógica para las relaciones interpersonales (i != j)
            # Obtener la acción real del Alter hacia el Ego
            alter_actions = questionnaire_responses_data.get((institution_name, group_name, alter_name), {})
            alter_did_action_towards_ego = ego_name in alter_actions.get(action_q_key, [])
            
            # Obtener la creencia del Ego sobre la acción de este Alter
            ego_believed_alter_would_act = alter_name in ego_beliefs
            
            # Asignar código de precisión
            code = 0  # Indiferencia Correcta por defecto
            if ego_believed_alter_would_act and alter_did_action_towards_ego:
                code = 1  # Acierto
            elif ego_believed_alter_would_act and not alter_did_action_towards_ego:
                code = 2  # Error
            elif not ego_believed_alter_would_act and alter_did_action_towards_ego:
                code = 3  # Omisión
            
            accuracy_matrix[i, j] = code

    # 3. Convertir la matriz final a una lista de Python para su uso en la UI
    final_matrix_python = [list(row) for row in accuracy_matrix]

    return final_matrix_python, members_list, legend

print("handlers_groups.py refactorizado y listo para su uso en la aplicación de escritorio.")