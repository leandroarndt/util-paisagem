@ECHO OFF

SET "ARG1=%1"
REM SET "PYTHON=PY"

IF "%ARG1%"=="" (
    set "PYTHON=py"
)
IF "%ARG1%"=="-h" (
    ECHO Usage: install.bat [--help]
    ECHO Installs the application and its dependencies.
    ECHO.
    ECHO Options:
    ECHO   --help      Show this help message and exit.
    EXIT /B 0
)
IF "%ARG1%"=="-p" (
    SET "PYTHON=%~2"
)

ECHO Creating virtual environment...
%PYTHON% -m venv .env

ECHO Activating virtual environment...
call .env\Scripts\activate.bat

ECHO Installing required Python modules...
pip install -r requirements.txt

ECHO Compiling translations...
pybabel compile -D utilpaisagem -d resources/locale

ECHO Creating shortcut...
%~dp0\.env\Scripts\python.exe %~dp0\shortcut.py

ECHO.
ECHO Run Util paisagem using the application shortcut.
