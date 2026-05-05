import asyncio
from http import HTTPStatus
from urllib.parse import unquote

from app.main import app as fastapi_app


class ASGIToWSGI:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        body = environ["wsgi.input"].read()
        if method == "HEAD":
            body = b""

        headers = []
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                header_name = key[5:].replace("_", "-").lower().encode("latin-1")
                headers.append((header_name, str(value).encode("latin-1")))
        if environ.get("CONTENT_TYPE"):
            headers.append((b"content-type", str(environ["CONTENT_TYPE"]).encode("latin-1")))
        if environ.get("CONTENT_LENGTH"):
            headers.append((b"content-length", str(environ["CONTENT_LENGTH"]).encode("latin-1")))

        response_state = {"status": "500 Internal Server Error", "headers": []}
        response_body: list[bytes] = []
        request_consumed = False

        async def receive():
            nonlocal request_consumed
            if request_consumed:
                return {"type": "http.disconnect"}
            request_consumed = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                phrase = HTTPStatus(status_code).phrase if status_code in HTTPStatus._value2member_map_ else "OK"
                response_state["status"] = f"{status_code} {phrase}"
                response_state["headers"] = [
                    (name.decode("latin-1"), value.decode("latin-1"))
                    for name, value in message.get("headers", [])
                ]
            elif message["type"] == "http.response.body":
                chunk = message.get("body", b"")
                if chunk:
                    response_body.append(chunk)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": environ.get("SERVER_PROTOCOL", "HTTP/1.1").replace("HTTP/", ""),
            "method": method,
            "scheme": environ.get("wsgi.url_scheme", "http"),
            "path": unquote(environ.get("PATH_INFO", "") or "/"),
            "raw_path": (environ.get("PATH_INFO", "") or "/").encode("utf-8"),
            "query_string": environ.get("QUERY_STRING", "").encode("latin-1"),
            "root_path": environ.get("SCRIPT_NAME", ""),
            "headers": headers,
            "client": (environ.get("REMOTE_ADDR", "127.0.0.1"), 0),
            "server": (environ.get("SERVER_NAME", "localhost"), int(environ.get("SERVER_PORT", 80))),
        }

        asyncio.run(self.app(scope, receive, send))
        start_response(response_state["status"], response_state["headers"])
        return [b"".join(response_body)]


application = ASGIToWSGI(fastapi_app)
