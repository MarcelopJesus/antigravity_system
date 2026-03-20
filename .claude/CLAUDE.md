# Synkra AIOX Development Rules for Claude Code

You are working with Synkra AIOX, an AI-Orchestrated System for Full Stack Development.

<!-- AIOX-MANAGED-START: core-framework -->
## Core Framework Understanding

Synkra AIOX is a meta-framework that orchestrates AI agents to handle complex development workflows. Always recognize and work within this architecture.
<!-- AIOX-MANAGED-END: core-framework -->

<!-- AIOX-MANAGED-START: constitution -->
## Constitution

O AIOX possui uma **Constitution formal** com princípios inegociáveis e gates automáticos.

**Documento completo:** `.aiox-core/constitution.md`

**Princípios fundamentais:**

| Artigo | Princípio | Severidade |
|--------|-----------|------------|
| I | CLI First | NON-NEGOTIABLE |
| II | Agent Authority | NON-NEGOTIABLE |
| III | Story-Driven Development | MUST |
| IV | No Invention | MUST |
| V | Quality First | MUST |
| VI | Absolute Imports | SHOULD |

**Gates automáticos bloqueiam violações.** Consulte a Constitution para detalhes completos.
<!-- AIOX-MANAGED-END: constitution -->

<!-- AIOX-MANAGED-START: sistema-de-agentes -->
## Sistema de Agentes

### Ativação de Agentes
Use `@agent-name` ou `/AIOX:agents:agent-name`:

| Agente | Persona | Escopo Principal |
|--------|---------|------------------|
| `@dev` | Dex | Implementação de código |
| `@qa` | Quinn | Testes e qualidade |
| `@architect` | Aria | Arquitetura e design técnico |
| `@pm` | Morgan | Product Management |
| `@po` | Pax | Product Owner, stories/epics |
| `@sm` | River | Scrum Master |
| `@analyst` | Alex | Pesquisa e análise |
| `@data-engineer` | Dara | Database design |
| `@ux-design-expert` | Uma | UX/UI design |
| `@devops` | Gage | CI/CD, git push (EXCLUSIVO) |

### Comandos de Agentes
Use prefixo `*` para comandos:
- `*help` - Mostrar comandos disponíveis
- `*create-story` - Criar story de desenvolvimento
- `*task {name}` - Executar task específica
- `*exit` - Sair do modo agente
<!-- AIOX-MANAGED-END: sistema-de-agentes -->

<!-- AIOX-MANAGED-START: agent-system -->
## Agent System

### Agent Activation
- Agents are activated with @agent-name syntax: @dev, @qa, @architect, @pm, @po, @sm, @analyst
- The master agent is activated with @aiox-master
- Agent commands use the * prefix: *help, *create-story, *task, *exit

### Agent Context
When an agent is active:
- Follow that agent's specific persona and expertise
- Use the agent's designated workflow patterns
- Maintain the agent's perspective throughout the interaction
<!-- AIOX-MANAGED-END: agent-system -->

## Development Methodology

### Story-Driven Development
1. **Work from stories** - All development starts with a story in `docs/stories/`
2. **Update progress** - Mark checkboxes as tasks complete: [ ] → [x]
3. **Track changes** - Maintain the File List section in the story
4. **Follow criteria** - Implement exactly what the acceptance criteria specify

### Code Standards
- Write clean, self-documenting code
- Follow existing patterns in the codebase
- Include comprehensive error handling
- Add unit tests for all new functionality
- Use TypeScript/JavaScript best practices

### Testing Requirements
- Run all tests before marking tasks complete
- Ensure linting passes: `npm run lint`
- Verify type checking: `npm run typecheck`
- Add tests for new features
- Test edge cases and error scenarios

<!-- AIOX-MANAGED-START: framework-structure -->
## AIOX Framework Structure

```
aiox-core/
├── agents/         # Agent persona definitions (YAML/Markdown)
├── tasks/          # Executable task workflows
├── workflows/      # Multi-step workflow definitions
├── templates/      # Document and code templates
├── checklists/     # Validation and review checklists
└── rules/          # Framework rules and patterns

docs/
├── stories/        # Development stories (numbered)
├── prd/            # Product requirement documents
├── architecture/   # System architecture documentation
└── guides/         # User and developer guides
```
<!-- AIOX-MANAGED-END: framework-structure -->

<!-- AIOX-MANAGED-START: framework-boundary -->
## Framework vs Project Boundary

O AIOX usa um modelo de 4 camadas (L1-L4) para separar artefatos do framework e do projeto. Deny rules em `.claude/settings.json` reforçam isso deterministicamente.

