# =============================================================================
#  Red_Sociograma_App.py - Versión Final Completa
# =============================================================================

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

# --- BLOQUE 3: DEFINICIONES DE LAYOUTS ---

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
    
    # <-- CAMBIO CLAVE: Se añade 'scrollable=True' a la columna que contiene el contenido principal
    layout = [
        [form_frame], 
        [sg.Column(main_content, key='-MAIN_INST_COL-', expand_x=True, expand_y=True, scrollable=True)]
    ]
    return layout

def create_layout_form_institution(is_new=True, initial_data=None):
    d = initial_data or {}
    title = "Nueva Institución" if is_new else f"Modificar Institución"
    layout = [[sg.Text(title, font=("Helvetica", 14))], [sg.Text("Nombre:", size=(12, 1)), sg.Input(d.get('name', ''), key='-NAME-')], [sg.Text("Anotaciones:", size=(12, 1)), sg.Multiline(d.get('annotations', ''), size=(40, 5), key='-ANNOT-')], [sg.Submit("Guardar"), sg.Cancel("Cancelar")]]
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
    main_content = [
        [sg.Text(f"Grupos de: {institution_name}", font=("Helvetica", 16), key='-GROUPS_TITLE-')],
        [sg.Column([[sg.Text("Seleccionar Grupo:")], [sg.Listbox(values=[], size=(30, 15), key='-GROUP_SELECT-', enable_events=True, expand_y=True, expand_x=True)]]), 
         sg.VSeperator(), 
         sg.Column(details, expand_x=True)],
        [sg.HorizontalSeparator()], 
        [sg.Column([[sg.Button("Nuevo Grupo", key='-NEW_GROUP-'), sg.Button("Modificar Grupo", key='-MOD_GROUP-', disabled=True), sg.Button("Eliminar Grupo", key='-DEL_GROUP-', disabled=True)], [sg.Button("Ver Miembros", key='-NAV_TO_MEMBERS-', disabled=True), sg.Button("Sociograma", key='-NAV_TO_SOCIOGRAM-', disabled=True)]]), 
         sg.VSeperator(), 
         sg.Column([[sg.Text("Análisis y Reportes:", font=("Helvetica", 10, "bold"))], [sg.Button("Matriz Sociométrica", key='-NAV_TO_MATRIX-', disabled=True)], [sg.Button("Diana de Afinidad", key='-NAV_TO_DIANA-', disabled=True)], [sg.Button("PDF Resumen Cuestionario", key='-PDF_SUMMARY-', disabled=True)]])], 
        [sg.HorizontalSeparator()],
        [sg.Push(), sg.Button("Volver a Instituciones", key='-BACK_TO_INST-')]
    ]
    
    # <-- CAMBIO CLAVE: Se añade 'scrollable=True' a la columna que contiene el contenido principal
    layout = [
        [form_frame], 
        [sg.Column(main_content, key='-MAIN_GROUP_COL-', expand_x=True, expand_y=True, scrollable=True)]
    ]
    return layout

def create_layout_form_group(institution_name, is_new=True, initial_data=None):
    d = initial_data or {}; title = "Nuevo Grupo" if is_new else "Modificar Grupo"
    layout = [[sg.Text(title, font=("Helvetica", 14))], [sg.Text(f"Institución: {institution_name}")], [sg.Text("Nombre:", size=(15, 1)), sg.Input(d.get('name', ''), key='-NAME-')], [sg.Text("Coordinador:", size=(15, 1)), sg.Input(d.get('coordinator', ''), key='-COORD-')], [sg.Text("Profesor 2:", size=(15, 1)), sg.Input(d.get('ins2', ''), key='-INS2-')], [sg.Text("Profesor 3:", size=(15, 1)), sg.Input(d.get('ins3', ''), key='-INS3-')], [sg.Text("Sostén:", size=(15, 1)), sg.Input(d.get('sostegno', ''), key='-SOST-')], [sg.Text("Anotaciones:", size=(15, 1)), sg.Multiline(d.get('annotations', ''), size=(35, 4), key='-ANNOT-')], [sg.Submit("Guardar"), sg.Cancel("Cancelar")]]
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
        [sg.Button("Cuestionario", key='-NAV_TO_QUESTIONNAIRE-', disabled=True), sg.Push(), sg.Button("Volver a Grupos", key='-BACK_TO_GROUPS-')]
    ]
    
    # <-- CAMBIO CLAVE: Se añade 'scrollable=True' a la columna que contiene el contenido principal
    layout = [
        [form_frame], 
        [sg.Column(main_content, key='-MAIN_MEMBER_COL-', expand_x=True, expand_y=True, scrollable=True)]
    ]
    return layout

def create_layout_form_member(is_new=True, initial_data=None):
    d = initial_data or {}; title = "Nuevo Miembro" if is_new else "Modificar Miembro"
    layout = [[sg.Text(title, font=("Helvetica", 14))], [sg.Text("Apellido:", size=(15,1)), sg.Input(d.get('cognome', '').title(), key='-COGNOME-')], [sg.Text("Nombre:", size=(15,1)), sg.Input(d.get('nome', '').title(), key='-NOME-')], [sg.Text("Iniciales (3-4):", size=(15,1)), sg.Input(d.get('iniz', ''), key='-INIZ-', size=(10,1))], [sg.Text("Sexo:"), sg.Radio("Masculino", "SEXO", key='-SEXO_M-', default=d.get('sexo') == 'Masculino'), sg.Radio("Femenino", "SEXO", key='-SEXO_F-', default=d.get('sexo') == 'Femenino'), sg.Radio("Desconocido", "SEXO", key='-SEXO_D-', default=d.get('sexo', 'Desconocido') not in ['Masculino', 'Femenino'])], [sg.Text("Fecha Nacimiento:", size=(15,1)), sg.Input(d.get('fecha_nac', ''), key='-DOB-')], [sg.Text("Anotaciones:"), sg.Multiline(d.get('annotations', ''), size=(35,4), key='-ANNOT-')], [sg.Submit("Guardar"), sg.Cancel("Cancelar")]]
    return layout

def create_layout_questionnaire(questionnaire_data, member_name, institution_name, group_name):
    """
    Crea el layout para la ventana INDEPENDIENTE del cuestionario.
    Usa el método robusto con VPush para garantizar la funcionalidad de los botones.
    """
    title = f"Cuestionario para: {member_name}"
    subtitle = f"Institución: {institution_name} | Grupo: {group_name}"

    header_layout = [
        [sg.Text(title, font=("Helvetica", 16))],
        [sg.Text(subtitle, font=("Helvetica", 10))]
    ]
    
    body_rows = []
    if not questionnaire_data['success']:
        body_rows.append([sg.Text(questionnaire_data['message'], text_color='red')])
    elif not questionnaire_data['questions']:
        body_rows.append([sg.Text("No hay preguntas definidas para este grupo.")])
    else:
        for q in questionnaire_data['questions']:
            options = [opt[0] for opt in q['options'] if opt[1] not in [None, '']]
            selections = questionnaire_data['saved_responses'].get(q['data_key'], [])
            rows_for_frame = []
            for i in range(q['max_selections']):
                default_val = selections[i] if i < len(selections) else 'Seleccionar'
                rows_for_frame.append([
                    sg.Text(f"Elección {i+1}:", size=(10, 1)),
                    sg.Combo(['Seleccionar'] + options, default_value=default_val, key=f"-Q_{q['data_key']}_{i}-", readonly=True, expand_x=True)
                ])
            body_rows.append([sg.Frame(q['text'], rows_for_frame, expand_x=True)])

    footer_layout = [
        [sg.HorizontalSeparator()],
        [sg.Button("Guardar", key='-SAVE_Q-'),
         sg.Button("PDF Plantilla", key='-PDF_TEMPLATE_Q-'),
         sg.Button("Gestionar Preguntas", key='-MANAGE_Q-'),
         sg.Push(),
         sg.Button("Volver a Miembros", key='-BACK_TO_MEMBERS-')]
    ]

    layout = [[
        sg.Column(
            header_layout +
            [[sg.Column(body_rows, expand_x=True, expand_y=True, scrollable=True, vertical_scroll_only=True)]] +
            [[sg.VPush()]] +
            footer_layout,
            expand_x=True, expand_y=True
        )
    ]]
    return layout

def create_layout_question_management(institution_name, group_name):
    layout = [[sg.Text("Gestionar Preguntas", font=("Helvetica", 16))], [sg.Text(f"Para: {group_name} ({institution_name})")], [sg.Listbox(values=[], size=(80, 20), key='-Q_LIST-', enable_events=True)], [sg.Button("Nueva Pregunta", key='-NEW_Q-'), sg.Button("Modificar Pregunta", key='-MOD_Q-', disabled=True), sg.Button("Eliminar Pregunta", key='-DEL_Q-', disabled=True)], [sg.Button("Volver", key='-BACK_TO_Q-')]]
    return layout

