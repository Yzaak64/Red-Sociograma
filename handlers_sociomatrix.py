# handlers_sociomatrix.py (v2.1 - Corregido y robustecido)
import os
import webbrowser
import collections
from sociograma_data import members_data, get_class_question_definitions, questionnaire_responses_data, cognitive_social_structures_data
from handlers_utils import normalizar_nombre_para_comparacion

def log_matrix(message):
    """Función de logging para la consola."""
    print(f"[MATRIX_HANDLER_LOG] {message}")

def handle_draw_sociomatrix_data(institution_name, group_name, selected_data_keys_list, 
                                 aggregation_mode=None,
                                 perceiver_name=None,
                                 allow_self_on_diagonal=False,
                                 network_data_override=None):
    """
    Versión final, definitiva y robusta.
    - Corrige el bug que ignoraba los datos de `network_data_override`.
    """
    log_matrix(f"--- Iniciando handle_draw_sociomatrix_data (v2.2 - CORREGIDO) ---")
    
    members_list_raw = members_data.get(institution_name, {}).get(group_name, [])
    if not members_list_raw:
        return {'success': False, 'message': f"No hay miembros en el grupo '{group_name}'."}

    member_info_list = sorted([
        {
            'full_name': f"{m.get('nome', '').strip().title()} {m.get('cognome', '').strip().upper().title()}",
            'display_name': f"{m.get('cognome', '').strip().upper()}, {m.get('nome', '').strip().title()}",
            'iniz': m.get('iniz', 'N/A').upper(),
            'sexo': m.get('sexo', '').lower()
        } for m in members_list_raw
    ], key=lambda x: x['display_name'])
    
    fullname_to_index_map = {mem['full_name']: i for i, mem in enumerate(member_info_list)}
    norm_to_fullname_map = { normalizar_nombre_para_comparacion(mem['full_name']): mem['full_name'] for mem in member_info_list }
    
    source_responses = network_data_override if network_data_override is not None else questionnaire_responses_data
    election_matrix = collections.defaultdict(lambda: collections.defaultdict(int))
    
    for (resp_inst, resp_grp, nominator_orig), member_responses in source_responses.items():
        if resp_inst == institution_name and resp_grp == group_name:
            nominator_fullname = norm_to_fullname_map.get(normalizar_nombre_para_comparacion(nominator_orig))
            if not nominator_fullname: continue

            for question_key, nominees in member_responses.items():
                # --- INICIO DE LA CORRECCIÓN ---
                # Si estamos usando datos estándar (NO override), filtramos por las preguntas seleccionadas.
                # Si SÍ estamos usando un override, asumimos que ya viene filtrado y procesamos todas sus claves.
                if network_data_override is None:
                    if question_key not in selected_data_keys_list:
                        continue
                # --- FIN DE LA CORRECCIÓN ---

                for nominee_orig in nominees:
                    nominee_fullname = norm_to_fullname_map.get(normalizar_nombre_para_comparacion(nominee_orig))
                    if nominee_fullname:
                        election_matrix[nominator_fullname][nominee_fullname] += 1

    header_for_table = ['Nominador'] + [mem['iniz'] for mem in member_info_list] + ['TOTAL Hechas']
    data_for_table = []
    grand_column_totals = collections.defaultdict(int)

    female_members_info = [m for m in member_info_list if m['sexo'] == 'femenino']
    male_members_info = [m for m in member_info_list if m['sexo'] != 'femenino']

    def _process_gender_group(members_info, group_name):
        rows = []
        if not members_info: return rows
        
        rows.append([f'---{group_name}---'] + [''] * (len(header_for_table) - 1))
        
        column_subtotals = collections.defaultdict(int)
        total_hechas_subtotal = 0

        for member_info in members_info:
            data_cells = []
            row_total_made = 0
            nominator_index = fullname_to_index_map.get(member_info['full_name'])

            for j, nominee_info in enumerate(member_info_list):
                count = election_matrix[member_info['full_name']].get(nominee_info['full_name'], 0)
                
                is_diagonal = (j == nominator_index)
                if is_diagonal:
                    # Si la opción de auto-selección está activada...
                    if allow_self_on_diagonal:
                        # ...muestra el conteo (o una celda vacía si es cero).
                        cell_value = str(count) if count > 0 else ''
                    else:
                        # Si no está activada, muestra la 'X' tradicional.
                        cell_value = 'X'
                else:
                    # El comportamiento para las celdas no diagonales no cambia.
                    cell_value = str(count) if count > 0 else ''
                
                data_cells.append(cell_value)
                
                if not is_diagonal:
                    row_total_made += count
                    column_subtotals[nominee_info['full_name']] += count
                    grand_column_totals[nominee_info['full_name']] += count
            
            final_row = [member_info['display_name']] + data_cells + [row_total_made]
            rows.append(final_row)
            total_hechas_subtotal += row_total_made
        
        subtotal_row = [f'Total por {group_name} (Hechas)']
        for nominee_info in member_info_list:
            subtotal_row.append(column_subtotals[nominee_info['full_name']])
        subtotal_row.append(total_hechas_subtotal)
        rows.append(subtotal_row)
        return rows

    data_for_table.extend(_process_gender_group(female_members_info, "Femenino"))
    data_for_table.extend(_process_gender_group(male_members_info, "Masculino"))

    total_row = ['TOTAL GENERAL Recibidas']
    total_general = sum(grand_column_totals.values())
    for nominee_info in member_info_list:
        total_row.append(grand_column_totals[nominee_info['full_name']])
    total_row.append(total_general)
    data_for_table.append(total_row)
    
    return { 'success': True, 'header': header_for_table, 'data': data_for_table }

