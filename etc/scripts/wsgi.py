import os
import sys
import time

os.environ['TZ'] = 'America/Sao_Paulo'
time.tzset()

# 1. Chave que criptografa a sessão do usuário.
os.environ['SECRET_KEY'] = 'J8WBXXnRvmr1fVWuXYayjVMh41zk5YqWDiGqWbICdxQ='

# 2. Credenciais do banco de dados MySQL.
os.environ['DB_HOSTNAME'] = 'dlancioni.mysql.pythonanywhere-services.com'
os.environ['DB_USERNAME'] = 'dlancioni'
os.environ['DB_PASSWORD'] = '123456abcdef'
os.environ['DB_NAME'] = 'dlancioni$recon'

# Adiciona o caminho do seu projeto ao Python Path
path = '/home/dlancioni/www/recon'
if path not in sys.path:
    sys.path.append(path)

# Importa a sua variável 'app' do seu arquivo principal (ex: main.py ou app.py)
from app import app as application