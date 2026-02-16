$ErrorActionPreference = "Stop"

Write-Host "Starting Local CI/CD Checks..." -ForegroundColor Cyan

# 1. Linting
Write-Host "`n[1/5] Running Flake8..." -ForegroundColor Yellow
python -m flake8 scripts/ api/ tests/
if ($LASTEXITCODE -ne 0) { Write-Error "Flake8 failed!" }

Write-Host "`n[2/5] Running Pylint..." -ForegroundColor Yellow
python -m pylint scripts/ api/ tests/
if ($LASTEXITCODE -ne 0) { Write-Error "Pylint failed!" }

# 2. Unit Tests
Write-Host "`n[3/5] Running Unit Tests..." -ForegroundColor Yellow
python -m pytest
if ($LASTEXITCODE -ne 0) { Write-Error "Unit Tests failed!" }

# 3. Validation
Write-Host "`n[4/5] Running Integrity Validation..." -ForegroundColor Yellow
python scripts/validate_integrity.py
if ($LASTEXITCODE -ne 0) { Write-Error "Integrity Validation failed!" }

Write-Host "`n[5/5] Running Strictness Verification..." -ForegroundColor Yellow
python scripts/verify_strictness.py
if ($LASTEXITCODE -ne 0) { Write-Error "Strictness Verification failed!" }

Write-Host "`nAll checks passed successfully!" -ForegroundColor Green
