/* Optional DOM behavior regression: install jsdom 26.1.0 in a separate
 * tooling environment and make it available through NODE_PATH. No network
 * requests or real browser/account data are used. This is not visual/AT QA.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const wait = () => new Promise(resolve => setTimeout(resolve, 80));
(async () => {
  let failSave = false, failHistory = false, saves = 0, deletes = 0, confirmDelete = false;
  let rows = [{ id: 1, date: '2026-01-01', ticker: 'SAMPLE', direction: 'LONG', qty: 1,
    entry: 10, exit: 11, pnl: 1, result: 'WIN', setup: '<em>Example</em>', emotion: 'Calm', mistake: 'Synthetic only' }];
  const dom = new JSDOM(fs.readFileSync(path.join(__dirname, '../../Journal/journal.html'), 'utf8'), {
    url: 'http://journal.test/', runScripts: 'dangerously', beforeParse(window) {
      window.confirm = () => confirmDelete;
      window.fetch = async (url, options = {}) => {
        let body, ok = true;
        if (url === '/api/stats') body = { message: 'No closed trades yet.' };
        else if (url === '/api/ai_prompt') body = { prompt: 'Synthetic prompt.' };
        else if (url === '/api/trades' && options.method === 'POST') { saves++; await wait(); ok = !failSave; body = { result: 'OPEN', pnl: null }; }
        else if (url === '/api/trades') { ok = !failHistory; body = rows; }
        else if (url === '/api/trades/1' && options.method === 'DELETE') { deletes++; rows = []; body = { status: 'deleted' }; }
        else throw new Error(`Unexpected request: ${url}`);
        return { ok, json: async () => body };
      };
    }
  });
  try {
    const w = dom.window, d = w.document;
    await wait();
    d.querySelector('#tab-log').focus();
    for (const [key, id] of [['ArrowRight','trades'],['End','ai'],['ArrowRight','log'],['ArrowLeft','ai'],['Home','log']]) {
      d.activeElement.dispatchEvent(new w.KeyboardEvent('keydown', { key, bubbles: true }));
      assert.equal(d.activeElement.id, `tab-${id}`);
      assert.equal(d.activeElement.getAttribute('aria-selected'), 'true');
      assert.equal(d.querySelectorAll('.panel:not([hidden])').length, 1);
    }
    d.querySelector('#f-ticker').value = 'SAMPLE';
    d.querySelector('#f-entry').value = '10';
    const submit = () => d.querySelector('form').dispatchEvent(new w.Event('submit', { bubbles: true, cancelable: true }));
    failSave = true; submit(); await wait(); await wait();
    assert.equal(d.querySelector('#f-ticker').value, 'SAMPLE');
    assert.match(d.querySelector('#toast').textContent, /Could not confirm the save/);
    assert.equal(d.querySelector('[type="submit"]').disabled, false);
    failSave = false; submit(); submit(); await wait(); await wait();
    assert.equal(saves, 2);
    assert.match(d.querySelector('#toast').textContent, /Trade saved/);
    assert.equal(d.activeElement.id, 'f-ticker');
    w.switchTab('trades'); await wait();
    assert.equal(d.querySelector('#trades-body em'), null, 'Stored text stays literal');
    assert.match(d.querySelector('#trades-body').textContent, /<em>Example<\/em>/);
    const remove = d.querySelector('[data-trade-id]'); remove.focus();
    await w.deleteTrade(1, remove);
    assert.equal(deletes, 0);
    assert.equal(d.activeElement, remove);
    const originalRows = rows;
    confirmDelete = true; await w.deleteTrade(1, remove); await wait();
    assert.equal(deletes, 1);
    assert.equal(d.activeElement.id, 'panel-trades');
    assert.match(d.querySelector('#toast').textContent, /Trade deleted/);
    rows = originalRows; await w.loadTrades();
    const refreshFailureRemove = d.querySelector('[data-trade-id]'); refreshFailureRemove.focus();
    failHistory = true; await w.deleteTrade(1, refreshFailureRemove); await wait();
    assert.equal(deletes, 2);
    assert.equal(d.querySelector('[data-trade-id]'), null, 'Confirmed deleted row must not remain as stale data');
    assert.equal(d.activeElement.id, 'panel-trades');
    assert.match(d.querySelector('#toast').textContent, /Trade deleted, but history could not be refreshed/);
    await w.loadTrades(); await wait();
    assert.match(d.querySelector('#toast').textContent, /Could not load trade history/);
    w.switchTab('ai'); await w.loadAIPrompt(); await wait();
    assert.equal(d.querySelector('#ai-prompt').textContent, 'Synthetic prompt.');
    await w.copyPrompt(); await wait();
    assert.equal(d.activeElement.id, 'ai-prompt');
    assert.match(d.querySelector('#toast').textContent, /Clipboard is unavailable/);
    // Review regressions use controlled completion order, not timing guesses.
    const regressions = [];
    async function regression(name, check) {
      try { await check(); console.log(`PASS review regression: ${name}`); }
      catch (error) { regressions.push(`${name}: ${error.message}`); }
    }
    await regression('offscreen save error is revealed without moving focus', async () => {
      w.switchTab('log');
      const status = d.querySelector('#toast');
      const originalRect = status.getBoundingClientRect;
      let scrolled = false;
      status.getBoundingClientRect = () => ({ top: -500, bottom: -450 });
      status.scrollIntoView = () => { scrolled = true; };
      d.querySelector('#f-ticker').value = 'SAMPLE';
      d.querySelector('#f-entry').value = '10';
      d.querySelector('[type="submit"]').focus();
      failSave = true; submit(); await wait(); await wait();
      status.getBoundingClientRect = originalRect;
      assert.equal(scrolled, true);
      assert.equal(d.activeElement, d.querySelector('[type="submit"]'));
      assert.equal(status.getAttribute('role'), 'status');
      assert.equal(status.getAttribute('aria-live'), 'polite');
    });
    await regression('save failure respects navigation to another panel', async () => {
      w.switchTab('log');
      const status = d.querySelector('#toast');
      const originalRect = status.getBoundingClientRect;
      let scrolled = false;
      status.getBoundingClientRect = () => ({ top: -500, bottom: -450 });
      status.scrollIntoView = () => { scrolled = true; };
      submit(); w.switchTab('ai'); d.querySelector('#tab-ai').focus();
      await wait(); await wait();
      status.getBoundingClientRect = originalRect;
      assert.equal(scrolled, false);
      assert.equal(d.activeElement.id, 'tab-ai');
    });
    const originalFetch = w.fetch;
    for (const [loader, url] of [['loadTrades', '/api/trades'], ['loadStats', '/api/stats']]) {
      await regression(`${loader} ignores stale failures`, async () => {
        let rejectOld, requests = 0;
        w.fetch = (requested, options) => {
          if (requested === url && ++requests === 1) return new Promise((resolve, reject) => { rejectOld = reject; });
          return Promise.resolve({ ok: true, json: async () => url.endsWith('trades') ? [] : { message: 'Newest stats' } });
        };
        try {
          const old = w[loader]();
          await w[loader]();
          w.toast('Latest operation succeeded.'); await wait();
          rejectOld(new Error('Old request failed'));
          await old; await wait();
          assert.equal(d.querySelector('#toast').textContent, 'Latest operation succeeded.');
        } finally { w.fetch = originalFetch; }
      });
    }
    for (const [loader, url] of [['loadTrades', '/api/trades'], ['loadStats', '/api/stats']]) {
      await regression(`${loader} suppresses a queued error after a newer read`, async () => {
        const originalTimer = w.setTimeout, originalClear = w.clearTimeout;
        const callbacks = [];
        w.setTimeout = callback => { callbacks.push(callback); return callbacks.length; };
        w.clearTimeout = () => {};
        let requests = 0;
        w.fetch = async () => ({ ok: ++requests > 1, json: async () => url.endsWith('trades') ? [] : { message: 'Latest stats' } });
        try {
          await w[loader]();
          await w[loader]();
          d.querySelector('#toast').textContent = 'Newer status';
          callbacks.forEach(callback => callback());
          assert.equal(d.querySelector('#toast').textContent, 'Newer status');
        } finally { w.setTimeout = originalTimer; w.clearTimeout = originalClear; w.fetch = originalFetch; }
      });
    }
    await regression('delete refresh preserves newly selected focus', async () => {
      rows = originalRows; failHistory = false;
      w.switchTab('trades'); await w.loadTrades();
      const button = d.querySelector('[data-trade-id]'); button.focus();
      let releaseRefresh, markRefresh;
      const refreshStarted = new Promise(resolve => { markRefresh = resolve; });
      w.fetch = (url, options) => {
        if (url === '/api/trades' && !options) return new Promise(resolve => {
          releaseRefresh = () => resolve({ ok: true, json: async () => [] });
          markRefresh();
        });
        return originalFetch(url, options);
      };
      try {
        const deleting = w.deleteTrade(1, button);
        await refreshStarted;
        const exportButton = d.querySelector('#panel-trades .btn-export');
        exportButton.focus();
        releaseRefresh(); await deleting; await wait();
        assert.equal(d.activeElement, exportButton);
      } finally { w.fetch = originalFetch; }
    });
    await regression('delete refresh preserves focus on a surviving row action', async () => {
      const survivor = { ...originalRows[0], id: 2, ticker: 'SURVIVOR' };
      rows = [...originalRows, survivor]; failHistory = false;
      w.switchTab('trades'); await w.loadTrades();
      const button = d.querySelector('[data-trade-id="1"]'); button.focus();
      let releaseRefresh, markRefresh;
      const refreshStarted = new Promise(resolve => { markRefresh = resolve; });
      w.fetch = (url, options) => {
        if (url === '/api/trades/1' && options?.method === 'DELETE') {
          rows = [survivor];
          return Promise.resolve({ ok: true, json: async () => ({ status: 'deleted' }) });
        }
        if (url === '/api/trades' && !options) return new Promise(resolve => {
          releaseRefresh = () => resolve({ ok: true, json: async () => [survivor] });
          markRefresh();
        });
        return originalFetch(url, options);
      };
      try {
        const deleting = w.deleteTrade(1, button);
        await refreshStarted;
        d.querySelector('[data-trade-id="2"]').focus();
        releaseRefresh(); await deleting; await wait();
        assert.equal(d.activeElement, d.querySelector('[data-trade-id="2"]'));
        assert.equal(d.activeElement.isConnected, true);
      } finally { w.fetch = originalFetch; }
    });
    await regression('superseded delete refresh cannot overwrite a newer read failure', async () => {
      rows = originalRows; failHistory = false;
      w.switchTab('trades'); await w.loadTrades();
      const button = d.querySelector('[data-trade-id="1"]'); button.focus();
      let rejectRefresh, markRefresh, reads = 0;
      const refreshStarted = new Promise(resolve => { markRefresh = resolve; });
      w.fetch = (url, options) => {
        if (url === '/api/trades' && !options) {
          if (++reads === 1) return new Promise((resolve, reject) => { rejectRefresh = reject; markRefresh(); });
          return Promise.resolve({ ok: false });
        }
        return originalFetch(url, options);
      };
      try {
        const deleting = w.deleteTrade(1, button);
        await refreshStarted;
        await w.loadTrades(); await wait();
        const newerError = d.querySelector('#toast').textContent;
        assert.match(newerError, /Could not load trade history/);
        rejectRefresh(new Error('Superseded refresh failed'));
        await deleting; await wait();
        assert.equal(d.querySelector('#toast').textContent, newerError);
      } finally { w.fetch = originalFetch; }
    });
    assert.deepEqual(regressions, [], 'Review findings must stay fixed');
    console.log('PASS: tab keys/state, save error preservation, retry, duplicate suppression, focus, delete cancel/confirm and refresh failure, history error, literal text, prompt generation, clipboard fallback.');
  } finally { dom.window.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
