# src/utils/output.py
import json
from pathlib import Path
from datetime import datetime
import config


def save_json(name, data, timestamp: bool = False):
    """
    Save dict `data` to results/{name}.json
    If timestamp=True, append UTC timestamp to filename.
    Returns Path to saved file.
    """
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if timestamp:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{ts}.json"
    else:
        filename = f"{name}.json"

    path = config.RESULTS_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return path


def pretty(data):
    """
    Pretty print dict or list to console.
    """
    try:
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[pretty] error: {e} -> raw={data}")
