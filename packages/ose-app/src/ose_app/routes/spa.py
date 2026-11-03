import json
from pathlib import Path

from flask import Blueprint, Response, abort, current_app

bp = Blueprint("spa", __name__)

INDEX_FILE = Path(__file__).parent.parent / "static" / "app" / "index.html"
HEAD_PLACEHOLDER = "<!--ose-head-->"


def _head(prefix: str) -> str:
    app_dir = f"{prefix}/static/app"
    # Escape "</" so the JSON can never close the script tag
    config = json.dumps({"prefix": prefix}).replace("</", "<\\/")
    importmap = json.dumps({"imports": {
        "vue": f"{app_dir}/vue-shim.js",
        "@ontospreaded/js-core": f"{app_dir}/ose-js-core-shim.js",
    }}).replace("</", "<\\/")
    return (f'<script>window.OSE_CONFIG = {config}</script>\n'
            f'<script type="importmap">{importmap}</script>')


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def spa(path: str):
    """Serves the single page app. Routing is done client side; auth is handled through /api/me and 401s."""
    if path == "api" or path.startswith(("api/", "static/")):
        abort(404)

    if not INDEX_FILE.exists():
        return Response("The frontend has not been built. Run `npm run build`.", status=500, mimetype="text/plain")

    prefix = current_app.config.get("URL_PREFIX", "")
    html = INDEX_FILE.read_text(encoding="utf-8").replace(HEAD_PLACEHOLDER, _head(prefix), 1)
    # Vite writes relative asset URLs ("./assets/..."); make them absolute without a <base> tag
    html = html.replace('="./', f'="{prefix}/static/app/')
    return Response(html, mimetype="text/html")
