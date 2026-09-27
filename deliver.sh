#!/usr/bin/env bash
# After B.I.G files Roach Clips: print the issue, rebuild the pages and ring The Corner Chronicle's bell.
set -u
D="$HOME/.hermes/garden/roach-clips"; PY="$HOME/.hermes/hermes-agent/venv/bin/python"; T=$(TZ=America/New_York date +%F)
F="$D/drafts/$T.json"; [ -f "$F" ] || { echo "no Roach Clips draft for $T"; exit 0; }
cd "$D" && "$PY" "$D/render_clips.py" "$F" || exit 1
N=$("$PY" -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["coupons"]))' "$F" 2>/dev/null)
"$PY" "$HOME/.hermes/garden/newsstand/notify.py" "✂️ Roach Clips is here" "${N:-New} things to try this week, found by B.I.G" "/roach-clips/"
