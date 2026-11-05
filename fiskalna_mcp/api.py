"""Reads the static API (web/public/api/v1/ or its published copy) with an in-memory cache.

The base is an http(s) URL or a local folder. Every file is fetched once per process; a
missing file gives None, so callers can treat fields and files that an older API lacks as absent.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

PUBLIC_SITE = "https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/"
DEFAULT_API = PUBLIC_SITE + "api/v1/"
DEFAULT_TIMEOUT = 20.0
USER_AGENT = "fiskalna-karta-mcp/1.0 (+https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026)"


class ApiError(Exception):
    """The API could not be read (network, timeout, broken JSON). The message is shown to the user."""


class Api:
    def __init__(self, base: str | Path = DEFAULT_API, timeout: float = DEFAULT_TIMEOUT):
        base = str(base)
        self.remote = base.startswith(("http://", "https://"))
        if self.remote:
            self.base = base if base.endswith("/") else base + "/"
        else:
            self.base = str(Path(base).resolve())
        self.timeout = timeout
        self._cache: dict[str, object] = {}
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        return f"Api({self.base!r})"

    @property
    def site(self) -> str:
        """Public site the links point to. For a local folder it is the published site,
        because the local API is a build of the same pages."""
        if self.remote and "api/v1/" in self.base:
            return self.base.rsplit("api/v1/", 1)[0]
        return PUBLIC_SITE

    @property
    def public_api(self) -> str:
        return self.base if self.remote else DEFAULT_API

    def url(self, path: str) -> str:
        """Public link to an API file (the published API, also when reading a local folder)."""
        return self.public_api + path

    def get(self, path: str):
        """Parsed JSON at `path` (relative to the API root), or None when the file does not exist."""
        with self._lock:
            if path in self._cache:
                return self._cache[path]
        value = self._fetch(path)
        if value is not None:                      # a missing file may still appear (publish in progress)
            with self._lock:
                self._cache[path] = value
        return value

    def text(self, path: str) -> str | None:
        """Raw text of an API file, for resources."""
        v = self.get(path)
        return None if v is None else json.dumps(v, ensure_ascii=False)

    def _fetch(self, path: str):
        if self.remote:
            req = urllib.request.Request(self.base + path, headers={"User-Agent": USER_AGENT,
                                                                    "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    raw = r.read()
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                raise ApiError(f"API je vratio HTTP {e.code} za {path}.") from e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                raise ApiError(f"API nije dostupan ({self.base}{path}): {e}") from e
        else:
            p = Path(self.base) / path
            if not p.is_file():
                return None
            try:
                raw = p.read_bytes()
            except OSError as e:
                raise ApiError(f"Datoteka {p} se ne može pročitati: {e}") from e
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ApiError(f"Datoteka {path} nije ispravan JSON (možda se upravo objavljuje).") from e
