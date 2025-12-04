import re
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import sys 

# --- FUNCIÓN CENTRAL DE ANÁLISIS ---

# Reemplaza la FUNCIÓN CENTRAL DE ANÁLISIS con esta V11.0.


# Reemplaza la FUNCIÓN CENTRAL DE ANÁLISIS con esta V12.0.

def locate_method_starts(code, filename, output_widget):
    """
    Busca firmas de método de clase y reporta la línea de inicio de su llave '{'.
    (V12.0: Precisión de alcance y limpieza explícita de comentarios al inicio de línea)
    """
    
    def log(message, color="black"):
        output_widget.tag_config(color, foreground=color)
        output_widget.insert(tk.END, message + "\n", color)
        output_widget.see(tk.END)
    
    log(f"==================================================================")
    log(f"🔎 INICIANDO BÚSQUEDA DE MÉTODOS EN: {filename}", "blue")
    log(f"==================================================================\n")
    
    # 1. Palabras clave de control de flujo a excluir
    EXCLUDED_KEYWORDS = r'(?:if|for|while|switch|catch|do|try|new|delete|sizeof|return|NULL|class|struct|enum|using)\b'

    # 2. PATRÓN FINAL (V12.0)
    FUNCTION_SIG_PATTERN = re.compile(
        # COMIENZO CRÍTICO: Coincide con inicio de línea/newline, espacios, y CUALQUIER NÚMERO
        # de comentarios de una o varias líneas que puedan estar entre el método anterior y este.
        r'(?:^|\n)\s*(?:/\*[\s\S]*?\*/|//[^\n]*\n)*\s*'
        
        # Group 1: Tipo de retorno. NO permite ':' para evitar consumir parte del alcance '::'.
        r'([a-zA-Z_][a-zA-Z0-9_&\s*<>()\[\]]+\s+)?' 
        
        r'(?!' + EXCLUDED_KEYWORDS + r')' # Negación de palabras clave
        
        r'(' # Group 2 (ALCANCE Y NOMBRE DEL MÉTODO): DEBE contener '::' o 'operator'
            
            # Opción 1: Método/Constructor/Destructor con alcance anidado (Clase::SubClase::Metodo)
            r'(?:[a-zA-Z_][a-zA-Z0-9_]*::)+[a-zA-Z_~][a-zA-Z0-9_:]*' 
            r'|'
            # Opción 2: Operador sobrecargado (con o sin alcance)
            r'(?:[a-zA-Z_][a-zA-Z0-9_]*::)?operator\s*(?:<<|>>|==|!=|<=|>=|<|>|\+\+|--|\+|-|\*|/|%|=|\[\]|&|\||\^|~|\(\))'
        r')'  
        
        # Group 3 (Parámetros): Permite cualquier contenido, incluyendo comentarios y newlines.
        r'\s*\(([\s\S]*?)\)' 
        r'(\s*const)?'                        # Group 4: Modificador const (opcional)
        r'(\s*:[\s\S]*?)?'                    # Group 5: Lista de inicialización (opcional)
        r'\s*\{'                              # Coincide con la llave de apertura
        , re.DOTALL  
    )
    
    current_pos = 0  
    results = []
    
    while True:
        # Usa re.search desde la posición actual
        match = FUNCTION_SIG_PATTERN.search(code, current_pos)
        
        if not match:
            break  
        
        # 3. Calcular la línea y posición del inicio de la llave '{'
        start_brace_index = match.end() - 1
        line_number = code.count('\n', 0, start_brace_index) + 1
        full_name = match.group(2).strip()
        
        # 4. Determinar el índice de inicio real de la firma
        # match.start() devuelve el inicio de la coincidencia completa (incluyendo comentarios y \n)
        
        # Intentamos obtener el inicio del Grupo 1, y si no existe (constructor), el inicio del Grupo 2.
        real_start_index = match.start(1) if match.group(1) else match.start(2)
        
        signature_line = code[real_start_index:start_brace_index].strip()
        
        # 5. Encontrar el final del cuerpo de la función (llave de cierre '}')
        body, body_end_index = _extract_brace_body(code, start_brace_index)
        
        if body is None or body_end_index == -1:
            log(f"   ⚠️ ERROR: Cuerpo no cerrado para '{full_name}'. Saltando.", "red")
            current_pos = start_brace_index + 1
            continue

        results.append({
            'name': full_name,
            'signature': signature_line,
            'line_start': line_number,
        })
        
        # 6. Mover la posición de búsqueda justo después del cierre de llave
        current_pos = body_end_index + 1
        
    # --- REPORTE DE RESULTADOS ---
    log("\n==================================================================")
    log(f"🎉 ANÁLISIS COMPLETADO. {len(results)} métodos de clase identificados.", "blue")
    log("==================================================================")

    if results:
        log("\n| Línea | Método de Clase/Operador |")
        log("|-------|--------------------------|")
        for r in results:
            display_signature = r['signature'].replace(r['name'], f"**{r['name']}**")
            log(f"| {r['line_start']:<5} | {display_signature} {{...}}", "green")
    else:
        log("No se encontraron métodos de clase con notación de alcance (::) o sobrecarga de operador.", "red")
        
    log("\n--- FIN DEL REPORTE ---")
    
