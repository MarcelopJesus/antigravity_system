---
description: Criar novo tenant/cliente no sistema Fábrica de Artigos SEO
---

# Workflow: Criar Novo Tenant

## Pré-requisitos (perguntar ao usuário se não informou)

Solicitar ao usuário as seguintes informações:

1. **Nome da Empresa** - Nome descritivo do cliente
2. **Company ID** - Identificador único (letras minúsculas, números, underscores)
3. **Spreadsheet ID** - ID da planilha Google Sheets do cliente
4. **WordPress URL** - URL do site WordPress (sem barra no final)
5. **WordPress Username** - Usuário do WordPress
6. **WordPress App Password** - Senha de aplicativo do WordPress
7. **Tem Knowledge Base?** - Se tem metodologia própria (sim/não)

## Passos de Execução

### 1. Criar estrutura de pastas

// turbo
```bash
mkdir -p "config/companies/{company_id}/knowledge_base"
```

### 2. Criar README na knowledge base

Criar arquivo `config/companies/{company_id}/knowledge_base/README.md` com instruções.

### 3. Adicionar ao sites.json

Editar `config/sites.json` e adicionar novo objeto ao array:

```json
{
  "site_name": "{nome_empresa}",
  "company_id": "{company_id}",
  "spreadsheet_id": "{spreadsheet_id}",
  "wordpress_url": "{wordpress_url}",
  "persona_prompt": "Especialista em {area}",
  "wordpress_username": "{wordpress_username}",
  "wordpress_app_password": "{wordpress_app_password}"
}
```

### 4. Aplicar formatação na planilha

// turbo
```bash
source venv/bin/activate && python format_spreadsheet.py {spreadsheet_id}
```

### 5. Testar conexão com Google Sheets

// turbo
```bash
source venv/bin/activate && python -c "
from core.sheets_client import SheetsClient
sheets = SheetsClient('config/service_account.json')
pending = sheets.get_pending_rows('{spreadsheet_id}')
print(f'✅ Sheets OK - {len(pending)} keywords pendentes')
"
```

### 6. Testar autenticação WordPress

// turbo
```bash
source venv/bin/activate && python -c "
from core.wordpress_client import WordPressClient
wp = WordPressClient('{wordpress_url}', '{wordpress_username}', '{wordpress_app_password}')
if wp.verify_auth():
    print('✅ WordPress autenticado com sucesso!')
else:
    print('❌ Falha na autenticação WordPress')
"
```

### 7. Confirmar criação

Exibir resumo:

```
✅ TENANT CRIADO COM SUCESSO!

📋 Resumo:
- Nome: {nome_empresa}
- Company ID: {company_id}
- Knowledge Base: {tem_kb}
- Sheets: ✅ Conectado
- WordPress: ✅ Autenticado

🚀 Próximos passos:
1. Cliente pode adicionar keywords na planilha
2. Execute 'python main.py' para gerar artigos
3. (Opcional) Adicione arquivos .txt na knowledge_base
```

## Troubleshooting

### Erro: "Planilha não encontrada"
- Verifique se o Spreadsheet ID está correto
- Confirme que compartilhou com: `seo-robo@seo-orchestrador.iam.gserviceaccount.com`
- Permissão deve ser "Editor"

### Erro: "WordPress authentication failed"
- Gere nova senha de aplicativo no WordPress
- Verifique se o username está correto (case sensitive)
- Confirme que a API REST está ativa

### Erro: "Company ID já existe"
- Escolha outro company_id único
- Verifique `config/sites.json` para IDs existentes
