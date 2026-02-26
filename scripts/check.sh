#!/usr/bin/env bash

set -e # Exit on error

# ANSI color codes
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}Starting Local CI/CD Checks...${NC}"

# 1. Linting & Formatting
echo -e "\n${YELLOW}[1/5] Running Ruff Check...${NC}"
python -m ruff check scripts/ tests/ || { echo -e "${RED}Ruff Check failed!${NC}"; exit 1; }

echo -e "\n${YELLOW}[2/5] Running Ruff Format...${NC}"
python -m ruff format --check scripts/ tests/ || { echo -e "${RED}Ruff Format failed!${NC}"; exit 1; }

# 2. Unit Tests
echo -e "\n${YELLOW}[3/5] Running Unit Tests...${NC}"
python -m pytest || { echo -e "${RED}Unit Tests failed!${NC}"; exit 1; }

# 3. Validation
echo -e "\n${YELLOW}[4/5] Running Integrity Validation...${NC}"
python scripts/validate_integrity.py || { echo -e "${RED}Integrity Validation failed!${NC}"; exit 1; }

echo -e "\n${YELLOW}[5/5] Running Strictness Verification...${NC}"
python scripts/verify_strictness.py || { echo -e "${RED}Strictness Verification failed!${NC}"; exit 1; }

echo -e "\n${GREEN}All checks passed successfully!${NC}"
