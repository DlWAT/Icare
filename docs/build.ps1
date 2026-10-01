$ErrorActionPreference = 'Stop'

# Compile the Icare manual (LaTeX -> PDF).
# Output: docs\icare.pdf
#
# Requires a LaTeX distribution (MiKTeX or TeX Live) providing pdflatex/latexmk.

Set-Location -Path $PSScriptRoot

# Two passes so the table of contents and references settle.
# (latexmk is not used because it requires a Perl install on Windows.)
pdflatex -interaction=nonstopmode -halt-on-error icare.tex
pdflatex -interaction=nonstopmode -halt-on-error icare.tex

if (Test-Path .\icare.pdf) {
  Write-Host "`nPDF OK: docs\icare.pdf"
} else {
  throw "Compilation failed: icare.pdf was not produced"
}
