import os
import sys
import time

os.environ['TZ'] = 'America/Sao_Paulo'
time.tzset()

# 1. Define as variáveis de ambiente diretamente aqui
os.environ['DB_HOSTNAME'] = 'dlancioni.mysql.pythonanywhere-services.com'
os.environ['DB_USERNAME'] = 'dlancioni'
os.environ['DB_PASSWORD'] = '123456abcdef'
os.environ['DB_NAME'] = 'dlancioni$recon'
os.environ['FILE_PATH'] = '/home/dlancioni/www/recon/upload'

# Adiciona o caminho do seu projeto ao Python Path
path = '/home/dlancioni/www/recon'
if path not in sys.path:
    sys.path.append(path)

# Importa a sua variável 'app' do seu arquivo principal (ex: main.py ou app.py)
from app import app as application