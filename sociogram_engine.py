# sociogram_engine.py
# (v11.1 - Versión FINAL con todas las funcionalidades de la UI)

import networkx as nx
import json
import collections
import handlers_groups as hgrp

def log_engine(message):
    """Función de logging simple para este motor."""
    print(f"[SOCIOGRAM_ENGINE_v11.1] {message}")

# =============================================================================
# --- FUNCIONES CONSTRUCTORAS (BUILDERS) ---
# Cada función tiene la única responsabilidad de añadir aristas a un grafo.
# =============================================================================

def _build_real_action_graph(G, school_name, class_name, selected_data_keys, app_data_ref):
    """Añade aristas basadas en las acciones reales de los miembros."""
    log_engine("Construyendo grafo de 'Acción Real'...")
    class_questions = app_data_ref.get_class_question_definitions(school_name, class_name)
    source_responses = app_data_ref.questionnaire_responses_data
    
    for nominator_name in list(G.nodes()):
        responses = source_responses.get((school_name, class_name, nominator_name), {})
        for q_key, nominees in responses.items():
            if q_key not in selected_data_keys: continue
            q_def = next((d for d in class_questions.values() if d.get('data_key') == q_key), {})
            for idx, nominee_name in enumerate(nominees):
                if G.has_node(nominee_name):
                     G.add_edge(nominator_name, nominee_name, relation_data_key=q_key, election_index=idx, polarity=q_def.get('polarity', 'positive'))
    return G

def _build_meta_perception_graph(G, school_name, class_name, selected_data_keys, app_data_ref):
    """Añade aristas basadas en la meta-percepción (creencias sobre quién elige a quién)."""
    log_engine("Construyendo grafo de 'Meta-Percepción'...")
    class_questions = app_data_ref.get_class_question_definitions(school_name, class_name)
    source_perceptions = app_data_ref.cognitive_social_structures_data
    
    for ego_name in list(G.nodes()):
        ego_beliefs = source_perceptions.get((school_name, class_name, ego_name), {})
        for meta_q_key, believed_data in ego_beliefs.items():
            if meta_q_key not in selected_data_keys: continue
            q_def = next((d for d in class_questions.values() if d.get('data_key') == meta_q_key), {})
            if ego_name in believed_data:
                believed_nominators = believed_data[ego_name]
                for alter_name in believed_nominators:
                    if G.has_node(alter_name) and G.has_node(ego_name):
                        G.add_edge(alter_name, ego_name, relation_data_key=meta_q_key, election_index=0, polarity=q_def.get('polarity', 'positive'))
    return G

def _build_civsoc_graph(G, school_name, class_name, selected_data_keys, app_data_ref):
    """Añade aristas coloreadas basadas en la matriz de relaciones completas (CIVSOC)."""
    log_engine("Construyendo grafo 'CIVSOC'...")
    class_questions = app_data_ref.get_class_question_definitions(school_name, class_name)
    selected_defs = [d for d in class_questions.values() if d.get('data_key') in selected_data_keys]
    
    q_keys = {k: next(d['data_key'] for d in selected_defs if d.get('type')==t and d.get('polarity')==p) for k,t,p in [('accion_pos','[Acción Real]','positive'), ('accion_neg','[Acción Real]','negative'), ('meta_pos','[Meta-Percepción]','positive'), ('meta_neg','[Meta-Percepción]','negative')]}
    matrix, members, legend = hgrp.calculate_civsoc_matrix(school_name, class_name, q_keys)
    color_map = { "1": "#a8dada", "2": "#f9a8a8", "3": "#d5aaff", "4": "#ffd5a8", "5": "#64b5f6", "6": "#ff8a80", "7": "#ffb74d", "8": "#b39ddb" }
    
    for i, actor in enumerate(members):
        for j, target in enumerate(members):
            if i == j: continue
            code = str(matrix[i][j])
            if code in ['0', 'X']: continue
            actor_name = f"{actor.get('nome','').title()} {actor.get('cognome','').title()}"
            target_name = f"{target.get('nome','').title()} {target.get('cognome','').title()}"
            if G.has_node(actor_name) and G.has_node(target_name):
                G.add_edge(actor_name, target_name, relation_data_key=f"civsoc_{code}", label=legend.get(code, f"C.{code}"), color_override=color_map.get(code, "#6c757d"))
    return G

