# Epic E5 — Rate Limiter

**PRD:** prd-escalabilidade-v2.md
**Status:** Ready
**Owner:** @dev (Dex)
**Priority:** P1 — Paralelo
**FRs:** FR13, FR14, FR15
**Dependências:** Nenhuma (paralelo com E1)

---

## Objetivo

Implementar rate limiting inteligente para evitar que múltiplos tenants esgotem quotas da API do Gemini e outras APIs externas.

---

## Stories

### E5.S1 — Implementar RateLimiter

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev

**Descrição:**
Criar rate limiter baseado em sliding window que controla RPM (requests per minute).

**Acceptance Criteria:**
- [ ] Classe `RateLimiter` com parâmetro `rpm` (default: 15 para Gemini free tier)
- [ ] Sliding window algorithm: mantém deque de timestamps
- [ ] Método `wait_if_needed()` — bloqueia se necessário, retorna tempo de espera
- [ ] Método `acquire()` — registra nova requisição
- [ ] Thread-safe (usando Lock)
- [ ] Suporta múltiplas instâncias (uma por pool de API keys)
- [ ] Testes unitários cobrindo: under limit, at limit, over limit

**Files:**
- `core/rate_limiter.py` (create)
- `tests/test_rate_limiter.py` (create)

---

### E5.S2 — Integrar RateLimiter no LLMClient

**Status:** [ ] Ready
**Esforço:** ~1h
**Agente:** @dev
**Depende de:** E5.S1

**Descrição:**
Integrar rate limiter no `LLMClient` para que todas as chamadas ao Gemini respeitem o limite.

**Acceptance Criteria:**
- [ ] `LLMClient.__init__()` recebe `rate_limiter` (opcional)
- [ ] Toda chamada `generate()` chama `rate_limiter.wait_if_needed()` antes
- [ ] Se tenant tem API keys próprias, usa rate limiter separado
- [ ] Se usa pool global, compartilha rate limiter entre todos
- [ ] Log quando rate limiter ativa espera: `"Rate limit: waiting {n}s"`
- [ ] Métricas: total waits, total wait time
- [ ] Testes com mock de time

**Files:**
- `core/llm_client.py` (modify)
- `tests/test_rate_limiter.py` (modify)

---
