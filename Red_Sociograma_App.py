# --- BLOQUE 1 DE 10: IMPORTACIONES E INICIALIZACIÓN ---
# =============================================================================
#  Red_Sociograma_App.py - Versión de Depuración
# =============================================================================

# --- ¡¡¡NUEVA LÍNEA DE PRUEBA!!! ---
print("\n" + "="*50)
print("--- ¡VERSIÓN DE PRUEBA DE Red_Sociograma_App.py CARGADA! ---")
print("="*50 + "\n")
# --- FIN DE LA LÍNEA DE PRUEBA ---

# --- BLOQUE 1: IMPORTACIONES (Sin cambios) ---
import sys, os, collections, functools, io, re, traceback, datetime, unicodedata, csv, json
import FreeSimpleGUI as sg
import tkinter as tk
import subprocess
import pandas
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import threading
import time
import webbrowser
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    import sociograma_data
    import pdf_generator
    import handlers_utils as hutils
    import handlers_csv_excel as hcsv
    import handlers_institutions as hinst
    import handlers_groups as hgrp
    import handlers_members as hmemb
    import handlers_form_member as hfmember
    import handlers_questionnaire as hquest
    import handlers_questions as hq
    import handlers_sociogram as hsoc
    import handlers_print_view as hprint
    import handlers_sociomatrix as hsm
    import sociogram_engine
    import sociogram_utils
    from popapp import show_coffee_popup # <-- Importación clave
except ImportError as e:
    # Este popup funcionará incluso si otros fallan, ya que no depende de módulos locales
    sg.popup_error(f"Error Crítico de Importación:\n\n{e}\n\nAsegúrate de que todos los archivos .py del programa estén en la misma carpeta.\n\nLa aplicación se cerrará.", title="Error Fatal")
    sys.exit(1)

# --- BLOQUE 2: INICIALIZACIÓN (Sin cambios) ---
app_data = sociograma_data
app_data.initialize_data()
app_state = {} 
def log_message(message, level='info'):
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}][{level.upper()}] {message}")

# --- BLOQUE 2 DE 10: LAYOUTS (INSTITUCIONES, GRUPOS, MIEMBROS) ---
# =============================================================================
#  BLOQUE 3: DEFINICIONES DE LAYOUTS
# =============================================================================

def create_layout_institutions():
    form_frame = sg.Frame("", [
        [sg.Text("", key='-FORM_INST_TITLE-', font=("Helvetica", 14))],
        [sg.Text("Nombre de la institución:", size=(25, 1)), sg.Input(key='-FORM_INST_NAME-', expand_x=True)], 
        [sg.Text("Anotaciones varias sobre la institución:", size=(35, 1))],
        [sg.Multiline(size=(40, 5), key='-FORM_INST_ANNOT-', expand_x=True, expand_y=True)], 
        [sg.Push(), sg.Button("Guardar Institución", key='-FORM_INST_SAVE-'), sg.Button("Cancelar", key='-FORM_INST_CANCEL-')]
    ], key='-FORM_INST_FRAME-', visible=False, expand_x=True, element_justification='center')

    main_content = [
        [sg.Text("Tabla de Instituciones", font=("Helvetica", 16))],
        [sg.Text("Institución:"), sg.Push(), sg.Text("Anotaciones de Institución:")],
        [sg.Listbox(values=[], size=(40, 15), key='-INST_SELECT-', enable_events=True, expand_x=True, expand_y=True), 
         sg.Multiline(size=(40, 15), key='-INST_ANNOTATIONS-', disabled=True, expand_x=True, expand_y=True)],
        [sg.Button("Nueva Institución", key='-NEW_INST-'), sg.Button("Modificar Institución", key='-MOD_INST-', disabled=True), sg.Button("Eliminar Institución", key='-DEL_INST-', disabled=True)],
        [sg.HorizontalSeparator()],
        [sg.Button("Ver Grupos", key='-NAV_TO_GROUPS-', disabled=True), sg.Button("Importar/Exportar...", key='-MANAGE_CSV-'), sg.Push(), sg.Button("Salir App", key='-EXIT-')]
    ]
    
    layout = [
        [form_frame], 
        [sg.Column(main_content, key='-MAIN_INST_COL-', expand_x=True, expand_y=True, scrollable=True)]
    ]
    return layout

def create_layout_groups(institution_name):
    form_frame = sg.Frame("", [
        [sg.Text("", key='-FORM_GROUP_TITLE-', font=("Helvetica", 14))],
        [sg.Text(f"Institución: {institution_name}")],
        [sg.Text("Nombre:", size=(15, 1)), sg.Input(key='-FORM_GROUP_NAME-', expand_x=True)],
        [sg.Text("Coordinador:", size=(15, 1)), sg.Input(key='-FORM_GROUP_COORD-', expand_x=True)],
        [sg.Text("Profesor 2:", size=(15, 1)), sg.Input(key='-FORM_GROUP_INS2-', expand_x=True)],
        [sg.Text("Profesor 3:", size=(15, 1)), sg.Input(key='-FORM_GROUP_INS3-', expand_x=True)],
        [sg.Text("Sostén:", size=(15, 1)), sg.Input(key='-FORM_GROUP_SOST-', expand_x=True)],
        [sg.Text("Anotaciones:", size=(15, 1)), sg.Multiline(size=(35, 4), key='-FORM_GROUP_ANNOT-', expand_x=True)],
        [sg.Push(), sg.Button("Guardar Grupo", key='-FORM_GROUP_SAVE-'), sg.Button("Cancelar", key='-FORM_GROUP_CANCEL-')]
    ], key='-FORM_GROUP_FRAME-', visible=False, expand_x=True)

    details = [
        [sg.Text("Detalles del Grupo:", font=("Helvetica", 10, "bold"))], 
        [sg.Text("Coordinador:", size=(12,1)), sg.Input(key='-GROUP_COORD-', disabled=True, expand_x=True)], 
        [sg.Text("Profesor 2:", size=(12,1)), sg.Input(key='-GROUP_INS2-', disabled=True, expand_x=True)],
        [sg.Text("Profesor 3:", size=(12,1)), sg.Input(key='-GROUP_INS3-', disabled=True, expand_x=True)],
        [sg.Text("Sostén:", size=(12,1)), sg.Input(key='-GROUP_SOST-', disabled=True, expand_x=True)],
        [sg.Text("Anotaciones:", size=(12,1)), sg.Multiline(key='-GROUP_ANNOT-', size=(28,4), disabled=True, expand_x=True)]
    ]
    
    # --- CORRECCIÓN: Botón "Reporte de Precisión" eliminado de esta columna ---
    analysis_and_reports_column = [
        [sg.Text("Análisis y Reportes:", font=("Helvetica", 10, "bold"))],
        [sg.Button("Matriz Sociométrica", key='-NAV_TO_MATRIX-', disabled=True)],
        [sg.Button("Diana de Afinidad", key='-NAV_TO_DIANA-', disabled=True)],
        [sg.Button("PDF Resumen Cuestionario", key='-PDF_SUMMARY-', disabled=True)]
    ]

    main_content = [
        [sg.Text(f"Grupos de: {institution_name}", font=("Helvetica", 16), key='-GROUPS_TITLE-')],
        [sg.Column([[sg.Text("Seleccionar Grupo:")], [sg.Listbox(values=[], size=(30, 15), key='-GROUP_SELECT-', enable_events=True, expand_y=True, expand_x=True)]]), 
         sg.VSeperator(), 
         sg.Column(details, expand_x=True)],
        [sg.HorizontalSeparator()], 
        [sg.Column([[sg.Button("Nuevo Grupo", key='-NEW_GROUP-'), sg.Button("Modificar Grupo", key='-MOD_GROUP-', disabled=True), sg.Button("Eliminar Grupo", key='-DEL_GROUP-', disabled=True)], [sg.Button("Ver Miembros", key='-NAV_TO_MEMBERS-', disabled=True), sg.Button("Sociograma", key='-NAV_TO_SOCIOGRAM-', disabled=True)]]), 
         sg.VSeperator(), 
         sg.Column(analysis_and_reports_column)],
        [sg.HorizontalSeparator()],
        [sg.Push(), sg.Button("Volver a Instituciones", key='-BACK_TO_INST-')]
    ]
    
    layout = [
        [form_frame], 
        [sg.Column(main_content, key='-MAIN_GROUP_COL-', expand_x=True, expand_y=True, scrollable=True)]
    ]
    return layout

def create_layout_members(institution_name, group_name):
    form_frame = sg.Frame("", [
        [sg.Text("", font=("Helvetica", 14), key='-FORM_MEMBER_TITLE-')], 
        [sg.Text("Apellido:", size=(15,1)), sg.Input(key='-FORM_MEMBER_COGNOME-')], 
        [sg.Text("Nombre:", size=(15,1)), sg.Input(key='-FORM_MEMBER_NOME-')], 
        [sg.Text("Iniciales (3-4):", size=(15,1)), sg.Input(key='-FORM_MEMBER_INIZ-', size=(10,1))], 
        [sg.Text("Sexo:"), sg.Radio("Masculino", "SEXO", key='-FORM_MEMBER_SEXO_M-'), sg.Radio("Femenino", "SEXO", key='-FORM_MEMBER_SEXO_F-'), sg.Radio("Desconocido", "SEXO", key='-FORM_MEMBER_SEXO_D-')], 
        [sg.Text("Fecha Nacimiento:", size=(15,1)), sg.Input(key='-FORM_MEMBER_DOB-')], 
        [sg.Text("Anotaciones:"), sg.Multiline(size=(35,4), key='-FORM_MEMBER_ANNOT-')], 
        [sg.Push(), sg.Button("Guardar Miembro", key='-FORM_MEMBER_SAVE-'), sg.Button("Cancelar", key='-FORM_MEMBER_CANCEL-')]
    ], key='-FORM_MEMBER_FRAME-', visible=False, expand_x=True)
    
    details = [
        [sg.Text("Detalles del Miembro:", font=("Helvetica", 10, "bold"))],
        [sg.Text("Apellido:", size=(12,1)), sg.Input(key='-MEMBER_COGNOME-', disabled=True)], 
        [sg.Text("Nombre:", size=(12,1)), sg.Input(key='-MEMBER_NOME-', disabled=True)], 
        [sg.Text("Iniciales:", size=(12,1)), sg.Input(key='-MEMBER_INIZ-', disabled=True)], 
        [sg.Text("Anotaciones:", size=(12,1)), sg.Multiline(key='-MEMBER_ANNOT-', size=(35,6), disabled=True)]
    ]
    
    main_content = [
        [sg.Text(f"Miembros de: {group_name} ({institution_name})", font=("Helvetica", 16), key='-MEMBERS_TITLE-')],
        [sg.Column([[sg.Text("Seleccionar Miembro:")], [sg.Listbox(values=[], size=(30, 15), key='-MEMBER_SELECT-', expand_x=True, expand_y=True, enable_events=True)]]), 
         sg.VSeperator(), 
         sg.Column(details, expand_x=True)], 
        [sg.Button("Nuevo Miembro", key='-NEW_MEMBER-'), sg.Button("Modificar Miembro", key='-MOD_MEMBER-', disabled=True), sg.Button("Eliminar Miembro", key='-DEL_MEMBER-', disabled=True)],
        [sg.HorizontalSeparator()],
        
        [sg.Text("Acciones para el Miembro Seleccionado:", font=("Helvetica", 10, "bold"))],
        [sg.Button("Cuestionario", key='-NAV_TO_QUESTIONNAIRE-', disabled=True, 
                     tooltip="Abrir el cuestionario unificado (acciones y percepciones) para este miembro.")],

        [sg.Push(), sg.Button("Volver a Grupos", key='-BACK_TO_GROUPS-')]
    ]
    
    layout = [
        [form_frame], 
        [sg.Column(main_content, key='-MAIN_MEMBER_COL-', expand_x=True, expand_y=True, scrollable=True)]
    ]
    return layout

# --- BLOQUE 3 DE 10: LAYOUTS (CUESTIONARIOS, PREGUNTAS, ANÁLISIS) ---

def create_layout_questionnaire(questionnaire_data, member_name, institution_name, group_name):
    """
    Crea el layout para la ventana INDEPENDIENTE del cuestionario híbrido.
    Usa el método robusto con VPush para garantizar la funcionalidad de los botones.
    """
    title = f"Cuestionario para: {member_name}"
    subtitle = f"Institución: {institution_name} | Grupo: {group_name}"

    header_layout = [
        # Se añaden claves a los textos para poder actualizarlos después
        [sg.Text(title, font=("Helvetica", 16), key='-QUESTIONNAIRE_TITLE-')],
        [sg.Text(subtitle, font=("Helvetica", 10), key='-QUESTIONNAIRE_SUBTITLE-')]
    ]
    
    # Este contenedor contendrá las preguntas y se podrá limpiar y rellenar
    questions_container_layout = [
        [sg.Column([], key='-QUESTIONNAIRE_CONTENT-', expand_x=True, expand_y=True, scrollable=True, vertical_scroll_only=True)]
    ]
    
    body_rows = []
    if not questionnaire_data['success']:
        body_rows.append([sg.Text(questionnaire_data['message'], text_color='red')])
    elif not questionnaire_data['questions']:
        body_rows.append([sg.Text("No hay preguntas definidas para este grupo.")])
    else:
        for q in questionnaire_data['questions']:
            options = [opt[0] for opt in q['options'] if opt[1] not in [None, '']]
            
            # Ahora, en lugar de buscar en un diccionario general, usamos las selecciones
            # que vienen pre-cargadas DENTRO de cada objeto de pregunta 'q'.
            selections = q.get('saved_selections', [])
            
            rows_for_frame = []
            for i in range(q['max_selections']):
                default_val = selections[i] if i < len(selections) else 'Seleccionar'
                rows_for_frame.append([
                    sg.Text(f"Elección {i+1}:", size=(10, 1)),
                    sg.Combo(['Seleccionar'] + options, default_value=default_val, key=f"-Q_{q['data_key']}_{i}-", readonly=True, expand_x=True)
                ])
            
            # El texto de la pregunta 'q['text']' ya viene formateado para indicar si es de percepción
            body_rows.append([sg.Frame(q['text'], rows_for_frame, expand_x=True)])

    # Se actualiza el contenedor con las filas generadas
    questions_container_layout = [
        [sg.Column(body_rows, key='-QUESTIONNAIRE_CONTENT-', expand_x=True, expand_y=True, scrollable=True, vertical_scroll_only=True)]
    ]

    footer_layout = [
        [sg.HorizontalSeparator()],
        [sg.Button("Guardar", key='-SAVE_Q-'),
         sg.Button("PDF Plantilla", key='-PDF_TEMPLATE_Q-'),
         sg.Button("Gestionar Preguntas", key='-MANAGE_Q-'),
         sg.Push(),
         sg.Button("Volver a Miembros", key='-BACK_TO_MEMBERS-')]
    ]

    # Estructura final con VPush para mantener los botones fijos en la parte inferior
    layout = [[
        sg.Column(
            header_layout +
            questions_container_layout +
            [[sg.VPush()]] +
            footer_layout,
            expand_x=True, expand_y=True
        )
    ]]
    
    return layout

