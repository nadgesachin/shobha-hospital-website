#!/usr/bin/env python3
"""Static site generator for Suvacha Healthcare.

    python3 build.py            # build into site/
    python3 build.py --serve    # build, then serve on http://localhost:8000

Content lives in content/*.json; styles/scripts/images in src/.
URL structure mirrors the original WordPress site (/service/<slug>/,
/doctor/<slug>/ ...) so existing links and search rankings keep working.
"""
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

from PIL import Image

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "site"
SITE = json.loads((ROOT / "content" / "site.json").read_text())
SERVICES = json.loads((ROOT / "content" / "services.json").read_text())
DOCTORS = json.loads((ROOT / "content" / "doctors.json").read_text())
DOC_BY = {d["slug"]: d for d in DOCTORS}
REVIEWS = json.loads((ROOT / "content" / "reviews.json").read_text())
SEO = json.loads((ROOT / "content" / "seo.json").read_text())
OG_IMAGES = set()
# Content hashes for cache-busting: asset URLs change whenever the file changes.
VER = {k: hashlib.md5((SRC / k).read_bytes()).hexdigest()[:10] for k in ("css/style.css", "js/main.js")}  # image names that need a 1200x630 JPEG share image
FONTS_CSS = ("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500;1,600"
             "&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Tiro+Devanagari+Hindi&display=swap")
UNIVERSITIES = {"BHU": "Banaras Hindu University", "MUHS": "Maharashtra University of Health Sciences",
                "GAMC, Bengaluru": "Government Ayurveda Medical College, Bengaluru"}
SVC_BY = {s["slug"]: s for s in SERVICES}
TODAY = dt.date.today().isoformat()

# Doctor filter categories for /doctors/
DOC_TAGS = {
    "sachin": ["womens", "surgery"], "vaishali-mishra": ["womens"], "lalita": ["womens"],
    "anushka": ["womens"], "manish": ["children"], "neha-sunia": ["ayurveda"],
    "shailesh": ["ayurveda", "wellness"], "shobhan": ["wellness"],
    "rangaswamy": ["ayurveda", "wellness"], "srinivasa": ["surgery"], "randheer-kadam": ["surgery"],
}
FILTERS = [("all", "All doctors"), ("womens", "Women’s health & fertility"), ("surgery", "Surgery"),
           ("ayurveda", "Ayurveda & Panchakarma"), ("wellness", "Yoga, mind & wellness"), ("children", "Children")]


def e(s):
    return escape(str(s), quote=True)


def wa_link(text=None):
    return f"https://wa.me/{SITE['whatsapp']}?text={quote(text or SITE['whatsapp_greeting'])}"


TEL = f"tel:{SITE['phone']}"
MAIL = f"mailto:{SITE['email']}"
EMERG = f"tel:{SITE['emergency_phone']}"
GEO = f"{SITE['geo']['lat']},{SITE['geo']['lng']}"
MAP_EMBED = f"https://maps.google.com/maps?q={GEO}&z=16&output=embed"
DIRECTIONS = f"https://www.google.com/maps/dir/?api=1&destination={GEO}"

# ---------------------------------------------------------------- icons
ICONS = {
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "arrow": '<path d="M5 12h14M13 5l7 7-7 7"/>',
    "arrow-left": '<path d="M19 12H5M11 19l-7-7 7-7"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "chev-down": '<path d="m6 9 6 6 6-6"/>',
    "chev-right": '<path d="m9 6 6 6-6 6"/>',
    "chev-up": '<path d="m18 15-6-6-6 6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7z"/>',
    "leaf": '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>',
    "flower": '<circle cx="12" cy="12" r="3"/><path d="M12 16.5A4.5 4.5 0 1 1 7.5 12 4.5 4.5 0 1 1 12 7.5a4.5 4.5 0 1 1 4.5 4.5 4.5 4.5 0 1 1-4.5 4.5"/><path d="M12 7.5V9M7.5 12H9M16.5 12H15M12 16.5V15"/>',
    "baby": '<path d="M9 12h.01M15 12h.01M10 16c.5.3 1.2.5 2 .5s1.5-.2 2-.5"/><path d="M19 6.3a9 9 0 0 1 1.8 3.9 2 2 0 0 1 0 3.6 9 9 0 0 1-17.6 0 2 2 0 0 1 0-3.6A9 9 0 0 1 12 3c2 0 3.5 1.1 3.5 2.5s-.9 2.5-2 2.5c-.8 0-1.5-.4-1.5-1"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
    "repeat": '<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14M7 22l-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/>',
    "stethoscope": '<path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6 6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6 6 6 0 0 0 6-6v-4"/><circle cx="20" cy="10" r="2"/>',
    "graduation": '<path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>',
    "video": '<path d="m22 8-6 4 6 4V8z"/><rect x="2" y="6" width="14" height="12" rx="2"/>',
    "hospital": '<path d="M3 21h18M5 21V7l7-4 7 4v14"/><path d="M10 12h4M12 10v4M9 21v-4h6v4"/>',
    "navigation": '<path d="m3 11 19-9-9 19-2-8-8-2z"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
}
WA_PATH = '<path d="M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.16-.17.2-.35.22-.64.08-.3-.15-1.26-.47-2.4-1.48-.88-.79-1.48-1.76-1.65-2.06-.17-.3-.02-.46.13-.6.13-.14.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.03-.52-.07-.15-.67-1.61-.92-2.21-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.79.37-.27.3-1.04 1.02-1.04 2.48s1.07 2.88 1.21 3.07c.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.7.63.71.22 1.36.19 1.87.12.57-.09 1.76-.72 2-1.41.25-.7.25-1.29.17-1.41-.07-.13-.27-.2-.57-.35m-5.42 7.4h-.01a9.87 9.87 0 0 1-5.03-1.38l-.36-.21-3.74.98 1-3.65-.24-.37a9.86 9.86 0 0 1-1.51-5.26c0-5.45 4.44-9.88 9.89-9.88 2.64 0 5.12 1.03 6.99 2.9a9.83 9.83 0 0 1 2.89 6.99c0 5.45-4.44 9.88-9.88 9.88m8.41-18.3A11.82 11.82 0 0 0 12.05 0C5.5 0 .16 5.34.16 11.89c0 2.1.55 4.14 1.59 5.95L.06 24l6.3-1.65a11.88 11.88 0 0 0 5.68 1.45h.01c6.55 0 11.89-5.34 11.89-11.89a11.82 11.82 0 0 0-3.48-8.41z"/>'


def icon(name, cls="icon"):
    if name == "whatsapp":
        return f'<svg class="{cls} icon--fill" viewBox="0 0 24 24" aria-hidden="true">{WA_PATH}</svg>'
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


# ---------------------------------------------------------------- images
_dims = {}


def img(name, alt, sizes="100vw", cls="", eager=False, width=960):
    """Responsive <img> for a processed image in src/img (<name>-480/960.webp)."""
    path = SRC / "img" / f"{name}-960.webp"
    if name not in _dims:
        with Image.open(path) as im:
            _dims[name] = im.size
    w, h = _dims[name]
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="/assets/img/{name}-{width}.webp" '
            f'srcset="/assets/img/{name}-480.webp 480w, /assets/img/{name}-960.webp 960w" '
            f'sizes="{sizes}" width="{w}" height="{h}" alt="{e(alt)}" {load} decoding="async">')


def dr_name(d):
    n = d["name"]
    return n if n.lower().startswith("dr") else "Dr. " + n


# ---------------------------------------------------------------- JSON-LD
def clinic_ld():
    a = SITE["address"]
    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    return {
        "@context": "https://schema.org",
        "@type": "MedicalClinic",
        "@id": SITE["url"] + "/#clinic",
        "name": SITE["name"],
        "alternateName": "Suvacha Healthcare Khanvel",
        "description": SITE["about_short"],
        "slogan": SITE["tagline"],
        "url": SITE["url"],
        "logo": SITE["url"] + "/assets/img/logo.png",
        "image": SITE["url"] + "/assets/og/hero.jpg",
        "telephone": SITE["phone"],
        "email": SITE["email"],
        "address": {"@type": "PostalAddress", "streetAddress": a["street"], "addressLocality": a["locality"],
                    "addressRegion": a["region"], "postalCode": a["postal"], "addressCountry": a["country"]},
        "hasMap": SITE["google_place_url"],
        "areaServed": [{"@type": "City", "name": n} for n in [SITE["address"]["locality"], *SITE["nearby"]]],
        "sameAs": [SITE["google_place_url"]],
        "isAcceptingNewPatients": True,
        "geo": {"@type": "GeoCoordinates", "latitude": SITE["geo"]["lat"], "longitude": SITE["geo"]["lng"]},
        "contactPoint": [{"@type": "ContactPoint", "telephone": SITE["emergency_phone"], "contactType": "emergency"}],
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": [day_names[d] for d in h["dow"]],
             "opens": h["open"], "closes": h["close"]} for h in SITE["hours"]],
        "medicalSpecialty": ["Obstetric", "Gynecologic", "Pediatric", "Surgical"],
        "availableService": [{"@type": "MedicalTherapy", "name": s["title"]} for s in SERVICES],
        "founder": {"@id": SITE["url"] + "/doctor/sachin/#physician"},
        "employee": [{"@id": f"{SITE['url']}/doctor/{d['slug']}/#physician"} for d in DOCTORS],
    }


def breadcrumb_ld(trail):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": name, "item": SITE["url"] + url}
        for i, (name, url) in enumerate(trail)]}


def ld_script(obj):
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'


# ---------------------------------------------------------------- layout
NAV = [("Home", "/"), ("About", "/about/"), ("Services", "/services/"), ("Doctors", "/doctors/"),
       ("Health Tips", "/blog/"), ("Contact", "/contact/")]


