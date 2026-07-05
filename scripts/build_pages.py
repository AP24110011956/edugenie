"""Build the static GitHub Pages artifact from the canonical Jinja template."""

from __future__ import annotations

import os
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
TEMPLATE = ROOT / "app" / "templates" / "index.html"


def main() -> None:
    api_base = os.environ.get("API_BASE_URL", "").strip().rstrip("/")
    if not api_base.startswith("https://"):
        raise SystemExit("API_BASE_URL must be a public https:// Cloud Run URL")

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace(
        "{{ url_for('static', path='/style.css') }}", "./static/style.css"
    ).replace("{{ url_for('static', path='/app.js') }}", "./static/app.js")
    html = html.replace(
        '<meta name="edugenie-api-base" content="" />',
        f'<meta name="edugenie-api-base" content="{api_base}" />',
    )
    html = html.replace('href="/docs"', f'href="{api_base}/docs"')

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    (OUTPUT / "static").mkdir(parents=True)
    (OUTPUT / "index.html").write_text(html, encoding="utf-8")
    shutil.copy2(ROOT / "app" / "static" / "style.css", OUTPUT / "static")
    shutil.copy2(ROOT / "app" / "static" / "app.js", OUTPUT / "static")
    (OUTPUT / ".nojekyll").touch()
    print(f"Built GitHub Pages artifact for {api_base}")


if __name__ == "__main__":
    main()

