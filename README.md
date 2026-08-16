# Web Content Analyzer

A command-line tool that fetches any public webpage and generates a structured report on its content, structure, and links — metadata, heading outline, internal/external links, word count, reading time, and top keywords.

## What it does

- Fetches and parses any public URL (Requests + BeautifulSoup)
- Pulls out metadata: title, meta description, `<html lang>`, Open Graph tags
- Builds a heading outline (h1–h6) to sketch the page's structure
- Splits links into internal vs. external, de-duplicated
- Runs keyword-frequency analysis (stopwords filtered) and estimates reading time
- Outputs either raw JSON (for piping into other tools) or a clean, styled HTML report

## Tech Stack

- **Language:** Python
- **Libraries:** Requests, BeautifulSoup4, argparse
- **Testing:** Pytest — fully offline, using a local HTML fixture (no live network needed to run the test suite)

## How it works

1. `analyzer.fetch_html()` downloads the page (or you can pass HTML you already have straight to `analyzer.analyze_html()`)
2. BeautifulSoup parses the page once, then four focused functions each pull out one thing: metadata, headings, links, and text stats
3. Everything gets packed into an `AnalysisReport` object, which `cli.py` either dumps as JSON or renders into an HTML report

## Getting Started

```bash
git clone https://github.com/Sumith0805/web-content-analyzer.git
cd web-content-analyzer

python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

```bash
# Print a JSON report to the terminal
python cli.py https://example.com

# Save a styled HTML report to a file
python cli.py https://example.com --format html --output report.html
```

## Running tests

```bash
pytest -v
```

## What I'd improve next

- Add readability scoring (Flesch-Kincaid)
- Support crawling multiple pages of a site (respecting robots.txt)
- Add a small web UI so it doesn't have to run from the command line

## Author

**Nalla Sumith** — [LinkedIn](https://www.linkedin.com/in/sumithn) | [GitHub](https://github.com/Sumith0805)
