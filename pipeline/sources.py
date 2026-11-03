"""Download sources with conditional GET and record where every file came from.

Each download is logged in data/raw/sources.json with the URL, the time, ETag or
Last-Modified, size and sha256. The methodology page and the "Izvori" page read
that log, so every number in the product can be traced to a dated request.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from . import config

UA = {"User-Agent": "fiskalna-karta-jls/0.1 (Datathon Portala otvorenih podataka 2026)"}


def _log():
    if config.SOURCES_LOG.exists():
        return json.loads(config.SOURCES_LOG.read_text(encoding="utf-8"))
    return {}


def _save_log(log):
    config.SOURCES_LOG.parent.mkdir(parents=True, exist_ok=True)
    config.SOURCES_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(key, url, dest, *, timeout=600, retries=3, meta=None):
    """Download url to dest unless the server says it has not changed.

    Returns the path. key names the source in the provenance log."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    log = _log()
    prev = log.get(key, {})
    headers = dict(UA)
    if dest.exists() and prev.get("url") == url:
        if prev.get("etag"):
            headers["If-None-Match"] = prev["etag"]
        if prev.get("last_modified"):
            headers["If-Modified-Since"] = prev["last_modified"]
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=timeout, stream=True)
            break
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if r.status_code == 304:
        prev["checked"] = now
        log[key] = prev
        _save_log(log)
        print(f"  {key}: unchanged (304)")
        return dest
    r.raise_for_status()
    tmp = dest.with_suffix(dest.suffix + ".part")
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(1 << 20):
            f.write(chunk)
    tmp.replace(dest)
    log[key] = {
        "url": url,
        "file": str(dest.relative_to(config.ROOT)).replace("\\", "/"),
        "retrieved": now,
        "checked": now,
        "etag": r.headers.get("ETag"),
        "last_modified": r.headers.get("Last-Modified"),
        "bytes": dest.stat().st_size,
        "sha256": _sha256(dest),
        **(meta or {}),
    }
    _save_log(log)
    print(f"  {key}: downloaded {dest.stat().st_size:,} B")
    return dest


def ckan(action, **params):
    """Call a CKAN API v3 action on data.gov.hr and return its result."""
    r = requests.get(config.CKAN + action, params=params, headers=UA, timeout=120)
    r.raise_for_status()
    body = r.json()
    if not body.get("success"):
        raise RuntimeError(f"CKAN {action} failed: {body.get('error')}")
    return body["result"]


def ckan_resource(key, package_id, pick, dest):
    """Find a resource in a CKAN package (pick(resource) -> bool) and download it.

    The package's metadata_modified is stored with the file, so the "Izvori" page
    can show what the portal reported at download time."""
    pkg = ckan("package_show", id=package_id)
    res = [r for r in pkg["resources"] if pick(r)]
    if not res:
        raise RuntimeError(f"no matching resource in CKAN package {package_id}")
    r = res[0]
    meta = {
        "ckan_package": package_id,
        "ckan_resource": r["id"],
        "ckan_metadata_modified": pkg.get("metadata_modified"),
        "publisher": (pkg.get("organization") or {}).get("title"),
        "license": pkg.get("license_title") or pkg.get("license_id"),
    }
    return fetch(key, r["url"], dest, meta=meta)
