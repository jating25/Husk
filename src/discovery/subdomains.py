# src/discovery/subdomains.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import dns.resolver
import dns.exception
import random
import time
import sys

# Configurable resolvers: public resolvers reduce false negatives
DEFAULT_RESOLVERS = ["8.8.8.8", "1.1.1.1"]  # Google, Cloudflare

def _get_resolver(nameservers: Optional[List[str]] = None) -> dns.resolver.Resolver:
    r = dns.resolver.Resolver()
    if nameservers:
        r.nameservers = nameservers
    return r

def _resolve_a(host: str, resolver: dns.resolver.Resolver, lifetime: float = 3.0) -> List[str]:
    try:
        ans = resolver.resolve(host, "A", lifetime=lifetime)
        return [r.to_text() for r in ans]
    except dns.exception.DNSException:
        return []

def detect_wildcard(domain: str, resolver: dns.resolver.Resolver) -> bool:
    """Return True if wildcard A records seem present for domain."""
    # try a few random labels; if they all resolve to the same IPs, it's likely wildcard
    tries = []
    for _ in range(3):
        rnd = f"w{int(time.time()*1000)%100000}-{random.randint(1000,9999)}"
        fqdn = f"{rnd}.{domain}"
        ips = _resolve_a(fqdn, resolver)
        if ips:
            tries.append(tuple(sorted(ips)))
    # if we got consistent non-empty results, treat as wildcard
    if len(tries) >= 2 and all(t == tries[0] for t in tries):
        return True
    return False

def bruteforce_subdomains(domain: str, wordlist: List[str], workers: int = 40,
                          nameservers: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """
    Bruteforce subdomains by DNS A record resolution.

    Returns: dict mapping 'sub.domain' -> [ip, ...]
    """
    resolver = _get_resolver(nameservers or DEFAULT_RESOLVERS)

    # detect wildcard DNS — if present, we'll try to filter results later
    wildcard = detect_wildcard(domain, resolver)
    if wildcard:
        print(f"[subdomains] Warning: wildcard DNS detected for {domain}. Results may contain false positives.", file=sys.stderr)

    found: Dict[str, List[str]] = {}

    def task(sub):
        fqdn = f"{sub}.{domain}"
        ips = _resolve_a(fqdn, resolver)
        # if wildcard present, we still keep only if different from wildcard sample
        return fqdn, ips

    with ThreadPoolExecutor(max_workers=workers) as exe:
        futures = {exe.submit(task, w): w for w in wordlist}
        for fut in as_completed(futures):
            fqdn, ips = fut.result()
            if ips:
                # if wildcard was detected, do one extra check against a random unseen label
                if wildcard:
                    # quick check: resolve a random unlikely name; if equal, skip
                    rnd = f"random-skip-{random.randint(10000,99999)}.{domain}"
                    sample = _resolve_a(rnd, resolver)
                    if sample and sorted(sample) == sorted(ips):
                        # likely wildcard match — skip
                        continue
                # record hit
                found[fqdn] = ips
                print(f"[subdomains] found: {fqdn} -> {ips}")
    return found

# quick manual test
if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    wl = ["www","mail","dev","api","test","staging","admin"]
    print(bruteforce_subdomains(d, wl, workers=10))