def create_layout_question_management(institution_name, group_name):
    """
    Versión FINAL. Crea el layout para la gestión de preguntas, separando la
    'Categoría Temática' (editable) del 'Tipo Estructural' (manejado internamente).
    """
    cognitive_options_frame = sg.Frame("Opciones Cognitivas", [
        [sg.Checkbox("Es una pregunta de Meta-Percepción (ej: '¿Quién crees que te elegirá a TI?')",
                     key='-FORM_Q_IS_META_PERCEPTION-',
                     tooltip="Marcar si la pregunta es sobre las percepciones del miembro sobre sí mismo.")]
    ], expand_x=True)

    form_frame = sg.Frame("", [
        [sg.Text("", font=("Helvetica", 14), key='-FORM_Q_TITLE-')],
        [sg.Text("ID Único:", size=(20,1)), sg.Input(key='-FORM_Q_ID-')],
        [sg.Text("Texto Pregunta (Base):", size=(20,1)), sg.Multiline(size=(40,3), key='-FORM_Q_TEXT-')],
        
        # --- CAMBIO CLAVE: Nuevo campo para la categoría temática ---
        [sg.Text("Categoría Temática:", size=(20,1)), sg.Input(key='-FORM_Q_CATEGORY-', tooltip="Ej: Trabajo, Juego, Amistad")],
        # El antiguo campo 'Tipo' se ha eliminado del formulario.

        [sg.Text("Clave de Datos:", size=(20,1)), sg.Input(key='-FORM_Q_DK-')],
        [cognitive_options_frame],
        [sg.HorizontalSeparator()],
        [sg.Text("Polaridad:"), sg.Radio("Positiva", "POL", default=True, key='-FORM_Q_POL_POS-'), sg.Radio("Negativa", "POL", key='-FORM_Q_POL_NEG-')],
        [sg.Text("Orden:", size=(20,1)), sg.Input(size=(5,1), key='-FORM_Q_ORDER-')],
        [sg.Text("Máx. Selecciones:", size=(20,1)), sg.Input(size=(5,1), key='-FORM_Q_MAX-')],
        [sg.Checkbox("Permitir auto-selección", key='-FORM_Q_SELF-')],
        [sg.Push(), sg.Button("Guardar Pregunta", key='-FORM_Q_SAVE-'), sg.Button("Cancelar", key='-FORM_Q_CANCEL-')]
    ], key='-FORM_Q_FRAME-', visible=False, expand_x=True)
    
    main_content = [
        [sg.Text("Gestionar Preguntas", font=("Helvetica", 16))],
        [sg.Text(f"Para: {group_name} ({institution_name})")],
        [sg.Listbox(values=[], size=(80, 20), key='-Q_LIST-', enable_events=True, expand_x=True, expand_y=True)],
        [sg.Button("Nueva Pregunta", key='-NEW_Q-'), sg.Button("Modificar Pregunta", key='-MOD_Q-', disabled=True), sg.Button("Eliminar Pregunta", key='-DEL_Q-', disabled=True)],
        [sg.Push(), sg.Button("Volver", key='-BACK_TO_Q-')]
    ]
    
    return [[form_frame], [sg.Column(main_content, key='-MAIN_Q_COL-', expand_x=True, expand_y=True, scrollable=True)]]

def create_layout_sociogram(institution_name, group_name, relation_options, participant_options):
    """
    Versión FINAL y COMPLETA. Crea el layout para la ventana del Sociograma,
    incluyendo los controles para todos los modos de agregación de red.
    """
    log_message(f"Creando layout de Sociograma para: {group_name}", 'info')
    
    # --- Frame 1: Selección de Preguntas ---
    checkboxes_layout = []
    if relation_options:
        checkboxes_layout = [[sg.Checkbox(opt['label'], default=True, key=f"-SOC_REL__{opt['data_key']}__")] for opt in relation_options]
    else:
        checkboxes_layout = [[sg.Text("No hay relaciones para seleccionar.")]]

    relation_frame = sg.Frame("Preguntas a Incluir", [
        [sg.Column(checkboxes_layout, size=(300, 150), scrollable=True, vertical_scroll_only=True)],
        [sg.Button("Todas", key='-SOC_SEL_ALL-'), sg.Button("Ninguna", key='-SOC_SEL_NONE-'), sg.Button("Positivas", key='-SOC_SEL_POS-'), sg.Button("Negativas", key='-SOC_SEL_NEG-')]
    ], expand_y=True)
    
    # --- Frame 2: Filtros por Sexo ---
    filter_frame = sg.Frame("Filtro por Sexo", [
        [sg.Text("Nodos (Miembros):")],
        [sg.Radio("Todos", "GENDER_FILTER", default=True, key='-SOC_GENDER_ALL-'), sg.Radio("Masculino", "GENDER_FILTER", key='-SOC_GENDER_M-'), sg.Radio("Femenino", "GENDER_FILTER", key='-SOC_GENDER_F-')],
        [sg.HorizontalSeparator()],
        [sg.Text("Aristas (Conexiones):")],
        [sg.Radio("Todas", "CONN_GENDER", default=True, key='-SOC_CONN_ALL-'), sg.Radio("Mismo Sexo", "CONN_GENDER", key='-SOC_CONN_SAME-'), sg.Radio("Diferente Sexo", "CONN_GENDER", key='-SOC_CONN_DIFF-')]
    ])
    
    # --- Frame 3: Modos de Red (Fuente de Datos) ---
    aggregation_options = [
        ("Red Real (Acciones Directas)", "real_actions"),
        ("Red de Relaciones Completas (CIVSOC)", "civsoc_matrix"),
        ("Red de Meta-Percepción (SELF)", "meta_perceptions"),
        ("Análisis de Precisión (Global)", "accuracy_analysis"), # Texto final corregido
    ]

    aggregation_frame = sg.Frame("Fuente de Datos y Agregación", [
        [sg.Text("Modo de Red:", size=(28,1)),
         sg.Combo([opt[0] for opt in aggregation_options], default_value=aggregation_options[0][0],
                  key='-SOC_AGGREGATION_MODE-', readonly=True, enable_events=True, expand_x=True,
                  tooltip="Define el tipo de análisis a visualizar.")],
        [sg.Text("Perceptor (para Foco):", size=(28,1)),
         sg.Combo([p[0] for p in participant_options if p[1] is not None], 
                  key='-SOC_PERCEIVER-', readonly=True, disabled=True, expand_x=True,
                  tooltip="Este campo se activa solo para modos que requieren un foco individual.")]
    ], expand_x=True)
    
    # --- Ensamblaje de la Columna Izquierda ---
    left_col_layout = sg.Column([[relation_frame], [filter_frame], [aggregation_frame]], vertical_alignment='top')
    
    # --- Controles de la Columna Derecha ---
    style_frame = sg.Frame("Estilos y Etiquetas", [
        [sg.Text("Etiquetas Nodos:"), sg.Combo(['Iniciales', 'Nombre Apellido', 'Anónimo'], default_value='Iniciales', key='-SOC_LABEL_MODE-', readonly=True, size=(20,1))],
        [sg.Checkbox("Estilo de Arista Recíproca", default=True, key='-SOC_RECIPROCAL_STYLE-')],
        [sg.Checkbox("Mostrar Nodos Aislados", default=True, key='-SOC_SHOW_ISOLATES-')],
        [sg.Checkbox("Mostrar solo Miembros Activos", key='-SOC_ACTIVE_ONLY-')]
    ])
    
    color_role_frame = sg.Frame("Coloreado por Rol", [
        [sg.Checkbox("En Relación Recíproca", key='-SOC_COLOR_RECIP_NODES-')]
    ])
    
    analysis_frame = sg.Frame("Análisis y Resaltado", [
        [sg.Text("Foco en un Participante:")],
        [sg.Combo([p[0] for p in participant_options], default_value=participant_options[0][0] if participant_options else '', size=(25, 1), key='-SOC_FOCUS_PARTICIPANT-', readonly=True)],
        [sg.Radio("Todas Conexiones", "FOCUS_MODE", default=True, key='-SOC_FOCUS_ALL-'), sg.Radio("Salientes", "FOCUS_MODE", key='-SOC_FOCUS_OUT-'), sg.Radio("Entrantes", "FOCUS_MODE", key='-SOC_FOCUS_IN-')],
    ])

    # --- Ensamblaje de la Columna Derecha ---
    right_col_layout = sg.Column([[style_frame], [color_role_frame], [analysis_frame]], vertical_alignment='top')
    
    # --- Layout Principal de Controles ---
    top_controls_layout = [[left_col_layout, sg.VSeperator(), right_col_layout]]
    
    # --- Instrucciones de Uso ---
    info_layout = [
        [sg.Text("1. Selecciona el 'Modo de Red' y los filtros deseados.")],
        [sg.Text("2. Haz clic en 'Generar y Ver Sociograma'. Se abrirá una nueva ventana con el grafo interactivo.")],
        [sg.Text("3. CIERRA LA VENTANA DEL SOCIOGRAMA para volver a esta pantalla.")]
    ]
    
    # --- Ensamblaje Final de la Ventana ---
    main_content = [
        [sg.Text(f"Sociograma Interactivo: {group_name} ({institution_name})", font=("Helvetica", 16))],
        [sg.Frame("Opciones de Visualización", top_controls_layout, expand_x=True)],
        [sg.Frame("Uso", info_layout, expand_x=True)],
        [sg.HorizontalSeparator()],
        [sg.Button("Generar y Ver Sociograma", key='-SOC_GENERATE_INTERACTIVE-'),
         sg.Push(),
         sg.Button("Volver a Grupos", key='-BACK_TO_GROUPS-')]
    ]
    
    layout = [[sg.Column(main_content, scrollable=True, vertical_scroll_only=True, expand_x=True, expand_y=True)]]
    return layout

def create_layout_sociomatrix(institution_name, group_name):
    """
    Versión final que unifica la selección de preguntas mediante checkboxes para todos los modos.
    """
    # --- 1. DEFINICIÓN DE LOS CONTROLES DE LA UI ---

    # Frame de selección de preguntas (UNIFICADO PARA TODOS LOS MODOS)
    relation_options = sociogram_utils.get_relation_options(institution_name, group_name, app_data)
    q_layout_rows = [[sg.Checkbox(opt['label'], key=f"-MATRIXQ__{opt['data_key']}__", default=True)] for opt in relation_options] if relation_options else [[sg.Text("No hay preguntas definidas.")]]
    questions_frame = sg.Frame("Preguntas a Incluir",
        [[sg.Column(q_layout_rows, size=(780, 120), scrollable=True, vertical_scroll_only=True)],
         [sg.Button("Todas", k='-MATRIX_ALL-'), sg.Button("Ninguna", k='-MATRIX_NONE-'), sg.Button("Positivas", k='-MATRIX_POS-'), sg.Button("Negativas", k='-MATRIX_NEG-')]],
        expand_x=True, key='-QUESTIONS_FRAME-'
    )

    # Frame para seleccionar el modo de análisis
    aggregation_options = [
        ("Matriz de Elecciones (Estándar)", "real_actions"),
        ("Matriz de Relaciones Completas (CIVSOC)", "civsoc_matrix"),
        ("Meta-Percepción (SELF)", "meta_perceptions"),
        ("Análisis de Precisión", "accuracy_analysis"),
    ]
    participant_options = sociogram_utils.get_participant_options(app_state, app_data, hutils)
    aggregation_frame = sg.Frame("Fuente de Datos y Agregación", [
        [sg.Text("Modo de Análisis:", size=(25,1)), sg.Combo([opt[0] for opt in aggregation_options], default_value=aggregation_options[0][0], key='-MATRIX_AGGREGATION_MODE-', readonly=True, enable_events=True, expand_x=True)],
        [sg.Text("Miembro Foco / Perceptor:", size=(25,1)), sg.Combo([p[0] for p in participant_options if p[1] is not None], key='-MATRIX_PERCEIVER-', readonly=True, disabled=True)]
    ], expand_x=True)

    # Panel de estado
    status_panel = sg.Frame("Estado",
        [[sg.Multiline("Seleccione un modo, las preguntas y haga clic en 'Generar y Abrir Matriz'.",
                       key='-MATRIX_STATUS-', size=(80, 4), disabled=True, autoscroll=True, background_color='white', text_color='black')]],
        expand_x=True
    )
    
    # --- Ensamblaje del Layout Final ---
    layout = [
        [sg.Text(f"Matriz Sociométrica: {group_name} ({institution_name})", font=("Helvetica", 16))],
        [aggregation_frame],
        [questions_frame], # El único frame de selección, siempre visible
        [sg.Checkbox("Permitir auto-elección en la diagonal (solo modo estándar)", key='-MATRIX_ALLOW_SELF-', default=False)],
        [sg.Button("Generar y Abrir Matriz", key='-MATRIX_UPDATE-')],
        [status_panel],
        [sg.VPush()],
        [sg.HorizontalSeparator()],
        [sg.Button("Generar PDF", key='-MATRIX_PDF-'), sg.Push(), sg.Button("Volver", key='-BACK_TO_GROUPS-')]
    ]
    
    return [[sg.Column(layout, expand_x=True, expand_y=True)]]

