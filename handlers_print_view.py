# handlers_print_view.py
# (v4.3 - Refactorizado para aplicación de escritorio.
#  Usa "Institución"/"Grupo" y "Miembro". Funciones devuelven datos o estado.)

import traceback
from sociograma_data import (
    members_data,
    questionnaire_responses_data,
    get_class_question_definitions
)
# Se asume que pdf_generator será importado en el módulo principal
import pdf_generator

# --- Funciones Lógicas de la Vista de Impresión/Previa ---

def handle_generate_html_preview(institution_name, group_name):
    """
    Genera el contenido HTML para la vista previa del cuestionario respondido.
    Devuelve una tupla (éxito, contenido_html_o_mensaje_error).
    """
    if not institution_name or not group_name:
        return False, "<p style='color:red;'>Error: Institución o grupo no especificados.</p>"

    html_content = f"<h2 style='text-align:center; color:#333;'>Respuestas del Cuestionario</h2>"
    html_content += f"<h3 style='text-align:center; color:#555;'>Institución: {institution_name} &nbsp;&nbsp;&nbsp;&nbsp; Grupo: {group_name}</h3><hr>"

    members_list = members_data.get(institution_name, {}).get(group_name, [])
    if not members_list:
        html_content += "<p style='color:orange; text-align:center;'>No hay miembros registrados en este grupo.</p>"
        return True, html_content

    try:
        sorted_members = sorted(members_list, key=lambda s: (s.get('cognome', '').strip().upper(), s.get('nome', '').strip().upper()))
    except Exception as e_sort:
        return False, f"<p style='color:red;'>Error al ordenar miembros: {e_sort}</p>"

    current_group_defs = get_class_question_definitions(institution_name, group_name)
    if not current_group_defs:
        html_content += "<p style='color:orange; text-align:center;'>No hay preguntas definidas para este grupo.</p>"
        return True, html_content

    sorted_q_items = sorted(current_group_defs.items(), key=lambda item: (item[1].get('order', 99), item[0]))

    any_response_found_overall = False
    for i, member in enumerate(sorted_members):
        full_name = f"{member.get('nome', '').strip().title()} {member.get('cognome', '').strip().title()}".strip()
        member_response_key = (institution_name, group_name, full_name)
        member_responses_dict = questionnaire_responses_data.get(member_response_key, {})

        if i > 0:
            html_content += "<hr style='border: 1px dashed #ccc; margin-top: 20px; margin-bottom: 20px;'>"

        html_content += f"<div style='border: 1px solid #e0e0e0; padding: 15px; margin: 15px 0; border-radius: 8px; background-color: #f9f9f9;'>"
        display_name = f"{member.get('cognome', '').strip().title()}, {member.get('nome', '').strip().title()}"
        html_content += f"<h4 style='color:#0056b3; margin-top:0;'>Miembro: {display_name}</h4>"

        if not member_responses_dict:
            html_content += "<p><i>Este miembro no ha respondido el cuestionario.</i></p>"
        else:
            any_response_found_for_member = False
            html_content += "<ul style='list-style-type: none; padding-left: 0;'>"
            for q_id, q_def in sorted_q_items:
                question_text = q_def.get('text', f"Pregunta {q_id}")
                data_key = q_def.get('data_key', q_id)
                responses_for_q = member_responses_dict.get(data_key, [])

                html_content += f"<li style='margin-bottom: 10px;'>"
                html_content += f"<strong style='color:#333;'>{question_text}:</strong>"
                if responses_for_q:
                    any_response_found_for_member = True
                    any_response_found_overall = True
                    html_content += "<ul style='list-style-type: disc; margin-left: 20px; color:#555;'>"
                    for resp_name in responses_for_q:
                        html_content += f"<li>{resp_name}</li>"
                    html_content += "</ul>"
                else:
                    html_content += " <span style='color: #888;'><em>Sin respuesta</em></span>"
                html_content += f"</li>"
            html_content += "</ul>"
            if not any_response_found_for_member and member_responses_dict:
                html_content += "<p><i>No se encontraron respuestas para las preguntas actuales del cuestionario.</i></p>"
        html_content += "</div>"

    if not any_response_found_overall and members_list:
        html_content += "<p style='text-align:center; color:orange;'>Ningún miembro parece haber respondido a las preguntas actuales del cuestionario para este grupo.</p>"

    return True, html_content


def handle_export_responses_pdf(institution_name, group_name):
    """
    Llama al generador de PDF para las respuestas detalladas del grupo.
    Devuelve (éxito, mensaje/ruta_archivo). La descarga real la maneja la GUI.
    """
    if not all([institution_name, group_name]):
        return False, "Faltan datos (institución o grupo) para exportar."

    # En una app de escritorio, la función de `pdf_generator` podría guardar el archivo
    # y devolver la ruta, en lugar de generar un enlace de descarga en base64.
    # Por ahora, mantenemos la lógica de que `generate_...` maneja la descarga.
    
    try:
        # La función de `pdf_generator` ya maneja la lógica de guardado y feedback.
        # Aquí solo la invocamos. En una app de escritorio real, esto podría cambiar
        # para devolver la ruta del archivo y que la GUI le diga al usuario dónde se guardó.
        pdf_generator.generate_and_download_questionnaire_pdf(institution_name, group_name, registro_output=None)
        return True, "Se ha iniciado la generación del PDF de respuestas. Revisa la carpeta de descargas."
    except Exception as e:
        traceback.print_exc()
        return False, f"Error al generar el PDF de respuestas: {e}"

# La exportación a RTF sigue pendiente, por lo que no se incluye un handler funcional.

print("handlers_print_view.py refactorizado y listo para su uso en la aplicación de escritorio.")