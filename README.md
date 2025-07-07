# Aplicación de Escritorio para Sociogramas <a href="https://www.buymeacoffee.com/Yzaak64" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-green.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

Esta es una aplicación de escritorio completa, desarrollada con Python y FreeSimpleGUI, para la creación, gestión y análisis de datos sociométricos. Permite visualizar las dinámicas de grupo a través de sociogramas interactivos, matrices sociométricas y dianas de afinidad.

## Características

*   **Gestión Jerárquica:** Organiza los datos en Instituciones, Grupos y Miembros.
*   **Creación de Cuestionarios:** Permite definir cuestionarios personalizados para cada grupo, estableciendo el texto, polaridad (positiva/negativa), orden y número de elecciones para cada pregunta.
*   **Registro de Datos Detallado:** Un formulario dedicado para registrar las elecciones de cada miembro.
*   **Sociograma Interactivo:** Genera un grafo interactivo donde los nodos (miembros) y las aristas (elecciones) pueden ser filtrados y estilizados para un análisis profundo. Los filtros incluyen sexo, tipo de relación, reciprocidad y foco en un participante específico.
*   **Matriz Sociométrica:** Crea una tabla que resume numéricamente "quién elige a quién", con subtotales por género y totales generales.
*   **Diana de Afinidad:** Visualiza los niveles de integración social colocando a los miembros en círculos concéntricos según la cantidad de elecciones recibidas.
*   **Importación y Exportación CSV:** Funcionalidad robusta para cargar y descargar datos masivamente, compatible con el formato de Google Forms, incluyendo opciones granulares para la gestión de entidades, preguntas y respuestas.
*   **Generación de Reportes PDF:** Exporta la Matriz Sociométrica, resúmenes de cuestionario y plantillas en blanco a formato PDF.

## Requisitos (para ejecutar desde el código fuente)

*   Python 3.9
*   Librerías listadas en `requirements.txt`. Puedes instalarlas usando pip:
    ```bash
    pip install -r requirements.txt
    ```
    Las principales dependencias son:
    *   `FreeSimpleGUI`
    *   `pandas`, `numpy`
    *   `matplotlib`
    *   `networkx`
    *   `reportlab`
    *   `Pillow`

## Uso

**Opción 1: Ejecutar desde el Código Fuente**

1.  Asegúrate de tener Python y las librerías requeridas instaladas.
2.  Clona o descarga este repositorio.
3.  Abre una terminal o símbolo del sistema en la carpeta del proyecto.
4.  Ejecuta el script principal:
    ```bash
    python Red_Sociograma_App.py
    ```
5.  Sigue las opciones en la interfaz gráfica que aparecerá.

**Opción 2: Usar el Ejecutable (Windows)**

1.  Ve a la sección [**Releases**](https://github.com/TuUsuario/Red-Sociograma-App/releases) de este repositorio. *(Recuerda cambiar `TuUsuario` y el nombre del repo por los tuyos)*.
2.  Descarga el archivo `.zip` de la última versión disponible (ej. `Red_Sociograma_v1.0.zip`).
3.  Descomprime la carpeta en tu computadora.
4.  Haz doble clic en el archivo `Red Sociograma.exe` para iniciar la aplicación. No requiere instalación de Python.

**Opción 3: Probar en Google Colab (Demo Online)**

1.  Haz clic en el siguiente enlace para abrir una versión del núcleo de la aplicación directamente en tu navegador usando Google Colab:
    [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1D0cQItenmmMBM9mF4oSU6SOUdGvApeHn)
    *(O copia y pega esta URL: `https://colab.research.google.com/drive/1D0cQItenmmMBM9mF4oSU6SOUdGvApeHn`)*
2.  Es posible que Colab muestre una advertencia. Haz clic en "Ejecutar de todos modos".
3.  Ejecuta las celdas de código. **Nota:** Esta versión de Colab se enfoca en la lógica de cálculo y la generación de los gráficos. Las funciones de la interfaz gráfica de FreeSimpleGUI no estarán disponibles.

## Generación del Ejecutable (Instrucciones para desarrollador)

Si deseas crear el archivo `.exe` tú mismo desde el código fuente:

1.  Asegúrate de tener Python y las librerías de `requirements.txt` instaladas en tu entorno (preferiblemente un entorno virtual).
2.  Instala PyInstaller: `pip install pyinstaller`
3.  Navega a la carpeta raíz del proyecto en tu terminal.
4.  Asegúrate de que el archivo de ícono `Red_Sociograma.ico` y la imagen `Buy_Coffe.png` estén presentes.
5.  Ejecuta el comando usando el archivo de configuración `.spec` (recomendado):
    ```bash
    pyinstaller Red_Sociograma_App.spec
    ```
6.  La aplicación completa (`Red Sociograma.exe` y sus dependencias) se encontrará en la subcarpeta `dist/Red Sociograma`.

## Notas

*   La importación desde CSV es muy potente pero requiere que el archivo siga la estructura especificada en el manual de usuario (accesible desde la propia aplicación).
*   Se recomienda usar la plantilla generada por la aplicación para asegurar la compatibilidad al recolectar datos.