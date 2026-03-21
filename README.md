# Fabrica de Artigos SEO

Sistema automatizado de geracao de artigos SEO com IA, multi-tenant, que gera artigos otimizados e publica diretamente no WordPress.

## Stack

- **Python 3.12+**
- **Google Gemini** (geracao de texto e imagens via Imagen 4.0)
- **WordPress REST API** + Yoast SEO
- **Google Sheets** (keywords, status, sugestoes)
- **SerperAPI** (inteligencia competitiva SERP)
- **Google Search Console** (monitoramento de performance)
- **Redis + rq** (modo assincrono opcional)
- **FastAPI** (modo API REST opcional)

## Pipeline de Agentes

```
Keyword
  |
  v
[SERP Analyzer] → Dados competitivos dos top 10 do Google
  |
  v
[Analyst] → Outline JSON (titulo, secoes, FAQ, LSI keywords, entities)
  |
  v
[Writer] → Artigo HTML (1800-3000 palavras)
  |
  v
[Humanizer] → Opcional (voz do profissional)
  |
  v
[Editor] → Polish, correcao HTML
  |
  v
[SEO Scorer] → 15 checks, 100 pontos (gate minimo: 40)
  |
  v
[Schema Markup] → Article + LocalBusiness + FAQ (JSON-LD via meta field)
  |
  v
[Internal Links] → Cluster-aware, prioridade por topic cluster
  |
  v
[Visual Agent] → 2-3 imagens por artigo (Imagen 4.0, alt text SEO)
  |
  v
[WordPress] → Publicacao automatica com Yoast SEO
  |
  v
[Growth Agent] → Cluster map com 6-8 keywords sugeridas
```

## Setup

### 1. Instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar credenciais

```bash
cp .env.example .env
```

Edite `.env` com:
```
GOOGLE_API_KEYS=key1,key2
SERPER_API_KEY=sua_chave_serper
GSC_PROPERTY_URL=https://seusite.com.br
```

Coloque `config/service_account.json` (Google Sheets + GSC).

### 3. Configurar tenant

```bash
python add_tenant.py
```

Ou manualmente em `config/tenants/seu_tenant/tenant.yaml`.

## Comandos

```bash
# Producao: processa keywords da planilha e publica
python main.py

# Dry-run: salva em output/ sem publicar
python main.py --dry-run

# Keywords de arquivo
python main.py --keywords keywords.json --dry-run

# Tenant especifico
python main.py --tenant mjesus

# Modo fila (Redis)
python main.py --queue

# Descoberta de keywords
python main.py --discover-keywords "ansiedade" --tenant mjesus

# Re-otimizar artigos existentes
python main.py --reoptimize

# Dashboard de performance
python dashboard.py --tenant mjesus
python dashboard.py --tenant mjesus --json report.json
python dashboard.py --tenant mjesus --freshness

# API REST (requer: pip install fastapi uvicorn)
uvicorn api.app:app --reload
```

## Estrutura do Projeto

```
core/
  agents/
    analyst.py          # Outline estrategico (JSON)
    writer.py           # Redacao HTML
    humanizer.py        # Voz do profissional (opcional)
    editor.py           # Polish e correcao
    visual.py           # Geracao de imagens (Imagen 4.0)
    growth.py           # Cluster map e sugestoes
    seo_scorer.py       # 15 checks, 100 pontos
    serp_analyzer.py    # SerperAPI (top 10 Google)
  seo/
    schema.py           # JSON-LD (Article, LocalBusiness, FAQ)
    internal_links.py   # Linkagem interna cluster-aware
    readability.py      # Flesch-Kincaid PT-BR
    topic_clusters.py   # Pillar/cluster relationships + TOC
    content_gap.py      # Lacunas de conteudo vs SERP
    entity_checker.py   # Cobertura de entidades
    eeat.py             # E-E-A-T (author schema, badges)
    featured_snippets.py # Otimizacao para Position Zero
    ab_testing.py       # A/B de titulos e metas
    entity_mapping.py   # Knowledge Graph API
    multilang.py        # hreflang, multi-idioma
  integrations/
    gsc_client.py       # Google Search Console
  dashboard/
    dashboard.py        # Dashboard CLI + JSON
    multi_tenant.py     # Dashboard multi-tenant
  keyword_discovery/
    discovery.py        # Auto keyword discovery
  pipeline.py           # Orquestracao dos agentes
  wordpress_client.py   # WordPress REST API
  sheets_client.py      # Google Sheets API
  tenant_config.py      # Config por tenant
  prompt_engine.py      # Templates Jinja2
  llm_client.py         # Gemini com rate limiter + circuit breaker
  reoptimizer.py        # Re-otimizacao v1
  reoptimizer_v2.py     # Content freshness engine

config/
  tenants/
    _default/            # Template base (heranca)
      tenant.yaml
      prompts/           # analyst.txt, writer.txt, editor.txt, etc.
    mjesus/              # Tenant especifico
      tenant.yaml
      knowledge_base/

api/
  app.py                # FastAPI REST API

deploy/
  mu-seo-schema.php              # WordPress mu-plugin (schema JSON-LD)
  INSTRUCOES-WORDPRESS-SCHEMA.md # Guia de instalacao do mu-plugin
  WORDPRESS-THEME-GUIDE.md       # Requisitos do tema WP + CSS

tests/                   # 396 testes
```

## SEO Scorer v2 (15 checks, 100 pontos)

| # | Check | Peso |
|---|-------|------|
| 1 | Keyword no titulo | 12 |
| 2 | Keyword no 1o paragrafo | 8 |
| 3 | H1 unico | 8 |
| 4 | Hierarquia de headings | 7 |
| 5 | Meta description length | 8 |
| 6 | Keyword density | 10 |
| 7 | Links internos | 7 |
| 8 | Imagens | 5 |
| 9 | Word count (min 1000) | 7 |
| 10 | CTA presente | 3 |
| 11 | Readability (Flesch PT-BR) | 10 |
| 12 | Semantic coverage (LSI) | 5 |
| 13 | Entity coverage | 3 |
| 14 | Slug optimization | 5 |
| 15 | Outbound links | 2 |
| | **Total** | **100** |

Grades: A (70+), B (50+), C (40+), D (<40). Gate minimo: 40.

## Topic Clusters

Configure em `tenant.yaml`:

```yaml
topic_clusters:
  - name: Ansiedade
    pillar_keyword: ansiedade tratamento completo
    cluster_keywords:
      - ansiedade generalizada
      - crise de ansiedade
      - ansiedade noturna
      - ansiedade sintomas fisicos
```

O pipeline automaticamente:
- Prioriza links entre artigos do mesmo cluster
- Gera TOC para pillar pages
- Growth Agent sugere keywords de cluster

## Testes

```bash
pytest tests/              # 396 testes
pytest tests/ -v           # Verbose
pytest tests/test_seo_scorer.py  # Modulo especifico
```

## Seguranca

Arquivos sensiveis no `.gitignore`:
- `.env` (API keys)
- `config/service_account.json`
- `config/sites.json`
- `output/`

## WordPress Setup

Para schema JSON-LD funcionar, instalar o mu-plugin:
1. Copiar `deploy/mu-seo-schema.php` para `wp-content/mu-plugins/`
2. Ver `deploy/INSTRUCOES-WORDPRESS-SCHEMA.md` para detalhes

Para CSS dos componentes (CTA, author badge, TOC):
- Ver `deploy/WORDPRESS-THEME-GUIDE.md`

---

**Versao:** 3.0