def create_layout_diana(institution_name, group_name, relation_options):
    """
    Crea el layout para la ventana de Análisis Gráfico en Diana.
    """
    # --- Columna Izquierda: Controles ---
    aggregation_options = [
        "Diana de Afinidad (Popularidad)",
        "Diana de Distancia (CIVSOC)",
        "Diana de Precisión (Global)",
        "Red de Meta-Percepción (SELF)",
    ]
    participant_options = sociogram_utils.get_participant_options(app_state, app_data, hutils)

    analysis_frame = sg.Frame("Modo de Análisis", [
        [sg.Combo(aggregation_options, default_value=aggregation_options[0], key='-DIANA_AGGREGATION_MODE-', readonly=True, enable_events=True, expand_x=True)],
        [sg.Text("Miembro Foco (para CIVSOC):", size=(25,1))],
        [sg.Combo([p[0] for p in participant_options if p[1] is not None], key='-DIANA_PERCEIVER-', readonly=True, disabled=True, expand_x=True)]
    ], expand_x=True)

    q_layout_rows = [[sg.Checkbox(opt['label'], key=f"-DIANA_Q__{opt['data_key']}__", default=True)] for opt in relation_options] if relation_options else [[sg.Text("No hay preguntas.")]]
    questions_frame = sg.Frame("Preguntas a Incluir", [
        [sg.Column(q_layout_rows, size=(380, 150), scrollable=True, vertical_scroll_only=True)],
        [sg.Button("Todas", k='-DIANA_ALL-'), sg.Button("Ninguna", k='-DIANA_NONE-'), sg.Button("Positivas", k='-DIANA_POS-'), sg.Button("Negativas", k='-DIANA_NEG-')]
    ], expand_x=True)

    options_frame = sg.Frame("Opciones de Visualización", [
        [sg.Checkbox("Mostrar Líneas de Elección (solo en modo Afinidad)", key='-DIANA_SHOW_LINES-', default=True)]
    ], expand_x=True)

    left_column = sg.Column([
        [analysis_frame],
        [questions_frame],
        [options_frame],
        [sg.Button("Generar/Actualizar Diana", key='-DIANA_GENERATE-')],
        [sg.VPush()] # Empuja los botones de abajo al fondo
    ], vertical_alignment='top')

    # --- Columna Derecha: Visualización ---
    image_viewer = sg.Column([
        [sg.Image(key='-DIANA_IMAGE-', background_color='white')]
    ], key='-DIANA_IMAGE_CONTAINER-', justification='center', expand_x=True, expand_y=True, background_color='white')

    # --- Layout Principal ---
    layout = [
        [sg.Text(f"Análisis Gráfico en Diana: {group_name} ({institution_name})", font=("Helvetica", 16))],
        [sg.HorizontalSeparator()],
        [left_column, sg.VSeperator(), sg.Column([[image_viewer]], expand_x=True, expand_y=True)],
        [sg.HorizontalSeparator()],
        [
            sg.Text("Zoom:", pad=((10,0),0)),
            sg.Slider(range=(25, 200), default_value=100, orientation='h', size=(30, 15), key='-DIANA_ZOOM_SLIDER-', enable_events=True),
            sg.Text("100%", key='-DIANA_ZOOM_TEXT-'),
            sg.Push(),
            sg.Button("Guardar Imagen (PNG)", key='-DIANA_SAVE-', disabled=True),
            sg.Button("Volver a Grupos", key='-BACK_TO_GROUPS-')
        ]
    ]

    return layout

def create_layout_sociogram(institution_name, group_name, relation_options, participant_options):
    """
    Versión FINAL. Incluye todos los controles de la interfaz, incluyendo el resaltado de líderes
    y el coloreado por rol de "Solo Reciben".
    """
    log_message(f"Creando layout de Sociograma para: {group_name}", 'info')
    
    # --- Columna Izquierda (sin cambios) ---
    checkboxes_layout = [[sg.Checkbox(opt['label'], default=True, key=f"-SOC_REL__{opt['data_key']}__")] for opt in relation_options] if relation_options else [[sg.Text("No hay relaciones para seleccionar.")]]
    relation_frame = sg.Frame("Preguntas a Incluir", [[sg.Column(checkboxes_layout, size=(300, 150), scrollable=True, vertical_scroll_only=True)], [sg.Button("Todas", key='-SOC_SEL_ALL-'), sg.Button("Ninguna", key='-SOC_SEL_NONE-'), sg.Button("Positivas", key='-SOC_SEL_POS-'), sg.Button("Negativas", key='-SOC_SEL_NEG-')]], expand_y=True)
    filter_frame = sg.Frame("Filtro por Sexo", [[sg.Text("Nodos (Miembros):")], [sg.Radio("Todos", "GENDER_FILTER", default=True, key='-SOC_GENDER_ALL-'), sg.Radio("Masculino", "GENDER_FILTER", key='-SOC_GENDER_M-'), sg.Radio("Femenino", "GENDER_FILTER", key='-SOC_GENDER_F-')], [sg.HorizontalSeparator()], [sg.Text("Aristas (Conexiones):")], [sg.Radio("Todas", "CONN_GENDER", default=True, key='-SOC_CONN_ALL-'), sg.Radio("Mismo Sexo", "CONN_GENDER", key='-SOC_CONN_SAME-'), sg.Radio("Diferente Sexo", "CONN_GENDER", key='-SOC_CONN_DIFF-')]])
    aggregation_options = [("Red Real (Acciones Directas)", "real_actions"), ("Red de Relaciones Completas (CIVSOC)", "civsoc_matrix"), ("Red de Meta-Percepción (SELF)", "meta_perceptions"), ("Análisis de Precisión (Global)", "accuracy_analysis")]
    aggregation_frame = sg.Frame("Fuente de Datos y Agregación", [[sg.Text("Modo de Red:", size=(28,1)), sg.Combo([opt[0] for opt in aggregation_options], default_value=aggregation_options[0][0], key='-SOC_AGGREGATION_MODE-', readonly=True, enable_events=True, expand_x=True, tooltip="Define el tipo de análisis a visualizar.")], [sg.Text("Perceptor (para Foco):", size=(28,1)), sg.Combo([p[0] for p in participant_options if p[1] is not None], key='-SOC_PERCEIVER-', readonly=True, disabled=True, expand_x=True, tooltip="Este campo se activa solo para modos que requieren un foco individual.")]], expand_x=True)
    left_col_layout = sg.Column([[relation_frame], [filter_frame], [aggregation_frame]], vertical_alignment='top')

    # --- INICIO DE LA MODIFICACIÓN: Columna Derecha ---

    style_frame = sg.Frame("Estilos y Etiquetas", [
        # Se añade la opción "Anónimo"
        [sg.Text("Etiquetas Nodos:"), sg.Combo(['Iniciales', 'Nombre Apellido', 'Anónimo'], default_value='Iniciales', key='-SOC_LABEL_MODE-', readonly=True, size=(20,1))],
        [sg.Checkbox("Estilo de Arista Recíproca", default=True, key='-SOC_RECIPROCAL_STYLE-')],
        [sg.Checkbox("Mostrar Nodos Aislados", default=True, key='-SOC_SHOW_ISOLATES-')],
        [sg.Checkbox("Mostrar solo Miembros Activos", key='-SOC_ACTIVE_ONLY-')]
    ])
    
    color_role_frame = sg.Frame("Coloreado por Rol", [
        # Se añade el nuevo checkbox
        [sg.Checkbox("Solo Reciben / Auto-eligen", key='-SOC_COLOR_RECEIVERS-')],
        [sg.Checkbox("En Relación Recíproca", key='-SOC_COLOR_RECIP_NODES-')]
    ])
    
    analysis_frame = sg.Frame("Análisis y Resaltado", [
        [sg.Text("Foco en un Participante:")],
        [sg.Combo([p[0] for p in participant_options], default_value=participant_options[0][0] if participant_options else '', size=(25, 1), key='-SOC_FOCUS_PARTICIPANT-', readonly=True)],
        [sg.Radio("Todas Conexiones", "FOCUS_MODE", default=True, key='-SOC_FOCUS_ALL-'), sg.Radio("Salientes", "FOCUS_MODE", key='-SOC_FOCUS_OUT-'), sg.Radio("Entrantes", "FOCUS_MODE", key='-SOC_FOCUS_IN-')],
        [sg.HorizontalSeparator()],
        # Se añade la sección de Resaltar Líderes
        [sg.Text("Resaltar Líderes (por elecciones positivas):")],
        [sg.Radio("Ninguno", "HIGHLIGHT", default=True, key='-SOC_HL_NONE-', enable_events=True), 
         sg.Radio("Top N", "HIGHLIGHT", key='-SOC_HL_TOPN-', enable_events=True), 
         sg.Radio("K-ésimo", "HIGHLIGHT", key='-SOC_HL_KTH-', enable_events=True)],
        [sg.Text("Valor (N o K):", size=(12,1)), sg.Input("1", size=(5,1), key='-SOC_HL_VALUE-', disabled=True)],
    ])

    right_col_layout = sg.Column([[style_frame], [color_role_frame], [analysis_frame]], vertical_alignment='top')
    # --- FIN DE LA MODIFICACIÓN ---
    
    # --- Ensamblaje Final (sin cambios) ---
    top_controls_layout = [[left_col_layout, sg.VSeperator(), right_col_layout]]
    info_layout = [[sg.Text("1. Selecciona el 'Modo de Red' y los filtros deseados.")], [sg.Text("2. Haz clic en 'Generar y Ver Sociograma'. Se abrirá una nueva ventana con el grafo interactivo.")], [sg.Text("3. CIERRA LA VENTANA DEL SOCIOGRAMA para volver a esta pantalla.")]]
    main_content = [[sg.Text(f"Sociograma Interactivo: {group_name} ({institution_name})", font=("Helvetica", 16))], [sg.Frame("Opciones de Visualización", top_controls_layout, expand_x=True)], [sg.Frame("Uso", info_layout, expand_x=True)], [sg.HorizontalSeparator()], [sg.Button("Generar y Ver Sociograma", key='-SOC_GENERATE_INTERACTIVE-'), sg.Push(), sg.Button("Volver a Grupos", key='-BACK_TO_GROUPS-')]]
    layout = [[sg.Column(main_content, scrollable=True, vertical_scroll_only=True, expand_x=True, expand_y=True)]]
    return layout

def create_layout_accuracy_report(institution_name, group_name):
    """Crea el layout para la ventana del reporte de precisión de percepción."""
    
    headings = ["Miembro (Ego)", "Categoría", "Aciertos", "Errores (Falsos Positivos)", "Omisiones (Falsos Negativos)", "Precisión"]
    col_widths = [25, 15, 25, 25, 25, 10]

    main_content = [
        [sg.Text("Reporte de Precisión de Meta-Percepción", font=("Helvetica", 16))],
        [sg.Text(f"Institución: {institution_name} | Grupo: {group_name}")],
        [sg.Table(
            values=[[]], # Se llenará dinámicamente
            headings=headings,
            key='-ACCURACY_TABLE-',
            auto_size_columns=False,
            col_widths=col_widths,
            justification='left',
            num_rows=20,
            expand_x=True,
            expand_y=True
        )],
        [sg.Push(), sg.Button("Cerrar", key='-CLOSE-')]
    ]
    
    layout = [[sg.Column(main_content, expand_x=True, expand_y=True)]]
    return layout

# --- BLOQUE 4 DE 10: LAYOUT DE GESTIÓN DE CSV ---

def create_layout_csv_management():
    """
    Crea la ventana completa para la gestión de datos CSV (Importar/Exportar).
    Incluye TODAS las opciones de importación granular.
    """
    
    # --- Sección de Entidades a Importar ---
    entities_options_layout = [
        [sg.Text("¿Qué entidades base deseas importar/crear?", font=("Helvetica", 10, "bold"))],
        [sg.Checkbox("Instituciones", default=True, key='-CSV_OPT_INST-', 
                     tooltip="Crea nuevas instituciones si no existen en los datos.")],
        [sg.Checkbox("Grupos", default=True, key='-CSV_OPT_GRP-', 
                     tooltip="Crea nuevos grupos en sus instituciones si no existen.")],
        [sg.Checkbox("Miembros (desde columna 'Nombre y Apellido')", default=True, key='-CSV_OPT_MEMB_NOMINATORS-', 
                     tooltip="Crea perfiles para los miembros listados en la columna principal 'Nombre y Apellido' (los nominadores).")]
    ]

    # --- Sección de Gestión de Preguntas ---
    question_options_layout = [
        [sg.Text("¿Cómo gestionar las Definiciones de Preguntas?", font=("Helvetica", 10, "bold"))],
        [sg.Checkbox("Importar/Actualizar Definiciones de Preguntas", default=True, key='-CSV_OPT_DEFS-', enable_events=True,
                     tooltip="Permite que el CSV modifique las preguntas del grupo. Si se desmarca, las preguntas deben coincidir exactamente.")],
        
        [sg.Checkbox("Solo agregar preguntas nuevas (no sobreescribir existentes)",
                     default=True, key='-CSV_OPT_ADD_Q_ONLY-', pad=((20, 0), (0, 0)),
                     tooltip="MARCADO: Solo añade preguntas del CSV que no existan en el grupo.\nDESMARCADO: Reemplaza TODAS las preguntas del grupo con las del CSV.",
                     disabled=False)],

        [sg.Checkbox("Permitir auto-selección en preguntas NUEVAS", default=False, key='-CSV_OPT_SELF-', pad=((20, 0), (0, 0)),
                     tooltip="Si se crean preguntas nuevas desde el CSV, esta opción define si los miembros pueden elegirse a sí mismos en ellas.")],

        [sg.Checkbox("Ampliar 'max_selections' si el CSV tiene más respuestas", default=False, key='-CSV_OPT_EXPAND-', pad=((20, 0), (0, 5)),
                     tooltip="Si una pregunta existente permite 2 respuestas pero el CSV tiene 5, esta opción actualizará la pregunta para permitir 5.")]
    ]

    # --- Sección de Gestión de Respuestas ---
    responses_options_layout = [
        [sg.Text("¿Cómo gestionar las Respuestas del Cuestionario?", font=("Helvetica", 10, "bold"))],
        [sg.Checkbox("Importar Respuestas del Cuestionario", default=True, key='-CSV_OPT_RESPS-', enable_events=True,
                     tooltip="Importa las elecciones de cada miembro según las preguntas.")],
        
        [sg.Checkbox("Crear miembros MENCIONADOS si no existen", default=True, key='-CSV_OPT_CREATE_MENTIONED-', pad=((20, 0), (0, 5)),
                     tooltip="Si un miembro es elegido en una respuesta pero no existe, se creará un perfil básico para él.\nDesmarcar si solo quieres considerar elecciones a miembros ya registrados.",
                     disabled=False)] 
    ]
    
    import_layout = [
        [sg.Text("Importar desde Archivo CSV", font=("Helvetica", 12, "bold"))],
        [sg.Text("Selecciona el archivo CSV:"), sg.Input(key='-CSV_IN_PATH-'), sg.FileBrowse(file_types=(("CSV Files", "*.csv"),))],
        [sg.Frame("1. Entidades a Crear", entities_options_layout, expand_x=True)],
        [sg.Frame("2. Definiciones de Preguntas", question_options_layout, expand_x=True)],
        [sg.Frame("3. Respuestas", responses_options_layout, expand_x=True)],
        [sg.Button("Procesar Archivo CSV", key='-CSV_PROCESS-')]
    ]
    
    # --- Sección de Exportación ---
    export_layout = [
        [sg.Text("Exportar a Archivo CSV", font=("Helvetica", 12, "bold"))],
        [sg.Text("Selecciona los grupos a exportar:")],
        [sg.Listbox(values=[], size=(60, 10), key='-CSV_OUT_GROUPS-', select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, expand_x=True, expand_y=True)],
        [sg.Button("Cargar Todos los Grupos", key='-CSV_LOAD_GROUPS-')],
        [sg.Button("Generar CSV de Grupos Seleccionados", key='-CSV_EXPORT-')]
    ]
    
    # --- Sección de Ayuda ---
    help_layout = [[sg.Button("Ver Instrucciones (PDF)", key='-PDF_INSTRUCTIONS-')]]

    # --- Layout Principal de la Ventana ---
    main_content = [
        [sg.Text("Gestión de Datos CSV", font=("Helvetica", 16))],
        [sg.Frame("Importar", import_layout, expand_x=True)],
        [sg.Frame("Exportar", export_layout, expand_x=True, expand_y=True)],
        [sg.Frame("Ayuda", help_layout, expand_x=True)],
        [sg.Push(), sg.Button("Volver", key='-BACK-')]
    ]
    
    layout = [[sg.Column(main_content, expand_x=True, expand_y=True, scrollable=True)]]
    return layout

