import logging
import os
import re
import sys

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

# Sem isso, o módulo logging usa o "handler de última instância" (só mostra WARNING+, sem
# timestamp) - os logs INFO do job (um por passo) não apareceriam no console/log do cron.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    stream=sys.stdout
)

# Load etc/environment.txt into os.environ (bash export format) - mesma lógica do app.py,
# necessária aqui porque o script roda fora do processo do Flask (chamado direto pelo cron)
_env_file = os.path.join(_project_root, 'etc', 'environment.txt')
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            m = re.match(r'^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)=["\']?(.*?)["\']?\s*$', _line.strip())
            if m:
                os.environ.setdefault(m.group(1), m.group(2))

from src.core.joblib import JobLib

if __name__ == '__main__':
    JobLib().run()
