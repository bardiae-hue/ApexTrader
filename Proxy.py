#!/usr/bin/env python3
"""
Apex Trader — Proxy
Run: python proxy.py
Then open trader.html

Routes:
  /yahoo/*   -> Yahoo Finance (chart endpoint, with cookie handling)
  /alpaca/*  -> Alpaca paper trading
  /live/*    -> Alpaca live trading
  /data/*    -> Alpaca market data (free, just needs API key)
  /ollama/*  -> Ollama local AI (port 11434)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, json, time

PORT = 8765

ROUTES = {
    "/yahoo/":  "https://query1.finance.yahoo.com",
    "/alpaca/": "https://paper-api.alpaca.markets",
    "/live/":   "https://api.alpaca.markets",
    "/data/":   "https://data.alpaca.markets",
    "/ollama/": "http://localhost:11434",
}

# Cache Yahoo cookies so we don't re-fetch every time
_yf_cookies = {}
_yf_cookie_ts = 0

def get_yf_cookies():
    global _yf_cookies, _yf_cookie_ts
    if time.time() - _yf_cookie_ts < 3600:
        return _yf_cookies
    try:
        req = urllib.request.Request(
            "https://finance.yahoo.com/",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.headers.get("Set-Cookie", "")
            cookies = {}
            for part in raw.split(","):
                kv = part.strip().split(";")[0]
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    cookies[k.strip()] = v.strip()
            _yf_cookies   = cookies
            _yf_cookie_ts = time.time()
    except:
        pass
    return _yf_cookies


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        status = args[1] if len(args) > 1 else "?"
        path   = args[0] if args else "?"
        print(f"  [{status}]  {path}")

    def _proxy(self, method):
        path   = self.path
        target = None
        is_yahoo = False

        for prefix, base in ROUTES.items():
            if path.startswith(prefix):
                rest   = path[len(prefix):]
                target = base.rstrip("/") + "/" + rest.lstrip("/")
                is_yahoo = prefix == "/yahoo/"
                break

        if not target:
            self._respond(404, b'{"error":"no route"}')
            return

        body = None
        if method in ("POST", "PUT", "PATCH"):
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length) if length else None

        req = urllib.request.Request(target, data=body, method=method)
        req.add_header("User-Agent",   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36")
        req.add_header("Accept",       "application/json, */*")
        req.add_header("Content-Type", self.headers.get("Content-Type", "application/json"))

        if is_yahoo:
            req.add_header("Referer", "https://finance.yahoo.com/")
            cookies = get_yf_cookies()
            if cookies:
                req.add_header("Cookie", "; ".join(f"{k}={v}" for k, v in cookies.items()))

        for h in ("APCA-API-KEY-ID", "APCA-API-SECRET-KEY", "Authorization", "x-api-key"):
            v = self.headers.get(h)
            if v: req.add_header(h, v)

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                self._respond(resp.status, data)
        except urllib.error.HTTPError as e:
            self._respond(e.code, e.read())
        except Exception as e:
            self._respond(502, json.dumps({"error": str(e)}).encode())

    def _respond(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type",                "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length",              str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,PUT,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization,x-api-key,APCA-API-KEY-ID,APCA-API-SECRET-KEY")
        self.end_headers()

    def do_GET(self):    self._proxy("GET")
    def do_POST(self):   self._proxy("POST")
    def do_DELETE(self): self._proxy("DELETE")
    def do_PUT(self):    self._proxy("PUT")


if __name__ == "__main__":
    print("""
  ┌──────────────────────────────────────┐
  │  Apex Trader Proxy  →  port 8765     │
  │  Open trader.html in your browser    │
  │  Ctrl+C to stop                      │
  └──────────────────────────────────────┘
""")
    HTTPServer(("localhost", PORT), ProxyHandler).serve_forever()