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
        same_shape("seo", {"pages": seo_en["pages"], "services": seo_en["services"]}, seo)

    docs = load(lang, "doctors")
    if docs is not None:
        for slug in doc_en:
            if "specialty" not in docs.get(slug, {}):
                err(f"doctors.{slug}.specialty: missing")
            else:
                deva(f"doctors.{slug}.specialty", docs[slug]["specialty"])

    for name, keyfile in (("strings", "strings-keys.json"), ("js", "js-keys.json")):
        table = load(lang, name)
        keys = json.loads((ROOT / "build" / keyfile).read_text())
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
