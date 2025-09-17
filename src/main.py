# src/main.py
"""
Entrypoint CLI for husk — Recon automation helper.
Run examples:
  python3 src/main.py --help
  python3 src/main.py subs example.com
  python3 src/main.py recon example.com --timestamp --debug
"""

from pathlib import Path
import multiprocessing
from typing import List, Optional

import typer

import config
from logging_conf import setup_logging
from utils.output import save_json, pretty
from discovery.subdomains import bruteforce_subdomains
from discovery.hosts import filter_live
from screenshots.screenshots import screenshot_url
from scanner.nmap_integration import run_nmap
from fuzz.path_fuzzer import fuzz_paths

app = typer.Typer(help="husk — Recon automation helper (use responsibly)")

TOOL_NAME = "husk"
VERSION = "0.1.0"

BANNER = r"""
========================================
 _   _ _    _  ____  _  __  _  __
| | | | |  | |/ ___|| |/ / | |/ /
| |_| | |  | |\___ \| ' /  | ' / 
|  _  | |__| | ___) | . \  | . \ 
|_| |_| \____/ |____/|_|\_\ |_|  
========================================
"""

def _make_logger(level: str = "INFO"):
    # setup_logging returns a logger configured with RichHandler
    logger = setup_logging(level)
    return logger

def load_wordlist(path: Path) -> List[str]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]

# callback runs before every command (including --help)
@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    # print colored banner and welcome/warning using typer.style
    typer.echo(typer.style(BANNER, fg=typer.colors.GREEN, bold=True))
    typer.echo(typer.style(f"{TOOL_NAME} v{VERSION}", fg=typer.colors.CYAN, bold=True))
    typer.echo(typer.style("⚠ Use responsibly. Only run against authorized targets.\n", fg=typer.colors.YELLOW))

    # if no subcommand, show help
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())

# ---- commands ----

@app.command()
def subs(
    domain: str,
    wl: Path = typer.Option(config.DEFAULT_WORDLIST, help="subdomain wordlist"),
    workers: Optional[int] = typer.Option(None, help="number of threads (auto if omitted)"),
    resolvers: str = typer.Option("", help="comma-separated DNS resolvers, e.g. 8.8.8.8,1.1.1.1"),
    timestamp: bool = typer.Option(False, "--timestamp", "-t", help="append UTC timestamp to results filename"),
    debug: bool = typer.Option(False, "--debug", "-d", help="enable debug logging"),
):
    """
    Run subdomain bruteforce resolution and save results.
    """
    logger = _make_logger("DEBUG" if debug else "INFO")

    workers_count = workers if workers else min(200, multiprocessing.cpu_count() * 10)
    wl_path = Path(wl)
    if not wl_path.exists():
        typer.echo(typer.style(f"[subs] Wordlist not found: {wl_path.resolve()}", fg=typer.colors.RED))
        raise typer.Exit(code=1)

    entries = load_wordlist(wl_path)
    typer.echo(typer.style(f"[subs] domain={domain} wordlist={wl_path.resolve()} entries={len(entries)} workers={workers_count}", fg=typer.colors.BLUE))

    resolvers_list = [r.strip() for r in resolvers.split(",") if r.strip()]
    if resolvers_list:
        typer.echo(typer.style(f"[subs] using resolvers: {resolvers_list}", fg=typer.colors.MAGENTA))
    else:
        typer.echo(typer.style(f"[subs] using default public resolvers (Google/Cloudflare)", fg=typer.colors.MAGENTA))

    found = bruteforce_subdomains(domain, entries, workers=workers_count,
                                  nameservers=resolvers_list if resolvers_list else None)

    saved_path = save_json(f"{domain}_subdomains", found, timestamp=timestamp)
    typer.echo(typer.style(f"[subs] saved results -> {saved_path.resolve()}", fg=typer.colors.GREEN))
    pretty(found)


@app.command()
def hosts_cmd(domain: str, wl: Path = typer.Option(config.DEFAULT_WORDLIST, help="subdomain wordlist"),
              timestamp: bool = typer.Option(False, "--timestamp", "-t", help="append UTC timestamp to results filename"),
              debug: bool = typer.Option(False, "--debug", "-d", help="enable debug logging")):
    """
    Find live hosts from subdomain wordlist and save results.
    """
    logger = _make_logger("DEBUG" if debug else "INFO")
    wl_list = load_wordlist(wl)
    typer.echo(typer.style(f"[hosts] domain={domain} wordlist_entries={len(wl_list)}", fg=typer.colors.BLUE))
    subs_result = bruteforce_subdomains(domain, wl_list)
    live = filter_live(list(subs_result.keys()))
    saved = save_json(f"{domain}_live", {"live": live}, timestamp=timestamp)
    typer.echo(typer.style(f"[hosts] found {len(live)} live hosts, saved -> {saved.resolve()}", fg=typer.colors.GREEN))
    pretty({"live": live})


@app.command()
def screenshots_cmd(domain: str,
                    wl: Path = typer.Option(config.DEFAULT_WORDLIST, help="subdomain wordlist"),
                    outdir: Path = typer.Option(config.SCREENSHOT_DIR, help="output directory for screenshots"),
                    timestamp: bool = typer.Option(False, "--timestamp", "-t", help="append UTC timestamp to results filename"),
                    debug: bool = typer.Option(False, "--debug", "-d", help="enable debug logging")):
    """
    Take screenshots of live hosts and save mapping.
    """
    logger = _make_logger("DEBUG" if debug else "INFO")
    wl_list = load_wordlist(wl)
    sub_result = bruteforce_subdomains(domain, wl_list)
    live = filter_live(list(sub_result.keys()))
    typer.echo(typer.style(f"[screenshots] taking screenshots of {len(live)} live hosts", fg=typer.colors.BLUE))
    shots = {}
    for h in live:
        url = f"https://{h}"
        try:
            p = screenshot_url(url, outdir=outdir)
            shots[h] = str(p)
            typer.echo(typer.style(f"[screenshots] saved -> {p}", fg=typer.colors.GREEN))
        except Exception as e:
            shots[h] = f"error:{e}"
            typer.echo(typer.style(f"[screenshots] error for {h}: {e}", fg=typer.colors.RED))
    saved = save_json(f"{domain}_screenshots", shots, timestamp=timestamp)
    typer.echo(typer.style(f"[screenshots] saved mapping -> {saved.resolve()}", fg=typer.colors.GREEN))
    pretty(shots)


