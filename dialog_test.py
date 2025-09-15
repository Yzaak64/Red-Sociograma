# Archivo: dialog_test.py
# Ejecútalo para probar la ventana de forma aislada.

import tkinter as tk
from tkinter import ttk, messagebox

# --- ESTA ES LA CLASE DEFINITIVA Y AUTOCONTENIDA ---
# Una vez que confirmes que funciona, la copiaremos a tu proyecto.

class ConfirmQuestionsDialog(tk.Toplevel):
    """
    Versión FINAL y ROBUSTA. Garantiza scrolls y botón de maximizar
    usando el layout '.grid()' de manera consistente y sin interferencias.
    """
    def __init__(self, parent, questions_data):
        super().__init__(parent)
        
        # ELIMINAMOS self.transient(parent) para GARANTIZAR el botón de maximizar.
        self.grab_set()  # Mantenemos esto para que la ventana sea modal.
        
        self.title("Confirmar Detalles de Importación")
        self.geometry("850x600")
        self.minsize(600, 400)
        
        # Esta línea permite que la ventana sea redimensionable (y por tanto, maximizable).
        self.resizable(True, True) 
        
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self.result = None
        self.question_widgets = []

        # Usamos .grid() para el layout principal para un control total del espacio.
        # Hacemos que la única celda (0,0) de la ventana se expanda con ella.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_widgets(questions_data)
        
        self.wait_window(self)

    def _create_widgets(self, questions_data):
        # Frame principal que se expandirá para llenar la ventana.
        main_frame = ttk.Frame(self, padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)  # La fila del scroll (1) se expandirá.
        main_frame.grid_columnconfigure(0, weight=1) # La columna del scroll (0) se expandirá.

        # --- Cabecera ---
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        
        ttk.Label(header_frame, text="Confirmar Detalles de Nuevas Preguntas", font=("-size 14 -weight bold")).pack(anchor='w')
        ttk.Label(
            header_frame, 
            text="Para cada pregunta, confirma su polaridad (márcala si es positiva) y edita la categoría sugerida si es necesario.",
            justify=tk.LEFT
        ).pack(anchor='w', pady=(5, 0))

        # --- Contenedor para Canvas y Scrollbars ---
        scroll_container = ttk.Frame(main_frame)
        scroll_container.grid(row=1, column=0, sticky='nsew')
        scroll_container.grid_rowconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(0, weight=1)

        # --- Canvas y Scrollbars ---
        canvas = tk.Canvas(scroll_container, borderwidth=0, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(scroll_container, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        canvas.grid(row=0, column=0, sticky='nsew')

        scrollable_frame = ttk.Frame(canvas, padding="10")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # --- Poblar con las preguntas ---
        for i, (text, details) in enumerate(questions_data.items()):
            data_key = details['data_key']
            if i > 0:
                ttk.Separator(scrollable_frame).pack(fill='x', expand=True, pady=15)
            
            card = ttk.Frame(scrollable_frame)
            card.pack(fill='x', expand=True)
            
            ttk.Label(card, text=f'Pregunta: "{text}"').pack(anchor='w', pady=(0, 8))
            
            polarity_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(card, text="Es una pregunta Positiva (de aceptación)", variable=polarity_var).pack(anchor='w', padx=20)
            
            category_var = tk.StringVar(value=details['suggested_category'])
            category_frame = ttk.Frame(card)
            category_frame.pack(fill='x', expand=True, padx=20, pady=8)
            ttk.Label(category_frame, text="Categoría:").pack(side=tk.LEFT, pr=5)
            ttk.Entry(category_frame, textvariable=category_var, width=30).pack(side=tk.LEFT)

            self.question_widgets.append((data_key, polarity_var, category_var))

        # --- Botones de acción ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky='e', pady=(15, 0))
        ttk.Button(button_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Confirmar e Importar", command=self._on_confirm).pack(side=tk.RIGHT)

    def _on_confirm(self):
        confirmed_data = {}
        for data_key, polarity_var, category_var in self.question_widgets:
            polarity = 'positive' if polarity_var.get() else 'negative'
            confirmed_data[data_key] = {'polarity': polarity, 'category': category_var.get().strip() or "General"}
        self.result = confirmed_data
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

# --- Aplicación de Ejemplo para Probar la Ventana ---
class SampleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Prueba de Diálogo de Importación")
        self.geometry("400x150")
        
        label = ttk.Label(self, text="Haz clic en el botón para probar la ventana.")
        label.pack(pady=20)
        
        button = ttk.Button(self, text="Procesar Archivo CSV (Simulado)", command=self.open_dialog)
        button.pack(pady=10)

    def open_dialog(self):
        # Datos de ejemplo que tu función `handle_csv_import_stage1` generaría
        sample_data = {
            'Si pudieras elegir, ¿a quién evitarías totalmente como compañero de asiento en un viaje muy largo?': {
                'data_key': 'q_evitar_asiento', 'suggested_category': 'Evitarias'
            },
            'Si pudieras elegir, ¿a quién querrías como compañero de asiento?': {
                'data_key': 'q_querer_asiento', 'suggested_category': 'Querrias'
            },
            'Indica los nombres de dos compañeros a quienes preferirías no invitar al picnic.': {
                'data_key': 'q_no_invitar', 'suggested_category': 'Preferirias'
            },
            'Pregunta muy larga para probar el scroll horizontal. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.': {
                'data_key': 'q_larga', 'suggested_category': 'Larga'
            },
            'Pregunta 5': {'data_key': 'q5', 'suggested_category': 'General'},
            'Pregunta 6': {'data_key': 'q6', 'suggested_category': 'General'},
            'Pregunta 7': {'data_key': 'q7', 'suggested_category': 'General'},
            'Pregunta 8': {'data_key': 'q8', 'suggested_category': 'General'}
        }
        
        dialog = ConfirmQuestionsDialog(self, sample_data)
        
        if dialog.result is not None:
            messagebox.showinfo("Éxito", f"El diálogo se cerró y devolvió:\n{dialog.result}")
        else:
            messagebox.showwarning("Cancelado", "El diálogo fue cancelado.")

if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()
    