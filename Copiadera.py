import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import os

CONFIG_FILE = "botones.json"

class CopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Copiar al portapapeles")

        # Frame para los botones dinámicos
        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(pady=10)

        # Botones de control
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        btn_add = tk.Button(control_frame, text="Agregar otro botón", command=self.add_button)
        btn_add.pack(side=tk.LEFT, padx=5)

        btn_delete = tk.Button(control_frame, text="Eliminar botón", command=self.delete_button)
        btn_delete.pack(side=tk.LEFT, padx=5)

        # Cargar botones desde JSON
        self.buttons_data = self.load_buttons()
        self.render_buttons()

    def copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        print(f"Texto copiado: {text}")

    def add_button(self):
        text = simpledialog.askstring("Nuevo botón", "¿Qué texto quieres que copie este botón?")
        if text:
            self.buttons_data.append(text)
            self.save_buttons()
            self.render_buttons()

    def delete_button(self):
        if not self.buttons_data:
            messagebox.showinfo("Eliminar", "No hay botones para eliminar.")
            return

        # Preguntar cuál eliminar
        text = simpledialog.askstring("Eliminar botón", "Escribe el texto exacto del botón a eliminar:")
        if text in self.buttons_data:
            self.buttons_data.remove(text)
            self.save_buttons()
            self.render_buttons()
        else:
            messagebox.showerror("Error", f"No existe un botón con el texto: {text}")

    def render_buttons(self):
        # Limpiar botones anteriores
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()

        # Crear botones nuevos
        for text in self.buttons_data:
            btn = tk.Button(self.buttons_frame, text=text, command=lambda t=text: self.copy_text(t))
            btn.pack(pady=5)

    def load_buttons(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_buttons(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.buttons_data, f, indent=4, ensure_ascii=False)


# =========================================================================
# === Bloque de Ejecución Principal ===
# =========================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = CopyApp(root)
    root.mainloop()
