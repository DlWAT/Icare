"""Small shared helpers used by the REST blueprints.

Keeping file-path sanitising in one place means the sequence, live and palette
APIs cannot drift apart on how they treat user-supplied names.
"""

from __future__ import annotations

import os

from werkzeug.utils import secure_filename


def safe_json_path(name: str, directory: str) -> str | None:
    """Return an absolute, sanitized ``.json`` path inside ``directory``.

    ``None`` is returned when ``name`` cannot be turned into a safe file name
    (empty input, hidden file, or a name that sanitises away to nothing).
    """
    if not name:
        return None
    sanitized = secure_filename(name)
    if not sanitized.lower().endswith(".json"):
        sanitized += ".json"
    if not sanitized or sanitized.startswith("."):
        return None
    return os.path.join(directory, sanitized)
