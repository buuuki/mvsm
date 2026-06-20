# mvsm

Script de `bash` para inspeccionar archivos de vídeo (`avi`, `mkv`, `mp4`, `mov`, etc.) y ver las características técnicas de un fichero, o comparar dos si quieres estimar cuál tiene mejor calidad técnica.

## Qué hace

- Con 1 fichero:
  - muestra resolución
  - muestra codecs de vídeo y audio
  - muestra bitrate, FPS, duración y tamaño
  - muestra canales de audio y frecuencia de muestreo
- Con 2 ficheros:
  - muestra la información de ambos
  - muestra un resumen de puntuaciones por criterio para cada archivo
  - calcula una puntuación técnica aproximada
  - indica cuál parece mejor y por qué

## Requisitos

- `bash`
- `ffprobe` de FFmpeg
- `awk`
- Opcional para la interfaz gráfica Qt6: `python3` y `PySide6`

En Debian/Ubuntu:

```bash
sudo apt update
sudo apt install ffmpeg
```

En macOS con Homebrew:

```bash
brew install ffmpeg
```

Para la interfaz gráfica en Ubuntu 24.04:

```bash
sudo apt install python3.12-venv
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

## Uso

Dar permisos de ejecución:

```bash
chmod +x ./mvsm.sh
```

Inspeccionar un vídeo:

```bash
./mvsm.sh pelicula.mkv
```

Comparar dos vídeos, opcionalmente:

```bash
./mvsm.sh version1.mkv version2.mp4
```

Abrir la interfaz gráfica Qt6:

```bash
. .venv/bin/activate
python mvsm.py
```

La ventana permite seleccionar un fichero con el botón `Buscar...` o arrastrarlo sobre la aplicación para ver sus características, o añadir un segundo fichero opcional para compararlos. La ayuda y los formatos soportados aparecen encima de las rutas, y los botones `Analizar` y `Limpiar` quedan justo debajo. La información del primer archivo aparece a la izquierda y la del segundo a la derecha; en la vista comparativa se muestra solo el nombre del fichero, no la ruta completa. Duración, tamaño, bitrate, resolución y puntuación se muestran una sola vez en una zona compacta de métricas principales. El ganador muestra una pequeña animación de trofeo/medalla, y el resultado aparece debajo de ambos vídeos con una lectura rápida que indica si la ventaja es ligera, notable, clara, si dobla o si triplica en métricas importantes. La salida completa del script queda en un panel de debug inferior redimensionable.

## Instalar lanzador de escritorio

El logo optimizado está en `assets/icons/` en tamaños estándar para escritorio y dock. Para instalar la app en tu usuario:

```bash
./install_desktop.sh
```

El instalador crea:

- `~/.local/bin/mvsm` como comando de lanzamiento
- `~/.local/share/applications/mvsm.desktop`
- iconos hicolor en `~/.local/share/icons/hicolor/` y un PNG directo en `~/.local/share/icons/mvsm.png`
- una copia del lanzador en `~/Escritorio` o `~/Desktop` si existe

Después podrás buscar "mvsm" en el lanzador de aplicaciones y anclarlo a la dock.

## Cómo decide cuál es mejor

La comparación es heurística. El script puntúa principalmente:

- resolución total
- bitrate de vídeo
- FPS
- codec de vídeo
- codec de audio
- número de canales de audio
- bitrate de audio

Ponderación actual de la puntuación:

- `resolucion = (ancho * alto) / 1000`
- `bitrate_video = bitrate_video_bps / 100000`
- `fps = fps * 10`
- `canales_audio = canales * 50`
- `bitrate_audio = bitrate_audio_bps / 10000`
- `codec_video = ranking_codec_video * 3`
- `codec_audio = ranking_codec_audio * 4`

Puntuación total:

```text
total = resolucion
      + bitrate_video
      + fps
      + canales_audio
      + bitrate_audio
      + codec_video
      + codec_audio
```

Si `ffprobe` no informa del bitrate del stream de vídeo, el script estima:

```text
bitrate_video_estimado = bitrate_total - bitrate_audio
```

Además, al comparar dos vídeos el script puede añadir una nota separada de eficiencia si:

- las duraciones son muy parecidas
- la puntuación técnica total es similar
- uno de los ficheros ocupa bastante menos espacio

Esa nota no cambia el ganador técnico principal; solo indica cuál parece mejor optimizado en relación calidad/espacio.

No evalúa calidad visual real cuadro a cuadro. Por tanto:

- una codificación más eficiente puede verse mejor con menos bitrate
- un remux puede ganar aunque el origen visual sea igual
- no detecta filtros, grano, compresión subjetiva ni HDR con precisión completa

La salida debe interpretarse como una ayuda técnica rápida, no como una verdad absoluta.

## Estructura

```text
.
├── README.md
├── .gitignore
├── requirements.txt
├── mvsm.py
└── mvsm.sh
```

## Ejemplo de salida

```text
$ ./mvsm.sh a.mkv b.mp4

=== Archivo 1 ===
Ruta: a.mkv
Resolución: 1920x1080
Codec vídeo: h264
Codec audio: aac
Bitrate vídeo: 4200000 bps

=== Archivo 2 ===
Ruta: b.mp4
Resolución: 1280x720
Codec vídeo: hevc
Codec audio: aac
Bitrate vídeo: 1800000 bps

Resultado: Archivo 1 parece mejor.
Motivos:
- mayor resolución
- mayor bitrate de vídeo

Puntuación archivo 1: 2750.27
Resumen puntuacion:
- resolucion: 1543.68
- bitrate_video: 58.03
- fps: 239.76
- canales_audio: 300.00
- bitrate_audio: 76.80
- codec_video: 216.00
- codec_audio: 316.00

Puntuación archivo 2: 2738.03
Resumen puntuacion:
- resolucion: 1536.00
- bitrate_video: 21.87
- fps: 239.76
- canales_audio: 300.00
- bitrate_audio: 38.40
- codec_video: 258.00
- codec_audio: 344.00

Eficiencia: Archivo 2 parece mejor optimizado; ofrece una calidad tecnica similar ocupando bastante menos espacio.
```

## GitHub

Proyecto preparado para subirse a GitHub como repositorio simple. El repositorio incluye `.gitignore` para no publicar `.venv/`, `__pycache__/`, builds, logs, `.env` ni claves locales.

Antes del primer commit puedes revisar el contenido con:

```bash
git status --short
```


Pasos típicos:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <URL_DEL_REPO>
git push -u origin main
```

## Mejoras futuras

- salida JSON
- comparación de subtítulos
- detección de HDR / profundidad de color
- comparación por SSIM o VMAF usando FFmpeg
- tests automáticos con muestras de vídeo