@app.command()
def nmap_cmd(target: str,
             timestamp: bool = typer.Option(False, "--timestamp", "-t", help="append UTC timestamp to results filename"),
             debug: bool = typer.Option(False, "--debug", "-d", help="enable debug logging")):
    """
    Run nmap on a target host and save results.
    """
    logger = _make_logger("DEBUG" if debug else "INFO")
    typer.echo(typer.style(f"[nmap] running nmap against {target} (this requires system 'nmap' installed)", fg=typer.colors.BLUE))
    try:
        res = run_nmap(target)
    except Exception as e:
        res = {"error": str(e)}
    saved = save_json(f"{target}_nmap", res, timestamp=timestamp)
    typer.echo(typer.style(f"[nmap] saved -> {saved.resolve()}", fg=typer.colors.GREEN))
    pretty(res)


@app.command()
def fuzz_cmd(domain: str, paths: Path = typer.Option(config.DEFAULT_PATH_WORDLIST, help="paths wordlist"),
             timestamp: bool = typer.Option(False, "--timestamp", "-t", help="append UTC timestamp to results filename"),
             debug: bool = typer.Option(False, "--debug", "-d", help="enable debug logging")):
    """
    Fuzz paths on the first live host found and save results.
    """
    logger = _make_logger("DEBUG" if debug else "INFO")
    wl_list = load_wordlist(config.DEFAULT_WORDLIST)
    subs_result = bruteforce_subdomains(domain, wl_list)
    live = filter_live(list(subs_result.keys()))
    if not live:
        typer.echo(typer.style("[fuzz] no live hosts found for fuzzing.", fg=typer.colors.YELLOW))
        raise typer.Exit(code=1)
    target = f"https://{live[0]}"
    typer.echo(typer.style(f"[fuzz] fuzzing {target} with {paths} entries", fg=typer.colors.BLUE))
    path_list = load_wordlist(paths)
    res = fuzz_paths(target, path_list)
    saved = save_json(f"{domain}_fuzz_first", res, timestamp=timestamp)
    typer.echo(typer.style(f"[fuzz] saved -> {saved.resolve()}", fg=typer.colors.GREEN))
    pretty(res)


@app.command()
def recon(domain: str,
          wl: Path = typer.Option(config.DEFAULT_WORDLIST, help="subdomain wordlist"),
          paths: Path = typer.Option(config.DEFAULT_PATH_WORDLIST, help="paths wordlist"),
          no_screenshots: bool = typer.Option(False, "--no-screenshots", "-n", help="skip screenshots"),
          timestamp: bool = typer.Option(False, "--timestamp", "-t", help="append UTC timestamp to results filenames"),
          debug: bool = typer.Option(False, "--debug", "-d", help="enable debug logging")):
    """
    Full recon pipeline (subdomains -> hosts -> screenshots -> nmap -> fuzz).
    """
    logger = _make_logger("DEBUG" if debug else "INFO")
    typer.echo(typer.style(BANNER, fg=typer.colors.GREEN, bold=True))
    typer.echo(typer.style(f"Welcome to {TOOL_NAME} — use responsibly. Only run against authorized targets.\n", fg=typer.colors.CYAN, bold=True))

    wl_list = load_wordlist(wl)
    typer.echo(typer.style(f"[recon] running subdomain bruteforce ({len(wl_list)} entries)", fg=typer.colors.BLUE))
    sub_result = bruteforce_subdomains(domain, wl_list)
    save_json(f"{domain}_subdomains", sub_result, timestamp=timestamp)

    live = filter_live(list(sub_result.keys()))
    save_json(f"{domain}_live", {"live": live}, timestamp=timestamp)
    typer.echo(typer.style(f"[recon] {len(live)} live hosts found", fg=typer.colors.BLUE))

    shots = {}
    if not no_screenshots:
        for h in live:
            url = f"https://{h}"
            try:
                p = screenshot_url(url)
                shots[h] = str(p)
                typer.echo(typer.style(f"[recon] screenshot -> {p}", fg=typer.colors.GREEN))
            except Exception as e:
                shots[h] = f"error:{e}"
    save_json(f"{domain}_screenshots", shots, timestamp=timestamp)

    nmap_res = []
    if live:
        try:
            nmap_res = run_nmap(live[0])
        except Exception as e:
            nmap_res = {"error": str(e)}
    save_json(f"{domain}_nmap_first", nmap_res, timestamp=timestamp)

    fuzz_res = []
    if live:
        try:
            fuzz_res = fuzz_paths(f"https://{live[0]}", load_wordlist(paths))
        except Exception as e:
            fuzz_res = {"error": str(e)}
    save_json(f"{domain}_fuzz_first", fuzz_res, timestamp=timestamp)

    typer.echo(typer.style(f"Recon for {domain} complete. Results saved in {config.RESULTS_DIR.resolve()}", fg=typer.colors.CYAN))


if __name__ == "__main__":
    app()

