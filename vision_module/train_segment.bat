@echo off
setlocal
cd /d "%~dp0"

REM Uses the currently active Python environment.
python train_model.py

