import base64
import json
import requests
import os

# ------------------------------------------------------------
# Configurações da API
# ------------------------------------------------------------
API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/gemini-2.5-flash:generateContent?key={API_KEY}"
)
HEADERS = {"Content-Type": "application/json"}

# ------------------------------------------------------------
# monta e envia a requisição para o Gemini
# ------------------------------------------------------------
def _chamar_gemini(partes: list) -> str:
    if not API_KEY:
        raise Exception("Chave da API não configurada. Defina a variável GEMINI_API_KEY.")
 
    payload = {"contents": [{"parts": partes}]}
    response = requests.post(GEMINI_URL, json=payload, headers=HEADERS)
    dados = response.json()
 
    if not response.ok:
        msg = dados.get("error", {}).get("message", "Erro desconhecido")
        raise Exception(f"Gemini API erro: {msg}")
 
    candidatos = dados.get("candidates", [])
    if not candidatos:
        raise Exception("A IA não retornou nenhuma resposta.")
 
    return candidatos[0]["content"]["parts"][0]["text"].strip()
 

# ------------------------------------------------------------
# Utilitário interno: converte bytes para base64 string
# ------------------------------------------------------------
def _para_base64(dados: bytes) -> str:
    return base64.b64encode(dados).decode("utf-8")


def _ler_json_resposta(texto: str) -> dict:
    texto = texto.strip()
    if texto.startswith("```"):
        linhas = texto.splitlines()
        texto = "\n".join(linhas[1:-1]).strip()
    return json.loads(texto)


# ============================================================
#  FLASHCARDS
# ============================================================
def gerar_flashcards(dados_imagem: bytes, mime_type: str, prompt: str = "") -> list:
    partes = [
        {
            "text": (
                f"Crie 3 flashcards sobre a imagem.\n"
                f"Instrução adicional do usuário: {prompt or 'Nenhuma'}\n"
                "Retorne APENAS no formato: P: [pergunta] R: [resposta]. "
                "Não use mais nenhuma palavra."
            )
        },
        {
            "inline_data": {
                "mime_type": mime_type,
                "data": _para_base64(dados_imagem),
            }
        },
    ]

    texto = _chamar_gemini(partes)

    cards = []
    blocos = texto.split("P:")[1:]  

    for bloco in blocos:
        if "R:" not in bloco:
            continue
        partes_bloco = bloco.split("R:")
        frente = partes_bloco[0].strip()
        verso = "R:".join(partes_bloco[1:]).strip()
        cards.append({"frente": frente, "verso": verso})

    return cards


def gerar_flashcards_texto(texto: str, prompt: str = "") -> list:
    partes = [{
        "text": f"""Crie 3 flashcards com base no texto abaixo.
Instrução adicional do usuário: {prompt or "Nenhuma"}
Retorne somente JSON válido no formato:
{{"cards": [{{"frente": "Pergunta", "verso": "Resposta"}}]}}

Texto:
{texto}"""
    }]
    resposta = _ler_json_resposta(_chamar_gemini(partes))
    return resposta["cards"]


# ============================================================
#  EDITOR DE DOCUMENTO
# ============================================================
def gerar_documento(dados_imagem: bytes, mime_type: str, prompt: str = "") -> str:
    partes = [
        {
            "text": (
                f"Transcreva todo o texto presente nesta imagem de forma clara e organizada.\n"
                f"Instrução adicional do usuário: {prompt or 'Nenhuma'}\n"
                "Corrija eventuais erros de digitação ou leitura. "
                "Retorne APENAS o texto transcrito, sem comentários adicionais."
            )
        },
        {
            "inline_data": {
                "mime_type": mime_type,
                "data": _para_base64(dados_imagem),
            }
        },
    ]

    return _chamar_gemini(partes)


