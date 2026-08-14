@echo off
rem Сборка standalone-дистрибутива gostdoc.exe (Windows)
setlocal
cd /d %~dp0

python -m pip install pyinstaller -q
python -m pyinstaller --noconfirm --clean gostdoc.spec

echo.
echo Готово: dist\gostdoc.exe
echo Тест: dist\gostdoc.exe --version
endlocal
