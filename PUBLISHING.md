# Weekly publishing

The website is built from one JSON file per issue in `content/issues/`.
GitHub Pages serves the generated `docs/` folder at
https://bethlinkstorwekar.github.io/Monday_Morning_Drip/

## Each week (run by the "Publish Monday Morning Drip site" routine)

1. Find the newest sent issue in Gmail. Search:
   `from:bethlinks@gmail.com (subject:"The Drip" OR subject:"Monday Morning Drip") newer_than:8d -subject:test -subject:sample`
   and read it with `get_message` (FULL_CONTENT).
2. Read the issue number from the header ("PEDIATRIC MED ED · ISSUE N").
   If `content/issues/*-issue-N.json` already exists, stop: nothing to publish.
3. Write `content/issues/<YYYY-MM-DD>-issue-<N>.json` using the same fields as
   the existing files. Copy the text exactly as sent; do not rewrite or add
   findings. Unwrap Gmail links: `https://www.google.com/url?q=<REAL URL>&source=gmail...`
   becomes `<REAL URL>`. Colors: `teal`, `coral`, `purple`, `slate`.
4. Run `python3 scripts/build_site.py` and check that it prints the new issue.
5. Commit `content/` and `docs/` and push to the publishing branch.

## Fields

| field | meaning |
| --- | --- |
| `issue`, `date_iso`, `week_label` | issue number, Monday's date, "Week of ..." label |
| `breath_title`, `breath_text` | "This week in one breath" |
| `in_this_issue` | the short labels |
| `calendar[]` | `mon`, `day`, `text`, optional `link_label` + `url` |
| `top[]` | `color`, `chips` ([label, color] pairs), `headline`, `bullets`, `tip_label`, `tip`, `citation`, `links` |
| `news[]` | `text`, `links` |
| `acadpeds[]`, `quick[]` | `chips`, `text`, optional `authors`, `url`, `link_label` |
| `footer` | sources and caveats |

Text fields may contain `<b>`, `<i>` and HTML entities.
