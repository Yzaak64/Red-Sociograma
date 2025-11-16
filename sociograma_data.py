# sociograma_data.py
# (v1.28 - ESTRUCTURA MODULAR: Los datos del Grupo B ahora se cargan desde data_grupo_b.py)

import collections
import datetime
import re
import unicodedata

# --- INICIO DE LA MODIFICACIÓN: Importar el nuevo módulo de datos ---
import data_grupo_b
# --- FIN DE LA MODIFICACIÓN ---

# --- Estructuras de Datos Globales ---
schools_data = collections.OrderedDict()
classes_data = collections.OrderedDict()
members_data = collections.OrderedDict()
questionnaire_responses_data = collections.OrderedDict() 
question_definitions = collections.OrderedDict()
cognitive_social_structures_data = collections.OrderedDict()
relationship_types_map = collections.OrderedDict()
sociogram_relation_options_map = collections.OrderedDict()

# --- FUNCIONES HELPER (sin cambios) ---
def _generar_iniciales_local(nombre_str, apellido_str):
    iniciales = []
    if nombre_str:
        for parte_n in nombre_str.strip().split():
            if parte_n: iniciales.append(parte_n[0].upper())
    if apellido_str:
        for parte_a in apellido_str.strip().split():
            if parte_a: iniciales.append(parte_a[0].upper())
    final_str_iniciales = "".join(iniciales)
    if not final_str_iniciales: return "N/A"
    return final_str_iniciales[:4] if len(final_str_iniciales) > 4 else final_str_iniciales.ljust(3, 'X')

def get_class_question_definitions(institution_name, group_name):
    class_key = (institution_name, group_name)
    if class_key not in question_definitions:
        question_definitions[class_key] = collections.OrderedDict()
    return question_definitions[class_key]

def regenerate_relationship_maps_for_class(institution_name, group_name):
    global relationship_types_map, sociogram_relation_options_map
    relationship_types_map.clear()
    sociogram_relation_options_map.clear()
    sociogram_relation_options_map["all"] = "Todos los Tipos de Relación"
    current_class_questions = get_class_question_definitions(institution_name, group_name)
    if not isinstance(current_class_questions, collections.OrderedDict) or not current_class_questions:
        return
    try:
        sorted_q_items = sorted(
            current_class_questions.items(), 
            key=lambda item: (item[1].get('order', 999), item[0])
        )
        for q_id, q_def in sorted_q_items:
            data_key = q_def.get('data_key', q_id)
            polarity = q_def.get('polarity')
            polarity_char = "Pos" if polarity == 'positive' else "Neg" if polarity == 'negative' else "Neu"
            categoria_pregunta = q_def.get('type', 'General') 
            label_for_map = f"({polarity_char}) {categoria_pregunta}"
            relationship_types_map[data_key] = f"{q_def.get('polarity','neutral').title()} - {q_def.get('type', 'General')}"
            sociogram_relation_options_map[data_key] = label_for_map
    except Exception as e:
        print(f"ERROR (sociograma_data.regenerate_relationship_maps): {e}")

