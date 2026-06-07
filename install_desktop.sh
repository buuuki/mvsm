#!/usr/bin/env bash

set -euo pipefail

APP_ID="mvsm"
APP_NAME="mvsm"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_DIR="${HOME}/.local/bin"
WRAPPER_PATH="${WRAPPER_DIR}/${APP_ID}"
APPLICATIONS_DIR="${XDG_DATA_HOME:-${HOME}/.local/share}/applications"
ICONS_BASE_DIR="${XDG_DATA_HOME:-${HOME}/.local/share}/icons/hicolor"
DESKTOP_FILE="${APPLICATIONS_DIR}/${APP_ID}.desktop"
ABSOLUTE_ICON_FILE="${XDG_DATA_HOME:-${HOME}/.local/share}/icons/${APP_ID}.png"
SOURCE_ICON_DIR="${APP_DIR}/assets/icons"
LEGACY_APP_ID="video-compare"
LEGACY_DESKTOP_FILE="${APPLICATIONS_DIR}/${LEGACY_APP_ID}.desktop"
LEGACY_WRAPPER_PATH="${WRAPPER_DIR}/${LEGACY_APP_ID}"

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Error: no se encontro ${path}" >&2
    exit 1
  fi
}

desktop_dir() {
  if command -v xdg-user-dir >/dev/null 2>&1; then
    local configured
    configured="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
    if [[ -n "$configured" && -d "$configured" ]]; then
      echo "$configured"
      return
    fi
  fi

  if [[ -d "${HOME}/Escritorio" ]]; then
    echo "${HOME}/Escritorio"
  elif [[ -d "${HOME}/Desktop" ]]; then
    echo "${HOME}/Desktop"
  fi
}

require_file "${APP_DIR}/mvsm.py"
require_file "${APP_DIR}/mvsm.sh"
require_file "${SOURCE_ICON_DIR}/${APP_ID}-512.png"

mkdir -p "$WRAPPER_DIR" "$APPLICATIONS_DIR"

cat >"$WRAPPER_PATH" <<WRAPPER
#!/usr/bin/env bash
set -euo pipefail
cd "${APP_DIR}"
if [[ -x "${APP_DIR}/.venv/bin/python" ]]; then
  exec -a "${APP_ID}" "${APP_DIR}/.venv/bin/python" "${APP_DIR}/mvsm.py" "\$@"
fi
exec -a "${APP_ID}" python3 "${APP_DIR}/mvsm.py" "\$@"
WRAPPER
chmod +x "$WRAPPER_PATH"

for size in 16 24 32 48 64 128 256 512 1024; do
  source_icon="${SOURCE_ICON_DIR}/${APP_ID}-${size}.png"
  if [[ -f "$source_icon" ]]; then
    target_dir="${ICONS_BASE_DIR}/${size}x${size}/apps"
    mkdir -p "$target_dir"
    install -m 0644 "$source_icon" "${target_dir}/${APP_ID}.png"
  fi
done
install -m 0644 "${SOURCE_ICON_DIR}/${APP_ID}-512.png" "$ABSOLUTE_ICON_FILE"

cat >"$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Version=1.0
Name=${APP_NAME}
Comment=Comparar tecnicamente dos archivos de video
Exec=${WRAPPER_PATH} %F
Icon=${ABSOLUTE_ICON_FILE}
Terminal=false
Categories=AudioVideo;Video;
StartupNotify=true
StartupWMClass=${APP_ID}
MimeType=video/mp4;video/x-matroska;video/x-msvideo;video/quicktime;video/webm;
DESKTOP
chmod +x "$DESKTOP_FILE"

if desktop_path="$(desktop_dir)"; then
  desktop_launcher="${desktop_path}/${APP_NAME}.desktop"
  cp "$DESKTOP_FILE" "$desktop_launcher"
  chmod +x "$desktop_launcher"
  if command -v gio >/dev/null 2>&1; then
    gio set "$desktop_launcher" metadata::trusted true >/dev/null 2>&1 || true
  fi
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "$ICONS_BASE_DIR" >/dev/null 2>&1 || true
fi

rm -f "$LEGACY_DESKTOP_FILE" "$LEGACY_WRAPPER_PATH"
rm -f "${XDG_DATA_HOME:-${HOME}/.local/share}/icons/${LEGACY_APP_ID}.png"
for size in 16 24 32 48 64 128 256 512 1024; do
  rm -f "${ICONS_BASE_DIR}/${size}x${size}/apps/${LEGACY_APP_ID}.png"
done
if legacy_desktop_path="$(desktop_dir)"; then
  rm -f "${legacy_desktop_path}/Video Compare.desktop"
fi

echo "Instalado ${APP_NAME}."
echo "Comando: ${WRAPPER_PATH}"
echo "Lanzador: ${DESKTOP_FILE}"
