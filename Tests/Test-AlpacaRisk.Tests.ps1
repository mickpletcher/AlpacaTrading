#Requires -Version 5.1
<#
.SYNOPSIS
    Pester tests for the Alpaca.Risk module.

.DESCRIPTION
    Tests risk limits enforcement, kill switch, daily loss tracking,
    duplicate order prevention, and client order ID generation.
    No API calls are made.
#>

$global:TradingTestRepoRoot = Split-Path $PSScriptRoot -Parent
Import-Module (Join-Path $global:TradingTestRepoRoot 'src\Alpaca.Config\Alpaca.Config.psd1') -Force
Import-Module (Join-Path $global:TradingTestRepoRoot 'src\Alpaca.Auth\Alpaca.Auth.psd1') -Force
Import-Module (Join-Path $global:TradingTestRepoRoot 'src\Alpaca.Risk\Alpaca.Risk.psd1') -Force

Describe 'Initialize-AlpacaRisk' {
    BeforeAll {
        $env:ALPACA_API_KEY = 'TEST-API-KEY-001'
        $env:ALPACA_SECRET_KEY = 'TEST-SECRET-001'
        Initialize-AlpacaConfig -EnvFilePath 'C:\nonexistent\.env' | Out-Null
    }

    It 'Returns a config object with supplied limits' {
        $rc = Initialize-AlpacaRisk -MaxPositionValue 2500 -MaxShares 25 -MaxDailyLoss 250
        $rc.MaxPositionValue | Should -Be 2500
        $rc.MaxShares | Should -Be 25
        $rc.MaxDailyLoss | Should -Be 250
    }

    It 'Returns a config object with defaults when no params given' {
        $rc = Initialize-AlpacaRisk
        $rc.MaxPositionValue | Should -Be 10000
        $rc.MaxShares | Should -Be 500
        $rc.MaxDailyLoss | Should -Be 1000
    }

    It 'Throws when MaxPositionValue is below minimum' {
        { Initialize-AlpacaRisk -MaxPositionValue 0 } | Should -Throw
    }
}

Describe 'New-AlpacaClientOrderId' {
    BeforeAll {
        $env:ALPACA_API_KEY = 'TEST-API-KEY-001'
        $env:ALPACA_SECRET_KEY = 'TEST-SECRET-001'
        Initialize-AlpacaConfig -EnvFilePath 'C:\nonexistent\.env' | Out-Null
    }

    It 'Returns a non-empty string' {
        $id = New-AlpacaClientOrderId -Strategy 'ema' -Symbol 'AAPL' -Side 'buy'
        $id | Should -Not -BeNullOrEmpty
    }

    It 'Is deterministic within the same minute' {
        $id1 = New-AlpacaClientOrderId -Strategy 'ema' -Symbol 'AAPL' -Side 'buy'
        $id2 = New-AlpacaClientOrderId -Strategy 'ema' -Symbol 'AAPL' -Side 'buy'
        $id1 | Should -Be $id2
    }

    It 'Differs for different sides' {
        $buy  = New-AlpacaClientOrderId -Strategy 'ema' -Symbol 'AAPL' -Side 'buy'
        $sell = New-AlpacaClientOrderId -Strategy 'ema' -Symbol 'AAPL' -Side 'sell'
        $buy | Should -Not -Be $sell
    }

    It 'Differs for different symbols' {
        $aapl = New-AlpacaClientOrderId -Strategy 'ema' -Symbol 'AAPL' -Side 'buy'
        $msft = New-AlpacaClientOrderId -Strategy 'ema' -Symbol 'MSFT' -Side 'buy'
        $aapl | Should -Not -Be $msft
    }

    It 'Strips slashes from crypto pairs' {
        $id = New-AlpacaClientOrderId -Strategy 'crypto' -Symbol 'BTC/USD' -Side 'buy'
        $id | Should -Not -Match '/'
    }

    It 'Does not exceed 128 characters' {
        $longStrategy = 'a' * 100
        $id = New-AlpacaClientOrderId -Strategy $longStrategy -Symbol 'AAPL' -Side 'buy'
        ($id.Length -le 128) | Should -Be $true
    }
}

Describe 'Test-AlpacaDuplicateOrder and Register-AlpacaOrderSent' {
    BeforeAll {
        $env:ALPACA_API_KEY = 'TEST-API-KEY-001'
        $env:ALPACA_SECRET_KEY = 'TEST-SECRET-001'
        Initialize-AlpacaConfig -EnvFilePath 'C:\nonexistent\.env' | Out-Null
    }

    It 'Returns false for an ID that has never been registered' {
        Initialize-AlpacaRisk | Out-Null
        $id = 'test-dup-check-' + [guid]::NewGuid().ToString()
        Test-AlpacaDuplicateOrder -ClientOrderId $id | Should -Be $false
    }

    It 'Returns true after the same ID is registered' {
        Initialize-AlpacaRisk | Out-Null
        $id = 'test-dup-register-' + [guid]::NewGuid().ToString()
        Register-AlpacaOrderSent -ClientOrderId $id
        Test-AlpacaDuplicateOrder -ClientOrderId $id | Should -Be $true
    }

    It 'Returns false for a different ID even after registration' {
        Initialize-AlpacaRisk | Out-Null
        $id1 = 'dup-id-1-' + [guid]::NewGuid().ToString()
        $id2 = 'dup-id-2-' + [guid]::NewGuid().ToString()
        Register-AlpacaOrderSent -ClientOrderId $id1
        Test-AlpacaDuplicateOrder -ClientOrderId $id2 | Should -Be $false
    }
}

