#!/usr/bin/env bash

set -euo pipefail

VIDEO_CODECS_ORDER="av1 vp9 hevc h265 h264 x264 mpeg4 xvid divx vp8 mpeg2video"
AUDIO_CODECS_ORDER="flac eac3 ac3 dts aac opus mp3 vorbis pcm_s16le"

usage() {
  cat <<'EOF'
Uso:
  ./mvsm.sh <video>
  ./mvsm.sh <video1> <video2>

Descripción:
  Con 1 archivo muestra características técnicas del vídeo.
  Con 2 archivos compara ambos e indica cuál parece mejor técnicamente.
EOF
}

require_bin() {
  local bin="$1"
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "Error: no se encontró '$bin' en el PATH." >&2
    exit 1
  fi
}

file_exists() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "Error: el fichero no existe o no es un archivo regular: $file" >&2
    exit 1
  fi
}

ffprobe_format() {
  local file="$1"
  local key="$2"
  ffprobe -v error -show_entries "format=${key}" -of default=noprint_wrappers=1:nokey=1 "$file" | head -n 1
}

ffprobe_stream() {
  local file="$1"
  local selector="$2"
  local key="$3"
  ffprobe -v error -select_streams "$selector" -show_entries "stream=${key}" -of default=noprint_wrappers=1:nokey=1 "$file" | head -n 1
}

safe_value() {
  local value="${1:-}"
  if [[ -z "$value" || "$value" == "N/A" ]]; then
    echo "unknown"
  else
    echo "$value"
  fi
}

normalize_number() {
  local value="${1:-unknown}"
  if [[ "$value" == "unknown" ]]; then
    echo "0"
  else
    echo "$value"
  fi
}

estimate_video_bit_rate() {
  local total_bit_rate="$1"
  local audio_bit_rate="$2"

  total_bit_rate="$(normalize_number "$total_bit_rate")"
  audio_bit_rate="$(normalize_number "$audio_bit_rate")"

  awk -v total="$total_bit_rate" -v audio="$audio_bit_rate" '
    BEGIN {
      estimated = total - audio
      if (estimated < 0) {
        estimated = 0
      }
      printf "%.0f", estimated
    }
  '
}

fps_to_decimal() {
  local raw="$1"
  if [[ -z "$raw" || "$raw" == "unknown" || "$raw" == "0/0" ]]; then
    echo "0"
    return
  fi

  awk -v value="$raw" '
    BEGIN {
      split(value, p, "/")
      if (length(p) == 2 && p[2] != 0) {
        printf "%.3f", p[1] / p[2]
      } else {
        printf "%.3f", value
      }
    }
  '
}

codec_rank() {
  local codec="$1"
  local list="$2"
  local rank=0
  local index=100

  for item in $list; do
    if [[ "$codec" == "$item" ]]; then
      rank="$index"
      break
    fi
    index=$((index - 7))
  done

  if (( rank < 0 )); then
    rank=0
  fi

  echo "$rank"
}

