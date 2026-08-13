"""
cli.py
------
Command-line interface for the Web Content Analyzer.

Usage:
    python cli.py https://example.com
    python cli.py https://example.com --format html --output report.html
    python cli.py https://example.com --format json --output report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from analyzer import analyze_url, FetchError, AnalysisReport

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Content Report - {title}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 16px; color: #222; }}
  h1 {{ font-size: 22px; }}
  h2 {{ font-size: 16px; margin-top: 28px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
  .meta {{ color: #666; font-size: 13px; }}
  ul {{ padding-left: 20px; }}
  .keyword {{ display: inline-block; background: #eef2ff; color: #33449b; padding: 3px 8px; margin: 2px; border-radius: 10px; font-size: 13px; }}
  a {{ color: #4f8cff; text-decoration: none; word-break: break-all; }}
</style>
</head>
<body>
  <h1>{title}</h1>
  <p class="meta">{url}</p>
  <p>{description}</p>

  <h2>Stats</h2>
  <ul>
    <li>Word count: {word_count}</li>
    <li>Estimated reading time: {reading_time} min</li>
    <li>Internal links: {n_internal}</li>
    <li>External links: {n_external}</li>
  </ul>

  <h2>Top Keywords</h2>
  <div>{keywords_html}</div>

  <h2>Headings</h2>
  {headings_html}

  <h2>Internal Links ({n_internal})</h2>
  <ul>{internal_html}</ul>

  <h2>External Links ({n_external})</h2>
  <ul>{external_html}</ul>
</body>
</html>
"""


def render_html(report: AnalysisReport) -> str:
    keywords_html = "".join(
        f'<span class="keyword">{kw["word"]} ({kw["count"]})</span>' for kw in report.top_keywords
    ) or "<em>None found</em>"

    headings_html = ""
    for level, items in report.headings.items():
        headings_html += f"<h3>{level.upper()}</h3><ul>" + "".join(f"<li>{h}</li>" for h in items) + "</ul>"
    if not headings_html:
        headings_html = "<em>No headings found</em>"

    internal_html = "".join(f'<li><a href="{l}">{l}</a></li>' for l in report.links_internal) or "<li><em>None</em></li>"
    external_html = "".join(f'<li><a href="{l}">{l}</a></li>' for l in report.links_external) or "<li><em>None</em></li>"

    return HTML_TEMPLATE.format(
        title=report.title or "Untitled page",
        url=report.url or "",
        description=report.meta_description or "<em>No meta description found.</em>",
        word_count=report.word_count,
        reading_time=report.estimated_reading_time_minutes,
        n_internal=len(report.links_internal),
        n_external=len(report.links_external),
        keywords_html=keywords_html,
        headings_html=headings_html,
        internal_html=internal_html,
        external_html=external_html,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a webpage's content, structure, and links.")
    parser.add_argument("url", help="URL of the page to analyze")
    parser.add_argument("--format", choices=["json", "html"], default="json", help="Report output format")
    parser.add_argument("--output", "-o", help="File path to write the report to (defaults to stdout)")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    args = parser.parse_args()

    try:
        report = analyze_url(args.url, timeout=args.timeout)
    except FetchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        output = json.dumps(report.to_dict(), indent=2)
    else:
        output = render_html(report)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