def header(current):
    def link(label, url):
        cur = ' aria-current="page"' if current == url else ""
        return f'<li class="nav__item"><a class="nav__link" href="{url}"{cur}>{label}</a></li>'

    svc_links = "".join(
        f'<a href="/service/{s["slug"]}/">{img("svc-" + s["slug"], "", "40px", width=480)}<span>{e(s["title"])}</span></a>'
        for s in SERVICES)
    items = []
    for label, url in NAV:
        if label == "Services":
            cur = ' aria-current="page"' if current.startswith(("/services", "/service/")) else ""
            items.append(
                f'<li class="nav__item nav__item--has-menu"><button class="nav__link" type="button" aria-expanded="false" aria-haspopup="true"{cur}>'
                f'Services {icon("chev-down")}</button><div class="dropdown">{svc_links}'
                f'<a class="dropdown__all" href="/services/">View all services {icon("arrow")}</a></div></li>')
        else:
            items.append(link(label, url))
    drawer_links = "".join(
        f'<li><a href="{u}">{l} {icon("chev-right")}</a></li>' if l != "Services" else
        '<li><details><summary>Services ' + icon("chev-down") + '</summary><ul>' +
        "".join(f'<li><a href="/service/{s["slug"]}/">{e(s["title"])}</a></li>' for s in SERVICES) +
        '<li><a href="/services/"><strong>All services →</strong></a></li></ul></details></li>'
        for l, u in NAV)
    today_hours = " · ".join(f'{h["days"].split(" ")[0][:3]}{"–Fri" if len(h["dow"]) > 1 else ""} {h["label"]}' for h in SITE["hours"])
    return f'''
<a class="skip-link" href="#main">Skip to content</a>
<div class="topbar"><div class="container">
  <ul class="topbar__list">
    <li>{icon("pin")}<a href="{SITE["maps_link"]}" target="_blank" rel="noopener">{e(SITE["address"]["short"])}</a></li>
    <li class="topbar__hours">{icon("clock")}<span>{e(today_hours)}</span></li>
  </ul>
  <ul class="topbar__list">
    <li><span class="open-badge" data-open-badge>Clinic hours</span></li>
    <li>{icon("phone")}<a href="{EMERG}">Emergency: {e(SITE["emergency_display"])}</a></li>
    <li>{icon("mail")}<a href="{MAIL}">{e(SITE["email"])}</a></li>
  </ul>
</div></div>
<header class="header"><div class="container">
  <a class="brand" href="/" aria-label="Suvacha Healthcare — home"><img src="/assets/img/logo.webp" width="420" height="145" alt="Suvacha Healthcare — Creating Shreyasi Praja"></a>
  <nav class="nav" aria-label="Main"><ul class="nav__list">{"".join(items)}</ul></nav>
  <div class="header__actions">
    <a class="btn btn--ghost btn--sm" href="{TEL}">{icon("phone")} {e(SITE["phone_display"])}</a>
    <a class="btn btn--coral btn--sm" href="/appointment/">{icon("calendar")} Book Appointment</a>
    <button class="menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="drawer">{icon("menu")}</button>
  </div>
</div></header>
<div class="drawer" id="drawer" aria-hidden="true">
  <div class="drawer__backdrop" data-close-drawer></div>
  <div class="drawer__panel" role="dialog" aria-modal="true" aria-label="Menu">
    <div class="drawer__head"><img src="/assets/img/logo.webp" width="420" height="145" alt="Suvacha Healthcare">
      <button class="menu-toggle drawer__close" style="display:inline-flex" type="button" aria-label="Close menu" data-close-drawer>{icon("x")}</button></div>
    <nav aria-label="Mobile"><ul>{drawer_links}</ul></nav>
    <div class="drawer__cta">
      <a class="btn btn--coral" href="/appointment/">{icon("calendar")} Book Appointment</a>
      <a class="btn btn--wa" href="{wa_link()}" target="_blank" rel="noopener">{icon("whatsapp")} Chat on WhatsApp</a>
      <a class="btn btn--ghost" href="{TEL}">{icon("phone")} {e(SITE["phone_display"])}</a>
    </div>
  </div>
</div>'''


def footer():
    svc = "".join(f'<li><a href="/service/{s["slug"]}/">{e(s["title"])}</a></li>' for s in SERVICES)
    hours = "".join(f'<li><span>{e(h["days"])}</span><span>{e(h["label"])}</span></li>' for h in SITE["hours"])
    year = dt.date.today().year
    return f'''
<footer class="footer"><div class="container">
  <div class="footer__grid">
    <div class="footer__brand">
      <img src="/assets/img/logo.webp" width="420" height="145" alt="Suvacha Healthcare" loading="lazy">
      <p>{e(SITE["about_short"])}</p>
      <p class="footer__tagline">Creating श्रेयसी प्रजा</p>
    </div>
    <div><h2 class="footer__h">Our Services</h2><ul>{svc}</ul></div>
    <div><h2 class="footer__h">Quick Links</h2><ul>
      <li><a href="/about/">About Us</a></li><li><a href="/doctors/">Our Doctors</a></li>
      <li><a href="/appointment/">Book Appointment</a></li><li><a href="/contact/">Contact &amp; Directions</a></li>
      <li><a href="/pregnancy-tools/">Pregnancy calculators</a></li>
      <li><a href="/#faq">FAQs</a></li>
      <li><a href="/blog/">Health tips</a></li>
      <li><a href="{SITE["google_place_url"]}" target="_blank" rel="noopener">Review us on Google ★</a></li>
    </ul></div>
    <div>
      <h2 class="footer__h">Visit Us</h2>
      <ul class="footer__contact">
        <li>{icon("pin")}<a href="{SITE["maps_link"]}" target="_blank" rel="noopener">{e(SITE["address"]["display"])}</a></li>
        <li>{icon("phone")}<a href="{TEL}">{e(SITE["phone_display"])} <small>(appointments)</small></a></li>
        <li>{icon("phone")}<a href="{EMERG}">{e(SITE["emergency_display"])} <small>(emergency)</small></a></li>
        <li>{icon("whatsapp")}<a href="{wa_link()}" target="_blank" rel="noopener">WhatsApp us</a></li>
        <li>{icon("mail")}<a href="{MAIL}">{e(SITE["email"])}</a></li>
      </ul>
      <h2 class="footer__h" style="margin-top:28px">Clinic Hours</h2>
      <ul class="footer__hours">{hours}</ul>
    </div>
  </div>
  <p class="disclaimer">Information on this website is for general awareness and does not replace a consultation with a qualified doctor. In a medical emergency, please call {e(SITE["emergency_display"])} or visit the nearest hospital.</p>
  <div class="footer__bottom"><span>© {year} Suvacha Healthcare. All rights reserved.</span><span>{e(SITE["address"]["short"])}</span></div>
</div></footer>
<div class="wa-float">
  <span class="wa-float__label">Questions? Chat with us</span>
  <a class="wa-float__btn" href="{wa_link()}" target="_blank" rel="noopener" aria-label="Chat with Suvacha Healthcare on WhatsApp">{icon("whatsapp")}</a>
</div>
<button class="to-top" type="button" aria-label="Back to top">{icon("chev-up")}</button>
<nav class="mobile-bar" aria-label="Quick actions">
  <a href="{TEL}">{icon("phone")}Call</a>
  <a class="is-wa" href="{wa_link()}" target="_blank" rel="noopener">{icon("whatsapp")}WhatsApp</a>
  <a href="/pregnancy-tools/">{icon("baby")}Tools</a>
  <a class="is-book" href="/appointment/">{icon("calendar")}Book</a>
</nav>'''


