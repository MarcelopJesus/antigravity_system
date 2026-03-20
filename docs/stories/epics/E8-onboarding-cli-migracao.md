# Epic E8 — Onboarding CLI + Migração

**PRD:** prd-escalabilidade-v2.md
**Status:** Ready
**Owner:** @dev (Dex)
**Priority:** P1 — Após E1 e E2
**FRs:** FR19, FR20
**Dependências:** E1 (Tenant Config), E2 (Prompts Template)

---

## Objetivo

Criar CLI interativa para onboarding de novos tenants em ~5 minutos, e script de migração para tenants existentes.

---

## Stories

### E8.S1 — Refatorar add_company.py → add_tenant CLI

**Status:** [ ] Ready
**Esforço:** ~3h
**Agente:** @dev

**Descrição:**
Refatorar `add_company.py` existente para criar tenants no novo formato `config/tenants/`.

**Acceptance Criteria:**
- [ ] CLI interativa `python add_tenant.py` que pergunta:
  1. Company ID (slug)
  2. Site name
  3. WordPress URL
  4. Env prefix para credenciais
  5. Google Spreadsheet ID
  6. CTA tipo (whatsapp/email/phone/link)
  7. CTA URL e texto
  8. Persona (nome, título, expertise)
  9. Agentes habilitados (checkboxes)
  10. Schedule (frequency, times)
- [ ] Cria estrutura completa:
  ```
  config/tenants/{id}/
  ├── tenant.yaml
  ├── knowledge_base/    (vazio, com .gitkeep)
  ├── prompts/           (vazio = usa _default)
  └── images/            (vazio)
  ```
- [ ] Adiciona variáveis ao `.env` (com valores placeholder)
- [ ] Valida WordPress auth: testa GET /wp-json/wp/v2/users/me
- [ ] Valida Sheets access: testa read da spreadsheet
- [ ] Modo `--non-interactive` com JSON de input para automação
- [ ] Output: resumo do tenant criado + próximos passos

**Files:**
- `add_tenant.py` (create — substitui add_company.py)
- `tests/test_add_tenant.py` (create)

---

### E8.S2 — Script de migração completa

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev

**Descrição:**
Script que migra TUDO do formato antigo para o novo: sites.json, companies/, prompts hardcoded.

**Acceptance Criteria:**
- [ ] `scripts/migrate_v2.py` que:
  1. Lê `config/sites.json`
  2. Para cada entry, cria `config/tenants/{id}/tenant.yaml`
  3. Move `config/companies/{id}/knowledge_base/` → `config/tenants/{id}/knowledge_base/`
  4. Extrai CTA de `config/prompts.py` → `tenant.yaml`
  5. Cria backup: `config/sites.json.bak`, `config/prompts.py.bak`
  6. Valida migração: carrega todos os tenants com `TenantConfig`
- [ ] Modo `--dry-run` que mostra o que seria feito sem executar
- [ ] Modo `--rollback` que restaura backups
- [ ] Report de migração: tenants migrados, warnings, erros
- [ ] Idempotente: pode rodar múltiplas vezes sem duplicar

**Files:**
- `scripts/migrate_v2.py` (create)

---

### E8.S3 — Documentação de Onboarding

**Status:** [ ] Ready
**Esforço:** ~1h
**Agente:** @dev

**Descrição:**
Atualizar documentação de onboarding para refletir o novo processo.

**Acceptance Criteria:**
- [ ] `GUIA_ONBOARDING_CLIENTES.md` atualizado com novo processo (add_tenant.py)
- [ ] `MULTI_TENANT_GUIDE.md` atualizado com nova estrutura de diretórios
- [ ] `README.md` atualizado com comandos novos (scheduler, worker, queue)
- [ ] Seção "Migração v1 → v2" documentada
- [ ] Exemplos de `tenant.yaml` completo para referência

**Files:**
- `GUIA_ONBOARDING_CLIENTES.md` (modify)
- `MULTI_TENANT_GUIDE.md` (modify)
- `README.md` (modify)

---
