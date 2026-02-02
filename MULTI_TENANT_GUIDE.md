# 🏢 Guia Multi-Tenant - Fábrica de Artigos SEO

## 📋 Visão Geral

Este sistema permite gerenciar **múltiplas empresas/clientes** com configurações independentes, incluindo:
- ✅ **Prompts compartilhados** (todos usam a mesma estrutura TRI)
- ✅ **Knowledge Base opcional** por empresa
- ✅ **Credenciais WordPress separadas**
- ✅ **Planilhas Google Sheets independentes**

---

## 🗂️ Estrutura de Pastas

```
Fábrica de Artigos SEO/
├── config/
│   ├── sites.json                    # Configuração de TODAS as empresas
│   ├── prompts.py                    # Prompts COMPARTILHADOS (TRI)
│   ├── service_account.json          # Credencial Google Sheets
│   └── companies/                    # Pasta de empresas
│       ├── mjesus/                   # Empresa 1: Marcelo Jesus
│       │   └── knowledge_base/
│       │       ├── TRI Premium.txt   # Base de conhecimento TRI
│       │       └── ...
│       ├── empresa2/                 # Empresa 2: Exemplo
│       │   └── knowledge_base/       # (vazia = usa conhecimento geral da IA)
│       └── empresa3/
│           └── knowledge_base/
```

---

## ➕ Como Adicionar uma Nova Empresa

### **Passo 1: Criar a estrutura de pastas**

```bash
mkdir -p "config/companies/NOME_DA_EMPRESA/knowledge_base"
```

**Exemplo:**
```bash
mkdir -p "config/companies/clinica_odonto/knowledge_base"
```

### **Passo 2: Adicionar configuração no `config/sites.json`**

Abra o arquivo `config/sites.json` e adicione um novo objeto no array:

```json
[
  {
    "site_name": "https://mjesus.com.br/",
    "company_id": "mjesus",
    "spreadsheet_id": "1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4",
    "wordpress_url": "https://mjesus.com.br",
    "persona_prompt": "Especialista em Terapia de Reintegração Implícita (TRI)",
    "wordpress_username": "marcelo_seo",
    "wordpress_app_password": "NRb7 y9D7 jnNQ IELM HeZZ LXEf"
  },
  {
    "site_name": "Clínica Odontológica Exemplo",
    "company_id": "clinica_odonto",
    "spreadsheet_id": "SEU_SPREADSHEET_ID_AQUI",
    "wordpress_url": "https://clinicaodonto.com.br",
    "persona_prompt": "Especialista em Odontologia e Saúde Bucal",
    "wordpress_username": "admin",
    "wordpress_app_password": "xxxx xxxx xxxx xxxx"
  }
]
```

### **Passo 3: (Opcional) Adicionar Knowledge Base**

Se a empresa tiver uma metodologia própria ou conteúdo específico:

1. Crie arquivos `.txt` em `config/companies/NOME_DA_EMPRESA/knowledge_base/`
2. **IMPORTANTE:** Use "premium" no nome do arquivo para ser carregado
   - ✅ `metodologia_premium.txt`
   - ✅ `conhecimento_premium.txt`
   - ❌ `documento.txt` (será ignorado)

**Se NÃO adicionar arquivos:** O sistema usará apenas o conhecimento geral da IA Gemini.

### **Passo 4: Configurar a Planilha Google Sheets**

Cada empresa precisa de uma planilha com a seguinte estrutura:

| Keyword | Status | Link |
|---------|--------|------|
| palavra-chave 1 | Pending | |
| palavra-chave 2 | Pending | |

**Como obter o Spreadsheet ID:**
- URL da planilha: `https://docs.google.com/spreadsheets/d/1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4/edit`
- O ID é: `1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4`

### **Passo 5: Configurar WordPress**

1. Acesse o WordPress da empresa
2. Vá em **Usuários → Perfil**
3. Role até **Senhas de Aplicativo**
4. Crie uma nova senha com nome "SEO Automation"
5. Copie a senha gerada (formato: `xxxx xxxx xxxx xxxx`)
6. Use no campo `wordpress_app_password` do `sites.json`

