"""Validate content/i18n/<lang>/ against the English source.

    python3 tools/check_i18n.py hi
    python3 tools/check_i18n.py mr

Checks: valid JSON, every key/field present, list lengths match English (so the
build can overlay item by item), {placeholders} kept, and text is in Devanagari.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = ROOT / "content"
DEVA = re.compile(r"[ऀ-ॿ]")
PH = re.compile(r"\{[a-z]+\}")
errors = []


def err(msg):
    errors.append(msg)


def load(lang, name):
    p = C / "i18n" / lang / f"{name}.json"
    if not p.exists():
        err(f"missing file {p.relative_to(ROOT)}")
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        err(f"{p.relative_to(ROOT)}: invalid JSON ({e})")
        return None


def deva(where, s):
    if isinstance(s, str) and s.strip() and re.search(r"[A-Za-z]{4,}", s) and not DEVA.search(s) \
            and not re.fullmatch(r"[A-Z0-9 /+–().,-]+", s):  # abbreviations like "PCOD / PCOS" stay in Latin
        err(f"{where}: looks untranslated: {s[:60]!r}")


def same_shape(where, en, tr):
    """tr must mirror en: same keys for dicts it covers, same lengths for lists."""
    if isinstance(en, dict):
        if not isinstance(tr, dict):
            return err(f"{where}: expected object")
        for k, v in tr.items():
            if k not in en:
                err(f"{where}.{k}: unknown field")
            else:
                same_shape(f"{where}.{k}", en[k], v)
    elif isinstance(en, list):
        if not isinstance(tr, list) or len(tr) != len(en):
            return err(f"{where}: expected list of {len(en)}, got {len(tr) if isinstance(tr, list) else type(tr).__name__}")
        for i, (a, b) in enumerate(zip(en, tr)):
            same_shape(f"{where}[{i}]", a, b)
    elif isinstance(en, str):
        if not isinstance(tr, str):
            return err(f"{where}: expected text")
        deva(where, tr)


def main(lang):
    site_en = json.loads((C / "site.json").read_text())
    svc_en = {s["slug"]: s for s in json.loads((C / "services.json").read_text())}
    seo_en = json.loads((C / "seo.json").read_text())
    doc_en = {d["slug"]: d for d in json.loads((C / "doctors.json").read_text())}

    site = load(lang, "site")
    if site is not None:
        need = ["whatsapp_greeting", "address", "nearby", "hours", "about_short", "about", "hero", "stats", "journey",
                "why", "mission", "vision", "values", "why_us_about", "founder_message", "contact_intro",
                "contact_reasons", "faqs"]
        for k in need:
            if k not in site:
                err(f"site.{k}: missing")
        same_shape("site", site_en, site)

    svc = load(lang, "services")
    if svc is not None:
        for slug, en in svc_en.items():
            tr = svc.get(slug)
            if not tr:
                err(f"services.{slug}: missing")
                continue
            for k in ("title", "tagline", "short", "intro", "sections"):
                if k not in tr:
                    err(f"services.{slug}.{k}: missing")
            same_shape(f"services.{slug}", {k: en[k] for k in ("title", "tagline", "short", "intro", "sections")}, tr)

    seo = load(lang, "seo")
    if seo is not None:
        for path in seo_en["pages"]:
            if path not in seo.get("pages", {}):
                err(f"seo.pages[{path}]: missing")
        for slug in seo_en["services"]:
            if slug not in seo.get("services", {}):
                err(f"seo.services.{slug}: missing")
        same_shape("seo", {"pages": seo_en["pages"], "services": seo_en["services"]},
                   {k: v for k, v in seo.items() if k in ("pages", "services")})

    docs = load(lang, "doctors")
    if docs is not None:
        for slug, en in doc_en.items():
            tr = docs.get(slug, {})
            fields = ["specialty", "role", "bio", "sections", "closing"] + (["roles2"] if en.get("roles2") else [])
            for k in fields:
                if k not in tr:
                    err(f"doctors.{slug}.{k}: missing")
            same_shape(f"doctors.{slug}", {k: en[k] for k in fields}, {k: v for k, v in tr.items() if k in fields})
        for slug in doc_en:
            if slug not in seo.get("doctors", {}) if seo else False:
                err(f"seo.doctors.{slug}: missing (title keyword)")

    blog_en = sorted((C / "blog").glob("*.md"))
    for f in blog_en:
        tr = C / "i18n" / lang / "blog" / f.name
        if not tr.exists():
            err(f"blog/{f.name}: missing translation")
            continue
        raw_en, raw_tr = f.read_text(), tr.read_text()
        try:
            _, fm, body = raw_tr.split("---", 2)
        except ValueError:
            err(f"blog/{f.name}: front matter missing")
            continue
        for key in ("title", "description", "category"):
            m = re.search(rf"^{key}: (.+)$", fm, re.M)
            if not m:
                err(f"blog/{f.name}: front matter '{key}' missing")
            else:
                deva(f"blog/{f.name}:{key}", m.group(1))
        body_en = raw_en.split("---", 2)[2]
        for mark, name in (("## ", "h2"), ("### ", "h3"), ("- ", "list items"), ("> ", "callouts")):
            a = sum(1 for l in body_en.splitlines() if l.startswith(mark))
            b = sum(1 for l in body.splitlines() if l.startswith(mark))
            if a != b:
                err(f"blog/{f.name}: {name} count {b} != English {a}")
        for url in re.findall(r"\]\((/[^)]+)\)", body_en):
            if f"]({url})" not in body:
                err(f"blog/{f.name}: internal link {url} missing")

    for name, keyfiles in (("strings", ("strings-keys.json", "strings-keys-2.json")), ("js", ("js-keys.json",))):
        table = load(lang, name)
        keys = [k for kf in keyfiles for k in json.loads((ROOT / "build" / kf).read_text())]
        if table is None:
            continue
        for k in keys:
            if k not in table:
                err(f"{name}: missing key {k!r}")
            elif sorted(PH.findall(k)) != sorted(PH.findall(table[k])):
                err(f"{name}: placeholders changed for {k!r}")

    if errors:
        print(f"{len(errors)} problem(s):")
        print("\n".join("  " + e for e in errors[:80]))
        sys.exit(1)
    print(f"{lang}: OK")


if __name__ == "__main__":
    main(sys.argv[1])