def _generate_html_from_data(header, data):
    """Función auxiliar para crear una tabla HTML simple a partir de datos."""
    html = "<table border='1' style='border-collapse: collapse; font-family: sans-serif; font-size: 10px;'>"
    html += "<thead><tr>"
    for h in header:
        html += f"<th style='padding: 4px; background-color: #e0e0e0;'>{h}</th>"
    html += "</tr></thead>"
    html += "<tbody>"
    for row in data:
        html += "<tr>"
        for i, cell in enumerate(row):
            style = "padding: 4px; text-align: center;"
            if i == 0:
                style += " text-align: left; background-color: #f2f2f2; font-weight: bold;"
            if "Total" in str(cell):
                 style += " background-color: #e9e9e9; font-weight: bold;"
            html += f"<td style='{style}'>{cell}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

def generate_html_for_matrix(header, data, cell_color_map=None, legend_html=None):
    """
    Convierte los datos de la matriz en una tabla HTML bien formateada y con estilos.
    Acepta un mapa de colores para las celdas y un bloque HTML para la leyenda.
    """
    # Estilos CSS para que la tabla se vea profesional y sea fácil de usar.
    styles = """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 20px; background-color: #fdfdfd; }
        h2, h3 { color: #333; }
        .matrix-container { overflow-x: auto; border: 1px solid #ddd; }
        table { border-collapse: collapse; width: auto; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); white-space: nowrap; }
        th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: center; }
        
        /* Encabezado fijo al hacer scroll vertical */
        thead th { background-color: #e9ecef; font-weight: bold; position: sticky; top: 0; z-index: 10; }
        
        /* Primera columna (Nominador) fija al hacer scroll horizontal */
        td.nominador { text-align: left; font-weight: bold; background-color: #f8f9fa; position: sticky; left: 0; z-index: 5; }
        
        /* La esquina superior izquierda debe estar por encima de todo */
        thead th:first-child { position: sticky; left: 0; z-index: 15; }

        /* Estilos para filas especiales */
        tr.gender-header td { background-color: #dce6f2; font-weight: bold; text-align: left; }
        tr.total-row td { background-color: #f0f0f0; font-weight: bold; }

        /* Estilos para la leyenda */
        .legend { border: 1px solid #ccc; padding: 15px; margin-top: 20px; margin-bottom: 30px; background-color: #f9f9f9; max-width: 650px; border-radius: 5px;}
        .legend h4 { margin-top: 0; }
        .legend-item { display: inline-block; margin: 2px 10px 2px 0; }
        .legend-color-box { width: 15px; height: 15px; display: inline-block; vertical-align: middle; margin-right: 5px; border: 1px solid #777; }
    </style>
    """
    
    html = f"<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'><title>Matriz Sociométrica</title>{styles}</head><body>"
    
    # Insertar la leyenda si se proporcionó
    if legend_html:
        html += legend_html
    
    html += "<h2>Matriz Sociométrica</h2>"
    
    # Contenedor para permitir el scroll horizontal en tablas anchas
    html += "<div class='matrix-container'><table>"
    
    # Construir el encabezado de la tabla
    html += "<thead><tr>"
    for i, h in enumerate(header):
        html += f"<th>{h}</th>"
    html += "</tr></thead>"
    
    # Construir el cuerpo de la tabla
    html += "<tbody>"
    for row_data in data:
        row_class = ""
        first_cell_val = str(row_data[0])
        
        # Detectar y formatear filas de encabezado de género
        if '---' in first_cell_val:
            row_class = "gender-header"
            clean_text = first_cell_val.replace("---", "")
            html += f'<tr class="{row_class}"><td colspan="{len(header)}">{clean_text}</td></tr>'
            continue # Saltar al siguiente ciclo de la fila
        # Detectar y formatear filas de totales
        elif 'Total' in first_cell_val:
            row_class = "total-row"

        html += f'<tr class="{row_class}">'
        for i, cell in enumerate(row_data):
            cell_class = "nominador" if i == 0 else ""
            
            # Aplicar color de fondo si se proporciona un mapa de colores y el valor coincide
            bg_color_style = ""
            if cell_color_map and str(cell) in cell_color_map:
                bg_color_style = f"background-color: {cell_color_map[str(cell)]};"

            html += f'<td class="{cell_class}" style="{bg_color_style}">{cell}</td>'
        html += "</tr>"

    html += "</tbody></table></div></body></html>"
    return html

print("handlers_sociomatrix.py refactorizado y listo para su uso en la aplicación de escritorio.")