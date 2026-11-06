import os

from app import create_app

os.environ.setdefault("APP_ALLOW_HTTP", "1")
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
