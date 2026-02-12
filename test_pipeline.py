"""
🧪 TEST PIPELINE — Teste do Pipeline V3 com Humanizador TRI
Executa os 4 agentes de conteúdo sem precisar de WordPress ou Google Sheets.
Salva o resultado em HTML para avaliação visual.
"""

import json
import os
import sys
from datetime import datetime

# ─── Setup ───────────────────────────────────────────────────────
COMPANY_ID = "mjesus"
TEST_KEYWORD = "ansiedade tem cura"
KB_PATH = f"config/companies/{COMPANY_ID}/knowledge_base"

def main():
    print("🧪 ═══════════════════════════════════════════════════════")
    print("   TESTE DO PIPELINE V3 — TRI Humanized")
    print(f"   Keyword: '{TEST_KEYWORD}'")
    print(f"   KB Path: {KB_PATH}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═══════════════════════════════════════════════════════════\n")

    # Init Brain
    from core.gemini_brain import GeminiBrain
    
    try:
        brain = GeminiBrain(knowledge_base_path=KB_PATH)
        print("✅ Brain inicializado com sucesso!\n")
    except Exception as e:
        print(f"❌ Erro ao inicializar Brain: {e}")
        sys.exit(1)

    # Simular inventário de links internos
    mock_inventory = [
        {"keyword": "hipnoterapia", "url": "https://marcelojesus.com.br/hipnoterapia/"},
        {"keyword": "terapia online", "url": "https://marcelojesus.com.br/terapia-online/"},
        {"keyword": "autoconhecimento", "url": "https://marcelojesus.com.br/autoconhecimento/"},
    ]

    results = {}

    # ─────────────────────────────────────────────────────────────
    # STEP 1: ANALISTA DE CONTEÚDO
    # ─────────────────────────────────────────────────────────────
    print("━" * 60)
    print("📋 STEP 1: Analista de Conteúdo — Criando Outline...")
    print("━" * 60)
    
    try:
        outline = brain.analyze_and_plan(TEST_KEYWORD, mock_inventory)
        results['outline'] = outline
        
        print(f"   ✅ Título: {outline.get('title', 'N/A')}")
        print(f"   ✅ Meta: {outline.get('meta_description', 'N/A')}")
        print(f"   ✅ Pilar: {outline.get('is_pillar_page', False)}")
        print(f"   ✅ Seções: {len(outline.get('outline', []))}")
        for section in outline.get('outline', []):
            print(f"      → {section}")
        print()
    except Exception as e:
        print(f"   ❌ ERRO no Analista: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    # ─────────────────────────────────────────────────────────────
    # STEP 2: REDATOR SÊNIOR
    # ─────────────────────────────────────────────────────────────
    print("━" * 60)
    print("✍️  STEP 2: Redator Sênior — Escrevendo Artigo...")
    print("━" * 60)
    
    try:
        draft_html = brain.write_article_body(outline)
        results['draft'] = draft_html
        
        word_count = len(draft_html.split())
        print(f"   ✅ Draft gerado: {len(draft_html):,} chars / ~{word_count} palavras")
        print()
    except Exception as e:
        print(f"   ❌ ERRO no Redator: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    # ─────────────────────────────────────────────────────────────
    # STEP 3: HUMANIZADOR TRI (NOVO!)
    # ─────────────────────────────────────────────────────────────
    print("━" * 60)
    print("🎭 STEP 3: Humanizador TRI — Injetando Voz do Marcelo...")
    print("━" * 60)
    
    try:
        humanized_html = brain.humanize_with_tri_voice(draft_html)
        results['humanized'] = humanized_html
        
        word_count = len(humanized_html.split())
        print(f"   ✅ Humanizado: {len(humanized_html):,} chars / ~{word_count} palavras")
        print()
    except Exception as e:
        print(f"   ❌ ERRO no Humanizador: {e}")
        import traceback; traceback.print_exc()
        # Continue even if humanizer fails — use draft
        humanized_html = draft_html
        results['humanized'] = "FALLBACK: Using raw draft (humanizer failed)"

    # ─────────────────────────────────────────────────────────────
    # STEP 4: EDITOR DE CONVERSÃO
    # ─────────────────────────────────────────────────────────────
    print("━" * 60)
    print("🔧 STEP 4: Editor de Conversão — Polimento Final...")
    print("━" * 60)
    
    try:
        final_html = brain.edit_and_refine(humanized_html)
        results['final'] = final_html
        
        word_count = len(final_html.split())
        print(f"   ✅ Final: {len(final_html):,} chars / ~{word_count} palavras")
        print()
    except Exception as e:
        print(f"   ❌ ERRO no Editor: {e}")
        import traceback; traceback.print_exc()
        final_html = humanized_html
        results['final'] = final_html

    # ─────────────────────────────────────────────────────────────
    # SALVAR RESULTADOS
    # ─────────────────────────────────────────────────────────────
    print("━" * 60)
    print("💾 Salvando resultados...")
    print("━" * 60)

    # Ensure output directory exists
    os.makedirs("test_output", exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save outline JSON
    outline_path = f"test_output/outline_{timestamp}.json"
    with open(outline_path, 'w', encoding='utf-8') as f:
        json.dump(outline, f, indent=2, ensure_ascii=False)
    print(f"   📄 Outline: {outline_path}")

    # Save each stage as HTML for comparison
    title = outline.get('title', TEST_KEYWORD)
    
    stages = {
        'draft': ('Redator Sênior (Bruto)', draft_html),
        'humanized': ('Humanizador TRI (Voz Marcelo)', humanized_html),
        'final': ('Editor Final (Polido)', final_html),
    }

    for stage_key, (stage_name, content) in stages.items():
        filepath = f"test_output/{stage_key}_{timestamp}.html"
        full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — [{stage_name}]</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', sans-serif;
            max-width: 780px;
            margin: 0 auto;
            padding: 40px 24px;
            line-height: 1.8;
            color: #1a1a2e;
            background: #fafafa;
        }}
        
        .stage-badge {{
            display: inline-block;
            background: #6c5ce7;
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 24px;
            letter-spacing: 0.5px;
        }}
        
        h1 {{ 
            font-size: 2.2rem; 
            line-height: 1.3; 
            margin-bottom: 24px;
            color: #0d1b2a;
        }}
        
        h2 {{ 
            font-size: 1.6rem; 
            margin: 40px 0 16px; 
            color: #1b263b;
            border-left: 4px solid #6c5ce7;
            padding-left: 16px;
        }}
        
        h3 {{ 
            font-size: 1.2rem; 
            margin: 24px 0 12px; 
            color: #415a77;
        }}
        
        p {{ margin-bottom: 16px; }}
        
        ul, ol {{ 
            margin: 16px 0; 
            padding-left: 24px; 
        }}
        
        li {{ margin-bottom: 8px; }}
        
        strong {{ color: #0d1b2a; }}
        
        .cta-box {{
            background: linear-gradient(135deg, #0d1b2a, #1b263b);
            color: white;
            padding: 32px;
            border-radius: 16px;
            margin: 40px 0;
            text-align: center;
        }}
        
        .cta-box p {{ color: #e0e1dd; font-size: 1.1rem; }}
        
        .btn-whatsapp {{
            display: inline-block;
            background: #25D366;
            color: white;
            padding: 14px 32px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 16px;
            transition: transform 0.2s;
        }}
        
        .btn-whatsapp:hover {{ transform: scale(1.05); }}
        
        figure {{
            margin: 32px 0;
            text-align: center;
        }}
        
        figcaption {{
            font-size: 0.85rem;
            color: #778da9;
            margin-top: 8px;
        }}
    </style>
</head>
<body>
    <div class="stage-badge">🔍 {stage_name}</div>
    {content}
</body>
</html>"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"   📄 {stage_name}: {filepath}")

    # Summary
    print(f"\n{'═'*60}")
    print(f"🎉 TESTE COMPLETO!")
    print(f"{'═'*60}")
    print(f"   📂 Resultados em: test_output/")
    print(f"   🔑 Keyword: {TEST_KEYWORD}")
    print(f"   📝 Título: {title}")
    print(f"   📊 Draft: {len(draft_html):,} chars")
    print(f"   🎭 Humanizado: {len(humanized_html):,} chars")
    print(f"   ✨ Final: {len(final_html):,} chars")
    print(f"\n   💡 Abra os 3 HTMLs no navegador para comparar a evolução!")
    print(f"   💡 Compare 'draft' vs 'humanized' para ver o efeito do Humanizador TRI.")

if __name__ == "__main__":
    main()