# --- Fin del Bloque 3 (en el archivo original) ---

# --- BLOQUE 5 DE 10: FUNCIONES AUXILIARES Y VENTANAS DE FORMULARIOS/CSV ---
# =============================================================================
#  BLOQUE 4.1: Función Auxiliar y Formularios (movido aquí, antes eran Bloques 4.1 y 4.2)
# =============================================================================

def draw_figure(canvas, figure):
    """
    Función auxiliar para dibujar una figura de Matplotlib en un Canvas de Tkinter.
    """
    for item in canvas.winfo_children():
        item.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

# --- BLOQUE 4.2: Ventana de Gestión de CSV ---

def window_csv_management(ui_context, tk_parent_window):
    """
    Lanza y gestiona la ventana de Importación/Exportación de CSV, incluyendo la lógica
    para todos los checkboxes de importación granular. La ventana inicia maximizada.
    
    AHORA ACEPTA tk_parent_window para pasarlo a los diálogos de Tkinter.
    """
    layout = create_layout_csv_management()
    window = sg.Window("Gestión de Datos CSV", layout, modal=True, finalize=True, resizable=True)
    window.maximize()
    
    data_was_imported = False
    
    def load_all_groups():
        all_groups = [f"{inst} / {group['name']}" for inst, groups in app_data.classes_data.items() for group in groups]
        window['-CSV_OUT_GROUPS-'].update(values=sorted(all_groups))

    load_all_groups()

    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-BACK-'):
            break

        if event == '-CSV_OPT_DEFS-':
            is_enabled = values['-CSV_OPT_DEFS-']
            window['-CSV_OPT_ADD_Q_ONLY-'].update(disabled=not is_enabled)
            window['-CSV_OPT_SELF-'].update(disabled=not is_enabled)
            window['-CSV_OPT_EXPAND-'].update(disabled=not is_enabled)
        
        if event == '-CSV_OPT_RESPS-':
            is_enabled = values['-CSV_OPT_RESPS-']
            window['-CSV_OPT_CREATE_MENTIONED-'].update(disabled=not is_enabled)
            
        elif event == '-PDF_INSTRUCTIONS-':
            pdf_bytes, result_or_error = pdf_generator.generate_import_instructions_pdf()
            if pdf_bytes:
                try:
                    # Guardar y abrir el PDF
                    save_path = sg.popup_get_file("Guardar Manual de Usuario", save_as=True, default_extension=".pdf", default_path=result_or_error, file_types=(("PDF Files", "*.pdf"),))
                    if save_path:
                        with open(save_path, 'wb') as f: f.write(pdf_bytes)
                        sg.popup_ok(f"El manual de usuario ha sido guardado en:\n\n{save_path}\n\nSe intentará abrir a continuación.", title="Manual Generado")
                        webbrowser.open_new(f"file://{os.path.abspath(save_path)}")
                except Exception as e: sg.popup_error(f"Error al guardar o abrir el manual:\n{e}")
            else: sg.popup_error(f"No se pudo generar el PDF del manual:\n{result_or_error}")

        elif event == '-CSV_PROCESS-':
            filepath = values['-CSV_IN_PATH-']
            if not filepath or not os.path.exists(filepath):
                sg.popup_error("Por favor, selecciona un archivo CSV válido."); continue
            
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f: csv_content = f.read()
                
                import_options = {
                    'import_escuelas': values['-CSV_OPT_INST-'], 'import_grupos': values['-CSV_OPT_GRP-'], 
                    'import_miembros_nominadores': values['-CSV_OPT_MEMB_NOMINATORS-'], 'import_defs_preguntas': values['-CSV_OPT_DEFS-'], 
                    'import_respuestas': values['-CSV_OPT_RESPS-'], 'add_new_questions_only': values['-CSV_OPT_ADD_Q_ONLY-'],
                    'allow_self_selection_new': values['-CSV_OPT_SELF-'], 'expand_max_selections': values['-CSV_OPT_EXPAND-'],
                    'create_mentioned_members': values['-CSV_OPT_CREATE_MENTIONED-']
                }
                
                final_result = hcsv.run_full_csv_import_flow(tk_parent_window, csv_content, import_options, ui_context)
                
                if final_result and final_result.get('status') == 'success':
                    sg.popup_scrolled(final_result['message'], title="Resultado de Importación")
                    data_was_imported = True
                elif final_result and final_result.get('status') == 'error':
                    sg.popup_error(final_result.get('message', 'Ocurrió un error.'))

            except Exception as e:
                sg.popup_error(f"Error al procesar el archivo CSV: {e}\n\n{traceback.format_exc()}")
        
        elif event == '-CSV_EXPORT-':
            selected_groups_str = values['-CSV_OUT_GROUPS-']
            if not selected_groups_str: sg.popup_error("Por favor, selecciona al menos un grupo para exportar."); continue
            groups_to_export = [tuple(s.split(' / ')) for s in selected_groups_str]
            success, data_to_write = hcsv.handle_prepare_data_for_csv_export(groups_to_export)
            if success:
                save_path = sg.popup_get_file("Guardar Exportación CSV", save_as=True, default_extension=".csv", file_types=(("CSV Files", "*.csv"),))
                if save_path:
                    try:
                        # La única corrección es cambiar 'utf-8' a 'utf-8-sig'
                        with open(save_path, 'w', newline='', encoding='utf-8-sig') as f:
                            writer = csv.writer(f)
                            writer.writerows(data_to_write)
                        sg.popup("Exportación completada exitosamente.")
                    except Exception as e:
                        sg.popup_error(f"Error al guardar el archivo: {e}")
            else: sg.popup_error(data_to_write[0][0])
            
        elif event == '-CSV_LOAD_GROUPS-':
            load_all_groups()
    
    window.close()
    return data_was_imported

# --- BLOQUE 6 DE 10: FUNCIONES DE VENTANAS DE ANÁLISIS (CUESTIONARIO, PREGUNTAS, SOCIOGRAMA) ---
# =============================================================================
#  BLOQUE 4.3: Ventanas de Cuestionario y Gestión de Preguntas
# =============================================================================

def window_question_management(institution_name, group_name):
    """
    Versión FINAL. Gestiona el formulario de preguntas con la lógica separada para
    'type' (estructural) y 'category' (temática), leyendo y guardando ambos campos
    correctamente al crear o modificar preguntas.
    """
    app_state['current_institution_viewing_groups'] = institution_name
    app_state['current_group_viewing_questions'] = group_name
    layout = create_layout_question_management(institution_name, group_name)
    window = sg.Window("Gestión de Preguntas", layout, modal=True, finalize=True, resizable=True)
    window.maximize()
    
    def refresh_list():
        questions = hq.get_question_definitions_for_group(institution_name, group_name)
        display_list = []
        for qid, q in questions:
            text = q.get('text', 'Sin texto')
            display_list.append(f"[{q.get('order', '?')}] {text} (ID: {qid})")
        window['-Q_LIST-'].update(values=display_list, set_to_index=[])
        window['-MOD_Q-'].update(disabled=True); window['-DEL_Q-'].update(disabled=True)
    
    refresh_list()
    return_value = 'reload_previous' 
    
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == '-BACK_TO_Q-':
            break
        
        selected_q_display = values.get('-Q_LIST-')[0] if values.get('-Q_LIST-') else None
        form_is_visible = window['-FORM_Q_FRAME-'].visible
        window['-NEW_Q-'].update(disabled=form_is_visible)
        window['-MOD_Q-'].update(disabled=form_is_visible or not selected_q_display)
        window['-DEL_Q-'].update(disabled=form_is_visible or not selected_q_display)

        if event == '-Q_LIST-':
             window['-FORM_Q_FRAME-'].update(visible=False)

        elif event == '-NEW_Q-':
            app_state['form_q_mode'] = 'new'
            current_defs_tuples = hq.get_question_definitions_for_group(institution_name, group_name)
            next_order = max([q_def.get('order', -1) for _, q_def in current_defs_tuples]) + 1 if current_defs_tuples else 0
            
            window['-FORM_Q_TITLE-'].update("Nueva Pregunta")
            for key in ['-FORM_Q_ID-', '-FORM_Q_TEXT-', '-FORM_Q_CATEGORY-', '-FORM_Q_DK-']: window[key].update('')
            window['-FORM_Q_ORDER-'].update(next_order); window['-FORM_Q_MAX-'].update('1')
            window['-FORM_Q_POL_POS-'].update(True); window['-FORM_Q_SELF-'].update(False)
            window['-FORM_Q_IS_META_PERCEPTION-'].update(False)
            window['-FORM_Q_FRAME-'].update(visible=True)

        elif event == '-MOD_Q-' and selected_q_display:
            app_state['form_q_mode'] = 'modify'
            try:
                q_id = re.search(r'\(ID: (.*?)\)$', selected_q_display).group(1)
            except (IndexError, AttributeError):
                sg.popup_error("No se pudo identificar la pregunta seleccionada."); continue
            
            all_defs = dict(hq.get_question_definitions_for_group(institution_name, group_name))
            original_data = all_defs.get(q_id)

            if original_data:
                app_state['original_q_id'] = q_id
                window['-FORM_Q_TITLE-'].update(f"Modificar Pregunta (ID: {q_id})")
                window['-FORM_Q_ID-'].update(q_id)
                window['-FORM_Q_TEXT-'].update(original_data.get('text', ''))
                
                # --- LÍNEA CORREGIDA ---
                # Ahora lee el campo 'category' en lugar de 'type'
                window['-FORM_Q_CATEGORY-'].update(original_data.get('category', ''))
                
                window['-FORM_Q_DK-'].update(original_data.get('data_key', ''))
                window['-FORM_Q_ORDER-'].update(original_data.get('order', '99'))
                window['-FORM_Q_MAX-'].update(original_data.get('max_selections', '1'))
                window['-FORM_Q_POL_POS-'].update(original_data.get('polarity', 'positive') == 'positive')
                window['-FORM_Q_POL_NEG-'].update(original_data.get('polarity') == 'negative')
                window['-FORM_Q_SELF-'].update(original_data.get('allow_self_selection', False))
                
                is_meta = original_data.get('type') == '[Meta-Percepción]'
                window['-FORM_Q_IS_META_PERCEPTION-'].update(is_meta)
                
                window['-FORM_Q_FRAME-'].update(visible=True)

        elif event == '-DEL_Q-' and selected_q_display:
            try: q_id = re.search(r'\(ID: (.*?)\)$', selected_q_display).group(1)
            except (IndexError, AttributeError): sg.popup_error("No se pudo identificar la pregunta."); continue
            if sg.popup_yes_no(f"¿Eliminar '{q_id}' y sus respuestas asociadas?", title="Confirmar") == 'Yes':
                success, msg = hq.handle_delete_question(institution_name, group_name, q_id)
                sg.popup(msg)
                if success: refresh_list()

        elif event == '-FORM_Q_CANCEL-':
            window['-FORM_Q_FRAME-'].update(visible=False)

        elif event == '-FORM_Q_SAVE-':
            try:
                is_meta_perception = values['-FORM_Q_IS_META_PERCEPTION-']
                
                # --- INICIO DE LA LÓGICA CORREGIDA ---
                q_data = {
                    'id': values['-FORM_Q_ID-'], 
                    'text': values['-FORM_Q_TEXT-'],
                    
                    # 1. El 'type' (Tipo Estructural) se asigna basado en el checkbox.
                    'type': '[Meta-Percepción]' if is_meta_perception else '[Acción Real]',
                    
                    # 2. La 'category' (Categoría Temática) viene del campo de texto.
                    'category': values['-FORM_Q_CATEGORY-'],
                    
                    'data_key': values['-FORM_Q_DK-'], 
                    'polarity': 'positive' if values['-FORM_Q_POL_POS-'] else 'negative', 
                    'order': int(values['-FORM_Q_ORDER-']), 
                    'max_selections': int(values['-FORM_Q_MAX-']), 
                    'allow_self_selection': values['-FORM_Q_SELF-'],
                    
                    # 3. Los flags internos se mantienen consistentes.
                    'is_cognitive': is_meta_perception,
                    'perceived_nominator': '[SELF]' if is_meta_perception else None
                }
                # --- FIN DE LA LÓGICA CORREGIDA ---
                
                if app_state.get('form_q_mode') == 'new':
                    success, msg = hq.handle_add_question(institution_name, group_name, q_data)
                else:
                    success, msg = hq.handle_modify_question(institution_name, group_name, app_state.get('original_q_id'), q_data)
                
                sg.popup(msg)
                if success:
                    window['-FORM_Q_FRAME-'].update(visible=False)
                    refresh_list()
            except ValueError: 
                sg.popup_error("'Orden' y 'Máx. Selecciones' deben ser números enteros.")
            except Exception as e: 
                sg.popup_error(f"Error inesperado al guardar: {e}")
    
    window.close()
    return return_value

