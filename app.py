# ============================================================
#  Este arquivo é o "servidor" da aplicação.
# ============================================================

import base64
from io import BytesIO
import random
import string
import qrcode
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
import gemini

load_dotenv()

app = Flask(__name__)
CORS(app)  # Conexao Frontend - servidor


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
# Qr Code
# ------------------------------------------------------------
@app.route("/gerar_qr", methods=["POST"])
def gerar_qr():
    # 1. Criamos um link fictício/estático local idêntico ao do seu mockup
    hash_aleatorio = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=6)
    )
    link_ficticio = f"https://snap.link/share/{hash_aleatorio}"

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(link_ficticio)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return jsonify({"link": link_ficticio, "qr_base64": img_str})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ------------------------------------------------------------
# Inicia o servidor na porta 5000
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)