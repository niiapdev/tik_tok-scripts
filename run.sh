#!/bin/bash
# TikTok Video Generator - Linux/macOS Launcher
# This script runs the generator from the current directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_error() {
    echo -e "${RED}[!] $1${NC}" >&2
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_info() {
    echo -e "${GREEN}[*] $1${NC}"
}

# Determine Python command
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found in PATH."
    print_error "Please install Python 3.10+ and ensure 'python3' or 'python' is in PATH."
    exit 1
fi

# Check Python version
PY_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    print_warning "Python 3.10+ recommended. Found Python $PY_VERSION. May work but not officially supported."
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    print_error "main.py not found in current directory."
    print_error "Please run this script from the project directory containing main.py"
    exit 1
fi

# Run the generator
print_info "Starting TikTok Video Generator..."
echo
$PYTHON_CMD main.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo
    print_error "Program exited with code $EXIT_CODE."
fi

exit $EXIT_CODE