def window_questionnaire(institution_name, group_name, member_name):
    q_data = hquest.get_questionnaire_data_for_member(institution_name, group_name, member_name, app_data_ref=app_data)
    layout = create_layout_questionnaire(q_data, member_name, institution_name, group_name)
    window = sg.Window("Cuestionario", layout, finalize=True, resizable=True)
    window.maximize()
    action, data = 'open_members', {'school': institution_name, 'class_name': group_name}

    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-BACK_TO_MEMBERS-'):
            break

        if event == sg.WIN_CLOSED:
            action = 'exit'
            break
        
        if event == '-SAVE_Q-':
            responses = {}
            for q in q_data.get('questions', []):
                selections = [values.get(f"-Q_{q['data_key']}_{i}-") for i in range(q['max_selections']) if values.get(f"-Q_{q['data_key']}_{i}-") and values.get(f"-Q_{q['data_key']}_{i}-") != 'Seleccionar']
                responses[q['data_key']] = selections
            success, msg = hquest.save_questionnaire_responses(institution_name, group_name, member_name, responses)
            sg.popup(msg)

        elif event == '-PDF_TEMPLATE_Q-':
            pdf_bytes, filename = pdf_generator.generate_class_questionnaire_template_pdf(institution_name, group_name)
            if pdf_bytes:
                save_path = sg.popup_get_file('Guardar Plantilla', save_as=True, default_extension=".pdf", default_path=filename)
                if save_path:
                    try:
                        with open(save_path, 'wb') as f: f.write(pdf_bytes)
                    except Exception as e: sg.popup_error(f"Error al guardar: {e}")
            else: sg.popup_error("No se pudo generar el PDF.")
        
        elif event == '-MANAGE_Q-':
            window.hide()
            exit_signal = window_question_management(institution_name, group_name)
            window.un_hide()
            if exit_signal == 'exit':
                action = 'exit'
                break
            
            sg.popup("Las preguntas han cambiado. El cuestionario se recargará.")
            action = 'open_questionnaire'
            data = {'school': institution_name, 'class_name': group_name, 'member': member_name}
            break
            
    window.close()
    return action, data

# En Red_Sociograma_App.py

def window_sociogram(institution_name, group_name):
    """
    Versión FINAL, COMPLETA Y CON LOGS. Gestiona la ventana del sociograma.
    - Incluye todos los controles de la interfaz, como el resaltado de líderes.
    - Maneja todos los modos de red (CIVSOC, Precisión Global, etc.).
    - Realiza validaciones de preguntas específicas para cada modo.
    - Utiliza el navegador web predeterminado para la visualización.
    """
    app_state['current_group_viewing_members'] = {'school': institution_name, 'class_name': group_name}
    participant_options = sociogram_utils.get_participant_options(app_state, app_data, hutils)
    relation_options = sociogram_utils.get_relation_options(institution_name, group_name, app_data)
    
    layout = create_layout_sociogram(institution_name, group_name, relation_options, participant_options)
    window = sg.Window("Lanzador de Sociograma Interactivo", layout, finalize=True, resizable=True)
    window.maximize()
    
    action, data = 'open_groups', institution_name

    aggregation_map = {
        "Red Real (Acciones Directas)": "real_actions",
        "Red de Relaciones Completas (CIVSOC)": "civsoc_matrix",
        "Red de Meta-Percepción (SELF)": "meta_perceptions",
        "Análisis de Precisión (Global)": "accuracy_analysis",
    }
    all_defs = app_data.get_class_question_definitions(institution_name, group_name)

    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-BACK_TO_GROUPS-'):
            break
        if event == sg.WIN_CLOSED:
            action = 'exit'
            break

        if event == '-SOC_AGGREGATION_MODE-':
            # El perceptor/foco no es necesario para ningún modo de sociograma en la versión actual.
            is_perceiver_needed = False 
            window['-SOC_PERCEIVER-'].update(disabled=not is_perceiver_needed, value='')

        if event in ('-SOC_HL_TOPN-', '-SOC_HL_KTH-'):
            window['-SOC_HL_VALUE-'].update(disabled=False)
        elif event == '-SOC_HL_NONE-':
            window['-SOC_HL_VALUE-'].update(disabled=True)

        if event in ('-SOC_SEL_ALL-', '-SOC_SEL_NONE-', '-SOC_SEL_POS-', '-SOC_SEL_NEG-'):
            for opt in relation_options:
                key = f"-SOC_REL__{opt['data_key']}__"
                if key in window.key_dict:
                    if event == '-SOC_SEL_ALL-': window[key].update(True)
                    elif event == '-SOC_SEL_NONE-': window[key].update(False)
                    elif event == '-SOC_SEL_POS-': window[key].update(opt['polarity'] == 'positive')
                    elif event == '-SOC_SEL_NEG-': window[key].update(opt['polarity'] == 'negative')
        
        if event == '-SOC_GENERATE_INTERACTIVE-':
            log_message("[DEBUG] Evento '-SOC_GENERATE_INTERACTIVE-' detectado.", "debug")
            sg.popup_quick_message("Procesando red...", background_color='lightblue')

            aggregation_mode_text = values['-SOC_AGGREGATION_MODE-']
            aggregation_mode = aggregation_map.get(aggregation_mode_text, 'real_actions')
            selected_keys = [k.split('__')[1] for k, v in values.items() if k.startswith('-SOC_REL__') and v]
            perceiver_name = values['-SOC_PERCEIVER-']

            is_valid, error_msg = True, ""
            selected_defs = [d for d in all_defs.values() if d.get('data_key') in selected_keys]
            if not selected_keys:
                is_valid, error_msg = False, "Debe seleccionar al menos una pregunta."
            
            if is_valid:
                if aggregation_mode == 'civsoc_matrix':
                    counts = {'ap': sum(1 for d in selected_defs if d.get('type')=='[Acción Real]' and d.get('polarity')=='positive'), 'an': sum(1 for d in selected_defs if d.get('type')=='[Acción Real]' and d.get('polarity')=='negative'), 'mp': sum(1 for d in selected_defs if d.get('type')=='[Meta-Percepción]' and d.get('polarity')=='positive'), 'mn': sum(1 for d in selected_defs if d.get('type')=='[Meta-Percepción]' and d.get('polarity')=='negative')}
                    if len(selected_defs) != 4 or not all(c == 1 for c in counts.values()):
                        is_valid, error_msg = False, "Para el modo CIVSOC, debe seleccionar exactamente 4 preguntas: una para cada combinación de Acción/Meta y Positiva/Negativa."
                elif aggregation_mode == 'accuracy_analysis':
                    if len(selected_defs) != 2:
                        is_valid, error_msg = False, "Para el Análisis de Precisión, debe seleccionar exactamente 2 preguntas: una de '[Acción Real]' y una de '[Meta-Percepción]'."
                    else:
                        action_q = next((d for d in selected_defs if d.get('type') == '[Acción Real]'), None)
                        meta_q = next((d for d in selected_defs if d.get('type') == '[Meta-Percepción]'), None)
                        if not action_q or not meta_q:
                            is_valid, error_msg = False, "La selección es incorrecta. Debe incluir una pregunta de '[Acción Real]' Y una de '[Meta-Percepción]'."
                        elif action_q.get('polarity') != meta_q.get('polarity'):
                            is_valid, error_msg = False, "Las polaridades no coinciden. Ambas preguntas deben ser positivas o ambas deben ser negativas."

            if not is_valid:
                sg.popup_error(f"Error de Selección:\n\n{error_msg}", title="Configuración Incorrecta")
                log_message(f"[DEBUG] Validación fallida: {error_msg}", "error")
                continue
            
            val_str = values.get('-SOC_HL_VALUE-', '1')
            highlight_val = int(val_str) if val_str.isdigit() else 1

            params = {
                'node_gender_filter': 'Masculino' if values.get('-SOC_GENDER_M-') else 'Femenino' if values.get('-SOC_GENDER_F-') else 'Todos',
                'label_display_mode': 'iniciales' if values.get('-SOC_LABEL_MODE-') == 'Iniciales' else 'anónimo' if values.get('-SOC_LABEL_MODE-') == 'Anónimo' else 'nombre_apellido',
                'connection_gender_type': 'mismo_genero' if values.get('-SOC_CONN_SAME-') else 'diferente_genero' if values.get('-SOC_CONN_DIFF-') else 'todas',
                'active_members_filter': values.get('-SOC_ACTIVE_ONLY-', False), 
                'nominators_option': values.get('-SOC_SHOW_ISOLATES-', True),
                'reciprocal_nodes_color_filter': values.get('-SOC_COLOR_RECIP_NODES-', False), 
                'style_reciprocal_links': values.get('-SOC_RECIPROCAL_STYLE-', True),
                'selected_participant_focus': next((p[1] for p in participant_options if p[0] == values.get('-SOC_FOCUS_PARTICIPANT-')), None),
                'connection_focus_mode': 'outgoing' if values.get('-SOC_FOCUS_OUT-') else 'incoming' if values.get('-SOC_FOCUS_IN-') else 'all',
                'layout_to_use': 'cose', 
                'aggregation_mode': aggregation_mode, 
                'perceiver_name': perceiver_name,
                'received_color_filter': values.get('-SOC_COLOR_RECEIVERS-', False),
                'highlight_mode': 'top_n' if values.get('-SOC_HL_TOPN-') else 'k_th' if values.get('-SOC_HL_KTH-') else 'none',
                'highlight_value': highlight_val
            }
            log_message(f"[DEBUG] Parámetros para el motor: {params}", "debug")
            
            output_path = os.path.join(os.getcwd(), "sociograma_interactivo.html")
            window.set_cursor('watch'); window.refresh()
            
            log_message("[DEBUG] Llamando al motor sociogram_engine.generate_interactive_html...", "debug")
            html_content = sociogram_engine.generate_interactive_html(
                school_name=institution_name, class_name=group_name, app_data_ref=app_data,
                selected_data_keys=selected_keys, **params
            )
            
            if html_content:
                log_message(f"[DEBUG] Contenido HTML generado (longitud: {len(html_content)}).", "info")
            else:
                log_message("[DEBUG] El motor NO devolvió contenido HTML (resultado nulo o vacío).", "error")

            window.set_cursor('arrow')
            
            if html_content:
                result_path = sociogram_engine.save_interactive_sociogram(html_content=html_content, output_path=output_path)
                
                try:
                    webbrowser.open(f'file:///{os.path.abspath(result_path)}')
                    log_message(f"[INFO] Sociograma abierto en el navegador web predeterminado: {result_path}", "info")
                except Exception as e:
                    log_message(f"[ERROR] No se pudo abrir el sociograma en el navegador. Error: {e}", "error")
                    sg.popup_error(f"Se generó el sociograma, pero no se pudo abrir automáticamente.\n\nPuedes abrirlo manualmente en:\n{result_path}\n\nError: {e}")
            else:
                sg.popup_error("No se pudo generar el archivo del sociograma. Revisa la consola para más detalles.")
            
    window.close()
    return action, data

# --- BLOQUE 7 DE 10: FUNCIONES DE VENTANAS DE ANÁLISIS (MATRIZ Y DIANA) ---

