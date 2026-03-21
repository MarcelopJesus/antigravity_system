# WordPress Theme Integration Guide — Fabrica de Artigos SEO

## Requisitos do Tema

O tema WordPress deve suportar os seguintes elementos gerados pela Fabrica:

### 1. Estrutura HTML dos Artigos

O pipeline gera artigos com esta estrutura:

```html
<h1>Titulo do Artigo</h1>
<h2>Primeira secao (funciona como introducao)</h2>
<p>Paragrafos de conteudo...</p>
<h2>Segunda secao</h2>
<h3>Sub-secao</h3>
<p>Mais conteudo...</p>
<!-- Imagens com figure e alt text -->
<figure class="wp-block-image"><img src="..." alt="keyword - contexto"/></figure>
<!-- FAQ section -->
<h2>Perguntas Frequentes</h2>
<h3>Pergunta 1?</h3>
<p>Resposta direta.</p>
<!-- Author badge -->
<div class="author-badge">
  <p><strong>Revisado por:</strong> Nome — Credenciais</p>
</div>
<!-- CTA box -->
<div class="cta-box">
  <p>Texto do CTA</p>
  <a href="https://wa.me/..." class="btn-whatsapp">Texto do botao</a>
</div>
<!-- TOC (pillar pages) -->
<nav class="toc-box">
  <p><strong>Neste artigo:</strong></p>
  <ul><li><a href="#secao">Secao</a></li></ul>
</nav>
```

### 2. CSS Necessario

Adicione ao tema (Appearance > Customize > Additional CSS):

```css
/* CTA Box — WhatsApp */
.cta-box {
  background: #f0f9f0;
  border: 2px solid #25D366;
  border-radius: 12px;
  padding: 24px;
  margin: 32px 0;
  text-align: center;
}
.cta-box p {
  font-size: 1.1em;
  margin-bottom: 16px;
  color: #333;
}
.btn-whatsapp {
  display: inline-block;
  background: #25D366;
  color: white !important;
  padding: 14px 28px;
  border-radius: 8px;
  font-size: 1.1em;
  font-weight: bold;
  text-decoration: none;
  transition: background 0.3s;
}
.btn-whatsapp:hover {
  background: #1da851;
  color: white !important;
}

/* Author Badge */
.author-badge {
  background: #f8f9fa;
  border-left: 4px solid #0066cc;
  padding: 12px 16px;
  margin: 24px 0;
  border-radius: 0 8px 8px 0;
}
.author-badge p {
  margin: 0;
  font-size: 0.95em;
  color: #555;
}

/* Table of Contents (Pillar Pages) */
.toc-box {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 20px;
  margin: 24px 0;
}
.toc-box p {
  margin: 0 0 12px 0;
  font-size: 1.05em;
}
.toc-box ul {
  margin: 0;
  padding-left: 20px;
}
.toc-box li {
  margin-bottom: 6px;
}
.toc-box a {
  color: #0066cc;
  text-decoration: none;
}
.toc-box a:hover {
  text-decoration: underline;
}

/* FAQ Accordion (optional) */
article h3 {
  cursor: default;
}

/* Images */
.wp-block-image {
  margin: 24px 0;
}
.wp-block-image img {
  border-radius: 8px;
  max-width: 100%;
  height: auto;
}
```

### 3. Plugins Recomendados

| Plugin | Motivo | Obrigatorio? |
|--------|--------|-------------|
| **Yoast SEO** | Meta descriptions, OG tags, sitemap | Sim |
| **WP Fastest Cache** ou **LiteSpeed Cache** | Performance (Core Web Vitals) | Sim |
| **WebP Express** | Converter imagens para WebP automaticamente | Recomendado |
| **Autoptimize** | Minificar CSS/JS | Recomendado |
| **Schema JSON-LD** (mu-plugin) | Dados estruturados | Sim (ver INSTRUCOES-WORDPRESS-SCHEMA.md) |

### 4. Configuracoes do Tema

#### Excerpt
- O pipeline envia excerpt vazio (" ") para evitar duplicacao visual
- Se o tema mostra excerpt no single post, desative via:
  - Tema > Customize > Single Post > Desativar excerpt
  - Ou CSS: `.single-post .entry-excerpt { display: none; }`

#### Featured Image
- Pipeline seta featured image automaticamente
- Tema deve exibir featured image no topo do post
- Tamanho recomendado: 1200x630px (OG image)

#### Headings
- H1 e gerado pelo pipeline (no conteudo)
- Se o tema tambem gera H1 do titulo, desative para evitar duplicacao
- Verificar: View Source > contar quantos `<h1>` existem (deve ser 1)

### 5. Template Recomendado (single.php)

Se tiver acesso ao tema, o template ideal para single posts:

```php
<?php get_header(); ?>
<main>
  <article>
    <?php
    // Featured image
    if (has_post_thumbnail()) {
        the_post_thumbnail('full', ['class' => 'featured-img']);
    }
    // Content (includes H1, sections, CTA, etc.)
    the_content();
    ?>
  </article>
</main>
<?php get_footer(); ?>
```

**NAO inclua** no template:
- `the_title()` dentro de `<h1>` (pipeline ja inclui H1 no conteudo)
- `the_excerpt()` (envia duplicacao visual)

---

*Guia gerado pela Fabrica de Artigos SEO — 2026-03-21*
