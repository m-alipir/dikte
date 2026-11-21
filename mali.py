"""Personal launch preset with separate settings and the existing local models."""

import os
from pathlib import Path

from dikte import paths

paths.CONFIG_DIR = paths.DATA_DIR / "mali-settings"

from dikte import config, ggml  # noqa: E402

config.DEFAULTS.update(local_progressive=True, cleanup_enabled=False, auto_paste=False,
                       language="tr", keep_audio=True)
available = sorted((ggml.MODELS_DIR / "whisper").glob("*large-v3-turbo*.bin"))
if available:
    config.DEFAULTS["local_model"] = available[-1].name

bundled = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Dikte/bin"
if (bundled / "ffmpeg.exe").is_file():
    os.environ["PATH"] = str(bundled) + os.pathsep + os.environ.get("PATH", "")

from dikte.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
