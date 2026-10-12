@echo off
setlocal
set "PROYECTO=C:\Users\Nitropc\Carpeta Principal\Proyectos Programacion\Maria 4.0"
set "PYTHON=C:\Users\Nitropc\AppData\Local\Programs\Python\Python312\python.exe"

cd /d "%PROYECTO%"
"%PYTHON%" "%PROYECTO%\stream_deck\stream_deck.py" "FINANZAS"
endlocal