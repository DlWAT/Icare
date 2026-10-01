# Documentation Icare

Ce dossier contient le manuel complet d'Icare, rédigé en LaTeX et compilé en
PDF.

## Contenu

| Fichier | Rôle |
|---|---|
| `icare.tex` | Document principal (page de titre, sommaire, assemblage). |
| `preamble.tex` | Paquets, couleurs, styles de code et macros. |
| `part1-guide.tex` | Partie I — Guide utilisateur. |
| `part2-comprendre.tex` | Partie II — DMX, Enttec, effets, audio-réactif. |
| `part3-technique.tex` | Partie III — Architecture et code interne. |
| `part4-api.tex` | Partie IV — API REST, tests et déploiement. |
| `annexes.tex` | Annexes (aide-mémoire DSL, dépannage, glossaire). |
| `build.ps1` | Script de compilation. |

## Compiler le PDF

```powershell
.\build.ps1
```

ou manuellement (deux passes pour stabiliser le sommaire) :

```bash
pdflatex icare.tex
pdflatex icare.tex
```

Sous Windows, `latexmk` réclame une installation de Perl : le script
`build.ps1` utilise donc directement `pdflatex`.

Le résultat est `icare.pdf`. Les fichiers auxiliaires (`*.aux`, `*.log`,
`*.toc`, `*.out`, `*.fls`, `*.fdb_latexmk`) sont générés par LaTeX et ignorés
par Git.

## Prérequis

Une distribution LaTeX fournissant `pdflatex` (MiKTeX sous Windows, TeX Live
ailleurs). Les paquets utilisés (`babel-french`, `listings`, `tikz`,
`booktabs`, `hyperref`, `lmodern`) sont installés automatiquement par MiKTeX au
premier passage.