def _build_accuracy_graph(G, school_name, class_name, selected_data_keys, app_data_ref):
    """Añade aristas coloreadas basadas en el análisis de precisión global."""
    log_engine("Construyendo grafo de 'Análisis de Precisión'...")
    class_questions = app_data_ref.get_class_question_definitions(school_name, class_name)
    selected_defs = [d for d in class_questions.values() if d.get('data_key') in selected_data_keys]
    
    action_key = next(d['data_key'] for d in selected_defs if d.get('type') == '[Acción Real]')
    meta_key = next(d['data_key'] for d in selected_defs if d.get('type') == '[Meta-Percepción]')
    
    matrix, members, legend = hgrp.calculate_accuracy_matrix(school_name, class_name, action_key, meta_key)
    color_map = {"1": "#a5d6a7", "2": "#ef9a9a", "3": "#90caf9"} # Acierto (verde), Error (rojo), Omisión (azul)
    
    for i, ego_member in enumerate(members):
        for j, alter_member in enumerate(members):
            if i == j: continue
            code = str(matrix[i][j])
            if code in ['0', 'X']: continue
            
            alter_name = f"{alter_member.get('nome','').title()} {alter_member.get('cognome','').title()}"
            ego_name = f"{ego_member.get('nome','').title()} {ego_member.get('cognome','').title()}"
            
            if G.has_node(alter_name) and G.has_node(ego_name):
                G.add_edge(alter_name, ego_name, relation_data_key=f"accuracy_{code}", label=legend.get(code, f"C.{code}"), color_override=color_map.get(code, "#6c757d"))
    return G

# =============================================================================
# --- FUNCIÓN DIRECTORA PRINCIPAL ---
# =============================================================================

