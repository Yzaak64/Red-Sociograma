# sociogram_viewer.py (Versión Combinada: Servidor HTTP + Bucle Manual)
# Este enfoque ataca tanto el problema de seguridad como el del UI thread.

import sys
import os
import tkinter as tk
from cefpython3 import cefpython as cef
import http.server
import socketserver
import threading
import time

def log_viewer(message):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[VIEWER_LOG {timestamp}] {message}")

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sociograma Interactivo - Visor")
        self.geometry("1200x800")
        self.browser = None
        
        self.browser_frame = tk.Frame(self, bg="white")
        self.browser_frame.pack(fill=tk.BOTH, expand=True)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def embed_browser(self, url):
        log_viewer(f"embed_browser - Incrustando URL: {url}")
        window_info = cef.WindowInfo()
        window_info.SetAsChild(self.browser_frame.winfo_id())
        
        self.browser = cef.CreateBrowserSync(window_info, url=url)
        log_viewer("embed_browser - CreateBrowserSync() completado.")
        
        self.browser_frame.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        if self.browser:
            self.browser.WasResized()

    def on_close(self):
        log_viewer("on_close - INICIO")
        global httpd
        if httpd:
            log_viewer("on_close - Apagando servidor HTTP")
            # El servidor se apaga solo al terminar el programa principal
            httpd.shutdown()

        if self.browser:
            self.browser.CloseBrowser(True)
        
        self.quit() # Usar quit() para terminar el bucle manual
        log_viewer("on_close - FIN")

# Variable global para el servidor
httpd = None

def start_server(directory):
    global httpd
    os.chdir(directory)
    PORT = 8000
    while True:
        try:
            Handler = http.server.SimpleHTTPRequestHandler
            httpd = socketserver.TCPServer(("", PORT), Handler)
            log_viewer(f"Servidor HTTP iniciado en el puerto: {PORT}")
            break
        except OSError:
            PORT += 1
    
    # El servidor se ejecuta en su propio hilo
    httpd.serve_forever()
    log_viewer("Hilo del servidor terminado.")


def main_viewer(file_path):
    log_viewer("main_viewer - INICIO")

    # --- Iniciar el servidor en un hilo ---
    server_dir = os.path.dirname(file_path)
    server_thread = threading.Thread(target=start_server, args=(server_dir,))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.2) # Dar un momento al servidor para que se inicie

    if not httpd:
        log_viewer("Error crítico: no se pudo iniciar el servidor HTTP.")
        return

    # --- Iniciar CEF ---
    # Usamos el modo de bucle manual
    settings = {"multi_threaded_message_loop": False}
    cef.Initialize(settings=settings)
    
    # --- Crear la GUI de Tkinter ---
    app = MainApp()
    
    # --- Incrustar el navegador ---
    port = httpd.server_address[1]
    filename = os.path.basename(file_path)
    url_to_load = f"http://127.0.0.1:{port}/{filename}"
    app.embed_browser(url_to_load)
    
    # --- Bucle de eventos manual ---
    log_viewer("Entrando en el bucle de eventos manual.")
    while True:
        cef.MessageLoopWork()
        try:
            if not app.winfo_exists(): break
            app.update()
        except tk.TclError:
            break
            
    cef.Shutdown()
    log_viewer("main_viewer - FIN")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        html_file_path = sys.argv[1]
        if os.path.exists(html_file_path):
            main_viewer(html_file_path)
        else:
            print(f"Error: El archivo no existe -> {html_file_path}")
    else:
        print("Error: No se proporcionó argumento de ruta de archivo.")