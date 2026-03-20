# Epic E7 — Scheduler + Deploy VPS

**PRD:** prd-escalabilidade-v2.md
**Status:** Ready
**Owner:** @dev (Dex) + @devops (Gage)
**Priority:** P0 — Critical Path
**FRs:** FR10, FR11, FR12
**Dependências:** E6 (Sistema de Filas)

---

## Objetivo

Implementar scheduler que dispara geração de artigos automaticamente (2x/dia por tenant), com deploy configurado para VPS usando Supervisor.

---

## Stories

### E7.S1 — Implementar Scheduler

**Status:** [ ] Ready
**Esforço:** ~3h
**Agente:** @dev

**Descrição:**
Criar `scheduler.py` que lê schedule de cada tenant e enfileira jobs nos horários configurados.

**Acceptance Criteria:**
- [ ] `scheduler.py` como entry point independente
- [ ] Lê `schedule` de cada `tenant.yaml`:
  ```yaml
  schedule:
    frequency: twice_daily  # daily, twice_daily, weekly
    times: ["09:00", "21:00"]
    timezone: "America/Sao_Paulo"
    max_articles_per_run: 1
  ```
- [ ] Para cada tenant, nos horários configurados:
  1. Conecta ao Google Sheets
  2. Busca keywords pendentes
  3. Enfileira `max_articles_per_run` jobs
- [ ] Respeita timezone por tenant
- [ ] Log de cada enfileiramento: `"Scheduled: {tenant_id} - {keyword} at {time}"`
- [ ] Modo `--once` para execução única (para uso com cron)
- [ ] Modo `--daemon` para execução contínua (APScheduler)
- [ ] Testes unitários com mock de time/timezone

**Files:**
- `scheduler.py` (create)
- `tests/test_scheduler.py` (create)

---

### E7.S2 — Configuração de Deploy (Supervisor + Cron)

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev

**Descrição:**
Criar arquivos de configuração para deploy em VPS com Supervisor e crontab.

**Acceptance Criteria:**
- [ ] `deploy/supervisor.conf` com:
  - `[program:article-worker]` — 2 workers rq (numprocs=2)
  - `[program:rq-dashboard]` — monitoring UI na porta 9181
- [ ] `deploy/crontab.txt` com schedule padrão:
  ```
  0 9 * * * cd /opt/article-factory && python scheduler.py --once
  0 21 * * * cd /opt/article-factory && python scheduler.py --once
  ```
- [ ] `deploy/setup.sh` — script de setup da VPS:
  - Instala Python 3.12, Redis, Supervisor
  - Cria virtualenv
  - Instala dependências
  - Configura supervisor
  - Configura crontab
- [ ] `deploy/.env.production.example` — template de env para produção
- [ ] README com instruções de deploy

**Files:**
- `deploy/supervisor.conf` (create)
- `deploy/crontab.txt` (create)
- `deploy/setup.sh` (create)
- `deploy/.env.production.example` (create)
- `deploy/README.md` (create)

---

### E7.S3 — Health Check e Monitoramento

**Status:** [ ] Ready
**Esforço:** ~2h
**Agente:** @dev

**Descrição:**
Implementar health check endpoint e sistema de alertas básico.

**Acceptance Criteria:**
- [ ] Script `health_check.py` que verifica:
  - Redis está acessível
  - Workers estão rodando (rq info)
  - Último job processado < 2h atrás
  - Nenhum tenant com > 3 falhas consecutivas
- [ ] Output JSON para integração com monitoring:
  ```json
  {
    "status": "healthy|degraded|critical",
    "redis": true,
    "workers_active": 2,
    "last_job_age_minutes": 45,
    "failed_tenants": []
  }
  ```
- [ ] Flag `--alert` envia notificação se status != healthy
- [ ] Crontab entry: a cada 30 min roda health check
- [ ] Testes unitários

**Files:**
- `health_check.py` (create)
- `tests/test_health_check.py` (create)

---
