$ErrorActionPreference = 'Stop'

# Installe le remote script AbletonOSC dans Ableton Live (Windows).
# Après l'installation : redémarrer Live, puis Préférences > Link/Tempo/MIDI,
# choisir "AbletonOSC" dans la liste Control Surface.

$dest = Join-Path $env:USERPROFILE 'Documents\Ableton\User Library\Remote Scripts'
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$zip = Join-Path $env:TEMP 'AbletonOSC.zip'
$url = 'https://github.com/ideoforms/AbletonOSC/archive/refs/heads/master.zip'

Write-Host "Téléchargement d'AbletonOSC…"
Invoke-WebRequest -Uri $url -OutFile $zip

$extract = Join-Path $env:TEMP 'AbletonOSC-extract'
if (Test-Path $extract) { Remove-Item -Recurse -Force $extract }
Expand-Archive -Path $zip -DestinationPath $extract -Force

$src = Join-Path $extract 'AbletonOSC-master'
$target = Join-Path $dest 'AbletonOSC'
if (Test-Path $target) { Remove-Item -Recurse -Force $target }
Move-Item $src $target

Write-Host ""
Write-Host "AbletonOSC installé dans : $target"
Write-Host "1. Redémarre Ableton Live."
Write-Host "2. Préférences > Link, Tempo & MIDI > Control Surface = AbletonOSC."
Write-Host "3. Dans Icare, onglet Show > « Connecter Ableton »."
