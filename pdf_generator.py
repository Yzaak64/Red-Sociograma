# pdf_generator.py
# (v1.12 - Refactorizado para aplicación de escritorio.
#  Las funciones de generación de PDF ahora devuelven los bytes del archivo.
#  Terminología actualizada a Institución/Grupo/Miembro.)

# --- BLOQUE 1: IMPORTACIONES Y CONFIGURACIÓN DE DEPENDENCIAS ---

# --- Importaciones Estándar de Python ---
import sys
import io
import re
import collections
import traceback
import base64
import datetime
import math
import unicodedata

# --- Importaciones de Módulos Personalizados ---
import sociograma_data # Para acceder a members_data, etc.
from handlers_utils import normalizar_nombre_para_comparacion

# --- Dependencias de ReportLab (para generación de PDF) ---
REPORTLAB_AVAILABLE = False
# Definir fallbacks para constantes y clases de ReportLab si no está instalado
A4_SIZE, LANDSCAPE_FUNC, LETTER_SIZE, CM_UNIT, INCH_UNIT, MM_UNIT = (595.27, 841.89), lambda x: x, (612.0, 792.0), 28.3464566929, 72, 2.83464566929
ParagraphStyleClass = type('ParagraphStyle', (object,), {'__init__': lambda self, name, **kwargs: setattr(self, 'name', name)})
SpacerClass, PageBreakClass, FrameClass, PageTemplateClass, BaseDocTemplateClass, TableClass, TableStyleClass, ImageClass, KeepInFrameClass, ListFlowableClass, ListItemClass = (type(f'DummyRL_{i}', (object,), {}) for i in range(11))
ALIGN_CENTER, ALIGN_LEFT, ALIGN_JUSTIFY, ALIGN_RIGHT = 1, 0, 4, 2
HexColorFunc = lambda x: None; color_black = None; color_lightgrey = None; color_white = None; color_grey = None; ColorClass = lambda r,g,b,a=1: None; toColorFunc = lambda x: None

def getSampleStyleSheet_fallback_func():
    default_styles = collections.defaultdict(lambda: ParagraphStyleClass(name='Normal'))
    default_styles['Normal'] = ParagraphStyleClass(name='Normal')
    default_styles['h1'] = ParagraphStyleClass(name='h1')
    style_names_to_add_fb = [
        'h2', 'h3', 'Bullet_Point', 'Member_Name_Header', 'Questionnaire_Header', 'Question_Text',
        'Response_Line', 'Response_Label', 'Small_Info', 'Table_Header', 'Table_Cell',
        'Table_Cell_Left', 'Legend_MainTitle', 'Legend_Subtitle', 'Legend_Item_Color_Symbol',
        'Legend_Item_Text', 'Legend_Item_Width_Symbol', 'H1_Custom_Instr', 'H2_Custom_Instr',
        'H3_Custom_Instr', 'Normal_Custom_Instr', 'Table_Header_Instr', 'Table_Cell_Left_Instr',
        'Bullet_Point_Instr'
    ]
    for style_n_fb in style_names_to_add_fb:
        default_styles[style_n_fb] = ParagraphStyleClass(name=style_n_fb)
    return default_styles
getSampleStyleSheet_actual = getSampleStyleSheet_fallback_func

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4 as RL_A4, landscape as RL_landscape, letter as RL_letter
    from reportlab.lib.units import cm as RL_cm, inch as RL_inch, mm as RL_mm
    from reportlab.lib.styles import getSampleStyleSheet as RL_getSampleStyleSheet, ParagraphStyle as RL_ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer as RL_Spacer, PageBreak as RL_PageBreak, Frame as RL_Frame, PageTemplate as RL_PageTemplate, BaseDocTemplate as RL_BaseDocTemplate, Table as RL_Table, TableStyle as RL_TableStyle, Image as RL_Image, KeepInFrame as RL_KeepInFrame, ListFlowable as RL_ListFlowable, ListItem as RL_ListItem
    from reportlab.lib.enums import TA_CENTER as RL_TA_CENTER, TA_LEFT as RL_TA_LEFT, TA_JUSTIFY as RL_TA_JUSTIFY, TA_RIGHT as RL_TA_RIGHT
    from reportlab.lib.colors import HexColor as RL_HexColor, black as RL_black, lightgrey as RL_lightgrey, white as RL_white, grey as RL_grey, Color as RL_Color, toColor as RL_toColor
    
    REPORTLAB_AVAILABLE = True
    A4_SIZE, LANDSCAPE_FUNC, LETTER_SIZE, CM_UNIT, INCH_UNIT, MM_UNIT = RL_A4, RL_landscape, RL_letter, RL_cm, RL_inch, RL_mm
    ParagraphStyleClass, SpacerClass, PageBreakClass, FrameClass, PageTemplateClass, BaseDocTemplateClass, TableClass, TableStyleClass, ImageClass, KeepInFrameClass, ListFlowableClass, ListItemClass = RL_ParagraphStyle, RL_Spacer, RL_PageBreak, RL_Frame, RL_PageTemplate, RL_BaseDocTemplate, RL_Table, RL_TableStyle, RL_Image, RL_KeepInFrame, RL_ListFlowable, RL_ListItem
    ALIGN_CENTER, ALIGN_LEFT, ALIGN_JUSTIFY, ALIGN_RIGHT = RL_TA_CENTER, RL_TA_LEFT, RL_TA_JUSTIFY, RL_TA_RIGHT
    HexColorFunc, color_black, color_lightgrey, color_white, color_grey, ColorClass, toColorFunc = RL_HexColor, RL_black, RL_lightgrey, RL_white, RL_grey, RL_Color, RL_toColor
    getSampleStyleSheet_actual = RL_getSampleStyleSheet
except ImportError:
    print("ADVERTENCIA (pdf_generator): ReportLab no está instalado. La funcionalidad de PDF estará limitada.")

# --- Dependencias de Pillow ---
PILLOW_AVAILABLE = False
PILImage, ImageDraw, ImageFont = None, None, None
try:
    from PIL import Image as PILImage_local, ImageDraw as ImageDraw_local, ImageFont as ImageFont_local
    PILImage, ImageDraw, ImageFont = PILImage_local, ImageDraw_local, ImageFont_local
    PILLOW_AVAILABLE = True
except ImportError:
    print("ADVERTENCIA (pdf_generator): Pillow no está instalado. La creación de imágenes para leyendas estará deshabilitada.")

# --- Dependencia de xhtml2pdf ---
XHTML2PDF_AVAILABLE = False
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    print("ADVERTENCIA (pdf_generator): xhtml2pdf no está instalado. La conversión de HTML a PDF estará deshabilitada.")

# --- Dependencias para Diana de Afinidad (Matplotlib, NumPy, NetworkX) ---
MATPLOTLIB_AVAILABLE = False
plt, mpatches, np, mlines, nx = None, None, None, None, None
try:
    import matplotlib.pyplot as plt_local
    import matplotlib.patches as mpatches_local
    import numpy as np_local
    import matplotlib.lines as mlines_local
    import networkx as nx_local
    plt, mpatches, np, mlines, nx = plt_local, mpatches_local, np_local, mlines_local, nx_local
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("ADVERTENCIA (pdf_generator): Matplotlib/NumPy/NetworkX no están instalados. La Diana de Afinidad no funcionará.")

# --- FIN BLOQUE 1 ---
# --- BLOQUE 2: FUNCIONES HELPER GENERALES DE PDF ---

def _draw_page_number_general(canvas, doc):
    """Dibuja el número de página en el canvas de ReportLab."""
    if not REPORTLAB_AVAILABLE: return
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(HexColorFunc("#333333") if HexColorFunc else color_black)
    page_str = f"Página {doc.page}"
    margin_adj = 1.5 * CM_UNIT
    
    # Determinar el tamaño y orientación de la página
    is_landscape = doc.pagesize[0] > doc.pagesize[1]
    
    if is_landscape:
        # Para páginas apaisadas
        page_width = doc.pagesize[0]
        canvas.drawRightString(page_width - margin_adj, 1 * CM_UNIT, page_str)
    else:
        # Para páginas verticales
        page_width = doc.pagesize[0]
        canvas.drawRightString(page_width - margin_adj, 1.5 * CM_UNIT, page_str)
        
    canvas.restoreState()

