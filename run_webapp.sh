#!/bin/bash
# TSS Converter Web App Launcher
# Run this script to start the Streamlit web application

echo "🚀 Starting TSS Converter Web App..."

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit is not installed. Installing..."
    pip install -r requirements.txt
fi

# Create temp directories if they don't exist
mkdir -p temp/uploads temp/outputs

# Set environment variables
export STREAMLIT_ENV=development

# Launch Streamlit app
echo "📊 Launching web application..."
echo "🌐 Access the app at: http://localhost:8501"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

streamlit run app.py \
    --server.port 8501 \
    --server.address localhost \
    --browser.gatherUsageStats false \
    --theme.primaryColor "#FF6B6B" \
    --theme.backgroundColor "#FFFFFF" \
    --theme.secondaryBackgroundColor "#F0F2F6"