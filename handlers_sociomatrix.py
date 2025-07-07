# handlers_sociomatrix.py
# (v27.1 - Refactorizado para aplicación de escritorio.
#  Usa "Institución"/"Grupo", "sexo" y "miembro".
#  La función principal devuelve datos de tabla en lugar de HTML.)

import collections
from sociograma_data import members_data, get_class_question_definitions, questionnaire_responses_data
from handlers_utils import normalizar_nombre_para_comparacion

def log_matrix(message):
    """Función de logging para la consola."""
    print(f"[MATRIX_HANDLER_LOG] {message}")

def handle_draw_sociomatrix_data(institution_name, group_name, selected_data_keys_list):
    """
    Versión final que respeta estrictamente el orden de los miembros tal como
    aparecen en sociograma_data.py tanto para las filas como para las columnas.
    """
    log_matrix("--- Iniciando handle_draw_sociomatrix_data (v. respetando orden original de datos) ---")
    
    members_list_raw = members_data.get(institution_name, {}).get(group_name, [])
    if not members_list_raw:
        return {'success': False, 'message': f"No hay miembros en el grupo '{group_name}'."}
    
    log_matrix(f"Encontrados {len(members_list_raw)} miembros. Se usará el orden original de la lista de datos.")

    # 1. USAR LA LISTA ORIGINAL SIN NINGÚN TIPO DE ORDENAMIENTO
    # Esta lista determinará el orden de las FILAS Y de las COLUMNAS.
    all_members_in_original_order = members_list_raw
    
    # El mapa de normalización sigue siendo necesario para emparejar nombres de forma robusta
    members_map = {
        normalizar_nombre_para_comparacion(f"{m.get('nome', '').title()} {m.get('cognome', '').title()}"): 
        f"{m.get('nome', '').title()} {m.get('cognome', '').title()}" 
        for m in all_members_in_original_order
    }
    
    # Crear las listas para las columnas y las claves A PARTIR de la lista original
    member_initials_for_cols = [m.get('iniz','N/A').upper() for m in all_members_in_original_order]
    member_fullnames_for_key = [f"{m.get('nome','').strip().title()} {m.get('cognome','').strip().title()}" for m in all_members_in_original_order]
    header_for_table = ['Nominador'] + member_initials_for_cols + ['TOTAL Hechas']
    log_matrix(f"Cabecera generada respetando el orden de datos: {header_for_table}")
    
    # 2. Calcular la matriz de elecciones usando normalización
    election_matrix = collections.defaultdict(lambda: collections.defaultdict(int))
    for (resp_inst, resp_grp, nominator_orig), member_responses in questionnaire_responses_data.items():
        if resp_inst == institution_name and resp_grp == group_name:
            nominator_norm = normalizar_nombre_para_comparacion(nominator_orig)
            nominator_key_final = members_map.get(nominator_norm)
            
            if not nominator_key_final:
                log_matrix(f"AVISO (Cálculo Matriz): Nominador '{nominator_orig}' no encontrado en el mapa. Se omite.")
                continue

            for question_key in selected_data_keys_list:
                if question_key in member_responses:
                    for nominee_orig in member_responses[question_key]:
                        nominee_norm = normalizar_nombre_para_comparacion(nominee_orig)
                        nominee_key_final = members_map.get(nominee_norm)
                        if nominee_key_final:
                            election_matrix[nominator_key_final][nominee_key_final] += 1
                        else:
                            log_matrix(f"AVISO (Cálculo Matriz): Nominado '{nominee_orig}' no encontrado en el mapa.")
    
    # 3. Construir la tabla usando el orden original para todo
    data_for_table = []
    row_colors_for_gui = []
    grand_column_totals = [0] * len(all_members_in_original_order)
    
    femenino_members = [m for m in all_members_in_original_order if m.get('sexo', '').lower() == 'femenino']
    masculino_members = [m for m in all_members_in_original_order if m.get('sexo', '').lower() == 'masculino']
    other_members = [m for m in all_members_in_original_order if m.get('sexo', '').lower() not in ['femenino', 'masculino']]
    
    groups_by_gender_ordered = [('Femenino', femenino_members), ('Masculino', masculino_members), ('Otro/Desconocido', other_members)]
    
    current_row_index = 0
    for gender_name, members_in_group in groups_by_gender_ordered:
        if members_in_group:
            row_colors_for_gui.append((current_row_index, '#E6F2FF'))
            data_for_table.append([f"--- {gender_name} ---"] + [''] * (len(header_for_table) - 1))
            current_row_index += 1

            group_column_totals = [0] * len(all_members_in_original_order)
            group_total_made_by_gender = 0
            
            for nominator_data in members_in_group:
                nominator_key = f"{nominator_data.get('nome','').strip().title()} {nominator_data.get('cognome','').strip().title()}"
                display_name = f"{nominator_data.get('cognome','').strip().title()}, {nominator_data.get('nome','').strip().title()}"
                row_data = [display_name]
                row_total_made_by_member = 0
                
                for i, nominee_key in enumerate(member_fullnames_for_key):
                    if nominator_key == nominee_key:
                        row_data.append('X')
                    else:
                        count = election_matrix[nominator_key].get(nominee_key, 0)
                        row_data.append(str(count) if count > 0 else '')
                        row_total_made_by_member += count
                        group_column_totals[i] += count
                        grand_column_totals[i] += count
                
                row_data.append(row_total_made_by_member)
                data_for_table.append(row_data)
                current_row_index += 1
                group_total_made_by_gender += row_total_made_by_member

            row_colors_for_gui.append((current_row_index, '#F0F0F0'))
            data_for_table.append([f"Total por {gender_name} (Hechas)"] + group_column_totals + [group_total_made_by_gender])
            log_matrix(f"Subtotales para {gender_name}: Columnas={group_column_totals}, Total Hechas={group_total_made_by_gender}")
            current_row_index += 1

    grand_total_selections = sum(grand_column_totals)
    row_colors_for_gui.append((current_row_index, '#E0E0E0'))
    data_for_table.append(['TOTAL GENERAL Recibidas'] + grand_column_totals + [grand_total_selections])
    log_matrix(f"Totales Generales: Columnas={grand_column_totals}, Total Final={grand_total_selections}")
    
    html_output = _generate_html_from_data(header_for_table, data_for_table)

    return {
        'success': True,
        'header': header_for_table,
        'data': data_for_table,
        'row_colors': row_colors_for_gui,
        'html': html_output,
        'message': "Datos generados."
    }

