@echo off
title Trader Dashboard Pro Terminal
echo ===================================================
echo     Launching Trader Dashboard (Laptop & Mobile)
echo ===================================================
echo.

python -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Streamlit start failed. Checking if Python or dependencies are installed...
    echo Trying with py launcher:
    py -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501
)

pause
