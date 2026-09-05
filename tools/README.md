# tools/

Build- and check-time helpers. Not deployed — `.gitlab-ci.yml` excludes
`tools/*` from the S3 sync.

## verify-open-graph.py

Asserts the Open Graph / Twitter Card meta tags LinkedIn, Facebook, and X
need for rich link previews.

```sh
python3 tools/verify-open-graph.py                              # local index.html
python3 tools/verify-open-graph.py --url https://engineeringwithai.org  # deployed page + og:image fetch
```

Exit code is non-zero on any failed assertion.

## og-image/

Source for `og-image.png` (the 1200x630 share card at the repo root, served
at `https://engineeringwithai.org/og-image.png`).

```sh
bash tools/og-image/build.sh
```

`build.sh` renders `template.html` with headless Chromium — required because
the card uses the Google-hosted brand fonts (Playfair Display, DM Mono,
Outfit) that are not installed on the build host. Edit `template.html` and
re-run to regenerate. The card deliberately mirrors the site hero.
