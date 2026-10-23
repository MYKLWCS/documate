# Test-only OIDC provider that answers like Cloudflare Access with a one-time PIN: the ID token carries email and sub,
# no name. Usage: python3 mock-oidc.py <port> <email-file>  (the email to sign in as is re-read at every login).
import base64, json, sys, time, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9999
BASE = f"http://127.0.0.1:{PORT}"
EMAIL_FILE = sys.argv[2] if len(sys.argv) > 2 else "mock-email"
codes = {}
def b64(d): return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): sys.stderr.write("mock: " + (a[0] % a[1:]) + "\n")
    def send(self, code, body=None, headers=()):
        self.send_response(code)
        for k, v in headers: self.send_header(k, v)
        if body is not None:
            b = json.dumps(body).encode(); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        else:
            self.end_headers()
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = dict(urllib.parse.parse_qsl(u.query))
        if u.path == "/.well-known/openid-configuration":
            return self.send(200, {"issuer": BASE, "authorization_endpoint": BASE + "/authorize",
                                   "token_endpoint": BASE + "/token", "scopes_supported": ["openid", "email", "profile", "groups"]})
        if u.path == "/authorize":
            code = "c" + str(len(codes) + 1); codes[code] = q
            loc = q["redirect_uri"] + "?" + urllib.parse.urlencode({"code": code, "state": q["state"]})
            return self.send(302, headers=[("Location", loc)])
        self.send(404, {"error": "not found"})
    def do_POST(self):
        if self.path != "/token": return self.send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0)); form = dict(urllib.parse.parse_qsl(self.rfile.read(n).decode()))
        if form.get("code") not in codes: return self.send(400, {"error": "invalid_grant"})
        now = int(time.time())
        email = open(EMAIL_FILE).read().strip()
        sub = "sub-" + email.split("@")[0]
        claims = {"iss": BASE, "aud": "test-client", "sub": sub, "email": email,
                  "iat": now, "exp": now + 3600, "nonce": "", "identity_nonce": "x", "country": "US"}
        idt = b64({"alg": "RS256", "kid": "k1", "typ": "JWT"}) + "." + b64(claims) + ".c2ln"
        self.send(200, {"access_token": "at-" + form["code"], "token_type": "Bearer", "expires_in": 3600, "id_token": idt})
HTTPServer(("127.0.0.1", PORT), H).serve_forever()
