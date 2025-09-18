# Husk

Husk is a professional recon automation tool for ethical hacking and penetration testing.

## Features

- Subdomain discovery
- Live host detection
- Screenshots of live hosts
- Nmap scanning integration
- Path fuzzing
- Full recon pipeline

## Installation

```bash
git clone https://github.com/jating25/Husk.git 
cd Husk
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Usage
# Show all CLI commands
python3 src/main.py --help

# Subdomain discovery
python3 src/main.py subs example.com

# Full recon pipeline
python3 src/main.py recon example.com



```

##DISCLAIMER

Husk – Recon Automation Tool is intended for educational and ethical purposes only.

By using this tool, you agree to the following:

Authorized Use Only
You must only run Husk against systems you own or have explicit permission to test. Unauthorized scanning or hacking of third-party systems is illegal and punishable under law.

No Liability
The creators and maintainers of Husk are not responsible for any damage, data loss, or legal consequences arising from misuse of the tool.

Ethical Use
Husk is designed for penetration testing, security research, and learning purposes. Any use beyond this scope is strictly prohibited.

Compliance
Always ensure compliance with local laws, organizational policies, and cybersecurity regulations before using Husk.

