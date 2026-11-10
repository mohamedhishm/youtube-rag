"""Open this file in IDLE and press F5.
Starts the backend (port 8000) and the frontend (port 5500), then opens the browser.
To stop: close the IDLE shell window, or use Shell > Restart Shell (Ctrl+F6)."""
import http.server
import os
import socketserver
import sys
import threading
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)


def serve_frontend():
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(
        *a, directory=os.path.join(HERE, "frontend"), **k
    )
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", 5500), handler) as httpd:
        httpd.serve_forever()


threading.Thread(target=serve_frontend, daemon=True).start()
threading.Timer(3, lambda: webbrowser.open("http://localhost:5500")).start()
print("Frontend: http://localhost:5500")
print("Backend:  http://localhost:8000/docs")

import uvicorn  # noqa: E402

uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
