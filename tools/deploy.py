"""Build the site and deploy site/ to Netlify (suvacha-healthcare).

    python3 tools/deploy.py

Uses the token saved by `npx netlify-cli login`; no secrets live in this repo.
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_ID = "b54f5c13-c7c2-406b-98b6-75200ec44d61"  # suvacha-healthcare.netlify.app


def token():
    cfg = json.loads(Path(os.path.expanduser("~/.config/netlify/config.json")).read_text())
    users = cfg.get("users", {})
    if not users:
        sys.exit("Not logged in to Netlify. Run: npx netlify-cli login")
    return next(iter(users.values()))["auth"]["token"]


def main():
    subprocess.run([sys.executable, str(ROOT / "build.py")], check=True)
    buf = io.BytesIO()
    site = ROOT / "site"
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in site.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(site).as_posix())
    req = urllib.request.Request(
        f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys", data=buf.getvalue(), method="POST",
        headers={"Authorization": "Bearer " + token(), "Content-Type": "application/zip"})
    try:
        dep = json.loads(urllib.request.urlopen(req, timeout=300).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Deploy failed: {e.code} {e.read().decode()[:300]}")
    # Netlify processes the upload before it goes live; wait so callers can check the site right away.
    for _ in range(60):
        if dep["state"] in ("ready", "error"):
            break
        time.sleep(3)
        req = urllib.request.Request(f"https://api.netlify.com/api/v1/deploys/{dep['id']}", headers={"Authorization": "Bearer " + token()})
        dep = json.loads(urllib.request.urlopen(req, timeout=60).read())
    if dep["state"] != "ready":
        sys.exit(f"Deploy {dep['id']} ended as {dep['state']}: {dep.get('error_message') or ''}")
    print(f"Deployed {dep['id']} (live) -> {dep.get('ssl_url') or dep.get('url')}")


if __name__ == "__main__":
    main()