gather_video_info() {
  local file="$1"
  local prefix="$2"

  local filename duration size bit_rate
  local width height video_codec video_bit_rate video_pix_fmt fps_raw fps
  local audio_codec audio_bit_rate audio_channels audio_sample_rate

  filename="$file"
  duration="$(safe_value "$(ffprobe_format "$file" duration)")"
  size="$(safe_value "$(ffprobe_format "$file" size)")"
  bit_rate="$(safe_value "$(ffprobe_format "$file" bit_rate)")"

  width="$(safe_value "$(ffprobe_stream "$file" v:0 width)")"
  height="$(safe_value "$(ffprobe_stream "$file" v:0 height)")"
  video_codec="$(safe_value "$(ffprobe_stream "$file" v:0 codec_name)")"
  video_bit_rate="$(safe_value "$(ffprobe_stream "$file" v:0 bit_rate)")"
  video_pix_fmt="$(safe_value "$(ffprobe_stream "$file" v:0 pix_fmt)")"
  fps_raw="$(safe_value "$(ffprobe_stream "$file" v:0 avg_frame_rate)")"
  fps="$(fps_to_decimal "$fps_raw")"

  audio_codec="$(safe_value "$(ffprobe_stream "$file" a:0 codec_name)")"
  audio_bit_rate="$(safe_value "$(ffprobe_stream "$file" a:0 bit_rate)")"
  audio_channels="$(safe_value "$(ffprobe_stream "$file" a:0 channels)")"
  audio_sample_rate="$(safe_value "$(ffprobe_stream "$file" a:0 sample_rate)")"

  if [[ "$video_bit_rate" == "unknown" && "$bit_rate" != "unknown" ]]; then
    video_bit_rate="$(estimate_video_bit_rate "$bit_rate" "$audio_bit_rate")"
  fi

  printf -v "${prefix}_file" '%s' "$filename"
  printf -v "${prefix}_duration" '%s' "$duration"
  printf -v "${prefix}_size" '%s' "$size"
  printf -v "${prefix}_bit_rate" '%s' "$bit_rate"
  printf -v "${prefix}_width" '%s' "$width"
  printf -v "${prefix}_height" '%s' "$height"
  printf -v "${prefix}_video_codec" '%s' "$video_codec"
  printf -v "${prefix}_video_bit_rate" '%s' "$video_bit_rate"
  printf -v "${prefix}_video_pix_fmt" '%s' "$video_pix_fmt"
  printf -v "${prefix}_fps" '%s' "$fps"
  printf -v "${prefix}_audio_codec" '%s' "$audio_codec"
  printf -v "${prefix}_audio_bit_rate" '%s' "$audio_bit_rate"
  printf -v "${prefix}_audio_channels" '%s' "$audio_channels"
  printf -v "${prefix}_audio_sample_rate" '%s' "$audio_sample_rate"
}

format_bytes() {
  local bytes="$1"
  if [[ "$bytes" == "unknown" ]]; then
    echo "unknown"
    return
  fi

  awk -v b="$bytes" '
    BEGIN {
      split("B KB MB GB TB", u, " ")
      i = 1
      while (b >= 1024 && i < 5) {
        b /= 1024
        i++
      }
      printf "%.2f %s", b, u[i]
    }
  '
}

format_duration() {
  local seconds="$1"
  if [[ "$seconds" == "unknown" ]]; then
    echo "unknown"
    return
  fi

  awk -v s="$seconds" '
    BEGIN {
      total = int(s)
      h = int(total / 3600)
      m = int((total % 3600) / 60)
      sec = total % 60
      printf "%02d:%02d:%02d", h, m, sec
    }
  '
}

durations_are_similar() {
  local left="$1"
  local right="$2"

  left="$(normalize_number "$left")"
  right="$(normalize_number "$right")"

  awk -v l="$left" -v r="$right" '
    BEGIN {
      if (l == 0 || r == 0) {
        exit 1
      }

      diff = l - r
      if (diff < 0) {
        diff = -diff
      }

      base = l < r ? l : r
      ratio = diff / base
      exit !(ratio <= 0.05)
    }
  '
}

codec_efficiency_factor() {
  local codec="$1"

  case "$codec" in
    av1) echo "2.0" ;;
    vp9) echo "1.7" ;;
    hevc|h265) echo "1.6" ;;
    h264|x264) echo "1.0" ;;
    mpeg4|xvid|divx) echo "0.7" ;;
    vp8) echo "0.8" ;;
    mpeg2video) echo "0.6" ;;
    *) echo "1.0" ;;
  esac
}

compression_efficiency_score() {
  local prefix="$1"

  local video_bit_rate_var="${prefix}_video_bit_rate"
  local video_codec_var="${prefix}_video_codec"

  local video_bit_rate video_codec factor

  video_bit_rate="$(normalize_number "${!video_bit_rate_var}")"
  video_codec="${!video_codec_var}"
  factor="$(codec_efficiency_factor "$video_codec")"

  awk -v video_bit_rate="$video_bit_rate" -v factor="$factor" '
    BEGIN {
      if (video_bit_rate <= 0 || factor <= 0) {
        printf "0"
        exit
      }

      score = factor / video_bit_rate
      printf "%.10f", score
    }
  '
}