def page(path, title, description, body, extra_ld=(), og_image="hero", og_type="website", preload=None, noindex=False, published=None, suffix=True):
    override = SEO["pages"].get(path)
    if override:
        title, description = override["title"], override["description"]
    full_title = title if ("Suvacha" in title or not suffix) else f"{title} | Suvacha Healthcare"
    canonical = SITE["url"] + path
    cfg = {"whatsapp": SITE["whatsapp"], "hours": SITE["hours"]}
    if path == "/":
        extra_ld = [{"@context": "https://schema.org", "@type": "WebSite", "@id": SITE["url"] + "/#website", "name": SITE["name"],
                     "url": SITE["url"] + "/", "inLanguage": "en-IN", "publisher": {"@id": SITE["url"] + "/#clinic"}}, *extra_ld]
    lds = "".join(ld_script(x) for x in (clinic_ld(), *extra_ld))
    OG_IMAGES.add(og_image)
    g = SITE["geo"]
    verify = f'<meta name="google-site-verification" content="{e(SITE["google_site_verification"])}">\n' if SITE.get("google_site_verification") else ""
    robots = "noindex, follow" if noindex else "index, follow, max-image-preview:large, max-snippet:-1"
    pre = (f'<link rel="preload" as="image" href="/assets/img/{preload}-960.webp" '
           f'imagesrcset="/assets/img/{preload}-480.webp 480w, /assets/img/{preload}-960.webp 960w" imagesizes="(max-width: 860px) 90vw, 480px" fetchpriority="high">\n') if preload else ""
    art = f'<meta property="article:published_time" content="{published}">\n' if published else ""
    html = f'''<!doctype html>
<html lang="en-IN" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
{verify}<meta name="theme-color" content="#1f2e1c">
<meta name="geo.region" content="{SITE["address"]["region_code"]}">
<meta name="geo.placename" content="{SITE["address"]["locality"]}, {SITE["address"]["district"]}">
<meta name="geo.position" content="{g["lat"]};{g["lng"]}">
<meta name="ICBM" content="{g["lat"]}, {g["lng"]}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Suvacha Healthcare">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE["url"]}/assets/og/{og_image}.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_IN">
{art}<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/img/favicon-180.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{pre}<link rel="preload" as="style" href="{FONTS_CSS}" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{FONTS_CSS}"></noscript>
<link rel="stylesheet" href="/assets/css/style.css?v={VER["css/style.css"]}">
<script>window.SUVACHA={json.dumps(cfg)};</script>
<script src="/assets/js/main.js?v={VER["js/main.js"]}" defer></script>
{lds}
</head>
<body>
{header(path)}
<main id="main">
{body}
</main>
{footer()}
</body>
</html>
'''
    dest = OUT / path.lstrip("/") / "index.html" if path.endswith("/") else OUT / path.lstrip("/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html)
    return path


# ---------------------------------------------------------------- shared components
def page_hero(title, lead, trail, media=None, cta=None, eyebrow=None):
    crumbs = "".join(
        f'<li><a href="{u}">{e(n)}</a></li>' if i < len(trail) - 1 else f'<li aria-current="page">{e(n)}</li>'
        for i, (n, u) in enumerate(trail))
    eb = f'<span class="eyebrow">{e(eyebrow)}</span>' if eyebrow else ""
    lead_html = f'<p class="lead">{e(lead)}</p>' if lead else ""
    cta_html = f'<div class="page-hero__cta">{cta}</div>' if cta else ""
    text = f'<div><nav aria-label="Breadcrumb"><ol class="breadcrumb">{crumbs}</ol></nav>{eb}<h1>{e(title)}</h1>{lead_html}{cta_html}</div>'
    if media:
        return f'<section class="page-hero page-hero--media"><div class="container">{text}<div class="page-hero__img">{media}</div></div></section>'
    return f'<section class="page-hero"><div class="container">{text}</div></section>'


def service_card(s):
    return f'''<a class="svc-card reveal" href="/service/{s["slug"]}/">
  <div class="svc-card__img">{img("svc-" + s["slug"], s["title"], "(max-width: 600px) 100vw, (max-width: 860px) 50vw, 380px")}</div>
  <div class="svc-card__body"><h3>{e(s["title"])}</h3><p>{e(s["short"])}</p>
  <span class="svc-card__more">Learn more {icon("arrow")}</span></div></a>'''


def doctor_card(d, tag="a"):
    badge = f'<span class="doc-card__badge">{icon("video")} Online consults</span>' if d["online"] else ""
    if d["slug"] == "sachin":
        badge = f'<span class="doc-card__badge">{icon("hospital")} Founder</span>'
    tags = "|".join(DOC_TAGS.get(d["slug"], []))
    return f'''<a class="doc-card reveal" href="/doctor/{d["slug"]}/" data-tags="{tags}">
  <div class="doc-card__img">{img("dr-" + d["slug"], dr_name(d), "(max-width: 600px) 50vw, (max-width: 1100px) 33vw, 280px")}{badge}</div>
  <div class="doc-card__body"><h3>{e(dr_name(d))}</h3><p class="doc-card__spec">{e(d["specialty"])}</p>
  <p class="doc-card__qual">{e(d["qualification"])}</p></div></a>'''


def journey():
    items = "".join(
        f'<li class="reveal"><a href="/service/{j["service"]}/"><span class="journey__dot" aria-hidden="true"></span>'
        f'<h3>{e(j["stage"])}</h3><p>{e(j["text"])}</p></a></li>' for j in SITE["journey"])
    return f'''<section class="section"><div class="container">
  <div class="section-head section-head--center reveal"><span class="eyebrow">Care for every stage</span>
  <h2>With you through every phase of life</h2>
  <p>Suvacha supports women from adolescence to fertility, pregnancy, childbirth, postnatal care and menopause.</p></div>
  <ol class="journey reveal-line">{items}</ol>
</div></section>'''


def booking_form(heading=True, id_="book"):
    svc_opts = "".join(f'<option value="{s["slug"]}">{e(s["title"])}</option>' for s in SERVICES)
    doc_opts = "".join(f'<option value="{d["slug"]}">{e(dr_name(d))} — {e(d["specialty"])}</option>' for d in DOCTORS)
    hours = "".join(f'<li><div><span class="ci">{icon("clock")}</span><span><small>{e(h["days"])}</small><strong>{e(h["label"])}</strong></span></div></li>' for h in SITE["hours"][:1])
    head = '''<span class="eyebrow">Book an appointment</span>
      <h2>Book a consultation with <em>confidence</em></h2>''' if heading else '<h2>Request your appointment</h2>'
    return f'''<div class="booking reveal" id="{id_}">
  <div class="booking__aside">
    {head}
    <p>Whether you are seeking support for menstrual health, fertility, pregnancy or overall wellness, our team is here to guide you with compassion, clarity and personalised care.</p>
    <ul class="contact-lines">
      <li><a href="{TEL}"><span class="ci">{icon("phone")}</span><span><small>Appointments</small><strong>{e(SITE["phone_display"])}</strong></span></a></li>
      <li><a href="{EMERG}"><span class="ci">{icon("phone")}</span><span><small>Emergency</small><strong>{e(SITE["emergency_display"])}</strong></span></a></li>
      <li><a href="{wa_link()}" target="_blank" rel="noopener"><span class="ci">{icon("whatsapp")}</span><span><small>WhatsApp</small><strong>Chat with our team</strong></span></a></li>
      {hours}
    </ul>
  </div>
  <form class="booking__form" data-booking novalidate>
    <div class="form-grid">
      <div class="field"><label for="{id_}-name">Full name <span class="req">*</span></label>
        <input id="{id_}-name" name="name" type="text" autocomplete="name" required placeholder="Your name"></div>
      <div class="field"><label for="{id_}-phone">Mobile number <span class="req">*</span></label>
        <input id="{id_}-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" required pattern="[0-9+ \\-]{{10,15}}" placeholder="10-digit mobile"></div>
      <div class="field"><label for="{id_}-service">Service</label>
        <select id="{id_}-service" name="service"><option value="">Select a service</option>{svc_opts}</select></div>
      <div class="field"><label for="{id_}-doctor">Preferred doctor</label>
        <select id="{id_}-doctor" name="doctor"><option value="">Any available doctor</option>{doc_opts}</select></div>
      <div class="field field--full"><fieldset><legend>Consultation type</legend>
        <div class="segmented">
          <label><input type="radio" name="mode" value="In-clinic visit" checked><span>{icon("hospital")} In-clinic visit</span></label>
          <label><input type="radio" name="mode" value="Online consultation"><span>{icon("video")} Online consultation</span></label>
        </div></fieldset></div>
      <div class="field"><label for="{id_}-date">Preferred date</label><input id="{id_}-date" name="date" type="date"></div>
      <div class="field"><label for="{id_}-time">Preferred time</label>
        <select id="{id_}-time" name="time"><option value="">Any time</option><option>Morning (8 AM – 12 PM)</option><option>Afternoon (12 – 4 PM)</option><option>Evening (4 – 7 PM)</option></select></div>
      <div class="field field--full"><label for="{id_}-message">Your concern <small style="font-weight:400;color:var(--muted)">(optional)</small></label>
        <textarea id="{id_}-message" name="message" placeholder="Briefly describe your concern or question"></textarea></div>
    </div>
    <div class="form-actions">
      <button class="btn btn--wa" type="submit">{icon("whatsapp")} Send request on WhatsApp</button>
      <a class="btn btn--ghost" href="{TEL}">{icon("phone")} Or call us</a>
    </div>
    <p class="form-note">{icon("lock")} Your details go straight to our clinic WhatsApp — nothing is stored on this website. We’ll confirm your slot shortly.</p>
  </form>
</div>'''


def faq_section(faqs, white=True):
    items = "".join(
        f'<details{" open" if i == 0 else ""}><summary>{e(f["q"])}<span class="faq__plus">{icon("plus")}</span></summary><p>{e(f["a"])}</p></details>'
        for i, f in enumerate(faqs))
    return f'''<section class="section {"section--white" if white else ""}" id="faq"><div class="container faq-wrap">
  <div class="section-head reveal"><span class="eyebrow">FAQs</span><h2>Answers to common questions</h2>
  <p>Can’t find what you’re looking for? Message us on WhatsApp and our team will help.</p>
  <a class="btn btn--wa" href="{wa_link("Namaste, I have a question.")}" target="_blank" rel="noopener">{icon("whatsapp")} Ask on WhatsApp</a></div>
  <div class="faq reveal">{items}</div>
</div></section>'''


def faq_ld(faqs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]}


def hours_table():
    return "<table class=\"hours\"><tbody>" + "".join(
        f'<tr data-hours-row="{",".join(map(str, h["dow"]))}"><th scope="row">{e(h["days"])}</th><td>{e(h["label"])}</td></tr>'
        for h in SITE["hours"]) + "</tbody></table>"


def map_section(sand=True):
    return f'''<section class="section {"section--sand" if sand else ""}" id="location"><div class="container">
  <div class="section-head reveal"><span class="eyebrow">Visit us</span><h2>Find us in Khanvel</h2><p>Easily reachable from {", ".join(SITE["nearby"][:-1])} and {SITE["nearby"][-1]}.</p></div>
  <div class="map-card reveal">
    <div class="map-card__info">
      <ul class="info-list">
        <li><span class="ci">{icon("pin")}</span><div><small>Address</small><a href="{SITE["maps_link"]}" target="_blank" rel="noopener">{e(SITE["address"]["display"])}</a></div></li>
        <li><span class="ci">{icon("phone")}</span><div><small>Appointments</small><a href="{TEL}">{e(SITE["phone_display"])}</a></div></li>
        <li><span class="ci">{icon("phone")}</span><div><small>Emergency</small><a href="{EMERG}">{e(SITE["emergency_display"])}</a></div></li>
        <li><span class="ci">{icon("mail")}</span><div><small>Email</small><a href="{MAIL}">{e(SITE["email"])}</a></div></li>
      </ul>
      <p style="margin:0 0 4px;font-weight:600;color:var(--green-900)">Clinic hours <span class="open-badge" data-open-badge style="margin-left:8px;font-size:.85rem;color:var(--muted)"></span></p>
      {hours_table()}
      <div style="display:flex;flex-wrap:wrap;gap:10px">
        <a class="btn btn--sm" href="{DIRECTIONS}" target="_blank" rel="noopener">{icon("navigation")} Get directions</a>
        <a class="btn btn--wa btn--sm" href="{wa_link("Namaste, please share the clinic location and directions.")}" target="_blank" rel="noopener">{icon("whatsapp")} Ask for directions</a>
      </div>
    </div>
    <div class="map-card__map"><iframe src="{MAP_EMBED}" title="Map showing Suvacha Healthcare, Khanvel" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>
  </div>
  <nav class="from-towns reveal" aria-label="Directions from nearby towns"><span>{icon("navigation")} Directions from:</span>{"".join(f'<a href="https://www.google.com/maps/dir/?api=1&amp;origin={quote(t + ", India")}&amp;destination={GEO}" target="_blank" rel="noopener">{e(t)}</a>' for t in SITE["nearby"])}</nav>
</div></section>'''