| Camada | Mutabilidade | Paths | Notas |
|--------|-------------|-------|-------|
| **L1** Framework Core | NEVER modify | `.aiox-core/core/`, `.aiox-core/constitution.md`, `bin/aiox.js`, `bin/aiox-init.js` | Protegido por deny rules |
| **L2** Framework Templates | NEVER modify | `.aiox-core/development/tasks/`, `.aiox-core/development/templates/`, `.aiox-core/development/checklists/`, `.aiox-core/development/workflows/`, `.aiox-core/infrastructure/` | Extend-only |
| **L3** Project Config | Mutable (exceptions) | `.aiox-core/data/`, `agents/*/MEMORY.md`, `core-config.yaml` | Allow rules permitem |
| **L4** Project Runtime | ALWAYS modify | `docs/stories/`, `packages/`, `squads/`, `tests/` | Trabalho do projeto |

**Toggle:** `core-config.yaml` → `boundary.frameworkProtection: true/false` controla se deny rules são ativas (default: true para projetos, false para contribuidores do framework).

> **Referência formal:** `.claude/settings.json` (deny/allow rules), `.claude/rules/agent-authority.md`
<!-- AIOX-MANAGED-END: framework-boundary -->

<!-- AIOX-MANAGED-START: rules-system -->
## Rules System

O AIOX carrega regras contextuais de `.claude/rules/` automaticamente. Regras com frontmatter `paths:` só carregam quando arquivos correspondentes são editados.

| Rule File | Description |
|-----------|-------------|
| `agent-authority.md` | Agent delegation matrix and exclusive operations |
| `agent-handoff.md` | Agent switch compaction protocol for context optimization |
| `agent-memory-imports.md` | Agent memory lifecycle and CLAUDE.md ownership |
| `coderabbit-integration.md` | Automated code review integration rules |
| `ids-principles.md` | Incremental Development System principles |
| `mcp-usage.md` | MCP server usage rules and tool selection priority |
| `story-lifecycle.md` | Story status transitions and quality gates |
| `workflow-execution.md` | 4 primary workflows (SDC, QA Loop, Spec Pipeline, Brownfield) |

> **Diretório:** `.claude/rules/` — rules são carregadas automaticamente pelo Claude Code quando relevantes.
<!-- AIOX-MANAGED-END: rules-system -->

<!-- AIOX-MANAGED-START: code-intelligence -->
## Code Intelligence

O AIOX possui um sistema de code intelligence opcional que enriquece operações com dados de análise de código.

| Status | Descrição | Comportamento |
|--------|-----------|---------------|
| **Configured** | Provider ativo e funcional | Enrichment completo disponível |
| **Fallback** | Provider indisponível | Sistema opera normalmente sem enrichment — graceful degradation |
| **Disabled** | Nenhum provider configurado | Funcionalidade de code-intel ignorada silenciosamente |

**Graceful Fallback:** Code intelligence é sempre opcional. `isCodeIntelAvailable()` verifica disponibilidade antes de qualquer operação. Se indisponível, o sistema retorna o resultado base sem modificação — nunca falha.

**Diagnóstico:** `aiox doctor` inclui check de code-intel provider status.

> **Referência:** `.aiox-core/core/code-intel/` — provider interface, enricher, client
<!-- AIOX-MANAGED-END: code-intelligence -->

<!-- AIOX-MANAGED-START: graph-dashboard -->
## Graph Dashboard

O CLI `aiox graph` visualiza dependências, estatísticas de entidades e status de providers.

### Comandos

```bash
aiox graph --deps                        # Dependency tree (ASCII)
aiox graph --deps --format=json          # Output como JSON
aiox graph --deps --format=html          # Interactive HTML (abre browser)
aiox graph --deps --format=mermaid       # Mermaid diagram
aiox graph --deps --format=dot           # DOT format (Graphviz)
aiox graph --deps --watch                # Live mode com auto-refresh
aiox graph --deps --watch --interval=10  # Refresh a cada 10 segundos
aiox graph --stats                       # Entity stats e cache metrics
```

**Formatos de saída:** ascii (default), json, dot, mermaid, html

> **Referência:** `.aiox-core/core/graph-dashboard/` — CLI, renderers, data sources
<!-- AIOX-MANAGED-END: graph-dashboard -->

## Workflow Execution

### Task Execution Pattern
1. Read the complete task/workflow definition
2. Understand all elicitation points
3. Execute steps sequentially
4. Handle errors gracefully
5. Provide clear feedback

### Interactive Workflows
- Workflows with `elicit: true` require user input
- Present options clearly
- Validate user responses
- Provide helpful defaults

