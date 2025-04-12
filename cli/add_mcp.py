import os
import sys
import json
import platform
import subprocess
import re
from pathlib import Path
import config_util  # Importar o módulo de utilitários de configuração
import time

def cabecalho(titulo):
    """Exibe um cabeçalho estilizado no console."""
    largura = 70
    print("\n" + "=" * largura)
    print(f"{titulo.center(largura)}")
    print("=" * largura)

def verificar_ambiente():
    """Verifica se o ambiente básico já foi configurado pelo quick_setup.py."""
    # Verificar se a pasta mcp_server existe
    if not os.path.exists("mcp_server"):
        print("Erro: A pasta 'mcp_server' não foi encontrada!")
        print("Execute primeiro o script quick_setup.py para criar o ambiente básico.")
        return False
    
    # Determinar o caminho do projeto ("mcp_server")
    projeto_dir = "mcp_server"
    
    # Verificar se o ambiente virtual existe
    venv_path = os.path.join(projeto_dir, ".venv")
    if not os.path.exists(venv_path) or not os.path.isdir(venv_path):
        print(f"Erro: O ambiente virtual não foi encontrado em {projeto_dir}/.venv!")
        print("Execute primeiro o script quick_setup.py para criar o ambiente básico.")
        return False
    
    # Verificar se o log.txt existe
    if not os.path.exists("log.txt"):
        print("Erro: O arquivo log.txt não foi encontrado!")
        print("Execute primeiro o script quick_setup.py para criar o ambiente básico.")
        return False
    
    return True

