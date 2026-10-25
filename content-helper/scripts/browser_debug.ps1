param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('brave', 'chrome', 'edge')]
  [string]$Browser,
  [int]$Port = 9223,
  [switch]$Stop,
  [switch]$KeepOpen
)

$ErrorActionPreference = 'Stop'

$processName = @{ brave = 'brave'; chrome = 'chrome'; edge = 'msedge' }[$Browser]
$candidates = @{
  brave = @(
    "$env:ProgramFiles\BraveSoftware\Brave-Browser\Application\brave.exe",
    "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe"
  )
  chrome = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
  )
  edge = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
  )
}

function Test-Port {
  try {
    $null = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/json/version" -UseBasicParsing -TimeoutSec 3
    return $true
  } catch { return $false }
}

function Stop-Browser {
  $procs = @(Get-Process -Name $processName -ErrorAction SilentlyContinue)
  if ($procs.Count -eq 0) { return }
  foreach ($proc in $procs) { $proc.CloseMainWindow() | Out-Null }
  $deadline = (Get-Date).AddSeconds(25)
  while ((Get-Date) -lt $deadline) {
    if (-not (Get-Process -Name $processName -ErrorAction SilentlyContinue)) { return }
    Start-Sleep -Milliseconds 500
  }
  Get-Process -Name $processName -ErrorAction SilentlyContinue | Stop-Process -Force
  Start-Sleep -Seconds 2
}

if ($Stop) {
  Stop-Browser
  Write-Output "closed $Browser"
  exit 0
}

if (Test-Port) {
  Write-Output "port $Port already serving DevTools"
  exit 0
}

$exe = $candidates[$Browser] | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $exe) {
  Write-Output "could not find $Browser"
  exit 1
}

Stop-Browser

Start-Process -FilePath $exe -ArgumentList @(
  "--remote-debugging-port=$Port",
  '--restore-last-session',
  '--no-first-run',
  '--no-default-browser-check'
)

$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
  if (Test-Port) {
    Write-Output "$Browser listening on $Port"
    exit 0
  }
  Start-Sleep -Milliseconds 500
}

Write-Output "$Browser did not open a debug port"
exit 1
