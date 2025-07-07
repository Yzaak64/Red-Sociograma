# handlers_institutions.py
# (v17.2 - Refactorizado para aplicación de escritorio.
#  Usa "Institución" y "Miembro". Funciones devuelven tuplas (éxito, mensaje).)

import collections
import traceback
from sociograma_data import (
    schools_data,
    classes_data,
    members_data,
    question_definitions,
    questionnaire_responses_data
)

# Nota: Las funciones de la GUI (on_main_..._button_handler) se eliminan.
# Su lógica de interacción se moverá a la clase principal de la aplicación.
# Las funciones de los formularios empotrados (on_form_...) también se
# refactorizan en funciones de lógica pura.

# --- Funciones Lógicas de Gestión de Instituciones ---

def handle_add_institution(name, annotations):
    """
    Lógica para añadir una nueva institución.
    Devuelve una tupla (éxito, mensaje).
    """
    if not name:
        return False, "El nombre de la institución no puede estar vacío."
    if name in schools_data:
        return False, f"La institución '{name}' ya existe."
    
    try:
        schools_data[name] = annotations
        # Inicializar las demás estructuras de datos para esta nueva institución
        classes_data.setdefault(name, [])
        members_data.setdefault(name, collections.OrderedDict())
        
        return True, f"Institución '{name}' añadida correctamente."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al añadir la institución: {e}"

def handle_modify_institution(original_name, new_name, new_annotations):
    """
    Lógica para modificar una institución existente.
    Devuelve una tupla (éxito, mensaje).
    """
    if not new_name:
        return False, "El nuevo nombre de la institución no puede estar vacío."
    if original_name not in schools_data:
        return False, f"La institución original '{original_name}' no fue encontrada."
    if new_name != original_name and new_name in schools_data:
        return False, f"Ya existe una institución con el nuevo nombre '{new_name}'."
        
    try:
        name_changed = (new_name != original_name)
        
        # Primero, actualizamos la anotación. Si el nombre no cambia, es todo lo que hacemos.
        # Si el nombre cambia, guardamos la nueva anotación en la nueva clave.
        if not name_changed:
            schools_data[original_name] = new_annotations
        else:
            # Si el nombre cambia, debemos migrar todos los datos
            # 1. Mover la entrada en schools_data
            schools_data[new_name] = new_annotations
            del schools_data[original_name]
            
            # 2. Mover datos en classes_data
            if original_name in classes_data:
                classes_data[new_name] = classes_data.pop(original_name)
            
            # 3. Mover datos en members_data
            if original_name in members_data:
                members_data[new_name] = members_data.pop(original_name)

            # 4. Migrar claves en question_definitions y questionnaire_responses_data
            for data_dict in [question_definitions, questionnaire_responses_data]:
                keys_to_migrate = [k for k in data_dict if k[0] == original_name]
                for old_key in keys_to_migrate:
                    new_key = (new_name,) + old_key[1:]
                    data_dict[new_key] = data_dict.pop(old_key)

        return True, f"Institución '{original_name}' actualizada correctamente a '{new_name}'."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al modificar la institución: {e}"

def handle_delete_institution(name_to_delete):
    """
    Lógica para eliminar una institución y todos sus datos asociados.
    Devuelve una tupla (éxito, mensaje).
    """
    if name_to_delete not in schools_data:
        return False, f"La institución '{name_to_delete}' no fue encontrada."
        
    try:
        # Eliminar de todas las estructuras de datos principales
        if name_to_delete in schools_data: del schools_data[name_to_delete]
        if name_to_delete in classes_data: del classes_data[name_to_delete]
        if name_to_delete in members_data: del members_data[name_to_delete]

        # Eliminar de diccionarios con claves compuestas
        for data_dict in [question_definitions, questionnaire_responses_data]:
            keys_to_delete = [k for k in data_dict if k[0] == name_to_delete]
            for key in keys_to_delete:
                del data_dict[key]
        
        return True, f"Institución '{name_to_delete}' y todos sus datos asociados han sido eliminados."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al eliminar la institución: {e}"

print("handlers_institutions.py refactorizado y listo para su uso en la aplicación de escritorio.")