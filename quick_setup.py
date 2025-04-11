import os
import sys
import platform
import subprocess
import re
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