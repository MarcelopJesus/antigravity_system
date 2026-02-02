# 📋 Guia de Onboarding de Clientes - Fábrica de Artigos SEO

## 🎯 Visão Geral

Este guia explica como adicionar novos clientes ao sistema de geração de artigos SEO.

**Modelo:** Cada cliente tem sua própria planilha Google Sheets para preencher keywords.

---

## 📊 PASSO 1: Criar Planilha do Cliente

### Opção A: Duplicar Template (Recomendado)

1. Acesse a planilha template: `[Criar link do seu template]`
2. Clique em **Arquivo → Fazer uma cópia**
3. Renomeie: `[Nome do Cliente] - Keywords SEO`
4. Mova para sua pasta de clientes no Google Drive

### Opção B: Criar do Zero

1. Acesse [Google Sheets](https://sheets.google.com)
2. Crie nova planilha
3. Configure conforme a estrutura abaixo

---

## 📋 Estrutura da Planilha

### Headers (Linha 1)

| A | B | C |
|---|---|---|
| **Keyword** | **Status** | **Link** |

### Descrição das Colunas

| Coluna | Nome | Descrição | Preenchido por |
|--------|------|-----------|----------------|
| A | **Keyword** | Palavra-chave para gerar artigo | 👤 Cliente |
| B | **Status** | Status do artigo (ver tabela abaixo) | 🤖 Sistema |
| C | **Link** | URL do artigo publicado | 🤖 Sistema |

### Valores de Status

| Status | Significado | Preenchido por |
|--------|-------------|----------------|
| *(vazio)* | Aguardando processamento | 👤 Cliente deixa vazio |
| `Pending` | Cliente adicionou, aguardando | 👤 Cliente (opcional) |
| `Done` | Artigo publicado | 🤖 Sistema |
| `Error` | Falha na geração | 🤖 Sistema |
| `💡 Sugestão IA` | Sugestão gerada pela IA | 🤖 Sistema |

### Exemplo de Preenchimento

| Keyword | Status | Link |
|---------|--------|------|
| como tratar ansiedade | | | ← Cliente adiciona
| sintomas de depressão | Pending | | ← Aguardando
| hipnoterapia funciona | Done | https://site.com/... | ← Publicado
| técnicas de relaxamento | 💡 Sugestão IA | | ← Sugerido pela IA

---

## 🎨 Formatação da Planilha

### Opção A: Script Automático (Recomendado) ⭐

Execute este comando após compartilhar a planilha com o service account:

```bash
source venv/bin/activate
python format_spreadsheet.py SPREADSHEET_ID
```

**Exemplo:**
```bash
python format_spreadsheet.py 1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4
```

O script aplicará automaticamente:
- ✅ Header azul escuro + texto branco
- ✅ Formatação condicional completa
- ✅ Largura de colunas otimizada
- ✅ Header congelado

### Opção B: Formatação Manual

#### Cores dos Headers
- **Linha 1:** Fundo azul escuro (#1a365d), texto branco, negrito

#### Formatação Condicional (Status)
1. Selecione a coluna B (Status)
2. Clique em **Formatar → Formatação Condicional**
3. Adicione regras:

| Regra | Condição | Cor de Fundo |
|-------|----------|--------------|
| 1 | Texto é exatamente "Pending" | 🟡 Amarelo (#fef3c7) |
| 2 | Texto é exatamente "Done" | 🟢 Verde (#d1fae5) |
| 3 | Texto é exatamente "Error" | 🔴 Vermelho (#fee2e2) |
| 4 | Texto contém "Sugestão IA" | 💜 Roxo (#e6ccff) |

#### Largura das Colunas
- Coluna A (Keyword): 350px
- Coluna B (Status): 120px
- Coluna C (Link): 400px

---

## 🔗 PASSO 2: Compartilhar com o Sistema

### Obter o Email do Service Account

O email está em `config/service_account.json`, campo `client_email`.

Exemplo: `seo-automation@projeto-12345.iam.gserviceaccount.com`

### Compartilhar a Planilha

1. Abra a planilha do cliente
2. Clique em **Compartilhar** (canto superior direito)
3. Adicione o email do service account
4. Permissão: **Editor**
5. Desmarque "Notificar pessoas"
6. Clique em **Compartilhar**

---

## 📝 PASSO 3: Obter Spreadsheet ID

O ID está na URL da planilha:

```
https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
```

**Exemplo:**
```
URL: https://docs.google.com/spreadsheets/d/1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4/edit
ID:  1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4
```

---

## ⚙️ PASSO 4: Configurar no Sistema

### Usar Script Interativo (Recomendado)

```bash
cd "Fábrica de Artigos SEO"
source venv/bin/activate
python add_company.py
```

### Ou Editar Manualmente

Abra `config/sites.json` e adicione:

```json
{
  "site_name": "Nome do Cliente",
  "company_id": "nome_cliente",
  "spreadsheet_id": "COLE_O_ID_AQUI",
  "wordpress_url": "https://site-do-cliente.com",
  "persona_prompt": "Especialista em [ÁREA DO CLIENTE]",
  "wordpress_username": "usuario_wp",
  "wordpress_app_password": "xxxx xxxx xxxx xxxx"
}
```

---

## 🌐 PASSO 5: Configurar WordPress do Cliente

### Obter Senha de Aplicativo

1. Acesse o WordPress do cliente
2. Vá em **Usuários → Perfil**
3. Role até **Senhas de Aplicativo**
4. Nome: `SEO Automation`
5. Clique em **Adicionar Nova Senha**
6. **COPIE A SENHA** (só aparece uma vez!)
7. Use no campo `wordpress_app_password`

### Verificar Autenticação

```bash
python -c "
from core.wordpress_client import WordPressClient
wp = WordPressClient('https://site-cliente.com', 'usuario', 'senha')
print('✅ OK' if wp.verify_auth() else '❌ Falhou')
"
```

---

## 📚 PASSO 6: Knowledge Base (Opcional)

Se o cliente tem metodologia proprietária:

1. Crie pasta: `config/companies/{company_id}/knowledge_base/`
2. Adicione arquivos `.txt` com "premium" no nome
3. Exemplo: `metodologia_premium.txt`

Se não tem metodologia própria:
- Deixe a pasta vazia
- Sistema usará conhecimento geral da IA

---

## 🚀 PASSO 7: Executar

### Para TODOS os clientes

```bash
source venv/bin/activate
python main.py
```

### Apenas testar um cliente

```bash
# Temporariamente comente outros clientes no sites.json
python main.py
```

---

## 📧 Template de Email para o Cliente

```
Assunto: Acesso à Planilha de Keywords SEO

Olá [Nome do Cliente],

Preparei sua planilha de keywords para o serviço de geração de artigos SEO.

📊 ACESSE SUA PLANILHA:
[Cole o link da planilha aqui]

📝 COMO USAR:

1. Abra a planilha
2. Na coluna "Keyword", adicione as palavras-chave que deseja transformar em artigos
3. Deixe a coluna "Status" como "Pending"
4. Deixe a coluna "Link" vazia

Exemplo:
- como tratar ansiedade
- sintomas de estresse
- técnicas de relaxamento

🚀 O QUE ACONTECE DEPOIS:

1. Eu proceso suas keywords
2. Artigos são gerados e publicados automaticamente
3. O "Status" muda para "Done"
4. O "Link" é preenchido com a URL do artigo

💡 DICAS:

- Use palavras-chave específicas (long tail)
- Adicione quantas quiser
- Novos artigos são processados regularmente

Qualquer dúvida, estou à disposição!

Atenciosamente,
[Seu Nome]
```

---

## ✅ Checklist de Onboarding

```
□ Criar planilha para o cliente
□ Configurar headers e formatação
□ Compartilhar com service account
□ Copiar spreadsheet_id
□ Obter credenciais WordPress do cliente
□ Adicionar ao sites.json (ou usar add_company.py)
□ Criar pasta knowledge_base (se aplicável)
□ Testar conexão com Sheets
□ Testar autenticação WordPress
□ Enviar email de acesso para o cliente
□ Processar primeiro artigo de teste
```

---

## 🔧 Troubleshooting

### "Error accessing sheets"
- Verifique se compartilhou com o service account
- Confirme permissão de Editor
- Verifique se o spreadsheet_id está correto

### "WordPress authentication failed"
- Gere nova senha de aplicativo
- Verifique username (case sensitive)
- Confirme que API REST está ativa

### "No pending keywords"
- Verifique se a coluna Status tem "Pending"
- Confirme que está na primeira aba
- Verifique se os headers estão corretos

---

**Versão:** 1.0  
**Data:** 2026-02-01  
**Autor:** Sistema Fábrica de Artigos SEO
