#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import platform
import subprocess
import psutil
import socket
import time
import re
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Inicializa o console do Rich para saída formatada
console = Console()

def verificar_e_ativar_ambiente():
    """Verifica se o ambiente virtual mencionado no log.txt está ativado, e o ativa caso necessário."""
    try:
        # Verificar se o arquivo log.txt existe no diretório atual ou no diretório pai
        log_paths = [
            "log.txt",                                          # Diretório atual
            os.path.join("..", "log.txt"),                       # Diretório pai
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.txt"),        # Diretório do script
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log.txt")  # Diretório pai do script
        ]
        
        log_path = None
        for path in log_paths:
            if os.path.exists(path):
                log_path = path
                break
        
        if not log_path:
            console.print("[yellow]Arquivo log.txt não encontrado em nenhum dos caminhos pesquisados. O ambiente virtual não pode ser ativado automaticamente.[/yellow]")
            return False
        
        # Ler o log.txt para obter informações do projeto
        with open(log_path, "r", encoding="utf-8") as f:
            conteudo_log = f.read()
        
        # Extrair o caminho do projeto
        caminho_match = re.search(r"Caminho do Projeto: (.+)", conteudo_log)
        if not caminho_match:
            console.print("[yellow]Não foi possível encontrar o caminho do projeto no log.txt.[/yellow]")
            return False
        
        caminho_projeto = caminho_match.group(1).strip()
        
        # Verificar se o diretório do projeto existe
        if not os.path.exists(caminho_projeto):
            console.print(f"[yellow]O diretório do projeto não foi encontrado: {caminho_projeto}[/yellow]")
            return False
        
        # Verificar se o ambiente virtual está ativo
        venv_ativo = False
        
        # No Windows, verificamos a variável VIRTUAL_ENV
        if 'VIRTUAL_ENV' in os.environ:
            venv_ativo = True
        
        # Verificar se existe um ambiente virtual no projeto
        venv_path = os.path.join(caminho_projeto, ".venv")
        if not os.path.exists(venv_path):
            console.print(f"[yellow]Não foi encontrado ambiente virtual em: {venv_path}[/yellow]")
            return False
        
        # Se o ambiente virtual não estiver ativo, ativá-lo
        if not venv_ativo:
            # Determinar caminhos de ativação do ambiente virtual
            if platform.system() == "Windows":
                activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
                python_exe = os.path.join(venv_path, "Scripts", "python.exe")
            else:
                activate_script = os.path.join(venv_path, "bin", "activate")
                python_exe = os.path.join(venv_path, "bin", "python")
            
            if not os.path.exists(activate_script):
                console.print(f"[yellow]Script de ativação não encontrado: {activate_script}[/yellow]")
                return False
            
            # Em vez de reiniciar em uma nova janela, vamos modificar as variáveis de ambiente
            # para simular a ativação do ambiente virtual
            if platform.system() == "Windows":
                # No Windows, precisamos executar o script de ativação e capturar as variáveis de ambiente alteradas
                # Cria um script temporário para capturar o ambiente
                temp_script = "temp_env_capture.bat"
                with open(temp_script, "w", encoding="cp1252") as f:
                    f.write("@echo off\n")
                    f.write(f"call \"{activate_script}\"\n")
                    f.write("set > env_vars.txt\n")
                
                # Executa o script para capturar as variáveis de ambiente
                subprocess.run(["cmd", "/c", temp_script], capture_output=True)
                
                # Lê as variáveis de ambiente capturadas
                with open("env_vars.txt", "r") as f:
                    env_vars = f.readlines()
                
                # Atualiza as variáveis de ambiente do processo atual
                for line in env_vars:
                    if "=" in line:
                        name, value = line.strip().split("=", 1)
                        os.environ[name] = value
                
                # Limpa arquivos temporários
                if os.path.exists(temp_script):
                    os.remove(temp_script)
                if os.path.exists("env_vars.txt"):
                    os.remove("env_vars.txt")
                
                console.print(f"[green]Ambiente virtual ativado em background com sucesso![/green]")
            else:
                # No Linux/macOS, podemos ativar diretamente
                source_cmd = f"source {activate_script}"
                subprocess.run(source_cmd, shell=True, executable="/bin/bash")
                console.print(f"[green]Ambiente virtual ativado em background com sucesso![/green]")
            
            # Defina a variável de ambiente para indicar que o ambiente virtual está ativado
            os.environ['VIRTUAL_ENV'] = venv_path
            # Adiciona o diretório bin/Scripts ao PATH
            if platform.system() == "Windows":
                bin_dir = os.path.join(venv_path, "Scripts")
            else:
                bin_dir = os.path.join(venv_path, "bin")
            os.environ['PATH'] = bin_dir + os.pathsep + os.environ['PATH']
            
        return True
    
    except Exception as e:
        console.print(f"[red]Erro ao verificar/ativar o ambiente virtual: {str(e)}[/red]")
        return False

