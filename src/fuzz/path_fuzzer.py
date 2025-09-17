# src/fuzz/path_fuzzer.py
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
from urllib.parse import urljoin
from utils.helpers import requests_session
import config

session = requests_session(timeout=config.HTTP_TIMEOUT)

def fuzz_paths(base_url: str, paths: List[str], workers: int = 30) -> List[Dict]:
    found = []
    def check(p):
        url = urljoin(base_url if base_url.endswith("/") else base_url + "/", p)
        try:
            r = session.get(url, timeout=config.HTTP_TIMEOUT, allow_redirects=True)
            if r.status_code != 404 and len(r.content) > 0:
                return {"url": url, "status": r.status_code, "len": len(r.content)}
        except Exception:
            return None
        return None
    with ThreadPoolExecutor(max_workers=workers) as exe:
        for res in exe.map(check, paths):
            if res:
                found.append(res)
    return found
