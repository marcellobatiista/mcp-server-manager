# MCP Server Manager

[![Licença MIT](https://img.shields.io/badge/Licença-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Status do Projeto](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow.svg)]()
[![Documentação](https://img.shields.io/badge/Docs-README-orange.svg)]()
[![Versão](https://img.shields.io/badge/Versão-1.0.0-brightgreen.svg)]()
[![Dependências](https://img.shields.io/badge/Dependências-5-informational.svg)](requirements.txt)
[![Compatibilidade](https://img.shields.io/badge/Compatibilidade-Windows%20|%20macOS-lightgrey.svg)]()
[![MCP Protocol](https://img.shields.io/badge/MCP-Model%20Control%20Protocol-blueviolet.svg)]()

Um gerenciador de servidores MCP (Model Control Protocol) para Cursor e Claude Desktop, proporcionando interfaces de linha de comando (CLI) e gráfica (GUI) para facilitar o gerenciamento de servidores MCP.

## 🔎 Visão Geral

O MCP Server Manager facilita a criação, configuração e gerenciamento de servidores MCP (Model Control Protocol). 
Este projeto é destinado principalmente a desenvolvedores que desejam criar, testar e utilizar servidores MCP locais com Cursor e Claude Desktop.

## 📋 Funcionalidades

- **Gerenciamento de Servidores MCP:** Iniciar, parar, reiniciar e monitorar servidores MCP
- **Interface Dupla:** Interface de linha de comando e interface gráfica
- **Configuração Automática:** Integração com Cursor e Claude Desktop
- **Detecção de Processos:** Identificação automática de servidores em execução
- **Quick Setup:** Sistema de configuração rápida para novos ambientes
- **Importação de Servidores:** Capacidade de importar servidores MCP existentes através da interface gráfica
- **Sistema Multi-plataforma:** Compatível com Windows e macOS
- **Gestão de Ambiente:** Configuração automática do ambiente Python

## 🖥️ Compatibilidade

| Plataforma | Estado | Observações |
|------------|--------|-------------|
| Windows    | ✅ Completo | Testado no Windows 10/11 |
| macOS      | ✅ Completo | Testado no macOS 12+ |
| Linux      | ⚠️ Parcial | Suporte experimental |


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
- [ ] Suporte completo para Linux
- [ ] Painel de métricas e desempenho
- [ ] Modo debug avançado

## 📸 Screenshots

### Interface Gráfica (GUI)
![Interface Gráfica](gui/assets/screenshorts/gui-menu.png)

### Interface de Linha de Comando (CLI)
![Interface de Linha de Comando](gui/assets/screenshorts/cli-menu.png)

### Integração com Cursor
![Cursor MCP Servers](gui/assets/screenshorts/cursor-servers.png)

## 🎬 Vídeo Demonstrativo

![Demonstração do MCP Server Manager](gui/assets/videos/video_cursor.gif)

## 🛠️ Tecnologias Utilizadas

- Python 3.10+
- GUI com Tkinter e ttkthemes
- CLI com Rich para interface colorida e formatada
- Gestão de configuração TOML
- Detecção de processos com Psutil
- Gerenciamento de ambientes Python com UV

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

### Verificação da Instalação

Para verificar se a instalação foi bem-sucedida, execute:
```
mcp
```

Você deve ver a versão atual do MCP Server Manager.

## 🚀 Primeiros Passos

Para começar a usar o MCP Server Manager rapidamente, siga estas etapas:

### 1. Criando seu Primeiro Servidor

Depois de completar a instalação, você pode criar seu primeiro servidor MCP:

1. Inicie a interface gráfica com o comando `mcp`
2. Na tela principal, clique em "Adicionar Novo Servidor"
3. Escolha um dos modelos disponíveis ou importe um servidor existente
4. Dê um nome ao seu servidor
5. Clique em "Criar" para finalizar

### 2. Configurando o Cursor

Para usar seu servidor com o Cursor:

1. Inicie o Cursor
2. Acesse as configurações (ícone de engrenagem)
3. Vá para a seção "Servidores MCP" 
4. Seu servidor criado com o MCP Server Manager já deve aparecer na lista
5. Selecione-o para ativar

### 3. Teste Rápido

Para verificar se seu servidor está funcionando corretamente:

1. No MCP Server Manager, inicie seu servidor clicando no botão "Iniciar"
2. Abra o Cursor e crie um novo documento
3. No seletor de modelos, escolha seu servidor MCP
4. Digite uma pergunta simples para testar a resposta

Agora você está pronto para utilizar seu servidor MCP personalizado!

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

## 🔧 Configuração

### Arquivos de Configuração do Cliente
O sistema interage com arquivos de configuração nas seguintes localizações:

- **Cursor:** `%USERPROFILE%\.cursor\mcp.json`
- **Claude Desktop (Windows):** `%USERPROFILE%\AppData\Roaming\Claude\claude_desktop_config.json`
- **Claude Desktop (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`

### Configuração Manual
Se preferir configurar manualmente os clientes, siga estas instruções:

#### Cursor
1. Abra o arquivo `%USERPROFILE%\.cursor\mcp.json`
2. Adicione seu servidor à lista `localMcpServers`

#### Claude Desktop
1. Abra o arquivo de configuração adequado ao seu sistema
2. Adicione o caminho para o servidor na seção `mcp.localServers`

## 🧪 Testes

### Executando Testes
Para executar os testes automatizados:
```
python -m pytest tests/
```

O diretório `tests/` contém testes automatizados que verificam:
- A existência da estrutura de diretórios esperada
- A presença dos servidores MCP implementados
- A configuração correta dos clientes Cursor/Claude Desktop

## ❤️ Apoie o Projeto

Este projeto é open source e disponibilizado gratuitamente sob a [Licença MIT](LICENSE).

### ☕ Me Pague um Café

Se este gerenciador de servidores MCP foi útil para você, considere apoiar o desenvolvimento contínuo do projeto:

[☕ Doar um Café](https://link.mercadopago.com.br/doarumcafe)

### 🌟 Benefícios do Seu Apoio

Com seu apoio, posso:

- ✅ Desenvolver novas funcionalidades
- ✅ Aprimorar a interface gráfica e experiência do usuário
- ✅ Criar mais documentação e tutoriais
- ✅ Manter a compatibilidade com novas versões do Cursor e Claude Desktop
- ✅ Dedicar mais tempo à resolução de problemas e suporte à comunidade

### 🤝 Outras Formas de Contribuir

- **Código:** Contribua com pull requests para melhorar o projeto
- **Ideias:** Abra issues com sugestões e funcionalidades desejadas
- **Compartilhe:** Divulgue o projeto para quem possa se beneficiar dele
- **Documentação:** Ajude a melhorar tutoriais e documentação

## ❓ Perguntas Frequentes (FAQ)

<details>
<summary><b>O que é o Model Control Protocol (MCP)?</b></summary>
O MCP é um protocolo que permite que aplicativos como Cursor e Claude Desktop se comuniquem com modelos de linguagem. Ele define como os aplicativos enviam solicitações para esses modelos e como recebem suas respostas.
</details>

<details>
<summary><b>Preciso conhecer Python para usar o MCP Server Manager?</b></summary>
Não necessariamente. Para usar servidores já existentes, a interface gráfica (GUI) é intuitiva e não requer conhecimentos de programação. No entanto, para desenvolver seus próprios servidores MCP, conhecimentos básicos de Python são recomendados.
</details>

<details>
<summary><b>Posso usar o MCP Server Manager com outros aplicativos além do Cursor e Claude Desktop?</b></summary>
Sim, desde que esses aplicativos suportem o protocolo MCP. No entanto, nossa documentação e testes focam principalmente na integração com Cursor e Claude Desktop.
</details>

<details>
<summary><b>É seguro executar servidores MCP locais?</b></summary>
Sim. Os servidores MCP locais executam apenas em sua máquina e não expõem endpoints HTTP externos. As comunicações acontecem via stdio (entrada/saída padrão), o que limita o risco de exposição externa.
</details>

<details>
<summary><b>O MCP Server Manager consome muitos recursos do sistema?</b></summary>
Não. O MCP Server Manager foi projetado para ser leve e eficiente. O consumo de recursos depende principalmente dos servidores MCP específicos que você está executando.
</details>

<details>
<summary><b>Posso usar o MCP Server Manager em ambientes de produção?</b></summary>
Atualmente, o MCP Server Manager é mais adequado para ambientes de desenvolvimento e teste. Para uso em produção, recomendamos aguardar futuras versões com suporte a servidores remotos e recursos de segurança adicionais.
</details>

## 🔒 Segurança

### Práticas de Segurança

O MCP Server Manager foi desenvolvido com as seguintes considerações de segurança:

- **Isolamento Local**: Os servidores MCP são executados localmente, minimizando riscos de exposição externa
- **Sem Endpoints Expostos**: Não há endpoints HTTP expostos na implementação atual
- **Validação de Entradas**: As entradas do usuário são validadas antes do processamento
- **Gerenciamento de Processos**: Processos de servidor são monitorados e gerenciados de forma segura

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<p align="center">
  <sub>Desenvolvido com ❤️ por <a href="https://github.com/marcellobatiista">Marcelo Batista</a></sub>
</p>
