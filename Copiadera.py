import tkinter as tk
from tkinter import simpledialog, messagebox, Menu, ttk
import json
import os

CONFIG_FILE = "botones.json"

## ------------------------------
## Class: CopyApp
## Description: Aplicación principal para copiar texto al portapapeles mediante botones dinámicos.
## ------------------------------
class CopyApp:

    ## ------------------------------
    ## Function: __init__
    ## Description: Inicializa la aplicación y carga la configuración.
    ## param root: Ventana raíz de Tkinter.
    ## ------------------------------
    def __init__(self, root):
        self.root = root
        self.root.title("Quick Copy Panel")

        # Cargar configuración (antes de aplicar tamaño)
        self.buttons_data = self.load_buttons()

        # Aplicar último tamaño guardado (si existe), si no usar pequeño por defecto
        w = self.buttons_data.get("window_width", 420)
        h = self.buttons_data.get("window_height", 300)
        try:
            root.geometry(f"{w}x{h}")
        except Exception:
            pass

        # Usamos este atributo para comparar cambios y para debounce al guardar
        self._last_known_size = (w, h)
        self._resize_after_id = None
        # Debounce id for re-rendering when geometry changes
        self._render_after_id = None

        # Menú
        menubar = Menu(root)
        tools_menu = Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Options", command=self.open_options_window)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        root.config(menu=menubar)

        # Frame botones (expandible) - ocupa la mayor parte de la ventana
        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Footer: separador + controles + status (siempre visible en la parte inferior)
        self.footer_frame = tk.Frame(root)
        # Use place to pin the footer to the bottom so it remains visible even
        # when the window becomes very small.
        self.footer_frame.place(relx=0, rely=1.0, relwidth=1.0, anchor='sw')

        separator = ttk.Separator(self.footer_frame, orient="horizontal")
        separator.pack(fill="x", pady=(2,4))

        # Frame control (siempre visible) dentro del footer, arriba del status
        control_frame = tk.Frame(self.footer_frame)
        control_frame.pack(fill="x", padx=5, pady=(4,6))

        # Centrar los botones Add/Delete: creamos un contenedor centrado
        center_frame = tk.Frame(control_frame)
        center_frame.pack()

        # Misma anchura para ambos botones
        control_btn_width = 12
        btn_add = tk.Button(center_frame, text="Add", command=self.add_button, width=control_btn_width)
        btn_add.pack(side=tk.LEFT, padx=6)

        btn_delete = tk.Button(center_frame, text="Delete", command=self.delete_button, width=control_btn_width)
        btn_delete.pack(side=tk.LEFT, padx=6)

        # Barra de estado (debajo de los controles en el footer)
        self.status_label = tk.Label(self.footer_frame, text="", anchor="w", bg="#e0e0e0")
        self.status_label.pack(fill="x", padx=3, pady=(0,4))

        # Ajustar el padding inferior del área de botones para reservar espacio
        # para el footer y evitar que se solapen.
        try:
            self.root.update_idletasks()
            fh = self.footer_frame.winfo_reqheight()
            # Repack buttons_frame with bottom padding equal to footer height
            try:
                self.buttons_frame.pack_configure(padx=5, pady=(5, fh+5))
            except Exception:
                pass
        except Exception:
            pass

        # Asegurar que el footer siempre sea visible: fijar tamaño mínimo.
        self._ensure_footer_minsize()

        # Estado eliminar
        self.delete_mode = False
        self.original_button_colors = {}
        # Track previously configured grid sizes to reset them when matrix dims shrink
        self._configured_cols = 0
        self._configured_rows = 0

        # Bind para detectar cambios de tamaño y guardar (debounced)
        self.root.bind("<Configure>", self._on_configure)

        # Renderizar inmediatamente y también programar un rápido recheck.
        # Esto evita esperar mucho tiempo para que aparezcan los botones.
        try:
            self.render_buttons()
        except Exception:
            pass
        self.root.after(40, self._initial_layout_setup)

    ## ------------------------------
    ## Function: copy_text
    ## Description: Copia el texto proporcionado al portapapeles.
    ## param text: Texto a copiar.
    ## ------------------------------
    def copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        # Mostrar notificación en la barra de estado y limpiarla después de 3s
        try:
            # Mostrar solo una porción corta si el texto es muy largo
            display = text if len(text) <= 60 else text[:57] + "..."
            self.status_label.config(text=f"Copied: {display}")
            # Limpiar mensaje después de 3 segundos
            self.root.after(3000, lambda: self.status_label.config(text=""))
        except Exception:
            pass

    ## ------------------------------
    ## Function: add_button
    ## Description: Agrega un nuevo botón con el texto proporcionado.
    ## ------------------------------
    def add_button(self):
        text = simpledialog.askstring("New button", "What text would you like to copy?")
        if text:
            self.buttons_data["labels"].append(text)
            self.save_buttons()
            self.render_buttons()

    ## ------------------------------
    ## Function: delete_button
    ## Description: Elimina un botón basado en el texto proporcionado.
    ## ------------------------------
    def delete_button(self):
        if self.delete_mode:
            # ---- Apagar modo eliminar ----
            self.delete_mode = False
            self.status_label.config(text="")

            # Restaurar colores correctos SIN depender del evento <Leave>
            for btn, color in self.original_button_colors.items():
                btn.config(bg=color)

            return

        # Si no hay botones
        if not self.buttons_data["labels"]:
            messagebox.showinfo("Delete", "There aren't any buttons to delete.")
            return

        # ---- Activar modo borrar ----
        self.delete_mode = True
        self.status_label.config(text="Delete mode ON — click a button to delete it")

        # MUY IMPORTANTE:
        # Restaurar todos los colores ANTES de empezar de nuevo el modo eliminar
        for btn, color in self.original_button_colors.items():
            btn.config(bg=color)

    ## ------------------------------
    ## Function: render_buttons
    ## Description: Renderiza los botones en la interfaz según la configuración.
    ## ------------------------------
    def render_buttons(self):
        # Reforzar minsize del footer cada vez que renderizamos (evita que se oculte)
        try:
            self._ensure_footer_minsize()
        except Exception:
            pass

        for widget in self.buttons_frame.winfo_children():
            widget.destroy()

        # Reiniciar colores guardados (muy importante para evitar bug)
        self.original_button_colors = {}

        # Asegura que ningún botón queda rojo por un modo anterior
        self.delete_mode = False
        self.status_label.config(text="")

        columns = self.buttons_data["columns"]
        rows = self.buttons_data["rows"]

        # Si está activado el auto-resize, configuramos la grilla para que las
        # columnas y filas se expandan uniformemente. Si no, dejamos el tamaño
        # fijo según button_width/height.
        auto = self.buttons_data.get("auto_resize", True)

        # Resetear configuración previa en caso de que la nueva matriz sea
        # más pequeña (evita que queden columnas/filas con weight activo)
        try:
            for i in range(self._configured_cols):
                # limpiar columnas anteriores
                self.buttons_frame.grid_columnconfigure(i, weight=0, minsize=0, uniform=None)
            for j in range(self._configured_rows):
                # limpiar filas anteriores
                self.buttons_frame.grid_rowconfigure(j, weight=0, minsize=0, uniform=None)
        except Exception:
            pass

        # Configurar pesos de columna/fila de acuerdo a las dimensiones solicitadas
        for c in range(columns):
            # weight 1 para que se expandan si auto_resize está activo, 0 si no
            # Añadimos minsize y uniform para asegurar reparto equitativo
            self.buttons_frame.grid_columnconfigure(c, weight=(1 if auto else 0), minsize=(20 if auto else 0), uniform=("col" if auto else None))
        for r in range(rows):
            self.buttons_frame.grid_rowconfigure(r, weight=(1 if auto else 0), minsize=(20 if auto else 0), uniform=("row" if auto else None))

        # Guardar los valores configurados actualmente
        self._configured_cols = columns
        self._configured_rows = rows

        # Forzar cálculo de geometría antes de colocar botones para evitar que
        # las columnas aparezcan apiladas en una sola columna en algunos sistemas
        self.buttons_frame.update_idletasks()

        # Decidir si mostrar los botones de copiado según el espacio disponible
        avail_w = max(1, self.buttons_frame.winfo_width())
        avail_h = max(1, self.buttons_frame.winfo_height())
        MIN_CELL_W = 40  # px mínimos por celda (para aviso)
        MIN_CELL_H = 24
        need_w = columns * MIN_CELL_W
        need_h = rows * MIN_CELL_H

        # Si el espacio es limitado, mostramos una advertencia en la barra
        # pero NO ocultamos los botones: siempre se renderizan.
        if (avail_w < need_w) or (avail_h < need_h):
            self.status_label.config(text="Window small — buttons may be clipped")
        else:
            if self.status_label.cget("text").startswith("Window small"):
                self.status_label.config(text="")

        for index, text in enumerate(self.buttons_data["labels"]):
            r = index // columns
            c = index % columns
            if r >= rows:
                break

            # Crear botón. Si auto_resize está activado, no forzamos width/height
            # y usamos sticky="nsew" para que ocupe todo el espacio de la celda.
            if auto:
                btn = tk.Button(self.buttons_frame, text=text)
            else:
                btn = tk.Button(
                    self.buttons_frame,
                    text=text,
                    width=self.buttons_data["button_width"],
                    height=self.buttons_data["button_height"]
                )

            # Registrar color ORIGINAL del botón actual
            original_color = btn.cget("bg")
            self.original_button_colors[btn] = original_color

            def normal_click(t=text, b=btn):
                if not self.delete_mode:
                    self.copy_text(t)
                else:
                    resp = messagebox.askyesno("Delete",
                        f"do you want to delete:\n\n{t}?")
                    if resp:
                        self.buttons_data["labels"].remove(t)
                        self.save_buttons()
                        self.render_buttons()

            btn.config(command=normal_click)

            # Hover modo eliminar
            def on_enter(b=btn):
                if self.delete_mode:
                    b.config(bg="red")

            def on_leave(b=btn):
                if self.delete_mode:
                    b.config(bg=self.original_button_colors[b])

            btn.bind("<Enter>", lambda e, b=btn: on_enter(b))
            btn.bind("<Leave>", lambda e, b=btn: on_leave(b))

            if auto:
                btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            else:
                btn.grid(row=r, column=c, padx=5, pady=5)

        # Después de colocar botones, medir tamaño real de un botón para guardar en px
        try:
            self.buttons_frame.update_idletasks()
            any_btn = None
            for w in self.buttons_frame.winfo_children():
                if isinstance(w, tk.Button):
                    any_btn = w
                    break
            if any_btn:
                bw = any_btn.winfo_width()
                bh = any_btn.winfo_height()
                # Guardar tamaño en pixeles para referencia futura
                self.buttons_data["button_pixel_width"] = int(bw)
                self.buttons_data["button_pixel_height"] = int(bh)
                # Persistir (no es demasiado frecuente: render_buttons se llama en cambios)
                try:
                    self.save_buttons()
                except Exception:
                    pass
        except Exception:
            pass

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

        # Auto-resize checkbox
        auto_var = tk.BooleanVar(value=self.buttons_data.get("auto_resize", True))
        def toggle_auto(*args):
            if auto_var.get():
                width_entry.config(state="disabled")
                height_entry.config(state="disabled")
            else:
                width_entry.config(state="normal")
                height_entry.config(state="normal")

        # Inicialmente deshabilitar o habilitar entradas según el valor
        toggle_auto()

        auto_cb = tk.Checkbutton(win, text="Auto-resize buttons to fit window (show full matrix)", variable=auto_var, onvalue=True, offvalue=False)
        auto_cb.pack(pady=8)

        # Usar trace_add para actualizar el estado de las entradas cuando cambia el checkbox
        try:
            auto_var.trace_add("write", toggle_auto)
        except AttributeError:
            # fallback para versiones antiguas
            auto_var.trace("w", toggle_auto)

        def save_options():
            try:
                self.buttons_data["button_width"] = int(width_entry.get())
                self.buttons_data["button_height"] = int(height_entry.get())
                self.buttons_data["columns"] = int(columns_entry.get())
                self.buttons_data["rows"] = int(rows_entry.get())
                self.buttons_data["auto_resize"] = bool(auto_var.get())

                self.save_buttons()
                self.render_buttons()
                win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid values. Use integer numbers..")

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
        data.setdefault("auto_resize", True)
        # Defaults para tamaño de ventana
        data.setdefault("window_width", 420)
        data.setdefault("window_height", 300)

        return data

    def _ensure_footer_minsize(self):
        # Calcular altura requerida del footer y asegurarse de que la ventana
        # no pueda hacerse más pequeña que eso.
        try:
            # Asegurar que estén calculadas las geometrías
            self.root.update_idletasks()
            fh = self.footer_frame.winfo_reqheight()
            fw = self.footer_frame.winfo_reqwidth()
            min_w = max(200, fw)
            min_h = max(fh + 10, 60)
            try:
                self.root.minsize(min_w, min_h)
            except Exception:
                pass
        except Exception:
            pass

    ## ------------------------------
    ## Function: save_buttons
    ## Description: Guarda la configuración de botones en un archivo JSON.
    ## ------------------------------
    def save_buttons(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.buttons_data, f, indent=4, ensure_ascii=False)

    ## ------------------------------
    ## Function: exit_delete_mode
    ## Description: Sale del modo eliminar si está activo.
    ## ------------------------------
    def exit_delete_mode(self):
        if self.delete_mode:
            self.delete_mode = False
            self.status_label.config(text="")
    
            # Restaurar colores
            for btn, color in self.original_button_colors.items():
                btn.config(bg=color)

    ## ------------------------------
    ## Function: _on_configure
    ## Description: Maneja el evento de cambio de tamaño de la ventana.
    ## Guarda el tamaño en la configuración (debounced).
    ## ------------------------------
    def _on_configure(self, event):
        # Solo manejar eventos del root (evita hijos) y cuando la ventana esté normal
        try:
            if event.widget is not self.root:
                return
        except Exception:
            return
        
        # En cada configure reforzamos la minsize del footer para evitar que se
        # oculte accidentalmente durante redimensiones muy pequeñas.
        try:
            self._ensure_footer_minsize()
        except Exception:
            pass

        # Tomar tamaño actual
        w = event.width
        h = event.height

        # Ignorar cambios que no modifican tamaño
        if (w, h) == getattr(self, "_last_known_size", (None, None)):
            return

        # Actualizar último tamaño conocido
        self._last_known_size = (w, h)

        # Debounce la escritura al archivo para evitar demasiadas operaciones
        if self._resize_after_id:
            try:
                self.root.after_cancel(self._resize_after_id)
            except Exception:
                pass

        self._resize_after_id = self.root.after(700, self._save_window_size)
        # También programar un render para actualizar visibilidad de botones
        try:
            self._schedule_render()
        except Exception:
            pass

    ## ------------------------------
    ## Function: _save_window_size
    ## Description: Guarda el tamaño actual de la ventana en la configuración y persiste en JSON.
    ## ------------------------------
    def _save_window_size(self):
        # Guardar tamaño actual en la configuración y persistir en JSON
        try:
            w, h = self._last_known_size
            self.buttons_data["window_width"] = int(w)
            self.buttons_data["window_height"] = int(h)
            self.save_buttons()
        except Exception:
            pass

    def _initial_layout_setup(self):
        # Called after startup to ensure sizes are calculated and then render
        try:
            self._ensure_footer_minsize()
        except Exception:
            pass
        try:
            self.render_buttons()
        except Exception:
            pass

    def _schedule_render(self, delay=250):
        # Debounce re-render calls when window resizes
        try:
            if self._render_after_id:
                self.root.after_cancel(self._render_after_id)
        except Exception:
            pass
        self._render_after_id = self.root.after(delay, lambda: self.render_buttons())


## ------------------------------
## Function: main
## Description: Punto de entrada principal de la aplicación.
## ------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = CopyApp(root)
    root.mainloop()
