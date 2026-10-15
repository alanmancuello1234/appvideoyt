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
import subprocess
from moviepy import (
    VideoFileClip, ColorClip, TextClip, CompositeVideoClip,
    AudioFileClip, vfx,
)

from parser import build_scene_plan
from tts import narrar_escena
from media_fetcher import find_clip_for_scene, download_file

# 480p en vez de 720p: baja bastante el consumo de RAM/CPU durante el
# procesamiento, clave para entrar en el plan free de Render (poca RAM).
# Cuando pases a un plan pago con más memoria, se puede subir de nuevo.
RESOLUCION = (854, 480)
CARPETA_TEMP = "temp_assets"
# DejaVu Sans soporta ñ y tildes; sin especificar fuente, la que usa
# moviepy por defecto en el servidor no tiene esos caracteres cargados
# (salen como cuadraditos). Se instala vía apt en el Dockerfile.
FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _clip_de_respaldo(texto_escena: str, duracion: float):
    """Plan B visual cuando no hay match en los bancos de video. Ya
    incluye el texto grande centrado, así que NO hay que agregarle
    además el subtítulo de abajo (quedaría duplicado/superpuesto)."""
    fondo = ColorClip(size=RESOLUCION, color=(20, 20, 30), duration=duracion)
    texto = (
        TextClip(text=texto_escena, font=FUENTE, font_size=32, color="white",
                 size=(RESOLUCION[0] - 160, None), method="caption")
        .with_duration(duracion)
        .with_position("center")
    )
    return CompositeVideoClip([fondo, texto])


def _subtitulo(texto_escena: str, duracion: float):
    return (
        TextClip(text=texto_escena, font=FUENTE, font_size=24, color="white",
                 stroke_color="black", stroke_width=2,
                 size=(RESOLUCION[0] - 120, None), method="caption")
        .with_duration(duracion)
        .with_position(("center", "bottom"))
    )


def construir_escena(escena: dict, idx: int) -> str:
    """
    Arma UNA escena (audio + visual + subtítulo), la renderiza a su
    propio archivo .mp4, y cierra todos los clips para liberar RAM y
    los procesos de ffmpeg que moviepy abre por detrás. Devuelve la
    ruta del archivo ya renderizado, no el objeto en memoria.
    """
    os.makedirs(CARPETA_TEMP, exist_ok=True)
    audio_path = os.path.join(CARPETA_TEMP, f"escena_{idx}.mp3")
    duracion = narrar_escena(escena["texto"], audio_path)

    clip_info = find_clip_for_scene(escena["keywords"])
    clips_a_cerrar = []

    if clip_info:
        video_path = os.path.join(CARPETA_TEMP, f"escena_{idx}_src.mp4")
        download_file(clip_info["url"], video_path)
        base = VideoFileClip(video_path).without_audio()
        clips_a_cerrar.append(base)
        if base.duration < duracion:
            base = base.with_effects([vfx.Loop(duration=duracion)])
        else:
            base = base.subclipped(0, duracion)
        base = base.resized(RESOLUCION)
        fondo_visual = base
        licencia = clip_info["licencia"]
        capas = [fondo_visual, _subtitulo(escena["texto"], duracion)]
    else:
        # El plan B ya trae el texto completo centrado — agregar el
        # subtítulo de abajo acá duplicaría el texto en pantalla.
        fondo_visual = _clip_de_respaldo(escena["texto"], duracion)
        licencia = "sin match en banco — usado respaldo local (sin riesgo de licencia)"
        capas = [fondo_visual]

    audio_clip = AudioFileClip(audio_path)
    clips_a_cerrar.append(audio_clip)
    escena_final = CompositeVideoClip(capas).with_audio(audio_clip)

    salida_path = os.path.join(CARPETA_TEMP, f"escena_{idx}_render.mp4")
    escena_final.write_videofile(
        salida_path, fps=24, codec="libx264", audio_codec="aac",
        preset="ultrafast",  # prioriza RAM/CPU bajos por sobre peso del archivo
        logger=None,
    )

    # Cerrar todo explícitamente: moviepy deja procesos de ffmpeg y
    # buffers abiertos si no se cierran a mano, y eso es justo lo que
    # acumula memoria escena tras escena.
    escena_final.close()
    for c in clips_a_cerrar:
        c.close()

    print(f"  Escena {idx}: '{escena['texto'][:50]}...' | {duracion:.1f}s | {licencia}")
    return salida_path


def _concatenar_archivos(rutas: list[str], salida_mp4: str):
    """
    Concatena los .mp4 ya renderizados con el demuxer de ffmpeg
    (copia los streams, no vuelve a decodificar/codificar) — mucho
    más liviano en memoria que recargar todo en moviepy de nuevo.
    """
    lista_path = os.path.join(CARPETA_TEMP, "lista_concat.txt")
    with open(lista_path, "w", encoding="utf-8") as f:
        for ruta in rutas:
            f.write(f"file '{os.path.abspath(ruta)}'\n")

    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", lista_path, "-c", "copy", salida_mp4],
        check=True, capture_output=True,
    )


def generar_video(guion_texto: str, salida_mp4: str = "video_final.mp4"):
    plan = build_scene_plan(guion_texto)
    print(f"Guión partido en {len(plan)} escenas. Generando...\n")

    rutas_escenas = [construir_escena(escena, idx) for idx, escena in enumerate(plan)]
    _concatenar_archivos(rutas_escenas, salida_mp4)

    print(f"\n✅ Video generado: {salida_mp4}")
    return salida_mp4
