import http.server
import socketserver
from typing import override

PORT = 8000


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    @override
    def do_GET(self) -> None:

        print(self.path)

        super().do_GET()


def fake_controller() -> None:
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"Serving at port {PORT}, ready to handle POST requests")
        httpd.serve_forever()
