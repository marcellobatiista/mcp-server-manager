"""
Gerenciador de configurações para a interface gráfica do MCP Server.

Este módulo contém classes e funções para gerenciar as configurações da aplicação.
"""
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

# Tenta importar temas adicionais, se estiverem instalados
try:
    from ttkthemes import ThemedStyle
    TTKTHEMES_AVAILABLE = True
except ImportError:
    TTKTHEMES_AVAILABLE = False

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.utils import (
    COLORS,
    show_error_message,
    show_info_message
)

# Gera o conteúdo do script para mostrar mensagem colorida no terminal
UV_WARNING_SCRIPT = '''
try:
    from rich.console import Console
    from rich import print as rprint
    
    console = Console()
    
    console.print("\\n[bold]IMPORTANTE:[/bold] Para instalar pacotes neste ambiente use ", 
                 "[bold green]uv pip install [pacote][/bold green]", 
                 " em vez de ", 
                 "[bold red]pip install [pacote][/bold red]", 
                 ".")
    console.print("Saiba mais sobre o UV em [link]https://github.com/astral-sh/uv[/link]\\n")
except ImportError:
    print("\\nIMPORTANTE: Para instalar pacotes neste ambiente use 'uv pip install [pacote]' em vez de 'pip install [pacote]'.\\n")
'''

