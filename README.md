# Icare

> Browser-based DMX lighting controller for amateur music groups.

Icare is a small, local Flask web app that turns a USB-DMX (Enttec-compatible)
adapter into a friendly light board. It is meant for bands and amateur
performance groups who want to fly without a dedicated lighting designer.

The app runs entirely on your machine; the browser at
[`http://127.0.0.1:5000`](http://127.0.0.1:5000) is the only UI you need.

---

## Features

| Page         | What you get |
|--------------|---|
| **Direct**   | Live RGB / amplitude / pan / tilt sliders, color picker, favourite-color palette, blackout, random colors, strobe overlay, **rainbow / fire / police / chase** procedural effects, **microphone audio-reactive** mode, real-time 3D visualization. |
| **Séquence** | Visual editor for a beat-by-beat show. Insert *Uniform*, *Fade* and *Strobe* effects per fixture, save/load JSON files, accepts both the modern and the legacy schema. |
| **Live**     | Loads a saved sequence and walks through it at a configurable BPM with a **tap-tempo** button, transport controls, progress bar and a 3D beam visualization mirroring the DMX output. |
| **Show**     | Multi-fixture **patch** (11 fixtures), **looks** (static light states you author in the browser), a **3D simulation** of the whole stage with **fluid smoke**, and a link to **Ableton Live**: each Ableton scene triggers a look. Uses the AbletonOSC remote script. |
| **Topbar**   | Live DMX connection status indicator and a **dark/light theme** toggle. Settings (theme, last port, base channel, favourites) are persisted to disk. |

### Ableton Live link

Icare can follow Ableton Live with the free **AbletonOSC** remote script:

1. Install the script: `.\tools\install_abletonosc.ps1`
   (or follow the [AbletonOSC instructions](https://github.com/ideoforms/AbletonOSC)).
2. Restart Live and pick **AbletonOSC** as a Control Surface in
   *Preferences → Link, Tempo & MIDI*.
3. In Icare, open the **Show** tab and click **Connecter Ableton**.
4. Map each Ableton *scene name* to an Icare *look*. Selecting/firing a scene
   then recalls the matching light look.

The link uses OSC over localhost (send to `:11000`, listen on `:11001`); no
Ableton running simply leaves the link "disconnected".

The repository ships a demo look library in `Looks/` (all fixtures + fog) and a
ready-made scene mapping in `scenes.json`, matching the studio template scenes
(`INTRO`, `A`, `B`, `CHORUS`, `BREAK`, `SOLO`, `OUTRO`). The Show tab also
renders the whole rig in 3D, so you can design shows without any hardware.

---

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

Python 3.10 or newer is required.

### 2. Run the web server

```bash
python run_webapp.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

### 3. Connect your DMX adapter

In the **Direct** tab, click **Connexion DMX**. The status pill in the topbar
turns green when the serial port opens. The auto-detection picks the first
COM port whose description contains "USB"; you can also override the port
manually in the input next to the button.

---

## Build a standalone Windows executable

```powershell
.\build_exe.ps1
```

This produces `dist/IcareWeb.exe` (~30 MB). Double-click it: the app starts
and prints the local URL. The runtime persists settings, palettes and logs
in the same folder as the `.exe`.

---

## Sequence file format

Sequences live as JSON files in `Sequences/`. The modern schema is:

```json
{
  "Header": {
    "Structure": ["Intro_x4", "Intro_x4", ...],
    "Tempo": "60",
    "Modules": ["ParLED1", "ParLED2", ...],
    "Line":    ["1", "2", ...]
  },
  "data": {
    "1": { "section": "Intro_x4", "function": ["uni_4_255_0_0", "", ...] },
    "2": { "section": "Intro_x4", "function": ["|",            "", ...] }
  }
}
```

Legacy files using the older `headers/structure` shape (such as
`Doctor_doctor.json` from older releases) are auto-migrated on load.

### Function-string DSL

Each cell in a row is a small string describing what one fixture should do:

| Token                                          | Meaning                                  |
|------------------------------------------------|------------------------------------------|
| `""`                                           | Keep current state                       |
| `"\|"`                                         | Continue the previous multi-step effect  |
| `uni_<n>_<R>_<G>_<B>`                          | Hold a uniform colour for `n` beats      |
| `fond_<n>_<R1>_<G1>_<B1>_<R2>_<G2>_<B2>`       | Linear fade from `c1` to `c2` over `n`   |
| `str_<n>_<R>_<G>_<B>_<freq>`                   | Strobe at `freq` Hz for `n` beats        |

The continuation token `|` re-uses the previously-set effect for that cell's
fixture. So a 4-beat fade looks like:

```
fond_4_255_0_0_0_0_255   |   |   |
```

---

## REST API (selected endpoints)

| Method | Endpoint                                     | Purpose                          |
|--------|----------------------------------------------|----------------------------------|
| GET    | `/api/health`                                | Service + DMX status             |
| GET    | `/api/settings`                              | Persisted user settings          |
| POST   | `/api/settings`                              | Update settings (theme, …)       |
| POST   | `/api/experiment/connect`                    | Open the DMX serial port         |
| POST   | `/api/experiment/set-values`                 | Push RGB / amp / pan / tilt      |
| POST   | `/api/experiment/effect/start`               | Start a procedural effect        |
| POST   | `/api/experiment/audio/push`                 | Audio-reactive sample            |
| GET    | `/api/sequence/list`                         | List sequences                   |
| GET    | `/api/sequence/load?name=…`                  | Load and normalise a sequence    |
| POST   | `/api/sequence/save`                         | Save a sequence                  |
| POST   | `/api/live/load`                             | Load a sequence into the player  |
| POST   | `/api/live/play`                             | Start playback                   |
| POST   | `/api/live/tap`                              | Tap-tempo                        |
| GET    | `/api/live/status`                           | Player status                    |
| GET    | `/api/palettes/favorites`                    | Favourite-colour list            |

Status responses are JSON of the form `{"ok": true, ...}` on success and
`{"ok": false, "error": "..."}` with an HTTP error code otherwise.

---

## Development

```bash
# Install dev tools
pip install -r requirements-dev.txt

# Run tests
pytest

# Lint
ruff check .
```

Project layout:

```
Icare/
├── pydmxIcare.py             # Low-level Enttec USB Pro framing (serial I/O)
├── pydmxlight.py             # Fixture descriptors (Par LED, Strobe)
├── run_webapp.py             # CLI entry point
├── webapp/
│   ├── __init__.py           # create_app()
│   ├── config.py             # constants, paths, UserSettings, logging
│   ├── services.py           # DMX + Ableton + settings singletons
│   ├── utils.py              # shared HTTP/file helpers
│   ├── fixtures.py           # DMX fixture profiles + patch model
│   ├── looks.py              # light looks (static per-fixture states)
│   ├── osc.py                # minimal OSC encoder/decoder
│   ├── ableton.py            # AbletonOSC client + scene engine
│   ├── dmx_controller.py     # output thread state machine
│   ├── live_player.py        # sequence playback engine + tap-tempo
│   ├── dsl.py                # function-string DSL parser
│   ├── schemas.py            # sequence schema validator + migrator
│   ├── pages.py              # HTML routes
│   ├── api_experiment.py     # Direct tab API
│   ├── api_sequence.py       # Sequence editor API
│   ├── api_live.py           # Live playback API
│   ├── api_health.py         # /api/health
│   ├── api_palettes.py       # Favourite colours + named palettes
│   ├── api_settings.py       # Persistent user settings
│   ├── api_show.py           # Patch, looks, scenes, Ableton link
│   ├── templates/            # Jinja2 templates
│   └── static/
│       ├── app.css
│       ├── app.js
│       └── vendor/three.min.js
├── Sequences/                # Sample shows
├── Looks/                    # Demo look library (JSON)
├── tests/                    # pytest suite
├── tools/                    # helpers (install_abletonosc.ps1)
├── docs/                     # LaTeX manual + compiled PDF
├── pyproject.toml            # Build, ruff & pytest config
└── README.md
```

## Documentation

A complete French manual lives in `docs/` as LaTeX sources. It covers the user
guide (Direct / Séquence / Live), the DMX and Enttec background, the internal
architecture, the sequence DSL and the full REST API. Build the PDF with:

```powershell
.\docs\build.ps1
```

The compiled `docs/icare.pdf` is kept in the repository for convenience.

## License

MIT — see `LICENSE`.
