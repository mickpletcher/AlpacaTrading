<#
.SYNOPSIS
    Validates connectivity and configuration for the Alpaca paper trading API.

.DESCRIPTION
    Test-AlpacaConnection performs a series of diagnostic checks against the Alpaca
    paper trading environment to verify that API credentials are valid, the account
    is in good standing, and that crypto assets (BTC/USD) are tradable and returning
    live quote data. This script is intended to be run before deploying any automated
    trading bot to confirm the foundation is solid.

    Credentials are retrieved at runtime from LastPass CLI (lpass) and are never
    stored in the script or as plaintext environment variables on disk.

    Checks performed:
        1. Account status, buying power, cash, and portfolio value
        2. Market clock status (open/closed) and next open/close times
        3. BTC/USD asset tradability and fractional share support
        4. Live BTC/USD bid/ask quote from Alpaca market data endpoint

.PARAMETER LastPassEntry
    The LastPass entry name where Alpaca credentials are stored.
    Defaults to "Alpaca/PaperTrading".
    Username field = API Key, Password field = API Secret.

.INPUTS
    None. Does not accept pipeline input.

.OUTPUTS
    Formatted console output for each diagnostic section. No objects are written
    to the pipeline.

.EXAMPLE
    # Run using the default LastPass entry name
    .\Test-AlpacaConnection.ps1

.EXAMPLE
    # Run with a custom LastPass entry name
    .\Test-AlpacaConnection.ps1 -LastPassEntry "Trading/Alpaca Paper"

.NOTES
    Author      : Mick Pletcher
    Version     : 1.1
    Created     : 2026-03-20
    Environment : Alpaca Paper Trading (paper-api.alpaca.markets)

    Prerequisites:
        - PowerShell 5.1 or later
        - LastPass CLI installed (choco install lastpass-cli)
        - Active lpass session (run: lpass login your@email.com)
        - Alpaca credentials stored in LastPass:
            lpass add --non-interactive "Alpaca/PaperTrading" `
                --username "YOUR_API_KEY" `
                --password "YOUR_API_SECRET"

    LastPass entry structure:
        Entry Name : Alpaca/PaperTrading (or custom via -LastPassEntry)
        Username   : Alpaca API Key     (APCA-API-KEY-ID)
        Password   : Alpaca API Secret  (APCA-API-SECRET-KEY)

    API Endpoints used:
        GET /v2/account                          - Account details
        GET /v2/clock                            - Market clock
        GET /v2/assets/BTC%2FUSD                - Asset info
        GET /v1beta3/crypto/us/latest/quotes     - Live quote data

    Notes:
        - Crypto markets are 24/7 so the clock will always show as open.
        - Paper trading buying power defaults to $100,000.
        - This script is read-only and does not place any orders.
        - Credentials are held in memory only for the duration of the script
          and are not written to disk or persisted as environment variables.

.LINK
    Alpaca API Docs     : https://docs.alpaca.markets
    Alpaca Paper Trading: https://paper-api.alpaca.markets
    LastPass CLI Docs   : https://github.com/lastpass/lastpass-cli
#>

param (
    [string]$LastPassEntry = "Alpaca/PaperTrading"
)

