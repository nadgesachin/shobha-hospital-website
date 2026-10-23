"""Parse the scraped page text (_original/text/*.md) into structured JSON
content files under content/. Run once after scraping; the JSON is then
the editable source of truth for build.py."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / "_original" / "text"
OUT = ROOT / "content"

IMG_RE = re.compile(r"\[IMG [^\]]*\]")


def body_lines(name):
    """Main-content lines of a page, without the shared header/footer."""
    raw = (TEXT / f"{name}.md").read_text()
    on, lines = False, []
    for line in raw.splitlines():
        if "Week Days: 09.00" in line:
            on = True
            continue
        if "women-focused wellness center integrating" in line:
            break
        if on:
            lines.append(line)
    return lines


def clean(s):
    s = IMG_RE.sub("", s).replace("​", "")
    s = re.sub(r"\s+([,.;:!?)])", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_sections(lines):
    """Split '### heading' blocks into {title, paras, groups:[{label, items}], note}."""
    sections, cur = [], None
    pending_heading = False
    for raw in lines:
        is_h3 = raw.startswith("### ")
        line = clean(raw[4:] if is_h3 else raw)
        if is_h3:
            cur = {"title": line, "paras": [], "groups": [], "note": ""}
            sections.append(cur)
            pending_heading = not line
            continue
        if cur is None or not line:
            continue
        if pending_heading:  # heading text came on the line after '### '
            cur["title"] = line
            pending_heading = False
            continue
        if line.endswith(":") and len(line) < 70:
            cur["groups"].append({"label": line.rstrip(":"), "items": []})
        elif cur["groups"] and not line.endswith("."):
            cur["groups"][-1]["items"].append(line)
        elif cur["groups"]:
            cur["note"] = (cur["note"] + " " + line).strip()
        elif len(line) < 90 and not line.endswith("."):
            # short bullet-like lines with no label (e.g. "Qualifications")
            cur["groups"].append({"label": "", "items": [line]}) if not cur["groups"] else None
        else:
            cur["paras"].append(line)
    # merge consecutive unlabeled single-item groups produced above
    for s in sections:
        merged = []
        for g in s["groups"]:
            if merged and not g["label"] and not merged[-1]["label"]:
                merged[-1]["items"] += g["items"]
            else:
                merged.append(g)
        s["groups"] = merged
    return sections


END_MARKERS = ("Need guidance for your health concerns?", "Creating श्रेयसी प्रजा —")


def parse_service(name, slug):
    lines = body_lines(name)
    # skip the side-nav list of services; content starts at the first image
    start = next(i for i, l in enumerate(lines) if l.startswith("[IMG"))
    lines = lines[start + 1:]
    end = next((i for i, l in enumerate(lines) if any(m in l for m in END_MARKERS)), len(lines))
    lines = lines[:end]
    if lines and clean(lines[-1]) == "Suvacha Healthcare":
        lines = lines[:-1]
    head = []
    for i, l in enumerate(lines):
        if l.startswith("### "):
            break
        head.append(clean(l.lstrip("# ")))
    head = [h for h in head if h]
    return {
        "slug": slug,
        "title": head[0],
        "tagline": head[1] if len(head) > 1 else "",
        "intro": head[2:],
        "sections": parse_sections(lines[len(head) and i:]),
    }


def parse_doctor(name, slug):
    lines = [l for l in body_lines(name) if not l.startswith("[IMG")]
    name_i = next(i for i, l in enumerate(lines) if l.startswith("## "))
    head = []
    for l in lines[name_i:]:
        if l.startswith("### "):
            break
        head.append(clean(l.lstrip("# ")))
    head = [h for h in head if h]
    rest = lines[name_i + len(head):]
    sections = parse_sections(rest)
    closing = ""
    if sections and sections[-1]["groups"] and sections[-1]["note"]:
        closing = sections[-1]["note"]
        sections[-1]["note"] = ""
    return {
        "slug": slug,
        "name": head[0],
        "role": head[1],
        "bio": head[2:],
        "sections": sections,
        "closing": closing,
    }


SERVICES = [
    ("service_womens_health_integrative_care", "womens-health-integrative-care"),
    ("service_pregnancy_maternal_care", "pregnancy-maternal-care"),
    ("service_infertility_reproductive_health", "infertility-reproductive-health"),
    ("service_gynecology_surgical_care", "gynecology-surgical-care"),
    ("service_garbhasanskar", "garbhasanskar"),
    ("service_panchakarma_therapies", "panchakarma-therapies"),
    ("service_basic_pediatrics", "basic-pediatrics"),
    ("service_holistic_wellness_preventive_care", "holistic-wellness-preventive-care"),
    ("service_andrology_male_infertility", "andrology-male-infertility"),
]
DOCTORS = [
    ("doctor_sachin", "sachin"),
    ("doctor_vaishali_mishra", "vaishali-mishra"),
    ("doctor_lalita", "lalita"),
    ("doctor_anushka", "anushka"),
    ("doctor_manish", "manish"),
    ("doctor_neha_sunia", "neha-sunia"),
    ("doctor_shailesh", "shailesh"),
    ("doctor_shobhan", "shobhan"),
    ("doctor_rangaswamy", "rangaswamy"),
    ("doctor_srinivasa", "srinivasa"),
    ("doctor_randheer_kadam", "randheer-kadam"),
]

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    services = [parse_service(n, s) for n, s in SERVICES]
    doctors = [parse_doctor(n, s) for n, s in DOCTORS]
    (OUT / "services.parsed.json").write_text(json.dumps(services, ensure_ascii=False, indent=2))
    (OUT / "doctors.parsed.json").write_text(json.dumps(doctors, ensure_ascii=False, indent=2))
    for s in services:
        print(s["title"], "|", s["tagline"][:40], "|", len(s["intro"]), "intro |",
              [(x["title"][:28], len(x["paras"]), [len(g["items"]) for g in x["groups"]], bool(x["note"])) for x in s["sections"]])
    for d in doctors:
        print(d["name"], "|", d["role"][:40], "|", [(x["title"][:20], len(x["paras"]), [len(g["items"]) for g in x["groups"]]) for x in d["sections"]], bool(d["closing"]))
