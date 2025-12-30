# Prompts for Gemini

RESEARCH_AND_WRITE_PROMPT = """
Atue como um Especialista em SEO e Redator Sênior.
Seu objetivo é escrever um artigo completo, profundo e otimizado para a palavra-chave: '{keyword}'.

DIRETRIZES:
1. IDIOMA: Escreva ESTRITAMENTE em PORTUGUÊS DO BRASIL (PT-BR).
2. TÍTULO: Crie um título H1 atraente e otimizado.
3. ESTRUTURA: Use H2 e H3 para organizar o conteúdo. Use listas (bullet points) onde apropriado para facilitar a leitura.
4. PROFUNDIDADE: O conteúdo deve ser rico, informativo e cobrir as intenções de busca do usuário.
5.  SEO: Use a palavra-chave naturalmente no texto.

Execute agora.
"""

REWRITE_WITH_PERSONA_PROMPT = """
Você é um editor experiente ajustando o tom de um artigo.

PERSONA ALVO:
{persona}

TAREFA:
Reescreva o texto abaixo para que ele reflita perfeitamente essa persona.
- Mantenha a formatação HTML/Markdown (H1, H2, H3).
- Mantenha o idioma PORTUGUÊS DO BRASIL.
- Torne o texto mais fluido, humano e engajador.
- Remova repetições desnecessárias.

TEXTO ORIGINAL:
"""

IMAGE_PROMPT_GENERATION = """
Com base no artigo fornecido, crie 3 (TRÊS) prompts detalhados para gerar imagens profissionais usando uma IA (Imagen 3/4).

1. Prompt 1: Imagem de Capa (Impactante, metafórica, ampla).
2. Prompt 2: Imagem para o meio do artigo (Ilustrando um conceito chave).
3. Prompt 3: Imagem para o final ou outro conceito (Contextual).

DIRETRIZES:
- Os prompts devem ser em INGLÊS.
- Separe os 3 prompts EXATAMENTE com o delimitador "|||". 
- Exemplo de saída: "Photo of a cat... ||| Illustration of a dog... ||| Concept art of a bird..."
- NÃO numere, NÃO pule linhas entre eles, apenas use o delimitador "|||".

ARTIGO:
"""