# --- FUNCIONES DE SOPORTE y CLASE DE UI (Mantener el código sin cambios) ---
# ... (El código de _extract_brace_body y MethodLocatorApp es estable y no necesita cambios) ...
def _extract_brace_body(code_snippet, start_brace_index):
    balance = 1
    body_end_index = start_brace_index + 1
    code_length = len(code_snippet)
    
    while body_end_index < code_length:
        char = code_snippet[body_end_index]
        
        # Manejo de Strings
        if char == '"' or char == "'":
            end_quote = code_snippet.find(char, body_end_index + 1)
            while end_quote != -1 and code_snippet[end_quote - 1] == '\\':
                end_quote = code_snippet.find(char, end_quote + 1)
            if end_quote != -1:
                body_end_index = end_quote + 1
                continue
            
        # Manejo de Comentarios C/C++
        elif char == '/':
            next_char_index = body_end_index + 1
            if next_char_index < code_length:
                next_char = code_snippet[next_char_index]
                if next_char == '/':
                    newline_index = code_snippet.find('\n', next_char_index)
                    body_end_index = newline_index + 1 if newline_index != -1 else code_length  
                    continue
                elif next_char == '*':
                    end_comment_index = code_snippet.find('*/', next_char_index + 1)
                    body_end_index = end_comment_index + 2 if end_comment_index != -1 else code_length  
                    continue
        
        # Contador de Llaves
        if char == '{':
            balance += 1
        elif char == '}':
            balance -= 1
            if balance == 0:
                return code_snippet[start_brace_index + 1 : body_end_index], body_end_index
        
        body_end_index += 1
        
    return None, -1 


class MethodLocatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Localizador de Métodos C++ (Línea de Inicio)")
        master.geometry("800x600")
        
        self.file_path = tk.StringVar(value="Ningún archivo seleccionado")

        style = ttk.Style()
        style.configure('TButton', font=('Helvetica', 10), padding=5)

        control_frame = ttk.Frame(master, padding="10 10 10 10")
        control_frame.pack(fill='x')

        ttk.Button(control_frame, text="1. Seleccionar Archivo C++", command=self.open_file_dialog).pack(side='left', padx=5)
        ttk.Label(control_frame, textvariable=self.file_path, width=50).pack(side='left', padx=10, fill='x', expand=True)
        
        ttk.Button(control_frame, text="2. ANALIZAR", command=self.start_analysis).pack(side='right', padx=5)

        output_frame = ttk.Frame(master, padding="10 0 10 10")
        output_frame.pack(fill='both', expand=True)
        
        ttk.Label(output_frame, text="Resultado y Posiciones de Línea:").pack(fill='x')
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, width=80, height=30, font=('Consolas', 10), background="#f5f5f5")
        self.output_text.pack(fill='both', expand=True)

    def open_file_dialog(self):
        filetypes = (
            ('Archivos C/C++', '*.cpp;*.cxx;*.cc'),
            ('Archivos de Cabecera C/C++', '*.h;*.hpp'),
            ('Todos los archivos', '*.*')
        )
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo C++ para analizar",
            initialdir=os.path.expanduser("~"),
            filetypes=filetypes
        )
        if filepath:
            self.file_path.set(filepath)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"Archivo seleccionado: {os.path.basename(filepath)}\nListo para analizar.")

    def start_analysis(self):
        filepath = self.file_path.get()
        if not os.path.exists(filepath):
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "ERROR: Por favor, selecciona un archivo válido primero.", "red")
            return

        try:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    code_content = f.read()
            except UnicodeDecodeError:
                with open(filepath, 'r', encoding='latin-1') as f:
                    code_content = f.read()
            
            filename = os.path.basename(filepath)
            self.output_text.delete(1.0, tk.END)
            
            locate_method_starts(code_content, filename, self.output_text)

        except Exception as e:
            self.output_text.insert(tk.END, f"\n--- ERROR FATAL DURANTE EL ANÁLISIS ---\n{type(e).__name__}: {str(e)}", "red")


if __name__ == "__main__":
    root = tk.Tk()
    root.option_add('*tearOff', False) 
    app = MethodLocatorApp(root)
    root.mainloop()