import os
import re
import platform
import subprocess
import sys
import json

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Importa o módulo de utilitários de configuração
import cli.config_util as config_util

def ler_log():
    """Lê o arquivo log.txt e extrai as informações relevantes."""
    try:
        with open("log.txt", "r", encoding="utf-8") as log_file:
            conteudo = log_file.read()
            
            # Extrair nome do projeto
            nome_match = re.search(r"Nome do Projeto: (.+)", conteudo)
            if nome_match:
                nome_projeto = nome_match.group(1)
            else:
                raise ValueError("Nome do projeto não encontrado no log.txt")
                
            # Extrair caminho do projeto
            caminho_match = re.search(r"Caminho do Projeto: (.+)", conteudo)
            if caminho_match:
                caminho_projeto = caminho_match.group(1)
            else:
                raise ValueError("Caminho do projeto não encontrado no log.txt")
                
            return nome_projeto, caminho_projeto
    except FileNotFoundError:
        print("Arquivo log.txt não encontrado. Execute primeiro os scripts instalar_uv.py e criar_projeto_mcp.py")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler o arquivo log.txt: {e}")
        sys.exit(1)

def criar_config_mcp(nome_projeto, caminho_projeto):
    """Cria e atualiza a configuração MCP nos clientes."""
    # Determinar o caminho do uv para o JSON
    uv_path = os.path.join(os.path.expanduser("~"), "pipx", "venvs", "uv", "Scripts", "uv.exe")
    if not os.path.exists(uv_path):
        uv_path = "uv"  # Fallback para o comando simples se não encontrar o executável
        
    # Configurar argumentos para o servidor
    args = [
        "--directory",
        caminho_projeto,
        "run",
        "demon.py"
    ]
    
    # Atualizar configurações usando config_util
    try:
        resultado = config_util.atualizar_configuracoes(nome_servidor=nome_projeto, comando=uv_path, argumentos=args)
        
        print("\n=== CONFIGURAÇÃO MCP ATUALIZADA ===")
        for cliente, info in resultado.items():
            if info["status"] == "sucesso":
                print(f"✅ {cliente.title()}: Configuração atualizada em {info['caminho']}")
            else:
                print(f"❌ {cliente.title()}: {info['mensagem']}")
        print("=========================================")
        
    except Exception as e:
        print(f"❌ Erro ao atualizar configurações MCP: {e}")

def criar_servidor_teste(nome_projeto, caminho_projeto):
    """Cria um arquivo demon.py com um servidor MCP básico."""
    
    # Determinar o caminho do uv
    uv_path = os.path.join(os.path.expanduser("~"), "pipx", "venvs", "uv", "Scripts", "uv.exe")
    if not os.path.exists(uv_path):
        print(f"⚠️ Não foi possível encontrar o uv em {uv_path}")
        print("Tentando usar o comando 'uv' diretamente...")
        uv_path = "uv"
    else:
        print(f"✅ Usando uv de: {uv_path}")
    
    # Conteúdo do arquivo demon.py
    servidor_conteudo = '''
import os
import re
from mcp.server.fastmcp import FastMCP

# Inicializa o servidor FastMCP
mcp = FastMCP("teste")

def ler_log():
    """Lê o arquivo log.txt e retorna as informações."""
    try:
        # Subir um nível de diretório para encontrar o log.txt
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log.txt")
        with open(log_path, "r", encoding="utf-8") as log_file:
            return log_file.read()
    except Exception as e:
        return f"Erro ao ler o arquivo log.txt: {e}"

@mcp.tool()
async def config_info() -> str:
    """Retorna as informações de configuração do servidor MCP.
    
    Returns:
        Informações detalhadas sobre a configuração do servidor
    """
    log_conteudo = ler_log()
    
    # Processamento adicional para formatação
    if log_conteudo:
        return f"""
**Configurações do Servidor MCP**

{log_conteudo}

**Diretório atual**: {os.path.abspath('.')}
**Status**: Servidor MCP funcionando corretamente!
"""
    else:
        return "Não foi possível recuperar as informações de configuração."

@mcp.tool()
async def soma(a: float, b: float) -> float:
    """Soma dois números.
    
    Args:
        a: Primeiro número
        b: Segundo número
    """
    return a + b

if __name__ == "__main__":
    # Inicializa e executa o servidor
    print("Iniciando servidor MCP de teste...")
    print("Use a ferramenta config_info para ver as configurações do servidor")
    print("Use Ctrl+C para encerrar.")
    mcp.run(transport='stdio')
'''
    
    try:
        # Criar o arquivo demon.py
        with open("demon.py", "w", encoding="utf-8") as f:
            f.write(servidor_conteudo.strip())
        print("\nServidor MCP de teste criado com sucesso: demon.py")
        
        print("Para executar o servidor, use:")
        print(f"  {uv_path} --directory {os.path.abspath('.')} run demon.py")
        
        # Mostrar a configuração MCP antes de executar o servidor
        criar_config_mcp(nome_projeto, caminho_projeto)
    except Exception as e:
        print(f"Erro ao criar os arquivos do servidor: {e}")

