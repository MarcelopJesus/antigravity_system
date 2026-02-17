# Fábrica de Artigos SEO — PRD: Robustez e Resiliência (Fase 1)

**Versão:** 1.0
**Data:** 2026-02-17
**Autor:** Orion (AIOS Master) + Marcelo Jesus
**Status:** Draft — Aguardando Aprovação

---

## 1. Goals

- Tornar o pipeline de geração de artigos resiliente a falhas de APIs externas (Gemini, Imagen, WordPress, Google Sheets)
- Implementar logging estruturado que permita diagnosticar problemas sem acesso ao terminal
- Proteger credenciais sensíveis contra exposição acidental em commits
- Garantir que falhas em uma keyword não afetem o processamento das demais
- Estabelecer validação de inputs/outputs entre os 6 agentes do pipeline
- Criar base de testes automatizados para prevenir regressões

## 2. Background Context

O sistema "Fábrica de Artigos SEO" está funcional em produção, gerando artigos para o site do Marcelo Jesus (TRI — Terapia de Reintegração Implícita). A arquitetura multi-tenant suporta múltiplas empresas via `sites.json`.

Porém, o sistema foi construído em modo MVP: não possui tratamento de erros robusto, logs persistentes, ou testes automatizados. Uma falha na API do Gemini pode derrubar todo o processamento. Credenciais do WordPress estão em plaintext no `sites.json`. Não há forma de saber se um artigo falhou sem estar olhando o terminal em tempo real.

Esta Fase 1 visa transformar o MVP funcional em um sistema de produção confiável.

### Change Log

| Data | Versão | Descrição | Autor |
|------|--------|-----------|-------|
| 2026-02-17 | 1.0 | Criação inicial do PRD | Orion / Marcelo |

---

## 3. Requirements

### 3.1 Functional Requirements

- **FR1:** O sistema DEVE registrar logs estruturados em arquivo (`logs/pipeline-YYYY-MM-DD.log`) com níveis DEBUG, INFO, WARNING, ERROR usando o módulo `logging` do Python
- **FR2:** O sistema DEVE capturar e logar exceções por keyword individualmente, sem interromper o processamento das keywords restantes
- **FR3:** Quando uma keyword falhar, o sistema DEVE atualizar o Google Sheets com status "Error" e a mensagem de erro resumida na coluna de observações
- **FR4:** O sistema DEVE implementar retry com backoff exponencial (base 2s, max 3 tentativas) para chamadas ao Gemini API, Imagen API e WordPress API
- **FR5:** Credenciais sensíveis (wordpress_username, wordpress_app_password) DEVEM ser movidas de `sites.json` para variáveis de ambiente ou arquivo `.env`, referenciadas por chave no `sites.json`
- **FR6:** O sistema DEVE validar dados do Google Sheets antes de processar: keyword não vazia, sem duplicatas na mesma execução, comprimento máximo de 200 caracteres
- **FR7:** Cada agente DEVE validar que seu output não está vazio e contém o formato esperado antes de passar ao próximo agente (outline é JSON válido, HTML contém tags, etc.)
- **FR8:** Se a geração de imagem falhar (Imagen API), o sistema DEVE publicar o artigo sem imagem em vez de abortar, logando um WARNING
- **FR9:** O sistema DEVE gerar um relatório resumo ao final de cada execução: total de keywords processadas, sucesso, falhas, tempo total
- **FR10:** O sistema DEVE ter testes unitários com `pytest` cobrindo: validação de inputs, parsing de JSON do analyst, limpeza de HTML do editor, rotação de API keys

### 3.2 Non-Functional Requirements

- **NFR1:** O pipeline DEVE continuar funcionando mesmo que 1 das 3 APIs externas esteja temporariamente indisponível (degradação graciosa)
- **NFR2:** Logs NÃO DEVEM conter API keys, senhas ou tokens — apenas referências mascaradas (ex: `key_1`, `****`)
- **NFR3:** O tempo adicional de retry/backoff NÃO DEVE exceder 60 segundos por keyword (timeout total)
- **NFR4:** Testes unitários DEVEM rodar em menos de 30 segundos sem acesso a APIs externas (mocks)
- **NFR5:** O sistema DEVE ser compatível com Python 3.9+

---

## 4. Technical Assumptions

### 4.1 Repository Structure
- **Monorepo** — o projeto inteiro em um único repositório (mantém estrutura atual)

