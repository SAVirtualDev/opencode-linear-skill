#!/usr/bin/env python3
"""One-shot Linear OAuth PKCE flow to obtain an access token.

Usage:
    python3 setup-oauth.py <CLIENT_ID> <CLIENT_SECRET>

Saves the token to ~/.config/opencode/.env.linear
"""

import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

REDIRECT_URI = "http://localhost:8888/callback"
AUTHORIZE_URL = "https://linear.app/oauth/authorize"
TOKEN_URL = "https://api.linear.app/oauth/token"
SCOPES = "read,write,issues:create"


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 setup-oauth.py <CLIENT_ID> <CLIENT_SECRET>")
        sys.exit(1)

    client_id = sys.argv[1]
    client_secret = sys.argv[2]

    # PKCE
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    auth_code = None

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            if "code" in params:
                auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Success!</h1><p>You can close this tab.</p>")
            else:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                error = params.get("error", ["unknown"])[0]
                self.wfile.write(f"<h1>Error: {error}</h1>".encode())

            threading.Thread(target=self.server.shutdown).start()

        def log_message(self, format, *args):
            pass

    # Start local server
    server = http.server.HTTPServer(("localhost", 8888), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    # Build authorization URL
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "consent",
    })
    auth_url = f"{AUTHORIZE_URL}?{params}"

    print(f"\nOpening browser for Linear authorization...")
    print(f"If it doesn't open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    # Wait for callback
    server_thread.join(timeout=120)

    if not auth_code:
        print("ERROR: No authorization code received. Timed out or denied.")
        sys.exit(1)

    # Exchange code for token
    token_data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "code": auth_code,
        "code_verifier": code_verifier,
    }).encode()

    req = urllib.request.Request(
        TOKEN_URL,
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"ERROR exchanging token: {e.code} {body}")
        sys.exit(1)

    access_token = result["access_token"]

    # Save token
    config_dir = os.path.expanduser("~/.config/opencode")
    os.makedirs(config_dir, exist_ok=True)
    env_path = os.path.join(config_dir, ".env.linear")
    with open(env_path, "w") as f:
        f.write(f"LINEAR_API_KEY={access_token}\n")
    os.chmod(env_path, 0o600)

    print(f"\n✓ Token saved to: {env_path}")
    print(f"  Token preview: {access_token[:12]}...{access_token[-4:]}")
    print(f"\nNext steps:")
    print(f"  1. Add the token to your opencode.json MCP config (see README.md)")
    print(f"  2. Restart OpenCode")


if __name__ == "__main__":
    main()
