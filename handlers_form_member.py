# handlers_form_member.py
# (v10.1 - Refactorizado para aplicación de escritorio.
#  Usa "miembro", "sexo", "Institución"/"Grupo". Funciones devuelven tuplas (éxito, mensaje).)

import collections
import traceback
from sociograma_data import members_data, questionnaire_responses_data

# --- Funciones Lógicas del Formulario de Miembro ---

def _validate_member_data(institution_name, group_name, member_data, is_new, original_name_key=None):
    """
    Función interna para validar los datos de un miembro antes de guardarlos.
    Devuelve (es_valido, mensaje_error).
    """
    errors = []
    cognome = member_data.get('cognome', '').strip()
    nome = member_data.get('nome', '').strip()
    iniz = member_data.get('iniz', '').strip()
    sexo = member_data.get('sexo', 'Desconocido')

    if not cognome:
        errors.append("El apellido es obligatorio.")
    if not nome:
        errors.append("El nombre es obligatorio.")
    if not iniz or len(iniz) < 3 or len(iniz) > 4 or not iniz.isalpha():
        errors.append("Las iniciales deben ser 3 o 4 letras (ej. MRG o MRGL).")
    if sexo not in ['Masculino', 'Femenino', 'Desconocido']:
        errors.append(f"El valor para Sexo ('{sexo}') no es válido.")

    # Validar unicidad del nombre completo en el grupo
    if nome and cognome:
        full_name_check = f"{nome.title()} {cognome.title()}".strip()
        existing_members = members_data.get(institution_name, {}).get(group_name, [])
        
        is_duplicate = False
        if is_new:
            if any(f"{m.get('nome','').title()} {m.get('cognome','').title()}".strip().lower() == full_name_check.lower() for m in existing_members):
                is_duplicate = True
        else: # Modificando
            if full_name_check.lower() != original_name_key.lower():
                if any(f"{m.get('nome','').title()} {m.get('cognome','').title()}".strip().lower() == full_name_check.lower() for m in existing_members):
                    is_duplicate = True
        
        if is_duplicate:
            errors.append(f"Ya existe un miembro llamado '{full_name_check}' en este grupo.")

    if errors:
        return False, "\n".join(errors)
    
    return True, "Validación exitosa."


def handle_add_member(institution_name, group_name, new_member_data):
    """
    Lógica para añadir un nuevo miembro a un grupo.
    new_member_data es un diccionario con los campos del miembro.
    Devuelve (éxito, mensaje).
    """
    is_valid, msg = _validate_member_data(institution_name, group_name, new_member_data, is_new=True)
    if not is_valid:
        return False, msg

    try:
        # Asegurar capitalización correcta
        new_member_data['cognome'] = new_member_data.get('cognome', '').strip().upper()
        new_member_data['nome'] = new_member_data.get('nome', '').strip().title()
        new_member_data['iniz'] = new_member_data.get('iniz', '').strip().upper()

        members_data.setdefault(institution_name, {}).setdefault(group_name, []).append(new_member_data)
        
        full_name = f"{new_member_data['nome']} {new_member_data.get('cognome','').title()}"
        return True, f"Miembro '{full_name}' añadido correctamente."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al añadir miembro: {e}"


def handle_modify_member(institution_name, group_name, original_name_key, original_data_dict, updated_member_data):
    """
    Lógica para modificar un miembro existente.
    original_name_key es el nombre completo original para buscarlo.
    original_data_dict es el diccionario original del miembro.
    updated_member_data es un diccionario con los nuevos datos.
    Devuelve (éxito, mensaje).
    """
    is_valid, msg = _validate_member_data(institution_name, group_name, updated_member_data, is_new=False, original_name_key=original_name_key)
    if not is_valid:
        return False, msg
        
    try:
        # Asegurar capitalización correcta
        updated_member_data['cognome'] = updated_member_data.get('cognome', '').strip().upper()
        updated_member_data['nome'] = updated_member_data.get('nome', '').strip().title()
        updated_member_data['iniz'] = updated_member_data.get('iniz', '').strip().upper()

        group_members = members_data.get(institution_name, {}).get(group_name)
        if group_members is None:
            return False, "El grupo especificado no fue encontrado."

        # Buscar el miembro por sus datos originales para evitar problemas si el nombre cambió
        original_cognome_search = original_data_dict.get('cognome', '').upper()
        original_nome_search = original_data_dict.get('nome', '').title()

        member_found_and_updated = False
        for i, member_dict in enumerate(group_members):
            if member_dict.get('cognome','').upper() == original_cognome_search and \
               member_dict.get('nome','').title() == original_nome_search:
                
                # Actualizar el diccionario del miembro en la lista
                group_members[i].update(updated_member_data)
                member_found_and_updated = True
                
                # Si el nombre cambió, hay que migrar la clave de sus respuestas
                new_name_key = f"{updated_member_data['nome']} {updated_member_data.get('cognome','').title()}"
                if new_name_key.lower() != original_name_key.lower():
                    old_resp_key = (institution_name, group_name, original_name_key)
                    if old_resp_key in questionnaire_responses_data:
                        responses = questionnaire_responses_data.pop(old_resp_key)
                        new_resp_key = (institution_name, group_name, new_name_key)
                        questionnaire_responses_data[new_resp_key] = responses
                break

        if not member_found_and_updated:
            return False, f"No se encontró al miembro original '{original_name_key}' para modificar."

        return True, "Miembro actualizado correctamente."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error inesperado al modificar miembro: {e}"


print("handlers_form_member.py refactorizado y listo para su uso en la aplicación de escritorio.")