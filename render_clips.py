#!/usr/bin/env python3
"""Render ROACH CLIPS — B.I.G's paper: Tuesday's clip-out coupons (new apps, software, Pi/ESP32 projects and deals that fit
the gear CAK3D already has) and his nightly WISH-BOOK of side gigs, each with a price-tag starburst and a full start-to-finish plan.

Usage: render_clips.py drafts/<tuesday>.json   -> site/issues/<date>.html (+ site/data/<date>.json), then build_clips.py
The home page (latest coupons + latest Wish-Book) is rebuilt by build_clips.py after every catalog, issue or plan.
Uses its own copy of The Double Wide's flipbook (flipbook.py) with its own pack and stylesheet.
"""
import datetime as dt, glob, json, os, sys

import flipbook as fb
from flipbook import e, para, page, SEAL, catalog_block, back_codes

fb.CSS_FILE = "roach-clips.css"
ROOT, SITE = fb.ROOT, fb.SITE
KEYS = ("title", "category", "what", "why", "fits", "price", "deal", "expires", "time", "difficulty", "links")


def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return {}


def latest_catalog():
    files = sorted(glob.glob(os.path.join(SITE, "data", "market-20*.json")))
    if not files:
        return None, []
    return os.path.basename(files[-1])[7:17], [x for x in load(files[-1]).get("items") or [] if isinstance(x, dict)]


def coupon_card(i, c):
    return ('<button type="button" class="coupon" data-kind="coupon" data-idx="%d"><span class="cp-scissors">✂</span>'
            '<span class="cp-cat">%s</span><span class="cp-price">%s</span><b class="cp-title">%s</b><span class="cp-what">%s</span>'
            '<span class="cp-fits">%s</span><span class="cp-foot"><span>%s</span><span class="job-status">Tap to clip or set up ›</span></span></button>'
            % (i, e(c.get("category") or "try it"), e(c.get("price") or "FREE"), e(c.get("title")), e(c.get("what")),
               ("For: " + e(c.get("fits"))) if c.get("fits") else "", e(c.get("expires") or c.get("time") or "")))


def render(ed, up="../", cat_date=None, cat_items=None):
    """ed = the coupon issue (or None before the first Tuesday); up = link prefix back to the paper's root."""
    ed = ed or {}
    if cat_items is None:
        cat_date, cat_items = latest_catalog()
    cps = [c for c in ed.get("coupons") or [] if isinstance(c, dict)][:12]
    date = ed.get("date") or cat_date or dt.date.today().isoformat()
    d = dt.date.fromisoformat(date)
    no = max(1, (d - dt.date(2026, 9, 29)).days // 7 + 1)
    pages = []
    if cps:
        pages.append(page("This Week's Coupons", '<div class="box cp-intro"><h2>This Week\'s Coupons</h2>%s<p class="small">Tap a coupon: <b>✂ Clip it</b> to save it '
                          'for later, or <b>🛠 Have the Garden set it up</b>. Nothing is ever bought without you. <a href="%sclipped.html">Your clip board ›</a></p></div>'
                          % (para(ed.get("intro")), up)))
        for n in range(0, len(cps), 4):
            pages.append(page("Coupons %d–%d" % (n + 1, min(n + 4, len(cps))),
                              '<div class="coupons">%s</div>' % "".join(coupon_card(n + i, c) for i, c in enumerate(cps[n:n + 4]))))
    if cat_items:
        pages.append(page("B.I.G's Wish-Book", '<div class="box market">%s<p class="small center">Filed %s · <a href="%scatalog.html">every past Wish-Book ›</a></p></div>'
                          % (catalog_block(cat_items), e(dt.date.fromisoformat(cat_date).strftime("%A, %B %-d")), up)))
    plans = load(os.path.join(ROOT, "plans", "state.json"))
    ready = [k for k in plans if os.path.exists(os.path.join(SITE, "guides", k + ".html"))]
    if plans:
        rows = "".join('<li><a href="%sguides/%s.html">📋 %s</a> <span class="small">Item No. %s</span></li>' % (up, e(k), e(plans[k].get("title") or k), e(k)) for k in ready)
        rows += "".join('<li>✍️ %s <span class="small">— B.I.G is writing it</span></li>' % e(v.get("title") or k)
                        for k, v in plans.items() if k not in ready and v.get("status") == "writing")
        pages.append(page("B.I.G's Plans", '<div class="box plans"><h2>B.I.G\'s Start-to-Finish Plans</h2><ul class="plan-links">%s</ul></div>'
                          % (rows or "<li>No plans yet — tap an idea in the Wish-Book.</li>")))
    if not pages:
        pages.append(page("Coming Soon", '<div class="box"><h2>The first Roach Clips is on its way</h2><p>Tuesdays B.I.G clips new things to try; '
                          'every night he files his Wish-Book of side gigs.</p></div>'))
    seal = '<a class="seal" href="/" aria-label="Back to The Corner Chronicle" title="Back to The Corner Chronicle">%s</a>' % SEAL
    front = page("Roach Clips", (
        '<div class="gum"><span>KUTCORNERS · CLIP &amp; SAVE · FOUND BY B.I.G</span></div>'
        '<div class="pc-top">%s<div class="ear">No. %s<br>%s<br><b>%s</b><br>%s</div></div>'
        '<div class="flag"><div class="est">QUALITÉ SUPÉRIEURE · THE GARDEN</div><h1>Roach<br>Clips</h1><div class="motto">Clip it · Try it · Keep it</div></div>'
        '<div class="pc-band"><span>COUPONS</span><span>WISH-BOOK</span><span>SIDE GIGS</span></div>'
        '<div class="pc-teaser"><div class="kicker">%s</div><b>%s</b></div><div class="pc-open">Start clipping ›</div>')
        % (seal, e(no), d.strftime("%a"), d.strftime("%b %-d"), d.strftime("%Y"), "Top coupon this week" if cps else "Tonight's Wish-Book",
           e(cps[0].get("title") if cps else (cat_items[0].get("title") if cat_items else "New things to try"))), " hardcover")
    back = page("Back Page", (
        '<div class="gum"><span>SCOUTED BY B.I.G · THE GARDEN</span></div>'
        '<div class="pb-body">%s<h2 class="pb-title">Roach Clips</h2>'
        '<p>Scouted by B.I.G for the gear you already have.<br>Prices checked the night before — they can change. Nothing is bought without you.</p>'
        '%s<p class="pb-code">%s · No. %s</p><p><a href="%sclipped.html">Your clip board ›</a> · <a href="%scatalog.html">Wish-Book archive ›</a> · '
        '<a href="%sarchive.html">Back issues ›</a></p></div>')
        % (seal, back_codes("https://github.com/real-CAK3D/RoachClips", "RoachClips"), date, e(no), up, up, up), " hardcover back")
    lists = {"coupon": [{k: c.get(k) for k in KEYS} for c in cps], "market": [{k: x.get(k) for k in fb.MARKET_KEYS} for x in cat_items or []],
             "market_date": cat_date or ""}
    return fb.book([front] + pages + [back], date=date, no=no, lists=lists,
                   paper="Roach Clips", motto="Clip it · Try it · Keep it", gum="KUTCORNERS · CLIP & SAVE · FOUND BY B.I.G",
                   price="PRICE: FREE (MOSTLY)", delivered="SCOUTED BY B.I.G", flap="Scouted by B.I.G · Nothing is bought without CAK3D",
                   body_class="pub-cp", est="QUALITÉ SUPÉRIEURE · THE GARDEN")


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
