# guion2video — versión web

App web (backend Flask + página mobile-friendly) para generar videos
desde un guión, usable desde el navegador del celular una vez desplegada.

## Por qué necesita servidor propio

Una página "pura" (sin servidor) no puede pegarle directo a las APIs de
Pexels/Pixabay por las políticas de seguridad del navegador y de donde
se aloje. Por eso esto es un **servidor chiquito** que vos alojás gratis,
y la página del celular solo le habla a tu servidor.

## Deploy gratis en Render (recomendado, ~10 min)

1. Creá un repo en GitHub y subí **todos los archivos de esta carpeta**
   (`app.py`, `video_builder.py`, `parser.py`, `media_fetcher.py`, `tts.py`,
   `templates/index.html`, `requirements.txt`, `Dockerfile`).

2. Entrá a https://render.com → **New +** → **Web Service** → conectá tu repo de GitHub.

3. Render va a detectar el `Dockerfile` solo. Dejá todo por defecto y elegí el plan **Free**.

4. Click en **Create Web Service**. Esperá el build (~3-5 min la primera vez).

5. Cuando termine, Render te da una URL tipo `https://tu-app.onrender.com`.
   Esa es tu app — abrila desde el navegador del celular y listo.

## Uso desde el celular

1. Abrís la URL de Render en Chrome/Safari.
2. Pegás tu Pexels API key y tu Pixabay API key (quedan guardadas solo
   en ese navegador, en `localStorage` — no se mandan a ningún lado más
   que a tu propio servidor).
3. Pegás el guión.
4. Tocás "Generar video" y esperás.
5. Te aparece el botón de descarga cuando termina.

## Limitaciones a tener en cuenta

- **Plan Free de Render "duerme"** el servidor si no se usa por un
  rato — el primer request después de estar inactivo tarda ~30-50s
  extra en levantar. Es normal, no es que se rompió.
- **Videos largos (8+ min) pueden tardar varios minutos en generarse**
  y, en el plan gratis, el servidor tiene recursos limitados (CPU/RAM
  compartida) — anda bien para probar, pero si lo usás todos los días
  en serio capaz conviene pasar al plan pago más barato de Render
  (unos USD 7/mes) para que no se duerma y sea más rápido.
- Esta primera versión genera el video de forma síncrona (la página
  espera a que termine). Para guiones muy largos, si el request tarda
  demasiado y da timeout, avisame y lo pasamos a un sistema de cola
  (generás, te vas, volvés y lo descargás) que es más robusto.
