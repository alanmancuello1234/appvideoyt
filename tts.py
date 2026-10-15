"""
tts.py
Genera la narración en audio. Usa edge-tts (voces de Microsoft Edge,
gratis, sin API key, sin límite de créditos). Si no hay salida a
internet disponible (por ejemplo corriendo en un sandbox restringido),
cae a un modo demo que genera silencio con la duración estimada,
solo para poder probar el ensamblado de video sin la voz real.
"""
import asyncio
import edge_tts
from moviepy import AudioClip
import numpy as np

VOZ_ESPANOL = "es-AR-TomasNeural"  # voz masculina rioplatense, gratis
DEMO_MODE = False  # se activa automáticamente si falla la conexión real


async def _generar_audio_real(texto: str, destino_mp3: str, voz: str = VOZ_ESPANOL):
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(destino_mp3)


def _estimar_duracion(texto: str) -> float:
    """~150 palabras por minuto de narración en español, ritmo normal."""
    palabras = len(texto.split())
    return max(1.5, (palabras / 150) * 60)


def narrar_escena(texto: str, destino_mp3: str, voz: str = VOZ_ESPANOL) -> float:
    """
    Genera el audio de la escena y devuelve su duración en segundos.
    Devuelve esa duración para que video_builder sepa cuánto debe
    durar el clip visual de esa escena.
    """
    global DEMO_MODE
    if not DEMO_MODE:
        try:
            asyncio.run(_generar_audio_real(texto, destino_mp3, voz))
            clip = AudioClip(lambda t: 0, duration=0.01)  # solo para no romper si hace falta
            from moviepy import AudioFileClip
            with AudioFileClip(destino_mp3) as audio:
                return audio.duration
        except Exception as e:
            print(f"[tts] Sin salida a internet para voz real ({e}). Paso a modo demo.")
            DEMO_MODE = True

    # --- Modo demo: silencio con la duración estimada, para probar el pipeline ---
    duracion = _estimar_duracion(texto)

    def make_frame(t):
        if np.isscalar(t):
            return np.array([0.0, 0.0])
        return np.zeros((len(t), 2))

    silencio = AudioClip(make_frame, duration=duracion, fps=24000)
    silencio.write_audiofile(destino_mp3, fps=24000, logger=None)
    return duracion
