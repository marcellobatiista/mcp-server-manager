import os
import re
import platform
import subprocess
import sys
import tomli_w
import tomli

def ler_log():
    """Lê o arquivo log.txt e extrai as informações relevantes."""
    try:
        with open("log.txt", "r", encoding="utf-8") as log_file:
            conteudo = log_file.read()
            
            # Extrair versão do Python
            versao_match = re.search(r"Versão do Python: Python (\d+\.\d+\.\d+)", conteudo)
            if versao_match:
                versao_python = versao_match.group(1)
                versao_base = ".".join(versao_python.split(".")[:2])  # Obtém apenas X.Y
            else:
                raise ValueError("Não foi possível encontrar a versão do Python no log")

            # Extrair caminho do Python
            caminho_match = re.search(r"Caminho do Python: (.+)", conteudo)
            if caminho_match:
                caminho_python = caminho_match.group(1)
            else:
                raise ValueError("Não foi possível encontrar o caminho do Python no log")

            return versao_base, caminho_python
    except FileNotFoundError:
        print("❌ Arquivo log.txt não encontrado. Execute primeiro o script instalar_uv.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo log.txt: {e}")
        sys.exit(1)

def atualizar_log(nome_projeto, caminho_projeto):
    """Atualiza o log.txt com informações do projeto."""
    try:
        with open("../log.txt", "r", encoding="utf-8") as log_file:
            conteudo = log_file.read()
        
        with open("../log.txt", "w", encoding="utf-8") as log_file:
            log_file.write(conteudo)
            log_file.write(f"Nome do Projeto: {nome_projeto}\n")
            log_file.write(f"Caminho do Projeto: {caminho_projeto}\n")
        
        print(f"✅ Arquivo log.txt atualizado com informações do projeto")
    except Exception as e:
        print(f"❌ Erro ao atualizar o arquivo log.txt: {e}")

def executar_comando(comando, shell=False):
    """Executa um comando e retorna o resultado."""
    try:
        return subprocess.run(comando, check=True, shell=shell, text=True, 
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar o comando: {' '.join(comando) if isinstance(comando, list) else comando}")
        print(f"Erro: {e.stderr}")
        sys.exit(1)

def modificar_pyproject_toml(caminho_arquivo, versao_python):
    """Modifica o arquivo pyproject.toml para usar a versão correta do Python."""
    try:
        # Ler o arquivo TOML
        with open(caminho_arquivo, "rb") as f:
            dados = tomli.load(f)
        
        # Modificar a versão do Python
        if "project" in dados:
            dados["project"]["requires-python"] = f">={versao_python}"
        
        # Escrever de volta no arquivo
        with open(caminho_arquivo, "wb") as f:
            tomli_w.dump(dados, f)
        
        print(f"✅ Arquivo {caminho_arquivo} atualizado com requires-python = \">={versao_python}\"")
    except Exception as e:
        print(f"❌ Erro ao modificar o arquivo pyproject.toml: {e}")
        sys.exit(1)

def main():
    # Obter a versão e caminho do Python do log
    versao_python, caminho_python = ler_log()
    print(f"🔍 Informações encontradas no log:")
    print(f"  • Versão do Python: {versao_python}")
    print(f"  • Caminho do Python: {caminho_python}")
    
    # Determinar o caminho do uv
    uv_path = os.path.join(os.path.expanduser("~"), "pipx", "venvs", "uv", "Scripts", "uv.exe")
    if not os.path.exists(uv_path):
        print(f"⚠️ Não foi possível encontrar o uv em {uv_path}")
        print("Tentando usar o comando 'uv' diretamente...")
        uv_path = "uv"
    else:
        print(f"✅ Usando uv de: {uv_path}")
    
    # Pedir o nome do projeto
    nome_projeto = input("\n💡 Digite o nome do projeto MCP: ").strip()
    if not nome_projeto:
        print("❌ Nome do projeto não pode ser vazio.")
        sys.exit(1)
    
    # Verificar se o diretório já existe
    if os.path.exists(nome_projeto):
        resposta = input(f"⚠️ O diretório '{nome_projeto}' já existe. Deseja remover e criar um novo? (s/n): ").lower()
        if resposta != 's':
            print("❌ Operação cancelada pelo usuário.")
            sys.exit(0)
        
        # Remover o diretório existente
        print(f"🗑️ Removendo diretório existente '{nome_projeto}'...")
        import shutil
        try:
            shutil.rmtree(nome_projeto)
            print(f"✅ Diretório '{nome_projeto}' removido com sucesso.")
        except Exception as e:
            print(f"❌ Erro ao remover o diretório: {e}")
            sys.exit(1)
    
    print(f"\n🚀 Criando projeto '{nome_projeto}'...")
    
    # Inicializar o projeto com uv
    executar_comando([uv_path, "init", nome_projeto])
    
    # Mudar para o diretório do projeto
    os.chdir(nome_projeto)
    print(f"📂 Navegando para o diretório '{nome_projeto}'")
    
    # Criar ambiente virtual
    print("🔨 Criando ambiente virtual...")
    executar_comando([uv_path, "venv"])
    
    # Modificar o pyproject.toml
    pyproject_path = "pyproject.toml"
    if os.path.exists(pyproject_path):
        print(f"📝 Modificando {pyproject_path}...")
        modificar_pyproject_toml(pyproject_path, versao_python)
    else:
        print(f"❌ Arquivo {pyproject_path} não encontrado.")
    
    # Configurar o .python-version com o caminho escolhido
    print("🔧 Configurando arquivo .python-version...")
    executar_comando([uv_path, "python", "pin", caminho_python])
    
    # Atualizar o log.txt com informações do projeto
    caminho_projeto = os.path.abspath(".")
    atualizar_log(nome_projeto, caminho_projeto)
    
    print(f"\n✅ Projeto '{nome_projeto}' criado e configurado com sucesso!")
    print(f"📂 Localização: {caminho_projeto}")

if __name__ == "__main__":
    main() 