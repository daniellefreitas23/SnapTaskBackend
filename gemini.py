import base64
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


# ============================================================
#  FLASHCARDS
# ============================================================
def gerar_flashcards(dados_imagem: bytes, mime_type: str) -> list:
    partes = [
        {
            "text": (
                "Crie 3 flashcards sobre a imagem. "
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


# ============================================================
#  EDITOR DE DOCUMENTO
# ============================================================
def gerar_documento(dados_imagem: bytes, mime_type: str) -> str:
    partes = [
        {
            "text": (
                "Transcreva todo o texto presente nesta imagem de forma clara e organizada. "
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


# ============================================================
#  LEITOR DE CÓDIGO
# ============================================================
def ler_codigo(dados_imagem: bytes, mime_type: str) -> dict:
    partes = [
        {
            "text": (
                "Identifique a linguagem e extraia o código desta imagem. "
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


# ============================================================
#  TRADUTOR DE LIBRAS
# ============================================================
def traduzir_libras(dados_video: bytes, mime_type: str) -> str:
    partes = [
        {
            "text": (
                "Observe este vídeo com linguagem de sinais (Libras). "
                "Transcreva TUDO que foi sinalizado, sem resumir, sem omitir nada. "
                "Se forem letras do alfabeto, retorne cada letra na ordem. "
                "Se for uma palavra, retorne a palavra completa. "
                "Se for uma frase, retorne a frase completa. "
                "Se for uma música, retorne a letra completa como foi sinalizada. "
                "Se for uma ação ou gesto descritivo, retorne a ação em português. "
                "Se houver múltiplos sinais, retorne todos em sequência. "
                "Retorne APENAS a transcrição, sem explicações, sem aspas, sem comentários."
            )
        },
        {
            "inline_data": {
                "mime_type": mime_type,
                "data": _para_base64(dados_video),
            }
        },
    ]
    return _chamar_gemini(partes)