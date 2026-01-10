import threading
import time
from flask import jsonify

from .services import dmx


class LivePlayer:
    def __init__(self):
        self.data = None  # Loaded JSON sequence
        self.freq = 60
        self.index = 0
        self.playing = False
        self.paused = False
        self.selected_modules = set()
        self._thread = None
        self._stop_event = threading.Event()
        # Visualization / DMX state
        self.current_rgb = (0, 0, 0)
        # Effect state
        self.effect = {
            "mode": None,          # 'uni' | 'fond' | 'str'
            "len": 0,
            "step": 0,
            "c1": (0, 0, 0),
            "c2": (0, 0, 0),
            "freq": 60,
            "toggle": True,
        }

    def load(self, data):
        self.data = data
        self.index = 0
        self.playing = False
        self.paused = False
        self.selected_modules = set()
        self.current_rgb = (0, 0, 0)
        self.effect = {"mode": None, "len": 0, "step": 0, "c1": (0,0,0), "c2": (0,0,0), "freq": 60, "toggle": True}

    def start(self, freq: int | None = None):
        if freq:
            self.freq = max(1, int(freq))
        self.playing = True
        self.paused = False
        self._ensure_thread()

    def pause(self):
        self.paused = not self.paused

    def stop(self):
        self.playing = False
        self.paused = False
        self.index = 0

    def next(self):
        if not self.data:
            return
        self.index = min(self.index + 1, len(self.data.get("data", {})))

    def prev(self):
        self.index = max(self.index - 1, 0)

    def toggle_module(self, name: str):
        if name in self.selected_modules:
            self.selected_modules.remove(name)
        else:
            self.selected_modules.add(name)

    def select_all(self):
        if not self.data:
            return
        self.selected_modules = set(self.data["Header"].get("Modules", []))

    def unselect_all(self):
        self.selected_modules.clear()

    def status(self):
        total = len(self.data.get("data", {})) if self.data else 0
        current_section = None
        if self.data and self.index > 0 and str(self.index) in self.data["data"]:
            current_section = self.data["data"][str(self.index)]["section"]
        pct = int(100 * self.index / total) if total else 0
        return {
            "playing": self.playing,
            "paused": self.paused,
            "index": self.index,
            "total": total,
            "progress": pct,
            "section": current_section,
            "selected": sorted(list(self.selected_modules)),
            "rgb": {"r": int(self.current_rgb[0]), "g": int(self.current_rgb[1]), "b": int(self.current_rgb[2])},
            "beamAngle": 45,
        }

    def _ensure_thread(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def _run(self):
        while not self._stop_event.is_set():
            if self.playing and not self.paused and self.data:
                total = len(self.data.get("data", {}))
                if total == 0:
                    time.sleep(0.25)
                    continue
                # Determine function for selected module or default ParLED1
                header_modules = self.data["Header"].get("Modules", [])
                target_module = None
                if self.selected_modules:
                    # Take the first selected module present in header
                    for m in self.selected_modules:
                        if m in header_modules:
                            target_module = m
                            break
                if not target_module and header_modules:
                    target_module = header_modules[0]

                # Advance index
                self.index = min(self.index + 1, total)
                line_key = str(self.index)
                funcs = self.data["data"].get(line_key, {}).get("function", [])
                if target_module and target_module in header_modules:
                    mi = header_modules.index(target_module)
                    fx = funcs[mi] if mi < len(funcs) else ""
                else:
                    fx = ""

                # Parse effects: uni, fond, str, or '|' continuation
                try:
                    if isinstance(fx, str) and fx:
                        if fx.startswith("uni_"):
                            parts = fx.split("_")
                            # uni_n_R_G_B
                            r, g, b = int(parts[2]), int(parts[3]), int(parts[4])
                            self.current_rgb = (r, g, b)
                            dmx.set_values(r=r, g=g, b=b)
                            # reset effect
                            self.effect = {"mode": None, "len": 0, "step": 0, "c1": (0,0,0), "c2": (0,0,0), "freq": 60, "toggle": True}
                        elif fx.startswith("fond_"):
                            parts = fx.split("_")
                            # fond_n_R1_G1_B1_R2_G2_B2
                            n = int(parts[1])
                            c1 = (int(parts[2]), int(parts[3]), int(parts[4]))
                            c2 = (int(parts[5]), int(parts[6]), int(parts[7]))
                            self.effect = {"mode": "fond", "len": max(1, n), "step": 0, "c1": c1, "c2": c2, "freq": 60, "toggle": True}
                            # set first color
                            self.current_rgb = c1
                            dmx.set_values(r=c1[0], g=c1[1], b=c1[2])
                        elif fx.startswith("str_"):
                            parts = fx.split("_")
                            # str_n_R_G_B_freq
                            n = int(parts[1])
                            c1 = (int(parts[2]), int(parts[3]), int(parts[4]))
                            freq = int(parts[5]) if len(parts) > 5 else 60
                            self.effect = {"mode": "str", "len": max(1, n), "step": 0, "c1": c1, "c2": c1, "freq": max(1, freq), "toggle": True}
                            self.current_rgb = c1
                            dmx.set_values(r=c1[0], g=c1[1], b=c1[2])
                        elif fx == "|" and self.effect["mode"] == "fond":
                            # continue fade
                            self.effect["step"] = min(self.effect["step"] + 1, self.effect["len"] - 1)
                            t = 0 if self.effect["len"] <= 1 else self.effect["step"] / (self.effect["len"] - 1)
                            r = int(self.effect["c1"][0] + t * (self.effect["c2"][0] - self.effect["c1"][0]))
                            g = int(self.effect["c1"][1] + t * (self.effect["c2"][1] - self.effect["c1"][1]))
                            b = int(self.effect["c1"][2] + t * (self.effect["c2"][2] - self.effect["c1"][2]))
                            self.current_rgb = (r, g, b)
                            dmx.set_values(r=r, g=g, b=b)
                        elif fx == "|" and self.effect["mode"] == "str":
                            # continue strobe: toggle color on/off per step
                            self.effect["step"] = min(self.effect["step"] + 1, self.effect["len"] - 1)
                            self.effect["toggle"] = not self.effect["toggle"]
                            if self.effect["toggle"]:
                                r, g, b = self.effect["c1"]
                            else:
                                r, g, b = (0, 0, 0)
                            self.current_rgb = (r, g, b)
                            dmx.set_values(r=r, g=g, b=b)
                        else:
                            # unknown or empty: keep current
                            pass
                except Exception:
                    # Robust against malformed strings
                    pass

                time.sleep(60 / max(1, self.freq))
            else:
                time.sleep(0.2)
