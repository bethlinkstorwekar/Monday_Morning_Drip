#!/usr/bin/env python3
"""Build the Monday Morning Drip website from issues/*.json.

Usage: python3 scripts/build_site.py

Reads every issue JSON in content/issues/, writes:
  docs/index.html                     latest issue + archive links
  docs/issues/<date>-issue-<n>.html   one page per issue
  docs/archive.html                   list of all issues
GitHub Pages serves the docs/ folder.
"""
import datetime
import email.utils
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "issues"
OUT = ROOT / "docs"

COLORS = {"teal": "#0e6e73", "coral": "#e2574c", "purple": "#6b4c9a", "slate": "#44525f"}

CSS = """
:root{--teal:#0e6e73;--coral:#e2574c;--purple:#6b4c9a;--slate:#44525f;--gold:#f4b73f;
--ink:#1d2733;--muted:#5a6776;--line:#d8dee4;--cream:#fff6e0;--blush:#fdecea;--mint:#e3f3f2;
--gray:#f2f4f6;--page:#eef1f4;--card:#ffffff}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:16px/1.55 Helvetica,Arial,sans-serif}
a{color:var(--teal)}
.wrap{max-width:680px;margin:0 auto;padding:20px 16px 40px}
.sheet{background:var(--card);border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.mast{background:var(--cream);border-top:6px solid var(--teal);border-bottom:4px solid var(--teal);padding:26px 26px 20px}
.kicker{font-size:11px;letter-spacing:1px;color:var(--coral);font-weight:bold;text-transform:uppercase}
.title{font:bold 34px/1.15 Georgia,'Times New Roman',serif;color:var(--teal);margin:6px 0 0}
.title a{color:inherit;text-decoration:none}.title span{color:var(--coral)}
.tag{font:italic 17px Georgia,'Times New Roman',serif;margin-top:4px}
.meta{font-size:14px;color:var(--muted);margin-top:8px}
.body{padding:6px 24px 24px}
.breath{margin-top:20px;background:var(--cream);border-left:5px solid var(--gold);padding:14px 16px}
.label{font-size:11px;font-weight:bold;letter-spacing:1.5px;color:var(--muted)}
.breath h2{font:bold 21px Georgia,'Times New Roman',serif;margin:6px 0}
.breath p{margin:0;line-height:1.6}
.inissue{margin-top:12px;font-size:13px;color:var(--muted)}.inissue b{color:var(--ink)}
.sec{display:flex;align-items:center;gap:10px;margin:28px 0 12px;font-size:12px;font-weight:bold;letter-spacing:1.5px;white-space:nowrap}
.sec::after{content:"";flex:1;border-bottom:2px solid currentColor}
.cal{background:var(--blush);border-radius:10px;padding:16px 16px 4px}
.ev{display:flex;gap:12px;align-items:center;padding-bottom:12px}
.date{flex:0 0 56px;border:2px solid var(--coral);border-radius:8px;overflow:hidden;text-align:center}
.date .m{background:var(--coral);color:#fff;font-size:11px;font-weight:bold;letter-spacing:1px;padding:3px 0}
.date .d{font:bold 22px Georgia,serif;padding:3px 0 4px}
.more{font-weight:bold;text-decoration:none;white-space:nowrap}
.card{border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:16px}
.card .bar{height:5px}
.card .in{padding:14px 18px 16px}
.rank{font:bold 26px/1 Georgia,serif;margin-right:10px;vertical-align:middle}
.chip{display:inline-block;font-size:10px;font-weight:bold;letter-spacing:.5px;padding:2px 7px;border-radius:10px;margin-right:4px;text-transform:uppercase;vertical-align:middle}
.card h3{font:bold 20px/1.3 Georgia,'Times New Roman',serif;margin:10px 0}
.card ul{margin:0 0 8px;padding-left:20px}.card li{margin-bottom:8px}.card li::marker{color:var(--m);font-weight:bold}
.tip{background:var(--gray);border-radius:8px;padding:10px 12px;font-size:14px;margin:4px 0 12px}
.tip b{color:var(--coral)}
.cite{font-size:12px;color:var(--muted)}
.btn{display:inline-block;font-size:13px;font-weight:bold;color:#fff;text-decoration:none;padding:7px 14px;border-radius:16px;margin:10px 6px 0 0}
.news{background:var(--mint);border-radius:10px;padding:14px 16px;margin-bottom:10px}
.ap{border-left:4px solid var(--line);padding:2px 0 2px 14px;margin-bottom:14px}
.ap .au{color:var(--muted);font-size:13px}
.qh{padding:10px 0;border-bottom:1px solid var(--line);font-size:14px}
.foot{background:var(--gray);border-radius:10px;padding:14px 16px;font-size:12px;color:var(--muted);margin-top:22px}
.tabs{display:flex;gap:8px;padding:14px 24px 0;background:var(--card)}
.tab{flex:1;display:block;text-decoration:none;border:2px solid var(--teal);border-radius:10px;padding:10px 14px;color:var(--teal)}
.tab .t{display:block;font:bold 17px Georgia,'Times New Roman',serif}
.tab .sub{display:block;font-size:12px;color:var(--muted);margin-top:2px}
.tab.on{background:var(--teal);color:#fff}.tab.on .sub{color:#d6ecea}
.tab:hover{box-shadow:0 2px 6px rgba(14,110,115,.25)}
.older{margin:14px 24px 0;background:var(--blush);border-radius:8px;padding:10px 14px;font-size:14px}
@media (max-width:520px){.tabs{padding:12px 16px 0}.older{margin:12px 16px 0}.tab{padding:8px 10px}.tab .t{font-size:15px}}
.ainote{margin-top:14px;border:1px dashed var(--line);border-radius:8px;padding:8px 12px;font-size:12px;color:var(--muted)}
.sign{text-align:center;font-size:12px;color:var(--muted);padding:0 20px 20px}
.nav{display:flex;justify-content:space-between;gap:12px;font-size:14px;margin:18px 4px 0}
.arch{list-style:none;margin:0;padding:0}
.arch li{border-bottom:1px solid var(--line);padding:14px 0}
.arch a{font:bold 19px Georgia,serif;text-decoration:none}
.arch .s{color:var(--muted);font-size:14px;margin-top:4px}
@media (max-width:520px){.title{font-size:28px}.mast{padding:22px 18px 16px}.body{padding:4px 16px 20px}}
"""


