"""
video_builder.py
Toma el plan de escenas (texto + keywords), busca el clip de cada una
(Pexels/Pixabay), lo recorta a la duración exacta del audio narrado,
le pega subtítulos quemados, y concatena todo en el video final.

Si no se encuentra clip real para una escena (sin API key configurada,
sin internet, o sin match), usa un clip de "respaldo" (color sólido +
el texto de la escena) para que el video nunca quede roto — exactamente
el plan B que mencioné antes para cuando el banco no tiene match exacto.
"""
import os
from moviepy import (
    VideoFileClip, ColorClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, AudioFileClip, vfx,
)

from parser import build_scene_plan
from tts import narrar_escena
from media_fetcher import find_clip_for_scene, download_file

RESOLUCION = (1280, 720)
CARPETA_TEMP = "temp_assets"


def _clip_de_respaldo(texto_escena: str, duracion: float):
    """Plan B visual cuando no hay match en los bancos de video."""
    fondo = ColorClip(size=RESOLUCION, color=(20, 20, 30), duration=duracion)
    texto = (
        TextClip(text=texto_escena, font_size=36, color="white",
                 size=(RESOLUCION[0] - 160, None), method="caption")
        .with_duration(duracion)
        .with_position("center")
    )
    return CompositeVideoClip([fondo, texto])


def _subtitulo(texto_escena: str, duracion: float):
    return (
        TextClip(text=texto_escena, font_size=28, color="white",
                 stroke_color="black", stroke_width=2,
                 size=(RESOLUCION[0] - 120, None), method="caption")
        .with_duration(duracion)
        .with_position(("center", "bottom"))
    )


def construir_escena(escena: dict, idx: int):
    """Arma UNA escena: audio narrado + clip visual + subtítulo quemado."""
    os.makedirs(CARPETA_TEMP, exist_ok=True)
    audio_path = os.path.join(CARPETA_TEMP, f"escena_{idx}.mp3")
    duracion = narrar_escena(escena["texto"], audio_path)

    clip_info = find_clip_for_scene(escena["keywords"])

    if clip_info:
        video_path = os.path.join(CARPETA_TEMP, f"escena_{idx}.mp4")
        download_file(clip_info["url"], video_path)
        base = VideoFileClip(video_path).without_audio()
        # Si el clip de stock es más corto que el audio, lo loopeamos;
        # si es más largo, lo recortamos. Nunca queda desincronizado.
        if base.duration < duracion:
            base = base.with_effects([vfx.Loop(duration=duracion)])
        else:
            base = base.subclipped(0, duracion)
        base = base.resized(RESOLUCION)
        fondo_visual = base
        licencia = clip_info["licencia"]
    else:
        fondo_visual = _clip_de_respaldo(escena["texto"], duracion)
        licencia = "sin match en banco — usado respaldo local (sin riesgo de licencia)"

    sub = _subtitulo(escena["texto"], duracion)
    escena_final = CompositeVideoClip([fondo_visual, sub]).with_audio(
        AudioFileClip(audio_path)
    )
    print(f"  Escena {idx}: '{escena['texto'][:50]}...' | {duracion:.1f}s | {licencia}")
    return escena_final


def generar_video(guion_texto: str, salida_mp4: str = "video_final.mp4"):
    plan = build_scene_plan(guion_texto)
    print(f"Guión partido en {len(plan)} escenas. Generando...\n")

    clips = [construir_escena(escena, idx) for idx, escena in enumerate(plan)]
    video_final = concatenate_videoclips(clips, method="compose")
    video_final.write_videofile(salida_mp4, fps=24, codec="libx264",
                                 audio_codec="aac", logger=None)
    print(f"\n✅ Video generado: {salida_mp4} ({video_final.duration:.1f}s totales)")
    return salida_mp4