def melhorar_documento(texto: str, prompt: str = "") -> dict:
    partes = [{
        "text": f"""Melhore o documento abaixo.
Mantenha as informações originais.
Retorne JSON válido com:
- texto: documento melhorado
- comentario: explicação do que foi melhorado

Solicitação:
{prompt}

Documento original:
{texto}"""
    }]
    resultado = _ler_json_resposta(_chamar_gemini(partes))
    if not isinstance(resultado.get("texto"), str) or not isinstance(resultado.get("comentario"), str):
        raise ValueError("A IA não retornou texto e comentario válidos.")
    return resultado


# ============================================================
#  LEITOR DE CÓDIGO
# ============================================================
def ler_codigo(dados_imagem: bytes, mime_type: str, prompt: str = "") -> dict:
    partes = [
        {
            "text": (
                f"Identifique a linguagem e extraia o código desta imagem.\n"
                f"Instrução adicional do usuário: {prompt or 'Nenhuma'}\n"
                "Retorne APENAS no seguinte formato:\n"
                "LINGUAGEM: [nome da linguagem]\n"
                "CODIGO:\n[código perfeitamente indentado]\n"
                "Não use blocos de markdown como ```python."
            )
        },
        {
            "inline_data": {
                "mime_type": mime_type,
                "data": _para_base64(dados_imagem),
            }
        },
    ]

    texto = _chamar_gemini(partes)

    linguagem = "Desconhecida"
    linhas_codigo = []
    dentro_bloco = False

    for linha in texto.split("\n"):
        if linha.startswith("LINGUAGEM:"):
            linguagem = linha.replace("LINGUAGEM:", "").strip()
        elif linha.startswith("CODIGO:"):
            dentro_bloco = True
        elif dentro_bloco:
            linhas_codigo.append(linha)

    return {
        "linguagem": linguagem,
        "codigo": "\n".join(linhas_codigo).strip(),
    }


def melhorar_codigo(codigo_original: str, prompt: str = "") -> str:
    partes = [
        {
            "text": f"""Melhore o código abaixo.
Mantenha o comportamento original.
Retorne somente o código, sem explicações ou markdown.

Solicitação:
{prompt}

Código original:
{codigo_original}"""
        }
    ]

    return _chamar_gemini(partes)


# ============================================================
#  TRADUTOR DE LIBRAS
# ============================================================
def traduzir_libras(
    dados_video: bytes,
    mime_type: str,
    prompt: str = "",
    categoria: str = "",
) -> str:
    partes = [
        {
                "text": f"""Você é um tradutor e intérprete especialista em Língua Brasileira de Sinais (Libras). Sua tarefa é assistir ao vídeo fornecido e realizar uma transcrição literal e detalhada de tudo o que é sinalizado.

            Instrução adicional do usuário: {prompt or "Nenhuma"}
            Categoria selecionada: {categoria or "Não informada"}

    Siga rigorosamente as seguintes regras de transcrição:
    1. TRANSCREVA TUDO: Não resuma, não omita e não pule nenhum trecho.
    2. ALFABETO RESTRITO (Dactilologia): Se forem letras isoladas do alfabeto, retorne cada letra na ordem exata em que foi soletrada (ex: C-A-S-A).
    3. PALAVRAS E FRASES: Se for uma palavra ou frase, retorne-a completa e corrigida para a estrutura gramatical do português, mantendo o sentido exato do sinal.
    4. MÚSICAS: Se o vídeo for uma interpretação musical, retorne a letra completa da música exatamente como foi sinalizada.
    5. SINAIS DESCRITIVOS/CLASSIFICADORES: Se houver uma ação, expressão facial gramatical ou gesto descritivo sem palavra direta, descreva a ação em português entre colchetes (ex: [acenando com raiva], [indicando um objeto grande]).
    6. SEQUÊNCIA: Se houver múltiplos sinais em sequência, mantenha a ordem cronológica exata do vídeo.

    DIRETRIZ DE FORMATAÇÃO (CRÍTICA):
    - Retorne APENAS a transcrição final.
    - Não inclua explicações, introduções, saudações, comentários ou notas de rodapé.
    - Não use aspas no texto final."""
        },
        {
            "inline_data": {
                "mime_type": mime_type,
                "data": _para_base64(dados_video),
            }
        },
    ]
    return _chamar_gemini(partes)