# sociograma_data.py
# (v1.11 - Versión final con el orden de los miembros y columnas sincronizado con la referencia de Colab)

import collections
import datetime
import re
import unicodedata

# --- Estructuras de Datos Globales ---
schools_data = collections.OrderedDict()
classes_data = collections.OrderedDict()
members_data = collections.OrderedDict()
questionnaire_responses_data = collections.OrderedDict()
question_definitions = collections.OrderedDict()
relationship_types_map = collections.OrderedDict()
sociogram_relation_options_map = collections.OrderedDict()

# --- FUNCIONES HELPER LOCALES ---
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
    """
    Regenera los mapas de relaciones para un grupo, usando el texto de la
    pregunta para los labels, asegurando que se muestre la descripción correcta.
    """
    global relationship_types_map, sociogram_relation_options_map
    relationship_types_map.clear()
    sociogram_relation_options_map.clear()
    
    # Opción por defecto para seleccionar "todos" los tipos de relación
    sociogram_relation_options_map["all"] = "Todos los Tipos de Relación"
    
    current_class_questions = get_class_question_definitions(institution_name, group_name)
    
    if not isinstance(current_class_questions, collections.OrderedDict) or not current_class_questions:
        return # No hacer nada si no hay preguntas definidas
        
    try:
        # Ordenar las preguntas por su propiedad 'order' para una visualización consistente
        sorted_q_items = sorted(
            current_class_questions.items(), 
            key=lambda item: (item[1].get('order', 999), item[0])
        )
        
        for q_id, q_def in sorted_q_items:
            data_key = q_def.get('data_key', q_id)
            q_type_desc = q_def.get('type', 'General')
            
            # Determinar el prefijo de polaridad
            polarity = q_def.get('polarity')
            if polarity == 'positive':
                polarity_char = "Pos"
            elif polarity == 'negative':
                polarity_char = "Neg"
            else:
                polarity_char = "Neu"
            
            # --- INICIO DE LA NUEVA LÓGICA ---
            # Ahora usamos la Categoría/Tipo de la pregunta para el label.
            # Mantenemos el prefijo de polaridad para que siga siendo útil.
            # CAMBIO 1: Añadir esta línea para obtener la categoría
            categoria_pregunta = q_def.get('type', 'General') 

            # CAMBIO 2: Reemplazar 'q_id' por 'categoria_pregunta'
            label_for_map = f"({polarity_char}) {categoria_pregunta}"
            # --- FIN DE LA NUEVA LÓGICA ---

            # Este mapa se puede usar internamente si se necesita el tipo y la polaridad
            relationship_types_map[data_key] = f"{q_def.get('polarity','neutral').title()} - {q_type_desc}"

            # Este es el mapa que usa la UI para generar los checkboxes
            sociogram_relation_options_map[data_key] = label_for_map
            
    except Exception as e:
        print(f"ERROR (sociograma_data.regenerate_relationship_maps): {e}")

