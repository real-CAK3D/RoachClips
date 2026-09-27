#!/usr/bin/env python3
"""Roach Clips web server (Tailscale-only; mounted at /roach-clips/ under The Corner Chronicle).

  GET  /api/jobs?date=YYYY-MM-DD      -> each coupon's state ("coupon:<idx>": clipped / approved + result)
  POST /api/jobs {date, kind: "coupon", idx, decision: approve | clip | dismiss}
        "approve" = Have the Garden set it up: a one-off job for Ganja (never buys anything or opens accounts).
  GET  /api/plans                     -> {"<item_no>": {"status": writing|ready|failed, "url": ...}}
  POST /api/plan {date, idx}          -> B.I.G writes a full start-to-finish plan for that Wish-Book item
Usage: serve.py <site_dir> <host> <port>
"""
import datetime as dt, glob, json, os, re, subprocess, sys

import gardenweb as gw
from gardenweb import jload, jsave, LOCK

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "site")
HERMES = os.path.expanduser("~/.hermes")
PY = os.path.join(HERMES, "hermes-agent/venv/bin/python")
NEWSSTAND = os.path.join(HERMES, "garden", "newsstand")   # notices go out through The Corner Chronicle app
RESULT_RULE = ("START your final reply with exactly one line: 'RESULT: OK — <what worked>', 'RESULT: FAILED — <what went wrong>' or "
               "'RESULT: NEEDS CAK3D — <the step he must do>'. Roach Clips shows that line on the clip board, so keep it under 120 characters.")


def sh(s):
    return "'" + str(s).replace("'", "'\\''") + "'"


