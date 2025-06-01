#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación de Escritorio - Calculadora de Turnos en Radiología
--------------------------------------------------------------
Versión 0.8.1
"""

import os
import sys
import subprocess
import webbrowser
import time
import signal
import platform
import threading
import tkinter as tk
from tkinter import messagebox, ttk

# Definir el directorio base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Icono en formato base64 para usar en la ventana
ICON = None  # Se definirá después con el icono real

class CalculadoraApp:
    def __init__(self, root):
        # Configurar la ventana principal
        self.root = root
        self.root.title("Calculadora de Turnos en Radiología v0.8.1")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Intentar establecer un icono si es posible
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap(os.path.join(BASE_DIR, "recursos", "icono.ico"))
            elif platform.system() == "Darwin":  # macOS
                # En macOS el icono se establece de otra manera
                pass
        except:
            pass
        
        # Variables de la aplicación
        self.proceso_streamlit = None
        self.url = "http://localhost:8501"
        self.streamlit_iniciado = False
        
        # Crear el marco principal
        self.frame_principal = ttk.Frame(self.root, padding="20")
        self.frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(
            self.frame_principal, 
            text="Calculadora de Turnos en Radiología", 
            font=("Helvetica", 16, "bold")
        ).pack(pady=10)
        
        ttk.Label(
            self.frame_principal, 
            text="Versión 0.8.1", 
            font=("Helvetica", 10)
        ).pack(pady=5)
        
        # Información
        info_texto = (
            "Esta aplicación le permite procesar datos radiológicos,\n"
            "calcular turnos, y generar reportes económicos.\n\n"
            "Al iniciar, la aplicación se abrirá en su navegador web."
        )
        ttk.Label(
            self.frame_principal, 
            text=info_texto,
            justify=tk.CENTER,
            font=("Helvetica", 11)
        ).pack(pady=20)
        
        # Marco para botones
        self.frame_botones = ttk.Frame(self.frame_principal)
        self.frame_botones.pack(fill=tk.X, pady=10)
        
        # Botón para iniciar
        self.boton_iniciar = ttk.Button(
            self.frame_botones,
            text="Iniciar Aplicación",
            command=self.iniciar_streamlit,
            width=20
        )
        self.boton_iniciar.pack(side=tk.LEFT, padx=10)
        
        # Botón para abrir navegador
        self.boton_navegador = ttk.Button(
            self.frame_botones,
            text="Abrir en Navegador",
            command=self.abrir_navegador,
            width=20,
            state=tk.DISABLED
        )
        self.boton_navegador.pack(side=tk.RIGHT, padx=10)
        
        # Barra de progreso
        self.progreso = ttk.Progressbar(
            self.frame_principal,
            orient=tk.HORIZONTAL,
            length=300,
            mode='indeterminate'
        )
        self.progreso.pack(pady=20, fill=tk.X, padx=50)
        
        # Estado
        self.estado_var = tk.StringVar(value="Listo para iniciar")
        self.estado_label = ttk.Label(
            self.frame_principal, 
            textvariable=self.estado_var,
            font=("Helvetica", 10),
            foreground="blue"
        )
        self.estado_label.pack(pady=10)
        
        # Configurar cierre de la ventana
        self.root.protocol("WM_DELETE_WINDOW", self.salir)
    
    def iniciar_streamlit(self):
        """Inicia el servidor Streamlit en segundo plano"""
        if self.streamlit_iniciado:
            messagebox.showinfo("Información", "La aplicación ya está en ejecución.")
            return
        
        self.estado_var.set("Iniciando aplicación...")
        self.progreso.start()
        self.boton_iniciar.configure(state=tk.DISABLED)
        
        # Iniciar en un hilo separado para no bloquear la interfaz
        threading.Thread(target=self._iniciar_streamlit_thread, daemon=True).start()
    
    def _iniciar_streamlit_thread(self):
        """Función que se ejecuta en un hilo separado para iniciar Streamlit"""
        try:
            # Cambiar al directorio base
            os.chdir(BASE_DIR)
            
            # Buscar python o python3
            python_cmd = "python"
            if platform.system() != "Windows" and os.system("which python3 > /dev/null 2>&1") == 0:
                python_cmd = "python3"
            
            # Construir el comando para Streamlit
            cmd = [python_cmd, "-m", "streamlit", "run", "ui/calculadora_streamlit.py"]
            
            # Iniciar el proceso
            if platform.system() == "Windows":
                self.proceso_streamlit = subprocess.Popen(
                    cmd, 
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                self.proceso_streamlit = subprocess.Popen(
                    cmd,
                    preexec_fn=os.setsid,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Esperar hasta que Streamlit esté listo
            streamlit_listo = False
            
            # Leer la salida hasta encontrar el mensaje de que está listo
            for i in range(10):  # Intentar durante 50 segundos
                if self.proceso_streamlit.poll() is not None:
                    # El proceso terminó
                    break
                    
                # Ver si hay salida en stdout
                output = self.proceso_streamlit.stdout.readline().decode('utf-8', errors='ignore')
                if "You can now view your Streamlit app in your browser" in output:
                    streamlit_listo = True
                    break
                    
                time.sleep(5)
            
            # Actualizar la interfaz en el hilo principal
            self.root.after(0, self._actualizar_ui, streamlit_listo)
        
        except Exception as e:
            # Actualizar la interfaz en el hilo principal
            self.root.after(0, self._mostrar_error, str(e))
    
    def _actualizar_ui(self, exito):
        """Actualiza la interfaz después de intentar iniciar Streamlit"""
        self.progreso.stop()
        self.boton_iniciar.configure(state=tk.NORMAL)
        
        if exito:
            self.streamlit_iniciado = True
            self.estado_var.set("Aplicación iniciada correctamente")
            self.boton_navegador.configure(state=tk.NORMAL)
            # No abrimos automáticamente para evitar la apertura doble
            # El usuario puede hacer clic en "Abrir en Navegador" si lo desea
        else:
            self.estado_var.set("Error al iniciar la aplicación")
            messagebox.showerror("Error", "No se pudo iniciar la aplicación Streamlit.")
    
    def _mostrar_error(self, mensaje):
        """Muestra un mensaje de error"""
        self.progreso.stop()
        self.boton_iniciar.configure(state=tk.NORMAL)
        self.estado_var.set("Error")
        messagebox.showerror("Error", f"Ocurrió un error: {mensaje}")
    
    def abrir_navegador(self):
        """Abre la aplicación en el navegador web"""
        if not self.streamlit_iniciado:
            messagebox.showinfo("Información", "La aplicación no ha sido iniciada aún.")
            return
        
        try:
            webbrowser.open_new(self.url)
            self.estado_var.set("Navegador abierto con la aplicación")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el navegador: {e}")
    
    def salir(self):
        """Función para cerrar la aplicación y detener Streamlit"""
        if messagebox.askyesno("Confirmar", "¿Está seguro que desea salir?\nSe cerrará la aplicación Streamlit."):
            if self.proceso_streamlit:
                # Detener el proceso de Streamlit
                try:
                    if platform.system() == "Windows":
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.proceso_streamlit.pid)])
                    else:  # Linux/Mac
                        os.killpg(os.getpgid(self.proceso_streamlit.pid), signal.SIGTERM)
                except:
                    pass
            
            # Cerrar la aplicación
            self.root.destroy()
            sys.exit(0)

def main():
    # Iniciar la aplicación
    root = tk.Tk()
    app = CalculadoraApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()