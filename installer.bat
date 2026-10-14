@echo off
chcp 65001 >nul
echo ============================================================
echo   Installation du chatbot de reglementation pharmaceutique
echo ============================================================
cd /d "%~dp0"

echo [1/3] Creation de l'environnement Python (.venv)...
py -3.12 -m venv .venv || python -m venv .venv
if errorlevel 1 (
  echo ERREUR : Python n'est pas installe ou pas dans le PATH. Voir l'etape 2 du guide.
  pause & exit /b 1
)

echo [2/3] Mise a jour de pip...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo [3/3] Installation des bibliotheques (quelques minutes)...
pip install -r requirements.txt
if errorlevel 1 (
  echo ERREUR pendant l'installation. Voir la section Depannage du guide.
  pause & exit /b 1
)

echo.
echo Installation terminee. Lancez maintenant : lancer_chatbot.bat
pause