print_efficiency_note() {
  local technical_score_a="$1"
  local technical_score_b="$2"
  local size_a="$3"
  local size_b="$4"
  local duration_a="$5"
  local duration_b="$6"
  local efficiency_a="$7"
  local efficiency_b="$8"

  if ! durations_are_similar "$duration_a" "$duration_b"; then
    return
  fi

  size_a="$(normalize_number "$size_a")"
  size_b="$(normalize_number "$size_b")"

  awk \
    -v ta="$technical_score_a" \
    -v tb="$technical_score_b" \
    -v sa="$size_a" \
    -v sb="$size_b" \
    -v ea="$efficiency_a" \
    -v eb="$efficiency_b" '
    BEGIN {
      if (ta <= 0 || tb <= 0 || sa <= 0 || sb <= 0 || ea <= 0 || eb <= 0) {
        exit 1
      }

      quality_gap = ta > tb ? ta / tb : tb / ta
      size_gap = sa > sb ? sa / sb : sb / sa
      efficiency_gap = ea > eb ? ea / eb : eb / ea

      if (quality_gap <= 1.10 && size_gap >= 1.50 && efficiency_gap >= 1.20) {
        if (sa > sb && eb > ea) {
          printf "Eficiencia: Archivo 2 parece mejor optimizado; ofrece una calidad tecnica similar ocupando bastante menos espacio.\n"
        } else if (sb > sa && ea > eb) {
          printf "Eficiencia: Archivo 1 parece mejor optimizado; ofrece una calidad tecnica similar ocupando bastante menos espacio.\n"
        } else if (sa > sb) {
          printf "Eficiencia: Archivo 1 parece bastante menos optimizado; ocupa mucho mas para una calidad tecnica similar.\n"
        } else {
          printf "Eficiencia: Archivo 2 parece bastante menos optimizado; ocupa mucho mas para una calidad tecnica similar.\n"
        }
      }
    }
  '
}

print_info() {
  local prefix="$1"

  local file_var="${prefix}_file"
  local duration_var="${prefix}_duration"
  local size_var="${prefix}_size"
  local bit_rate_var="${prefix}_bit_rate"
  local width_var="${prefix}_width"
  local height_var="${prefix}_height"
  local video_codec_var="${prefix}_video_codec"
  local video_bit_rate_var="${prefix}_video_bit_rate"
  local video_pix_fmt_var="${prefix}_video_pix_fmt"
  local fps_var="${prefix}_fps"
  local audio_codec_var="${prefix}_audio_codec"
  local audio_bit_rate_var="${prefix}_audio_bit_rate"
  local audio_channels_var="${prefix}_audio_channels"
  local audio_sample_rate_var="${prefix}_audio_sample_rate"

  local file="${!file_var}"
  local duration="${!duration_var}"
  local size="${!size_var}"
  local bit_rate="${!bit_rate_var}"
  local width="${!width_var}"
  local height="${!height_var}"
  local video_codec="${!video_codec_var}"
  local video_bit_rate="${!video_bit_rate_var}"
  local video_pix_fmt="${!video_pix_fmt_var}"
  local fps="${!fps_var}"
  local audio_codec="${!audio_codec_var}"
  local audio_bit_rate="${!audio_bit_rate_var}"
  local audio_channels="${!audio_channels_var}"
  local audio_sample_rate="${!audio_sample_rate_var}"

  cat <<EOF
Ruta: $file
Duración: $(format_duration "$duration")
Tamaño: $(format_bytes "$size")
Bitrate total: $bit_rate bps
Resolución: ${width}x${height}
Codec vídeo: $video_codec
Bitrate vídeo: $video_bit_rate bps
Formato de píxel: $video_pix_fmt
FPS: $fps
Codec audio: $audio_codec
Bitrate audio: $audio_bit_rate bps
Canales audio: $audio_channels
Frecuencia audio: $audio_sample_rate Hz
EOF
}

