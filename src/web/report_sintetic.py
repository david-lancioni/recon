import datetime
from flask import render_template, jsonify, session
from src.web.models import db, Recon
from src.core.constlib import const
from src.web.access import get_visible_recon_ids
from src.core.loglib import read_log
from src.core.resultlib import read_result


def _count_by_status(table_dump):
    counts = {}
    if not table_dump:
        return counts
    columns = table_dump.get('columns', [])
    if const.FIELD_STATUS not in columns:
        return counts
    idx = columns.index(const.FIELD_STATUS)
    for row in table_dump.get('rows', []):
        status = row[idx]
        counts[status] = counts.get(status, 0) + 1
    return counts


def register(app):
    @app.route('/report_sintetic')
    def report_sintetic():
        return render_template('report_sintetic.html', current_page='report_sintetic')

    @app.route('/api/report_sintetic')
    def api_report_sintetic():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        user_id    = session['user_id']
        id_company = session['company_id']

        visible_recon_ids = get_visible_recon_ids(id_company, user_id)
        if not visible_recon_ids:
            return jsonify([])

        recon_query = (
            db.select(Recon.id, Recon.name)
            .filter_by(id_company=id_company)
            .filter(Recon.id.in_(visible_recon_ids))
            .order_by(Recon.id)
        )
        recons = db.session.execute(recon_query).all()

        rows = []
        for id_recon, recon_name in recons:
            log_data = read_log(id_company, id_recon) or {}
            created_at_values = [e.get('created_at') for e in log_data.get('entries', []) if e.get('created_at')]
            max_created_at = max(created_at_values) if created_at_values else None
            execution_date = datetime.datetime.fromisoformat(max_created_at).strftime('%d/%m/%Y %H:%M') if max_created_at else ''

            result = read_result(id_company, id_recon)
            if not result:
                continue
            for side_key, side_label in (('lado1', 'Lado 1'), ('lado2', 'Lado 2')):
                for status, total in _count_by_status(result.get(side_key)).items():
                    rows.append({
                        'id_recon': id_recon, 'recon': recon_name, 'execution_date': execution_date,
                        'lado': side_label, 'status': status, 'total': total
                    })

        return jsonify(rows)
