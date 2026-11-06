"""Fetching the portal catalogue (pipeline/openness.fetch_packages), without network.

On 6.11.2026 at 1 h package_search answered with count 0 and the CI build stopped. A wrong
answer is now retried, and if it persists the pages of the previous build are used.
"""
import json

import pytest

from pipeline import config, openness, sources


class FakeResponse:
    def __init__(self, body, status=200):
        self.status_code = status
        self.headers = {}
        self._data = json.dumps(body).encode()

    def raise_for_status(self):
        if self.status_code >= 400:
            raise sources.requests.HTTPError(f"HTTP {self.status_code}")

    def iter_content(self, n):
        yield self._data


def answer(count, start=0, page=2):
    """A package_search body with `count` datasets in total, the page from `start`."""
    names = [f"skup-{i:03d}" for i in range(start, min(start + page, count))]
    return {"success": True, "result": {"count": count, "results": [{"name": n} for n in names]}}


@pytest.fixture
def portal(tmp_path, monkeypatch):
    """Point data/raw at tmp_path, use pages of 2 and replay the given answers in order."""
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "RAW", tmp_path / "raw")
    monkeypatch.setattr(config, "SOURCES_LOG", tmp_path / "raw" / "sources.json")
    monkeypatch.setattr(openness, "PAGE", 2)
    monkeypatch.setattr(openness.time, "sleep", lambda s: None)
    queue = []

    def get(url, **kw):
        start = int(url.split("start=")[1].split("&")[0])
        item = queue.pop(0)
        return item(start) if callable(item) else item

    monkeypatch.setattr(sources.requests, "get", get)
    return queue


def good(count):
    return lambda start: FakeResponse(answer(count, start))


def names(pages):
    return [p["name"] for p in pages]


def test_good_answer_pages_through_everything(portal):
    portal += [good(5)] * 3
    assert names(openness.fetch_packages()) == [f"skup-{i:03d}" for i in range(5)]
    assert sorted(sources.log_entries("ckan_package_search_")) == [
        "ckan_package_search_00000", "ckan_package_search_00002", "ckan_package_search_00004"]


def test_empty_answer_is_retried(portal):
    portal += [FakeResponse(answer(0)), FakeResponse({"success": False}, 502)] + [good(3)] * 2
    assert len(openness.fetch_packages(tries=3)) == 3
    assert not portal


def test_persistent_empty_answer_keeps_previous_pages_and_log(portal):
    portal += [good(5)] * 3
    openness.fetch_packages()
    before_files = {p.name: p.read_bytes() for p in (config.RAW / "ckan").iterdir()}
    before_log = sources.log_entries("ckan_package_search_")

    portal += [FakeResponse(answer(0))] * 4
    pages = openness.fetch_packages(tries=4)
    assert names(pages) == [f"skup-{i:03d}" for i in range(5)]
    assert {p.name: p.read_bytes() for p in (config.RAW / "ckan").iterdir()} == before_files
    assert sources.log_entries("ckan_package_search_") == before_log


def test_half_built_index_counts_as_wrong(portal):
    portal += [good(10)] * 5
    openness.fetch_packages()
    # 4 of 10 datasets: below MIN_SHARE, so the saved 10 stay
    portal += [good(4)] * 2
    assert len(openness.fetch_packages(tries=2)) == 10


def test_no_saved_copy_fails_loudly(portal):
    portal += [FakeResponse(answer(0))] * 2
    with pytest.raises(RuntimeError, match="spremljene kopije nema"):
        openness.fetch_packages(tries=2)


def test_offline_uses_saved_pages_without_network(portal):
    portal += [good(3)] * 2
    openness.fetch_packages()
    assert len(openness.fetch_packages(offline=True)) == 3
    assert not portal
