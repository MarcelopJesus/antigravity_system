# Session Review — Meta-Learning Cross-Session

Você é um facilitador de reflexão estruturada. Ao final desta sessão, execute o protocolo abaixo para capturar meta-learning que evitará repetição de erros e consolidará padrões de sucesso em sessões futuras.

## Protocolo de Execução

### Passo 1: Coleta — Analise a sessão atual

Revise TODA a conversa desta sessão e identifique:

1. **What I got WRONG** (máx 5 itens)
   - Erros cometidos: false positives aceitos sem verificar, over-engineering, aceitação rápida demais, padrão corrigido parcialmente, comandos arriscados
   - Para cada erro: descreva O QUE aconteceu, POR QUE foi um erro, e COMO deveria ter sido feito

2. **What I did RIGHT** (máx 5 itens)
   - Acertos que devem virar padrão: ler antes de editar, build checks, fixes sequenciais, cross-validation, verificar imports órfãos
   - Para cada acerto: descreva O QUE funcionou e POR QUE foi a abordagem correta

3. **Where I HESITATED** (máx 3 itens)
   - Pontos de tensão/trade-off: schema vs pragmático, limitação de plataforma, backwards compatibility vs data migration
   - Para cada hesitação: descreva o DILEMA, a DECISÃO tomada, e se foi CORRETA em retrospecto

4. **Cross-session patterns** (máx 4 itens)
   - Meta-padrões recorrentes que transcendem uma sessão específica
   - Exemplos: "ship then audit" vs "audit then ship", "agent trust without verification", "fix symptom vs fix pattern", "scope containment"

### Passo 2: Leitura do arquivo existente

Leia o arquivo de meta-learning existente em:
`/Users/marcelojesus/.claude/projects/-Users-marcelojesus-Code-F-brica-de-Artigos-SEO/memory/meta_learning.md`

Se não existir, crie-o com a estrutura base do Passo 3.

### Passo 3: Atualização do meta_learning.md

Atualize o arquivo seguindo estas regras:

- **Formato de cada entrada:** `- [YYYY-MM-DD] descrição concisa`
- **Máximo por seção:** 5 itens mais recentes. Quando ultrapassar 5, remova o mais antigo EXCETO se ele tiver sido marcado como `[PADRÃO]` (padrão consolidado que apareceu 3+ vezes)
- **Promoção a padrão:** Se um aprendizado aparece em 3+ sessões diferentes, prefixe com `[PADRÃO]` e ele se torna permanente
- **Não duplicar:** Se o aprendizado já existe, atualize a data e incremente a contagem entre parênteses, ex: `(x3)`

Estrutura do arquivo:

```markdown
---
name: meta_learning
description: Aprendizados cross-session — erros, acertos, hesitações e padrões recorrentes do Claude
type: feedback
---

# Meta-Learning Cross-Session

> Última atualização: YYYY-MM-DD
> Total de sessões registradas: N

## What I Got WRONG
<!-- Erros que NÃO devo repetir -->
- [YYYY-MM-DD] descrição do erro e como evitar

## What I Did RIGHT
<!-- Acertos que DEVO manter como padrão -->
- [YYYY-MM-DD] descrição do acerto

## Where I HESITATED
<!-- Trade-offs e decisões difíceis para referência futura -->
- [YYYY-MM-DD] dilema → decisão tomada → resultado

## Cross-Session Patterns
<!-- Meta-padrões consolidados (3+ ocorrências = [PADRÃO]) -->
- [PADRÃO] "nome do padrão": descrição e quando aplicar

## Mandatory Ritual Checklist
Antes de encerrar qualquer sessão, verificar:
- [ ] Erros desta sessão foram registrados?
- [ ] Acertos desta sessão foram registrados?
- [ ] Algum padrão atingiu 3+ ocorrências para promoção?
- [ ] Itens antigos sem recorrência foram removidos?
- [ ] MEMORY.md está indexando este arquivo?
```

### Passo 4: Indexação no MEMORY.md

Verifique se o arquivo `MEMORY.md` em `/Users/marcelojesus/.claude/projects/-Users-marcelojesus-Code-F-brica-de-Artigos-SEO/memory/MEMORY.md` contém referência ao `meta_learning.md`.

Se não contiver, adicione:
```
- [meta_learning.md](meta_learning.md) — Aprendizados cross-session: erros, acertos, hesitações e padrões recorrentes
```

### Passo 5: Apresentação ao usuário

Apresente um resumo compacto do que foi registrado:

```
📝 Session Review registrado:
- ❌ N erros capturados
- ✅ N acertos consolidados
- 🤔 N hesitações documentadas
- 🔄 N padrões cross-session (M promovidos a [PADRÃO])
```

## Regras Importantes

1. **Seja brutalmente honesto** — Não minimize erros nem exagere acertos
2. **Seja específico** — "Editei sem ler o arquivo" é melhor que "fui descuidado"
3. **Foque no actionable** — Cada item deve ter uma ação clara para o futuro
4. **Não invente** — Se a sessão foi limpa sem erros, registre apenas os acertos
5. **Mantenha enxuto** — O arquivo deve ser rápido de ler (~50 linhas máx)
