# src/scanner/nmap_integration.py
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict
import config

def run_nmap(target: str, ports: str = None, extra_args: str = None) -> List[Dict]:
    ports = ports or config.NMAP_PORTS
    extra_args = extra_args or config.NMAP_EXTRA_ARGS
    tmp_xml = Path("tmp_nmap.xml")
    cmd = ["nmap", *extra_args.split(), "-p", ports, "-oX", str(tmp_xml), target]
    subprocess.run(cmd, check=False)
    return parse_nmap_xml(tmp_xml)

def parse_nmap_xml(xml_path: Path) -> List[Dict]:
    if not xml_path.exists():
        return []
    tree = ET.parse(xml_path)
    root = tree.getroot()
    results = []
    for host in root.findall("host"):
        addr_el = host.find("address")
        addr = addr_el.attrib.get("addr") if addr_el is not None else None
        ports = []
        for p in host.findall(".//port"):
            state = p.find("state")
            svc = p.find("service")
            ports.append({
                "port": p.attrib.get("portid"),
                "protocol": p.attrib.get("protocol"),
                "state": state.attrib.get("state") if state is not None else None,
                "service": svc.attrib.get("name") if svc is not None else None,
            })
        results.append({"addr": addr, "ports": ports})
    return results
