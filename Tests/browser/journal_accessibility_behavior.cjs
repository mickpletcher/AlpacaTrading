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
    confirmDelete = true; await w.deleteTrade(1, remove); await wait();
    assert.equal(deletes, 1);
    assert.equal(d.activeElement.id, 'panel-trades');
    assert.match(d.querySelector('#toast').textContent, /Trade deleted/);
    failHistory = true; await w.loadTrades(); await wait();
    assert.match(d.querySelector('#toast').textContent, /Could not load trade history/);
    w.switchTab('ai'); await w.loadAIPrompt(); await wait();
    assert.equal(d.querySelector('#ai-prompt').textContent, 'Synthetic prompt.');
    await w.copyPrompt(); await wait();
    assert.equal(d.activeElement.id, 'ai-prompt');
    assert.match(d.querySelector('#toast').textContent, /Clipboard is unavailable/);
    console.log('PASS: tab keys/state, save error preservation, retry, duplicate suppression, focus, delete cancel/confirm, history error, literal text, prompt generation, clipboard fallback.');
  } finally { dom.window.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
