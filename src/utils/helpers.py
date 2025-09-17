# src/utils/helpers.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def requests_session(timeout: int = 6, max_retries: int = 3) -> requests.Session:
    s = requests.Session()
    retries = Retry(total=max_retries, backoff_factor=0.3,
                    status_forcelist=(429, 500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({"User-Agent": "husk-recon/0.1"})
    s.request_timeout = timeout
    return s
