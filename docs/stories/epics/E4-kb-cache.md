# Epic E4 — KB Cache + Otimização

**PRD:** prd-escalabilidade-v2.md
**Status:** Ready
**Owner:** @dev (Dex)
**Priority:** P1 — Paralelo
**FRs:** FR17
**Dependências:** Nenhuma (paralelo com E1)

---

## Objetivo

Eliminar carregamento redundante da Knowledge Base (atualmente 4x por keyword) implementando cache em memória com TTL.

---

## Stories

### E4.S1 — Implementar KnowledgeBaseCache

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev

**Descrição:**
Criar sistema de cache para KB que evita recarregamento a cada chamada de agente.

**Acceptance Criteria:**
- [ ] Classe `KnowledgeBaseCache` com cache em memória (dict)
- [ ] Chave de cache: `{tenant_id}:{filter_key}` (ex: `mjesus:tri_essencia`)
- [ ] TTL configurável (default: 3600s / 1 hora)
- [ ] Método `get(tenant_id, kb_filter)` — retorna do cache ou carrega
- [ ] Método `invalidate(tenant_id)` — limpa cache de um tenant
- [ ] Método `clear()` — limpa todo o cache
- [ ] Métricas: cache hits, misses, evictions
- [ ] Testes unitários cobrindo: hit, miss, TTL expiration, invalidation

**Files:**
- `core/kb_cache.py` (create)
- `tests/test_kb_cache.py` (create)

---

### E4.S2 — Integrar cache nos agentes e pipeline

**Status:** [ ] Ready
**Esforço:** ~1h
**Agente:** @dev
**Depende de:** E4.S1

**Descrição:**
Substituir chamadas diretas à `KnowledgeBase.load()` pelo `KnowledgeBaseCache`.

**Acceptance Criteria:**
- [ ] Pipeline cria uma instância de `KnowledgeBaseCache` por execução
- [ ] Agentes recebem `kb_cache` em vez de `knowledge_base` diretamente
- [ ] `BaseAgent._get_kb_content()` usa cache
- [ ] KB carregada 1x por tenant por hora (não 4x por keyword)
- [ ] Log de cache stats ao final do pipeline (hits/misses)
- [ ] Testes existentes continuam passando

**Files:**
- `core/agents/base.py` (modify)
- `core/pipeline.py` (modify)
- `core/knowledge_base.py` (modify)

---