## Best Practices

### When implementing features:
- Check existing patterns first
- Reuse components and utilities
- Follow naming conventions
- Keep functions focused and testable
- Document complex logic

### When working with agents:
- Respect agent boundaries
- Use appropriate agent for each task
- Follow agent communication patterns
- Maintain agent context

### When handling errors:
```javascript
try {
  // Operation
} catch (error) {
  console.error(`Error in ${operation}:`, error);
  // Provide helpful error message
  throw new Error(`Failed to ${operation}: ${error.message}`);
}
```

## Git & GitHub Integration

### Commit Conventions
- Use conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, etc.
- Reference story ID: `feat: implement IDE detection [Story 2.1]`
- Keep commits atomic and focused

### GitHub CLI Usage
- Ensure authenticated: `gh auth status`
- Use for PR creation: `gh pr create`
- Check org access: `gh api user/memberships`

<!-- AIOX-MANAGED-START: aiox-patterns -->
## AIOX-Specific Patterns

### Working with Templates
```javascript
const template = await loadTemplate('template-name');
const rendered = await renderTemplate(template, context);
```

### Agent Command Handling
```javascript
if (command.startsWith('*')) {
  const agentCommand = command.substring(1);
  await executeAgentCommand(agentCommand, args);
}
```

### Story Updates
```javascript
// Update story progress
const story = await loadStory(storyId);
story.updateTask(taskId, { status: 'completed' });
await story.save();
```
<!-- AIOX-MANAGED-END: aiox-patterns -->

## Environment Setup

### Required Tools
- Node.js 18+
- GitHub CLI
- Git
- Your preferred package manager (npm/yarn/pnpm)

### Configuration Files
- `.aiox/config.yaml` - Framework configuration
- `.env` - Environment variables
- `aiox.config.js` - Project-specific settings

<!-- AIOX-MANAGED-START: common-commands -->
## Common Commands

### AIOX Master Commands
- `*help` - Show available commands
- `*create-story` - Create new story
- `*task {name}` - Execute specific task
- `*workflow {name}` - Run workflow

### Development Commands
- `npm run dev` - Start development
- `npm test` - Run tests
- `npm run lint` - Check code style
- `npm run build` - Build project
<!-- AIOX-MANAGED-END: common-commands -->

## Debugging

### Enable Debug Mode
```bash
export AIOX_DEBUG=true
```

### View Agent Logs
```bash
tail -f .aiox/logs/agent.log
```

### Trace Workflow Execution
```bash
npm run trace -- workflow-name
```

## Claude Code Specific Configuration

### Performance Optimization
- Prefer batched tool calls when possible for better performance
- Use parallel execution for independent operations
- Cache frequently accessed data in memory during sessions

### Tool Usage Guidelines
- Always use the Grep tool for searching, never `grep` or `rg` in bash
- Use the Task tool for complex multi-step operations
- Batch file reads/writes when processing multiple files
- Prefer editing existing files over creating new ones

### Session Management
- Track story progress throughout the session
- Update checkboxes immediately after completing tasks
- Maintain context of the current story being worked on
- Save important state before long-running operations

### Error Recovery
- Always provide recovery suggestions for failures
- Include error context in messages to user
- Suggest rollback procedures when appropriate
- Document any manual fixes required

### Testing Strategy
- Run tests incrementally during development
- Always verify lint and typecheck before marking complete
- Test edge cases for each new feature
- Document test scenarios in story files

### Documentation
- Update relevant docs when changing functionality
- Include code examples in documentation
- Keep README synchronized with actual behavior
- Document breaking changes prominently

---

## Fábrica de Artigos SEO — Contexto do Projeto

### O que é

Sistema de **geração automática de artigos SEO** com IA (Gemini), multi-tenant, que gera artigos otimizados e publica diretamente no WordPress. Cada tenant (cliente/site) tem configuração isolada: prompts, knowledge base, CTA, persona e agentes habilitados.

### Stack

- **Linguagem:** Python 3.12+
- **LLM:** Google Gemini (via `google-generativeai`, modelo configurável no .env)
- **CMS:** WordPress REST API + Yoast SEO
- **Planilha:** Google Sheets (keywords pendentes, status, sugestões)
- **Imagens:** Imagen 4.0 (Google)
- **Queue:** Redis + rq (opcional, para modo assíncrono)
- **Templates:** Jinja2 (prompts com herança por tenant)

### Estrutura de Diretórios