def _generate_html_from_data(header, data):
    """Función auxiliar para crear una tabla HTML simple a partir de datos."""
    html = "<table border='1' style='border-collapse: collapse; font-family: sans-serif; font-size: 10px;'>"
    # Header
    html += "<thead><tr>"
    for h in header:
        html += f"<th style='padding: 4px; background-color: #e0e0e0;'>{h}</th>"
    html += "</tr></thead>"
    # Body
    html += "<tbody>"
    for row in data:
        html += "<tr>"
        for i, cell in enumerate(row):
            style = "padding: 4px; text-align: center;"
            if i == 0:
                style += " text-align: left; background-color: #f2f2f2; font-weight: bold;"
            if "---" in str(cell):
                html += f"<td colspan='{len(header)}' style='background-color: #cce5ff; font-weight: bold; padding: 5px;'>{cell.replace('---', '').strip()}</td>"
                break 
            if "Total" in str(cell):
                 style += " background-color: #e9e9e9; font-weight: bold;"

            html += f"<td style='{style}'>{cell}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

# Las funciones on_sociomatrix_..._click que manejaban los checkboxes son eliminadas.
# La GUI se encargará de gestionar el estado de los checkboxes y pasar la lista
# de data_keys seleccionados a `handle_draw_sociomatrix_data`.

print("handlers_sociomatrix.py refactorizado y listo para su uso en la aplicación de escritorio.")