def ativar_e_instalar():
    """Ativa o ambiente virtual e instala os pacotes necessários."""
    # Ler as informações do projeto no log
    nome_projeto, caminho_projeto = ler_log()
    print(f"Informações do projeto encontradas:")
    print(f"  * Nome do projeto: {nome_projeto}")
    print(f"  * Caminho: {caminho_projeto}")
    
    # Verificar se o diretório do projeto existe
    if not os.path.exists(caminho_projeto):
        print(f"O diretório do projeto não foi encontrado: {caminho_projeto}")
        sys.exit(1)
    
    # Navegar para o diretório do projeto
    os.chdir(caminho_projeto)
    print(f"Navegando para o diretório do projeto: {caminho_projeto}")
    
    # Determinar o caminho do uv
    uv_path = os.path.join(os.path.expanduser("~"), "pipx", "venvs", "uv", "Scripts", "uv.exe")
    if not os.path.exists(uv_path):
        print(f"⚠️ Não foi possível encontrar o uv em {uv_path}")
        print("Tentando usar o comando 'uv' diretamente...")
        uv_path = "uv"
    else:
        print(f"✅ Usando uv de: {uv_path}")
    
    # Detectar o sistema operacional para determinar o caminho do script de ativação
    system = platform.system()
    
    if system == "Windows":
        activate_script = os.path.join(".venv", "Scripts", "activate")
        
        # Executar instalação dentro do ambiente virtual usando um script batch
        batch_script = "temp_activate.bat"
        with open(batch_script, "w", encoding="cp1252") as f:
            f.write(f"@echo off\n")
            f.write(f"call .venv\\Scripts\\activate\n")
            f.write(f"echo [OK] Ambiente virtual ativado\n")
            f.write(f"echo [INFO] Instalando pacotes...\n")
            f.write(f"{uv_path} add mcp[cli] httpx\n")
            f.write(f"echo [OK] Pacotes instalados com sucesso\n")
        
        print("Ativando ambiente virtual e instalando pacotes...")
        subprocess.run(["cmd", "/c", batch_script], check=True)
        
        # Remover script temporário
        os.remove(batch_script)
        
    else:  # Linux/macOS
        activate_script = os.path.join(".venv", "bin", "activate")
        
        # Executar instalação dentro do ambiente virtual usando um script shell
        shell_script = "temp_activate.sh"
        with open(shell_script, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\n")
            f.write(f"source .venv/bin/activate\n")
            f.write(f"echo '[OK] Ambiente virtual ativado'\n")
            f.write(f"echo '[INFO] Instalando pacotes...'\n")
            f.write(f"{uv_path} add mcp[cli] httpx\n")
            f.write(f"echo '[OK] Pacotes instalados com sucesso'\n")
        
        # Tornar o script executável
        os.chmod(shell_script, 0o755)
        
        print("Ativando ambiente virtual e instalando pacotes...")
        subprocess.run(["bash", shell_script], check=True)
        
        # Remover script temporário
        os.remove(shell_script)
    
    print("\nAmbiente virtual ativado e pacotes instalados com sucesso!")
    print("O projeto está pronto para uso.")
    
    # Criar o arquivo demon.py
    criar_servidor_teste("demon", caminho_projeto)

if __name__ == "__main__":
    ativar_e_instalar() 