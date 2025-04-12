"""
Utilitários para a interface gráfica do MCP Server.

Este módulo contém funções e constantes utilitárias para a interface gráfica.
"""
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import ast

# Cores para a interface gráfica
COLORS = {
    "primary": "#1a73e8",
    "secondary": "#5f6368",
    "success": "#0f9d58",
    "warning": "#f4b400",
    "danger": "#ea4335",
    "light": "#f8f9fa",
    "dark": "#202124",
    "bg": "#ffffff",
    "text": "#202124",
    "border": "#dadce0",
    "hover": "#f1f3f4",
    "selected": "#e8f0fe",
}


def center_window(window, width=None, height=None):
    """
    Centraliza uma janela na tela.
    
    Args:
        window: Janela a ser centralizada
        width: Largura da janela (opcional)
        height: Altura da janela (opcional)
    """
    if width and height:
        window.geometry(f"{width}x{height}")
    
    window.update_idletasks()
    
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x = (screen_width - window.winfo_width()) // 2
    y = (screen_height - window.winfo_height()) // 2
    
    window.geometry(f"+{x}+{y}")


def show_error_message(title, message):
    """
    Exibe uma mensagem de erro.
    
    Args:
        title: Título da mensagem
        message: Conteúdo da mensagem
    """
    messagebox.showerror(title, message)


def show_info_message(title, message):
    """
    Exibe uma mensagem informativa.
    
    Args:
        title: Título da mensagem
        message: Conteúdo da mensagem
    """
    messagebox.showinfo(title, message)


def show_warning_message(title, message):
    """
    Exibe uma mensagem de aviso.
    
    Args:
        title: Título da mensagem
        message: Conteúdo da mensagem
    """
    messagebox.showwarning(title, message)


def ask_yes_no(title, message):
    """
    Exibe uma caixa de diálogo para resposta sim/não.
    
    Args:
        title: Título da mensagem
        message: Conteúdo da mensagem
    
    Returns:
        bool: True se sim, False se não
    """
    return messagebox.askyesno(title, message)


def show_options_dialog(title, message, options):
    """
    Exibe uma caixa de diálogo com opções para escolha.
    
    Args:
        title: Título da mensagem
        message: Conteúdo da mensagem
        options: Lista de strings com as opções disponíveis
    
    Returns:
        str: A opção escolhida ou None se o diálogo foi cancelado
    """
    # Criar uma janela de diálogo customizada
    dialog = tk.Toplevel()
    dialog.title(title)
    dialog.transient()  # Torna o diálogo modal
    dialog.resizable(False, False)
    dialog.grab_set()  # Bloqueia outras janelas até que esta seja fechada
    
    # Centralizar a janela
    center_window(dialog)
    
    # Adicionar mensagem
    ttk.Label(dialog, text=message, padding=(10, 10)).pack()
    
    # Variável para armazenar a opção escolhida
    result = [None]  # Usar lista para poder modificar de dentro da função interna
    
    # Função para selecionar opção e fechar o diálogo
    def select_option(option):
        result[0] = option
        dialog.destroy()
    
    # Adicionar botões para cada opção
    buttons_frame = ttk.Frame(dialog, padding=(10, 0, 10, 10))
    buttons_frame.pack(fill=tk.X)
    
    for option in options:
        btn = ttk.Button(
            buttons_frame, 
            text=option, 
            command=lambda opt=option: select_option(opt)
        )
        btn.pack(fill=tk.X, pady=2)
    
    # Adicionar botão Cancelar
    ttk.Separator(dialog, orient="horizontal").pack(fill=tk.X, padx=10)
    cancel_btn = ttk.Button(dialog, text="Cancelar", command=dialog.destroy)
    cancel_btn.pack(pady=10)
    
    # Esperar até que o diálogo seja fechado
    dialog.wait_window()
    
    return result[0]


def apply_default_styles(root):
    """
    Aplica estilos padrão para a aplicação.
    
    Args:
        root: Janela raiz da aplicação
    
    Returns:
        O objeto de estilo configurado
    """
    style = ttk.Style(root)
    
    # Configurar tema
    if "clam" in style.theme_names():
        style.theme_use("clam")
    
    # Estilos de texto
    style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
    style.configure("Subtitle.TLabel", font=("Segoe UI", 14))
    
    # Estilos de botões
    style.configure(
        "Primary.TButton",
        background=COLORS["primary"],
        foreground="white"
    )
    
    # Estilo de notebooks
    style.configure(
        "TNotebook", 
        background=COLORS["bg"]
    )
    style.configure(
        "TNotebook.Tab", 
        padding=[10, 5], 
        background=COLORS["light"]
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLORS["bg"])]
    )
    
    return style