---

## 🚀 Como Executar

```bash
source venv/bin/activate
python main.py
```

O sistema irá:
1. ✅ Processar **todas as empresas** do `sites.json` em sequência
2. ✅ Carregar a knowledge base específica de cada empresa (se existir)
3. ✅ Gerar artigos para palavras-chave pendentes
4. ✅ Publicar no WordPress correspondente
5. ✅ Atualizar a planilha com o link do artigo

---

## 📊 Exemplo de Saída

```
🚀 SEO Orchestrator (Multi-Tenant Architecture) Starting...

================================================================================
🏢 Processing Company: https://mjesus.com.br/ (ID: mjesus)
================================================================================
✅ Brain initialized for 'mjesus' with KB path: config/companies/mjesus/knowledge_base
     [Brain] Loaded Base: TRI Premium.txt
     Fetching Article Inventory for Link Building...
     Found 15 existing articles to potential link to.
Found 6 pending keywords to write.

👉 Working on Keyword: Hipnoterapia para Iniciantes
     1. Analyst Agent: Creating Strategic Outline...
     ...

================================================================================
🏢 Processing Company: Clínica Odontológica (ID: clinica_odonto)
================================================================================
✅ Brain initialized for 'clinica_odonto' with KB path: config/companies/clinica_odonto/knowledge_base
     [Brain] No .txt files in 'config/companies/clinica_odonto/knowledge_base'. Using AI's general knowledge.
     ...
```

---

## 🎯 Campos do `sites.json` Explicados

| Campo | Descrição | Obrigatório |
|-------|-----------|-------------|
| `site_name` | Nome descritivo da empresa | ✅ Sim |
| `company_id` | ID único (usado para pasta de knowledge base) | ✅ Sim |
| `spreadsheet_id` | ID da planilha Google Sheets | ✅ Sim |
| `wordpress_url` | URL do site WordPress (sem barra no final) | ✅ Sim |
| `persona_prompt` | Descrição da especialidade (para contexto) | ⚠️ Opcional |
| `wordpress_username` | Usuário do WordPress | ✅ Sim |
| `wordpress_app_password` | Senha de aplicativo do WordPress | ✅ Sim |

---

## 💡 Dicas e Boas Práticas

### **Knowledge Base:**
- ✅ Use apenas arquivos com "premium" no nome
- ✅ Mantenha arquivos pequenos (< 100KB) para evitar limite de tokens
- ✅ Se não tiver metodologia própria, deixe a pasta vazia

### **Company ID:**
- ✅ Use apenas letras minúsculas, números e underscores
- ✅ Exemplos: `mjesus`, `clinica_odonto`, `consultoria_ti`
- ❌ Evite: `Clínica Odonto`, `empresa-2`, `Site #1`

### **Planilhas:**
- ✅ Compartilhe a planilha com o email do service account
- ✅ Dê permissão de **Editor**
- ✅ Use a aba padrão (primeira aba)

---

## 🔧 Troubleshooting

### Erro: "No knowledge base found"
**Solução:** Isso é normal! Se a empresa não tem base de conhecimento, o sistema usa conhecimento geral da IA.

### Erro: "Error accessing sheets"
**Solução:** Verifique se:
1. O `spreadsheet_id` está correto
2. A planilha foi compartilhada com o service account
3. O service account tem permissão de Editor

### Erro: "Cannot authenticate with WordPress"
**Solução:** 
1. Verifique se o `wordpress_username` está correto
2. Gere uma nova senha de aplicativo no WordPress
3. Certifique-se de que o plugin de API REST está ativo

---

## 📝 Próximos Passos

Após configurar o sistema multi-tenant, você pode:
1. ✅ Adicionar mais empresas facilmente
2. ✅ Criar bases de conhecimento customizadas
3. ✅ Escalar para dezenas de clientes sem modificar código
4. ✅ Gerar artigos em massa para múltiplos sites simultaneamente

---

**Criado por:** Antigravity AI Assistant  
**Data:** 2026-02-01  
**Versão:** 2.0 Multi-Tenant
