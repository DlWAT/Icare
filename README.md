# Icare
DMX interface for shows. 
This interface will help amateur groups without a lighting designer. It aims at writing and decoding sequences of light shows during music concerts. However, it will not stop only at light shows, but also at handcrafted lightings.

## Web Interface

The project now includes a lightweight web interface that replaces the desktop window. It exposes the main "Direct" (Experiment) controls through a browser.

- Backend: Flask (in `webapp/app.py`)
- Frontend: HTML/CSS/JS (under `webapp/templates` and `webapp/static`)

### Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the web server:

```bash
python webapp/app.py
```

3. Open your browser at: http://127.0.0.1:5000

### Features

- Connect to DMX and control RGB, amplitude, pan, tilt.
- Start/Stop continuous send, Blackout, Random mode, Strobe (frequency + shuffle).
- Live color preview and color picker.

Future work will add "Sequence" and "Live" tabs to the web UI.