def window_sociomatrix(institution_name, group_name):
    """
    Versión final: Análisis de Precisión es global, sin foco.
    """
    app_state['current_group_viewing_members'] = {'school': institution_name, 'class_name': group_name}
    layout = create_layout_sociomatrix(institution_name, group_name)
    window = sg.Window(f"Matriz Sociométrica: Controles", layout, finalize=True, resizable=True)
    window.maximize()
    
    action, data = 'open_groups', institution_name
    last_generated_header, last_generated_data = [], []
    
    # --- MODIFICACIÓN: El mapa ahora refleja que 'accuracy_analysis' no usa foco ---
    aggregation_map = {
        "Matriz de Elecciones (Estándar)": "real_actions",
        "Matriz de Relaciones Completas (CIVSOC)": "civsoc_matrix",
        "Meta-Percepción (SELF)": "meta_perceptions",
        "Análisis de Precisión": "accuracy_analysis", # Nombre actualizado
    }
    
    all_defs = app_data.get_class_question_definitions(institution_name, group_name)
    relation_options = sociogram_utils.get_relation_options(institution_name, group_name, app_data)

    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-BACK_TO_GROUPS-'): break
        if event == sg.WIN_CLOSED: action = 'exit'; break

        if event == '-MATRIX_AGGREGATION_MODE-':
            mode_text = values[event]
            
            # El foco ahora NUNCA se activa, ya que ningún modo lo requiere
            is_perceiver_needed = False 
            window['-MATRIX_PERCEIVER-'].update(disabled=not is_perceiver_needed)

            required_type = None
            if mode_text == "Matriz de Elecciones (Estándar)":
                required_type = '[Acción Real]'
            elif mode_text == "Meta-Percepción (SELF)":
                required_type = '[Meta-Percepción]'

            for opt in relation_options:
                key = f"-MATRIXQ__{opt['data_key']}__"
                q_def = next((d for d in all_defs.values() if d.get('data_key') == opt['data_key']), None)
                if key in window.key_dict and q_def:
                    if required_type:
                        should_be_checked = (q_def.get('type') == required_type)
                        window[key].update(should_be_checked)
                    elif mode_text in ["Matriz de Relaciones Completas (CIVSOC)", "Análisis de Precisión"]: # Nombre actualizado
                        window[key].update(False)
            
        if event in ('-MATRIX_ALL-', '-MATRIX_NONE-', '-MATRIX_POS-', '-MATRIX_NEG-'):
            for opt in relation_options:
                key = f"-MATRIXQ__{opt['data_key']}__"
                if key in window.key_dict:
                    if event == '-MATRIX_ALL-': window[key].update(True)
                    elif event == '-MATRIX_NONE-': window[key].update(False)
                    elif event == '-MATRIX_POS-': window[key].update(opt['polarity'] == 'positive')
                    elif event == '-MATRIX_NEG-': window[key].update(opt['polarity'] == 'negative')

        elif event == '-MATRIX_UPDATE-':
            sg.popup_quick_message("Validando y generando...", background_color='lightblue')
            
            aggregation_mode = aggregation_map.get(values['-MATRIX_AGGREGATION_MODE-'], 'real_actions')
            selected_keys = [k.split('__')[1] for k, v in values.items() if k.startswith('-MATRIXQ__') and v]
            html_content = ""
            
            is_valid = True
            error_msg = ""
            selected_defs = [d for d in all_defs.values() if d.get('data_key') in selected_keys]
            
            perceiver_name = values['-MATRIX_PERCEIVER-']

            # --- MODIFICACIÓN: La validación de foco ya no incluye 'accuracy_analysis' ---
            if not selected_keys:
                is_valid, error_msg = False, "Debe seleccionar al menos una pregunta."
            
            if is_valid:
                # =============================================================================
                # INICIO DEL BLOQUE DE CÓDIGO CORREGIDO Y ROBUSTO
                # =============================================================================
                
                # Validación para: Matriz de Elecciones (Estándar)
                if aggregation_mode == 'real_actions':
                    if any(d.get('is_cognitive') for d in selected_defs):
                        is_valid, error_msg = False, "Este modo solo permite preguntas de '[Acción Real]'."
                
                # Validación para: Meta-Percepción (SELF)
                elif aggregation_mode == 'meta_perceptions':
                    # Verifica que TODAS las preguntas seleccionadas sean de tipo [Meta-Percepción]
                    if any(d.get('type') != '[Meta-Percepción]' for d in selected_defs):
                        is_valid, error_msg = False, "Este modo solo permite preguntas de '[Meta-Percepción]'."
                
                # Validación para: Matriz de Relaciones Completas (CIVSOC)
                elif aggregation_mode == 'civsoc_matrix':
                    if len(selected_defs) != 4:
                        is_valid, error_msg = False, f"Se requieren exactamente 4 preguntas, pero ha seleccionado {len(selected_defs)}."
                    else:
                        # Cuenta cuántas preguntas hay de cada tipo/polaridad requerida
                        counts = {
                            'accion_pos': sum(1 for d in selected_defs if d.get('type') == '[Acción Real]' and d.get('polarity') == 'positive'),
                            'accion_neg': sum(1 for d in selected_defs if d.get('type') == '[Acción Real]' and d.get('polarity') == 'negative'),
                            'meta_pos': sum(1 for d in selected_defs if d.get('type') == '[Meta-Percepción]' and d.get('polarity') == 'positive'),
                            'meta_neg': sum(1 for d in selected_defs if d.get('type') == '[Meta-Percepción]' and d.get('polarity') == 'negative')
                        }
                        # Verifica que haya exactamente una de cada una
                        if not all(c == 1 for c in counts.values()):
                            is_valid, error_msg = False, "La selección es incorrecta. Debe haber exactamente una pregunta para cada combinación:\n\n- Acción Real (Positiva)\n- Acción Real (Negativa)\n- Meta-Percepción (Positiva)\n- Meta-Percepción (Negativa)"
                
                # Validación para: Análisis de Precisión
                elif aggregation_mode == 'accuracy_analysis':
                    # Primero, verifica que haya exactamente dos preguntas seleccionadas
                    if len(selected_defs) != 2:
                        is_valid, error_msg = False, "Debe seleccionar exactamente 2 preguntas: una de '[Acción Real]' y una de '[Meta-Percepción]'."
                    else:
                        # Busca explícitamente la pregunta de Acción y la de Meta, sin importar su orden
                        action_q = next((d for d in selected_defs if d.get('type') == '[Acción Real]'), None)
                        meta_q = next((d for d in selected_defs if d.get('type') == '[Meta-Percepción]'), None)

                        # Verifica que ambos tipos de pregunta se hayan encontrado
                        if not action_q or not meta_q:
                            is_valid, error_msg = False, "La selección es incorrecta. Debe incluir una pregunta de '[Acción Real]' Y una de '[Meta-Percepción]'."
                        # Verifica que las polaridades de las dos preguntas encontradas coincidan
                        elif action_q.get('polarity') != meta_q.get('polarity'):
                            is_valid, error_msg = False, "Las polaridades no coinciden. Ambas preguntas (Acción Real y Meta-Percepción) deben ser positivas o ambas deben ser negativas."            
            if not is_valid:
                sg.popup_error(f"Error de Selección para '{values['-MATRIX_AGGREGATION_MODE-']}':\n\n{error_msg}", title="Configuración Incorrecta")
                continue
            
            network_data = hutils.get_aggregated_network(institution_name, group_name, aggregation_mode, app_data, perceiver_name, selected_keys)
            
            if aggregation_mode == 'civsoc_matrix':
                q_keys = {
                    'accion_pos': next(d['data_key'] for d in selected_defs if d.get('type') == '[Acción Real]' and d.get('polarity') == 'positive'),
                    'accion_neg': next(d['data_key'] for d in selected_defs if d.get('type') == '[Acción Real]' and d.get('polarity') == 'negative'),
                    'meta_pos': next(d['data_key'] for d in selected_defs if d.get('type') == '[Meta-Percepción]' and d.get('polarity') == 'positive'),
                    'meta_neg': next(d['data_key'] for d in selected_defs if d.get('type') == '[Meta-Percepción]' and d.get('polarity') == 'negative')
                }
                matrix_data, members, legend_dict = hgrp.calculate_civsoc_matrix(
                    institution_name, group_name, q_keys,
                    allow_self_on_diagonal=values['-MATRIX_ALLOW_SELF-']
                )
                header = ['Miembro'] + [m.get('iniz', 'N/A') for m in members]
                data_with_names = [[f"{m.get('cognome', '')}, {m.get('nome', '')}".strip(', ')] + row for m, row in zip(members, matrix_data)]
                color_map = { "1": "#a8dada", "2": "#f9a8a8", "3": "#d5aaff", "4": "#ffd5a8", "5": "#64b5f6", "6": "#ff8a80", "7": "#ffb74d", "8": "#b39ddb", "0": "#e0e0e0", "X": "#ffffff" }
                legend_html = "<div class='legend'><h4>Leyenda (CIVSOC)</h4>" + "".join([f"<div class='legend-item'><span class='legend-color-box' style='background-color:{color_map.get(c, '#fff')};'></span> <b>{c}</b>: {d}</div>" for c, d in sorted(legend_dict.items(), key=lambda item: int(item[0]))]) + "</div>"
                html_content = hsm.generate_html_for_matrix(header, data_with_names, cell_color_map=color_map, legend_html=legend_html)
                last_generated_header, last_generated_data = header, data_with_names

            elif aggregation_mode == 'accuracy_analysis':
                action_key = next(d['data_key'] for d in selected_defs if d.get('type') == '[Acción Real]')
                meta_key = next(d['data_key'] for d in selected_defs if d.get('type') == '[Meta-Percepción]')
                matrix_data, members, legend_dict = hgrp.calculate_accuracy_matrix(
                    institution_name, group_name, action_key, meta_key,
                    allow_self_on_diagonal=values['-MATRIX_ALLOW_SELF-']
                )
                header = ['Miembro (Ego)'] + [m.get('iniz', 'N/A') for m in members]
                data_with_names = [[f"{m.get('cognome', '')}, {m.get('nome', '')}".strip(', ')] + row for m, row in zip(members, matrix_data)]
                color_map = {"1": "#a5d6a7", "2": "#ef9a9a", "3": "#90caf9", "0": "#f5f5f5", "X": "#ffffff"}
                legend_html = "<div class='legend'><h4>Leyenda de Precisión</h4>" + "".join([f"<div class='legend-item'><span class='legend-color-box' style='background-color:{color_map.get(c, '#fff')};'></span> <b>{c}</b>: {d}</div>" for c, d in sorted(legend_dict.items(), key=lambda item: int(item[0]))]) + "</div>"
                html_content = hsm.generate_html_for_matrix(header, data_with_names, cell_color_map=color_map, legend_html=legend_html)
                last_generated_header, last_generated_data = header, data_with_names
            
            else:
                result = hsm.handle_draw_sociomatrix_data(
                    institution_name=institution_name,
                    group_name=group_name,
                    selected_data_keys_list=selected_keys,
                    allow_self_on_diagonal=values['-MATRIX_ALLOW_SELF-'],
                    network_data_override=network_data
                )
                if result and result.get('success'):
                    html_content = hsm.generate_html_for_matrix(result.get('header', []), result.get('data', []))
                    last_generated_header, last_generated_data = result.get('header', []), result.get('data', [])
                else:
                    sg.popup_error(result.get('message', "Error al generar datos para la matriz."))
                    continue

            if html_content:
                try:
                    filepath = os.path.join(os.getcwd(), "matriz_sociometrica_temp.html")
                    with open(filepath, 'w', encoding='utf-8') as f: f.write(html_content)
                    webbrowser.open(f'file:///{os.path.abspath(filepath)}')
                    window['-MATRIX_STATUS-'].update("¡Éxito! La matriz se ha abierto en una nueva pestaña de su navegador.")
                except Exception as e: sg.popup_error(f"Error al generar o abrir el archivo HTML: {e}")
        
        elif event == '-MATRIX_PDF-':
            if not last_generated_header:
                sg.popup_error("Primero debes generar una matriz con el botón 'Generar y Abrir Matriz'.")
                continue
            pdf_bytes, filename = pdf_generator.generate_sociomatrix_pdf(institution_name, group_name, last_generated_header, last_generated_data)
            if pdf_bytes:
                save_path = sg.popup_get_file('Guardar PDF de la Matriz', save_as=True, default_extension=".pdf", default_path=filename)
                if save_path:
                    try:
                        with open(save_path, 'wb') as f: f.write(pdf_bytes)
                        sg.popup("PDF de la Matriz guardado exitosamente.")
                    except Exception as e: sg.popup_error(f"Error al guardar el archivo: {e}")
            else:
                sg.popup_error("No se pudo generar el PDF.")
            
    window.close()
    return action, data

