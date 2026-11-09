#!/usr/bin/env bash
# Install the DeepSeek Quota chip into a local Hermes desktop install.
#   ./install.sh            # install / update
#   ./install.sh --remove   # uninstall
set -euo pipefail

ID="deepseek-quota"
H="${HERMES_HOME:-$HOME/.hermes}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "${1:-}" = "--remove" ]; then
  rm -rf "$H/plugins/$ID" "$H/desktop-plugins/$ID"
  hermes plugins disable "$ID" >/dev/null 2>&1 || true
  echo "removed: $H/plugins/$ID and $H/desktop-plugins/$ID"
  exit 0
fi

mkdir -p "$H/plugins/$ID/dashboard" "$H/desktop-plugins/$ID"
cp "$SRC/plugin.yaml" "$SRC/__init__.py" "$H/plugins/$ID/"
cp "$SRC/dashboard/manifest.json" "$SRC/dashboard/plugin_api.py" "$H/plugins/$ID/dashboard/"
cp "$SRC/desktop/plugin.js" "$H/desktop-plugins/$ID/plugin.js"

if ! grep -q "^DEEPSEEK_API_KEY=" "$H/.env" 2>/dev/null; then
  echo "!! DEEPSEEK_API_KEY not found in $H/.env — the chip will show '—' until it is set." >&2
fi

hermes plugins enable "$ID" >/dev/null 2>&1 || hermes plugins enable "$ID"
echo "installed: $H/plugins/$ID + $H/desktop-plugins/$ID"
echo "The chip appears in the status bar within a few seconds (if not: Cmd+K -> Reload desktop plugins)."
