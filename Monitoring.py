# Monitoring.py

import re
import os


def monitor_methods(code, filename):
    """
    Identifica y extrae métodos/funciones de C++ (y similares) con su contenido
    y su comentario de cabecera. Utiliza búsqueda secuencial para evitar anidamiento.
    """
    results = []
    
    if filename.lower().endswith(('.html', '.css', '.md')):
        return "Extracción de Métodos", [f"ℹ️ OMITIDO. No aplica para archivos {os.path.splitext(filename)[1].upper()}."], 0
    # Palabras clave de control de flujo C/C++ a excluir de ser nombres de función
    EXCLUDED_KEYWORDS = r'(?:if|for|while|switch|catch|do|try|new|delete|sizeof|return|NULL|class|struct|enum|using)\b'
    # PATRÓN V15: Usamos el mismo patrón que en check_unused_parameters para ser consistentes
    FUNCTION_SIG_PATTERN = re.compile(
        # Start of string OR after a newline, followed by optional whitespace
        r'(?:^|\n)\s*'
        # Tipo de retorno o scope (opcional, flexible con espacios/saltos de línea)
        r'(?:[a-zA-Z_][a-zA-Z0-9_:\s*&<>]+\s+)?' 
        r'(?!' + EXCLUDED_KEYWORDS + r')'
        r'([a-zA-Z_][a-zA-Z0-9_:]*|operator\s*(?:==|!=|<=|>=|<|>|\+\+|--|\+|-|\*|/|%|=|\[\]|<<|>>|&|\||\^|~|\(\)))'  # Group 1 (Name or Operator)
        r'\s*\((.*?)\)'              # Group 2 (Parameters)
        r'(?:\s*const)?'             # Modificador const (opcional)
        r'(\s*:[\s\S]*?)?'           # Group 3: Lista de inicialización (Constructor), opcional
        r'\s*\{'                     # Coincide con la llave de apertura
        , re.DOTALL 
    )
    current_pos = 0 
    
    while True:
        match = FUNCTION_SIG_PATTERN.search(code, current_pos)
        if not match:
            break 
        param_string = match.group(2) 
        init_list = match.group(3) # Lista de inicialización
        start_brace_index = match.end() - 1 
        
        func_body, body_end_index = _extract_brace_body(code, start_brace_index)
        if func_body is None or body_end_index == -1:
            current_pos = start_brace_index + 1
            continue
        full_name = match.group(1) 
        
        # 1. Definir el inicio real del código (después de newlines/whitespaces que vienen antes)
        match_start = match.start()
        if code[match_start] == '\n':
            match_start += 1
            
        real_signature_start = re.search(r'\S', code[match_start:start_brace_index])
        real_start_index = match_start + real_signature_start.start() if real_signature_start else match_start
        
        # 2. Extraer el encabezado de la función (hasta el inicio de la lista de inicialización Group 3)
        # Esto corrige el problema de la firma multi-línea con la lista de inicialización.
        header_end_index = match.start(3) if match.group(3) else start_brace_index
        signature_header = code[real_start_index:header_end_index].strip()
        
        # 3. Extraer el comentario de cabecera 
        header_comment = _get_header_comment(code, real_start_index)
        
        clean_body = func_body.strip()
        init_list_text = init_list.strip() if init_list else 'N/A'
        
        results.append({
            'name': full_name, 
            'comment': header_comment,
            'signature_header': signature_header, # AHORA SOLO LA CABECERA (sin lista de inicialización)
            'parameters': param_string.strip(), 
            'init_list': init_list_text,        # Lista de inicialización (multilínea)
            'content': clean_body 
        })
        
        current_pos = body_end_index + 1
        
    # Formatear la salida para el área de monitoreo
    output_lines = [f"--- MONITOREO DE MÉTODOS: {filename} ({len(results)} encontrados) ---"]
    if results:
        for r in results:
            output_lines.append(f"\n==================================================================")
            output_lines.append(f"🔹 MÉTODO IDENTIFICADO: {r['name']}")
            output_lines.append(f"==================================================================")
            
            output_lines.append(f"💬 COMENTARIO DE CABECERA:")
            output_lines.append(r['comment'])
            
            output_lines.append(f"\n📝 FIRMA (Solo cabecera):")
            output_lines.append(r['signature_header']) # Muestra solo la parte de la función
            
            # MOSTRAR PARÁMETROS y LISTA DE INICIALIZACIÓN (separados para claridad)
            output_lines.append(f"\n⚙️ PARÁMETROS:") 
            output_lines.append(f"({r['parameters']})") 
            
            output_lines.append(f"\n⚙️ LISTA DE INICIALIZACIÓN (C++):") 
            output_lines.append(r['init_list']) # Muestra la lista completa, incluyendo saltos de línea
            output_lines.append(f"\n💻 CONTENIDO DEL CUERPO (Solo lo que está dentro de {{}}):")
            output_lines.append(r['content'])
    else:
        output_lines.append("No se encontraron métodos que cumplan el patrón de extracción.")
    return "Extracción de Métodos", output_lines, len(results)