AI_NOTE = ("<b>Heads up:</b> this digest is AI-generated (compiled by Claude) and may not have been "
           "fully checked by me. Summaries can contain errors, so please verify with the original source before citing or acting on anything.")


def esc(s):
    return html.escape(s, quote=True)


def color(name):
    return COLORS.get(name, name)


def chips(items):
    out = []
    for label, c in items:
        c = color(c)
        out.append(f'<span class="chip" style="color:{c};background:{c}1a">{esc(label)}</span>')
    return "".join(out)


def page(title, body, desc="", depth=0):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>☕</text></svg>">
<link rel="alternate" type="application/rss+xml" title="The Monday Morning Drip" href="{up}feed.xml">
<style>{CSS}</style></head>
<body><div class="wrap">{body}</div></body></html>
"""


SITE = {}


def tabs(active, depth):
    up = "../" * depth
    latest = SITE["latest"]
    cur = "tab on" if active == "current" else "tab"
    arc = "tab on" if active == "archive" else "tab"
    return (f'<nav class="tabs" aria-label="Site">'
            f'<a class="{cur}" href="{up}index.html"><span class="t">&#9749; Current issue</span>'
            f'<span class="sub">Issue {latest["issue"]} &middot; {esc(latest["week_label"])}</span></a>'
            f'<a class="{arc}" href="{up}archive.html"><span class="t">&#128218; Archive</span>'
            f'<span class="sub">All {SITE["count"]} issues</span></a></nav>')


def masthead(kicker, meta, depth, active=None):
    up = "../" * depth
    older = ""
    if active is None:
        older = (f'<div class="older">You&#39;re reading an earlier issue. '
                 f'<a class="more" href="{up}index.html">Go to the current issue &rsaquo;</a></div>')
    return tabs(active, depth) + older + f"""<header class="mast" style="margin-top:14px"><div class="kicker">{kicker}</div>
