#!/usr/bin/env python3
"""
Script Helper para adicionar novas empresas ao sistema Multi-Tenant
"""

import os
import json
import sys

def create_company_structure(company_id):
    """Cria a estrutura de pastas para uma nova empresa"""
    kb_path = f"config/companies/{company_id}/knowledge_base"
    
    try:
        os.makedirs(kb_path, exist_ok=True)
        
        # Criar README na knowledge base
        readme_content = f"""# Knowledge Base - {company_id}

Esta pasta está vazia. Adicione arquivos .txt com "premium" no nome para carregar conhecimento específico.

Exemplo: `metodologia_premium.txt`

Se não adicionar arquivos, o sistema usará conhecimento geral da IA Gemini.
"""
        
        readme_path = os.path.join(kb_path, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ Estrutura criada em: config/companies/{company_id}/")
        print(f"   └── knowledge_base/")
        print(f"       └── README.md")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar estrutura: {e}")
        return False

def add_to_sites_json(company_data):
    """Adiciona nova empresa ao sites.json"""
    sites_path = "config/sites.json"
    
    try:
        # Ler sites existentes
        with open(sites_path, 'r', encoding='utf-8') as f:
            sites = json.load(f)
        
        # Adicionar nova empresa
        sites.append(company_data)
        
        # Salvar
        with open(sites_path, 'w', encoding='utf-8') as f:
            json.dump(sites, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Empresa adicionada ao sites.json")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar sites.json: {e}")
        return False

def main():
    print("=" * 80)
    print("🏢 ADICIONAR NOVA EMPRESA - Fábrica de Artigos SEO")
    print("=" * 80)
    print()
    
    # Coletar informações
    print("Preencha as informações da nova empresa:\n")
    
    company_id = input("1. Company ID (ex: clinica_odonto): ").strip()
    if not company_id:
        print("❌ Company ID é obrigatório!")
        sys.exit(1)
    
    # Validar company_id
    if not company_id.replace('_', '').isalnum():
        print("❌ Company ID deve conter apenas letras, números e underscores!")
        sys.exit(1)
    
    site_name = input("2. Nome do Site (ex: Clínica Odontológica): ").strip()
    spreadsheet_id = input("3. Google Sheets ID: ").strip()
    wordpress_url = input("4. WordPress URL (ex: https://site.com): ").strip()
    persona_prompt = input("5. Persona/Especialidade (ex: Especialista em Odontologia): ").strip()
    wordpress_username = input("6. WordPress Username: ").strip()
    wordpress_app_password = input("7. WordPress App Password: ").strip()
    
    print("\n" + "=" * 80)
    print("📋 RESUMO DA CONFIGURAÇÃO")
    print("=" * 80)
    print(f"Company ID: {company_id}")
    print(f"Site Name: {site_name}")
    print(f"Spreadsheet ID: {spreadsheet_id}")
    print(f"WordPress URL: {wordpress_url}")
    print(f"Persona: {persona_prompt}")
    print(f"WordPress User: {wordpress_username}")
    print(f"WordPress Password: {'*' * len(wordpress_app_password)}")
    print("=" * 80)
    
    confirm = input("\nConfirmar adição? (s/n): ").strip().lower()
    if confirm != 's':
        print("❌ Operação cancelada.")
        sys.exit(0)
    
    # Criar estrutura
    print("\n📁 Criando estrutura de pastas...")
    if not create_company_structure(company_id):
        sys.exit(1)
    
    # Adicionar ao sites.json
    print("\n📝 Adicionando ao sites.json...")
    company_data = {
        "site_name": site_name,
        "company_id": company_id,
        "spreadsheet_id": spreadsheet_id,
        "wordpress_url": wordpress_url,
        "persona_prompt": persona_prompt,
        "wordpress_username": wordpress_username,
        "wordpress_app_password": wordpress_app_password
    }
    
    if not add_to_sites_json(company_data):
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ EMPRESA ADICIONADA COM SUCESSO!")
    print("=" * 80)
    print("\n📚 Próximos passos:")
    print(f"1. (Opcional) Adicione arquivos .txt em: config/companies/{company_id}/knowledge_base/")
    print(f"   - Use 'premium' no nome do arquivo (ex: metodologia_premium.txt)")
    print(f"2. Configure a planilha Google Sheets com colunas: Keyword | Status | Link")
    print(f"3. Compartilhe a planilha com o service account (permissão Editor)")
    print(f"4. Execute: python main.py")
    print()

if __name__ == "__main__":
    main()
