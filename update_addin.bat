@echo off
setlocal

set "ADDINS=%AppData%\Autodesk\Autodesk Fusion 360\API\AddIns"
set "REPO=https://github.com/AnhDuck/QuickSTL.git"
set "BRANCH=codex/implement-auto-close-and-debug-improvements"

if not exist "%ADDINS%" (
  echo AddIns folder not found: %ADDINS%
  exit /b 1
)

cd /d "%ADDINS%"
if not exist "QuickSTL" (
  git clone "%REPO%" QuickSTL
)

cd /d "%ADDINS%\QuickSTL"
git fetch --all
git checkout "%BRANCH%"
git pull

echo Updated QuickSTL add-in.
pause
