"""
parser.py
Parte el guión en "escenas" (bloques narrativos) y extrae palabras clave
de cada una para poder buscar el video/imagen que mejor matchea.
"""
import re
import yake


# Extractor de keywords: funciona 100% local, sin API ni créditos de IA.
_kw_extractor = yake.KeywordExtractor(lan="es", n=2, top=3, dedupLim=0.9)


def split_into_scenes(guion_texto: str) -> list[str]:
    """
    Parte el guión en bloques (escenas). Usa párrafos si existen;
    si el guión viene como texto corrido, parte por oraciones agrupadas
    de a 2 para que cada escena tenga suficiente contexto.
    """
    parrafos = [p.strip() for p in guion_texto.split("\n") if p.strip()]

    # Si ya viene en párrafos razonables (guión bien escrito), los usamos tal cual.
    if len(parrafos) > 1:
        return parrafos

    # Si vino todo en una sola línea, partimos por oraciones de a 2.
    oraciones = re.split(r"(?<=[.!?])\s+", guion_texto.strip())
    escenas = []
    for i in range(0, len(oraciones), 2):
        bloque = " ".join(oraciones[i:i + 2]).strip()
        if bloque:
            escenas.append(bloque)
    return escenas


def extract_keywords(escena_texto: str) -> list[str]:
    """Devuelve las 1-3 palabras/frases clave más relevantes de la escena."""
    keywords = _kw_extractor.extract_keywords(escena_texto)
    # yake devuelve (frase, score) donde menor score = más relevante
    keywords.sort(key=lambda x: x[1])
    return [kw for kw, score in keywords] or [escena_texto.split()[0]]


def build_scene_plan(guion_texto: str) -> list[dict]:
    """
    Devuelve la lista de escenas con su texto y sus keywords,
    lista para pasarle al buscador de medios.
    """
    escenas = split_into_scenes(guion_texto)
    plan = []
    for idx, escena in enumerate(escenas):
        plan.append({
            "id": idx,
            "texto": escena,
            "keywords": extract_keywords(escena),
        })
    return plan


if __name__ == "__main__":
    guion_demo = (
        "En 1453, el Imperio Bizantino vivía sus últimas horas.\n"
        "Las murallas de Constantinopla, que habían resistido mil años, "
        "comenzaban a ceder ante los cañones otomanos.\n"
        "El emperador Constantino XI sabía que no habría rendición posible."
    )
    for escena in build_scene_plan(guion_demo):
        print(escena)
