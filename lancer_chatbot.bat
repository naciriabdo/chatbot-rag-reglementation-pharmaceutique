@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo L'installation n'a pas encore ete faite : lancez d'abord installer.bat
  pause & exit /b 1
)
call .venv\Scripts\activate.bat
echo Le chatbot s'ouvre dans votre navigateur (http://localhost:8501).
echo Pour l'arreter : fermez cette fenetre ou appuyez sur Ctrl+C.
streamlit run app.py
pause
