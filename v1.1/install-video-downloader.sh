#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Install Simple Video Downloader from an existing Git checkout.

Usage:
  install-video-downloader.sh [--check]

Options:
  --check    Validate the Debian container and repository without changing it
  --help     Show this help

Run this script as root inside the new Debian CT from any location. The script
installs the app.py and video-downloader.service found in the same repository.
EOF
}

CHECK_ONLY="0"
case "${1:-}" in
  "") ;;
  --check) CHECK_ONLY="1" ;;
  --help|-h) usage; exit 0 ;;
  *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
esac
if (($# > 1)); then
  echo "Too many arguments." >&2
  usage >&2
  exit 2
fi

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this script as root inside the Debian CT." >&2
  exit 1
fi
if [[ ! -r /etc/os-release ]]; then
  echo "Cannot identify the operating system." >&2
  exit 1
fi
# shellcheck disable=SC1091
source /etc/os-release
if [[ ${ID:-} != "debian" ]]; then
  echo "This installer supports Debian only; detected: ${PRETTY_NAME:-unknown}." >&2
  exit 1
fi
if [[ ! -d /run/systemd/system ]]; then
  echo "systemd is not running; this does not look like a started Debian CT." >&2
  exit 1
fi

REPO_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
for required_file in app.py video-downloader.service; do
  if [[ ! -f "$REPO_DIR/$required_file" ]]; then
    echo "Missing repository file: $REPO_DIR/$required_file" >&2
    exit 1
  fi
done

echo "Debian installation plan"
echo "  Operating system: ${PRETTY_NAME}"
echo "  Source checkout:  $REPO_DIR"
echo "  Application:      /opt/video-downloader/app.py"
echo "  Download path:    /downloads"
echo "  Service:          video-downloader.service"

if [[ $CHECK_ONLY == "1" ]]; then
  echo "Check completed; no packages or files were changed."
  exit 0
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl ffmpeg python3 python3-flask

temp_dir=$(mktemp -d)
trap 'rm -rf -- "$temp_dir"' EXIT
curl --fail --location --proto '=https' --tlsv1.2 \
  https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
  --output "$temp_dir/yt-dlp"
curl --fail --location --proto '=https' --tlsv1.2 \
  https://github.com/yt-dlp/yt-dlp/releases/latest/download/SHA2-256SUMS \
  --output "$temp_dir/SHA2-256SUMS"
checksum_line=$(grep -E '^[[:xdigit:]]{64}[[:space:]]+yt-dlp$' "$temp_dir/SHA2-256SUMS" || true)
if [[ -z $checksum_line ]]; then
  echo "The yt-dlp checksum manifest did not contain the expected entry." >&2
  exit 1
fi
(cd "$temp_dir" && printf '%s\n' "$checksum_line" | sha256sum --check --strict -)

install -d -m 0755 /opt/video-downloader /downloads
install -m 0755 "$REPO_DIR/app.py" /opt/video-downloader/app.py
install -m 0755 "$temp_dir/yt-dlp" /usr/local/bin/yt-dlp
install -m 0644 "$REPO_DIR/video-downloader.service" /etc/systemd/system/video-downloader.service

systemctl daemon-reload
systemctl enable --now video-downloader.service

echo "Video Downloader is installed and running."
echo "Open http://CONTAINER_IP:8080 on a trusted LAN or VPN."
