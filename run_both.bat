@echo off
chcp 65001 >nul
pushd "%~dp0"

echo ========================================
echo  Acoustic Simulation - Dual App Launcher
echo ========================================

start "Acoustic Simulator" cmd /k streamlit run app.py --server.port 8501
start "RNN Spectrum App" cmd /k streamlit run dl_spectrum_rnn_app.py --server.port 8502

echo.
echo [1] app.py                 : http://localhost:8501
echo [2] dl_spectrum_rnn_app.py : http://localhost:8502
echo.
pause