def _create_pdf_styles_general():
    """Crea y devuelve una hoja de estilos personalizada para los PDFs."""
    styles = getSampleStyleSheet_actual()
    if not REPORTLAB_AVAILABLE: return styles
        
    # Definición de colores
    color_dark_blue_pdf = HexColorFunc("#2c3e50") if HexColorFunc else color_black
    color_medium_blue_pdf = HexColorFunc("#34495e") if HexColorFunc else color_black
    color_light_blue_pdf = HexColorFunc("#2980b9") if HexColorFunc else color_black
    color_gray_text_pdf = HexColorFunc("#7f8c8d") if HexColorFunc else color_black
    color_dark_text_pdf = HexColorFunc("#555555") if HexColorFunc else color_black

    # Estilos de párrafo
    styles.add(ParagraphStyleClass(name='Normal_Custom', parent=styles['Normal'], spaceBefore=3, spaceAfter=3, fontSize=10, leading=12))
    styles.add(ParagraphStyleClass(name='H1_Custom', parent=styles['h1'], fontSize=18, spaceBefore=12, spaceAfter=12, alignment=ALIGN_CENTER, textColor=color_dark_blue_pdf))
    styles.add(ParagraphStyleClass(name='H2_Custom', parent=styles['h2'], fontSize=14, spaceBefore=10, spaceAfter=5, alignment=ALIGN_LEFT, textColor=color_medium_blue_pdf))
    styles.add(ParagraphStyleClass(name='H3_Custom', parent=styles['h3'], fontSize=12, spaceBefore=8, spaceAfter=4, alignment=ALIGN_LEFT, textColor=color_dark_text_pdf))
    styles.add(ParagraphStyleClass(name='Bullet_Point', parent=styles['Normal_Custom'], leftIndent=1*CM_UNIT, firstLineIndent=-0.5*CM_UNIT, spaceBefore=0.1*CM_UNIT, leading=12, fontSize=9))
    styles.add(ParagraphStyleClass(name='Member_Name_Header', parent=styles['h3'], fontSize=12, spaceBefore=8, spaceAfter=8, alignment=ALIGN_LEFT, fontName='Helvetica-Bold', textColor=color_light_blue_pdf))
    styles.add(ParagraphStyleClass(name='Questionnaire_Header', parent=styles['Normal_Custom'], fontSize=9, spaceBefore=2, spaceAfter=2, alignment=ALIGN_LEFT, textColor=color_gray_text_pdf))
    styles.add(ParagraphStyleClass(name='Question_Text', parent=styles['Normal_Custom'], fontSize=10, leading=14, spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyleClass(name='Response_Line', parent=styles['Normal_Custom'], fontSize=10, leading=16, leftIndent=1*CM_UNIT))
    styles.add(ParagraphStyleClass(name='Response_Label', parent=styles['Normal_Custom'], fontSize=9, spaceBefore=2, spaceAfter=6, fontName='Helvetica-Oblique', textColor=color_dark_text_pdf))
    styles.add(ParagraphStyleClass(name='Small_Info', parent=styles['Normal_Custom'], fontSize=8, textColor=color_gray_text_pdf, alignment=ALIGN_RIGHT))
    
    # Estilos de tabla y leyenda
    styles.add(ParagraphStyleClass(name='Table_Header', parent=styles['Normal_Custom'], fontName='Helvetica-Bold', fontSize=8, alignment=ALIGN_LEFT, leading=10))
    styles.add(ParagraphStyleClass(name='Table_Cell', parent=styles['Normal_Custom'], fontSize=8, alignment=ALIGN_CENTER, leading=10))
    styles.add(ParagraphStyleClass(name='Table_Cell_Left', parent=styles['Table_Cell'], alignment=ALIGN_LEFT))
    styles.add(ParagraphStyleClass(name='Legend_MainTitle', parent=styles['h2'], fontSize=12, spaceBefore=10, spaceAfter=6, textColor=color_dark_text_pdf, alignment=ALIGN_LEFT))
    styles.add(ParagraphStyleClass(name='Legend_Subtitle', parent=styles['Normal_Custom'], fontSize=10, spaceBefore=4, spaceAfter=3, textColor=color_dark_text_pdf, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyleClass(name='Legend_Item_Color_Symbol', parent=styles['Normal_Custom'], fontSize=10, leading=12))
    styles.add(ParagraphStyleClass(name='Legend_Item_Text', parent=styles['Normal_Custom'], fontSize=9, leading=12, leftIndent=0))
    styles.add(ParagraphStyleClass(name='Legend_Item_Width_Symbol', parent=styles['Normal_Custom'], fontSize=10, leading=12, fontName='Helvetica-Bold'))
    
    return styles

def _create_legend_line_image_pil(color_hex, line_style_name, arrow_shape_name, source_arrow_shape_name,
                                 img_width_px=60, img_height_px=20, line_thickness=2):
    """Crea una pequeña imagen de una línea/flecha para la leyenda del sociograma."""
    if not PILLOW_AVAILABLE or not PILImage or not ImageDraw:
        return None
    try:
        pil_color_val_legend = (0,0,0)
        if color_hex.startswith('#') and len(color_hex) == 7:
            pil_color_val_legend = (int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16))
        elif REPORTLAB_AVAILABLE and toColorFunc:
            try:
                rl_color_obj_legend = toColorFunc(color_hex)
                if rl_color_obj_legend: pil_color_val_legend = tuple(int(c * 255) for c in rl_color_obj_legend.rgb())
            except: pass

        img_legend_line = PILImage.new("RGBA", (img_width_px, img_height_px), (255, 255, 255, 0))
        draw_legend_line = ImageDraw.Draw(img_legend_line)
        y_center_img_line = img_height_px // 2
        line_start_x_img_line, line_end_x_img_line = 5, img_width_px - 5

        if line_style_name == 'dashed':
            for i in range(line_start_x_img_line, line_end_x_img_line, 8):
                draw_legend_line.line([(i, y_center_img_line), (min(i + 4, line_end_x_img_line), y_center_img_line)], fill=pil_color_val_legend, width=line_thickness)
        elif line_style_name == 'dotted':
            for i in range(line_start_x_img_line, line_end_x_img_line, 4):
                draw_legend_line.line([(i, y_center_img_line), (min(i + 1, line_end_x_img_line), y_center_img_line)], fill=pil_color_val_legend, width=line_thickness)
        else:
            draw_legend_line.line([(line_start_x_img_line, y_center_img_line), (line_end_x_img_line, y_center_img_line)], fill=pil_color_val_legend, width=line_thickness)

        arrow_head_size = 6
        if arrow_shape_name != 'none':
            points = [(line_end_x_img_line - arrow_head_size, y_center_img_line - arrow_head_size//2), (line_end_x_img_line, y_center_img_line), (line_end_x_img_line - arrow_head_size, y_center_img_line + arrow_head_size//2)]
            draw_legend_line.polygon(points, fill=pil_color_val_legend)
            
        if source_arrow_shape_name != 'none':
            points_source = [(line_start_x_img_line + arrow_head_size, y_center_img_line - arrow_head_size//2), (line_start_x_img_line, y_center_img_line), (line_start_x_img_line + arrow_head_size, y_center_img_line + arrow_head_size//2)]
            draw_legend_line.polygon(points_source, fill=pil_color_val_legend)
            
        buffer_img_leg = io.BytesIO()
        img_legend_line.save(buffer_img_leg, format="PNG")
        buffer_img_leg.seek(0)
        return buffer_img_leg
    except Exception:
        return None

# --- FIN BLOQUE 2 ---
# --- BLOQUE 3: PDF DE INSTRUCCIONES DE IMPORTACIÓN CSV ---

def _draw_page_number_csv_instructions(canvas, doc):
    """Función de callback para dibujar el número de página en el PDF de instrucciones."""
    if not REPORTLAB_AVAILABLE: return
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(color_grey if color_grey else ColorClass(0.5,0.5,0.5))
    margin_adj = 1 * CM_UNIT
    doc_width = doc.width
    doc_left_margin = doc.leftMargin
    canvas.drawRightString(doc_width + doc_left_margin, margin_adj, f"Página {doc.page}")
    canvas.restoreState()

def _create_pdf_styles_csv_instructions():
    """Crea y devuelve una hoja de estilos específica para el PDF de instrucciones."""
    styles = getSampleStyleSheet_actual()
    if not REPORTLAB_AVAILABLE: return styles
    styles.add(ParagraphStyleClass(name='H1_Custom_Instr', parent=styles['h1'], alignment=ALIGN_CENTER, fontSize=16, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyleClass(name='H2_Custom_Instr', parent=styles['h2'], fontSize=13, spaceBefore=8, spaceAfter=4, alignment=ALIGN_LEFT))
    styles.add(ParagraphStyleClass(name='H3_Custom_Instr', parent=styles['h3'], fontSize=11, spaceBefore=6, spaceAfter=3, alignment=ALIGN_LEFT))
    styles.add(ParagraphStyleClass(name='Normal_Custom_Instr', parent=styles['Normal'], fontSize=9, leading=11, spaceBefore=3, spaceAfter=3))
    styles.add(ParagraphStyleClass(name='Code_Instr', parent=styles['Normal'], fontName='Courier', fontSize=8, textColor=color_grey, backColor=color_lightgrey, borderWidth=1, borderColor=color_grey, padding=2, leading=10))
    styles.add(ParagraphStyleClass(name='Table_Header_Instr', parent=styles['Normal_Custom_Instr'], fontName='Helvetica-Bold', fontSize=8, alignment=ALIGN_LEFT, leading=10))
    styles.add(ParagraphStyleClass(name='Table_Cell_Left_Instr', parent=styles['Normal_Custom_Instr'], fontSize=8, alignment=ALIGN_LEFT, leading=10))
    styles.add(ParagraphStyleClass(name='Bullet_Point_Instr', parent=styles['Normal_Custom_Instr'], leftIndent=1*CM_UNIT, firstLineIndent=-0.5*CM_UNIT, bulletIndent=0*CM_UNIT, spaceBefore=2, fontSize=9, leading=11))
    return styles

def generate_import_instructions_pdf():
    """
    Genera el MANUAL DE USUARIO COMPLETO del programa Sociograma, replicando
    fielmente el contenido y la estructura del documento de referencia.
    """
    if not REPORTLAB_AVAILABLE:
        return None, "Error: La librería ReportLab no está instalada."

    filename = "Manual_Usuario_Sociograma.pdf"
    buffer = io.BytesIO()
    
    try:
        doc = BaseDocTemplateClass(buffer, pagesize=A4_SIZE,
                                   leftMargin=2*CM_UNIT, rightMargin=2*CM_UNIT,
                                   topMargin=2*CM_UNIT, bottomMargin=2.5*CM_UNIT)
        
        frame = FrameClass(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='frame_manual')
        page_template = PageTemplateClass(id='page_tpl_manual', frames=[frame], onPage=_draw_page_number_general)
        doc.addPageTemplates([page_template])
        
        styles = _create_pdf_styles_general()
        story = []

        # Alias de estilos para mayor claridad
        H1 = styles['H1_Custom']
        H2 = styles['H2_Custom']
        H3 = styles['H3_Custom']
        H4 = styles.get('H4_Custom', styles['h4'])
        Body = styles['Normal_Custom']
        Bullet = styles.get('Bullet_Point', styles['Normal'])
        if 'Bullet_Sub' not in styles:
            styles.add(ParagraphStyleClass(name='Bullet_Sub', parent=Bullet, leftIndent=35))
        Bullet_Sub = styles['Bullet_Sub']
        Table_Header = styles['Table_Header']
        Table_Cell = styles['Table_Cell_Left']
        
        # --- PORTADA ---
        story.append(Paragraph("Manual de Usuario", H1))
        story.append(SpacerClass(1, 1*CM_UNIT))
        story.append(Paragraph("Programa de Sociograma", H2))
        story.append(SpacerClass(1, 0.5*CM_UNIT))
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except locale.Error:
            locale.setlocale(locale.LC_TIME, '')
        story.append(Paragraph(f"Versión del documento: {datetime.date.today().strftime('%d de %B de %Y')}", Body))
        story.append(PageBreakClass())

        # --- ÍNDICE NAVEGABLE ---
        story.append(Paragraph("Índice", H1))
        story.append(SpacerClass(1, 0.5 * CM_UNIT))
        toc_data = [
            ("1. Introducción al Programa", "intro"),
            ("2. Flujo de Trabajo Básico", "flujo"),
            ("3. Guía Detallada de la Interfaz", "guia"),
            ("   3.1. Pantalla Principal: Gestión de Instituciones", "guia_inst"),
            ("   3.2. Pantalla de Grupos", "guia_grp"),
            ("   3.3. Pantalla de Miembros", "guia_memb"),
            ("   3.4. Cuestionario y Gestión de Preguntas", "guia_quest"),
            ("4. Herramientas de Análisis", "analisis"),
            ("   4.1. El Sociograma Interactivo", "analisis_socio"),
            ("   4.2. La Matriz Sociométrica", "analisis_matriz"),
            ("   4.3. La Diana de Afinidad", "analisis_diana"),
            ("5. Importación y Exportación de Datos (CSV)", "csv"),
            ("   5.1. Configuración de un Formulario de Google", "csv_gforms"),
            ("   5.2. Estructura del Archivo CSV", "csv_struct"),
            ("   5.3. Panel de Importación y Exportación en la App", "csv_panel"),
        ]
        for text, key in toc_data:
            style = H2 if text[0].isdigit() and '.' in text else H3
            link = f'<a href="#{key}">{text}</a>'
            story.append(Paragraph(link, style))
        story.append(PageBreakClass())

        # --- SECCIONES DEL MANUAL ---
        
        story.append(Paragraph('<a name="intro"/>1. Introducción al Programa', H2))
        story.append(Paragraph("Este programa está diseñado para facilitar la creación, gestión y análisis de datos sociométricos. Permite definir instituciones, grupos y miembros, registrar respuestas a cuestionarios sociométricos y visualizar las dinámicas grupales a través de sociogramas, matrices y otros reportes.", Body))
        
        story.append(Paragraph('<a name="flujo"/>2. Flujo de Trabajo Básico', H2))
        story.append(Paragraph("El uso principal de la aplicación sigue una jerarquía lógica, desde lo más general a lo más específico:", Body))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Gestión de Instituciones:</b> El nivel más alto. Aquí puede crear, modificar o eliminar instituciones.", Bullet)),
            ListItemClass(Paragraph("<b>Gestión de Grupos:</b> Dentro de cada institución, puede crear y gestionar grupos.", Bullet)),
            ListItemClass(Paragraph("<b>Gestión de Miembros:</b> Dentro de cada grupo, se añaden los miembros participantes.", Bullet)),
            ListItemClass(Paragraph("<b>Registro de Cuestionarios:</b> Para cada miembro, se puede acceder a un formulario para registrar sus elecciones.", Bullet)),
            ListItemClass(Paragraph("<b>Análisis y Reportes:</b> Con los datos cargados, se pueden generar sociogramas, matrices, reportes PDF y la Diana de Afinidad.", Bullet))
        ], bulletType='bullet'))
        
        story.append(Paragraph('<a name="guia"/>3. Guía Detallada de la Interfaz', H2))
        story.append(Paragraph('<a name="guia_inst"/><b>3.1. Pantalla Principal: Gestión de Instituciones</b>', H3))
        story.append(Paragraph("Esta es la primera pantalla. Muestra una lista de todas las instituciones y sus controles asociados.", Body))
        story.append(Paragraph("<u>Componentes de la Pantalla de Instituciones:</u>", H4))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Lista de Instituciones:</b> Un cuadro de selección que muestra todas las instituciones existentes. Haga clic en el nombre de una institución para seleccionarla. Esto es necesario para poder modificarla, eliminarla o ver sus grupos.", Bullet)),
            ListItemClass(Paragraph("<b>Anotaciones de Institución:</b> Un cuadro de texto a la derecha que muestra las notas guardadas para la institución seleccionada. Es de solo lectura en esta vista.", Bullet)),
        ], bulletType='bullet'))
        story.append(Paragraph("<u>Botones de Acción:</u>", H4))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Nueva Institución:</b> Muestra un formulario para crear una nueva institución. Deberá proporcionar un nombre único y, opcionalmente, anotaciones.", Bullet)),
            ListItemClass(Paragraph("<b>Modificar Institución:</b> (Se habilita al seleccionar una). Permite cambiar el nombre y las anotaciones de la institución seleccionada.", Bullet)),
            ListItemClass(Paragraph("<b>Eliminar Institución:</b> (Se habilita al seleccionar una). Borra permanentemente la institución y todos sus datos asociados (grupos, miembros, respuestas, etc.). <b>Esta acción es irreversible y requiere confirmación.</b>", Bullet)),
            ListItemClass(Paragraph("<b>Ver Grupos:</b> (Se habilita al seleccionar una). Navega a la pantalla de gestión de grupos de la institución seleccionada. Es el paso principal para profundizar en los datos..", Bullet)),
            ListItemClass(Paragraph("<b>Importar/Exportar CSV:</b> Despliega el panel para la gestión de datos masivos (ver sección 5).", Bullet)),
            ListItemClass(Paragraph("<b>Salir App:</b> Cierra la aplicación y finaliza la sesión.", Bullet)),
        ], bulletType='bullet'))

        story.append(Paragraph('<a name="guia_grp"/><b>3.2. Pantalla de Grupos</b>', H3))
        story.append(Paragraph("Tras seleccionar una institución y hacer clic en 'Ver Grupos', llegará aquí. Esta pantalla lista todos los grupos de esa institución. Al seleccionar un grupo, verá sus detalles (coordinador, profesores, etc.) en el panel derecho.", Body))
        story.append(Paragraph("<u>Componentes de la Pantalla de Grupos:</u>", H4))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Lista de Grupos:</b> Cuadro de selección con todos los grupos de la institución. Seleccione uno para habilitar las acciones sobre él.", Bullet)),
            ListItemClass(Paragraph("<b>Detalles del Grupo:</b> Muestra información adicional del grupo seleccionado como el coordinador, profesores de apoyo y anotaciones.", Bullet)),
        ], bulletType='bullet'))
        story.append(Paragraph("<u>Botones de Acción Principales:</u>", H4))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Nuevo Grupo:</b> Abre un formulario para crear un nuevo grupo en la institución actual.", Bullet)),
            ListItemClass(Paragraph("<b>Modificar Grupo:</b> Permite editar los detalles del grupo seleccionado.", Bullet)),
            ListItemClass(Paragraph("<b>Eliminar Grupo:</b> Borra el grupo y todos sus miembros y respuestas.", Bullet_Sub)),
            ListItemClass(Paragraph("<b>Ver Miembros:</b> Navega a la siguiente pantalla para gestionar los miembros del grupo.", Bullet_Sub)),
            ListItemClass(Paragraph("<b>Volver a Instituciones:</b> Regresa a la pantalla principal.", Bullet_Sub)),
        ], bulletType='bullet'))
        story.append(Paragraph("<u>Botones de Análisis y Reportes:</u>", H4))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Ver Sociograma:</b> Abre la herramienta de visualización del sociograma para el grupo seleccionado (ver sección 4.1).", Bullet)),
            ListItemClass(Paragraph("<b>Reportes del Grupo:</b> Despliega un sub-menú con tres herramientas:", Bullet)),
            ListItemClass(Paragraph("<b>Matriz Sociométrica:</b> Navega a una vista de tabla que resume numéricamente las elecciones (ver sección 4.2).", Bullet_Sub)),
            ListItemClass(Paragraph("<b>PDF Datos Cuestionario:</b> Genera y descarga un PDF con todas las respuestas detalladas de cada miembro.", Bullet_Sub)),
            ListItemClass(Paragraph("<b>Diana de Afinidad:</b> Despliega un panel para generar la visualización de la Diana que muestra los niveles de seleccion de los miembros en círculos concéntricos (ver sección 4.3).", Bullet_Sub)),
        ], bulletType='bullet'))

        story.append(Paragraph('<a name="guia_memb"/><b>3.3. Pantalla de Miembros</b>', H3))
        story.append(Paragraph("Muestra la lista de todos los miembros de un grupo. Permite añadir, modificar o eliminar miembros individualmente.", Body))
        story.append(Paragraph("<u>Componentes y Botones:</u>", H4))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Lista de Miembros:</b> Seleccione un miembro para ver sus detalles (apellido, nombre, iniciales, anotaciones) y activar los botones.", Bullet)),
            ListItemClass(Paragraph("<b>Nuevo Miembro:</b> Abre el formulario para añadir un nuevo participante al grupo, donde podrá introducir su nombre, apellido, sexo, fecha de nacimiento y anotaciones.", Bullet)),
            ListItemClass(Paragraph("<b>Modificar Miembro:</b> Permite editar los detalles del miembro seleccionado.", Bullet)),
            ListItemClass(Paragraph("<b>Eliminar Grupo:</b> Borra al miembro seleccionado y sus respuestas del cuestionario.", Bullet_Sub)),
            ListItemClass(Paragraph("<b>Cuestionario:</b> Abre el formulario de elecciones para el miembro seleccionado. Este es el paso clave para registrar los datos sociométricos.", Bullet_Sub)),
            ListItemClass(Paragraph("<b>Volver a Instituciones:</b> Regresa a la pantalla de gestión de grupos.", Bullet_Sub)),
        ], bulletType='bullet'))
        story.append(Paragraph('<a name="guia_quest"/><b>3.4. Cuestionario y Gestión de Preguntas</b>', H3))
        story.append(Paragraph("Este formulario muestra todas las preguntas definidas para el grupo. Para cada pregunta, puede seleccionar a otros miembros de las listas desplegables. Una vez completado, haga clic en <b>'Guardar Respuestas'</b>.", Body))
        story.append(Paragraph("<u>Botones del Cuestionario:</u>", H4))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Guardar Respuestas:</b> Guarda las elecciones hechas en el formulario.", Bullet)),
            ListItemClass(Paragraph("<b>Generar PDF Cuestionario:</b> Crea un PDF en blanco con las preguntas del grupo, útil para imprimir y aplicar en papel.", Bullet)),
            ListItemClass(Paragraph("<b>Salir sin Guardar:</b> Cierra el cuestionario y descarta cualquier cambio no guardado.", Bullet)),
            ListItemClass(Paragraph("<b>Gestionar Preguntas:</b> Abre una pantalla avanzada para configurar el cuestionario.", Bullet)),
        ], bulletType='bullet'))
        story.append(Paragraph("<u>Pantalla de Gestión de Preguntas:</u>", H4))
        story.append(Paragraph("Aquí puede personalizar completamente el cuestionario para cada grupo. Puede añadir, modificar o eliminar preguntas, definiendo para cada una:", Body))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>ID Único y Clave de Datos:</b> Identificadores internos para la pregunta.", Bullet)),
            ListItemClass(Paragraph("<b>Texto y Tipo:</b> El texto que verá el usuario y una categoría (ej. 'Juego', 'Tarea').", Bullet)),
            ListItemClass(Paragraph("<b>Polaridad:</b> Define si la pregunta es de aceptación (positiva) o de rechazo (negativa).", Bullet)),
            ListItemClass(Paragraph("<b>Orden y Nº de Selecciones:</b> Controla el orden de aparición y cuántas elecciones puede hacer un miembro por pregunta.", Bullet)),
        ], bulletType='bullet'))

        story.append(Paragraph('<a name="analisis"/>4. Herramientas de Análisis', H2))
        story.append(Paragraph("Una vez que los datos han sido ingresados, el programa ofrece varias herramientas para su análisis visual y cuantitativo.", Body))
        
        story.append(Paragraph('<a name="analisis_socio"/><b>4.1. El Sociograma Interactivo</b>', H3))
        story.append(Paragraph("Esta es la visualización principal, que muestra a los miembros como nodos y sus elecciones como flechas. Puede filtrar y colorear la red para destacar patrones.", Body))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Relaciones a Incluir:</b> Marque las preguntas específicas que desea visualizar en el grafo.", Bullet)),
            ListItemClass(Paragraph("<b>Filtro por Sexo de Miembros:</b> Muestra solo nodos de un sexo específico (Masculino, Femenino) o todos.", Bullet)),
            ListItemClass(Paragraph("<b>Etiquetas de Nodos:</b> Cambia el texto dentro de cada nodo entre el nombre completo del miembro, sus iniciales o un identificador anónimo.", Bullet)),
            ListItemClass(Paragraph("<b>Filtro de Miembros Activos:</b> Si se marca, oculta a los miembros que no han realizado ninguna elección.", Bullet)),
            ListItemClass(Paragraph("<b>Opción Nominadores/Aislados:</b> Si está marcada, los nodos que no reciben ninguna elección (aislados) se colorean de un color especial. Si se desmarca, estos nodos se ocultan del grafo.", Bullet)),
            ListItemClass(Paragraph("<b>Coloreado Especial:</b> Puede activar checkboxes para resaltar con colores distintivos a los nodos que solo reciben elecciones o a aquellos que participan en relaciones recíprocas (elecciones mutuas).", Bullet)),
            ListItemClass(Paragraph("<b>Filtro de Conexión por Sexo:</b> Muestra solo las elecciones entre miembros del mismo sexo, de diferente sexo, o todas.", Bullet)),
            ListItemClass(Paragraph("<b>Foco en Participante:</b> Permite seleccionar un miembro de una lista desplegable para ver únicamente sus conexiones (las que hace, las que recibe, o ambas). Esto es muy útil para analizar la perspectiva de un individuo.", Bullet)),
            ListItemClass(Paragraph("<b>Resaltar Líderes:</b> Colorea automáticamente los N miembros más elegidos en las preguntas positivas.", Bullet)),
            ListItemClass(Paragraph("<b>Botones de Dibujo:</b> 'Redibujar' aplica un layout orgánico, mientras que 'Dibujar en Círculo' organiza los nodos de forma circular. 'Generar PDF' exporta la vista actual.", Bullet)),
        ], bulletType='bullet'))

        story.append(Paragraph('<a name="analisis_matriz"/><b>4.2. La Matriz Sociométrica</b>', H3))
        story.append(Paragraph("Es una tabla que resume numéricamente quién elige a quién. Las filas representan a los nominadores y las columnas a los elegidos.", Body))
        story.append(Paragraph("<u>Controles de la Matriz:</u>", H4))        
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Selección de Preguntas:</b> Utilice los checkboxes para seleccionar las preguntas que desea incluir en el conteo de la matriz.", Bullet)),
            ListItemClass(Paragraph("<b>Botones de Selección Rápida:</b> Los botones 'Todas', 'Ninguna', 'Positivas' y 'Negativas' le permiten marcar o desmarcar rápidamente grupos de preguntas según su polaridad.", Bullet)),
            ListItemClass(Paragraph("<b>Actualizar Matriz:</b> Este botón regenera la tabla con las preguntas que haya seleccionado.", Bullet)),
            ListItemClass(Paragraph("<b>Generar PDF:</b> Exporta la tabla actualmente visible a un archivo PDF.", Bullet)),
        ], bulletType='bullet'))

        story.append(Paragraph('<a name="analisis_diana"/><b>4.3. La Diana de Afinidad</b>', H3))
        story.append(Paragraph("Esta visualización coloca a los miembros en círculos concéntricos. Los miembros con más elecciones recibidas (los 'populares') se sitúan en el centro, mientras que los menos elegidos quedan en la periferia. Permite identificar rápidamente los distintos niveles de integración social.", Body))
        story.append(Paragraph("<u>Controles de la Diana:</u>", H4))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Selección de Preguntas:</b> Al igual que en la matriz, puede seleccionar las preguntas (positivas, negativas o una mezcla) que se usarán para calcular el puntaje de afinidad de cada miembro.", Bullet)),
            ListItemClass(Paragraph("<b>Mostrar Líneas de Elección:</b> Este checkbox le permite mostrar u ocultar las flechas de elección en el gráfico para una vista más limpia o más detallada.", Bullet)),
            ListItemClass(Paragraph("<b>Generar/Actualizar Diana:</b> Dibuja o redibuja la diana con las opciones seleccionadas.", Bullet)),
            ListItemClass(Paragraph("<b>Descargar Diana (PNG):</b> Una vez generada, este botón se habilita para que pueda descargar la imagen de la diana en formato PNG.", Bullet)),
        ], bulletType='bullet'))

        story.append(Paragraph('<a name="csv"/>5. Importación y Exportación de Datos (CSV)', H2))
        story.append(Paragraph("Esta funcionalidad, accesible desde la pantalla de Instituciones, es crucial para la carga y descarga masiva de datos, especialmente cuando se utilizan formularios externos como Google Forms.", Body))

        story.append(Paragraph('<a name="csv_gforms"/><b>5.1. Configuración de un Formulario de Google</b>', H3))
        story.append(Paragraph("Para que el archivo CSV exportado desde Google Forms sea compatible, configure su formulario con los siguientes tipos de pregunta:", Body))
        story.append(ListFlowableClass([
            ListItemClass(Paragraph("<b>Institucion:</b> 'Lista desplegable'.", Bullet)),
            ListItemClass(Paragraph("<b>Grupo:</b> 'Lista desplegable'.", Bullet)),
            ListItemClass(Paragraph("<b>Nombre y Apellido:</b> 'Lista desplegable'.", Bullet)),
            ListItemClass(Paragraph("<b>Sexo:</b> 'Opción múltiple' (con opciones 'Masculino' y 'Femenino').", Bullet)),
            ListItemClass(Paragraph("<b>Fecha De Nacimiento:</b> 'Fecha'.", Bullet)),
            ListItemClass(Paragraph("<b>Preguntas de Elección (¡MUY IMPORTANTE!):</b>", Bullet)),
        ], bulletType='bullet'))
            
        story.append(Paragraph("Use el tipo de pregunta <b>'Cuadrícula de opción múltiple':</b>", Body))
        story.append(ListFlowableClass([    
            ListItemClass(Paragraph("<b>Pregunta:</b> Coloca una pregunta (ej. '¿Con quién te gustaría jugar?').", Bullet)),
            ListItemClass(Paragraph("<b>Filas:</b> Use los identificadores como 'Opcion 1', 'Opcion 2', etc.", Bullet)),
            ListItemClass(Paragraph("<b>Columnas:</b> Use los mismos nombres de 'Nombre y Apellido' aqui.", Bullet)),
        ], bulletType='bullet'))

        story.append(Paragraph('<a name="csv_struct"/><b>5.2. Estructura del Archivo CSV</b>', H3))
        story.append(Paragraph("Si crea el CSV manualmente, debe seguir esta estructura exacta. El orden de las primeras columnas es fundamental.", Body))
        id_cols_data = [
            ["Columna CSV", "Descripción"],
            ["Marca temporal", "Generada por G-Forms. Opcional."],
            ["Dirección de correo electrónico", "Opcional."],
            ["Institucion", "<b>Obligatorio</b>. Nombre exacto de la institución."],
            ["Grupo", "<b>Obligatorio</b>. Nombre exacto del grupo."],
            ["Nombre y Apellido", "<b>Obligatorio</b>. Nombre del miembro que responde."],
            ["Sexo", "<b>Obligatorio</b>. Valores: 'Masculino', 'Femenino'."],
            ["Fecha De Nacimiento", "<b>Obligatorio</b>. Formato: DD/MM/YYYY."],
            ["Pregunta [Opcion N]", "<b>Obligatorio para respuestas</b>. El valor debe ser el nombre del miembro elegido."]]
        id_table_data = [[Paragraph(cell, Table_Cell) for cell in row] for row in id_cols_data]
        id_table_data[0] = [Paragraph(f"<b>{cell}</b>", Table_Header) for cell in id_cols_data[0]]
        id_table = TableClass(id_table_data, colWidths=[6*CM_UNIT, 10*CM_UNIT])
        id_table.setStyle(TableStyleClass([('BACKGROUND',(0,0),(-1,0), color_lightgrey),('GRID',(0,0),(-1,-1),0.5, color_grey),('VALIGN',(0,0),(-1,-1),'TOP')]))
        story.append(id_table)

        story.append(Paragraph('<a name="csv_panel"/><b>5.3. Panel de Importación y Exportación en la App</b>', H3))
        story.append(Paragraph("<u>Sección de Importación:</u>", H4))
        story.append(ListFlowableClass([    
            ListItemClass(Paragraph("<b>Nombre Archivo:</b> Escriba el nombre exacto del archivo CSV que ha subido a la carpeta `/content/` de Colab.", Bullet)),
            ListItemClass(Paragraph("<b>Opciones de Importación (Checkboxes):</b> Seleccione qué partes de su CSV desea procesar. Por ejemplo, puede importar solo los miembros y sus datos demográficos sin cargar las respuestas, o viceversa. Esto le da un control total sobre la actualización de datos.", Bullet)),
            ListItemClass(Paragraph("<b>Opciones Adicionales:</b> Controle comportamientos específicos, como si se deben crear miembros que son mencionados en las respuestas pero no están en la lista principal.", Bullet)),
        ], bulletType='bullet'))

        story.append(Paragraph("<u>Sección de Exportación:</u>", H4))
        story.append(Paragraph("Esta sección le permite descargar los datos de su proyecto en un formato CSV compatible. Siga los pasos numerados:", Body))
        story.append(ListFlowableClass([    
            ListItemClass(Paragraph("<b>1. Cargar Instituciones:</b> Muestra una lista de todas sus instituciones para que las seleccione.", Bullet)),
            ListItemClass(Paragraph("<b>2. Cargar Grupos:</b> Muestra los grupos pertenecientes a las instituciones que marcó en el paso anterior.", Bullet)),
            ListItemClass(Paragraph("<b>3. Generar CSV:</b> Crea y ofrece para descargar un archivo CSV que contiene todos los datos (miembros, respuestas, etc.) de los grupos que haya seleccionado.", Bullet)),
        ], bulletType='bullet'))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes, filename

    except Exception as e:
        return None, traceback.format_exc()

