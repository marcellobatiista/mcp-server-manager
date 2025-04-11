# CLI - Ferramentas de Linha de Comando para MCP Server

Este diretório contém as ferramentas de linha de comando para gerenciamento e configuração de servidores MCP.

## Componentes

- **launcher.py**: Interface principal para gerenciar servidores MCP. Permite listar, iniciar, parar e remover servidores.
- **add_mcp.py**: Utilitário para adicionar novos servidores MCP personalizados.
- **config_util.py**: Módulo de utilitários para manipular arquivos de configuração dos clientes MCP (Cursor e Claude Desktop).

## Uso

Para iniciar o gerenciamento de servidores MCP, use o script `launcher.py`:

```bash
python cli/launcher.py
```

Para adicionar um novo servidor MCP:

```bash
python cli/add_mcp.py
```

## Arquivos de Configuração

O módulo `config_util.py` gerencia os arquivos de configuração nas seguintes localizações:

- Cursor: `~/.cursor/mcp.json`
- Claude Desktop (Windows): `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`
- Claude Desktop (macOS): `~/Library/Application Support/Claude/claude_desktop_config.json`
