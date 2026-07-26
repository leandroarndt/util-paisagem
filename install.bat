echo OFF
echo "Creating virtual environment..."
py -m venv .env

echo "Activating virtual environment..."
call .env\Scripts\activate.bat

echo "Installing required Python modules..."
pip install -r requirements.txt

echo "Compiling translations..."
pybabel compile -D utilpaisagem -d resources/locale

echo "Creating shortcut..."
python shortcut.py

echo ""
echo "Installation successful."
echo "Run Útil paisagem using the application shortcut."