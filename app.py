# ============================================================
#  Este arquivo é o "servidor" da aplicação.
# ============================================================

import random
import os
import io
import base64
import segno
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
import gemini
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)
CORS(app, origins=os.environ.get("FRONTEND_ORIGIN", "*"))
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

TIPOS_GEMINI = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "text/markdown",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "video/mp4",
    "video/mpeg",
    "video/mov",
    "video/avi",
    "video/x-flv",
    "video/mpg",
    "video/webm",
    "video/wmv",
    "video/3gpp",
}


def _receber_arquivo(*nomes):
    arquivo = next((request.files.get(nome) for nome in nomes if request.files.get(nome)), None)
    if arquivo is None or not arquivo.filename:
        raise ValueError("Nenhum arquivo enviado. Use o campo multipart 'arquivo'.")

    dados = arquivo.read()
    if not dados:
        raise ValueError("O arquivo enviado está vazio.")

    mime_type = arquivo.mimetype or "application/octet-stream"
    if mime_type not in TIPOS_GEMINI:
        raise ValueError(f"Formato não suportado: {mime_type}.")

    return arquivo, dados, mime_type

# ------------------------------------------------------------
# Configurações da API
# ------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------------------
# Ping para não ibernar
# ------------------------------------------------------------
@app.route("/ping", methods=["GET"])
def ping():
    try:
        supabase.storage.list_buckets()
        return jsonify({"status": "ok"})
    except:
        return jsonify({"status": "ok"})

# ------------------------------------------------------------
#  Flashcards
# ------------------------------------------------------------
@app.route("/flashcards", methods=["POST"])
def flashcards():
    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada."}), 400

    prompt = request.form.get("prompt", "").strip()
    arquivo = request.files["imagem"]
    dados_imagem = arquivo.read()
    mime_type = arquivo.mimetype or "image/jpeg"

    try:
        cards = gemini.gerar_flashcards(dados_imagem, mime_type, prompt)
        return jsonify({"cards": cards})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ------------------------------------------------------------
# Editor de Documento
# ------------------------------------------------------------
@app.route("/documento", methods=["POST"])
def documento():
    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada."}), 400

    prompt = request.form.get("prompt", "").strip()
    arquivo = request.files["imagem"]
    dados_imagem = arquivo.read()
    mime_type = arquivo.mimetype or "image/jpeg"

    try:
        texto = gemini.gerar_documento(dados_imagem, mime_type, prompt)
        return jsonify({"texto": texto})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ------------------------------------------------------------
# Leitor de Código
# ------------------------------------------------------------
@app.route("/codigo", methods=["POST"])
def codigo():
    codigo_original = request.form.get("codigo", "").strip()
    prompt = request.form.get("prompt", "").strip()

    if codigo_original:
        try:
            resultado = gemini.melhorar_codigo(codigo_original, prompt)
            return jsonify({"codigo_melhorado": resultado})
        except Exception as e:
            return jsonify({"erro": str(e)}), 500

    if "imagem" not in request.files:
        return jsonify({"erro": "Envie uma imagem ou um código."}), 400

    arquivo = request.files["imagem"]
    dados_imagem = arquivo.read()
    mime_type = arquivo.mimetype or "image/jpeg"

    try:
        resultado = gemini.ler_codigo(dados_imagem, mime_type, prompt)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ------------------------------------------------------------
# Tradutor de Libras
# ------------------------------------------------------------
@app.route("/libras", methods=["POST"])
def libras():
    if "video" not in request.files:
        return jsonify({"erro": "Nenhum vídeo enviado."}), 400

    prompt = request.form.get("prompt", "").strip()
    categoria = request.form.get("categoria", "").strip()
    categorias_validas = {
        "Abecedário",
        "Música",
        "Ação",
        "Escrever",
        "Saudações",
        "Números",
    }
    if categoria not in categorias_validas:
        categoria = ""

    arquivo = request.files["video"]
    dados_video = arquivo.read()
    mime_type = arquivo.mimetype or "video/mp4"

    try:
        traducao = gemini.traduzir_libras(dados_video, mime_type, prompt, categoria)
        return jsonify({"traducao": traducao})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ------------------------------------------------------------
#  Qr Code
# ------------------------------------------------------------
@app.route("/gerar_qr", methods=["POST"])
def gerar_qr():
    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada."}), 400
 
    arquivo = request.files["imagem"]
    dados_imagem = arquivo.read()
    nome_remoto = f"snap_{random.randint(10000, 99999)}.jpg"
 
    try:
        supabase.storage.from_("fotos").upload(nome_remoto, dados_imagem)
        link = supabase.storage.from_("fotos").get_public_url(nome_remoto)
 
        qr = segno.make(link, error="h")
        buffer = io.BytesIO()
        qr.save(buffer, kind="png", scale=8)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
 
        return jsonify({"link": link, "qr_base64": qr_base64})
 
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ------------------------------------------------------------
# Inicia o servidor na porta 5000
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
