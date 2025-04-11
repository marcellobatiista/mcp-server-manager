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