# Obtém o PID do processo atual para filtrar da listagem
CURRENT_PID = os.getpid()

def cabecalho(titulo):
    """Exibe um cabeçalho estilizado no console."""
    console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
    console.print(f"[bold cyan]{titulo.center(60)}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")

def obter_caminhos_config():
    """Retorna os caminhos para os arquivos de configuração do Cursor e Claude Desktop."""
    home = os.path.expanduser("~")
    
    # Caminho para o arquivo de configuração do Cursor
    cursor_config = os.path.join(home, ".cursor", "mcp.json")
    
    # Caminho para o arquivo de configuração do Claude Desktop
    if platform.system() == "Windows":
        claude_config = os.path.join(home, "AppData", "Roaming", "Claude", "claude_desktop_config.json")
    else:  # macOS
        claude_config = os.path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json")
    
    return cursor_config, claude_config

def carregar_configuracoes():
    """Carrega as configurações dos servidores MCP dos arquivos de configuração."""
    cursor_config, claude_config = obter_caminhos_config()
    configs = {
        "cursor": {"caminho": cursor_config, "servidores": {}, "status": "não encontrado"},
        "claude": {"caminho": claude_config, "servidores": {}, "status": "não encontrado"}
    }
    
    # Tenta carregar a configuração do Cursor
    if os.path.exists(cursor_config):
        try:
            with open(cursor_config, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if 'mcpServers' in dados:
                    configs["cursor"]["servidores"] = dados['mcpServers']
                    configs["cursor"]["status"] = "carregado"
                    console.print(f"[dim]Configuração do Cursor carregada: {len(dados['mcpServers'])} servidores[/dim]")
        except Exception as e:
            configs["cursor"]["status"] = f"erro: {str(e)}"
            console.print(f"[yellow]Erro ao carregar configuração do Cursor: {str(e)}[/yellow]")
    
    # Tenta carregar a configuração do Claude Desktop
    if os.path.exists(claude_config):
        try:
            with open(claude_config, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if 'mcpServers' in dados:
                    configs["claude"]["servidores"] = dados['mcpServers']
                    configs["claude"]["status"] = "carregado"
                    console.print(f"[dim]Configuração do Claude carregada: {len(dados['mcpServers'])} servidores[/dim]")
        except Exception as e:
            configs["claude"]["status"] = f"erro: {str(e)}"
            console.print(f"[yellow]Erro ao carregar configuração do Claude: {str(e)}[/yellow]")
    
    return configs

def verificar_porta_em_uso(porta):
    """Verifica se uma porta específica está em uso."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', porta)) == 0
    except:
        return False

def obter_processos_python():
    """Retorna todos os processos Python em execução."""
    processos_python = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cwd', 'ppid']):
        try:
            # Filtra apenas processos Python
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                processos_python.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return processos_python

def identificar_servidores_mcp(processos):
    """Identifica quais processos Python estão executando servidores MCP."""
    servidores_mcp = []
    grupos_servidores = {}  # Para agrupar processos relacionados
    processos_filhos = set()  # Para identificar processos filhos
    
    # Primeiro passo: identificar todos os processos MCP
    for proc in processos:
        try:
            # Ignora o processo atual
            if proc.info['pid'] == CURRENT_PID:
                continue
                
            cmdline = proc.info['cmdline']
            if not cmdline:
                continue
            
            # Identifica servidor MCP pelos parâmetros na linha de comando
            is_mcp = False
            
            # Verifica se é o launcher.py sendo executado (não o processo atual)
            is_launcher = False
            for cmd in cmdline:
                if "launcher.py" in cmd:
                    is_launcher = True
                    break
            
            # Se for o script launcher.py, pula este processo
            if is_launcher:
                continue
            
            # Palavras-chave para identificar processos MCP
            keywords = ["mcp", "demon.py", ".py"]
            for keyword in keywords:
                for cmd in cmdline:
                    if keyword in cmd:
                        is_mcp = True
                        break
                if is_mcp:
                    break
            
            if is_mcp:
                # Tenta encontrar a porta do servidor
                porta = None
                nome_projeto = "Desconhecido"
                arquivo_python = "Desconhecido"
                
                # Procura pelo arquivo .py no comando
                for i, cmd in enumerate(cmdline):
                    # Verifica se é um arquivo .py
                    if cmd.endswith('.py'):
                        arquivo_python = os.path.basename(cmd)
                        break
                    # Caso especial para "run" seguido do arquivo .py
                    elif cmd == 'run' and i+1 < len(cmdline) and cmdline[i+1].endswith('.py'):
                        arquivo_python = os.path.basename(cmdline[i+1])
                        break
                    # Verifica outros padrões comuns
                    elif 'python' in cmd.lower() and i+1 < len(cmdline) and cmdline[i+1].endswith('.py'):
                        arquivo_python = os.path.basename(cmdline[i+1])
                        break
                
                # Obtém o diretório e nome do projeto
                try:
                    diretorio = proc.info['cwd']
                    
                    # Tenta identificar o nome do ambiente virtual
                    partes_caminho = diretorio.split(os.path.sep)
                    
                    # Se o caminho contém "demon" ou "mcp_server", usa-o como nome do projeto
                    if "demon" in partes_caminho:
                        nome_projeto = "demon"
                    elif "mcp_server" in partes_caminho:
                        nome_projeto = "demon"  # Também usar "demon" para caminhos antigos com "mcp_server"
                    else:
                        # Caso contrário, usa o último diretório
                        nome_projeto = os.path.basename(diretorio)
                except Exception:
                    nome_projeto = "Desconhecido"
                
                # Verifica se há porta específica definida
                for i, cmd in enumerate(cmdline):
                    if cmd == "--port" and i+1 < len(cmdline):
                        try:
                            porta = int(cmdline[i+1])
                        except:
                            pass
                    elif cmd.startswith("--port="):
                        try:
                            porta = int(cmd.split("=")[1])
                        except:
                            pass
                
                # Verifica se usa transporte stdio
                usando_stdio = False
                for i, cmd in enumerate(cmdline):
                    if cmd == 'transport=stdio' or cmd == '--transport=stdio' or cmd == '-t=stdio':
                        usando_stdio = True
                        break
                    if i+2 < len(cmdline) and (cmd == 'transport' or cmd == '--transport' or cmd == '-t') and cmdline[i+1] == 'stdio':
                        usando_stdio = True
                        break
                
                # Porta padrão para MCP se não foi encontrada
                if not porta:
                    porta = 8080
                
                # Formato do projeto: nome_projeto/arquivo_python
                nome_completo = f"{nome_projeto}/{arquivo_python}"
                
                # Verifica se a porta está ativa
                porta_ativa = verificar_porta_em_uso(porta)
                
                # Define o tipo de atividade com base na porta e no modo de transporte
                if porta_ativa:
                    tipo_ativo = "http"  # Ativo via HTTP (porta)
                elif usando_stdio:
                    tipo_ativo = "stdio"  # Ativo via stdio (sem porta)
                else:
                    tipo_ativo = None  # Inativo
                
                # Adiciona à lista de servidores
                servidor = {
                    'pid': proc.info['pid'],
                    'ppid': proc.info.get('ppid', 0),  # Processo pai, se disponível
                    'nome_projeto': nome_completo,
                    'nome_ambiente': nome_projeto,
                    'arquivo_python': arquivo_python,
                    'porta': porta,
                    'porta_ativa': porta_ativa,
                    'tipo_ativo': tipo_ativo,
                    'tempo_execucao': time.time() - proc.info['create_time'],
                    'diretorio': proc.info['cwd'],
                    'comando': ' '.join(cmdline),
                    'processos_relacionados': [],  # Lista para armazenar PIDs de processos relacionados
                    'e_processo_pai': True,  # Assume inicialmente que é processo pai
                    'processo_pai_pid': None  # Será preenchido para processos filhos
                }
                
                # Agrupa servidores pelo nome do arquivo para identificar processos relacionados
                chave_agrupamento = f"{nome_projeto}_{arquivo_python}"
                if chave_agrupamento not in grupos_servidores:
                    grupos_servidores[chave_agrupamento] = []
                grupos_servidores[chave_agrupamento].append(servidor)
                
                servidores_mcp.append(servidor)
        
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Segundo passo: identificar relações pai-filho e marcar os processos filhos
    for i, servidor in enumerate(servidores_mcp):
        pid = servidor['pid']
        ppid = servidor['ppid']
        
        # Verifica se este processo é filho de outro processo MCP
        for outro_servidor in servidores_mcp:
            if outro_servidor['pid'] == ppid:
                # Este é um processo filho
                processos_filhos.add(pid)
                servidor['e_processo_pai'] = False
                servidor['processo_pai_pid'] = ppid
                
                # Adiciona à lista de processos relacionados do pai
                outro_servidor['processos_relacionados'].append(pid)
    
    # Terceiro passo: filtrar apenas os processos pai
    servidores_filtrados = [s for s in servidores_mcp if s['e_processo_pai']]
    
    return servidores_filtrados

def formatar_tempo(segundos):
    """Formata o tempo em segundos para um formato legível."""
    if segundos < 60:
        return f"{int(segundos)}s"
    elif segundos < 3600:
        return f"{int(segundos / 60)}m {int(segundos % 60)}s"
    else:
        return f"{int(segundos / 3600)}h {int((segundos % 3600) / 60)}m"

def listar_servidores_configurados(configs):
    """Lista os servidores configurados nos arquivos de configuração."""
    cabecalho("SERVIDORES MCP CONFIGURADOS")
    
    servidores_unicos = set()
    
    # Cria uma tabela para os servidores do Cursor
    tabela_cursor = Table(title="Cursor MCP Servers", show_header=True, header_style="bold")
    tabela_cursor.add_column("Nome", style="cyan")
    tabela_cursor.add_column("Comando", style="green")
    tabela_cursor.add_column("Diretório", style="yellow")
    tabela_cursor.add_column("Arquivo", style="magenta")
    
    # Adiciona servidores do Cursor à tabela
    if configs["cursor"]["status"] == "carregado":
        for nome, config in configs["cursor"]["servidores"].items():
            servidores_unicos.add(nome)
            
            # Extrai informações relevantes
            comando = config.get("command", "N/A")
            
            # Extrai diretório e arquivo .py dos argumentos
            diretorio = "N/A"
            arquivo = "N/A"
            
            args = config.get("args", [])
            for i, arg in enumerate(args):
                if arg == "--directory" and i+1 < len(args):
                    diretorio = args[i+1]
                elif arg == "run" and i+1 < len(args) and args[i+1].endswith('.py'):
                    arquivo = args[i+1]
            
            tabela_cursor.add_row(nome, comando, diretorio, arquivo)
    else:
        tabela_cursor.add_row("Erro", f"Configuração não encontrada: {configs['cursor']['status']}", "", "")
    
    # Cria uma tabela para os servidores do Claude Desktop
    tabela_claude = Table(title="Claude Desktop MCP Servers", show_header=True, header_style="bold")
    tabela_claude.add_column("Nome", style="cyan")
    tabela_claude.add_column("Comando", style="green")
    tabela_claude.add_column("Diretório", style="yellow")
    tabela_claude.add_column("Arquivo", style="magenta")
    
    # Adiciona servidores do Claude Desktop à tabela
    if configs["claude"]["status"] == "carregado":
        for nome, config in configs["claude"]["servidores"].items():
            servidores_unicos.add(nome)
            
            # Extrai informações relevantes
            comando = config.get("command", "N/A")
            
            # Extrai diretório e arquivo .py dos argumentos
            diretorio = "N/A"
            arquivo = "N/A"
            
            args = config.get("args", [])
            for i, arg in enumerate(args):
                if arg == "--directory" and i+1 < len(args):
                    diretorio = args[i+1]
                elif arg == "run" and i+1 < len(args) and args[i+1].endswith('.py'):
                    arquivo = args[i+1]
            
            tabela_claude.add_row(nome, comando, diretorio, arquivo)
    else:
        tabela_claude.add_row("Erro", f"Configuração não encontrada: {configs['claude']['status']}", "", "")
    
    # Exibe as tabelas
    console.print(tabela_cursor)
    console.print(tabela_claude)
    
    return len(servidores_unicos)

def listar_servidores_ativos(servidores_mcp):
    """Lista os servidores MCP ativos no sistema."""
    cabecalho("SERVIDORES MCP ATIVOS")
    
    if not servidores_mcp:
        console.print("[yellow]Nenhum servidor MCP ativo no momento.[/yellow]")
        return 0
    
    # Cria uma tabela para os servidores ativos
    tabela = Table(show_header=True, header_style="bold")
    tabela.add_column("PID", style="cyan")
    tabela.add_column("Nome", style="green")
    tabela.add_column("Arquivo", style="magenta")
    tabela.add_column("Tempo", style="dim")
    
    for servidor in servidores_mcp:
        # Adiciona a linha à tabela
        tabela.add_row(
            str(servidor['pid']),
            servidor['nome_ambiente'],
            servidor['arquivo_python'],
            formatar_tempo(servidor['tempo_execucao'])
        )
    
    console.print(tabela)
    return len(servidores_mcp)

def iniciar_servidor(configs):
    """Inicia um servidor MCP a partir das configurações."""
    cabecalho("INICIAR SERVIDOR MCP")
    
    # Combina todos os servidores disponíveis
    servidores_disponiveis = {}
    
    for cliente, config in configs.items():
        if config["status"] == "carregado":
            for nome, servidor in config["servidores"].items():
                servidores_disponiveis[nome] = {
                    "origem": cliente,
                    "config": servidor
                }
    
    if not servidores_disponiveis:
        console.print("[yellow]Nenhuma configuração de servidor encontrada.[/yellow]")
        return
    
    # Lista os servidores disponíveis
    console.print("[bold]Servidores disponíveis:[/bold]")
    for i, (nome, info) in enumerate(servidores_disponiveis.items(), 1):
        console.print(f"[cyan]{i}.[/cyan] {nome} [dim]({info['origem']})[/dim]")
    
    # Solicita ao usuário que escolha um servidor
    escolha = input("\nEscolha um servidor pelo número (ou 'q' para cancelar): ")
    if escolha.lower() == 'q':
        return
    
    try:
        idx = int(escolha) - 1
        if idx < 0 or idx >= len(servidores_disponiveis):
            console.print("[yellow]Escolha inválida.[/yellow]")
            return
        
        # Obtém o nome e configuração do servidor escolhido
        nome_servidor = list(servidores_disponiveis.keys())[idx]
        config_servidor = servidores_disponiveis[nome_servidor]["config"]
        
        console.print(f"\n[bold]Iniciando servidor:[/bold] {nome_servidor}")
        
        # Prepara o comando para iniciar o servidor
        comando = [config_servidor["command"]]
        comando.extend(config_servidor["args"])
        
        # Exibe o comando a ser executado
        comando_str = " ".join(comando)
        console.print(f"[green]Executando:[/green] {comando_str}")
        
        # Executa o servidor em background
        if platform.system() == "Windows":
            # No Windows, usa startupinfo para esconder a janela do console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(comando, startupinfo=startupinfo, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # No Linux/macOS
            subprocess.Popen(comando, start_new_session=True)
        
        console.print(f"[bold green]✓[/bold green] Servidor {nome_servidor} iniciado com sucesso!")
        
    except ValueError:
        console.print("[yellow]Escolha inválida. Digite um número.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Erro ao iniciar o servidor:[/bold red] {str(e)}")

def reiniciar_servidor(servidores_mcp):
    """Reinicia um servidor MCP específico."""
    cabecalho("REINICIAR SERVIDOR MCP")
    
    if not servidores_mcp:
        console.print("[yellow]Nenhum servidor MCP ativo no momento.[/yellow]")
        return
    
    # Lista os servidores disponíveis
    console.print("[bold]Servidores ativos:[/bold]")
    for i, servidor in enumerate(servidores_mcp, 1):
        status = "HTTP" if servidor['tipo_ativo'] == 'http' else "STDIO" if servidor['tipo_ativo'] == 'stdio' else "INATIVO"
        console.print(f"[cyan]{i}.[/cyan] {servidor['nome_ambiente']}/{servidor['arquivo_python']} (PID: {servidor['pid']}, Status: {status})")
    
    # Solicita ao usuário que escolha um servidor
    escolha = input("\nEscolha um servidor para reiniciar pelo número (ou 'q' para cancelar): ")
    if escolha.lower() == 'q':
        return
    
    try:
        idx = int(escolha) - 1
        if idx < 0 or idx >= len(servidores_mcp):
            console.print("[yellow]Escolha inválida.[/yellow]")
            return
        
        servidor = servidores_mcp[idx]
        
        # Encerra o processo
        try:
            processo = psutil.Process(servidor['pid'])
            processo.terminate()
            
            console.print(f"[yellow]Encerrando processo {servidor['pid']}...[/yellow]")
            
            # Aguarda o processo encerrar
            gone, alive = psutil.wait_procs([processo], timeout=3)
            if processo in alive:
                processo.kill()
                console.print(f"[yellow]Processo não respondeu, forçando encerramento...[/yellow]")
            
            console.print(f"[green]Processo {servidor['pid']} encerrado.[/green]")
            
            # Extrai o comando original
            comando = servidor['comando'].split()
            if not comando:
                console.print("[red]Não foi possível extrair o comando original.[/red]")
                return
            
            # Reinicia o servidor
            console.print("[green]Reiniciando servidor...[/green]")
            
            # Executa o servidor em background
            if platform.system() == "Windows":
                # No Windows, usa startupinfo para esconder a janela do console
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.Popen(comando, startupinfo=startupinfo, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=servidor['diretorio'])
            else:
                # No Linux/macOS
                subprocess.Popen(comando, start_new_session=True, cwd=servidor['diretorio'])
            
            console.print(f"[bold green]✓[/bold green] Servidor reiniciado com sucesso!")
            
        except psutil.NoSuchProcess:
            console.print(f"[yellow]Processo {servidor['pid']} não encontrado.[/yellow]")
        except psutil.AccessDenied:
            console.print(f"[red]Acesso negado ao encerrar processo {servidor['pid']}.[/red]")
        except Exception as e:
            console.print(f"[bold red]Erro ao reiniciar o servidor:[/bold red] {str(e)}")
            
    except ValueError:
        console.print("[yellow]Escolha inválida. Digite um número.[/yellow]")

def encerrar_servidor(servidores_mcp):
    """Encerra um servidor MCP específico."""
    cabecalho("ENCERRAR SERVIDOR MCP")
    
    if not servidores_mcp:
        console.print("[yellow]Nenhum servidor MCP ativo no momento.[/yellow]")
        return
    
    # Lista os servidores disponíveis
    console.print("[bold]Servidores ativos:[/bold]")
    for i, servidor in enumerate(servidores_mcp, 1):
        status = "HTTP" if servidor['tipo_ativo'] == 'http' else "STDIO" if servidor['tipo_ativo'] == 'stdio' else "INATIVO"
        console.print(f"[cyan]{i}.[/cyan] {servidor['nome_ambiente']}/{servidor['arquivo_python']} (PID: {servidor['pid']}, Status: {status})")
    
    # Solicita ao usuário que escolha um servidor
    escolha = input("\nEscolha um servidor para encerrar pelo número (ou 'q' para cancelar): ")
    if escolha.lower() == 'q':
        return
    
    try:
        idx = int(escolha) - 1
        if idx < 0 or idx >= len(servidores_mcp):
            console.print("[yellow]Escolha inválida.[/yellow]")
            return
        
        servidor = servidores_mcp[idx]
        
        # Encerra o processo
        try:
            processo = psutil.Process(servidor['pid'])
            console.print(f"[yellow]Encerrando processo {servidor['pid']}...[/yellow]")
            
            processo.terminate()
            
            # Aguarda o processo encerrar
            gone, alive = psutil.wait_procs([processo], timeout=3)
            if processo in alive:
                processo.kill()
                console.print(f"[yellow]Processo não respondeu, forçando encerramento...[/yellow]")
            
            console.print(f"[bold green]✓[/bold green] Servidor {servidor['nome_ambiente']}/{servidor['arquivo_python']} encerrado com sucesso!")
            
        except psutil.NoSuchProcess:
            console.print(f"[yellow]Processo {servidor['pid']} não encontrado.[/yellow]")
        except psutil.AccessDenied:
            console.print(f"[red]Acesso negado ao encerrar processo {servidor['pid']}.[/red]")
        except Exception as e:
            console.print(f"[bold red]Erro ao encerrar o servidor:[/bold red] {str(e)}")
            
    except ValueError:
        console.print("[yellow]Escolha inválida. Digite um número.[/yellow]")

def encerrar_todos_servidores(servidores_mcp):
    """Encerra todos os servidores MCP ativos."""
    cabecalho("ENCERRAR TODOS OS SERVIDORES MCP")
    
    if not servidores_mcp:
        console.print("[yellow]Nenhum servidor MCP ativo no momento.[/yellow]")
        return
    
    console.print(f"[bold yellow]Encerrando {len(servidores_mcp)} servidores MCP...[/bold yellow]")
    
    encerrados = 0
    falhas = 0
    
    for servidor in servidores_mcp:
        try:
            processo = psutil.Process(servidor['pid'])
            processo.terminate()
            
            # Aguarda o processo encerrar
            gone, alive = psutil.wait_procs([processo], timeout=2)
            if processo in alive:
                processo.kill()
            
            encerrados += 1
            console.print(f"[green]✓ Processo {servidor['pid']} ({servidor['nome_ambiente']}/{servidor['arquivo_python']}) encerrado.[/green]")
            
        except psutil.NoSuchProcess:
            console.print(f"[yellow]Processo {servidor['pid']} não encontrado.[/yellow]")
            falhas += 1
        except psutil.AccessDenied:
            console.print(f"[red]Acesso negado ao encerrar processo {servidor['pid']}.[/red]")
            falhas += 1
        except Exception as e:
            console.print(f"[red]Erro ao encerrar processo {servidor['pid']}: {str(e)}[/red]")
            falhas += 1
    
    if encerrados > 0:
        console.print(f"\n[bold green]✓ {encerrados} servidor(es) encerrado(s) com sucesso![/bold green]")
    
    if falhas > 0:
        console.print(f"[bold red]✗ {falhas} servidor(es) não pôde(puderam) ser encerrado(s).[/bold red]")

def mostrar_animacao_carregamento(duracao=2, simbolos=".:", mensagem="Carregando menu"):
    """Mostra uma animação de carregamento simples por um determinado tempo."""
    import sys
    import time
    
    # Número de caracteres para a animação
    comprimento_max = 15
    
    try:
        # Desabilita o buffer de saída para que a animação apareça em tempo real
        sys.stdout.flush()
        
        # Loop de animação até o tempo especificado
        inicio = time.time()
        i = 0
        while time.time() - inicio < duracao:
            # Alterna entre os símbolos
            char = simbolos[i % len(simbolos)]
            
            # Calcula a quantidade de caracteres com base no tempo decorrido
            progresso = min(int((time.time() - inicio) / duracao * comprimento_max), comprimento_max)
            
            # Constrói a string de animação
            barra = char * progresso
            
            # Imprime a mensagem e a barra de progresso
            print(f"\r{mensagem} {barra}", end='', flush=True)
            
            # Incrementa o contador e aguarda
            i += 1
            time.sleep(0.1)
        
        # Limpa a linha ao finalizar
        print("\r" + " " * (len(mensagem) + comprimento_max + 1) + "\r", end='', flush=True)
    
    except Exception as e:
        # Em caso de erro, simplesmente finaliza sem mostrar erro
        pass

def remover_servidor_configurado(configs):
    """Remove um servidor da configuração dos arquivos JSON dos clientes."""
    cabecalho("REMOVER SERVIDOR CONFIGURADO")
    
    # Combina todos os servidores disponíveis
    servidores_disponiveis = {}
    
    for cliente, config in configs.items():
        if config["status"] == "carregado":
            for nome, servidor in config["servidores"].items():
                servidores_disponiveis[f"{nome}_{cliente}"] = {
                    "nome": nome,
                    "origem": cliente,
                    "config": servidor,
                    "caminho_config": config["caminho"]
                }
    
    if not servidores_disponiveis:
        console.print("[yellow]Nenhuma configuração de servidor encontrada.[/yellow]")
        return
    
    # Lista os servidores disponíveis
    console.print("[bold]Servidores disponíveis para remoção:[/bold]")
    for i, (chave, info) in enumerate(servidores_disponiveis.items(), 1):
        console.print(f"[cyan]{i}.[/cyan] {info['nome']} [dim]({info['origem']})[/dim]")
    
    # Solicita ao usuário que escolha um servidor
    escolha = input("\nEscolha um servidor pelo número (ou 'q' para cancelar): ")
    if escolha.lower() == 'q':
        return
    
    try:
        idx = int(escolha) - 1
        if idx < 0 or idx >= len(servidores_disponiveis):
            console.print("[yellow]Escolha inválida.[/yellow]")
            return
        
        # Obtém o nome e configuração do servidor escolhido
        chave_servidor = list(servidores_disponiveis.keys())[idx]
        info_servidor = servidores_disponiveis[chave_servidor]
        nome_servidor = info_servidor["nome"]
        cliente_origem = info_servidor["origem"]
        caminho_config = info_servidor["caminho_config"]
        
        # Confirma a remoção
        confirmar = input(f"\nTem certeza que deseja remover o servidor '{nome_servidor}' ({cliente_origem})? (s/n): ")
        if confirmar.lower() != 's':
            console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
            return
        
        # Remove o servidor do arquivo de configuração
        try:
            # Carrega o arquivo de configuração
            with open(caminho_config, 'r', encoding='utf-8') as f:
                dados_config = json.load(f)
            
            # Remove o servidor da configuração
            if 'mcpServers' in dados_config and nome_servidor in dados_config['mcpServers']:
                del dados_config['mcpServers'][nome_servidor]
                
                # Salva o arquivo de configuração atualizado
                with open(caminho_config, 'w', encoding='utf-8') as f:
                    json.dump(dados_config, f, indent=2)
                
                console.print(f"[green]✓ Servidor '{nome_servidor}' removido da configuração do {cliente_origem}.[/green]")
            else:
                console.print(f"[yellow]Servidor '{nome_servidor}' não encontrado na configuração.[/yellow]")
        
        except Exception as e:
            console.print(f"[red]Erro ao remover servidor da configuração: {str(e)}[/red]")
            
    except ValueError:
        console.print("[yellow]Escolha inválida. Digite um número.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Erro ao remover o servidor:[/bold red] {str(e)}")

def mostrar_menu():
    """Mostra o menu principal do launcher."""
    cabecalho("LAUNCHER MCP")
    
    console.print("[bold cyan]Opções disponíveis:[/bold cyan]\n")
    console.print("1. [green]Listar servidores configurados[/green] (Cursor e Claude Desktop)")
    console.print("2. [green]Listar servidores ativos[/green] (Processos em execução)")
    console.print("3. [cyan]Iniciar servidor[/cyan] (A partir da configuração)")
    console.print("4. [cyan]Reiniciar servidor[/cyan] (Encerrar e iniciar novamente)")
    console.print("5. [yellow]Encerrar servidor específico[/yellow]")
    console.print("6. [red]Encerrar todos os servidores[/red]")
    console.print("7. [red]Remover servidor configurado[/red] (Exclui dos arquivos de configuração)")
    console.print("0. [bold]Sair[/bold]\n")
    
    opcao = input("Escolha uma opção: ")
    return opcao

def main():
    """Função principal do launcher."""
    try:
        # Verificar e ativar o ambiente virtual
        ambiente_ativado = verificar_e_ativar_ambiente()
        
        # Se o ambiente foi ativado com sucesso, mostra a animação
        if ambiente_ativado:
            mostrar_animacao_carregamento(duracao=2, simbolos=".:", mensagem="Carregando menu")
        
        while True:
            # Cada vez que o menu é exibido, atualiza as informações
            configs = carregar_configuracoes()
            processos_python = obter_processos_python()
            servidores_mcp = identificar_servidores_mcp(processos_python)
            
            opcao = mostrar_menu()
            
            if opcao == '1':
                total = listar_servidores_configurados(configs)
                print(f"\nTotal: {total} servidores configurados")
                input("\nPressione ENTER para continuar...")
                
            elif opcao == '2':
                total = listar_servidores_ativos(servidores_mcp)
                print(f"\nTotal: {total} servidores ativos")
                input("\nPressione ENTER para continuar...")
                
            elif opcao == '3':
                iniciar_servidor(configs)
                input("\nPressione ENTER para continuar...")
                
            elif opcao == '4':
                reiniciar_servidor(servidores_mcp)
                input("\nPressione ENTER para continuar...")
                
            elif opcao == '5':
                encerrar_servidor(servidores_mcp)
                input("\nPressione ENTER para continuar...")
                
            elif opcao == '6':
                encerrar_todos_servidores(servidores_mcp)
                input("\nPressione ENTER para continuar...")
                
            elif opcao == '7':
                remover_servidor_configurado(configs)
                input("\nPressione ENTER para continuar...")
                
            elif opcao == '0':
                cabecalho("ATÉ LOGO!")
                console.print("[green]Obrigado por usar o MCP Launcher![/green]")
                break
                
            else:
                console.print("[yellow]Opção inválida. Por favor, tente novamente.[/yellow]")
                time.sleep(1)
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Operação interrompida pelo usuário.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Erro não esperado:[/bold red] {str(e)}")
    
    console.print("[dim]Encerrando...[/dim]")

if __name__ == "__main__":
    main() 