import os
import sys
import pytest
import json

# Adiciona o diretório raiz ao sys.path para importações relativas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_mcp_server_directory_exists():
    """Verifica se a pasta mcp_server existe no projeto"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mcp_server_path = os.path.join(base_dir, 'mcp_server')
    
    assert os.path.exists(mcp_server_path), f"A pasta mcp_server não foi encontrada em {base_dir}"
    assert os.path.isdir(mcp_server_path), f"O caminho {mcp_server_path} existe, mas não é uma pasta"

def test_demon_py_exists():
    """Verifica se o arquivo demon.py existe dentro do diretório mcp_server"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mcp_server_path = os.path.join(base_dir, 'mcp_server')
    demon_py_path = os.path.join(mcp_server_path, 'demon.py')
    
    assert os.path.exists(demon_py_path), f"O arquivo demon.py não foi encontrado em {mcp_server_path}"
    assert os.path.isfile(demon_py_path), f"O caminho {demon_py_path} existe, mas não é um arquivo"

def test_client_config_exists():
    """Verifica se os arquivos de configuração dos clientes existem"""
    # Obtém o diretório do usuário
    user_profile = os.environ.get('USERPROFILE')
    
    # Caminho para o arquivo de configuração do Cursor
    cursor_config_path = os.path.join(user_profile, '.cursor', 'mcp.json')
    
    # Caminho para o arquivo de configuração do Claude Desktop
    claude_config_path = os.path.join(user_profile, 'AppData', 'Roaming', 'Claude', 'claude_desktop_config.json')
    
    # Verifica se pelo menos um dos arquivos de configuração existe
    cursor_exists = os.path.exists(cursor_config_path)
    claude_exists = os.path.exists(claude_config_path)
    
    # O teste passa se pelo menos um dos arquivos existir
    assert cursor_exists or claude_exists, "Nenhum arquivo de configuração do cliente encontrado (nem Cursor nem Claude Desktop)"
    
    # Mensagem informativa sobre quais arquivos foram encontrados
    if cursor_exists and claude_exists:
        print("Ambos os arquivos de configuração do Cursor e Claude Desktop foram encontrados")
    elif cursor_exists:
        print("Apenas o arquivo de configuração do Cursor foi encontrado")
    elif claude_exists:
        print("Apenas o arquivo de configuração do Claude Desktop foi encontrado")

