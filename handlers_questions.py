# handlers_questions.py
# (v18.1 - Refactorizado para aplicación de escritorio.
#  Usa "Institución"/"Grupo" y "Miembro". Funciones devuelven tuplas (éxito, mensaje/datos).)

import collections
import traceback
from sociograma_data import (
    questionnaire_responses_data,
    regenerate_relationship_maps_for_class,
    get_class_question_definitions,
    members_data
)

# Nota: Las funciones de logging y auxiliares que antes estaban aquí
# ahora son responsabilidad de la capa de la GUI (la clase SociogramaApp).

# --- Funciones Lógicas de Gestión de Preguntas ---

def get_question_definitions_for_group(institution_name, group_name):
    """
    Obtiene las definiciones de preguntas para un grupo específico, ordenadas.
    Devuelve una lista de tuplas (q_id, q_def).
    """
    if not institution_name or not group_name:
        return []
    
    current_group_defs = get_class_question_definitions(institution_name, group_name)
    if not isinstance(current_group_defs, collections.OrderedDict) or not current_group_defs:
        return []
        
    try:
        sorted_q_items = sorted(
            current_group_defs.items(),
            key=lambda item: (item[1].get('order', 99), item[0])
        )
        return sorted_q_items
    except Exception as e:
        print(f"ERROR en get_question_definitions_for_group: {e}")
        return []

def get_max_possible_selections(institution_name, group_name, allow_self_selection):
    """
    Calcula el máximo número de selecciones posibles basado en N miembros.
    """
    num_members = 0
    if institution_name in members_data and group_name in members_data.get(institution_name, {}):
        num_members = len(members_data[institution_name].get(group_name, []))

    if num_members <= 0: return 0
    if num_members == 1 and not allow_self_selection: return 0
    
    max_sel_calc = num_members if allow_self_selection else (num_members - 1)
    return max(0, max_sel_calc)

def _validate_question_data(institution_name, group_name, q_data, is_new, original_q_id=None):
    """
    Función interna de validación. Reúne todos los chequeos de una pregunta.
    Devuelve (es_valido, mensaje_error).
    """
    q_id = q_data.get('id', '').strip()
    q_text = q_data.get('text', '').strip()
    q_data_key = q_data.get('data_key', '').strip()
    q_max_selections = q_data.get('max_selections', 0)
    q_allow_self = q_data.get('allow_self_selection', False)
    
    errors = []
    if not q_id: errors.append("El ID de la pregunta es obligatorio.")
    if not q_text: errors.append("El texto de la pregunta es obligatorio.")
    if not q_data_key: errors.append("La Clave de Datos (Data Key) es obligatoria.")

    current_defs = get_class_question_definitions(institution_name, group_name)
    
    # Validar unicidad de ID y Data Key
    if is_new:
        if q_id in current_defs:
            errors.append(f"Ya existe una pregunta con el ID '{q_id}'.")
        if any(d.get('data_key') == q_data_key for d in current_defs.values()):
            errors.append(f"Ya existe una pregunta con la Clave de Datos '{q_data_key}'.")
    else: # Modificando
        if q_id != original_q_id and q_id in current_defs:
            errors.append(f"El nuevo ID '{q_id}' ya pertenece a otra pregunta.")
        if any(d.get('data_key') == q_data_key for id_key, d in current_defs.items() if id_key != original_q_id):
            errors.append(f"La Clave de Datos '{q_data_key}' ya pertenece a otra pregunta.")

    # Validar max_selections
    max_possible = get_max_possible_selections(institution_name, group_name, q_allow_self)
    if q_max_selections < 0:
        errors.append("El máximo de selecciones no puede ser negativo.")
    elif q_max_selections > max_possible:
        errors.append(f"El máximo de selecciones ({q_max_selections}) excede el límite permitido de {max_possible} para este grupo.")
        
    if errors:
        return False, "\n".join(errors)
    
    return True, "Validación exitosa."

def handle_add_question(institution_name, group_name, new_q_data):
    """
    Lógica para añadir una nueva definición de pregunta.
    new_q_data es un diccionario con todos los campos de la pregunta.
    Devuelve (éxito, mensaje).
    """
    is_valid, msg = _validate_question_data(institution_name, group_name, new_q_data, is_new=True)
    if not is_valid:
        return False, msg

    try:
        q_id = new_q_data.pop('id') # Extraer el ID para usarlo como clave
        current_defs = get_class_question_definitions(institution_name, group_name)
        current_defs[q_id] = new_q_data
        
        regenerate_relationship_maps_for_class(institution_name, group_name)
        
        return True, f"Pregunta '{q_id}' añadida correctamente."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al añadir la pregunta: {e}"

def handle_modify_question(institution_name, group_name, original_q_id, updated_q_data):
    """
    Lógica para modificar una definición de pregunta existente.
    updated_q_data es un diccionario con los nuevos datos.
    Devuelve (éxito, mensaje).
    """
    current_defs = get_class_question_definitions(institution_name, group_name)
    if original_q_id not in current_defs:
        return False, f"La pregunta original con ID '{original_q_id}' no fue encontrada."

    is_valid, msg = _validate_question_data(institution_name, group_name, updated_q_data, is_new=False, original_q_id=original_q_id)
    if not is_valid:
        return False, msg

    try:
        new_q_id = updated_q_data.pop('id')
        original_data_key = current_defs[original_q_id].get('data_key')
        new_data_key = updated_q_data.get('data_key')

        # Si el ID cambia, hay que eliminar el antiguo y añadir el nuevo
        if new_q_id != original_q_id:
            del current_defs[original_q_id]
        
        current_defs[new_q_id] = updated_q_data
        
        # Si la data_key cambió, hay que migrar las respuestas guardadas
        if new_data_key != original_data_key:
            for key, responses in questionnaire_responses_data.items():
                # La clave es (institución, grupo, nombre_miembro)
                if key[0] == institution_name and key[1] == group_name:
                    if original_data_key in responses:
                        responses[new_data_key] = responses.pop(original_data_key)
        
        regenerate_relationship_maps_for_class(institution_name, group_name)
        
        return True, f"Pregunta '{original_q_id}' actualizada a '{new_q_id}'."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al modificar la pregunta: {e}"

def handle_delete_question(institution_name, group_name, q_id_to_delete):
    """
    Lógica para eliminar una definición de pregunta.
    Devuelve (éxito, mensaje).
    """
    current_defs = get_class_question_definitions(institution_name, group_name)
    if q_id_to_delete not in current_defs:
        return False, f"La pregunta con ID '{q_id_to_delete}' no fue encontrada."

    try:
        q_def_to_delete = current_defs.pop(q_id_to_delete)
        data_key_to_clean = q_def_to_delete.get('data_key')

        # Limpiar las respuestas asociadas a esta data_key
        if data_key_to_clean:
            for key, responses in questionnaire_responses_data.items():
                if key[0] == institution_name and key[1] == group_name:
                    if data_key_to_clean in responses:
                        del responses[data_key_to_clean]
        
        regenerate_relationship_maps_for_class(institution_name, group_name)
        
        return True, f"Pregunta '{q_id_to_delete}' y sus respuestas asociadas eliminadas."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al eliminar la pregunta: {e}"

print("handlers_questions.py refactorizado y listo para su uso en la aplicación de escritorio.")