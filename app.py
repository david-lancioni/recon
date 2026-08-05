import os, re
from flask import Flask, request
from src.web.models import db

# Load etc/environment.txt into os.environ (bash export format)
_env_file = os.path.join(os.path.dirname(__file__), 'etc', 'environment.txt')
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            m = re.match(r'^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)=["\']?(.*?)["\']?\s*$', _line.strip())
            if m:
                os.environ.setdefault(m.group(1), m.group(2))

from src.web import pages, auth, user, recon, ds, field, rule, rule_field, profile, transaction, profile_transaction, run, report_sintetic, report_analitic, report_log, report_overview, company, area, area_user, area_recon, lead
from src.web.tokensession import TokenSessionInterface

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.environ['DB_USERNAME']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOSTNAME']}/{os.environ['DB_NAME']}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'init_command': "SET time_zone = '-03:00'"},
    'pool_pre_ping': True,
    'pool_recycle': 280,
    # Teto real é max_user_connections da conta MySQL (22), compartilhado entre os 3
    # processos worker e TODOS os pools que usam essas credenciais (este + o pool DB_NAME
    # do dblib). Sem isso, o default do SQLAlchemy (pool_size=5, max_overflow=10 = até
    # 15 conexões só deste pool, por processo) já estoura o teto sozinho.
    'pool_size': int(os.getenv('SQLALCHEMY_POOL_SIZE', '3')),
    'max_overflow': int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', '0')),
    'pool_timeout': int(os.getenv('SQLALCHEMY_POOL_TIMEOUT', '60')),
}
app.secret_key = os.environ['SECRET_KEY']
app.session_interface = TokenSessionInterface()

db.init_app(app)

@app.after_request
def no_cache_api(response):
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

pages.register(app)
auth.register(app)
user.register(app)
recon.register(app)
ds.register(app)
field.register(app)
rule.register(app)
rule_field.register(app)
profile.register(app)
transaction.register(app)
profile_transaction.register(app)
run.register(app)
report_sintetic.register(app)
report_analitic.register(app)
report_log.register(app)
report_overview.register(app)
company.register(app)
area.register(app)
area_user.register(app)
area_recon.register(app)
lead.register(app)

if __name__ == '__main__':
    app.run(debug=True)