Describe 'Kill Switch' {
    BeforeAll {
        $env:ALPACA_API_KEY = 'TEST-API-KEY-001'
        $env:ALPACA_SECRET_KEY = 'TEST-SECRET-001'
        Initialize-AlpacaConfig -EnvFilePath 'C:\nonexistent\.env' | Out-Null
    }

    BeforeEach {
        Reset-AlpacaKillSwitch -Confirm:$false
    }

    AfterEach {
        Reset-AlpacaKillSwitch -Confirm:$false
    }

    It 'Is inactive at start' {
        Test-AlpacaKillSwitch | Should -Be $false
    }

    It 'Becomes active after Invoke-AlpacaKillSwitch' {
        Invoke-AlpacaKillSwitch -Reason 'Unit test activation'
        Test-AlpacaKillSwitch | Should -Be $true
    }

    It 'Is cleared by Reset-AlpacaKillSwitch' {
        Invoke-AlpacaKillSwitch -Reason 'Unit test'
        Reset-AlpacaKillSwitch -Confirm:$false
        Test-AlpacaKillSwitch | Should -Be $false
    }
}

Describe 'Test-AlpacaOrderRisk' {
    BeforeAll {
        $env:ALPACA_API_KEY = 'TEST-API-KEY-001'
        $env:ALPACA_SECRET_KEY = 'TEST-SECRET-001'
        Initialize-AlpacaConfig -EnvFilePath 'C:\nonexistent\.env' | Out-Null
    }

    BeforeEach {
        Initialize-AlpacaRisk -MaxPositionValue 1000 -MaxShares 10 -MaxDailyLoss 200 | Out-Null
        Reset-AlpacaKillSwitch -Confirm:$false
        $riskStatePath = Join-Path $global:TradingTestRepoRoot 'Journal\alpaca_risk_state.json'
        @'
{
  "daily_loss_date": "",
  "kill_switch_active": false,
  "daily_loss": 0.0
}
'@ | Set-Content -Path $riskStatePath -Encoding UTF8
    }

    AfterEach {
        Reset-AlpacaKillSwitch -Confirm:$false
    }

    It 'Returns true for a valid order within limits' {
        $result = Test-AlpacaOrderRisk -Symbol 'AAPL' -Side 'buy' -Qty 5 -EstimatedPrice 150
        $result | Should -Be $true
    }

    It 'Throws when order qty exceeds MaxShares' {
        { Test-AlpacaOrderRisk -Symbol 'AAPL' -Side 'buy' -Qty 11 -EstimatedPrice 50 } | Should -Throw
    }

    It 'Throws when notional exceeds MaxPositionValue' {
        { Test-AlpacaOrderRisk -Symbol 'AAPL' -Side 'buy' -Qty 5 -EstimatedPrice 250 } | Should -Throw
    }

    It 'Throws when kill switch is active' {
        Invoke-AlpacaKillSwitch -Reason 'Test'
        { Test-AlpacaOrderRisk -Symbol 'AAPL' -Side 'buy' -Qty 1 -EstimatedPrice 100 } | Should -Throw
    }

    It 'Throws when daily loss limit is reached' {
        Add-AlpacaDailyLoss -AmountLost 201
        { Test-AlpacaOrderRisk -Symbol 'AAPL' -Side 'buy' -Qty 1 -EstimatedPrice 100 } | Should -Throw
    }
}

Describe 'Daily Loss Tracking' {
    BeforeAll {
        $env:ALPACA_API_KEY = 'TEST-API-KEY-001'
        $env:ALPACA_SECRET_KEY = 'TEST-SECRET-001'
        Initialize-AlpacaConfig -EnvFilePath 'C:\nonexistent\.env' | Out-Null
    }

    BeforeEach {
        $riskStatePath = Join-Path $global:TradingTestRepoRoot 'Journal\alpaca_risk_state.json'
        @'
{
  "daily_loss_date": "",
  "kill_switch_active": false,
  "daily_loss": 0.0
}
'@ | Set-Content -Path $riskStatePath -Encoding UTF8
    }

    It 'Returns 0 before any losses are recorded today' {
        $loss = Get-AlpacaDailyLoss
        $loss | Should -Be 0
    }

    It 'Accumulates losses across multiple Add-AlpacaDailyLoss calls' {
        $before = Get-AlpacaDailyLoss
        Add-AlpacaDailyLoss -AmountLost 10
        Add-AlpacaDailyLoss -AmountLost 15
        $after = Get-AlpacaDailyLoss
        ($after - $before) | Should -Be 25
    }
}
