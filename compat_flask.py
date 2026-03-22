from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

_CURRENT_REQUEST: "Request | None" = None


class Request:
    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        query: str = "",
        body: bytes = b"",
        headers: dict[str, str] | None = None,
    ):
        self.method = method.upper()
        self.path = path
        self.query_string = query
        self.args = {
            key: values[0] if len(values) == 1 else values
            for key, values in parse_qs(query).items()
        }
        self._body = body
        self.headers = headers or {}

    def get_json(self, silent: bool = False) -> Any:
        if not self._body:
            return None
        try:
            return json.loads(self._body.decode("utf-8"))
        except Exception:
            if silent:
                return None
            raise


class RequestProxy:
    def __getattr__(self, item: str) -> Any:
        if _CURRENT_REQUEST is None:
            raise RuntimeError("Request context is not active.")
        return getattr(_CURRENT_REQUEST, item)


request = RequestProxy()


class Response:
    def __init__(
        self,
        data: bytes | str,
        status_code: int = 200,
        mimetype: str = "text/plain; charset=utf-8",
    ):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.data = data
        self.status_code = status_code
        self.mimetype = mimetype
        self.headers: list[tuple[str, str]] = [
            ("Content-Type", mimetype),
            ("Content-Length", str(len(data))),
        ]

    @property
    def json(self) -> Any:
        return json.loads(self.data.decode("utf-8"))


@dataclass
class _Route:
    path: str
    methods: set[str]
    func: Callable[..., Any]


class Flask:
    def __init__(self, import_name: str, static_folder: str | None = None):
        self.import_name = import_name
        self.static_folder = static_folder
        self._routes: list[_Route] = []
        self.debug = False

    def route(
        self, path: str, methods: list[str] | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        route_methods = set(methods or ["GET"])

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._routes.append(
                _Route(path=path, methods={m.upper() for m in route_methods}, func=func)
            )
            return func

        return decorator

    def get(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(path, methods=["GET"])

    def post(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(path, methods=["POST"])

    def _find_route(self, path: str, method: str) -> _Route | None:
        for route in self._routes:
            if route.path == path and method in route.methods:
                return route
        return None

    def _dispatch(self, request_obj: Request) -> Response:
        global _CURRENT_REQUEST
        route = self._find_route(request_obj.path, request_obj.method)
        if route is None:
            return Response("Not Found", 404)
        _CURRENT_REQUEST = request_obj
        try:
            result = route.func()
        finally:
            _CURRENT_REQUEST = None

        if isinstance(result, Response):
            return result
        if isinstance(result, tuple):
            payload, status = result
            if isinstance(payload, Response):
                payload.status_code = status
                return payload
            if isinstance(payload, (dict, list)):
                return jsonify(payload, status=status)
            return Response(str(payload), status)
        if isinstance(result, (dict, list)):
            return jsonify(result)
        return Response(result)

    def __call__(
        self, environ: dict[str, Any], start_response: Callable[..., Any]
    ) -> list[bytes]:
        body = environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH") or 0))
        request_obj = Request(
            method=environ.get("REQUEST_METHOD", "GET"),
            path=environ.get("PATH_INFO", "/"),
            query=environ.get("QUERY_STRING", ""),
            body=body,
            headers={
                key: value for key, value in environ.items() if key.startswith("HTTP_")
            },
        )
        response = self._dispatch(request_obj)
        start_response(f"{response.status_code} OK", response.headers)
        return [response.data]

    def run(
        self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False
    ) -> None:
        self.debug = debug
        with make_server(host, port, self) as server:
            print(f" * Running on http://{host}:{port}")
            server.serve_forever()

    def test_client(self) -> "TestClient":
        return TestClient(self)


class TestClient:
    def __init__(self, app: Flask):
        self.app = app

    def get(self, path: str) -> Response:
        route, _, query = path.partition("?")
        return self.app._dispatch(Request(method="GET", path=route, query=query))

    def post(self, path: str, json: Any | None = None) -> Response:
        body = b"" if json is None else __import__("json").dumps(json).encode("utf-8")
        return self.app._dispatch(
            Request(
                method="POST",
                path=path,
                body=body,
                headers={"CONTENT_TYPE": "application/json"},
            )
        )


def jsonify(payload: Any, status: int = 200) -> Response:
    return Response(json.dumps(payload), status, "application/json; charset=utf-8")


def send_from_directory(directory: str | Path, filename: str) -> Response:
    path = Path(directory) / filename
    data = path.read_bytes()
    mimetype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    if mimetype.startswith("text/"):
        mimetype = f"{mimetype}; charset=utf-8"
    return Response(data, 200, mimetype)