print_score_summary() {
  local prefix="$1"

  local width_var="${prefix}_width"
  local height_var="${prefix}_height"
  local video_bit_rate_var="${prefix}_video_bit_rate"
  local fps_var="${prefix}_fps"
  local audio_channels_var="${prefix}_audio_channels"
  local audio_bit_rate_var="${prefix}_audio_bit_rate"
  local video_codec_var="${prefix}_video_codec"
  local audio_codec_var="${prefix}_audio_codec"

  local width height video_bit_rate fps audio_channels audio_bit_rate video_codec audio_codec
  local pixels video_rank audio_rank

  width="$(normalize_number "${!width_var}")"
  height="$(normalize_number "${!height_var}")"
  video_bit_rate="$(normalize_number "${!video_bit_rate_var}")"
  fps="$(normalize_number "${!fps_var}")"
  audio_channels="$(normalize_number "${!audio_channels_var}")"
  audio_bit_rate="$(normalize_number "${!audio_bit_rate_var}")"
  video_codec="${!video_codec_var}"
  audio_codec="${!audio_codec_var}"

  pixels=$((width * height))
  video_rank="$(codec_rank "$video_codec" "$VIDEO_CODECS_ORDER")"
  audio_rank="$(codec_rank "$audio_codec" "$AUDIO_CODECS_ORDER")"

  awk \
    -v pixels="$pixels" \
    -v video_bit_rate="$video_bit_rate" \
    -v fps="$fps" \
    -v audio_channels="$audio_channels" \
    -v audio_bit_rate="$audio_bit_rate" \
    -v video_rank="$video_rank" \
    -v audio_rank="$audio_rank" '
    BEGIN {
      printf "Resumen puntuacion:\n"
      printf "- resolucion: %.2f\n", pixels / 1000
      printf "- bitrate_video: %.2f\n", video_bit_rate / 100000
      printf "- fps: %.2f\n", fps * 10
      printf "- canales_audio: %.2f\n", audio_channels * 50
      printf "- bitrate_audio: %.2f\n", audio_bit_rate / 10000
      printf "- codec_video: %.2f\n", video_rank * 3
      printf "- codec_audio: %.2f\n", audio_rank * 4
    }
  '
}

score_video() {
  local prefix="$1"

  local width_var="${prefix}_width"
  local height_var="${prefix}_height"
  local video_bit_rate_var="${prefix}_video_bit_rate"
  local fps_var="${prefix}_fps"
  local audio_channels_var="${prefix}_audio_channels"
  local audio_bit_rate_var="${prefix}_audio_bit_rate"
  local video_codec_var="${prefix}_video_codec"
  local audio_codec_var="${prefix}_audio_codec"

  local width height video_bit_rate fps audio_channels audio_bit_rate video_codec audio_codec
  local pixels video_rank audio_rank

  width="$(normalize_number "${!width_var}")"
  height="$(normalize_number "${!height_var}")"
  video_bit_rate="$(normalize_number "${!video_bit_rate_var}")"
  fps="$(normalize_number "${!fps_var}")"
  audio_channels="$(normalize_number "${!audio_channels_var}")"
  audio_bit_rate="$(normalize_number "${!audio_bit_rate_var}")"
  video_codec="${!video_codec_var}"
  audio_codec="${!audio_codec_var}"

  pixels=$((width * height))
  video_rank="$(codec_rank "$video_codec" "$VIDEO_CODECS_ORDER")"
  audio_rank="$(codec_rank "$audio_codec" "$AUDIO_CODECS_ORDER")"

  awk \
    -v pixels="$pixels" \
    -v video_bit_rate="$video_bit_rate" \
    -v fps="$fps" \
    -v audio_channels="$audio_channels" \
    -v audio_bit_rate="$audio_bit_rate" \
    -v video_rank="$video_rank" \
    -v audio_rank="$audio_rank" '
    BEGIN {
      score = 0
      score += pixels / 1000
      score += video_bit_rate / 100000
      score += fps * 10
      score += audio_channels * 50
      score += audio_bit_rate / 10000
      score += video_rank * 3
      score += audio_rank * 4
      printf "%.2f", score
    }
  '
}

