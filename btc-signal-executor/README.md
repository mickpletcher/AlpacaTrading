<!-- markdownlint-disable MD013 -->

# BTC Signal Executor

Fully automated TradingView webhook receiver for BTC or crypto signals with immediate Alpaca execution.

No UI, no approval step, no retry logic, and no database.

## Features

- FastAPI webhook endpoint at `POST /webhook`
- Strict payload validation with pydantic
- Shared secret passphrase check
- Immediate buy, sell, or close execution via Alpaca
- Failure safe webhook response rules to prevent TradingView alert spam
- Logging to `executor.log` and stdout

## Project Files

```text
btc-signal-executor/
├── main.py
├── executor.py
├── validator.py
├── config.py
├── .env.example
├── requirements.txt
└── README.md
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\requirements.txt
```

## Environment

Copy `.env.example` to `.env`:

```dotenv
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets
WEBHOOK_PASSPHRASE=
PORT=8080
```

## Run Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

Windows PowerShell from repo root:

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir .\btc-signal-executor
```

Health check:

```bash
curl http://127.0.0.1:8080/health
```

Expected response:

```json
{"status":"ok","timestamp":"..."}
```

## Webhook Contract

Endpoint:

```text
POST /webhook
```

Payload:

```json
{
  "passphrase": "YOUR_SECRET",
  "ticker": "BTCUSD",
  "action": "buy",
  "price": 67000.00,
  "quantity": 0.001
}
```

TradingView can send `BTCUSD`, and the executor normalizes that to `BTC/USD` before routing to Alpaca.

Accepted `action` values:

- `buy`
- `sell`
- `close`

## Execution Rules

- `buy` sends a market buy order with fractional quantity
- `sell` sends market sell if shorting is enabled, else closes long position
- `close` attempts to flatten full symbol position via `close_position()`
- unknown action is logged and skipped
- no automatic retry logic

## End to End Webhook Tests

Run these while the server is active.

### Valid buy

```bash
curl -X POST http://127.0.0.1:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"passphrase":"YOUR_SECRET","ticker":"BTCUSD","action":"buy","price":67000.00,"quantity":0.001}'
```

### Valid sell

```bash
curl -X POST http://127.0.0.1:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"passphrase":"YOUR_SECRET","ticker":"BTCUSD","action":"sell","price":67050.00,"quantity":0.001}'
```

### Valid close

```bash
curl -X POST http://127.0.0.1:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"passphrase":"YOUR_SECRET","ticker":"BTCUSD","action":"close","price":67050.00,"quantity":0.001}'
```

### Unauthorized request

```bash
curl -X POST http://127.0.0.1:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"passphrase":"wrong","ticker":"BTCUSD","action":"buy","price":67000.00,"quantity":0.001}'
```

Expected result: HTTP `401`.

### Malformed payload

```bash
curl -X POST http://127.0.0.1:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"passphrase":"YOUR_SECRET","ticker":"BTCUSD","action":"buy"}'
```

Expected result: HTTP `422`.

## Response Rules

- invalid passphrase returns `401`
- malformed or missing required fields return `422`
- Alpaca API errors are logged and still return `200`
- unknown action is logged and returns `200`

This is intentional to avoid TradingView retry loops that can spam alerts.

## What TradingView Should Send

Use one alert message template per strategy action, or include dynamic placeholders if your strategy script sets action text.

Buy template:

```json
{
  "passphrase": "YOUR_SECRET",
  "ticker": "BTCUSD",
  "action": "buy",
  "price": {{close}},
  "quantity": 0.001
}
```

Sell template:

```json
{
  "passphrase": "YOUR_SECRET",
  "ticker": "BTCUSD",
  "action": "sell",
  "price": {{close}},
  "quantity": 0.001
}
```

Close template:

```json
{
  "passphrase": "YOUR_SECRET",
  "ticker": "BTCUSD",
  "action": "close",
  "price": {{close}},
  "quantity": 0.001
}
```

## TradingView Alert Setup

Webhook URL format:

```text
http://YOUR_SERVER_IP:8080/webhook
```

Alert message body template to paste in TradingView:

```json
{
  "passphrase": "YOUR_SECRET",
  "ticker": "BTCUSD",
  "action": "buy",
  "price": {{close}},
  "quantity": 0.001
}
```

Set `YOUR_SECRET` to match `WEBHOOK_PASSPHRASE` in `.env`.

If TradingView and your server are on different networks, use a public URL from reverse proxy or ngrok.

## Deployment Notes

### systemd service example

Save as `/etc/systemd/system/btc-signal-executor.service`:

```ini
[Unit]
Description=BTC Signal Executor FastAPI Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/btc-signal-executor
EnvironmentFile=/opt/btc-signal-executor/.env
ExecStart=/opt/btc-signal-executor/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable btc-signal-executor
sudo systemctl start btc-signal-executor
sudo systemctl status btc-signal-executor
```

Log tail command:

```bash
sudo journalctl -u btc-signal-executor -f
```

### Switch from paper to live

Change one `.env` line:

```dotenv
ALPACA_BASE_URL=https://api.alpaca.markets
```

### Expose local server with ngrok

```bash
ngrok http 8080
```

Use the HTTPS forwarding URL from ngrok as the TradingView webhook URL.

## Operations Runbook

Startup checklist:

1. confirm `.env` values are present
2. keep `ALPACA_BASE_URL=https://paper-api.alpaca.markets` during testing
3. start server and confirm `/health`
4. send one manual buy test via curl
5. verify `executor.log` entry and Alpaca paper activity

If execution fails:

1. check `executor.log` for API status code and message
2. verify trading permissions and account status in Alpaca dashboard
3. verify symbol normalization expected by your account
4. do not add retries in webhook path

If no TradingView requests arrive:

1. verify webhook URL and port in TradingView alert
2. verify server is reachable from internet path
3. if testing locally, confirm ngrok tunnel is active
4. confirm firewall allows inbound TCP on selected port

## Logging

Every request and decision is logged to:

- `executor.log`
- stdout

Logged events include:

- inbound webhook summary
- validation rejections
- order submissions with order IDs
- Alpaca API failures

Sample log lines:

```text
[2026-04-03 21:05:00] INFO WEBHOOK_RECEIVED | ticker=BTCUSD action=buy quantity=0.00100000 price=67000.00
[2026-04-03 21:05:01] INFO ORDER_SUBMITTED | symbol=BTC/USD action=buy qty=0.00100000 order_id=... status=accepted
[2026-04-03 21:06:00] WARNING WEBHOOK_REJECTED | reason=invalid_passphrase | ticker=BTCUSD action=buy quantity=0.00100000
```

<!-- markdownlint-enable MD013 -->