def _extract_brace_body(code_snippet, start_brace_index):
    """
    Extrae el cuerpo de la función contando llaves anidadas ({ y }).
    """
    balance = 1
    body_end_index = start_brace_index + 1
    code_length = len(code_snippet)
    
    # Iterar desde el caracter después del '{' inicial
    while body_end_index < code_length:
        char = code_snippet[body_end_index]
        
        # --- Manejo de Strings ---
        # Simplificación: Asumir que la lógica de quote escapado es correcta para avanzar el índice
        if char == '"' or char == "'":
            # start_quote = body_end_index # Not used, can be removed
            end_quote = code_snippet.find(char, body_end_index + 1)
            
            # Simple loop to skip escaped quotes: '\"' or '\''
            while end_quote != -1 and code_snippet[end_quote - 1] == '\\':
                end_quote = code_snippet.find(char, end_quote + 1)

            if end_quote != -1:
                body_end_index = end_quote + 1
                continue
            # If end_quote not found, assume unclosed string and continue char by char
            
        # --- Manejo de Comentarios C/C++ ---
        elif char == '/':
            next_char_index = body_end_index + 1
            if next_char_index < code_length:
                next_char = code_snippet[next_char_index]
                
                if next_char == '/':
                    # Comentario de una línea (//...)
                    newline_index = code_snippet.find('\n', next_char_index)
                    if newline_index != -1:
                        body_end_index = newline_index + 1
                    else:
                        # Fin del archivo
                        body_end_index = code_length 
                    continue
                    
                elif next_char == '*':
                    # Comentario de bloque (/*...*/)
                    end_comment_index = code_snippet.find('*/', next_char_index + 1)
                    if end_comment_index != -1:
                        body_end_index = end_comment_index + 2
                    else:
                        # Comentario de bloque sin cerrar, avanzar hasta el final para evitar bucle infinito
                        body_end_index = code_length 
                    continue
            
        # --- Manejo de Comentarios Python/Shell ---
        elif char == '#':
            newline_index = code_snippet.find('\n', body_end_index + 1)
            if newline_index != -1:
                body_end_index = newline_index + 1
            else:
                body_end_index = code_length
            continue
        
        # --- Contador de Llaves ---
        if char == '{':
            balance += 1
        elif char == '}':
            balance -= 1
            if balance == 0:
                # Encontró el cierre de la función/método
                return code_snippet[start_brace_index + 1 : body_end_index], body_end_index
        
        body_end_index += 1
        
    return None, -1 # Cuerpo no cerrado encontrado (función malformada)



def _get_header_comment(code_snippet, func_start_index):
    """
    Extrae el comentario que precede inmediatamente a la firma de la función.
    """
    preceding_code = code_snippet[:func_start_index].rstrip()
    
    # 1. Patrón para comentario de bloque C-style (/* ... */) al final
    block_comment_match = re.search(r'/\*[\s\S]*?\*/\s*$', preceding_code, re.DOTALL)
    if block_comment_match:
        return block_comment_match.group(0).strip()

    # 2. Patrón para comentarios de una línea (//) o inicio de bloque (doc-strings Py/JS)
    line_comments = []
    lines = preceding_code.split('\n')
    
    # Revisar las últimas líneas
    for line in reversed(lines):
        stripped_line = line.strip()
        # Buscar líneas de comentario C++/JS (//) o líneas de documentación de Python/JS (#)
        if stripped_line.startswith('//') or stripped_line.startswith('*') or stripped_line.startswith('#'):
            line_comments.append(stripped_line)
        elif stripped_line and not stripped_line.startswith(('template<', '#')):
            # Si encontramos código real (y no es una directiva o template), paramos
            break
            
    if line_comments:
        line_comments.reverse() # Poner en orden correcto
        return '\n'.join(line_comments).strip()

    return "No se encontró comentario de cabecera."