def create_tooltip(widget, text):
    """
    Cria uma tooltip para um widget.
    
    Args:
        widget: Widget que receberá a tooltip
        text: Texto da tooltip
    
    Returns:
        Uma função para destruir a tooltip
    """
    tooltip = None
    
    def enter(event=None):
        nonlocal tooltip
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        
        # Cria uma janela de nível superior
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(
            tooltip, 
            text=text, 
            justify=tk.LEFT,
            background="#ffffe0", 
            relief=tk.SOLID, 
            borderwidth=1,
            font=("tahoma", "8", "normal"),
            padding=(5, 3)
        )
        label.pack()
    
    def leave(event=None):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None
    
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)
    
    # Retorna uma função para destruir a tooltip (útil ao destruir o widget)
    return lambda: widget.unbind("<Enter>"), widget.unbind("<Leave>")


def create_directory_if_not_exists(directory_path):
    """
    Cria um diretório se ele não existir.
    
    Args:
        directory_path: Caminho do diretório
    
    Returns:
        bool: True se o diretório foi criado ou já existia, False caso contrário
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception:
        return False


def load_json_file(file_path, default=None):
    """
    Carrega dados de um arquivo JSON.
    
    Args:
        file_path: Caminho do arquivo JSON
        default: Valor padrão a ser retornado se o arquivo não existir
    
    Returns:
        Dados carregados do arquivo ou o valor padrão
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except Exception as e:
        show_error_message(
            "Erro ao carregar arquivo", 
            f"Não foi possível carregar o arquivo: {str(e)}"
        )
        return default


def save_json_file(file_path, data):
    """
    Salva dados em um arquivo JSON.
    
    Args:
        file_path: Caminho do arquivo JSON
        data: Dados a serem salvos
    
    Returns:
        bool: True se o arquivo foi salvo com sucesso, False caso contrário
    """
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        show_error_message(
            "Erro ao salvar arquivo", 
            f"Não foi possível salvar o arquivo: {str(e)}"
        )
        return False


def format_path(path):
    """
    Formata um caminho para exibição, abreviando-o se for muito longo.
    
    Args:
        path: Caminho a ser formatado
    
    Returns:
        str: Caminho formatado
    """
    path_obj = Path(path)
    
    if len(str(path)) > 60:
        parts = path_obj.parts
        if len(parts) > 3:
            # Mostrar apenas o drive, "...", e os 2 últimos diretórios
            formatted = str(Path(parts[0]) / "..." / Path(*parts[-2:]))
            return formatted
    
    return str(path)


def clean_docstring(docstring):
    """
    Limpa e formata uma docstring para melhor exibição.
    
    Args:
        docstring (str): A docstring original
        
    Returns:
        str: A docstring formatada
    """
    if not docstring:
        return "Sem descrição disponível"
    
    # Remover delimitadores de docstring (""" ou ''')
    if docstring.startswith('"""') and docstring.endswith('"""'):
        docstring = docstring[3:-3]
    elif docstring.startswith("'''") and docstring.endswith("'''"):
        docstring = docstring[3:-3]
    
    # Tratar caso onde as aspas triplas não estão na mesma linha
    # Às vezes a regex captura a aspas do início numa linha e do final noutra
    docstring = docstring.replace('"""\n', '\n').replace('\n"""', '\n')
    docstring = docstring.replace("'''\n", '\n').replace("\n'''", '\n')
    
    # Dividir em linhas e remover indentação comum
    lines = docstring.split('\n')
    
    # Remover linhas em branco no início e no fim
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    if not lines:
        return "Sem descrição disponível"
    
    # Encontrar indentação comum (exceto para a primeira linha)
    indent = float('inf')
    for line in lines[1:]:
        if line.strip():  # Ignorar linhas vazias
            line_indent = len(line) - len(line.lstrip())
            indent = min(indent, line_indent)
    
    if indent == float('inf'):
        indent = 0
    
    # Remover indentação comum de todas as linhas (exceto a primeira)
    result = [lines[0].strip()]
    for line in lines[1:]:
        if line.strip():  # Manter linhas não vazias
            result.append(line[indent:] if indent <= len(line) else line.strip())
        else:
            result.append('')  # Manter linhas vazias
    
    # Verificar se a docstring contém tabulações e convertê-las para espaços
    result = [line.replace('\t', '    ') for line in result]
    
    return '\n'.join(result).strip()


