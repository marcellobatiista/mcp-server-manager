"""
Aplicação principal da interface gráfica do MCP Server.

Este módulo contém a classe principal da aplicação e o ponto de entrada
para a interface gráfica.
"""
import os
import sys
import tkinter as tk
import subprocess
import threading
import time
import platform
import json
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
import re

# Adiciona o diretório raiz ao sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Importa utilitários da GUI
from gui.utils import (
    COLORS, 
    center_window, 
    apply_default_styles,
    show_error_message,
    show_info_message,
    ask_yes_no,
    show_options_dialog,
    extract_mcp_tools,
    extract_mcp_resources,
    extract_mcp_prompts
)

# Importa o gerenciador de servidores
from gui.server_manager import ServerManager, Server, ServerStatus
from gui.config_manager import ConfigManager

# Importa utilitário de configuração
from cli import config_util

class MCPServerGUI(tk.Tk):
    """Classe principal da aplicação GUI para o MCP Server."""
    
    def __init__(self):
        """Inicializa a aplicação."""
        super().__init__()
        
        # Configuração básica da janela
        self.title("MCP Server Manager")
        self.minsize(800, 600)
        
        # Definir ícone da aplicação (se existir)
        icon_path = Path(__file__).resolve().parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))
        
        # Centralizar a janela
        center_window(self, 1024, 768)
        
        # Maximizar a janela ao iniciar
        if os.name == 'nt':  # Windows
            self.state('zoomed')
        else:  # Linux/macOS
            self.attributes('-zoomed', True)
        
        # Verificar se o ambiente virtual está configurado
        if not self.check_venv_exists():
            # Não seguimos com a inicialização normal se o ambiente não está configurado
            self.after(100, self.ask_to_setup_environment)
            return
        
        # Inicialização normal da aplicação
        self._init_application()
    
    def _init_application(self):
        """Inicializa o restante da aplicação após verificação do ambiente."""
        # Inicializar gerenciador de servidores
        self.server_manager = ServerManager()
        
        # Registrar callbacks de eventos
        self.server_manager.on_server_status_changed = self.on_server_status_changed
        self.server_manager.on_log_added = self.on_log_added
        
        # Carregar configurações
        self._load_app_config()
        
        # Configurar estilos e tema
        self.style = apply_default_styles(self)
        self._apply_theme_from_config()
        
        # Criar o menu principal
        self.create_menu()
        
        # Criar a estrutura principal da interface
        self.create_main_frame()
        
        # Configurar o gerenciador de abas
        self.create_notebook()
        
        # Carregar inicialmente a lista de servidores (sem verificar status)
        self.populate_servers_list()
        
        # Configurar manipuladores de eventos
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Atualizar contadores
        self.update_server_count()
        
        # Iniciar o verificador de status em background
        self.should_check_status = True
        self.status_check_thread = threading.Thread(target=self._background_status_checker, daemon=True)
        self.status_check_thread.start()
    
    def populate_servers_list(self):
        """Popula a lista de servidores com informações básicas, sem verificar status."""
        # Limpar a lista
        for item in self.servers_tree.get_children():
            self.servers_tree.delete(item)
        
        # Adicionar servidores à lista
        servers = self.server_manager.get_all_servers()
        for server in servers:
            self.servers_tree.insert(
                "", 
                "end", 
                values=(
                    server.name, 
                    server.status, 
                    os.path.basename(server.script_path)
                )
            )
        
        # Selecionar o primeiro item da lista, se houver algum
        if self.servers_tree.get_children():
            first_item = self.servers_tree.get_children()[0]
            self.servers_tree.selection_set(first_item)
            self.servers_tree.focus_set()
            self.servers_tree.focus(first_item)
            # Disparar manualmente o evento de seleção para atualizar os detalhes
            self.on_server_selected(None)
            
        # Mostrar mensagem na barra de status
        self.update_status(f"Carregados {len(servers)} servidores")
    
    def _background_status_checker(self):
        """Função que roda em background para verificar periodicamente o status dos servidores."""
        try:
            # Primeiro espere um pouco mais para a interface terminar de carregar completamente
            time.sleep(2.5)
            
            # Faça a primeira verificação (com um pequeno atraso)
            self.after(100, self.refresh_servers)
            
            # Loop de verificação periódica
            while self.should_check_status:
                # Espera 20 segundos entre verificações (aumentar o intervalo reduz o impacto)
                time.sleep(20)
                
                # Executa a verificação na thread principal usando after com um atraso maior
                # Usar 300ms ajuda a garantir que a interface não travará
                self.after(300, self.refresh_servers)
        except Exception as e:
            print(f"Erro no verificador de status: {str(e)}")
    
    def _load_app_config(self):
        """Carrega as configurações da aplicação."""
        self.app_config = {}
        config_file = os.path.join(Path(__file__).resolve().parent.parent, "config", "app_config.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.app_config = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configurações: {str(e)}")
    
    def _apply_theme_from_config(self):
        """Aplica o tema definido nas configurações."""
        theme = self.app_config.get("theme")
        
        if not theme:
            return  # Usar o tema padrão se não estiver configurado
        
        try:
            # Tentar importar ThemedStyle se o ttkthemes estiver disponível
            try:
                from ttkthemes import ThemedStyle
                themed_style = ThemedStyle(self)
                if theme in themed_style.theme_names():
                    themed_style.set_theme(theme)
                    return
            except ImportError:
                pass  # Continuar com os temas padrão se ttkthemes não estiver disponível
            
            # Tentar usar os temas padrão do ttk
            if theme in self.style.theme_names():
                self.style.theme_use(theme)
        except Exception as e:
            print(f"Erro ao aplicar tema '{theme}': {str(e)}")
    
    def check_venv_exists(self):
        """
        Verifica se o ambiente virtual existe e se as dependências necessárias estão instaladas.
        
        Returns:
            bool: True se o ambiente virtual existir e as dependências estiverem instaladas, False caso contrário
        """
        # Obter caminho do projeto a partir do log.txt se existir
        log_paths = [
            "log.txt",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log.txt")
        ]
        
        project_path = None
        for log_path in log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        log_content = f.read()
                        # Procurar o caminho do projeto no log
                        for line in log_content.splitlines():
                            if "Caminho do Projeto:" in line:
                                project_path = line.split("Caminho do Projeto:")[1].strip()
                                break
                except:
                    pass
        
        # Se não encontrou o caminho do projeto, usa o diretório atual
        if not project_path:
            project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Verifica se existe o diretório .venv no caminho do projeto
        venv_path = os.path.join(project_path, ".venv")
        venv_exists = os.path.exists(venv_path) and os.path.isdir(venv_path)
        
        # Verifica se as dependências estão instaladas
        deps_installed = self.check_dependencies()
        
        return venv_exists and deps_installed
    
    def check_dependencies(self):
        """
        Verifica se as dependências necessárias estão instaladas.
        
        Returns:
            bool: True se todas as dependências estiverem instaladas, False caso contrário
        """
        required_modules = ['tkinter', 'rich', 'psutil']
        missing_modules = []
        
        for module in required_modules:
            try:
                if module == 'tkinter':
                    # tkinter já está importado se este código está rodando
                    continue
                
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            messagebox.showwarning(
                "Dependências faltando",
                f"Os seguintes módulos Python são necessários mas não estão instalados: {', '.join(missing_modules)}\n\n"
                "Execute o Quick Setup para instalar todas as dependências."
            )
            return False
        
        return True
    
    def ask_to_setup_environment(self):
        """
        Pergunta ao usuário se deseja configurar o ambiente virtual e executa o quick_setup.py
        """
        # Obter caminho do projeto
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        venv_path = os.path.join(project_dir, ".venv")
        
        # Criar uma janela de diálogo personalizada
        dialog = tk.Toplevel(self)
        dialog.title("Ambiente não configurado")
        dialog.geometry("500x300")
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.grab_set()  # Torna o diálogo modal
        
        # Centralizar a janela
        center_window(dialog)
        
        # Conteúdo da janela
        content_frame = ttk.Frame(dialog, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            content_frame, 
            text="Ambiente Virtual não encontrado", 
            style="Title.TLabel"
        )
        title_label.pack(pady=(0, 10))
        
        # Mensagem
        message_text = (
            "O ambiente virtual necessário não foi encontrado.\n\n"
            "Para usar todas as funcionalidades deste aplicativo, é necessário executar a configuração inicial "
            "que irá criar e configurar o ambiente virtual com todas as dependências necessárias.\n\n"
            f"Caminho esperado do ambiente virtual:\n{venv_path}"
        )
        
        message_label = ttk.Label(
            content_frame, 
            text=message_text,
            wraplength=460,
            justify="left"
        )
        message_label.pack(pady=(0, 20))
        
        # Botões
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(fill=tk.X)
        
        # Função para abrir o diretório do projeto
        def open_project_dir():
            if os.name == 'nt':  # Windows
                os.startfile(project_dir)
            else:  # Linux/macOS
                subprocess.Popen(['xdg-open', project_dir])
        
        # Botão para abrir o diretório do projeto
        open_dir_button = ttk.Button(
            buttons_frame,
            text="Abrir diretório do projeto",
            command=open_project_dir
        )
        open_dir_button.pack(side=tk.LEFT, padx=5)
        
        # Função para continuar sem configurar
        def continue_without_setup():
            messagebox.showwarning(
                "Aviso",
                "Sem o ambiente virtual configurado, algumas funcionalidades podem não funcionar corretamente."
            )
            dialog.destroy()
            # Inicialize a aplicação normalmente
            self._init_application()
        
        # Botão para ignorar
        ignore_button = ttk.Button(
            buttons_frame,
            text="Continuar sem configurar",
            command=continue_without_setup
        )
        ignore_button.pack(side=tk.RIGHT, padx=5)
        
        # Função para executar o setup
        def run_setup():
            dialog.destroy()
            self.run_quick_setup()
        
        # Botão para executar quick_setup
        setup_button = ttk.Button(
            buttons_frame,
            text="Executar Quick Setup",
            command=run_setup,
            style="Primary.TButton"
        )
        setup_button.pack(side=tk.RIGHT, padx=5)
        
        # Espera até que o diálogo seja fechado
        self.wait_window(dialog)
    
    def run_quick_setup(self):
        """
        Executa o script quick_setup.py
        """
        try:
            # Obter caminho do projeto
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            quick_setup_path = os.path.join(project_dir, "quick_setup.py")
            
            # Verificar se o arquivo existe
            if not os.path.exists(quick_setup_path):
                messagebox.showerror(
                    "Erro",
                    f"O arquivo quick_setup.py não foi encontrado em: {quick_setup_path}"
                )
                return
            
            # Obter caminho do python
            python_exe = sys.executable
            
            # Executar o quick_setup.py em um processo separado
            messagebox.showinfo(
                "Configuração",
                "O script de configuração será executado em uma janela separada.\n"
                "Aguarde a conclusão antes de continuar."
            )
            
            # Configuração específica do sistema operacional
            command = None
            if os.name == 'nt':  # Windows
                command = [python_exe, quick_setup_path]
                creation_flags = subprocess.CREATE_NEW_CONSOLE
            else:  # Linux/macOS
                command = ['xterm', '-e', python_exe, quick_setup_path]
                creation_flags = 0
            
            # Informação para o usuário
            result = messagebox.askokcancel(
                "Configuração",
                "Após a execução do Quick Setup, a aplicação será fechada.\n"
                "Você deverá reiniciá-la manualmente após a conclusão da configuração.\n\n"
                "Deseja continuar?"
            )
            
            if result:
                # Executar o quick_setup.py em um processo separado
                if os.name == 'nt':  # Windows
                    subprocess.Popen(command, creationflags=creation_flags)
                else:  # Linux/macOS
                    subprocess.Popen(command)
                
                # Encerra a aplicação de forma segura
                self.quit()
                
        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Ocorreu um erro ao executar o Quick Setup: {str(e)}"
            )
    
    def create_menu(self):
        """Cria o menu principal da aplicação."""
        menubar = tk.Menu(self)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Configurações", command=self.open_settings)
        file_menu.add_command(label="Executar Quick Setup", command=self.run_quick_setup)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.on_closing)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        
        # Menu Servidores
        server_menu = tk.Menu(menubar, tearoff=0)
        server_menu.add_command(label="Adicionar Servidor", command=self.add_server)
        menubar.add_cascade(label="Servidores", menu=server_menu)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Documentação", command=self.open_documentation)
        help_menu.add_command(label="Sobre", command=self.show_about)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        
        self.config(menu=menubar)
    
    def create_main_frame(self):
        """Cria o frame principal da aplicação."""
        # Frame principal com padding
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título da aplicação
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame, 
            text="MCP Server Manager", 
            style="Title.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        # Frame da barra de status
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        self.status_label = ttk.Label(
            self.status_frame, 
            text="Pronto", 
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def create_notebook(self):
        """Cria o gerenciador de abas (notebook)."""
        # Frame para o notebook
        notebook_frame = ttk.Frame(self.main_frame)
        notebook_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Criar o notebook (abas)
        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Criar abas
        self.servers_tab = ttk.Frame(self.notebook)
        self.logs_tab = ttk.Frame(self.notebook)
        self.config_tab = ttk.Frame(self.notebook)
        
        # Adicionar abas ao notebook
        self.notebook.add(self.servers_tab, text="Servidores")
        self.notebook.add(self.logs_tab, text="Logs")
        self.notebook.add(self.config_tab, text="Configurações")
        
        # Configurar abas
        self.setup_logs_tab()  # Configurar a aba de logs primeiro para garantir que self.logs_text exista
        self.setup_config_tab()
        self.setup_servers_tab()  # Mover para o final para que refresh_servers possa usar logs_text
    
    def setup_servers_tab(self):
        """Configura a aba de gerenciamento de servidores."""
        # Frame principal da aba
        servers_frame = ttk.Frame(self.servers_tab, padding="10")
        servers_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título da seção
        servers_title = ttk.Label(
            servers_frame, 
            text="Servidores MCP", 
            style="Subtitle.TLabel"
        )
        servers_title.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Botões de ação principais
        actions_frame = ttk.Frame(servers_frame)
        actions_frame.grid(row=0, column=1, sticky="e", pady=(0, 10))
        
        add_button = ttk.Button(
            actions_frame, 
            text="Adicionar Servidor", 
            command=self.add_server
        )
        add_button.pack(side=tk.LEFT, padx=5)
        
        import_button = ttk.Button(
            actions_frame, 
            text="Importar Servidor", 
            command=self.import_server
        )
        import_button.pack(side=tk.LEFT, padx=5)
        
        # Contador de servidores ativos
        self.active_servers_label = ttk.Label(actions_frame, text="Servidores ativos: 0")
        self.active_servers_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Lista de servidores
        servers_container = ttk.Frame(servers_frame)
        servers_container.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        
        # Configurar coluna e linha para expandir
        servers_frame.columnconfigure(0, weight=3)
        servers_frame.columnconfigure(1, weight=1)
        servers_frame.rowconfigure(1, weight=1)
        
        # Criar Treeview para a lista de servidores
        columns = ("name", "status", "script")
        self.servers_tree = ttk.Treeview(
            servers_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Configurar cabeçalhos
        self.servers_tree.heading("name", text="Nome")
        self.servers_tree.heading("status", text="Status")
        self.servers_tree.heading("script", text="Script")
        
        # Configurar colunas
        self.servers_tree.column("name", width=150, anchor=tk.CENTER)
        self.servers_tree.column("status", width=100, anchor=tk.CENTER)
        self.servers_tree.column("script", width=300, anchor=tk.CENTER)
        
        # Adicionar scrollbar
        scrollbar_y = ttk.Scrollbar(
            servers_container, 
            orient="vertical", 
            command=self.servers_tree.yview
        )
        self.servers_tree.configure(yscrollcommand=scrollbar_y.set)
        
        # Posicionar elementos
        self.servers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Vincular eventos de seleção
        self.servers_tree.bind("<<TreeviewSelect>>", self.on_server_selected)
        
        # Painel de detalhes do servidor
        details_frame = ttk.LabelFrame(servers_frame, text="Detalhes do Servidor")
        details_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        # Botões de ação para o servidor selecionado
        server_actions_frame = ttk.Frame(details_frame)
        server_actions_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(
            server_actions_frame, 
            text="Iniciar", 
            command=self.start_selected_server,
            state=tk.DISABLED
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            server_actions_frame, 
            text="Parar", 
            command=self.stop_selected_server,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.restart_button = ttk.Button(
            server_actions_frame, 
            text="Reiniciar", 
            command=self.restart_selected_server,
            state=tk.DISABLED
        )
        self.restart_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_button = ttk.Button(
            server_actions_frame, 
            text="Editar", 
            command=self.edit_selected_server,
            state=tk.DISABLED
        )
        self.edit_button.pack(side=tk.LEFT, padx=5)
        
        self.remove_button = ttk.Button(
            server_actions_frame, 
            text="Remover", 
            command=self.remove_selected_server,
            state=tk.DISABLED,
            style="Danger.TButton"
        )
        self.remove_button.pack(side=tk.RIGHT, padx=5)
        
        # Dados do servidor
        server_details_frame = ttk.Frame(details_frame)
        server_details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Linha 1: Nome e Status
        row1 = ttk.Frame(server_details_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="Nome:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.server_name_label = ttk.Label(row1, text="-")
        self.server_name_label.grid(row=0, column=1, sticky="w", padx=(0, 20))
        
        ttk.Label(row1, text="Status:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.server_status_label = ttk.Label(row1, text="-")
        self.server_status_label.grid(row=0, column=3, sticky="w")
        
        # Linha 2: Script e Porta
        row2 = ttk.Frame(server_details_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(row2, text="Script:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.server_script_label = ttk.Label(row2, text="-")
        self.server_script_label.grid(row=0, column=1, sticky="w", columnspan=3)
        
        # Linha 3: Arquivo de Configuração e Porta
        row3 = ttk.Frame(server_details_frame)
        row3.pack(fill=tk.X, pady=2)
        
        ttk.Label(row3, text="Diretório:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.server_config_label = ttk.Label(row3, text="-")
        self.server_config_label.grid(row=0, column=1, sticky="w")
        
        # Linha 4: Botão de Ferramentas
        row4 = ttk.Frame(server_details_frame)
        row4.pack(fill=tk.X, pady=5)
        
        self.tools_button = ttk.Button(
            row4, 
            text="Ferramentas", 
            command=self.show_server_tools,
            state=tk.DISABLED
        )
        self.tools_button.pack(side=tk.LEFT)
        
        # Botão de Recursos
        self.resources_button = ttk.Button(
            row4, 
            text="Recursos", 
            command=self.show_server_resources,
            state=tk.DISABLED
        )
        self.resources_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Botão de Prompts
        self.prompts_button = ttk.Button(
            row4, 
            text="Prompts", 
            command=self.show_server_prompts,
            state=tk.DISABLED
        )
        self.prompts_button.pack(side=tk.LEFT, padx=(5, 0))
    
    def setup_logs_tab(self):
        """Configura a aba de logs."""
        log_frame = ttk.Frame(self.logs_tab, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título da seção
        logs_title = ttk.Label(
            log_frame, 
            text="Logs do Sistema", 
            style="Subtitle.TLabel"
        )
        logs_title.pack(anchor=tk.W, pady=(0, 10))
        
        # Área de texto para logs com scrollbar
        logs_container = ttk.Frame(log_frame)
        logs_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(logs_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.logs_text = tk.Text(
            logs_container, 
            wrap=tk.WORD, 
            yscrollcommand=scrollbar.set,
            bg="white",
            fg=COLORS["text"],
            font=("Consolas", 10)
        )
        self.logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.logs_text.yview)
        
        # Botões de controle
        buttons_frame = ttk.Frame(log_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        clear_button = ttk.Button(
            buttons_frame, 
            text="Limpar Logs", 
            command=self.clear_logs
        )
        clear_button.pack(side=tk.LEFT)
        
        refresh_button = ttk.Button(
            buttons_frame, 
            text="Atualizar", 
            command=self.refresh_logs
        )
        refresh_button.pack(side=tk.LEFT, padx=(5, 0))
        
        export_button = ttk.Button(
            buttons_frame, 
            text="Exportar Logs", 
            command=self.export_logs
        )
        export_button.pack(side=tk.RIGHT)
    
    def setup_config_tab(self):
        """Configura a aba de configurações."""
        # Adiciona o gerenciador de configurações
        self.config_manager = ConfigManager(self.config_tab)
        self.config_manager.pack(fill=tk.BOTH, expand=True)
    
    def on_server_selected(self, event):
        """Manipula o evento de seleção de um servidor na lista."""
        selection = self.servers_tree.selection()
        if not selection:
            # Nenhum item selecionado, desabilitar botões
            self.update_server_details(None)
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)
            self.edit_button.config(state=tk.DISABLED)
            self.remove_button.config(state=tk.DISABLED)
            self.tools_button.config(state=tk.DISABLED)
            self.resources_button.config(state=tk.DISABLED)
            self.prompts_button.config(state=tk.DISABLED)
            return
        
        # Obter o servidor selecionado
        item = self.servers_tree.item(selection[0])
        server_name = item["values"][0]
        server = self.server_manager.get_server(server_name)
        
        if server:
            # Atualizar detalhes do servidor
            self.update_server_details(server)
            
            # Habilitar/desabilitar botões com base no status
            if server.status == ServerStatus.RUNNING:
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                self.restart_button.config(state=tk.NORMAL)
            elif server.status == ServerStatus.STOPPED:
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.restart_button.config(state=tk.DISABLED)
            else:  # STARTING, STOPPING ou ERROR
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.DISABLED)
                self.restart_button.config(state=tk.DISABLED)
            
            # Sempre habilitar botões de edição, remoção, ferramentas, recursos e prompts
            self.edit_button.config(state=tk.NORMAL)
            self.remove_button.config(state=tk.NORMAL)
            self.tools_button.config(state=tk.NORMAL)
            self.resources_button.config(state=tk.NORMAL)
            self.prompts_button.config(state=tk.NORMAL)
    
    def update_server_details(self, server):
        """Atualiza as informações de detalhes do servidor selecionado."""
        if server:
            self.server_name_label.config(text=server.name)
            self.server_status_label.config(text=server.status)
            self.server_script_label.config(text=server.script_path)
            
            # Obter o diretório do ambiente virtual (diretório pai do script)
            venv_dir = os.path.dirname(server.script_path) if server.script_path else "-"
            self.server_config_label.config(text=venv_dir)
        else:
            self.server_name_label.config(text="-")
            self.server_status_label.config(text="-")
            self.server_script_label.config(text="-")
            self.server_config_label.config(text="-")
    
    def refresh_servers(self):
        """Atualiza a lista de servidores."""
        # Usar uma thread separada para verificar status
        def check_status_thread():
            try:
                # Verificar o status atual dos processos dos servidores
                changes = self.server_manager.check_servers_status()
                
                # Atualizar a interface na thread principal usando after com um pequeno atraso
                # para dar tempo para o sistema processar outras mensagens da interface
                self.after(100, lambda: self._update_servers_ui(changes))
            except Exception as e:
                print(f"Erro ao verificar status: {str(e)}")
        
        # Indicar visualmente que a atualização está em andamento
        self.update_status("Verificando status dos servidores...")
        
        # Usar uma prioridade muito baixa para esta thread
        thread = threading.Thread(target=check_status_thread, daemon=True)
        thread.start()
    
    def _update_servers_ui(self, changes):
        """Atualiza a interface com base nas mudanças de status detectadas."""
        # Guardar a seleção atual antes de limpar a lista
        current_selection = None
        selection = self.servers_tree.selection()
        if selection:
            item = self.servers_tree.item(selection[0])
            if "values" in item and len(item["values"]) > 0:
                current_selection = item["values"][0]  # Nome do servidor selecionado
        
        # Se houve mudanças no status, registrar no log
        if changes:
            for server_name, old_status, new_status in changes:
                self.log(f"Status do servidor '{server_name}' atualizado: {old_status} → {new_status}")
            
            # Mostrar mensagem de status mais detalhada
            if len(changes) == 1:
                server_name, old_status, new_status = changes[0]
                status_msg = f"Atualização: Servidor '{server_name}' mudou de '{old_status}' para '{new_status}'"
                self.update_status(status_msg)
            else:
                # Listar todos os servidores que mudaram de status
                status_msg = "Atualização: Servidores com status alterado: "
                for i, (server_name, old_status, new_status) in enumerate(changes):
                    if i > 0:
                        status_msg += ", "
                    status_msg += f"'{server_name}' ({old_status} → {new_status})"
                self.update_status(status_msg)
                
            # Apenas atualizar a interface se houve mudanças no status
            self._refresh_servers_tree(current_selection)
        else:
            # Se não houve mudanças, apenas atualizar a barra de status sem reconstruir a árvore
            current_time = datetime.now().strftime("%H:%M:%S")
            self.update_status(f"Status verificado às {current_time}")
    
    def _refresh_servers_tree(self, current_selection=None):
        """Atualiza a árvore de servidores preservando a seleção atual."""
        # Limpar a lista
        for item in self.servers_tree.get_children():
            self.servers_tree.delete(item)
        
        # Adicionar servidores à lista
        servers = self.server_manager.get_all_servers()
        server_items = {}  # Mapear nome do servidor para o item na árvore
        
        for server in servers:
            item_id = self.servers_tree.insert(
                "", 
                "end", 
                values=(
                    server.name, 
                    server.status, 
                    os.path.basename(server.script_path)
                )
            )
            server_items[server.name] = item_id
        
        # Restaurar a seleção anterior se o servidor ainda existe na lista
        if current_selection and current_selection in server_items:
            item_to_select = server_items[current_selection]
            # Selecionar o item
            self.servers_tree.selection_set(item_to_select)
            self.servers_tree.focus_set()
            self.servers_tree.focus(item_to_select)
            # Disparar manualmente o evento de seleção para atualizar os detalhes
            self.on_server_selected(None)
        # Se não temos uma seleção anterior ou o servidor foi removido, selecionar o primeiro se houver algum
        elif self.servers_tree.get_children():
            first_item = self.servers_tree.get_children()[0]
            self.servers_tree.selection_set(first_item)
            self.servers_tree.focus_set()
            self.servers_tree.focus(first_item)
            # Disparar manualmente o evento de seleção para atualizar os detalhes
            self.on_server_selected(None)
        
        # Atualizar contagem
        self.update_server_count()
    
    def update_server_count(self):
        """Atualiza o contador de servidores ativos."""
        active_count = sum(1 for server in self.server_manager.get_all_servers() 
                           if server.status == ServerStatus.RUNNING)
        self.active_servers_label.config(text=f"Servidores ativos: {active_count}")
    
    def on_server_status_changed(self, server_name, status):
        """Callback chamado quando o status de um servidor muda."""
        # Atualizar imediatamente o status visual na árvore
        server = self.server_manager.get_server(server_name)
        if server:
            # Atualizar o item na árvore
            for item_id in self.servers_tree.get_children():
                item = self.servers_tree.item(item_id)
                if item["values"] and item["values"][0] == server_name:
                    # Atualiza o valor do status diretamente na árvore
                    self.servers_tree.item(item_id, values=(
                        server_name,
                        status,
                        os.path.basename(server.script_path)
                    ))
                    # Se este é o item selecionado, atualizar os detalhes
                    if self.servers_tree.selection() and self.servers_tree.selection()[0] == item_id:
                        self.update_server_details(server)
                        self.on_server_selected(None)  # Atualizar estado dos botões
                    break
        
        # Atualizar a contagem de servidores ativos
        self.update_server_count()
        
        # Registrar no log
        self.log(f"Servidor '{server_name}' mudou para status '{status}'")
        
        # Atualizar a barra de status
        self.update_status(f"Servidor '{server_name}' agora está '{status}'")
    
    def on_log_added(self, server_name, log_entry):
        """Callback chamado quando um log é adicionado a um servidor."""
        # Adicionar ao log geral
        self.log(f"[{server_name}] {log_entry}")
    
    def start_selected_server(self):
        """Inicia o servidor selecionado."""
        selection = self.servers_tree.selection()
        if not selection:
            return
        
        item = self.servers_tree.item(selection[0])
        server_name = item["values"][0]
        
        # Iniciar servidor
        if self.server_manager.start_server(server_name):
            # Atualizar status na barra
            self.update_status(f"Iniciando servidor '{server_name}'...")
            
            # Atualizar imediatamente o status visual na árvore
            server = self.server_manager.get_server(server_name)
            if server:
                # Atualizar o item na árvore
                for item_id in self.servers_tree.get_children():
                    item = self.servers_tree.item(item_id)
                    if item["values"][0] == server_name:
                        # Atualiza o valor do status diretamente na árvore
                        self.servers_tree.item(item_id, values=(
                            server_name,
                            server.status,
                            os.path.basename(server.script_path)
                        ))
                        # Atualizar detalhes do servidor na parte inferior da interface
                        self.update_server_details(server)
                        # Atualizar estado dos botões
                        self.on_server_selected(None)
                        break
    
    def stop_selected_server(self):
        """Para o servidor selecionado."""
        selection = self.servers_tree.selection()
        if not selection:
            return
        
        item = self.servers_tree.item(selection[0])
        server_name = item["values"][0]
        server = self.server_manager.get_server(server_name)
        
        if not server:
            self.update_status(f"Servidor '{server_name}' não encontrado")
            return
        
        # Verificar se o servidor está em execução
        if server.status not in [ServerStatus.RUNNING, ServerStatus.STARTING]:
            show_info_message(
                "Informação", 
                f"O servidor '{server_name}' não está em execução."
            )
            return
        
        # Confirmar encerramento
        if not ask_yes_no("Encerrar Servidor", 
                          f"Tem certeza que deseja encerrar o servidor '{server_name}'?"):
            return
        
        # Mostrar indicador visual de processo sendo encerrado
        self.update_status(f"Encerrando servidor '{server_name}'...")
        
        # Atualizar estado visual do servidor na árvore
        for item_id in self.servers_tree.get_children():
            item = self.servers_tree.item(item_id)
            if item["values"][0] == server_name:
                self.servers_tree.item(item_id, tags=("stopping",))
                break
        
        # Parar servidor no gerenciador
        if self.server_manager.stop_server(server_name):
            self.log(f"Iniciando encerramento do servidor '{server_name}'...")
        else:
            self.update_status(f"Não foi possível encerrar o servidor '{server_name}'")
    
    def restart_selected_server(self):
        """Reinicia o servidor selecionado."""
        selection = self.servers_tree.selection()
        if not selection:
            return
        
        item = self.servers_tree.item(selection[0])
        server_name = item["values"][0]
        server = self.server_manager.get_server(server_name)
        
        if not server:
            self.update_status(f"Servidor '{server_name}' não encontrado")
            return
        
        # Verificar se o servidor está em execução
        if server.status not in [ServerStatus.RUNNING, ServerStatus.STARTING]:
            # Se não estiver em execução, perguntar se deseja iniciar
            if ask_yes_no("Iniciar Servidor", 
                        f"O servidor '{server_name}' não está em execução. Deseja iniciá-lo?"):
                return self.start_selected_server()
            return
        
        # Confirmar reinicialização
        if not ask_yes_no("Reiniciar Servidor", 
                        f"Tem certeza que deseja reiniciar o servidor '{server_name}'?"):
            return
        
        # Mostrar indicador visual de reinicialização
        self.update_status(f"Reiniciando servidor '{server_name}'...")
        
        # Atualizar estado visual do servidor na árvore
        for item_id in self.servers_tree.get_children():
            item = self.servers_tree.item(item_id)
            if item["values"][0] == server_name:
                self.servers_tree.item(item_id, tags=("stopping",))
                break
        
        # Iniciar thread para reiniciar o servidor (para não bloquear a interface)
        thread = threading.Thread(
            target=self._restart_server_thread,
            args=(server_name,),
            daemon=True
        )
        thread.start()
    
    def _restart_server_thread(self, server_name):
        """
        Thread para reiniciar o servidor sem bloquear a interface.
        Segue uma abordagem similar ao método reiniciar_servidor do launcher.py.
        """
        server = self.server_manager.get_server(server_name)
        if not server:
            self.update_status(f"Erro: Servidor '{server_name}' não encontrado")
            return
        
        try:
            # Registrar nos logs
            self.log(f"Iniciando reinicialização do servidor '{server_name}'...")
            
            # 1. Parar o servidor
            if not self.server_manager.stop_server(server_name):
                self.update_status(f"Erro ao parar o servidor '{server_name}' para reinicialização")
                return
            
            # 2. Aguardar o servidor parar completamente
            max_attempts = 30  # 30 * 0.2 = 6 segundos máximo
            for attempt in range(max_attempts):
                server = self.server_manager.get_server(server_name)  # Atualizar estado
                if server.status == ServerStatus.STOPPED:
                    break
                time.sleep(0.2)
            
            # Se ainda não parou, registrar aviso
            if server.status != ServerStatus.STOPPED:
                self.log(f"Aviso: Servidor '{server_name}' não parou completamente após {max_attempts * 0.2} segundos")
            
            # 3. Iniciar o servidor novamente após uma pequena pausa
            time.sleep(0.5)  # Pequena pausa para garantir que tudo foi encerrado
            
            # 4. Atualizar o status visual
            self.update_status(f"Reiniciando servidor '{server_name}'...")
            
            # 5. Iniciar o servidor
            for item_id in self.servers_tree.get_children():
                item = self.servers_tree.item(item_id)
                if item["values"][0] == server_name:
                    self.servers_tree.item(item_id, tags=("starting",))
                    break
            
            if self.server_manager.start_server(server_name):
                self.log(f"Servidor '{server_name}' reiniciado com sucesso")
            else:
                self.log(f"Erro ao iniciar o servidor '{server_name}' após parada")
            
        except Exception as e:
            error_msg = f"Erro durante reinicialização do servidor '{server_name}': {str(e)}"
            self.log(error_msg)
            self.update_status(error_msg)
    
    def edit_selected_server(self):
        """Abre o script do servidor com o programa padrão do sistema."""
        selection = self.servers_tree.selection()
        if not selection:
            return
        
        item = self.servers_tree.item(selection[0])
        server_name = item["values"][0]
        server = self.server_manager.get_server(server_name)
        
        if server:
            # Verificar se o arquivo existe
            if os.path.exists(server.script_path):
                try:
                    # Usar a função de sistema para abrir o arquivo com o programa padrão
                    # ou deixar o usuário escolher o programa
                    if sys.platform == 'win32':
                        os.startfile(server.script_path)
                    elif sys.platform == 'darwin':
                        subprocess.call(['open', server.script_path])
                    else:  # Linux/Unix
                        subprocess.call(['xdg-open', server.script_path])
                    
                    self.log(f"Arquivo '{os.path.basename(server.script_path)}' aberto para edição")
                except Exception as e:
                    error_msg = f"Erro ao abrir arquivo: {str(e)}"
                    show_error_message("Erro", error_msg)
                    self.log(error_msg)
            else:
                error_msg = f"Arquivo não encontrado: {server.script_path}"
                show_error_message("Erro", error_msg)
                self.log(error_msg)
    
    def remove_selected_server(self):
        """Remove o servidor selecionado da interface e de todos os arquivos de configuração."""
        selection = self.servers_tree.selection()
        if not selection:
            return
        
        item = self.servers_tree.item(selection[0])
        server_name = item["values"][0]
        server = self.server_manager.get_server(server_name)
        
        if not server:
            self.update_status(f"Servidor '{server_name}' não encontrado")
            return
        
        # Se o servidor tiver uma configuração original, mostrar a fonte dessa configuração
        config_sources = []
        if hasattr(server, 'original_config') and server.original_config:
            source = server.original_config.get('source')
            if source:
                config_sources.append(source)
        
        # Montar mensagem de confirmação
        confirmation_message = f"Tem certeza que deseja remover o servidor '{server_name}'?"
        if config_sources:
            confirmation_message += f"\n\nO servidor será removido de: {', '.join(config_sources)} e config/servers.json"
        
        # Confirmar remoção
        if ask_yes_no("Remover Servidor", confirmation_message):
            # Atualizar status
            self.update_status(f"Removendo servidor '{server_name}'...")
            
            # Remover servidor do gerenciador
            if self.server_manager.remove_server(server_name):
                # Remover o item diretamente da árvore sem esperar pelo refresh
                self.servers_tree.delete(selection[0])
                
                # Atualizar a lista de servidores para garantir consistência
                self._refresh_servers_tree()
                
                # Atualizar contador
                self.update_server_count()
                
                # Registrar no log
                self.log(f"Servidor '{server_name}' removido com sucesso")
                
                # Atualizar status
                self.update_status(f"Servidor '{server_name}' removido com sucesso")
            else:
                self.update_status(f"Erro ao remover servidor '{server_name}'")
                self.log(f"Falha ao remover servidor '{server_name}'")
                
                # Atualizar a lista de servidores mesmo em caso de erro
                self._refresh_servers_tree()
    
    def add_server(self):
        """Adiciona um novo servidor."""
        self.open_server_dialog()
    
    def open_server_dialog(self, server=None):
        """Abre o diálogo para adicionar ou editar um servidor."""
        # Criar janela de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Adicionar Servidor" if not server else "Editar Servidor")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.resizable(False, False)
        
        # Centralizar a janela
        center_window(dialog)
        
        # Configurar estilos
        content_frame = ttk.Frame(dialog, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title = ttk.Label(
            content_frame, 
            text="Configuração do Servidor", 
            style="Subtitle.TLabel"
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Apenas o campo Nome
        ttk.Label(content_frame, text="Nome:").grid(row=1, column=0, sticky="w", pady=5)
        name_entry = ttk.Entry(content_frame, width=30)
        name_entry.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Descrição do funcionamento
        description_text = "O script Python será criado automaticamente na\npasta do ambiente virtual com o mesmo nome do servidor."
        description = ttk.Label(content_frame, text=description_text, justify="left")
        description.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        
        # Configurar valores padrão se for edição
        if server:
            name_entry.insert(0, server.name)
        
        # Botões de ação
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, sticky="e", pady=(20, 0))
        
        cancel_button = ttk.Button(
            buttons_frame, 
            text="Cancelar", 
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        save_button = ttk.Button(
            buttons_frame, 
            text="Salvar", 
            command=lambda: self.save_server(
                dialog, 
                name_entry.get(), 
                server.name if server else None
            ),
            style="Primary.TButton"
        )
        save_button.pack(side=tk.RIGHT)
        
        # Configurar redimensionamento
        content_frame.columnconfigure(1, weight=1)
        
        # Tornar o diálogo modal
        dialog.grab_set()
        dialog.focus_set()
        name_entry.focus()
    
    def save_server(self, dialog, name, original_name=None):
        """Salva o servidor (adiciona ou atualiza)."""
        # Validar campos
        if not name:
            show_error_message("Erro", "O nome do servidor é obrigatório")
            return
        
        # Converter o nome para snake_case para o arquivo
        snake_case_name = self._to_snake_case(name)
        
        # Obter o diretório raiz do projeto
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Definir caminho do diretório mcp_server (não dentro de .venv)
        mcp_server_dir = os.path.join(project_dir, "mcp_server")
        
        # Verificar se o diretório existe
        if not os.path.exists(mcp_server_dir):
            show_error_message(
                "Erro", 
                f"A pasta mcp_server não foi encontrada em: {project_dir}"
            )
            return
        
        # Caminho para o script Python (diretamente na pasta mcp_server)
        script_path = os.path.join(mcp_server_dir, f"{snake_case_name}.py")
        
        # Criar ou atualizar servidor
        if not original_name:  # Novo servidor
            # Verificar se o arquivo já existe
            if os.path.exists(script_path):
                # Perguntar se deseja substituir
                if not ask_yes_no(
                    "Arquivo existente", 
                    f"O arquivo '{snake_case_name}.py' já existe. Deseja usar este arquivo?"
                ):
                    return
            else:
                # Criar um arquivo Python básico com o template MCP
                try:
                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(self._get_mcp_template(name, snake_case_name))
                        
                    self.log(f"Arquivo '{snake_case_name}.py' criado em '{mcp_server_dir}'")
                except Exception as e:
                    show_error_message(
                        "Erro ao criar arquivo", 
                        f"Não foi possível criar o arquivo: {str(e)}"
                    )
                    return
            
            # Criar o servidor
            server = Server(name, script_path, None)
            if self.server_manager.add_server(server):
                # Atualizar as configurações dos clientes (mcp.json, etc.)
                self._update_client_configs(name, script_path, mcp_server_dir)
                
                self.update_status(f"Servidor '{name}' adicionado")
                # Chamando _refresh_servers_tree() diretamente ao invés de refresh_servers()
                self._refresh_servers_tree(name)  # Passar o nome para selecionar o novo servidor
                dialog.destroy()
        else:  # Atualizar servidor existente
            server = self.server_manager.get_server(original_name)
            if not server:
                show_error_message("Erro", f"Servidor '{original_name}' não encontrado")
                return
                
            # Se o nome mudou, precisamos atualizar o arquivo
            if name != original_name:
                # Obter caminho do script existente para poder renomeá-lo
                old_script_path = server.script_path
                
                if os.path.exists(old_script_path):
                    # Se existe um arquivo com o nome antigo, tenta renomeá-lo
                    try:
                        new_script_path = os.path.join(os.path.dirname(old_script_path), f"{snake_case_name}.py")
                        
                        # Verificar se o novo nome de arquivo já existe
                        if os.path.exists(new_script_path) and old_script_path != new_script_path:
                            if not ask_yes_no(
                                "Arquivo existente", 
                                f"O arquivo '{snake_case_name}.py' já existe. Deseja substituir?"
                            ):
                                return
                            os.remove(new_script_path)
                            
                        # Renomear o arquivo
                        if old_script_path != new_script_path:
                            os.rename(old_script_path, new_script_path)
                            self.log(f"Arquivo renomeado de '{os.path.basename(old_script_path)}' para '{snake_case_name}.py'")
                            script_path = new_script_path
                        else:
                            script_path = old_script_path
                    except Exception as e:
                        show_error_message(
                            "Erro ao renomear arquivo", 
                            f"Não foi possível renomear o arquivo: {str(e)}"
                        )
                        return
                else:
                    # Se não existe um arquivo no caminho antigo, cria um novo
                    try:
                        with open(script_path, "w", encoding="utf-8") as f:
                            f.write(self._get_mcp_template(name, snake_case_name))
                            
                        self.log(f"Arquivo '{snake_case_name}.py' criado em '{mcp_server_dir}'")
                    except Exception as e:
                        show_error_message(
                            "Erro ao criar arquivo", 
                            f"Não foi possível criar o arquivo: {str(e)}"
                        )
                        return
            else:
                # Se o nome não mudou, manter o caminho do script
                script_path = server.script_path
            
            # Atualizar o servidor
            updates = {
                "name": name,
                "script_path": script_path
            }
            
            if self.server_manager.update_server(original_name, **updates):
                # Atualizar as configurações dos clientes (mcp.json, etc.)
                # Se o nome mudou, remover a antiga configuração e adicionar a nova
                if name != original_name:
                    # Esta é uma simplificação. Idealmente, deveríamos editar as
                    # configurações existentes para manter metadados, mas isso exigiria
                    # mais trabalho.
                    self._update_client_configs(name, script_path, mcp_server_dir)
                    
                self.update_status(f"Servidor '{name}' atualizado")
                # Chamando _refresh_servers_tree() diretamente ao invés de refresh_servers()
                self._refresh_servers_tree(name)  # Passar o nome para selecionar o novo servidor
                dialog.destroy()
    
    def _update_client_configs(self, server_name, script_path, mcp_server_dir):
        """
        Atualiza os arquivos de configuração dos clientes.
        
        Args:
            server_name: Nome do servidor
            script_path: Caminho do script Python
            mcp_server_dir: Diretório mcp_server
        """
        try:
            # Determinar o caminho do executável uv.exe usando where.exe no Windows
            uv_path = ""
            
            if os.name == 'nt':  # Windows
                try:
                    # Tentar encontrar uv.exe usando where.exe (ferramenta padrão do Windows)
                    result = subprocess.run(
                        ["where.exe", "uv.exe"], 
                        capture_output=True, 
                        text=True, 
                        check=False
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        # Pegar a primeira linha do resultado (primeiro caminho encontrado)
                        uv_path = result.stdout.strip().split('\n')[0]
                        self.log(f"Caminho do uv.exe encontrado: {uv_path}")
                    else:
                        # Se não encontrar, tentar encontrar em caminhos comuns
                        common_paths = [
                            os.path.expanduser("~/.local/bin/uv.exe"),
                            os.path.expanduser("~/AppData/Local/Programs/Python/Python312/Scripts/uv.exe"),
                            os.path.expanduser("~/pipx/venvs/uv/Scripts/uv.exe"),
                            "C:\\Users\\JAMILE\\pipx\\venvs\\uv\\Scripts\\uv.exe"
                        ]
                        
                        for path in common_paths:
                            if os.path.exists(path):
                                uv_path = path
                                self.log(f"Caminho do uv.exe encontrado em caminhos comuns: {uv_path}")
                                break
                                
                        if not uv_path:
                            raise Exception("Não foi possível encontrar o executável uv.exe")
                except Exception as e:
                    self.log(f"Erro ao tentar encontrar uv.exe: {str(e)}")
                    raise Exception(f"Não foi possível encontrar o executável uv.exe: {str(e)}")
            else:  # Linux/macOS
                try:
                    # Tentar encontrar uv usando which (equivalente ao where no Unix)
                    result = subprocess.run(
                        ["which", "uv"], 
                        capture_output=True, 
                        text=True, 
                        check=False
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        uv_path = result.stdout.strip()
                    else:
                        # Tentar encontrar em caminhos comuns no Unix
                        common_paths = [
                            os.path.expanduser("~/.local/bin/uv"),
                            "/usr/local/bin/uv"
                        ]
                        
                        for path in common_paths:
                            if os.path.exists(path):
                                uv_path = path
                                break
                                
                        if not uv_path:
                            raise Exception("Não foi possível encontrar o executável uv")
                except Exception as e:
                    self.log(f"Erro ao tentar encontrar uv: {str(e)}")
                    raise Exception(f"Não foi possível encontrar o executável uv: {str(e)}")
            
            # Se não encontrou uv.exe, lançar erro
            if not uv_path:
                raise Exception("Não foi possível determinar o caminho do executável uv")
                
            # Criação dos argumentos para executar o script
            argumentos = [
                "--directory",
                mcp_server_dir,
                "run",
                os.path.basename(script_path),
                "--log-level",
                "ERROR"
            ]
            
            # Atualizar os arquivos de configuração
            resultado = config_util.atualizar_configuracoes(
                nome_servidor=server_name,
                comando=uv_path,
                argumentos=argumentos
            )
            
            # Registrar resultado nos logs
            if resultado["cursor"]["status"] == "sucesso":
                self.log(f"Configuração do Cursor atualizada em {resultado['cursor']['caminho']}")
            else:
                self.log(f"Falha ao atualizar configuração do Cursor: {resultado['cursor']['mensagem']}")
                
            if resultado["claude"]["status"] == "sucesso":
                self.log(f"Configuração do Claude Desktop atualizada em {resultado['claude']['caminho']}")
            else:
                self.log(f"Falha ao atualizar configuração do Claude Desktop: {resultado['claude']['mensagem']}")
                
        except Exception as e:
            self.log(f"Erro ao atualizar configurações dos clientes: {str(e)}")
            show_error_message(
                "Aviso", 
                f"O servidor foi adicionado, mas ocorreu um erro ao atualizar as configurações dos clientes: {str(e)}"
            )
    
    def _to_snake_case(self, name):
        """Converte um nome para snake_case."""
        # Remover caracteres especiais
        name = ''.join(c for c in name if c.isalnum() or c.isspace())
        # Converter espaços para underscores e tudo para minúsculo
        return name.replace(' ', '_').lower()
    
    def _get_mcp_template(self, name, file_name):
        """Retorna um template básico para um servidor MCP usando FastMCP."""
        template = f'''"""
Servidor MCP: {name}
Arquivo: {file_name}.py

Este servidor MCP foi gerado automaticamente pelo MCP Server Manager.
"""
from typing import Any
from mcp.server.fastmcp import FastMCP

# Inicializa o servidor FastMCP
mcp = FastMCP("{name}", log_level="ERROR")

@mcp.tool()
async def hello(name: str = "Mundo") -> str:
    """Retorna uma saudação personalizada.
    
    Args:
        name: O nome para saudar. Padrão: "Mundo"
        
    Returns:
        Uma mensagem de saudação personalizada
    """
    return f"Olá {{name}} do servidor {name}!"

@mcp.tool()
async def soma(a: float, b: float) -> float:
    """Soma dois números.
    
    Args:
        a: Primeiro número
        b: Segundo número
        
    Returns:
        A soma dos dois números
    """
    return a + b

if __name__ == "__main__":
    # Inicializa e executa o servidor
    print("Iniciando o servidor MCP {name}...")
    print("Use Ctrl+C para encerrar.")
    mcp.run(transport='stdio')
'''
        return template
    
    # Funções de callback para operações do menu
    def open_settings(self):
        """Abre as configurações da aplicação."""
        self.notebook.select(2)  # Seleciona a aba de configurações
    
    def open_documentation(self):
        """Abre a documentação da aplicação."""
        show_info_message("Documentação", "Funcionalidade em desenvolvimento")
    
    def show_about(self):
        """Mostra informações sobre a aplicação."""
        about_text = """
        MCP Server Manager
        
        Versão: 1.0.0
        
        Uma interface gráfica para gerenciar servidores MCP.
        
        © 2023 MCP Server Team
        """
        show_info_message("Sobre", about_text.strip())
    
    # Funções de utilitários
    def update_status(self, message):
        """Atualiza a mensagem na barra de status."""
        self.status_label.config(text=message)
        self.update_idletasks()
    
    def log(self, message):
        """Adiciona uma mensagem ao log."""
        self.logs_text.insert(tk.END, f"{message}\n")
        self.logs_text.see(tk.END)  # Rola para o final
    
    def clear_logs(self):
        """Limpa os logs."""
        self.logs_text.delete(1.0, tk.END)
    
    def refresh_logs(self):
        """Atualiza os logs."""
        self.update_status("Logs atualizados")
    
    def export_logs(self):
        """Exporta os logs para um arquivo."""
        try:
            filetypes = [("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
            filename = filedialog.asksaveasfilename(
                filetypes=filetypes,
                defaultextension=".txt"
            )
            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.logs_text.get(1.0, tk.END))
                self.update_status(f"Logs exportados para {filename}")
                show_info_message("Exportar Logs", "Logs exportados com sucesso!")
        except Exception as e:
            show_error_message("Erro ao exportar logs", str(e))
    
    def on_closing(self):
        """Função chamada ao fechar a aplicação."""
        # Parar o verificador de status
        self.should_check_status = False
        
        # Verificar se há servidores em execução
        active_servers = [s for s in self.server_manager.get_all_servers() 
                          if s.status == ServerStatus.RUNNING]
        
        if active_servers and not ask_yes_no(
            "Fechar aplicação", 
            f"Existem {len(active_servers)} servidores em execução. Deseja realmente sair?"
        ):
            return
        
        # Encerrar todos os servidores antes de sair
        for server in active_servers:
            self.server_manager.stop_server(server.name)
        
        # Fechar a aplicação
        self.destroy()

    def show_server_tools(self):
        """Exibe uma janela com as ferramentas MCP do servidor selecionado."""
        selection = self.servers_tree.selection()
        if not selection:
            return
        
        item = self.servers_tree.item(selection[0])
        server_name = item["values"][0]
        server = self.server_manager.get_server(server_name)
        
        if not server or not server.script_path or not os.path.exists(server.script_path):
            show_error_message("Erro", "Arquivo de script do servidor não encontrado.")
            return
        
        # Extrair as ferramentas MCP do arquivo do servidor
        tools = extract_mcp_tools(server.script_path)
        
        # Log para depuração
        self.log(f"Encontradas {len(tools)} ferramentas MCP no servidor '{server_name}'")
        for tool in tools:
            self.log(f"  - {tool['name']}")
        
        if not tools:
            message = (
                f"Nenhuma ferramenta MCP encontrada no servidor '{server_name}'.\n\n"
                "Possíveis soluções:\n"
                "1. Verifique se o script utiliza o decorador @mcp.tool() corretamente.\n"
                "2. Edite o script para usar log_level=\"ERROR\" na inicialização do FastMCP:\n"
                "   mcp = FastMCP(\"{name}\", log_level=\"ERROR\")\n"
                "3. Reinicie o servidor após fazer alterações.\n"
                "4. Se estiver usando outro formato de MCP Server, verifique a documentação."
            )
            show_info_message("Ferramentas MCP", message)
            
            # Oferecer a opção de editar o script
            if ask_yes_no("Editar Script", "Deseja abrir o script para edição?"):
                self.edit_selected_server()
            return
        
        # Criar janela de ferramentas
        tools_window = tk.Toplevel(self)
        tools_window.title(f"Ferramentas MCP - {server_name}")
        tools_window.transient(self)  # Fazer esta janela filho da janela principal
        tools_window.grab_set()  # Tornar a janela modal
        
        # Tamanho e posicionamento
        tools_window.minsize(600, 500)  # Aumentado de 500x400 para 600x500
        center_window(tools_window, 700, 600)  # Aumentado de 600x500 para 700x600
        
        # Configurar grid
        tools_window.columnconfigure(0, weight=1)
        tools_window.rowconfigure(0, weight=0)
        tools_window.rowconfigure(1, weight=1)
        
        # Título
        ttk.Label(
            tools_window, 
            text=f"Ferramentas do Servidor: {server_name}", 
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Frame principal
        main_frame = ttk.Frame(tools_window)
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Criar notebook para organizar as ferramentas
        tools_notebook = ttk.Notebook(main_frame)
        tools_notebook.grid(row=0, column=0, sticky="nsew")
        
        # Adicionar uma aba para cada ferramenta (sem duplicações)
        tab_names = set()  # Conjunto para controlar abas já adicionadas
        for tool in tools:
            # Pular se uma aba com este nome já foi adicionada
            if tool["name"] in tab_names:
                self.log(f"Aviso: Ferramenta duplicada '{tool['name']}' ignorada")
                continue
                
            # Registrar o nome da aba
            tab_names.add(tool["name"])
            
            # Criar a aba para esta ferramenta
            tool_frame = ttk.Frame(tools_notebook, padding=10)
            tools_notebook.add(tool_frame, text=tool["name"])
            
            # Configurar o frame da ferramenta
            tool_frame.columnconfigure(0, weight=0)
            tool_frame.columnconfigure(1, weight=1)
            
            # Adicionar descrição com título mais descritivo
            ttk.Label(tool_frame, text="Documentação:", font=("Arial", 11, "bold")).grid(
                row=0, column=0, sticky="nw", pady=(0, 5), padx=(0, 10)
            )
            
            # Criar um frame para conter o texto com scrollbar, se necessário
            desc_frame = ttk.Frame(tool_frame)
            desc_frame.grid(row=0, column=1, sticky="ew", pady=(0, 10))
            desc_frame.columnconfigure(0, weight=1)
            
            # Scrollbar vertical
            scrollbar = ttk.Scrollbar(desc_frame, orient="vertical")
            scrollbar.grid(row=0, column=1, sticky="ns")
            
            # Usar Text widget para docstring para permitir texto de várias linhas
            desc_text = tk.Text(desc_frame, 
                               wrap=tk.WORD, 
                               height=15,  # Aumentado de 8 para 15
                               width=60,   # Aumentado de 50 para 60
                               yscrollcommand=scrollbar.set)
            desc_text.grid(row=0, column=0, sticky="ew")
            scrollbar.config(command=desc_text.yview)
            
            # Processar a docstring para melhor exibição
            docstring = tool["docstring"]
            
            # Formatar a docstring para melhor legibilidade
            # Formatação especial para docstrings que seguem o formato Google ou NumPy
            formatted_docstring = docstring
            
            # Configurar o widget de texto com estilo
            desc_text.tag_configure("bold", font=("Arial", 9, "bold"))
            desc_text.tag_configure("italic", font=("Arial", 9, "italic"))
            desc_text.tag_configure("normal", font=("Arial", 9))
            desc_text.tag_configure("heading", font=("Arial", 9, "bold"), foreground="#333399")
            desc_text.tag_configure("param_name", font=("Arial", 9, "bold"), foreground="#0066CC")
            desc_text.tag_configure("param_type", font=("Arial", 9, "italic"), foreground="#006600")
            desc_text.tag_configure("example_code", font=("Courier New", 9), background="#F0F0F0")
            desc_text.tag_configure("note_text", font=("Arial", 9, "italic"), foreground="#666666")
            
            # Identificar possíveis seções na docstring (Args:, Returns:, etc)
            lines = formatted_docstring.split('\n')
            i = 0
            in_examples = False
            in_notes = False
            example_block = False
            
            # Adicionar informações sobre parâmetros com valores padrão disponíveis
            if "params" in tool and tool["params"]:
                params_with_defaults = [p for p in tool["params"] if p.get("has_default", False)]
                if params_with_defaults:
                    desc_text.insert("end", "Parâmetros com valores padrão:\n", "heading")
                    for param in params_with_defaults:
                        param_name = param["name"]
                        param_type = param["type"] if param["type"] else "não especificado"
                        default_value = repr(param["default"]) if param["default"] is not None else "None"
                        desc_text.insert("end", f"{param_name}", "param_name")
                        desc_text.insert("end", f" ({param_type})", "param_type")
                        desc_text.insert("end", f": valor padrão = {default_value}\n", "normal")
                    desc_text.insert("end", "\n", "normal")
            
            while i < len(lines):
                line = lines[i]
                
                # Detectar cabeçalhos de seção (Args:, Returns:, etc)
                if line.strip().endswith(':') and line.strip().split()[0] in ['Args:', 'Returns:', 'Raises:', 'Examples:', 'Notes:', 'Parameters:', 'See:']:
                    # Marcar se estamos entrando em seções especiais
                    in_examples = line.strip().startswith('Examples:')
                    in_notes = line.strip().startswith('Notes:')
                    example_block = False
                    
                    # Inserir o cabeçalho com formatação
                    if i > 0:
                        desc_text.insert("end", "\n", "normal")
                    desc_text.insert("end", line.strip() + "\n", "heading")
                    
                elif in_examples:
                    # Dentro da seção Examples
                    if line.strip().startswith('>>>'):
                        # Início de um bloco de código
                        example_block = True
                        desc_text.insert("end", line + "\n", "example_code")
                    elif example_block and not line.strip().startswith('>>>') and line.strip():
                        # Continuação de um bloco de código (resultado)
                        desc_text.insert("end", line + "\n", "example_code")
                    elif not line.strip():
                        # Linha vazia termina um bloco de exemplo
                        example_block = False
                        desc_text.insert("end", "\n", "normal")
                    else:
                        # Texto normal dentro de Examples
                        example_block = False
                        desc_text.insert("end", line + "\n", "normal")
                        
                elif in_notes:
                    # Dentro da seção Notes
                    desc_text.insert("end", line + "\n", "note_text")
                    
                elif ':' in line and not line.endswith(':') and len(line.split(':', 1)[0].strip().split()) == 1:
                    # Parece ser um parâmetro no formato "name: description"
                    parts = line.split(':', 1)
                    param_name = parts[0].strip()
                    
                    # Verificar se há tipo em parênteses na descrição
                    desc_text.insert("end", param_name + ":", "param_name")
                    
                    # Verificar se há tipo especificado (tipo) na descrição
                    param_desc = parts[1].strip()
                    type_match = re.match(r'\s*\(([^)]+)\)(.*)', param_desc)
                    
                    if type_match:
                        param_type = type_match.group(1)
                        rest_desc = type_match.group(2)
                        desc_text.insert("end", " (", "normal")
                        desc_text.insert("end", param_type, "param_type")
                        desc_text.insert("end", ")" + rest_desc + "\n", "normal")
                    else:
                        desc_text.insert("end", " " + param_desc + "\n", "normal")
                else:
                    # Texto normal
                    desc_text.insert("end", line + "\n", "normal")
                i += 1
            
            # Remover a última linha em branco, se houver
            content = desc_text.get("1.0", "end-1c")
            if content.endswith('\n'):
                desc_text.delete("end-2c", "end-1c")
                
            # Tornar somente leitura com melhor visual
            desc_text.config(state="disabled", 
                            bg="#f8f8f8", 
                            bd=1, 
                            relief="solid", 
                            padx=5, 
                            pady=5)
        
        # Botão de fechar
        ttk.Button(
            tools_window, 
            text="Fechar", 
            command=tools_window.destroy
        ).grid(row=2, column=0, sticky="e", padx=10, pady=10)

    def import_server(self):
        """Importa um arquivo de servidor Python existente."""
        # Abrir diálogo para selecionar arquivo
        file_path = filedialog.askopenfilename(
            title="Selecionar Arquivo de Servidor",
            filetypes=[("Arquivos Python", "*.py"), ("Todos os arquivos", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        
        if not file_path:
            return  # Usuário cancelou
            
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            show_error_message("Erro", f"O arquivo {file_path} não existe.")
            return
            
        # Obter nome do arquivo sem extensão para usar como nome do servidor
        file_name = os.path.basename(file_path)
        server_name = os.path.splitext(file_name)[0]
        
        # Obter o diretório raiz do projeto
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Definir caminho do diretório mcp_server
        mcp_server_dir = os.path.join(project_dir, "mcp_server")
        
        # Verificar se o diretório existe
        if not os.path.exists(mcp_server_dir):
            show_error_message(
                "Erro", 
                f"A pasta mcp_server não foi encontrada em: {project_dir}"
            )
            return
            
        # Caminho para onde o arquivo será copiado
        dest_path = os.path.join(mcp_server_dir, file_name)
        
        # Verificar se já existe um arquivo com o mesmo nome no destino
        if os.path.exists(dest_path) and file_path != dest_path:
            if not ask_yes_no(
                "Arquivo existente", 
                f"Já existe um arquivo com o nome '{file_name}' na pasta mcp_server. Deseja substituí-lo?"
            ):
                return
                
        try:
            # Copiar o arquivo para a pasta mcp_server (se não for o mesmo arquivo)
            if file_path != dest_path:
                # Ler o conteúdo do arquivo de origem
                with open(file_path, 'r', encoding='utf-8') as src_file:
                    content = src_file.read()
                    
                # Escrever o conteúdo no arquivo de destino
                with open(dest_path, 'w', encoding='utf-8') as dest_file:
                    dest_file.write(content)
                    
                self.log(f"Arquivo '{file_name}' copiado para '{mcp_server_dir}'")
            
            # Adicionar novo servidor ao gerenciador
            server = Server(server_name, dest_path, None)
            if self.server_manager.add_server(server):
                # Atualizar as configurações dos clientes
                self._update_client_configs(server_name, dest_path, mcp_server_dir)
                
                self.update_status(f"Servidor '{server_name}' importado com sucesso")
                # Atualizar a lista de servidores
                self._refresh_servers_tree(server_name)
                
                # Mostrar mensagem de sucesso
                show_info_message(
                    "Importação concluída", 
                    f"O servidor '{server_name}' foi importado com sucesso e está pronto para uso."
                )
            else:
                self.update_status(f"Erro ao adicionar servidor '{server_name}'")
                self.log(f"Falha ao adicionar servidor '{server_name}' após importação")
                
        except Exception as e:
            show_error_message(
                "Erro ao importar servidor", 
                f"Ocorreu um erro durante a importação: {str(e)}"
            )
            self.log(f"Erro ao importar servidor de {file_path}: {str(e)}")

    def show_server_resources(self):
        """Exibe uma janela com os recursos MCP do servidor selecionado."""
        selection = self.servers_tree.selection()
        if not selection:
            return
        
        item = self.servers_tree.item(selection[0])
        server_name = item["values"][0]
        server = self.server_manager.get_server(server_name)
        
        if not server or not server.script_path or not os.path.exists(server.script_path):
            show_error_message("Erro", "Arquivo de script do servidor não encontrado.")
            return
        
        # Extrair os recursos MCP do arquivo do servidor
        resources = extract_mcp_resources(server.script_path)
        
        # Log para depuração
        self.log(f"Encontrados {len(resources)} recursos MCP no servidor '{server_name}'")
        for resource in resources:
            self.log(f"  - {resource['name']}")
        
        if not resources:
            message = (
                f"Nenhum recurso MCP encontrado no servidor '{server_name}'.\n\n"
                "Possíveis soluções:\n"
                "1. Verifique se o script utiliza o decorador @mcp.resource() corretamente.\n"
                "2. Edite o script para usar log_level=\"ERROR\" na inicialização do FastMCP:\n"
                "   mcp = FastMCP(\"{name}\", log_level=\"ERROR\")\n"
                "3. Reinicie o servidor após fazer alterações.\n"
                "4. Se estiver usando outro formato de MCP Server, verifique a documentação."
            )
            show_info_message("Recursos MCP", message)
            
            # Oferecer a opção de editar o script
            if ask_yes_no("Editar Script", "Deseja abrir o script para edição?"):
                self.edit_selected_server()
            return
        
        # Criar janela de recursos
        resources_window = tk.Toplevel(self)
        resources_window.title(f"Recursos MCP - {server_name}")
        resources_window.transient(self)  # Fazer esta janela filho da janela principal
        resources_window.grab_set()  # Tornar a janela modal
        
        # Tamanho e posicionamento
        resources_window.minsize(600, 500)
        center_window(resources_window, 700, 600)
        
        # Configurar grid
        resources_window.columnconfigure(0, weight=1)
        resources_window.rowconfigure(0, weight=0)
        resources_window.rowconfigure(1, weight=1)
        
        # Título
        ttk.Label(
            resources_window, 
            text=f"Recursos do Servidor: {server_name}", 
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Frame principal
        main_frame = ttk.Frame(resources_window)
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Criar notebook para organizar os recursos
        resources_notebook = ttk.Notebook(main_frame)
        resources_notebook.grid(row=0, column=0, sticky="nsew")
        
        # Adicionar uma aba para cada recurso (sem duplicações)
        tab_names = set()  # Conjunto para controlar abas já adicionadas
        for resource in resources:
            # Pular se uma aba com este nome já foi adicionada
            if resource["name"] in tab_names:
                self.log(f"Aviso: Recurso duplicado '{resource['name']}' ignorado")
                continue
                
            # Registrar o nome da aba
            tab_names.add(resource["name"])
            
            # Criar a aba para este recurso
            resource_frame = ttk.Frame(resources_notebook, padding=10)
            resources_notebook.add(resource_frame, text=resource["name"])
            
            # Configurar o frame do recurso
            resource_frame.columnconfigure(0, weight=0)
            resource_frame.columnconfigure(1, weight=1)
            
            # Adicionar descrição com título mais descritivo
            ttk.Label(resource_frame, text="Documentação:", font=("Arial", 11, "bold")).grid(
                row=0, column=0, sticky="nw", pady=(0, 5), padx=(0, 10)
            )
            
            # Criar um frame para conter o texto com scrollbar, se necessário
            desc_frame = ttk.Frame(resource_frame)
            desc_frame.grid(row=0, column=1, sticky="ew", pady=(0, 10))
            desc_frame.columnconfigure(0, weight=1)
            
            # Scrollbar vertical
            scrollbar = ttk.Scrollbar(desc_frame, orient="vertical")
            scrollbar.grid(row=0, column=1, sticky="ns")
            
            # Usar Text widget para docstring para permitir texto de várias linhas
            desc_text = tk.Text(desc_frame, 
                               wrap=tk.WORD, 
                               height=15,
                               width=60,
                               yscrollcommand=scrollbar.set)
            desc_text.grid(row=0, column=0, sticky="ew")
            scrollbar.config(command=desc_text.yview)
            
            # Processar a docstring para melhor exibição
            docstring = resource["docstring"]
            
            # Formatar a docstring para melhor legibilidade
            formatted_docstring = docstring
            
            # Configurar o widget de texto com estilo
            desc_text.tag_configure("bold", font=("Arial", 9, "bold"))
            desc_text.tag_configure("italic", font=("Arial", 9, "italic"))
            desc_text.tag_configure("normal", font=("Arial", 9))
            desc_text.tag_configure("heading", font=("Arial", 9, "bold"), foreground="#333399")
            desc_text.tag_configure("param_name", font=("Arial", 9, "bold"), foreground="#0066CC")
            desc_text.tag_configure("param_type", font=("Arial", 9, "italic"), foreground="#006600")
            desc_text.tag_configure("example_code", font=("Courier New", 9), background="#F0F0F0")
            desc_text.tag_configure("note_text", font=("Arial", 9, "italic"), foreground="#666666")
            
            # Identificar possíveis seções na docstring (Args:, Returns:, etc)
            lines = formatted_docstring.split('\n')
            i = 0
            in_examples = False
            in_notes = False
            example_block = False
            
            # Adicionar informações sobre parâmetros com valores padrão disponíveis
            if "params" in resource and resource["params"]:
                params_with_defaults = [p for p in resource["params"] if p.get("has_default", False)]
                if params_with_defaults:
                    desc_text.insert("end", "Parâmetros com valores padrão:\n", "heading")
                    for param in params_with_defaults:
                        param_name = param["name"]
                        param_type = param["type"] if param["type"] else "não especificado"
                        default_value = repr(param["default"]) if param["default"] is not None else "None"
                        desc_text.insert("end", f"{param_name}", "param_name")
                        desc_text.insert("end", f" ({param_type})", "param_type")
                        desc_text.insert("end", f": valor padrão = {default_value}\n", "normal")
                    desc_text.insert("end", "\n", "normal")
            
            while i < len(lines):
                line = lines[i]
                
                # Detectar cabeçalhos de seção (Args:, Returns:, etc)
                if line.strip().endswith(':') and line.strip().split()[0] in ['Args:', 'Returns:', 'Raises:', 'Examples:', 'Notes:', 'Parameters:', 'See:']:
                    # Marcar se estamos entrando em seções especiais
                    in_examples = line.strip().startswith('Examples:')
                    in_notes = line.strip().startswith('Notes:')
                    example_block = False
                    
                    # Inserir o cabeçalho com formatação
                    if i > 0:
                        desc_text.insert("end", "\n", "normal")
                    desc_text.insert("end", line.strip() + "\n", "heading")
                    
                elif in_examples:
                    # Dentro da seção Examples
                    if line.strip().startswith('>>>'):
                        # Início de um bloco de código
                        example_block = True
                        desc_text.insert("end", line + "\n", "example_code")
                    elif example_block and not line.strip().startswith('>>>') and line.strip():
                        # Continuação de um bloco de código (resultado)
                        desc_text.insert("end", line + "\n", "example_code")
                    elif not line.strip():
                        # Linha vazia termina um bloco de exemplo
                        example_block = False
                        desc_text.insert("end", "\n", "normal")
                    else:
                        # Texto normal dentro de Examples
                        example_block = False
                        desc_text.insert("end", line + "\n", "normal")
                        
                elif in_notes:
                    # Dentro da seção Notes
                    desc_text.insert("end", line + "\n", "note_text")
                    
                elif ':' in line and not line.endswith(':') and len(line.split(':', 1)[0].strip().split()) == 1:
                    # Parece ser um parâmetro no formato "name: description"
                    parts = line.split(':', 1)
                    param_name = parts[0].strip()
                    
                    # Verificar se há tipo em parênteses na descrição
                    desc_text.insert("end", param_name + ":", "param_name")
                    
                    # Verificar se há tipo especificado (tipo) na descrição
                    param_desc = parts[1].strip()
                    type_match = re.match(r'\s*\(([^)]+)\)(.*)', param_desc)
                    
                    if type_match:
                        param_type = type_match.group(1)
                        rest_desc = type_match.group(2)
                        desc_text.insert("end", " (", "normal")
                        desc_text.insert("end", param_type, "param_type")
                        desc_text.insert("end", ")" + rest_desc + "\n", "normal")
                    else:
                        desc_text.insert("end", " " + param_desc + "\n", "normal")
                else:
                    # Texto normal
                    desc_text.insert("end", line + "\n", "normal")
                i += 1
            
            # Remover a última linha em branco, se houver
            content = desc_text.get("1.0", "end-1c")
            if content.endswith('\n'):
                desc_text.delete("end-2c", "end-1c")
                
            # Tornar somente leitura com melhor visual
            desc_text.config(state="disabled", 
                            bg="#f8f8f8", 
                            bd=1, 
                            relief="solid", 
                            padx=5, 
                            pady=5)
        
        # Botão de fechar
        ttk.Button(
            resources_window, 
            text="Fechar", 
            command=resources_window.destroy
        ).grid(row=2, column=0, sticky="e", padx=10, pady=10)

    def show_server_prompts(self):
        """Exibe uma janela com os prompts MCP do servidor selecionado."""
        selection = self.servers_tree.selection()
        if not selection:
            return
        
        item = self.servers_tree.item(selection[0])
        server_name = item["values"][0]
        server = self.server_manager.get_server(server_name)
        
        if not server or not server.script_path or not os.path.exists(server.script_path):
            show_error_message("Erro", "Arquivo de script do servidor não encontrado.")
            return
        
        # Extrair os prompts MCP do arquivo do servidor
        prompts = extract_mcp_prompts(server.script_path)
        
        # Log para depuração
        self.log(f"Encontrados {len(prompts)} prompts MCP no servidor '{server_name}'")
        for prompt in prompts:
            self.log(f"  - {prompt['name']}")
        
        if not prompts:
            message = (
                f"Nenhum prompt MCP encontrado no servidor '{server_name}'.\n\n"
                "Possíveis soluções:\n"
                "1. Verifique se o script utiliza o decorador @mcp.prompt() corretamente.\n"
                "2. Edite o script para usar log_level=\"ERROR\" na inicialização do FastMCP:\n"
                "   mcp = FastMCP(\"{name}\", log_level=\"ERROR\")\n"
                "3. Reinicie o servidor após fazer alterações.\n"
                "4. Se estiver usando outro formato de MCP Server, verifique a documentação."
            )
            show_info_message("Prompts MCP", message)
            
            # Oferecer a opção de editar o script
            if ask_yes_no("Editar Script", "Deseja abrir o script para edição?"):
                self.edit_selected_server()
            return
        
        # Criar janela de prompts
        prompts_window = tk.Toplevel(self)
        prompts_window.title(f"Prompts MCP - {server_name}")
        prompts_window.transient(self)  # Fazer esta janela filho da janela principal
        prompts_window.grab_set()  # Tornar a janela modal
        
        # Tamanho e posicionamento
        prompts_window.minsize(650, 500)
        center_window(prompts_window, 750, 600)
        
        # Configurar grid
        prompts_window.columnconfigure(0, weight=1)
        prompts_window.rowconfigure(0, weight=0)
        prompts_window.rowconfigure(1, weight=1)
        
        # Título
        ttk.Label(
            prompts_window, 
            text=f"Prompts do Servidor: {server_name}", 
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        # Frame principal - Reduzir padding para 0
        main_frame = ttk.Frame(prompts_window, padding=(0, 0, 0, 0))
        main_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Criar notebook para organizar os prompts
        prompts_notebook = ttk.Notebook(main_frame)
        prompts_notebook.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Adicionar uma aba para cada prompt (sem duplicações)
        tab_names = set()  # Conjunto para controlar abas já adicionadas
        for prompt in prompts:
            # Pular se uma aba com este nome já foi adicionada
            if prompt["name"] in tab_names:
                self.log(f"Aviso: Prompt duplicado '{prompt['name']}' ignorado")
                continue
                
            # Registrar o nome da aba
            tab_names.add(prompt["name"])
            
            # Criar a aba para este prompt - Reduzir padding para mínimo necessário
            prompt_frame = ttk.Frame(prompts_notebook, padding=(5, 5, 0, 5))
            prompts_notebook.add(prompt_frame, text=prompt["name"])
            
            # Configurar o frame do prompt para usar um layout de duas colunas
            prompt_frame.columnconfigure(0, weight=0)
            prompt_frame.columnconfigure(1, weight=1)
            prompt_frame.rowconfigure(0, weight=0)  # Documentação
            prompt_frame.rowconfigure(1, weight=0)  # Separador
            prompt_frame.rowconfigure(2, weight=1)  # Conteúdo
            
            # Adicionar descrição com título mais descritivo
            ttk.Label(prompt_frame, text="Documentação:", font=("Arial", 11, "bold")).grid(
                row=0, column=0, sticky="nw", pady=(0, 5), padx=(0, 10)
            )
            
            # Criar um frame para conter o texto da documentação com scrollbar
            doc_frame = ttk.Frame(prompt_frame)
            doc_frame.grid(row=0, column=1, sticky="ew", pady=(0, 10))
            doc_frame.columnconfigure(0, weight=1)
            
            # Scrollbar vertical para documentação
            doc_scrollbar = ttk.Scrollbar(doc_frame, orient="vertical")
            doc_scrollbar.grid(row=0, column=1, sticky="ns")
            
            # Usar Text widget para docstring
            doc_text = tk.Text(doc_frame, 
                              wrap=tk.WORD, 
                              height=5,
                              width=60,
                              yscrollcommand=doc_scrollbar.set)
            doc_text.grid(row=0, column=0, sticky="ew")
            doc_scrollbar.config(command=doc_text.yview)
            
            # Processar e exibir a docstring
            docstring = prompt["docstring"] if prompt["docstring"] else "Sem documentação disponível."
            doc_text.insert("end", docstring)
            
            # Configurações visuais do campo de documentação
            doc_text.config(state="disabled", 
                           bg="#f8f8f8", 
                           bd=1, 
                           relief="solid", 
                           padx=5, 
                           pady=5)
            
            # Adicionar separador
            ttk.Separator(prompt_frame, orient="horizontal").grid(
                row=1, column=0, columnspan=2, sticky="ew", pady=10
            )
            
            # Adicionar título para o conteúdo do prompt
            ttk.Label(prompt_frame, text="Conteúdo:", font=("Arial", 11, "bold")).grid(
                row=2, column=0, sticky="nw", pady=(0, 5), padx=(0, 10)
            )
            
            # Criar um frame para conter o texto do conteúdo do prompt com scrollbar
            content_frame = ttk.Frame(prompt_frame)
            content_frame.grid(row=2, column=1, sticky="nsew", pady=(0, 0), padx=(0, 0))
            content_frame.columnconfigure(0, weight=1)
            content_frame.rowconfigure(0, weight=1)
            
            # Scrollbar vertical para conteúdo
            content_scrollbar = ttk.Scrollbar(content_frame, orient="vertical")
            content_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 0))
            
            # Usar Text widget para o conteúdo do prompt - Aumentar largura
            content_text = tk.Text(content_frame, 
                                  wrap=tk.WORD, 
                                  height=15,
                                  width=70,
                                  yscrollcommand=content_scrollbar.set)
            content_text.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            content_scrollbar.config(command=content_text.yview)
            
            # Processar e exibir o conteúdo do prompt
            prompt_content = prompt.get("content")
            if prompt_content:
                # Remover indentação desnecessária do prompt
                lines = prompt_content.splitlines()
                # Determinar a indentação mínima (exceto linhas vazias)
                min_indent = float('inf')
                for line in lines:
                    if line.strip():  # Ignorar linhas vazias
                        spaces = len(line) - len(line.lstrip())
                        min_indent = min(min_indent, spaces)
                
                # Se encontrou indentação mínima, remover esse número de espaços de cada linha
                if min_indent != float('inf'):
                    processed_lines = []
                    for line in lines:
                        if line.strip():  # Se a linha não estiver vazia
                            processed_lines.append(line[min_indent:])
                        else:
                            processed_lines.append(line)
                    processed_content = '\n'.join(processed_lines)
                else:
                    processed_content = prompt_content
                
                content_text.insert("end", processed_content)
            else:
                content_text.insert("end", "Conteúdo do prompt não disponível.")
            
            # Configurações visuais do campo de conteúdo - Margins 0
            content_text.config(state="disabled", 
                               bg="#f8f8f8", 
                               bd=1, 
                               relief="solid", 
                               padx=0, 
                               pady=0)
        
        # Botão de fechar
        ttk.Button(
            prompts_window, 
            text="Fechar", 
            command=prompts_window.destroy
        ).grid(row=2, column=0, sticky="e", padx=10, pady=10)


def main():
    """Função principal para iniciar a aplicação."""
    app = MCPServerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
