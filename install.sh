#!/usr/bin/env bash
# Pasang chip "DeepSeek quota" ke Hermes desktop pada mesin ni.
#   ./install.sh          # pasang / kemas kini
#   ./install.sh --remove  # buang
set -euo pipefail

ID="deepseek-quota"
H="${HERMES_HOME:-$HOME/.hermes}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "${1:-}" = "--remove" ]; then
  rm -rf "$H/plugins/$ID" "$H/desktop-plugins/$ID"
  hermes plugins disable "$ID" >/dev/null 2>&1 || true
  echo "dibuang: $H/plugins/$ID dan $H/desktop-plugins/$ID"
  exit 0
fi

mkdir -p "$H/plugins/$ID/dashboard" "$H/desktop-plugins/$ID"
cp "$SRC/plugin.yaml" "$SRC/__init__.py" "$H/plugins/$ID/"
cp "$SRC/dashboard/manifest.json" "$SRC/dashboard/plugin_api.py" "$H/plugins/$ID/dashboard/"
cp "$SRC/desktop/plugin.js" "$H/desktop-plugins/$ID/plugin.js"

if ! grep -q "^DEEPSEEK_API_KEY=" "$H/.env" 2>/dev/null; then
  echo "!! DEEPSEEK_API_KEY tak dijumpai dalam $H/.env — chip akan tunjuk '—' sampai key dimasukkan." >&2
fi

hermes plugins enable "$ID" >/dev/null 2>&1 || hermes plugins enable "$ID"
echo "siap: $H/plugins/$ID + $H/desktop-plugins/$ID"
echo "chip muncul dalam status bar bawah dalam beberapa saat (kalau tak, ⌘K → Reload desktop plugins)."
