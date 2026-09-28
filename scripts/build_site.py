#!/usr/bin/env python3
"""Build the Monday Morning Drip website from content/issues/*.json.

Usage: python3 scripts/build_site.py

Writes into docs/ (served by GitHub Pages):
  index.html                     the current issue
  issues/<date>-issue-<n>.html   one page per issue
  archive.html                   all issues
  feed.xml, podcast.xml          RSS feeds (written issues, audio episodes)
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
:root{--teal:#0e6e73;--teal-dk:#0a5357;--coral:#e2574c;--purple:#6b4c9a;--slate:#44525f;--gold:#f4b73f;
--ink:#1d2733;--muted:#5a6776;--line:#dfe4e9;--cream:#fff6e0;--blush:#fdecea;--mint:#e3f3f2;
--gray:#f2f4f6;--page:#f5f3ee;--card:#ffffff;--serif:Georgia,'Times New Roman',serif}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--page);color:var(--ink);font:16px/1.55 Helvetica,Arial,sans-serif}
a{color:var(--teal)}
.w{max-width:1120px;margin:0 auto;padding:0 24px}

/* sticky top bar */
.top{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.94);backdrop-filter:blur(6px);
  border-bottom:1px solid var(--line)}
.top .w{display:flex;align-items:center;gap:16px;min-height:62px}
.brand{font:bold 22px/1.1 var(--serif);color:var(--teal);text-decoration:none;flex:1}
.brand span{color:var(--coral)}
.brand small{display:block;font:italic 13px var(--serif);color:var(--muted);font-weight:normal}
.pills{display:flex;gap:8px}
.pill{text-decoration:none;font-weight:bold;font-size:14px;padding:9px 16px;border-radius:999px;
  border:2px solid var(--teal);color:var(--teal);white-space:nowrap}
.pill.on{background:var(--teal);color:#fff}
.pill:hover{box-shadow:0 2px 8px rgba(14,110,115,.25)}

/* hero */
.hero{background:var(--cream);border-bottom:4px solid var(--teal)}
.hero .w{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:40px;padding-top:40px;padding-bottom:40px;align-items:start}
.kicker{font-size:12px;letter-spacing:1.5px;color:var(--coral);font-weight:bold;text-transform:uppercase}
.hero h1{font:bold 46px/1.08 var(--serif);margin:10px 0 14px;color:var(--ink)}
.hero .lede{font-size:18px;line-height:1.6;margin:0}
.inissue{margin-top:18px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.inissue b{font-size:12px;letter-spacing:1px;color:var(--muted);text-transform:uppercase;margin-right:2px}
.inissue a{background:#fff;border:1px solid var(--line);border-radius:999px;padding:5px 12px;font-size:14px;
  text-decoration:none;color:var(--ink)}
.inissue a:hover{border-color:var(--teal);color:var(--teal)}
.side-hero{display:flex;flex-direction:column;gap:14px}
.listen{background:var(--teal);color:#fff;border-radius:16px;padding:18px 18px 16px;box-shadow:0 6px 20px rgba(14,110,115,.25)}
.listen .lt{font:bold 20px var(--serif)}
.listen .ls{font-size:13px;color:#d6ecea;margin:2px 0 12px}
.listen audio{width:100%;display:block}
.listen a{color:#fff}
.meta{font-size:14px;color:var(--muted)}
.ainote{border:1px dashed #d9cfae;border-radius:10px;padding:10px 12px;font-size:12.5px;color:var(--muted);background:rgba(255,255,255,.5)}
.older{background:var(--blush);border-radius:10px;padding:10px 14px;font-size:14px}

/* body grid */
.grid{display:grid;grid-template-columns:minmax(0,1.75fr) minmax(0,1fr);gap:40px;padding-top:36px;padding-bottom:20px}
.aside{position:sticky;top:84px;align-self:start;display:flex;flex-direction:column;gap:22px}
.sec{display:flex;align-items:center;gap:10px;margin:0 0 14px;font-size:12px;font-weight:bold;letter-spacing:1.5px;white-space:nowrap;text-transform:uppercase}
.sec::after{content:"";flex:1;border-bottom:2px solid currentColor;opacity:.8}
.block{margin-bottom:36px}
.more{font-weight:bold;text-decoration:none;white-space:nowrap}
.chip{display:inline-block;font-size:10.5px;font-weight:bold;letter-spacing:.5px;padding:3px 8px;border-radius:999px;margin-right:4px;text-transform:uppercase;vertical-align:middle}

/* top reads */
.card{background:var(--card);border-radius:16px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.06),0 6px 18px rgba(0,0,0,.04);
  display:grid;grid-template-columns:64px minmax(0,1fr);overflow:hidden;scroll-margin-top:84px}
.card .num{background:var(--c);color:#fff;font:bold 34px var(--serif);display:flex;justify-content:center;padding-top:18px}
.card .in{padding:18px 22px 20px}
.card h3{font:bold 23px/1.25 var(--serif);margin:10px 0 12px}
.card ul{margin:0 0 12px;padding-left:20px}.card li{margin-bottom:8px}.card li::marker{color:var(--c);font-weight:bold}
.tip{background:var(--gray);border-left:4px solid var(--c);border-radius:0 10px 10px 0;padding:10px 14px;font-size:15px;margin:4px 0 12px}
.tip b{color:var(--c)}
.cite{font-size:12.5px;color:var(--muted)}
.btn{display:inline-block;font-size:13px;font-weight:bold;color:#fff;background:var(--c);text-decoration:none;padding:8px 16px;border-radius:999px;margin:12px 6px 0 0}
.btn:hover{filter:brightness(1.1)}

/* sidebar */
.cal{background:var(--card);border-radius:16px;padding:18px 18px 6px;box-shadow:0 1px 3px rgba(0,0,0,.06);border-top:5px solid var(--coral)}
.ev{display:flex;gap:12px;align-items:flex-start;padding-bottom:14px;font-size:14.5px;line-height:1.45}
.date{flex:0 0 50px;border:2px solid var(--coral);border-radius:8px;overflow:hidden;text-align:center;background:#fff}
.date .m{background:var(--coral);color:#fff;font-size:10px;font-weight:bold;letter-spacing:1px;padding:2px 0}
.date .d{font:bold 20px var(--serif);padding:2px 0 3px}
.news{background:var(--mint);border-radius:14px;padding:16px 18px;margin-bottom:12px;font-size:14.5px}

/* card grids */
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}
.tile{background:var(--card);border-radius:14px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.06);font-size:15px;border-top:4px solid var(--line)}
.tile .chips{margin-bottom:8px}
.tile .au{color:var(--muted);font-size:13px}
.tiles.quick .tile{font-size:14.5px;background:transparent;box-shadow:none;border:1px solid var(--line);border-top:4px solid var(--line)}

.foot{background:var(--card);border-radius:14px;padding:16px 18px;font-size:13px;color:var(--muted);margin:10px 0 18px;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.sign{text-align:center;font-size:13px;color:var(--muted);padding:6px 0 18px}
.nav{display:flex;justify-content:space-between;gap:12px;font-size:15px;padding-bottom:40px}
.nav a{font-weight:bold;text-decoration:none}

/* archive */
.arch-hero h1{font-size:40px}
.issues{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px;padding:36px 0 50px}
.issue{display:block;background:var(--card);border-radius:16px;padding:20px 22px;text-decoration:none;color:var(--ink);
  box-shadow:0 1px 3px rgba(0,0,0,.06),0 6px 18px rgba(0,0,0,.04);border-top:5px solid var(--teal);transition:transform .15s}
.issue:hover{transform:translateY(-2px)}
.issue .n{font-size:12px;font-weight:bold;letter-spacing:1.5px;color:var(--coral);text-transform:uppercase}
.issue h2{font:bold 22px/1.25 var(--serif);margin:6px 0 8px;color:var(--teal)}
.issue p{margin:0 0 10px;font-size:14.5px;color:var(--muted)}
.issue .tags{font-size:13px;color:var(--ink)}
.badges{margin-top:8px;min-height:20px}
.badge{display:inline-block;background:var(--teal);color:#fff;border-radius:999px;font-size:11px;font-weight:bold;padding:2px 9px;margin-right:6px}
.issue.latest{border-top-color:var(--coral)}

@media (max-width:900px){
  .hero .w,.grid{grid-template-columns:minmax(0,1fr);gap:24px}
  .aside{display:contents}
  .aside .s-cal{order:-1}.aside .s-news{order:1}
  .hero h1{font-size:34px}
}
@media (max-width:560px){
  .w{padding:0 16px}
  .top .w{flex-wrap:wrap;gap:8px;padding-top:8px;padding-bottom:10px}
  .brand{font-size:19px}.brand small{display:none}
  .pills{width:100%}.pill{flex:1;text-align:center;padding:8px 10px}
  .hero .w{padding-top:26px;padding-bottom:26px}
  .hero h1{font-size:29px}.hero .lede{font-size:16.5px}
  .card{grid-template-columns:minmax(0,1fr)}
  .card .num{justify-content:flex-start;padding:8px 18px;font-size:22px}
  .card .in{padding:14px 16px 16px}.card h3{font-size:20px}
  .tiles,.issues{grid-template-columns:minmax(0,1fr)}
}
"""

