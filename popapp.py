# popapp.py (Versión de Aislamiento Total - Recomendada)

import tkinter as tk
from tkinter import ttk
import webbrowser
import os
import traceback
import sys

# Intenta importar Pillow, si no está disponible, se usará un botón de texto.
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("ADVERTENCIA (popapp.py): Pillow no está instalado. Se usará un botón de texto.")

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def show_coffee_popup():
    """
    Muestra una ventana emergente en su propia instancia de Tkinter,
    bloqueando la ejecución del script principal hasta que se cierre.
    """
    print("[LOG] Iniciando show_coffee_popup (Aislamiento Total).")
    
    # 1. Crear una instancia de Tkinter temporal y ocultarla inmediatamente.
    temp_root = tk.Tk()
    temp_root.withdraw()

    popup = None
    try:
        # 2. El Toplevel (la ventana del popup) pertenece a la raíz temporal.
        popup = tk.Toplevel(temp_root)
        popup.title("Apoya este Proyecto")
        
        def on_close_popup():
            """Función para cerrar el popup y terminar el bucle de eventos temporal."""
            print("[LOG] Popup cerrado. Destruyendo la instancia temporal de Tkinter.")
            temp_root.quit()      # Rompe el mainloop
            temp_root.destroy()   # Destruye la ventana raíz temporal

        # Asigna la función de cierre al botón 'X' de la ventana
        popup.protocol("WM_DELETE_WINDOW", on_close_popup)
        
        # --- Contenido de la ventana ---
        popup_frame = ttk.Frame(popup, padding="20")
        popup_frame.pack(expand=True, fill=tk.BOTH)

        # Puedes usar un emoji o un texto simple
        ttk.Label(popup_frame, text="❤️", font=("Segoe UI Emoji", 20)).pack(pady=(0, 5))
        
        support_text = "Si esta herramienta te resulta útil, considera apoyar su desarrollo futuro."
        ttk.Label(popup_frame, text=support_text, wraplength=350, justify=tk.CENTER).pack(pady=(0, 20))

        # --- Botón de Apoyo ---
        support_url = "https://www.buymeacoffee.com/Yzaak64"
        image_path = resource_path("Buy_Coffe.png")

        try:
            # Usar imagen si Pillow está disponible y el archivo existe
            if PIL_AVAILABLE and os.path.exists(image_path):
                img = Image.open(image_path)
                img.thumbnail((300, 100), Image.Resampling.LANCZOS)
                popup.coffee_photo = ImageTk.PhotoImage(img) 
                
                # Usamos un botón de Tkinter normal para un mejor control
                coffee_button = tk.Button(
                    popup_frame, 
                    image=popup.coffee_photo, 
                    command=lambda: [webbrowser.open_new(support_url), on_close_popup()], 
                    borderwidth=0, 
                    cursor="hand2"
                )
                coffee_button.pack(pady=10)
            else:
                # Botón de texto como alternativa
                fallback_button = ttk.Button(
                    popup_frame, 
                    text="☕ Invítame un café", 
                    command=lambda: [webbrowser.open_new(support_url), on_close_popup()]
                )
                fallback_button.pack(pady=10)
        except Exception as e:
            print(f"[LOG] ERROR al cargar la imagen del pop-up: {e}")
            traceback.print_exc()
            fallback_button = ttk.Button(
                popup_frame, 
                text="☕ Invítame un café", 
                command=lambda: [webbrowser.open_new(support_url), on_close_popup()]
            )
            fallback_button.pack(pady=10)
        
        # --- Botón para continuar sin apoyar ---
        continue_button = ttk.Button(popup_frame, text="Continuar al programa", command=on_close_popup)
        continue_button.pack(pady=(20, 0))

        # --- Centrar la ventana y hacerla visible ---
        popup.update_idletasks()
        p_width = popup.winfo_width()
        p_height = popup.winfo_height()
        s_width = popup.winfo_screenwidth()
        s_height = popup.winfo_screenheight()
        x = (s_width // 2) - (p_width // 2)
        y = (s_height // 2) - (p_height // 2)
        popup.geometry(f"{p_width}x{p_height}+{x}+{y}")
        
        # Comandos para asegurar que la ventana sea visible y tenga el foco
        popup.attributes('-topmost', True)
        popup.deiconify()
        popup.focus_force()
        popup.grab_set()

        # 3. Iniciar el bucle de eventos para la instancia temporal.
        #    Esto detiene la ejecución del script principal aquí.
        print("[LOG] Iniciando bucle de eventos del popup.")
        temp_root.mainloop()
        print("[LOG] Bucle de eventos del popup finalizado.")

    except Exception as e:
        print(f"ERROR FATAL en show_coffee_popup: {e}")
        traceback.print_exc()
        # Asegurarse de destruir la raíz temporal si algo falla
        if 'temp_root' in locals() and temp_root.winfo_exists():
            temp_root.destroy()

# Esta sección permite probar el popup por sí solo
if __name__ == '__main__':
    print("Ejecutando popapp.py como script independiente para prueba.")
    show_coffee_popup()
    print("Prueba de popapp.py finalizada.")