class ConfigManager(ttk.Frame):
    """
    Gerenciador de configurações para a aplicação MCP Server.
    """
    def __init__(self, parent):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            parent: Widget pai
        """
        super().__init__(parent, padding=10)
        
        # Configurações padrão
        self.config = {
            "python_path": sys.executable,
            "log_dir": os.path.join(Path(__file__).resolve().parent.parent, "logs"),
            "data_dir": os.path.join(Path(__file__).resolve().parent.parent, "data"),
            "venv_path": os.path.join(Path(__file__).resolve().parent.parent, "mcp_server"),
            "theme": "default"  # Usando 'default' como tema padrão
        }
        
        # Carregar configurações
        self.config_file = os.path.join(Path(__file__).resolve().parent.parent, "config", "app_config.json")
        self._load_config()
        
        # Criar interface
        self._create_interface()
    
    def _load_config(self):
        """
        Carrega as configurações do arquivo.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # Atualizar apenas as chaves existentes
                    for key, value in saved_config.items():
                        if key in self.config:
                            self.config[key] = value
        except Exception as e:
            print(f"Erro ao carregar configurações: {str(e)}")
    
    def _save_config(self):
        """
        Salva as configurações no arquivo.
        """
        try:
            # Garantir que o diretório de configuração existe
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Salvar configurações
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
                
            show_info_message("Configurações", "Configurações salvas com sucesso.")
        except Exception as e:
            show_error_message("Erro", f"Erro ao salvar configurações: {str(e)}")
    
    def _create_interface(self):
        """
        Cria a interface do gerenciador de configurações.
        """
        # Título da seção
        title_label = ttk.Label(
            self, 
            text="Configurações do Sistema", 
            style="Subtitle.TLabel"
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Obter lista de temas disponíveis
        available_themes = []
        if TTKTHEMES_AVAILABLE:
            # Usar temas adicionais se disponíveis
            themed_style = ThemedStyle(self.master)
            available_themes = sorted(themed_style.theme_names())
        else:
            # Usar apenas temas nativos do ttk
            style = ttk.Style()
            available_themes = sorted(style.theme_names())
        
        # Configurações gerais
        general_frame = ttk.LabelFrame(self, text="Configurações Gerais")
        general_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Python Path
        python_frame = ttk.Frame(general_frame, padding=5)
        python_frame.pack(fill=tk.X)
        
        ttk.Label(python_frame, text="Caminho do Python:").pack(side=tk.LEFT)
        self.python_path_label = self._create_link_label(python_frame, self.config["python_path"])
        self.python_path_label.pack(side=tk.LEFT, padx=5)
        
        # Diretório de Logs
        log_dir_frame = ttk.Frame(general_frame, padding=5)
        log_dir_frame.pack(fill=tk.X)
        
        ttk.Label(log_dir_frame, text="Diretório de Logs:").pack(side=tk.LEFT)
        self.log_dir_label = self._create_link_label(log_dir_frame, self.config["log_dir"])
        self.log_dir_label.pack(side=tk.LEFT, padx=5)
        
        # Ambiente Virtual
        venv_frame = ttk.Frame(general_frame, padding=5)
        venv_frame.pack(fill=tk.X)
        
        ttk.Label(venv_frame, text="Ambiente Virtual dos Servidores:").pack(side=tk.LEFT)
        self.venv_path_label = self._create_link_label(venv_frame, self.config["venv_path"])
        self.venv_path_label.pack(side=tk.LEFT, padx=5)
        
        # Botão para abrir terminal com ambiente virtual ativado
        open_terminal_btn = ttk.Button(
            venv_frame,
            text="Abrir terminal do ambiente",
            command=self._show_terminal_menu
        )
        open_terminal_btn.pack(side=tk.RIGHT, padx=5)
        
        # Tema - modificado para mostrar temas nativos disponíveis
        theme_frame = ttk.Frame(general_frame, padding=5)
        theme_frame.pack(fill=tk.X)
        
        ttk.Label(theme_frame, text="Tema da Interface:").pack(side=tk.LEFT)
        
        # Combobox para seleção de tema
        self.theme_combo = ttk.Combobox(
            theme_frame, 
            values=available_themes,
            state="readonly",
            width=20
        )
        self.theme_combo.pack(side=tk.LEFT, padx=5)
        
        # Configurar tema atual ou padrão
        current_theme = self.config.get("theme")
        if not current_theme or current_theme not in available_themes:
            # Se não tiver tema ou o tema não estiver disponível, usar 'default' se disponível
            if "default" in available_themes:
                current_theme = "default"
            # Caso contrário usa o tema atual
            elif TTKTHEMES_AVAILABLE:
                current_theme = themed_style.theme_use()
            else:
                current_theme = ttk.Style().theme_use()
        
        self.theme_combo.set(current_theme)
        
        # Vincular evento de mudança do tema
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_changed)
        
        # Seção de Arquivos de Configuração dos Clientes
        from cli.config_util import obter_caminhos_config
        
        client_configs_frame = ttk.LabelFrame(self, text="Arquivos de Configuração dos Clientes")
        client_configs_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Obter caminhos dos arquivos de configuração
        cursor_config_path, claude_config_path = obter_caminhos_config()
        
        # Verificar existência dos arquivos
        cursor_status = "Encontrado" if os.path.exists(cursor_config_path) else "Não encontrado"
        claude_status = "Encontrado" if os.path.exists(claude_config_path) else "Não encontrado"
        
        # Frame para Cursor
        cursor_frame = ttk.Frame(client_configs_frame, padding=5)
        cursor_frame.pack(fill=tk.X)
        
        ttk.Label(cursor_frame, text="Cursor MCP:").pack(side=tk.LEFT)
        cursor_path_text = f"{cursor_config_path} ({cursor_status})"
        cursor_path_label = self._create_link_label(cursor_frame, cursor_path_text, cursor_config_path)
        cursor_path_label.pack(side=tk.LEFT, padx=5)
        
        # Frame para Claude Desktop
        claude_frame = ttk.Frame(client_configs_frame, padding=5)
        claude_frame.pack(fill=tk.X)
        
        ttk.Label(claude_frame, text="Claude Desktop:").pack(side=tk.LEFT)
        claude_path_text = f"{claude_config_path} ({claude_status})"
        claude_path_label = self._create_link_label(claude_frame, claude_path_text, claude_config_path)
        claude_path_label.pack(side=tk.LEFT, padx=5)
    
    def _create_link_label(self, parent, text, path=None):
        """
        Cria um label com estilo de link que abre o arquivo/diretório quando clicado.
        
        Args:
            parent: Widget pai
            text: Texto a ser exibido no label
            path: Caminho a ser aberto (se diferente do texto)
            
        Returns:
            tk.Label: Label com estilo de link
        """
        # Se não for fornecido um caminho específico, usar o texto
        if path is None:
            path = text
            
        # Extrair apenas o caminho do arquivo/diretório a partir do texto
        # (remove a parte de status se existir)
        if " (" in path:
            path = path.split(" (")[0]
        
        # Criar label com estilo de link, usando a cor padrão do tema
        link_label = tk.Label(
            parent,
            text=text,
            cursor="hand2"
        )
        
        # Aplicar sublinhado
        font = link_label.cget("font")
        link_label.configure(font=(font, 9, "underline"))
        
        # Vincular evento de clique
        link_label.bind("<Button-1>", lambda e: self._open_path(path))
        
        return link_label
    
    def _open_path(self, path):
        """
        Abre o arquivo ou diretório no explorador de arquivos.
        
        Args:
            path: Caminho do arquivo ou diretório a ser aberto
        """
        try:
            # Verificar se o arquivo ou diretório existe
            if not os.path.exists(path):
                # Se o arquivo não existir, criar o diretório pai
                parent_dir = os.path.dirname(path)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)
                    
                # Se for um diretório que não existe, criar
                if not os.path.splitext(path)[1]:  # Sem extensão = diretório
                    os.makedirs(path, exist_ok=True)
            
            # Abrir no explorador de arquivos dependendo do sistema operacional
            if sys.platform == 'win32':
                # Windows
                # Se for um arquivo que não existe, abrir o diretório pai
                if not os.path.exists(path) and os.path.splitext(path)[1]:
                    path = os.path.dirname(path)
                
                os.startfile(path)
            elif sys.platform == 'darwin':
                # macOS
                import subprocess
                subprocess.run(['open', path])
            else:
                # Linux/Unix
                import subprocess
                subprocess.run(['xdg-open', path])
        except Exception as e:
            show_error_message("Erro", f"Erro ao abrir o caminho: {str(e)}")
    
    def _show_terminal_menu(self, event=None):
        """
        Mostra um menu de contexto para escolher o tipo de terminal.
        """
        # Criar um menu de contexto
        terminal_menu = tk.Menu(self, tearoff=0)
        terminal_menu.add_command(label="CMD", command=lambda: self._open_venv_terminal("cmd"))
        terminal_menu.add_command(label="PowerShell", command=lambda: self._open_venv_terminal("powershell"))
        
        # Verificar se o Git Bash está instalado - verificar caminhos comuns
        git_bash_paths = [
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Git', 'bin', 'bash.exe'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Git', 'usr', 'bin', 'bash.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Git', 'bin', 'bash.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Git', 'usr', 'bin', 'bash.exe')
        ]
        
        git_bash_path = None
        for path in git_bash_paths:
            if os.path.exists(path):
                git_bash_path = path
                break
        
        if git_bash_path:
            terminal_menu.add_command(label="Git Bash", command=lambda: self._open_venv_terminal("git-bash", git_bash_path))
        
        # Obter widget que acionou o evento (botão)
        widget = event.widget if event else self.winfo_containing(
            self.winfo_pointerx(), self.winfo_pointery()
        )
        
        # Mostrar o menu abaixo do botão
        terminal_menu.tk_popup(
            widget.winfo_rootx(), 
            widget.winfo_rooty() + widget.winfo_height()
        )
    
    def _open_venv_terminal(self, terminal_type="cmd", git_bash_path=None):
        """
        Abre um terminal com o ambiente virtual ativado.
        
        Args:
            terminal_type: Tipo de terminal a ser aberto (cmd, powershell, git-bash)
            git_bash_path: Caminho para o executável do Git Bash (opcional)
        """
        try:
            venv_path = self.config["venv_path"]
            
            if not os.path.exists(venv_path):
                os.makedirs(venv_path, exist_ok=True)
                show_info_message(
                    "Ambiente Virtual", 
                    f"O diretório do ambiente virtual foi criado em: {venv_path}"
                )
            
            # Determinar o caminho do ambiente virtual
            activate_script_win = os.path.join(venv_path, ".venv", "Scripts", "activate.bat")
            activate_script_ps = os.path.join(venv_path, ".venv", "Scripts", "Activate.ps1")
            
            # Verificar se existe uma pasta .venv
            venv_folder = os.path.join(venv_path, ".venv")
            venv_exists = os.path.exists(venv_folder)
            
            # Criar arquivo temporário com script para exibir a mensagem colorida
            uv_warning_script_path = os.path.join(venv_path, ".uv_warning.py")
            with open(uv_warning_script_path, 'w', encoding='utf-8') as f:
                f.write(UV_WARNING_SCRIPT)
            
            # Abrir terminal selecionado
            if terminal_type == "cmd":
                # CMD
                if venv_exists and os.path.exists(activate_script_win):
                    activate_cmd = f'start cmd.exe /K "cd /d "{venv_path}" && "{activate_script_win}" && python .uv_warning.py"'
                else:
                    if venv_exists:
                        show_error_message("Ambiente Virtual", "Pasta .venv encontrada, mas script de ativação não localizado.")
                        activate_cmd = f'start cmd.exe /K "cd /d "{venv_path}" && python .uv_warning.py"'
                    else:
                        show_info_message("Ambiente Virtual", "Ambiente virtual não encontrado. Será necessário criar com 'python -m venv .venv'")
                        activate_cmd = f'start cmd.exe /K "cd /d "{venv_path}" && echo Ambiente virtual nao encontrado. Use python -m venv .venv para criar && python .uv_warning.py"'
                os.system(activate_cmd)
                
            elif terminal_type == "powershell":
                # PowerShell
                if venv_exists and os.path.exists(activate_script_ps):
                    activate_cmd = f'start powershell -NoExit -Command "cd \'{venv_path}\'; & \'{activate_script_ps}\'; python .uv_warning.py"'
                else:
                    if venv_exists:
                        show_error_message("Ambiente Virtual", "Pasta .venv encontrada, mas script de ativação do PowerShell não localizado.")
                        activate_cmd = f'start powershell -NoExit -Command "cd \'{venv_path}\'; python .uv_warning.py"'
                    else:
                        show_info_message("Ambiente Virtual", "Ambiente virtual não encontrado. Será necessário criar com 'python -m venv .venv'")
                        activate_cmd = f'start powershell -NoExit -Command "cd \'{venv_path}\'; Write-Host \'Ambiente virtual nao encontrado. Use python -m venv .venv para criar\'; python .uv_warning.py"'
                os.system(activate_cmd)
                
            elif terminal_type == "git-bash":
                # Git Bash
                if not git_bash_path:
                    # Se não foi passado o caminho, tentar encontrar
                    git_bash_paths = [
                        os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Git', 'bin', 'bash.exe'),
                        os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Git', 'usr', 'bin', 'bash.exe'),
                        os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Git', 'bin', 'bash.exe'),
                        os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Git', 'usr', 'bin', 'bash.exe')
                    ]
                    
                    for path in git_bash_paths:
                        if os.path.exists(path):
                            git_bash_path = path
                            break
                
                if not git_bash_path or not os.path.exists(git_bash_path):
                    show_error_message("Git Bash", "Não foi possível encontrar o Git Bash. Verifique se está instalado.")
                    return
                
                # Ajustar o caminho para o formato Unix (usar barras em vez de contrabarras)
                venv_path_unix = venv_path.replace("\\", "/")
                
                if venv_exists:
                    # Git Bash - tentar ativar ambiente virtual
                    # Encontrar o script de ativação bash
                    bash_activate = os.path.join(venv_path, ".venv", "Scripts", "activate")
                    
                    # Ajustar caminho para formato Unix
                    bash_activate_unix = bash_activate.replace("\\", "/")
                    
                    if os.path.exists(bash_activate):
                        cmd = f'start "" "{git_bash_path}" --login -i -c "cd \'{venv_path_unix}\' && source \'{bash_activate_unix}\' && python .uv_warning.py; exec bash"'
                    else:
                        cmd = f'start "" "{git_bash_path}" --login -i -c "cd \'{venv_path_unix}\' && echo \'Ambiente virtual encontrado, mas script de ativação para Bash não localizado.\' && python .uv_warning.py; exec bash"'
                else:
                    cmd = f'start "" "{git_bash_path}" --login -i -c "cd \'{venv_path_unix}\' && echo \'Ambiente virtual não encontrado. Use python -m venv .venv para criar.\' && python .uv_warning.py; exec bash"'
                
                print(f"Executando comando: {cmd}")  # Debug
                result = os.system(cmd)
                print(f"Resultado da execução: {result}")  # Debug
                
            else:
                # Sistema não suportado ou terminal não reconhecido
                show_error_message("Erro", f"Tipo de terminal não suportado: {terminal_type}")
                
        except Exception as e:
            show_error_message("Erro", f"Erro ao abrir terminal com ambiente virtual: {str(e)}")
    
    def _on_theme_changed(self, event=None):
        """
        Manipula o evento de mudança do tema.
        Aplica o tema imediatamente ao ser selecionado.
        """
        selected_theme = self.theme_combo.get()
        self.config["theme"] = selected_theme
        self._apply_theme(selected_theme)
        self._save_config()
    
    def _apply_theme(self, theme_name):
        """
        Aplica o tema selecionado à interface.
        
        Args:
            theme_name: Nome do tema a ser aplicado
        """
        try:
            if TTKTHEMES_AVAILABLE:
                # Usar ThemedStyle para acessar temas adicionais
                themed_style = ThemedStyle(self.master)
                available_themes = themed_style.theme_names()
                
                if theme_name in available_themes:
                    themed_style.set_theme(theme_name)
                    show_info_message(
                        "Tema Alterado", 
                        f"Tema '{theme_name}' aplicado com sucesso."
                    )
                else:
                    show_error_message(
                        "Tema não disponível", 
                        f"O tema '{theme_name}' não está disponível.\nTemas disponíveis: {', '.join(available_themes)}"
                    )
            else:
                # Usar apenas os temas nativos do ttk
                style = ttk.Style()
                available_themes = style.theme_names()
                
                if theme_name in available_themes:
                    style.theme_use(theme_name)
                    show_info_message(
                        "Tema Alterado", 
                        f"Tema '{theme_name}' aplicado com sucesso."
                    )
                else:
                    show_error_message(
                        "Tema não disponível", 
                        f"O tema '{theme_name}' não está disponível nesta instalação.\nTemas disponíveis: {', '.join(available_themes)}"
                    )
        except Exception as e:
            show_error_message(
                "Erro ao aplicar tema", 
                f"Não foi possível aplicar o tema '{theme_name}': {str(e)}"
            )
    
    def _reset_settings(self):
        """
        Restaura as configurações para os valores padrão.
        """
        # Configurações padrão
        self.config = {
            "python_path": sys.executable,
            "log_dir": os.path.join(Path(__file__).resolve().parent.parent, "logs"),
            "data_dir": os.path.join(Path(__file__).resolve().parent.parent, "data"),
            "venv_path": os.path.join(Path(__file__).resolve().parent.parent, "mcp_server"),
            "theme": "default"  # Usando 'default' como tema padrão
        }
        
        # Atualizar componentes visuais
        if "default" in ttk.Style().theme_names():
            self.theme_combo.set("default")
            self._apply_theme("default")
        
        # Informar usuário
        show_info_message("Configurações", "Configurações restauradas para os valores padrão.")

# Função para testar o módulo individualmente
def main():
    """Função principal para teste do módulo."""
    root = tk.Tk()
    root.title("Gerenciador de Configurações MCP")
    
    # Configurar estilo
    style = ttk.Style()
    style.theme_use("clam")  # Usa um tema mais moderno
    
    # Configurar estilos personalizados
    style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground="#1E88E5")
    style.configure("Card.TFrame", background="white", relief="raised", borderwidth=1)
    
    # Criar e adicionar o gerenciador de configurações
    config_manager = ConfigManager(root)
    config_manager.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Dimensões da janela
    root.geometry("800x600")
    root.mainloop()

if __name__ == "__main__":
    main()
