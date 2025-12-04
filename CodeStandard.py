import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from collections import OrderedDict 
import os
import re
# ASUMIMOS que Monitoring.py sigue proveyendo estas funciones
from Monitoring import monitor_methods, _extract_brace_body, _get_header_comment


class CodeReviewApp:
    """
    Clase principal que gestiona el estado de la aplicación, la interfaz de usuario
    y la lógica de análisis de código de forma modular.
    
    Version V26: Implementa una corrección robusta para la detección de parámetros
    documentados con sintaxis Doxygen (ej. \param[in] tag).
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Revisor y Monitor de Código (Standards V26 - Consistencia de Parámetros)")
        self.root.geometry("1400x750")

        self.loaded_files = OrderedDict() 

        self.var_120_chars = tk.BooleanVar(value=True)
        self.var_check_todos = tk.BooleanVar(value=True) 
        self.var_unused_params = tk.BooleanVar(value=True) 
        
        # 🌟 Parámetros Documentados
        self.var_header_params = tk.BooleanVar(value=True) 
        
        self.var_monitor_methods = tk.BooleanVar(value=True) 
        
        self.setup_ui()

    def setup_ui(self):
        """Configura el layout de la interfaz de Tkinter (Panel Izquierdo y Derecho)."""
        # ... (La configuración de UI permanece igual, omitida por brevedad) ...
        
        frame_principal = tk.Frame(self.root, padx=15, pady=15)
        frame_principal.pack(expand=True, fill='both')
        frame_principal.grid_columnconfigure(0, weight=1)
        frame_principal.grid_columnconfigure(1, weight=4) 
        frame_principal.grid_rowconfigure(3, weight=1) 

        # --- Panel Izquierdo: Gestión de Archivos (Columna 0) ---
        frame_archivos = tk.Frame(frame_principal, padx=10, pady=5, relief=tk.GROOVE, bd=1)
        frame_archivos.grid(row=0, column=0, rowspan=4, sticky='nsew', padx=(0, 10))
        frame_archivos.grid_rowconfigure(2, weight=1)

        tk.Label(frame_archivos, text="Archivos Cargados", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 5))

        self.boton_cargar = tk.Button(
            frame_archivos, text="➕ Cargar Archivos", font=('Arial', 10, 'bold'),
            bg="#4CAF50", fg="white", 
            command=self.load_files_to_list
        )
        self.boton_cargar.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)

        self.listbox_archivos = tk.Listbox(
            frame_archivos, selectmode=tk.EXTENDED, font=('Consolas', 10),
            height=25, relief=tk.SUNKEN
        )
        self.listbox_archivos.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=5)

        self.boton_eliminar = tk.Button(
            frame_archivos, text="🗑️ Eliminar Seleccionados", font=('Arial', 10),
            bg="#f44336", fg="white",
            command=self.remove_selected_files
        )
        self.boton_eliminar.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)

        # --- Panel Derecho: Controles y Resultados (Columna 1) ---

        # Fila 0: Controles
        frame_controles = tk.Frame(frame_principal, bd=2, relief=tk.RIDGE, padx=10, pady=10)
        frame_controles.grid(row=0, column=1, sticky='ew', pady=(0, 10))
        
        tk.Label(frame_controles, text="Estándares de Revisión:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 5))

        tk.Checkbutton(
            frame_controles, text="Límite 120 Car.", variable=self.var_120_chars,
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=5)

        tk.Checkbutton(
            frame_controles, text="'TODOs'", variable=self.var_check_todos,
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Checkbutton(
            frame_controles, text="Params No Usados", variable=self.var_unused_params,
            font=('Arial', 10, 'bold'), fg="#1e88e5" 
        ).pack(side=tk.LEFT, padx=5)
        
        # 🌟 NUEVO CHECKBOX
        tk.Checkbutton(
            frame_controles, text="Params Documentados (Header)", variable=self.var_header_params,
            font=('Arial', 10, 'bold'), fg="#8B4513"
        ).pack(side=tk.LEFT, padx=5)


        # Separador para Monitoreo
        tk.Label(frame_controles, text="|", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        
        # Checkbox para Monitoreo
        tk.Checkbutton(
            frame_controles, text="MONITOREO: Extracción de Métodos", variable=self.var_monitor_methods,
            font=('Arial', 10, 'bold'), fg="#008080"
        ).pack(side=tk.LEFT, padx=5)
        
        # Botón de acción
        self.boton_verificar = tk.Button(
            frame_principal, 
            text="Ejecutar Revisión y Monitoreo Completos", 
            font=('Arial', 12, 'bold'), 
            bg="#3f51b5", fg="white", 
            activebackground="#303f9f",
            activeforeground="white",
            command=self.analyze_all_files
        )
        self.boton_verificar.grid(row=1, column=1, sticky='ew', pady=(5, 5))
        
        # Fila 2: Títulos de las Áreas de Texto
        frame_titulos = tk.Frame(frame_principal)
        frame_titulos.grid(row=2, column=1, sticky='ew')
        
        # Título Revisión
        tk.Label(frame_titulos, text="RESULTADOS DE REVISIÓN (Violaciones)", font=('Arial', 11, 'bold'), fg="#cc0000").pack(side=tk.LEFT, expand=True, fill='x')
        # Título Monitoreo
        tk.Label(frame_titulos, text="RESULTADOS DE MONITOREO (Extracción de Datos)", font=('Arial', 11, 'bold'), fg="#008080").pack(side=tk.RIGHT, expand=True, fill='x')

        # Fila 3: Áreas de Texto (Side-by-Side)
        frame_resultados_monitoreo = tk.Frame(frame_principal)
        frame_resultados_monitoreo.grid(row=3, column=1, sticky='nsew')
        frame_resultados_monitoreo.grid_columnconfigure(0, weight=1)
        frame_resultados_monitoreo.grid_columnconfigure(1, weight=1)
        frame_resultados_monitoreo.grid_rowconfigure(0, weight=1)


        # Área de Resultados de Revisión (Columna 0 del sub-frame)
        self.area_resultado = scrolledtext.ScrolledText(
            frame_resultados_monitoreo, wrap=tk.WORD, font=('Consolas', 10),
            bg="#fffafa", relief=tk.SUNKEN 
        )
        self.area_resultado.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        self.area_resultado.insert(tk.END, "Selecciona los archivos y presiona 'Ejecutar Revisión Completa'.\n")
        self.area_resultado.config(state=tk.DISABLED)
        
        # Área de Resultados de Monitoreo (Columna 1 del sub-frame)
        self.area_monitoreo = scrolledtext.ScrolledText(
            frame_resultados_monitoreo, wrap=tk.WORD, font=('Consolas', 10),
            bg="#f0fff0", relief=tk.SUNKEN 
        )
        self.area_monitoreo.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        self.area_monitoreo.insert(tk.END, "Aquí se mostrarán los datos de monitoreo (e.g., métodos extraídos).\n")
        self.area_monitoreo.config(state=tk.DISABLED)
        
        self.area_resultado.tag_config("warning", foreground="red", font=('Consolas', 10, 'bold'))
        self.area_resultado.tag_config("ok", foreground="green", font=('Consolas', 10))

    # =========================================================================
    # === Lógica de Gestión de Archivos ===
    # =========================================================================

    def load_files_to_list(self):
        """Permite al usuario seleccionar múltiples archivos y los carga."""
        filepaths = filedialog.askopenfilenames(
            title="Seleccionar múltiples archivos para revisión",
            filetypes=(
                ("Archivos de Código (Py/JS/C++)", "*.h *.cpp *.hpp *.cc *.c *.py *.js *.ts *.jsx *.tsx"), 
                ("Todos los archivos", "*.*")
            )
        )
        if not filepaths: return

        count_new = 0
        for filepath in filepaths:
            try:
                if filepath in self.loaded_files: continue
                
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                self.loaded_files[filepath] = content
                self.listbox_archivos.insert(tk.END, os.path.basename(filepath))
                count_new += 1

            except Exception as e:
                messagebox.showerror("Error de Carga", f"No se pudo leer el archivo '{os.path.basename(filepath)}': {e}")
    
    def remove_selected_files(self):
        """Elimina los archivos seleccionados del Listbox y de la estructura global."""
        selected_indices = self.listbox_archivos.curselection()
        if not selected_indices:
            messagebox.showwarning("Advertencia", "Selecciona al menos un archivo para eliminar.")
            return

        files_to_remove_names = [self.listbox_archivos.get(i) for i in selected_indices]
        
        for i in reversed(selected_indices):
            self.listbox_archivos.delete(i)
            
        keys_to_delete = []
        for filepath in self.loaded_files.keys():
            if os.path.basename(filepath) in files_to_remove_names:
                keys_to_delete.append(filepath)

        for key in keys_to_delete:
            del self.loaded_files[key]
            
        messagebox.showinfo("Archivos Eliminados", f"Se eliminaron {len(keys_to_delete)} archivo(s) de la lista.")

    # =========================================================================
    # === Lógica Central de Detección (Funciones de utilidad) ===
    # =========================================================================

    def _format_header_violation_message(self, func_name: str, line_num: int, param_list: list, error_type: str) -> str:
        """
        Formatea el mensaje de error para violaciones en la documentación del header (MISSING/EXTRA).
        """
        num_params = len(param_list)
        quoted_params = [f"'{p}'" for p in param_list]
        
        if num_params == 1:
            param_str = quoted_params[0]
            param_word = "parameter"
            verb = "is"
        else:
            param_word = "parameters"
            verb = "are"
            if num_params == 2:
                param_str = f"{quoted_params[0]} and {quoted_params[1]}"
            else:
                param_str = ", ".join(quoted_params[:-1])
                param_str += f", and {quoted_params[-1]}"

        if error_type == 'MISSING':
            header = f"The {param_word} {param_str} {verb} not mentioned in the function header comment."
        elif error_type == 'EXTRA':
            header = f"The {param_word} {param_str} {verb} documented in the header but {verb} not found in the function signature."
        else:
            header = f"Header documentation issue with {param_word} {param_str}."

        message = f"\n    Line {line_num} (Function '{func_name}'): {header}"
        return message

    def _format_unused_params_message_en(self, func_name: str, line_num: int, unused_list: list) -> str:
        """
        Formatea el mensaje de error para parámetros no utilizados (en inglés).
        """
        num_unused = len(unused_list)
        quoted_params = [f"'{p}'" for p in unused_list]
        
        if num_unused == 1:
            param_str = quoted_params[0]
            verb = "is"
            word = "parameter"
            header = f"The {word} {param_str} {verb} defined but not used in the function body."
        else:
            verb = "are"
            word = "parameters"
            if num_unused == 2:
                param_str = f"{quoted_params[0]} and {quoted_params[1]}"
            else:
                param_str = ", ".join(quoted_params[:-1])
                param_str += f", and {quoted_params[-1]}"
            header = f"The {word} {param_str} {verb} defined but not used in the function body."
            
        message = f"\n    Line {line_num} (Function '{func_name}'): {header}"
        return message
    
    def _get_clean_param_name(self, param_str):
        """
        Limpia una cadena de parámetro para aislar el nombre de la variable.
        """
        param_str = param_str.strip()
        
        if param_str.lower() == 'void' or not param_str:
            return None
    
        param_str = param_str.split('=')[0].strip()
        
        if param_str.startswith('{') or param_str.startswith('['):
            return None 
    
        parts = param_str.split()
        if not parts: return None
    
        potential_name_token = parts[-1]
        
        match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)(?=[\[*&])', potential_name_token)
        
        clean_name = potential_name_token
        
        if match:
            clean_name = match.group(1)
        else:
            clean_name = re.sub(r'[^\w]', '', potential_name_token).strip()
    
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', clean_name):
            return clean_name
            
        return None

    def _clean_body_for_param_search(self, body_content: str) -> str:
        """
        Limpia el cuerpo de la función para la búsqueda de parámetros de forma ULTRA-AGRESIVA.
        """
        # === FASE 1: Limpieza de COMENTARIOS (Alta Precedencia) =============
        body_content = re.sub(r'(//|#).*$', ' ', body_content, flags=re.MULTILINE)
        body_content = re.sub(r'/\*[\s\S]*?\*/', ' ', body_content, flags=re.DOTALL)

        # === FASE 2: Limpieza de STRINGS (Precedencia Media) =================
        body_content = re.sub(r'"([^"\\]|\\.)*"', ' ', body_content, flags=re.DOTALL)
        body_content = re.sub(r"'([^'\\]|\\.)*'", ' ', body_content, flags=re.DOTALL)

        # === FASE 3: Normalización y Aislamiento de Tokens ===================
        # Eliminar U+00A0
        body_content = body_content.replace('\u00A0', ' ')
        body_content = re.sub(r'\s', ' ', body_content) 

        body_content = re.sub(r'::', ' ', body_content) 
        body_content = re.sub(r'->', ' ', body_content) 
        body_content = re.sub(r'\.', ' ', body_content) 

        body_content = re.sub(r'[^\w]', ' ', body_content)

        body_content = re.sub(r' +', ' ', body_content).strip() 
        
        return body_content

    # =========================================================================
    # === Lógica de Estándares de Código (Módulos de Revisión) ===
    # =========================================================================

    def check_line_length(self, code, filename):
        """Verifica las líneas que exceden el límite de 120 caracteres."""
        LINE_LIMIT = 120
        lines = code.split('\n')
        violations = []
        for num_line, line in enumerate(lines, 1):
            if len(line) > LINE_LIMIT:
                violations.append(f"Line {num_line}: {len(line)} characters (Limit: {LINE_LIMIT})")
        return "Límite de 120 Caracteres", violations, LINE_LIMIT

    def check_for_todos(self, code, filename):
        """Verifica la existencia de comentarios 'TODO', 'FIXME', o 'HACK'."""
        keywords = ["TODO", "FIXME", "HACK"]
        lines = code.split('\n')
        violations = []
        
        pattern = re.compile(r'\b(?:' + '|'.join(keywords) + r')\b', re.IGNORECASE)
        
        for num_line, line in enumerate(lines, 1):
            if pattern.search(line):
                violations.append(f"Línea {num_line}: Se encontró un marcador de tarea (TODO/FIXME/HACK).")
        return "Comentarios Pendientes (TODOs)", violations, 0 

    def check_unused_parameters(self, code, filename):
        """
        Revisa si los parámetros definidos en funciones o métodos son utilizados
        dentro del cuerpo de la función, incluyendo la lista de inicialización.
        """
        
        # Palabras clave de control de flujo C/C++ a excluir
        EXCLUDED_KEYWORDS = r'(?:if|for|while|switch|catch|do|try|new|delete|sizeof|return|NULL|class|struct|enum|using)\b'

        # PATRÓN V15: Captura la firma y la lista de inicialización.
        FUNCTION_SIG_PATTERN = re.compile(
            r'(?:^|\n)\s*'
            r'(?:[a-zA-Z_][a-zA-Z0-9_:\s*&<>]+\s+)?' 
            r'(?!' + EXCLUDED_KEYWORDS + r')'
            r'([a-zA-Z_][a-zA-Z0-9_:]*)'  # Group 1 (Function/Method Name)
            r'\s*\((.*?)\)'              # Group 2 (Parameters)
            r'(?:\s*const)?' 
            r'(\s*:[\s\S]*?)?'           # Group 3: Lista de inicialización (Constructor), opcional
            r'\s*\{'                     # Coincide con la llave de apertura
            , re.DOTALL 
        )
        
        violations = []
        
        if filename.lower().endswith(('.html', '.css', '.md')):
            return "Parámetros No Utilizados", violations, 0

        current_pos = 0 
        
        while True:
            match = FUNCTION_SIG_PATTERN.search(code, current_pos)
            if not match:
                break 

            func_name = match.group(1).split('::')[-1] 
            param_string = match.group(2) 
            init_list = match.group(3) 
            start_brace_index = match.end() - 1 
            
            func_body, body_end_index = _extract_brace_body(code, start_brace_index)
            
            if func_body is None or body_end_index == -1:
                current_pos = start_brace_index + 1
                continue 

            start_line_index = code[:match.start()].count('\n') + 1

            # 1. Extraer nombres de parámetros limpios
            raw_params = [p.strip() for p in re.split(r',\s*', param_string) if p.strip()]
            parameters = []
            for p in raw_params:
                param_name = self._get_clean_param_name(p)
                if param_name and param_name not in ('self', 'cls', '_', '__'): 
                    parameters.append(param_name)

            if parameters:
                used_in_init_list = set()
                
                # 2. Verificar uso en la Lista de Inicialización 
                if init_list:
                    for param in parameters:
                        usage_pattern = re.compile(r'\b' + re.escape(param) + r'\b')
                        if usage_pattern.search(init_list):
                            used_in_init_list.add(param)
                            
                params_to_check_in_body = [p for p in parameters if p not in used_in_init_list]

                unused_params_in_func = []
                
                if params_to_check_in_body:
                    body_to_search = self._clean_body_for_param_search(func_body)

                    # 5. Verificar el uso en el cuerpo limpio 
                    for param in params_to_check_in_body:
                        usage_pattern = re.compile(r'\b' + re.escape(param) + r'\b')
                        
                        if not usage_pattern.search(body_to_search):
                            unused_params_in_func.append(param)
                
                # 6. Generar el mensaje de violación agrupado en inglés
                if unused_params_in_func:
                    violation_message = self._format_unused_params_message_en(
                        func_name, start_line_index, unused_params_in_func
                    )
                    violations.append(violation_message)

            current_pos = body_end_index + 1
        
        return "Parámetros No Utilizados", violations, 0

    # 🌟 FUNCIÓN DE REVISIÓN CORREGIDA (V26)
    def check_header_params_documentation(self, code, filename):
        """
        Verifica la consistencia entre los parámetros de la firma de la función
        y los parámetros documentados en el comentario de cabecera.
        
        Corrige la detección de \param[in] name (ej. 'tag').
        """
        
        EXCLUDED_KEYWORDS = r'(?:if|for|while|switch|catch|do|try|new|delete|sizeof|return|NULL|class|struct|enum|using)\b'

        FUNCTION_SIG_PATTERN = re.compile(
            r'(?:^|\n)\s*'
            r'(?:[a-zA-Z_][a-zA-Z0-9_:\s*&<>]+\s+)?' 
            r'(?!' + EXCLUDED_KEYWORDS + r')'
            r'([a-zA-Z_][a-zA-Z0-9_:]*)'  # Group 1 (Function/Method Name)
            r'\s*\((.*?)\)'              # Group 2 (Parameters)
            r'(?:\s*const)?'
            r'(\s*:[\s\S]*?)?'           # Group 3: Lista de inicialización
            r'\s*([;\{])'                # Group 4: Llave de apertura '{' o punto y coma ';' (declaración)
            , re.DOTALL 
        )
        
        violations = []
        
        if not filename.lower().endswith(('.cpp', '.c', '.h', '.hpp', '.py', '.js', '.ts')):
            return "Documented Parameters (Header)", violations, 0

        current_pos = 0 
        
        while True:
            match = FUNCTION_SIG_PATTERN.search(code, current_pos)
            if not match:
                break 

            func_name_full = match.group(1) 
            param_string = match.group(2) 
            end_char = match.group(4) 
            start_index = match.start()
            start_line_index = code[:start_index].count('\n') + 1

            # --- A. PARÁMETROS EN LA FIRMA (Signature Parameters) ---
            raw_params = [p.strip() for p in re.split(r',\s*', param_string) if p.strip()]
            sig_params = set() 
            for p in raw_params:
                param_name = self._get_clean_param_name(p)
                if param_name and param_name not in ('self', 'cls', '_', '__'): 
                    sig_params.add(param_name)

            # --- B. PARÁMETROS EN LA DOCUMENTACIÓN (Header Parameters) ---
            header_comment = _get_header_comment(code, start_index) 
            doc_params = set() 
            
            if header_comment:
                clean_comment = re.sub(r'\s+', ' ', header_comment)
                
                # 🎯 CORRECCIÓN ROBUSTA V26: Maneja todos los casos Doxygen.
                # (\param o @param) seguido de [optional modifiers] luego (el nombre)
                param_tag_matches = re.findall(
                    r'(?:\\param|@param)\s+'
                    r'(?:\[[^\]]+\]\s*)?' # [in], [out], [in, out] o cualquier cosa entre corchetes, opcional
                    r'([a-zA-Z_][a-zA-Z0-9_]*)\b', 
                    clean_comment
                )
                
                for name in param_tag_matches:
                    doc_params.add(name)

            # --- C. COMPARACIÓN DE CONJUNTOS Y GENERACIÓN DE VIOLACIONES ---

            # 1. Parámetros FALTANTES (En la firma, pero NO en la documentación)
            missing_params = sorted(list(sig_params - doc_params))

            if missing_params:
                violation_message = self._format_header_violation_message(
                    func_name_full, start_line_index, missing_params, 'MISSING'
                )
                violations.append(violation_message)

            # 2. Parámetros EXTRA (En la documentación, pero NO en la firma)
            extra_params = sorted(list(doc_params - sig_params))
            
            if extra_params:
                violation_message = self._format_header_violation_message(
                    func_name_full, start_line_index, extra_params, 'EXTRA'
                )
                violations.append(violation_message)
            
            # 3. Mover la posición de búsqueda
            if end_char == ';':
                current_pos = match.end()
            else:
                start_brace_index = match.end() - 1 
                func_body, body_end_index = _extract_brace_body(code, start_brace_index)
                
                if body_end_index == -1:
                    current_pos = match.end() # Fallback
                else:
                    current_pos = body_end_index + 1
        
        return "Documented Parameters (Header)", violations, 0
    # =========================================================================
    # === Lógica de Monitoreo ===
    # =========================================================================

    # ... (Lógica de Monitoreo no se toca) ...
    def analyze_all_files(self):
        """Ejecuta todos los checks seleccionados en todos los archivos cargados (Revisión y Monitoreo)."""
        
        self.area_resultado.config(state=tk.NORMAL)
        self.area_monitoreo.config(state=tk.NORMAL)
        self.area_resultado.delete(1.0, tk.END)
        self.area_monitoreo.delete(1.0, tk.END)
        
        if not self.loaded_files:
            self.area_resultado.insert(tk.END, "⚠️ No hay archivos cargados para analizar.")
            self.area_resultado.config(state=tk.DISABLED)
            self.area_monitoreo.config(state=tk.DISABLED)
            return

        total_violations = 0
        
        # --- EJECUTAR REVISIÓN (Violaciones) ---
        for filepath, content in self.loaded_files.items():
            filename = os.path.basename(filepath)
            
            file_violations_count = 0
            file_results = []

            self.area_resultado.insert(tk.END, f"\n\n==================================================================\n")
            self.area_resultado.insert(tk.END, f"🔎 REVISIÓN DE ESTÁNDARES: {filename}\n", "ok")
            self.area_resultado.insert(tk.END, f"==================================================================\n")
            
            # 1. Check: Límite de 120 Caracteres
            if self.var_120_chars.get():
                _, violations, _ = self.check_line_length(content, filename)
                if violations:
                    file_results.append(f"❌ VIOLACIÓN: Límite de 120 Caracteres ({len(violations)} líneas)")
                    file_results.extend([f"     > {v}" for v in violations])
                    file_violations_count += len(violations)
                else:
                    file_results.append("✅ Límite de 120 Caracteres: OK")
                    
            # 2. Check: TODOs/FIXMEs
            if self.var_check_todos.get():
                _, violations, _ = self.check_for_todos(content, filename)
                if violations:
                    file_results.append(f"⚠️ PENDIENTE: Comentarios Pendientes (TODOs/FIXMEs) ({len(violations)} encontrados)")
                    file_results.extend([f"     > {v}" for v in violations])
                    file_violations_count += len(violations)
                else:
                    file_results.append("✅ Comentarios Pendientes: OK")
            
            # 3. Check: Parámetros No Utilizados
            if self.var_unused_params.get():
                _, violations, _ = self.check_unused_parameters(content, filename)
                if violations:
                    file_results.append(f"❌ VIOLACIÓN CRÍTICA: Parámetros No Utilizados ({len(violations)} funciones afectadas)")
                    file_results.extend(violations) 
                    file_violations_count += len(violations)
                else:
                    file_results.append("✅ Parámetros No Utilizados: OK")

            # 🌟 4. Check: Parámetros Documentados en Header (¡Actualizado V26!)
            if self.var_header_params.get():
                _, violations, _ = self.check_header_params_documentation(content, filename)
                if violations:
                    file_results.append(f"❌ VIOLACIÓN: Consistencia de Documentación de Parámetros ({len(violations)} problemas)")
                    file_results.extend(violations) 
                    file_violations_count += len(violations)
                else:
                    file_results.append("✅ Parámetros Documentados: OK")
                        
            # Mostrar resultados de revisión
            for result in file_results:
                if result.startswith(('❌', '⚠️')):
                    self.area_resultado.insert(tk.END, result + "\n", "warning")
                else:
                    self.area_resultado.insert(tk.END, result + "\n", "ok")

            total_violations += file_violations_count
            
            # --- EJECUTAR MONITOREO (Extracción de Datos) ---
            for filepath, content in self.loaded_files.items():
                filename = os.path.basename(filepath)
                
                if self.var_monitor_methods.get():
                    _, output_lines, _ = monitor_methods(content, filename)
                    
                    self.area_monitoreo.insert(tk.END, "\n".join(output_lines) + "\n\n")

        # Mensaje de Resumen Final de Revisión
        final_summary = f"\n\n--- RESUMEN FINAL DE REVISIÓN ---\n"
        if total_violations > 0:
            final_summary += f"🔴 ALERTA: Se encontraron {total_violations} violaciones de estándares en total.\n"
            self.area_resultado.insert(tk.END, final_summary, "warning")
        else:
            final_summary += "🟢 ÉXITO: Todos los archivos cargados cumplen con los estándares seleccionados.\n"
            self.area_resultado.insert(tk.END, final_summary, "ok")
            
        self.area_resultado.config(state=tk.DISABLED)
        self.area_monitoreo.config(state=tk.DISABLED)

# =========================================================================
# === Bloque de Ejecución Principal ===
# =========================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = CodeReviewApp(root)
    root.mainloop()