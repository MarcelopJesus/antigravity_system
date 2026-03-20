# 🚀 Plano de Execução — Escalabilidade v2.0

**PRD:** `docs/prd/prd-escalabilidade-v2.md`
**Data:** 2026-03-20
**Status:** Ready for Development

---

## Visão Geral

| Total | Valor |
|-------|-------|
| Épicos | 8 |
| Stories | 24 |
| Caminho Crítico | E1 → E2 → E6 → E7 |
| Paralelo | E3, E4, E5 (independentes) |
| Final | E8 (depende de E1 + E2) |

---

## Ordem de Execução (Waves)

### 🌊 Wave 1 — Fundação (Paralelo)
*Sem dependências entre si*

| Story | Epic | Descrição | Esforço |
|-------|------|-----------|---------|
| E1.S1 | Tenant Config | Estrutura de diretórios + schema | ~2h |
| E3.S1 | Pipeline | AgentStep com retry universal | ~2h |
| E4.S1 | KB Cache | KnowledgeBaseCache | ~2h |
| E5.S1 | Rate Limiter | RateLimiter sliding window | ~2h |

### 🌊 Wave 2 — Core (Depende de Wave 1)

| Story | Epic | Descrição | Esforço | Depende de |
|-------|------|-----------|---------|------------|
| E1.S2 | Tenant Config | TenantConfig loader | ~3h | E1.S1 |
| E3.S2 | Pipeline | Integrar AgentStep no Pipeline | ~2h | E3.S1 |
| E4.S2 | KB Cache | Integrar cache nos agentes | ~1h | E4.S1 |
| E5.S2 | Rate Limiter | Integrar no LLMClient | ~1h | E5.S1 |
| E3.S3 | Pipeline | Circuit Breaker | ~2h | — |

### 🌊 Wave 3 — Migração + Templates (Depende de Wave 2)

| Story | Epic | Descrição | Esforço | Depende de |
|-------|------|-----------|---------|------------|
| E1.S3 | Tenant Config | Migrar sites.json → tenant.yaml | ~2h | E1.S2 |
| E2.S1 | Prompts | Extrair prompts para Jinja2 | ~3h | E1.S2 |

### 🌊 Wave 4 — Integração (Depende de Wave 3)

| Story | Epic | Descrição | Esforço | Depende de |
|-------|------|-----------|---------|------------|
| E1.S4 | Tenant Config | Adaptar main.py | ~3h | E1.S3 |
| E2.S2 | Prompts | PromptEngine com herança | ~3h | E2.S1 |

### 🌊 Wave 5 — Prompts nos Agentes (Depende de Wave 4)

| Story | Epic | Descrição | Esforço | Depende de |
|-------|------|-----------|---------|------------|
| E2.S3 | Prompts | Integrar PromptEngine nos agentes | ~2h | E2.S2 |

### 🌊 Wave 6 — Sistema de Filas (Depende de Wave 4)

| Story | Epic | Descrição | Esforço | Depende de |
|-------|------|-----------|---------|------------|
| E6.S1 | Filas | Setup Redis + rq | ~1h | E1.S4 |
| E6.S2 | Filas | Job de geração de artigo | ~3h | E6.S1 |
| E6.S3 | Filas | Enqueue + Worker | ~2h | E6.S2 |
| E6.S4 | Filas | Adaptar main.py modo fila | ~2h | E6.S3 |

### 🌊 Wave 7 — Scheduler + Deploy (Depende de Wave 6)

| Story | Epic | Descrição | Esforço | Depende de |
|-------|------|-----------|---------|------------|
| E7.S1 | Scheduler | Implementar Scheduler | ~3h | E6.S4 |
| E7.S2 | Deploy | Config Supervisor + Cron | ~2h | E7.S1 |
| E7.S3 | Deploy | Health Check + Monitoring | ~2h | E7.S1 |

### 🌊 Wave 8 — Onboarding + Docs (Depende de Wave 5)

| Story | Epic | Descrição | Esforço | Depende de |
|-------|------|-----------|---------|------------|
| E8.S1 | Onboarding | add_tenant CLI | ~3h | E1.S4, E2.S3 |
| E8.S2 | Onboarding | Script migração completa | ~2h | E8.S1 |
| E8.S3 | Onboarding | Documentação | ~1h | E8.S2 |

---

## Checklist de Progresso

### Wave 1 — Fundação
- [ ] E1.S1 — Estrutura de diretórios + schema
- [ ] E3.S1 — AgentStep com retry
- [ ] E4.S1 — KnowledgeBaseCache
- [ ] E5.S1 — RateLimiter

### Wave 2 — Core
- [ ] E1.S2 — TenantConfig loader
- [ ] E3.S2 — AgentStep no Pipeline
- [ ] E4.S2 — Cache nos agentes
- [ ] E5.S2 — RateLimiter no LLMClient
- [ ] E3.S3 — Circuit Breaker

### Wave 3 — Migração + Templates
- [ ] E1.S3 — Migrar sites.json
- [ ] E2.S1 — Prompts → Jinja2

### Wave 4 — Integração
- [ ] E1.S4 — main.py com TenantConfig
- [ ] E2.S2 — PromptEngine

### Wave 5 — Prompts nos Agentes
- [ ] E2.S3 — PromptEngine nos agentes

### Wave 6 — Sistema de Filas
- [ ] E6.S1 — Redis + rq setup
- [ ] E6.S2 — Article job
- [ ] E6.S3 — Enqueue + Worker
- [ ] E6.S4 — main.py modo fila

### Wave 7 — Scheduler + Deploy
- [ ] E7.S1 — Scheduler
- [ ] E7.S2 — Config deploy
- [ ] E7.S3 — Health check

### Wave 8 — Onboarding + Docs
- [ ] E8.S1 — add_tenant CLI
- [ ] E8.S2 — Script migração
- [ ] E8.S3 — Documentação

---

## Notas para Execução em Modo YOLO

1. **Testes:** Rodar `pytest tests/` após cada Wave para garantir regressão zero
2. **Backward compatibility:** Manter `sites.json` funcionando até Wave 8 (migração)
3. **Commits:** Um commit por story completada (`feat: E{n}.S{n} — {descrição}`)
4. **Branches:** Pode trabalhar direto na `main` ou criar `feat/escalabilidade-v2`
5. **Se algo falhar:** Não pular — resolver o problema antes de avançar

---

*Morgan, planejando o futuro 📊*