def cta_band(title="Ready to begin your care journey?", text="Book an in-clinic visit or online consultation with our specialists."):
    return f'''<section class="section--tight"><div class="container"><div class="cta-band reveal">
  <div><h2>{e(title)}</h2><p>{e(text)}</p></div>
  <div class="cta-band__actions">
    <a class="btn btn--coral" href="/appointment/">{icon("calendar")} Book appointment</a>
    <a class="btn btn--ghost-light" href="{wa_link()}" target="_blank" rel="noopener">{icon("whatsapp")} WhatsApp</a>
  </div></div></div></section>'''


def why_section(with_stats=True):
    stats = "".join(f'<div class="stat"><strong{" data-count=" + chr(34) + s["value"] + chr(34) if s["value"].isdigit() else ""}>{e(s["value"])}</strong><span>{e(s["label"])}</span></div>' for s in SITE["stats"])
    why = "".join(f'<div class="why reveal"><div class="why__icon">{icon(w["icon"])}</div><h3>{e(w["title"])}</h3><p>{e(w["text"])}</p></div>' for w in SITE["why"])
    stats_html = f'<div class="stats reveal" style="margin-bottom:64px">{stats}</div>' if with_stats else ""
    return f'''<section class="section section--green"><div class="container">
  {stats_html}
  <div class="section-head section-head--center reveal"><span class="eyebrow">Why Suvacha</span>
  <h2>Why choose Suvacha Healthcare</h2>
  <p>A holistic, woman-centred approach that blends modern gynecology with the timeless wisdom of Ayurveda — supporting you at every stage of life.</p></div>
  <div class="why-grid">{why}</div>
</div></section>'''


def section_blocks(sections, numbered=True):
    out = []
    for i, sec in enumerate(sections, 1):
        parts = [f'<div class="block__head">{"<span class=block__num>%02d</span>" % i if numbered else ""}<h2>{e(sec["title"])}</h2></div>']
        parts += [f"<p>{e(p)}</p>" for p in sec["paras"]]
        for g in sec["groups"]:
            if g["label"]:
                parts.append(f'<p class="block__label">{e(g["label"])}</p>')
            single = " ticks--single" if any(len(x) > 60 for x in g["items"]) or len(g["items"]) < 3 else ""
            parts.append(f'<ul class="ticks{single}">' + "".join(f"<li>{icon('check-circle')}<span>{e(x)}</span></li>" for x in g["items"]) + "</ul>")
        if sec["note"]:
            parts.append(f'<p class="block__note">{icon("info")}<span>{e(sec["note"])}</span></p>')
        out.append(f'<article class="block reveal">{"".join(parts)}</article>')
    return "".join(out)


def book_aside(text, url, wa_text):
    return f'''<div class="aside-card aside-card--book">
  <h3>Book a consultation</h3><p>{e(text)}</p>
  <a class="btn btn--coral" href="{url}">{icon("calendar")} Book appointment</a>
  <a class="btn btn--wa" href="{wa_link(wa_text)}" target="_blank" rel="noopener">{icon("whatsapp")} Ask on WhatsApp</a>
  <a class="btn btn--ghost-light" href="{TEL}">{icon("phone")} {e(SITE["phone_display"])}</a>
</div>'''


TOOL_FOR = {"pregnancy-maternal-care": "due-date", "garbhasanskar": "due-date",
            "infertility-reproductive-health": "ovulation", "andrology-male-infertility": "ovulation"}


def tool_aside(slug):
    anchor = TOOL_FOR.get(slug)
    if not anchor:
        return ""
    title, text = (("Due date & scan planner", "Find your due date, current week and a personal scan timeline.")
                   if anchor == "due-date" else
                   ("Fertile window calculator", "See your most fertile days for the next three cycles."))
    return (f'<a class="aside-card aside-tool" href="/pregnancy-tools/#{anchor}"><span class="pillar__icon">{icon("calendar")}</span>'
            f'<span><strong>{title}</strong><span>{text}</span></span></a>')


def mini_docs(slugs):
    return "".join(
        f'<a class="mini-doc" href="/doctor/{s}/">{img("dr-" + s, "", "56px", width=480)}<div><strong>{e(dr_name(DOC_BY[s]))}</strong><span>{e(DOC_BY[s]["specialty"])}</span></div></a>'
        for s in slugs)


# ---------------------------------------------------------------- pages
def build_home():
    h = SITE["hero"]
    title_html = e(h["title"]).replace("Ayurveda", '<em class="swash">Ayurveda<svg class="swash__line" viewBox="0 0 200 16" preserveAspectRatio="none" aria-hidden="true"><path d="M3 11C46 3 120 2 197 9"/></svg></em>')
    pillars = "".join(f'<div class="pillar reveal"><div class="pillar__icon">{icon(p["icon"])}</div><h3>{e(p["title"])}</h3><p>{e(p["text"])}</p></div>' for p in SITE["pillars"])
    services = "".join(service_card(s) for s in SERVICES)
    docs = "".join(doctor_card(d) for d in DOCTORS)
    founder = DOC_BY["sachin"]
    body = f'''
<section class="hero"><span class="hero__blob hero__blob--a" aria-hidden="true"></span><span class="hero__blob hero__blob--b" aria-hidden="true"></span><div class="container">
  <div>
    <span class="eyebrow hero-in" style="--d:0">{e(h["eyebrow"])}</span>
    <h1><span class="h1-kicker hero-in" style="--d:1">Gynecology, Maternity &amp; Ayurveda Clinic in Khanvel, Silvassa</span><span class="hero-in" style="--d:2">{title_html}</span></h1>
    <p class="hero__lead hero-in" style="--d:4">{e(h["lead"])}</p>
    <div class="hero__cta hero-in" style="--d:5">
      <a class="btn btn--coral" href="/appointment/">{icon("calendar")} Book Appointment</a>
      <a class="btn btn--wa" href="{wa_link()}" target="_blank" rel="noopener">{icon("whatsapp")} WhatsApp Us</a>
      <a class="btn btn--ghost" href="/doctor/sachin/">Meet the Doctor {icon("arrow")}</a>
    </div>
    <ul class="hero__trust">
      <li class="hero-in" style="--d:6">{icon("check-circle")} Normal delivery first</li>
      <li class="hero-in" style="--d:7">{icon("check-circle")} IMS–BHU trained specialists</li>
      <li class="hero-in" style="--d:8">{icon("check-circle")} Online &amp; in-clinic</li>
    </ul>
  </div>
  <div class="hero__media" data-parallax>
    <div class="hero__img">{img("hero", "A Suvacha gynecologist consulting with a pregnant woman", "(max-width: 860px) 90vw, 480px", eager=True)}</div>
    <a class="float-card float-card--a float-in" style="--d:6" href="{EMERG}"><span class="float-card__icon">{icon("phone")}</span><span>Emergency contact<strong>{e(SITE["emergency_display"])}</strong></span></a>
    <div class="float-card float-card--b float-in" style="--d:8"><span class="float-card__icon">{icon("users")}</span><span><strong>11 specialists</strong>Ayurveda + modern care</span></div>
  </div>
</div></section>

<div class="info-strip"><div class="container"><div class="info-strip__grid">
  <a class="info-strip__item" href="{TEL}"><span class="info-strip__icon info-strip__icon--coral">{icon("phone")}</span><span><small>Call us</small><strong>{e(SITE["phone_display"])}</strong></span></a>
  <a class="info-strip__item" href="{wa_link()}" target="_blank" rel="noopener"><span class="info-strip__icon">{icon("whatsapp")}</span><span><small>WhatsApp</small><strong>Quick replies</strong></span></a>
  <div class="info-strip__item"><span class="info-strip__icon">{icon("clock")}</span><span><small>Today</small><strong class="open-badge" data-open-badge>Mon–Fri 8 AM – 7 PM</strong></span></div>
  <a class="info-strip__item" href="#location"><span class="info-strip__icon info-strip__icon--coral">{icon("pin")}</span><span><small>Location</small><strong>{e(SITE["address"]["short"])}</strong></span></a>
</div></div></div>

<section class="section"><div class="container">
  <div class="section-head section-head--center reveal"><span class="eyebrow">Holistic care</span><h2>Holistic women’s healthcare you can trust</h2></div>
  <div class="pillars">{pillars}</div>
</div></section>

<section class="section section--white"><div class="container split">
  <div class="collage reveal">
    {img("about-1", "Mother cradling her newborn", "(max-width: 860px) 55vw, 320px", "collage__a")}
    {img("about-3", "Doctor consultation at Suvacha", "(max-width: 860px) 40vw, 240px", "collage__b")}
    <span class="collage__badge">श्रेयसी प्रजा</span>
  </div>
  <div class="reveal">
    <span class="eyebrow">About Suvacha</span>
    <h2>Ayurveda’s wisdom, modern medicine’s precision</h2>
    {"".join(f"<p>{e(p)}</p>" for p in SITE["about"])}
    <ul class="checklist">{"".join(f"<li>{icon('check-circle')}<span>{e(v)}</span></li>" for v in SITE["values"][1:4])}</ul>
    <a class="btn btn--ghost" href="/about/">Our story {icon("arrow")}</a>
  </div>
</div></section>

<section class="section section--sand"><div class="container">
  <div class="section-head section-head--split reveal"><div><span class="eyebrow">Our services</span><h2>Comprehensive care, personalised for you</h2>
  <p>Comprehensive, personalised care designed to support women’s health, fertility and wellness at every stage of life.</p></div>
  <a class="btn btn--ghost" href="/services/">All services {icon("arrow")}</a></div>
  <div class="services-grid">{services}</div>
</div></section>

{journey()}

{tools_promo()}

<section class="section section--sand"><div class="container founder">
  <div class="founder__photo reveal">{img("dr-sachin", "Dr. Sachin Ladak Shedad", "(max-width: 860px) 90vw, 440px")}</div>
  <div class="reveal">
    <span class="eyebrow">Founder’s message</span>
    <blockquote>{e(SITE["founder_message"])}</blockquote>
    <p class="founder__name"><strong>Dr. Sachin Ladak Shedad</strong><span>Founder &amp; Clinical Director · {e(founder["qualification"])}</span></p>
    <ul class="tags"><li>High-risk pregnancy</li><li>Laparoscopic surgery</li><li>Hysteroscopy</li><li>Infertility</li><li>Normal &amp; caesarean delivery</li></ul>
    <a class="btn" href="/doctor/sachin/">View full profile {icon("arrow")}</a>
  </div>
</div></section>

<section class="section section--white"><div class="container" data-slider>
  <div class="section-head section-head--split reveal"><div><span class="eyebrow">Our team</span><h2>Doctors you can trust</h2>
  <p>Experienced doctors delivering compassionate, integrative women’s and family healthcare.</p></div>
  <div style="display:flex;gap:12px;align-items:center"><div class="slider-nav">
    <button class="slider-btn" type="button" data-dir="-1" aria-label="Previous doctors">{icon("arrow-left")}</button>
    <button class="slider-btn" type="button" data-dir="1" aria-label="Next doctors">{icon("arrow")}</button></div>
    <a class="btn btn--ghost" href="/doctors/">All doctors</a></div></div>
  <div class="slider">{docs}</div>
</div></section>

{why_section()}

<section class="section"><div class="container">{booking_form()}</div></section>

{blog_section()}

{reviews_section()}

{faq_section(SITE["faqs"])}

{map_section()}
'''
    page("/", "", "", body, extra_ld=[faq_ld(SITE["faqs"])], preload="hero")


