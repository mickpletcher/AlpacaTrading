"""Credential-free checks for community routes and accessible issue intake."""
from pathlib import Path
import json
import re
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/mickpletcher/AlpacaTrading'
POLICIES = ('CODE_OF_CONDUCT.md', 'CONTRIBUTING.md', 'SUPPORT.md', 'ACCESSIBILITY.md', 'SECURITY.md')
FORMS = ('bug_report.yml', 'feature_request.yml', 'documentation.yml', 'question.yml', 'accessibility.yml')


def test_required_community_documents_have_real_content_and_readme_routes():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    for filename in POLICIES:
        content = (ROOT / filename).read_text(encoding='utf-8')
        assert content.startswith('# ') or '\n# ' in content
        assert len(content.split()) >= 100
        assert f']({filename})' in readme
        assert '[INSERT' not in content
    assert 'MIT License' in (ROOT / 'LICENSE').read_text(encoding='utf-8')
    pr = (ROOT / '.github/PULL_REQUEST_TEMPLATE.md').read_text(encoding='utf-8')
    for term in ('Validation', 'accessibility', 'paper-only', 'secrets', 'Limitations'):
        assert term in pr


def test_issue_forms_have_valid_unique_fields_and_privacy_guidance():
    names = set()
    for filename in FORMS:
        form = yaml.safe_load((ROOT / '.github/ISSUE_TEMPLATE' / filename).read_text(encoding='utf-8'))
        assert set(form) == {'name', 'description', 'title', 'body'}
        assert form['name'] not in names
        names.add(form['name'])
        assert all(isinstance(form[k], str) and form[k].strip() for k in ('name', 'description', 'title'))
        ids = []
        for element in form['body']:
            assert element['type'] in ('markdown', 'input', 'textarea', 'dropdown', 'checkboxes')
            if element['type'] == 'markdown':
                assert element['attributes']['value'].strip()
                continue
            ids.append(element['id'])
            assert re.fullmatch(r'[A-Za-z0-9_-]+', element['id'])
            assert element['attributes']['label'].strip()
            assert isinstance(element['validations']['required'], bool)
        assert ids and len(ids) == len(set(ids))
        intro = form['body'][0]['attributes']['value']
        assert 'public' in intro and 'synthetic' in intro and 'SECURITY.md' in intro
        assert 'account identifiers' in intro


def test_accessibility_form_keeps_sensitive_details_optional_and_blank_route_open():
    directory = ROOT / '.github/ISSUE_TEMPLATE'
    form = yaml.safe_load((directory / 'accessibility.yml').read_text(encoding='utf-8'))
    text = str(form)
    assert 'diagnoses are not required' in text and 'Do not share medical information' in text
    assert REPO + '/issues/new' in text
    fields = {e['id']: e for e in form['body'] if 'id' in e}
    assert fields['environment']['validations']['required'] is False
    assert fields['alternative']['validations']['required'] is False
    config = yaml.safe_load((directory / 'config.yml').read_text(encoding='utf-8'))
    assert config['blank_issues_enabled'] is True
    assert config['contact_links'][0]['url'] == REPO + '/security/advisories/new'


def test_policies_map_to_existing_authorities_and_verified_reporting_destination():
    config = json.loads((ROOT / '.docs-authority.json').read_text(encoding='utf-8'))
    mapping = config['responsibilities']
    standard = (ROOT / 'PROJECT-STANDARD.md').read_text(encoding='utf-8')
    for name, path in [('Contribution process', 'CONTRIBUTING.md'), ('Community conduct', 'CODE_OF_CONDUCT.md'),
                       ('Accessibility', 'ACCESSIBILITY.md'), ('Support', 'SUPPORT.md'), ('Security policy', 'SECURITY.md')]:
        assert mapping[name]['authority'] == path
        assert f'| {name} | `{path}` |' in standard
    security = (ROOT / 'SECURITY.md').read_text(encoding='utf-8')
    assert REPO + '/security/advisories/new' in security
    assert 'do not disclose details publicly' in security
    conduct = (ROOT / 'CODE_OF_CONDUCT.md').read_text(encoding='utf-8')
    assert 'Request for private conduct contact' in conduct
    assert 'not incident details' in conduct


def test_new_community_markdown_relative_links_resolve():
    files = [ROOT / path for path in POLICIES]
    files += list((ROOT / 'specs/007-community-accessibility').glob('*.md'))
    for path in files:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith(('#', 'mailto:')):
                continue
            target = unquote(target.split('#')[0])
            assert (path.parent / target).exists(), f'{path.name}: broken relative target {target}'


def test_required_python_job_runs_pinned_credential_free_browser_checks():
    workflow = (ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8')
    python_job = workflow.split('  python-quality:')[1].split('  powershell-quality:')[0]
    assert 'npm ci --prefix Tests/browser --ignore-scripts' in python_job
    assert 'npx --no-install playwright install chromium' in python_job
    assert 'python Tests/browser/generate_reports.py --output Tests/browser/.reports' in python_job
    assert 'npm --prefix Tests/browser test' in python_job
    package = json.loads((ROOT / 'Tests/browser/package.json').read_text(encoding='utf-8'))
    lock = json.loads((ROOT / 'Tests/browser/package-lock.json').read_text(encoding='utf-8'))
    for name, version in package['devDependencies'].items():
        assert re.fullmatch(r'\d+\.\d+\.\d+', version)
        assert lock['packages'][f'node_modules/{name}']['version'] == version
    assert package['private'] is True
