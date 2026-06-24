from dataclasses import dataclass
import http.server
import socketserver
from typing import override

PORT = 8003



class FlowerCylinder:
    _position_mm: int

    def __init__(self) -> None:
        self._position_mm = 0


class CustomHandler(http.server.SimpleHTTPRequestHandler):


    @override
    def do_GET(self) -> None:

        print(self.path)

        self.send_response(301)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        _ = self.wfile.write("reply text".encode())



# TODO: register routes
def fake_controller() -> None:

    httpd = socketserver.TCPServer(("", PORT), CustomHandler)
    httpd.allow_reuse_port = True
    httpd.allow_reuse_address = True
    print(f"webserver running at port {PORT}")
    httpd.serve_forever()


