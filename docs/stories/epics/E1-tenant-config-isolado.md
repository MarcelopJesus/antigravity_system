# Epic E1 — Tenant Config Isolado

**PRD:** prd-escalabilidade-v2.md
**Status:** Ready
**Owner:** @dev (Dex)
**Priority:** P0 — Critical Path
**FRs:** FR1, FR3, FR4
**Dependências:** Nenhuma (primeiro do caminho crítico)

---

## Objetivo

Migrar de `sites.json` monolítico para estrutura isolada `config/tenants/{id}/tenant.yaml`, permitindo configuração independente por tenant incluindo CTA, persona, agentes habilitados e schedule.

---

## Stories

### E1.S1 — Criar estrutura de diretórios e schema do tenant.yaml

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev

**Descrição:**
Criar a estrutura de diretórios `config/tenants/_default/` e `config/tenants/{company_id}/` com o schema do `tenant.yaml`.

**Acceptance Criteria:**
- [ ] Diretório `config/tenants/_default/` criado com prompts base
- [ ] Diretório `config/tenants/_default/prompts/` com arquivos: `analyst.txt`, `writer.txt`, `humanizer.txt`, `editor.txt`
- [ ] Schema `tenant.yaml` documentado com todos os campos (site, credentials, CTA, persona, agents, schedule, seo)
- [ ] Arquivo `config/tenants/_default/tenant.yaml` como template de referência
- [ ] Campos obrigatórios vs opcionais claramente definidos

**Files:**
- `config/tenants/_default/tenant.yaml` (create)
- `config/tenants/_default/prompts/analyst.txt` (create)
- `config/tenants/_default/prompts/writer.txt` (create)
- `config/tenants/_default/prompts/humanizer.txt` (create)
- `config/tenants/_default/prompts/editor.txt` (create)

---

### E1.S2 — Implementar TenantConfig loader

**Status:** [ ] Ready
**Esforço:** ~3h
**Agente:** @dev

**Descrição:**
Criar módulo `core/tenant_config.py` que carrega e valida `tenant.yaml`, com fallback para valores default.

**Acceptance Criteria:**
- [ ] Classe `TenantConfig` com método `load(company_id)` que retorna config completa
- [ ] Validação de campos obrigatórios (company_id, wordpress_url, spreadsheet_id, credentials_env_prefix)
- [ ] Merge automático com `_default/tenant.yaml` para campos não especificados
- [ ] Método `get_enabled_agents()` retorna lista de agentes habilitados
- [ ] Método `get_cta()` retorna CTA configurada (nunca hardcoded)
- [ ] Método `get_schedule()` retorna configuração de agendamento
- [ ] Testes unitários cobrindo: load, validação, merge, fallback

**Files:**
- `core/tenant_config.py` (create)
- `tests/test_tenant_config.py` (create)

---

### E1.S3 — Migrar sites.json para tenant.yaml

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev
**Depende de:** E1.S1, E1.S2

**Descrição:**
Criar script de migração que converte entries de `sites.json` para `tenant.yaml` individuais, e mover KB existente.

**Acceptance Criteria:**
- [ ] Script `scripts/migrate_to_tenants.py` criado
- [ ] Migra cada entry de sites.json para `config/tenants/{company_id}/tenant.yaml`
- [ ] Move `config/companies/{id}/knowledge_base/` para `config/tenants/{id}/knowledge_base/`
- [ ] Move `config/companies/{id}/images/` para `config/tenants/{id}/images/`
- [ ] Gera CTA a partir de dados existentes (extrai do prompts.py se possível)
- [ ] Valida migração (diff antes/depois)
- [ ] Backup de sites.json antes de migrar

**Files:**
- `scripts/migrate_to_tenants.py` (create)

---

### E1.S4 — Adaptar main.py para usar TenantConfig

**Status:** [ ] Ready
**Esforço:** ~3h
**Agente:** @dev
**Depende de:** E1.S2, E1.S3

**Descrição:**
Refatorar `main.py` para usar `TenantConfig` em vez de ler diretamente do `sites.json`. Manter backward compatibility.

**Acceptance Criteria:**
- [ ] `main.py` usa `TenantConfig.load(company_id)` para cada tenant
- [ ] `TenantConfig.list_all()` descobre todos os tenants em `config/tenants/`
- [ ] Pipeline recebe `tenant_config` em vez de `site_config` dict
- [ ] CTA vem do `tenant_config.get_cta()`, não do prompts.py
- [ ] Agentes habilitados vêm do `tenant_config.get_enabled_agents()`
- [ ] Backward compatibility: se `config/tenants/` não existe, fallback para `sites.json`
- [ ] Todos os testes existentes continuam passando

**Files:**
- `main.py` (modify)
- `core/pipeline.py` (modify)
- `config/settings.py` (modify)

---