# --- FIN BLOQUE 3 ---
# --- BLOQUE 4: PDF DEL SOCIOGRAMA CON LEYENDA (DESDE IMAGEN PRE-RENDERIZADA) ---

def generate_sociogram_with_legend_pdf(image_bytes, legend_info,
                                         institution_name, group_name,
                                         style_reciprocal_links_active=False,
                                         force_error_message=None):
    """
    Genera el PDF del sociograma a partir de una imagen y datos de leyenda.
    Devuelve:
        - tuple(bytes, filename): Si tiene éxito.
        - tuple(None, error_message): Si falla.
    """
    if not REPORTLAB_AVAILABLE:
        return (None, "Error: ReportLab no está instalado.")

    # Si no hay imagen y se fuerza un error, se crea un placeholder con el mensaje.
    if not image_bytes and force_error_message:
        if PILLOW_AVAILABLE:
            try:
                img = PILImage.new('RGB', (600, 400), color = (250, 250, 250))
                d = ImageDraw.Draw(img)
                # Usar una fuente por defecto si es posible
                try:
                    font = ImageFont.load_default()
                except IOError:
                    font = None
                d.text((20, 150), force_error_message, fill=(200, 0, 0), font=font)
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                image_bytes = buf.getvalue()
            except Exception:
                pass # Si falla, la siguiente comprobación lo manejará
        
    if not image_bytes:
        return (None, "No se proporcionaron datos de imagen válidos para el PDF.")

    # Preparar el documento PDF
    clean_institution = re.sub(r'[^\w\s-]', '', institution_name).replace(' ', '_')
    clean_group = re.sub(r'[^\w\s-]', '', group_name).replace(' ', '_')
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M')
    filename = f"Sociograma_{clean_institution}_{clean_group}_{timestamp}.pdf"

    buffer = io.BytesIO()
    doc_width, doc_height = LANDSCAPE_FUNC(A4_SIZE)
    doc = BaseDocTemplateClass(buffer, pagesize=(doc_width, doc_height),
                             leftMargin=1.5*CM_UNIT, rightMargin=1.5*CM_UNIT,
                             topMargin=1.5*CM_UNIT, bottomMargin=2*CM_UNIT)

    frame = FrameClass(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='frame_sociogram')
    template = PageTemplateClass(id='tpl_sociogram', frames=[frame], onPage=_draw_page_number_general)
    doc.addPageTemplates([template])

    styles = _create_pdf_styles_general()
    story = []

    story.append(Paragraph(f"Sociograma: {institution_name} - {group_name}", styles['H1_Custom']))
    story.append(SpacerClass(1, 0.3*CM_UNIT))

    # Añadir la imagen del sociograma al PDF
    try:
        img_obj = ImageClass(io.BytesIO(image_bytes))
        img_avail_width = doc.width
        img_avail_height = doc.height * 0.60
        
        aspect = img_obj.drawHeight / float(img_obj.drawWidth) if img_obj.drawWidth > 0 else 1
        new_w, new_h = img_avail_width, img_avail_width * aspect
        if new_h > img_avail_height:
            new_h, new_w = img_avail_height, img_avail_height / aspect if aspect > 0 else img_avail_width
        img_obj.drawWidth, img_obj.drawHeight = new_w, new_h
        
        story.append(KeepInFrameClass(doc.width, img_avail_height + 0.5*CM_UNIT, [img_obj], hAlign='CENTER'))
        story.append(SpacerClass(1, 0.4*CM_UNIT))
    except Exception as e:
        story.append(Paragraph(f"Error al procesar la imagen del sociograma: {e}", styles['Normal_Custom']))

    # Construir la leyenda
    legend_elements = []
    if legend_info and isinstance(legend_info, dict):
        legend_elements.append(Paragraph("Leyenda:", styles['Legend_MainTitle']))
        
        node_colors_legend = legend_info.get("node_colors", {})
        if node_colors_legend and PILLOW_AVAILABLE:
            legend_elements.append(Paragraph("Color de Nodo:", styles['Legend_Subtitle']))
            node_color_items = []
            col_widths_node_leg = [1.5*CM_UNIT, doc.width - 1.5*CM_UNIT - 2*CM_UNIT]
            for color_h, desc_n in sorted(node_colors_legend.items(), key=lambda item: item[1]):
                img_buf_rect_n = _create_legend_line_image_pil(color_h, "solid", "none", "none", img_width_px=25, img_height_px=12, line_thickness=10)
                rect_img_n = ImageClass(img_buf_rect_n, width=0.8*CM_UNIT, height=0.4*CM_UNIT) if img_buf_rect_n else Paragraph(f"<font color='{color_h}'>■</font>", styles['Legend_Item_Color_Symbol'])
                node_color_items.append([rect_img_n, Paragraph(desc_n, styles['Legend_Item_Text'])])
            if node_color_items:
                node_table_leg = TableClass(node_color_items, colWidths=col_widths_node_leg)
                node_table_leg.setStyle(TableStyleClass([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),1*MM_UNIT)]))
                legend_elements.append(node_table_leg)
            legend_elements.append(SpacerClass(1, 0.3*CM_UNIT))

        edge_styles_legend = legend_info.get("edge_styles", {})
        if edge_styles_legend and PILLOW_AVAILABLE:
            legend_elements.append(Paragraph("Color/Estilo de Flecha:", styles['Legend_Subtitle']))
            edge_style_items = []
            col_widths_edge_leg = [2.0*CM_UNIT, doc.width - 2.0*CM_UNIT - 2*CM_UNIT]
            sorted_edge_styles_leg = sorted(edge_styles_legend.items(), key=lambda item: ("A_" if item[1].get('is_focus') else "B_") + item[0] )
            for desc_e, style_attrs in sorted_edge_styles_leg:
                color = style_attrs.get('color', '#000000')
                is_focus = style_attrs.get('is_focus', False)
                can_be_recip = style_attrs.get('can_be_reciprocal_styled', False)
                line_style1 = style_attrs.get('base_line_style', 'solid')
                arrow_shape1 = style_attrs.get('base_arrow_shape', 'triangle')
                source_arrow_shape1 = style_attrs.get('source_arrow_shape', 'none')
                img_buf1 = _create_legend_line_image_pil(color, line_style1, arrow_shape1, source_arrow_shape1)
                image1 = ImageClass(img_buf1, width=1.8*CM_UNIT, height=0.6*CM_UNIT) if img_buf1 else Paragraph(" ", styles['Normal_Custom'])
                suffix1 = " (Doble Foco)" if source_arrow_shape1 != 'none' and source_arrow_shape1 == arrow_shape1 and is_focus else ""
                edge_style_items.append([image1, Paragraph(f"{desc_e}{suffix1}", styles['Legend_Item_Text'])])
                if style_reciprocal_links_active and can_be_recip and not is_focus:
                    img_buf2 = _create_legend_line_image_pil(color, 'dashed', style_attrs.get('base_arrow_shape', 'triangle'), style_attrs.get('base_arrow_shape', 'triangle'))
                    img2 = ImageClass(img_buf2, width=1.8*CM_UNIT, height=0.6*CM_UNIT) if img_buf2 else Paragraph(" ", styles['Normal_Custom'])
                    edge_style_items.append([img2, Paragraph(f"<font name='Helvetica-Oblique'>{desc_e} (Doble Recíproca)</font>", styles['Legend_Item_Text'])])
            if edge_style_items:
                edge_table_leg = TableClass(edge_style_items, colWidths=col_widths_edge_leg)
                edge_table_leg.setStyle(TableStyleClass([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0),(-1,-1),0), ('BOTTOMPADDING', (0,0),(-1,-1),2*MM_UNIT)]))
                legend_elements.append(edge_table_leg)
            legend_elements.append(SpacerClass(1,0.3*CM_UNIT))

        width_styles_legend = legend_info.get("widths", {})
        if width_styles_legend and PILLOW_AVAILABLE:
            legend_elements.append(Paragraph("Grosor de Flecha (Orden de Elección):", styles['Legend_Subtitle']))
            width_items = []
            col_widths_width_leg = [1.5*CM_UNIT, doc.width - 1.5*CM_UNIT - 2*CM_UNIT]
            sorted_widths = sorted(width_styles_legend.items(), key=lambda item: int(item[0].split(" ")[1]) if "Elección" in item[0] and item[0].split(" ")[1].isdigit() else 99 )
            for desc_w, width_px_str in sorted_widths:
                try: line_thick = float(width_px_str.replace('px',''))
                except: line_thick = 1.0
                img_buf_w = _create_legend_line_image_pil("#000000", "solid", "none", "none", line_thickness=max(1,int(line_thick)))
                symbol_w = ImageClass(img_buf_w, width=1.3*CM_UNIT, height=0.5*CM_UNIT) if img_buf_w else Paragraph("━", styles['Legend_Item_Width_Symbol'])
                width_items.append([symbol_w, Paragraph(f"{desc_w} (aprox. {width_px_str})", styles['Legend_Item_Text'])])
            if width_items:
                width_table_leg = TableClass(width_items, colWidths=col_widths_width_leg)
                width_table_leg.setStyle(TableStyleClass([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0),(-1,-1),0), ('BOTTOMPADDING', (0,0),(-1,-1),1*MM_UNIT)]))
                legend_elements.append(width_table_leg)
        
        if legend_elements:
            story.append(KeepInFrameClass(doc.width, doc.height * 0.35, legend_elements, hAlign='LEFT'))

    # Construir y devolver el PDF
    try:
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return (pdf_bytes, filename)
    except Exception as e:
        if not buffer.closed: buffer.close()
        return (None, f"Error al construir el PDF del sociograma: {e}")

