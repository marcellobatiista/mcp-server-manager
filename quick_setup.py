import os
import sys
import platform
import subprocess
import re
import logging
from pathlib import Path
import cli.config_util as config_util

class MCPSetup:
    """Classe responsável pela configuração inicial do ambiente MCP."""
    
    # Configurações padrão
    NOME_SERVIDOR_PADRAO = "demon"
    NOME_DIRETORIO_PADRAO = "mcp_server"
    TOOLS_DIR = "tools"
    
    def __init__(self):
        """Inicializa o configurador MCP."""
        self.sistema = platform.system()
        self.python_exe = sys.executable
        self.diretorio_base = os.path.dirname(os.path.abspath(__file__))
        self.arquivos_temp = []
        
        # Configurar logging básico
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger("mcp_setup")
    
    def cabecalho(self, titulo):
        """Exibe um cabeçalho simples."""
        print(f"\n=== {titulo} ===")
    
    def executar_comando(self, comando, mostrar_saida=False, shell=False):
        """Executa um comando e retorna o status de saída."""
        try:
            if mostrar_saida:
                return subprocess.call(comando, shell=shell)
            else:
                resultado = subprocess.run(comando, capture_output=True, text=True, shell=shell)
                return resultado.returncode
        except Exception as e:
            self.logger.error(f"Erro ao executar comando: {e}")
            return 1
    
    def criar_arquivo_temporario(self, nome, conteudo, encoding='utf-8'):
        """Cria um arquivo temporário e o adiciona à lista para limpeza posterior."""
        try:
            with open(nome, "w", encoding=encoding) as f:
                f.write(conteudo)
            self.arquivos_temp.append(nome)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao criar arquivo temporário {nome}: {e}")
            return False
    
    def limpar_arquivos_temporarios(self):
        """Remove todos os arquivos temporários criados durante o processo."""
        for arquivo in self.arquivos_temp:
            if os.path.exists(arquivo):
                try:
                    os.remove(arquivo)
                except Exception as e:
                    self.logger.warning(f"Não foi possível remover o arquivo temporário {arquivo}: {e}")
        
        # Limpar a lista de arquivos temporários
        self.arquivos_temp = []
    
    def atualizar_pip(self):
        """Atualiza o pip para a versão mais recente."""
        self.cabecalho("Atualizando pip")
        self.executar_comando([self.python_exe, "-m", "pip", "install", "--upgrade", "pip"], 
                             mostrar_saida=False)
        self.logger.info("Pip atualizado com sucesso.")
    
    def instalar_dependencias(self):
        """Instala dependências necessárias."""
        self.cabecalho("Instalando dependências")
        requirements = ["tomli>=2.0.0", "tomli-w>=1.0.0"]
        for req in requirements:
            resultado = self.executar_comando([self.python_exe, "-m", "pip", "install", req], 
                                            mostrar_saida=False)
            if resultado == 0:
                self.logger.info(f"Instalado {req}")
            else:
                self.logger.warning(f"Falha ao instalar {req}")
    
    def detectar_versoes_python(self):
        """Detecta as versões do Python instaladas no sistema."""
        pythons_encontrados = []
        
        if self.sistema == "Windows":
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
                    except Exception:
                        # Ignorar erros ao verificar versão de um Python específico
                        pass
            except Exception:
                # Ignorar erro ao executar where python
                pass
        
        # Se não encontrou nenhum Python, adicionar o atual
        if not pythons_encontrados:
            self.logger.info("Nenhuma versão do Python encontrada. Usando o Python atual.")
            pythons_encontrados.append((0, self.python_exe, "Python atual", True))
        
        return pythons_encontrados
    
    def escolher_melhor_python(self, pythons_encontrados):
        """Escolhe a melhor versão de Python disponível."""
        # Primeiro, procurar por compatíveis
        for idx, path, version, compatible in pythons_encontrados:
            if compatible:
                return idx
        
        # Se não tiver compatível, pegar o primeiro disponível
        if pythons_encontrados:
            return pythons_encontrados[0][0]
        
        return 0  # Fallback para o índice 0
    
    def instalar_uv(self):
        """Instala o UV usando o script da pasta tools."""
        self.cabecalho("Instalando UV")
        
        # Detectar versões do Python
        self.logger.info("Detectando versões do Python...")
        pythons_encontrados = self.detectar_versoes_python()
        
        # Escolher a melhor versão
        escolhido = self.escolher_melhor_python(pythons_encontrados)
        
        # Criar arquivo de resposta
        self.criar_arquivo_temporario("python_choice.txt", f"{escolhido}\n")
        
        # Obter caminho do script
        script_path = os.path.join(self.TOOLS_DIR, "instalar_uv.py")
        
        if self.sistema == "Windows":
            # Criar batch com redirecionamento
            self.criar_arquivo_temporario(
                "instalar_uv_auto.bat", 
                f"@echo off\ntype python_choice.txt | {self.python_exe} {script_path}\n", 
                encoding="cp1252"
            )
            
            self.logger.info(f"Instalando UV automaticamente com Python índice {escolhido}...")
            self.executar_comando(["instalar_uv_auto.bat"], mostrar_saida=True, shell=True)
        else:
            # No Linux/macOS
            os.system(f"cat python_choice.txt | {self.python_exe} {script_path}")
        
        # Limpar arquivos temporários
        self.limpar_arquivos_temporarios()
    
    def criar_projeto(self):
        """Cria o projeto MCP com nome padrão."""
        self.cabecalho("Criando projeto MCP")
        script_path = os.path.join(self.TOOLS_DIR, "criar_projeto_mcp.py")
        
        # Criar script temporário para resposta automática
        resposta_automatica = f"""
import sys
print("{self.NOME_DIRETORIO_PADRAO}")  # Nome do projeto
print("s")    # Responder 's' para sobrescrever o diretório existente
"""
        
        # Criar arquivo de resposta
        self.criar_arquivo_temporario("temp_criar_projeto.py", resposta_automatica)
        
        if self.sistema == "Windows":
            # Criar batch com redirecionamento
            self.criar_arquivo_temporario(
                "temp_criar_projeto.bat", 
                f"@echo off\n{self.python_exe} temp_criar_projeto.py | {self.python_exe} {script_path}\n", 
                encoding="cp1252"
            )
            
            self.executar_comando(["temp_criar_projeto.bat"], mostrar_saida=True, shell=True)
        else:
            # No Linux/macOS
            os.system(f"{self.python_exe} temp_criar_projeto.py | {self.python_exe} {script_path}")
        
        # Limpar arquivos temporários
        self.limpar_arquivos_temporarios()
    
    def ativar_ambiente(self):
        """Ativa o ambiente virtual e cria o servidor de teste."""
        self.cabecalho("Configurando ambiente")
        script_path = os.path.join(self.TOOLS_DIR, "ativar_ambiente.py")
        
        # Criar resposta automática
        self.criar_arquivo_temporario("temp_resposta.txt", "n\n")  # Responder 'n' para não executar o servidor
        
        if self.sistema == "Windows":
            # Criar batch com redirecionamento
            self.criar_arquivo_temporario(
                "temp_ativar.bat", 
                f"@echo off\ntype temp_resposta.txt | {self.python_exe} {script_path}\n", 
                encoding="cp1252"
            )
            
            self.executar_comando(["temp_ativar.bat"], mostrar_saida=True, shell=True)
        else:
            # No Linux/macOS
            os.system(f"cat temp_resposta.txt | {self.python_exe} {script_path}")
        
        # Limpar arquivos temporários
        self.limpar_arquivos_temporarios()
    
    def criar_launcher_bat(self):
        """Cria um arquivo batch para facilitar a execução do launcher."""
        try:
            launcher_script = os.path.join('cli', 'launcher.py')
            # Criar arquivo launcher.bat
            with open("launcher.bat", "w", encoding="cp1252") as f:
                f.write("@echo off\n")
                f.write("echo Iniciando MCP Launcher...\n")
                f.write(f"{self.python_exe} {launcher_script}\n")
            
            self.logger.info("✅ Criado arquivo 'launcher.bat' para execução rápida")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar arquivo launcher.bat: {e}")
            return False
    
    def ir_para_launcher(self):
        """Executa o script launcher.py para começar a gerenciar os servidores."""
        self.cabecalho("INICIANDO LAUNCHER")
        
        print("\n🚀 Iniciando o launcher MCP para gerenciar seus servidores...")
        
        try:
            # Executa o launcher.py
            script_path = os.path.join("cli", "launcher.py")
            if os.path.exists(script_path):
                self.executar_comando([self.python_exe, script_path], mostrar_saida=True)
            else:
                self.logger.error(f"❌ Não foi possível encontrar o launcher em {script_path}")
        except Exception as e:
            self.logger.error(f"❌ Erro ao iniciar o launcher: {e}")
    
    def executar_setup(self):
        """Executa o processo completo de setup."""
        self.cabecalho("CONFIGURAÇÃO RÁPIDA DO SERVIDOR MCP")
        
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
            return False
        
        try:
            # Executar cada etapa do processo
            self.atualizar_pip()
            self.instalar_dependencias()
            self.instalar_uv()
            self.criar_projeto()
            self.ativar_ambiente()
            self.criar_launcher_bat()
            
            print("\n✅ Configuração rápida concluída com sucesso!")
            print("Agora você pode executar o launcher para gerenciar seus servidores.")
            
            iniciar_launcher = input("\nDeseja iniciar o launcher agora? (s/n): ")
            if iniciar_launcher.lower() == 's':
                self.ir_para_launcher()
            else:
                print("\nVocê pode iniciar o launcher a qualquer momento executando:")
                launcher_script = os.path.join('cli', 'launcher.py')
                print(f"  python {launcher_script}")
                print("Ou usando o atalho 'launcher.bat' criado na pasta do projeto.")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erro durante o processo de setup: {e}")
            print("\n❌ Ocorreu um erro durante o processo de configuração.")
            print("Verifique os logs para mais detalhes.")
            return False
        finally:
            # Garantir que todos os arquivos temporários sejam removidos
            self.limpar_arquivos_temporarios()

def main():
    """Função principal do script."""
    setup = MCPSetup()
    setup.executar_setup()

if __name__ == "__main__":
    main() 