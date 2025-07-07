# handlers_utils.py
# (v1.7 - Versión final para aplicación de escritorio.
#  Incluye función de normalización de nombres y la aplica para
#  hacer la obtención de opciones más robusta.)

import re
import unicodedata

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
    Obtiene una lista de tuplas (display_label, value) para poblar un
    desplegable de selección de miembros. Es la función centralizada para
    obtener listas de miembros.

    Args:
        school_name (str): Nombre de la institución.
        class_name (str): Nombre del grupo.
        app_data_ref: Referencia al módulo de datos (sociograma_data).
        order_by (str): 'Apellido' o 'Nombre' para el ordenamiento.
        exclude_member_display_name (str, optional): Nombre completo del miembro a excluir.
        include_all_option (bool): Si es True, añade ("Todos (Grafo Completo)", None) al
                                    principio. Si es False, añade ("Seleccionar", None).

    Returns:
        list: Una lista de tuplas para las opciones del desplegable.
    """
    if not app_data_ref or not hasattr(app_data_ref, 'members_data'):
        print("ERROR en get_member_options: app_data_ref no es válido.")
        return [('Error: Datos no disponibles', None)]

    options = []
    if include_all_option:
        # Para el filtro del sociograma, 'None' sigue siendo correcto.
        options.append(('Todos (Grafo Completo)', None))
    else:
        # Para el cuestionario, hacemos que "Seleccionar" sea una opción real.
        # El valor interno será un string vacío '' para representar "sin elección".
        options.append(('Seleccionar', ''))

    local_members_data = app_data_ref.members_data
    members_list_all = local_members_data.get(school_name, {}).get(class_name, [])
    if not members_list_all:
        # Devuelve la opción por defecto ("Todos" o "Seleccionar") si no hay miembros
        return options

    members_to_process = list(members_list_all)

    if exclude_member_display_name:
        normalized_exclude_name = normalizar_nombre_para_comparacion(exclude_member_display_name)
        members_to_process = [
            m for m in members_to_process
            if normalizar_nombre_para_comparacion(f"{m.get('nome', '')} {m.get('cognome', '')}") != normalized_exclude_name
        ]

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
        internal_value = display_label  # El valor y el texto son los mismos para PySimpleGUI

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
        
    # Ordenar la lista aquí para asegurar consistencia
    # Ordenamos por Nombre, Apellido
    sorted_list = sorted(lista_miembros, key=lambda m: (str(m.get('nome','')).strip().title(), str(m.get('cognome','')).strip().title()))

    options = []
    for m in sorted_list:
        nome = m.get('nome', '').strip().title()
        cognome = m.get('cognome', '').strip().title()
        display_text = f"{nome} {cognome}".strip()
        if display_text:
            options.append(display_text)
    return options


print("handlers_utils.py refactorizado y listo para su uso en la aplicación de escritorio.")