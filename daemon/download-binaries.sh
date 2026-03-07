#!/usr/bin/env bash
set -euo pipefail

repo="palladium-coin/palladiumcore"
platform="linux"
arch=""
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/palladium-bin.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

die(){ echo "[download-binaries] ERROR: $*" >&2; exit 1; }
log(){ echo "[download-binaries] $*"; }
usage(){ echo "Usage: ./download-binaries.sh [--platform linux|darwin|windows] [--arch x86_64|aarch64|armv7l] [--repo owner/name]"; }

norm_arch(){ case "$1" in x86_64|amd64) echo x86_64;; aarch64|arm64) echo aarch64;; armv7l|armv7) echo armv7l;; *) die "Unsupported arch: $1";; esac; }
norm_platform(){ case "$1" in linux) echo linux;; darwin|macos|osx) echo darwin;; windows|win|mingw|msys|cygwin) echo windows;; *) die "Unsupported platform: $1";; esac; }

http_get(){
  if command -v curl >/dev/null 2>&1; then curl -fsSL --retry 3 --connect-timeout 15 "$1"
  elif command -v wget >/dev/null 2>&1; then wget -qO- "$1"
  else die "Install curl or wget"; fi
}
http_download(){
  if command -v curl >/dev/null 2>&1; then curl -fL --retry 3 --connect-timeout 15 -o "$2" "$1"
  elif command -v wget >/dev/null 2>&1; then wget -O "$2" "$1"
  else die "Install curl or wget"; fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform) [[ $# -ge 2 ]] || die "Missing value for --platform"; platform="$(norm_platform "$2")"; shift 2 ;;
    --arch) [[ $# -ge 2 ]] || die "Missing value for --arch"; arch="$(norm_arch "$2")"; shift 2 ;;
    --repo) [[ $# -ge 2 ]] || die "Missing value for --repo"; repo="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

[[ -n "$arch" ]] || arch="$(norm_arch "$(uname -m)")"
api="https://api.github.com/repos/${repo}/releases/latest"
assets="$(http_get "$api" | grep -oE '"browser_download_url":[[:space:]]*"[^"]+"' | sed -E 's/.*"([^"]+)"/\1/')"
[[ -n "$assets" ]] || die "No release assets found"

pick_asset(){
  local strict="${1:-0}" url name
  while IFS= read -r url; do
    [[ -n "$url" ]] || continue
    name="$(echo "${url##*/}" | tr '[:upper:]' '[:lower:]')"
    [[ "$name" == *.tar.gz || "$name" == *.tgz || "$name" == *.zip ]] || continue
    case "$platform" in
      linux) [[ "$name" == *linux* ]] || continue ;;
      darwin) [[ "$name" == *darwin* || "$name" == *mac* || "$name" == *osx* ]] || continue ;;
      windows) [[ "$name" == *windows* || "$name" == *win* ]] || continue ;;
    esac
    if [[ "$strict" == "1" ]]; then
      case "$arch" in
        x86_64) [[ "$name" == *x86_64* || "$name" == *amd64* ]] || continue ;;
        aarch64) [[ "$name" == *aarch64* || "$name" == *arm64* ]] || continue ;;
        armv7l) [[ "$name" == *armv7* ]] || continue ;;
      esac
    fi
    echo "$url"; return 0
  done <<< "$assets"
  return 1
}

url="$(pick_asset 1 || pick_asset 0 || true)"
[[ -n "$url" ]] || die "No compatible asset for platform=$platform arch=$arch"
archive="$tmp/${url##*/}"

log "Platform: $platform | Arch: $arch"
log "Downloading: $url"
http_download "$url" "$archive"

log "Extracting: ${archive##*/}"
case "$archive" in
  *.tar.gz|*.tgz) tar -xzf "$archive" -C "$tmp" ;;
  *.zip) command -v unzip >/dev/null 2>&1 || die "Install unzip"; unzip -q "$archive" -d "$tmp" ;;
  *) die "Unsupported archive format: ${archive##*/}" ;;
esac

for b in palladiumd palladium-cli palladium-tx palladium-wallet; do
  src="$(find "$tmp" -type f \( -name "$b" -o -name "$b.exe" \) | head -n 1 || true)"
  [[ -n "$src" ]] || die "Binary not found: $b"
  cp "$src" "$dir/$(basename "$src")"
  chmod +x "$dir/$(basename "$src")"
  log "Installed: $(basename "$src")"
done

log "Done. Updated binaries in $dir"
