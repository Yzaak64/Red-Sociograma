# handlers_groups.py
# (v16.1 - Refactorizado para aplicación de escritorio.
#  Usa "Grupo/Institución" y "miembro". Funciones devuelven tuplas o datos.)

import traceback
import collections
from sociograma_data import (
    classes_data,
    members_data,
    questionnaire_responses_data,
    get_class_question_definitions,
    question_definitions
)
# Se asume que pdf_generator será importado en el módulo principal
import pdf_generator

# Nota: on_groups_select_change_handler y los handlers de formularios
# (add/modify) ya han sido refactorizados y movidos a la capa de lógica
# principal en Bloque 5 del script de la app.

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
    
    # Podrían ir más validaciones aquí, por ejemplo, verificar si el grupo existe.
    
    context = {
        'school': institution_name,
        'class_name': group_name
    }
    return context


def handle_generate_diana_data(institution_name, group_name, selected_question_keys, show_lines):
    """
    Recopila datos, llama al generador de imagen de la Diana y devuelve los bytes de la imagen.
    Devuelve los bytes de la imagen PNG o None si hay error.
    """
    if not all([institution_name, group_name]):
        print("Error en handle_generate_diana_data: Faltan institución o grupo.")
        return None
    if not selected_question_keys:
        print("Info en handle_generate_diana_data: No hay preguntas seleccionadas.")
        return None

    class_members_raw = members_data.get(institution_name, {}).get(group_name, [])
    if not class_members_raw:
        print(f"Error en handle_generate_diana_data: No hay miembros en {institution_name}/{group_name}.")
        return None

    # Mapear nombres a detalles para un acceso rápido
    member_info_intermediate = {
        f"{m.get('nome','').strip().title()} {m.get('cognome','').strip().title()}".strip(): {
            'id_corto': m.get('iniz', 'N/A'),
            'sexo': m.get('sexo', 'Desconocido')
        } for m in class_members_raw
    }

    # Calcular puntajes de afinidad
    detailed_affinity_scores = collections.defaultdict(lambda: {'total_recibido': 0, 'choices_by_pos': collections.defaultdict(int)})
    edges_data_for_viz = []
    members_in_class_set = set(member_info_intermediate.keys())

    for (resp_inst, resp_grp, nominator_key), resp_dict in questionnaire_responses_data.items():
        if resp_inst == institution_name and resp_grp == group_name and nominator_key in members_in_class_set:
            for q_key, nominees_list in resp_dict.items():
                if q_key in selected_question_keys:
                    for idx, nominee_key in enumerate(nominees_list):
                        if nominee_key in members_in_class_set:
                            detailed_affinity_scores[nominee_key]['total_recibido'] += 1
                            detailed_affinity_scores[nominee_key]['choices_by_pos'][idx] += 1
                            edges_data_for_viz.append((nominator_key, nominee_key, q_key, idx))
    
    # Preparar la lista final de datos de miembros para el generador de imágenes
    members_data_list_detailed_final = [
        {
            'nombre_completo': name,
            **info,
            **detailed_affinity_scores.get(name, {'total_recibido': 0, 'choices_by_pos': collections.defaultdict(int)})
        } for name, info in member_info_intermediate.items()
    ]
    
    # Llamar a la función de `pdf_generator` para crear la imagen
    try:
        image_buffer = pdf_generator.generate_affinity_diana_image(
            institution_name=institution_name,
            group_name=group_name,
            members_data_list_detailed=members_data_list_detailed_final,
            edges_data=edges_data_for_viz,
            show_lines=show_lines,
            registro_output=None # En la app de escritorio, el log lo maneja la capa superior
        )
        return image_buffer.getvalue() if image_buffer else None
    except Exception as e:
        print(f"Error al generar la imagen de la Diana de Afinidad: {e}")
        traceback.print_exc()
        return None

print("handlers_groups.py refactorizado y listo para su uso en la aplicación de escritorio.")