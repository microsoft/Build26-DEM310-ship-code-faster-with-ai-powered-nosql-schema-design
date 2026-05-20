"""Tiny shared helper: tee stdout/stderr to a `--log` path.

Used by every `scripts/*_iteration_*.py` wrapper so the runtime obeys
the convention from `docs/03-walkthrough/CONVENTIONS.md`:

    > Filenames bind to content. The script writes its own file via a
    > `--log <path>` flag rather than relying on `Tee-Object`.
"""

from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path


class _Tee:
    """Forward writes to multiple streams (stdout + a log file)."""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for s in self._streams:
            try:
                s.write(data)
                s.flush()
            except (ValueError, OSError):
                # Underlying stream may be closed during interpreter
                # shutdown; ignore so we don't trip the unraisable hook.
                pass

    def flush(self):
        for s in self._streams:
            try:
                s.flush()
            except (ValueError, OSError):
                pass


def attach_log(log_path: str | os.PathLike | None):
    """Open ``log_path`` for write+tee. Returns the file handle (or None).

    Parent directories are created on demand so callers can pass paths
    like ``logs/iter-01/seed.log`` without pre-creating the folder.

    Registers an ``atexit`` hook that restores the original
    stdout/stderr **before** closing the log file, so Python's shutdown
    flush doesn't write to a closed handle (which would otherwise raise
    a ``ValueError`` and surface as a non-zero process exit code).
    """
    if not log_path:
        return None
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fh = p.open("w", encoding="utf-8")
    real_stdout, real_stderr = sys.__stdout__, sys.__stderr__
    sys.stdout = _Tee(real_stdout, fh)
    sys.stderr = _Tee(real_stderr, fh)

    def _cleanup():
        sys.stdout = real_stdout
        sys.stderr = real_stderr
        try:
            fh.close()
        except OSError:
            pass

    atexit.register(_cleanup)
    return fh
