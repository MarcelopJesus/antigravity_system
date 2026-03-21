# ROADMAP — Fabrica de Artigos SEO: Evolucao Completa

> Documento mestre de evolucao do projeto. Cada fase contem tarefas executaveis.
> Marque [x] conforme concluir. Use `@dev` para implementar cada tarefa.
>
> Criado em: 2026-03-20 | Autor: Atlas (Analyst Agent)
> Referencia: Analise completa do projeto (pipeline, SEO, agentes, integracao)

---

## Visao Geral

```
FASE 1: Correcoes Criticas (bugs e falhas que prejudicam SEO hoje)
FASE 2: SEO Scorer v2 (scoring inteligente baseado em dados reais)
FASE 3: Inteligencia Competitiva (SERP analysis, content gaps)
FASE 4: Topic Clusters & Autoridade Topica
FASE 5: Monitoramento & Feedback Loop (GSC, Analytics, Dashboard)
FASE 6: Otimizacao Avancada (E-E-A-T, Featured Snippets, A/B Testing)
FASE 7: Escala (Auto Keyword Discovery, Multi-language, Multi-tenant)
```

**Estimativa total:** ~45 tarefas across 7 fases
**Prioridade:** Fase 1 primeiro (impacto imediato), demais sequenciais

---

## FASE 1 — Correcoes Criticas

> Bugs e falhas que prejudicam o SEO HOJE. Resolver antes de qualquer feature nova.

