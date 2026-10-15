"""
app.py
Backend web que envuelve el pipeline guion2video. Corre en un servidor
propio (no en Claude), así que no tiene las restricciones de red de
una página publicada: puede pegarle directo a Pexels, Pixabay y al
servicio de voz.
"""
import os
import uuid
from flask import Flask, request, send_file, jsonify, render_template

from video_builder import generar_video

app = Flask(__name__)
CARPETA_SALIDA = "generados"
os.makedirs(CARPETA_SALIDA, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generar", methods=["POST"])
def generar():
    data = request.get_json(force=True)
    guion = (data.get("guion") or "").strip()
    pexels_key = data.get("pexels_key") or ""
    pixabay_key = data.get("pixabay_key") or ""

    if not guion:
        return jsonify({"error": "El guión está vacío."}), 400

    # Las keys viajan en cada request, no se guardan en el servidor.
    os.environ["PEXELS_API_KEY"] = pexels_key
    os.environ["PIXABAY_API_KEY"] = pixabay_key

    job_id = uuid.uuid4().hex[:10]
    salida = os.path.join(CARPETA_SALIDA, f"{job_id}.mp4")

    try:
        generar_video(guion, salida)
    except Exception as e:
        return jsonify({"error": f"Falló la generación: {e}"}), 500

    return jsonify({"ok": True, "job_id": job_id})


@app.route("/descargar/<job_id>")
def descargar(job_id):
    path = os.path.join(CARPETA_SALIDA, f"{job_id}.mp4")
    if not os.path.isfile(path):
        return jsonify({"error": "Video no encontrado (¿ya se generó?)"}), 404
    return send_file(path, as_attachment=True, download_name="mi_video.mp4")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
