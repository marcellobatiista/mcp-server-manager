import os
import sys
import time
import json
import platform
import subprocess
import re
from pathlib import Path
import cli.config_util as config_util  # Importar o módulo de utilitários de configuração da pasta cli

# Configurações padrão
NOME_SERVIDOR_PADRAO = "demon"
NOME_DIRETORIO_PADRAO = "mcp_server"
TOOLS_DIR = "tools"

def cabecalho(titulo):
    """Exibe um cabeçalho simples."""
    print(f"\n=== {titulo} ===")

def executar_comando(comando, mostrar_saida=False, shell=False):
    """Executa um comando e retorna o status de saída."""
    try:
        if mostrar_saida:
            return subprocess.call(comando, shell=shell)
        else:
            resultado = subprocess.run(comando, capture_output=True, text=True, shell=shell)
            return resultado.returncode
    except Exception as e:
        print(f"Erro ao executar comando: {e}")
        return 1

def criar_env_var(nome, valor):
    """Cria uma variável de ambiente temporária."""
    os.environ[nome] = valor

def atualizar_pip():
    """Atualiza o pip para a versão mais recente."""
    cabecalho("Atualizando pip")
    executar_comando([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                    mostrar_saida=False)

def instalar_dependencias():
    """Instala dependências necessárias."""
    cabecalho("Instalando dependências")
    requirements = ["tomli>=2.0.0", "tomli-w>=1.0.0"]
    for req in requirements:
        executar_comando([sys.executable, "-m", "pip", "install", req], 
                        mostrar_saida=False)

def instalar_uv():
    """Instala o UV usando o script da pasta tools."""
    cabecalho("Instalando UV")
    
    # Vamos detectar as versões do Python diretamente
    print("Detectando versões do Python...")
    pythons_encontrados = []
    
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output("where python", shell=True, text=True, stderr=subprocess.DEVNULL)
            paths = [p.strip() for p in output.splitlines() if "WindowsApps" not in p]
            for i, path in enumerate(paths):
                try:
                    result = subprocess.check_output([path, "--version"], text=True, stderr=subprocess.STDOUT)
                    version = result.strip()
                    # Verificar se é Python 3.10+
                    match = re.search(r"Python (\d+)\.(\d+)", version)
                    if match:
                        major, minor = map(int, match.groups())
                        compatible = (major == 3 and minor >= 10)
                        pythons_encontrados.append((i, path, version, compatible))
                except:
                    pass
        except:
            pass
    
    # Encontrar a melhor versão: primeiro compatível ou primeiro disponível
    escolhido = None
    # Primeiro, procurar por compatíveis
    for idx, path, version, compatible in pythons_encontrados:
        if compatible:
            escolhido = idx
            break
    
    # Se não tiver compatível, pegar o primeiro disponível
    if escolhido is None and pythons_encontrados:
        escolhido = pythons_encontrados[0][0]
    
    # Se ainda não tiver encontrado, usar o Python atual
    if escolhido is None:
        print("Nenhuma versão do Python encontrada. Usando o Python atual.")
        escolhido = 0
        
    # Modificar o script para ser mais simples: criar um arquivo de resposta
    with open("python_choice.txt", "w") as f:
        f.write(f"{escolhido}\n")
    
    # Executar o script
    script_path = os.path.join(TOOLS_DIR, "instalar_uv.py")
    
    if platform.system() == "Windows":
        # Criar um batch mais simples que fornecerá a entrada
        with open("instalar_uv_auto.bat", "w", encoding="cp1252") as f:
            f.write("@echo off\n")
            f.write(f"type python_choice.txt | {sys.executable} {script_path}\n")
        
        print(f"Instalando UV automaticamente com Python índice {escolhido}...")
        executar_comando(["instalar_uv_auto.bat"], mostrar_saida=True, shell=True)
        
        # Limpar arquivos temporários
        if os.path.exists("instalar_uv_auto.bat"):
            os.remove("instalar_uv_auto.bat")
    else:
        # No Linux/macOS
        os.system(f"cat python_choice.txt | {sys.executable} {script_path}")
    
    # Limpar arquivos temporários
    if os.path.exists("python_choice.txt"):
        os.remove("python_choice.txt")

def criar_projeto():
    """Cria o projeto MCP com nome padrão."""
    cabecalho("Criando projeto MCP")
    script_path = os.path.join(TOOLS_DIR, "criar_projeto_mcp.py")
    
    # Criar script temporário para resposta automática
    resposta_automatica = r"""
import sys
print("{0}")  # Nome do projeto
print("s")    # Responder 's' para sobrescrever o diretório existente
""".format(NOME_DIRETORIO_PADRAO)
    
    # Criar arquivo temporário para o script de resposta automática
    with open("temp_criar_projeto.py", "w", encoding="utf-8") as f:
        f.write(resposta_automatica)
    
    # Em Windows, usar um arquivo batch
    if platform.system() == "Windows":
        # Criar um arquivo batch temporário
        with open("temp_criar_projeto.bat", "w", encoding="cp1252") as f:
            f.write(f"@echo off\n")
            f.write(f"{sys.executable} temp_criar_projeto.py | {sys.executable} {script_path}\n")
        
        executar_comando(["temp_criar_projeto.bat"], mostrar_saida=True, shell=True)
        
        # Limpar arquivos temporários
        if os.path.exists("temp_criar_projeto.bat"):
            os.remove("temp_criar_projeto.bat")
    else:
        # No Linux/macOS podemos usar pipes diretamente
        os.system(f"{sys.executable} temp_criar_projeto.py | {sys.executable} {script_path}")
    
    # Limpar arquivos temporários
    if os.path.exists("temp_criar_projeto.py"):
        os.remove("temp_criar_projeto.py")

def ativar_ambiente():
    """Ativa o ambiente virtual e cria o servidor de teste."""
    cabecalho("Configurando ambiente")
    script_path = os.path.join(TOOLS_DIR, "ativar_ambiente.py")
    
    # Criar script para resposta automática (não executar o servidor)
    resposta_automatica = "n\n"  # Responder 'n' para não executar o servidor
    
    # Criar arquivo temporário para a resposta
    with open("temp_resposta.txt", "w", encoding="utf-8") as f:
        f.write(resposta_automatica)
    
    # Em Windows, usar um arquivo batch
    if platform.system() == "Windows":
        # Criar um arquivo batch temporário
        with open("temp_ativar.bat", "w", encoding="cp1252") as f:
            f.write(f"@echo off\n")
            f.write(f"type temp_resposta.txt | {sys.executable} {script_path}\n")
        
        executar_comando(["temp_ativar.bat"], mostrar_saida=True, shell=True)
        
        # Limpar arquivos temporários
        if os.path.exists("temp_ativar.bat"):
            os.remove("temp_ativar.bat")
    else:
        # No Linux/macOS podemos usar pipes diretamente
        os.system(f"cat temp_resposta.txt | {sys.executable} {script_path}")
    
    # Limpar arquivos temporários
    if os.path.exists("temp_resposta.txt"):
        os.remove("temp_resposta.txt")

def gerar_config_json():
    """Gera e mostra o config JSON para o Claude for Desktop."""
    cabecalho("CONFIGURAÇÃO PARA O CLAUDE FOR DESKTOP")
    
    try:
        # Ler informações do log
        with open("log.txt", "r", encoding="utf-8") as log_file:
            conteudo = log_file.read()
        
        # Extrair nome do projeto e caminho
        nome_match = re.search(r"Nome do Projeto: (.+)", conteudo)
        caminho_match = re.search(r"Caminho do Projeto: (.+)", conteudo)
        
        if nome_match and caminho_match:
            nome_projeto = nome_match.group(1)
            caminho_projeto = caminho_match.group(1)
            
            # Determinar o caminho do UV
            uv_path = os.path.join(os.path.expanduser("~"), "pipx", "venvs", "uv", "Scripts", "uv.exe")
            if not os.path.exists(uv_path) and platform.system() != "Windows":
                uv_path = os.path.join(os.path.expanduser("~"), ".local", "pipx", "venvs", "uv", "bin", "uv")
            if not os.path.exists(uv_path):
                uv_path = "uv"
            
            # Criar o objeto JSON - usar NOME_SERVIDOR_PADRAO para o nome do servidor
            config = {
                "mcpServers": {
                    NOME_SERVIDOR_PADRAO: {
                        "command": uv_path,
                        "args": [
                            "--directory",
                            caminho_projeto,
                            "run",
                            "demon.py"
                        ]
                    }
                }
            }
            
            # Mostrar o JSON para o usuário
            print("\nCopie o JSON abaixo para o arquivo de configuração do Claude for Desktop:")
            print(json.dumps(config, indent=4))
            
            # Mostrar onde colocar o JSON
            print("\nCaminho do arquivo de configuração:")
            if platform.system() == "Windows":
                print("  %USERPROFILE%\\AppData\\Roaming\\Claude\\claude_desktop_config.json")
            else:
                print("  ~/Library/Application Support/Claude/claude_desktop_config.json")
            
            # Mostrar como executar o servidor manualmente
            print(f"\nPara executar o servidor: {uv_path} --directory {caminho_projeto} run demon.py")
            
            # Atualizar automaticamente os arquivos de configuração
            print("\n🔄 Atualizando configurações das IDEs automaticamente...")
            
            argumentos = [
                "--directory",
                caminho_projeto,
                "run",
                "demon.py"
            ]
            
            resultado = config_util.atualizar_configuracoes(
                nome_servidor=NOME_SERVIDOR_PADRAO,
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
                
            print("\n🎉 Para usar o servidor, apenas reinicie o Cursor ou Claude Desktop!")
            
        else:
            print("Não foi possível extrair as informações do log.txt")
    
    except Exception as e:
        print(f"Erro ao gerar configuração: {e}")

def criar_servidor_teste(nome_projeto, caminho_projeto):
    """Cria um arquivo de servidor MCP para teste."""
    cabecalho("Criando servidor MCP de teste")
    
    # Determinar o caminho do UV
    uv_path = os.path.join(os.path.expanduser("~"), "pipx", "venvs", "uv", "Scripts", "uv.exe")
    if not os.path.exists(uv_path) and platform.system() != "Windows":
        uv_path = os.path.join(os.path.expanduser("~"), ".local", "pipx", "venvs", "uv", "bin", "uv")
    if not os.path.exists(uv_path):
        uv_path = "uv"
    
    print(f"✅ Usando uv de: {uv_path}")
    
    # Conteúdo do servidor MCP básico - usar NOME_SERVIDOR_PADRAO para o nome do servidor
    conteudo_servidor = f'''#!/usr/bin/env python3
# Servidor MCP de teste para o projeto {NOME_SERVIDOR_PADRAO}
# Criado automaticamente por quick_setup.py

import os
from mcp.server.fastmcp import FastMCP

# Criar instância do servidor MCP
mcp = FastMCP(
    name="{NOME_SERVIDOR_PADRAO}",
    description="Servidor MCP básico para testes"
)

def ler_log():
    """Função interna para ler o arquivo log.txt."""
    try:
        # Tenta encontrar o log.txt um nível acima
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), "log.txt")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                return f.read()
        return "Arquivo log.txt não encontrado"
    except Exception as e:
        return f"Erro ao ler log.txt: {{e}}"

@mcp.tool()
def hello(name: str = "World") -> str:
    """Retorna uma saudação simples.
    
    Args:
        name: O nome para saudar. Padrão: "World"
        
    Returns:
        Uma mensagem de saudação
    """
    return f"Hello {{name}} from MCP!"

@mcp.tool()
def add(a: float, b: float) -> float:
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
    """Retorna informações de configuração do servidor.
    
    Returns:
        Uma string com informações sobre o servidor e o projeto
    """
    diretorio_atual = os.getcwd()
    conteudo_log = ler_log()
    
    return f"""
=== INFORMAÇÕES DO SERVIDOR MCP ===
Nome do servidor: {NOME_SERVIDOR_PADRAO}
Diretório: {{diretorio_atual}}

=== LOG DE INSTALAÇÃO ===
{{conteudo_log}}

=== STATUS ===
Servidor em execução: Sim
"""

if __name__ == "__main__":
    print(f"Iniciando servidor MCP: {NOME_SERVIDOR_PADRAO}")
    print("Você pode usar as seguintes ferramentas:")
    print("  - hello: Retorna uma saudação simples")
    print("  - add: Soma dois números")
    print("  - config_info: Retorna informações de configuração")
    mcp.run(transport='stdio')
'''
    
    caminho_arquivo = os.path.join(caminho_projeto, "demon.py")
    
    try:
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo_servidor)
        print(f"Servidor MCP de teste criado com sucesso: demon.py")
        print("Para executar o servidor, use:")
        print(f"  {uv_path} --directory {caminho_projeto} run demon.py")
        return True
    except Exception as e:
        print(f"Erro ao criar o servidor de teste: {e}")
        return False

def ir_para_launcher():
    """Executa o script launcher.py para começar a gerenciar os servidores."""
    cabecalho("INICIANDO LAUNCHER")
    
    print("\n🚀 Iniciando o launcher MCP para gerenciar seus servidores...")
    
    try:
        # Executa o launcher.py no novo caminho
        script_path = os.path.join("cli", "launcher.py")
        if os.path.exists(script_path):
            executar_comando([sys.executable, script_path], mostrar_saida=True)
        else:
            print(f"❌ Erro: Não foi possível encontrar o launcher em {script_path}")
    except Exception as e:
        print(f"❌ Erro ao iniciar o launcher: {e}")

def main():
    """Função principal do script de setup rápido."""
    cabecalho("CONFIGURAÇÃO RÁPIDA DO SERVIDOR MCP")
    
    print("Este script vai configurar rapidamente o ambiente para os servidores MCP.")
    print("Ele irá realizar as seguintes operações:")
    print("  1. Atualizar o pip")
    print("  2. Instalar dependências necessárias")
    print("  3. Instalar o gerenciador UV")
    print("  4. Criar o projeto MCP básico")
    print("  5. Ativar o ambiente virtual")
    print("  6. Iniciar o launcher para gerenciar servidores")
    
    continuar = input("\nDeseja continuar? (s/n): ")
    if continuar.lower() != 's':
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)
    
    # Atualizar o pip
    atualizar_pip()
    
    # Instalar dependências
    instalar_dependencias()
    
    # Instalar o UV
    instalar_uv()
    
    # Criar o projeto MCP
    criar_projeto()
    
    # Ativar ambiente e criar servidor teste
    ativar_ambiente()
    
    # Criar arquivo .bat para executar o launcher
    criar_launcher_bat()
    
    print("\n✅ Configuração rápida concluída com sucesso!")
    print("Agora você pode executar o launcher para gerenciar seus servidores.")
    
    iniciar_launcher = input("\nDeseja iniciar o launcher agora? (s/n): ")
    if iniciar_launcher.lower() == 's':
        ir_para_launcher()
    else:
        print("\nVocê pode iniciar o launcher a qualquer momento executando:")
        print(f"  python {os.path.join('cli', 'launcher.py')}")
        print("Ou usando o atalho 'launcher.bat' criado na pasta do projeto.")

def criar_launcher_bat():
    """Cria um arquivo batch para facilitar a execução do launcher."""
    try:
        # Criar arquivo launcher.bat
        with open("launcher.bat", "w", encoding="cp1252") as f:
            f.write(f"@echo off\n")
            f.write("echo Iniciando MCP Launcher...\n")
            f.write(f"{sys.executable} {os.path.join('cli', 'launcher.py')}\n")
        
        print("✅ Criado arquivo 'launcher.bat' para execução rápida")
    except Exception as e:
        print(f"❌ Erro ao criar arquivo launcher.bat: {e}")
        
if __name__ == "__main__":
    main() 