def generate_sociomatrix_pdf(institution_name, group_name, header, data):
    """
    Genera un PDF de la Matriz Sociométrica directamente con ReportLab
    para un control total sobre el estilo y la legibilidad.
    """
    if not REPORTLAB_AVAILABLE:
        return (None, "Error: La librería ReportLab no está instalada.")
    
    filename = f"MatrizSociometrica_{re.sub(r'[^a-zA-Z0-9_]+', '', institution_name)}_{re.sub(r'[^a-zA-Z0-9_]+', '', group_name)}.pdf"
    buffer = io.BytesIO()
    
    # --- INICIO DE LA CORRECCIÓN ---
    # Usar el alias correcto 'BaseDocTemplateClass' en lugar de 'BaseDocTemplate'
    doc = BaseDocTemplateClass(buffer, pagesize=LANDSCAPE_FUNC(A4_SIZE),
                               leftMargin=1.5*CM_UNIT, rightMargin=1.5*CM_UNIT,
                               topMargin=1.5*CM_UNIT, bottomMargin=2*CM_UNIT)
    # --- FIN DE LA CORRECCIÓN ---

    # El resto de la función es idéntico y correcto
    frame = FrameClass(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='frame_matrix')
    template = PageTemplateClass(id='tpl_matrix', frames=[frame], onPage=_draw_page_number_general)
    doc.addPageTemplates([template])
    
    styles = _create_pdf_styles_general()
    story = []

    story.append(Paragraph("Matriz Sociométrica", styles['H1_Custom']))
    story.append(Paragraph(f"Institución: {institution_name}    -    Grupo: {group_name}", styles['H2_Custom']))
    story.append(SpacerClass(1, 0.5 * CM_UNIT))

    if not header or not data:
        story.append(Paragraph("No hay datos para mostrar en la tabla.", styles['Normal_Custom']))
    else:
        table_data_reportlab = []
        table_styles_commands = []

        header_row = [Paragraph(f"<b>{str(cell)}</b>", styles['Table_Header']) for cell in header]
        table_data_reportlab.append(header_row)

        for row_index, row in enumerate(data):
            row_elements = []
            current_row_num = len(table_data_reportlab)
            if isinstance(row[0], str) and "---" in row[0]:
                cell_text = row[0].replace('---','').strip()
                p = Paragraph(f"<b><i>{cell_text}</i></b>", styles['H3_Custom'])
                row_elements.append(p)
                table_styles_commands.append(('SPAN', (0, current_row_num), (-1, current_row_num)))
                table_styles_commands.append(('BACKGROUND', (0, current_row_num), (-1, current_row_num), HexColorFunc("#E6F2FF")))
                table_styles_commands.append(('TEXTCOLOR', (0, current_row_num), (-1, current_row_num), HexColorFunc("#003366")))
                table_styles_commands.append(('ALIGN', (0, current_row_num), (-1, current_row_num), 'LEFT'))
            else:
                for i, cell in enumerate(row):
                    cell_text = str(cell)
                    style = styles['Table_Cell']
                    if i == 0:
                        style = styles['Table_Cell_Left']
                        if "Total" in cell_text:
                            cell_text = f"<b>{cell_text}</b>"
                    row_elements.append(Paragraph(cell_text, style))
            if row_elements:
                 table_data_reportlab.append(row_elements)

        num_cols = len(header)
        first_col_width = 4.0 * CM_UNIT
        last_col_width = 2.0 * CM_UNIT
        remaining_width = doc.width - first_col_width - last_col_width
        choice_col_width = remaining_width / (num_cols - 2) if num_cols > 2 else 0
        col_widths = [first_col_width] + [choice_col_width] * (num_cols - 2) + [last_col_width]

        matrix_table = TableClass(table_data_reportlab, colWidths=col_widths, repeatRows=1)
        
        base_style = [('GRID', (0,0), (-1,-1), 0.5, color_grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BACKGROUND', (0,0), (-1,0), HexColorFunc("#D0D0D0")), ('TEXTCOLOR', (0,0), (-1,0), color_black), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5)]
        for i, row in enumerate(data):
            if "Total" in str(row[0]):
                base_style.append(('BACKGROUND', (0, i+1), (-1, i+1), HexColorFunc("#F0F0F0")))
                base_style.append(('FONTNAME', (0, i+1), (-1, i+1), 'Helvetica-Bold'))
        base_style.extend(table_styles_commands)
        
        matrix_table.setStyle(TableStyleClass(base_style))
        story.append(matrix_table)

    try:
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return (pdf_bytes, filename)
    except Exception as e:
        if not buffer.closed: buffer.close()
        traceback.print_exc()
        return (None, f"Error al construir el PDF de la matriz: {e}")
    
# --- FIN BLOQUE 4 ---
# --- BLOQUE 5: PDF DESDE JSON DE CYTOSCAPE (RENDERIZANDO CON MATPLOTLIB) ---

def generate_pdf_from_cytoscape_json(graph_json, legend_info,
                                       institution_name, group_name,
                                       layout_hint='cose',
                                       style_reciprocal_links_active_param=False,
                                       force_error_message_on_image_fail=None):
    """
    Genera una imagen del grafo con Matplotlib a partir de datos JSON y luego
    la inserta en un PDF usando la función del Bloque 4.
    """
    if not REPORTLAB_AVAILABLE:
        return (None, "Error: ReportLab no está instalado.")

    # Validar que el JSON de entrada es correcto
    valid_graph_json = False
    if isinstance(graph_json, dict) and 'elements' in graph_json:
        elements = graph_json.get('elements')
        if isinstance(elements, dict) and ('nodes' in elements or 'edges' in elements):
            valid_graph_json = True

    if not valid_graph_json:
        return generate_sociogram_with_legend_pdf(
            None, legend_info, institution_name, group_name,
            style_reciprocal_links_active=style_reciprocal_links_active_param,
            force_error_message="Datos del grafo (JSON) no válidos para generar imagen."
        )

    image_bytes = None
    
    if not MATPLOTLIB_AVAILABLE or plt is None or not nx:
        current_force_error_msg = force_error_message_on_image_fail or "Librerías de graficación (Matplotlib/NetworkX) no disponibles."
        image_bytes = None
        force_error_message_on_image_fail = current_force_error_msg
    else:
        try:
            # Crear el grafo de NetworkX a partir del JSON
            G = nx.cytoscape_graph(graph_json)

            if not G.nodes():
                fig, ax = plt.subplots(figsize=(5,3))
                ax.text(0.5, 0.5, "Grafo sin nodos para mostrar.", ha='center', va='center', fontsize=10, color='grey', wrap=True)
                ax.set_axis_off()
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=90)
                buf.seek(0)
                image_bytes = buf.getvalue()
                plt.close(fig)
            else:
                # Extraer datos de estilo y posición del grafo JSON
                pos = {n: (d.get('position', {}).get('x', 0), -d.get('position', {}).get('y', 0)) for n, d in G.nodes(data=True)}
                
                # Si las posiciones no están en el JSON, calcularlas
                if not all(p in pos for p in G.nodes()):
                    node_count = G.number_of_nodes()
                    if layout_hint == 'circle':
                        pos = nx.circular_layout(G)
                    else:
                        k_val = 0.8 / math.sqrt(node_count) if node_count > 1 else 1.0
                        pos = nx.spring_layout(G, seed=42, k=k_val, iterations=75)

                # Preparar atributos para el dibujo
                node_colors = [d.get('node_color', 'lightgrey') for n, d in G.nodes(data=True)]
                labels = {n: d.get('label_to_display', '') for n, d in G.nodes(data=True)}
                edge_colors = [d.get('edge_color', 'grey') for u,v,d in G.edges(data=True)]
                edge_styles_map = {'solid': '-', 'dotted': ':', 'dashed': '--'}
                edge_styles = [edge_styles_map.get(d.get('edge_line_style', 'solid'), '-') for u,v,d in G.edges(data=True)]
                edge_widths = [float(str(d.get('edge_width_attr', '1.0px')).replace('px','')) for u,v,d in G.edges(data=True)]
                
                # Crear la figura y dibujar
                fig, ax = plt.subplots(figsize=(14, 10))
                
                nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1200, edgecolors='black', ax=ax)
                nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=edge_widths, style=edge_styles, arrowsize=20, ax=ax, connectionstyle='arc3,rad=0.1')
                nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, ax=ax)

                ax.set_title(f"Sociograma: {institution_name} - {group_name}", fontsize=16)
                ax.margins(0.1)
                plt.tight_layout()
                ax.axis("off")
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150)
                buf.seek(0)
                image_bytes = buf.getvalue()
                plt.close(fig)
        
        except Exception as e:
            traceback.print_exc()
            force_error_message_on_image_fail = f"Error al renderizar grafo con Matplotlib: {e}"
            image_bytes = None

    final_error_message = force_error_message_on_image_fail
    if image_bytes is None and force_error_message_on_image_fail is None:
        final_error_message = "Error crítico al generar la imagen del grafo."
                
    # Llamar a la función del Bloque 4 para componer el PDF final
    return generate_sociogram_with_legend_pdf(
        image_bytes, legend_info, institution_name, group_name,
        style_reciprocal_links_active=style_reciprocal_links_active_param,
        force_error_message=final_error_message
    )

