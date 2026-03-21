<#
=============================================================
  Alpaca Paper Trading Environment for PowerShell
  Paper trading = real market data, fake money. No risk.

  SETUP:
  1. Create a FREE account at https://alpaca.markets
  2. Go to Paper Trading section and generate API keys
  3. Set environment variables:

     Windows PowerShell:
       [System.Environment]::SetEnvironmentVariable("ALPACA_API_KEY","YOUR_KEY","User")
       [System.Environment]::SetEnvironmentVariable("ALPACA_SECRET_KEY","YOUR_SECRET","User")

     PowerShell session only:
       $env:ALPACA_API_KEY = "YOUR_KEY"
       $env:ALPACA_SECRET_KEY = "YOUR_SECRET"

  Usage:
    .\alpaca_paper.ps1 status
    .\alpaca_paper.ps1 quote AAPL
    .\alpaca_paper.ps1 buy AAPL 1
    .\alpaca_paper.ps1 sell AAPL 1
    .\alpaca_paper.ps1 positions
    .\alpaca_paper.ps1 orders
    .\alpaca_paper.ps1 bot
=============================================================
#>

param(
    [Parameter(Position=0)]
    [string]$Command = "status",

    [Parameter(Position=1)]
    [string]$Ticker,

    [Parameter(Position=2)]
    [int]$Qty
)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
$script:AlpacaApiKey    = $env:ALPACA_API_KEY
$script:AlpacaSecretKey = $env:ALPACA_SECRET_KEY

$script:TradingBaseUrl  = "https://paper-api.alpaca.markets"
$script:DataBaseUrl     = "https://data.alpaca.markets"

$script:BotTicker       = "SPY"
$script:BotInterval     = 60
$script:BotQty          = 1
$script:EmaFast         = 9
$script:EmaSlow         = 21
$script:PriceHistory    = New-Object System.Collections.Generic.List[double]

function Test-Config {
    if ([string]::IsNullOrWhiteSpace($script:AlpacaApiKey) -or [string]::IsNullOrWhiteSpace($script:AlpacaSecretKey)) {
        Write-Host ""
        Write-Host "API keys not configured." -ForegroundColor Yellow
        Write-Host "Set these environment variables first:"
        Write-Host "  ALPACA_API_KEY"
        Write-Host "  ALPACA_SECRET_KEY"
        exit 1
    }
}

function Get-AlpacaHeaders {
    Test-Config
    return @{
        "APCA-API-KEY-ID"     = $script:AlpacaApiKey
        "APCA-API-SECRET-KEY" = $script:AlpacaSecretKey
        "accept"              = "application/json"
    }
}

function Invoke-AlpacaTradingApi {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("GET","POST","DELETE","PUT","PATCH")]
        [string]$Method,

        [Parameter(Mandatory)]
        [string]$Path,

        [object]$Body = $null
    )

    $uri = "{0}{1}" -f $script:TradingBaseUrl, $Path
    $headers = Get-AlpacaHeaders

    try {
        if ($null -ne $Body) {
            $json = $Body | ConvertTo-Json -Depth 10
            return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -ContentType "application/json" -Body $json
        } else {
            return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
        }
    }
    catch {
        $msg = $_.Exception.Message
        if ($_.ErrorDetails.Message) {
            $msg = $_.ErrorDetails.Message
        }
        throw $msg
    }
}

function Invoke-AlpacaDataApi {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    $uri = "{0}{1}" -f $script:DataBaseUrl, $Path
    $headers = Get-AlpacaHeaders

    try {
        return Invoke-RestMethod -Method GET -Uri $uri -Headers $headers
    }
    catch {
        $msg = $_.Exception.Message
        if ($_.ErrorDetails.Message) {
            $msg = $_.ErrorDetails.Message
        }
        throw $msg
    }
}

function Get-Account {
    Invoke-AlpacaTradingApi -Method GET -Path "/v2/account"
}

function Get-Clock {
    Invoke-AlpacaTradingApi -Method GET -Path "/v2/clock"
}

