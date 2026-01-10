import threading
import time
import os
import sys

# Ensure imports of local DMX modules work when running from webapp/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pydmxIcare
import pydmxlight


class DMXController:
    def __init__(self):
        self.mydmx = pydmxIcare.DMX_Icare()
        # Example fixture (adjust if needed)
        self.par_led1 = pydmxlight.Par_Led_615_AFX(15, 0)

        # State
        self.enabled = False
        self.strobe_enabled = False
        self.random_enabled = False
        self.strobe_random_enabled = False  # legacy, not used in UI
        self.freq = 60
        self.shuffle = 50
        self.r = 0
        self.g = 0
        self.b = 0
        self.amp = 0
        self.pan = 0
        self.tilt = 0
        # Base color channel (R,G,B at base, base+1, base+2)
        self.base_color_channel = 9

        self._thread = None
        self._stop_event = threading.Event()

        # Overlay strobe (non-destructive): toggles output on top of current values
        self.overlay = {
            "active": False,
            "freq_hz": 10.0,
            "duty": 0.5,  # 0..1
            "until": 0.0,
            "channel": 0,  # DMX channel used for overlay gating (0 = disabled)
        }

        # Random color mode parameters
        self.random_params = {
            "freq_hz": 1.0,      # target color changes per second
            "smooth": 0.5,       # 0..1, 0 = hard cut, 1 = very smooth
            "brightness": 128,   # maps to amplitude channel
        }
        self._random_target = (0, 0, 0)
        self._random_next = time.time()

    def connection(self):
        self.mydmx.connection()

    def _send_current(self):
        # Map channels based on ExperimentTab
        self.mydmx.set_channel(0, 255)
        self.mydmx.set_channel(8, 0)
        self.mydmx.set_channel(1, int(self.amp))
        try:
            base = int(self.base_color_channel)
        except Exception:
            base = 9
        self.mydmx.set_channel(base + 0, int(self.r))
        self.mydmx.set_channel(base + 1, int(self.g))
        self.mydmx.set_channel(base + 2, int(self.b))
        self.mydmx.set_channel(3, int(self.pan))
        self.mydmx.set_channel(5, int(self.tilt))
        try:
            self.mydmx.send_data()
        except Exception:
            # Gracefully ignore send errors when DMX interface isn't connected
            pass

    def _send_black(self):
        # Send "off" for color and amplitude channels only
        try:
            self.mydmx.set_channel(1, 0)
            base = int(self.base_color_channel)
            self.mydmx.set_channel(base + 0, 0)
            self.mydmx.set_channel(base + 1, 0)
            self.mydmx.set_channel(base + 2, 0)
            self.mydmx.send_data()
        except Exception:
            pass

    def _send_with_overlay(self):
        # If overlay active, apply duty cycle toggling at freq_hz on top of current values
        now = time.time()
        if self.overlay["active"]:
            if now >= self.overlay["until"]:
                self.overlay["active"] = False
            else:
                # phase in seconds; use fractional part for duty cycle
                phase = (now * float(self.overlay["freq_hz"])) % 1.0
                on_phase = phase < float(self.overlay["duty"])  # True => send current, False => black
                ch = int(self.overlay.get("channel", 0))
                if ch > 0:
                    # Gate designated channel while preserving color
                    try:
                        self._send_current()
                        self.mydmx.set_channel(ch, 255 if on_phase else 0)
                        self.mydmx.send_data()
                    except Exception:
                        pass
                else:
                    # Default gating by toggling color output
                    if on_phase:
                        self._send_current()
                    else:
                        self._send_black()
                return
        # default behavior (no overlay)
        self._send_current()

    def set_values(self, r=None, g=None, b=None, amp=None, pan=None, tilt=None):
        if r is not None:
            self.r = max(0, min(255, int(r)))
        if g is not None:
            self.g = max(0, min(255, int(g)))
        if b is not None:
            self.b = max(0, min(255, int(b)))
        if amp is not None:
            self.amp = max(0, min(255, int(amp)))
        if pan is not None:
            self.pan = max(0, min(255, int(pan)))
        if tilt is not None:
            self.tilt = max(0, min(255, int(tilt)))
        self._send_current()

    def start(self):
        self.enabled = True
        self.strobe_enabled = False
        self.random_enabled = False
        self._ensure_thread()

    def stop(self):
        self.enabled = False
        self.random_enabled = False
        self.strobe_enabled = False
        self._stop_thread()

    def blackout(self):
        self.enabled = False
        self.random_enabled = False
        self.strobe_enabled = False
        self.r = 0
        self.g = 0
        self.b = 0
        self.amp = 0
        # Zero several groups (following blackout from ExperimentTab)
        for i in range(7):
            self.mydmx.set_channel(10 * i + 0, 0)
            self.mydmx.set_channel(10 * i + 1, 0)
            self.mydmx.set_channel(10 * i + 2, 0)
        try:
            self.mydmx.send_data()
        except Exception:
            pass

    def strobe(self, freq: int, shuffle: int = 50):
        self.freq = max(1, int(freq))
        self.shuffle = max(0, min(100, int(shuffle)))
        self.strobe_enabled = True
        self.enabled = False
        self.random_enabled = False
        self._ensure_thread()

    def random(self):
        # Backward compatible start
        self.random_enabled = True
        self.strobe_enabled = False
        self.enabled = False
        self._ensure_thread()

    def random_config(self, freq_hz=None, smooth=None, brightness=None):
        if freq_hz is not None:
            try:
                self.random_params["freq_hz"] = max(0.1, float(freq_hz))
            except Exception:
                pass
        if smooth is not None:
            try:
                self.random_params["smooth"] = max(0.0, min(1.0, float(smooth)))
            except Exception:
                pass
        if brightness is not None:
            try:
                self.random_params["brightness"] = max(0, min(255, int(brightness)))
            except Exception:
                pass

    def random_start(self):
        self.random_enabled = True
        self.strobe_enabled = False
        self.enabled = False
        self._ensure_thread()

    def random_stop(self):
        self.random_enabled = False

    def _ensure_thread(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def _stop_thread(self):
        if self._thread is not None and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=1.5)
        self._thread = None

    def _run(self):
        while not self._stop_event.is_set():
            if self.enabled:
                self._send_with_overlay()
                time.sleep(0.05)
            elif self.strobe_enabled:
                # On period
                # If random strobe, change color when turning on
                if self.strobe_random_enabled:
                    import random as _rnd
                    self.r = _rnd.randint(0, 255)
                    self.g = _rnd.randint(0, 255)
                    self.b = _rnd.randint(0, 255)
                self._send_with_overlay()
                on_time = max(0.001, 60 / self.freq * (self.shuffle / 100))
                time.sleep(on_time)
                # Off period (keep same color but resend)
                if self.strobe_random_enabled:
                    # Turn off
                    prev = (self.r, self.g, self.b)
                    self._send_with_overlay()
                    try:
                        self.mydmx.set_channel(9, 0)
                        self.mydmx.set_channel(10, 0)
                        self.mydmx.set_channel(11, 0)
                        self.mydmx.send_data()
                    except Exception:
                        pass
                    # Restore for next cycle
                    self.r, self.g, self.b = prev
                else:
                    self._send_with_overlay()
                off_time = max(0.001, 60 / max(1, self.freq) * (1 - self.shuffle / 100))
                time.sleep(off_time)
            elif self.random_enabled:
                # Random color target at configured frequency, with optional smoothing
                now = time.time()
                # Update target color at interval
                if now >= self._random_next:
                    import random as _rnd
                    self._random_target = (
                        _rnd.randint(0, 255),
                        _rnd.randint(0, 255),
                        _rnd.randint(0, 255),
                    )
                    self._random_next = now + (1.0 / max(0.1, self.random_params["freq_hz"]))
                # Apply smoothing towards target
                smooth = float(self.random_params.get("smooth", 0.0))
                if smooth <= 0.01:
                    self.r, self.g, self.b = self._random_target
                else:
                    # Exponential smoothing factor scaled for ~40Hz loop (more intermediate values)
                    alpha = max(0.01, min(0.35, smooth * 0.18))
                    self.r = int(self.r + alpha * (self._random_target[0] - self.r))
                    self.g = int(self.g + alpha * (self._random_target[1] - self.g))
                    self.b = int(self.b + alpha * (self._random_target[2] - self.b))
                # Brightness maps to amplitude
                self.amp = int(self.random_params.get("brightness", 128))
                self._send_with_overlay()
                time.sleep(0.025)
            else:
                time.sleep(0.1)
