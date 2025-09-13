# sociogram_utils.py
# (v1.13.0 - Versión para aplicación de escritorio.
#  Corregida la cascada de llamadas para los parámetros de opciones.
#  Terminología "Miembro" y "Institución/Grupo".)

import collections
import traceback

# Se asume que los módulos de datos y handlers serán importados en el módulo principal
# que llama a estas funciones.

# --- Funciones de Utilidad para la UI del Sociograma ---

def get_participant_options(app_state, app_data_ref, handlers_utils_ref):
    """
    Obtiene la lista de miembros de un grupo para poblar el desplegable de foco.
    
    Args:
        app_state (dict): El estado de la aplicación.
        app_data_ref: Referencia al módulo de datos (sociograma_data).
        handlers_utils_ref: Referencia al módulo de utilidades (handlers_utils).

    Returns:
        Una lista de tuplas (texto_display, valor_interno) para un desplegable.
        Incluye la opción "Todos (Grafo Completo)".
    """
    context = app_state.get('current_group_viewing_members')
    if not context or not context.get('school') or not context.get('class_name'):
        print("Error en get_participant_options: Contexto de grupo no válido.")
        return [('Error: Sin contexto', None)]

    institution_name = context['school']
    group_name = context['class_name']

    get_member_options_func = getattr(handlers_utils_ref, 'get_member_options_for_dropdown', None)
    if not callable(get_member_options_func):
        print("Error crítico en get_participant_options: get_member_options_for_dropdown no es llamable.")
        return [('Error: Función no encontrada', None)]

    try:
        # La llamada INTERNA a la función de utils SÍ lleva el parámetro.
        # Esto le dice a la función de utils que añada la opción "Todos..."
        member_options = get_member_options_func(
            school_name=institution_name,
            class_name=group_name,
            app_data_ref=app_data_ref,
            include_all_option=True
        )
        return member_options
    except Exception as e:
        print(f"Excepción en get_participant_options al llamar a get_member_options_for_dropdown: {e}")
        traceback.print_exc()
        return [('Error al cargar', None)]


def get_relation_options(app_state, app_data_ref):
    """
    Obtiene las relaciones (preguntas) de un grupo para poblar checkboxes.
    AHORA INCLUYE LA POLARIDAD para los botones de selección rápida.
    
    Args:
        app_state (dict): El estado de la aplicación.
        app_data_ref: Referencia al módulo de datos (sociograma_data).

    Returns:
        Una lista de diccionarios, cada uno con 'data_key', 'label' y 'polarity'.
    """
    context = app_state.get('current_group_viewing_members')
    if not context or not context.get('school') or not context.get('class_name'):
        print("Error en get_relation_options: Contexto de grupo no válido.")
        return []

    institution_name = context['school']
    group_name = context['class_name']

    try:
        app_data_ref.regenerate_relationship_maps_for_class(institution_name, group_name)
        
        relation_options_map = app_data_ref.sociogram_relation_options_map
        # Obtenemos las definiciones completas para poder acceder a la polaridad
        current_class_questions = app_data_ref.get_class_question_definitions(institution_name, group_name)
        
        options_list = []
        if isinstance(relation_options_map, dict):
            sorted_items = sorted(
                [(k, v) for k, v in relation_options_map.items() if k != 'all'],
                key=lambda item: item[1]
            )
            for data_key, label in sorted_items:
                # Buscamos la definición de la pregunta para obtener su polaridad
                q_def = next((d for d in current_class_questions.values() if d.get('data_key') == data_key), {})
                polarity = q_def.get('polarity', 'neutral')
                # <-- CAMBIO CLAVE: Añadimos la polaridad al diccionario -->
                options_list.append({'data_key': data_key, 'label': label, 'polarity': polarity})
        
        return options_list
    except Exception as e:
        print(f"Error en get_relation_options al regenerar/procesar mapas: {e}")
        traceback.print_exc()
        return []


print("sociogram_utils.py refactorizado y listo para su uso en la aplicación de escritorio.")