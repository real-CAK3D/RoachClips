#!/usr/bin/env python3
"""B.I.G's Wish-Book for Roach Clips: copies his nightly catalogs from the vault, builds the catalog archive and turns his
Markdown start-to-finish plans into pages. Run by build_clips.py (after every catalog, coupon issue or finished plan)."""
import datetime as dt, glob, html, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
VAULT = "/home/ubuntu/CAK3D_Garden_Wiki"
VENV_PY = os.path.expanduser("~/.hermes/hermes-agent/venv/bin/python")
try:
    import markdown
except ImportError:   # system python: rerun with the Hermes venv, which has the markdown package
    if os.path.exists(VENV_PY) and sys.executable != VENV_PY:
        os.execv(VENV_PY, [VENV_PY] + sys.argv)
    markdown = None
sys.path.insert(0, ROOT)
import flipbook as rd   # noqa: E402
from flipbook import e, mug, catalog_block   # noqa: E402

rd.CSS_FILE = "roach-clips.css"

from zoneinfo import ZoneInfo
TZ_NOW = dt.datetime.now(ZoneInfo("America/New_York"))


def load(p, default=None):
    try:
        return json.load(open(p))
    except Exception:
        return default if default is not None else {}


def nice(day, fmt="%A, %B %-d, %Y"):
    try:
        return dt.date.fromisoformat(day).strftime(fmt)
    except Exception:
        return day


def shell(title, body, cls="stand", extra_head="", scripts=""):
    """A plain (non-flipbook) newsstand page with the paper's fonts, colors and app hookups."""
    css = open(os.path.join(ROOT, rd.CSS_FILE)).read()
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#2a1a10">'
            '<link rel="icon" href="/icons/icon-192.png"><link rel="apple-touch-icon" href="/icons/icon-192.png">'
            '<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Rye&family=UnifrakturMaguntia&family=Bangers&family=Patrick+Hand+SC'
            '&family=Oswald:wght@400;600;700&family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">'
            '<style>%s</style>%s<script src="/app.js" defer></script></head><body class="%s pub-cp">%s%s</body></html>'
            % (e(title), css, extra_head, cls, body, scripts))


def topbar(title, sub="", up=""):
    return ('<header class="stand-top"><a class="stand-home ns-home" href="/" aria-label="The Corner Chronicle" title="The Corner Chronicle">🏠</a><a class="stand-home" href="%s" aria-label="Roach Clips">✂</a>'
            '<div><h1>%s</h1>%s</div><a class="stand-home" href="%sarchive.html" aria-label="Back issues">🗂</a></header>'
            % (up or "./", e(title), ('<div class="stand-sub">%s</div>' % e(sub)) if sub else "", up))