def window_diana(institution_name, group_name):
    """
    Versión FINAL. Lanza y gestiona la ventana de Análisis Gráfico en Diana.
    - Llama a la función de dibujo correcta (`generate_affinity_diana_image` o `generate_distance_diana_image`) según el modo.
    """
    app_state['current_group_viewing_members'] = {'school': institution_name, 'class_name': group_name}
    relation_options = sociogram_utils.get_relation_options(institution_name, group_name, app_data)
    layout = create_layout_diana(institution_name, group_name, relation_options)
    window = sg.Window("Análisis Gráfico en Diana", layout, finalize=True, resizable=True)
    window.maximize()
    
    original_image_bytes = None
    all_defs = app_data.get_class_question_definitions(institution_name, group_name)

    def update_diana_image(zoom_level=100):
        if not original_image_bytes: return
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(original_image_bytes))
            container_size = window['-DIANA_IMAGE_CONTAINER-'].get_size()
            widget_width, widget_height = container_size[0] - 20, container_size[1] - 20
            if widget_width <= 0 or widget_height <= 0: return
            img_width, img_height = img.size
            scale = min(widget_width / img_width, widget_height / img_height) if img_width > 0 and img_height > 0 else 1
            final_scale = scale * (zoom_level / 100.0)
            new_size = (int(img_width * final_scale), int(img_height * final_scale))
            if new_size[0] < 10 or new_size[1] < 10: return
            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
            with io.BytesIO() as bio:
                img_resized.save(bio, format="PNG")
                img_bytes_for_gui = bio.getvalue()
            window['-DIANA_IMAGE-'].update(data=img_bytes_for_gui)
            window['-DIANA_ZOOM_TEXT-'].update(f"{int(zoom_level)}%")
        except Exception as e:
            log_message(f"Error al aplicar zoom: {e}", "error")

    q_widgets_info = { f"-DIANA_Q__{opt['data_key']}__": {'polarity': opt['polarity']} for opt in relation_options }
    action, data = 'open_groups', institution_name

    aggregation_map = {
        "Diana de Afinidad (Popularidad)": "affinity",
        "Diana de Distancia (CIVSOC)": "civsoc_distance",
        "Diana de Precisión (Global)": "accuracy_diana",
        "Red de Meta-Percepción (SELF)": "meta_perceptions",
    }

    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-BACK_TO_GROUPS-'): break
        if event == sg.WIN_CLOSED: action = 'exit'; break

        if event == '-DIANA_AGGREGATION_MODE-':
            mode_text = values[event]
            is_focus_needed = mode_text == "Diana de Distancia (CIVSOC)"
            window['-DIANA_PERCEIVER-'].update(disabled=not is_focus_needed)
            is_affinity_mode = mode_text in ["Diana de Afinidad (Popularidad)", "Red de Meta-Percepción (SELF)"]
            window['-DIANA_SHOW_LINES-'].update(value=is_affinity_mode, disabled=not is_affinity_mode)

        if event in ('-DIANA_ALL-', '-DIANA_NONE-', '-DIANA_POS-', '-DIANA_NEG-'):
            for key, info in q_widgets_info.items():
                if key in window.key_dict:
                    if event == '-DIANA_ALL-': window[key].update(True)
                    elif event == '-DIANA_NONE-': window[key].update(False)
                    elif event == '-DIANA_POS-': window[key].update(info['polarity'] == 'positive')
                    elif event == '-DIANA_NEG-': window[key].update(info['polarity'] == 'negative')
        
        elif event == '-DIANA_GENERATE-':
            sg.popup_quick_message("Generando Gráfico...", background_color='lightblue')
            
            aggregation_mode_key = aggregation_map.get(values['-DIANA_AGGREGATION_MODE-'], 'affinity')
            selected_keys = [key.split('__')[1] for key, val in values.items() if key.startswith('-DIANA_Q__') and val]
            image_buffer = None
            
            if aggregation_mode_key == 'civsoc_distance':
                focus_member_name = values['-DIANA_PERCEIVER-']
                if not focus_member_name or focus_member_name == "Todos (Grafo Completo)":
                    sg.popup_error("Por favor, selecciona un 'Miembro Foco' para este análisis.")
                    continue
                
                selected_defs = [d for d in all_defs.values() if d.get('data_key') in selected_keys]
                counts = {'ap': sum(1 for d in selected_defs if d.get('type')=='[Acción Real]' and d.get('polarity')=='positive'), 'an': sum(1 for d in selected_defs if d.get('type')=='[Acción Real]' and d.get('polarity')=='negative'), 'mp': sum(1 for d in selected_defs if d.get('type')=='[Meta-Percepción]' and d.get('polarity')=='positive'), 'mn': sum(1 for d in selected_defs if d.get('type')=='[Meta-Percepción]' and d.get('polarity')=='negative')}
                if len(selected_defs) != 4 or not all(c == 1 for c in counts.values()):
                    sg.popup_error("Error de Selección para Distancia CIVSOC:\n\nDebe seleccionar exactamente 4 preguntas: una para cada combinación de Acción/Meta y Positiva/Negativa.")
                    continue
                
                q_keys = {k: next(d['data_key'] for d in selected_defs if d.get('type')==t and d.get('polarity')==p) for k,t,p in [('accion_pos','[Acción Real]','positive'), ('accion_neg','[Acción Real]','negative'), ('meta_pos','[Meta-Percepción]','positive'), ('meta_neg','[Meta-Percepción]','negative')]}
                members_data_list = hgrp.calculate_civsoc_distance_data(institution_name, group_name, focus_member_name, q_keys)
                
                if members_data_list:
                    image_buffer = pdf_generator.generate_distance_diana_image(
                        title_text=f"Distancias Sociométricas respecto a {focus_member_name}\n({group_name})",
                        members_data_list=members_data_list, score_key='distancia_sociometrica',
                        score_range=(-4, 4), ring_labels={-4:"-4", -3:"-3", -2:"-2", -1:"-1", 0:"Foco", 1:"+1", 2:"+2", 3:"+3", 4:"+4"}
                    )

            elif aggregation_mode_key == 'accuracy_diana':
                selected_defs = [d for d in all_defs.values() if d.get('data_key') in selected_keys]
                action_q = next((d for d in selected_defs if d.get('type') == '[Acción Real]'), None); meta_q = next((d for d in selected_defs if d.get('type') == '[Meta-Percepción]'), None)
                if len(selected_defs) != 2 or not action_q or not meta_q or action_q.get('polarity') != meta_q.get('polarity'):
                    sg.popup_error("Error de Selección para Diana de Precisión:\n\nDebe seleccionar 2 preguntas (1 de Acción Real y 1 de Meta-Percepción) de la misma polaridad.")
                    continue
                
                matrix_data, members, _ = hgrp.calculate_accuracy_matrix(institution_name, group_name, action_q['data_key'], meta_q['data_key'])
                members_data_list = []
                for i, member in enumerate(members):
                    counts = collections.Counter(matrix_data[i]); num_aciertos = counts.get(1, 0); num_errores = counts.get(2, 0); num_omisiones = counts.get(3, 0)
                    category = "Indiferencia";
                    if num_aciertos > num_errores + num_omisiones: category = "Aciertos"
                    elif num_errores + num_omisiones > num_aciertos: category = "Errores/Omisiones"
                    members_data_list.append({'nombre_completo': f"{member.get('nome','').title()} {member.get('cognome','').title()}", 'id_corto': member.get('iniz', 'N/A'), 'sexo': member.get('sexo'), 'accuracy_category': category})
                
                if members_data_list:
                    ring_labels_categorical = {"Aciertos": "Aciertos", "Indiferencia": "Indiferencia Correcta", "Errores/Omisiones": "Errores / Omisiones"}
                    image_buffer = pdf_generator.generate_distance_diana_image(
                        title_text=f"Precisión Perceptual Global\n({group_name})",
                        members_data_list=members_data_list, score_key='accuracy_category', score_range=(0, 0), ring_labels=ring_labels_categorical
                    )
            
            else: # Modos de Afinidad y Meta-Percepción
                if aggregation_mode_key == 'affinity': aggregation_mode_key = 'real_actions'
                if not selected_keys: sg.popup_error("Por favor, selecciona al menos una pregunta para el análisis."); continue
                
                network_data = hutils.get_aggregated_network(institution_name, group_name, aggregation_mode_key, app_data, None, selected_keys)
                members_data, edges_data = hgrp.handle_generate_diana_data(institution_name, group_name, selected_keys, network_data_override=network_data)
                
                if members_data:
                    # ESTA ES LA LLAMADA CORREGIDA
                    image_buffer = pdf_generator.generate_affinity_diana_image(
                        title_text=f"{values['-DIANA_AGGREGATION_MODE-']}\n({group_name})",
                        members_data_list=members_data,
                        edges_data=edges_data,
                        show_lines=values['-DIANA_SHOW_LINES-']
                    )
            
            if image_buffer:
                original_image_bytes = image_buffer; window['-DIANA_SAVE-'].update(disabled=False); update_diana_image(values['-DIANA_ZOOM_SLIDER-'])
            else:
                sg.popup_error("No se pudo generar la imagen. Verifica la selección de preguntas o si hay datos disponibles.")
                original_image_bytes = None; window['-DIANA_IMAGE-'].update(data=None); window['-DIANA_SAVE-'].update(disabled=True)
        
        elif event == '-DIANA_ZOOM_SLIDER-':
            if original_image_bytes: update_diana_image(values['-DIANA_ZOOM_SLIDER-'])
        
        elif event == '-DIANA_SAVE-':
            if original_image_bytes:
                mode_name = values['-DIANA_AGGREGATION_MODE-'].split('(')[0].strip().replace(' ', '_')
                filename = f"Diana_{mode_name}_{group_name.replace(' ', '_')}.png"
                save_path = sg.popup_get_file('Guardar Gráfico', save_as=True, default_extension=".png", file_types=(("PNG", "*.png"),), default_path=filename)
                if save_path:
                    try:
                        with open(save_path, 'wb') as f: f.write(original_image_bytes)
                        sg.popup("Gráfico guardado.")
                    except Exception as e: sg.popup_error(f"Error al guardar: {e}")
            else: sg.popup_error("Primero genera un gráfico.")
            
    window.close()
    return action, data

# --- BLOQUE 8 DE 10: CLASE PRINCIPAL Y ARQUITECTURA ---
# =============================================================================
#  BLOQUE 5: CLASE PRINCIPAL (ARQUITECTURA DE VENTANA ÚNICA - VERSIÓN ESTABLE)
# =============================================================================

class SociogramaApp:
    def __init__(self):
        """Inicializa la aplicación, los datos y la ventana principal."""
        self.app_state = {}
        self.view_keys = [
            '-VIEW_INSTITUTIONS-', '-VIEW_GROUPS-', '-VIEW_MEMBERS-',
            '-VIEW_QUESTIONS-',
        ]
        
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()

        self.window = self._create_main_window()

    def _create_main_window(self):
        """
        Crea la ventana principal con todas las vistas (Columnas) pre-cargadas y ocultas.
        """
        layout = [
            [
                sg.Column(create_layout_institutions(), key='-VIEW_INSTITUTIONS-', visible=True, expand_x=True, expand_y=True),
                sg.Column(create_layout_groups("..."), key='-VIEW_GROUPS-', visible=False, expand_x=True, expand_y=True),
                sg.Column(create_layout_members("...", "..."), key='-VIEW_MEMBERS-', visible=False, expand_x=True, expand_y=True),
                sg.Column(create_layout_question_management("...", "..."), key='-VIEW_QUESTIONS-', visible=False, expand_x=True, expand_y=True),
            ]
        ]
        return sg.Window("Suite de Análisis Sociométrico", layout, finalize=True, resizable=True)

    def switch_view(self, view_key_to_show, context_data=None):
        """
        Gestiona el cambio entre las vistas principales (Columnas).
        """
        self.app_state['context'] = context_data
                
        for key in self.view_keys:
            self.window[key].update(visible=False)
                
        self.window[view_key_to_show].update(visible=True)

        # Refresca el contenido de la vista que se va a mostrar
        if view_key_to_show == '-VIEW_INSTITUTIONS-':
            self.refresh_institutions_list()
        elif view_key_to_show == '-VIEW_GROUPS-':
            self.refresh_groups_list(context_data)
        elif view_key_to_show == '-VIEW_MEMBERS-':
            self.refresh_members_list(context_data['school'], context_data['class_name'])
        elif view_key_to_show == '-VIEW_QUESTIONNAIRE-': # Aunque es una ventana aparte, refrescamos por si acaso
            self.refresh_questionnaire_view(context_data['school'], context_data['class_name'], context_data['member'])
        elif view_key_to_show == '-VIEW_QUESTIONS-':
            self.refresh_questions_list(context_data['school'], context_data['class_name'])

    def run(self):
        """El bucle de eventos principal."""
        self.window.maximize()
        self.refresh_institutions_list()
        
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED or event == '-EXIT-':
                break

            active_view = next((key for key in self.view_keys if self.window[key].visible), None)
            
            if active_view == '-VIEW_INSTITUTIONS-':
                self.handle_institutions_events(event, values)
            elif active_view == '-VIEW_GROUPS-':
                self.handle_groups_events(event, values)
            elif active_view == '-VIEW_MEMBERS-':
                self.handle_members_events(event, values)
            # El caso para '-VIEW_QUESTIONNAIRE-' se maneja en su propia ventana.
            elif active_view == '-VIEW_QUESTIONS-':
                self.handle_questions_events(event, values)
            
        self.window.close()

