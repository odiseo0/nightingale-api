param(
    [ValidateSet('Start', 'Stop')]
    [string]$Action = 'Start',
    [ValidateSet('Development', 'Test')]
    [string]$Mode = 'Test',
    [string]$PostgresBin = 'C:\Program Files\PostgreSQL\18\bin'
)

$ErrorActionPreference = 'Stop'
$repository = Split-Path $PSScriptRoot -Parent
$directory = Join-Path $repository ".tmp/test-services/postgres-$($Mode.ToLowerInvariant())"
$dataDirectory = Join-Path $directory 'data'
$port = if ($Mode -eq 'Test') { 55433 } else { 55432 }
$pgCtl = Join-Path $PostgresBin 'pg_ctl.exe'

if (-not (Test-Path -LiteralPath $pgCtl)) {
    throw "PostgreSQL 18 tools not found in $PostgresBin"
}

if ($Action -eq 'Stop') {
    if (Test-Path -LiteralPath (Join-Path $dataDirectory 'postmaster.pid')) {
        & $pgCtl stop -D $dataDirectory -m fast -w -t 30
        if ($LASTEXITCODE -ne 0) { throw 'Could not stop the isolated PostgreSQL process' }
    }
    return
}

New-Item -ItemType Directory -Force $directory | Out-Null

if (-not (Test-Path -LiteralPath (Join-Path $dataDirectory 'PG_VERSION'))) {
    # This public fixture password belongs only to the isolated loopback cluster.
    $passwordFile = Join-Path $directory 'fixture-password.txt'
    [IO.File]::WriteAllText($passwordFile, 'Fixture-postgres-only-2026!')
    & (Join-Path $PostgresBin 'initdb.exe') -D $dataDirectory -U nightingale_fixture `
        --pwfile=$passwordFile --auth=scram-sha-256 --encoding=UTF8 --no-locale
    if ($LASTEXITCODE -ne 0) { throw 'Could not initialize the isolated PostgreSQL cluster' }
}

$version = (Get-Content -LiteralPath (Join-Path $dataDirectory 'PG_VERSION')).Trim()
if ($version -ne '18') { throw "Expected PostgreSQL 18 data, found $version" }

if (Test-Path -LiteralPath (Join-Path $dataDirectory 'postmaster.pid')) {
    throw 'This cluster has a process marker. Stop it or check its status before starting it again.'
}

# Bind only to loopback. These ports never use the personal PostgreSQL service.
# https://www.postgresql.org/docs/18/app-pg-ctl.html
& $pgCtl start -D $dataDirectory -l (Join-Path $directory 'postgres.log') `
    -o "-h 127.0.0.1 -p $port" -w -t 30
if ($LASTEXITCODE -ne 0) { throw 'Could not start the isolated PostgreSQL cluster' }

Write-Output "PostgreSQL ${Mode}: 127.0.0.1:$port; user nightingale_fixture; database postgres"
