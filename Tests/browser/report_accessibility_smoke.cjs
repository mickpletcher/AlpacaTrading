/* Real-browser accessibility checks of deterministic local reports.
 * First run: python Tests/browser/generate_reports.py
 * Then run: node Tests/browser/report_accessibility_smoke.cjs
 * All browser requests are intercepted. No server, credentials, or account is used.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;
const reports = ['evaluation-report.html', 'journal-report.html', 'health-report.html'];
const fixtures = process.env.REPORT_FIXTURES || path.join(__dirname, '.reports');

(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}) });
  const checks = [];
  try {
    for (const file of reports) {
      const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const document = fs.readFileSync(path.join(fixtures, file), 'utf8');
      await page.route('**/*', route => {
        if (route.request().url() === `http://reports.test/${file}`) {
          return route.fulfill({ contentType: 'text/html', body: document });
        }
        return route.abort();
      });
      await page.goto(`http://reports.test/${file}`);
      if (file === 'evaluation-report.html') {
        const disclosure = page.getByText('Read the equity curve as a data table', { exact: true });
        await disclosure.focus();
        await page.keyboard.press('Enter');
        assert.notEqual(await page.locator('details').getAttribute('open'), null);
        assert.equal(await page.getByRole('table', { name: 'Out-of-sample equity observations' }).isVisible(), true);
        assert.ok(await page.locator('details tbody tr').count() > 0);
        await page.keyboard.press('Enter');
        assert.equal(await page.locator('details').getAttribute('open'), null);
        await page.keyboard.press('Enter'); // Audit the complete table alternative while expanded.
      }
      for (const width of [1280, 320]) {
        await page.setViewportSize({ width, height: 900 });
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true,
          `${file}: page must reflow at ${width}px; tables may scroll inside their named regions`);
        for (const region of await page.locator('[role="region"]:visible').all()) {
          await region.focus();
          assert.equal(await region.evaluate(element => element === document.activeElement), true);
          assert.notEqual(await region.evaluate(element => getComputedStyle(element).outlineStyle), 'none');
          if (await region.evaluate(element => element.scrollWidth > element.clientWidth + 1)) {
            await region.evaluate(element => { element.scrollLeft = 0; });
            await page.keyboard.press('ArrowRight');
            await page.waitForFunction(element => element.scrollLeft > 0, await region.elementHandle());
          }
        }
        const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
        assert.deepEqual(result.violations.map(v => ({ id: v.id, impact: v.impact, targets: v.nodes.map(n => n.target) })), [],
          `${file}: automated WCAG A/AA findings at ${width}px`);
        checks.push(`${file}: ${width}px reflow, keyboard scroll, and axe A/AA passed`);
      }
      // Text-only enlargement is distinct from a browser-zoom or screen-reader audit.
      await page.evaluate(() => {
        const sizes = [...document.querySelectorAll('body, body *')].map(element =>
          [element, Number.parseFloat(getComputedStyle(element).fontSize)]);
        for (const [element, size] of sizes) element.style.fontSize = `${size * 2}px`;
      });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true,
        `${file}: 200% text must not cause whole-page horizontal overflow at 320px`);
      for (const region of await page.locator('[role="region"]:visible').all()) {
        assert.equal(await region.evaluate(element => element.clientWidth > 0 && element.clientHeight > 0), true);
      }
      assert.deepEqual(errors, [], `${file}: unexpected browser JavaScript errors`);
      checks.push(`${file}: 200% text enlargement and JavaScript error check passed`);
      await page.close();
    }
    console.log(checks.join('\n'));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