# --- BLOQUE 9 DE 10: MÉTODOS DE REFRESCO Y MANEJADORES DE EVENTOS PRINCIPALES ---

    # --- Métodos de Refresco ---
    def refresh_institutions_list(self):
        institutions = sorted(list(app_data.schools_data.keys()))
        self.window['-INST_SELECT-'].update(values=institutions, set_to_index=[])
        self.window['-INST_ANNOTATIONS-'].update('')
        self.window['-MOD_INST-'].update(disabled=True)
        self.window['-DEL_INST-'].update(disabled=True)
        self.window['-NAV_TO_GROUPS-'].update(disabled=True)

    def refresh_groups_list(self, institution_name):
        self.window['-GROUPS_TITLE-'].update(f"Grupos de: {institution_name}")
        groups = sorted([g['name'] for g in app_data.classes_data.get(institution_name, [])])
        self.window['-GROUP_SELECT-'].update(values=groups, set_to_index=[])
        for key in ['-MOD_GROUP-', '-DEL_GROUP-', '-NAV_TO_MEMBERS-', '-NAV_TO_SOCIOGRAM-', '-NAV_TO_MATRIX-', '-NAV_TO_DIANA-', '-PDF_SUMMARY-']:
            if key in self.window.key_dict: self.window[key].update(disabled=True)
        for key in ['-GROUP_COORD-', '-GROUP_INS2-', '-GROUP_INS3-', '-GROUP_SOST-', '-GROUP_ANNOT-']:
            if key in self.window.key_dict: self.window[key].update('')

    def refresh_members_list(self, institution_name, group_name):
        self.window['-MEMBERS_TITLE-'].update(f"Miembros de: {group_name} ({institution_name})")
        members_list = app_data.members_data.get(institution_name, {}).get(group_name, [])
        member_names = hutils.generar_opciones_dropdown_miembros_main_select(members_list)
        self.window['-MEMBER_SELECT-'].update(values=member_names, set_to_index=[])
        for key in ['-MOD_MEMBER-', '-DEL_MEMBER-', '-NAV_TO_QUESTIONNAIRE-']:
            if key in self.window.key_dict: self.window[key].update(disabled=True)
        for key in ['-MEMBER_COGNOME-', '-MEMBER_NOME-', '-MEMBER_INIZ-', '-MEMBER_ANNOT-']:
            if key in self.window.key_dict: self.window[key].update('')

    def refresh_questions_list(self, institution_name, group_name):
        questions = hq.get_question_definitions_for_group(institution_name, group_name)
        display_list = [f"[{q.get('order', '?')}] {q.get('text', 'Sin texto')} (ID: {qid})" for qid, q in questions]
        self.window['-Q_LIST-'].update(values=display_list, set_to_index=[])
        self.window['-MOD_Q-'].update(disabled=True)
        self.window['-DEL_Q-'].update(disabled=True)

    # --- Manejadores de Eventos ---
    def handle_institutions_events(self, event, values):
        selected_inst = values.get('-INST_SELECT-')[0] if values.get('-INST_SELECT-') else None
        form_is_visible = self.window['-FORM_INST_FRAME-'].visible
        self.window['-NEW_INST-'].update(disabled=form_is_visible)
        self.window['-MOD_INST-'].update(disabled=form_is_visible or not selected_inst)
        self.window['-DEL_INST-'].update(disabled=form_is_visible or not selected_inst)
        self.window['-NAV_TO_GROUPS-'].update(disabled=form_is_visible or not selected_inst)

        if event == '-INST_SELECT-':
            self.window['-FORM_INST_FRAME-'].update(visible=False)
            self.window['-INST_ANNOTATIONS-'].update(app_data.schools_data.get(selected_inst, "") if selected_inst else "")
        elif event == '-NAV_TO_GROUPS-' and selected_inst:
            self.switch_view('-VIEW_GROUPS-', context_data=selected_inst)
        elif event == '-NEW_INST-':
            self.app_state['form_inst_mode'] = 'new'
            self.window['-FORM_INST_TITLE-'].update("Nueva Institución")
            self.window['-FORM_INST_NAME-'].update('')
            self.window['-FORM_INST_ANNOT-'].update('')
            self.window['-FORM_INST_FRAME-'].update(visible=True)
        elif event == '-MOD_INST-' and selected_inst:
            self.app_state['form_inst_mode'] = 'modify'
            self.app_state['original_inst_name'] = selected_inst
            self.window['-FORM_INST_TITLE-'].update(f"Modificar: {selected_inst}")
            self.window['-FORM_INST_NAME-'].update(selected_inst)
            self.window['-FORM_INST_ANNOT-'].update(values['-INST_ANNOTATIONS-'])
            self.window['-FORM_INST_FRAME-'].update(visible=True)
        elif event == '-FORM_INST_SAVE-':
            form_name = values['-FORM_INST_NAME-']
            form_annot = values['-FORM_INST_ANNOT-']
            if self.app_state.get('form_inst_mode') == 'new':
                success, msg = hinst.handle_add_institution(form_name, form_annot)
            else:
                success, msg = hinst.handle_modify_institution(self.app_state.get('original_inst_name'), form_name, form_annot)
            sg.popup(msg)
            if success:
                self.window['-FORM_INST_FRAME-'].update(visible=False)
                self.refresh_institutions_list()
        elif event == '-FORM_INST_CANCEL-':
            self.window['-FORM_INST_FRAME-'].update(visible=False)
        elif event == '-DEL_INST-' and selected_inst:
            if sg.popup_yes_no(f"¿Eliminar '{selected_inst}' y TODOS sus datos asociados?", title="Confirmar Eliminación") == 'Yes':
                success, msg = hinst.handle_delete_institution(selected_inst)
                sg.popup(msg)
                if success:
                    self.refresh_institutions_list()
        elif event == '-MANAGE_CSV-':
            if window_csv_management({'school': selected_inst, 'group': None}, self.tk_root):
                log_message("Datos importados, refrescando instituciones.")
                self.refresh_institutions_list()

    def handle_groups_events(self, event, values):
        institution_name = self.app_state.get('context')
        selected_group = values.get('-GROUP_SELECT-')[0] if values.get('-GROUP_SELECT-') else None
        form_is_visible = self.window['-FORM_GROUP_FRAME-'].visible
        
        # Lógica de habilitación/deshabilitación de botones que se ejecuta en cada evento
        is_group_selected = not form_is_visible and selected_group is not None
        self.window['-NEW_GROUP-'].update(disabled=form_is_visible)
        self.window['-MOD_GROUP-'].update(disabled=not is_group_selected)
        self.window['-DEL_GROUP-'].update(disabled=not is_group_selected)
        self.window['-NAV_TO_MEMBERS-'].update(disabled=not is_group_selected)
        self.window['-NAV_TO_SOCIOGRAM-'].update(disabled=not is_group_selected)
        self.window['-NAV_TO_MATRIX-'].update(disabled=not is_group_selected)
        self.window['-NAV_TO_DIANA-'].update(disabled=not is_group_selected)
        self.window['-PDF_SUMMARY-'].update(disabled=not is_group_selected)

        # Manejo de eventos específicos
        if event == '-BACK_TO_INST-':
            self.switch_view('-VIEW_INSTITUTIONS-')
            
        elif event == '-NAV_TO_SOCIOGRAM-' and selected_group:
            self.window.hide()
            action_result, _ = window_sociogram(institution_name, selected_group)
            self.window.un_hide()
            self.window.maximize()
            if action_result == 'exit': self.window.write_event_value('-EXIT-', None)

        elif event == '-NAV_TO_MATRIX-' and selected_group:
            self.window.hide()
            action_result, _ = window_sociomatrix(institution_name, selected_group)
            self.window.un_hide()
            self.window.maximize()
            if action_result == 'exit': self.window.write_event_value('-EXIT-', None)

        elif event == '-NAV_TO_DIANA-' and selected_group:
            self.window.hide()
            action_result, _ = window_diana(institution_name, selected_group)
            self.window.un_hide()
            self.window.maximize()
            if action_result == 'exit': self.window.write_event_value('-EXIT-', None)

        elif event == '-NAV_TO_MEMBERS-' and selected_group:
            context = {'school': institution_name, 'class_name': selected_group}
            self.switch_view('-VIEW_MEMBERS-', context_data=context)
            
        elif event == '-GROUP_SELECT-':
            is_valid = selected_group is not None
            group_info = next((g for g in app_data.classes_data.get(institution_name, []) if g['name'] == selected_group), {}) if is_valid else {}
            self.window['-GROUP_COORD-'].update(group_info.get('coordinator', ''))
            self.window['-GROUP_INS2-'].update(group_info.get('ins2', ''))
            self.window['-GROUP_INS3-'].update(group_info.get('ins3', ''))
            self.window['-GROUP_SOST-'].update(group_info.get('sostegno', ''))
            self.window['-GROUP_ANNOT-'].update(group_info.get('annotations', ''))
            self.window['-FORM_GROUP_FRAME-'].update(visible=False)

        elif event == '-NEW_GROUP-':
            self.app_state['form_group_mode'] = 'new'
            self.window['-FORM_GROUP_TITLE-'].update("Nuevo Grupo")
            for key in ['-FORM_GROUP_NAME-', '-FORM_GROUP_COORD-', '-FORM_GROUP_INS2-', '-FORM_GROUP_INS3-', '-FORM_GROUP_SOST-', '-FORM_GROUP_ANNOT-']: self.window[key].update('')
            self.window['-FORM_GROUP_FRAME-'].update(visible=True)
            
        elif event == '-MOD_GROUP-' and selected_group:
            self.app_state['form_group_mode'] = 'modify'; self.app_state['original_group_name'] = selected_group
            group_info = next((g for g in app_data.classes_data.get(institution_name, []) if g['name'] == selected_group), {})
            self.window['-FORM_GROUP_TITLE-'].update(f"Modificar: {selected_group}")
            self.window['-FORM_GROUP_NAME-'].update(group_info.get('name', ''))
            self.window['-FORM_GROUP_COORD-'].update(group_info.get('coordinator', ''))
            self.window['-FORM_GROUP_INS2-'].update(group_info.get('ins2', ''))
            self.window['-FORM_GROUP_INS3-'].update(group_info.get('ins3', ''))
            self.window['-FORM_GROUP_SOST-'].update(group_info.get('sostegno', ''))
            self.window['-FORM_GROUP_ANNOT-'].update(group_info.get('annotations', ''))
            self.window['-FORM_GROUP_FRAME-'].update(visible=True)
            
        elif event == '-FORM_GROUP_SAVE-':
            group_details = {'name': values['-FORM_GROUP_NAME-'], 'coordinator': values['-FORM_GROUP_COORD-'], 'ins2': values['-FORM_GROUP_INS2-'], 'ins3': values['-FORM_GROUP_INS3-'], 'sostegno': values['-FORM_GROUP_SOST-'], 'annotations': values['-FORM_GROUP_ANNOT-']}
            if self.app_state.get('form_group_mode') == 'new': success, msg = hgrp.handle_add_group(institution_name, group_details)
            else: success, msg = hgrp.handle_modify_group(institution_name, self.app_state.get('original_group_name'), group_details)
            sg.popup(msg)
            if success: self.window['-FORM_GROUP_FRAME-'].update(visible=False); self.refresh_groups_list(institution_name)
            
        elif event == '-FORM_GROUP_CANCEL-':
            self.window['-FORM_GROUP_FRAME-'].update(visible=False)
            
        elif event == '-DEL_GROUP-' and selected_group:
            if sg.popup_yes_no(f"¿Eliminar grupo '{selected_group}' y todos sus datos asociados?", title="Confirmar") == 'Yes':
                success, msg = hgrp.handle_delete_group(institution_name, selected_group)
                sg.popup(msg)
                if success: self.refresh_groups_list(institution_name)
                
        elif event == '-PDF_SUMMARY-' and selected_group:
            pdf_bytes, filename = pdf_generator.generate_class_summary_report_pdf(institution_name, selected_group)
            if pdf_bytes:
                save_path = sg.popup_get_file('Guardar PDF Resumen', save_as=True, default_extension=".pdf", default_path=filename)
                if save_path:
                   try:
                       with open(save_path, 'wb') as f: f.write(pdf_bytes)
                       sg.popup("PDF Resumen guardado.")
                   except Exception as e: sg.popup_error(f"Error al guardar: {e}")
            else: sg.popup_error("No se pudo generar el PDF Resumen.")

    def handle_members_events(self, event, values):
        context = self.app_state.get('context', {})
        institution_name = context.get('school')
        group_name = context.get('class_name')
        selected_name = values.get('-MEMBER_SELECT-')[0] if values.get('-MEMBER_SELECT-') else None

        form_is_visible = self.window['-FORM_MEMBER_FRAME-'].visible
        is_member_selected = not form_is_visible and selected_name is not None
        self.window['-NEW_MEMBER-'].update(disabled=form_is_visible)
        self.window['-MOD_MEMBER-'].update(disabled=not is_member_selected)
        self.window['-DEL_MEMBER-'].update(disabled=not is_member_selected)
        self.window['-NAV_TO_QUESTIONNAIRE-'].update(disabled=not is_member_selected)

        if event == '-BACK_TO_GROUPS-':
            self.switch_view('-VIEW_GROUPS-', context_data=institution_name)
        elif event == '-NAV_TO_QUESTIONNAIRE-' and selected_name:
            self.window.hide()
            window_questionnaire(institution_name, group_name, selected_name)
            self.window.un_hide()
            self.window.maximize()
        elif event == '-MEMBER_SELECT-':
            self.window['-FORM_MEMBER_FRAME-'].update(visible=False)
            member_details = {}
            if selected_name:
                members_list = app_data.members_data.get(institution_name, {}).get(group_name, [])
                member_details = next((m for m in members_list if f"{m.get('nome','').title()} {m.get('cognome','').title()}" == selected_name), {})
            self.window['-MEMBER_COGNOME-'].update(member_details.get('cognome', ''))
            self.window['-MEMBER_NOME-'].update(member_details.get('nome', ''))
            self.window['-MEMBER_INIZ-'].update(member_details.get('iniz', ''))
            self.window['-MEMBER_ANNOT-'].update(member_details.get('annotations', ''))
        elif event == '-NEW_MEMBER-':
            self.app_state['form_member_mode'] = 'new'
            self.window['-FORM_MEMBER_TITLE-'].update("Nuevo Miembro")
            for key in ['-FORM_MEMBER_COGNOME-', '-FORM_MEMBER_NOME-', '-FORM_MEMBER_INIZ-', '-FORM_MEMBER_DOB-', '-FORM_MEMBER_ANNOT-']: self.window[key].update('')
            self.window['-FORM_MEMBER_SEXO_D-'].update(True)
            self.window['-FORM_MEMBER_FRAME-'].update(visible=True)
        elif event == '-MOD_MEMBER-' and selected_name:
            self.app_state['form_member_mode'] = 'modify'
            members_list = app_data.members_data.get(institution_name, {}).get(group_name, [])
            d = next((m for m in members_list if f"{m.get('nome','').title()} {m.get('cognome','').title()}" == selected_name), {})
            self.app_state['original_member_data'] = d
            self.window['-FORM_MEMBER_TITLE-'].update(f"Modificar: {selected_name}")
            self.window['-FORM_MEMBER_COGNOME-'].update(d.get('cognome', '').title())
            self.window['-FORM_MEMBER_NOME-'].update(d.get('nome', '').title())
            self.window['-FORM_MEMBER_INIZ-'].update(d.get('iniz', ''))
            self.window['-FORM_MEMBER_SEXO_M-'].update(d.get('sexo') == 'Masculino')
            self.window['-FORM_MEMBER_SEXO_F-'].update(d.get('sexo') == 'Femenino')
            self.window['-FORM_MEMBER_SEXO_D-'].update(d.get('sexo', 'Desconocido') not in ['Masculino', 'Femenino'])
            self.window['-FORM_MEMBER_DOB-'].update(d.get('fecha_nac', ''))
            self.window['-FORM_MEMBER_ANNOT-'].update(d.get('annotations', ''))
            self.window['-FORM_MEMBER_FRAME-'].update(visible=True)
        elif event == '-FORM_MEMBER_SAVE-':
            sexo = 'Masculino' if values['-FORM_MEMBER_SEXO_M-'] else 'Femenino' if values['-FORM_MEMBER_SEXO_F-'] else 'Desconocido'
            member_details = {'cognome': values['-FORM_MEMBER_COGNOME-'], 'nome': values['-FORM_MEMBER_NOME-'], 'iniz': values['-FORM_MEMBER_INIZ-'], 'sexo': sexo, 'fecha_nac': values['-FORM_MEMBER_DOB-'], 'annotations': values['-FORM_MEMBER_ANNOT-']}
            if self.app_state.get('form_member_mode') == 'new':
                success, msg = hfmember.handle_add_member(institution_name, group_name, member_details)
            else:
                original_data = self.app_state.get('original_member_data', {})
                original_name_key = f"{original_data.get('nome','').title()} {original_data.get('cognome','').title()}"
                success, msg = hfmember.handle_modify_member(institution_name, group_name, original_name_key, original_data, member_details)
            sg.popup(msg)
            if success:
                self.window['-FORM_MEMBER_FRAME-'].update(visible=False)
                self.refresh_members_list(institution_name, group_name)
        elif event == '-FORM_MEMBER_CANCEL-':
            self.window['-FORM_MEMBER_FRAME-'].update(visible=False)
        elif event == '-DEL_MEMBER-' and selected_name:
            if sg.popup_yes_no(f"¿Seguro que quieres eliminar a '{selected_name}'?", title="Confirmar Eliminación") == 'Yes':
                success, msg = hmemb.handle_delete_member(institution_name, group_name, selected_name)
                sg.popup(msg)
                if success:
                    self.refresh_members_list(institution_name, group_name)

# --- BLOQUE 10 DE 10: MANEJADOR DE EVENTOS DE PREGUNTAS (CON DEBUG) Y PUNTO DE ENTRADA ---

    def handle_questions_events(self, event, values):
        """
        Esta función ahora solo maneja la navegación desde la vista de preguntas,
        ya que la lógica interna fue movida a window_question_management.
        """
        context = self.app_state.get('context', {})
        institution_name = context.get('school')
        group_name = context.get('class_name')

        # La única acción que esta vista principal necesita manejar es cómo se llegó a ella y cómo salir.
        if event == '-BACK_TO_Q-':
            # Vuelve a la pantalla de Cuestionario, pasando el contexto necesario.
            self.switch_view('-VIEW_QUESTIONNAIRE-', context_data=self.app_state['context'])

# =============================================================================
#  BLOQUE 6: PUNTO DE ENTRADA DE LA APLICACIÓN
# =============================================================================
if __name__ == "__main__":
    try:
        app_data.initialize_data()
        show_coffee_popup()
        
        app = SociogramaApp()
        app.run()
        
    except Exception as e:
        error_details = f'Error no controlado en Sociograma:\n\n{e}\n\nTraceback:\n{traceback.format_exc()}'
        sg.popup_error(error_details, title="Error Fatal en Sociograma")
