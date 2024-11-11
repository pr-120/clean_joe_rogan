import base64
import json
import secrets
import string
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests

from Programming_Dictionary.projects.clean_joe_rogan.app_state.perm_state import client_id, fail_redirect_uri, \
    succ_redirect_uri


def generate_url_safe_random_string(length=12):
    # Use only URL-safe characters: letters, digits, -, and _
    characters = string.ascii_letters + string.digits + "-_"
    secure_string = ''.join(secrets.choice(characters) for _ in range(length))
    return secure_string


class SpotifyAuthHandler(BaseHTTPRequestHandler):

    def get_bearer_token(self, authorization_code: str):
        token_uri = "https://accounts.spotify.com/api/token"

        client_id = "0aeb145b6b6b4d1ca6532c5d7029fee5"
        client_secret = "5f42a5e199c143e3876a2bf12b348b6c"

        # Concatenate client ID and secret, encode, and then Base64 encode it
        credentials = f"{client_id}:{client_secret}".encode("utf-8")
        base64_credentials = base64.b64encode(credentials).decode("utf-8")

        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + base64_credentials
        }
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": "http://localhost:8888/callback"
        }
        response = requests.post(token_uri, headers=headers, data=data)

        token = json.loads(response.content.decode("utf-8"))["access_token"]
        return token

    def do_GET(self):
        # Parse the query parameters from the redirected URL
        query_components = parse_qs(urlparse(self.path).query)
        auth_code = query_components.get("code")

        if auth_code:
            print("Authorization code received:", auth_code[0])
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization successful. You can close this window.</h1></body></html>")
            bearer_token = self.get_bearer_token(auth_code[0])
        else:
            print("Authorization failed or denied.")
            self.send_response(400)
            webbrowser.open(fail_redirect_uri)


def authenticate():
    """ authenticate to the spotify API"""

    authentication_url = "https://accounts.spotify.com/authorize?"
    state = generate_url_safe_random_string(16)

    response = requests.get(url=authentication_url,
                            params={
                                "response_type": "code",
                                "client_id": client_id,
                                "scope": "user-read-private user-read-email",
                                "state": state,
                                "redirect_uri": succ_redirect_uri,
                                "show_dialog": "true"
                            })

    response.raise_for_status()

    # open authorization dialog
    webbrowser.open(response.url)

    # start local server to catch redirect
    server_address = ("", 8888)
    httpd = HTTPServer(server_address, SpotifyAuthHandler)
    httpd.serve_forever()
