# MCP_SERVER

Plataforma para criação, gerenciamento e execução de servidores MCP (Model Context Protocol).

## Estrutura do Projeto

- `cli/`: Ferramentas de linha de comando para gerenciamento de servidores
  - `launcher.py`: Interface principal para gerenciar servidores MCP
  - `add_mcp.py`: Utilitário para adicionar novos servidores personalizados
  - `config_util.py`: Módulo de utilitários para configuração

- `gui/`: Interface gráfica para gerenciamento de servidores
  - `app.py`: Aplicação principal da interface gráfica
  - `server_manager.py`: Gerenciador de servidores 
  - `config_manager.py`: Gerenciador de configurações
  - `utils.py`: Utilitários para a interface gráfica
  
- `mcp_server/`: Diretório onde ficam os scripts dos servidores MCP

- `tools/`: Scripts auxiliares para configuração de ambiente
  - `instalar_uv.py`: Instalação do gerenciador de pacotes UV
  - `criar_projeto_mcp.py`: Criação da estrutura de projeto
  - `ativar_ambiente.py`: Ativação do ambiente virtual

- `config/`: Arquivos de configuração
  - `servers.json`: Configuração dos servidores MCP
  - `app_config.json`: Configuração da aplicação gráfica

- `quick_setup.py`: Configuração inicial automatizada
- `log.txt`: Arquivo de registro da instalação
- `requirements.txt`: Lista de dependências do projeto

## Arquivos de Atalho

- `launcher.bat`: Atalho para iniciar o gerenciador de servidores
- `add_mcp.bat`: Atalho para adicionar novos servidores

## Instalação e Uso

### Configuração Inicial

Para configurar o ambiente pela primeira vez:

```bash
python quick_setup.py
```

### Interface Gráfica (Recomendada)

Para iniciar a interface gráfica:

```bash
python gui/app.py
```

A interface gráfica oferece:
- Gerenciamento visual de servidores MCP
- Monitoramento de status em tempo real
- Iniciar, parar e reiniciar servidores
- Gerenciamento de configurações
- Visualização de logs

### Interface de Linha de Comando

Para iniciar o gerenciador de servidores via terminal:

```bash
python cli/launcher.py
```

Ou simplesmente use o atalho:

```bash
launcher.bat
```

### Adicionar Novo Servidor

Para adicionar um novo servidor personalizado via terminal:

```bash
python cli/add_mcp.py
```

Ou use o atalho:

```bash
add_mcp.bat
```

## Arquivos de Configuração

Os servidores MCP são configurados automaticamente nos seguintes locais:

- Cursor: `~/.cursor/mcp.json`
- Claude Desktop (Windows): `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`
- Claude Desktop (macOS): `~/Library/Application Support/Claude/claude_desktop_config.json`

## Recursos da Interface Gráfica

- **Sistema de Temas**: Suporte a temas para personalização da interface
- **Verificação Automática**: Monitoramento em tempo real do status dos servidores
- **Gerenciamento Simplificado**: Criação e edição de servidores com apenas alguns cliques
- **Logs Integrados**: Visualização e exportação de logs do sistema
- **Configurações Acessíveis**: Interface intuitiva para gerenciar configurações
