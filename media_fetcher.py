"""
media_fetcher.py
Busca video/imagen de libre uso SOLO en Pexels y Pixabay — ambas con
licencia propia que permite uso comercial y monetización en YouTube
sin atribución obligatoria. A propósito no se agregan otras fuentes
(Openverse, Wikimedia, Internet Archive) porque mezclan licencias
CC-BY-NC / solo-atribución y rompen la garantía de "apto monetización".
"""
import os
import requests

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
PIXABAY_VIDEO_URL = "https://pixabay.com/api/videos/"


def search_pexels_video(query: str, per_page: int = 3) -> list[dict]:
    """Busca videos en Pexels. Requiere PEXELS_API_KEY (gratis en pexels.com/api)."""
    if not PEXELS_API_KEY:
        return []
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": per_page, "orientation": "landscape"}
    try:
        r = requests.get(PEXELS_VIDEO_URL, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        resultados = []
        for video in data.get("videos", []):
            # Elegimos el archivo de mejor calidad en HD, no 4K, para no gastar de más.
            archivos_hd = [f for f in video["video_files"] if f.get("quality") == "hd"]
            archivo = archivos_hd[0] if archivos_hd else video["video_files"][0]
            resultados.append({
                "fuente": "pexels",
                "url": archivo["link"],
                "duracion": video.get("duration", 0),
                "licencia": "Pexels License — uso comercial permitido, sin atribución",
            })
        return resultados
    except requests.RequestException as e:
        print(f"[media_fetcher] Error consultando Pexels: {e}")
        return []


def search_pixabay_video(query: str, per_page: int = 3) -> list[dict]:
    """Busca videos en Pixabay. Requiere PIXABAY_API_KEY (gratis en pixabay.com/api/docs)."""
    if not PIXABAY_API_KEY:
        return []
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "per_page": per_page,
        "video_type": "all",
    }
    try:
        r = requests.get(PIXABAY_VIDEO_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        resultados = []
        for hit in data.get("hits", []):
            archivo = hit["videos"].get("medium") or hit["videos"].get("small")
            resultados.append({
                "fuente": "pixabay",
                "url": archivo["url"],
                "duracion": hit.get("duration", 0),
                "licencia": "Pixabay License — uso comercial permitido, sin atribución",
            })
        return resultados
    except requests.RequestException as e:
        print(f"[media_fetcher] Error consultando Pixabay: {e}")
        return []


def find_clip_for_scene(keywords: list[str]) -> dict | None:
    """
    Prueba cada keyword (de la más específica a la más general) en Pexels
    primero y Pixabay como respaldo, hasta encontrar un clip.
    Devuelve None si no hay match (el video_builder debe tener un plan B).
    """
    for kw in keywords:
        resultados = search_pexels_video(kw) or search_pixabay_video(kw)
        if resultados:
            return resultados[0]
    return None


def download_file(url: str, destino: str) -> str:
    """Descarga el archivo de video a disco local para editarlo con moviepy."""
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()
    with open(destino, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return destino