```
core/                    # Lógica central
├── agents/              # 6 agentes (analyst, writer, editor, visual, growth, humanizer)
├── pipeline.py          # Orquestração sequencial dos agentes
├── tenant_config.py     # Configuração isolada por tenant
├── prompt_engine.py     # Templates Jinja2 com herança
├── llm_client.py        # Cliente Gemini com rotação de keys + rate limiter + circuit breaker
├── kb_cache.py          # Cache de Knowledge Base com TTL
├── rate_limiter.py      # Sliding window rate limiter
├── circuit_breaker.py   # Circuit breaker para APIs
├── queue_config.py      # Conexão Redis
├── queue_manager.py     # Gerenciador de filas rq
├── wordpress_client.py  # WordPress REST API
├── sheets_client.py     # Google Sheets API
├── knowledge_base.py    # Carregamento de KB por tenant
└── seo/                 # SEO: internal links, schema markup

config/
├── tenants/             # Configuração por tenant (NOVA estrutura v2)
│   ├── _default/        # Template base (herança)
│   │   ├── tenant.yaml
│   │   └── prompts/     # analyst.txt, writer.txt, editor.txt, etc.
│   └── mjesus/          # Tenant específico
│       ├── tenant.yaml
│       ├── knowledge_base/
│       └── prompts/     # Overrides (vazio = usa _default)
├── sites.json           # Legacy (backward compatible)
├── prompts.py           # Legacy prompts hardcoded (fallback)
└── settings.py          # Carrega .env

jobs/                    # Jobs para fila Redis/rq
├── article_job.py       # Job de geração de artigo

deploy/                  # Deploy VPS
├── supervisor.conf
├── crontab.txt
└── setup.sh

tests/                   # 263 testes
```

### Pipeline de Agentes

```
Keyword → Analyst (outline JSON) → Writer (HTML) → [Humanizer opcional] → Editor (polish) → SEO Scorer → Schema Injection → Internal Links → Visual (imagens) → WordPress publish → Sheets update → Growth (sugestões)
```

### Comandos Principais

```bash
python main.py                          # Produção: processa keywords pendentes da planilha
python main.py --dry-run                # Teste: salva em output/ sem publicar
python main.py --keywords file.json     # Keywords de arquivo (produção ou dry-run)
python main.py --queue                  # Enfileira jobs no Redis
python main.py --tenant mjesus          # Apenas um tenant
python add_tenant.py                    # Adicionar novo tenant (interativo)
python scheduler.py --once              # Scheduler para cron
python worker.py                        # Worker rq
python health_check.py                  # Health check
pytest tests/                           # Rodar testes
```

### Regras CRÍTICAS do Projeto

1. **Excerpt do WordPress:** SEMPRE usar `meta_description` como excerpt, NUNCA auto-gerar do conteúdo (causa duplicação visual)
2. **H1 no conteúdo:** Manter 1 H1 no HTML do artigo. NÃO remover.
3. **Sem parágrafos soltos entre H1 e primeiro H2:** O primeiro H2 faz papel de introdução
4. **Prompts em Jinja2:** Ficam em `config/tenants/_default/prompts/`. Cada agente tem seu .txt
5. **Humanizer é OPCIONAL:** Desabilitado por default. A voz do profissional está integrada no Writer
6. **Keywords no título:** O Analyst DEVE manter a keyword exata da planilha no título
7. **SEO Scorer:** 10 checks, 100 pontos. Mínimo 40 para publicar.
8. **Credenciais:** NUNCA no código. Sempre via .env com prefix do tenant (ex: MJESUS_WP_USERNAME)
9. **sites.json:** Legacy, mantido para backward compatibility. Nova config em `config/tenants/`
10. **Testes:** 263 testes. SEMPRE rodar antes de commitar. Zero regressão.

### Problema ABERTO (não resolvido)

- **Duplicação visual no WordPress:** O tema do WordPress mostra o título + excerpt ANTES do conteúdo do artigo, criando duplicação visual. O excerpt já foi corrigido para usar meta_description, mas o tema pode ainda estar mostrando um preview customizado. Investigar o tema WordPress do mjesus.com.br.

### Tenant Atual

- **mjesus** — Marcelo Jesus, Hipnoterapeuta TRI em Moema, São Paulo
  - WordPress: mjesus.com.br
  - Credenciais: MJESUS_WP_USERNAME / MJESUS_WP_APP_PASSWORD no .env
  - KB: 5 arquivos TRI (essência, voz, premium, formação)
  - CTA: WhatsApp
  - Agentes: analyst, writer, editor, visual, growth (sem humanizer)

---
*Synkra AIOX Claude Code Configuration v2.0 + Fábrica de Artigos SEO v2.0*
