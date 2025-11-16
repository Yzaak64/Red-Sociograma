# handlers_questionnaire.py
# (v15.1 - Refactorizado para aplicación de escritorio.
#  Usa "Institución"/"Grupo" y "Miembro". Funciones devuelven datos y estados.)

import collections
import traceback
from sociograma_data import (
    cognitive_social_structures_data, # <-- AÑADE ESTA LÍNEA
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
    VERSIÓN HÍBRIDA v4: Muestra el nombre del nominator percibido, manejando
    correctamente tanto la percepción de otros como la auto-percepción ([SELF]).
    """
    if not all([institution_name, group_name, member_name_key, app_data_ref]):
        return {'success': False, 'message': "Contexto inválido.", 'questions': [], 'saved_responses': {}}

    current_group_defs = get_class_question_definitions(institution_name, group_name)
    if not current_group_defs:
        return {'success': True, 'message': "No hay preguntas definidas.", 'questions': [], 'saved_responses': {}}

    questions_to_render = []
    try:
        sorted_q_items = sorted(current_group_defs.items(), key=lambda item: (item[1].get('order', 99), item[0]))
    except Exception as e:
        return {'success': False, 'message': f"Error al ordenar preguntas: {e}", 'questions': [], 'saved_responses': {}}

    for q_id, q_def in sorted_q_items:
        data_key = q_def.get('data_key', q_id)
        max_selections = q_def.get('max_selections', 0)
        if max_selections == 0: continue

        is_cognitive = q_def.get('is_cognitive', False)
        perceived_nominator = q_def.get('perceived_nominator')
        
        saved_responses = []
        # Tomamos el texto base directamente de la definición guardada
        question_text = q_def.get('text', 'Pregunta sin texto')

        if is_cognitive:
            if not perceived_nominator: 
                continue

            # --- INICIO DE LA NUEVA LÓGICA SIMPLIFICADA ---
            final_perceived_nominator = perceived_nominator
            
            # Comprobamos si es una pregunta de auto-percepción
            if perceived_nominator == '[SELF]':
                # El nominador percibido es el propio miembro que responde
                final_perceived_nominator = member_name_key
                # Añadimos SIEMPRE el nombre del miembro al final
                question_text = f"{question_text} **[{member_name_key}]**"
            else:
                # Si es una percepción sobre otro, hacemos lo mismo que antes
                question_text = f"{question_text} **[{perceived_nominator}]**"
            # --- FIN DE LA NUEVA LÓGICA SIMPLIFICADA ---
            
            # Buscamos la respuesta en la estructura de datos de percepciones
            cognitive_key = (institution_name, group_name, member_name_key) # El que responde es el perceptor
            perceiver_data = app_data_ref.cognitive_social_structures_data.get(cognitive_key, {})
            # Usamos 'final_perceived_nominator' para buscar la respuesta correcta
            saved_responses = perceiver_data.get(data_key, {}).get(final_perceived_nominator, [])
        else:
            # Si no es cognitiva, buscamos la respuesta en la estructura de acciones directas
            direct_action_key = (institution_name, group_name, member_name_key)
            saved_responses = app_data_ref.questionnaire_responses_data.get(direct_action_key, {}).get(data_key, [])
        
        allow_self = q_def.get('allow_self_selection', False)
        exclude_name_for_options = member_name_key if not allow_self else None
        
        try:
            # Obtenemos la lista de miembros para los dropdowns
            member_options = get_member_options_for_dropdown(
                school_name=institution_name, class_name=group_name,
                exclude_member_display_name=exclude_name_for_options, app_data_ref=app_data_ref
            )
        except Exception as e_get_opts:
            return {'success': False, 'message': f"Error al obtener opciones para '{data_key}':\n{e_get_opts}", 'questions': [], 'saved_responses': {}}
        
        question_info = {
            'data_key': data_key,
            'text': question_text, # El texto ya está formateado
            'max_selections': max_selections,
            'options': member_options,
            'saved_selections': saved_responses
        }
        questions_to_render.append(question_info)

    return {'success': True, 'message': "Datos del cuestionario recuperados.", 'questions': questions_to_render, 'saved_responses': {}}

def save_questionnaire_responses(institution_name, group_name, member_name_key, responses_from_ui):
    """
    VERSIÓN HÍBRIDA v2 CORREGIDA: Arregla el KeyError al buscar la definición de la pregunta.
    """
    if not all([institution_name, group_name, member_name_key]):
        return False, "Contexto inválido para guardar respuestas."

    for data_key, selections in responses_from_ui.items():
        actual_selections = [s for s in selections if s and s != 'Seleccionar']
        if len(actual_selections) != len(set(actual_selections)):
            counts = collections.Counter(actual_selections)
            first_duplicate = next((item for item, count in counts.items() if count > 1), "desconocido")
            return False, f"Error: Se encontraron selecciones duplicadas de '{first_duplicate}'. Por favor, corrija."

    try:
        direct_actions_to_save = {}
        cognitive_perceptions_to_save = collections.defaultdict(lambda: collections.defaultdict(list))
        
        current_defs = get_class_question_definitions(institution_name, group_name)
        
        for data_key, selections in responses_from_ui.items():
            # --- INICIO DE LA CORRECCIÓN ---
            # ANTES: q_def = current_defs.get(data_key)  <-- ¡INCORRECTO!
            # AHORA: Buscamos la definición correcta iterando sobre los valores.
            q_def = next((d for d in current_defs.values() if d.get('data_key') == data_key), None)
            # --- FIN DE LA CORRECCIÓN ---
            
            if not q_def: continue

            cleaned_selections = [s for s in selections if s and s != 'Seleccionar']

            if q_def.get('is_cognitive'):
                perceived_nominator = q_def.get('perceived_nominator')
                
                if perceived_nominator == '[SELF]':
                    if cleaned_selections:
                        cognitive_perceptions_to_save[data_key][member_name_key] = cleaned_selections
                elif perceived_nominator:
                    cognitive_perceptions_to_save[data_key][perceived_nominator] = cleaned_selections

            else:
                direct_actions_to_save[data_key] = cleaned_selections

        direct_action_key = (institution_name, group_name, member_name_key)
        questionnaire_responses_data.setdefault(direct_action_key, {}).update(direct_actions_to_save)
        
        if cognitive_perceptions_to_save:
            cognitive_key = (institution_name, group_name, member_name_key)
            perceiver_all_perceptions = cognitive_social_structures_data.setdefault(cognitive_key, collections.defaultdict(dict))
            
            for data_key, perceived_data in cognitive_perceptions_to_save.items():
                # Asegurarse de que el diccionario para esta clave de pregunta exista
                perceiver_all_perceptions.setdefault(data_key, {}).update(perceived_data)

        return True, "Respuestas guardadas correctamente."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al guardar las respuestas: {e}"


print("handlers_questionnaire.py refactorizado y listo para su uso en la aplicación de escritorio.")