/* Optional real-browser smoke check. Install Playwright in a separate tooling
 * environment, then run npm --prefix Tests/browser test.
 * Set CHROMIUM_EXECUTABLE only to an installed trusted Chromium executable.
 * All requests are intercepted; no server, credentials, or trading account is used.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;
(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}) });
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const screenshots = path.join(__dirname, '.reports');
    fs.mkdirSync(screenshots, { recursive: true });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    let failSave = false, failHistory = false, failDelete = false, slowHistory = false, saves = 0, deletes = 0;
    let releaseStaleHistory, staleCapturedResolve;
    const staleCaptured = new Promise(resolve => { staleCapturedResolve = resolve; });
    let rows = [{ id: 1, date: '2026-01-01', ticker: 'SAMPLE', direction: 'LONG', qty: 1,
      entry: 10, exit: 11, pnl: 1, result: 'WIN', setup: 'Example', emotion: 'Calm', mistake: 'Synthetic data only' }];
    await page.route('**/*', async route => {
      const request = route.request(), url = new URL(request.url());
      let body, status = 200;
      if (url.pathname === '/') return route.fulfill({ contentType: 'text/html', body: fs.readFileSync(path.join(__dirname, '../../Journal/journal.html'), 'utf8') });
      if (url.pathname === '/api/stats') body = { total_pnl: 1, win_rate: 100, total_trades: rows.length, avg_win: 1, avg_loss: 0, profit_factor: '1.0', current_streak: { type: 'WIN', count: 1 }, setup_performance: { Example: { wins: 1, losses: 0, pnl: 1 } } };
      else if (url.pathname === '/api/ai_prompt') body = { prompt: 'Synthetic coaching prompt.' };
      else if (url.pathname === '/api/trades' && request.method() === 'POST') {
        saves++; await new Promise(r => setTimeout(r, 150)); status = failSave ? 500 : 201;
        body = { result: 'OPEN', pnl: null };
      } else if (url.pathname === '/api/trades') {
        body = rows; status = failHistory ? 500 : 200;
        if (slowHistory) {
          slowHistory = false;
          body = [{ ...rows[0], ticker: 'STALE' }];
          await new Promise(resolve => { releaseStaleHistory = resolve; staleCapturedResolve(); });
        }
      }
      else if (url.pathname === '/api/trades/1' && request.method() === 'DELETE') { deletes++; status = failDelete ? 500 : 200; if (!failDelete) rows = []; body = { status: 'deleted' }; }
      else return route.abort();
      await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
    });
    await page.goto('http://journal.test/');
    await page.keyboard.press('Tab');
    assert.equal(await page.locator(':focus').textContent(), 'Skip to journal');
    await page.keyboard.press('Enter');
    assert.equal(await page.locator(':focus').getAttribute('id'), 'main-content');
    await page.locator('#tab-log').focus();
    for (const [key, id] of [['ArrowRight', 'trades'], ['End', 'ai'], ['ArrowRight', 'log'], ['ArrowLeft', 'ai'], ['Home', 'log']]) {
      await page.keyboard.press(key);
      assert.equal(await page.locator(':focus').getAttribute('id'), `tab-${id}`);
      assert.equal(await page.locator(`#tab-${id}`).getAttribute('aria-selected'), 'true');
      assert.equal(await page.locator('.panel:not([hidden])').count(), 1);
    }
    await page.getByLabel('Ticker (required)').fill('SAMPLE');
    await page.getByLabel('Entry Price (required)').fill('10');
    failSave = true;
    await page.locator('[type="submit"]').click();
    await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('Could not confirm the save'));
    assert.equal(await page.locator('#f-ticker').inputValue(), 'SAMPLE');
    failSave = false;
    await page.evaluate(() => { const f = document.querySelector('form'); f.requestSubmit(); f.requestSubmit(); });
    await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('Trade saved'));
    assert.equal(saves, 2, 'One failed save plus one successful save; repeated submission suppressed');
    assert.equal(await page.locator(':focus').getAttribute('id'), 'f-ticker');
    slowHistory = true;
    await page.evaluate(() => {
      document.querySelector('#trades-body').replaceChildren();
      window.historyChecks = Promise.all([loadTrades(), loadTrades()]);
    });
    await staleCaptured;
    await page.waitForFunction(() => document.querySelector('#trades-body').textContent.includes('SAMPLE'));
    releaseStaleHistory();
    await page.evaluate(() => window.historyChecks);
    assert.equal(await page.locator('#trades-body').textContent().then(t => t.includes('STALE')), false, 'Older trade loads cannot replace newer data');
    await page.locator('#tab-trades').click();
    const remove = page.getByRole('button', { name: 'Delete SAMPLE trade from 2026-01-01' });
    await remove.waitFor();
    // Audit populated history before deleting its only row.
    for (const width of [1280, 320]) {
      await page.setViewportSize({ width, height: 900 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true,
        `Populated history reflows at ${width}px`);
      await page.screenshot({ path: path.join(screenshots, `journal-populated-${width}.png`), fullPage: true });
      const report = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
      assert.deepEqual(report.violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) })), [],
        `Populated history has no axe WCAG A/AA violations at ${width}px`);
    }
    await page.setViewportSize({ width: 1280, height: 900 });
    page.once('dialog', dialog => dialog.dismiss());
    await remove.click();
    assert.equal(deletes, 0);
    assert.equal(await remove.isVisible(), true);
    failDelete = true;
    page.once('dialog', dialog => dialog.accept());
    await remove.click();
    await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('Could not confirm deletion'));
    assert.equal(await remove.isEnabled(), true);
    assert.equal(await remove.isVisible(), true);
    assert.equal(deletes, 1);
    failDelete = false;
    failHistory = true; // DELETE succeeds, but the follow-up refresh fails.
    page.once('dialog', dialog => dialog.accept());
    await remove.click();
    await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('Trade deleted'));
    assert.equal(deletes, 2);
    assert.equal(await page.locator('[data-trade-id]').count(), 0);
    assert.match(await page.locator('#toast').textContent(), /history could not be refreshed/);
    assert.equal(await page.locator(':focus').getAttribute('id'), 'panel-trades');
    failHistory = true;
    await page.locator('#tab-trades').click();
    await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('Could not load trade history'));
    failHistory = false;
    await page.locator('#tab-ai').click();
    await page.getByRole('button', { name: /GENERATE PROMPT/ }).click();
    await page.waitForFunction(() => document.querySelector('#ai-prompt').textContent === 'Synthetic coaching prompt.');
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { value: { writeText: async () => { throw Error('Unavailable'); } }, configurable: true }));
    await page.getByRole('button', { name: /COPY TO CLIPBOARD/ }).click();
    await page.waitForFunction(() => document.activeElement.id === 'ai-prompt');
    for (const name of ['log', 'trades', 'stats', 'ai']) {
      await page.locator(`#tab-${name}`).click();
      if (name === 'stats') await page.getByRole('table', { name: 'Results by setup' }).waitFor();
      await page.screenshot({ path: path.join(screenshots, `journal-${name}-1280.png`), fullPage: true });
      const report = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
      assert.deepEqual(report.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.map(n => n.target) })), [], `${name} has no axe WCAG A/AA violations`);
    }
    // 320 CSS pixels approximates the reflow viewport at 400% desktop zoom.
    await page.setViewportSize({ width: 320, height: 900 });
    for (const name of ['log', 'trades', 'stats', 'ai']) {
      await page.locator(`#tab-${name}`).click();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${name} reflows without page-wide horizontal scrolling`);
      await page.screenshot({ path: path.join(screenshots, `journal-${name}-320.png`), fullPage: true });
    }
    assert.equal(await page.locator('.panel.active').evaluate(el => getComputedStyle(el).animationName), 'none');
    assert.deepEqual(errors, []);
    console.log('Journal accessibility browser smoke passed: keyboard, form errors/retry, duplicate suppression, delete cancel/confirm, focus, clipboard fallback, 320px reflow, reduced motion.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
