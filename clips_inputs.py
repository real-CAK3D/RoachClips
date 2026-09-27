#!/usr/bin/env python3
"""Input for ROACH CLIPS (B.I.G, Tuesdays): what CAK3D already runs (from The Green Thumb, no secrets),
what was offered before (so nothing repeats) and what he clipped or had set up."""
import datetime as dt, glob, json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")


def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return {}


today = dt.date.today()
print("ROACH CLIPS — edition date %s (Tuesday)\n" % today)
yp = load(os.path.expanduser("~/.hermes/garden/green-thumb/site/data/green-thumb.json")).get("entries") or []
by = {}
for x in yp:
    by.setdefault(x.get("device") or "Other", []).append("%s (%s)" % (x.get("name"), x.get("category") or "?"))
print("WHAT CAK3D ALREADY HAS (from The Green Thumb):")
for dev, items in sorted(by.items()):
    print("- %s: %s" % (dev, "; ".join(items)))
print("\nPAST COUPONS (never offer these again):")
for f in sorted(glob.glob(os.path.join(SITE, "data", "20*.json")))[-8:]:
    for c in load(f).get("coupons") or []:
        print("- %s: %s" % (os.path.basename(f)[:10], c.get("title")))
print("\nWHAT HE CLIPPED OR HAD SET UP (more like these):")
for f in sorted(glob.glob(os.path.join(ROOT, "jobs", "*.json")))[-40:]:
    for k, v in load(f).items():
        if k.startswith("coupon:") and v.get("status") in ("clipped", "approved"):
            print("- %s (%s)" % (v.get("title"), v.get("status")))