def create_layout_question_management(institution_name, group_name):
    form_frame = sg.Frame("", [
        [sg.Text("", font=("Helvetica", 14), key='-FORM_Q_TITLE-')],
        [sg.Text("ID Único:", size=(20,1)), sg.Input(key='-FORM_Q_ID-')],
        [sg.Text("Texto Pregunta:", size=(20,1)), sg.Multiline(size=(40,3), key='-FORM_Q_TEXT-')],
        [sg.Text("Tipo/Categoría:", size=(20,1)), sg.Input(key='-FORM_Q_TYPE-')],
        [sg.Text("Clave de Datos:", size=(20,1)), sg.Input(key='-FORM_Q_DK-')],
        [sg.Text("Polaridad:"), sg.Radio("Positiva", "POL", key='-FORM_Q_POL_POS-'), sg.Radio("Negativa", "POL", key='-FORM_Q_POL_NEG-')],
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
    
    # <-- CAMBIO CLAVE: Se añade 'scrollable=True' a la columna que contiene el contenido principal
    layout = [
        [form_frame], 
        [sg.Column(main_content, key='-MAIN_Q_COL-', expand_x=True, expand_y=True, scrollable=True)]
    ]
    return layout


def create_layout_sociogram(institution_name, group_name, relation_options, participant_options):
    """
    VERSIÓN DEFINITIVA Y CORRECTA: Replica la estructura funcional de la
    vista de CSV, colocando TODO el contenido, incluyendo los botones,
    dentro de una única Columna scrollable para garantizar su funcionalidad.
    """
    log_message(f"Creando layout de Sociograma (v. funcional): {group_name}", 'info')

    # --- Definición de los controles (esta parte no cambia) ---
    checkboxes_layout = []
    if relation_options:
        checkboxes_layout = [[sg.Checkbox(opt['label'], default=True, key=f"-SOC_REL__{opt['data_key']}__")] for opt in relation_options]
    else:
        checkboxes_layout = [[sg.Text("No hay relaciones para seleccionar.")]]
    relation_frame = sg.Frame("Relaciones a Incluir", [
        [sg.Column(checkboxes_layout, size=(300, 150), scrollable=True, vertical_scroll_only=True)],
        [sg.Button("Todas", key='-SOC_SEL_ALL-'), sg.Button("Ninguna", key='-SOC_SEL_NONE-'), sg.Button("Positivas", key='-SOC_SEL_POS-'), sg.Button("Negativas", key='-SOC_SEL_NEG-')]
    ], expand_y=True)
    filter_frame = sg.Frame("Filtro por Sexo", [
        [sg.Text("Nodos (Miembros):")],
        [sg.Radio("Todos", "GENDER_FILTER", default=True, key='-SOC_GENDER_ALL-'), sg.Radio("Masculino", "GENDER_FILTER", key='-SOC_GENDER_M-'), sg.Radio("Femenino", "GENDER_FILTER", key='-SOC_GENDER_F-')],
        [sg.HorizontalSeparator()],
        [sg.Text("Aristas (Conexiones):")],
        [sg.Radio("Todas", "CONN_GENDER", default=True, key='-SOC_CONN_ALL-'), sg.Radio("Mismo Sexo", "CONN_GENDER", key='-SOC_CONN_SAME-'), sg.Radio("Diferente Sexo", "CONN_GENDER", key='-SOC_CONN_DIFF-')]
    ])
    left_col_layout = sg.Column([[relation_frame], [filter_frame]], vertical_alignment='top')
    style_frame = sg.Frame("Estilos y Etiquetas", [
        [sg.Text("Etiquetas Nodos:"), sg.Combo(['Iniciales', 'Nombre Apellido', 'Anónimo'], default_value='Iniciales', key='-SOC_LABEL_MODE-', readonly=True, size=(20,1))],
        [sg.Checkbox("Estilo de Arista Recíproca", default=True, key='-SOC_RECIPROCAL_STYLE-')],
        [sg.Checkbox("Mostrar Nodos Aislados", default=True, key='-SOC_SHOW_ISOLATES-')],
        [sg.Checkbox("Mostrar solo Miembros Activos", key='-SOC_ACTIVE_ONLY-')]
    ])
    color_role_frame = sg.Frame("Coloreado por Rol", [
        [sg.Checkbox("Solo Reciben / Auto-eligen", key='-SOC_COLOR_RECEIVERS-')],
        [sg.Checkbox("En Relación Recíproca", key='-SOC_COLOR_RECIP_NODES-')]
    ])
    analysis_frame = sg.Frame("Análisis y Resaltado", [
        [sg.Text("Foco en un Participante:")],
        [sg.Combo([p[0] for p in participant_options], default_value=participant_options[0][0] if participant_options else '', size=(25, 1), key='-SOC_FOCUS_PARTICIPANT-', readonly=True)],
        [sg.Radio("Todas Conexiones", "FOCUS_MODE", default=True, key='-SOC_FOCUS_ALL-'), sg.Radio("Salientes", "FOCUS_MODE", key='-SOC_FOCUS_OUT-'), sg.Radio("Entrantes", "FOCUS_MODE", key='-SOC_FOCUS_IN-')],
        [sg.HorizontalSeparator()],
        [sg.Text("Resaltar Líderes (por elecciones positivas):")],
        [sg.Radio("Ninguno", "HIGHLIGHT", default=True, key='-SOC_HL_NONE-', enable_events=True), sg.Radio("Top N", "HIGHLIGHT", key='-SOC_HL_TOPN-', enable_events=True), sg.Radio("K-ésimo", "HIGHLIGHT", key='-SOC_HL_KTH-', enable_events=True)],
        [sg.Text("Valor (N o K):", size=(12,1)), sg.Input("1", size=(5,1), key='-SOC_HL_VALUE-', disabled=True)],
    ])
    right_col_layout = sg.Column([[style_frame], [color_role_frame], [analysis_frame]], vertical_alignment='top')
    top_controls_layout = [[left_col_layout, sg.VSeperator(), right_col_layout]]
    info_layout = [
        [sg.Text("Instrucciones:", font=("Helvetica", 10, "bold"))],
        [sg.Text("1. Selecciona los filtros y relaciones deseados.")],
        [sg.Text("2. Haz clic en 'Generar y Ver Sociograma'.")],
        [sg.Text("3. Se abrirá una nueva ventana con el grafo interactivo.")],
        [sg.Text("4. En esa ventana, puedes arrastrar los nodos, hacer zoom, etc.")],
        [sg.Text("5. CIERRA LA VENTANA DEL SOCIOGRAMA para volver a esta pantalla.")]
    ]

    # --- INICIO DE LA CORRECCIÓN ---

    # 1. Se define UNA ÚNICA lista que contiene todas las filas de la vista
    main_content = [
        [sg.Text(f"Sociograma Interactivo: {group_name} ({institution_name})", font=("Helvetica", 16))],
        [sg.Frame("Opciones de Visualización", top_controls_layout, expand_x=True)],
        [sg.Frame("Uso", info_layout, expand_x=True)],
        [sg.HorizontalSeparator()],
        # La fila de botones AHORA ESTÁ DENTRO de esta lista principal
        [sg.Button("Generar y Ver Sociograma", key='-SOC_GENERATE_INTERACTIVE-'),
         sg.Push(),
         sg.Button("Volver a Grupos", key='-BACK_TO_GROUPS-')]
    ]
    
    # 2. Toda la vista se envuelve en UNA ÚNICA COLUMNA con scroll
    layout = [[sg.Column(main_content, scrollable=True, vertical_scroll_only=True, expand_x=True, expand_y=True)]]
    
    return layout

    # --- FIN DE LA CORRECCIÓN ---

def create_layout_sociomatrix(institution_name, group_name):
    """
    VERSIÓN FINAL Y DEFINITIVA: Crea el layout de la Matriz Sociométrica,
    asegurando que los encabezados de la tabla y la lista de preguntas se
    generen respetando el orden original de los datos.
    """
    
    # 1. Preparar la sección de PREGUNTAS
    defs = app_data.get_class_question_definitions(institution_name, group_name)
    q_layout_rows = []
    
    if defs:
        # Ordenar las preguntas por su propiedad 'order' para una visualización consistente
        sorted_q_items = sorted(defs.items(), key=lambda item: (item[1].get('order', 99), item[0]))
        for q_id, q_def in sorted_q_items:
            data_key = q_def.get('data_key')
            polarity = q_def.get('polarity')
            widget_key = f"-MATRIXQ__{data_key}__"
            
            # ¡AQUÍ ESTÁ EL CAMBIO CLAVE!
            # Obtenemos la categoría de la pregunta en lugar del texto completo.
            categoria = q_def.get('type', 'General')
            
            # Creamos el checkbox usando la polaridad y la categoría.
            q_layout_rows.append([sg.Checkbox(f"({polarity[:3].title()}) {categoria}", 
                                           key=widget_key, default=True)])
    else:
        q_layout_rows = [[sg.Text("No hay preguntas definidas para este grupo.")]]

    # Crear el contenedor con scroll para las preguntas
    questions_column = sg.Column(
        q_layout_rows, 
        size=(780, 120), 
        scrollable=True, 
        vertical_scroll_only=True
    )
    
    questions_frame = sg.Frame(
        "Preguntas",
        [
            [questions_column],
            [sg.Button("Todas", key='-MATRIX_ALL-'), 
             sg.Button("Ninguna", key='-MATRIX_NONE-'), 
             sg.Button("Positivas", key='-MATRIX_POS-'), 
             sg.Button("Negativas", key='-MATRIX_NEG-')]
        ]
    )
    
    # 2. Pre-calcular los encabezados para la TABLA, respetando el orden original
    # Obtener la lista de miembros SIN ORDENARLA
    temp_members_list = app_data.members_data.get(institution_name, {}).get(group_name, [])
    
    # Crear las iniciales A PARTIR de esa lista original, SIN usar sorted()
    temp_initials = [m.get('iniz','N/A').upper() for m in temp_members_list]
    
    table_headings = ['Nominador'] + temp_initials + ['TOTAL Hechas']
    
    # Definir anchos de columna
    col_widths = [25] + [5] * len(temp_initials) + [10]

    # 3. Definir el layout de la tabla
    table_layout = [[sg.Table(
        values=[[]],
        headings=table_headings, # Usar los encabezados en el orden correcto
        key='-MATRIX_TABLE-',
        justification='center',
        auto_size_columns=False,
        col_widths=col_widths,
        num_rows=25,
        background_color='white', text_color='black',
        header_background_color='#D0D0D0',
        alternating_row_color='#F7F7F7',
        expand_x=True, expand_y=True
    )]]
    
    # 4. Ensamblar el contenido principal de la ventana
    main_content = [
        [sg.Text(f"Matriz Sociométrica: {group_name} ({institution_name})", font=("Helvetica", 16))],
        [questions_frame],
        [sg.Button("Actualizar Matriz", key='-MATRIX_UPDATE-')],
        [sg.Text("Resultado:")],
        [sg.Column(table_layout, expand_x=True, expand_y=True)],
        [sg.Button("PDF Matriz", key='-MATRIX_PDF-'), sg.Push(), sg.Button("Volver", key='-BACK_TO_GROUPS-')]
    ]
    
    # <-- CAMBIO CLAVE: Se envuelve todo el contenido en una columna con scroll
    layout = [[sg.Column(main_content, expand_x=True, expand_y=True, scrollable=True)]]
    return layout

def create_layout_diana(institution_name, group_name, relation_options):
    """
    Crea el layout para la Diana, haciendo que el área de la imagen
    sea expandible para ocupar más espacio en la ventana.
    """
    log_message(f"Creando layout para Diana: {group_name}", 'info')
    
    # --- Columna Izquierda: Controles ---
    checkboxes_layout = []
    if relation_options:
        # CORRECCIÓN: Se añade el campo 'polarity' a la información de cada opción para usarlo después
        defs = app_data.get_class_question_definitions(institution_name, group_name)
        for opt in relation_options:
            polarity = next((d.get('polarity', 'neutral') for d in defs.values() if d.get('data_key') == opt['data_key']), 'neutral')
            checkboxes_layout.append([sg.Checkbox(opt['label'], default=(polarity == 'positive'), key=f"-DIANA_Q__{opt['data_key']}__")])
    else:
        checkboxes_layout = [[sg.Text("No hay preguntas definidas.")]]
        
    questions_column = sg.Column(checkboxes_layout, size=(450, 150), scrollable=True, vertical_scroll_only=True)
    
    controls_layout = [
        [sg.Text("Seleccione preguntas para el cálculo de afinidad:")],
        [questions_column],
        [sg.Checkbox("Mostrar líneas de elección", default=True, key='-DIANA_SHOW_LINES-')],
        # <-- INICIO DEL CAMBIO CLAVE: Añadir keys a los botones -->
        [sg.Button("Todas", key='-DIANA_ALL-'), 
         sg.Button("Ninguna", key='-DIANA_NONE-'), 
         sg.Button("Positivas", key='-DIANA_POS-'), 
         sg.Button("Negativas", key='-DIANA_NEG-')]
        # <-- FIN DEL CAMBIO CLAVE -->
    ]
    
    zoom_controls_layout = [
        [sg.Text("Zoom:", size=(5,1)), 
         sg.Slider(range=(20, 300), default_value=100, resolution=10, orientation='h', key='-DIANA_ZOOM_SLIDER-', enable_events=True, disable_number_display=True),
         sg.Text("100%", key='-DIANA_ZOOM_TEXT-', size=(5,1))]
    ]
    
    left_col = [
        [sg.Frame("Controles", controls_layout)],
        [sg.Button("Generar/Actualizar Diana", key='-DIANA_GENERATE-')],
        [sg.Frame("Visualización", zoom_controls_layout)],
    ]

    # --- Columna Derecha: Imagen ---
    image_layout = [[sg.Image(key='-DIANA_IMAGE-', background_color='white')]]
    
    right_col = [
        [sg.Column(image_layout, size=(800, 800), background_color='white', key='-DIANA_IMAGE_CONTAINER-', expand_x=True, expand_y=True)]
    ]
    
    # --- Ensamblaje del contenido principal ---
    main_content = [
        [sg.Text(f"Diana de Afinidad: {group_name} ({institution_name})", font=("Helvetica", 16))],
        [sg.Column(left_col), sg.Column(right_col, expand_x=True, expand_y=True)],
        [sg.Button("Guardar Diana (PNG)", key='-DIANA_SAVE-', disabled=True), sg.Push(), sg.Button("Volver a Grupos", key='-BACK_TO_GROUPS-')]
    ]
    
    layout = [[sg.Column(main_content, expand_x=True, expand_y=True, scrollable=True)]]
    
    return layout

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
    
    # <-- CAMBIO CLAVE: Se envuelve todo el contenido en una columna con scroll
    layout = [[sg.Column(main_content, expand_x=True, expand_y=True, scrollable=True)]]
    return layout

def create_layout_confirm_polarity(questions_to_confirm):
    layout = [[sg.Text("Confirmación de Polaridad", font=("Helvetica", 14))], [sg.Text("Marque si la pregunta es Positiva (Aceptación).")]]
    for question_text, q_data in questions_to_confirm.items():
        is_neg_guess = any(word in question_text.lower() for word in ['no ', 'evitar', 'nunca', 'rechaz'])
        layout.append([sg.Checkbox(question_text, default=not is_neg_guess, key=q_data['data_key'])])
    layout.append([sg.Button("Confirmar", key='-CONFIRM-'), sg.Button("Cancelar", key='-CANCEL-')])
    return layout

# --- Fin del Bloque 3 ---

# --- BLOQUE 4.1: Función Auxiliar y Formularios ---

def draw_figure(canvas, figure):
    """
    Función auxiliar para dibujar una figura de Matplotlib en un Canvas de Tkinter.
    """
    # Borrar la figura anterior del canvas si existe
    for item in canvas.winfo_children():
        item.destroy()
        
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def window_form_institution(is_new=True, original_data=None):
    layout = create_layout_form_institution(is_new, original_data)
    window = sg.Window("Formulario Institución", layout, modal=True, finalize=True)
    saved = False
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancelar'):
            break
        if event == 'Guardar':
            if is_new:
                success, msg = hinst.handle_add_institution(values['-NAME-'], values['-ANNOT-'])
            else:
                success, msg = hinst.handle_modify_institution(original_data['name'], values['-NAME-'], values['-ANNOT-'])
            sg.popup(msg)
            if success:
                saved = True
                break
    window.close()
    return saved

def window_form_group(institution_name, is_new=True, original_data=None):
    layout = create_layout_form_group(institution_name, is_new, original_data)
    window = sg.Window("Formulario Grupo", layout, modal=True, finalize=True)
    saved = False
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancelar'):
            break
        if event == 'Guardar':
            group_details = {'name': values['-NAME-'], 'coordinator': values['-COORD-'], 'ins2': values['-INS2-'], 'ins3': values['-INS3-'], 'sostegno': values['-SOST-'], 'annotations': values['-ANNOT-']}
            if is_new:
                success, msg = hgrp.handle_add_group(institution_name, group_details)
            else:
                success, msg = hgrp.handle_modify_group(institution_name, original_data['name'], group_details)
            sg.popup(msg)
            if success:
                saved = True
                break
    window.close()
    return saved

def window_form_member(institution_name, group_name, is_new=True, original_data=None):
    layout = create_layout_form_member(is_new, original_data)
    window = sg.Window("Formulario Miembro", layout, modal=True, finalize=True)
    saved = False
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancelar'):
            break
        if event == 'Guardar':
            sexo = 'Masculino' if values['-SEXO_M-'] else 'Femenino' if values['-SEXO_F-'] else 'Desconocido'
            member_details = {'cognome': values['-COGNOME-'], 'nome': values['-NOME-'], 'iniz': values['-INIZ-'], 'sexo': sexo, 'fecha_nac': values['-DOB-'], 'annotations': values['-ANNOT-']}
            if is_new:
                success, msg = hfmember.handle_add_member(institution_name, group_name, member_details)
            else:
                original_name_key = f"{original_data.get('nome','').title()} {original_data.get('cognome','').title()}"
                success, msg = hfmember.handle_modify_member(institution_name, group_name, original_name_key, original_data, member_details)
            sg.popup(msg)
            if success:
                saved = True
                break
    window.close()
    return saved

def window_form_question(is_new=True, initial_data=None, next_order_number=99):
    """
    Abre el formulario para crear o modificar una pregunta.
    
    Args:
        is_new (bool): True si es una pregunta nueva, False si se está modificando.
        initial_data (dict, optional): Datos de la pregunta a modificar.
        next_order_number (int, optional): El siguiente número de orden disponible,
                                           usado solo al crear una nueva pregunta.
    """
    d = initial_data or {}
    title = "Nueva Pregunta" if is_new else "Modificar Pregunta"

    # Determinar el valor para el campo 'Orden'.
    # Si es una pregunta nueva, usa el número calculado que se le pasa.
    # Si se está modificando, usa el valor que ya tenía la pregunta.
    order_value = next_order_number if is_new else d.get('order', '99')

    layout = [
        [sg.Text(title, font=("Helvetica", 14))],
        [sg.Text("ID Único:", size=(20,1)), sg.Input(d.get('id', ''), key='-Q_ID-')],
        [sg.Text("Texto Pregunta:", size=(20,1)), sg.Multiline(d.get('text', ''), size=(40,3), key='-Q_TEXT-')],
        [sg.Text("Tipo/Categoría:", size=(20,1)), sg.Input(d.get('type', ''), key='-Q_TYPE-')],
        [sg.Text("Clave de Datos:", size=(20,1)), sg.Input(d.get('data_key', ''), key='-Q_DK-')],
        [sg.Text("Polaridad:"), sg.Radio("Positiva", "POL", key='-Q_POL_POS-', default=d.get('polarity', 'positive')=='positive'), sg.Radio("Negativa", "POL", key='-Q_POL_NEG-', default=d.get('polarity')=='negative')],
        [sg.Text("Orden:", size=(20,1)), sg.Input(order_value, size=(5,1), key='-Q_ORDER-')],
        [sg.Text("Máx. Selecciones:", size=(20,1)), sg.Input(d.get('max_selections', '2'), size=(5,1), key='-Q_MAX-')],
        [sg.Checkbox("Permitir auto-selección", default=d.get('allow_self_selection', False), key='-Q_SELF-')],
        [sg.Submit("Guardar"), sg.Cancel("Cancelar")]
    ]
    
    window = sg.Window("Formulario Pregunta", layout, modal=True, finalize=True)
    saved = False
    
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancelar'):
            break
        
        if event == 'Guardar':
            try:
                q_data = {
                    'id': values['-Q_ID-'],
                    'text': values['-Q_TEXT-'],
                    'type': values['-Q_TYPE-'],
                    'data_key': values['-Q_DK-'],
                    'polarity': 'positive' if values['-Q_POL_POS-'] else 'negative',
                    'order': int(values['-Q_ORDER-']),
                    'max_selections': int(values['-Q_MAX-']),
                    'allow_self_selection': values['-Q_SELF-']
                }
                
                if is_new:
                    # Llama al handler para añadir la nueva pregunta
                    success, msg = hq.handle_add_question(app_state['current_institution_viewing_groups'], app_state['current_group_viewing_questions'], q_data)
                else:
                    # Llama al handler para modificar la pregunta existente
                    success, msg = hq.handle_modify_question(app_state['current_institution_viewing_groups'], app_state['current_group_viewing_questions'], initial_data['id'], q_data)
                
                sg.popup(msg)
                if success:
                    saved = True
                    break
            except ValueError:
                sg.popup_error("Error: 'Orden' y 'Máximo de Selecciones' deben ser números enteros.")
            except Exception as e:
                sg.popup_error(f"Error inesperado: {e}")
                
    window.close()
    return saved

def window_confirm_import_details(questions_to_confirm):
    """
    Muestra un pop-up para que el usuario confirme la polaridad Y la categoría
    de cada nueva pregunta encontrada en el CSV.
    """
    layout = [
        [sg.Text("Confirmar Detalles de Nuevas Preguntas", font=("Helvetica", 14))],
        [sg.Text("Para cada pregunta, confirma su polaridad (márcala si es positiva) y edita la categoría sugerida si es necesario.")]
    ]

    for question_text, q_data in questions_to_confirm.items():
        data_key = q_data['data_key']
        # Adivinar si la pregunta es negativa para el default del checkbox
        is_neg_guess = any(word in question_text.lower() for word in ['no ', 'evitar', 'nunca', 'rechaz'])
        
        layout += [
            [sg.HorizontalSeparator()],
            [sg.Text(f'Pregunta: "{question_text}"', font=("Helvetica", 10, "bold"))],
            [sg.Checkbox("Es una pregunta Positiva (de aceptación)", default=not is_neg_guess, key=f"pol__{data_key}")],
            [sg.Text("Categoría:", size=(10, 1)), sg.Input(q_data['suggested_category'], key=f"cat__{data_key}", size=(25, 1))]
        ]

    layout.append([sg.Button("Confirmar e Importar", key='-CONFIRM-'), sg.Button("Cancelar", key='-CANCEL-')])
    
    window = sg.Window("Confirmar Detalles de Importación", layout, modal=True, finalize=True)
    
    confirmed_details = None
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, '-CANCEL-'):
            break
        if event == '-CONFIRM-':
            confirmed_details = {}
            for q_text, q_data in questions_to_confirm.items():
                data_key = q_data['data_key']
                polarity = 'positive' if values[f"pol__{data_key}"] else 'negative'
                category = values[f"cat__{data_key}"].strip().capitalize() or "General"
                confirmed_details[data_key] = {'polarity': polarity, 'category': category}
            break
            
    window.close()
    return confirmed_details

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

        # Habilitar/deshabilitar checkboxes dependientes
        if event == '-CSV_OPT_DEFS-':
            is_enabled = values['-CSV_OPT_DEFS-']
            window['-CSV_OPT_ADD_Q_ONLY-'].update(disabled=not is_enabled)
            window['-CSV_OPT_SELF-'].update(disabled=not is_enabled)
            window['-CSV_OPT_EXPAND-'].update(disabled=not is_enabled)
        
        if event == '-CSV_OPT_RESPS-':
            is_enabled = values['-CSV_OPT_RESPS-']
            window['-CSV_OPT_CREATE_MENTIONED-'].update(disabled=not is_enabled)
            
        elif event == '-PDF_INSTRUCTIONS-':
            # ... (esta parte no cambia)
            pdf_bytes, result_or_error = hcsv.handle_generate_instructions_pdf()
            if pdf_bytes:
                try:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    save_path = os.path.join(base_dir, result_or_error) 
                    with open(save_path, 'wb') as f: f.write(pdf_bytes)
                    sg.popup_ok(f"El manual de usuario ha sido generado y guardado en:\n\n{save_path}\n\nSe abrirá a continuación.", title="Manual Generado")
                    webbrowser.open_new(f"file://{save_path}")
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
                
                # --- CAMBIO CLAVE: Pasamos 'tk_parent_window' a la función orquestadora ---
                final_result = hcsv.run_full_csv_import_flow(tk_parent_window, csv_content, import_options, ui_context)
                
                if final_result and final_result.get('status') == 'success':
                    sg.popup_scrolled(final_result['message'], title="Resultado de Importación")
                    data_was_imported = True
                elif final_result and final_result.get('status') == 'error':
                    sg.popup_error(final_result.get('message', 'Ocurrió un error.'))
                # Si es 'cancelled', no se muestra nada.

            except Exception as e:
                sg.popup_error(f"Error al procesar el archivo CSV: {e}\n\n{traceback.format_exc()}")
        
        elif event == '-CSV_EXPORT-':
            # ... (esta parte no cambia)
            selected_groups_str = values['-CSV_OUT_GROUPS-']
            if not selected_groups_str: sg.popup_error("Por favor, selecciona al menos un grupo para exportar."); continue
            groups_to_export = [tuple(s.split(' / ')) for s in selected_groups_str]
            success, data_to_write = hcsv.handle_prepare_data_for_csv_export(groups_to_export)
            if success:
                save_path = sg.popup_get_file("Guardar Exportación CSV", save_as=True, default_extension=".csv", file_types=(("CSV Files", "*.csv"),))
                if save_path:
                    try:
                        with open(save_path, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f); writer.writerows(data_to_write)
                        sg.popup("Exportación completada exitosamente.")
                    except Exception as e: sg.popup_error(f"Error al guardar el archivo: {e}")
            else: sg.popup_error(data_to_write[0][0])
            
        elif event == '-CSV_LOAD_GROUPS-':
            load_all_groups()
    
    window.close()
    return data_was_imported

# --- BLOQUE 4.3: Ventanas de Cuestionario y Gestión de Preguntas ---

# --- EN Red_Sociograma_App.py ---

def window_question_management(institution_name, group_name):
    app_state['current_institution_viewing_groups'] = institution_name
    app_state['current_group_viewing_questions'] = group_name
    layout = create_layout_question_management(institution_name, group_name)
    window = sg.Window("Gestión de Preguntas", layout, modal=True, finalize=True, resizable=True)
    window.maximize()
    
    def refresh_list():
        questions = hq.get_question_definitions_for_group(institution_name, group_name)
        display_list = [f"[{q.get('order', '?')}] {q.get('text', 'Sin texto')} (ID: {qid})" for qid, q in questions]
        window['-Q_LIST-'].update(values=display_list, set_to_index=[])
        window['-MOD_Q-'].update(disabled=True); window['-DEL_Q-'].update(disabled=True)
    
    refresh_list()
    # Valor de retorno por defecto es True (indica que no hay que salir)
    return_value = True 
    
    while True:
        event, values = window.read()
        
        # --- CORRECCIÓN: El cierre de ventana ('X') ahora finaliza la app ---
        if event == sg.WIN_CLOSED:
            return_value = 'exit'
            break
            
        if event == '-BACK_TO_Q-':
            break
            
        selected_q_display = values['-Q_LIST-'][0] if values['-Q_LIST-'] else None
        
        form_is_visible = window['-FORM_Q_FRAME-'].visible
        window['-NEW_Q-'].update(disabled=form_is_visible)
        window['-MOD_Q-'].update(disabled=form_is_visible or not selected_q_display)
        window['-DEL_Q-'].update(disabled=form_is_visible or not selected_q_display)

        # ... (resto de la lógica de la ventana no cambia)
        if event == '-Q_LIST-':
             window['-FORM_Q_FRAME-'].update(visible=False)
        elif event == '-NEW_Q-':
            app_state['form_q_mode'] = 'new'
            current_defs_tuples = hq.get_question_definitions_for_group(institution_name, group_name)
            next_order = max([q_def.get('order', -1) for _, q_def in current_defs_tuples]) + 1 if current_defs_tuples else 0
            window['-FORM_Q_TITLE-'].update("Nueva Pregunta")
            for key in ['-FORM_Q_ID-', '-FORM_Q_TEXT-', '-FORM_Q_TYPE-', '-FORM_Q_DK-']: window[key].update('')
            window['-FORM_Q_ORDER-'].update(next_order); window['-FORM_Q_MAX-'].update('2')
            window['-FORM_Q_POL_POS-'].update(True); window['-FORM_Q_SELF-'].update(False)
            window['-FORM_Q_FRAME-'].update(visible=True)
        elif event == '-MOD_Q-' and selected_q_display:
            app_state['form_q_mode'] = 'modify'
            try: q_id = selected_q_display.split('(ID: ')[1][:-1]
            except IndexError: sg.popup_error("No se pudo identificar la pregunta."); continue
            all_defs = hq.get_question_definitions_for_group(institution_name, group_name)
            original_data_tuple = next(((qid, q_def) for qid, q_def in all_defs if qid == q_id), None)
            if original_data_tuple:
                d = original_data_tuple[1]; app_state['original_q_id'] = q_id
                window['-FORM_Q_TITLE-'].update(f"Modificar Pregunta (ID: {q_id})"); window['-FORM_Q_ID-'].update(q_id)
                window['-FORM_Q_TEXT-'].update(d.get('text', '')); window['-FORM_Q_TYPE-'].update(d.get('type', ''))
                window['-FORM_Q_DK-'].update(d.get('data_key', '')); window['-FORM_Q_ORDER-'].update(d.get('order', '99'))
                window['-FORM_Q_MAX-'].update(d.get('max_selections', '2'))
                window['-FORM_Q_POL_POS-'].update(d.get('polarity', 'positive') == 'positive'); window['-FORM_Q_POL_NEG-'].update(d.get('polarity') == 'negative')
                window['-FORM_Q_SELF-'].update(d.get('allow_self_selection', False))
                window['-FORM_Q_FRAME-'].update(visible=True)
        elif event == '-DEL_Q-' and selected_q_display:
            try: q_id = selected_q_display.split('(ID: ')[1][:-1]
            except IndexError: sg.popup_error("No se pudo identificar la pregunta."); continue
            if sg.popup_yes_no(f"¿Eliminar '{q_id}' y sus respuestas?", title="Confirmar") == 'Yes':
                success, msg = hq.handle_delete_question(institution_name, group_name, q_id)
                sg.popup(msg)
                if success:
                    refresh_list()
        elif event == '-FORM_Q_CANCEL-':
            window['-FORM_Q_FRAME-'].update(visible=False)
        elif event == '-FORM_Q_SAVE-':
            try:
                q_data = {'id': values['-FORM_Q_ID-'], 'text': values['-FORM_Q_TEXT-'], 'type': values['-FORM_Q_TYPE-'], 'data_key': values['-FORM_Q_DK-'], 'polarity': 'positive' if values['-FORM_Q_POL_POS-'] else 'negative', 'order': int(values['-FORM_Q_ORDER-']), 'max_selections': int(values['-FORM_Q_MAX-']), 'allow_self_selection': values['-FORM_Q_SELF-']}
                if app_state.get('form_q_mode') == 'new':
                    success, msg = hq.handle_add_question(institution_name, group_name, q_data)
                else:
                    success, msg = hq.handle_modify_question(institution_name, group_name, app_state.get('original_q_id'), q_data)
                sg.popup(msg)
                if success:
                    window['-FORM_Q_FRAME-'].update(visible=False)
                    refresh_list()
            except ValueError: sg.popup_error("'Orden' y 'Máx. Selecciones' deben ser números enteros.")
            except Exception as e: sg.popup_error(f"Error: {e}")
    
    window.close()
    return return_value


def window_questionnaire(institution_name, group_name, member_name):
    """
    Lanza y gestiona la ventana del Cuestionario de forma AISLADA.
    """
    q_data = hquest.get_questionnaire_data_for_member(institution_name, group_name, member_name, app_data_ref=app_data)
    layout = create_layout_questionnaire(q_data, member_name, institution_name, group_name)
    
    window = sg.Window("Cuestionario", layout, finalize=True, resizable=True)
    window.maximize()
    
    action, data = 'open_members', {'school': institution_name, 'class_name': group_name}

    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-BACK_TO_MEMBERS-'):
            break # Cierra esta ventana y vuelve al bucle principal

        if event == sg.WIN_CLOSED:
            action = 'exit'
            break
        
        if event == '-SAVE_Q-':
            # Lógica de guardado (sin cambios)
            responses = {}
            for q in q_data.get('questions', []):
                selections = [values.get(f"-Q_{q['data_key']}_{i}-") for i in range(q['max_selections']) if values.get(f"-Q_{q['data_key']}_{i}-") and values.get(f"-Q_{q['data_key']}_{i}-") != 'Seleccionar']
                responses[q['data_key']] = selections
            success, msg = hquest.save_questionnaire_responses(institution_name, group_name, member_name, responses)
            sg.popup(msg)

        elif event == '-PDF_TEMPLATE_Q-':
            # Lógica de PDF (sin cambios)
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
            
            # Si se modificaron las preguntas, debemos recargar esta ventana
            sg.popup("Las preguntas han cambiado. El cuestionario se recargará.")
            action = 'open_questionnaire'
            data = {'school': institution_name, 'class_name': group_name, 'member': member_name}
            break
            
    window.close()
    return action, data
# --- BLOQUE 4.4: Ventanas de Navegación Principales (Instituciones y Grupos) ---

def window_institutions():
    """Lanza y gestiona la ventana principal de Instituciones en tamaño normal."""
    layout = create_layout_institutions()
    
    # Se crea la ventana en su tamaño por defecto. Es redimensionable.
    window = sg.Window("Tabla de Instituciones", layout, finalize=True, resizable=True)
    
    def refresh_list():
        """Refresca la lista de instituciones y resetea los controles."""
        institutions = sorted(list(app_data.schools_data.keys()))
        window['-INST_SELECT-'].update(values=institutions, set_to_index=[])
        window['-INST_ANNOTATIONS-'].update('')
        window['-MOD_INST-'].update(disabled=True)
        window['-DEL_INST-'].update(disabled=True)
        window['-VIEW_GROUPS-'].update(disabled=True)

    refresh_list()
    action, data = None, None
    
    while True:
        event, values = window.read()
        
        # El cierre de la ventana principal ('X') finaliza toda la aplicación.
        if event in (sg.WIN_CLOSED, '-EXIT-'):
            action = 'exit'
            break
            
        selected_inst = values['-INST_SELECT-'][0] if values['-INST_SELECT-'] else None
        
        # Lógica para deshabilitar botones mientras el formulario está visible.
        form_is_visible = window['-FORM_INST_FRAME-'].visible
        window['-NEW_INST-'].update(disabled=form_is_visible)
        window['-MOD_INST-'].update(disabled=form_is_visible or not selected_inst)
        window['-DEL_INST-'].update(disabled=form_is_visible or not selected_inst)
        window['-VIEW_GROUPS-'].update(disabled=form_is_visible or not selected_inst)
        
        if event == '-INST_SELECT-':
            window['-FORM_INST_FRAME-'].update(visible=False)
            window['-INST_ANNOTATIONS-'].update(app_data.schools_data.get(selected_inst, "") if selected_inst else "")
        elif event == '-NEW_INST-':
            app_state['form_inst_mode'] = 'new'
            window['-FORM_INST_TITLE-'].update("Nueva Institución")
            window['-FORM_INST_NAME-'].update(''); window['-FORM_INST_ANNOT-'].update('')
            window['-FORM_INST_FRAME-'].update(visible=True)
        elif event == '-MOD_INST-' and selected_inst:
            app_state['form_inst_mode'] = 'modify'; app_state['original_inst_name'] = selected_inst
            window['-FORM_INST_TITLE-'].update(f"Modificar: {selected_inst}")
            window['-FORM_INST_NAME-'].update(selected_inst); window['-FORM_INST_ANNOT-'].update(values['-INST_ANNOTATIONS-'])
            window['-FORM_INST_FRAME-'].update(visible=True)
        elif event == '-FORM_INST_SAVE-':
            form_name = values['-FORM_INST_NAME-']; form_annot = values['-FORM_INST_ANNOT-']
            if app_state.get('form_inst_mode') == 'new':
                success, msg = hinst.handle_add_institution(form_name, form_annot)
            else:
                success, msg = hinst.handle_modify_institution(app_state.get('original_inst_name'), form_name, form_annot)
            sg.popup(msg)
            if success:
                window['-FORM_INST_FRAME-'].update(visible=False)
                refresh_list()
        elif event == '-FORM_INST_CANCEL-':
            window['-FORM_INST_FRAME-'].update(visible=False)
        elif event == '-VIEW_GROUPS-' and selected_inst:
            action, data = 'open_groups', selected_inst
            break
        elif event == '-DEL_INST-' and selected_inst:
            if sg.popup_yes_no(f"¿Eliminar '{selected_inst}' y TODOS sus datos?", title="Confirmar") == 'Yes':
                success, msg = hinst.handle_delete_institution(selected_inst)
                sg.popup(msg)
                if success:
                    refresh_list()
        elif event == '-MANAGE_CSV-':
            if window_csv_management({'school': selected_inst, 'group': None}):
                log_message("Datos importados, refrescando instituciones.")
                refresh_list()
    
    window.close()
    return action, data

def window_groups(institution_name):
    """Lanza y gestiona la ventana de Grupos en tamaño normal."""
    app_state['current_institution_viewing_groups'] = institution_name
    layout = create_layout_groups(institution_name)
    
    # Se crea la ventana en su tamaño por defecto. Es redimensionable.
    window = sg.Window(f"Grupos de: {institution_name}", layout, finalize=True, resizable=True)

    def refresh_list():
        """Refresca la lista de grupos y resetea los controles."""
        groups = sorted([g['name'] for g in app_data.classes_data.get(institution_name, [])])
        window['-GROUP_SELECT-'].update(values=groups, set_to_index=[])
        for key in ['-MOD_GROUP-', '-DEL_GROUP-', '-VIEW_MEMBERS-', '-VIEW_SOCIOGRAM-', '-VIEW_MATRIX-', '-VIEW_DIANA-', '-PDF_SUMMARY-']:
            if key in window.key_dict: window[key].update(disabled=True)
        for key in ['-GROUP_COORD-', '-GROUP_INS2-', '-GROUP_INS3-', '-GROUP_SOST-', '-GROUP_ANNOT-']: window[key].update('')
    
    refresh_list()
    action, data = 'open_institutions', institution_name
    
    while True:
        event, values = window.read()
        
        # El cierre de la ventana ('X') finaliza toda la aplicación.
        if event == sg.WIN_CLOSED:
            action = 'exit'
            break
        
        # El botón de "Volver" nos lleva a la pantalla anterior.
        if event == '-BACK_TO_INST-':
            break 
            
        selected_group = values['-GROUP_SELECT-'][0] if values['-GROUP_SELECT-'] else None
        
        # Lógica para deshabilitar botones mientras el formulario está visible.
        form_is_visible = window['-FORM_GROUP_FRAME-'].visible
        window['-NEW_GROUP-'].update(disabled=form_is_visible)
        window['-MOD_GROUP-'].update(disabled=form_is_visible or not selected_group)
        window['-DEL_GROUP-'].update(disabled=form_is_visible or not selected_group)
        window['-VIEW_MEMBERS-'].update(disabled=form_is_visible or not selected_group)
        window['-VIEW_SOCIOGRAM-'].update(disabled=form_is_visible or not selected_group)
        window['-VIEW_MATRIX-'].update(disabled=form_is_visible or not selected_group)
        window['-VIEW_DIANA-'].update(disabled=form_is_visible or not selected_group)
        
        if event == '-GROUP_SELECT-':
            is_valid = selected_group is not None
            for key in ['-MOD_GROUP-', '-DEL_GROUP-', '-VIEW_MEMBERS-', '-VIEW_SOCIOGRAM-', '-VIEW_MATRIX-', '-VIEW_DIANA-', '-PDF_SUMMARY-']:
                if key in window.key_dict: window[key].update(disabled=not is_valid)
            group_info = next((g for g in app_data.classes_data.get(institution_name, []) if g['name'] == selected_group), {}) if is_valid else {}
            window['-GROUP_COORD-'].update(group_info.get('coordinator', '')); window['-GROUP_INS2-'].update(group_info.get('ins2', '')); window['-GROUP_INS3-'].update(group_info.get('ins3', '')); window['-GROUP_SOST-'].update(group_info.get('sostegno', '')); window['-GROUP_ANNOT-'].update(group_info.get('annotations', ''))
            window['-FORM_GROUP_FRAME-'].update(visible=False)
        elif event == '-NEW_GROUP-':
            app_state['form_group_mode'] = 'new'
            window['-FORM_GROUP_TITLE-'].update("Nuevo Grupo")
            for key in ['-FORM_GROUP_NAME-', '-FORM_GROUP_COORD-', '-FORM_GROUP_INS2-', '-FORM_GROUP_INS3-', '-FORM_GROUP_SOST-', '-FORM_GROUP_ANNOT-']: window[key].update('')
            window['-FORM_GROUP_FRAME-'].update(visible=True)
        elif event == '-MOD_GROUP-' and selected_group:
            app_state['form_group_mode'] = 'modify'; app_state['original_group_name'] = selected_group
            group_info = next((g for g in app_data.classes_data.get(institution_name, []) if g['name'] == selected_group), {})
            window['-FORM_GROUP_TITLE-'].update(f"Modificar: {selected_group}")
            window['-FORM_GROUP_NAME-'].update(group_info.get('name', '')); window['-FORM_GROUP_COORD-'].update(group_info.get('coordinator', '')); window['-FORM_GROUP_INS2-'].update(group_info.get('ins2', '')); window['-FORM_GROUP_INS3-'].update(group_info.get('ins3', '')); window['-FORM_GROUP_SOST-'].update(group_info.get('sostegno', '')); window['-FORM_GROUP_ANNOT-'].update(group_info.get('annotations', ''))
            window['-FORM_GROUP_FRAME-'].update(visible=True)
        elif event == '-FORM_GROUP_SAVE-':
            group_details = {'name': values['-FORM_GROUP_NAME-'], 'coordinator': values['-FORM_GROUP_COORD-'], 'ins2': values['-FORM_GROUP_INS2-'], 'ins3': values['-FORM_GROUP_INS3-'], 'sostegno': values['-FORM_GROUP_SOST-'], 'annotations': values['-FORM_GROUP_ANNOT-']}
            if app_state.get('form_group_mode') == 'new':
                success, msg = hgrp.handle_add_group(institution_name, group_details)
            else:
                success, msg = hgrp.handle_modify_group(institution_name, app_state.get('original_group_name'), group_details)
            sg.popup(msg)
            if success:
                window['-FORM_GROUP_FRAME-'].update(visible=False)
                refresh_list()
        elif event == '-FORM_GROUP_CANCEL-':
            window['-FORM_GROUP_FRAME-'].update(visible=False)
        elif event == '-DEL_GROUP-' and selected_group:
            if sg.popup_yes_no(f"¿Eliminar grupo '{selected_group}'?", title="Confirmar") == 'Yes':
                success, msg = hgrp.handle_delete_group(institution_name, selected_group)
                sg.popup(msg)
                if success:
                    refresh_list()
        elif event in ['-VIEW_MEMBERS-', '-VIEW_SOCIOGRAM-', '-VIEW_MATRIX-', '-VIEW_DIANA-'] and selected_group:
            action_map = {'-VIEW_MEMBERS-': 'open_members', '-VIEW_SOCIOGRAM-': 'open_sociogram', '-VIEW_MATRIX-': 'open_matrix', '-VIEW_DIANA-': 'open_diana'}
            action, data = action_map[event], {'school': institution_name, 'class_name': selected_group}
            break
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
            
    window.close()
    return action, data
# --- BLOQUE 4.5: Ventanas de Navegación Secundarias (Miembros, Sociograma, Matriz, Diana) ---

def window_members(institution_name, group_name):
    """Lanza y gestiona la ventana de Miembros en tamaño normal."""
    app_state['current_group_viewing_members'] = {'school': institution_name, 'class_name': group_name}
    layout = create_layout_members(institution_name, group_name)
    
    # Se crea la ventana en su tamaño por defecto. Es redimensionable.
    window = sg.Window(f"Miembros de: {group_name}", layout, finalize=True, resizable=True)

    def refresh_list():
        """Refresca la lista de miembros y resetea los controles."""
        members_list = app_data.members_data.get(institution_name, {}).get(group_name, [])
        member_names = hutils.generar_opciones_dropdown_miembros_main_select(members_list)
        window['-MEMBER_SELECT-'].update(values=member_names, set_to_index=[])
        for key in ['-MEMBER_COGNOME-', '-MEMBER_NOME-', '-MEMBER_INIZ-', '-MEMBER_ANNOT-']: window[key].update('')
        for key in ['-MOD_MEMBER-', '-DEL_MEMBER-', '-VIEW_QUESTIONNAIRE-']: window[key].update(disabled=True)
    
    refresh_list()
    action, data = 'open_groups', institution_name
    
    while True:
        event, values = window.read()
        
        # El cierre de la ventana ('X') finaliza toda la aplicación.
        if event == sg.WIN_CLOSED:
            action = 'exit'
            break
        
        # El botón de "Volver" nos lleva a la pantalla anterior.
        if event == '-BACK_TO_GROUPS-':
            break
            
        selected_name = values['-MEMBER_SELECT-'][0] if values['-MEMBER_SELECT-'] else None
        
        # Lógica para deshabilitar botones mientras el formulario está visible.
        form_is_visible = window['-FORM_MEMBER_FRAME-'].visible
        window['-NEW_MEMBER-'].update(disabled=form_is_visible)
        window['-MOD_MEMBER-'].update(disabled=form_is_visible or not selected_name)
        window['-DEL_MEMBER-'].update(disabled=form_is_visible or not selected_name)
        window['-VIEW_QUESTIONNAIRE-'].update(disabled=form_is_visible or not selected_name)

        if event == '-MEMBER_SELECT-':
            is_valid = selected_name is not None
            # Deshabilitar botones de Modificar/Eliminar/Cuestionario si no hay selección válida.
            window['-MOD_MEMBER-'].update(disabled=not is_valid); window['-DEL_MEMBER-'].update(disabled=not is_valid); window['-VIEW_QUESTIONNAIRE-'].update(disabled=not is_valid)
            
            member_details = {}
            if is_valid:
                members_list = app_data.members_data.get(institution_name, {}).get(group_name, [])
                member_details = next((m for m in members_list if f"{m.get('nome','').title()} {m.get('cognome','').title()}" == selected_name), {})
            
            # Actualizar campos de detalle.
            window['-MEMBER_COGNOME-'].update(member_details.get('cognome', '')); window['-MEMBER_NOME-'].update(member_details.get('nome', '')); window['-MEMBER_INIZ-'].update(member_details.get('iniz', '')); window['-MEMBER_ANNOT-'].update(member_details.get('annotations', ''))
            window['-FORM_MEMBER_FRAME-'].update(visible=False)
        elif event == '-NEW_MEMBER-':
            app_state['form_member_mode'] = 'new'
            window['-FORM_MEMBER_TITLE-'].update("Nuevo Miembro")
            for key in ['-FORM_MEMBER_COGNOME-', '-FORM_MEMBER_NOME-', '-FORM_MEMBER_INIZ-', '-FORM_MEMBER_DOB-', '-FORM_MEMBER_ANNOT-']: window[key].update('')
            window['-FORM_MEMBER_SEXO_D-'].update(True)
            window['-FORM_MEMBER_FRAME-'].update(visible=True)
        elif event == '-MOD_MEMBER-' and selected_name:
            app_state['form_member_mode'] = 'modify'
            members_list = app_data.members_data.get(institution_name, {}).get(group_name, [])
            d = next((m for m in members_list if f"{m.get('nome','').title()} {m.get('cognome','').title()}" == selected_name), {})
            app_state['original_member_data'] = d
            window['-FORM_MEMBER_TITLE-'].update(f"Modificar: {selected_name}")
            window['-FORM_MEMBER_COGNOME-'].update(d.get('cognome', '').title()); window['-FORM_MEMBER_NOME-'].update(d.get('nome', '').title()); window['-FORM_MEMBER_INIZ-'].update(d.get('iniz', ''))
            window['-FORM_MEMBER_SEXO_M-'].update(d.get('sexo') == 'Masculino'); window['-FORM_MEMBER_SEXO_F-'].update(d.get('sexo') == 'Femenino'); window['-FORM_MEMBER_SEXO_D-'].update(d.get('sexo', 'Desconocido') not in ['Masculino', 'Femenino'])
            window['-FORM_MEMBER_DOB-'].update(d.get('fecha_nac', '')); window['-FORM_MEMBER_ANNOT-'].update(d.get('annotations', ''))
            window['-FORM_MEMBER_FRAME-'].update(visible=True)
        elif event == '-FORM_MEMBER_SAVE-':
            sexo = 'Masculino' if values['-FORM_MEMBER_SEXO_M-'] else 'Femenino' if values['-FORM_MEMBER_SEXO_F-'] else 'Desconocido'
            member_details = {'cognome': values['-FORM_MEMBER_COGNOME-'], 'nome': values['-FORM_MEMBER_NOME-'], 'iniz': values['-FORM_MEMBER_INIZ-'], 'sexo': sexo, 'fecha_nac': values['-FORM_MEMBER_DOB-'], 'annotations': values['-FORM_MEMBER_ANNOT-']}
            if app_state.get('form_member_mode') == 'new':
                success, msg = hfmember.handle_add_member(institution_name, group_name, member_details)
            else:
                original_data = app_state.get('original_member_data', {}); original_name_key = f"{original_data.get('nome','').title()} {original_data.get('cognome','').title()}"
                success, msg = hfmember.handle_modify_member(institution_name, group_name, original_name_key, original_data, member_details)
            sg.popup(msg)
            if success:
                window['-FORM_MEMBER_FRAME-'].update(visible=False)
                refresh_list()
        elif event == '-FORM_MEMBER_CANCEL-':
            window['-FORM_MEMBER_FRAME-'].update(visible=False)
        elif event == '-DEL_MEMBER-' and selected_name:
            if sg.popup_yes_no(f"¿Seguro que quieres eliminar a '{selected_name}'?", title="Confirmar") == 'Yes':
                success, msg = hmemb.handle_delete_member(institution_name, group_name, selected_name)
                sg.popup(msg)
                if success:
                    refresh_list()
        elif event == '-VIEW_QUESTIONNAIRE-' and selected_name:
            action, data = 'open_questionnaire', {'school': institution_name, 'class_name': group_name, 'member': selected_name}
            break
    
    window.close()
    return action, data

def run_sociogram_window(file_path):
    """
    Función que se ejecuta en el hilo principal para crear y manejar la ventana
    del sociograma con Tkinter y CEF, utilizando las importaciones globales.
    """
    # Ya no se necesitan importaciones locales ni bloques try-except para ellas.
    # Se asume que 'tk' y 'cef' ya están importados globalmente.
    
    # --- Inicialización de CEF ---
    settings = { "multi_threaded_message_loop": True }
    cef.Initialize(settings=settings)

    class MainApp(tk.Tk):
        """La ventana principal de Tkinter que contendrá el navegador."""
        def __init__(self, file_url):
            super().__init__()
            self.title("Sociograma Interactivo")
            self.geometry("1200x800")
            
            self.browser_frame = tk.Frame(self, bg="white")
            self.browser_frame.pack(fill=tk.BOTH, expand=True)

            window_info = cef.WindowInfo()
            window_info.SetAsChild(self.browser_frame.winfo_id())

            self.browser = cef.CreateBrowserSync(window_info, url=file_url)

            self.browser_frame.bind("<Configure>", self.on_resize)
            self.protocol("WM_DELETE_WINDOW", self.on_close)
            self.message_loop_timer()

        def on_resize(self, event):
            if self.browser:
                self.browser.WasResized()
        
        def message_loop_timer(self):
            cef.MessageLoopWork()
            self.after(10, self.message_loop_timer)

        def on_close(self):
            if self.browser:
                # El argumento True fuerza el cierre inmediato del navegador
                self.browser.CloseBrowser(True)
            self.destroy()

    file_url_for_cef = f'file:///{os.path.abspath(file_path)}'
    
    app = MainApp(file_url_for_cef)
    app.mainloop()
    
    cef.Shutdown()
    print("Ventana de sociograma y proceso CEF cerrados correctamente.")

def window_sociogram(institution_name, group_name):
    """
    Lanza y gestiona la ventana del Sociograma de forma AISLADA.
    """
    # Preparar datos para el layout
    app_state['current_group_viewing_members'] = {'school': institution_name, 'class_name': group_name}
    participant_options = sociogram_utils.get_participant_options(app_state, app_data, hutils)
    relation_options = sociogram_utils.get_relation_options(app_state, app_data)
    
    layout = create_layout_sociogram(institution_name, group_name, relation_options, participant_options)
    
    window = sg.Window("Lanzador de Sociograma Interactivo", layout, finalize=True, resizable=True)
    window.maximize()
    
    action, data = 'open_groups', institution_name

    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-BACK_TO_GROUPS-'):
            break # Cierra esta ventana y devuelve el control

        if event == sg.WIN_CLOSED:
            action = 'exit'
            break
            
        # Lógica de los botones de selección rápida de checkboxes
        if event in ('-SOC_SEL_ALL-', '-SOC_SEL_NONE-', '-SOC_SEL_POS-', '-SOC_SEL_NEG-'):
            for opt in relation_options:
                widget_key = f"-SOC_REL__{opt['data_key']}__"
                if widget_key in window.key_dict:
                    if event == '-SOC_SEL_ALL-': window[widget_key].update(True)
                    elif event == '-SOC_SEL_NONE-': window[widget_key].update(False)
                    elif event == '-SOC_SEL_POS-': window[widget_key].update(opt['polarity'] == 'positive')
                    elif event == '-SOC_SEL_NEG-': window[widget_key].update(opt['polarity'] == 'negative')
        
        # Lógica para habilitar/deshabilitar el campo de valor
        if event in ('-SOC_HL_TOPN-', '-SOC_HL_KTH-'):
            window['-SOC_HL_VALUE-'].update(disabled=False)
        elif event == '-SOC_HL_NONE-':
            window['-SOC_HL_VALUE-'].update(disabled=True)
        
        # Lógica para generar el sociograma
        if event == '-SOC_GENERATE_INTERACTIVE-':
            selected_keys = [k.split('__')[1] for k, v in values.items() if k.startswith('-SOC_REL__') and v]
            if not selected_keys:
                sg.popup_error("Por favor, selecciona al menos una relación para dibujar."); 
                continue

            params = {
                'node_gender_filter': 'Masculino' if values.get('-SOC_GENDER_M-') else 'Femenino' if values.get('-SOC_GENDER_F-') else 'Todos',
                'label_display_mode': 'iniciales' if values.get('-SOC_LABEL_MODE-') == 'Iniciales' else 'nombre_apellido',
                'connection_gender_type': 'mismo_genero' if values.get('-SOC_CONN_SAME-') else 'diferente_genero' if values.get('-SOC_CONN_DIFF-') else 'todas',
                'active_members_filter': values.get('-SOC_ACTIVE_ONLY-', False),
                'nominators_option': values.get('-SOC_SHOW_ISOLATES-', True),
                'received_color_filter': values.get('-SOC_COLOR_RECEIVERS-', False),
                'reciprocal_nodes_color_filter': values.get('-SOC_COLOR_RECIP_NODES-', False),
                'style_reciprocal_links': values.get('-SOC_RECIPROCAL_STYLE-', True),
                'selected_participant_focus': next((val for txt, val in participant_options if txt == values.get('-SOC_FOCUS_PARTICIPANT-')), None),
                'connection_focus_mode': 'outgoing' if values.get('-SOC_FOCUS_OUT-') else 'incoming' if values.get('-SOC_FOCUS_IN-') else 'all',
                'layout_to_use': 'cose',
                'highlight_mode': 'top_n' if values.get('-SOC_HL_TOPN-') else 'k_th' if values.get('-SOC_HL_KTH-') else 'none',
                'highlight_value': int(values.get('-SOC_HL_VALUE-', 1)) if str(values.get('-SOC_HL_VALUE-')).isdigit() else 1
            }
            
            output_path = os.path.join(os.getcwd(), "sociograma_interactivo.html")
            window.set_cursor('watch'); window.refresh()
            html_content = sociogram_engine.generate_interactive_html(
                school_name=institution_name, class_name=group_name, app_data_ref=app_data,
                selected_data_keys=selected_keys, **params
            )
            result_path = sociogram_engine.save_interactive_sociogram(html_content=html_content, output_path=output_path) if html_content else None
            window.set_cursor('arrow')
            
            if result_path:
                webbrowser.open(f'file:///{os.path.abspath(result_path)}')
                sg.popup_ok("El sociograma se ha abierto en tu navegador web.", "Éxito")
            else:
                sg.popup_error("No se pudo generar el archivo del sociograma.")
            
    window.close()
    return action, data

def window_sociomatrix(institution_name, group_name):
    """
    Lanza y gestiona la ventana de la Matriz Sociométrica de forma AISLADA.
    """
    layout = create_layout_sociomatrix(institution_name, group_name)
    window = sg.Window(f"Matriz de: {group_name}", layout, finalize=True, resizable=True)
    window.maximize()
    
    # Poblar dinámicamente la información de los checkboxes
    defs = app_data.get_class_question_definitions(institution_name, group_name)
    q_widgets_info = {} 
    if defs:
        # Ordenar para consistencia visual
        sorted_q_items = sorted(defs.items(), key=lambda item: (item[1].get('order', 99), item[0]))
        for q_id, q_def in sorted_q_items:
            widget_key = f"-MATRIXQ__{q_def.get('data_key')}__"
            q_widgets_info[widget_key] = {'polarity': q_def.get('polarity')}
    
    action, data = 'open_groups', institution_name
    last_generated_header = []
    last_generated_data = []
    
    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-BACK_TO_GROUPS-'):
            break # Cierra esta ventana y devuelve el control

        if event == sg.WIN_CLOSED:
            action = 'exit'
            break
            
        # Lógica para los botones de selección rápida de checkboxes
        if event in ('-MATRIX_ALL-', '-MATRIX_NONE-', '-MATRIX_POS-', '-MATRIX_NEG-'):
            for key, info in q_widgets_info.items():
                if key in window.key_dict:
                    if event == '-MATRIX_ALL-': window[key].update(True)
                    elif event == '-MATRIX_NONE-': window[key].update(False)
                    elif event == '-MATRIX_POS-': window[key].update(info['polarity'] == 'positive')
                    elif event == '-MATRIX_NEG-': window[key].update(info['polarity'] == 'negative')
                    
        elif event == '-MATRIX_UPDATE-':
            selected_keys = [key.split('__')[1] for key, val in values.items() if isinstance(key, str) and key.startswith('-MATRIXQ__') and val]
            if not selected_keys:
                sg.popup_ok("Selecciona al menos una pregunta para generar la matriz."); continue

            result = hsm.handle_draw_sociomatrix_data(institution_name, group_name, selected_keys)
            
            if result and result.get('success'):
                last_generated_header = result.get('header', [])
                last_generated_data = result.get('data', [])
                row_colors = result.get('row_colors', [])
                window['-MATRIX_TABLE-'].update(values=last_generated_data, row_colors=row_colors)
            else:
                last_generated_header, last_generated_data = [], []
                sg.popup_error(result.get('message', "Ocurrió un error."))

        elif event == '-MATRIX_PDF-':
            if not last_generated_header or not last_generated_data:
                sg.popup_error("Primero debes generar una matriz válida."); continue

            pdf_bytes, filename_or_error = pdf_generator.generate_sociomatrix_pdf(institution_name, group_name, last_generated_header, last_generated_data)

            if pdf_bytes:
                save_path = sg.popup_get_file('Guardar PDF', save_as=True, default_extension=".pdf", default_path=filename_or_error)
                if save_path:
                    try:
                        with open(save_path, 'wb') as f: f.write(pdf_bytes)
                        sg.popup(f"Matriz guardada en:\n{save_path}")
                    except Exception as e: sg.popup_error(f"Error al guardar:\n{e}")
            else:
                sg.popup_error(f"No se pudo generar el PDF:\n{filename_or_error}")

    window.close()
    return action, data

def window_diana(institution_name, group_name):
    """
    Lanza y gestiona la ventana de la Diana de Afinidad, AHORA CON
    LA FUNCIONALIDAD DE ZOOM CORREGIDA.
    """
    # Preparar datos para el layout
    app_state['current_group_viewing_members'] = {'school': institution_name, 'class_name': group_name}
    relation_options = sociogram_utils.get_relation_options(app_state, app_data)
    
    layout = create_layout_diana(institution_name, group_name, relation_options)
    window = sg.Window("Diana de Afinidad", layout, finalize=True, resizable=True)
    window.maximize()
    
    original_image_bytes = None
    
    # --- INICIO DE LA CORRECCIÓN ---

    def update_diana_image(zoom_level=100):
        """
        Función auxiliar interna para redimensionar y actualizar la imagen de la diana.
        """
        if not original_image_bytes: return
        try:
            # Se necesita Pillow para esta operación
            from PIL import Image
            img = Image.open(io.BytesIO(original_image_bytes))
            
            # Obtener el tamaño del contenedor para un escalado inicial correcto
            container_size = window['-DIANA_IMAGE_CONTAINER-'].get_size()
            widget_width, widget_height = container_size[0] - 20, container_size[1] - 20
            
            if widget_width <= 0 or widget_height <= 0: return # Evitar errores si la ventana es muy pequeña

            img_width, img_height = img.size
            scale = min(widget_width / img_width, widget_height / img_height) if img_width > 0 and img_height > 0 else 1
            
            # Aplicar el nivel de zoom del slider
            final_scale = scale * (zoom_level / 100.0)
            new_size = (int(img_width * final_scale), int(img_height * final_scale))

            if new_size[0] < 10 or new_size[1] < 10: return # Evitar redimensionar a tamaños minúsculos
            
            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
            
            with io.BytesIO() as bio:
                img_resized.save(bio, format="PNG")
                img_bytes_for_gui = bio.getvalue()
            
            window['-DIANA_IMAGE-'].update(data=img_bytes_for_gui)
            window['-DIANA_ZOOM_TEXT-'].update(f"{int(zoom_level)}%")
        except ImportError:
            log_message("Pillow no está instalado, el zoom no funcionará.", "warning")
        except Exception as e:
            log_message(f"Error al aplicar zoom: {e}", "error")

    # --- FIN DE LA CORRECCIÓN ---

    # Lógica para los botones de selección rápida (sin cambios)
    defs = app_data.get_class_question_definitions(institution_name, group_name)
    q_widgets_info = {}
    if defs:
        for opt in relation_options:
            data_key = opt['data_key']
            widget_key = f"-DIANA_Q__{data_key}__"
            polarity = next((d.get('polarity', 'neutral') for d in defs.values() if d.get('data_key') == data_key), 'neutral')
            q_widgets_info[widget_key] = {'polarity': polarity}

    action = 'open_groups'

    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-BACK_TO_GROUPS-'): break
        if event == sg.WIN_CLOSED: action = 'exit'; break

        # Eventos de los botones de selección rápida
        if event in ('-DIANA_ALL-', '-DIANA_NONE-', '-DIANA_POS-', '-DIANA_NEG-'):
            for key, info in q_widgets_info.items():
                if key in window.key_dict:
                    if event == '-DIANA_ALL-': window[key].update(True)
                    elif event == '-DIANA_NONE-': window[key].update(False)
                    elif event == '-DIANA_POS-': window[key].update(info['polarity'] == 'positive')
                    elif event == '-DIANA_NEG-': window[key].update(info['polarity'] == 'negative')
        
        elif event == '-DIANA_GENERATE-':
            selected_keys = [key.split('__')[1] for key, val in values.items() if isinstance(key, str) and key.startswith('-DIANA_Q__') and val]
            if not selected_keys:
                sg.popup_error("Selecciona al menos una pregunta."); continue
            
            sg.popup_quick_message("Generando Diana...", background_color='lightblue')
            image_bytes = hgrp.handle_generate_diana_data(institution_name, group_name, selected_keys, values['-DIANA_SHOW_LINES-'])
            
            if image_bytes:
                original_image_bytes = image_bytes
                window['-DIANA_SAVE-'].update(disabled=False)
                # --- CORRECCIÓN: Llamar a la función de zoom para el dibujado inicial ---
                update_diana_image(values['-DIANA_ZOOM_SLIDER-'])
            else:
                sg.popup_error("No se pudo generar la imagen.")
                original_image_bytes = None
                window['-DIANA_IMAGE-'].update(data=None)
                window['-DIANA_SAVE-'].update(disabled=True)
        
        # --- INICIO DE LA CORRECCIÓN ---
        # Añadir el manejador de eventos para el slider
        elif event == '-DIANA_ZOOM_SLIDER-':
            if original_image_bytes:
                update_diana_image(values['-DIANA_ZOOM_SLIDER-'])
        # --- FIN DE LA CORRECCIÓN ---
        
        elif event == '-DIANA_SAVE-':
            if original_image_bytes:
                filename = f"Diana_{institution_name}_{group_name}.png".replace('\"','').replace("'", "")
                save_path = sg.popup_get_file('Guardar Diana (PNG)', save_as=True, default_extension=".png", file_types=(("PNG", "*.png"),), default_path=filename)
                if save_path:
                    try:
                        with open(save_path, 'wb') as f: f.write(original_image_bytes)
                        sg.popup("Diana guardada.")
                    except Exception as e: sg.popup_error(f"Error al guardar: {e}")
            else:
                sg.popup_error("Primero genera una diana.")
            
    window.close()
    return action, None

# --- FIN BLOQUE 4.5 ---

# =============================================================================
#  BLOQUE 5: CLASE PRINCIPAL (ARQUITECTURA DE VENTANA ÚNICA - VERSIÓN ESTABLE)
# =============================================================================

class SociogramaApp:
    def __init__(self):
        """Inicializa la aplicación, los datos y la ventana principal."""
        self.app_state = {}
        # Lista de claves para todas las vistas que gestionaremos.
        self.view_keys = [
            '-VIEW_INSTITUTIONS-', '-VIEW_GROUPS-', '-VIEW_MEMBERS-',
            '-VIEW_QUESTIONNAIRE-', '-VIEW_QUESTIONS-', '-VIEW_SOCIOGRAM-',
            '-VIEW_MATRIX-', '-VIEW_DIANA-'
        ]
        
        # --- CAMBIO CLAVE: Crear y ocultar la ventana raíz de Tkinter ---
        # Esta ventana invisible servirá como "parent" para todos los diálogos de Tkinter.
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()
        # --- FIN DEL CAMBIO ---

        self.window = self._create_main_window()

    def _create_main_window(self):
        """
        Crea la ventana principal SIN las vistas de análisis complejas, que
        ahora se lanzan como ventanas independientes.
        """
        # Eliminar las claves de todas las vistas que ahora son ventanas separadas
        keys_to_remove = ['-VIEW_QUESTIONNAIRE-', '-VIEW_SOCIOGRAM-', '-VIEW_MATRIX-', '-VIEW_DIANA-']
        for key in keys_to_remove:
            if key in self.view_keys:
                self.view_keys.remove(key)

        layout = [
            [
                sg.Column(create_layout_institutions(), key='-VIEW_INSTITUTIONS-', visible=True, expand_x=True, expand_y=True),
                sg.Column(create_layout_groups("..."), key='-VIEW_GROUPS-', visible=False, expand_x=True, expand_y=True),
                sg.Column(create_layout_members("...", "..."), key='-VIEW_MEMBERS-', visible=False, expand_x=True, expand_y=True),
                # Todas las vistas de análisis complejas han sido eliminadas de aquí
                sg.Column(create_layout_question_management("...", "..."), key='-VIEW_QUESTIONS-', visible=False, expand_x=True, expand_y=True),
            ]
        ]
        return sg.Window("Suite de Análisis Sociométrico", layout, finalize=True, resizable=True)

    def switch_view(self, view_key_to_show, context_data=None):
        """
        VERSIÓN CORREGIDA: Gestiona el cambio de vistas de forma segura,
        reconstruyendo los layouts solo cuando es estrictamente necesario.
        """
        self.app_state['context'] = context_data
                
        # 1. Oculta todas las vistas
        for key in self.view_keys:
            self.window[key].update(visible=False)
                
        # 2. Muestra solo la vista de destino
        self.window[view_key_to_show].update(visible=True)

        # 3. Decide si refrescar datos o reconstruir el layout completo
        if view_key_to_show in ['-VIEW_INSTITUTIONS-', '-VIEW_GROUPS-', '-VIEW_MEMBERS-', '-VIEW_QUESTIONNAIRE-', '-VIEW_QUESTIONS-']:
            # Para estas vistas, solo necesitamos refrescar el contenido de los widgets existentes
            if view_key_to_show == '-VIEW_INSTITUTIONS-':
                self.refresh_institutions_list()
            elif view_key_to_show == '-VIEW_GROUPS-':
                self.refresh_groups_list(context_data)
            elif view_key_to_show == '-VIEW_MEMBERS-':
                self.refresh_members_list(context_data['school'], context_data['class_name'])
            elif view_key_to_show == '-VIEW_QUESTIONNAIRE-':
                self.refresh_questionnaire_view(context_data['school'], context_data['class_name'], context_data['member'])
            elif view_key_to_show == '-VIEW_QUESTIONS-':
                self.refresh_questions_list(context_data['school'], context_data['class_name'])

        elif view_key_to_show in ['-VIEW_SOCIOGRAM-', '-VIEW_MATRIX-', '-VIEW_DIANA-']:
            # Para las vistas de análisis, SÍ necesitamos reconstruir su layout dinámico
            institution_name = context_data['school']
            group_name = context_data['class_name']
            target_column = self.window[view_key_to_show]

            # Limpiar el contenido viejo para evitar duplicados
            for child in target_column.Widget.winfo_children():
                child.destroy()

            # Crear el nuevo layout basado en el nuevo contexto
            new_layout = [[]] # Valor por defecto
            if view_key_to_show == '-VIEW_SOCIOGRAM-':
                self.app_state['current_group_viewing_members'] = context_data
                participant_options = sociogram_utils.get_participant_options(self.app_state, app_data, hutils)
                relation_options = sociogram_utils.get_relation_options(self.app_state, app_data)
                new_layout = create_layout_sociogram(institution_name, group_name, relation_options, participant_options)
                
            elif view_key_to_show == '-VIEW_MATRIX-':
                new_layout = create_layout_sociomatrix(institution_name, group_name)
                
            elif view_key_to_show == '-VIEW_DIANA-':
                self.app_state['current_group_viewing_members'] = context_data
                relation_options = sociogram_utils.get_relation_options(self.app_state, app_data)
                new_layout = create_layout_diana(institution_name, group_name, relation_options)

            # Añadir el nuevo layout. Esta línea ahora está DENTRO del bloque correcto.
            self.window.extend_layout(target_column, new_layout)

    def run(self):
        """El bucle de eventos principal."""
        self.window.maximize()
        self.refresh_institutions_list()
        
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED or event == '-EXIT-':
                break

            # Despachador de eventos simple basado en qué vista está activa
            active_view = next((key for key in self.view_keys if self.window[key].visible), None)
            
            if active_view == '-VIEW_INSTITUTIONS-':
                self.handle_institutions_events(event, values)
            elif active_view == '-VIEW_GROUPS-':
                self.handle_groups_events(event, values)
            elif active_view == '-VIEW_MEMBERS-':
                self.handle_members_events(event, values)
            elif active_view == '-VIEW_QUESTIONNAIRE-':
                self.handle_questionnaire_events(event, values)
            elif active_view == '-VIEW_QUESTIONS-':
                self.handle_questions_events(event, values)
            elif active_view == '-VIEW_SOCIOGRAM-':
                self.handle_sociogram_events(event, values)
            elif active_view == '-VIEW_MATRIX-':
                self.handle_matrix_events(event, values)
            elif active_view == '-VIEW_DIANA-':
                self.handle_diana_events(event, values)
            
        self.window.close()

    # --- Métodos de Refresco (Ajustados para la nueva arquitectura) ---

    def refresh_institutions_list(self):
        institutions = sorted(list(app_data.schools_data.keys()))
        self.window['-INST_SELECT-'].update(values=institutions, set_to_index=[])
        self.window['-INST_ANNOTATIONS-'].update('')
        self.window['-MOD_INST-'].update(disabled=True)
        self.window['-DEL_INST-'].update(disabled=True)
        self.window['-NAV_TO_GROUPS-'].update(disabled=True)

    def refresh_groups_list(self, institution_name):
        # Actualiza el título de la vista. Esto se hace accediendo al widget de Tkinter subyacente.
        # Esta es una forma segura de cambiar texto estático creado al inicio.
        self.window['-GROUPS_TITLE-'].update(f"Grupos de: {institution_name}")
        
        groups = sorted([g['name'] for g in app_data.classes_data.get(institution_name, [])])
        self.window['-GROUP_SELECT-'].update(values=groups, set_to_index=[])

        buttons_to_disable = ['-MOD_GROUP-', '-DEL_GROUP-', '-NAV_TO_MEMBERS-', '-NAV_TO_SOCIOGRAM-', '-NAV_TO_MATRIX-', '-NAV_TO_DIANA-', '-PDF_SUMMARY-']
        for key in buttons_to_disable:
            if key in self.window.key_dict: self.window[key].update(disabled=True)
        
        text_fields_to_clear = ['-GROUP_COORD-', '-GROUP_INS2-', '-GROUP_INS3-', '-GROUP_SOST-', '-GROUP_ANNOT-']
        for key in text_fields_to_clear:
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

    def refresh_questionnaire_view(self, institution_name, group_name, member_name):
        """
        SOLUCIÓN DEFINITIVA: Actualiza los elementos de la estructura fija
        del cuestionario en lugar de intentar reconstruir layouts complejos.
        """
        # 1. Obtener los datos más recientes del cuestionario
        q_data = hquest.get_questionnaire_data_for_member(institution_name, group_name, member_name, app_data_ref=app_data)
        
        # 2. Actualizar los textos del título y subtítulo
        self.window['-QUESTIONNAIRE_TITLE-'].update(f"Cuestionario para: {member_name}")
        self.window['-QUESTIONNAIRE_SUBTITLE-'].update(f"Institución: {institution_name} | Grupo: {group_name}")
        
        # 3. Obtener la referencia al contenedor de contenido
        content_container = self.window['-QUESTIONNAIRE_CONTENT-']
        
        # 4. Limpiar de forma segura el contenido anterior
        for child in content_container.Widget.winfo_children():
            child.destroy()
        
        # 5. Construir las nuevas filas de preguntas
        new_content_rows = []
        if q_data['success'] and q_data['questions']:
            for q in q_data['questions']:
                options = [opt[0] for opt in q['options'] if opt[1] not in [None, '']]
                selections = q_data['saved_responses'].get(q['data_key'], [])
                
                frame_layout = []
                for i in range(q['max_selections']):
                    default_val = selections[i] if i < len(selections) else 'Seleccionar'
                    frame_layout.append([
                        sg.Text(f"Elección {i+1}:", size=(10, 1)),
                        sg.Combo(['Seleccionar'] + options, default_value=default_val,
                                key=f"-Q_{q['data_key']}_{i}-", readonly=True, expand_x=True)
                    ])
                
                new_content_rows.append([sg.Frame(q['text'], frame_layout, expand_x=True)])
        
        # 6. Añadir las nuevas filas al contenedor
        if new_content_rows:
            self.window.extend_layout(content_container, new_content_rows)
        
        # 7. Habilitar los botones del pie de página
        for key in ['-SAVE_Q-', '-PDF_TEMPLATE_Q-', '-MANAGE_Q-', '-BACK_TO_MEMBERS-']:
            self.window[key].update(disabled=False)
        
        # 8. Refrescar la ventana para que los cambios se muestren
        self.window.refresh()

    def handle_institutions_events(self, event, values):
        """Maneja todos los eventos de la pantalla de Instituciones."""
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
            if sg.popup_yes_no(f"¿Eliminar '{selected_inst}' y TODOS sus datos asociados (grupos, miembros, etc.)?", title="Confirmar Eliminación") == 'Yes':
                success, msg = hinst.handle_delete_institution(selected_inst)
                sg.popup(msg)
                if success:
                    self.refresh_institutions_list()
        elif event == '-MANAGE_CSV-':
            # --- CAMBIO CLAVE: Pasamos self.tk_root como segundo argumento ---
            if window_csv_management({'school': selected_inst, 'group': None}, self.tk_root):
                log_message("Datos importados, refrescando instituciones.")
                self.refresh_institutions_list()

    def handle_groups_events(self, event, values):
        """
        Maneja los eventos de Grupos, asegurando que la ventana principal
        se re-maximice al volver de CUALQUIER ventana de análisis secundaria.
        """
        institution_name = self.app_state.get('context')
        selected_group = values.get('-GROUP_SELECT-')[0] if values.get('-GROUP_SELECT-') else None
        
        # Habilitar/deshabilitar botones (sin cambios)
        form_is_visible = self.window['-FORM_GROUP_FRAME-'].visible
        self.window['-NEW_GROUP-'].update(disabled=form_is_visible)
        self.window['-MOD_GROUP-'].update(disabled=form_is_visible or not selected_group)
        self.window['-DEL_GROUP-'].update(disabled=form_is_visible or not selected_group)
        self.window['-NAV_TO_MEMBERS-'].update(disabled=form_is_visible or not selected_group)
        self.window['-NAV_TO_SOCIOGRAM-'].update(disabled=form_is_visible or not selected_group)
        self.window['-NAV_TO_MATRIX-'].update(disabled=form_is_visible or not selected_group)
        self.window['-NAV_TO_DIANA-'].update(disabled=form_is_visible or not selected_group)

        if event == '-BACK_TO_INST-':
            self.switch_view('-VIEW_INSTITUTIONS-')

        # CASOS ESPECIALES: Ventanas independientes para análisis
        elif event == '-NAV_TO_SOCIOGRAM-' and selected_group:
            self.window.hide()
            action_result, _ = window_sociogram(institution_name, selected_group)
            self.window.un_hide()
            self.window.maximize() # Re-maximizar
            if action_result == 'exit': self.window.write_event_value('-EXIT-', None)

        elif event == '-NAV_TO_MATRIX-' and selected_group:
            self.window.hide()
            action_result, _ = window_sociomatrix(institution_name, selected_group)
            self.window.un_hide()
            self.window.maximize() # Re-maximizar
            if action_result == 'exit': self.window.write_event_value('-EXIT-', None)

        elif event == '-NAV_TO_DIANA-' and selected_group:
            self.window.hide()
            action_result, _ = window_diana(institution_name, selected_group)
            self.window.un_hide()
            self.window.maximize() # <-- CORRECCIÓN AÑADIDA AQUÍ
            if action_result == 'exit': self.window.write_event_value('-EXIT-', None)

        # CASOS NORMALES: Vistas dentro de la ventana principal
        elif event == '-NAV_TO_MEMBERS-' and selected_group:
            context = {'school': institution_name, 'class_name': selected_group}
            self.switch_view('-VIEW_MEMBERS-', context_data=context)
        
        # El resto de la lógica de la función no necesita cambios...
        elif event == '-GROUP_SELECT-':
            is_valid = selected_group is not None
            buttons_to_update = ['-MOD_GROUP-', '-DEL_GROUP-', '-NAV_TO_MEMBERS-', '-NAV_TO_SOCIOGRAM-', '-NAV_TO_MATRIX-', '-NAV_TO_DIANA-', '-PDF_SUMMARY-']
            for key in buttons_to_update: self.window[key].update(disabled=not is_valid)
            group_info = next((g for g in app_data.classes_data.get(institution_name, []) if g['name'] == selected_group), {}) if is_valid else {}
            self.window['-GROUP_COORD-'].update(group_info.get('coordinator', '')); self.window['-GROUP_INS2-'].update(group_info.get('ins2', '')); self.window['-GROUP_INS3-'].update(group_info.get('ins3', '')); self.window['-GROUP_SOST-'].update(group_info.get('sostegno', '')); self.window['-GROUP_ANNOT-'].update(group_info.get('annotations', ''))
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
            self.window['-FORM_GROUP_NAME-'].update(group_info.get('name', '')); self.window['-FORM_GROUP_COORD-'].update(group_info.get('coordinator', '')); self.window['-FORM_GROUP_INS2-'].update(group_info.get('ins2', '')); self.window['-FORM_GROUP_INS3-'].update(group_info.get('ins3', '')); self.window['-FORM_GROUP_SOST-'].update(group_info.get('sostegno', '')); self.window['-FORM_GROUP_ANNOT-'].update(group_info.get('annotations', ''))
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
            if sg.popup_yes_no(f"¿Eliminar grupo '{selected_group}'?", title="Confirmar") == 'Yes':
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
        """
        Maneja los eventos de Miembros, asegurando que la ventana principal
        se re-maximice al volver del Cuestionario.
        """
        context = self.app_state.get('context', {})
        institution_name = context.get('school')
        group_name = context.get('class_name')
        selected_name = values.get('-MEMBER_SELECT-')[0] if values.get('-MEMBER_SELECT-') else None

        # Lógica de habilitación de botones (sin cambios)
        form_is_visible = self.window['-FORM_MEMBER_FRAME-'].visible
        self.window['-NEW_MEMBER-'].update(disabled=form_is_visible)
        self.window['-MOD_MEMBER-'].update(disabled=form_is_visible or not selected_name)
        self.window['-DEL_MEMBER-'].update(disabled=form_is_visible or not selected_name)
        self.window['-NAV_TO_QUESTIONNAIRE-'].update(disabled=form_is_visible or not selected_name)

        # Lógica de eventos
        if event == '-BACK_TO_GROUPS-':
            self.switch_view('-VIEW_GROUPS-', context_data=institution_name)

        elif event == '-NAV_TO_QUESTIONNAIRE-' and selected_name:
            self.window.hide()
            action, data = window_questionnaire(institution_name, group_name, selected_name)
            self.window.un_hide()
            self.window.maximize() # <-- CORRECCIÓN AÑADIDA
            if action == 'exit':
                self.window.write_event_value('-EXIT-', None)
            elif action == 'open_questionnaire':
                # Simular un nuevo clic para recargar el cuestionario si es necesario
                self.window.write_event_value('-NAV_TO_QUESTIONNAIRE-', selected_name)

        # El resto de los eventos de esta función no cambian
        elif event == '-MEMBER_SELECT-':
            self.window['-FORM_MEMBER_FRAME-'].update(visible=False)
            member_details = {}
            if selected_name:
                members_list = app_data.members_data.get(institution_name, {}).get(group_name, [])
                member_details = next((m for m in members_list if f"{m.get('nome','').title()} {m.get('cognome','').title()}" == selected_name), {})
            self.window['-MEMBER_COGNOME-'].update(member_details.get('cognome', '')); self.window['-MEMBER_NOME-'].update(member_details.get('nome', '')); self.window['-MEMBER_INIZ-'].update(member_details.get('iniz', '')); self.window['-MEMBER_ANNOT-'].update(member_details.get('annotations', ''))
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
            self.window['-FORM_MEMBER_COGNOME-'].update(d.get('cognome', '').title()); self.window['-FORM_MEMBER_NOME-'].update(d.get('nome', '').title()); self.window['-FORM_MEMBER_INIZ-'].update(d.get('iniz', ''))
            self.window['-FORM_MEMBER_SEXO_M-'].update(d.get('sexo') == 'Masculino'); self.window['-FORM_MEMBER_SEXO_F-'].update(d.get('sexo') == 'Femenino'); self.window['-FORM_MEMBER_SEXO_D-'].update(d.get('sexo', 'Desconocido') not in ['Masculino', 'Femenino'])
            self.window['-FORM_MEMBER_DOB-'].update(d.get('fecha_nac', '')); self.window['-FORM_MEMBER_ANNOT-'].update(d.get('annotations', ''))
            self.window['-FORM_MEMBER_FRAME-'].update(visible=True)
        elif event == '-FORM_MEMBER_SAVE-':
            sexo = 'Masculino' if values['-FORM_MEMBER_SEXO_M-'] else 'Femenino' if values['-FORM_MEMBER_SEXO_F-'] else 'Desconocido'
            member_details = {'cognome': values['-FORM_MEMBER_COGNOME-'], 'nome': values['-FORM_MEMBER_NOME-'], 'iniz': values['-FORM_MEMBER_INIZ-'], 'sexo': sexo, 'fecha_nac': values['-FORM_MEMBER_DOB-'], 'annotations': values['-FORM_MEMBER_ANNOT-']}
            if self.app_state.get('form_member_mode') == 'new':
                success, msg = hfmember.handle_add_member(institution_name, group_name, member_details)
            else:
                original_data = self.app_state.get('original_member_data', {}); original_name_key = f"{original_data.get('nome','').title()} {original_data.get('cognome','').title()}"
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

    def handle_questionnaire_events(self, event, values):
        """Maneja todos los eventos de la pantalla del Cuestionario."""
        context = self.app_state.get('context', {})
        institution_name = context.get('school')
        group_name = context.get('class_name')
        member_name = context.get('member')

        print(f"EVENTO CAPTURADO EN CUESTIONARIO: {event}")  # Debug
        
        if event == '-BACK_TO_MEMBERS-':
            print("Botón Volver clickeado!")
            context_members = {'school': institution_name, 'class_name': group_name}
            self.switch_view('-VIEW_MEMBERS-', context_data=context_members)
        
        elif event == '-SAVE_Q-':
            print("Botón Guardar clickeado!")
            # Tu lógica para guardar...
            q_data = hquest.get_questionnaire_data_for_member(institution_name, group_name, member_name, app_data_ref=app_data)
            responses = {}
            for q in q_data.get('questions', []):
                selections = []
                for i in range(q['max_selections']):
                    value = values.get(f"-Q_{q['data_key']}_{i}-")
                    if value and value != 'Seleccionar':
                        selections.append(value)
                responses[q['data_key']] = selections
            
            success, msg = hquest.save_questionnaire_responses(institution_name, group_name, member_name, responses)
            sg.popup(msg)
        
        elif event == '-PDF_TEMPLATE_Q-':
            print("Botón PDF clickeado!")
            pdf_bytes, filename = pdf_generator.generate_class_questionnaire_template_pdf(institution_name, group_name)
            if pdf_bytes:
                save_path = sg.popup_get_file('Guardar Plantilla', save_as=True, default_extension=".pdf", default_path=filename)
                if save_path:
                    try:
                        with open(save_path, 'wb') as f: 
                            f.write(pdf_bytes)
                        sg.popup("Plantilla PDF guardada.")
                    except Exception as e: 
                        sg.popup_error(f"Error al guardar: {e}")
            else: 
                sg.popup_error("No se pudo generar el PDF.")
        
        elif event == '-MANAGE_Q-':
            print("Botón Gestionar clickeado!")
            context_q_mgmt = {'school': institution_name, 'class_name': group_name, 'member': member_name}
            self.switch_view('-VIEW_QUESTIONS-', context_data=context_q_mgmt)
            
    def handle_questions_events(self, event, values):
        """Maneja todos los eventos de la pantalla de Gestión de Preguntas."""
        context = self.app_state.get('context', {})
        institution_name = context.get('school')
        group_name = context.get('class_name')
        selected_q_display = values.get('-Q_LIST-')[0] if values.get('-Q_LIST-') else None
        
        form_is_visible = self.window['-FORM_Q_FRAME-'].visible
        self.window['-NEW_Q-'].update(disabled=form_is_visible)
        self.window['-MOD_Q-'].update(disabled=form_is_visible or not selected_q_display)
        self.window['-DEL_Q-'].update(disabled=form_is_visible or not selected_q_display)

        if event == '-BACK_TO_Q-':
            # CORRECCIÓN: Ahora vuelve al cuestionario del miembro que estábamos editando.
            self.switch_view('-VIEW_QUESTIONNAIRE-', context_data=self.app_state['context'])
        elif event == '-Q_LIST-':
            self.window['-FORM_Q_FRAME-'].update(visible=False)
        elif event == '-NEW_Q-':
            self.app_state['form_q_mode'] = 'new'
            current_defs_tuples = hq.get_question_definitions_for_group(institution_name, group_name)
            next_order = max([q_def.get('order', -1) for _, q_def in current_defs_tuples]) + 1 if current_defs_tuples else 0
            self.window['-FORM_Q_TITLE-'].update("Nueva Pregunta")
            for key in ['-FORM_Q_ID-', '-FORM_Q_TEXT-', '-FORM_Q_TYPE-', '-FORM_Q_DK-']: self.window[key].update('')
            self.window['-FORM_Q_ORDER-'].update(next_order); self.window['-FORM_Q_MAX-'].update('2')
            self.window['-FORM_Q_POL_POS-'].update(True); self.window['-FORM_Q_SELF-'].update(False)
            self.window['-FORM_Q_FRAME-'].update(visible=True)
        elif event == '-MOD_Q-' and selected_q_display:
            self.app_state['form_q_mode'] = 'modify'
            try:
                q_id = selected_q_display.split('(ID: ')[1][:-1]
                all_defs = hq.get_question_definitions_for_group(institution_name, group_name)
                original_data_tuple = next(((qid, q_def) for qid, q_def in all_defs if qid == q_id), None)
                if original_data_tuple:
                    d = original_data_tuple[1]; self.app_state['original_q_id'] = q_id
                    self.window['-FORM_Q_TITLE-'].update(f"Modificar Pregunta (ID: {q_id})"); self.window['-FORM_Q_ID-'].update(q_id)
                    self.window['-FORM_Q_TEXT-'].update(d.get('text', '')); self.window['-FORM_Q_TYPE-'].update(d.get('type', ''))
                    self.window['-FORM_Q_DK-'].update(d.get('data_key', '')); self.window['-FORM_Q_ORDER-'].update(d.get('order', '99'))
                    self.window['-FORM_Q_MAX-'].update(d.get('max_selections', '2'))
                    self.window['-FORM_Q_POL_POS-'].update(d.get('polarity', 'positive') == 'positive'); self.window['-FORM_Q_POL_NEG-'].update(d.get('polarity') == 'negative')
                    self.window['-FORM_Q_SELF-'].update(d.get('allow_self_selection', False))
                    self.window['-FORM_Q_FRAME-'].update(visible=True)
            except IndexError:
                sg.popup_error("No se pudo identificar la pregunta seleccionada.")
        elif event == '-DEL_Q-' and selected_q_display:
            try:
                q_id = selected_q_display.split('(ID: ')[1][:-1]
                if sg.popup_yes_no(f"¿Eliminar la pregunta '{q_id}' y todas sus respuestas asociadas?", title="Confirmar Eliminación") == 'Yes':
                    success, msg = hq.handle_delete_question(institution_name, group_name, q_id)
                    sg.popup(msg)
                    if success: self.refresh_questions_list(institution_name, group_name)
            except IndexError: sg.popup_error("No se pudo identificar la pregunta seleccionada.")
        elif event == '-FORM_Q_CANCEL-':
            self.window['-FORM_Q_FRAME-'].update(visible=False)
        elif event == '-FORM_Q_SAVE-':
            try:
                q_data = {'id': values['-FORM_Q_ID-'], 'text': values['-FORM_Q_TEXT-'], 'type': values['-FORM_Q_TYPE-'], 'data_key': values['-FORM_Q_DK-'], 'polarity': 'positive' if values['-FORM_Q_POL_POS-'] else 'negative', 'order': int(values['-FORM_Q_ORDER-']), 'max_selections': int(values['-FORM_Q_MAX-']), 'allow_self_selection': values['-FORM_Q_SELF-']}
                if self.app_state.get('form_q_mode') == 'new': success, msg = hq.handle_add_question(institution_name, group_name, q_data)
                else: success, msg = hq.handle_modify_question(institution_name, group_name, self.app_state.get('original_q_id'), q_data)
                sg.popup(msg)
                if success:
                    self.window['-FORM_Q_FRAME-'].update(visible=False)
                    self.refresh_questions_list(institution_name, group_name)
            except ValueError: sg.popup_error("'Orden' y 'Máx. Selecciones' deben ser números enteros.")
            except Exception as e: sg.popup_error(f"Error inesperado al guardar: {e}")

    def handle_sociogram_events(self, event, values):
        context = self.app_state.get('context', {})
        institution_name = context.get('school'); group_name = context.get('class_name')
        
        # --- INICIO DE LA CORRECCIÓN ---
        if event == '-BACK_TO_GROUPS-':
            # Debe volver a la vista de grupos, pasando el nombre de la institución.
            self.switch_view('-VIEW_GROUPS-', context_data=institution_name)
        # --- FIN DE LA CORRECCIÓN ---
            
        elif event == '-SOC_GENERATE_INTERACTIVE-':
            log_message("Botón 'Generar y Ver Sociograma' presionado.", 'info')
            selected_keys = [k.split('__')[1] for k, v in values.items() if k.startswith('-SOC_REL__') and v]
            if not selected_keys:
                sg.popup_error("Por favor, selecciona al menos una relación para dibujar."); return

            params = { 'node_gender_filter': 'Masculino' if values.get('-SOC_GENDER_M-') else 'Femenino' if values.get('-SOC_GENDER_F-') else 'Todos', 'label_display_mode': 'iniciales' if values.get('-SOC_LABEL_MODE-') == 'Iniciales' else 'nombre_apellido', 'connection_gender_type': 'mismo_genero' if values.get('-SOC_CONN_SAME-') else 'diferente_genero' if values.get('-SOC_CONN_DIFF-') else 'todas', 'active_members_filter': values.get('-SOC_ACTIVE_ONLY-', False), 'nominators_option': values.get('-SOC_SHOW_ISOLATES-', True), 'received_color_filter': values.get('-SOC_COLOR_RECEIVERS-', False), 'reciprocal_nodes_color_filter': values.get('-SOC_COLOR_RECIP_NODES-', False), 'style_reciprocal_links': values.get('-SOC_RECIPROCAL_STYLE-', True), 'selected_participant_focus': next((val for txt, val in sociogram_utils.get_participant_options(self.app_state, app_data, hutils) if txt == values.get('-SOC_FOCUS_PARTICIPANT-')), None), 'connection_focus_mode': 'outgoing' if values.get('-SOC_FOCUS_OUT-') else 'incoming' if values.get('-SOC_FOCUS_IN-') else 'all', 'layout_to_use': 'cose', 'highlight_mode': 'top_n' if values.get('-SOC_HL_TOPN-') else 'k_th' if values.get('-SOC_HL_KTH-') else 'none', 'highlight_value': int(values.get('-SOC_HL_VALUE-', 1)) if str(values.get('-SOC_HL_VALUE-')).isdigit() else 1 }
            
            output_path = os.path.join(os.getcwd(), "sociograma_interactivo.html")
            self.window.set_cursor('watch'); self.window.refresh()
            html_content = sociogram_engine.generate_interactive_html(school_name=institution_name, class_name=group_name, app_data_ref=app_data, selected_data_keys=selected_keys, **params)
            result_path = sociogram_engine.save_interactive_sociogram(html_content=html_content, output_path=output_path) if html_content else None
            self.window.set_cursor('arrow')
            
            if result_path:
                webbrowser.open(f'file:///{os.path.abspath(result_path)}'); sg.popup_ok("El sociograma se ha abierto en tu navegador web.", "Éxito")
            else: sg.popup_error("No se pudo generar el archivo del sociograma. Revisa la consola para más detalles.")

    def handle_matrix_events(self, event, values):
        context = self.app_state.get('context', {})
        institution_name = context.get('school'); group_name = context.get('class_name')
        
        # --- INICIO DE LA CORRECCIÓN ---
        if event == '-BACK_TO_GROUPS-':
            self.switch_view('-VIEW_GROUPS-', context_data=institution_name)
        # --- FIN DE LA CORRECCIÓN ---

        elif event == '-MATRIX_UPDATE-':
            selected_keys = [key.split('__')[1] for key, val in values.items() if isinstance(key, str) and key.startswith('-MATRIXQ__') and val]
            if not selected_keys:
                sg.popup_ok("Por favor, selecciona al menos una pregunta para generar la matriz."); return
            
            result = hsm.handle_draw_sociomatrix_data(institution_name, group_name, selected_keys)
            
            if result and result.get('success'):
                self.app_state['last_matrix_header'] = result.get('header', [])
                self.app_state['last_matrix_data'] = result.get('data', [])
                row_colors = result.get('row_colors', [])
                
                if self.app_state['last_matrix_data']:
                    self.window['-MATRIX_TABLE-'].update(values=self.app_state['last_matrix_data'], row_colors=row_colors)
                else:
                    self.window['-MATRIX_TABLE-'].update(values=[["No hay datos para mostrar."]])
            else:
                self.app_state['last_matrix_header'], self.app_state['last_matrix_data'] = [], []
                sg.popup_error(result.get('message', "Ocurrió un error desconocido."))
        elif event == '-MATRIX_PDF-':
            header = self.app_state.get('last_matrix_header')
            data = self.app_state.get('last_matrix_data')
            if not header or not data:
                sg.popup_error("Primero debes generar una matriz válida."); return
            
            pdf_bytes, filename = pdf_generator.generate_sociomatrix_pdf(institution_name, group_name, header, data)
            if pdf_bytes:
                save_path = sg.popup_get_file('Guardar PDF', save_as=True, default_extension=".pdf", default_path=filename)
                if save_path:
                    try:
                        with open(save_path, 'wb') as f: f.write(pdf_bytes)
                        sg.popup("PDF guardado.")
                    except Exception as e: sg.popup_error(f"Error al guardar: {e}")
            else: sg.popup_error(f"No se pudo generar el PDF: {filename}")
            
    def handle_diana_events(self, event, values):
        context = self.app_state.get('context', {})
        institution_name = context.get('school'); group_name = context.get('class_name')

        # --- INICIO DE LA CORRECCIÓN ---
        if event == '-BACK_TO_GROUPS-':
            self.switch_view('-VIEW_GROUPS-', context_data=institution_name)
        # --- FIN DE LA CORRECCIÓN ---
            
        elif event == '-DIANA_GENERATE-':
            selected_keys = [key.split('__')[1] for key, val in values.items() if isinstance(key, str) and key.startswith('-DIANA_Q__') and val]
            if not selected_keys: sg.popup_error("Selecciona al menos una pregunta."); return
            
            sg.popup_quick_message("Generando Diana...", background_color='lightblue')
            image_bytes = hgrp.handle_generate_diana_data(institution_name, group_name, selected_keys, values['-DIANA_SHOW_LINES-'])
            
            if image_bytes:
                self.app_state['diana_image_bytes'] = image_bytes
                self.window['-DIANA_SAVE-'].update(disabled=False)
                # Actualizar la imagen en la GUI
                self.window['-DIANA_IMAGE-'].update(data=image_bytes)
            else:
                sg.popup_error("No se pudo generar la imagen.")
                self.app_state['diana_image_bytes'] = None
                self.window['-DIANA_IMAGE-'].update(data=None)
                self.window['-DIANA_SAVE-'].update(disabled=True)
        elif event == '-DIANA_SAVE-':
            image_bytes = self.app_state.get('diana_image_bytes')
            if image_bytes:
                filename = f"Diana_{institution_name}_{group_name}.png".replace('\"','').replace("'", "")
                save_path = sg.popup_get_file('Guardar Diana (PNG)', save_as=True, default_extension=".png", file_types=(("PNG", "*.png"),), default_path=filename)
                if save_path:
                    try:
                        with open(save_path, 'wb') as f: f.write(image_bytes)
                        sg.popup("Diana guardada.")
                    except Exception as e: sg.popup_error(f"Error al guardar: {e}")
            else: sg.popup_error("Primero genera una diana.")


# --- BLOQUE 6: PUNTO DE ENTRADA DE LA APLICACIÓN ---
if __name__ == "__main__":
    try:
        app_data.initialize_data() # Aseguramos que los datos están cargados
        show_coffee_popup()
        
        # En lugar de llamar a main(), ahora creamos una instancia de nuestra
        # nueva clase y ejecutamos su propio bucle interno.
        app = SociogramaApp()
        app.run()
        
    except Exception as e:
        error_details = f'Error no controlado en Sociograma:\n\n{e}\n\nTraceback:\n{traceback.format_exc()}'
        sg.popup_error(error_details, title="Error Fatal en Sociograma")