"""
Unit tests for analyzer.py.

These tests run entirely offline: they load a local HTML fixture instead of
hitting the network, and mock requests.get for the one test that exercises
fetch_html(). Run with:  pytest -v
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import analyzer

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.html"
BASE_URL = "https://example.com/sample"


@pytest.fixture
def sample_html() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_analyze_html_extracts_metadata(sample_html):
    report = analyzer.analyze_html(sample_html, url=BASE_URL)

    assert report.title == "Sample Page for Testing"
    assert "sample page" in report.meta_description.lower()
    assert report.language == "en"
    assert report.open_graph["title"] == "Sample OG Title"


def test_analyze_html_extracts_headings(sample_html):
    report = analyzer.analyze_html(sample_html, url=BASE_URL)

    assert report.headings["h1"] == ["Welcome to the Sample Page"]
    assert "Section One" in report.headings["h2"]
    assert "Subsection" in report.headings["h3"]


def test_analyze_html_splits_internal_and_external_links(sample_html):
    report = analyzer.analyze_html(sample_html, url=BASE_URL)

    assert any("internal-page" in link for link in report.links_internal)
    assert any("external-site.com" in link for link in report.links_external)
    # anchors and mailto links must be excluded entirely
    all_links = report.links_internal + report.links_external
    assert not any(link.startswith("#") for link in all_links)
    assert not any(link.startswith("mailto:") for link in all_links)


def test_analyze_html_word_count_and_keywords(sample_html):
    report = analyzer.analyze_html(sample_html, url=BASE_URL)

    assert report.word_count > 0
    assert report.estimated_reading_time_minutes >= 0
    # "testing" appears multiple times and should rank as a top keyword
    top_words = [kw["word"] for kw in report.top_keywords]
    assert "testing" in top_words


def test_analyze_html_handles_missing_metadata_gracefully():
    minimal_html = "<html><body><p>No metadata here.</p></body></html>"
    report = analyzer.analyze_html(minimal_html, url=BASE_URL)

    assert report.title is None
    assert report.meta_description is None
    assert report.open_graph == {}
    assert report.headings == {}


@patch("analyzer.requests.get")
def test_fetch_html_returns_text_on_success(mock_get, sample_html):
    mock_response = MagicMock()
    mock_response.text = sample_html
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    html = analyzer.fetch_html(BASE_URL)

    assert html == sample_html
    mock_get.assert_called_once()


@patch("analyzer.requests.get")
def test_fetch_html_raises_fetch_error_on_network_failure(mock_get):
    mock_get.side_effect = analyzer.requests.RequestException("connection refused")

    with pytest.raises(analyzer.FetchError):
        analyzer.fetch_html(BASE_URL)


@patch("analyzer.fetch_html")
def test_analyze_url_combines_fetch_and_analyze(mock_fetch_html, sample_html):
    mock_fetch_html.return_value = sample_html

    report = analyzer.analyze_url(BASE_URL)

    assert report.title == "Sample Page for Testing"
    mock_fetch_html.assert_called_once_with(BASE_URL, timeout=analyzer.DEFAULT_TIMEOUT)
