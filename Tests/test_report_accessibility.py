"""Semantic regression checks for generated reports; not a WCAG certification."""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import pytest

from Backtesting.reproducible_backtest import DEFAULT_CONFIG, build_report, write_outputs
from Journal.analyze_journal import SAMPLE_ROW, build_html_report, summarize
from Operations.health import CheckResult, write_report


class ReportParser(HTMLParser):
    def __init__(self, document: str):
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.feed(document)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def attrs(self, tag):
        return [attrs for name, attrs in self.tags if name == tag]


@pytest.fixture(params=['journal', 'backtest', 'health'])
def generated_report(request, tmp_path: Path):
    if request.param == 'journal':
        return build_html_report(summarize([dict(SAMPLE_ROW)]))
    if request.param == 'backtest':
        write_outputs(build_report(DEFAULT_CONFIG), tmp_path)
        return (tmp_path / 'evaluation-report.html').read_text(encoding='utf-8')
    write_report([CheckResult('Synthetic check', 'WARN', 'Synthetic warning', 'fixture')],
                 tmp_path, datetime(2026, 11, 4, tzinfo=timezone.utc))
    return (tmp_path / 'health-report.html').read_text(encoding='utf-8')


def test_report_has_language_viewport_and_main_landmark(generated_report):
    report = ReportParser(generated_report)
    assert report.attrs('html') == [{'lang': 'en'}]
    assert len(report.attrs('main')) == 1
    assert len(report.attrs('h1')) == 1
    assert any(meta.get('name') == 'viewport' and 'width=device-width' in meta['content']
               for meta in report.attrs('meta'))


def test_report_tables_have_captions_headers_and_keyboard_scroll_regions(generated_report):
    report = ReportParser(generated_report)
    assert len(report.attrs('caption')) == len(report.attrs('table'))
    assert all(header.get('scope') in ('col', 'row') for header in report.attrs('th'))
    regions = [attrs for attrs in report.attrs('div') if attrs.get('role') == 'region']
    assert len(regions) == len(report.attrs('table'))
    assert all(region.get('aria-label') and region.get('tabindex') == '0' for region in regions)
    assert ':focus-visible' in generated_report
    assert 'overflow-x:auto' in generated_report or 'overflow-x: auto' in generated_report


def test_equity_chart_has_complete_text_data_alternative(tmp_path):
    report = build_report(DEFAULT_CONFIG)
    write_outputs(report, tmp_path)
    document = (tmp_path / 'evaluation-report.html').read_text(encoding='utf-8')
    assert '<summary>Read the equity curve as a data table</summary>' in document
    assert '<caption>Out-of-sample equity observations</caption>' in document
    values = report['fixed_split']['out_of_sample_equity']
    for index, value in enumerate(values, start=1):
        assert f'<tr><th scope="row">{index}</th><td>{value:.6f}</td></tr>' in document


def test_journal_report_keeps_untrusted_text_as_text():
    trade = dict(SAMPLE_ROW, notes='<img src=x onerror=alert(1)>')
    document = build_html_report(summarize([trade]))
    assert '<img' not in document
    assert '&lt;img src=x onerror=alert(1)&gt;' in document