<div class="title"><a href="{up}index.html">The Monday Morning <span>Drip</span></a></div>
<div class="tag">Pediatric med ed for the busy educator</div>
<div class="meta">{meta}</div>
<div class="ainote">{AI_NOTE}</div></header>"""


def slug(d):
    return f"{d['date_iso']}-issue-{d['issue']}"


def render_issue(d, depth, active=None):
    p = []
    p.append(masthead(f"Pediatric Med Ed &middot; Issue {d['issue']}",
                      f"&#9749; Freshly brewed every Monday<br>{esc(d['week_label'])} &middot; ~5-min read", depth, active))
    p.append('<main class="body">')
    p.append(f'<section class="breath"><div class="label">THIS WEEK IN ONE BREATH</div>'
             f'<h2>{d["breath_title"]}</h2><p>{d["breath_text"]}</p></section>')
    if d.get("in_this_issue"):
        p.append('<div class="inissue"><b>In this issue:</b> ' + " &bull; ".join(esc(x) for x in d["in_this_issue"]) + "</div>")

    if d.get("calendar"):
        p.append('<div class="sec" style="color:var(--coral)">MARK YOUR CALENDAR</div><div class="cal">')
        for e in d["calendar"]:
            link = f' <a class="more" href="{esc(e["url"])}">{esc(e["link_label"])} &rsaquo;</a>' if e.get("url") else ""
            p.append(f'<div class="ev"><div class="date"><div class="m">{esc(e["mon"])}</div><div class="d">{esc(e["day"])}</div></div>'
                     f'<div>{e["text"]}{link}</div></div>')
        p.append("</div>")

    p.append('<div class="sec" style="color:var(--teal)">TOP READS</div>')
    for i, t in enumerate(d["top"], 1):
        c = color(t.get("color", "teal"))
        bullets = "".join(f"<li>{b}</li>" for b in t["bullets"])
        links = "".join(f'<a class="btn" style="background:{c}" href="{esc(l["url"])}">{esc(l["label"])} &rsaquo;</a>' for l in t["links"])
        p.append(f'<article class="card"><div class="bar" style="background:{c}"></div><div class="in">'
                 f'<span class="rank" style="color:{c}">{i}</span>{chips(t["chips"])}'
                 f'<h3>{t["headline"]}</h3><ul style="--m:{c}">{bullets}</ul>'
                 f'<div class="tip"><b>{esc(t["tip_label"])}</b> {t["tip"]}</div>'
                 f'<div class="cite">{t["citation"]}</div>{links}</div></article>')

    def more(item):
        return f' <a class="more" href="{esc(item["url"])}">{esc(item.get("link_label", "Full text"))} &rsaquo;</a>' if item.get("url") else ""

    if d.get("news"):
        p.append('<div class="sec" style="color:var(--teal)">APPD &amp; GME NEWS</div>')
        for n in d["news"]:
            links = "".join(f' <a class="more" href="{esc(l["url"])}">{esc(l["label"])} &rsaquo;</a>' for l in n.get("links", []))
            p.append(f'<div class="news">{n["text"]}{links}</div>')

    if d.get("acadpeds"):
        p.append('<div class="sec" style="color:var(--slate)">FROM ACADEMIC PEDIATRICS</div>')
        for a in d["acadpeds"]:
            au = f' <span class="au">{esc(a["authors"])}</span>' if a.get("authors") else ""
            p.append(f'<div class="ap">{chips(a.get("chips", []))}<br>{a["text"]}{au}{more(a)}</div>')

    if d.get("quick"):
        p.append('<div class="sec" style="color:var(--slate)">QUICK HITS</div>')
        for q in d["quick"]:
            p.append(f'<div class="qh">{chips(q.get("chips", []))}<br>{q["text"]}{more(q)}</div>')

    if d.get("footer"):
        p.append(f'<div class="foot"><b style="color:var(--ink)">Sources &amp; caveats:</b> {d["footer"]}</div>')
    p.append("</main>")
    p.append('<div class="sign">The Monday Morning Drip &middot; AI-generated by Claude, not fully reviewed &middot; see you next Monday &#9749;</div>')
    return '<div class="sheet">' + "".join(p) + "</div>"


def nav(prev, nxt, depth, here_is_index=False):
    up = "../" * depth
    left = f'<a href="{up}issues/{slug(prev)}.html">&lsaquo; Issue {prev["issue"]}</a>' if prev else "<span></span>"
    mid = f'<a href="{up}archive.html">All issues</a>'
    right = f'<a href="{up}issues/{slug(nxt)}.html">Issue {nxt["issue"]} &rsaquo;</a>' if nxt else "<span></span>"
    return f'<nav class="nav">{left}{mid}{right}</nav>'


def rfc822(date_iso):
    y, m, dd = map(int, date_iso.split("-"))
    return email.utils.format_datetime(datetime.datetime(y, m, dd, 13, 0, tzinfo=datetime.timezone.utc))


def rss(issues, base):
    items = []
    for d in reversed(issues):
        url = f"{base}issues/{slug(d)}.html"
        items.append(f"<item><title>Issue {d['issue']}: {esc(html.unescape(d['breath_title']))}</title>"
                     f"<link>{url}</link><guid>{url}</guid><pubDate>{rfc822(d['date_iso'])}</pubDate>"
                     f"<description>{esc(d['breath_text'])}</description></item>")
    return ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
            f"<title>The Monday Morning Drip</title><link>{base}</link>"
            "<description>Pediatric med ed for the busy educator</description>"
            + "".join(items) + "</channel></rss>\n")


def main():
    issues = [json.loads(p.read_text()) for p in sorted(CONTENT.glob("*.json"))]
    issues.sort(key=lambda d: (d["date_iso"], d["issue"]))
    if not issues:
        raise SystemExit("no issues found in content/issues")
    SITE.update(latest=issues[-1], count=len(issues))
    (OUT / "issues").mkdir(parents=True, exist_ok=True)
    (OUT / ".nojekyll").write_text("")

    for i, d in enumerate(issues):
        prev = issues[i - 1] if i > 0 else None
        nxt = issues[i + 1] if i + 1 < len(issues) else None
        body = render_issue(d, 1, "current" if nxt is None else None) + nav(prev, nxt, 1)
        (OUT / "issues" / f"{slug(d)}.html").write_text(
            page(f"Issue {d['issue']} - The Monday Morning Drip", body, html.unescape(d["breath_title"]), 1))

    latest = issues[-1]
    prev = issues[-2] if len(issues) > 1 else None
    (OUT / "index.html").write_text(
        page("The Monday Morning Drip", render_issue(latest, 0, "current") + nav(prev, None, 0),
             "Pediatric med ed for the busy educator. A fresh issue every Monday."))

    rows = []
    for d in reversed(issues):
        rows.append(f'<li><a href="issues/{slug(d)}.html">Issue {d["issue"]}: {d["breath_title"]}</a>'
                    f'<div class="s">{esc(d["week_label"])} &middot; {" &bull; ".join(esc(x) for x in d.get("in_this_issue", []))}</div></li>')
    arch = ('<div class="sheet">' + masthead("Archive", f"{len(issues)} issues so far", 0, "archive")
            + '<main class="body"><div class="sec" style="color:var(--teal)">ALL ISSUES</div><ul class="arch">'
            + "".join(rows) + "</ul></main></div>")
    (OUT / "archive.html").write_text(page("Archive - The Monday Morning Drip", arch))

    base = json.loads((ROOT / "content" / "site.json").read_text())["base_url"]
    (OUT / "feed.xml").write_text(rss(issues, base))
    print(f"built {len(issues)} issues; latest = issue {latest['issue']} ({latest['date_iso']})")


if __name__ == "__main__":
    main()
