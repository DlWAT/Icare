$ErrorActionPreference = 'Stop'

# Build a standalone Windows executable (no Python needed on target PC).
# Output: dist\IcareWeb.exe

Set-Location -Path $PSScriptRoot

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

if (Test-Path -Path .\build) { Remove-Item -Recurse -Force .\build }
if (Test-Path -Path .\dist)  { Remove-Item -Recurse -Force .\dist }

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name IcareWeb `
  --add-data "webapp\templates;webapp\templates" `
  --add-data "webapp\static;webapp\static" `
  --add-data "Sequences;Sequences" `
  --hidden-import pydmxIcare `
  --hidden-import pydmxlight `
  --hidden-import webapp.config `
  --hidden-import webapp.services `
  --hidden-import webapp.pages `
  --hidden-import webapp.dsl `
  --hidden-import webapp.schemas `
  --hidden-import webapp.dmx_controller `
  --hidden-import webapp.live_player `
  --hidden-import webapp.api_experiment `
  --hidden-import webapp.api_sequence `
  --hidden-import webapp.api_live `
  --hidden-import webapp.api_health `
  --hidden-import webapp.api_palettes `
  --hidden-import webapp.api_settings `
  .\run_webapp.py

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "`nBuild OK: dist\IcareWeb.exe"
