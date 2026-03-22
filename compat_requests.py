from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class Response:
    def __init__(self, url: str, content: bytes, status_code: int):
        self.url = url
        self.content = content
        self.text = content.decode("utf-8", errors="replace")
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code} for {self.url}")


def get(url: str, headers: dict[str, str] | None = None, timeout: int = 10) -> Response:
    req = Request(url, headers=headers or {})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return Response(url, resp.read(), getattr(resp, "status", 200))
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc.reason}") from exc
