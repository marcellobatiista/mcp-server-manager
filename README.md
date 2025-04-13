# MCP Server Manager

Um gerenciador de servidores MCP (Model Control Protocol) para Cursor e Claude Desktop, proporcionando interfaces de linha de comando (CLI) e gráfica (GUI) para facilitar o gerenciamento de servidores MCP.

## 📋 Funcionalidades

- **Gerenciamento de Servidores MCP:** Iniciar, parar, reiniciar e monitorar servidores MCP
- **Interface Dupla:** Interface de linha de comando e interface gráfica
- **Configuração Automática:** Integração com Cursor e Claude Desktop
- **Detecção de Processos:** Identificação automática de servidores em execução
- **Quick Setup:** Sistema de configuração rápida para novos ambientes
- **Importação de Servidores:** Capacidade de importar servidores MCP existentes através da interface gráfica

## 🔍 Escopo do Projeto

### Limitações Atuais

**Importante:** Esta versão do MCP Server Manager atualmente suporta apenas servidores MCP locais.

#### O que isso significa:

- ✅ **Servidores Locais**: O projeto permite criar, configurar e executar servidores MCP que rodam na mesma máquina que o cliente LLM
- ✅ **Transporte stdio**: Os servidores implementados usam entrada/saída padrão para comunicação
- ❌ **Servidores Remotos**: Atualmente não há suporte para servidores MCP remotos via HTTP/SSE
- ❌ **Autenticação OAuth**: Não implementamos ainda a autenticação necessária para servidores remotos

#### Detalhes Técnicos

Os servidores criados por este gerenciador:
- Utilizam exclusivamente o transporte `stdio` para comunicação
- São executados como processos locais
- Não possuem endpoints HTTP expostos externamente
- São adequados para testes e desenvolvimento local

#### Roadmap Futuro

Em versões futuras, pretendemos adicionar:
- [ ] Suporte para servidores MCP remotos via HTTP/SSE
- [ ] Integração com autenticação OAuth para acesso seguro
- [ ] Hospedagem simplificada de servidores em ambientes cloud
- [ ] Interface para gerenciamento de servidores remotos

## 📸 Screenshots

### Interface Gráfica (GUI)
![Interface Gráfica](gui/assets/screenshorts/gui-menu.png)

### Interface de Linha de Comando (CLI)
![Interface de Linha de Comando](gui/assets/screenshorts/cli-menu.png)

### Integração com Cursor
![Cursor MCP Servers](gui/assets/screenshorts/cursor-servers.png)

## 🎬 Vídeo Demonstrativo

https://github.com/marcellobatiista/mcp-server-manager/gui/assets/videos/video_cursor.mp4

## 🛠️ Tecnologias Utilizadas

- Python 3.10+
- GUI com Tkinter e ttkthemes
- CLI com Rich para interface colorida e formatada
- Gestão de configuração TOML

## 🚀 Instalação

### Requisitos
- Python 3.10 ou superior
- Pip (gerenciador de pacotes Python)

### Passos para Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/marcellobatiista/mcp-server-manager.git
   cd mcp-server-manager
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Execute o setup rápido:
   ```
   python quick_setup.py
   ```

## 📚 Como Usar

### Comando Global 'mcp'

Após executar o `quick_setup.py` com sucesso, você pode iniciar a interface gráfica do MCP a partir de qualquer local usando o comando:
```
mcp
```
> ℹ️ **Observação**: É necessário abrir um novo prompt de comando após a instalação para que o comando funcione.

### Interface de Linha de Comando (CLI)

Para iniciar a interface CLI:
```
.\cli-launcher.bat
```

Ou diretamente pelo Python:
```
python cli/launcher.py
```

### Interface Gráfica (GUI)

Para iniciar a interface gráfica:
```
.\gui-launcher.bat
```

Ou diretamente pelo Python:
```
python gui/app.py
```

### Importação de Servidores

Para importar um servidor MCP existente:
1. Inicie a interface gráfica
2. Na aba de gerenciamento de servidores, clique no botão "Importar Servidor"
3. Selecione o arquivo Python (.py) do servidor que deseja importar
4. O sistema copiará o arquivo para o diretório de servidores MCP e o adicionará à lista de servidores disponíveis

## 📁 Estrutura do Projeto

O projeto está organizado da seguinte maneira:

### Diretórios Principais
```
mcp-server-manager/
│
├── mcp_server/                  # Servidores MCP implementados
│   ├── demon.py                 # Servidor demon MCP de exemplo
│   └── main.py                  # Ponto de entrada para servidores
│
├── cli/                         # Interface de linha de comando (CLI)
│   ├── launcher.py              # Aplicação principal CLI
│   ├── add_mcp.py               # Utilitário para adicionar novos servidores
│   └── config_util.py           # Utilitários de configuração
│
├── gui/                         # Interface gráfica de usuário (GUI)
│   ├── app.py                   # Aplicação principal GUI
│   ├── server_manager.py        # Gerenciamento de servidores
│   ├── config_manager.py        # Gerenciamento de configurações
│   ├── utils.py                 # Utilitários e helpers
│   └── assets/                  # Recursos gráficos
│
├── config/                      # Configurações do sistema
│   ├── servers.json             # Lista de servidores disponíveis
│   └── app_config.json          # Configurações da aplicação
│
├── tests/                       # Testes automatizados
│   └── test_mcp_server.py       # Testes para verificar a estrutura do projeto
│
├── tools/                       # Scripts e ferramentas auxiliares
│
└── logs/                        # Registros de execução
```

### Arquivos Principais
- `quick_setup.py` - Configuração inicial automatizada
- `cli-launcher.bat` - Atalho para iniciar a CLI
- `gui-launcher.bat` - Atalho para iniciar a GUI
- `requirements.txt` - Dependências do projeto

### Arquivos de Configuração do Cliente
O sistema interage com arquivos de configuração nas seguintes localizações:

- **Cursor:** `%USERPROFILE%\.cursor\mcp.json`
- **Claude Desktop (Windows):** `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`
- **Claude Desktop (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`

### Testes
O diretório `tests/` contém testes automatizados que verificam:
- A existência da estrutura de diretórios esperada
- A presença dos servidores MCP implementados
- A configuração correta dos clientes Cursor/Claude Desktop

## 💡 Arquivos de Configuração

O sistema gerencia arquivos de configuração nas seguintes localizações:

- **Cursor:** `~/.cursor/mcp.json`
- **Claude Desktop (Windows):** `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`
- **Claude Desktop (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`

## ☕ Me Pague um Café

Se este projeto foi útil para você, considere me pagar um cafezinho!

[☕ Doar um Café](https://link.mercadopago.com.br/doarumcafe)

## 📄 Licença

Este projeto está licenciado sob os termos da [Licença MIT](LICENSE).