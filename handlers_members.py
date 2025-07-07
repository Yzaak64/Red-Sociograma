# handlers_members.py
# (v11.4 - Refactorizado para aplicación de escritorio.
#  Usa "miembro", "Institución"/"Grupo" y "sexo". Funciones devuelven tuplas (éxito, mensaje).)

import traceback
from sociograma_data import members_data, questionnaire_responses_data

# Nota: La función 'on_members_select_change_handler' es eliminada.
# Su lógica (actualizar campos de texto con detalles) ahora es responsabilidad
# directa de la clase de la GUI principal (SociogramaApp) al manejar el evento
# de selección de la lista.

# Nota: Las funciones 'on_members_nueva_button_handler' y 'on_members_modifica_button_handler'
# son eliminadas. La GUI principal ahora manejará la apertura y el llenado
# de los formularios directamente.

# --- Funciones Lógicas de la Vista de Miembros ---

def handle_delete_member(institution_name, group_name, member_name_key_to_delete):
    """
    Lógica para eliminar un miembro y sus datos asociados.
    member_name_key_to_delete es el 'Nombre Apellido' del miembro.
    Devuelve (éxito, mensaje).
    """
    if not all([institution_name, group_name, member_name_key_to_delete]):
        return False, "Faltan datos (institución, grupo o nombre de miembro) para la eliminación."

    try:
        group_members = members_data.get(institution_name, {}).get(group_name)
        if group_members is None:
            return False, f"No se encontró el grupo '{group_name}'."

        original_len = len(group_members)
        
        # Filtrar la lista, excluyendo al miembro a eliminar
        # Se busca por nombre completo, insensible a mayúsculas/minúsculas.
        members_data[institution_name][group_name] = [
            m for m in group_members 
            if f"{m.get('nome','').title()} {m.get('cognome','').title()}".strip().lower() != member_name_key_to_delete.lower()
        ]

        if len(members_data[institution_name][group_name]) < original_len:
            # Si el miembro fue eliminado, también eliminar sus respuestas.
            response_key_to_delete = (institution_name, group_name, member_name_key_to_delete)
            if response_key_to_delete in questionnaire_responses_data:
                del questionnaire_responses_data[response_key_to_delete]
            
            return True, f"Miembro '{member_name_key_to_delete}' y sus respuestas eliminados."
        else:
            return False, f"No se encontró al miembro '{member_name_key_to_delete}' para eliminar."

    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al eliminar miembro: {e}"


def prepare_for_questionnaire_view(institution_name, group_name, member_name_key):
    """
    Prepara el contexto necesario para abrir la vista del cuestionario.
    En una app de escritorio, esto principalmente valida que el contexto es correcto.
    La GUI se encargará de cambiar la vista.
    Devuelve un diccionario de contexto o None si hay error.
    """
    if not all([institution_name, group_name, member_name_key]):
        print("Error: Faltan datos para preparar el cuestionario.")
        return None
    
    # Aquí se podrían hacer validaciones adicionales si fuera necesario
    # Por ejemplo, verificar si el miembro realmente existe en los datos
    
    context = {
        'school': institution_name,
        'class_name': group_name,
        'member': member_name_key
    }
    
    return context

# Nota: La función 'on_members_salir_button_handler' es eliminada.
# La navegación hacia atrás será manejada directamente por la clase SociogramaApp.

print("handlers_members.py refactorizado y listo para su uso en la aplicación de escritorio.")