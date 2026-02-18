# Fabrica de Artigos SEO - Contexto do Projeto

## O que e este projeto
Pipeline automatizado de criacao de artigos SEO para blogs WordPress. Multi-tenant (suporta multiplos sites). Atualmente usado para mjesus.com.br (Marcelo Jesus - Hipnoterapeuta TRI em Moema, SP).

## Arquitetura do Pipeline
```
Keyword (Google Sheets) -> Analyst -> Writer -> Humanizer -> Editor -> Visual (3 imagens IA) -> WordPress
```

### Agentes (core/agents/)
- **Analyst** (`analyst.py`): Recebe keyword, gera outline JSON (titulo, meta desc, FAQ, LSI keywords, links internos)
- **Writer** (`writer.py`): Recebe outline, escreve artigo HTML completo com FAQ
- **Humanizer** (`humanizer.py`): Ajusta tom para voz do Marcelo Jesus (TRI)
- **Editor** (`editor.py`): Polimento final, posiciona 2x IMG_PLACEHOLDER, limpa HTML
- **Visual** (`visual.py`): Gera 3 imagens editoriais via Imagen API (capa, corpo, final)
- **Growth** (`growth.py`): Sugere 2 novos topicos apos publicacao
- **SEO Scorer** (`seo_scorer.py`): Avalia artigo em 10 criterios, gera score 0-100

### Pipeline (core/pipeline.py)
- Orquestra os 4 agentes textuais em sequencia
- Valida output de cada agente
- `fix_image_placement()`: Garante 2 IMG_PLACEHOLDER bem posicionados
- Injeta links internos
- SEO Quality Gate: score < 40 bloqueia, 40-59 warning, 60+ OK
- Gera slug e excerpt automaticamente
- Detecta keywords prioritarias (links para artigos inexistentes)

### Publicacao
- `core/wordpress_client.py`: API REST do WordPress (posts, media, Yoast SEO)
- `core/sheets_client.py`: Google Sheets (keywords pendentes, status, links)
- Keywords com status PRIORIDADE sao processadas primeiro

## Comandos CLI
```bash
python main.py                           # Producao (le keywords do Sheets, publica no WP)
python main.py --dry-run                 # Teste local (salva em output/)
python main.py --dry-run --keywords X    # Teste com keywords de arquivo JSON
python main.py --reoptimize              # Re-otimiza artigos existentes no WP
```

## Configuracao
- `config/sites.json`: Dados do site (WP URL, credenciais, SEO local, dados do negocio)
- `config/prompts.py`: Todos os prompts dos agentes
- `config/companies/{id}/knowledge_base/`: Base de conhecimento TRI (arquivos .txt)
- `config/service_account.json`: Credenciais Google Sheets (nao commitar)

## Decisoes Tecnicas Importantes
1. **Schema JSON-LD NAO vai no content** - WordPress filtra `<script>` tags e renderiza como texto. Yoast SEO cuida do schema.
2. **Imagens sao todas geradas por IA** (Imagen API) - 3 imagens: capa (featured), corpo (pos-intro), final (pre-CTA)
3. **FAQ obrigatorio** - Todo artigo deve ter secao "Perguntas Frequentes" com 4-5 perguntas H3
4. **Keywords prioritarias** - Quando o Analyst sugere link para artigo inexistente, a keyword vai para planilha como PRIORIDADE
5. **SEO local** - Artigos mencionam Moema/SP naturalmente via config `local_seo`
6. **Retry no Analyst** - Parser JSON robusto com 3 metodos de extracao + retry automatico (max 2 tentativas)

## Arquivos Principais
| Arquivo | Funcao |
|---------|--------|
| `main.py` | CLI principal |
| `core/pipeline.py` | Orquestrador do pipeline |
| `core/agents/*.py` | Agentes individuais |
| `core/wordpress_client.py` | API WordPress |
| `core/sheets_client.py` | API Google Sheets |
| `core/seo/schema.py` | Geradores JSON-LD (nao injeta no content) |
| `core/seo/internal_links.py` | Injecao de links internos |
| `core/reoptimizer.py` | Re-otimizacao de artigos existentes |
| `config/prompts.py` | Prompts de todos os agentes |
| `config/sites.json` | Configuracao multi-tenant |

## Testes
```bash
python -m pytest tests/ -v    # 211 testes
```

## Regras para Claude
- Seja direto e conciso. Nao repita contexto que ja esta aqui.
- Sempre rode `python -m pytest tests/` apos alteracoes.
- Nao injete schema JSON-LD no content do WordPress.
- Ao modificar prompts, verificar se o Analyst ainda retorna JSON valido.
- Ao modificar pipeline, testar com `--dry-run` antes de produzir.
- Responda sempre em portugues.