def build_about():
    mv = f'''<div class="mv-grid">
  <div class="mv-card reveal"><div class="pillar__icon">{icon("heart")}</div><h3>Mission</h3><p>{e(SITE["mission"])}</p></div>
  <div class="mv-card reveal"><div class="pillar__icon" style="background:var(--gold-100);color:var(--gold-600)">{icon("sun")}</div><h3>Vision</h3><p>{e(SITE["vision"])}</p></div>
  <div class="mv-card mv-card--green reveal"><h3>Core values</h3><ul class="checklist">{"".join(f"<li>{icon('check-circle')}<span>{e(v)}</span></li>" for v in SITE["values"])}</ul></div>
</div>'''
    body = f'''
{page_hero("About Suvacha Healthcare", SITE["about"][0], [("Home", "/"), ("About", "/about/")], media=img("about-2", "Lotus — symbol of Suvacha", "(max-width: 860px) 90vw, 460px", eager=True), eyebrow="Our story")}
<section class="section section--white"><div class="container split">
  <div class="reveal"><span class="eyebrow">Who we are</span><h2>Creating <span class="deva">श्रेयसी प्रजा</span></h2>
    {"".join(f"<p>{e(p)}</p>" for p in SITE["about"][1:])}
    <p>{e(SITE["about_short"])}</p>
    <p><strong>Suvacha supports women through every phase of life:</strong> Adolescence → Fertility → Pregnancy → Childbirth → Postnatal Care → Menopause.</p>
    <a class="btn btn--coral" href="/appointment/">{icon("calendar")} Book a consultation</a>
  </div>
  <div class="collage reveal">
    {img("about-1", "Mother and newborn", "(max-width: 860px) 55vw, 320px", "collage__a")}
    {img("hero", "Antenatal consultation", "(max-width: 860px) 40vw, 240px", "collage__b")}
  </div>
</div></section>
<section class="section"><div class="container">
  <div class="section-head section-head--center reveal"><span class="eyebrow">Purpose</span><h2>Our mission, vision &amp; values</h2></div>
  {mv}
</div></section>
<section class="section section--white"><div class="container split split--reverse">
  <div class="reveal"><span class="eyebrow">Why choose us</span><h2>Care rooted in understanding the whole woman</h2>
    {"".join(f"<p>{e(p)}</p>" for p in SITE["why_us_about"])}</div>
  <div class="reveal">{img("about-3", "Doctor consulting a patient at Suvacha", "(max-width: 860px) 90vw, 520px", "")}</div>
</div></section>
{journey()}
<section class="section section--sand"><div class="container founder">
  <div class="founder__photo reveal">{img("dr-sachin", "Dr. Sachin Ladak Shedad", "(max-width: 860px) 90vw, 440px")}</div>
  <div class="reveal"><span class="eyebrow">Founder’s message</span>
    <blockquote>{e(SITE["founder_message"])}</blockquote>
    <p class="founder__name"><strong>Dr. Sachin Ladak Shedad</strong><span>Founder &amp; Clinical Director</span></p>
    <p style="margin-top:1.4em"><strong>Because healthy women build a healthier society.</strong> Suvacha Healthcare is dedicated to nurturing physical, emotional and hormonal well-being through responsible, women-centred medical care.</p>
    <a class="btn" href="/doctor/sachin/">Meet Dr. Sachin {icon("arrow")}</a></div>
</div></section>
{why_section()}
{cta_band()}
'''
    page("/about/", "About Us", "Suvacha Healthcare is a visionary initiative by Dr. Sachin Ladak Shedad integrating Ayurveda with modern medicine for women’s health, maternal wellness and community well-being.",
         body, extra_ld=[breadcrumb_ld([("Home", "/"), ("About", "/about/")])])


def build_services():
    trail = [("Home", "/"), ("Services", "/services/")]
    body = f'''
{page_hero("Our Services", "Comprehensive, personalised care designed to support women’s health, fertility and wellness at every stage of life — integrating modern medicine with classical Ayurveda.", trail, eyebrow="What we offer")}
<section class="section"><div class="container"><div class="services-grid">{"".join(service_card(s) for s in SERVICES)}</div></div></section>
{journey()}
{cta_band("Not sure which service you need?", "Tell us your concern on WhatsApp and we’ll guide you to the right specialist.")}
'''
    page("/services/", "Our Services", "Women’s health, pregnancy & maternal care, infertility, gynecology surgery, Garbhasanskar, Panchakarma, pediatrics, preventive wellness and andrology at Suvacha Healthcare, Khanvel, Dadra & Nagar Haveli.",
         body, extra_ld=[breadcrumb_ld(trail)])

    for s in SERVICES:
        url = f"/service/{s['slug']}/"
        trail = [("Home", "/"), ("Services", "/services/"), (s["title"], url)]
        cta = (f'<a class="btn btn--coral" href="/appointment/?service={s["slug"]}">{icon("calendar")} Book for this service</a>'
               f'<a class="btn btn--wa" href="{wa_link("Namaste, I would like to know more about " + s["title"] + ".")}" target="_blank" rel="noopener">{icon("whatsapp")} Ask a question</a>')
        nav = "".join(
            f'<li><a href="/service/{o["slug"]}/"{" aria-current=page" if o is s else ""}>{e(o["title"])}{icon("chev-right")}</a></li>' for o in SERVICES)
        body = f'''
{page_hero(s["title"], s["tagline"], trail, media=img("svc-" + s["slug"], s["title"], "(max-width: 860px) 90vw, 460px", eager=True), cta=cta, eyebrow="Service")}
<section class="section"><div class="container detail">
  <div class="detail__main">
    <div class="intro reveal">{"".join(f"<p>{e(p)}</p>" for p in s["intro"])}</div>
    {section_blocks(s["sections"])}
    <div class="block reveal svc-faq"><div class="block__head"><span class="block__num">?</span><h2>Frequently asked questions</h2></div>
      <div class="faq">{"".join(f'<details><summary>{e(f["q"])}<span class="faq__plus">{icon("plus")}</span></summary><p>{e(f["a"])}</p></details>' for f in SEO["services"][s["slug"]]["faqs"])}</div></div>
    <p class="closing reveal">Creating <span class="deva">श्रेयसी प्रजा</span> — healthy mothers, strong families, and a balanced society.</p>
  </div>
  <aside class="aside">
    {book_aside("In-clinic visits in Khanvel and online consultations available.", f"/appointment/?service={s['slug']}", "Namaste, I would like to book a consultation for " + s["title"] + ".")}
    {tool_aside(s["slug"])}
    <div class="aside-card"><h3>Specialists</h3>{mini_docs(s["doctors"])}</div>
    <div class="aside-card"><h3>All services</h3><ul class="aside-nav">{nav}</ul></div>
  </aside>
</div></section>
{cta_band()}
'''
        ld = {"@context": "https://schema.org", "@type": "MedicalWebPage", "name": s["title"], "about": {"@type": "MedicalTherapy", "name": s["title"]},
              "description": s["short"], "url": SITE["url"] + url, "provider": {"@id": SITE["url"] + "/#clinic"}}
        seo = SEO["services"][s["slug"]]
        page(url, seo["title"], seo["description"], body,
             extra_ld=[breadcrumb_ld(trail), ld, faq_ld(seo["faqs"])], og_image=f"svc-{s['slug']}", preload=f"svc-{s['slug']}")


