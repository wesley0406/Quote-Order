@echo off
set PYTHON_EXEC=python
set SCRIPT_DIR=%CD%
set NN_SCRIPT=NN_Structure_AdamW_PKR.py
set PREDICT_SCRIPT=Predict.py
set LOG_FILE=execution_log.txt



if not exist "%SCRIPT_DIR%\%NN_SCRIPT%" (
    echo %DATE% %TIME% - ERROR: %NN_SCRIPT% not found. >> %LOG_FILE%
    exit /b 1
)

if not exist "%SCRIPT_DIR%\%PREDICT_SCRIPT%" (
    echo %DATE% %TIME% - ERROR: %PREDICT_SCRIPT% not found. >> %LOG_FILE%
    exit /b 1
)

echo %DATE% %TIME% - Running %NN_SCRIPT%... >> %LOG_FILE%
%PYTHON_EXEC% "%SCRIPT_DIR%\%NN_SCRIPT%" >> %LOG_FILE% 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %DATE% %TIME% - ERROR: %NN_SCRIPT% failed. >> %LOG_FILE%
    exit /b 1
)
echo %DATE% %TIME% - %NN_SCRIPT% completed successfully. >> %LOG_FILE%

echo %DATE% %TIME% - Running %PREDICT_SCRIPT%... >> %LOG_FILE%
%PYTHON_EXEC% "%SCRIPT_DIR%\%PREDICT_SCRIPT%" >> %LOG_FILE% 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %DATE% %TIME% - ERROR: %PREDICT_SCRIPT% failed. >> %LOG_FILE%
    exit /b 1
)
echo %DATE% %TIME% - %PREDICT_SCRIPT% completed successfully. >> %LOG_FILE%

echo %DATE% %TIME% - All scripts executed successfully. >> %LOG_FILE%