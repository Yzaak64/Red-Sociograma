# data_grupo_b.py
# Módulo aislado para contener los datos de prueba del "4to Grado B".
# (v6.0 - FINAL Y COMPLETO: Conjunto de 4 preguntas para CIVSOC con contexto de "Trabajo")

import collections

def load_grupo_b_data(schools, classes, members, questions, responses, cognitive_data):
    """
    Añade los datos específicos del "4to Grado B" a las estructuras de datos principales.
    Este conjunto de datos está diseñado para ser compatible con el análisis CIVSOC,
    con todas las preguntas centradas en el contexto de "trabajo en equipo".
    """
    institucion_nombre = "Colegio \"Miguel de Cervantes\""

    # 1. Añadir el grupo (sin cambios)
    if institucion_nombre in classes:
        if not any(g['name'] == "4to Grado B" for g in classes[institucion_nombre]):
            classes[institucion_nombre].append(
                {"name": "4to Grado B", "coordinator": "Prof. CIVSOC", "annotations": "Grupo de 6 miembros para validación de paper."}
            )

    # 2. Añadir los miembros (sin cambios)
    if institucion_nombre in members:
        members[institucion_nombre]["4to Grado B"] = [
            {"cognome": "PÉREZ", "nome": "Juan", "iniz": "JPX", "sexo": "Masculino"},
            {"cognome": "LÓPEZ", "nome": "José", "iniz": "JLX", "sexo": "Masculino"},
            {"cognome": "GARCÍA", "nome": "Julio", "iniz": "JGX", "sexo": "Masculino"},
            {"cognome": "RUIZ", "nome": "Jorge", "iniz": "JRX", "sexo": "Masculino"},
            {"cognome": "SÁNCHEZ", "nome": "Jesús", "iniz": "JSX", "sexo": "Masculino"},
            {"cognome": "DÍAZ", "nome": "Javier", "iniz": "JDX", "sexo": "Masculino"}
        ]

    # --- INICIO DE LA MODIFICACIÓN ---
    # --- INICIO DE LA MODIFICACIÓN ---
    # 3. Definiciones de preguntas con "type" (estructural) y "category" (temática) separados
    questions[(institucion_nombre, "4to Grado B")] = collections.OrderedDict([
        ("trabajo_pos",      {"text": "Si tuvieras que hacer un trabajo en equipo, ¿a quién elegirías?", "type": "[Acción Real]", "category": "Trabajo", "polarity": "positive", "order": 1, "data_key": "trabajo_accion_pos", "max_selections": 5, "is_cognitive": False}),
        ("trabajo_neg",      {"text": "Si pudieras, ¿a quién evitarías para un trabajo en equipo?", "type": "[Acción Real]", "category": "Trabajo", "polarity": "negative", "order": 2, "data_key": "trabajo_accion_neg", "max_selections": 5, "is_cognitive": False}),
        ("meta_trabajo_pos", {"text": "¿Quiénes crees que te elegirían a ti para un trabajo en equipo?", "type": "[Meta-Percepción]", "category": "Trabajo", "polarity": "positive", "order": 3, "data_key": "trabajo_meta_pos", "max_selections": 5, "is_cognitive": True, "perceived_nominator": "[SELF]"}),
        ("meta_trabajo_neg", {"text": "¿Quiénes crees que te evitarían a ti para un trabajo en equipo?", "type": "[Meta-Percepción]", "category": "Trabajo", "polarity": "negative", "order": 4, "data_key": "trabajo_meta_neg", "max_selections": 5, "is_cognitive": True, "perceived_nominator": "[SELF]"}),
    ])
    # --- FIN DE LA MODIFICACIÓN ---

    # 4. Respuestas de acciones reales con las nuevas data_key
    responses.update({
        (institucion_nombre, "4to Grado B", "Javier Díaz"):  {"trabajo_accion_pos": ["Juan Pérez", "Jesús Sánchez"], "trabajo_accion_neg": ["José López", "Jorge Ruiz"]},
        (institucion_nombre, "4to Grado B", "Julio García"): {"trabajo_accion_pos": ["Javier Díaz", "José López", "Jorge Ruiz"], "trabajo_accion_neg": ["Juan Pérez"]},
        (institucion_nombre, "4to Grado B", "José López"):   {"trabajo_accion_pos": ["Julio García", "Jorge Ruiz"], "trabajo_accion_neg": ["Juan Pérez"]},
        (institucion_nombre, "4to Grado B", "Juan Pérez"):   {"trabajo_accion_pos": ["José López", "Jesús Sánchez"], "trabajo_accion_neg": []},
        (institucion_nombre, "4to Grado B", "Jorge Ruiz"):   {"trabajo_accion_pos": ["Javier Díaz", "Julio García", "Juan Pérez"], "trabajo_accion_neg": []},
        (institucion_nombre, "4to Grado B", "Jesús Sánchez"):{"trabajo_accion_pos": ["Javier Díaz", "Juan Pérez"], "trabajo_accion_neg": []},
    })

    # 5. Datos cognitivos con las nuevas data_key
    cognitive_data.update({
        (institucion_nombre, "4to Grado B", "Javier Díaz"): {
            "trabajo_meta_pos": {"Javier Díaz": ["Julio García", "Juan Pérez", "Jesús Sánchez"]},
            "trabajo_meta_neg": {"Javier Díaz": ["Jorge Ruiz"]}
        },
        (institucion_nombre, "4to Grado B", "Julio García"): {
            "trabajo_meta_pos": {"Julio García": ["Javier Díaz", "José López"]},
            "trabajo_meta_neg": {"Julio García": ["Jorge Ruiz", "Jesús Sánchez"]}
        },
        (institucion_nombre, "4to Grado B", "José López"): {
            "trabajo_meta_pos": {"José López": ["Julio García", "Juan Pérez"]},
            "trabajo_meta_neg": {"José López": ["Jorge Ruiz", "Jesús Sánchez"]}
        },
        (institucion_nombre, "4to Grado B", "Juan Pérez"): {
            "trabajo_meta_pos": {"Juan Pérez": ["Jesús Sánchez"]},
            "trabajo_meta_neg": {"Juan Pérez": []}
        },
        (institucion_nombre, "4to Grado B", "Jorge Ruiz"): {
            "trabajo_meta_pos": {"Jorge Ruiz": ["Julio García", "Juan Pérez"]},
            "trabajo_meta_neg": {"Jorge Ruiz": []}
        },
        (institucion_nombre, "4to Grado B", "Jesús Sánchez"): {
            "trabajo_meta_pos": {"Jesús Sánchez": ["José López", "Juan Pérez"]},
            "trabajo_meta_neg": {"Jesús Sánchez": []}
        },
    })
    # --- FIN DE LA MODIFICACIÓN ---