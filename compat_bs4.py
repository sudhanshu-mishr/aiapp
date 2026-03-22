from __future__ import annotations


class _Node:
    def __init__(self, html: str = ""):
        self.html = html

    def select(self, selector: str):
        return []

    def select_one(self, selector: str):
        return None

    def get_text(self, separator: str = " ", strip: bool = False):
        return ""

    def get(self, key: str, default=None):
        return default


class BeautifulSoup(_Node):
    def __init__(self, html: str, parser: str = "html.parser"):
        super().__init__(html)
        self.parser = parser