AI_NOTE = ("<b>Heads up:</b> this digest is AI-generated (compiled by Claude) and may not have been "
           "fully checked by me. Summaries can contain errors, so please verify with the original source before citing or acting on anything.")

SITE = {}


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


def slug(d):
    return f"{d['date_iso']}-issue-{d['issue']}"


def page(title, body, desc="", depth=0):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE.get('base', '')}cover.png">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>☕</text></svg>">
<link rel="alternate" type="application/rss+xml" title="The Monday Morning Drip" href="{up}feed.xml">
<link rel="alternate" type="application/rss+xml" title="The Monday Morning Drip (podcast)" href="{up}podcast.xml">
<style>{CSS}</style></head>
<body>{body}</body></html>
"""


def topbar(active, depth):
    up = "../" * depth
    cur = "pill on" if active == "current" else "pill"
    arc = "pill on" if active == "archive" else "pill"
    return (f'<header class="top"><div class="w">'
            f'<a class="brand" href="{up}index.html">The Monday Morning <span>Drip</span>'
            f'<small>Pediatric med ed for the busy educator</small></a>'
            f'<nav class="pills" aria-label="Site">'
            f'<a class="{cur}" href="{up}index.html">&#9749; Current issue</a>'
            f'<a class="{arc}" href="{up}archive.html">&#128218; Archive ({SITE["count"]})</a>'
            f'</nav></div></header>')


def link_more(url, label="Full text"):
    return f' <a class="more" href="{esc(url)}">{esc(label)} &rsaquo;</a>' if url else ""


def render_issue(d, depth, active=None):
    up = "../" * depth
    p = [topbar(active, depth)]

    # hero
    side = []
    if active is None:
        side.append(f'<div class="older">You&#39;re reading an earlier issue. '
                    f'<a class="more" href="{up}index.html">Go to the current issue &rsaquo;</a></div>')
    if d.get("podcast"):
        pod = d["podcast"]
        mins = max(1, round(pod["seconds"] / 60))
        side.append(f'<section class="listen"><div class="lt">&#127911; Listen to this issue</div>'
                    f'<div class="ls">~{mins}-min audio edition &middot; AI-narrated &middot; '
                    f'<a href="{up}podcast.xml">Subscribe</a></div>'
                    f'<audio controls preload="none" src="{up}{esc(pod["file"])}"></audio></section>')
    side.append(f'<div class="meta">&#9749; Freshly brewed every Monday &middot; ~5-min read</div>')
    side.append(f'<div class="ainote">{AI_NOTE}</div>')

    jumps = ""
    if d.get("in_this_issue"):
        jumps = ('<div class="inissue"><b>In this issue</b>'
                 + "".join(f'<a href="#read-{i}">{esc(x)}</a>' for i, x in enumerate(d["in_this_issue"], 1))
                 + "</div>")
    p.append(f'<section class="hero"><div class="w"><div>'
             f'<div class="kicker">Issue {d["issue"]} &middot; {esc(d["week_label"])}</div>'
             f'<h1>{d["breath_title"]}</h1><p class="lede">{d["breath_text"]}</p>{jumps}</div>'
             f'<div class="side-hero">{"".join(side)}</div></div></section>')

    # main column: top reads
    main = ['<div class="sec" style="color:var(--teal)">Top reads</div>']
    for i, t in enumerate(d["top"], 1):
        c = color(t.get("color", "teal"))
        bullets = "".join(f"<li>{b}</li>" for b in t["bullets"])
        links = "".join(f'<a class="btn" href="{esc(l["url"])}">{esc(l["label"])} &rsaquo;</a>' for l in t["links"])
        main.append(f'<article class="card" id="read-{i}" style="--c:{c}"><div class="num">{i}</div><div class="in">'
                    f'{chips(t["chips"])}<h3>{t["headline"]}</h3><ul>{bullets}</ul>'
                    f'<div class="tip"><b>{esc(t["tip_label"])}</b> {t["tip"]}</div>'
                    f'<div class="cite">{t["citation"]}</div>{links}</div></article>')

    # sidebar: calendar + news
    aside = []
    if d.get("calendar"):
        ev = []
        for e in d["calendar"]:
            ev.append(f'<div class="ev"><div class="date"><div class="m">{esc(e["mon"])}</div><div class="d">{esc(e["day"])}</div></div>'
                      f'<div>{e["text"]}{link_more(e.get("url"), e.get("link_label", "Details"))}</div></div>')
        aside.append('<section class="s-cal"><div class="sec" style="color:var(--coral)">Mark your calendar</div>'
                     f'<div class="cal">{"".join(ev)}</div></section>')
    if d.get("news"):
        items = []
        for n in d["news"]:
            links = "".join(link_more(l["url"], l["label"]) for l in n.get("links", []))
            items.append(f'<div class="news">{n["text"]}{links}</div>')
        aside.append('<section class="s-news"><div class="sec" style="color:var(--teal)">APPD &amp; GME news</div>'
                     + "".join(items) + "</section>")

    p.append(f'<div class="w grid"><main>{"".join(main)}</main><aside class="aside">{"".join(aside)}</aside></div>')

    # full-width card grids
    lower = []
    if d.get("acadpeds"):
        tiles = []
        for a in d["acadpeds"]:
            au = f' <span class="au">{esc(a["authors"])}</span>' if a.get("authors") else ""
            c = color(a["chips"][0][1]) if a.get("chips") else "var(--line)"
            tiles.append(f'<div class="tile" style="border-top-color:{c}"><div class="chips">{chips(a.get("chips", []))}</div>'
                         f'{a["text"]}{au}{link_more(a.get("url"), a.get("link_label", "Full text"))}</div>')
        lower.append('<section class="block"><div class="sec" style="color:var(--slate)">From Academic Pediatrics</div>'
                     f'<div class="tiles">{"".join(tiles)}</div></section>')
    if d.get("quick"):
        tiles = []
        for q in d["quick"]:
            c = color(q["chips"][0][1]) if q.get("chips") else "var(--line)"
            tiles.append(f'<div class="tile" style="border-top-color:{c}"><div class="chips">{chips(q.get("chips", []))}</div>'
                         f'{q["text"]}{link_more(q.get("url"), q.get("link_label", "Full text"))}</div>')
        lower.append('<section class="block"><div class="sec" style="color:var(--slate)">Quick hits</div>'
                     f'<div class="tiles quick">{"".join(tiles)}</div></section>')
    if d.get("footer"):
        lower.append(f'<div class="foot"><b style="color:var(--ink)">Sources &amp; caveats:</b> {d["footer"]}</div>')
    lower.append('<div class="sign">The Monday Morning Drip &middot; AI-generated by Claude, not fully reviewed &middot; see you next Monday &#9749;</div>')
    p.append(f'<div class="w">{"".join(lower)}</div>')
    return "".join(p)


def nav(prev, nxt, depth):
    up = "../" * depth
    left = f'<a href="{up}issues/{slug(prev)}.html">&lsaquo; Issue {prev["issue"]}</a>' if prev else "<span></span>"
    mid = f'<a href="{up}archive.html">All issues</a>'
    right = f'<a href="{up}issues/{slug(nxt)}.html">Issue {nxt["issue"]} &rsaquo;</a>' if nxt else "<span></span>"
    return f'<div class="w"><nav class="nav">{left}{mid}{right}</nav></div>'


def render_archive(issues):
    cards = []
    for d in reversed(issues):
        latest = d is issues[-1]
        badges = ('<span class="badge" style="background:var(--coral)">Latest</span>' if latest else "") + \
                 ('<span class="badge">&#127911; Audio</span>' if d.get("podcast") else "")
        cards.append(f'<a class="issue{" latest" if latest else ""}" href="issues/{slug(d)}.html">'
                     f'<div class="n">Issue {d["issue"]} &middot; {esc(d["week_label"])}</div><div class="badges">{badges}</div>'
                     f'<h2>{d["breath_title"]}</h2><p>{d["breath_text"]}</p>'
                     f'<div class="tags">{" &bull; ".join(esc(x) for x in d.get("in_this_issue", []))}</div></a>')
    hero = (f'<section class="hero arch-hero"><div class="w" style="grid-template-columns:minmax(0,1fr)">'
            f'<div><div class="kicker">Archive &middot; {len(issues)} issues</div><h1>Every issue of the Drip</h1>'
            f'<p class="lede">Pediatric med ed for the busy educator, one Monday at a time. '
            f'Issues with &#127911; have an audio edition you can play on the page or '
            f'<a href="podcast.xml">subscribe to as a podcast</a>.</p></div>'
            f'<div class="ainote">{AI_NOTE}</div></div></section>')
    return topbar("archive", 0) + hero + f'<div class="w"><div class="issues">{"".join(cards)}</div></div>'


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


def podcast_feed(issues, base):
    items = []
    for d in reversed(issues):
        pod = d.get("podcast")
        if not pod:
            continue
        url = f"{base}issues/{slug(d)}.html"
        s = pod["seconds"]
        items.append(
            f"<item><title>Issue {d['issue']}: {esc(html.unescape(d['breath_title']))}</title>"
            f"<link>{url}</link><guid isPermaLink=\"false\">{base}{pod['file']}</guid>"
            f"<pubDate>{rfc822(d['date_iso'])}</pubDate>"
            f"<description>{esc(html.unescape(d['breath_text']))} This episode is AI-generated and may not be fully reviewed; "
            f"see the written issue for links: {url}</description>"
            f"<enclosure url=\"{base}{pod['file']}\" length=\"{pod['bytes']}\" type=\"audio/mpeg\"/>"
            f"<itunes:duration>{s // 60}:{s % 60:02d}</itunes:duration><itunes:episode>{d['issue']}</itunes:episode>"
            f"<itunes:explicit>false</itunes:explicit></item>")
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><channel>'
            f"<title>The Monday Morning Drip</title><link>{base}</link><language>en-us</language>"
            "<description>Pediatric med ed for the busy educator: a short audio edition of each weekly issue. "
            "AI-generated and AI-narrated; may not be fully reviewed. Verify with original sources.</description>"
            "<itunes:author>The Monday Morning Drip</itunes:author>"
            "<itunes:summary>Pediatric med ed for the busy educator. AI-generated weekly digest.</itunes:summary>"
            f'<itunes:image href="{base}cover.png"/><image><url>{base}cover.png</url>'
            f"<title>The Monday Morning Drip</title><link>{base}</link></image>"
            '<itunes:category text="Education"/><itunes:category text="Health &amp; Fitness">'
            '<itunes:category text="Medicine"/></itunes:category>'
            "<itunes:explicit>false</itunes:explicit><itunes:type>episodic</itunes:type>"
            + "".join(items) + "</channel></rss>\n")


def main():
    issues = [json.loads(p.read_text()) for p in sorted(CONTENT.glob("*.json"))]
    issues.sort(key=lambda d: (d["date_iso"], d["issue"]))
    if not issues:
        raise SystemExit("no issues found in content/issues")
    base = json.loads((ROOT / "content" / "site.json").read_text())["base_url"]
    SITE.update(latest=issues[-1], count=len(issues), base=base)
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
    (OUT / "archive.html").write_text(
        page("Archive - The Monday Morning Drip", render_archive(issues), "Every issue of The Monday Morning Drip."))

    (OUT / "feed.xml").write_text(rss(issues, base))
    (OUT / "podcast.xml").write_text(podcast_feed(issues, base))
    print(f"built {len(issues)} issues; latest = issue {latest['issue']} ({latest['date_iso']})")


if __name__ == "__main__":
    main()