# --- INICIO DE LA MODIFICACIÓN: Función initialize_data() actualizada ---
def initialize_data():
    """
    Inicializa los datos de ejemplo de forma modular.
    - Carga los datos del "4to Grado A" directamente.
    - Llama a una función externa para cargar los datos del "4to Grado B".
    """
    global schools_data, classes_data, members_data, questionnaire_responses_data, question_definitions, cognitive_social_structures_data

    print("Inicializando datos de forma MODULAR...")

    institucion1_nombre_es = "Colegio \"Miguel de Cervantes\""
    
    # Limpiar todas las estructuras de datos antes de cargar
    schools_data.clear(); classes_data.clear(); members_data.clear()
    question_definitions.clear(); questionnaire_responses_data.clear()
    cognitive_social_structures_data.clear()

    # --- DATOS BASE DE INSTITUCIONES Y GRUPOS (SIN GRUPO B) ---
    schools_data.update({ institucion1_nombre_es: "Anotaciones para el Colegio Cervantes." })
    classes_data.update({
        institucion1_nombre_es: [
            {"name": "4to Grado A", "coordinator": "Diana Batista", "annotations": "Grupo piloto de 16 miembros."},
            # La entrada del Grupo B se añadirá desde el módulo externo
        ]
    })

    # --- DATOS DEL "4TO GRADO A" (INTACTOS) ---
    members_data.update({
        institucion1_nombre_es: collections.OrderedDict({
            "4to Grado A": [
                {"cognome": "MARTÍNEZ", "nome": "Adela", "iniz": "AMX", "sexo": "Femenino"}, {"cognome": "BERNAL", "nome": "Alicia", "iniz": "ABX", "sexo": "Femenino"},
                {"cognome": "VARGAS", "nome": "Carmen", "iniz": "CVX", "sexo": "Femenino"}, {"cognome": "BENÍTEZ", "nome": "Daniela", "iniz": "DBX", "sexo": "Femenino"},
                {"cognome": "FLORES", "nome": "Jéssica", "iniz": "JFX", "sexo": "Femenino"}, {"cognome": "RAMÍREZ", "nome": "Luisa", "iniz": "LRX", "sexo": "Femenino"},
                {"cognome": "GUTIÉRREZ", "nome": "Martina", "iniz": "MGX", "sexo": "Femenino"}, {"cognome": "AGUILAR", "nome": "Ángela", "iniz": "ÁAX", "sexo": "Femenino"},
                {"cognome": "ROJAS", "nome": "Alejandro", "iniz": "ARX", "sexo": "Masculino"}, {"cognome": "BRAVO", "nome": "Esteban", "iniz": "EBX", "sexo": "Masculino"},
                {"cognome": "NAVARRO", "nome": "Manuel", "iniz": "MNX", "sexo": "Masculino"}, {"cognome": "CASTILLO", "nome": "Marcos", "iniz": "MCX", "sexo": "Masculino"},
                {"cognome": "BLANCO", "nome": "Mateo", "iniz": "MBX", "sexo": "Masculino"}, {"cognome": "VIDAL", "nome": "Matías", "iniz": "MVX", "sexo": "Masculino"},
                {"cognome": "VELÁZQUEZ", "nome": "Nicolás", "iniz": "NVX", "sexo": "Masculino"}, {"cognome": "GÓMEZ", "nome": "Óscar", "iniz": "ÓGX", "sexo": "Masculino"}
            ],
            # El diccionario para "4to Grado B" se creará desde el módulo externo
        })
    })

    question_definitions[(institucion1_nombre_es, "4to Grado A")] = collections.OrderedDict([
        ("q_asiento_pos", {"text": "Si pudieras elegir, ¿a quién querrías como compañero de asiento?", "type": "Asiento", "polarity": "positive", "order": 1, "data_key": "q_asiento_pos", "max_selections": 2}),
        ("q_trabajo_pos", {"text": "Indica dos compañeros con quienes te iría bien trabajando.", "type": "Tarea Escolar", "polarity": "positive", "order": 2, "data_key": "q_trabajo_pos", "max_selections": 2}),
        ("q_juego_pos", {"text": "Si tuvieras que organizar un picnic, ¿a qué compañeros invitarías?", "type": "Picnic/Juego", "polarity": "positive", "order": 3, "data_key": "q_juego_pos", "max_selections": 2}),
        ("q_asiento_neg", {"text": "Si pudieras elegir, ¿a quién evitarías como compañero de asiento?", "type": "Asiento", "polarity": "negative", "order": 4, "data_key": "q_asiento_neg", "max_selections": 2}),
        ("q_trabajo_neg", {"text": "Indica dos compañeros con quienes no querrías trabajar.", "type": "Tarea Escolar", "polarity": "negative", "order": 5, "data_key": "q_trabajo_neg", "max_selections": 2}),
        ("q_juego_neg", {"text": "Indica dos compañeros a quienes preferirías no invitar al picnic.", "type": "Picnic/Juego", "polarity": "negative", "order": 6, "data_key": "q_juego_neg", "max_selections": 2})
    ])

    questionnaire_responses_data.update({
        (institucion1_nombre_es, "4to Grado A", "Ángela Aguilar"): {"q_asiento_pos": ["Luisa Ramírez", "Adela Martínez"], "q_trabajo_pos": ["Adela Martínez", "Alicia Bernal"], "q_juego_pos": ["Luisa Ramírez", "Adela Martínez"], "q_asiento_neg": ["Alejandro Rojas", "Manuel Navarro"], "q_trabajo_neg": ["Alejandro Rojas", "Manuel Navarro"], "q_juego_neg": ["Manuel Navarro", "Alejandro Rojas"]},
        (institucion1_nombre_es, "4to Grado A", "Daniela Benítez"): { "q_asiento_pos": ["Martina Gutiérrez", "Jéssica Flores"], "q_trabajo_pos": ["Ángela Aguilar", "Alicia Bernal"], "q_juego_pos": ["Adela Martínez", "Martina Gutiérrez"], "q_asiento_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_trabajo_neg": ["Matías Vidal", "Nicolás Velázquez"], "q_juego_neg": ["Nicolás Velázquez", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Mateo Blanco"): { "q_asiento_pos": ["Marcos Castillo", "Óscar Gómez"], "q_trabajo_pos": ["Marcos Castillo", "Óscar Gómez"], "q_juego_pos": ["Marcos Castillo", "Óscar Gómez"], "q_asiento_neg": ["Alejandro Rojas", "Nicolás Velázquez"], "q_trabajo_neg": ["Alejandro Rojas", "Nicolás Velázquez"], "q_juego_neg": ["Alejandro Rojas", "Nicolás Velázquez"] },
        (institucion1_nombre_es, "4to Grado A", "Alicia Bernal"): { "q_asiento_pos": ["Martina Gutiérrez", "Luisa Ramírez"], "q_trabajo_pos": ["Ángela Aguilar", "Martina Gutiérrez"], "q_juego_pos": ["Luisa Ramírez", "Carmen Vargas"], "q_asiento_neg": ["Nicolás Velázquez", "Manuel Navarro"], "q_trabajo_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_juego_neg": ["Esteban Bravo", "Jéssica Flores"] },
        (institucion1_nombre_es, "4to Grado A", "Marcos Castillo"): { "q_asiento_pos": ["Óscar Gómez", "Mateo Blanco"], "q_trabajo_pos": ["Óscar Gómez", "Mateo Blanco"], "q_juego_pos": ["Óscar Gómez", "Mateo Blanco"], "q_asiento_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_trabajo_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_juego_neg": ["Nicolás Velázquez", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Jéssica Flores"): { "q_asiento_pos": ["Martina Gutiérrez", "Luisa Ramírez"], "q_trabajo_pos": ["Adela Martínez", "Martina Gutiérrez"], "q_juego_pos": ["Ángela Aguilar", "Martina Gutiérrez"], "q_asiento_neg": ["Nicolás Velázquez", "Esteban Bravo"], "q_trabajo_neg": ["Alejandro Rojas", "Mateo Blanco"], "q_juego_neg": ["Nicolás Velázquez", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Óscar Gómez"): { "q_asiento_pos": ["Mateo Blanco", "Martina Gutiérrez"], "q_trabajo_pos": ["Ángela Aguilar", "Carmen Vargas"], "q_juego_pos": ["Marcos Castillo", "Alejandro Rojas"], "q_asiento_neg": ["Marcos Castillo", "Mateo Blanco"], "q_trabajo_neg": ["Nicolás Velázquez", "Matías Vidal"], "q_juego_neg": ["Matías Vidal", "Nicolás Velázquez"] },
        (institucion1_nombre_es, "4to Grado A", "Martina Gutiérrez"): { "q_asiento_pos": ["Luisa Ramírez", "Ángela Aguilar"], "q_trabajo_pos": ["Alicia Bernal", "Adela Martínez"], "q_juego_pos": ["Carmen Vargas", "Luisa Ramírez"], "q_asiento_neg": ["Esteban Bravo", "Alejandro Rojas"], "q_trabajo_neg": ["Matías Vidal", "Alejandro Rojas"], "q_juego_neg": ["Nicolás Velázquez", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Adela Martínez"): { "q_asiento_pos": ["Luisa Ramírez", "Martina Gutiérrez"], "q_trabajo_pos": ["Luisa Ramírez", "Martina Gutiérrez"], "q_juego_pos": ["Luisa Ramírez", "Martina Gutiérrez"], "q_asiento_neg": ["Nicolás Velázquez", "Manuel Navarro"], "q_trabajo_neg": [], "q_juego_neg": [] },
        (institucion1_nombre_es, "4to Grado A", "Manuel Navarro"): { "q_asiento_pos": ["Marcos Castillo", "Óscar Gómez"], "q_trabajo_pos": ["Marcos Castillo", "Óscar Gómez"], "q_juego_pos": ["Marcos Castillo", "Óscar Gómez"], "q_asiento_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_trabajo_neg": ["Alejandro Rojas", "Nicolás Velázquez"], "q_juego_neg": ["Alejandro Rojas", "Nicolás Velázquez"] },
        (institucion1_nombre_es, "4to Grado A", "Luisa Ramírez"): { "q_asiento_pos": ["Martina Gutiérrez", "Ángela Aguilar"], "q_trabajo_pos": ["Alicia Bernal", "Adela Martínez"], "q_juego_pos": ["Martina Gutiérrez", "Adela Martínez"], "q_asiento_neg": ["Manuel Navarro", "Nicolás Velázquez"], "q_trabajo_neg": ["Nicolás Velázquez", "Esteban Bravo"], "q_juego_neg": ["Matías Vidal", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Alejandro Rojas"): { "q_asiento_pos": ["Marcos Castillo", "Esteban Bravo"], "q_trabajo_pos": ["Marcos Castillo", "Esteban Bravo"], "q_juego_pos": ["Adela Martínez", "Esteban Bravo"], "q_asiento_neg": ["Manuel Navarro", "Nicolás Velázquez"], "q_trabajo_neg": ["Manuel Navarro", "Nicolás Velázquez"], "q_juego_neg": ["Nicolás Velázquez", "Manuel Navarro"] },
        (institucion1_nombre_es, "4to Grado A", "Carmen Vargas"): { "q_asiento_pos": ["Ángela Aguilar", "Adela Martínez"], "q_trabajo_pos": ["Ángela Aguilar", "Martina Gutiérrez"], "q_juego_pos": ["Alicia Bernal", "Ángela Aguilar"], "q_asiento_neg": ["Alejandro Rojas", "Esteban Bravo"], "q_trabajo_neg": ["Esteban Bravo", "Nicolás Velázquez"], "q_juego_neg": ["Esteban Bravo", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Nicolás Velázquez"): { "q_asiento_pos": ["Marcos Castillo", "Mateo Blanco"], "q_trabajo_pos": ["Marcos Castillo", "Mateo Blanco"], "q_juego_pos": ["Marcos Castillo", "Manuel Navarro"], "q_asiento_neg": ["Esteban Bravo", "Mateo Blanco"], "q_trabajo_neg": ["Alicia Bernal", "Daniela Benítez"], "q_juego_neg": ["Alicia Bernal", "Daniela Benítez"] },
        (institucion1_nombre_es, "4to Grado A", "Matías Vidal"): { "q_asiento_pos": ["Marcos Castillo", "Mateo Blanco"], "q_trabajo_pos": ["Marcos Castillo", "Mateo Blanco"], "q_juego_pos": ["Mateo Blanco", "Marcos Castillo"], "q_asiento_neg": ["Alejandro Rojas", "Esteban Bravo"], "q_trabajo_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_juego_neg": ["Nicolás Velázquez", "Esteban Bravo"] },
        (institucion1_nombre_es, "4to Grado A", "Esteban Bravo"): { "q_asiento_pos": ["Marcos Castillo", "Mateo Blanco"], "q_trabajo_pos": ["Mateo Blanco", "Ángela Aguilar"], "q_juego_pos": ["Marcos Castillo", "Luisa Ramírez"], "q_asiento_neg": ["Carmen Vargas", "Alicia Bernal"], "q_trabajo_neg": ["Matías Vidal", "Carmen Vargas"], "q_juego_neg": ["Alicia Bernal", "Carmen Vargas"] },
    })

    # --- Cargar datos modulares del Grupo B ---
    print("Cargando datos modulares para el Grupo B...")
    data_grupo_b.load_grupo_b_data(
        schools_data,
        classes_data,
        members_data,
        question_definitions,
        questionnaire_responses_data,
        cognitive_social_structures_data
    )
    # --- FIN DE LA MODIFICACIÓN ---
    
    # --- INICIALIZACIÓN FINAL ---
    initial_context_institution = list(schools_data.keys())[0] if schools_data else None
    if initial_context_institution and classes_data.get(initial_context_institution):
        initial_context_group = classes_data[initial_context_institution][0]['name']
        regenerate_relationship_maps_for_class(initial_context_institution, initial_context_group)

    print("Datos cargados y sincronizados de forma modular.")


print("sociograma_data.py listo para su uso en la aplicación de escritorio.")