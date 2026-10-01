# Icare — todo list

> Suivi du chantier « refonte + Ableton ». Dernière mise à jour : 2026-10-01.
> Branche de travail : `feat/refonte-ableton`.

## Fait

- [x] Nettoyage du dépôt (caches, fichiers obsolètes, `.gitignore`).
- [x] Manuel LaTeX complet (`docs/icare.pdf`) : guide, DMX, architecture, API.
- [x] Moteur **multi-projecteurs** + **patch** (profils RGBWA 5ch, Wild Wash 6ch,
      Q-Spot 9ch, M-Fog 3ch).
- [x] **Looks** (états par cible) + **animation** (pulse, vague, teinte,
      scintillement).
- [x] Lien **Ableton Live** via AbletonOSC (tempo, transport, scènes) +
      mapping scènes → looks.
- [x] **Simulation 3D** de toute la scène : faisceaux par angle réel, contours
      (Q-Spot net, autres doux), Wild Wash en barre LED, fumée **éclairée par
      les feux**, tone mapping, flaques au sol.
- [x] **Morceau test** autonome (timeline de cues) + `Shows/demo.json`.
- [x] Nettoyage de l'onglet Direct (retrait pan/tilt et position : projos fixes).

## À faire — priorité

### Intégration Ableton (réelle)
- [ ] Installer AbletonOSC (`tools/install_abletonosc.ps1`) et redémarrer Live.
- [ ] Vérifier la connexion dans l'onglet Show (témoin vert, tempo, scènes).
- [ ] Valider le **mapping scènes → looks** avec le vrai template du studio.
- [ ] Gérer le cas où les noms de scènes changent (re-synchroniser le mapping).

### Matériel DMX (recette)
- [ ] Brancher l'Enttec USB Pro et **valider les adresses** du patch sur le
      matériel réel.
- [ ] Confirmer les **modes DMX** réels de chaque appareil (écran des projos).
- [ ] Tester la **machine à fumée** (volume, intervalle, durée).
- [ ] Vérifier une **frame complète** (tous les projos allumés en même temps).

### Éditeur de looks
- [ ] Charger puis **modifier** un look existant (aujourd'hui : recharge l'état).
- [ ] **Dupliquer** / renommer un look.
- [ ] Prévisualiser le look **avant** de l'appliquer.

## À faire — confort / robustesse

- [ ] Reconnexion automatique du port série (perte de trame / débranchement).
- [ ] Éditeur de **patch** dans l'interface (aujourd'hui : lecture + API).
- [ ] Mettre à jour le **packaging** (`build_exe.ps1`, `.spec`) avec les
      nouveaux modules.
- [ ] Sauvegardes versionnées des looks/shows (déjà dans Git ; prévoir export).

## Plus tard / idées

- [ ] **Caler l'animation sur le BPM** (vagues au tempo, beat events Ableton).
- [ ] **Transitions en fondu** entre les cues du morceau test.
- [ ] Autres mouvements : variation de saturation, stroboscope doux, dégradés.
- [ ] Déclencheurs **MIDI** (loopMIDI) en complément des scènes.
- [ ] **Ableton Link** pour une synchro tempo plus fine (optionnel).
- [ ] Plus de profils (RGBWA 6/7/10 canaux) et modes alternatifs
      (Wild Wash 3ch, Q-Spot 4ch).
- [ ] Captures d'écran de la 3D dans le manuel + tutoriel « premier show ».

## Fusion

- [ ] Relire / tester, puis **fusionner `feat/refonte-ableton` dans `main`**.
