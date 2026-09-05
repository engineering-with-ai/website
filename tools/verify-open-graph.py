#!/usr/bin/env python3
"""Verify Open Graph / Twitter Card meta tags for engineeringwithai.org.

Checks the tag set that LinkedIn, Facebook, and X require for rich link
previews (og:title, og:description, og:image, og:url) plus the extras that
make the large-image card render correctly.

By default it inspects the local ``index.html``. Pass ``--url`` to inspect a
deployed page instead; that mode additionally fetches ``og:image`` and asserts
it is publicly reachable, is an image, and is 1200x630.

Usage:
    python tools/verify-open-graph.py
    python tools/verify-open-graph.py --url https://engineeringwithai.org
"""

from __future__ import annotations

import argparse
import io
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://engineeringwithai.org/"
IMAGE_URL = "https://engineeringwithai.org/og-image.png"
IMAGE_SIZE = (1200, 630)


class MetaCollector(HTMLParser):
    """Collect <meta> content keyed by name/property, and <link rel> hrefs."""

    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.links: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "meta":
            key = a.get("property") or a.get("name")
            if key and "content" in a:
                self.meta[key.lower()] = a["content"]
        elif tag == "link" and "rel" in a and "href" in a:
            self.links[a["rel"].lower()] = a["href"]


def load_html(source: str | None) -> str:
    if source is None:
        return (REPO_ROOT / "index.html").read_text(encoding="utf-8")
    req = urllib.request.Request(source, headers={"User-Agent": "og-verify/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - trusted URL
        return resp.read().decode("utf-8", "replace")


def check_tags(meta: dict[str, str], links: dict[str, str]) -> list[str]:
    """Return a list of failure messages; empty means every assertion passed."""
    failures: list[str] = []

    def want(key: str, expected: str | None = None) -> None:
        value = meta.get(key, "").strip()
        if not value:
            failures.append(f"missing <meta> {key}")
        elif expected is not None and value != expected:
            failures.append(f"{key} = {value!r}, expected {expected!r}")

    want("description")
    want("og:type", "website")
    want("og:site_name")
    want("og:title")
    want("og:description")
    want("og:url", SITE_URL)
    want("og:image", IMAGE_URL)
    want("og:image:width", str(IMAGE_SIZE[0]))
    want("og:image:height", str(IMAGE_SIZE[1]))
    want("og:image:alt")
    want("twitter:card", "summary_large_image")
    want("twitter:title")
    want("twitter:description")
    want("twitter:image", IMAGE_URL)

    for key in ("og:image", "twitter:image"):
        value = meta.get(key, "")
        if value and not value.startswith("https://"):
            failures.append(f"{key} must be an absolute https URL, got {value!r}")

    if links.get("canonical", "").strip() != SITE_URL:
        failures.append(f"canonical link = {links.get('canonical')!r}, expected {SITE_URL!r}")

    return failures


def check_image_reachable(url: str) -> list[str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "og-verify/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            content_type = resp.headers.get("Content-Type", "")
            body = resp.read()
    except Exception as exc:  # noqa: BLE001 - report any fetch failure verbatim
        return [f"og:image not reachable: {exc}"]

    failures: list[str] = []
    if not content_type.startswith("image/"):
        failures.append(f"og:image Content-Type is {content_type!r}, expected image/*")
    try:
        from PIL import Image

        size = Image.open(io.BytesIO(body)).size
        if size != IMAGE_SIZE:
            failures.append(f"og:image is {size[0]}x{size[1]}, expected {IMAGE_SIZE[0]}x{IMAGE_SIZE[1]}")
    except ImportError:
        print("  (PIL not installed - skipping og:image dimension check)")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Inspect a deployed page instead of local index.html")
    args = parser.parse_args()

    collector = MetaCollector()
    collector.feed(load_html(args.url))

    failures = check_tags(collector.meta, collector.links)
    if args.url:
        failures += check_image_reachable(collector.meta.get("og:image", IMAGE_URL))

    target = args.url or str(REPO_ROOT / "index.html")
    if failures:
        print(f"FAIL  {target}")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"PASS  {target}  (all Open Graph / Twitter Card assertions hold)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
