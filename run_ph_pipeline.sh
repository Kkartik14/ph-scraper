#!/bin/bash

# Product Hunt Analytics Pipeline
# This script launches the Streamlit app for data collection, analysis, and visualization

echo "========================================"
echo "Product Hunt Analytics Pipeline"
echo "========================================"
echo

# Check for Python environment
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is required but not found. Please install Python 3."
    exit 1
fi

# Check for required packages
echo "Checking dependencies..."
python3 -m pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file template..."
    echo "# Product Hunt API Credentials" > .env
    echo "PH_CLIENT_ID=your_client_id_here" >> .env
    echo "PH_CLIENT_SECRET=your_client_secret_here" >> .env
    echo "" >> .env
    echo "# Groq API Key for LLM Analysis" >> .env
    echo "GROQ_API_KEY=your_groq_api_key_here" >> .env
    
    echo "Warning: Please edit the .env file with your actual API credentials."
    read -p "Would you like to continue without credentials? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please edit .env file and run again."
        exit 1
    fi
fi

# Launch the Streamlit app
echo
echo "========================================"
echo "Launching Product Hunt Trends Dashboard"
echo "========================================"
echo "Starting Streamlit app at http://localhost:8501"
echo "Use the web interface to collect data, view the raw CSV, and analyze trends."
echo "========================================"
streamlit run streamlit_app.py

echo
echo "Streamlit app stopped." 