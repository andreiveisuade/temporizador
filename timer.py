#!/usr/bin/env python3
import customtkinter as ctk
import subprocess
import time
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import re

class TimerState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"

@dataclass
class TimerConfig:
    """Configuración del temporizador"""
    sound_file: str = '/System/Library/Sounds/Ping.aiff'
    volume: str = '4'
    repetitions: int = 3
    window_size: str = "400x300"
    font_size_large: int = 48
    font_size_normal: int = 14
    padding: int = 20

class ModernTimer:
    def __init__(self, config: Optional[TimerConfig] = None):
        self.config = config or TimerConfig()
        self.setup_window()
        self.state = TimerState.STOPPED
        self.remaining = 0
        self.dialog: Optional[ctk.CTkToplevel] = None
        self.setup_ui()
        self.show_time_input()

    def setup_window(self) -> None:
        """Configuración inicial de la ventana"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("Temporizador")
        self.root.geometry(self.config.window_size)
        
        self.root.bind('<Key>', self.handle_key)
    
    def setup_ui(self) -> None:
        """Configuración de la interfaz de usuario"""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(expand=True, fill="both", padx=self.config.padding, pady=self.config.padding)
        
        self.setup_time_display()
        self.setup_buttons()
    
    def setup_time_display(self) -> None:
        """Configura el display del tiempo"""
        self.time_label = ctk.CTkLabel(
            self.main_frame, 
            text="00:00:00",
            font=ctk.CTkFont(size=self.config.font_size_large, weight="bold")
        )
        self.time_label.pack(pady=30)
    
    def setup_buttons(self) -> None:
        """Configura los botones de control"""
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(pady=20)
        
        buttons_config = [
            ("Iniciar", self.start_timer, True),
            ("Pausar", self.pause_timer, False),
            ("Detener", self.stop_timer, False)
        ]
        
        self.buttons = {}
        for text, command, enabled in buttons_config:
            button = ctk.CTkButton(
                self.button_frame,
                text=text,
                command=command,
                width=100,
                font=ctk.CTkFont(size=self.config.font_size_normal),
                state="normal" if enabled else "disabled"
            )
            button.pack(side="left", padx=5)
            self.buttons[text.lower()] = button

    def validate_input(self, input_text: str) -> bool:
        """Valida que el input sea solo números y punto decimal"""
        return re.match(r'^\d+(\.\d+)?$', input_text)

    def handle_key(self, event) -> Optional[str]:
        """Maneja las teclas D y F para iniciar el temporizador"""
        key = event.char.lower()
        
        if key in ['d', 'f']:
            self.process_time_input(key)
            return "break"
        
        if event.char and not (event.char.isdigit() or event.char == '.'):
            return "break"
        
        return None

    def process_time_input(self, key: str) -> None:
        """Procesa el input de tiempo ingresado"""
        try:
            input_value = self.time_entry.get()
            if not input_value:
                return
            
            time_val = float(input_value)
            if time_val <= 0:
                raise ValueError
            
            self.remaining = int(time_val * (60 if key == 'd' else 1))
            self.dialog.destroy()
            self.start_countdown()
            
        except ValueError:
            self.show_error_message("Por favor ingrese un número válido mayor que 0")

    def show_error_message(self, message: str) -> None:
        """Muestra un mensaje de error temporal"""
        error_label = ctk.CTkLabel(
            self.dialog,
            text=message,
            text_color="red"
        )
        error_label.pack(pady=10)
        self.dialog.after(2000, error_label.destroy)

    def show_time_input(self) -> None:
        """Muestra el diálogo para ingresar el tiempo"""
        self.dialog = ctk.CTkToplevel(self.root)
        self.dialog.title("Ingresar Tiempo")
        self.dialog.geometry("300x200")
        self.dialog.transient(self.root)
        self.dialog.grab_set()
        
        self.setup_input_dialog()
    
    def setup_input_dialog(self) -> None:
        """Configura el diálogo de input"""
        input_frame = ctk.CTkFrame(self.dialog)
        input_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        instructions = ctk.CTkLabel(
            input_frame,
            text="Ingrese el tiempo y presione:\n'D' para minutos\n'F' para segundos",
            font=ctk.CTkFont(size=self.config.font_size_normal),
            justify="left"
        )
        instructions.pack(pady=(0, 20))
        
        self.time_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Ingrese el valor",
            width=200,
            font=ctk.CTkFont(size=self.config.font_size_normal)
        )
        self.time_entry.pack(pady=10)
        self.time_entry.bind('<Key>', self.handle_key)
        self.time_entry.focus()

    def format_time(self) -> str:
        """Formatea el tiempo restante en formato HH:MM:SS"""
        hours = self.remaining // 3600
        minutes = (self.remaining % 3600) // 60
        seconds = self.remaining % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def update_display(self) -> None:
        """Actualiza el display del tiempo"""
        self.time_label.configure(text=self.format_time())
    
    def start_countdown(self) -> None:
        """Inicia la cuenta regresiva"""
        self.state = TimerState.RUNNING
        self.buttons['pausar'].configure(state="normal")
        self.buttons['detener'].configure(state="normal")
        self.buttons['iniciar'].configure(state="disabled")
        self.update_timer()
    
    def update_timer(self) -> None:
        """Actualiza el temporizador"""
        if self.state == TimerState.RUNNING and self.remaining > 0:
            self.update_display()
            self.remaining -= 1
            self.root.after(1000, self.update_timer)
        elif self.state == TimerState.RUNNING and self.remaining <= 0:
            self.update_display()
            self.play_alarm()
            self.state = TimerState.STOPPED
            self.root.after(1000, self.root.destroy)
    
    def start_timer(self) -> None:
        self.show_time_input()
    
    def pause_timer(self) -> None:
        """Pausa o reanuda el temporizador"""
        if self.state in [TimerState.RUNNING, TimerState.PAUSED]:
            self.state = TimerState.PAUSED if self.state == TimerState.RUNNING else TimerState.RUNNING
            self.buttons['pausar'].configure(text="Reanudar" if self.state == TimerState.PAUSED else "Pausar")
            if self.state == TimerState.RUNNING:
                self.update_timer()
    
    def stop_timer(self) -> None:
        """Detiene el temporizador"""
        self.state = TimerState.STOPPED
        self.remaining = 0
        self.update_display()
        self.buttons['iniciar'].configure(state="normal")
        self.buttons['pausar'].configure(state="disabled")
        self.buttons['detener'].configure(state="disabled")
    
    def play_alarm(self) -> None:
        """Reproduce el sonido de alarma"""
        try:
            for _ in range(self.config.repetitions):
                subprocess.run([
                    'afplay',
                    '-v', self.config.volume,
                    self.config.sound_file
                ])
                time.sleep(0.1)
        except Exception as e:
            print(f"Error al reproducir el sonido: {e}")

def main():
    app = ModernTimer()
    app.root.mainloop()

if __name__ == "__main__":
    main()