def extract_mcp_tools(file_path):
    """
    Extrai as ferramentas MCP de um arquivo Python.
    
    Args:
        file_path (str): Caminho para o arquivo Python
        
    Returns:
        list: Lista de dicionários com informações das ferramentas MCP
    """
    tools = []
    # Conjunto para rastrear nomes de ferramentas já encontradas e evitar duplicações
    tool_names = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Analisar o código Python
        tree = ast.parse(content)
        
        # Procurar por funções decoradas com @mcp.tool()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Pular se esta função já foi processada
                if node.name in tool_names:
                    continue
                    
                # Verificar se a função tem decoradores
                for decorator in node.decorator_list:
                    # Procurar por diferentes formas do decorador @mcp.tool()
                    is_mcp_tool = False
                    
                    # Caso 1: @mcp.tool()
                    if (isinstance(decorator, ast.Call) and 
                        isinstance(decorator.func, ast.Attribute) and 
                        decorator.func.attr == 'tool' and 
                        isinstance(decorator.func.value, ast.Name) and 
                        decorator.func.value.id == 'mcp'):
                        is_mcp_tool = True
                    
                    # Caso 2: @mcp.tool
                    elif (isinstance(decorator, ast.Attribute) and 
                          decorator.attr == 'tool' and 
                          isinstance(decorator.value, ast.Name) and 
                          decorator.value.id == 'mcp'):
                        is_mcp_tool = True
                        
                    # Caso 3: @tool (se a função mcp.tool foi importada diretamente)
                    elif (isinstance(decorator, ast.Name) and 
                          decorator.id == 'tool'):
                        is_mcp_tool = True
                    
                    if is_mcp_tool:
                        # Adicionar o nome da ferramenta ao conjunto para evitar duplicações
                        tool_names.add(node.name)
                        
                        # Método 1: Extrair a docstring com ast.get_docstring
                        docstring = ast.get_docstring(node)
                        
                        # Método 2: Tentar extrair diretamente do nó AST
                        if not docstring:
                            for item in node.body:
                                if isinstance(item, ast.Expr) and hasattr(item.value, 'value') and isinstance(item.value.value, str):
                                    docstring = item.value.value
                                    break
                                elif isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(item.value.s, str):
                                    docstring = item.value.s
                                    break
                                elif isinstance(item, ast.Expr) and isinstance(item.value, ast.Str):
                                    # Para Python 3.7 e versões anteriores
                                    docstring = item.value.s
                                    break
                        
                        # Método 3: Extrair usando expressões regulares
                        if not docstring:
                            import re
                            
                            # Obter a linha inicial da função
                            lineno = node.lineno
                            col_offset = node.col_offset
                            
                            # Extrair o conteúdo da função do código fonte
                            func_pattern = rf"def\s+{node.name}\s*\(.*?\).*?:(.*?)(?=\n\s*[^\s\n]|\Z)"
                            func_match = re.search(func_pattern, content, re.DOTALL)
                            
                            if func_match:
                                func_body = func_match.group(1)
                                
                                # Procurar por docstrings com aspas triplas duplas
                                doc_match = re.search(r'"""(.*?)"""', func_body, re.DOTALL)
                                if doc_match:
                                    docstring = doc_match.group(1)
                                else:
                                    # Procurar por docstrings com aspas triplas simples
                                    doc_match = re.search(r"'''(.*?)'''", func_body, re.DOTALL)
                                    if doc_match:
                                        docstring = doc_match.group(1)
                        
                        # Se mesmo assim não encontrou, use uma mensagem padrão
                        if not docstring:
                            docstring = f"Ferramenta: {node.name} (sem descrição disponível)"
                        
                        # Limpar e formatar a docstring
                        docstring = clean_docstring(docstring)
                        
                        # Coletar informações dos parâmetros
                        params = []
                        for arg in node.args.args:
                            if arg.arg != 'self':  # Ignorar self em métodos
                                param_name = arg.arg
                                param_type = ""
                                
                                # Tentar extrair o tipo de anotação
                                if arg.annotation:
                                    if isinstance(arg.annotation, ast.Name):
                                        param_type = arg.annotation.id
                                    elif isinstance(arg.annotation, ast.Subscript):
                                        if isinstance(arg.annotation.value, ast.Name):
                                            container = arg.annotation.value.id
                                            # Tentar obter o tipo interno
                                            if isinstance(arg.annotation.slice, ast.Index):  # Python 3.8 e anterior
                                                if isinstance(arg.annotation.slice.value, ast.Name):
                                                    inner_type = arg.annotation.slice.value.id
                                                    param_type = f"{container}[{inner_type}]"
                                                else:
                                                    param_type = f"{container}"
                                            else:  # Python 3.9+
                                                if isinstance(arg.annotation.slice, ast.Name):
                                                    inner_type = arg.annotation.slice.id
                                                    param_type = f"{container}[{inner_type}]"
                                                else:
                                                    param_type = f"{container}"
                                
                                # Verificar se há valor padrão para este parâmetro
                                param_default = None
                                param_has_default = False
                                
                                # Encontrar valores padrão examinando defaults na função
                                if node.args.defaults:
                                    # Calcular o índice do argumento na lista de defaults
                                    # Os defaults são alinhados à direita na lista de argumentos
                                    args_without_defaults = len(node.args.args) - len(node.args.defaults)
                                    arg_idx = list(node.args.args).index(arg)
                                    if arg_idx >= args_without_defaults:
                                        default_idx = arg_idx - args_without_defaults
                                        if default_idx >= 0 and default_idx < len(node.args.defaults):
                                            default_node = node.args.defaults[default_idx]
                                            param_has_default = True
                                            # Extrair o valor literal do default
                                            if isinstance(default_node, ast.Constant):
                                                param_default = default_node.value
                                            elif isinstance(default_node, ast.Str):  # Para compatibilidade com versões antigas
                                                param_default = default_node.s
                                            elif isinstance(default_node, ast.Num):  # Para compatibilidade com versões antigas
                                                param_default = default_node.n
                                            elif isinstance(default_node, ast.NameConstant):  # Para compatibilidade com versões antigas
                                                param_default = default_node.value
                                            elif isinstance(default_node, ast.Name) and default_node.id == 'None':
                                                param_default = None
                                
                                params.append({
                                    "name": param_name,
                                    "type": param_type,
                                    "has_default": param_has_default,
                                    "default": param_default
                                })
                        
                        # Extrair tipo de retorno
                        return_type = ""
                        if node.returns:
                            if isinstance(node.returns, ast.Name):
                                return_type = node.returns.id
                            elif isinstance(node.returns, ast.Subscript):
                                if isinstance(node.returns.value, ast.Name):
                                    container = node.returns.value.id
                                    # Similar ao código para param_type
                                    if isinstance(node.returns.slice, ast.Index):  # Python 3.8 e anterior
                                        if isinstance(node.returns.slice.value, ast.Name):
                                            inner_type = node.returns.slice.value.id
                                            return_type = f"{container}[{inner_type}]"
                                        else:
                                            return_type = f"{container}"
                                    else:  # Python 3.9+
                                        if isinstance(node.returns.slice, ast.Name):
                                            inner_type = node.returns.slice.id
                                            return_type = f"{container}[{inner_type}]"
                                        else:
                                            return_type = f"{container}"
                        
                        tools.append({
                            "name": node.name,
                            "docstring": docstring,
                            "params": params,
                            "return_type": return_type
                        })
                        
                        # Não continuar verificando outros decoradores desta função
                        break
        
        # Verificar se não encontrou nenhuma ferramenta e tentar buscar de forma alternativa
        if not tools:
            # Tentar buscar usando expressões regulares para os casos onde o AST falha
            import re
            
            # Padrões para encontrar funções decoradas com docstrings
            patterns = [
                # Função com docstring em aspas triplas duplas
                r'@mcp\.tool\s*\(\s*\)\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->[^:]*)?:\s*"""(.*?)"""',
                r'@mcp\.tool\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->[^:]*)?:\s*"""(.*?)"""',
                r'@tool\s*\(\s*\)\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->[^:]*)?:\s*"""(.*?)"""',
                r'@tool\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->[^:]*)?:\s*"""(.*?)"""',
                
                # Função com docstring em aspas triplas simples
                r"@mcp\.tool\s*\(\s*\)\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->[^:]*)?:\s*'''(.*?)'''",
                r"@mcp\.tool\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->[^:]*)?:\s*'''(.*?)'''",
                r"@tool\s*\(\s*\)\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->[^:]*)?:\s*'''(.*?)'''",
                r"@tool\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->[^:]*)?:\s*'''(.*?)'''",
                
                # Função sem docstring
                r'@mcp\.tool\s*\(\s*\)\s*\n\s*(?:async\s+)?def\s+(\w+)',
                r'@mcp\.tool\s*\n\s*(?:async\s+)?def\s+(\w+)',
                r'@tool\s*\(\s*\)\s*\n\s*(?:async\s+)?def\s+(\w+)',
                r'@tool\s*\n\s*(?:async\s+)?def\s+(\w+)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.DOTALL)
                for match in matches:
                    function_name = match.group(1)
                    
                    # Pular se esta função já foi processada
                    if function_name in tool_names:
                        continue
                        
                    # Adicionar o nome da ferramenta ao conjunto para evitar duplicações
                    tool_names.add(function_name)
                    
                    docstring = "Sem descrição disponível"
                    
                    # Se o padrão capturou uma docstring (grupo 2), use-a
                    if len(match.groups()) > 1 and match.group(2):
                        docstring = match.group(2)
                    
                    # Limpar e formatar a docstring
                    docstring = clean_docstring(docstring)
                    
                    # Adicionar uma entrada para a ferramenta encontrada
                    tools.append({
                        "name": function_name,
                        "docstring": docstring,
                        "params": [],
                        "return_type": ""
                    })
        
        return tools
    except Exception as e:
        print(f"Erro ao extrair ferramentas MCP: {str(e)}")
        return []
