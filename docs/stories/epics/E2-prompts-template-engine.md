# Epic E2 — Prompts com Template Engine (Jinja2)

**PRD:** prd-escalabilidade-v2.md
**Status:** Ready
**Owner:** @dev (Dex)
**Priority:** P0 — Critical Path
**FRs:** FR2, FR4
**Dependências:** E1 (Tenant Config)

---

## Objetivo

Substituir prompts hardcoded em `config/prompts.py` por templates Jinja2 com herança, permitindo que cada tenant customize CTA, persona, tom de voz e conteúdo sem alterar código.

---

## Stories

### E2.S1 — Extrair prompts para templates Jinja2

**Status:** [ ] Ready
**Esforço:** ~3h
**Agente:** @dev

**Descrição:**
Extrair os 6 prompts de `config/prompts.py` para arquivos template em `config/tenants/_default/prompts/`, usando sintaxe Jinja2 para variáveis dinâmicas.

**Acceptance Criteria:**
- [ ] Cada prompt extraído para arquivo `.txt` com placeholders Jinja2:
  - `{{ persona.name }}`, `{{ persona.title }}`, `{{ persona.expertise }}`
  - `{{ cta.url }}`, `{{ cta.text }}`, `{{ cta.box_text }}`
  - `{{ knowledge_base }}`, `{{ keyword }}`, `{{ outline }}`
- [ ] `TRI_PRINCIPLES` extraído para `config/tenants/_default/prompts/tri_principles.txt` (incluído via `{% include %}` quando necessário)
- [ ] Prompts originais preservados em `config/prompts.py.bak` como referência
- [ ] Variáveis de CTA hardcoded (WhatsApp URL, nome) removidas dos templates default

**Files:**
- `config/tenants/_default/prompts/analyst.txt` (modify)
- `config/tenants/_default/prompts/writer.txt` (modify)
- `config/tenants/_default/prompts/humanizer.txt` (modify)
- `config/tenants/_default/prompts/editor.txt` (modify)
- `config/tenants/_default/prompts/visual.txt` (create)
- `config/tenants/_default/prompts/growth.txt` (create)
- `config/tenants/_default/prompts/tri_principles.txt` (create)

---

### E2.S2 — Implementar PromptEngine com herança

**Status:** [ ] Ready
**Esforço:** ~3h
**Agente:** @dev
**Depende de:** E2.S1

**Descrição:**
Criar `core/prompt_engine.py` que renderiza templates Jinja2 com contexto do tenant, suportando herança (_default → tenant override).

**Acceptance Criteria:**
- [ ] Classe `PromptEngine` com método `render(agent_name, context)` que retorna prompt final
- [ ] Busca template em `config/tenants/{id}/prompts/` primeiro, fallback para `_default/prompts/`
- [ ] Suporta `overrides.yaml` que define substituições parciais por agente
- [ ] Contexto inclui: `tenant_config`, `keyword`, `outline`, `knowledge_base`, `content`
- [ ] Jinja2 `{% include %}` funcional para composição de prompts
- [ ] Testes unitários: renderização, herança, override, fallback

**Files:**
- `core/prompt_engine.py` (create)
- `tests/test_prompt_engine.py` (create)

---

### E2.S3 — Integrar PromptEngine nos agentes

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev
**Depende de:** E2.S2

**Descrição:**
Refatorar agentes para usar `PromptEngine` em vez de importar prompts diretamente de `config/prompts.py`.

**Acceptance Criteria:**
- [ ] `BaseAgent.__init__()` recebe `prompt_engine` (ou `tenant_config`)
- [ ] `_build_prompt()` em cada agente usa `self.prompt_engine.render(self.agent_name, context)`
- [ ] Removida dependência direta de `config/prompts.py` em todos os agentes
- [ ] `config/prompts.py` mantido como fallback (deprecated) — warning no log se usado
- [ ] Todos os testes existentes continuam passando
- [ ] Teste de integração: gerar artigo com prompt customizado por tenant

**Files:**
- `core/agents/base.py` (modify)
- `core/agents/analyst.py` (modify)
- `core/agents/writer.py` (modify)
- `core/agents/humanizer.py` (modify)
- `core/agents/editor.py` (modify)
- `core/agents/visual.py` (modify)
- `core/agents/growth.py` (modify)
- `core/pipeline.py` (modify)

---
