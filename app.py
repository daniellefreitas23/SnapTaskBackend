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
CORS(app)  # Conexao Frontend - servidor

# ------------------------------------------------------------
# Configurações da API
# ------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------------------
#  Flashcards
# ------------------------------------------------------------
@app.route("/flashcards", methods=["POST"])
def flashcards():
    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada."}), 400

    arquivo = request.files["imagem"]
    dados_imagem = arquivo.read()
    mime_type = arquivo.mimetype or "image/jpeg"

    try:
        cards = gemini.gerar_flashcards(dados_imagem, mime_type)
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

    arquivo = request.files["imagem"]
    dados_imagem = arquivo.read()
    mime_type = arquivo.mimetype or "image/jpeg"

    try:
        texto = gemini.gerar_documento(dados_imagem, mime_type)
        return jsonify({"texto": texto})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ------------------------------------------------------------
# Leitor de Código
# ------------------------------------------------------------
@app.route("/codigo", methods=["POST"])
def codigo():
    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada."}), 400

    arquivo = request.files["imagem"]
    dados_imagem = arquivo.read()
    mime_type = arquivo.mimetype or "image/jpeg"

    try:
        resultado = gemini.ler_codigo(dados_imagem, mime_type)
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

    arquivo = request.files["video"]
    dados_video = arquivo.read()
    mime_type = arquivo.mimetype or "video/mp4"

    try:
        traducao = gemini.traduzir_libras(dados_video, mime_type)
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
