# 🏭 Fábrica de Artigos SEO - Sistema Multi-Tenant

Sistema automatizado de geração de artigos SEO com IA Gemini, suportando **múltiplas empresas/clientes** com configurações independentes.

## ✨ Recursos

- 🤖 **Geração de Artigos com IA Gemini** (5 agentes especializados)
- 🏢 **Multi-Tenant**: Gerencie múltiplas empresas/clientes
- 📚 **Knowledge Base Opcional**: Metodologias proprietárias por empresa
- 🎨 **Geração de Imagens**: Imagen 4.0 integrado
- 📊 **Google Sheets**: Gerenciamento de keywords e status
- 🌐 **WordPress**: Publicação automática com Yoast SEO
- 🔗 **Link Building Inteligente**: Linkagem interna automática

## 🚀 Setup Rápido

### 1. Clone e Instale

```bash
git clone <repository_url>
cd "Fábrica de Artigos SEO"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credenciais

**Google Gemini API:**
```bash
cp .env.example .env
# Edite .env e adicione suas chaves API (separadas por vírgula)
```

**Google Sheets Service Account:**
- Coloque `service_account.json` em `config/`
- [Como criar Service Account](https://cloud.google.com/iam/docs/service-accounts-create)

### 3. Configure sua Primeira Empresa

**Opção A - Script Interativo (Recomendado):**
```bash
python add_company.py
```

**Opção B - Manual:**
```bash
cp config/sites.json.example config/sites.json
# Edite config/sites.json com suas informações
```

## 🏢 Sistema Multi-Tenant

### Adicionar Nova Empresa

```bash
python add_company.py
```

O script irá:
1. ✅ Criar estrutura de pastas
2. ✅ Adicionar configuração ao `sites.json`
3. ✅ Criar pasta de knowledge base

### Estrutura por Empresa

```
config/companies/
├── mjesus/                    # Empresa 1
│   └── knowledge_base/
│       └── TRI Premium.txt    # Base de conhecimento TRI
├── empresa2/                  # Empresa 2
│   └── knowledge_base/        # (vazia = usa IA geral)
```

**Documentação completa:** [MULTI_TENANT_GUIDE.md](MULTI_TENANT_GUIDE.md)

## 📊 Configurar Planilha Google Sheets

Crie uma planilha com esta estrutura:

| Keyword | Status | Link |
|---------|--------|------|
| palavra-chave 1 | Pending | |
| palavra-chave 2 | Pending | |

1. Compartilhe com o email do service account
2. Dê permissão de **Editor**
3. Copie o ID da planilha da URL

## 🌐 Configurar WordPress

1. Acesse **Usuários → Perfil**
2. Role até **Senhas de Aplicativo**
3. Crie nova senha: "SEO Automation"
4. Use no `sites.json`

## 🎯 Executar

```bash
source venv/bin/activate
python main.py
```

O sistema irá:
1. ✅ Processar todas as empresas do `sites.json`
2. ✅ Carregar knowledge base específica (se existir)
3. ✅ Gerar artigos para keywords pendentes
4. ✅ Criar 3 imagens por artigo (Imagen 4.0)
5. ✅ Publicar no WordPress com Yoast SEO
6. ✅ Atualizar planilha com link do artigo
7. ✅ Sugerir novos tópicos relacionados

## 📚 Knowledge Base (Opcional)

Adicione arquivos `.txt` em `config/companies/SUA_EMPRESA/knowledge_base/`:

- ✅ Use "premium" no nome: `metodologia_premium.txt`
- ✅ Mantenha < 100KB para evitar limite de tokens
- ⚠️ Se não adicionar, sistema usa conhecimento geral da IA

## 🔒 Segurança

Arquivos sensíveis no `.gitignore`:
- `.env` (API keys)
- `config/service_account.json`
- `config/sites.json`

## 📖 Documentação Adicional

- [Guia Multi-Tenant Completo](MULTI_TENANT_GUIDE.md)
- [Exemplo de sites.json](config/sites.json.example)

## 🛠️ Troubleshooting

**Erro de autenticação Google Sheets:**
- Verifique se compartilhou a planilha com o service account
- Confirme permissão de Editor

**Erro de autenticação WordPress:**
- Gere nova senha de aplicativo
- Verifique se API REST está ativa

**Knowledge base não carrega:**
- Isso é normal se a pasta estiver vazia
- Sistema usará conhecimento geral da IA

---

**Versão:** 2.0 Multi-Tenant  
**Criado por:** Antigravity AI Assistant
