@echo off
REM TSS Converter Web App Launcher for Windows
REM Run this script to start the Streamlit web application

echo 🚀 Starting TSS Converter Web App...

REM Check if streamlit is installed
streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Streamlit is not installed. Installing...
    pip install -r requirements.txt
)

REM Create temp directories if they don't exist
if not exist "temp\uploads" mkdir temp\uploads
if not exist "temp\outputs" mkdir temp\outputs

REM Set environment variables
set STREAMLIT_ENV=development

REM Launch Streamlit app
echo 📊 Launching web application...
echo 🌐 Access the app at: http://localhost:8501
echo ⏹️  Press Ctrl+C to stop the server
echo.

streamlit run app.py ^
    --server.port 8501 ^
    --server.address localhost ^
    --browser.gatherUsageStats false ^
    --theme.primaryColor "#FF6B6B" ^
    --theme.backgroundColor "#FFFFFF" ^
    --theme.secondaryBackgroundColor "#F0F2F6"

pause