def build_doctors():
    trail = [("Home", "/"), ("Doctors", "/doctors/")]
    chips = "".join(f'<button class="chip" type="button" data-filter="{k}" aria-pressed="{str(k == "all").lower()}">{e(v)}</button>' for k, v in FILTERS)
    body = f'''
{page_hero("Our Doctors", "Experienced, IMS–BHU trained specialists delivering compassionate, integrative care for women, families and children.", trail, eyebrow="Meet the team")}
<section class="section"><div class="container">
  <div class="filters" role="group" aria-label="Filter doctors by speciality">{chips}</div>
  <div class="doctors-grid">{"".join(doctor_card(d) for d in DOCTORS)}</div>
</div></section>
{cta_band("Book with the right specialist", "Choose your preferred doctor in the booking form — or let us match you.")}
'''
    page("/doctors/", "Our Doctors", "Meet the Suvacha Healthcare team — obstetricians, gynaecologists, infertility, Panchakarma, paediatric, surgical and yoga specialists trained at IMS–BHU.",
         body, extra_ld=[breadcrumb_ld(trail)])

    for d in DOCTORS:
        url = f"/doctor/{d['slug']}/"
        name = dr_name(d)
        trail = [("Home", "/"), ("Doctors", "/doctors/"), (name, url)]
        services = [s for s in SERVICES if d["slug"] in s["doctors"]]
        facts = [f'<li>{icon("graduation")}{e(d["qualification"])}</li>', f'<li>{icon("stethoscope")}{e(d["specialty"])}</li>']
        if d["online"]:
            facts.append(f'<li>{icon("video")}Online consultations</li>')
        roles2 = f'<p class="profile-hero__roles2">{e(d["roles2"])}</p>' if d.get("roles2") else ""
        others = [o["slug"] for o in DOCTORS if o is not d][:4]
        svc_list = "".join(f'<li><a href="/service/{s["slug"]}/">{e(s["title"])}{icon("chev-right")}</a></li>' for s in services)
        body = f'''
<section class="page-hero"><div class="container">
  <nav aria-label="Breadcrumb"><ol class="breadcrumb"><li><a href="/">Home</a></li><li><a href="/doctors/">Doctors</a></li><li aria-current="page">{e(name)}</li></ol></nav>
  <div class="profile-hero">
    <div class="profile-hero__img reveal">{img("dr-" + d["slug"], name, "(max-width: 860px) 90vw, 380px", eager=True)}</div>
    <div class="reveal">
      <span class="eyebrow">{e(d["specialty"])}</span>
      <h1>{e(name)}</h1>
      <p class="profile-hero__role">{e(d["role"])}</p>{roles2}
      {"".join(f"<p>{e(p)}</p>" for p in d["bio"])}
      <ul class="facts">{"".join(facts)}</ul>
      <div class="page-hero__cta">
        <a class="btn btn--coral" href="/appointment/?doctor={d["slug"]}">{icon("calendar")} Book with {e(name)}</a>
        <a class="btn btn--wa" href="{wa_link("Namaste, I would like to consult " + name + ".")}" target="_blank" rel="noopener">{icon("whatsapp")} WhatsApp</a>
      </div>
    </div>
  </div>
</div></section>
<section class="section"><div class="container detail">
  <div class="detail__main">
    {section_blocks(d["sections"], numbered=False)}
    {f'<p class="closing reveal">{e(d["closing"])}</p>' if d["closing"] else ""}
  </div>
  <aside class="aside">
    {book_aside("Choose an in-clinic visit or an online consultation.", f"/appointment/?doctor={d['slug']}", "Namaste, I would like to book an appointment with " + name + ".")}
    {f'<div class="aside-card"><h3>Related services</h3><ul class="aside-nav">{svc_list}</ul></div>' if services else ""}
    <div class="aside-card"><h3>Other specialists</h3>{mini_docs(others)}<a class="link-arrow" style="margin-top:10px" href="/doctors/">All doctors {icon("arrow")}</a></div>
  </aside>
</div></section>
'''
        ld = {"@context": "https://schema.org", "@type": "Physician", "name": name, "description": d["role"],
              "image": f"{SITE['url']}/assets/img/dr-{d['slug']}-960.webp", "url": SITE["url"] + url,
              "@id": SITE["url"] + url + "#physician",
              "medicalSpecialty": d["specialty"], "hasCredential": d["qualification"], "jobTitle": d["role"],
              "alumniOf": [{"@type": "CollegeOrUniversity", "name": v} for k, v in UNIVERSITIES.items() if k in d["qualification"]],
              "address": clinic_ld()["address"], "isAcceptingNewPatients": True,
              "worksFor": {"@id": SITE["url"] + "/#clinic"}, "telephone": SITE["phone"]}
        kw = SEO["doctors"][d["slug"]]
        t = f"{name} – {kw}, Khanvel | Suvacha"
        if len(t) > 70:
            t = f"{name} – {kw}, Khanvel"
        desc = f"{name}, {kw} at Suvacha Healthcare, Khanvel near Silvassa. {d['qualification']}. Book in-clinic or online."
        if len(desc) > 158:
            desc = f"{name}, {kw} at Suvacha Healthcare, Khanvel near Silvassa. {d['qualification']}."
        if len(desc) > 158:
            desc = f"{name}, {kw} at Suvacha Healthcare, Khanvel near Silvassa. Book in-clinic or online."
        page(url, t, desc, body, extra_ld=[breadcrumb_ld(trail), ld], og_image=f"dr-{d['slug']}", preload=f"dr-{d['slug']}", suffix=False)


def build_appointment():
    trail = [("Home", "/"), ("Appointment", "/appointment/")]
    steps = [("calendar", "Fill the form", "Tell us your name, number, concern and preferred doctor or time."),
             ("whatsapp", "Send on WhatsApp", "Your request opens in WhatsApp, pre-filled — just press send."),
             ("check-circle", "Get confirmation", "Our team confirms your slot for an in-clinic or online consultation.")]
    steps_html = "".join(f'<div class="pillar reveal"><div class="pillar__icon">{icon(i)}</div><h3>{n}. {t}</h3><p>{x}</p></div>'
                         for n, (i, t, x) in enumerate(steps, 1))
    body = f'''
{page_hero("Book an Appointment", "Need guidance for your health concerns? Book an in-clinic visit at our Khanvel clinic or an online consultation — it takes less than a minute.", trail, eyebrow="Appointments")}
<section class="section"><div class="container">{booking_form(heading=False)}</div></section>
<section class="section section--white"><div class="container">
  <div class="section-head section-head--center reveal"><span class="eyebrow">How it works</span><h2>Three simple steps</h2></div>
  <div class="pillars">{steps_html}</div>
</div></section>
{map_section()}
'''
    page("/appointment/", "Book an Appointment", "Book an in-clinic or online consultation with Suvacha Healthcare specialists in Khanvel via WhatsApp or phone.",
         body, extra_ld=[breadcrumb_ld(trail)])


def build_contact():
    trail = [("Home", "/"), ("Contact", "/contact/")]
    cards = [
        ("phone", "Appointments", SITE["phone_display"], TEL, ""),
        ("phone", "Emergency", SITE["emergency_display"], EMERG, ""),
        ("whatsapp", "WhatsApp", "Chat with our team", wa_link(), ' target="_blank" rel="noopener"'),
        ("mail", "Email", SITE["email"], MAIL, ""),
        ("pin", "Visit", SITE["address"]["display"], DIRECTIONS, ' target="_blank" rel="noopener"'),
    ]
    cards_html = "".join(f'<a class="contact-card reveal" href="{u}"{x}><span class="ci">{icon(i)}</span><h3>{t}</h3><p>{e(v)}</p></a>' for i, t, v, u, x in cards)
    body = f'''
{page_hero("Get in Touch", SITE["contact_intro"], trail, eyebrow="Contact")}
<section class="section"><div class="container">
  <div class="contact-cards">{cards_html}</div>
  <div class="split" style="margin-top:64px;align-items:start">
    <div class="reveal"><span class="eyebrow">Reach out to us for</span><h2>We’re here to help</h2>
      <ul class="checklist">{"".join(f"<li>{icon('check-circle')}<span>{e(r)}</span></li>" for r in SITE["contact_reasons"])}</ul>
      <p>Call us or write to us, and we will respond at the earliest.</p></div>
    <div class="aside-card reveal"><h3>Clinic hours <span class="open-badge" data-open-badge style="font-size:.9rem;font-family:var(--font-sans);color:var(--muted);margin-left:8px"></span></h3>{hours_table()}
      <p class="form-note">{icon("info")} Timings may vary on public holidays — please call ahead.</p></div>
  </div>
</div></section>
{map_section(sand=True)}
<section class="section"><div class="container">{booking_form(heading=False, id_="contact-book")}</div></section>
'''
    page("/contact/", "Contact Us", f"Contact Suvacha Healthcare — {SITE['address']['display']}. Call {SITE['phone_display']}, WhatsApp or email {SITE['email']}.",
         body, extra_ld=[breadcrumb_ld(trail)])


def tools_promo():
    return f'''<section class="section section--white"><div class="container">
  <div class="section-head section-head--center reveal"><span class="eyebrow">Free tools</span>
  <h2>Pregnancy &amp; fertility calculators</h2>
  <p>Know your due date, your scan schedule and your fertile days — then book with our team in one tap.</p></div>
  <div class="tool-promos">
    <a class="tool-promo reveal" href="/pregnancy-tools/#due-date"><span class="pillar__icon">{icon("baby")}</span>
      <span><h3>Due date &amp; scan planner</h3><p>Your expected delivery date, current week, trimester and a personal timeline of scans and tests.</p>
      <span class="svc-card__more">Calculate {icon("arrow")}</span></span></a>
    <a class="tool-promo reveal" href="/pregnancy-tools/#ovulation"><span class="pillar__icon" style="background:var(--green-100);color:var(--green-700)">{icon("flower")}</span>
      <span><h3>Ovulation &amp; fertile window</h3><p>Planning a pregnancy? See your most fertile days for the next three cycles.</p>
      <span class="svc-card__more">Calculate {icon("arrow")}</span></span></a>
  </div>
</div></section>'''


