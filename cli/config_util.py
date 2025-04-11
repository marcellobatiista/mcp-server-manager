import json
import os
import platform
import sys
from pathlib import Path

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

def atualizar_configuracoes(nome_servidor, comando, argumentos):
    """
    Atualiza automaticamente os arquivos de configuração do Cursor e Claude Desktop.
    
    Args:
        nome_servidor: Nome do servidor MCP a ser adicionado
        comando: Caminho do executável (geralmente uv)
        argumentos: Lista de argumentos para o comando
        
    Returns:
        dict: Resultado da operação com status de cada arquivo
    """
    cursor_config_path, claude_config_path = obter_caminhos_config()
    resultado = {
        "cursor": {"status": "falha", "mensagem": ""},
        "claude": {"status": "falha", "mensagem": ""}
    }
    
    # Configuração a ser adicionada
    nova_config = {
        "command": comando,
        "args": argumentos
    }
    
    # Atualizar configuração do Cursor
    try:
        atualizar_arquivo_configuracao(cursor_config_path, nome_servidor, nova_config)
        resultado["cursor"] = {"status": "sucesso", "caminho": cursor_config_path}
    except Exception as e:
        resultado["cursor"] = {"status": "falha", "mensagem": str(e)}
    
    # Atualizar configuração do Claude Desktop
    try:
        atualizar_arquivo_configuracao(claude_config_path, nome_servidor, nova_config)
        resultado["claude"] = {"status": "sucesso", "caminho": claude_config_path}
    except Exception as e:
        resultado["claude"] = {"status": "falha", "mensagem": str(e)}
    
    return resultado

def atualizar_arquivo_configuracao(caminho_arquivo, nome_servidor, nova_config):
    """
    Atualiza um arquivo de configuração específico.
    
    Args:
        caminho_arquivo: Caminho do arquivo de configuração
        nome_servidor: Nome do servidor MCP
        nova_config: Configuração a ser adicionada
    """
    # Verificar se o diretório existe, se não, criar
    diretorio = os.path.dirname(caminho_arquivo)
    if not os.path.exists(diretorio):
        os.makedirs(diretorio, exist_ok=True)
    
    # Se o arquivo não existir, criar com a estrutura básica
    if not os.path.exists(caminho_arquivo):
        config = {"mcpServers": {}}
    else:
        # Ler configuração existente
        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            # Se o arquivo existe mas não é um JSON válido
            config = {"mcpServers": {}}
        
        # Garantir que a estrutura de mcpServers existe
        if "mcpServers" not in config:
            config["mcpServers"] = {}
    
    # Adicionar ou atualizar a configuração do servidor
    config["mcpServers"][nome_servidor] = nova_config
    
    # Salvar o arquivo atualizado
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4) 