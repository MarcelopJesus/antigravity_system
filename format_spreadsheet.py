#!/usr/bin/env python3
"""
Script para aplicar formatação padrão em planilhas de clientes.
Garante que todos os tenants tenham a mesma estrutura visual.

Uso:
    python format_spreadsheet.py SPREADSHEET_ID

Exemplo:
    python format_spreadsheet.py 1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4
"""

import sys
import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import *


def apply_standard_formatting(spreadsheet_id, worksheet_name=None):
    """
    Aplica formatação padrão na planilha:
    - Header azul escuro com texto branco
    - Formatação condicional por Status
    - Largura de colunas otimizada
    - Header congelado
    """
    
    # Configurar credenciais
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file('config/service_account.json', scopes=scopes)
    client = gspread.authorize(creds)
    
    # Abrir planilha
    spreadsheet = client.open_by_key(spreadsheet_id)
    
    # Selecionar aba (primeira se não especificada)
    if worksheet_name:
        ws = spreadsheet.worksheet(worksheet_name)
    else:
        ws = spreadsheet.get_worksheet(0)
    
    print(f"🎨 Aplicando formatação na planilha...")
    print(f"   📊 Aba: {ws.title}")
    print()
    
    # 1. Formatar Header (Linha 1)
    print("   1️⃣ Formatando header...")
    header_format = CellFormat(
        backgroundColor=Color(0.1, 0.2, 0.36),  # Azul escuro
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),  # Branco
        horizontalAlignment='CENTER'
    )
    format_cell_range(ws, 'A1:C1', header_format)
    print("      ✅ Header: azul escuro + texto branco")
    
    # 2. Limpar e adicionar regras de formatação condicional
    print("   2️⃣ Configurando formatação condicional...")
    rules = get_conditional_format_rules(ws)
    rules.clear()
    
    # Regra: Pending = Amarelo
    rules.append(ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('B:B', ws)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_EQ', ['Pending']),
            format=CellFormat(backgroundColor=Color(1, 0.95, 0.8))  # Amarelo claro
        )
    ))
    print("      ✅ Pending = 🟡 Amarelo")
    
    # Regra: Done = Verde
    rules.append(ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('B:B', ws)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_EQ', ['Done']),
            format=CellFormat(backgroundColor=Color(0.82, 0.98, 0.88))  # Verde claro
        )
    ))
    print("      ✅ Done = 🟢 Verde")
    
    # Regra: Error = Vermelho
    rules.append(ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('B:B', ws)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_EQ', ['Error']),
            format=CellFormat(backgroundColor=Color(1, 0.89, 0.88))  # Vermelho claro
        )
    ))
    print("      ✅ Error = 🔴 Vermelho")
    
    # Regra: 💡 Sugestão IA = Roxo
    rules.append(ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('B:B', ws)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_CONTAINS', ['Sugestão IA']),
            format=CellFormat(backgroundColor=Color(0.9, 0.8, 1))  # Roxo claro
        )
    ))
    print("      ✅ 💡 Sugestão IA = 💜 Roxo")
    
    rules.save()
    
    # 3. Ajustar largura das colunas
    print("   3️⃣ Ajustando largura das colunas...")
    set_column_width(ws, 'A', 350)  # Keyword
    set_column_width(ws, 'B', 120)  # Status
    set_column_width(ws, 'C', 400)  # Link
    print("      ✅ Colunas ajustadas (350, 120, 400)")
    
    # 4. Congelar header
    print("   4️⃣ Congelando header...")
    set_frozen(ws, rows=1)
    print("      ✅ Linha 1 fixa ao rolar")
    
    # 5. Verificar se tem headers
    print("   5️⃣ Verificando headers...")
    headers = ws.row_values(1)
    if not headers or headers[0] != 'Keyword':
        print("      ⚠️ Headers não encontrados, adicionando...")
        ws.update('A1:C1', [['Keyword', 'Status', 'Link']])
        print("      ✅ Headers adicionados")
    else:
        print("      ✅ Headers OK")
    
    print()
    print("=" * 60)
    print("🎉 FORMATAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print()
    print(f"📊 Planilha formatada: {ws.title}")
    print(f"🔗 Link: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    print()
    print("📋 Resumo das formatações:")
    print("   • Header azul escuro com texto branco")
    print("   • Pending = Amarelo 🟡")
    print("   • Done = Verde 🟢")
    print("   • Error = Vermelho 🔴")
    print("   • 💡 Sugestão IA = Roxo 💜")
    print("   • Colunas otimizadas")
    print("   • Header congelado")


def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("📋 FORMATADOR DE PLANILHAS - Fábrica de Artigos SEO")
        print("=" * 60)
        print()
        print("Uso:")
        print("  python format_spreadsheet.py SPREADSHEET_ID")
        print()
        print("Exemplo:")
        print("  python format_spreadsheet.py 1fzKSh0ct2kWzJy9prrHFWiZBBRP1mTwx9xM9mfuh6c4")
        print()
        print("Como obter o SPREADSHEET_ID:")
        print("  1. Abra a planilha no Google Sheets")
        print("  2. Copie o ID da URL:")
        print("     https://docs.google.com/spreadsheets/d/[ID_AQUI]/edit")
        print()
        sys.exit(1)
    
    spreadsheet_id = sys.argv[1]
    worksheet_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        apply_standard_formatting(spreadsheet_id, worksheet_name)
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Erro: Planilha não encontrada!")
        print("   Verifique se:")
        print("   1. O ID está correto")
        print("   2. A planilha foi compartilhada com o service account")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