### 4.2 Service Architecture
- **Script Python monolítico** — sem necessidade de microserviços nesta fase
- Refatoração para classes com interface padronizada (BaseAgent) preparando Fase 2

### 4.3 Testing Requirements
- **Unit tests** com `pytest` e `pytest-mock`
- Mocks para todas as APIs externas (Gemini, WordPress, Google Sheets)
- Sem testes de integração nesta fase (Fase 3)

### 4.4 Additional Technical Assumptions
- Manter Google Gemini como LLM principal (sem trocar para OpenAI/Claude)
- Manter estrutura de pastas atual (`core/`, `config/`)
- Adicionar pasta `tests/` e `logs/` ao projeto
- Usar `python-dotenv` (já instalado) para gestão de credenciais
- Adicionar `pytest` e `pytest-mock` ao `requirements.txt`

---

## 5. Epic List

### Epic 1: Fundação de Resiliência

**Goal:** Tornar o pipeline resistente a falhas, com logging, validação e gestão segura de credenciais, sem alterar a lógica de negócio existente.

> Este é o único épico necessário para a Fase 1. Ele entrega um incremento completo de robustez que pode ser deployado imediatamente. As melhorias de arquitetura (BaseAgent, pipeline com checkpoints) e escala pertencem às Fases 2 e 3.

---

## 6. Epic 1 — Fundação de Resiliência

**Goal expandido:** Estabelecer a infraestrutura de confiabilidade do sistema: logging estruturado para diagnosticar problemas, error handling granular por keyword, retry inteligente para APIs externas, proteção de credenciais, validação de dados entre agentes, e testes unitários para prevenir regressões. Ao final deste épico, o sistema pode rodar desacompanhado com confiança de que falhas serão registradas, isoladas e recuperáveis.

---

### Story 1.1 — Logging Estruturado

**Como** operador do sistema,
**Quero** que todas as operações sejam registradas em arquivo de log com níveis e timestamps,
**Para que** eu possa diagnosticar problemas sem estar assistindo o terminal em tempo real.

**Acceptance Criteria:**

1. Módulo `core/logger.py` criado com configuração de logging para console + arquivo
2. Logs salvos em `logs/pipeline-YYYY-MM-DD.log` com rotação diária
3. Todos os `print()` do `main.py`, `gemini_brain.py`, `sheets_client.py` e `wordpress_client.py` substituídos por chamadas de logging apropriadas (info, warning, error)
4. Logs incluem timestamp, nível, módulo de origem e mensagem
5. API keys e senhas NUNCA aparecem nos logs (mascaradas)
6. Nível de log configurável via variável de ambiente `LOG_LEVEL` (default: INFO)

---

### Story 1.2 — Error Handling Granular por Keyword

**Como** operador do sistema,
**Quero** que uma falha em uma keyword não interrompa o processamento das demais,
**Para que** eu maximize a produção mesmo quando há problemas pontuais.

**Acceptance Criteria:**

1. Loop de keywords em `main.py` possui try/except individual que captura e loga a exceção completa (com traceback)
2. Quando uma keyword falha, o status no Google Sheets é atualizado para "Error" com mensagem resumida
3. Ao final do processamento de cada empresa, um resumo é logado: X keywords processadas, Y sucesso, Z falhas
4. Ao final de TODAS as empresas, um relatório consolidado é logado com totais gerais
5. O sistema retorna exit code 0 se todas as keywords foram processadas, 1 se houve falhas parciais

---

### Story 1.3 — Retry com Backoff Exponencial

**Como** sistema automatizado,
**Quero** tentar novamente chamadas de API que falharam por motivos temporários,
**Para que** problemas de rede ou rate limiting não causem falhas desnecessárias.

**Acceptance Criteria:**

1. Função utilitária `core/retry.py` com decorator `@retry_with_backoff(max_retries=3, base_delay=2.0, max_delay=30.0)`
2. Decorator aplicado a todas as chamadas de API: Gemini text, Imagen, WordPress upload, WordPress create_post
3. Retry APENAS para erros recuperáveis (429, 500, 502, 503, 504, timeout, ConnectionError)
4. Erros não-recuperáveis (400, 401, 403) NÃO são retentados (falham imediatamente)
5. Cada retry é logado com número da tentativa e tempo de espera
6. Timeout total por keyword não excede 60 segundos (soma de todos os retries)
7. Rotação de API key do Gemini mantida e integrada com o retry (roda key antes do retry)

---

### Story 1.4 — Proteção de Credenciais

