# handlers_sociogram.py
# (v2.1 - Refactorizado para aplicación de escritorio.
#  Usa "Institución"/"Grupo" y "Miembro". Lógica centralizada en una función.)

import traceback
from sociogram_utils import get_participant_options, get_relation_options
# Se asume que sociogram_engine y pdf_generator serán importados en el módulo principal
import sociogram_engine
import pdf_generator

# --- Funciones Lógicas del Sociograma ---

def prepare_and_draw_sociogram(app_state, ui_values, layout_to_use, app_data_ref, handlers_utils_ref):
    """
    Función principal que recolecta todas las opciones de la UI,
    prepara el entorno y llama al motor de dibujo del sociograma.
    
    Args:
        app_state (dict): El estado actual de la aplicación.
        ui_values (dict): Un diccionario con los valores de los widgets de la UI del sociograma.
        layout_to_use (str): El nombre del layout a usar ('cose', 'circle', etc.).
        app_data_ref: Referencia al módulo de datos (sociograma_data).
        handlers_utils_ref: Referencia al módulo de utilidades (handlers_utils).

    Returns:
        Una tupla (figure, legend_html, graph_json):
        - figure: Un objeto Figure de Matplotlib con el grafo dibujado (o None).
        - legend_html: Una cadena HTML para la leyenda (o None).
        - graph_json: El JSON del grafo para posible uso futuro (o None).
    """
    context = app_state.get('current_group_viewing_members')
    if not context or not context.get('school') or not context.get('class_name'):
        print("Error en prepare_and_draw_sociogram: Falta contexto de institución/grupo.")
        return None, "Error: Contexto no disponible.", None

    institution_name = context['school']
    group_name = context['class_name']

    # Recolectar valores de los controles de la UI desde el diccionario `ui_values`
    selected_data_keys = ui_values.get('-SOC_RELATIONS_VALUES-', []) # La GUI debe proveer esto
    
    # En la implementación de la GUI, en lugar de pasar los widgets, pasaremos sus valores.
    # Por ahora, simulamos la recolección de valores.
    node_gender_filter = ui_values.get('-SOC_GENDER_FILTER-', 'Todos')
    label_display_mode = ui_values.get('-SOC_LABEL_MODE-', 'nombre_apellido')
    connection_gender_type = ui_values.get('-SOC_CONNECTION_GENDER-', 'todas')
    active_members_filter = ui_values.get('-SOC_ACTIVE_ONLY-', False)
    nominators_option = ui_values.get('-SOC_SHOW_ISOLATES-', True)
    received_color_filter = ui_values.get('-SOC_RECEIVED_COLOR-', False)
    reciprocal_nodes_color_filter = ui_values.get('-SOC_RECIPROCAL_COLOR-', False)
    style_reciprocal_links = ui_values.get('-SOC_RECIPROCAL_STYLE-', True)
    selected_participant_focus = ui_values.get('-SOC_PARTICIPANT_FOCUS-', None)
    connection_focus_mode = ui_values.get('-SOC_CONNECTION_FOCUS_MODE-', 'all')
    highlight_mode = ui_values.get('-SOC_HIGHLIGHT_MODE-', 'none')
    highlight_value = ui_values.get('-SOC_HIGHLIGHT_VALUE-', 1)

    try:
        # **NOTA IMPORTANTE:** `sociogram_engine.draw_sociogramma` también necesita ser refactorizado.
        # Asumiremos que ahora devuelve una figura de matplotlib en lugar de un widget.
        
        # Esta llamada ahora se hará desde la clase de la GUI.
        # Esta función se convierte en un placeholder o se elimina.
        # Por ahora, mantenemos la lógica conceptual.
        
        # La función del engine ahora no interactúa con la UI, solo dibuja y devuelve.
        # Por lo tanto, no le pasamos ui_sociogramma_dict_ref.
        fig, legend_info, graph_json = sociogram_engine.draw_sociogramma(
            school_name=institution_name,
            class_name=group_name,
            app_data_ref=app_data_ref,
            node_gender_filter=node_gender_filter,
            label_display_mode=label_display_mode,
            selected_data_keys_from_checkboxes=selected_data_keys,
            connection_gender_type=connection_gender_type,
            active_members_filter=active_members_filter,
            nominators_option=nominators_option,
            received_color_filter=received_color_filter,
            reciprocal_nodes_color_filter=reciprocal_nodes_color_filter,
            style_reciprocal_links=style_reciprocal_links,
            selected_participant_focus=selected_participant_focus,
            connection_focus_mode=connection_focus_mode,
            layout_to_use=layout_to_use,
            highlight_mode=highlight_mode,
            highlight_value=highlight_value,
            # Parámetros que ya no son necesarios porque la UI se maneja fuera:
            # ui_sociogramma_dict_ref=None,
            # registro_output=None
        )
        
        # Generar leyenda HTML a partir de `legend_info`
        legend_html = _create_legend_html(legend_info)

        return fig, legend_html, graph_json

    except Exception as e:
        print(f"Error crítico al preparar o dibujar el sociograma: {e}")
        traceback.print_exc()
        return None, f"Error: {e}", None

def handle_export_sociogram_pdf(graph_json, legend_info, institution_name, group_name, layout_hint, style_reciprocal_links):
    """
    Llama al generador de PDF para el sociograma.
    Devuelve (éxito, mensaje).
    """
    if not graph_json or not legend_info:
        return False, "No hay datos del grafo o leyenda para generar el PDF."
        
    try:
        # De nuevo, la función de pdf_generator se encargará de la lógica de guardado/descarga.
        pdf_generator.generate_pdf_from_cytoscape_json(
            graph_json,
            legend_info,
            institution_name,
            group_name,
            registro_output=None, # El log lo maneja la GUI
            layout_hint=layout_hint,
            style_reciprocal_links_active_param=style_reciprocal_links
        )
        return True, "Generación de PDF del sociograma iniciada."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error al generar el PDF del sociograma: {e}"

def _create_legend_html(legend_info):
    """
    Función auxiliar para generar una cadena HTML a partir de los datos de la leyenda.
    """
    if not legend_info:
        return "<p><i>Leyenda no disponible.</i></p>"
    
    html = "<h4>Leyenda:</h4>"
    # Lógica para construir el HTML de la leyenda a partir del diccionario legend_info...
    # (Esta parte puede ser tan simple o compleja como necesites)
    
    # Ejemplo simple:
    if "node_colors" in legend_info:
        html += "<b>Nodos:</b><ul>"
        for color, desc in legend_info["node_colors"].items():
            html += f"<li><span style='color:{color};'>■</span> {desc}</li>"
        html += "</ul>"
    
    if "edge_styles" in legend_info:
        html += "<b>Flechas:</b><ul>"
        for desc, style in legend_info["edge_styles"].items():
            html += f"<li><span style='color:{style.get('color', 'black')};'>→</span> {desc}</li>"
        html += "</ul>"

    return html

print("handlers_sociogram.py refactorizado y listo para su uso en la aplicación de escritorio.")