from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse, parse_qs


class MockAPIHandler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlparse(self.path).path != "/api/ngl":
            self.send_json(404, {"error": "Route tidak ditemukan"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 16384:
                self.send_json(413, {"error": "Request terlalu besar"})
                return

            raw = self.rfile.read(length)
            content_type = self.headers.get("Content-Type", "")
            if "application/json" in content_type:
                data = json.loads(raw.decode("utf-8"))
            else:
                data = parse_qs(raw.decode("utf-8"))
                data = {k: v[0] for k, v in data.items()}

            if not isinstance(data, dict):
                self.send_json(400, {"error": "Body harus berupa objek JSON"})
                return

            username = str(data.get("usr", "")).strip()
            message = str(data.get("text", "")).strip()

            if not username or not message:
                self.send_json(
                    400,
                    {"error": "Parameter usr dan text wajib diisi"}
                )
                return

            self.send_json(200, {
                "ok": True,
                "message": "Mock API berhasil menerima request",
                "received": {
                    "usr": username,
                    "text_length": len(message)
                }
            })

        except (ValueError, UnicodeDecodeError):
            self.send_json(400, {"error": "Format request tidak valid"})

    def log_message(self, fmt, *args):
        print("[Mock API]", fmt % args)


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8765), MockAPIHandler)
    print("Mock API berjalan di http://127.0.0.1:8765")
    print("Tekan Ctrl+C untuk berhenti.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMock API dihentikan.")
        server.server_close()
