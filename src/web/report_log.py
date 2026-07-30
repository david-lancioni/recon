import datetime
from flask import render_template, jsonify, session
from src.web.models import db, Recon, User
from src.web.access import get_visible_recon_ids
from src.core.loglib import read_log

_COLUMNS = ['recon', 'usuario', 'level', 'created_at', 'class_name', 'method_name', 'message']

_COLUMN_LABELS = {
    'usuario': 'Usuário',
    'recon': 'Conciliação',
    'level': 'Nivel',
    'created_at': 'Data de Inclusão',
    'class_name': 'Classe',
    'method_name': 'Método',
    'message': 'Mensagem'
}


def _format_created_at(value):
    try:
        return datetime.datetime.fromisoformat(value).strftime('%d/%m/%Y %H:%M:%S')
    except (TypeError, ValueError):
        return value


def register(app):
    @app.route('/report_log')
    def report_log():
        return render_template('report_log.html', current_page='report_log')

    @app.route('/api/report_log')
    def api_report_log():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        user_id    = session['user_id']
        id_company = session['company_id']
        visible_recon_ids = get_visible_recon_ids(id_company, user_id)

        rows = []
        if visible_recon_ids:
            recon_names = dict(db.session.execute(
                db.select(Recon.id, Recon.name)
                .filter_by(id_company=id_company)
                .filter(Recon.id.in_(visible_recon_ids))
            ).all())
            user_names = dict(db.session.execute(
                db.select(User.id, User.name).filter_by(id_company=id_company)
            ).all())

            for id_recon in visible_recon_ids:
                data = read_log(id_company, id_recon)
                if not data:
                    continue
                recon_name = recon_names.get(id_recon, '')
                usuario = user_names.get(data.get('id_user'), '')
                for entry in data.get('entries', []):
                    rows.append([
                        recon_name,
                        usuario,
                        entry.get('level'),
                        entry.get('created_at') or '',
                        entry.get('class_name'),
                        entry.get('method_name'),
                        entry.get('message')
                    ])

        rows.sort(key=lambda r: r[3])
        for row in rows:
            row[3] = _format_created_at(row[3])

        columns = [_COLUMN_LABELS[c] for c in _COLUMNS]
        return jsonify({'columns': columns, 'rows': rows})