def test_mcp_servers_config():
    """Verifica as configurações dos servidores MCP nos arquivos de configuração dos clientes"""
    # Obtém o diretório do usuário
    user_profile = os.environ.get('USERPROFILE')
    
    # Caminhos para os arquivos de configuração
    cursor_config_path = os.path.join(user_profile, '.cursor', 'mcp.json')
    claude_config_path = os.path.join(user_profile, 'AppData', 'Roaming', 'Claude', 'claude_desktop_config.json')
    
    # Caminho esperado para o diretório mcp_server
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    expected_mcp_server_path = os.path.join(base_dir, 'mcp_server')
    
    configs_found = False
    valid_servers_found = False
    
    # Verifica o arquivo de configuração do Cursor
    if os.path.exists(cursor_config_path):
        configs_found = True
        try:
            with open(cursor_config_path, 'r') as f:
                cursor_config = json.load(f)
            
            if 'mcpServers' in cursor_config:
                servers = cursor_config['mcpServers']
                assert isinstance(servers, dict), "mcpServers no arquivo do Cursor não é um dicionário"
                
                # Verifica cada servidor na configuração
                for server_name, server_config in servers.items():
                    print(f"Verificando servidor {server_name} na configuração do Cursor")
                    
                    # Verifica se o comando termina com uv.exe ou uvx.exe
                    command = server_config.get('command', '')
                    assert command.endswith('uv.exe') or command.endswith('uvx.exe'), \
                        f"Comando do servidor {server_name} não termina com uv.exe ou uvx.exe: {command}"
                    
                    # Verifica se args contém caminho para mcp_server
                    args = server_config.get('args', [])
                    assert isinstance(args, list), f"Args do servidor {server_name} não é uma lista"
                    
                    mcp_server_path_found = False
                    for arg in args:
                        if not isinstance(arg, str):
                            continue
                            
                        # Verifica se o argumento é um caminho para o diretório mcp_server
                        # Verifica exatamente o nome do diretório, não apenas se contém a string
                        if arg.endswith('mcp_server') or arg.endswith('mcp_server' + os.path.sep):
                            # Verifica se o caminho existe
                            if os.path.exists(arg) and os.path.isdir(arg):
                                mcp_server_path_found = True
                                break
                            
                        # Para caminhos com barras invertidas escapadas (como em JSON)
                        normalized_arg = arg.replace('\\\\', '\\')
                        if normalized_arg.endswith('mcp_server') or normalized_arg.endswith('mcp_server' + os.path.sep):
                            # Tenta normalizar o caminho para verificar sua existência
                            try:
                                if os.path.exists(normalized_arg) and os.path.isdir(normalized_arg):
                                    mcp_server_path_found = True
                                    break
                            except:
                                pass  # Ignora erros de caminho inválido
                    
                    assert mcp_server_path_found, f"Caminho válido para mcp_server não encontrado nos args do servidor {server_name}"
                    valid_servers_found = True
        except Exception as e:
            assert False, f"Erro ao analisar arquivo de configuração do Cursor: {str(e)}"
    
    # Verifica o arquivo de configuração do Claude Desktop
    if os.path.exists(claude_config_path):
        configs_found = True
        try:
            with open(claude_config_path, 'r') as f:
                claude_config = json.load(f)
            
            if 'mcpServers' in claude_config:
                servers = claude_config['mcpServers']
                assert isinstance(servers, dict), "mcpServers no arquivo do Claude Desktop não é um dicionário"
                
                # Verifica cada servidor na configuração
                for server_name, server_config in servers.items():
                    print(f"Verificando servidor {server_name} na configuração do Claude Desktop")
                    
                    # Verifica se o comando termina com uv.exe ou uvx.exe
                    command = server_config.get('command', '')
                    assert command.endswith('uv.exe') or command.endswith('uvx.exe'), \
                        f"Comando do servidor {server_name} não termina com uv.exe ou uvx.exe: {command}"
                    
                    # Verifica se args contém caminho para mcp_server
                    args = server_config.get('args', [])
                    assert isinstance(args, list), f"Args do servidor {server_name} não é uma lista"
                    
                    mcp_server_path_found = False
                    for arg in args:
                        if not isinstance(arg, str):
                            continue
                            
                        # Verifica se o argumento é um caminho para o diretório mcp_server
                        # Verifica exatamente o nome do diretório, não apenas se contém a string
                        if arg.endswith('mcp_server') or arg.endswith('mcp_server' + os.path.sep):
                            # Verifica se o caminho existe
                            if os.path.exists(arg) and os.path.isdir(arg):
                                mcp_server_path_found = True
                                break
                            
                        # Para caminhos com barras invertidas escapadas (como em JSON)
                        normalized_arg = arg.replace('\\\\', '\\')
                        if normalized_arg.endswith('mcp_server') or normalized_arg.endswith('mcp_server' + os.path.sep):
                            # Tenta normalizar o caminho para verificar sua existência
                            try:
                                if os.path.exists(normalized_arg) and os.path.isdir(normalized_arg):
                                    mcp_server_path_found = True
                                    break
                            except:
                                pass  # Ignora erros de caminho inválido
                    
                    assert mcp_server_path_found, f"Caminho válido para mcp_server não encontrado nos args do servidor {server_name}"
                    valid_servers_found = True
        except Exception as e:
            assert False, f"Erro ao analisar arquivo de configuração do Claude Desktop: {str(e)}"
    
    # Verifica se pelo menos um arquivo de configuração foi encontrado
    assert configs_found, "Nenhum arquivo de configuração encontrado"
    
    # Verifica se pelo menos um servidor válido foi encontrado
    assert valid_servers_found, "Nenhum servidor válido encontrado nas configurações"


if __name__ == '__main__':
    pytest.main(['-v']) 