# sociogram_engine.py
# (v10.3 - Versión final: Leyenda en banda superior y grosor de aristas)

import networkx as nx
import json
import base64
import collections

# Dependencias
import pdf_generator
from handlers_utils import normalizar_nombre_para_comparacion

def log_engine(message):
    """Función de logging simple para este motor."""
    print(f"[SOCIOGRAM_ENGINE_v10.3] {message}")


def generate_interactive_html(
    school_name, class_name,
    app_data_ref, 
    selected_data_keys,
    # --- Parámetros completos ---
    node_gender_filter='Todos',
    label_display_mode='nombre_apellido',
    connection_gender_type='todas',
    active_members_filter=False,
    nominators_option=True,
    received_color_filter=False,
    reciprocal_nodes_color_filter=False,
    style_reciprocal_links=False,
    selected_participant_focus=None,
    connection_focus_mode='all',
    layout_to_use='cose',
    highlight_mode='none',
    highlight_value=1
):
    """
    Versión final que muestra la leyenda en una banda superior fija, añade
    grosor dinámico a las aristas y asegura una impresión perfecta.
    """
    log_engine(f"Iniciando generación de sociograma para '{school_name}/{class_name}'")

    # ========================================================================
    # LÓGICA DE CÁLCULO Y CONSTRUCCIÓN DEL GRAFO
    # ========================================================================
    members_list_for_class_base = app_data_ref.members_data.get(school_name, {}).get(class_name, [])
    if not members_list_for_class_base: return None
    member_details_map = { f"{m.get('nome','').strip().title()} {m.get('cognome','').strip().title()}": m for m in members_list_for_class_base }
    G_base = nx.MultiDiGraph()
    for node_id, member_data in member_details_map.items():
        if node_gender_filter == 'Todos' or member_data.get('sexo') == node_gender_filter:
            G_base.add_node( node_id, id=node_id, sexo_attr=member_data.get('sexo', 'Desconocido'), iniz=member_data.get('iniz', 'N/A'), original_nome=member_data.get('nome','').strip(), original_cognome=member_data.get('cognome','').strip())
    if not G_base.nodes(): return None
    G_with_edges_full = G_base.copy()
    class_questions = app_data_ref.get_class_question_definitions(school_name, class_name)
    if selected_data_keys:
        for nominator_name in list(G_with_edges_full.nodes()):
            responses = app_data_ref.questionnaire_responses_data.get((school_name, class_name, nominator_name), {})
            for q_key, nominees in responses.items():
                if q_key not in selected_data_keys: continue
                q_def = next((d for d in class_questions.values() if d.get('data_key') == q_key), {})
                for idx, nominee_name in enumerate(nominees):
                    if G_with_edges_full.has_node(nominee_name):
                         G_with_edges_full.add_edge(nominator_name, nominee_name, relation_data_key=q_key, election_index=idx, polarity=q_def.get('polarity', 'neutral'))
    
    G = G_with_edges_full.copy()
    if not nominators_option: G.remove_nodes_from(list(nx.isolates(G)))

    # ========================================================================
    # APLICACIÓN DE ESTILOS Y FILTROS
    # ========================================================================
    is_focus_active = bool(selected_participant_focus and selected_participant_focus in G.nodes())
    
    active_focus_nodes = set()
    if is_focus_active:
        active_focus_nodes.add(selected_participant_focus)
        if connection_focus_mode == 'outgoing':
            for u, v in G.out_edges(selected_participant_focus): active_focus_nodes.add(v)
        elif connection_focus_mode == 'incoming':
            for u, v in G.in_edges(selected_participant_focus): active_focus_nodes.add(u)
        else: # 'all'
            for u, v in G.out_edges(selected_participant_focus): active_focus_nodes.add(v)
            for u, v in G.in_edges(selected_participant_focus): active_focus_nodes.add(u)

    for node_name, node_data in G.nodes(data=True):
        sexo = node_data.get('sexo_attr', 'Desconocido')
        node_data['node_shape'] = 'ellipse' if sexo == 'Masculino' else 'triangle' if sexo == 'Femenino' else 'rectangle'
        node_data['node_color'] = 'skyblue' if sexo == 'Masculino' else 'lightcoral' if sexo == 'Femenino' else 'lightgreen'
        node_data['opacity'] = 1.0

        if is_focus_active:
            if node_name not in active_focus_nodes:
                node_data['opacity'] = 0.15
            elif node_name == selected_participant_focus:
                node_data['node_color'] = 'darkorange'
            else:
                node_data['node_color'] = '#FFDB58'
        else:
            reciprocal_nodes = {n for u, v in G.edges() if G.has_edge(v, u) for n in (u, v)}
            if reciprocal_nodes_color_filter and node_name in reciprocal_nodes:
                node_data['node_color'] = 'mediumpurple'
            elif nominators_option and G.degree(node_name) == 0:
                node_data['node_color'] = 'silver'
        
        if label_display_mode == 'iniciales': node_data['label'] = node_data.get('iniz', 'N/A')
        else: node_data['label'] = f"{node_data.get('original_nome','')} {node_data.get('original_cognome','')}"

    width_map = {0: 4.0, 1: 2.5, 2: 1.5}
    active_widths = set()
    edge_color_map = {key: color for key, color in zip(selected_data_keys, ['#007bff','#dc3545','#ffc107','#6c757d','#17a2b8'])}
    for u, v, data in G.edges(data=True):
        data['opacity'] = 1.0
        
        election_index = data.get('election_index', 99)
        edge_width = width_map.get(election_index, 0.8)
        data['edge_width'] = edge_width
        active_widths.add(edge_width)

        is_relevant_edge = True
        if is_focus_active:
            if connection_focus_mode == 'outgoing': is_relevant_edge = (u == selected_participant_focus)
            elif connection_focus_mode == 'incoming': is_relevant_edge = (v == selected_participant_focus)
            elif connection_focus_mode == 'all': is_relevant_edge = (u == selected_participant_focus or v == selected_participant_focus)
        
        if not is_relevant_edge:
            data['opacity'] = 0.1
        
        if is_focus_active and is_relevant_edge:
            is_reciprocal_with_focus = G.has_edge(v, u) and (v == selected_participant_focus or u == selected_participant_focus)
            if u == selected_participant_focus and is_reciprocal_with_focus and connection_focus_mode == 'all':
                data['edge_color'], data['line_style'] = '#FF8C00', 'dotted'
            elif u == selected_participant_focus:
                data['edge_color'], data['line_style'] = '#32CD32', 'dotted'
            elif v == selected_participant_focus:
                data['edge_color'], data['line_style'] = '#1E90FF', 'dotted'
            else:
                data['opacity'] = 0.1
        else:
            q_def = next((d for d in class_questions.values() if d.get('data_key') == data.get('relation_data_key')), {})
            polarity = q_def.get('polarity', 'neutral')
            data['edge_color'] = '#dc3545' if polarity == 'negative' else edge_color_map.get(data.get('relation_data_key'), '#ccc')
            data['line_style'] = 'dashed' if style_reciprocal_links and G.has_edge(v, u) else 'solid'
            
    # ========================================================================
    # GENERACIÓN DE JSON Y HTML
    # ========================================================================
    log_engine("Convirtiendo grafo a formato JSON para Cytoscape.js...")
    elements = []
    active_node_colors, active_edge_colors, is_reciprocal_link_present = set(), set(), False
    for node_id, data in G.nodes(data=True):
        elements.append({ 'data': { **data } })
    for u, v, data in G.edges(data=True):
        elements.append({ 'data': { **data, 'source': u, 'target': v } })
        if data.get('opacity', 1.0) > 0.1: active_edge_colors.add(data.get('edge_color'))
        if data.get('line_style') == 'dashed': is_reciprocal_link_present = True
    elements_json = json.dumps(elements, indent=2)
    
    log_engine("Generando HTML para la leyenda en el encabezado...")
    title_html = f"<div class='header-title'>{school_name} / {class_name}</div>"
    
    legend_items = []
    node_legend_map = {'darkorange': "Foco", '#FFDB58': "Conectado al Foco", 'skyblue': "Masculino",'lightcoral': "Femenino", 'silver': "No Elegido"}
    for color, desc in node_legend_map.items():
        if color in active_node_colors:
            symbol = "●" if "Masculino" in desc else "▲" if "Femenino" in desc else "■"
            legend_items.append(f"<span class='legend-item'><span style='color:{color};'>{symbol}</span> {desc}</span>")

    edge_legend_map = collections.OrderedDict()
    if is_focus_active:
        edge_legend_map['#32CD32'] = ('Saliente', 'dotted'); edge_legend_map['#1E90FF'] = ('Entrante', 'dotted'); edge_legend_map['#FF8C00'] = ('Recíproca Foco', 'dotted')
    else:
        for key in selected_data_keys:
            q_def = next((d for d in class_questions.values() if d.get('data_key') == key), {}); 
            polarity = q_def.get('polarity', 'neutral')
            color = '#dc3545' if polarity == 'negative' else edge_color_map.get(key, '#ccc')
            edge_legend_map[color] = (f"({polarity[:3].title()}) {q_def.get('type', 'Relación')}", 'solid')
    for color, (desc, style) in edge_legend_map.items():
        if color in active_edge_colors:
             legend_items.append(f"<span class='legend-item' style='color:{color};'>→</span> {desc}")
    if is_reciprocal_link_present and not is_focus_active:
        legend_items.append("<span class='legend-item'><span style='font-family:monospace;'>- - -</span> Recíproca</span>")
    
    sorted_widths = sorted([w for w in active_widths if w != 0.8], reverse=True)
    width_desc_map = {4.0: "1ra Elección", 2.5: "2da Elección", 1.5: "3ra Elección"}
    if sorted_widths:
        legend_items.append("<span class='legend-divider'>|</span>")
        for i, width in enumerate(sorted_widths):
            desc = width_desc_map.get(width, f"{i+1}ra Elección")
            img_tag_width = f"<span style='display:inline-block; height: {width}px; width: 20px; background-color: white; vertical-align: middle; border-radius: 2px;'></span>"
            legend_items.append(f"<span class='legend-item'>{img_tag_width} {desc}</span>")
            
    symbol_legend_html = " | ".join(legend_items)
    
    # --- Ensamblar el Documento HTML Final ---
    log_engine("Ensamblando el archivo HTML final...")
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Sociograma Interactivo - {school_name} / {class_name}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.23.0/cytoscape.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        
        <style>
            body, html {{ margin: 0; padding: 0; height: 100%; font-family: sans-serif; overflow: hidden; }}
            .main-container {{ display: flex; flex-direction: column; width: 100vw; height: 100vh; }}
            #header-legend {{
                flex-shrink: 0; height: 90px;
                background-color: black; color: white;
                display: flex; flex-direction: column;
                justify-content: center; align-items: center;
                padding: 10px; box-sizing: border-box; z-index: 2;
            }}
            .header-title {{ font-size: 18px; font-weight: bold; margin-bottom: 8px; }}
            .symbol-line {{ font-size: 14px; white-space: nowrap; }}
            .legend-item {{ margin: 0 12px; }}
            .legend-item > span {{ font-size: 16px; vertical-align: middle; }}
            .legend-divider {{ margin: 0 15px; color: #555; }}
            #cy {{ flex-grow: 1; position: relative; }}
            .print-view {{ display: none; }}
            #print-image {{ width: 100%; height: auto; }}
            @media print {{
                .screen-view {{ display: none !important; }}
                .print-view {{ display: block !important; }}
                @page {{ margin: 1cm; }}
            }}
        </style>
    </head>
    <body>
        <div class="main-container screen-view">
            <div id="header-legend">
                {title_html}
                <div class="symbol-line">{symbol_legend_html}</div>
            </div>
            <div id="cy"></div>
            <button onclick="handlePrint()" style="position: absolute; top: 100px; left: 10px; z-index: 10; padding: 8px 12px; cursor: pointer;">Imprimir a PDF</button>
        </div>
        <div class="print-view">
            <img id="print-image" src="" alt="Vista para impresión del sociograma"/>
        </div>
        
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: {elements_json},
                style: [
                    {{ selector: 'node', style: {{ 'background-color': 'data(node_color)', 'shape': 'data(node_shape)', 'label': 'data(label)', 'width': 50, 'height': 50, 'font-size': 10, 'color': 'black', 'text-valign': 'center', 'text-halign': 'center', 'border-width': 2, 'border-color': '#333', 'opacity': 'data(opacity)' }} }},
                    {{ selector: 'edge', style: {{ 'width': 'data(edge_width)', 'line-color': 'data(edge_color)', 'target-arrow-color': 'data(edge_color)', 'line-style': 'data(line_style)', 'opacity': 'data(opacity)', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier' }} }}
                ],
                layout: {{ name: '{layout_to_use}', animate: true, animationDuration: 500, padding: 30, fit: true }}
            }});

            async function handlePrint() {{
                const printButton = document.querySelector('button');
                printButton.style.display = 'none';

                // Capturar el cuerpo entero, ya que ahora contiene la disposición correcta
                const fullViewElement = document.querySelector('.main-container');

                try {{
                    const canvas = await html2canvas(fullViewElement, {{ scale: 2, logging: false }});
                    const printImageElement = document.getElementById('print-image');
                    printImageElement.src = canvas.toDataURL('image/png', 1.0);

                    setTimeout(() => {{
                        window.print();
                        printButton.style.display = 'block';
                    }}, 100);

                }} catch (error) {{
                    console.error('Error al generar la imagen para impresión:', error);
                    alert('Hubo un error al preparar la impresión.');
                    printButton.style.display = 'block';
                }}
            }}
            window.handlePrint = handlePrint;
        }});
    </script>
    </body></html>
    """
    return html_content

def save_interactive_sociogram(html_content, output_path):
    log_engine(f"Guardando sociograma en el archivo '{output_path}'...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        log_engine(f"Sociograma guardado exitosamente.")
        return output_path
    except Exception as e:
        log_engine(f"ERROR CRÍTICO al guardar el archivo HTML: {e}")
        return None