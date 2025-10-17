#!/bin/bash

# ============================================
#   DISCORD GUILD MANAGER - MAC/LINUX LAUNCHER
# ============================================

echo ""
echo "============================================"
echo "   DISCORD GUILD MANAGER"
echo "============================================"
echo ""

# --- CHECK PYTHON ---
echo "[1/4] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo ""
    echo "======================================"
    echo "   ERROR: Python not found!"
    echo "======================================"
    echo ""
    echo "Python 3.8+ is required to run this script."
    echo ""
    echo "Install Python:"
    echo "  macOS:  brew install python3"
    echo "          or download from https://www.python.org/downloads/"
    echo "  Linux:  sudo apt install python3 python3-venv"
    echo "          (Ubuntu/Debian)"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "      Python $PYTHON_VERSION found"

# --- CHECK/CREATE VIRTUAL ENVIRONMENT ---
echo "[2/4] Checking virtual environment..."
if [ ! -d "venv" ]; then
    echo "      Virtual environment not found"
    echo "      Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "      ERROR: Failed to create virtual environment!"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "      Virtual environment created successfully"
else
    echo "      Virtual environment found"
fi

# --- ACTIVATE VIRTUAL ENVIRONMENT ---
echo "[3/4] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "      ERROR: Failed to activate virtual environment!"
    read -p "Press Enter to exit..."
    exit 1
fi

# --- CHECK/INSTALL DEPENDENCIES ---
echo "[4/4] Checking dependencies..."

REINSTALL=0

# Check if .installed marker exists
if [ -f ".installed" ]; then
    # Get current requirements hash
    if command -v md5sum &> /dev/null; then
        CURRENT_HASH=$(md5sum requirements.txt | awk '{print $1}')
    else
        # macOS uses md5 instead of md5sum
        CURRENT_HASH=$(md5 -q requirements.txt)
    fi
    
    # Get stored hash
    STORED_HASH=$(cat .installed 2>/dev/null)
    
    # Compare hashes
    if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
        echo "      Requirements changed, reinstalling dependencies..."
        REINSTALL=1
    else
        echo "      Dependencies already installed"
    fi
else
    echo "      First run detected, installing dependencies..."
    REINSTALL=1
fi

# Install dependencies if needed
if [ $REINSTALL -eq 1 ]; then
    echo "      Installing dependencies..."
    pip install -q -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "      ERROR: Failed to install dependencies!"
        echo "      Try running: pip install -r requirements.txt"
        read -p "Press Enter to exit..."
        exit 1
    fi
    
    # Save requirements hash
    if command -v md5sum &> /dev/null; then
        md5sum requirements.txt | awk '{print $1}' > .installed
    else
        md5 -q requirements.txt > .installed
    fi
    
    echo "      Dependencies installed successfully"
fi

echo ""
echo "============================================"
echo "   STARTING DISCORD GUILD MANAGER"
echo "============================================"
echo ""

# --- RUN MAIN SCRIPT ---
python main.py

# --- COMPLETION ---
echo ""
echo "============================================"
echo "   Script completed"
echo "   Press Enter to exit..."
echo "============================================"
read -r