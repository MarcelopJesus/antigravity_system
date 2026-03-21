# Instrucoes para Instalacao do Schema JSON-LD no WordPress

**Site:** mjesus.com.br
**Solicitante:** Marcelo Jesus
**Data:** 2026-03-21

---

## O que precisa ser feito

Instalar um pequeno arquivo PHP no WordPress que permite exibir dados estruturados (Schema JSON-LD) nos artigos do blog. Isso melhora o SEO e permite que o Google exiba rich results (FAQ, informacoes do autor, etc).

---

## Opcao A — MU-Plugin (RECOMENDADO)

MU-Plugin (Must-Use Plugin) e carregado automaticamente pelo WordPress, sem precisar ativar.

### Passo a passo

1. Acesse os arquivos do servidor via FTP, SSH ou Gerenciador de Arquivos da hospedagem
2. Navegue ate: `wp-content/mu-plugins/`
3. Se a pasta `mu-plugins` NAO existir, crie ela
4. Crie um arquivo chamado `mu-seo-schema.php` dentro dessa pasta
5. Cole o codigo PHP abaixo no arquivo
6. Salve

### Caminho final do arquivo:
```
wp-content/mu-plugins/mu-seo-schema.php
```

---

## Opcao B — functions.php do Tema

Se preferir nao criar mu-plugin, pode adicionar o codigo no functions.php do tema ativo.

### Passo a passo

1. No WP Admin: Aparencia → Editor de Arquivos do Tema
2. Selecione `functions.php` na lista de arquivos
3. Cole o codigo PHP abaixo NO FINAL do arquivo (antes do `?>` se existir, ou na ultima linha)
4. Salve

**ATENCAO:** Se o tema for atualizado ou trocado, esse codigo sera perdido. A Opcao A e mais segura.

---

## Opcao C — Plugin Code Snippets

1. No WP Admin: Plugins → Adicionar Novo
2. Pesquise "Code Snippets" (autor: Code Snippets Pro)
3. Instale e ative
4. Va em Snippets → Adicionar Novo
5. Nome: "SEO Schema JSON-LD"
6. Cole o codigo PHP abaixo (SEM as tags `<?php` e `?>`)
7. Marque "Executar em todo lugar"
8. Salve e ative

---

## Codigo PHP

```php
<?php
/**
 * SEO Schema JSON-LD Output
 *
 * Le o campo '_seo_schema_json_ld' dos posts e renderiza
 * como <script type="application/ld+json"> no <head> da pagina.
 *
 * Instalado para: mjesus.com.br
 * Sistema: Fabrica de Artigos SEO
 */

// Registra o campo meta para que a REST API aceite o dado
add_action('init', function () {
    register_post_meta('post', '_seo_schema_json_ld', array(
        'show_in_rest'  => true,
        'single'        => true,
        'type'          => 'string',
        'auth_callback' => function () {
            return current_user_can('edit_posts');
        },
    ));
});

// Renderiza o schema JSON-LD no <head> para posts individuais
add_action('wp_head', function () {
    if (!is_singular('post')) {
        return;
    }

    $schema_json = get_post_meta(get_the_ID(), '_seo_schema_json_ld', true);
    if (empty($schema_json)) {
        return;
    }

    $schemas = json_decode($schema_json, true);
    if (!is_array($schemas)) {
        return;
    }

    foreach ($schemas as $schema) {
        if (!empty($schema)) {
            $encoded = wp_json_encode($schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
            if ($encoded) {
                echo '<script type="application/ld+json">' . "\n" . $encoded . "\n" . '</script>' . "\n";
            }
        }
    }
}, 1);
```

---

## Como validar apos a instalacao

1. Publique um artigo pelo sistema de artigos SEO
2. Abra o artigo no navegador
3. Clique com botao direito → "Exibir codigo-fonte da pagina" (Ctrl+U)
4. Pesquise por `application/ld+json` (Ctrl+F)
5. Deve aparecer um bloco `<script type="application/ld+json">` com dados do artigo
6. Para validacao completa, cole a URL do artigo em: https://search.google.com/test/rich-results

---

## Informacoes tecnicas adicionais

- O codigo NAO conflita com o Yoast SEO
- O codigo NAO afeta artigos existentes (so funciona para artigos novos que tenham o campo preenchido)
- O campo `_seo_schema_json_ld` e preenchido automaticamente pelo sistema de publicacao via REST API
- Nenhuma configuracao adicional e necessaria apos a instalacao
- O codigo e compativel com WordPress 5.0+ e PHP 7.4+

---

*Gerado automaticamente pela Fabrica de Artigos SEO — 2026-03-21*
