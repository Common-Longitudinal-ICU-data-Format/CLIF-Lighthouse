#!/bin/bash

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 could not be found. Please install it first."
    exit
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv .clif_lighthouse

# Activate virtual environment
echo "Activating virtual environment..."
source .clif_lighthouse/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt


