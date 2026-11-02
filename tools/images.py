"""Convert the scraped originals (_original/assets) into optimised, sensibly
named WebP files in src/img/ (two widths each, for srcset)."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_original" / "assets"
OUT = ROOT / "src" / "img"

# friendly name -> original file
IMAGES = {
    "hero": "hero-original.png",
    "about-1": "Jan-13-2026-06_36_58-AM.png",
    "about-2": "ChatGPT-Image-Jan-13-2026-06_48_26-AM.png",
    "about-3": "ChatGPT-Image-Jan-13-2026-07_06_24-AM.png",
    "lotus": "lotus-6474572_1920.jpg",
    # home banner: Indian parents with their newborn (Pexels, free licence) — https://www.pexels.com/photo/30012175/
    "hero-family": "pexels-dream-makkerzz-30012175.jpg",
    # services
    "svc-womens-health-integrative-care": "kimia-kazemi-4jpue-X7cFU-unsplash.jpg",
    "svc-pregnancy-maternal-care": "shashank-verma-lxdDwKSWuT8-unsplash.jpg",
    "svc-infertility-reproductive-health": "pexels-pavel-danilyuk-7055859.jpg",
    "svc-gynecology-surgical-care": "pexels-jonathanborba-3259625.jpg",
    "svc-garbhasanskar": "pexels-mart-production-7089047.jpg",
    "svc-panchakarma-therapies": "herbal-compress-herbal-spa-treatment-equipments-put-dark-floor.jpg",
    "svc-basic-pediatrics": "pexels-kseniachernaya-6671023.jpg",
    "svc-holistic-wellness-preventive-care": "pexels-polina-tankilevitch-3873201.jpg",
    "svc-andrology-male-infertility": "couple-suffering-from-infertility-scaled.jpg",
    # doctors
    "dr-sachin": "WhatsApp-Image-2025-12-29-at-9.43.28-PM.jpeg",
    "dr-vaishali-mishra": "ChatGPT-Image-Jan-5-2026-09_33_23-AM.png",
    "dr-lalita": "ChatGPT-Image-Jan-5-2026-09_50_53-AM.png",
    "dr-anushka": "WhatsApp-Image-2025-12-29-at-9.43.24-PM.jpeg",
    "dr-manish": "ChatGPT-Image-Jan-5-2026-09_45_35-AM.png",
    "dr-neha-sunia": "ChatGPT-Image-Jan-5-2026-09_29_21-AM.png",
    "dr-shailesh": "ChatGPT-Image-Jan-5-2026-09_40_37-AM.png",
    "dr-shobhan": "Gemini_Generated_Image_asq6x1asq6x1asq6-1.png",
    "dr-rangaswamy": "WhatsApp-Image-2025-12-29-at-9.43.28-PM-1.jpeg",
    "dr-srinivasa": "ChatGPT-Image-Jan-5-2026-09_48_06-AM.png",
    "dr-randheer-kadam": "ChatGPT-Image-Jan-5-2026-09_02_09-AM.png",
}
WIDTHS = (480, 960)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, src in IMAGES.items():
        im = Image.open(SRC / src).convert("RGB")
        for w in WIDTHS:
            h = round(im.height * w / im.width)
            im.resize((w, h), Image.LANCZOS).save(OUT / f"{name}-{w}.webp", "WEBP", quality=78, method=6)
        # Open Graph / fallback JPEG
        if name == "hero":
            im.resize((960, round(im.height * 960 / im.width)), Image.LANCZOS).save(OUT / "og-image.jpg", quality=82)

    logo = Image.open(SRC / "suvacha-logo.png").convert("RGBA")
    logo.resize((420, round(logo.height * 420 / logo.width)), Image.LANCZOS).save(OUT / "logo.webp", "WEBP", quality=90)
    logo.resize((420, round(logo.height * 420 / logo.width)), Image.LANCZOS).save(OUT / "logo.png", optimize=True)
    fav = Image.open(SRC / "cropped-Favicon-1.png").convert("RGBA")
    for s in (32, 180, 512):
        fav.resize((s, s), Image.LANCZOS).save(OUT / f"favicon-{s}.png", optimize=True)

    before = sum((SRC / s).stat().st_size for s in IMAGES.values())
    after = sum(p.stat().st_size for p in OUT.glob("*-960.webp"))
    print(f"{len(IMAGES)} images: originals {before/1e6:.1f} MB -> 960w webp {after/1e6:.1f} MB")


if __name__ == "__main__":
    main()
