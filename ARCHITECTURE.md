# 🏗️ Arquitetura do Sistema Multi-Tenant

## Fluxo de Execução

```
┌─────────────────────────────────────────────────────────────────────┐
│                         main.py (Orquestrador)                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Carrega config/sites.json   │
                    │   (Lista de todas empresas)   │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌─────────────────────┐       ┌─────────────────────┐
        │   Empresa 1 (mjesus)│       │   Empresa 2         │
        └─────────────────────┘       └─────────────────────┘
                    │                               │
        ┌───────────┴───────────┐       ┌──────────┴──────────┐
        ▼                       ▼       ▼                     ▼
┌──────────────┐      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ GeminiBrain  │      │ SheetsClient │ │ GeminiBrain  │ │ SheetsClient │
│   + KB TRI   │      │  Planilha 1  │ │  (sem KB)    │ │  Planilha 2  │
└──────────────┘      └──────────────┘ └──────────────┘ └──────────────┘
        │                     │                │                  │
        └──────────┬──────────┘                └────────┬─────────┘
                   ▼                                    ▼
        ┌─────────────────────┐           ┌─────────────────────┐
        │  WordPress Site 1   │           │  WordPress Site 2   │
        │  mjesus.com.br      │           │  empresa2.com       │
        └─────────────────────┘           └─────────────────────┘
```

## Estrutura de Dados

```
config/
├── sites.json ──────────────────┐
│   [                            │
│     {                          │  Para cada empresa:
│       "company_id": "mjesus",  │  ├── Inicializa Brain com KB específico
│       "spreadsheet_id": "...", │  ├── Conecta ao Google Sheets
│       "wordpress_url": "...",  │  ├── Autentica no WordPress
│       ...                      │  └── Processa keywords pendentes
│     }                          │
│   ]                            │
└─────────────────────────────────┘
│
└── companies/
    ├── mjesus/
    │   └── knowledge_base/
    │       └── TRI Premium.txt ──► Carregado pelo Brain
    │
    └── empresa2/
        └── knowledge_base/
            └── (vazio) ──────────► Brain usa conhecimento geral da IA
```

## Pipeline de Geração de Artigos

```
Para cada empresa em sites.json:
  │
  ├─► 1. Inicializa Brain com knowledge_base específico
  │      ├─ Se KB existe: Carrega metodologia proprietária
  │      └─ Se KB vazio: Usa conhecimento geral da IA
  │
  ├─► 2. Conecta ao Google Sheets da empresa
  │      └─ Busca keywords com Status = "Pending"
  │
  ├─► 3. Para cada keyword:
  │      │
  │      ├─► Agente 1: ANALISTA
  │      │   └─ Cria outline estratégico (JSON)
  │      │
  │      ├─► Agente 2: REDATOR
  │      │   └─ Escreve conteúdo completo (HTML)
  │      │
  │      ├─► Agente 3: EDITOR
  │      │   └─ Refina e otimiza SEO
  │      │
  │      ├─► Agente 4: VISUAL
  │      │   ├─ Gera 3 prompts de imagem
  │      │   └─ Cria imagens com Imagen 4.0
  │      │
  │      ├─► Publica no WordPress
  │      │   ├─ Envia conteúdo + imagens
  │      │   ├─ Configura Yoast SEO
  │      │   └─ Status: PUBLISH
  │      │
  │      ├─► Atualiza Google Sheets
  │      │   └─ Status: "Done" + Link do artigo
  │      │
  │      └─► Agente 5: GROWTH HACKER
  │          └─ Sugere 2 novos tópicos relacionados
  │
  └─► Próxima empresa...
```

## Componentes Principais

### 1. GeminiBrain (core/gemini_brain.py)
- **Responsabilidade**: Gerenciar chamadas à API Gemini
- **Multi-tenant**: Aceita `knowledge_base_path` customizado
- **Features**:
  - Rotação automática de API keys
  - Carregamento de KB por empresa
  - 5 agentes especializados

### 2. SheetsClient (core/sheets_client.py)
- **Responsabilidade**: Gerenciar Google Sheets
- **Multi-tenant**: Aceita `spreadsheet_id` diferente por empresa
- **Features**:
  - Buscar keywords pendentes
  - Atualizar status e links
  - Adicionar novos tópicos

### 3. WordPressClient (core/wordpress_client.py)
- **Responsabilidade**: Publicar no WordPress
- **Multi-tenant**: Aceita credenciais diferentes por empresa
- **Features**:
  - Upload de imagens
  - Criação de posts
  - Configuração Yoast SEO

## Vantagens da Arquitetura Multi-Tenant

✅ **Escalabilidade**: Adicione empresas sem modificar código
✅ **Isolamento**: Cada empresa tem sua própria KB e configurações
✅ **Flexibilidade**: KB opcional - empresas sem metodologia própria
✅ **Manutenibilidade**: Prompts compartilhados, fácil de atualizar
✅ **Segurança**: Credenciais separadas por empresa

## Exemplo de Uso

```bash
# Adicionar nova empresa
python add_company.py

# Executar para todas as empresas
python main.py

# O sistema processa automaticamente:
# - mjesus.com.br (com KB TRI)
# - empresa2.com (sem KB)
# - empresa3.com (com KB próprio)
# ...
```