def obter_info_base():
    """Obtém informações básicas do ambiente MCP já configurado."""
    try:
        # Ler log.txt para obter informações
        with open("log.txt", "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        # Obter caminho do projeto
        match = re.search(r"Caminho do Projeto: (.+)", conteudo)
        if match:
            caminho_projeto = match.group(1)
        else:
            caminho_projeto = os.path.abspath("mcp_server")
        
        # Determinar o caminho do UV
        uv_path = os.path.join(os.path.expanduser("~"), "pipx", "venvs", "uv", "Scripts", "uv.exe")
        if not os.path.exists(uv_path) and platform.system() != "Windows":
            uv_path = os.path.join(os.path.expanduser("~"), ".local", "pipx", "venvs", "uv", "bin", "uv")
        if not os.path.exists(uv_path):
            uv_path = "uv"
        
        return {
            "caminho_projeto": caminho_projeto,
            "uv_path": uv_path
        }
    except Exception as e:
        print(f"Erro ao obter informações básicas: {e}")
        return {
            "caminho_projeto": os.path.abspath("mcp_server"),
            "uv_path": "uv"
        }

def criar_modelo_servidor(nome_arquivo, nome_mcp):
    """Cria um arquivo de servidor MCP personalizado."""
    
    # Usamos f-string tripla com aspas simples para evitar problemas de escape
    conteudo = f'''#!/usr/bin/env python3
# {nome_arquivo} - Servidor MCP personalizado para {nome_mcp}
# Criado automaticamente por add_mcp.py

import os
from mcp.server.fastmcp import FastMCP

# Criar instância do servidor MCP
mcp = FastMCP(
    name="{nome_mcp}",
    description="Servidor MCP personalizado"
)

@mcp.tool()
def hello(name: str = "World") -> str:
    """Retorna uma saudação personalizada.
    
    Args:
        name: O nome para saudar. Padrão: "World"
        
    Returns:
        Uma mensagem de saudação personalizada
    """
    return f"Olá {{name}} do servidor {{mcp.name}}!"

@mcp.tool()
def soma(a: float, b: float) -> float:
    """Soma dois números.
    
    Args:
        a: Primeiro número
        b: Segundo número
        
    Returns:
        A soma dos dois números
    """
    return a + b

@mcp.tool()
def config_info() -> str:
    """Retorna informações sobre a configuração do servidor.
    
    Returns:
        Um texto com as informações de configuração
    """
    try:
        diretorio_atual = os.getcwd()
        
        # Tenta ler o log.txt que está um nível acima
        log_path = os.path.join(os.path.dirname(os.path.dirname(diretorio_atual)), "log.txt")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                conteudo_log = f.read()
        else:
            conteudo_log = "Arquivo log.txt não encontrado"
        
        info = f"""
=== INFORMAÇÕES DE CONFIGURAÇÃO ===
Nome do servidor: {{mcp.name}}
Arquivo do servidor: {{os.path.basename(__file__)}}
Diretório atual: {{diretorio_atual}}

=== CONTEÚDO DO LOG ===
{{conteudo_log}}

=== STATUS ===
Servidor MCP em execução: Sim
"""
        return info
    except Exception as e:
        return f"Erro ao obter informações: {{e}}"

if __name__ == "__main__":
    # Iniciar o servidor MCP
    print(f"Iniciando servidor MCP: {{mcp.name}}")
    print("Use a ferramenta 'hello' para testar o servidor")
    print("Use a ferramenta 'config_info' para ver as informações de configuração")
    mcp.run(transport='stdio')
'''
    return conteudo

def main():
    """Função principal para adicionar um novo MCP."""
    cabecalho("ADICIONAR NOVO SERVIDOR MCP PERSONALIZADO")
    print("Este script permite adicionar um novo servidor MCP personalizado.")
    print("O ambiente básico (quick_setup.py) já deve ter sido executado anteriormente.")
    
    # Verificar se o ambiente está configurado
    if not verificar_ambiente():
        sys.exit(1)
    
    # Obter informações básicas
    info = obter_info_base()
    caminho_projeto = info["caminho_projeto"]
    uv_path = info["uv_path"]
    
    # Solicitar nome do MCP
    print("\nEscolha um nome para o seu novo servidor MCP:")
    print("(Este nome será usado para identificar o servidor na configuração)")
    nome_mcp = input("> ").strip()
    
    if not nome_mcp:
        print("Nome inválido. Operação cancelada.")
        sys.exit(1)
    
    # Validar o nome (remover caracteres especiais)
    nome_mcp_limpo = re.sub(r'[^a-zA-Z0-9_]', '_', nome_mcp)
    if nome_mcp != nome_mcp_limpo:
        print(f"Nome ajustado para: {nome_mcp_limpo}")
        nome_mcp = nome_mcp_limpo
    
    # Solicitar nome do arquivo
    print("\nEscolha um nome para o arquivo do servidor (sem a extensão .py):")
    print("(Este será o nome do arquivo que contém o código do servidor)")
    nome_arquivo = input("> ").strip()
    
    if not nome_arquivo:
        # Usar o nome do MCP como padrão
        nome_arquivo = nome_mcp.lower()
        print(f"Usando o nome padrão: {nome_arquivo}")
    
    # Validar o nome do arquivo
    nome_arquivo_limpo = re.sub(r'[^a-zA-Z0-9_]', '_', nome_arquivo)
    if nome_arquivo != nome_arquivo_limpo:
        print(f"Nome do arquivo ajustado para: {nome_arquivo_limpo}")
        nome_arquivo = nome_arquivo_limpo
    
    # Adicionar a extensão .py
    if not nome_arquivo.endswith(".py"):
        nome_arquivo += ".py"
    
    # Caminho completo do arquivo
    caminho_arquivo = os.path.join(caminho_projeto, nome_arquivo)
    
    # Verificar se o arquivo já existe
    if os.path.exists(caminho_arquivo):
        print(f"ATENÇÃO: O arquivo {nome_arquivo} já existe!")
        resposta = input("Deseja sobrescrevê-lo? (s/n): ").lower()
        if resposta != 's':
            print("Operação cancelada pelo usuário.")
            sys.exit(0)
    
    # Criar o arquivo do servidor
    try:
        conteudo = criar_modelo_servidor(nome_arquivo, nome_mcp)
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo)
        print(f"\n✅ Arquivo {nome_arquivo} criado com sucesso em {caminho_projeto}")
    except Exception as e:
        print(f"Erro ao criar o arquivo: {e}")
        sys.exit(1)
    
    # Definir argumentos para a configuração
    argumentos = [
        "--directory",
        caminho_projeto,
        "run",
        nome_arquivo
    ]
    
    # Gerar a configuração JSON
    config = {
        "mcpServers": {
            nome_mcp: {
                "command": uv_path,
                "args": argumentos,
                "metadata": {
                    "created": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        }
    }
    
    # Exibir a configuração para o usuário
    cabecalho("CONFIGURAÇÃO PARA O CLAUDE/CURSOR")
    print("\nCopie o JSON abaixo e adicione à configuração do seu cliente:")
    print("\nPara Cursor:")
    print("  Arquivo: C:\\Users\\<seu_usuario>\\.cursor\\mcp.json")
    print("\nPara Claude for Desktop:")
    if platform.system() == "Windows":
        print("  Arquivo: %USERPROFILE%\\AppData\\Roaming\\Claude\\claude_desktop_config.json")
    else:
        print("  Arquivo: ~/Library/Application Support/Claude/claude_desktop_config.json")
    
    print("\nConfiguração JSON:")
    print(json.dumps(config["mcpServers"][nome_mcp], indent=4))
    
    print("\n📋 Exemplo completo (integre com sua configuração existente):")
    print(json.dumps(config, indent=4))
    
    # Mostrar comando para executar o servidor
    print(f"\nPara executar o servidor manualmente:")
    print(f"{uv_path} --directory {caminho_projeto} run {nome_arquivo}")
    
    # Atualizar automaticamente os arquivos de configuração
    print("\n🔄 Atualizando configurações das IDEs automaticamente...")
    
    # Criar configuração para o módulo de utilitários
    resultado = config_util.atualizar_configuracoes(
        nome_servidor=nome_mcp,
        comando=uv_path, 
        argumentos=argumentos
    )
    
    # Mostrar resultados da atualização
    if resultado["cursor"]["status"] == "sucesso":
        print(f"✅ Cursor: Configuração atualizada em {resultado['cursor']['caminho']}")
    else:
        print(f"❌ Cursor: {resultado['cursor']['mensagem']}")
        
    if resultado["claude"]["status"] == "sucesso":
        print(f"✅ Claude Desktop: Configuração atualizada em {resultado['claude']['caminho']}")
    else:
        print(f"❌ Claude Desktop: {resultado['claude']['mensagem']}")
    
    # Instruções finais
    print("\n🎉 Servidor MCP criado e configurado com sucesso!")
    print("Para executar o servidor, basta reiniciar o Claude Desktop")
    print("Ou execute manualmente com os comandos:")
    print(f"  cd {caminho_projeto}")
    print(f"  {uv_path} activate")
    print(f"  {uv_path} run {nome_arquivo}")
    
    # Adicionar aviso final
    print("\n⚠️ IMPORTANTE: O servidor já está disponível e ativo no Cursor!")
    print("   Não é necessário executá-lo manualmente a menos que deseje fazê-lo posteriormente.")

if __name__ == "__main__":
    main() 