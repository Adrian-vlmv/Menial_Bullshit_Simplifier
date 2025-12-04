import tkinter as tk
import subprocess   # Para ejecutar otros scripts

class CodeReviewApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Review App")

        # Crear barra de menú
        menubar = tk.Menu(root)

        # Menú "Archivos"
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Abrir copiadera.py", command=self.open_copiadera)
        file_menu.add_command(label="Abrir codeStandard.py", command=self.open_codestandard)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=root.quit)

        menubar.add_cascade(label="Archivos", menu=file_menu)

        # Asignar la barra de menú a la ventana
        root.config(menu=menubar)

    def open_copiadera(self):
        # Ejecuta copiadera.py en un proceso separado
        subprocess.Popen(["python", "copiadera.py"])

    def open_codestandard(self):
        # Ejecuta codeStandard.py en un proceso separado
        subprocess.Popen(["python", "codeStandard.py"])


# =========================================================================
# === Bloque de Ejecución Principal ===
# =========================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = CodeReviewApp(root)
    root.mainloop()