def create_job(profile_home, prompt, name, schedule="1m", pause=False):
    code = ("import sys; from cron.jobs import create_job, pause_job\n"
            "j = create_job(sys.argv[1], sys.argv[3], name=sys.argv[2], repeat=1, deliver='discord')\n"
            "jid = j.get('id') if isinstance(j, dict) else j\n"
            "if sys.argv[4] == '1': pause_job(jid)\n"
            "print(jid)")
    r = subprocess.run([PY, "-c", code, prompt, name, schedule, "1" if pause else "0"], cwd=os.path.join(HERMES, "hermes-agent"),
                       env={**os.environ, "HERMES_HOME": profile_home}, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        return False, r.stderr.strip()[-200:]
    return True, (r.stdout.strip().splitlines() or [""])[-1]


def hand_to_ganja(date, c):
    prompt = (
        "CAK3D tapped 'Have the Garden set it up' on this coupon from ROACH CLIPS (%s):\n- %s (%s)\n- What: %s\n- Why it fits: %s\n"
        "- Works with: %s\n- Price: %s\n- Links: %s\n\n"
        "Figure out where it belongs (which device), check it's compatible, and set it up if the Garden agents can do it safely and for FREE "
        "(inspect first, back up before changes, keep a rollback path, never print or store secrets). Never buy anything, start trials that "
        "need a card, or create accounts — for those, give CAK3D short exact steps instead. If you add a new app or service, add a listing for it "
        "(no passwords) to the vault's 00_Command/The Green Thumb.json via ssh cak3d. Your final reply is posted to Discord. " + RESULT_RULE
    ) % (date, c.get("title"), c.get("category") or "", c.get("what") or "", c.get("why") or "", c.get("fits") or "", c.get("price") or "?",
         ", ".join(l.get("url", "") for l in c.get("links") or [] if isinstance(l, dict)))
    return create_job(HERMES, prompt, "Roach Clips set-up: " + str(c.get("title"))[:60])


def start_plan(date, item, item_no):
    """B.I.G's gateway is only up for shifts, so his one-off plan job runs through relay-step (start, run, stop);
    then the plan page is built and CAK3D gets a notice on The Corner Chronicle."""
    facts = json.dumps({k: item.get(k) for k in ("item_no", "title", "tag", "price", "desc", "how", "income_week", "tend", "upfront",
                                                  "weekly_cost", "risk", "links")}, ensure_ascii=False, indent=1)
    prompt = open(os.path.join(ROOT, "prompts", "big_plan_prompt.txt")).read() \
        .replace("@@ITEM@@", facts).replace("@@ITEM_NO@@", item_no).replace("@@DATE@@", date)
    name = "B.I.G plan: %s" % item_no
    ok, jid = create_job(os.path.join(HERMES, "profiles", "big"), prompt, name, schedule="0 0 1 1 *", pause=True)
    if not ok:
        return False, jid
    cmd = ("%s/bin/relay-step.sh big %s; %s %s/build_clips.py; [ -f %s/guides/%s.html ] && %s %s/notify.py %s %s %s") % (
        HERMES, sh(name), PY, ROOT, SITE, item_no, PY, NEWSSTAND, sh("📋 B.I.G's plan is ready"), sh(str(item.get("title") or item_no)[:80]),
        sh("/roach-clips/guides/%s.html" % item_no))
    subprocess.Popen(["systemd-run", "--user", "--collect", "--unit=big-plan-%s-%s" % (item_no.lower(), dt.datetime.now().strftime("%H%M%S")),
                      "/bin/bash", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True, jid


def plans_state():
    st = jload(os.path.join(ROOT, "plans", "state.json"), {})
    for no, v in st.items():   # a plan page on disk means it's done
        if os.path.exists(os.path.join(SITE, "guides", no + ".html")):
            v["status"], v["url"] = "ready", "guides/%s.html" % no
        elif v.get("status") == "writing" and v.get("at", "") < (dt.datetime.now() - dt.timedelta(hours=3)).isoformat():
            v["status"] = "failed"
    return st


def followup(date):
    f = os.path.join(ROOT, "jobs", date + ".json")
    st, changed = jload(f, {}), False
    for v in st.values():
        jid = v.get("hermes_job")
        if v.get("status") != "approved" or v.get("result_status") or not re.fullmatch(r"[0-9a-f]{6,32}", str(jid or "")):
            continue
        outs = sorted(glob.glob(os.path.join(HERMES, "cron", "output", jid, "*.md")))
        if not outs:
            continue
        txt = open(outs[-1], errors="ignore").read()
        m = re.search(r"RESULT:\s*(OK|FAILED|NEEDS CAK3D)\s*[—\-:]*\s*(.*)", txt[txt.rfind("## Response"):] if "## Response" in txt else txt)
        v["result_status"] = {"OK": "ok", "FAILED": "failed", "NEEDS CAK3D": "needs"}[m.group(1)] if m else "ok"
        v["result"] = (m.group(2).strip() if m else "finished — see Discord")[:160]
        changed = True
    if changed:
        with LOCK:
            jsave(f, st)
        subprocess.run([sys.executable, os.path.join(ROOT, "build_clips.py"), "--offline"], capture_output=True, timeout=120)
    return st


class Handler(gw.Handler):
    ROOT = ROOT

    def get_api(self, p):
        if p == "/api/plans":
            self.json(200, plans_state())
            return True
        if p == "/api/jobs":
            m = re.search(r"date=(\d{4}-\d{2}-\d{2})", self.path)
            self.json(200, followup(m.group(1)) if m else {})
            return True

    def post_api(self, p):
        if p == "/api/plan":
            req = self.body()
            date, idx = str(req.get("date")), int(req.get("idx"))
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)
            item = (jload(os.path.join(SITE, "data", "market-%s.json" % date), {}).get("items") or [])[idx]
            no = re.sub(r"[^A-Za-z0-9-]", "", str(item.get("item_no") or "%s-%d" % (date, idx + 1)))
            with LOCK:
                st = plans_state()
                if st.get(no, {}).get("status") in ("writing", "ready"):
                    s_ = st[no]["status"]
                    self.json(200, {"ok": True, "status": s_, "url": st[no].get("url"),
                                    "message": "B.I.G is already writing this one." if s_ == "writing" else "The plan is ready."})
                    return True
                ok, info = start_plan(date, item, no)
                if not ok:
                    self.json(500, {"ok": False, "message": "Couldn't reach B.I.G: " + info})
                    return True
                st[no] = {"status": "writing", "title": item.get("title"), "date": date, "idx": idx, "job": info,
                          "at": dt.datetime.now().isoformat(timespec="seconds")}
                jsave(os.path.join(ROOT, "plans", "state.json"), st)
            subprocess.Popen([sys.executable, os.path.join(ROOT, "build_clips.py"), "--offline"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.json(200, {"ok": True, "status": "writing",
                            "message": "B.I.G is on it — he researches and writes the full plan (about 15–30 min). You'll get a notice when it's ready."})
            return True
        if p != "/api/jobs":
            return False
        req = self.body()
        if req.get("kind") == "market":   # "not now" on a Wish-Book item: nothing to record
            self.json(200, {"ok": True, "message": "Okay, not now."})
            return True
        try:
            date, idx, decision = str(req.get("date")), int(req.get("idx")), str(req.get("decision"))
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) and decision in ("approve", "clip", "dismiss") and req.get("kind") == "coupon"
            c = (jload(os.path.join(SITE, "data", date + ".json"), {}).get("coupons") or [])[idx]
        except Exception:
            self.json(400, {"ok": False, "message": "That coupon couldn't be found."})
            return True
        key, f = "coupon:%d" % idx, os.path.join(ROOT, "jobs", date + ".json")
        with LOCK:
            st = jload(f, {})
            if decision == "approve" and st.get(key, {}).get("status") == "approved":
                self.json(200, {"ok": True, "message": "Already on it."})
                return True
            entry = {"status": {"approve": "approved", "clip": "clipped", "dismiss": "dismissed"}[decision], "kind": "coupon",
                     "at": dt.datetime.now().isoformat(timespec="seconds"), "title": c.get("title"), "agent": "Ganja"}
            if decision == "approve":
                ok, info = hand_to_ganja(date, c)
                if not ok:
                    self.json(500, {"ok": False, "message": "Couldn't hand it to Ganja: " + info})
                    return True
                entry["hermes_job"] = info
            st[key] = entry
            jsave(f, st)
        subprocess.Popen([sys.executable, os.path.join(ROOT, "build_clips.py"), "--offline"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.json(200, {"ok": True, "message": {"approve": "On it! Ganja sets it up (free things only) — the result shows on your clip board and in Discord.",
                                                "clip": "✂ Clipped — it's on your clip board.", "dismiss": "Okay, skipped."}[decision]})
        return True


if __name__ == "__main__":
    gw.run(Handler, sys.argv[1], sys.argv[2], int(sys.argv[3]))