### 1.1 Schema Markup nao chega ao WordPress
- [ ] **Problema:** `inject_schema_into_html()` e um no-op. WordPress strip `<script>` tags do conteudo. O schema JSON-LD gerado (Article, LocalBusiness, FAQ) NUNCA e publicado.
- [ ] **Solucao:** Implementar injecao via Yoast REST API ou custom fields do WordPress
- [ ] **Arquivos:** `core/seo/schema.py`, `core/wordpress_client.py`
- [ ] **Validacao:** Publicar artigo → inspecionar fonte HTML no browser → confirmar `<script type="application/ld+json">` presente
- [ ] **Teste:** Usar Google Rich Results Test (https://search.google.com/test/rich-results) para validar schema

### 1.2 Alt Text nas Imagens (SEO basico faltando)
- [ ] **Problema:** Visual Agent gera imagens e faz upload, mas nao seta alt text programaticamente. Cada `<img>` no artigo fica sem alt — penalidade direta no SEO.
- [ ] **Solucao:** Gerar alt text descritivo com keyword no Visual Agent e setar via WP REST API no upload
- [ ] **Arquivos:** `core/agents/visual.py`, `core/wordpress_client.py`
- [ ] **Regra:** Alt text = keyword principal + descricao contextual (max 125 chars)
- [ ] **Teste:** Verificar `alt=` em todas as `<img>` tags do artigo publicado

### 1.3 Duplicacao Visual no Tema WordPress
- [ ] **Problema:** Tema WP do mjesus.com.br mostra titulo + excerpt ANTES do conteudo, criando duplicacao visual. Excerpt ja usa meta_description, mas tema pode ter template customizado.
- [ ] **Investigacao:**
  - [ ] Acessar mjesus.com.br → inspecionar single post template
  - [ ] Verificar se tema tem `single.php` com excerpt hardcoded
  - [ ] Testar: publicar artigo sem excerpt → ver se duplicacao some
- [ ] **Solucao:** Ajustar tema OU enviar excerpt vazio OU usar CSS `display:none` no excerpt do tema

### 1.4 IMG_PLACEHOLDER restante no HTML publicado
- [ ] **Problema:** Se geracao de imagem falha, `<!-- IMG_PLACEHOLDER -->` fica no HTML publicado. Nao e visivel mas e lixo no codigo.
- [ ] **Solucao:** Editor Agent ou pipeline post-step deve limpar todos os placeholders antes de publicar
- [ ] **Arquivos:** `core/pipeline.py` (step final), `core/agents/editor.py`
- [ ] **Teste:** Simular falha de imagem → verificar que HTML publicado nao tem placeholder

### 1.5 Meta Description fora do range
- [ ] **Problema:** SEO Scorer da 0 pontos se meta_description tem 156 chars (1 char acima de 155). Artigo `ansiedade-generalizada` perdeu 10 pontos por 1 caractere.
- [ ] **Solucao A:** Analyst prompt deve enforcar limite de 150 chars (margem de seguranca)
- [ ] **Solucao B:** SEO Scorer usar pontuacao parcial (ex: 156-165 chars = 5 pts em vez de 0)
- [ ] **Arquivos:** `core/agents/seo_scorer.py`, `config/tenants/_default/prompts/analyst.txt`

---

## FASE 2 — SEO Scorer v2

> Transformar o scorer de "checklist basico" para "analise inteligente".

### 2.1 Readability Score (NLP para PT-BR)
- [ ] Implementar Flesch-Kincaid adaptado para portugues brasileiro
- [ ] Metricas: comprimento medio de sentenca, silabas por palavra, indice de legibilidade
- [ ] Target: Nivel "facil" (equivalente a 8a serie) para artigos de blog
- [ ] **Arquivos:** Novo `core/seo/readability.py`, integrar em `seo_scorer.py`
- [ ] **Peso:** 10 pontos no score total

### 2.2 Semantic Coverage Score
- [ ] Medir quantos LSI keywords sugeridos pelo Analyst foram usados no artigo
- [ ] Formula: (LSI usados / LSI sugeridos) × 100
- [ ] **Arquivos:** `core/agents/seo_scorer.py`
- [ ] **Peso:** 10 pontos no score total

### 2.3 Entity Coverage Check
- [ ] Extrair entidades mencionadas no artigo (pessoas, lugares, conceitos)
- [ ] Comparar com entidades esperadas para o topico (via Gemini)
- [ ] **Arquivos:** Novo `core/seo/entity_checker.py`
- [ ] **Peso:** 5 pontos no score total

### 2.4 URL/Slug Optimization Check
- [ ] Verificar que slug contem keyword principal
- [ ] Verificar comprimento do slug (max 60 chars, sem stop words)
- [ ] **Arquivos:** `core/agents/seo_scorer.py`, `core/dry_run.py` (slugify)
- [ ] **Peso:** 5 pontos no score total

### 2.5 Outbound Links Check
- [ ] Verificar presenca de 1-2 links para fontes autoritativas externas
- [ ] Google valoriza artigos que citam fontes confiaveis (PubMed, Wikipedia, .gov)
- [ ] **Arquivos:** `core/agents/seo_scorer.py`, prompt do Writer
- [ ] **Peso:** 5 pontos no score total

### 2.6 Recalibrar Pesos do Score
- [ ] Score total atual: 100 pontos (10 checks)
- [ ] Novo score total: 100 pontos (15 checks) — recalibrar pesos
- [ ] Manter gate minimo em 40, mas subir recomendacao para 70+
- [ ] **Arquivos:** `core/agents/seo_scorer.py`
- [ ] **Testes:** Atualizar todos os testes de scoring

---

## FASE 3 — Inteligencia Competitiva

> Parar de "voar cego" — saber o que o Google quer ANTES de escrever.

### 3.1 SERP Analyzer Agent (NOVO)
- [ ] Criar novo agente `core/agents/serp_analyzer.py`
- [ ] Integrar com API de SERP (opcoes: SerpAPI, DataForSEO, ou ValueSERP)
- [ ] Para cada keyword, antes do Analyst:
  - [ ] Buscar top 10 resultados no Google
  - [ ] Extrair: titulos, meta descriptions, word count estimado, headings
  - [ ] Identificar: featured snippets, "People Also Ask", entidades
- [ ] Output: `serp_brief.json` com dados estruturados
- [ ] Analyst recebe serp_brief como input adicional
- [ ] **Prompt template:** Novo `config/tenants/_default/prompts/serp_analyzer.txt`
- [ ] **Pipeline:** Inserir como Step 0 (antes do Analyst)
- [ ] **Config:** API key no .env (`SERP_API_KEY`)

### 3.2 People Also Ask Integration
- [ ] Extrair perguntas do "People Also Ask" do Google para cada keyword
- [ ] Injetar no prompt do Analyst para incluir no outline (FAQ section)
- [ ] Resultado: FAQ do artigo responde perguntas REAIS que as pessoas fazem
- [ ] **Arquivos:** `core/agents/serp_analyzer.py`, `config/tenants/_default/prompts/analyst.txt`

### 3.3 Content Gap Analyzer
- [ ] Novo modulo `core/seo/content_gap.py`
- [ ] Compara artigos publicados (via Sheets) vs keywords que concorrentes rankeiam
- [ ] Identifica oportunidades de keywords nao cobertas
- [ ] Output: lista priorizada por volume estimado × dificuldade
- [ ] Integra com planilha (adiciona keywords com tag "Gap Analysis")
- [ ] **Dependencia:** SERP API (mesma da 3.1)

### 3.4 Content Length Intelligence
- [ ] Analisar word count medio dos top 10 para cada keyword
- [ ] Ajustar meta de palavras do Writer: top10_media × 1.2 (20% mais)
- [ ] Resultado: artigos SEMPRE mais completos que a concorrencia
- [ ] **Arquivos:** `core/agents/serp_analyzer.py`, `core/pipeline.py` (passar meta ao Writer)

---

## FASE 4 — Topic Clusters & Autoridade Topica

> Estrategia que posiciona SITES INTEIROS na 1a pagina, nao so artigos isolados.

### 4.1 Topic Cluster Engine
- [ ] Novo modulo `core/seo/topic_clusters.py`
- [ ] Estrutura:
  ```
  Pillar Page (3000+ palavras, keyword principal broad)
  ├── Cluster Article 1 (1500+ palavras, long-tail)
  ├── Cluster Article 2
  ├── Cluster Article 3
  └── Cluster Article 4
  ```
- [ ] Cada cluster article linka para o Pillar e vice-versa
- [ ] Cluster articles linkam entre si
- [ ] **Dados:** Novo campo no tenant.yaml: `topic_clusters[]`

### 4.2 Pillar Page Generator
- [ ] Adaptar pipeline para gerar Pillar Pages (formato diferente)
- [ ] Pillar = artigo longo (3000-5000 palavras), cobre topico broad
- [ ] Inclui links para TODOS os artigos do cluster
- [ ] Table of Contents automatico
- [ ] **Prompt template:** Novo `pillar_writer.txt`

### 4.3 Cluster Map Automation
- [ ] Growth Agent evolui: em vez de 2 sugestoes genericas, gera mapa de cluster
- [ ] Input: keyword do Pillar → Output: 8-12 keywords de cluster
- [ ] Insere todas na planilha com tag "Cluster: [Pillar Name]"
- [ ] Ordem de publicacao estrategica (cluster articles primeiro, pillar por ultimo)
- [ ] **Arquivos:** `core/agents/growth.py` (refactor completo)

### 4.4 Internal Links por Cluster
- [ ] Refatorar `core/seo/internal_links.py` para ser cluster-aware
- [ ] Links dentro do cluster tem prioridade sobre links gerais
- [ ] Pillar page recebe links de TODOS os artigos do cluster
- [ ] **Metricas:** Rastrear "link equity" por cluster

---

## FASE 5 — Monitoramento & Feedback Loop

> Saber se os artigos estao funcionando e melhorar continuamente.

### 5.1 Google Search Console Integration
- [ ] Novo modulo `core/integrations/gsc_client.py`
- [ ] Autenticar via service account (mesma do Sheets)
- [ ] Metricas por artigo: posicao media, impressoes, clicks, CTR
- [ ] Detectar artigos na pagina 2 (posicoes 11-20) = oportunidade de otimizacao
- [ ] **Config:** `GSC_PROPERTY_URL` no .env

### 5.2 Content Freshness Engine
- [ ] Novo modulo `core/reoptimizer_v2.py` (evolucao do reoptimizer.py existente)
- [ ] Detecta artigos com queda de posicao (via GSC, comparando periodos)
- [ ] Re-otimiza: atualiza dados, adiciona secoes, refresh de exemplos
- [ ] Atualiza `dateModified` no schema
- [ ] Re-publica com "Atualizado em {data}"
- [ ] **Trigger:** Automatico via scheduler ou manual via `--reoptimize-v2`

### 5.3 Performance Dashboard
- [ ] Novo modulo `core/dashboard/` (pode ser CLI ou HTML simples)
- [ ] Metricas:
  - [ ] Artigos publicados (total, por mes, por tenant)
  - [ ] Posicao media no Google por keyword
  - [ ] CTR por artigo
  - [ ] Custo por artigo (API calls Gemini)
  - [ ] Score SEO medio
  - [ ] Top 5 artigos por performance
  - [ ] Artigos que precisam de re-otimizacao
- [ ] Output: JSON + HTML (opcional, abre no browser)
- [ ] **Comando:** `python dashboard.py --tenant mjesus`

### 5.4 Conversion Tracking (WhatsApp CTA)
- [ ] Implementar UTM parameters nos links de WhatsApp CTA
- [ ] Formato: `https://wa.me/...?text=Vim+do+artigo+{slug}`
- [ ] Permite rastrear qual artigo gerou qual lead
- [ ] **Arquivos:** `core/pipeline.py` (CTA generation), prompt do Writer

---

## FASE 6 — Otimizacao Avancada

> Features que separam artigos "bons" de artigos que DOMINAM a SERP.

### 6.1 E-E-A-T Enhancer
- [ ] Novo modulo `core/seo/eeat.py`
- [ ] Injetar sinais de autoridade:
  - [ ] Citacoes de estudos reais (PubMed, Google Scholar via API)
  - [ ] "Reviewed by" badge com credenciais do autor
  - [ ] Structured data de Author (schema.org/Person) com sameAs links
  - [ ] Dados estatisticos verificaveis com fonte
- [ ] **Prompt update:** Writer deve incluir pelo menos 2 citacoes de fontes reais
- [ ] **Schema:** Adicionar `author` com `sameAs: [linkedin, lattes]` no Article schema

### 6.2 Featured Snippet Optimizer
- [ ] Novo modulo `core/seo/featured_snippets.py`
- [ ] Detecta oportunidades de snippet (via SERP data)
- [ ] Formata secoes para capturar Position Zero:
  - [ ] Paragraph snippet: resposta direta em 40-60 palavras
  - [ ] List snippet: listas numeradas/com bullets
  - [ ] Table snippet: tabelas comparativas
- [ ] **Prompt update:** Analyst marca secoes com `snippet_type` no outline
- [ ] **Writer update:** Formata secao marcada no formato ideal para snippet

### 6.3 A/B Testing de Titulos e Meta Descriptions
- [ ] Novo modulo `core/seo/ab_testing.py`
- [ ] Para cada artigo, Analyst gera 3 variacoes de titulo + 3 de meta
- [ ] Publica com variacao A
- [ ] Apos 2 semanas (via scheduler), analisa CTR via GSC
- [ ] Se CTR < benchmark, atualiza para variacao B via WP REST API
- [ ] Registra resultados para learning
- [ ] **Dependencia:** GSC integration (5.1)

### 6.4 Semantic Entity Mapping
- [ ] Novo modulo `core/seo/entity_mapping.py`
- [ ] Consulta Google Knowledge Graph API para entidades do topico
- [ ] Garante que artigo menciona entidades esperadas
- [ ] Resultado: Google entende melhor sobre O QUE e o artigo
- [ ] **Config:** `KNOWLEDGE_GRAPH_API_KEY` no .env

---

## FASE 7 — Escala

> Transformar de "ferramenta" em "plataforma".

### 7.1 Auto Keyword Discovery
- [ ] Novo modulo `core/keyword_discovery/`
- [ ] Fontes:
  - [ ] Google Suggest API (autocomplete)
  - [ ] People Also Ask (do SERP Analyzer)
  - [ ] Google Trends API (trending topics)
  - [ ] Expansao semantica via Gemini
- [ ] Classificacao por volume estimado × dificuldade
- [ ] Insercao automatica na planilha com prioridade e tag
- [ ] **Comando:** `python main.py --discover-keywords --tenant mjesus`

### 7.2 Multi-Tenant Dashboard
- [ ] Dashboard unificado para todos os tenants
- [ ] Comparacao de performance entre tenants
- [ ] Metricas agregadas (total artigos, media score, total impressoes)
- [ ] **Dependencia:** Dashboard (5.3) + GSC (5.1)

### 7.3 Multi-Language Support
- [ ] Suporte a artigos em PT-BR, ES, EN
- [ ] hreflang tags automaticas no schema
- [ ] Adaptar CTA por regiao/idioma
- [ ] Prompts traduzidos por idioma
- [ ] **Config:** `tenant.yaml → languages: [pt-br, en, es]`

### 7.4 WordPress Theme Integration Guide
- [ ] Documentar requisitos do tema WP para funcionar com a Fabrica
- [ ] Template de single.php recomendado
- [ ] CSS para CTA box, FAQ accordion, author box
- [ ] Plugin recomendados (Yoast, WP Fastest Cache, etc.)

### 7.5 API Mode (SaaS Ready)
- [ ] Expor pipeline como API REST (FastAPI)
- [ ] Endpoints: POST /generate, GET /status, GET /articles
- [ ] Autenticacao por tenant (API key)
- [ ] Webhook para notificacao de conclusao
- [ ] **Estrutura:** Novo `api/` directory

---

## Registro de Progresso

| Fase | Total Tarefas | Concluidas | Status |
|------|---------------|------------|--------|
| 1. Correcoes Criticas | 5 | 5 | Concluido |
| 2. SEO Scorer v2 | 6 | 6 | Concluido |
| 3. Inteligencia Competitiva | 4 | 4 | Concluido |
| 4. Topic Clusters | 4 | 4 | Concluido |
| 5. Monitoramento | 4 | 4 | Concluido |
| 6. Otimizacao Avancada | 4 | 4 | Concluido |
| 7. Escala | 5 | 5 | Concluido |
| **TOTAL** | **32 blocos** | **32** | **100%** |

---

## Como Usar Este Documento

1. **Abra uma sessao Claude Code**
2. **Ative o dev:** `@dev`
3. **Diga:** "Implementar tarefa 1.1 do ROADMAP-SEO-EVOLUTION.md"
4. **O dev le a tarefa, implementa, roda testes, marca [x]**
5. **Repita** para a proxima tarefa

**Regras:**
- Fases sao sequenciais (1 antes de 2, etc.)
- Tarefas DENTRO de uma fase podem ser paralelas (exceto dependencias explicitas)
- Sempre rodar `pytest tests/` antes de marcar como concluida
- Zero regressao nos 263 testes existentes

---

*Documento gerado por Atlas (Analyst Agent) — 2026-03-20*
*Baseado em analise completa do codebase, pipeline, SEO, e integracao WordPress*
