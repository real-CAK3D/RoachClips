#!/usr/bin/env bash
# After B.I.G's nightly shift: pull his new Wish-Book into Roach Clips, rebuild the pages and ring the Newsstand's bell.
set -u
D="$HOME/.hermes/garden/roach-clips"; PY="$HOME/.hermes/hermes-agent/venv/bin/python"; T=$(TZ=America/New_York date +%F)
cd "$D" && "$PY" "$D/build_clips.py"
F="$D/site/data/market-$T.json"
[ -f "$F" ] || { echo "no Wish-Book for $T"; exit 0; }
N=$("$PY" -c 'import json,sys; print(len(json.load(open(sys.argv[1])).get("items") or []))' "$F" 2>/dev/null)
"$PY" "$HOME/.hermes/garden/newsstand/notify.py" "💰 B.I.G's Wish-Book: ${N:-new} ideas" "Tonight's side gigs are in Roach Clips — tap one for the full plan." "/roach-clips/"