**Como** desenvolvedor,
**Quero** que credenciais sensíveis estejam em variáveis de ambiente e não em arquivos JSON,
**Para que** não haja risco de exposição acidental em commits ou logs.

**Acceptance Criteria:**

1. `sites.json` reestruturado: campos `wordpress_username` e `wordpress_app_password` removidos, substituídos por referências (`credentials_env_prefix: "MJESUS"`)
2. Credenciais lidas de `.env` usando padrão: `{PREFIX}_WP_USERNAME`, `{PREFIX}_WP_APP_PASSWORD`
3. `.env.example` atualizado com as novas variáveis documentadas
4. `config/settings.py` atualizado com função de carregamento de credenciais por empresa
5. Validação na inicialização: se credenciais estiverem faltando, erro claro e descriptivo (não crash genérico)
6. `.gitignore` verificado: `.env` e `config/service_account.json` incluídos

---

### Story 1.5 — Validação de Inputs e Outputs dos Agentes

**Como** sistema automatizado,
**Quero** validar os dados entre cada etapa do pipeline,
**Para que** um agente com output inválido seja detectado antes de propagar dados corrompidos.

**Acceptance Criteria:**

1. Validação de input do Sheets: keyword não vazia, < 200 chars, sem duplicatas na batch atual
2. Output do Analyst validado: JSON válido com campos obrigatórios (`title`, `sections`, `meta_description`)
3. Output do Writer validado: string não vazia, contém pelo menos 1 tag HTML (`<h2>`, `<p>`)
4. Output do Humanizer validado: string não vazia, tamanho >= 50% do input (não apagou conteúdo)
5. Output do Editor validado: HTML limpo (sem blocos markdown residuais ```` ``` ````)
6. Quando validação falha, erro logado com contexto (nome do agente, keyword, tamanho do output) e keyword marcada como "Error"

---

### Story 1.6 — Fallback de Imagens

**Como** operador do sistema,
**Quero** que artigos sejam publicados mesmo se a geração de imagens falhar,
**Para que** a produção de conteúdo não dependa 100% do Imagen API.

**Acceptance Criteria:**

1. Se Imagen API falhar para imagem de capa, artigo é publicado SEM featured image e um WARNING é logado
2. Se Imagen API falhar para imagem final, artigo é publicado sem imagem final e WARNING é logado
3. Se foto do autor falhar, artigo é publicado sem foto do autor e WARNING é logado
4. Placeholders `<!-- IMG_PLACEHOLDER -->` restantes são removidos do HTML final antes da publicação
5. Relatório final inclui contagem de imagens com falha por empresa

---

### Story 1.7 — Testes Unitários Fundamentais

**Como** desenvolvedor,
**Quero** testes automatizados para as funções críticas do pipeline,
**Para que** mudanças futuras não quebrem funcionalidades existentes.

**Acceptance Criteria:**

1. Pasta `tests/` criada com `conftest.py` configurado
2. `pytest` e `pytest-mock` adicionados ao `requirements.txt`
3. Testes para `SheetsClient`: `test_get_pending_rows`, `test_update_row`, `test_get_all_completed_articles` (com mock do gspread)
4. Testes para `GeminiBrain`: `test_load_knowledge_base`, `test_rotate_key`, `test_analyze_and_plan_json_parsing`, `test_html_cleanup` (com mock do genai)
5. Testes para `WordPressClient`: `test_verify_auth`, `test_upload_media`, `test_create_post` (com mock do requests)
6. Testes para validações (Story 1.5): inputs inválidos, outputs vazios, JSON malformado
7. Todos os testes passam com `pytest tests/` sem acesso a APIs externas
8. Cobertura mínima: 70% das funções em `core/`

---

## 7. Checklist Results Report

_(A ser preenchido após validação do @po)_

---

## 8. Next Steps

### Prompt para @dev (após aprovação)

> Implemente o Epic 1 do PRD `docs/prd/prd-robustez-v1.md`. Comece pela Story 1.1 (Logging). O projeto é Python, os arquivos principais estão em `core/` e `main.py`. Siga a ordem das stories (1.1 → 1.7) pois há dependências sequenciais.

### Prompt para @qa (após implementação)

> Execute o QA Gate para o Epic 1. Valide que: (1) todos os testes passam, (2) logs são gerados corretamente, (3) credenciais não aparecem em nenhum output, (4) falhas em keywords individuais não interrompem o processamento.
