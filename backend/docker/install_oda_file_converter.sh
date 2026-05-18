#!/usr/bin/env bash
# Install ODA File Converter (Linux x86_64 .deb) for DWG export in Docker / Render builds.
# The .deb is not redistributed in this repo; obtain it from Open Design Alliance and either:
#   - set DWG_ODA_DEB_URL to a direct HTTPS URL to the .deb (Render / CI), or
#   - place docker/oda-file-converter.deb in the build context (Docker local build).
#
# Usage:
#   install_oda_file_converter.sh from-url <https://.../file.deb>
#   install_oda_file_converter.sh from-file </path/to/file.deb>

set -euo pipefail

_symlink_libxcb_util() {
  local d=/usr/lib/x86_64-linux-gnu
  if [[ -d "$d" && -f "$d/libxcb-util.so.1" ]] && [[ ! -e "$d/libxcb-util.so.0" ]]; then
    ln -sf "$d/libxcb-util.so.1" "$d/libxcb-util.so.0"
    echo "Created libxcb-util.so.0 symlink for ODA/Qt compatibility."
  fi
}

_install_prereqs() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends \
    ca-certificates wget \
    libxcb-util1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxkbcommon-x11-0 \
    libqt6gui6
}

_install_qt_headless_into_oda() {
  local sys_platforms="/usr/lib/x86_64-linux-gnu/qt6/plugins/platforms"
  local oda_platforms
  oda_platforms="$(find /usr -path '*/ODAFileConverter_*/plugins/platforms' -type d 2>/dev/null | head -1 || true)"
  if [[ -z "$oda_platforms" || ! -d "$sys_platforms" ]]; then
    return 0
  fi
  local p
  for p in libqoffscreen.so libqminimal.so; do
    if [[ -f "$sys_platforms/$p" && ! -f "$oda_platforms/$p" ]]; then
      cp "$sys_platforms/$p" "$oda_platforms/"
      echo "ODA: copied $p into $oda_platforms"
    fi
  done
}

_from_file() {
  local deb="$1"
  if [[ ! -f "$deb" ]]; then
    echo "ERROR: deb not found: $deb" >&2
    exit 1
  fi
  _install_prereqs
  dpkg -i "$deb" || apt-get install -yf
  _symlink_libxcb_util
  _install_qt_headless_into_oda
  command -v ODAFileConverter >/dev/null 2>&1 || {
    echo "ERROR: ODAFileConverter not on PATH after install." >&2
    exit 1
  }
  echo "ODA File Converter installed: $(command -v ODAFileConverter)"
}

_from_url() {
  local url="$1"
  if [[ -z "$url" ]]; then
    echo "ERROR: empty URL" >&2
    exit 1
  fi
  _install_prereqs
  local deb="/tmp/oda_file_converter.deb"
  wget -qO "$deb" "$url"
  dpkg -i "$deb" || apt-get install -yf
  rm -f "$deb"
  _symlink_libxcb_util
  _install_qt_headless_into_oda
  command -v ODAFileConverter >/dev/null 2>&1 || {
    echo "ERROR: ODAFileConverter not on PATH after install." >&2
    exit 1
  }
  echo "ODA File Converter installed: $(command -v ODAFileConverter)"
}

case "${1:-}" in
  from-file) _from_file "${2:-}" ;;
  from-url)  _from_url "${2:-}" ;;
  *)
    echo "Usage: $0 from-url <deb_url> | from-file <path_to_deb>" >&2
    exit 1
    ;;
esac