# --- FIN BLOQUE 5 ---
# --- BLOQUE 6: OTRAS FUNCIONES DE GENERACIÓN DE PDF ---

def generate_class_questionnaire_template_pdf(institution_name, group_name):
    """Genera una plantilla de cuestionario en blanco para un grupo."""
    if not REPORTLAB_AVAILABLE:
        return (None, "Error: ReportLab no está instalado.")
    
    filename = f"PlantillaCuestionario_{re.sub(r'[^a-zA-Z0-9_]+','',institution_name)}_{re.sub(r'[^a-zA-Z0-9_]+','',group_name)}.pdf"
    buffer = io.BytesIO()
    doc = BaseDocTemplateClass(buffer, pagesize=A4_SIZE, leftMargin=1.5*CM_UNIT, rightMargin=1.5*CM_UNIT, topMargin=2*CM_UNIT, bottomMargin=2.5*CM_UNIT)
    frame = FrameClass(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='frame_tpl')
    template = PageTemplateClass(id='tpl_page', frames=[frame], onPage=_draw_page_number_general)
    doc.addPageTemplates([template])
    styles = _create_pdf_styles_general()
    story = []

    story.append(Paragraph("Plantilla del Cuestionario Sociométrico", styles['H1_Custom']))
    story.append(Paragraph(f"Institución: {institution_name}", styles['H2_Custom']))
    story.append(Paragraph(f"Grupo: {group_name}", styles['H2_Custom']))
    story.append(SpacerClass(1, 0.3*CM_UNIT))
    story.append(Paragraph("Nombre del Miembro: ____________________________________________", styles['Member_Name_Header']))
    story.append(SpacerClass(1, 0.5*CM_UNIT))
    
    group_defs = sociograma_data.get_class_question_definitions(institution_name, group_name)
    if not group_defs:
        story.append(Paragraph("<i>Este grupo no tiene preguntas definidas.</i>", styles['Response_Label']))
    else:
        sorted_q_items = sorted(group_defs.items(), key=lambda item:(item[1].get('order',99),item[0]))
        for q_id, q_def in sorted_q_items:
            text = q_def.get('text', f"Pregunta {q_id}")
            max_sel = q_def.get('max_selections', 2)
            story.append(Paragraph(f"{text} (Máximo {max_sel} selecciones):", styles['Question_Text']))
            for i in range(max_sel):
                story.append(Paragraph(f"{i+1}. ___________________________________________________________", styles['Response_Line']))
            story.append(SpacerClass(1, 0.2*CM_UNIT))
    
    try:
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return (pdf_bytes, filename)
    except Exception as e:
        if not buffer.closed: buffer.close()
        return (None, f"Error construyendo plantilla PDF: {e}")

