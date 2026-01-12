import datetime
import json

from .constants import ADDIN_VERSION
from .paths import debug_path


def log(message: str) -> None:
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "type": "log",
            "timestamp": ts,
            "version": ADDIN_VERSION,
            "message": message,
        }
        with open(debug_path(), "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False))
            handle.write("\n")
    except Exception:
        pass
