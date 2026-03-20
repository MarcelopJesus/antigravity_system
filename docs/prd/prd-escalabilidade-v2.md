# Fábrica de Artigos SEO — PRD: Escalabilidade Multi-Tenant v2.0

**Versão:** 2.0
**Data:** 2026-03-20
**Autor:** Morgan (PM) + Aria (Architect) + Atlas (Analyst)
**Status:** Approved — Ready for Development
**Predecessor:** prd-robustez-v1.md (Fase 1 — Implementada)

---

## 1. Goals

- Transformar o MVP funcional em plataforma escalável para 10-100+ tenants
- Isolar completamente cada tenant (config, prompts, KB, credenciais, agentes)
- Implementar sistema de filas com execução paralela e rate limiting
- Automatizar execução em VPS (2x/dia) sem intervenção humana
- Reduzir onboarding de novo tenant de ~45min manual para ~5min via CLI
- Tornar agentes configuráveis e opcionais por tenant

## 2. Background Context

O sistema "Fábrica de Artigos SEO" passou pela Fase 1 (Robustez) e Fase 8 (SEO Profissional + Segurança), estando funcional em produção para 1 cliente (mjesus.com.br). A análise arquitetural revelou 7 problemas estruturais que impedem escalabilidade:

1. **Single-threaded** — processamento sequencial bloqueia com múltiplos tenants
2. **CTA/Prompts hardcoded** — WhatsApp, nome e persona fixos em `config/prompts.py`
3. **KB inteira em memória** — carregada 4x por keyword sem cache
4. **API keys globais** — uma pool para todos os tenants
5. **Zero retry na maioria dos agentes** — só Analyst tem retry
6. **Sem scheduler** — não roda automaticamente
7. **Onboarding manual** — 9 passos complexos para adicionar empresa

### Métricas Atuais (baseline)

| Métrica | Valor Atual | Meta v2.0 |
|---------|-------------|-----------|
| Tenants suportados | 1-3 (funcional) | 50+ |
| Tempo por artigo | ~60s | ~60s (paralelo) |
| Onboarding tenant | ~45min manual | ~5min CLI |
| Execução automática | Nenhuma | 2x/dia |
| Retry por agente | Só Analyst (2x) | Todos (3x + backoff) |
| Cache de KB | Nenhum | Redis/memória com TTL |

### Change Log

| Data | Versão | Descrição | Autor |
|------|--------|-----------|-------|
| 2026-03-20 | 2.0 | Criação do PRD de Escalabilidade | Morgan |

---

## 3. Requirements

### 3.1 Functional Requirements

#### Tenant Isolation
- **FR1:** Cada tenant DEVE ter configuração isolada em `config/tenants/{company_id}/tenant.yaml` com: dados do site, credenciais (ref .env), CTA customizada, persona, agentes habilitados e schedule
- **FR2:** Prompts DEVEM suportar herança: template base em `config/tenants/_default/prompts/` com overrides por tenant via `overrides.yaml`
- **FR3:** Cada tenant DEVE poder habilitar/desabilitar agentes individualmente (ex: sem Visual, sem Humanizer)
- **FR4:** CTA DEVE ser configurável por tenant (tipo, URL, texto, estilo) — nunca hardcoded

#### Sistema de Filas
- **FR5:** O sistema DEVE usar Redis + rq (ou similar) para enfileirar jobs de geração de artigos
- **FR6:** Cada job na fila DEVE conter: tenant_id, keyword, prioridade, timestamp
- **FR7:** Workers DEVEM processar jobs em paralelo (configurável: 1-4 workers)
- **FR8:** Se um job falhar, DEVE ser re-enfileirado com backoff (max 3 tentativas)
- **FR9:** Dashboard de monitoramento da fila DEVE estar acessível (rq-dashboard)

#### Scheduler
- **FR10:** O sistema DEVE ter scheduler configurável por tenant (horários, frequência, timezone)
- **FR11:** Scheduler DEVE respeitar `max_articles_per_run` por tenant
- **FR12:** Scheduler DEVE ser executável via cron em VPS (2 entrypoints: scheduler.py, worker.py)

#### Rate Limiting
- **FR13:** Rate limiter DEVE controlar RPM (requests per minute) por pool de API keys
- **FR14:** Backoff exponencial DEVE ser aplicado quando rate limit é atingido
- **FR15:** Tenants PODEM ter pools de API keys separadas (configurável)