append_reason_if_better() {
  local label="$1"
  local left="$2"
  local right="$3"
  local current="$4"

  if awk -v l="$left" -v r="$right" 'BEGIN { exit !(l > r) }'; then
    if [[ -n "$current" ]]; then
      current+=$'\n'
    fi
    current+="- $label"
  fi

  printf '%s' "$current"
}

compare_two() {
  local file1="$1"
  local file2="$2"

  gather_video_info "$file1" "a"
  gather_video_info "$file2" "b"

  echo "=== Archivo 1 ==="
  print_info "a"
  echo
  echo "=== Archivo 2 ==="
  print_info "b"
  echo

  local score_a score_b reasons_a reasons_b pixels_a pixels_b
  local efficiency_a efficiency_b
  score_a="$(score_video "a")"
  score_b="$(score_video "b")"
  efficiency_a="$(compression_efficiency_score "a")"
  efficiency_b="$(compression_efficiency_score "b")"
  reasons_a=""
  reasons_b=""
  pixels_a=$(( $(normalize_number "$a_width") * $(normalize_number "$a_height") ))
  pixels_b=$(( $(normalize_number "$b_width") * $(normalize_number "$b_height") ))

  reasons_a="$(append_reason_if_better "mayor resolución" "$pixels_a" "$pixels_b" "$reasons_a")"
  reasons_b="$(append_reason_if_better "mayor resolución" "$pixels_b" "$pixels_a" "$reasons_b")"

  reasons_a="$(append_reason_if_better "mayor bitrate de vídeo" "$(normalize_number "$a_video_bit_rate")" "$(normalize_number "$b_video_bit_rate")" "$reasons_a")"
  reasons_b="$(append_reason_if_better "mayor bitrate de vídeo" "$(normalize_number "$b_video_bit_rate")" "$(normalize_number "$a_video_bit_rate")" "$reasons_b")"

  reasons_a="$(append_reason_if_better "más FPS" "$(normalize_number "$a_fps")" "$(normalize_number "$b_fps")" "$reasons_a")"
  reasons_b="$(append_reason_if_better "más FPS" "$(normalize_number "$b_fps")" "$(normalize_number "$a_fps")" "$reasons_b")"

  reasons_a="$(append_reason_if_better "mejor audio técnico" "$(normalize_number "$a_audio_channels")" "$(normalize_number "$b_audio_channels")" "$reasons_a")"
  reasons_b="$(append_reason_if_better "mejor audio técnico" "$(normalize_number "$b_audio_channels")" "$(normalize_number "$a_audio_channels")" "$reasons_b")"

  echo "Puntuación archivo 1: $score_a"
  print_score_summary "a"
  echo
  echo "Puntuación archivo 2: $score_b"
  print_score_summary "b"
  echo

  if awk -v a="$score_a" -v b="$score_b" 'BEGIN { exit !(a > b) }'; then
    echo "Resultado: Archivo 1 parece mejor."
    if [[ -n "$reasons_a" ]]; then
      echo "Motivos:"
      printf '%s\n' "$reasons_a"
    fi
  elif awk -v a="$score_a" -v b="$score_b" 'BEGIN { exit !(b > a) }'; then
    echo "Resultado: Archivo 2 parece mejor."
    if [[ -n "$reasons_b" ]]; then
      echo "Motivos:"
      printf '%s\n' "$reasons_b"
    fi
  else
    echo "Resultado: Empate técnico aproximado."
  fi

  print_efficiency_note "$score_a" "$score_b" "$a_size" "$b_size" "$a_duration" "$b_duration" "$efficiency_a" "$efficiency_b"
}

inspect_one() {
  local file="$1"
  gather_video_info "$file" "single"
  print_info "single"
}

main() {
  require_bin "ffprobe"
  require_bin "awk"

  if [[ $# -lt 1 || $# -gt 2 ]]; then
    usage
    exit 1
  fi

  file_exists "$1"
  if [[ $# -eq 2 ]]; then
    file_exists "$2"
  fi

  if [[ $# -eq 1 ]]; then
    inspect_one "$1"
  else
    compare_two "$1" "$2"
  fi
}

main "$@"
