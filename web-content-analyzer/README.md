# Web Content Analyzer

A Python tool that fetches a webpage and generates a structured report on its
content, structure, and links — metadata, headings, internal/external links,
word count, reading time, and keyword frequency. Runs from the command line
and outputs either JSON or a styled HTML report.

## Features

- Fetches and parses any public URL with **Requests** + **BeautifulSoup**
- Extracts metadata: title, meta description, `<html lang>`, Open Graph tags
- Builds a heading outline (h1–h6) to sketch page structure
- Splits links into internal vs. external, with de-duplication
- Regex-based keyword frequency analysis (stopwords filtered) and estimated
  reading time
- Two output formats: raw **JSON** (for pipelines/further processing) or a
  clean, styled **HTML** report (for humans)
- Proper error handling for network failures, timeouts, and malformed pages
- Fully unit tested offline using a local HTML fixture — no live network
  needed to run the test suite

## Tech stack

Python · Requests · BeautifulSoup4 · Regex · argparse · Pytest

## Project structure

```
web-content-analyzer/
├── analyzer.py               # Core fetching + parsing + analysis logic
├── cli.py                    # Command-line interface, JSON/HTML rendering
├── tests/
│   ├── test_analyzer.py      # Unit tests (offline, uses local fixture)
│   └── fixtures/
│       └── sample.html       # Sample page used by the test suite
├── requirements.txt
└── README.md
```

## Getting started

```bash
# 1. Clone and enter the project
git clone https://github.com/<your-username>/web-content-analyzer.git
cd web-content-analyzer

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Print a JSON report to the terminal
python cli.py https://example.com

# Save a styled HTML report to a file
python cli.py https://example.com --format html --output report.html

# Save JSON to a file, with a custom timeout
python cli.py https://example.com --format json --output report.json --timeout 15
```

### Example JSON output (trimmed)

```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "meta_description": null,
  "word_count": 97,
  "estimated_reading_time_minutes": 0.5,
  "top_keywords": [
    { "word": "example", "count": 3 },
    { "word": "domain", "count": 2 }
  ],
  "links_internal": ["https://example.com/internal-page"],
  "links_external": ["https://external-site.com/page"]
}
```

## Running tests

```bash
pytest -v
```

Tests run entirely offline: `tests/fixtures/sample.html` stands in for a live
page, and the one test that touches `requests.get` mocks it out.

## How it works

1. `analyzer.fetch_html()` downloads the page HTML (or you can pass HTML you
   already have to `analyzer.analyze_html()` directly).
2. BeautifulSoup parses the DOM once and feeds it to focused extraction
   helpers: `_extract_metadata`, `_extract_headings`, `_extract_links`,
   `_analyze_text`.
3. Everything is assembled into an `AnalysisReport` dataclass, which
   `cli.py` serializes to JSON or renders into an HTML template.

## Possible extensions

- Add sentiment analysis or readability scoring (Flesch-Kincaid)
- Crawl and analyze multiple pages of a site (respecting `robots.txt`)
- Export reports to CSV for spreadsheet analysis
- Add a small Flask UI to run analyses from a browser instead of the CLI

## License

MIT
