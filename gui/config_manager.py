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