# --- Verify lpass is installed ---
if (-not (Get-Command lpass -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: LastPass CLI (lpass) is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Install it with:" -ForegroundColor Yellow
    Write-Host "  choco install lastpass-cli" -ForegroundColor Yellow
    Write-Host "  -- or --" -ForegroundColor Yellow
    Write-Host "  scoop install lastpass-cli" -ForegroundColor Yellow
    exit 1
}

# --- Verify lpass session is active ---
$LpassStatus = lpass status 2>&1
if ($LpassStatus -notmatch "Logged in") {
    Write-Host "ERROR: Not logged in to LastPass CLI." -ForegroundColor Red
    Write-Host "Run the following and authenticate:" -ForegroundColor Yellow
    Write-Host "  lpass login your@email.com" -ForegroundColor Yellow
    exit 1
}

# --- Pull credentials from LastPass ---
Write-Host "`nRetrieving credentials from LastPass entry: '$LastPassEntry'" -ForegroundColor DarkGray
try {
    $ApiKey    = lpass show --username "$LastPassEntry" 2>&1
    $ApiSecret = lpass show --password "$LastPassEntry" 2>&1

    if (-not $ApiKey -or $ApiKey -match "Error" -or -not $ApiSecret -or $ApiSecret -match "Error") {
        Write-Host "ERROR: Could not retrieve credentials from LastPass entry '$LastPassEntry'." -ForegroundColor Red
        Write-Host "Verify the entry exists with:" -ForegroundColor Yellow
        Write-Host "  lpass show '$LastPassEntry'" -ForegroundColor Yellow
        exit 1
    }
}
catch {
    Write-Host "ERROR: Failed to retrieve credentials from LastPass: $_" -ForegroundColor Red
    exit 1
}

# --- Configuration ---
$BaseUrl = "https://paper-api.alpaca.markets"

$Headers = @{
    "APCA-API-KEY-ID"     = $ApiKey
    "APCA-API-SECRET-KEY" = $ApiSecret
    "Accept"              = "application/json"
}

# --- Helper Function ---
function Invoke-AlpacaRequest {
    <#
    .SYNOPSIS
        Sends a REST request to the Alpaca API and returns the response object.
    .PARAMETER Endpoint
        The API endpoint path, e.g. /v2/account
    .PARAMETER Method
        HTTP method. Defaults to GET.
    #>
    param (
        [string]$Endpoint,
        [string]$Method = "GET"
    )
    try {
        $Response = Invoke-RestMethod -Uri "$BaseUrl$Endpoint" `
                                      -Method $Method `
                                      -Headers $Headers
        return $Response
    }
    catch {
        Write-Host "ERROR on $Endpoint : $_" -ForegroundColor Red
        return $null
    }
}

# --- 1. Account Info ---
Write-Host "`n=== ACCOUNT ===" -ForegroundColor Cyan
$Account = Invoke-AlpacaRequest -Endpoint "/v2/account"
if ($Account) {
    [PSCustomObject]@{
        Status           = $Account.status
        BuyingPower      = "$" + $Account.buying_power
        Cash             = "$" + $Account.cash
        PortfolioVal     = "$" + $Account.portfolio_value
        DaytradeCount    = $Account.daytrade_count
        PatternDayTrader = $Account.pattern_day_trader
    } | Format-List
}

# --- 2. Market Clock ---
Write-Host "=== MARKET CLOCK ===" -ForegroundColor Cyan
$Clock = Invoke-AlpacaRequest -Endpoint "/v2/clock"
if ($Clock) {
    [PSCustomObject]@{
        IsOpen    = $Clock.is_open
        NextOpen  = $Clock.next_open
        NextClose = $Clock.next_close
        Timestamp = $Clock.timestamp
    } | Format-List
}

# --- 3. BTC/USD Asset Check ---
Write-Host "=== ASSET CHECK (BTC/USD) ===" -ForegroundColor Cyan
$Asset = Invoke-AlpacaRequest -Endpoint "/v2/assets/BTC%2FUSD"
if ($Asset) {
    [PSCustomObject]@{
        Symbol       = $Asset.symbol
        Class        = $Asset.class
        Tradable     = $Asset.tradable
        Fractionable = $Asset.fractionable
        Status       = $Asset.status
    } | Format-List
}

# --- 4. Live BTC/USD Quote ---
Write-Host "=== LATEST BTC/USD PRICE ===" -ForegroundColor Cyan
$PriceUrl = "https://data.alpaca.markets/v1beta3/crypto/us/latest/quotes?symbols=BTC%2FUSD"
try {
    $Price = Invoke-RestMethod -Uri $PriceUrl -Headers $Headers
    $Quote = $Price.quotes."BTC/USD"
    [PSCustomObject]@{
        BidPrice  = "$" + $Quote.bp
        AskPrice  = "$" + $Quote.ap
        Timestamp = $Quote.t
    } | Format-List
}
catch {
    Write-Host "Price fetch error: $_" -ForegroundColor Red
}

# --- Scrub credentials from memory ---
$ApiKey    = $null
$ApiSecret = $null
$Headers   = $null

Write-Host "=== SANITY CHECK COMPLETE ===" -ForegroundColor Green