def generate_and_download_questionnaire_pdf(institution_name, group_name):
    """Genera un PDF con las respuestas detalladas de todos los miembros del grupo."""
    if not REPORTLAB_AVAILABLE:
        return (None, "Error: ReportLab no está instalado.")
    
    filename = f"RespuestasDetalladas_{re.sub(r'[^a-zA-Z0-9_]+','',institution_name)}_{re.sub(r'[^a-zA-Z0-9_]+','',group_name)}.pdf"
    buffer = io.BytesIO()
    doc = BaseDocTemplateClass(buffer, pagesize=A4_SIZE, leftMargin=1.5*CM_UNIT, rightMargin=1.5*CM_UNIT, topMargin=2*CM_UNIT, bottomMargin=2.5*CM_UNIT)
    frame = FrameClass(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='frame_resp_det')
    template = PageTemplateClass(id='tpl_resp_det', frames=[frame], onPage=_draw_page_number_general)
    doc.addPageTemplates([template])
    styles = _create_pdf_styles_general()
    story = []

    story.append(Paragraph("Respuestas Detalladas del Cuestionario", styles['H1_Custom']))
    story.append(Paragraph(f"Institución: {institution_name}", styles['H2_Custom']))
    story.append(Paragraph(f"Grupo: {group_name}", styles['H2_Custom']))
    story.append(SpacerClass(1, 0.5*CM_UNIT))
    
    group_defs = sociograma_data.get_class_question_definitions(institution_name, group_name)
    if not group_defs:
        story.append(Paragraph(f"<i>Este grupo ({group_name}) no tiene preguntas definidas.</i>", styles['Response_Label']))
    else:
        sorted_q_items = sorted(group_defs.items(), key=lambda item: (item[1].get('order', 99), item[0]))
        members_list = sociograma_data.members_data.get(institution_name, {}).get(group_name, [])
        if not members_list:
            story.append(Paragraph(f"<i>No hay miembros en el grupo {group_name}.</i>", styles['Response_Label']))
        else:
            sorted_members = sorted(members_list, key=lambda s:(s.get('cognome','').strip().upper(), s.get('nome','').strip().upper()))
            first_member_page = True
            for member in sorted_members:
                if not first_member_page: story.append(PageBreakClass())
                first_member_page = False
                
                full_name = f"{member.get('cognome','').strip().title()} {member.get('nome','').strip().title()}"
                story.append(Paragraph(f"Miembro: {full_name}", styles['Member_Name_Header']))
                
                response_key = (institution_name, group_name, f"{member.get('nome','').strip().title()} {member.get('cognome','').strip().title()}")
                member_responses = sociograma_data.questionnaire_responses_data.get(response_key, {})
                
                if not member_responses:
                    story.append(Paragraph("<i>No ha respondido el cuestionario.</i>", styles['Response_Label']))
                else:
                    for q_id, q_def in sorted_q_items:
                        text = q_def.get('text', f"Pregunta {q_id}")
                        data_key = q_def.get('data_key', q_id)
                        responses = member_responses.get(data_key, [])
                        story.append(Paragraph(f"{text}:", styles['Question_Text']))
                        if responses:
                            for i, resp_name in enumerate(responses):
                                story.append(Paragraph(f"    {i+1}. {resp_name}", styles['Normal_Custom']))
                        else:
                            story.append(Paragraph("    - Sin respuesta -", styles['Response_Label']))
                        story.append(SpacerClass(1, 0.1*CM_UNIT))

    try:
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return (pdf_bytes, filename)
    except Exception as e:
        if not buffer.closed: buffer.close()
        return (None, f"Error construyendo PDF de respuestas: {e}")

