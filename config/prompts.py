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
Com base no artigo fornecido, crie 1 (um) prompt detalhado para gerar uma imagem de capa impactante e profissional usando uma IA geradora de imagens (como Imagen 3 ou Midjourney).

DIRETRIZES DO PROMPT DE IMAGEM:
- O prompt deve ser em INGLÊS (para melhor compreensão da IA de imagem).
- Descreva o estilo visual: "Photorealistic, cinematic lighting, 8k resolution, high quality".
- Descreva o sujeito da imagem de forma clara e metafórica se necessário, evitando texto escrito na imagem.
- NÃO descreva interfaces de usuário, prints ou gráficos complexos. Foque em fotografia ou ilustração editorial.

SAÍDA:
Retorne APENAS o texto do prompt, sem introduções ou explicações.
"""
