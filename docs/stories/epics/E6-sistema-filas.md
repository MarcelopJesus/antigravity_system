# Epic E6 — Sistema de Filas (Redis + rq)

**PRD:** prd-escalabilidade-v2.md
**Status:** Ready
**Owner:** @dev (Dex)
**Priority:** P0 — Critical Path
**FRs:** FR5, FR6, FR7, FR8, FR9
**Dependências:** E1 (Tenant Config)

---

## Objetivo

Implementar sistema de filas com Redis + rq para processamento paralelo de artigos, substituindo o loop sequencial do `main.py`.

---

## Stories

### E6.S1 — Setup Redis + rq + dependências

**Status:** [ ] Ready
**Esforço:** ~1h
**Agente:** @dev

**Descrição:**
Adicionar Redis e rq como dependências, criar configuração de conexão.

**Acceptance Criteria:**
- [ ] `requirements.txt` atualizado com: `redis>=5.0.0`, `rq>=1.16.0`, `rq-dashboard>=0.7.0`
- [ ] Módulo `core/queue_config.py` criado com conexão Redis configurável
- [ ] Variáveis de ambiente: `REDIS_URL` (default: `redis://localhost:6379/0`)
- [ ] Fallback para processamento síncrono se Redis não disponível
- [ ] Health check: `queue_config.is_redis_available()` retorna bool
- [ ] `.env.example` atualizado com `REDIS_URL`

**Files:**
- `requirements.txt` (modify)
- `core/queue_config.py` (create)
- `.env.example` (modify)

---

### E6.S2 — Implementar job de geração de artigo

**Status:** [ ] Ready
**Esforço:** ~3h
**Agente:** @dev
**Depende de:** E6.S1

**Descrição:**
Criar função de job que processa uma keyword para um tenant, encapsulando o pipeline completo.

**Acceptance Criteria:**
- [ ] Função `jobs/article_job.py::process_article(tenant_id, keyword, priority='normal')`
- [ ] Carrega `TenantConfig` para o tenant
- [ ] Inicializa pipeline com config do tenant (agentes, prompts, KB)
- [ ] Executa pipeline: analyst → writer → humanizer → editor → visual → growth
- [ ] Publica no WordPress + atualiza Sheets
- [ ] Retorna dict de resultado: `{status, tenant_id, keyword, seo_score, duration_ms, url}`
- [ ] Em caso de erro, loga e retorna status `failed` com mensagem
- [ ] Job timeout configurável (default: 30 minutos)

**Files:**
- `jobs/__init__.py` (create)
- `jobs/article_job.py` (create)
- `tests/test_article_job.py` (create)

---

### E6.S3 — Implementar enqueue e worker

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev
**Depende de:** E6.S2

**Descrição:**
Criar lógica de enfileiramento e entry point do worker.

**Acceptance Criteria:**
- [ ] Módulo `core/queue_manager.py` com:
  - `enqueue_article(tenant_id, keyword, priority='normal')` — adiciona job à fila
  - `enqueue_tenant_batch(tenant_id, keywords, delay_between=10)` — enfileira com delay
  - `get_queue_stats()` — retorna: pending, started, failed, finished
- [ ] `worker.py` (entry point): `rq worker article-queue --with-scheduler`
- [ ] Suporta múltiplos workers (numprocs configurável)
- [ ] Jobs com prioridade: `high`, `normal`, `low` (filas separadas)
- [ ] Failed jobs vão para fila `failed` com info de erro
- [ ] Testes com mock de Redis

**Files:**
- `core/queue_manager.py` (create)
- `worker.py` (create)
- `tests/test_queue_manager.py` (create)

---

### E6.S4 — Adaptar main.py para modo fila

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev
**Depende de:** E6.S3

**Descrição:**
Refatorar `main.py` para suportar dois modos: `--queue` (enfileira) e `--sync` (legado).

**Acceptance Criteria:**
- [ ] `main.py --queue` — enfileira jobs para todos os tenants com keywords pendentes
- [ ] `main.py --sync` — comportamento atual (sequencial, sem Redis)
- [ ] `main.py` (sem flag) — auto-detecta: se Redis disponível, usa queue; senão, sync
- [ ] Flag `--tenant {id}` — processa apenas um tenant específico
- [ ] Flag `--workers {n}` — inicia N workers (default: 2)
- [ ] Output mostra: quantos jobs enfileirados, por tenant
- [ ] Testes de integração para ambos os modos

**Files:**
- `main.py` (modify)

---
