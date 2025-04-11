import os
import platform
import subprocess
from shutil import which
import datetime
import sys
import re

def find_python_paths():
    system = platform.system()
    python_paths = []

    if system == "Windows":
        try:
            output = subprocess.check_output("where python", shell=True, text=True, stderr=subprocess.DEVNULL)
            python_paths = [line.strip() for line in output.splitlines()]
        except subprocess.CalledProcessError:
            pass
    else:  # Linux / macOS
        possible_bins = ["python", "python3"]
        for bin_name in possible_bins:
            bin_path = which(bin_name)
            if bin_path and bin_path not in python_paths:
                python_paths.append(bin_path)

        for i in range(3, 13):
            bin_path = which(f"python3.{i}")
            if bin_path and bin_path not in python_paths:
                python_paths.append(bin_path)

    # Remove atalhos do Windows Store
    python_paths = [p for p in python_paths if "WindowsApps" not in p]

    return python_paths

def get_python_version(path):
    try:
        output = subprocess.check_output([path, "--version"], text=True, stderr=subprocess.STDOUT)
        return output.strip()
    except Exception:
        return None

def is_version_compatible(version_str):
    """Verifica se a versão do Python é 3.10 ou superior."""
    try:
        # Extrai o número da versão do formato "Python X.Y.Z"
        match = re.search(r"Python (\d+)\.(\d+)\.(\d+)", version_str)
        if match:
            major, minor, patch = map(int, match.groups())
            # Verifica se é Python 3.10+
            return (major == 3 and minor >= 10) or major > 3
        return False
    except Exception:
        return False

def main():
    print("🔍 Procurando instalações do Python na sua máquina...\n")
    python_paths = find_python_paths()

    valid_paths = []
    compatible_paths = []
    
    for idx, path in enumerate(python_paths):
        version = get_python_version(path)
        if version:
            valid_paths.append((path, version))
            if is_version_compatible(version):
                compatible_paths.append((path, version))
    
    # Mostrar todas as versões disponíveis, mas marcar as compatíveis
    if valid_paths:
        print("Instalações do Python encontradas:")
        for idx, (path, version) in enumerate(valid_paths):
            compatibility = "✅ (compatível)" if is_version_compatible(version) else "❌ (não compatível - requer 3.10+)"
            print(f"[{idx}] {version} → {path} {compatibility}")
    
    if not valid_paths:
        print("❌ Nenhuma instalação válida do Python foi encontrada.")
        print("Por favor, instale o Python 3.10 ou superior antes de continuar.")
        print("Você pode baixar em: https://www.python.org/downloads/")
        sys.exit(1)
    
    if not compatible_paths:
        print("\n❌ Nenhuma versão compatível do Python (3.10+) foi encontrada!")
        print("O MCP requer Python 3.10 ou superior para funcionar corretamente.")
        print("Por favor, instale o Python 3.10+ antes de continuar.")
        print("Você pode baixar em: https://www.python.org/downloads/")
        print("\nInstalação interrompida.")
        sys.exit(1)
    
    try:
        if compatible_paths:
            print("\n💡 Recomendado: Escolha uma versão marcada como compatível (Python 3.10+)")
        choice = int(input("\n💡 Escolha o número da versão onde deseja instalar o uv: "))
        selected_path, selected_version = valid_paths[choice]
        
        # Verificar se a versão escolhida é compatível
        if not is_version_compatible(selected_version):
            print(f"\n❌ Você escolheu {selected_version}, que não é compatível com MCP!")
            print("O MCP requer Python 3.10 ou superior para funcionar corretamente.")
            print("Por favor, instale o Python 3.10+ e tente novamente.")
            print("Você pode baixar em: https://www.python.org/downloads/")
            print("\nInstalação interrompida.")
            sys.exit(1)
    except (ValueError, IndexError):
        print("❌ Escolha inválida.")
        return

    print(f"\n🚀 Instalando pipx com: {selected_path}")
    subprocess.run([selected_path, "-m", "pip", "install", "--user", "pipx"], check=True)
    subprocess.run([selected_path, "-m", "pipx", "ensurepath"], check=True)

    # Determinar o caminho do pipx com base na versão do Python selecionada
    python_version = selected_path.split("Python")[-1].split("\\")[0]
    pipx_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Python", f"Python{python_version}", "Scripts", "pipx.exe")
    
    print(f"\n⚡ Instalando uv com essa versão do Python...")
    print(f"Usando pipx em: {pipx_path}")
    
    # Usar o caminho completo do pipx ao invés do comando simples
    try:
        subprocess.run([pipx_path, "install", "uv", "--python", selected_path, "--force"], check=True)
        print("\n✅ Pronto! 'uv' instalado com sucesso.")
        
        # Criar arquivo de log com as informações da instalação
        log_file_path = "log.txt"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"Data da instalação: {timestamp}\n")
            log_file.write(f"Versão do Python: {selected_version}\n")
            log_file.write(f"Caminho do Python: {selected_path}\n")
        
        print(f"\nℹ️ Informações da instalação salvas em '{log_file_path}'")
        
    except FileNotFoundError:
        print(f"\n❌ Não foi possível encontrar o pipx em {pipx_path}")
        print("Alternativa: Tente instalar o uv usando:")
        print(f"{selected_path} -m pipx install uv --python {selected_path}")

if __name__ == "__main__":
    main()
