@echo off
chcp 65001 >nul
cls
echo.
echo ==================================================
echo         Запуск LeakHunter v37.2
echo ==================================================
echo.

:: Проверка версии Windows
ver | findstr /i "10\.0" >nul
if %errorlevel%==0 (
    set IS_WIN10=1
) else (
    set IS_WIN10=0
)

:: Проверка Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python найден
) else (
    echo [ERROR] Python не найден или не добавлен в PATH!
    echo Установите Python с https://www.python.org/downloads/
    echo Обязательно поставьте галочку "Add Python to PATH"
    pause
    exit /b 1
)

:: Создание .venv, если нет
if not exist ".venv" (
    echo Создаём виртуальное окружение .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Не удалось создать .venv
        pause
        exit /b 1
    )
)

:: Активация venv
echo Активация виртуального окружения...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Не удалось активировать .venv
    pause
    exit /b 1
)

:: Обновление pip
echo Обновляем pip...
python -m pip install --upgrade pip >nul

:: Установка зависимостей (с prompt-toolkit)
echo Установка зависимостей (rich, requests, beautifulsoup4, fake-useragent, prompt-toolkit)...
pip install rich requests beautifulsoup4 fake-useragent prompt-toolkit >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Проблема с установкой — принудительная переустановка...
    pip install --force-reinstall --no-cache-dir rich requests beautifulsoup4 fake-useragent prompt-toolkit >nul 2>&1
)

echo [OK] Все зависимости готовы!

:: Запуск через Windows Terminal, если есть
where wt.exe >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Windows Terminal найден — лучший вид и кликабельные ссылки!
    echo.
    echo ==================================================
    echo               LeakHunter запускается...
    echo ==================================================
    echo.
    wt.exe -w 0 nt -- python main.py
    goto :finish
)

:: Если нет Terminal — предложение установить (только Win10)
if %IS_WIN10%==1 (
    echo.
    echo [ВНИМАНИЕ] Windows Terminal не найден
    echo → Ссылки не будут кликабельными
    echo → Но программа и автодополнение работают!
    echo.
    choice /c ДН /n /m "Установить Windows Terminal сейчас? (Д=Да, Н=Нет): "
    if errorlevel 1 (
        echo.
        echo Открываем Microsoft Store...
        start ms-windows-store://pdp/?ProductId=9N0DX20HK701
        echo После установки перезапустите .bat
        timeout /t 5 >nul
    )
)

:: Запуск в обычной консоли
echo.
echo ==================================================
echo               LeakHunter запускается...
echo ==================================================
echo.
python main.py

:finish
echo.
echo ==================================================
if %errorlevel% == 0 (
    echo   LeakHunter завершил работу успешно
) else (
    echo   [ERROR] Программа завершилась с ошибкой (код %errorlevel%)
    echo   Прочитайте сообщение выше
)
echo ==================================================
echo Нажмите любую клавишу для закрытия окна...
pause >nul
exit /b