def generate_class_summary_report_pdf(institution_name, group_name):
    """
    Genera una tabla PDF en modo apaisado con el resumen de elecciones recibidas,
    con encabezados correctos y ancho de tabla adaptativo.
    """
    if not REPORTLAB_AVAILABLE:
        return (None, "Error: ReportLab no está instalado.")
    
    filename = f"ResumenCuestionario_{re.sub(r'[^a-zA-Z0-9_]+','',institution_name)}_{re.sub(r'[^a-zA-Z0-9_]+','',group_name)}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    buffer = io.BytesIO()
    doc = BaseDocTemplateClass(buffer, pagesize=LANDSCAPE_FUNC(A4_SIZE), leftMargin=1*CM_UNIT, rightMargin=1*CM_UNIT, topMargin=1.5*CM_UNIT, bottomMargin=1.5*CM_UNIT)
    frame = FrameClass(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='frame_summary')
    template = PageTemplateClass(id='tpl_summary', frames=[frame], onPage=_draw_page_number_general)
    doc.addPageTemplates([template])
    styles = _create_pdf_styles_general()
    story = []

    story.append(Paragraph(f"RESUMEN DEL CUESTIONARIO SOCIOMÉTRICO", styles['H1_Custom']))
    story.append(Paragraph(f"Institución: {institution_name}   -   Grupo: {group_name}", styles['H2_Custom']))
    story.append(SpacerClass(1, 0.5*CM_UNIT))
    
    members_list = sociograma_data.members_data.get(institution_name, {}).get(group_name, [])
    group_defs = sociograma_data.get_class_question_definitions(institution_name, group_name)

    if not members_list or not group_defs:
        story.append(Paragraph("<i>No hay miembros o preguntas definidas para generar el resumen.</i>", styles['Response_Label']))
    else:
        pos_q = sorted([q for q in group_defs.values() if q.get('polarity') == 'positive'], key=lambda x: x.get('order', 99))
        neg_q = sorted([q for q in group_defs.values() if q.get('polarity') == 'negative'], key=lambda x: x.get('order', 99))
        
        header = [Paragraph("<b>MIEMBRO</b>", styles['Table_Header'])]
        
        # --- INICIO DE LA MODIFICACIÓN ---
        
        # 1. Usar la CATEGORÍA de la pregunta para los encabezados
        for q in pos_q:
            # Obtenemos la categoría en lugar del texto
            categoria = q.get('type', 'General')
            header_text = f"Acep.<br/><b>{categoria}</b>"
            header.append(Paragraph(header_text, styles['Table_Header']))
        header.append(Paragraph("<b>TOTAL<br/>Acep.</b>", styles['Table_Header']))
        
        for q in neg_q:
            # Hacemos lo mismo para las negativas
            categoria = q.get('type', 'General')
            header_text = f"Rech.<br/><b>{categoria}</b>"
            header.append(Paragraph(header_text, styles['Table_Header']))
        header.append(Paragraph("<b>TOTAL<br/>Rech.</b>", styles['Table_Header']))
        
        table_data = [header]
        
        # 2. Calcular anchos de columna dinámicamente
        num_cols_pos = len(pos_q)
        num_cols_neg = len(neg_q)
        num_total_cols = 1 + num_cols_pos + 1 + num_cols_neg + 1 # Miembro + Pos + TotalPos + Neg + TotalNeg

        # Asignar porcentajes del ancho disponible
        total_width = doc.width
        miembro_width = total_width * 0.25  # 25% para el nombre del miembro
        total_cols_width = total_width * 0.10 # 10% para las dos columnas de totales
        
        remaining_width = total_width - miembro_width - total_cols_width
        
        # El resto se divide entre las columnas de preguntas
        if (num_cols_pos + num_cols_neg) > 0:
            question_col_width = remaining_width / (num_cols_pos + num_cols_neg)
        else:
            question_col_width = 0

        col_widths = [miembro_width]
        col_widths.extend([question_col_width] * num_cols_pos)
        col_widths.append(total_cols_width / 2) # Total Acep.
        col_widths.extend([question_col_width] * num_cols_neg)
        col_widths.append(total_cols_width / 2) # Total Rech.
        
        # --- FIN DE LA MODIFICACIÓN ---

        nominations_received = collections.defaultdict(lambda: collections.defaultdict(int))
        # Normalizar nombres para la búsqueda
        normalized_member_map = {
            normalizar_nombre_para_comparacion(f"{m.get('nome','').title()} {m.get('cognome','').title()}"): f"{m.get('nome','').title()} {m.get('cognome','').title()}"
            for m in members_list
        }
        
        for (inst, grp, nominator), responses in sociograma_data.questionnaire_responses_data.items():
            if inst == institution_name and grp == group_name:
                for dk, nominees in responses.items():
                    for nominee in nominees:
                        # Usar el nombre normalizado para buscar y luego el nombre completo para contar
                        normalized_nominee = normalizar_nombre_para_comparacion(nominee)
                        if normalized_nominee in normalized_member_map:
                            final_nominee_name = normalized_member_map[normalized_nominee]
                            nominations_received[final_nominee_name][dk] += 1
        
        for member in sorted(members_list, key=lambda m: (str(m.get('cognome','')).upper(), str(m.get('nome','')).upper())):
            full_name = f"{member.get('nome','').title()} {member.get('cognome','').title()}"
            display_name = f"{member.get('cognome','').title()}, {member.get('nome','').title()}"
            row = [Paragraph(display_name, styles['Table_Cell_Left'])]
            total_pos = 0
            for q in pos_q:
                count = nominations_received[full_name].get(q['data_key'], 0)
                row.append(Paragraph(str(count), styles['Table_Cell']))
                total_pos += count
            row.append(Paragraph(f"<b>{total_pos}</b>", styles['Table_Cell']))
            
            total_neg = 0
            for q in neg_q:
                count = nominations_received[full_name].get(q['data_key'], 0)
                row.append(Paragraph(str(count), styles['Table_Cell']))
                total_neg += count
            row.append(Paragraph(f"<b>{total_neg}</b>", styles['Table_Cell']))
            
            table_data.append(row)

        summary_table = TableClass(table_data, colWidths=col_widths, repeatRows=1)
        summary_table.setStyle(TableStyleClass([('BACKGROUND',(0,0),(-1,0),color_lightgrey), ('GRID',(0,0),(-1,-1),0.5,color_grey), ('ALIGN',(1,0),(-1,-1),'CENTER'), ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
        story.append(summary_table)

    try:
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return (pdf_bytes, filename)
    except Exception as e:
        if not buffer.closed: buffer.close()
        return (None, f"Error construyendo PDF resumen: {e}")

def generate_pdf_from_html_content(html_string, output_filename_base):
    """Convierte una cadena HTML en un PDF usando xhtml2pdf, forzando la orientación horizontal."""
    if not XHTML2PDF_AVAILABLE:
        return (None, "Error: La librería xhtml2pdf no está instalada.")
    
    filename = f"{re.sub(r'[^a-zA-Z0-9_]+', '', output_filename_base)}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    buffer = io.BytesIO()
    
    # --- INICIO DEL CAMBIO ---
    # Añadir CSS para la orientación y el tamaño de la tabla
    css = """
    @page {
        size: A4 landscape;
        @frame {
            -pdf-frame-content: content;
            left: 2cm; right: 2cm; top: 2cm; bottom: 2cm;
        }
    }
    table {
        width: 100%;
        font-size: 8pt; /* Reducir un poco la fuente para que quepa mejor */
    }
    th, td {
        padding: 2px 4px; /* Ajustar el padding */
    }
    """
    
    # Envolver el HTML con el estilo
    full_html = f"<!doctype html><html><head><meta charset='utf-8'/><style>{css}</style></head><body>{html_string}</body></html>"
    # --- FIN DEL CAMBIO ---
    
    source_html = io.StringIO(full_html)
    
    pisa_status = pisa.CreatePDF(source_html, dest=buffer, encoding='utf-8')
    source_html.close()
    
    if pisa_status.err:
        return (None, f"Error de conversión HTML a PDF: {pisa_status.err}")
        
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return (pdf_bytes, filename)

# --- FIN BLOQUE 6 ---
# --- BLOQUE 7: GENERADOR DE IMAGEN DE LA DIANA DE AFINIDAD ---
def generate_affinity_diana_image(
    institution_name,
    group_name,
    members_data_list_detailed,
    edges_data,
    show_lines=True,
    registro_output=None, # Se mantiene por compatibilidad, pero no se usa activamente
    num_zonas_definidas=4,
    labels_zonas=None
):
    """
    VERSIÓN FINAL CON LOGS: Genera la imagen de la Diana de Afinidad con Matplotlib,
    con toda la lógica de estilo del notebook original y logs detallados.
    
    Devuelve un objeto BytesIO con la imagen PNG, o None si hay un error.
    """
    def log_diana(message):
        """Función de logging local para esta función."""
        print(f"[DIANA_ENGINE_LOG] {message}")

    log_diana("--- Iniciando generate_affinity_diana_image (versión completa) ---")

    if not MATPLOTLIB_AVAILABLE:
        log_diana("FALLO CRÍTICO: Matplotlib y/o sus dependencias (NumPy) no están disponibles.")
        return None

    if not members_data_list_detailed:
        log_diana("AVISO: No hay miembros para generar la diana. Devolviendo None.")
        return None

    # Ordenar miembros por puntaje para la lógica de posicionamiento
    members_ordenados = sorted(
        members_data_list_detailed,
        key=lambda x: (
            x.get('total_recibido', 0), 
            x.get('primeras_opciones', 0), 
            x.get('segundas_opciones', 0), 
            x.get('terceras_opciones', 0), 
            str(x.get('id_corto', 'Z'))
        ),
        reverse=True
    )

    # Crear figura y ejes de Matplotlib
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'aspect': 'equal'})
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.axis('off')
    
    # Dibujar gradiente de fondo
    log_diana("Dibujando fondo con gradiente...")
    n_grad_rings_bg = 100
    color_centro_grad_bg = np.array([1.0, 0.9, 0.7]) # Naranja/amarillo suave
    color_borde_grad_bg = np.array([1.0, 1.0, 1.0])   # Blanco
    for i_grad_bg in range(n_grad_rings_bg, 0, -1):
        radio_grad_bg = i_grad_bg / n_grad_rings_bg
        frac_grad_bg = (n_grad_rings_bg - i_grad_bg) / (n_grad_rings_bg - 1 if n_grad_rings_bg > 1 else 1)
        color_actual_grad_rgb_bg = np.clip(color_borde_grad_bg * (1 - frac_grad_bg) + color_centro_grad_bg * frac_grad_bg, 0, 1)
        grad_patch_bg = mpatches.Wedge((0, 0), radio_grad_bg, 0, 360, width=(radio_grad_bg / n_grad_rings_bg), facecolor=tuple(color_actual_grad_rgb_bg), edgecolor='none', zorder=0)
        ax.add_patch(grad_patch_bg)
    
    # Dibujar círculos de puntaje
    puntajes_reales = sorted(list(set(mem.get('total_recibido', 0) for mem in members_ordenados)), reverse=True)
    radios_puntajes = {}
    if puntajes_reales:
        log_diana(f"Puntajes reales encontrados para los círculos: {puntajes_reales}")
        max_p, min_p = puntajes_reales[0], puntajes_reales[-1]
        for puntaje in puntajes_reales:
            radio = 0.98 if max_p == min_p else 0.15 + ((max_p - puntaje) / (max_p - min_p)) * (0.98 - 0.15)
            radios_puntajes[puntaje] = radio
            circulo = mpatches.Circle((0, 0), radio, edgecolor='#333333', facecolor='none', lw=0.5, ls=':', zorder=15)
            ax.add_patch(circulo)
            ax.text(0, radio + 0.022, str(puntaje), ha='center', va='bottom', fontsize=6.5, color='#222222', zorder=20)

    # Posicionar los nodos (miembros)
    log_diana("Posicionando nodos en la diana...")
    node_positions = {}
    members_por_puntaje = collections.defaultdict(list)
    for mem in members_ordenados:
        members_por_puntaje[mem.get('total_recibido', 0)].append(mem)

    for puntaje, lista_miembros in members_por_puntaje.items():
        n_miembros = len(lista_miembros)
        if n_miembros == 0: continue
        
        radio_nominal = radios_puntajes.get(puntaje, 0.98)
        angulo_inicial = np.random.uniform(0, 2 * np.pi)
        
        for i, member in enumerate(lista_miembros):
            nombre_completo = member.get('nombre_completo')
            id_corto = member.get('id_corto')
            sexo = member.get('sexo', 'Desconocido')
            
            angulo = angulo_inicial + (i * (2 * np.pi / n_miembros))
            radio = radio_nominal
            
            x, y = (radio * np.cos(angulo), radio * np.sin(angulo)) if radio > 0.001 else (0, 0)
            node_positions[nombre_completo] = (x, y)

            marker, fc = ('^', '#FFC0CB') if sexo.lower() == 'femenino' else ('o', '#ADD8E6') if sexo.lower() == 'masculino' else ('s', '#A0E0A0')
            node_size = max(40, 1200 / (n_miembros**0.5 + 2))
            font_size = max(5, 8 - (n_miembros / 5))
            
            ax.scatter(x, y, s=node_size, marker=marker, edgecolor='#101010', facecolor=fc, zorder=25, lw=0.45)
            ax.text(x, y, id_corto, ha='center', va='center', fontsize=font_size, color='#000000', zorder=28, weight='normal')
            log_diana(f"  -> Nodo '{id_corto}' dibujado en ({x:.2f}, {y:.2f}) con puntaje {puntaje}")

    # Dibujar las líneas de elección si está activado
    if show_lines and edges_data:
        log_diana("Dibujando líneas de elección...")
        for nominator, nominee, _, _ in edges_data:
            if nominator in node_positions and nominee in node_positions:
                pos_start, pos_end = node_positions[nominator], node_positions[nominee]
                ax.annotate("", xy=pos_end, xytext=pos_start,
                            arrowprops=dict(arrowstyle="->", color="gray",
                                            shrinkA=15, shrinkB=15, # No tocar el nodo
                                            patchA=None, patchB=None,
                                            connectionstyle="arc3,rad=0.1", # Curva ligera
                                            alpha=0.6, lw=0.7), zorder=5)

    # Título y Leyenda final
    ax.set_title(f"Diana de Afinidad: {group_name}\n({institution_name})", fontsize=14, pad=20, weight='bold')
    legend_handles = [
        mlines.Line2D([], [], color='black', marker='o', ls='None', ms=7, mfc='#ADD8E6', mec='#101010', label='Masculino'),
        mlines.Line2D([], [], color='black', marker='^', ls='None', ms=7, mfc='#FFC0CB', mec='#101010', label='Femenino'),
        mlines.Line2D([], [], color='black', marker='s', ls='None', ms=6, mfc='#A0E0A0', mec='#101010', label='Desconocido/Otro')
    ]
    ax.legend(handles=legend_handles, title="Símbolos", loc='upper right', bbox_to_anchor=(1.14, 1.02), fontsize='x-small', title_fontsize='small')
    fig.tight_layout(rect=[0, 0.05, 1, 0.95]) # Ajustar márgenes para que todo quepa
    
    # Guardar la figura generada en un buffer de memoria en lugar de un archivo
    buffer_out = io.BytesIO()
    try:
        plt.savefig(buffer_out, format='png', dpi=150, bbox_inches='tight', pad_inches=0.1)
        plt.close(fig) # Liberar memoria de la figura
        buffer_out.seek(0) # Rebobinar el buffer para que se pueda leer desde el principio
        log_diana("Imagen de la Diana generada y guardada en buffer exitosamente.")
        return buffer_out
    except Exception as e:
        log_diana(f"ERROR CRÍTICO al guardar imagen de la Diana en el buffer: {e}\n{traceback.format_exc(limit=2)}")
        if 'fig' in locals() and fig is not None and plt is not None:
             try: plt.close(fig)
             except Exception: pass
        return None

# --- FIN BLOQUE 7 ---
print("pdf_generator.py refactorizado y COMPLETO, listo para su uso en la aplicación de escritorio.")
