# src/discovery/hosts.py
from typing import List
from concurrent.futures import ThreadPoolExecutor
import config
from utils.helpers import requests_session

session = requests_session(timeout=config.HTTP_TIMEOUT)

def is_live_http(host: str) -> bool:
    for proto in ("http://", "https://"):
        url = proto + host
        try:
            r = session.get(url, timeout=config.HTTP_TIMEOUT, allow_redirects=True)
            if 100 <= r.status_code < 600:
                return True
        except Exception:
            continue
    return False

def filter_live(hosts: List[str], workers: int = 20) -> List[str]:
    live = []
    with ThreadPoolExecutor(max_workers=workers) as exe:
        for res in exe.map(lambda h: h if is_live_http(h) else None, hosts):
            if res:
                live.append(res)
    return live