def build_tools():
    url = "/pregnancy-tools/"
    trail = [("Home", "/"), ("Pregnancy Tools", url)]
    body = f'''
{page_hero("Pregnancy & Fertility Tools", "Free calculators to estimate your due date, plan your antenatal scans and find your fertile window. Results stay on your device.", trail, eyebrow="Free tools")}
<section class="section"><div class="container tool-grid">
  <article class="tool-card reveal" id="due-date">
    <div class="block__head"><span class="pillar__icon">{icon("baby")}</span><div><h2>Due date &amp; scan planner</h2><p class="tool-card__sub">Based on the first day of your last period</p></div></div>
    <form data-tool="edd" novalidate>
      <div class="form-grid">
        <div class="field"><label for="edd-lmp">First day of last period <span class="req">*</span></label><input id="edd-lmp" name="lmp" type="date" required></div>
        <div class="field"><label for="edd-cycle">Average cycle length (days)</label><input id="edd-cycle" name="cycle" type="number" min="21" max="45" value="28" inputmode="numeric"></div>
      </div>
      <button class="btn btn--coral" type="submit" style="margin-top:18px">{icon("calendar")} Calculate due date</button>
    </form>
    <div class="tool-result" data-result="edd" aria-live="polite" hidden></div>
  </article>
  <article class="tool-card reveal" id="ovulation">
    <div class="block__head"><span class="pillar__icon" style="background:var(--green-100);color:var(--green-700)">{icon("flower")}</span><div><h2>Ovulation &amp; fertile window</h2><p class="tool-card__sub">For couples planning a pregnancy</p></div></div>
    <form data-tool="ovulation" novalidate>
      <div class="form-grid">
        <div class="field"><label for="ov-lmp">First day of last period <span class="req">*</span></label><input id="ov-lmp" name="lmp" type="date" required></div>
        <div class="field"><label for="ov-cycle">Average cycle length (days)</label><input id="ov-cycle" name="cycle" type="number" min="21" max="45" value="28" inputmode="numeric"></div>
      </div>
      <button class="btn" type="submit" style="margin-top:18px">{icon("calendar")} Show fertile days</button>
    </form>
    <div class="tool-result" data-result="ovulation" aria-live="polite" hidden></div>
  </article>
</div>
<div class="container"><p class="form-note" style="max-width:820px">{icon("info")} These are estimates for general guidance only. Your doctor will confirm your dates with an early ultrasound, and actual scan timing depends on your clinical needs. Nothing you enter is sent or stored.</p></div>
</section>
{cta_band("Pregnant or planning a pregnancy?", "Book antenatal care, Garbhasanskar or a fertility consultation with our specialists.")}
'''
    page(url, "Pregnancy Due Date & Ovulation Calculator", "Free pregnancy due date calculator with a personal antenatal scan timeline, plus an ovulation and fertile-window calculator — from Suvacha Healthcare, Khanvel.",
         body, extra_ld=[breadcrumb_ld(trail)])


# ---------------------------------------------------------------- blog
def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def md_inline(s):
    s = e(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)\*(?!\w)", r"<em>\1</em>", s)
    return re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)


def md_to_html(text):
    """Small Markdown subset: ## / ### headings, - and 1. lists, > callouts, paragraphs."""
    out, toc, lst = [], [], None
    def close():
        nonlocal lst
        if lst:
            out.append(f"</{lst}>")
            lst = None
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().split("\n")
        for line in lines:
            line = line.rstrip()
            if line.startswith("## "):
                close(); t = line[3:]; hid = slugify(t); toc.append((hid, t))
                out.append(f'<h2 id="{hid}">{md_inline(t)}</h2>')
            elif line.startswith("### "):
                close(); out.append(f"<h3>{md_inline(line[4:])}</h3>")
            elif line.startswith("- "):
                if lst != "ul": close(); out.append('<ul class="ticks ticks--single">'); lst = "ul"
                out.append(f"<li>{icon('check-circle')}<span>{md_inline(line[2:])}</span></li>")
            elif re.match(r"\d+\. ", line):
                if lst != "ol": close(); out.append("<ol>"); lst = "ol"
                out.append(f"<li>{md_inline(line.split('. ', 1)[1])}</li>")
            elif line.startswith("> "):
                close(); out.append(f'<p class="block__note">{icon("info")}<span>{md_inline(line[2:])}</span></p>')
            else:
                close(); out.append(f"<p>{md_inline(line)}</p>")
        close()
    return "\n".join(out), toc


def load_posts():
    posts = []
    for f in sorted((ROOT / "content" / "blog").glob("*.md")):
        raw = f.read_text()
        _, fm, body = raw.split("---", 2)
        meta = {}
        for line in fm.strip().splitlines():
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
        html, toc = md_to_html(body)
        words = len(re.findall(r"\w+", body))
        meta["sources"] = [tuple(x.strip().split("|", 1)) for x in meta.get("sources", "").split(";;") if "|" in x]
        meta["reviewer"] = DOC_BY.get(meta.get("reviewed_by", "").strip())
        posts.append({**meta, "slug": f.stem, "html": html, "toc": toc, "minutes": max(2, round(words / 200)),
                      "cat_slug": slugify(meta["category"]),
                      "date_display": dt.date.fromisoformat(meta["date"]).strftime("%-d %b %Y")})
    return sorted(posts, key=lambda p: p["date"], reverse=True)


POSTS = load_posts()


def post_card(p):
    return f'''<a class="svc-card post-card reveal" href="/blog/{p["slug"]}/" data-tags="{p["cat_slug"]}">
  <div class="svc-card__img">{img(p["image"], "", "(max-width: 600px) 100vw, (max-width: 860px) 50vw, 380px")}</div>
  <div class="svc-card__body"><span class="post-card__cat">{e(p["category"])}</span><h3>{e(p["title"])}</h3><p>{e(p["description"])}</p>
  <span class="post-card__meta">{icon("clock")} {p["minutes"]} min read</span></div></a>'''


def blog_section():
    cards = "".join(post_card(p) for p in POSTS[:3])
    return f'''<section class="section section--white"><div class="container">
  <div class="section-head section-head--split reveal"><div><span class="eyebrow">Health tips</span><h2>Guidance from our doctors’ desk</h2>
  <p>Simple, trustworthy information on women’s health, pregnancy and fertility.</p></div>
  <a class="btn btn--ghost" href="/blog/">All articles {icon("arrow")}</a></div>
  <div class="services-grid">{cards}</div>
</div></section>'''


def reviews_section():
    r = REVIEWS
    review_url = SITE["google_place_url"]
    if r.get("reviews"):
        stars = lambda n: "★" * int(n) + "☆" * (5 - int(n))
        cards = "".join(
            f'<figure class="review reveal"><div class="review__stars" aria-label="{x["rating"]} out of 5">{stars(x["rating"])}</div>'
            f'<blockquote>{e(x["text"])}</blockquote><figcaption>{e(x["author"])}</figcaption></figure>' for x in r["reviews"])
        summary = f'<p class="review-summary"><strong>{r["rating"]} ★</strong> from {r["count"]} Google reviews</p>' if r.get("rating") else ""
        return f'''<section class="section"><div class="container">
  <div class="section-head section-head--split reveal"><div><span class="eyebrow">Patient stories</span><h2>What families say about us</h2>{summary}</div>
  <a class="btn btn--ghost" href="{review_url}" target="_blank" rel="noopener">Read all on Google {icon("arrow")}</a></div>
  <div class="reviews">{cards}</div></div></section>'''
    return f'''<section class="section"><div class="container"><div class="review-cta reveal">
  <div class="review-cta__stars" aria-hidden="true">★★★★★</div>
  <div><span class="eyebrow">Your voice matters</span><h2>Had a good experience at Suvacha?</h2>
  <p>A short Google review helps other mothers and families in Khanvel, Silvassa and nearby find trusted care. It takes less than a minute.</p></div>
  <div class="review-cta__actions">
    <a class="btn btn--coral" href="{review_url}" target="_blank" rel="noopener">★ Write a Google review</a>
    <a class="btn btn--ghost" href="{wa_link("Namaste, I would like to share feedback about my visit.")}" target="_blank" rel="noopener">{icon("whatsapp")} Share feedback privately</a>
  </div></div></div></section>'''


