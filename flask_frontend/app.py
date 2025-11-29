from pathlib import Path
import requests
from flask import request, Response
from flask import Flask, render_template, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = (BASE_DIR / "dist").resolve()
ASSETS_DIR = DIST_DIR / "assets"


def create_app() -> Flask:
    """
    Khởi tạo Flask app để serve UI React đã build sẵn
    mà KHÔNG thay đổi code/logic trong folder frontend.
    """
    app = Flask(
        __name__,
        static_folder=str(ASSETS_DIR),
        template_folder=str(DIST_DIR),
    )

    @app.route("/")
    def index():
        """
        Trả về trang HTML chính của frontend (build từ Vite).
        """
        return render_template("index.html")

    @app.route("/assets/<path:filename>")
    def assets(filename: str):
        return send_from_directory(app.static_folder, filename)

    @app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
    def proxy_api(path):
        backend_url = f'http://127.0.0.1:8000/api/{path}'
        try:
            resp = requests.request(
                method=request.method,
                url=backend_url,
                headers={key: value for key, value in request.headers if key != 'Host'},
                params=request.args,
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                timeout=30,
            )
            excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
            headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
            response = Response(resp.content, resp.status_code, headers)
            return response
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}, 502

    @app.route("/<path:path>", methods=["GET"])
    def catch_all(path):
        """
        Catch-all route để hỗ trợ SPA routing (React Router).
        Nếu không khớp với các route API hoặc static file ở trên,
        trả về index.html để frontend tự xử lý routing.
        """
        return render_template("index.html")

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


