# Epic E3 — Pipeline Resiliente (Retry por Agente)

**PRD:** prd-escalabilidade-v2.md
**Status:** Ready
**Owner:** @dev (Dex)
**Priority:** P1 — Paralelo
**FRs:** FR16, FR17, FR18
**Dependências:** Nenhuma (paralelo com E1)

---

## Objetivo

Adicionar retry com backoff exponencial em TODOS os agentes do pipeline, não apenas no Analyst. Implementar circuit breaker e métricas por execução.

---

## Stories

### E3.S1 — Implementar AgentStep com retry universal

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev

**Descrição:**
Criar wrapper `AgentStep` que envolve qualquer agente com retry configurável, backoff exponencial e logging estruturado.

**Acceptance Criteria:**
- [ ] Classe `AgentStep` com parâmetros: `agent`, `max_retries=3`, `backoff_base=2`, `backoff_max=30`
- [ ] Método `execute(input_data)` com retry e backoff exponencial: `delay = min(base * 2^attempt, max)`
- [ ] Log estruturado por tentativa: `agent_name`, `attempt`, `delay`, `error`
- [ ] Exceções não-retriáveis (ValidationError) falham imediatamente
- [ ] Timeout configurável por step (default: 120s)
- [ ] Testes unitários cobrindo: retry success, retry exhaustion, non-retriable errors

**Files:**
- `core/agent_step.py` (create)
- `tests/test_agent_step.py` (create)

---

### E3.S2 — Integrar AgentStep no Pipeline

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev
**Depende de:** E3.S1

**Descrição:**
Refatorar `pipeline.py` para usar `AgentStep` em vez de chamar agentes diretamente.

**Acceptance Criteria:**
- [ ] Pipeline instancia `AgentStep(agent, config)` para cada agente
- [ ] Config de retry pode vir do `tenant.yaml` (override por tenant/agente)
- [ ] Métricas por step coletadas: `duration_ms`, `attempts`, `success`, `tokens_used`
- [ ] Pipeline reporta métricas completas ao final: `pipeline_metrics` dict
- [ ] Se agente opcional falha após retry (Visual, Growth), pipeline continua com warning
- [ ] Agentes obrigatórios (Analyst, Writer, Editor) falham o pipeline após retry exausto

**Files:**
- `core/pipeline.py` (modify)

---

### E3.S3 — Circuit Breaker por API

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev

**Descrição:**
Implementar circuit breaker no `LLMClient` para evitar requisições a APIs que estão consistentemente falhando.

**Acceptance Criteria:**
- [ ] Classe `CircuitBreaker` com estados: CLOSED (normal), OPEN (bloqueado), HALF_OPEN (testando)
- [ ] Abre após N falhas consecutivas (default: 5)
- [ ] Fecha após tempo de cooldown (default: 60s)
- [ ] Half-open permite 1 requisição de teste
- [ ] Aplicado no `LLMClient` e `WordPressClient`
- [ ] Log quando circuit abre/fecha
- [ ] Testes unitários cobrindo todos os estados

**Files:**
- `core/circuit_breaker.py` (create)
- `core/llm_client.py` (modify)
- `core/wordpress_client.py` (modify)
- `tests/test_circuit_breaker.py` (create)

---
