#!/usr/bin/env python3
"""Build tutorlawrence.com.

Reads src/ and site.json, writes the finished site to public/.
Run:  python3 build.py
No dependencies beyond the Python standard library.
"""
import hashlib
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "public"
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))

NAV = [
    ("/business-english", "Business English"),
    ("/ielts", "IELTS"),
    ("/exam-prep", "ECL exam prep"),
    ("/packages", "Packages"),
    ("/about", "About"),
]


def price(n):
    return f"{SITE['currency']}{n:,}"


def render_packages(keys):
    rows = []
    for key in keys:
        p = SITE["packages"][key]
        items = "".join(f"<li>{html.escape(i)}</li>" for i in p["includes"])
        rows.append(
            f'<article class="package" id="{key}">'
            f'<div class="package-head"><h3>{html.escape(p["name"])}</h3>'
            f'<p class="package-length">{html.escape(p["length"])}</p></div>'
            f'<ul class="package-includes">{items}</ul>'
            f'<p class="package-price"><span class="mark">{price(p["price"])}</span></p>'
            f"</article>"
        )
    return f'<div class="packages">{"".join(rows)}</div>'


def render_price_list(keys):
    rows = []
    for key in keys:
        p = SITE["packages"][key]
        rows.append(
            f'<li><a href="/packages#{key}"><span class="pl-name">{html.escape(p["name"])}</span>'
            f'<span class="pl-length">{html.escape(p["length"])}</span>'
            f'<span class="pl-price">{price(p["price"])}</span></a></li>'
        )
    return f'<ul class="price-list">{"".join(rows)}</ul>'


def render_nav(current):
    links = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        links.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
    return "".join(links)


def fill(text, extra):
    values = {
        "booking": SITE["booking_url"],
        "email": SITE["email"],
        "lessons": SITE["lessons"],
        "students": SITE["students"],
        "since": SITE["since"],
        "call_minutes": str(SITE["call_minutes"]),
        "lesson_minutes": str(SITE["lesson_minutes"]),
        "site_url": SITE["site_url"],
        "owner": SITE["owner"],
        "year": str(date.today().year),
    }
    values.update(extra)
    text = re.sub(r"\{\{packages:([a-z,]+)\}\}", lambda m: render_packages(m.group(1).split(",")), text)
    text = re.sub(r"\{\{pricelist:([a-z,]+)\}\}", lambda m: render_price_list(m.group(1).split(",")), text)
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), text)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(SRC / "assets", OUT / "assets")
    for item in (SRC / "static").iterdir():
        dest = OUT / item.name
        shutil.copytree(item, dest) if item.is_dir() else shutil.copy2(item, dest)

    css = (OUT / "assets/css/site.css").read_bytes()
    js = (OUT / "assets/js/site.js").read_bytes()
    version = hashlib.sha1(css + js).hexdigest()[:8]

    layout = (SRC / "layout.html").read_text(encoding="utf-8")
    sitemap = []
    for page in sorted((SRC / "pages").glob("*.html")):
        raw = page.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", raw, re.S)
        meta = json.loads(m.group(1))
        body = raw[m.end():]
        slug = page.stem
        path = "/" if slug == "index" else f"/{slug}"
        robots = '<meta name="robots" content="noindex">' if meta.get("noindex") else ""
        extra = {
            "title": html.escape(meta["title"]),
            "description": html.escape(meta["description"]),
            "path": path,
            "canonical": SITE["site_url"] + path,
            "nav": render_nav(path),
            "version": version,
            "robots": robots,
            "jsonld": meta.get("jsonld", ""),
        }
        content = fill(body, extra)
        out = fill(layout, {**extra, "content": content})
        leftover = re.findall(r"\{\{[^}]+\}\}", out)
        if leftover:
            raise SystemExit(f"{page.name}: unfilled tokens {leftover}")
        (OUT / f"{slug}.html").write_text(out, encoding="utf-8")
        if not meta.get("noindex"):
            sitemap.append(SITE["site_url"] + path)

    today = date.today().isoformat()
    urls = "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in sitemap)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        encoding="utf-8",
    )
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE['site_url']}/sitemap.xml\n", encoding="utf-8"
    )
    print(f"Built {len(sitemap)} indexable pages into {OUT}")


if __name__ == "__main__":
    main()
