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
   **Redact personal details for the public site:** drop any "Congrats!" chip
   or other personal shout-out, and replace mentions of OHSU (e.g. "may need
   an OHSU login") with a generic phrase ("an institutional login"). Keep
   author names that are part of a normal citation. The AI-generated
   disclaimer is added by the build script; don't remove it.
4. **Podcast.** Write `content/podcast/<YYYY-MM-DD>-issue-<N>.txt`, a spoken
   script of about 4-6 minutes (use the existing scripts as the model):
   - Use only what the issue says; never add findings, numbers or authors.
   - Open with the title and date, then say the episode is AI-generated, may
     not have been fully checked, and should be verified before citing.
   - Write for the ear: no URLs, DOIs or PMIDs; round numbers sensibly
     ("about 68 percent"); spell out abbreviations on first use where the
     issue does; one idea per paragraph (a blank line = a short pause).
   - Cover: one-breath summary, calendar, the 3 top reads with their tips,
     news, Academic Pediatrics, quick hits, then a sign-off that repeats the
     AI caveat and points to the written issue for links.
   - Apply the same redaction rules as the written issue.
   Then run `sh scripts/get_voice.sh` and
   `python3 scripts/make_podcast.py content/podcast/<file>.txt`.
   If the voice can't be downloaded, publish the written issue anyway and say
   the podcast was skipped and why.
5. Run `python3 scripts/build_site.py` and check that it prints the new issue.
6. Commit `content/` and `docs/` and push to the publishing branch.

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
