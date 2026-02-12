"""
🧪 TEST PIPELINE FULL — Teste Completo com Imagens
Executa TODOS os 6 agentes incluindo geração de imagens via Imagen 4.0
Salva o resultado final em HTML com imagens embutidas (base64).
"""

import json
import os
import sys
import base64
from datetime import datetime

COMPANY_ID = "mjesus"
TEST_KEYWORD = "ansiedade tem cura"
KB_PATH = f"config/companies/{COMPANY_ID}/knowledge_base"

def main():
    print("🧪 ═══════════════════════════════════════════════════════")
    print("   TESTE COMPLETO — Pipeline V3 com Imagens")
    print(f"   Keyword: '{TEST_KEYWORD}'")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═══════════════════════════════════════════════════════════\n")

    from core.gemini_brain import GeminiBrain
    
    try:
        brain = GeminiBrain(knowledge_base_path=KB_PATH)
        print("✅ Brain inicializado!\n")
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

    mock_inventory = [
        {"keyword": "hipnoterapia", "url": "https://marcelojesus.com.br/hipnoterapia/"},
        {"keyword": "terapia online", "url": "https://marcelojesus.com.br/terapia-online/"},
        {"keyword": "autoconhecimento", "url": "https://marcelojesus.com.br/autoconhecimento/"},
    ]

    # ─── STEP 1: ANALISTA ────────────────────────────────────────
    print("━" * 60)
    print("📋 STEP 1: Analista de Conteúdo...")
    print("━" * 60)
    outline = brain.analyze_and_plan(TEST_KEYWORD, mock_inventory)
    # Handle different return formats (dict vs list)
    if isinstance(outline, list):
        outline = outline[0] if outline else {}
    if not isinstance(outline, dict):
        print(f"   ⚠️ Outline format unexpected: {type(outline)}. Using fallback.")
        outline = {"title": TEST_KEYWORD.title(), "meta_description": "", "outline": []}
    title = outline.get('title', TEST_KEYWORD.title())
    print(f"   ✅ Título: {title}")
    print(f"   ✅ Seções: {len(outline.get('outline', []))}\n")

    # ─── STEP 2: REDATOR ─────────────────────────────────────────
    print("━" * 60)
    print("✍️  STEP 2: Redator Sênior...")
    print("━" * 60)
    draft_html = brain.write_article_body(outline)
    print(f"   ✅ Draft: {len(draft_html):,} chars\n")

    # ─── STEP 3: HUMANIZADOR TRI ─────────────────────────────────
    print("━" * 60)
    print("🎭 STEP 3: Humanizador TRI...")
    print("━" * 60)
    try:
        humanized_html = brain.humanize_with_tri_voice(draft_html)
        print(f"   ✅ Humanizado: {len(humanized_html):,} chars\n")
    except Exception as e:
        print(f"   ⚠️ Humanizer falhou, usando draft: {e}")
        humanized_html = draft_html

    # ─── STEP 4: EDITOR ──────────────────────────────────────────
    print("━" * 60)
    print("🔧 STEP 4: Editor de Conversão...")
    print("━" * 60)
    final_content = brain.edit_and_refine(humanized_html)
    print(f"   ✅ Editado: {len(final_content):,} chars\n")

    # ─── STEP 5: VISUAL (IMAGENS) ────────────────────────────────
    print("━" * 60)
    print("📷 STEP 5: Diretor de Arte — Gerando Imagens...")
    print("━" * 60)
    
    prompts_str = brain.generate_image_prompts(final_content)
    prompts_list = [p.strip() for p in prompts_str.split('|||') if p.strip()]
    print(f"   ✅ {len(prompts_list)} prompts de imagem gerados")
    
    images = {}  # Store base64 images
    slug = TEST_KEYWORD.replace(" ", "-").lower()[:30]
    
    # ---- IMAGE 1: AI Cover ----
    if len(prompts_list) >= 1:
        print(f"\n   📷 Image 1 (Capa): Gerando com Imagen 4.0...")
        print(f"      Prompt: {prompts_list[0][:100]}...")
        b64_cover = brain.generate_final_images(prompts_list[0])
        if b64_cover:
            images['cover'] = b64_cover
            print(f"      ✅ Capa gerada ({len(b64_cover):,} chars base64)")
        else:
            print(f"      ⚠️ Falha na geração da capa")

    # ---- IMAGE 2: Real Author Photo ----
    print(f"\n   📸 Image 2 (Autor): Carregando foto real...")
    author_data, author_filename = brain.get_real_author_photo()
    if author_data:
        images['author'] = base64.b64encode(author_data).decode('utf-8')
        images['author_ext'] = author_filename.split('.')[-1].lower()
        print(f"      ✅ Foto do autor: {author_filename}")
    else:
        print(f"      ⚠️ Nenhuma foto do autor encontrada")

    # ---- IMAGE 3: AI Final ----
    if len(prompts_list) >= 2:
        print(f"\n   📷 Image 3 (Final): Gerando com Imagen 4.0...")
        print(f"      Prompt: {prompts_list[1][:100]}...")
        b64_final = brain.generate_final_images(prompts_list[1])
        if b64_final:
            images['final'] = b64_final
            print(f"      ✅ Imagem final gerada ({len(b64_final):,} chars base64)")
        else:
            print(f"      ⚠️ Falha na geração da imagem final")

    # ─── MONTAR ARTIGO COMPLETO COM IMAGENS ──────────────────────
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔨 Montando artigo final com imagens embutidas...")
    print("━" * 60)

    # Inject images into placeholders or strategic positions
    # Image 1 (Cover) → After intro, before first H2
    if 'cover' in images:
        cover_html = (
            f"<figure class='wp-block-image alignwide size-large'>"
            f"<img src='data:image/png;base64,{images['cover']}' alt='{title}' style='width:100%;border-radius:12px;'/>"
            f"</figure>"
        )
        if "<!-- IMG_PLACEHOLDER -->" in final_content:
            final_content = final_content.replace("<!-- IMG_PLACEHOLDER -->", cover_html, 1)
            print("   ✅ Capa inserida no placeholder 1")
        else:
            # Insert after H1
            import re
            h1_match = re.search(r'(</h1>)', final_content)
            if h1_match:
                pos = h1_match.end()
                final_content = final_content[:pos] + "\n" + cover_html + "\n" + final_content[pos:]
                print("   ✅ Capa inserida após H1")

    # Image 2 (Author) → After first H2
    if 'author' in images:
        ext = images.get('author_ext', 'jpg')
        mime = f"image/{ext}" if ext != 'jpg' else 'image/jpeg'
        author_html = (
            f"<figure class='wp-block-image aligncenter size-large'>"
            f"<img src='data:{mime};base64,{images['author']}' "
            f"alt='Marcelo Jesus - Terapeuta TRI em Moema, São Paulo' "
            f"style='max-width:500px;border-radius:12px;'/>"
            f"<figcaption>Marcelo Jesus — Terapeuta especialista em TRI | Consultório em Moema, SP</figcaption>"
            f"</figure>"
        )
        if "<!-- IMG_PLACEHOLDER -->" in final_content:
            final_content = final_content.replace("<!-- IMG_PLACEHOLDER -->", author_html, 1)
            print("   ✅ Foto do autor inserida no placeholder 2")
        else:
            import re
            h2_match = re.search(r'(</h2>)', final_content)
            if h2_match:
                pos = h2_match.end()
                final_content = final_content[:pos] + "\n" + author_html + "\n" + final_content[pos:]
                print("   ✅ Foto do autor inserida após primeiro H2")

    # Image 3 (Final) → Before CTA
    if 'final' in images:
        final_img_html = (
            f"<figure class='wp-block-image alignwide'>"
            f"<img src='data:image/png;base64,{images['final']}' alt='{title}' "
            f"style='width:100%;border-radius:12px;'/>"
            f"</figure>"
        )
        if "<!-- IMG_PLACEHOLDER -->" in final_content:
            final_content = final_content.replace("<!-- IMG_PLACEHOLDER -->", final_img_html, 1)
            print("   ✅ Imagem final inserida no placeholder 3")
        elif '<div class="cta-box">' in final_content:
            final_content = final_content.replace(
                '<div class="cta-box">',
                final_img_html + '\n<div class="cta-box">'
            )
            print("   ✅ Imagem final inserida antes da CTA")

    # ─── STEP 6: GROWTH HACKER ───────────────────────────────────
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("💡 STEP 6: Growth Hacker — Sugestões de novos temas...")
    print("━" * 60)
    try:
        new_topics = brain.identify_new_topics(title, final_content)
        for topic in new_topics:
            print(f"   💡 {topic}")
    except Exception as e:
        print(f"   ⚠️ Growth Hacker falhou: {e}")

    # ─── SALVAR HTML FINAL COMPLETO ──────────────────────────────
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("💾 Salvando artigo completo...")
    print("━" * 60)

    os.makedirs("test_output", exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    meta_desc = outline.get('meta_description', '')

    full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{meta_desc}">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 48px 24px;
            line-height: 1.85;
            color: #2d2d3a;
            background: #fafaf9;
        }}
        
        h1 {{ 
            font-family: 'Playfair Display', serif;
            font-size: 2.4rem; 
            line-height: 1.25; 
            margin-bottom: 28px;
            color: #0d1b2a;
            letter-spacing: -0.02em;
        }}
        
        h2 {{ 
            font-family: 'Playfair Display', serif;
            font-size: 1.65rem; 
            margin: 48px 0 20px; 
            color: #1b263b;
            border-left: 4px solid #6c5ce7;
            padding-left: 20px;
            line-height: 1.35;
        }}
        
        h3 {{ 
            font-size: 1.2rem; 
            margin: 28px 0 14px; 
            color: #415a77;
            font-weight: 600;
        }}
        
        p {{ 
            margin-bottom: 18px; 
            font-size: 1.05rem;
        }}
        
        ul, ol {{ 
            margin: 18px 0; 
            padding-left: 28px; 
        }}
        
        li {{ margin-bottom: 10px; }}
        
        strong {{ color: #0d1b2a; font-weight: 600; }}
        em {{ color: #555; }}
        
        figure {{
            margin: 36px 0;
            text-align: center;
        }}
        
        figure img {{
            max-width: 100%;
            height: auto;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        }}
        
        figcaption {{
            font-size: 0.85rem;
            color: #778da9;
            margin-top: 10px;
            font-style: italic;
        }}
        
        .cta-box {{
            background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 50%, #415a77 100%);
            color: white;
            padding: 40px 36px;
            border-radius: 20px;
            margin: 48px 0 24px;
            text-align: center;
            box-shadow: 0 12px 40px rgba(13,27,42,0.25);
        }}
        
        .cta-box p {{ 
            color: #e0e1dd; 
            font-size: 1.15rem; 
            margin-bottom: 20px;
            line-height: 1.7;
        }}
        
        .btn-whatsapp {{
            display: inline-block;
            background: #25D366;
            color: white;
            padding: 16px 36px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 700;
            font-size: 1.05rem;
            margin-top: 8px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 16px rgba(37,211,102,0.35);
        }}
        
        .btn-whatsapp:hover {{ 
            transform: translateY(-2px); 
            box-shadow: 0 8px 24px rgba(37,211,102,0.45);
        }}
        
        a {{ color: #6c5ce7; text-decoration: none; border-bottom: 1px solid #6c5ce722; }}
        a:hover {{ border-bottom-color: #6c5ce7; }}
        
        blockquote {{
            border-left: 4px solid #6c5ce7;
            padding: 16px 24px;
            margin: 24px 0;
            background: #f0efff;
            border-radius: 0 8px 8px 0;
            font-style: italic;
            color: #415a77;
        }}

        /* Pipeline info footer */
        .pipeline-info {{
            margin-top: 60px;
            padding: 20px;
            background: #f0f0f0;
            border-radius: 8px;
            font-size: 0.8rem;
            color: #888;
        }}
    </style>
</head>
<body>
    {final_content}
    
    <div class="pipeline-info">
        <strong>🧪 Artigo de Teste — Pipeline V3 TRI Humanized</strong><br>
        Keyword: {TEST_KEYWORD} | 
        Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')} |
        Imagens: {'Capa ✅' if 'cover' in images else 'Capa ❌'} | 
        {'Autor ✅' if 'author' in images else 'Autor ❌'} | 
        {'Final ✅' if 'final' in images else 'Final ❌'}
    </div>
</body>
</html>"""

    filepath = f"test_output/ARTIGO_COMPLETO_{timestamp}.html"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    # Also save outline
    with open(f"test_output/outline_{timestamp}.json", 'w', encoding='utf-8') as f:
        json.dump(outline, f, indent=2, ensure_ascii=False)

    print(f"\n{'═'*60}")
    print(f"🎉 ARTIGO COMPLETO GERADO!")
    print(f"{'═'*60}")
    print(f"   📄 Arquivo: {filepath}")
    print(f"   📝 Título: {title}")
    print(f"   📊 Tamanho: {len(final_content):,} chars")
    print(f"   🖼️  Imagens: {len(images)} de 3")
    
    # Auto-open in browser
    import subprocess
    subprocess.run(['open', filepath])
    print(f"\n   🌐 Abrindo no navegador...")

if __name__ == "__main__":
    main()
