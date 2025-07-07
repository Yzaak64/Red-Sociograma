# handlers_questionnaire.py
# (v15.1 - Refactorizado para aplicación de escritorio.
#  Usa "Institución"/"Grupo" y "Miembro". Funciones devuelven datos y estados.)

import collections
import traceback
from sociograma_data import (
    questionnaire_responses_data,
    get_class_question_definitions,
    regenerate_relationship_maps_for_class
)
# Se asume que handlers_utils será importado en el módulo principal
# para acceder a sus funciones.
from handlers_utils import get_member_options_for_dropdown

# --- Funciones Lógicas del Cuestionario ---

def get_questionnaire_data_for_member(institution_name, group_name, member_name_key, app_data_ref):
    """
    Recopila todos los datos necesarios para renderizar el cuestionario de un miembro.
    """
    if not all([institution_name, group_name, member_name_key, app_data_ref]):
        return {'success': False, 'message': "Contexto inválido.", 'questions': [], 'saved_responses': {}}

    current_group_defs = get_class_question_definitions(institution_name, group_name)
    if not current_group_defs:
        return {'success': True, 'message': "No hay preguntas definidas.", 'questions': [], 'saved_responses': {}}

    data_key_member_lookup = (institution_name, group_name, member_name_key)
    saved_responses_for_member = questionnaire_responses_data.get(data_key_member_lookup, {})
    questions_to_render = []
    
    try:
        sorted_q_items = sorted(current_group_defs.items(), key=lambda item: (item[1].get('order', 99), item[0]))
    except Exception as e:
        return {'success': False, 'message': f"Error al ordenar preguntas: {e}", 'questions': [], 'saved_responses': {}}

    for q_id, q_def in sorted_q_items:
        data_key = q_def.get('data_key', q_id)
        max_selections = q_def.get('max_selections', 0)
        if max_selections == 0: continue

        allow_self = q_def.get('allow_self_selection', False)
        exclude_name_for_options = member_name_key if not allow_self else None

        try:
            # Llamada corregida sin el parámetro obsoleto
            member_options = get_member_options_for_dropdown(
                school_name=institution_name,
                class_name=group_name,
                exclude_member_display_name=exclude_name_for_options,
                app_data_ref=app_data_ref
            )
        except Exception as e_get_opts:
            # Mensaje de error más claro para la GUI
            error_message = f"Error al obtener opciones para pregunta '{data_key}':\n{e_get_opts}"
            return {'success': False, 'message': error_message, 'questions': [], 'saved_responses': {}}
        
        question_info = {
            'data_key': data_key,
            'text': q_def.get('text', 'Pregunta sin texto'),
            'max_selections': max_selections,
            'options': member_options,
        }
        questions_to_render.append(question_info)

    return {
        'success': True,
        'message': "Datos del cuestionario recuperados.",
        'questions': questions_to_render,
        'saved_responses': saved_responses_for_member
    }


def save_questionnaire_responses(institution_name, group_name, member_name_key, responses_from_ui):
    """
    Valida y guarda las respuestas del cuestionario para un miembro.
    
    responses_from_ui es un diccionario donde la clave es el 'data_key' de la pregunta
    y el valor es una lista de los miembros seleccionados.
    
    Devuelve una tupla (éxito, mensaje).
    """
    if not all([institution_name, group_name, member_name_key]):
        return False, "Contexto inválido para guardar respuestas."

    # Validación: verificar selecciones duplicadas dentro de una misma pregunta
    for data_key, selections in responses_from_ui.items():
        # ¡AQUÍ ESTÁ EL CAMBIO CLAVE!
        # Filtramos las selecciones para quitar los strings vacíos o "Seleccionar" ANTES de buscar duplicados.
        actual_selections = [s for s in selections if s and s != 'Seleccionar']
        
        if len(actual_selections) != len(set(actual_selections)):
            # Encontramos duplicados solo entre las selecciones reales
            counts = collections.Counter(actual_selections)
            first_duplicate = next((item for item, count in counts.items() if count > 1), "desconocido")
            return False, f"Error de validación: Se encontraron selecciones duplicadas de '{first_duplicate}' para una pregunta. Por favor, corrija."

    # Si la validación es exitosa, guardamos los datos
    try:
        data_key_member = (institution_name, group_name, member_name_key)
        
        # Limpiar respuestas de preguntas que ya no existen en las definiciones
        current_defs = get_class_question_definitions(institution_name, group_name)
        valid_data_keys = {q_def.get('data_key') for q_def in current_defs.values()}
        
        final_responses_to_save = {
            key: value for key, value in responses_from_ui.items() if key in valid_data_keys
        }

        questionnaire_responses_data[data_key_member] = final_responses_to_save
        
        # La regeneración de mapas puede ser llamada después de guardar, desde la capa de la GUI si es necesario
        # regenerate_relationship_maps_for_class(institution_name, group_name)

        return True, "Respuestas guardadas correctamente."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al guardar las respuestas: {e}"


def handle_manage_questions_request(institution_name, group_name):
    """
    Prepara el contexto para cambiar a la vista de gestión de preguntas.
    Es una función simple que principalmente regenera los mapas por si algo cambió.
    Devuelve (éxito, mensaje).
    """
    try:
        # Es una buena práctica regenerar los mapas antes de ir a gestionar preguntas,
        # ya que podrían haber cambiado en otra sesión.
        regenerate_relationship_maps_for_class(institution_name, group_name)
        return True, "Contexto para gestión de preguntas preparado."
    except Exception as e:
        return False, f"Error al preparar la gestión de preguntas: {e}"


print("handlers_questionnaire.py refactorizado y listo para su uso en la aplicación de escritorio.")