def listing(folder):
    return sorted((f[:-5] for f in os.listdir(os.path.join(SITE, folder)) if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.html", f)), reverse=True) \
        if os.path.isdir(os.path.join(SITE, folder)) else []


# ------------------------------------------------------------------ B.I.G's catalogs: copy every day's file from the vault
def sync_market():
    try:
        r = subprocess.run(["ssh", "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "cak3d",
                            "cd '%s/10_Constellations/B.I.G/Market' 2>/dev/null && for f in 20*.json; do [ -f \"$f\" ] && "
                            "{ echo \"=== $f\"; cat \"$f\"; echo; }; done" % VAULT], capture_output=True, text=True, timeout=60)
    except Exception:
        return
    for chunk in r.stdout.split("=== ")[1:]:
        name, _, body = chunk.partition("\n")
        m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.json", name.strip())
        if not m:
            continue
        try:
            data = json.loads(body)
        except Exception:
            continue
        out = os.path.join(SITE, "data", "market-%s.json" % m.group(1))
        if load(out) != data:
            json.dump(data, open(out, "w"), ensure_ascii=False, indent=1)


# ------------------------------------------------------------------ B.I.G's full plans (markdown he writes → a supplement page)
def md_to_html(text):
    if markdown:
        h = markdown.markdown(text, extensions=["tables", "sane_lists", "fenced_code"])
    else:
        h = "".join("<p>%s</p>" % e(p).replace("\n", "<br>") for p in re.split(r"\n\s*\n", text))
    return re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', h)


def build_guides():
    os.makedirs(os.path.join(SITE, "guides"), exist_ok=True)
    state = load(os.path.join(ROOT, "plans", "state.json"))
    for f in glob.glob(os.path.join(ROOT, "guides", "*.md")):
        no = os.path.basename(f)[:-3]
        if not re.fullmatch(r"[A-Za-z0-9-]+", no):
            continue
        out = os.path.join(SITE, "guides", no + ".html")
        if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(f) and os.path.getmtime(out) >= os.path.getmtime(__file__):
            continue
        text = open(f, errors="ignore").read()
        title = (re.search(r"^#\s+(.+)$", text, re.M) or [None, state.get(no, {}).get("title") or no])[1]
        written = dt.datetime.fromtimestamp(os.path.getmtime(f)).strftime("%B %-d, %Y")
        body = ('%s<main class="paper guide"><div class="guide-head"><span class="kicker">B.I.G\'s How-To Supplement · Item No. %s</span>'
                '<div class="guide-by">%s<span>Researched &amp; written by B.I.G · %s</span></div></div>'
                '<article class="guide-body">%s</article>'
                '<p class="guide-foot">B.I.G never buys anything or opens accounts for you — every sign-up and payment here is yours to do. '
                'Legal and tax notes are general information for Maine, not legal advice; check the official links.</p>'
                '<p class="center"><a href="../catalog.html">← B.I.G\'s catalog</a> · <a href="../">✂ Roach Clips</a> · <a href="/">🏠 The Corner Chronicle</a></p></main>'
                % (topbar("Start-to-Finish Plan", title, "../"), e(no), mug("B.I.G", "mug sm"), written, md_to_html(text)))
        open(out, "w").write(shell("%s — B.I.G's plan" % title, body, "stand guide-page"))


# ------------------------------------------------------------------ catalog archive
CARD_JS = r"""<script>
(function () {
  var DATA = @@DATA@@, PLANS = {};
  var BASE = location.pathname.replace(/[^\/]*$/, '');
  var modal = document.getElementById('jobmodal'), cur = null;
  function esc(t) { var d = document.createElement('div'); d.textContent = t == null ? '' : String(t); return d.innerHTML; }
  function row(l, v) { return v ? '<div class="tag-row"><span>' + esc(l) + '</span><b>' + esc(v) + '</b></div>' : ''; }
  function paint() {
    Array.prototype.forEach.call(document.querySelectorAll('.cat-item'), function (b) {
      var sec = b.closest('[data-date]'), j = (DATA[sec.dataset.date] || [])[+b.dataset.idx] || {}, p = PLANS[j.item_no], el = b.querySelector('.cat-more');
      if (p && el) el.textContent = p.status === 'ready' ? '📋 Full plan ready ›' : p.status === 'writing' ? '✍️ B.I.G is writing the plan…' : el.textContent;
    });
  }
  function load() { fetch(BASE + 'api/plans', { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (p) { PLANS = p || {}; paint(); }).catch(function () {}); }
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest && ev.target.closest('.cat-item'); if (!b) return;
    var date = b.closest('[data-date]').dataset.date, j = (DATA[date] || [])[+b.dataset.idx] || {}, p = PLANS[j.item_no] || {};
    cur = { date: date, idx: +b.dataset.idx };
    document.getElementById('jm-kind').textContent = 'B.I.G\'s Catalog · ' + date + ' · Item No. ' + (j.item_no || '');
    document.getElementById('jm-title').textContent = j.title || '';
    document.getElementById('jm-body').innerHTML = '<div class="burst big"><span>' + esc(j.price || j.income_week || '?') + '</span></div><p>' + esc(j.desc) + '</p>' +
      (j.how ? '<p><b>How it pays:</b> ' + esc(j.how) + '</p>' : '') + '<div class="tag-card">' + row('Potential income / week', j.income_week) +
      row('Time to keep it going', j.tend) + row('Up-front cost', j.upfront) + row('Weekly cost', j.weekly_cost) + row('Risk of loss', j.risk) + '</div>';
    document.getElementById('jm-links').innerHTML = (j.links || []).filter(function (l) { return /^https?:\/\//.test(l.url || ''); })
      .map(function (l) { return '<a class="btn link" target="_blank" rel="noopener" href="' + esc(l.url) + '">🔗 ' + esc(l.label || l.url) + '</a>'; }).join('');
    var go = document.getElementById('jm-go');
    go.dataset.d = p.status === 'ready' ? 'read' : 'plan'; go.dataset.url = p.url || '';
    go.innerHTML = p.status === 'ready' ? '📖 Read B.I.G\'s full start-to-finish plan' : p.status === 'writing' ? '✍️ B.I.G is writing the plan — check back soon'
                 : '📋 Have B.I.G write the full plan: every step, site, account &amp; legal need';
    document.getElementById('jm-msg').textContent = ''; modal.hidden = false;
  });
  document.getElementById('jm-close').onclick = function () { modal.hidden = true; };
  modal.addEventListener('click', function (e) { if (e.target === modal) modal.hidden = true; });
  document.getElementById('jm-go').onclick = function () {
    var go = this, msg = document.getElementById('jm-msg');
    if (go.dataset.d === 'read') { location.href = BASE + go.dataset.url; return; }
    msg.textContent = 'Sending…';
    fetch(BASE + 'api/plan', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Double-Wide': '1' }, body: JSON.stringify(cur) })
      .then(function (r) { return r.json(); })
      .then(function (res) { msg.textContent = res.message || 'Sent.'; if (res.status === 'ready' && res.url) location.href = BASE + res.url; load(); })
      .catch(function () { msg.textContent = 'Could not reach the Garden — try again in a minute.'; });
  };
  load();
})();
</script>"""

MODAL = ('<div class="modal" id="jobmodal" hidden><div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="jm-title">'
         '<button type="button" class="modal-x" id="jm-close" aria-label="Close">×</button>'
         '<div class="jm-head"><span id="jm-mug">%s</span><div><div class="kicker" id="jm-kind"></div><h3 id="jm-title"></h3></div></div>'
         '<div id="jm-body"></div><div id="jm-links" class="jm-links"></div>'
         '<div class="jm-actions"><button type="button" class="btn go" id="jm-go">📋 Plan</button></div><p class="small" id="jm-msg"></p></div></div>')


def build_catalog():
    days = sorted((os.path.basename(f)[7:17] for f in glob.glob(os.path.join(SITE, "data", "market-*.json"))), reverse=True)
    data, secs = {}, []
    for day in days:
        items = [x for x in load(os.path.join(SITE, "data", "market-%s.json" % day)).get("items") or [] if isinstance(x, dict)]
        if not items:
            continue
        data[day] = [{k: x.get(k) for k in rd.MARKET_KEYS} for x in items]
        secs.append('<section class="cat-day" data-date="%s"><h2 class="cat-date">%s <small>%d ideas</small></h2>%s</section>'
                    % (day, nice(day), len(items), '<div class="catalog">' + catalog_block(items).split('<div class="catalog">', 1)[1]))
    state = load(os.path.join(ROOT, "plans", "state.json"))
    ready = [(no, v) for no, v in state.items() if os.path.exists(os.path.join(SITE, "guides", no + ".html"))]
    plans = "".join('<li><a href="guides/%s.html">📋 %s</a> <span class="small">Item No. %s</span></li>' % (e(no), e(v.get("title") or no), e(no))
                    for no, v in sorted(ready, key=lambda kv: kv[1].get("at", ""), reverse=True))
    body = ('%s<main class="paper"><div class="catalog-head"><span>B.I.G\'s</span> Wish-Book Archive<small>Every idea B.I.G ever filed · tap one for the full tag and his start-to-finish plan</small></div>'
            '%s%s</main>%s'
            % (topbar("B.I.G's Catalog", "every listing, every day"),
               ('<div class="box plans"><h2>B.I.G\'s Finished Plans</h2><ul class="plan-links">%s</ul></div>' % plans) if plans else "",
               "".join(secs) or '<p class="small">No catalogs filed yet.</p>', MODAL % mug("B.I.G", "mug")))
    page_html = shell("B.I.G's Catalog Archive", body, "stand", scripts=CARD_JS.replace("@@DATA@@", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    open(os.path.join(SITE, "catalog.html"), "w").write(page_html.replace('src="../img/', 'src="img/'))


def main():
    os.makedirs(os.path.join(SITE, "data"), exist_ok=True)
    if "--offline" not in sys.argv:
        sync_market()
    for step in (build_guides, build_catalog):
        try:
            step()
        except Exception as ex:
            print("wishbook: %s failed: %s: %s" % (step.__name__, type(ex).__name__, ex))
    print("wishbook built")


if __name__ == "__main__":
    main()
