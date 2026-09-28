#!/usr/bin/env python3
"""Roach Clips' pages around the issues: home (the newest issue), back issues and the clip board (every coupon
CAK3D clipped or had set up, with the result)."""
import datetime as dt, glob, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
DW = os.path.expanduser("~/.hermes/garden/doublewide")
sys.path.insert(0, ROOT)
import flipbook as fb   # noqa: E402
from flipbook import e   # noqa: E402

fb.CSS_FILE = "roach-clips.css"


def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return {}


def nice(day):
    return dt.date.fromisoformat(day).strftime("%A, %B %-d, %Y")


def shell(title, body):
    css = open(os.path.join(ROOT, fb.CSS_FILE)).read()
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#d62828">'
            '<link rel="icon" href="/icons/icon-192.png"><link rel="apple-touch-icon" href="/icons/icon-192.png">'
            '<link href="https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Bangers&family=Oswald:wght@400;600;700'
            '&family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">'
            '<style>%s</style><script src="/app.js" defer></script></head><body class="stand pub-cp">%s</body></html>' % (e(title), css, body))


def topbar(title, sub):
    return ('<header class="stand-top"><a class="stand-home ns-home" href="/" aria-label="The Corner Chronicle" title="The Corner Chronicle">🏠</a><a class="stand-home" href="./" aria-label="This week\'s coupons">✂</a><div><h1>%s</h1>'
            '<div class="stand-sub">%s</div></div><a class="stand-home" href="archive.html" aria-label="Back issues">🗂</a></header>' % (e(title), e(sub)))


def issues():
    d = os.path.join(SITE, "issues")
    return sorted((f[:-5] for f in os.listdir(d) if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.html", f)), reverse=True) if os.path.isdir(d) else []


def sync_portraits():
    os.makedirs(os.path.join(SITE, "img"), exist_ok=True)
    for f in glob.glob(os.path.join(DW, "site", "img", "*.png")):
        dest = os.path.join(SITE, "img", os.path.basename(f))
        if not os.path.exists(dest) or os.path.getmtime(dest) < os.path.getmtime(f):
            shutil.copy2(f, dest)


def build_clipped():
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "jobs", "*.json")), reverse=True):
        day = os.path.basename(f)[:10]
        cps = load(os.path.join(SITE, "data", day + ".json")).get("coupons") or []
        for k, v in load(f).items():
            if not k.startswith("coupon:") or v.get("status") not in ("clipped", "approved"):
                continue
            c = cps[int(k.split(":")[1])] if int(k.split(":")[1]) < len(cps) else {}
            links = "".join('<a href="%s" target="_blank" rel="noopener">%s</a> ' % (e(l.get("url")), e(l.get("label") or "link"))
                            for l in c.get("links") or [] if str(l.get("url", "")).startswith("https://"))
            state = ("✂ Clipped" if v["status"] == "clipped" else {"ok": "✅ Set up", "failed": "❌ Didn't work", "needs": "👉 Needs you"}
                     .get(v.get("result_status"), "⏳ The Garden is setting it up"))
            rows.append('<div class="coupon st-%s"><span class="cp-cat">%s</span><span class="cp-price">%s</span><b class="cp-title">%s</b>'
                        '<span class="cp-what">%s</span><span class="cp-fits">%s</span><span class="cp-foot"><span>%s · %s</span><span>%s</span></span></div>'
                        % (e(v["status"]), e(c.get("category") or ""), e(c.get("price") or ""), e(v.get("title")), e(c.get("what") or ""),
                           e(v.get("result") or ""), state, nice(day), links))
    body = ('%s<main class="paper"><div class="coupons">%s</div></main>'
            % (topbar("Your Clip Board", "everything you clipped or had set up"), "".join(rows) or '<p class="small">Nothing clipped yet.</p>'))
    open(os.path.join(SITE, "clipped.html"), "w").write(shell("Roach Clips — Clip Board", body))


def build_archive():
    items = "".join('<li><a href="issues/%s.html">%s</a></li>' % (x, nice(x)) for x in issues())
    body = ('%s<main class="paper"><div class="box arch"><h2>Roach Clips</h2><ul class="archive">%s</ul></div>'
            '<div class="box arch"><h2>Also</h2><ul class="archive"><li><a href="clipped.html">✂ Your clip board</a></li><li><a href="catalog.html">💰 B.I.G&#39;s Wish-Book archive &amp; plans</a></li>'
            '<li><a href="/green-thumb/">🌱 The Green Thumb</a> <span class="small">(what you already have)</span></li></ul></div></main>'
            % (topbar("Back Issues", "every Roach Clips"), items or "<li>The first Roach Clips comes Tuesday.</li>"))
    open(os.path.join(SITE, "archive.html"), "w").write(shell("Roach Clips — Back Issues", body))


def build_index():
    """The home page is always live: the latest coupons (Tuesdays) plus B.I.G's latest Wish-Book (nightly)."""
    import render_clips
    eds = issues()
    ed = load(os.path.join(SITE, "data", eds[0] + ".json")) if eds else None
    cat_date, cat_items = render_clips.latest_catalog()
    open(os.path.join(SITE, "index.html"), "w").write(render_clips.render(ed, up="", cat_date=cat_date, cat_items=cat_items))
    cps = (ed or {}).get("coupons") or []
    issues_ = sorted(set(eds[:10] + ([cat_date] if cat_date else [])), reverse=True)
    title = " · ".join(x for x in (("%d coupons" % len(cps)) if cps else "", ("%d Wish-Book ideas" % len(cat_items)) if cat_items else "") if x) or "First issue coming soon"
    json.dump({"paper": "Roach Clips", "date": issues_[0] if issues_ else "", "title": title, "url": "", "issues": issues_},
              open(os.path.join(SITE, "latest.json"), "w"), ensure_ascii=False)


def build_wishbook():
    import wishbook
    wishbook.main()


if __name__ == "__main__":
    for step in (sync_portraits, build_wishbook, build_clipped, build_archive, build_index):
        try:
            step()
        except Exception as ex:
            print("roach clips: %s failed: %s: %s" % (step.__name__, type(ex).__name__, ex))
    print("roach clips pages built")
