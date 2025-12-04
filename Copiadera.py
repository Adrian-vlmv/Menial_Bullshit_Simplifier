import tkinter as tk
from tkinter import simpledialog, messagebox, Menu, ttk
import json
import os

CONFIG_FILE = "botones.json"

# ------------------------------
# Class: CopyApp
# Description: Aplicación principal para copiar texto al portapapeles mediante botones dinámicos.
# ------------------------------
class CopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Copiar al portapapeles")

        # Cargar configuración
        self.buttons_data = self.load_buttons()

        # =======================
        #  Menú superior
        # =======================
        menubar = Menu(root)
        tools_menu = Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Options", command=self.open_options_window)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        root.config(menu=menubar)

        # =======================
        #  Frame para botones dinámicos
        # =======================
        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(pady=10)

        # =======================
        #  Separador visual
        # =======================
        separator = ttk.Separator(root, orient="horizontal")
        separator.pack(fill="x", pady=8)

        # =======================
        #  Frame de control (Add / Delete)
        # =======================
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10)

        btn_add = tk.Button(control_frame, text="Agregar botón", command=self.add_button)
        btn_add.pack(side=tk.LEFT, padx=5)

        btn_delete = tk.Button(control_frame, text="Eliminar botón", command=self.delete_button)
        btn_delete.pack(side=tk.LEFT, padx=5)

        # Dibujar los botones
        self.render_buttons()

    ## ------------------------------
    ## Function: copy_text
    ## Description: Copia el texto dado al portapapeles.
    ## param text: Texto a copiar
    ## ------------------------------
    def copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        print(f"Texto copiado: {text}")


    ## ------------------------------
    ## Function: add_button
    ## Description: Agrega un nuevo botón con el texto proporcionado.
    ## ------------------------------
    def add_button(self):
        text = simpledialog.askstring("Nuevo botón", "¿Qué texto quieres que copie este botón?")
        if text:
            self.buttons_data["labels"].append(text)
            self.save_buttons()
            self.render_buttons()


    ## ------------------------------
    ## Function: delete_button
    ## Description: Elimina un botón basado en el texto proporcionado.
    ## ------------------------------
    def delete_button(self):
        labels = self.buttons_data["labels"]
        if not labels:
            messagebox.showinfo("Eliminar", "No hay botones para eliminar.")
            return

        text = simpledialog.askstring("Eliminar botón", "Escribe el texto exacto del botón a eliminar:")
        if text in labels:
            labels.remove(text)
            self.save_buttons()
            self.render_buttons()
        else:
            messagebox.showerror("Error", f"No existe un botón con el texto: {text}")


    ## ------------------------------
    ## Function: render_buttons
    ## Description: Renderiza los botones en la interfaz según la configuración actual.
    ## ------------------------------
    def render_buttons(self):
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()

        columns = self.buttons_data["columns"]
        rows = self.buttons_data["rows"]

        for index, text in enumerate(self.buttons_data["labels"]):
            r = index // columns
            c = index % columns
            if r >= rows:
                break  # No dibujar fuera de la matriz permitida

            btn = tk.Button(
                self.buttons_frame,
                text=text,
                width=self.buttons_data["button_width"],
                height=self.buttons_data["button_height"],
                command=lambda t=text: self.copy_text(t)
            )
            btn.grid(row=r, column=c, padx=5, pady=5)

    ## ------------------------------
    ## Function: open_options_window
    ## Description: Abre una ventana para configurar las opciones de los botones.
    ## ------------------------------
    def open_options_window(self):
        win = tk.Toplevel(self.root)
        win.title("Options")
        win.geometry("300x300")

        # Button width
        tk.Label(win, text="Button width:").pack(pady=5)
        width_entry = tk.Entry(win)
        width_entry.pack()
        width_entry.insert(0, str(self.buttons_data["button_width"]))

        # Button height
        tk.Label(win, text="Button height:").pack(pady=5)
        height_entry = tk.Entry(win)
        height_entry.pack()
        height_entry.insert(0, str(self.buttons_data["button_height"]))

        # Number of columns (matrix X)
        tk.Label(win, text="Matrix columns (X):").pack(pady=5)
        columns_entry = tk.Entry(win)
        columns_entry.pack()
        columns_entry.insert(0, str(self.buttons_data["columns"]))

        # Number of rows (matrix Y)
        tk.Label(win, text="Matrix rows (Y):").pack(pady=5)
        rows_entry = tk.Entry(win)
        rows_entry.pack()
        rows_entry.insert(0, str(self.buttons_data["rows"]))

        def save_options():
            try:
                self.buttons_data["button_width"] = int(width_entry.get())
                self.buttons_data["button_height"] = int(height_entry.get())
                self.buttons_data["columns"] = int(columns_entry.get())
                self.buttons_data["rows"] = int(rows_entry.get())

                self.save_buttons()
                self.render_buttons()
                win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Valores inválidos. Usa números enteros.")

        tk.Button(win, text="Save", command=save_options).pack(pady=20)


    ## ------------------------------
    ## Function: load_buttons
    ## Description: Carga la configuración de botones desde un archivo JSON.
    ## ------------------------------
    def load_buttons(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        # Set defaults
        data.setdefault("labels", [])
        data.setdefault("button_width", 20)
        data.setdefault("button_height", 2)
        data.setdefault("columns", 5)
        data.setdefault("rows", 5)

        return data


    ## ------------------------------
    ## Function: save_buttons
    ## Description: Guarda la configuración de botones en un archivo JSON.
    ## ------------------------------
    def save_buttons(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.buttons_data, f, indent=4, ensure_ascii=False)


## ------------------------------
## Function: main
## Description: Punto de entrada principal de la aplicación.
## ------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = CopyApp(root)
    root.mainloop()