def build_blog():
    trail = [("Home", "/"), ("Health Tips", "/blog/")]
    cats = []
    for p in POSTS:
        if (p["cat_slug"], p["category"]) not in cats:
            cats.append((p["cat_slug"], p["category"]))
    chips = '<button class="chip" type="button" data-filter="all" aria-pressed="true">All articles</button>' + "".join(
        f'<button class="chip" type="button" data-filter="{k}" aria-pressed="false">{e(v)}</button>' for k, v in cats)
    body = f'''
{page_hero("Health Tips & Guides", "Trustworthy, easy-to-read guidance on women’s health, pregnancy, fertility and wellness from the Suvacha Healthcare team.", trail, eyebrow="Blog")}
<section class="section"><div class="container">
  <div class="filters" role="group" aria-label="Filter articles by topic">{chips}</div>
  <div class="services-grid">{"".join(post_card(p) for p in POSTS)}</div>
</div></section>
{cta_band("Have a question about your health?", "Our doctors are happy to guide you — in clinic or online.")}
'''
    page("/blog/", "Health Tips & Guides", "Articles on PCOS, pregnancy diet, pregnancy warning signs, antenatal scans, Garbhasanskar, male fertility and irregular periods from Suvacha Healthcare, Khanvel.",
         body, extra_ld=[breadcrumb_ld(trail)])

    for p in POSTS:
        url = f"/blog/{p['slug']}/"
        trail = [("Home", "/"), ("Health Tips", "/blog/"), (p["title"], url)]
        svc = SVC_BY.get(p.get("service", ""))
        related = [q for q in POSTS if q is not p and q["category"] == p["category"]]
        related += [q for q in POSTS if q is not p and q not in related]
        toc = "".join(f'<li><a href="#{hid}">{e(t)}{icon("chev-right")}</a></li>' for hid, t in p["toc"])
        share = wa_link(f"{p['title']} — {SITE['url']}{url}")
        rv = p["reviewer"]
        reviewed = (f'<li>{icon("shield")} Medically reviewed by <a href="/doctor/{rv["slug"]}/">{e(dr_name(rv))}</a></li>') if rv else ""
        sources = ('<div class="sources"><h2>Sources &amp; further reading</h2><ol>' + "".join(
            f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a></li>' for t, u in p["sources"]) + "</ol></div>") if p["sources"] else ""
        svc_card = (f'<a class="aside-card aside-tool" href="/service/{svc["slug"]}/"><span class="pillar__icon">{icon("stethoscope")}</span>'
                    f'<span><strong>{e(svc["title"])}</strong><span>Learn about our care and specialists.</span></span></a>') if svc else ""
        body = f'''
<section class="page-hero"><div class="container">
  <nav aria-label="Breadcrumb"><ol class="breadcrumb"><li><a href="/">Home</a></li><li><a href="/blog/">Health Tips</a></li><li aria-current="page">{e(p["title"])}</li></ol></nav>
  <span class="eyebrow">{e(p["category"])}</span>
  <h1>{e(p["title"])}</h1>
  <p class="lead">{e(p["description"])}</p>
  <ul class="post-meta"><li>{icon("user")} Suvacha Healthcare Team</li>{reviewed}<li>{icon("calendar")} {p["date_display"]}</li><li>{icon("clock")} {p["minutes"]} min read</li></ul>
</div></section>
<section class="section"><div class="container detail">
  <article class="detail__main">
    <div class="post-cover">{img(p["image"], p["title"], "(max-width: 1100px) 100vw, 760px", eager=True)}</div>
    <div class="prose">{p["html"]}</div>
    {sources}
    <div class="post-foot">
      <a class="btn btn--wa btn--sm" href="{share}" target="_blank" rel="noopener">{icon("whatsapp")} Share on WhatsApp</a>
      <a class="btn btn--ghost btn--sm" href="/blog/">{icon("arrow-left")} All articles</a>
    </div>
    <p class="form-note">{icon("info")} This article is for general awareness and does not replace a consultation with a qualified doctor. In an emergency, call {e(SITE["emergency_display"])} or visit the nearest hospital.</p>
  </article>
  <aside class="aside">
    {book_aside("Talk to our specialists — in clinic or online.", f"/appointment/?service={svc['slug']}" if svc else "/appointment/", "Namaste, I read your article “" + p["title"] + "” and have a question.")}
    {f'<div class="aside-card"><h3>In this article</h3><ul class="aside-nav">{toc}</ul></div>' if toc else ""}
    {svc_card}
    {tool_aside(svc["slug"]) if svc else ""}
  </aside>
</div></section>
<section class="section section--sand"><div class="container">
  <div class="section-head reveal"><span class="eyebrow">Keep reading</span><h2>Related articles</h2></div>
  <div class="services-grid">{"".join(post_card(q) for q in related[:3])}</div>
</div></section>
'''
        ld = {"@context": "https://schema.org", "@type": "MedicalWebPage", "headline": p["title"], "description": p["description"],
              "datePublished": p["date"], "dateModified": p["date"], "url": SITE["url"] + url,
              "image": f"{SITE['url']}/assets/img/{p['image']}-960.webp",
              "author": {"@type": "Organization", "name": SITE["name"]}, "publisher": {"@id": SITE["url"] + "/#clinic"},
              "inLanguage": "en-IN", "lastReviewed": p["date"],
              "citation": [{"@type": "CreativeWork", "name": t_, "url": u_} for t_, u_ in p["sources"]],
              "about": {"@type": "MedicalCondition", "name": p["category"]} if p["category"] != "Ayurveda & Wellness" else None,
              "mainEntityOfPage": SITE["url"] + url}
        if rv:
            ld["reviewedBy"] = {"@id": f"{SITE['url']}/doctor/{rv['slug']}/#physician"}
        ld = {k: v for k, v in ld.items() if v is not None}
        t = f"{p['title']} | Suvacha" if len(p["title"]) <= 56 else p["title"]
        page(url, t, p["description"], body, extra_ld=[breadcrumb_ld(trail), ld],
             og_image=p["image"], og_type="article", published=p["date"], suffix=False)


def build_404():
    body = f'''<section class="notfound"><div class="container">
  <p class="big">404</p><h1>Page not found</h1>
  <p style="color:var(--muted);max-width:520px;margin:0 auto 2em">The page you are looking for may have moved. Try one of these instead:</p>
  <div style="display:flex;flex-wrap:wrap;gap:12px;justify-content:center">
    <a class="btn" href="/">Home</a><a class="btn btn--ghost" href="/services/">Services</a>
    <a class="btn btn--ghost" href="/doctors/">Doctors</a><a class="btn btn--coral" href="/appointment/">Book appointment</a></div>
</div></section>'''
    page("/404.html", "Page not found", "Page not found.", body, noindex=True)


def llms_txt():
    """Plain-text site summary for AI search engines (llmstxt.org convention)."""
    a = SITE["address"]
    hours = "; ".join(f'{h["days"]} {h["label"]}' for h in SITE["hours"])
    lines = [f"# {SITE['name']}", "",
             f"> {SITE['about_short']}", "",
             "## Key facts",
             f"- Address: {a['display']}",
             f"- Location: Khanvel, near Silvassa, Dadra and Nagar Haveli, India (lat {SITE['geo']['lat']}, lng {SITE['geo']['lng']})",
             f"- Appointments & WhatsApp: {SITE['phone_display']}",
             f"- Emergency: {SITE['emergency_display']}",
             f"- Email: {SITE['email']}",
             f"- Hours: {hours}",
             "- Founder & Clinical Director: Dr. Sachin Ladak Shedad, MS (PTSR) – IMS, Banaras Hindu University; FMAS – MUHS",
             "- Approach: modern obstetrics & gynecology integrated with classical Ayurveda; normal delivery preferred when medically safe",
             "- Consultations: in-clinic in Khanvel and online", "",
             "## Services"]
    lines += [f"- [{s['title']}]({SITE['url']}/service/{s['slug']}/): {s['short']}" for s in SERVICES]
    lines += ["", "## Doctors"]
    lines += [f"- [{dr_name(d)}]({SITE['url']}/doctor/{d['slug']}/): {d['role']} — {d['qualification']}" for d in DOCTORS]
    lines += ["", "## Health articles"]
    lines += [f"- [{p['title']}]({SITE['url']}/blog/{p['slug']}/): {p['description']}" for p in POSTS]
    lines += ["", "## Tools", f"- [Pregnancy due date & ovulation calculator]({SITE['url']}/pregnancy-tools/)", ""]
    return "\n".join(lines)


def build_og_images():
    """1200x630 JPEG share images (WhatsApp/Facebook don't reliably show WebP)."""
    out = OUT / "assets" / "og"
    out.mkdir(parents=True, exist_ok=True)
    for name in sorted(OG_IMAGES):
        with Image.open(SRC / "img" / f"{name}-960.webp") as im:
            im = im.convert("RGB")
            scale = max(1200 / im.width, 630 / im.height)
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
            top = int((im.height - 630) * (0.15 if name.startswith("dr-") else 0.35))
            left = (im.width - 1200) // 2
            im.crop((left, top, left + 1200, top + 630)).save(out / f"{name}.jpg", quality=80, optimize=True, progressive=True)


def build_meta(paths):
    urls = "".join(f"<url><loc>{SITE['url']}{p}</loc><lastmod>{TODAY}</lastmod></url>" for p in paths)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    (OUT / "_headers").write_text("""/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
/assets/img/*
  Cache-Control: public, max-age=2592000
/assets/css/*
  Cache-Control: public, max-age=31536000, immutable
/assets/js/*
  Cache-Control: public, max-age=31536000, immutable
""")
    # Old WordPress URLs -> new pages
    (OUT / "_redirects").write_text("""/home            /            301
/service         /services/   301
/doctor          /doctors/    301
/feed            /blog/       301
/feed/*          /blog/       301
/blog/feed/*     /blog/       301
/wp-admin/*      /            301
/wp-login.php    /            301
/?p=*            /            301
""")
    bots = ["Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Applebot"]
    (OUT / "robots.txt").write_text("".join(f"User-agent: {x}\nAllow: /\n\n" for x in bots) +
                                    f"User-agent: *\nAllow: /\n\nSitemap: {SITE['url']}/sitemap.xml\n")
    (OUT / "llms.txt").write_text(llms_txt())
    (OUT / "site.webmanifest").write_text(json.dumps({
        "name": SITE["name"], "short_name": "Suvacha", "start_url": "/", "display": "standalone",
        "background_color": "#fbf7f1", "theme_color": "#1f2e1c",
        "icons": [{"src": "/assets/img/favicon-180.png", "sizes": "180x180", "type": "image/png"},
                  {"src": "/assets/img/favicon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2))


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    for d in ("css", "js", "img"):
        shutil.copytree(SRC / d, OUT / "assets" / d)
    build_home()
    build_about()
    build_services()
    build_doctors()
    build_appointment()
    build_contact()
    build_tools()
    build_blog()
    build_404()
    paths = ["/", "/about/", "/services/", "/doctors/", "/appointment/", "/contact/", "/pregnancy-tools/"]
    paths += [f"/service/{s['slug']}/" for s in SERVICES] + [f"/doctor/{d['slug']}/" for d in DOCTORS]
    paths += ["/blog/"] + [f"/blog/{p['slug']}/" for p in POSTS]
    build_meta(paths)
    build_og_images()
    print(f"Built {len(paths) + 1} pages into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Serving on http://localhost:8000  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("", 8000), handler).serve_forever()
