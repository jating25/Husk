# src/config.py
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# root of the package (absolute)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Use absolute dirs so working directory doesn't matter
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))
SCREENSHOT_DIR = Path(os.getenv("SCREENSHOT_DIR", PROJECT_ROOT / "screenshots"))
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", PROJECT_ROOT / "results"))

# ensure these directories exist immediately
for d in (DATA_DIR, SCREENSHOT_DIR, RESULTS_DIR):
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # avoid raising on import; the caller can see logs/errors
        print(f"[config] could not create dir {d}: {e}")

SHODAN_API_KEY = os.getenv("SHODAN_API_KEY", "")
DEFAULT_WORDLIST = Path(os.getenv("DEFAULT_WORDLIST", DATA_DIR / "subdomains.txt"))
DEFAULT_PATH_WORDLIST = Path(os.getenv("PATH_WORDLIST", DATA_DIR / "paths.txt"))
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "6"))
NMAP_PORTS = os.getenv("NMAP_PORTS", "1-1000")
NMAP_EXTRA_ARGS = os.getenv("NMAP_EXTRA_ARGS", "-sV -sC")