#### Pipeline Resiliente
- **FR16:** TODOS os agentes DEVEM ter retry configurável (default: 3x com backoff exponencial)
- **FR17:** KB DEVE ser carregada uma vez e cacheada durante toda a execução do pipeline para um tenant
- **FR18:** Pipeline DEVE reportar métricas por execução: duração, tokens usados, score SEO, status

#### Onboarding
- **FR19:** CLI `add_tenant` DEVE criar estrutura completa de tenant (diretórios, yaml, .env vars)
- **FR20:** CLI DEVE validar credenciais (WordPress auth, Sheets access) durante setup

### 3.2 Non-Functional Requirements

- **NFR1:** O sistema DEVE suportar 50+ tenants sem degradação significativa (< 2x tempo total)
- **NFR2:** Falha em tenant A NÃO DEVE afetar processamento de tenant B (isolamento de falhas)
- **NFR3:** Memory footprint por worker DEVE ser < 500MB com 50 tenants configurados
- **NFR4:** Redis DEVE ser a única dependência de infraestrutura adicional
- **NFR5:** O sistema DEVE rodar em VPS com 2 vCPU / 4GB RAM para 50 tenants
- **NFR6:** Todos os testes existentes DEVEM continuar passando (backward compatibility)
- **NFR7:** Migração de `sites.json` para `tenant.yaml` DEVE ser automatizada

### 3.3 Constraints

- **CON1:** Manter Python como linguagem principal (equipe existente)
- **CON2:** Manter compatibilidade com Google Gemini API como LLM primário
- **CON3:** Manter integração WordPress REST API + Yoast SEO
- **CON4:** Manter integração Google Sheets como fonte de keywords
- **CON5:** Budget de VPS: até $20-40/mês (Hetzner, DigitalOcean, etc.)

---

## 4. Technical Architecture (by @architect Aria)

### Stack Additions

| Componente | Tecnologia | Justificativa |
|------------|-----------|---------------|
| Queue | Redis + rq | Simples, Python-native, suficiente para escala |
| Cache | Redis (mesmo) | KB cache, rate limit state |
| Scheduler | APScheduler ou cron | Leve, sem overhead |
| Process Manager | Supervisor | Robusto, auto-restart |
| Monitoring | rq-dashboard | Web UI para filas |

### Tenant Config Structure

```
config/tenants/
├── _default/              # Template base (herança)
│   └── prompts/
│       ├── analyst.txt
│       ├── writer.txt
│       ├── humanizer.txt
│       └── editor.txt
├── mjesus/
│   ├── tenant.yaml        # Config completa
│   ├── prompts/
│   │   └── overrides.yaml # Só o que muda
│   ├── knowledge_base/
│   └── images/
└── clinica_xyz/
    ├── tenant.yaml
    └── knowledge_base/
```

---

## 5. Epic Breakdown

| Epic | Nome | Esforço | Dependência | Stories |
|------|------|---------|-------------|---------|
| E1 | Tenant Config Isolado | 2-3 dias | — | 4 stories |
| E2 | Prompts com Template Engine | 2 dias | E1 | 3 stories |
| E3 | Pipeline Resiliente | 1-2 dias | — | 3 stories |
| E4 | KB Cache + Otimização | 1 dia | — | 2 stories |
| E5 | Rate Limiter | 1 dia | — | 2 stories |
| E6 | Sistema de Filas | 2-3 dias | E1 | 4 stories |
| E7 | Scheduler + Deploy VPS | 1-2 dias | E6 | 3 stories |
| E8 | Onboarding CLI + Migração | 1 dia | E1, E2 | 3 stories |

**Caminho Crítico:** E1 → E2 → E6 → E7
**Paralelo:** E3 + E4 + E5 (independentes)

---

## 6. Success Metrics

| Métrica | Critério de Sucesso |
|---------|-------------------|
| Tenants ativos | >= 5 tenants rodando simultaneamente |
| Uptime | >= 99% em 30 dias |
| Onboarding | < 5 minutos para novo tenant |
| Falha isolada | 0 cascading failures em 30 dias |
| SEO Score médio | >= 70 (grade B+) |
| Artigos/dia | 2 por tenant, automáticos |

---

## 7. Risks & Mitigations

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Rate limit Gemini com muitos tenants | Alta | Alto | Pool de keys por tenant + backoff |
| Redis single point of failure | Média | Alto | Fallback para in-memory queue |
| VPS undersized | Média | Médio | Monitoramento + scale vertical |
| Migração quebra tenants existentes | Baixa | Alto | Script de migração + rollback |
| KB muito grande para cache | Baixa | Médio | TTL + LRU eviction |

---

*Morgan, planejando o futuro 📊*