function Get-LatestQuoteAndTrade {
    param(
        [Parameter(Mandatory)]
        [string]$Symbol
    )

    $quoteResp = Invoke-AlpacaDataApi -Path "/v2/stocks/quotes/latest?symbols=$Symbol"
    $tradeResp = Invoke-AlpacaDataApi -Path "/v2/stocks/trades/latest?symbols=$Symbol"

    return [PSCustomObject]@{
        Quote = $quoteResp.quotes.$Symbol
        Trade = $tradeResp.trades.$Symbol
    }
}

function Get-Position {
    param(
        [Parameter(Mandatory)]
        [string]$Symbol
    )

    Invoke-AlpacaTradingApi -Method GET -Path "/v2/positions/$Symbol"
}

function Get-Positions {
    Invoke-AlpacaTradingApi -Method GET -Path "/v2/positions"
}

function Get-Orders {
    param(
        [string]$Status = "open"
    )

    Invoke-AlpacaTradingApi -Method GET -Path "/v2/orders?status=$Status"
}

function Submit-Order {
    param(
        [Parameter(Mandatory)]
        [string]$Symbol,

        [Parameter(Mandatory)]
        [int]$Qty,

        [Parameter(Mandatory)]
        [ValidateSet("buy","sell")]
        [string]$Side
    )

    $body = @{
        symbol        = $Symbol
        qty           = $Qty
        side          = $Side
        type          = "market"
        time_in_force = "day"
    }

    Invoke-AlpacaTradingApi -Method POST -Path "/v2/orders" -Body $body
}

function Show-Status {
    try {
        $acct = Get-Account
        $portfolioValue = [double]$acct.portfolio_value
        $cash = [double]$acct.cash
        $buyingPower = [double]$acct.buying_power
        $equity = [double]$acct.equity
        $lastEquity = [double]$acct.last_equity
        $pnl = $equity - $lastEquity
        $marker = if ($pnl -ge 0) { "[UP]" } else { "[DOWN]" }

        Write-Host ""
        Write-Host "PAPER ACCOUNT STATUS"
        Write-Host ("=" * 40)
        Write-Host ("  Status:          {0}" -f $acct.status)
        Write-Host ("  Portfolio Value: ${0,12:N2}" -f $portfolioValue)
        Write-Host ("  Cash:            ${0,12:N2}" -f $cash)
        Write-Host ("  Buying Power:    ${0,12:N2}" -f $buyingPower)
        Write-Host ("  Day Trades Used: {0} / 3 (PDT rule)" -f $acct.daytrade_count)
        Write-Host ("  Equity:          ${0,12:N2}" -f $equity)
        Write-Host ("  Today's P&L:     {0} ${1:+N2;-N2;0.00}" -f $marker, $pnl)
        Write-Host ("=" * 40)
    }
    catch {
        Write-Host "Status error: $_" -ForegroundColor Red
    }
}

function Show-Quote {
    param(
        [Parameter(Mandatory)]
        [string]$Symbol
    )

    try {
        $data = Get-LatestQuoteAndTrade -Symbol $Symbol.ToUpper()
        $quote = $data.Quote
        $trade = $data.Trade

        $bid = [double]$quote.bp
        $ask = [double]$quote.ap
        $last = [double]$trade.p
        $spread = $ask - $bid
        $spreadPct = if ($last -ne 0) { ($spread / $last) * 100 } else { 0 }

        Write-Host ""
        Write-Host $Symbol.ToUpper()
        Write-Host ("  Bid:    ${0,10:N2}  (x{1})" -f $bid, $quote.bs)
        Write-Host ("  Ask:    ${0,10:N2}  (x{1})" -f $ask, $quote.as)
        Write-Host ("  Last:   ${0,10:N2}  @ {1}" -f $last, $trade.t)
        Write-Host ("  Spread: ${0:N4}  ({1:N3}%)" -f $spread, $spreadPct)
    }
    catch {
        Write-Host "Quote error: $_" -ForegroundColor Red
    }
}

function Buy-Shares {
    param(
        [Parameter(Mandatory)]
        [string]$Symbol,

        [Parameter(Mandatory)]
        [int]$Qty
    )

    Write-Host ""
    Write-Host ("Buying {0} share(s) of {1} at market..." -f $Qty, $Symbol.ToUpper())

    try {
        $order = Submit-Order -Symbol $Symbol.ToUpper() -Qty $Qty -Side "buy"
        Write-Host ("  Order submitted: {0}" -f $order.id) -ForegroundColor Green
        Write-Host ("  Status: {0}" -f $order.status)
    }
    catch {
        Write-Host "  Order failed: $_" -ForegroundColor Red
    }
}

