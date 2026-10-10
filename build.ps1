# Builds a single portable dist\MarkItDownDrop.exe
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
.\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
# PyInstaller logs progress to stderr; Windows PowerShell 5.1 would treat that as an error.
$ErrorActionPreference = "Continue"
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name MarkItDownDrop --paths . `
    --collect-all customtkinter --collect-all tkinterdnd2 `
    --collect-all markitdown --collect-all magika `
    app\main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
Write-Host "Built: $PSScriptRoot\dist\MarkItDownDrop.exe"