def generate_interactive_html(
    school_name, class_name,
    app_data_ref, 
    selected_data_keys,
    node_gender_filter='Todos',
    label_display_mode='nombre_apellido',
    connection_gender_type='todas',
    active_members_filter=False,
    nominators_option=True,
    reciprocal_nodes_color_filter=False,
    style_reciprocal_links=False,
    selected_participant_focus=None,
    connection_focus_mode='all',
    layout_to_use='cose',
    aggregation_mode='real_actions',
    perceiver_name=None,
    received_color_filter=False,
    highlight_mode='none',
    highlight_value=1
):
    """
    Versión MODULAR. Actúa como un director que llama a la función constructora
    adecuada y luego aplica los estilos (incluyendo resaltado de líderes) y genera el HTML.
    """
    log_engine(f"Motor director iniciado. Modo: '{aggregation_mode}'")

    # --- 1. Crear grafo base con nodos ---
    members_list = app_data_ref.members_data.get(school_name, {}).get(class_name, [])
    if not members_list:
        log_engine("Error: No se encontraron miembros. Abortando.")
        return None
    
    G_base = nx.MultiDiGraph()
    for member_data in members_list:
        if node_gender_filter == 'Todos' or member_data.get('sexo') == node_gender_filter:
            node_id = f"{member_data.get('nome','').strip().title()} {member_data.get('cognome','').strip().title()}"
            G_base.add_node(node_id, id=node_id, sexo_attr=member_data.get('sexo', 'Desconocido'), iniz=member_data.get('iniz', 'N/A'), original_nome=member_data.get('nome','').strip(), original_cognome=member_data.get('cognome','').strip())
    
    if not G_base.nodes():
        log_engine("Error: No hay nodos después de filtrar por sexo. Abortando.")
        return None
    log_engine(f"Grafo base creado con {G_base.number_of_nodes()} nodos.")
    
    # --- 2. Llamar a la función constructora apropiada ---
    builders = {
        'real_actions': _build_real_action_graph,
        'meta_perceptions': _build_meta_perception_graph,
        'civsoc_matrix': _build_civsoc_graph,
        'accuracy_analysis': _build_accuracy_graph
    }
    builder_func = builders.get(aggregation_mode)
    if not builder_func:
        log_engine(f"Error: Modo de agregación desconocido '{aggregation_mode}'. Abortando.")
        return None

    G_with_edges = builder_func(G_base.copy(), school_name, class_name, selected_data_keys, app_data_ref)
    
    log_engine(f"Grafo procesado por constructor. Nodos: {G_with_edges.number_of_nodes()}, Aristas: {G_with_edges.number_of_edges()}.")
    if G_with_edges.number_of_edges() == 0:
        log_engine("Advertencia: No se generó ninguna arista. La red estará vacía.")

    # --- 3. Aplicar filtros y estilos visuales (Lógica común) ---
    log_engine("Aplicando filtros y estilos visuales...")
    G = G_with_edges.copy()
    if not nominators_option: G.remove_nodes_from(list(nx.isolates(G)))
    
    highlighted_nodes = set()
    if highlight_mode != 'none' and aggregation_mode == 'real_actions':
        positive_keys = {k for k in selected_data_keys if any(q.get('polarity') == 'positive' for q in app_data_ref.get_class_question_definitions(school_name, class_name).values() if q.get('data_key') == k)}
        positive_choices = collections.Counter(v for u, v, data in G.edges(data=True) if data.get('relation_data_key') in positive_keys)
        sorted_leaders = positive_choices.most_common()

        if highlight_mode == 'top_n':
            highlighted_nodes = {member for member, score in sorted_leaders[:highlight_value]}
        elif highlight_mode == 'k_th':
            if len(sorted_leaders) >= highlight_value:
                k_score = sorted_leaders[highlight_value - 1][1]
                highlighted_nodes = {member for member, score in sorted_leaders if score == k_score}

    is_focus_active = bool(selected_participant_focus and selected_participant_focus in G.nodes())
    active_focus_nodes = set()
    if is_focus_active:
        active_focus_nodes.add(selected_participant_focus)
        if connection_focus_mode == 'outgoing':
            for _, v in G.out_edges(selected_participant_focus): active_focus_nodes.add(v)
        elif connection_focus_mode == 'incoming':
            for u, _ in G.in_edges(selected_participant_focus): active_focus_nodes.add(u)
        else: # 'all'
            for u, v in G.out_edges(selected_participant_focus): active_focus_nodes.add(v)
            for u, _ in G.in_edges(selected_participant_focus): active_focus_nodes.add(u)
    
    active_node_colors = set()
    all_node_ids = sorted(list(G.nodes()))

    for node_name, node_data in G.nodes(data=True):
        sexo = node_data.get('sexo_attr', 'Desconocido')
        node_data['node_shape'] = 'ellipse' if sexo == 'Masculino' else 'triangle' if sexo == 'Femenino' else 'rectangle'
        node_data['node_color'] = 'skyblue' if sexo == 'Masculino' else 'lightcoral' if sexo == 'Femenino' else 'lightgreen'
        node_data['opacity'] = 1.0

        if node_name in highlighted_nodes:
            node_data['node_color'] = 'lawngreen'

        is_receiver = G.in_degree(node_name) > 0 and G.out_degree(node_name) == 0
        has_self_loop = G.has_edge(node_name, node_name)
        if received_color_filter and (is_receiver or has_self_loop):
             node_data['node_color'] = 'gold'

        reciprocal_nodes = {n for u, v in G.edges() if G.has_edge(v, u) for n in (u, v)}
        if reciprocal_nodes_color_filter and node_name in reciprocal_nodes:
            node_data['node_color'] = 'mediumpurple'
            
        if nominators_option and G.degree(node_name) == 0:
            node_data['node_color'] = 'silver'

        if is_focus_active:
            if node_name not in active_focus_nodes: node_data['opacity'] = 0.15
            elif node_name == selected_participant_focus: node_data['node_color'] = 'darkorange'
            else: node_data['node_color'] = '#FFDB58'
        
        if label_display_mode == 'iniciales':
            node_data['label'] = node_data.get('iniz', 'N/A')
        elif label_display_mode == 'anónimo':
            node_data['label'] = f'M{all_node_ids.index(node_name) + 1}'
        else: # nombre_apellido
            node_data['label'] = f"{node_data.get('original_nome','')} {node_data.get('original_cognome','')}"
            
        active_node_colors.add(node_data['node_color'])
        
    width_map = {0: 4.0, 1: 2.5, 2: 1.5}
    active_widths = set()
    active_edge_styles = collections.defaultdict(dict)
    is_reciprocal_link_present = False
    edge_color_map = {key: color for key, color in zip(selected_data_keys, ['#007bff','#dc3545','#ffc107','#6c757d','#17a2b8'])}
    class_questions = app_data_ref.get_class_question_definitions(school_name, class_name)
    
    for u, v, data in G.edges(data=True):
        data['opacity'] = 1.0
        if is_focus_active:
            # Lógica de estilo específica para el MODO FOCO
            is_relevant_edge = (u == selected_participant_focus or v == selected_participant_focus)
            
            if is_relevant_edge:
                is_reciprocal_with_focus = G.has_edge(v, u)
                
                # Define color y estilo basado en la dirección relativa al foco
                if u == selected_participant_focus and is_reciprocal_with_focus:
                    data['edge_color'], data['line_style'] = '#FF8C00', 'dotted' # Naranja para Recíproca con Foco
                elif u == selected_participant_focus:
                    data['edge_color'], data['line_style'] = '#32CD32', 'dotted' # Verde para Saliente
                elif v == selected_participant_focus:
                    data['edge_color'], data['line_style'] = '#1E90FF', 'dotted' # Azul para Entrante
                
                data['edge_width'] = 2.5 # Un grosor uniforme para el modo foco
                
            else:
                data['opacity'] = 0.1 # Ocultar aristas no relacionadas con el foco
        else:
            # Lógica de estilo para los MODOS NORMALES (sin foco)
            if 'color_override' in data:
                data['edge_color'] = data['color_override']
                data['line_style'] = 'solid'
                data['edge_width'] = 2.5
                active_edge_styles[data['label']] = {'color': data['edge_color'], 'style': 'solid'}
            else:
                election_index = data.get('election_index', 99)
                edge_width = width_map.get(election_index, 0.8)
                data['edge_width'] = edge_width
                active_widths.add(edge_width)
                q_def = next((d for d in class_questions.values() if d.get('data_key') == data.get('relation_data_key')), {})
                relation_label = q_def.get('type', 'Relación') if q_def else 'Relación Agregada'
                polarity = data.get('polarity', 'neutral')
                data['edge_color'] = '#dc3545' if polarity == 'negative' else edge_color_map.get(data.get('relation_data_key'), '#6c757d')
                data['line_style'] = 'dashed' if style_reciprocal_links and G.has_edge(v, u) else 'solid'
                if data['line_style'] == 'dashed': is_reciprocal_link_present = True
                style_key = f"({polarity[:3].title()}) {relation_label}"
                active_edge_styles[style_key] = {'color': data['edge_color'], 'style': 'solid'}

    # --- INICIO DEL BLOQUE DE CÓDIGO QUE PREGUNTASTE ---
    # --- 4. Generación de JSON y HTML ---
    log_engine("Generando JSON y HTML final...")
    elements = [{'data': {**data}} for node_id, data in G.nodes(data=True)]
    elements.extend([{'data': {'source': u, 'target': v, **data}} for u, v, data in G.edges(data=True)])
    elements_json = json.dumps(elements, indent=2)
    
    title_html = f"<div class='header-title'>{school_name} / {class_name}</div>"
    legend_items = []
    
    # Leyenda de Nodos (común para ambos modos)
    node_legend_map = collections.OrderedDict([
        ('darkorange', "Foco"), ('#FFDB58', "Conectado al Foco"), 
        ('lawngreen', "Líder"), ('gold', "Solo Recibe"), 
        ('skyblue', "Masculino"), ('lightcoral', "Femenino"), ('lightgreen', "Otro"),
        ('mediumpurple', "Nodo Recíproco"), ('silver', "No Elegido")
    ])
    for color, desc in node_legend_map.items():
        if color in active_node_colors:
            symbol = "▲" if "Femenino" in desc else "■" if "Otro" in desc else "●"
            legend_items.append(f"<span class='legend-item'><span style='color:{color};'>{symbol}</span> {desc}</span>")
    
    legend_items.append("<span class='legend-divider'>|</span>")

    # Leyenda de Aristas (depende del modo)
    if is_focus_active:
        # Leyenda específica para el modo Foco
        legend_items.append(f"<span class='legend-item'><span style='color:#32CD32; font-family:monospace; font-weight:bold;'>· · ·→</span> Saliente</span>")
        legend_items.append(f"<span class='legend-item'><span style='color:#1E90FF; font-family:monospace; font-weight:bold;'>· · ·→</span> Entrante</span>")
        legend_items.append(f"<span class='legend-item'><span style='color:#FF8C00; font-family:monospace; font-weight:bold;'>· · ·→</span> Recíproca con Foco</span>")
    else:
        # Leyenda para los modos normales
        for desc, style_info in sorted(active_edge_styles.items()):
            color, style = style_info['color'], style_info['style']
            line_symbol = "- - -" if style == 'dashed' else "· · ·" if style == 'dotted' else "———"
            legend_items.append(f"<span class='legend-item'><span style='color:{color}; font-family:monospace; font-weight:bold;'>{line_symbol}→</span> {desc}</span>")
        if is_reciprocal_link_present:
            legend_items.append(f"<span class='legend-item'><span style='font-family:monospace; font-weight:bold;'>- - -→</span> Recíproca</span>")
    
    # Leyenda de Grosor (solo para modos normales)
    if not is_focus_active and active_widths:
        sorted_widths = sorted([w for w in active_widths if w != 0.8], reverse=True)
        width_desc_map = {4.0: "1ra", 2.5: "2da", 1.5: "3ra"}
        if sorted_widths:
            legend_items.append("<span class='legend-divider'>|</span>")
            for i, width in enumerate(sorted_widths):
                desc = width_desc_map.get(width, f"{i+1}ra Elección")
                img_tag_width = f"<span style='display:inline-block; height: {width}px; width: 20px; background-color: #ccc; vertical-align: middle; border-radius: 2px;'></span>"
                legend_items.append(f"<span class='legend-item'>{img_tag_width} {desc}</span>")
            
    symbol_legend_html = " ".join(legend_items)
    
    log_engine("Contenido HTML final generado. Devolviendo resultado.")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Sociograma Interactivo - {school_name} / {class_name}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.23.0/cytoscape.min.js"></script>
        <style>
            body, html {{ margin: 0; padding: 0; height: 100%; font-family: sans-serif; overflow: hidden; background-color: #f0f0f0; }}
            #header-legend {{ background-color: #333; color: white; padding: 8px 15px; box-sizing: border-box; z-index: 2; text-align: center; }}
            .header-title {{ font-size: 16px; font-weight: bold; margin-bottom: 5px; }}
            .symbol-line {{ font-size: 12px; white-space: nowrap; overflow-x: auto; }}
            .legend-item {{ display: inline-block; margin: 0 8px; }} .legend-item > span {{ vertical-align: middle; }}
            .legend-divider {{ display: inline-block; margin: 0 8px; color: #777; }}
            #cy {{ width: 100%; height: calc(100% - 50px); }}
        </style>
    </head>
    <body>
        <div id="header-legend">
            {title_html}
            <div class="symbol-line">{symbol_legend_html}</div>
        </div>
        <div id="cy"></div>
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