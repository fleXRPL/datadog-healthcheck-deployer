#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${YELLOW}Starting local environment setup...${NC}\n"

# Function to run a command and check its status
run_check() {
    echo -e "${YELLOW}Running $1...${NC}"
    if eval "$2"; then
        echo -e "${GREEN}✓ $1 passed${NC}\n"
    else
        echo -e "${RED}✗ $1 failed${NC}\n"
        exit 1
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}\n"
else
    echo -e "${RED}Python 3 not found. Please install Python 3.9 or higher${NC}\n"
    exit 1
fi

# Create and activate virtual environment
echo -e "${YELLOW}Setting up virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Found existing virtual environment. Removing...${NC}"
    rm -rf venv
fi

run_check "Creating virtual environment" "python3 -m venv venv"
source venv/bin/activate

# Upgrade pip and install dependencies
run_check "Upgrading pip" "python -m pip install --upgrade pip"
run_check "Installing development dependencies" "pip install -r requirements-dev.txt"
run_check "Installing package in editable mode" "pip install -e ."

# Set up pre-commit hooks
run_check "Setting up pre-commit hooks" "pre-commit install"

# Create config directory if it doesn't exist
if [ ! -d "config" ]; then
    echo -e "${YELLOW}Creating config directory...${NC}"
    mkdir -p config
fi

# Check for DataDog credentials
echo -e "${YELLOW}Checking DataDog credentials...${NC}"
if [ -z "${DD_API_KEY}" ] || [ -z "${DD_APP_KEY}" ]; then
    echo -e "${YELLOW}DataDog credentials not found in environment.${NC}"
    echo -e "${YELLOW}Please set up your credentials by running:${NC}"
    echo -e "export DD_API_KEY='your-api-key'"
    echo -e "export DD_APP_KEY='your-app-key'"
    echo -e "\n${YELLOW}You can add these to your ~/.bashrc or ~/.zshrc for persistence${NC}"
fi

# Create example configuration if it doesn't exist
if [ ! -f "config/healthcheck.yaml" ]; then
    echo -e "${YELLOW}Creating example health check configuration...${NC}"
    cat > config/healthcheck.yaml << EOL
version: "1.0"
healthchecks:
  - name: "Example API Check"
    type: "http"
    url: "https://api.example.com/health"
    frequency: 60
    locations:
      - "aws:us-east-1"
    monitors:
      availability:
        enabled: true
        threshold: 99.9
      latency:
        enabled: true
        threshold: 500
    tags:
      - "env:production"
      - "service:api"
EOL
    echo -e "${GREEN}✓ Created example configuration${NC}\n"
fi

echo -e "${GREEN}Local environment setup complete!${NC}\n"
echo -e "Next steps:"
echo -e "1. Set up your DataDog credentials if you haven't already"
echo -e "2. Review and modify config/healthcheck.yaml"
echo -e "3. Run 'dd-healthcheck deploy config/healthcheck.yaml' to deploy your first health check"
echo -e "\nFor more information, visit: https://github.com/fleXRPL/datadog-healthcheck-deployer/wiki/Getting-Started" 