REM Execute from the repository's base dir

.freeze\scripts\pyinstaller.exe utilpaisagem-windows.spec
move dist\utilpaisagem-windows\_internal\LICENSE dist\utilpaisagem-windows
move dist\utilpaisagem-windows\_internal\README.md dist\utilpaisagem-windows
"c:\Program Files (x86)\NSIS\makensis.exe" utilpaisagem.nsi
rmdir /s /q build\utilpaisagem-windows
rmdir /s /q dist\utilpaisagem-windows