def initialize_data():
    """Inicializa todas las estructuras de datos con el orden de miembros corregido."""
    global schools_data, classes_data, members_data, questionnaire_responses_data, question_definitions

    print("Inicializando datos de ejemplo (con orden de miembros corregido para coincidir con Colab)...")

    institucion1_nombre_es = "Colegio \"Miguel de Cervantes\""
    institucion2_nombre_es = "Instituto \"Benito Juárez\""

    schools_data.clear(); classes_data.clear(); members_data.clear()
    question_definitions.clear(); questionnaire_responses_data.clear()

    schools_data.update({
        institucion1_nombre_es: "Anotaciones para el Colegio Cervantes. Grupo piloto.",
        institucion2_nombre_es: "Notas: Instituto con enfoque en ciencias sociales."
    })
    classes_data.update({
        institucion1_nombre_es: [{"name": "4to Grado A", "coordinator": "Diana Batista", "ins2": "Cristina Reyes", "ins3": "", "sostegno": "Marcos Neri", "annotations": "Grupo piloto. Activo."}, {"name": "4to Grado B", "coordinator": "Mario Romero", "ins2": "", "ins3": "", "sostegno": "", "annotations": "Grupo más tranquilo."}],
        institucion2_nombre_es: [{"name": "1er Año A (Secundaria)", "coordinator": "Prof. Elena Rivas", "ins2": "Prof. Luis Bravo", "ins3": "", "sostegno": "", "annotations": "Primer grupo."}, {"name": "2do Año A (Secundaria)", "coordinator": "Prof. Juan Herrera", "ins2": "", "ins3": "", "sostegno": "", "annotations": ""}]
    })

    # --- ORDEN DE MIEMBROS CORREGIDO PARA COINCIDIR CON LA IMAGEN DE REFERENCIA ---
    members_data.update({
        institucion1_nombre_es: collections.OrderedDict({
            "4to Grado A": [
                # Orden Femenino
                {"cognome": "MARTÍNEZ", "nome": "Adela", "iniz": "AMX", "sexo": "Femenino", "fecha_nac": "25/05/2015", "annotations": ""},
                {"cognome": "BERNAL", "nome": "Alicia", "iniz": "ABX", "sexo": "Femenino", "fecha_nac": "20/01/2015", "annotations": ""},
                {"cognome": "VARGAS", "nome": "Carmen", "iniz": "CVX", "sexo": "Femenino", "fecha_nac": "22/07/2015", "annotations": ""},
                {"cognome": "BENÍTEZ", "nome": "Daniela", "iniz": "DBX", "sexo": "Femenino", "fecha_nac": "10/07/2015", "annotations": ""},
                {"cognome": "FLORES", "nome": "Jéssica", "iniz": "JFX", "sexo": "Femenino", "fecha_nac": "12/04/2015", "annotations": ""},
                {"cognome": "RAMÍREZ", "nome": "Luisa", "iniz": "LRX", "sexo": "Femenino", "fecha_nac": "03/02/2015", "annotations": ""},
                {"cognome": "GUTIÉRREZ", "nome": "Martina", "iniz": "MGX", "sexo": "Femenino", "fecha_nac": "08/12/2014", "annotations": ""},
                {"cognome": "AGUILAR", "nome": "Ángela", "iniz": "ÁAX", "sexo": "Femenino", "fecha_nac": "15/03/2015", "annotations": "Miembro participativa."},
                # Orden Masculino
                {"cognome": "ROJAS", "nome": "Alejandro", "iniz": "ARX", "sexo": "Masculino", "fecha_nac": "14/10/2014", "annotations": ""},
                {"cognome": "BRAVO", "nome": "Esteban", "iniz": "EBX", "sexo": "Masculino", "fecha_nac": "10/10/2014", "annotations": ""},
                {"cognome": "NAVARRO", "nome": "Manuel", "iniz": "MNX", "sexo": "Masculino", "fecha_nac": "18/08/2015", "annotations": "Miembro nuevo este año."},
                {"cognome": "CASTILLO", "nome": "Marcos", "iniz": "MCX", "sexo": "Masculino", "fecha_nac": "05/09/2015", "annotations": ""},
                {"cognome": "BLANCO", "nome": "Mateo", "iniz": "MBX", "sexo": "Masculino", "fecha_nac": "02/11/2014", "annotations": "Líder natural."},
                {"cognome": "VIDAL", "nome": "Matías", "iniz": "MVX", "sexo": "Masculino", "fecha_nac": "01/06/2015", "annotations": ""},
                {"cognome": "VELÁZQUEZ", "nome": "Nicolás", "iniz": "NVX", "sexo": "Masculino", "fecha_nac": "09/04/2015", "annotations": "Necesita apoyo."},
                {"cognome": "GÓMEZ", "nome": "Óscar", "iniz": "ÓGX", "sexo": "Masculino", "fecha_nac": "30/06/2015", "annotations": ""}
            ],
            "4to Grado B": [{"cognome": "ROMERO", "nome": "Mario", "iniz": "MRO", "sexo": "Masculino"}, {"cognome": "BELTRÁN", "nome": "Laura", "iniz": "LBE", "sexo": "Femenino"}]
        }),
        institucion2_nombre_es: collections.OrderedDict({
            "1er Año A (Secundaria)": [{"cognome": "RÍOS", "nome": "Julia", "iniz": "JRI", "sexo": "Femenino"}, {"cognome": "CAMPOS", "nome": "Marco", "iniz": "MCA", "sexo": "Masculino"}],
            "2do Año A (Secundaria)": []
        })
    })

    # Asegurar que cada par institución/grupo tenga una entrada en members_data
    for inst, group_list in classes_data.items():
        if inst not in members_data: members_data[inst] = collections.OrderedDict()
        for group in group_list:
            if group['name'] not in members_data[inst]: members_data[inst][group['name']] = []
    
    for inst, group_list in classes_data.items():
        for group in group_list:
            class_key = (inst, group['name'])
            question_definitions[class_key] = collections.OrderedDict([
                ("q_asiento_pos", {"text": "Si pudieras elegir, ¿a quién querrías como compañero de asiento?", "type": "Asiento", "polarity": "positive", "order": 1, "data_key": "q_asiento_pos", "max_selections": 2, "allow_self_selection": False}),
                ("q_trabajo_pos", {"text": "Indica los nombres de dos compañeros con quienes crees que te iría bien trabajando en grupo para realizar una tarea escolar.", "type": "Tarea Escolar", "polarity": "positive", "order": 2, "data_key": "q_trabajo_pos", "max_selections": 2, "allow_self_selection": True}),
                ("q_juego_pos", {"text": "Si tuvieras que organizar un picnic, ¿a qué compañeros invitarías?", "type": "Picnic/Juego", "polarity": "positive", "order": 3, "data_key": "q_juego_pos", "max_selections": 2, "allow_self_selection": True}),
                ("q_asiento_neg", {"text": "Si pudieras elegir, ¿a quién evitarías totalmente como compañero de asiento?", "type": "Asiento", "polarity": "negative", "order": 4, "data_key": "q_asiento_neg", "max_selections": 2, "allow_self_selection": False}),
                ("q_trabajo_neg", {"text": "Indica los nombres de dos compañeros con quienes no querrías trabajar en absoluto para realizar una tarea escolar.", "type": "Tarea Escolar", "polarity": "negative", "order": 5, "data_key": "q_trabajo_neg", "max_selections": 2, "allow_self_selection": False}),
                ("q_juego_neg", {"text": "Indica los nombres de dos compañeros a quienes preferirías no invitar al picnic.", "type": "Picnic/Juego", "polarity": "negative", "order": 6, "data_key": "q_juego_neg", "max_selections": 2, "allow_self_selection": False})
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
        (institucion2_nombre_es, "1er Año A (Secundaria)", "Julia Ríos"): { "q_asiento_pos": ["Marco Campos"], "q_trabajo_pos": ["Marco Campos"], "q_juego_pos": ["Marco Campos"] },
        (institucion2_nombre_es, "1er Año A (Secundaria)", "Marco Campos"): { "q_asiento_pos": ["Julia Ríos"], "q_trabajo_pos": ["Julia Ríos"], "q_juego_neg": ["Julia Ríos"] }
    })
    
    # Inicializar mapas para la primera institución/grupo
    initial_context_institution = list(schools_data.keys())[0] if schools_data else None
    initial_context_group = classes_data[initial_context_institution][0]['name'] if initial_context_institution and classes_data.get(initial_context_institution) else None
    if initial_context_institution and initial_context_group:
        regenerate_relationship_maps_for_class(initial_context_institution, initial_context_group)

    print("Datos de ejemplo COMPLETOS cargados y sincronizados.")


print("sociograma_data.py listo para su uso en la aplicación de escritorio.")