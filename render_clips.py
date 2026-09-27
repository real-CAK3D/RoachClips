#!/usr/bin/env python3
"""Render ROACH CLIPS — B.I.G's Tuesday paper of clip-out coupons: new apps, software, Pi/ESP32 projects and deals
that fit the gear CAK3D already has.

Usage: render_clips.py drafts/<date>.json -> site/issues/<date>.html (+ site/data/<date>.json for the server), then build_clips.py.
Uses its own copy of The Double Wide's flipbook (flipbook.py) with its own masthead and stylesheet.
"""
import datetime as dt, json, os, sys

import flipbook as fb
from flipbook import e, para, page, SEAL

fb.CSS_FILE = "roach-clips.css"
ROOT, SITE = fb.ROOT, fb.SITE
KEYS = ("title", "category", "what", "why", "fits", "price", "deal", "expires", "time", "difficulty", "links")


def coupon_card(i, c):
    return ('<button type="button" class="coupon" data-kind="coupon" data-idx="%d"><span class="cp-scissors">✂</span>'
            '<span class="cp-cat">%s</span><span class="cp-price">%s</span><b class="cp-title">%s</b><span class="cp-what">%s</span>'
            '<span class="cp-fits">%s</span><span class="cp-foot"><span>%s</span><span class="job-status">Tap to clip or set up ›</span></span></button>'
            % (i, e(c.get("category") or "try it"), e(c.get("price") or "FREE"), e(c.get("title")), e(c.get("what")),
               ("For: " + e(c.get("fits"))) if c.get("fits") else "", e(c.get("expires") or c.get("time") or "")))


def render(ed):
    date = ed["date"]
    d = dt.date.fromisoformat(date)
    no = (d - dt.date(2026, 9, 29)).days // 7 + 1
    cps = [c for c in ed.get("coupons") or [] if isinstance(c, dict)][:12]
    pages = [page("This Week's Savings", '<div class="box cp-intro"><h2>This Week\'s Savings</h2>%s<p class="small">Tap a coupon: <b>✂ Clip it</b> to save it '
                  'for later, or <b>🛠 Have the Garden set it up</b>. Nothing is ever bought without you. <a href="clipped.html">Your clip board ›</a></p></div>'
                  % para(ed.get("intro")))]
    for n in range(0, len(cps), 4):
        pages.append(page("Coupons %d–%d" % (n + 1, min(n + 4, len(cps))),
                          '<div class="coupons">%s</div>' % "".join(coupon_card(n + i, c) for i, c in enumerate(cps[n:n + 4]))))
    front = page("Roach Clips", (
        '<div class="gum"><span>TUESDAY · CLIP &amp; SAVE · FOUND BY B.I.G</span></div>'
        '<div class="pc-top"><div class="seal">%s</div><div class="ear">No. %s<br>%s<br><b>%s</b><br>%s</div></div>'
        '<div class="flag"><div class="est">EST. 2026 · THE GARDEN · LEWISTON, ME</div><h1>The<br>Roach Clips</h1><div class="motto">Clip it · Try it · Keep it</div></div>'
        '<div class="pc-band"><span>APPS</span><span>ESP32</span><span>RASPBERRY PI</span></div>'
        '<div class="pc-teaser"><div class="kicker">Top coupon this week</div><b>%s</b></div><div class="pc-open">Start clipping ›</div>')
        % (SEAL, e(no), d.strftime("%a"), d.strftime("%b %-d"), d.strftime("%Y"), e(cps[0].get("title") if cps else "New things to try")), " hardcover")
    back = page("Back Page", (
        '<div class="gum"><span>SCOUTED BY B.I.G · THE GARDEN</span></div>'
        '<div class="pb-body"><div class="seal">%s</div><h2 class="pb-title">Roach Clips</h2>'
        '<p>Scouted by B.I.G for the gear you already have.<br>Prices checked the night before — they can change.</p>'
        '<p class="pb-code">%s · No. %s</p><p><a href="clipped.html">Your clip board ›</a> · <a href="archive.html">Back issues ›</a></p></div>')
        % (SEAL, date, e(no)), " hardcover back")
    return fb.book([front] + pages + [back], date=date, no=no, lists={"coupon": [{k: c.get(k) for k in KEYS} for c in cps]},
                   paper="Roach Clips", motto="Clip it · Try it · Keep it", gum="TUESDAY · CLIP & SAVE · FOUND BY B.I.G",
                   price="PRICE: FREE (MOSTLY)", delivered="DELIVERED TUESDAY BY B.I.G",
                   flap="Scouted by B.I.G · Nothing is bought without CAK3D", body_class="pub-cp")


def main():
    ed = json.load(open(sys.argv[1]))
    date = ed["date"]
    dt.date.fromisoformat(date)
    for sub in ("issues", "data"):
        os.makedirs(os.path.join(SITE, sub), exist_ok=True)
    json.dump(ed, open(os.path.join(SITE, "data", date + ".json"), "w"), ensure_ascii=False, indent=1)
    open(os.path.join(SITE, "issues", date + ".html"), "w").write(render(ed))
    print("rendered Roach Clips %s" % date)
    if "--no-build" not in sys.argv:
        import subprocess
        subprocess.run([sys.executable, os.path.join(ROOT, "build_clips.py")], check=False)


if __name__ == "__main__":
    main()
