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
    ("/guides", "Guides"),
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
            f'<div class="package-buy"><p class="package-price"><span class="mark">{price(p["price"])}</span></p>'
            + (f'<a class="button" href="{html.escape(p["payment_link"])}" data-buy="{key}">Buy now</a>' if p.get("payment_link") else "")
            + "</div>"
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


def render_reviews(keys):
    items = []
    for k in keys:
        r = SITE["reviews"][k]
        items.append(
            '<figure class="review">'
            f'<blockquote><p>{html.escape(r["text"])}</p></blockquote>'
            f'<figcaption><span class="review-name">{html.escape(r["name"])}</span> '
            f'<span class="review-meta">{html.escape(r["context"])}, {html.escape(r["date"])}</span></figcaption>'
            '</figure>'
        )
    return '<div class="reviews">' + "".join(items) + '</div><p class="reviews-note">From reviews my students left on Preply, quoted in their own words.</p>'


def render_guides_list(guides):
    if not guides:
        return ""
    items = []
    for g in guides:
        m = g["meta"]
        items.append(
            f'<li class="guide-item"><a href="{g["path"]}"><span class="guide-title">{html.escape(m["heading"])}</span>'
            f'<span class="guide-summary">{html.escape(m["description"])}</span></a></li>'
        )
    return '<ul class="guide-list">' + "".join(items) + "</ul>"


def render_jsonld(meta, path):
    url = SITE["site_url"] + path
    tutor = {
        "@type": "Person",
        "@id": SITE["site_url"] + "/#lawrence",
        "name": SITE["owner"],
        "jobTitle": "English tutor",
        "url": SITE["site_url"] + "/about",
        "image": SITE["site_url"] + "/assets/img/lawrence-480.jpg",
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "Goldsmiths, University of London"},
        "knowsLanguage": "en-GB",
    }
    business = {
        "@type": "ProfessionalService",
        "@id": SITE["site_url"] + "/#business",
        "name": SITE["site_name"],
        "url": SITE["site_url"] + "/",
        "email": SITE["email"],
        "image": SITE["site_url"] + "/assets/img/share.png",
        "founder": {"@id": tutor["@id"]},
        "areaServed": "Worldwide",
        "availableLanguage": ["en"],
        "description": "One-to-one online English lessons with a British tutor: Business English, IELTS and ECL exam preparation.",
    }
    graph = [business, tutor]
    services = meta.get("services")
    if services:
        for key in services:
            pk = SITE["packages"][key]
            graph.append({
                "@type": "Service",
                "name": pk["name"],
                "provider": {"@id": business["@id"]},
                "areaServed": "Worldwide",
                "url": SITE["site_url"] + pk.get("page", "/packages"),
                "offers": {"@type": "Offer", "price": str(pk["price"]), "priceCurrency": "GBP",
                           "description": pk["length"]},
            })
    if meta.get("type") == "guide":
        graph.append({
            "@type": "Article",
            "headline": meta["heading"],
            "description": meta["description"],
            "datePublished": meta["published"],
            "dateModified": meta.get("updated", meta["published"]),
            "author": {"@id": tutor["@id"]},
            "publisher": {"@id": business["@id"]},
            "mainEntityOfPage": url,
            "inLanguage": meta.get("lang", "en-GB"),
        })
    data = {"@context": "https://schema.org", "@graph": graph}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


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
        "lesson_booking": SITE["lesson_booking_url"],
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
    if "{{signup}}" in text:
        text = text.replace("{{signup}}", (SRC / "partials" / "signup.html").read_text(encoding="utf-8").replace("{{signup_id}}", "a"), 1)
    text = re.sub(r"\{\{reviews:([a-z,]+)\}\}", lambda m: render_reviews(m.group(1).split(",")), text)
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

    # Read every page first, so the guides index can list the guides.
    pages = []
    for page in sorted((SRC / "pages").rglob("*.html")):
        raw = page.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", raw, re.S)
        meta = json.loads(m.group(1))
        rel = page.relative_to(SRC / "pages").with_suffix("").as_posix()
        if rel == "index":
            path = "/"
        elif rel.endswith("/index"):
            path = "/" + rel[: -len("/index")]
        else:
            path = "/" + rel
        pages.append({"meta": meta, "body": raw[m.end():], "rel": rel, "path": path})

    guides = sorted(
        (p for p in pages if p["meta"].get("type") == "guide" and not p["meta"].get("draft")),
        key=lambda p: p["meta"]["published"], reverse=True,
    )

    sitemap = []
    for p in pages:
        meta, path = p["meta"], p["path"]
        if meta.get("draft"):
            continue
        robots = '<meta name="robots" content="noindex">' if meta.get("noindex") else ""
        extra = {
            "title": html.escape(meta["title"]),
            "description": html.escape(meta["description"]),
            "path": path,
            "canonical": SITE["site_url"] + path,
            "nav": render_nav(path),
            "version": version,
            "robots": robots,
            "lang": meta.get("lang", "en-GB"),
            "jsonld": render_jsonld(meta, path),
            "guides_list": render_guides_list(guides),
        }
        extra["signup_scripts"] = ""
        content = fill(p["body"], extra)
        if 'ml-subscribe-form-48738236' in content:
            extra["signup_scripts"] = (
                '<script>function ml_webform_success_48738236(){var $=ml_jQuery||jQuery;'
                '$(".ml-subscribe-form-48738236 .row-success").show();$(".ml-subscribe-form-48738236 .row-form").hide();}</script>\n'
                '<script src="https://www.google.com/recaptcha/api.js" async defer></script>\n'
                '<script src="https://groot.mailerlite.com/js/w/webforms.min.js?v83147fa8ce2d95cb73ece7f28b469519"></script>\n'
                '<script>fetch("https://assets.mailerlite.com/jsonp/2807138/forms/204499188840399998/takel")</script>'
            )
        out = fill(layout, {**extra, "content": content})
        leftover = re.findall(r"\{\{[^}]+\}\}", out)
        if leftover:
            raise SystemExit(f"{p['rel']}: unfilled tokens {leftover}")
        dest = OUT / (f"{p['rel'][:-len('/index')]}.html" if p['rel'].endswith('/index') else f"{p['rel']}.html")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(out, encoding="utf-8")
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