function Sell-Shares {
    param(
        [Parameter(Mandatory)]
        [string]$Symbol,

        [Parameter(Mandatory)]
        [int]$Qty
    )

    Write-Host ""
    Write-Host ("Selling {0} share(s) of {1} at market..." -f $Qty, $Symbol.ToUpper())

    try {
        $order = Submit-Order -Symbol $Symbol.ToUpper() -Qty $Qty -Side "sell"
        Write-Host ("  Order submitted: {0}" -f $order.id) -ForegroundColor Green
        Write-Host ("  Status: {0}" -f $order.status)
    }
    catch {
        Write-Host "  Order failed: $_" -ForegroundColor Red
    }
}

function Show-Positions {
    try {
        $positions = @(Get-Positions)
        if (-not $positions -or $positions.Count -eq 0) {
            Write-Host ""
            Write-Host "No open positions."
            return
        }

        Write-Host ""
        Write-Host ("OPEN POSITIONS ({0})" -f $positions.Count)
        Write-Host ("=" * 65)
        "{0,-8} {1,8} {2,12} {3,12} {4,14}" -f "Symbol","Qty","Entry","Current","P&L" | Write-Host
        Write-Host ("-" * 65)

        foreach ($p in $positions) {
            $pnl = [double]$p.unrealized_pl
            $marker = if ($pnl -ge 0) { "UP " } else { "DOWN" }

            "{0,-8} {1,8} ${2,11:N2} ${3,11:N2} {4} ${5,+10:N2}" -f `
                $p.symbol,
                $p.qty,
                ([double]$p.avg_entry_price),
                ([double]$p.current_price),
                $marker,
                $pnl | Write-Host
        }

        Write-Host ("=" * 65)
    }
    catch {
        Write-Host "Positions error: $_" -ForegroundColor Red
    }
}

function Show-Orders {
    try {
        $orders = @(Get-Orders -Status "open")
        if (-not $orders -or $orders.Count -eq 0) {
            Write-Host ""
            Write-Host "No open orders."
            return
        }

        Write-Host ""
        Write-Host ("OPEN ORDERS ({0})" -f $orders.Count)
        Write-Host ("=" * 65)

        foreach ($o in $orders) {
            Write-Host ("  {0} | {1} {2} | {3} | {4}" -f $o.symbol, $o.side.ToUpper(), $o.qty, $o.type, $o.status)
        }

        Write-Host ("=" * 65)
    }
    catch {
        Write-Host "Orders error: $_" -ForegroundColor Red
    }
}

function Get-EMA {
    param(
        [Parameter(Mandatory)]
        [double[]]$Prices,

        [Parameter(Mandatory)]
        [int]$Period
    )

    if ($Prices.Count -lt $Period) {
        return $null
    }

    $k = 2.0 / ($Period + 1)
    $ema = ($Prices[0..($Period - 1)] | Measure-Object -Average).Average

    for ($i = $Period; $i -lt $Prices.Count; $i++) {
        $ema = ($Prices[$i] * $k) + ($ema * (1 - $k))
    }

    return [double]$ema
}

function Test-MarketOpen {
    try {
        $clock = Get-Clock
        return [bool]$clock.is_open
    }
    catch {
        Write-Host "Clock error: $_" -ForegroundColor Red
        return $false
    }
}

function Start-EmaBot {
    Write-Host ""
    Write-Host ("EMA CROSSOVER BOT - {0}" -f $script:BotTicker)
    Write-Host ("  Fast EMA: {0} | Slow EMA: {1}" -f $script:EmaFast, $script:EmaSlow)
    Write-Host ("  Qty per trade: {0} share(s)" -f $script:BotQty)
    Write-Host ("  Check interval: {0}s" -f $script:BotInterval)
    Write-Host "  Press Ctrl+C to stop."
    Write-Host ""

    $inPosition = $false
    $prevFast = $null
    $prevSlow = $null

    try {
        $pos = Get-Position -Symbol $script:BotTicker
        if ($pos) {
            $inPosition = $true
            Write-Host ("  Existing position found: {0} shares" -f $pos.qty)
        }
    }
    catch {
        # No position is fine
    }

    while ($true) {
        try {
            if (-not (Test-MarketOpen)) {
                Write-Host ("  Market closed. Waiting... ({0})" -f (Get-Date -Format "HH:mm:ss"))
                Start-Sleep -Seconds 60
                continue
            }

            $data = Get-LatestQuoteAndTrade -Symbol $script:BotTicker
            $price = [double]$data.Trade.p
            $script:PriceHistory.Add($price)

            if ($script:PriceHistory.Count -gt 100) {
                $script:PriceHistory.RemoveAt(0)
            }

            $prices = $script:PriceHistory.ToArray()
            $fast = Get-EMA -Prices $prices -Period $script:EmaFast
            $slow = Get-EMA -Prices $prices -Period $script:EmaSlow
            $ts = Get-Date -Format "HH:mm:ss"

            if ($null -eq $fast -or $null -eq $slow) {
                $barsNeeded = [Math]::Max($script:EmaFast, $script:EmaSlow)
                Write-Host ("  [{0}] ${1:N2} | Collecting data... ({2}/{3})" -f $ts, $price, $script:PriceHistory.Count, $barsNeeded)
            }
            else {
                $signal = if ($fast -gt $slow) { "BULL" } else { "BEAR" }
                Write-Host -NoNewline ("  [{0}] ${1:N2} | EMA{2}={3:N2} EMA{4}={5:N2} | {6}" -f `
                    $ts, $price, $script:EmaFast, $fast, $script:EmaSlow, $slow, $signal)

                $crossUp = ($null -ne $prevFast -and $null -ne $prevSlow -and $prevFast -le $prevSlow -and $fast -gt $slow)
                $crossDown = ($null -ne $prevFast -and $null -ne $prevSlow -and $prevFast -ge $prevSlow -and $fast -lt $slow)

                if ($crossUp -and -not $inPosition) {
                    Write-Host " -> BUY"
                    Buy-Shares -Symbol $script:BotTicker -Qty $script:BotQty
                    $inPosition = $true
                }
                elseif ($crossDown -and $inPosition) {
                    Write-Host " -> SELL"
                    Sell-Shares -Symbol $script:BotTicker -Qty $script:BotQty
                    $inPosition = $false
                }
                else {
                    Write-Host " -> HOLD"
                }

                $prevFast = $fast
                $prevSlow = $slow
            }

            Start-Sleep -Seconds $script:BotInterval
        }
        catch [System.Management.Automation.PipelineStoppedException] {
            Write-Host ""
            Write-Host ""
            Write-Host "Bot stopped."
            Show-Status
            break
        }
        catch {
            Write-Host ""
            Write-Host "  Error: $_" -ForegroundColor Yellow
            Start-Sleep -Seconds 30
        }
    }
}

# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
switch ($Command.ToLower()) {
    "status" {
        Show-Status
    }
    "quote" {
        if (-not $Ticker) {
            Write-Host "Usage: .\alpaca_paper.ps1 quote AAPL"
            exit 1
        }
        Show-Quote -Symbol $Ticker
    }
    "buy" {
        if (-not $Ticker -or -not $Qty) {
            Write-Host "Usage: .\alpaca_paper.ps1 buy AAPL 1"
            exit 1
        }
        Buy-Shares -Symbol $Ticker -Qty $Qty
    }
    "sell" {
        if (-not $Ticker -or -not $Qty) {
            Write-Host "Usage: .\alpaca_paper.ps1 sell AAPL 1"
            exit 1
        }
        Sell-Shares -Symbol $Ticker -Qty $Qty
    }
    "positions" {
        Show-Positions
    }
    "orders" {
        Show-Orders
    }
    "bot" {
        Start-EmaBot
    }
    default {
        Write-Host ""
        Write-Host "Usage:"
        Write-Host "  .\alpaca_paper.ps1 status"
        Write-Host "  .\alpaca_paper.ps1 quote AAPL"
        Write-Host "  .\alpaca_paper.ps1 buy AAPL 1"
        Write-Host "  .\alpaca_paper.ps1 sell AAPL 1"
        Write-Host "  .\alpaca_paper.ps1 positions"
        Write-Host "  .\alpaca_paper.ps1 orders"
        Write-Host "  .\alpaca_paper.ps1 bot"
        exit 1
    }
}
