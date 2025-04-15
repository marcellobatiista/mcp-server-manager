"""
Gerenciador de servidores MCP.

Este módulo contém classes e funções para gerenciar os servidores MCP.
"""
import os
import sys
import json
import time
import threading
import subprocess
import platform
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import psutil  # Importar psutil para melhor gerenciamento de processos
import fnmatch  # Importar fnmatch para rotação de arquivos

# Definir o caminho para a raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, str(ROOT_DIR))

from gui.utils import (
    show_error_message, 
    show_info_message, 
    ask_yes_no,
    create_directory_if_not_exists,
    load_json_file,
    save_json_file
)


class ServerStatus:
    """Constantes para o status dos servidores."""
    STOPPED = "Parado"
    RUNNING = "Em execução"
    STARTING = "Iniciando"
    STOPPING = "Parando"
    ERROR = "Erro"


class Server:
    """
    Classe que representa um servidor MCP.
    """
    def __init__(self, name, script_path, config_file=None, port=8000):
        """
        Inicializa um novo servidor.
        
        Args:
            name: Nome do servidor
            script_path: Caminho para o script Python que inicia o servidor
            config_file: Caminho para o arquivo de configuração (opcional)
            port: Porta em que o servidor será executado
        """
        self.name = name
        self.script_path = script_path
        self.config_file = config_file
        self.port = port
        self.status = ServerStatus.STOPPED
        self.process = None
        self.logs = []
        self.start_time = None
        self.stop_time = None
        self.log_file = None
        self.original_config = None  # Armazena a configuração original do servidor

    def to_dict(self):
        """
        Converte o servidor para um dicionário para ser salvo em JSON.
        
        Returns:
            dict: Dados do servidor
        """
        return {
            "name": self.name,
            "script_path": str(self.script_path),
            "config_file": str(self.config_file) if self.config_file else None,
            "port": self.port,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Cria um servidor a partir de um dicionário.
        
        Args:
            data: Dicionário com os dados do servidor
            
        Returns:
            Server: Instância do servidor
        """
        server = cls(
            name=data["name"],
            script_path=data["script_path"],
            config_file=data.get("config_file"),
            port=data.get("port", 8000)
        )
        server.status = data.get("status", ServerStatus.STOPPED)
        return server


class ServerManager:
    """
    Gerenciador de servidores MCP.
    """
    def __init__(self, config_dir=None, log_dir=None):
        """
        Inicializa o gerenciador de servidores.
        
        Args:
            config_dir: Diretório de configuração (opcional)
            log_dir: Diretório de logs (opcional)
        """
        # Definir diretórios
        self.config_dir = config_dir or os.path.join(ROOT_DIR, "config")
        self.log_dir = log_dir or os.path.join(ROOT_DIR, "logs")
        
        # Criar diretórios se não existirem
        create_directory_if_not_exists(self.config_dir)
        create_directory_if_not_exists(self.log_dir)
        
        # Caminho para o arquivo de configuração dos servidores
        self.servers_config_file = os.path.join(self.config_dir, "servers.json")
        
        # Lista de servidores
        self.servers = []
        
        # Carregar servidores
        self._load_servers()
        
        # Carregar servidores do Cursor e Claude
        self._load_client_config_servers()
        
        # Callbacks
        self.on_server_status_changed = None
        self.on_log_added = None
    
    def _load_servers(self):
        """
        Carrega a lista de servidores do arquivo de configuração.
        """
        data = load_json_file(self.servers_config_file, default=[])
        self.servers = [Server.from_dict(server_data) for server_data in data]
    
    def _load_client_config_servers(self):
        """
        Carrega servidores configurados nos arquivos do Cursor e Claude Desktop.
        """
        # Obter caminhos para os arquivos de configuração
        config_files = self._get_client_config_paths()
        
        # Processar cada arquivo de configuração
        for config_type, config_path in config_files.items():
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        
                    if 'mcpServers' in config_data:
                        for name, server_config in config_data['mcpServers'].items():
                            # Verificar se o servidor já existe
                            if not any(s.name == name for s in self.servers):
                                # Extrair informações do servidor
                                script_path = None
                                config_file = None
                                directory = None
                                
                                # Analisar argumentos para obter informações
                                if 'args' in server_config:
                                    args = server_config['args']
                                    
                                    # Encontrar diretório
                                    for i, arg in enumerate(args):
                                        if arg == "--directory" and i+1 < len(args):
                                            directory = args[i+1]
                                    
                                    # Encontrar arquivo de script
                                    for i, arg in enumerate(args):
                                        if arg == "run" and i+1 < len(args) and args[i+1].endswith('.py'):
                                            script_path = args[i+1]
                                            if directory:
                                                script_path = os.path.join(directory, script_path)
                                
                                # Se encontrou um script, adicionar o servidor
                                if script_path:
                                    # Criar o servidor
                                    server = Server(name, script_path, config_file)
                                    
                                    # Adicionar os dados originais de configuração
                                    server.original_config = {
                                        "command": server_config.get("command", ""),
                                        "args": server_config.get("args", []),
                                        "source": config_type
                                    }
                                    
                                    self.add_server(server, save_config=False)
                except Exception as e:
                    print(f"Erro ao carregar configuração de {config_type}: {str(e)}")
    
    def _get_client_config_paths(self):
        """
        Retorna os caminhos para os arquivos de configuração do Cursor e Claude Desktop.
        
        Returns:
            dict: Dicionário com os caminhos
        """
        home = os.path.expanduser("~")
        
        # Caminho para o arquivo de configuração do Cursor
        cursor_config = os.path.join(home, ".cursor", "mcp.json")
        
        # Caminho para o arquivo de configuração do Claude Desktop
        if platform.system() == "Windows":
            claude_config = os.path.join(home, "AppData", "Roaming", "Claude", "claude_desktop_config.json")
        else:  # macOS
            claude_config = os.path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json")
        
        return {
            "cursor": cursor_config,
            "claude": claude_config
        }
    
    def _save_servers(self):
        """
        Salva a lista de servidores no arquivo de configuração.
        """
        data = [server.to_dict() for server in self.servers]
        save_json_file(self.servers_config_file, data)
    
    def add_server(self, server, save_config=True):
        """
        Adiciona um servidor à lista.
        
        Args:
            server: O servidor a ser adicionado
            save_config: Se deve salvar a configuração após adicionar
        
        Returns:
            bool: True se o servidor foi adicionado com sucesso
        """
        # Verificar se já existe um servidor com o mesmo nome
        for existing_server in self.servers:
            if existing_server.name == server.name:
                # Não mostrar erro se estamos carregando de configuração
                if save_config:
                    show_error_message(
                        "Erro ao adicionar servidor", 
                        f"Já existe um servidor com o nome '{server.name}'"
                    )
                return False
        
        # Adicionar servidor
        self.servers.append(server)
        
        # Salvar configuração se solicitado
        if save_config:
            self._save_servers()
            
        return True
    
    def remove_server(self, server_name):
        """
        Remove um servidor da lista e dos arquivos de configuração do Cursor e Claude Desktop.
        
        Args:
            server_name: Nome do servidor a ser removido
            
        Returns:
            bool: True se o servidor foi removido com sucesso
        """
        server = self.get_server(server_name)
        if not server:
            return False
        
        # Verificar se o servidor está em execução
        if server.status == ServerStatus.RUNNING:
            if not ask_yes_no(
                "Confirmação", 
                f"O servidor '{server_name}' está em execução. Deseja parar e remover?"
            ):
                return False
            self.stop_server(server_name)
        
        # Resultados da remoção
        success = True
        removed_from = []
        
        # 1. Remover dos arquivos de configuração do Cursor e Claude Desktop
        config_files = self._get_client_config_paths()
        for config_type, config_path in config_files.items():
            if os.path.exists(config_path):
                try:
                    # Carregar configuração
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # Verificar se o servidor existe na configuração
                    if 'mcpServers' in config_data and server_name in config_data['mcpServers']:
                        # Remover o servidor
                        del config_data['mcpServers'][server_name]
                        
                        # Salvar configuração atualizada
                        with open(config_path, 'w', encoding='utf-8') as f:
                            json.dump(config_data, f, indent=2)
                        
                        removed_from.append(config_type)
                except Exception as e:
                    print(f"Erro ao remover servidor '{server_name}' da configuração {config_type}: {str(e)}")
                    success = False
        
        # 2. Tentar remover o script do servidor, se existir
        if hasattr(server, 'script_path') and server.script_path and os.path.exists(server.script_path):
            try:
                script_name = os.path.basename(server.script_path)
                show_info_message(
                    "Informação",
                    f"O arquivo '{script_name}' não foi excluído automaticamente."
                )
            except:
                pass
        
        # 3. Remover da lista de servidores em memória
        self.servers = [s for s in self.servers if s.name != server_name]
        
        # 4. Salvar a lista de servidores no arquivo de configuração
        self._save_servers()
        
        # Resumo das operações realizadas
        summary = f"Servidor '{server_name}' removido"
        if removed_from:
            summary += f" das configurações: {', '.join(removed_from)}"
        show_info_message("Remoção concluída", summary)
        
        return success
    
    def get_server(self, server_name):
        """
        Obtém um servidor pelo nome.
        
        Args:
            server_name: Nome do servidor
            
        Returns:
            Server: O servidor encontrado ou None se não encontrado
        """
        for server in self.servers:
            if server.name == server_name:
                return server
        return None
    
    def get_all_servers(self):
        """
        Obtém todos os servidores.
        
        Returns:
            list: Lista de servidores
        """
        return self.servers
    
    def update_server(self, server_name, **kwargs):
        """
        Atualiza as propriedades de um servidor.
        
        Args:
            server_name: Nome do servidor
            **kwargs: Propriedades a serem atualizadas
            
        Returns:
            bool: True se o servidor foi atualizado com sucesso
        """
        server = self.get_server(server_name)
        if not server:
            return False
        
        # Atualizar propriedades válidas
        valid_props = ["name", "script_path", "config_file", "port"]
        for prop, value in kwargs.items():
            if prop in valid_props:
                # Caso especial para renomear o servidor
                if prop == "name" and value != server_name:
                    # Verificar se o novo nome já existe
                    if self.get_server(value):
                        show_error_message(
                            "Erro ao atualizar servidor", 
                            f"Já existe um servidor com o nome '{value}'"
                        )
                        return False
                
                # Atualizar propriedade
                setattr(server, prop, value)
        
        # Salvar alterações
        self._save_servers()
        return True
    
    def start_server(self, server_name):
        """
        Inicia um servidor.
        
        Args:
            server_name: Nome do servidor
            
        Returns:
            bool: True se o servidor foi iniciado com sucesso
        """
        server = self.get_server(server_name)
        if not server:
            return False
        
        # Verificar se o servidor já está em execução
        if server.status in [ServerStatus.RUNNING, ServerStatus.STARTING]:
            show_info_message(
                "Informação", 
                f"O servidor '{server_name}' já está em execução ou iniciando."
            )
            return False
        
        # Verificar se o script existe
        if not os.path.exists(server.script_path):
            show_error_message(
                "Erro ao iniciar servidor", 
                f"O script '{server.script_path}' não existe."
            )
            server.status = ServerStatus.ERROR
            self._notify_status_changed(server)
            return False
        
        # Definir status e iniciar thread
        server.status = ServerStatus.STARTING
        self._notify_status_changed(server)
        
        # Iniciar em uma thread separada
        threading.Thread(
            target=self._start_server_thread,
            args=(server,),
            daemon=True
        ).start()
        
        return True
    
    def _start_server_thread(self, server):
        """
        Thread que inicia o servidor.
        
        Args:
            server: O servidor a ser iniciado
        """
        try:
            # Criar arquivo de log
            log_filename = f"{server.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            log_path = os.path.join(self.log_dir, log_filename)
            server.log_file = log_path
            
            # Rotação de logs - manter no máximo 10 arquivos de log por servidor
            self._rotate_log_files(server.name)
            
            # Abrir arquivos para saída
            with open(log_path, "w", encoding="utf-8") as log_file:
                # Registrar início
                start_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando servidor '{server.name}'...\n"
                log_file.write(start_msg)
                self._add_log(server, start_msg)
                
                # Logar a configuração original para depuração
                if hasattr(server, 'original_config') and server.original_config:
                    config_info = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Configuração original: {json.dumps(server.original_config)}\n"
                    log_file.write(config_info)
                    log_file.flush()
                else:
                    log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sem configuração original encontrada\n")
                    log_file.flush()
                
                # Determinar comando e diretório de trabalho
                cmd = None
                cwd = None
                
                # Verificar se temos configuração original
                if hasattr(server, 'original_config') and server.original_config:
                    # Usar configuração do arquivo mcp.json
                    if server.original_config.get("command") and server.original_config.get("args"):
                        log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Usando configuração do arquivo {server.original_config.get('source', 'cliente')}\n")
                        
                        # Usar o comando exato (uv.exe)
                        cmd = [server.original_config["command"]]
                        
                        # Usar os argumentos exatos
                        if server.original_config.get("args"):
                            cmd.extend(server.original_config["args"])
                        
                        # Definir o diretório
                        if "--directory" in server.original_config.get("args", []):
                            dir_index = server.original_config["args"].index("--directory")
                            if dir_index + 1 < len(server.original_config["args"]):
                                cwd = server.original_config["args"][dir_index + 1]
                else:
                    # Não temos configuração original, vamos buscar diretamente do arquivo do Cursor
                    log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sem configuração original, buscando no arquivo mcp.json\n")
                    
                    try:
                        # Caminho para o arquivo mcp.json do Cursor
                        home = os.path.expanduser("~")
                        cursor_config = os.path.join(home, ".cursor", "mcp.json")
                        
                        # Verificar se o arquivo existe
                        if os.path.exists(cursor_config):
                            # Carregar configuração
                            with open(cursor_config, 'r', encoding='utf-8') as f:
                                config_data = json.load(f)
                            
                            # Verificar se o servidor está configurado
                            if 'mcpServers' in config_data and server.name in config_data['mcpServers']:
                                server_config = config_data['mcpServers'][server.name]
                                log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Encontrado servidor '{server.name}' no arquivo mcp.json\n")
                                
                                # Usar configuração do arquivo
                                cmd = [server_config["command"]]
                                cmd.extend(server_config["args"])
                                
                                # Definir o diretório
                                if "--directory" in server_config.get("args", []):
                                    dir_index = server_config["args"].index("--directory")
                                    if dir_index + 1 < len(server_config["args"]):
                                        cwd = server_config["args"][dir_index + 1]
                            else:
                                log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Servidor '{server.name}' não encontrado no arquivo mcp.json\n")
                        else:
                            log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Arquivo mcp.json não encontrado: {cursor_config}\n")
                    except Exception as e:
                        log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erro ao carregar arquivo mcp.json: {str(e)}\n")
                
                # Se ainda não temos um comando, usar a configuração padrão com uv
                if not cmd:
                    log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Usando configuração padrão com uv\n")
                    
                    # Usar o comando uv.exe diretamente
                    uv_path = os.path.expanduser("~\\pipx\\venvs\\uv\\Scripts\\uv.exe")
                    if not os.path.exists(uv_path):
                        uv_path = "uv"  # tenta usar o uv do PATH como fallback
                    
                    cmd = [uv_path]
                    
                    # Diretório do projeto
                    project_dir = os.path.join(os.path.dirname(os.path.dirname(server.script_path)), "mcp_server")
                    if not os.path.exists(project_dir):
                        project_dir = os.path.dirname(server.script_path)
                    
                    # Argumentos padrão para uv
                    cmd.extend(["--directory", project_dir, "run", os.path.basename(server.script_path)])
                    
                    # Definir diretório de trabalho
                    cwd = project_dir
                
                # Garantir que temos um diretório de trabalho
                if not cwd:
                    cwd = os.path.dirname(server.script_path)
                
                # Logar o comando e o diretório para depuração
                log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Comando final: {' '.join(cmd)}\n")
                log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Diretório de trabalho: {cwd}\n")
                log_file.flush()
                
                # Iniciar processo sem usar a flag CREATE_NEW_CONSOLE, para capturar a saída
                server.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=cwd  # Definir o diretório de trabalho
                )
                
                # Registrar hora de início
                server.start_time = datetime.now()
                server.status = ServerStatus.RUNNING
                self._notify_status_changed(server)
                
                # Ler a saída do processo
                for line in server.process.stdout:
                    log_msg = line.rstrip()
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_entry = f"[{timestamp}] {log_msg}\n"
                    log_file.write(log_entry)
                    log_file.flush()
                    self._add_log(server, log_entry)
                
                # Aguardar o término do processo
                return_code = server.process.wait()
                
                # Verificar código de retorno
                if return_code != 0:
                    # Verificar se o código 15 (SIGTERM) representa um encerramento solicitado pelo usuário
                    if return_code == 15 and server.status == ServerStatus.STOPPING:
                        # Este é um encerramento normal, então não é um erro
                        end_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Servidor '{server.name}' encerrado pelo usuário (SIGTERM)\n"
                        log_file.write(end_msg)
                        self._add_log(server, end_msg)
                        server.status = ServerStatus.STOPPED
                    else:
                        error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Servidor '{server.name}' encerrado com erro (código {return_code})\n"
                        log_file.write(error_msg)
                        self._add_log(server, error_msg)
                        server.status = ServerStatus.ERROR
                else:
                    end_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Servidor '{server.name}' encerrado normalmente\n"
                    log_file.write(end_msg)
                    self._add_log(server, end_msg)
                    server.status = ServerStatus.STOPPED
                
                # Registrar hora de término
                server.stop_time = datetime.now()
                server.process = None
                self._notify_status_changed(server)
        
        except Exception as e:
            # Registrar erro
            error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erro ao iniciar servidor '{server.name}': {str(e)}\n"
            
            # Tentar gravar no arquivo de log
            try:
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(error_msg)
            except:
                pass
            
            self._add_log(server, error_msg)
            server.status = ServerStatus.ERROR
            server.process = None
            self._notify_status_changed(server)
    
    def _rotate_log_files(self, server_name, max_files=10):
        """
        Rotação de logs - mantém apenas os X arquivos mais recentes por servidor.
        
        Args:
            server_name: Nome do servidor
            max_files: Número máximo de arquivos de log a manter (padrão: 10)
        """
        try:
            # Padrão de nome de arquivo para este servidor
            log_pattern = f"{server_name}_*.log"
            
            # Encontrar todos os arquivos de log para este servidor
            log_files = []
            for filename in os.listdir(self.log_dir):
                if fnmatch.fnmatch(filename, log_pattern):
                    file_path = os.path.join(self.log_dir, filename)
                    # Obter data de modificação do arquivo
                    mod_time = os.path.getmtime(file_path)
                    log_files.append((file_path, mod_time))
            
            # Ordenar por data de modificação (mais antigos primeiro)
            log_files.sort(key=lambda x: x[1])
            
            # Remover arquivos excedentes (mais antigos)
            files_to_remove = log_files[:-max_files] if len(log_files) > max_files else []
            
            for file_path, _ in files_to_remove:
                try:
                    os.remove(file_path)
                    print(f"Log rotacionado: {os.path.basename(file_path)} removido")
                except Exception as e:
                    print(f"Erro ao remover arquivo de log {file_path}: {str(e)}")
            
            # Após a rotação por servidor, limitar o número total de arquivos na pasta
            self._limitar_total_logs(100)  # Limite global de 100 arquivos
        
        except Exception as e:
            print(f"Erro durante rotação de logs: {str(e)}")
    
    def _limitar_total_logs(self, max_total=100):
        """
        Limita o número total de arquivos de log na pasta logs,
        independente de qual servidor gerou os arquivos.
        
        Args:
            max_total: Número máximo total de arquivos de log (padrão: 100)
        """
        try:
            # Obter todos os arquivos de log na pasta
            all_logs = []
            for filename in os.listdir(self.log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(self.log_dir, filename)
                    mod_time = os.path.getmtime(file_path)
                    all_logs.append((file_path, mod_time))
            
            # Se o número total de logs excede o limite
            if len(all_logs) > max_total:
                # Ordenar por data de modificação (mais antigos primeiro)
                all_logs.sort(key=lambda x: x[1])
                
                # Determinar quantos arquivos devem ser removidos
                to_remove = len(all_logs) - max_total
                
                # Remover os arquivos mais antigos
                for i in range(to_remove):
                    try:
                        file_path = all_logs[i][0]
                        os.remove(file_path)
                        print(f"Limite global: {os.path.basename(file_path)} removido")
                    except Exception as e:
                        print(f"Erro ao remover arquivo de log {all_logs[i][0]}: {str(e)}")
        
        except Exception as e:
            print(f"Erro ao limitar total de logs: {str(e)}")
    
    def stop_server(self, server_name):
        """
        Para um servidor.
        
        Args:
            server_name: Nome do servidor
            
        Returns:
            bool: True se o servidor foi parado com sucesso
        """
        server = self.get_server(server_name)
        if not server:
            return False
        
        # Verificar se o servidor está em execução
        if server.status not in [ServerStatus.RUNNING, ServerStatus.STARTING]:
            show_info_message(
                "Informação", 
                f"O servidor '{server_name}' não está em execução."
            )
            return False
        
        # Definir status
        server.status = ServerStatus.STOPPING
        self._notify_status_changed(server)
        
        # Iniciar thread para parar o servidor
        threading.Thread(
            target=self._stop_server_thread,
            args=(server,),
            daemon=True
        ).start()
        
        return True
    
    def _stop_server_thread(self, server):
        """
        Thread que para o servidor.
        
        Args:
            server: O servidor a ser parado
        """
        try:
            # Verificar se o processo existe
            if server.process:
                # Adicionar log
                stop_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Parando servidor '{server.name}'...\n"
                self._add_log(server, stop_msg)
                
                # Gravar no arquivo de log
                if server.log_file and os.path.exists(server.log_file):
                    try:
                        with open(server.log_file, "a", encoding="utf-8") as log_file:
                            log_file.write(stop_msg)
                    except:
                        pass
                
                # Obter PID do processo
                pid = server.process.pid
                
                try:
                    # Usar psutil para encontrar o processo pelo PID
                    processo = psutil.Process(pid)
                    processo_info = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Encerrando processo {pid}...\n"
                    self._add_log(server, processo_info)
                    
                    # Encerra o processo principal
                    processo.terminate()
                    
                    # Aguarda o processo encerrar por até 5 segundos
                    gone, alive = psutil.wait_procs([processo], timeout=5)
                    
                    # Se ainda estiver executando, força encerramento
                    if processo in alive:
                        kill_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processo não respondeu, forçando encerramento...\n"
                        self._add_log(server, kill_msg)
                        processo.kill()
                    
                    # Verifica se há processos filhos relacionados
                    try:
                        # Encontrar todos os processos filhos
                        children = processo.children(recursive=True)
                        if children:
                            child_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Encerrando {len(children)} processos filhos...\n"
                            self._add_log(server, child_msg)
                            
                            # Encerra todos os processos filhos
                            for child in children:
                                try:
                                    child.terminate()
                                except:
                                    pass
                            
                            # Aguarda processos filhos encerrarem
                            gone, alive = psutil.wait_procs(children, timeout=3)
                            
                            # Força encerramento de quaisquer processos filhos restantes
                            for child in alive:
                                try:
                                    child.kill()
                                except:
                                    pass
                    except:
                        pass
                    
                    # Verificar o código de retorno do processo original
                    return_code = None
                    if server.process:
                        return_code = server.process.poll()
                    
                    # Se o código de retorno for 15 (SIGTERM), isso é normal em um processo de encerramento
                    # então não vamos considerá-lo como um erro
                    if return_code == 15:
                        success_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Servidor '{server.name}' encerrado normalmente (SIGTERM)\n"
                        self._add_log(server, success_msg)
                    else:
                        # Adiciona mensagem de sucesso ao log
                        success_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Servidor '{server.name}' encerrado com sucesso\n"
                        self._add_log(server, success_msg)
                    
                    # Gravar no arquivo de log
                    if server.log_file and os.path.exists(server.log_file):
                        try:
                            with open(server.log_file, "a", encoding="utf-8") as log_file:
                                log_file.write(success_msg)
                        except:
                            pass
                
                except psutil.NoSuchProcess:
                    err_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processo {pid} não encontrado\n"
                    self._add_log(server, err_msg)
                
                except psutil.AccessDenied:
                    err_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Acesso negado ao encerrar processo {pid}\n"
                    self._add_log(server, err_msg)
                    
                    # Tentar terminar usando o processo original
                    try:
                        server.process.terminate()
                        time.sleep(1)
                        if server.process.poll() is None:
                            server.process.kill()
                    except:
                        pass
                
                except Exception as e:
                    err_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erro ao encerrar processo: {str(e)}\n"
                    self._add_log(server, err_msg)
            
            # Buscar processos pelo nome do script (caso o PID tenha mudado)
            try:
                script_name = os.path.basename(server.script_path)
                
                # Verificar todos os processos Python em execução
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info['cmdline']
                        if not cmdline:
                            continue
                        
                        # Procura pelo nome exato do script nos argumentos do processo
                        if any(arg.endswith('/' + script_name) or arg.endswith('\\' + script_name) or arg == script_name for arg in cmdline):
                            pid = proc.info['pid']
                            proc_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Encontrado processo adicional {pid} executando {script_name}, encerrando...\n"
                            self._add_log(server, proc_msg)
                            
                            # Encerrar o processo
                            processo = psutil.Process(pid)
                            processo.terminate()
                            
                            # Espera até 3 segundos para terminar
                            gone, alive = psutil.wait_procs([processo], timeout=3)
                            if processo in alive:
                                processo.kill()
                    except:
                        continue
            except:
                pass
            
            # Registrar hora de término
            server.stop_time = datetime.now()
            server.status = ServerStatus.STOPPED
            server.process = None
            self._notify_status_changed(server)
        
        except Exception as e:
            # Registrar erro
            error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erro ao parar servidor '{server.name}': {str(e)}\n"
            self._add_log(server, error_msg)
            
            # Tentar gravar no arquivo de log
            if server.log_file and os.path.exists(server.log_file):
                try:
                    with open(server.log_file, "a", encoding="utf-8") as log_file:
                        log_file.write(error_msg)
                except:
                    pass
            
            # Mesmo em caso de erro no encerramento, vamos mudar para STOPPED
            # já que o processo provavelmente foi encerrado de qualquer forma
            server.status = ServerStatus.STOPPED
            server.process = None
            self._notify_status_changed(server)
    
    def restart_server(self, server_name):
        """
        Reinicia um servidor.
        
        Args:
            server_name: Nome do servidor
            
        Returns:
            bool: True se o servidor foi reiniciado com sucesso
        """
        server = self.get_server(server_name)
        if not server:
            return False
        
        # Se o servidor estiver em execução, pará-lo primeiro
        if server.status in [ServerStatus.RUNNING, ServerStatus.STARTING]:
            def on_stop_complete():
                # Remover callback temporário
                self.on_server_status_changed = old_callback
                # Iniciar servidor
                self.start_server(server_name)
            
            # Salvar callback atual e definir callback temporário
            old_callback = self.on_server_status_changed
            self.on_server_status_changed = on_stop_complete
            
            # Parar servidor
            return self.stop_server(server_name)
        
        # Se não estiver em execução, iniciar diretamente
        return self.start_server(server_name)
    
    def get_server_logs(self, server_name, max_lines=None):
        """
        Obtém os logs de um servidor.
        
        Args:
            server_name: Nome do servidor
            max_lines: Número máximo de linhas a retornar (opcional)
            
        Returns:
            list: Lista de logs
        """
        server = self.get_server(server_name)
        if not server:
            return []
        
        # Retornar os logs mais recentes
        if max_lines:
            return server.logs[-max_lines:]
        
        return server.logs
    
    def _add_log(self, server, log_entry):
        """
        Adiciona uma entrada de log ao servidor.
        
        Args:
            server: O servidor
            log_entry: A entrada de log
        """
        # Adicionar log ao servidor
        server.logs.append(log_entry)
        
        # Limitar o número de logs em memória
        max_logs = 1000
        if len(server.logs) > max_logs:
            server.logs = server.logs[-max_logs:]
        
        # Notificar listeners
        if self.on_log_added:
            try:
                self.on_log_added(server.name, log_entry)
            except:
                pass
    
    def _notify_status_changed(self, server):
        """
        Notifica os listeners sobre a mudança de status de um servidor.
        
        Args:
            server: O servidor
        """
        if self.on_server_status_changed:
            try:
                self.on_server_status_changed(server.name, server.status)
            except:
                pass
        
        # Salvar a lista de servidores
        self._save_servers()

    def check_servers_status(self):
        """
        Verifica o status atual de todos os servidores com base nos processos em execução
        no sistema operacional.

        Esta função é útil para atualizar o status dos servidores quando a interface é iniciada
        ou quando o usuário solicita uma atualização manual.
        
        Returns:
            list: Lista de tuplas (nome_servidor, status_anterior, status_atual) dos servidores cujo status foi alterado
        """
        status_changes = []
        
        # Obter todos os processos Python uma única vez para reduzir chamadas de sistema
        python_processes = []
        try:
            # Filtrar apenas processos Python relevantes para reduzir o processamento
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower() and proc.info['cmdline']:
                        python_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception:
            pass
            
        # Para cada servidor na lista
        for server in self.servers:
            previous_status = server.status
            
            # Sempre verificar o status real, independente do status salvo
            is_running = False
            
            # Verificar se o processo existe usando o PID
            if server.process and server.process.pid:
                try:
                    # Verificar se o processo com este PID ainda existe
                    process = psutil.Process(server.process.pid)
                    if process.is_running() and not process.status() == psutil.STATUS_ZOMBIE:
                        is_running = True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Processo não existe mais ou não temos permissão para acessá-lo
                    is_running = False
            
            # Se o processo não foi encontrado pelo PID e temos um caminho de script válido,
            # buscar nos processos filtrados previamente
            if not is_running and server.script_path:
                script_name = os.path.basename(server.script_path)
                
                # Procurar apenas nos processos Python já identificados
                for proc in python_processes:
                    try:
                        cmdline = proc.info['cmdline']
                        # Usar uma verificação mais rigorosa e eficiente para o nome do script
                        if any(arg.endswith('/' + script_name) or arg.endswith('\\' + script_name) or arg == script_name for arg in cmdline):
                            is_running = True
                            # Atualizar a referência do processo associado ao servidor
                            try:
                                # Criar um objeto process simples com pid para referência
                                class DummyProcess:
                                    def __init__(self, pid):
                                        self.pid = pid
                                server.process = DummyProcess(proc.info['pid'])
                            except:
                                # Em caso de erro, apenas marcar como em execução
                                pass
                            break
                    except:
                        continue
            
            # Atualizar o status do servidor apenas se houver mudança
            if is_running and server.status != ServerStatus.RUNNING:
                server.status = ServerStatus.RUNNING
                status_changes.append((server.name, previous_status, server.status))
                self._notify_status_changed(server)
            elif not is_running and server.status != ServerStatus.STOPPED:
                server.status = ServerStatus.STOPPED
                server.process = None
                status_changes.append((server.name, previous_status, server.status))
                self._notify_status_changed(server)
        
        # Limpar memória explicitamente
        python_processes = None
        
        return status_changes

    def check_duplicate_processes(self):
        """
        Verifica se existem processos duplicados para os servidores.
        Considera a relação pai-filho entre processos, onde processos relacionados
        nessa hierarquia contam como um único processo.
        
        Returns:
            dict: Dicionário com nomes de servidores como chaves e listas de grupos de processos como valores
        """
        duplicates = {}
        
        # Obter todos os processos Python uma única vez
        python_processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower() and proc.info['cmdline']:
                        python_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception:
            pass
        
        # Para cada servidor, identificar processos e suas relações
        for server in self.servers:
            if server.script_path:
                script_name = os.path.basename(server.script_path)
                
                # Encontrar todos os processos para este script
                script_processes = []
                for proc in python_processes:
                    try:
                        cmdline = proc.info['cmdline']
                        if any(arg.endswith('/' + script_name) or arg.endswith('\\' + script_name) or arg == script_name for arg in cmdline):
                            script_processes.append(proc)
                    except:
                        continue
                
                # Se não encontrou pelo menos 2 processos, não pode ter duplicados
                if len(script_processes) < 2:
                    continue
                
                # Agrupar processos baseado nas relações pai-filho
                process_groups = self._group_related_processes(script_processes)
                
                # Se houver mais de um grupo, temos processos realmente duplicados
                if len(process_groups) > 1:
                    # Armazenar os grupos de PIDs
                    duplicates[server.name] = [
                        [proc.info['pid'] for proc in group] 
                        for group in process_groups
                    ]
        
        return duplicates
    
    def _group_related_processes(self, processes):
        """
        Agrupa processos baseados na relação pai-filho.
        
        Args:
            processes: Lista de processos para agrupar
            
        Returns:
            list: Lista de grupos de processos, onde cada grupo contém processos relacionados
        """
        # Crie um dicionário para mapear PIDs para processos
        pid_to_proc = {proc.info['pid']: proc for proc in processes}
        
        # Construa um grafo de relações pai-filho
        parent_child = {}
        for proc in processes:
            pid = proc.info['pid']
            ppid = proc.info.get('ppid', 0)
            
            # Se o pai também está na nossa lista, estabeleça a relação
            if ppid in pid_to_proc:
                if ppid not in parent_child:
                    parent_child[ppid] = []
                parent_child[ppid].append(pid)
        
        # Encontre processos "raiz" (que não têm pai na nossa lista ou têm pai fora da lista)
        roots = []
        for proc in processes:
            pid = proc.info['pid']
            ppid = proc.info.get('ppid', 0)
            
            # Se o pai não está na nossa lista ou o processo não tem um pai
            if ppid not in pid_to_proc:
                roots.append(pid)
        
        # Função para percorrer a árvore e coletar todos os processos relacionados
        def collect_tree(root_pid, visited=None):
            if visited is None:
                visited = set()
            
            # Evite ciclos
            if root_pid in visited:
                return []
            
            visited.add(root_pid)
            result = [pid_to_proc[root_pid]]
            
            # Adicione todos os filhos e seus descendentes
            children = parent_child.get(root_pid, [])
            for child_pid in children:
                result.extend(collect_tree(child_pid, visited))
                
            return result
        
        # Colete todos os grupos de processos relacionados
        groups = []
        visited_pids = set()
        
        # Primeiro, comece pelos processos raiz
        for root_pid in roots:
            if root_pid not in visited_pids:
                group = collect_tree(root_pid)
                visited_pids.update(proc.info['pid'] for proc in group)
                groups.append(group)
        
        # Verifique se há processos que não foram visitados (talvez devido a ciclos)
        for proc in processes:
            pid = proc.info['pid']
            if pid not in visited_pids:
                # Tente construir um grupo a partir deste processo
                group = collect_tree(pid)
                if group:
                    visited_pids.update(proc.info['pid'] for proc in group)
                    groups.append(group)
        
        return groups

# Função para testar o módulo individualmente
def main():
    """Função principal para teste do módulo."""
    root = tk.Tk()
    root.title("Gerenciador de Servidores MCP")
    
    # Configurar estilo
    style = ttk.Style()
    style.theme_use("clam")  # Usa um tema mais moderno
    
    # Configurar estilos personalizados
    style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground="#1E88E5")
    style.configure("ServerTitle.TLabel", font=("Segoe UI", 14, "bold"))
    style.configure("Card.TFrame", background="white", relief="raised", borderwidth=1)
    style.configure("Success.TButton", background="#4CAF50")
    style.configure("Danger.TButton", background="#F44336")
    
    # Criar e adicionar o gerenciador de servidores
    server_manager = ServerManager(root)
    server_manager.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Dimensões da janela
    root.geometry("800x600")
    root.mainloop()

if __name__ == "__main__":
    main()
