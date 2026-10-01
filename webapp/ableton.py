"""Ableton Live link (via the AbletonOSC remote script) and the scene engine.

* :class:`AbletonOSC` is a tiny UDP/OSC client: it listens on port 11001 and
  sends to port 11000, tracks tempo / transport / selected scene / beat and
  exposes them as plain attributes.
* :class:`SceneEngine` maps an Ableton **scene name** to a light **look** and
  applies it to the DMX controller whenever the selected scene changes.

Nothing here requires Ableton to be running: the client simply reports
``connected = False`` until it receives a ``/live/test`` reply.
"""

from __future__ import annotations

import json
import logging
import socket
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import osc

logger = logging.getLogger(__name__)

SEND_PORT = 11000
LISTEN_PORT = 11001
STALE_AFTER = 2.5  # seconds without a message before "disconnected"


class AbletonOSC:
    """Minimal AbletonOSC client."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        send_port: int = SEND_PORT,
        listen_port: int = LISTEN_PORT,
    ) -> None:
        self.host = host
        self.send_port = send_port
        self.listen_port = listen_port

        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.running = False

        # ---- Mirrored state ----
        self.connected = False
        self.last_seen = 0.0
        self.version: str | None = None
        self.tempo = 120.0
        self.is_playing = False
        self.selected_scene = -1
        self.num_scenes = 0
        self.scene_names: dict[int, str] = {}
        self.beat = -1

        # ---- Callbacks ----
        self.on_scene: Callable[[int, str | None], None] | None = None
        self.on_beat: Callable[[int], None] | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> bool:
        if self.running:
            return True
        self._stop.clear()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("127.0.0.1", self.listen_port))
            sock.settimeout(0.5)
        except OSError as exc:
            logger.warning("AbletonOSC: cannot bind UDP %s: %s", self.listen_port, exc)
            return False
        self._sock = sock
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="ableton-osc")
        self._thread.start()
        self._handshake()
        logger.info(
            "AbletonOSC client started (listen :%s -> send :%s)", self.listen_port, self.send_port
        )
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        self.running = False
        self.connected = False

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------
    def send(self, address: str, *args: Any) -> None:
        if self._sock is None:
            return
        try:
            self._sock.sendto(osc.encode(address, *args), (self.host, self.send_port))
        except (OSError, TypeError) as exc:
            logger.debug("AbletonOSC send %s failed: %s", address, exc)

    def _handshake(self) -> None:
        for address in (
            "/live/test",
            "/live/application/get/version",
            "/live/song/get/num_scenes",
            "/live/song/get/tempo",
            "/live/song/get/is_playing",
            "/live/view/get/selected_scene",
        ):
            self.send(address)
        for address in (
            "/live/view/start_listen/selected_scene",
            "/live/song/start_listen/tempo",
            "/live/song/start_listen/is_playing",
            "/live/song/start_listen/beat",
        ):
            self.send(address)

    # ------------------------------------------------------------------
    # Receive loop
    # ------------------------------------------------------------------
    def _run(self) -> None:
        last_probe = 0.0
        while not self._stop.is_set():
            try:
                assert self._sock is not None
                data, _ = self._sock.recvfrom(65535)
            except TimeoutError:
                data = None
            except OSError:
                break
            if data:
                self._dispatch(data)

            now = time.time()
            if self.connected and now - self.last_seen > STALE_AFTER:
                self.connected = False
            if now - last_probe > 2.0:
                last_probe = now
                self.send("/live/test")
                self.send("/live/view/get/selected_scene")

    def _dispatch(self, data: bytes) -> None:
        try:
            address, args = osc.decode(data)
        except Exception:  # noqa: BLE001 - never let a bad packet kill the thread
            logger.debug("AbletonOSC: undecodable packet")
            return
        self.last_seen = time.time()

        if address == "/live/test":
            self.connected = True
        elif address == "/live/application/get/version":
            self.version = ".".join(str(a) for a in args) if args else None
        elif address == "/live/song/get/tempo":
            if args:
                self.tempo = float(args[0])
        elif address == "/live/song/get/is_playing":
            if args:
                self.is_playing = bool(args[0])
        elif address == "/live/song/get/num_scenes":
            if args:
                self.num_scenes = int(args[0])
                for i in range(self.num_scenes):
                    self.send("/live/scene/get/name", i)
        elif address == "/live/scene/get/name":
            if len(args) >= 2:
                idx = int(args[0])
                self.scene_names[idx] = str(args[1])
                if idx == self.selected_scene:
                    self._fire_scene(idx)
        elif address == "/live/view/get/selected_scene":
            if args:
                self._select_scene(int(args[0]))
        elif address == "/live/song/get/beat":
            if args:
                self.beat = int(args[0])
                if self.on_beat:
                    self.on_beat(self.beat)
        elif address == "/live/error":
            logger.warning("AbletonOSC error: %s", args)

    def _select_scene(self, index: int) -> None:
        if index == self.selected_scene:
            return
        self.selected_scene = index
        self._fire_scene(index)

    def _fire_scene(self, index: int) -> None:
        name = self.scene_names.get(index)
        if name is None:
            self.send("/live/scene/get/name", index)
        if self.on_scene:
            self.on_scene(index, name)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "connected": self.connected,
            "version": self.version,
            "tempo": round(self.tempo, 2),
            "isPlaying": self.is_playing,
            "selectedScene": self.selected_scene,
            "selectedSceneName": self.scene_names.get(self.selected_scene),
            "numScenes": self.num_scenes,
            "sceneNames": [self.scene_names.get(i, "") for i in range(self.num_scenes)],
            "beat": self.beat,
        }


# ===========================================================================
# Scene engine
# ===========================================================================
class SceneEngine:
    """Maps Ableton scenes to looks and drives the DMX controller."""

    def __init__(self, client: AbletonOSC, dmx, look_dir: str, mapping_file: Path) -> None:
        self.client = client
        self.dmx = dmx
        self.look_dir = look_dir
        self.mapping_file = mapping_file

        self.enabled = True
        self.mapping: dict[str, str] = {}  # scene name -> look name
        self.active_scene: str | None = None
        self.active_look: str | None = None
        self.last_error: str | None = None

        self._load_mapping()
        client.on_scene = self._on_scene

    # ------------------------------------------------------------------
    def _load_mapping(self) -> None:
        if not self.mapping_file.is_file():
            return
        try:
            with self.mapping_file.open(encoding="utf-8") as fh:
                raw = json.load(fh)
            self.enabled = bool(raw.get("enabled", True))
            self.mapping = {str(k): str(v) for k, v in (raw.get("mapping") or {}).items()}
        except (OSError, ValueError, json.JSONDecodeError):
            logger.exception("Could not load scene mapping; starting empty")
            self.mapping = {}

    def save_mapping(self) -> None:
        try:
            self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
            with self.mapping_file.open("w", encoding="utf-8") as fh:
                json.dump(
                    {"enabled": self.enabled, "mapping": self.mapping},
                    fh,
                    indent=2,
                    ensure_ascii=False,
                )
        except OSError:
            logger.exception("Could not save scene mapping")

    # ------------------------------------------------------------------
    def set_mapping(self, scene: str, look_name: str | None) -> dict[str, str]:
        if look_name:
            self.mapping[scene] = look_name
        else:
            self.mapping.pop(scene, None)
        self.save_mapping()
        return self.mapping

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
        self.save_mapping()

    # ------------------------------------------------------------------
    def _on_scene(self, index: int, name: str | None) -> None:
        if not self.enabled or not name:
            return
        look_name = self.mapping.get(name)
        if not look_name:
            self.active_scene = name
            self.active_look = None
            return
        self.show_look(look_name, scene=name)

    def show_look(self, look_name: str, scene: str | None = None) -> bool:
        """Apply a look now (used by the scene callback and the UI)."""
        from .looks import load_look, resolve  # local import avoids a cycle

        try:
            look = load_look(self.look_dir, look_name)
        except (OSError, ValueError) as exc:
            self.last_error = f"look {look_name!r}: {exc}"
            logger.warning("Could not load look %r: %s", look_name, exc)
            return False
        self.dmx.apply_look(resolve(look, self.dmx.patch), motion=look.motion)
        if look.fog:
            self.dmx.set_fog(**look.fog)
        self.active_scene = scene if scene is not None else self.active_scene
        self.active_look = look_name
        self.last_error = None
        return True

    # ------------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mapping": dict(self.mapping),
            "activeScene": self.active_scene,
            "activeLook": self.active_look,
            "lastError": self.last_error,
        }
