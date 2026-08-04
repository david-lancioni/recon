import logging
import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
sys.path.insert(0, _project_root)

# Sem isso, o módulo logging usa o "handler de última instância" (só mostra WARNING+, sem
# timestamp) - os logs INFO do job (um por passo) não apareceriam no console/log do cron.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    stream=sys.stdout
)

# Load run.env (mesma pasta deste script) into os.environ (bash export format) -
# necessário aqui porque o script roda fora do processo do Flask (chamado direto pelo cron)
_env_file = os.path.join(_script_dir, 'run.env')
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip().removeprefix('export ')
            if _line and '=' in _line:
                key, _, value = _line.partition('=')
                os.environ.setdefault(key.strip(), value.strip().strip('"\''))

from src.core.joblib import JobLib

if __name__ == '__main__':
    JobLib().run()
