$ErrorActionPreference = "Stop"

Write-Host "Starting Local CI/CD Checks..." -ForegroundColor Cyan

# 1. Linting & Formatting
Write-Host "`n[1/5] Running Ruff Check..." -ForegroundColor Yellow
python -m ruff check scripts/ tests/
if ($LASTEXITCODE -ne 0) { Write-Error "Ruff Check failed!" }

Write-Host "`n[2/5] Running Ruff Format..." -ForegroundColor Yellow
python -m ruff format --check scripts/ tests/
if ($LASTEXITCODE -ne 0) { Write-Error "Ruff Format failed!" }

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
