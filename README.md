# Roach Clips

B.I.G's Tuesday paper of clip-out coupons: new apps, self-hosted software, Raspberry Pi and ESP32 projects, AI tools and real deals, picked for the gear already in the Garden. Tap a coupon to **✂ clip it** or **🛠 have the Garden set it up** (free things only — nothing is ever bought).

Part of the Garden's papers, all read through **[The Newsstand](https://github.com/real-CAK3D/NewsStand)** — one home-screen app that mounts every paper under one private (Tailscale-only) HTTPS address: [The Double Wide](https://github.com/real-CAK3D/TheDoubleWide) (daily), [The Re-Up](https://github.com/real-CAK3D/TheRe-Up) (want ads), [The Sunday Smoke](https://github.com/real-CAK3D/TheSundaySmoke) (Sundays), [Roach Clips](https://github.com/real-CAK3D/RoachClips) (Tuesdays) and [The Green Thumb](https://github.com/real-CAK3D/TheGreenThumb) (the directory). The papers are written by [Hermes](https://github.com/NousResearch/hermes-agent) agents running on a small Oracle VM called The Garden.

## Files

| File | What it does |
|---|---|
| `render_clips.py` | Prints an issue from B.I.G's JSON draft as a flipbook of dashed coupons. |
| `clips_inputs.py` | What's already in the Garden (from The Green Thumb) and past coupons, so nothing repeats. |
| `build_clips.py` | Home page, back issues and the clip board. |
| `serve.py` | Clip / set-up / pass for each coupon; set-ups go to Ganja as a one-off Hermes job. |
| `prompts/clips_prompt.txt` | B.I.G's instructions and the coupon schema. |
| `gardenweb.py` | The small shared web-server kit every Garden paper carries its own copy of. |

## Running

Runs Tuesdays at 05:00 Eastern; served at `/roach-clips/` under the Newsstand. Each project is Linux-first (`%-d` date formatting) and expects a Hermes install on the same machine.
