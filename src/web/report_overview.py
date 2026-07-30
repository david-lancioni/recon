from flask import render_template, jsonify, session
from src.web.models import db, Recon
from src.core.constlib import const
from src.web.access import get_visible_recon_ids
from src.core.resultlib import read_result

_STATUSES = ('Batido', 'Divergente', 'Órfão')


def _count_by_status(table_dump):
    counts = {status: 0 for status in _STATUSES}
    if not table_dump:
        return counts
    columns = table_dump.get('columns', [])
    if const.FIELD_STATUS not in columns:
        return counts
    idx = columns.index(const.FIELD_STATUS)
    for row in table_dump.get('rows', []):
        status = row[idx]
        if status in counts:
            counts[status] += 1
    return counts


def register(app):
    @app.route('/report_overview')
    def report_overview():
        return render_template('report_overview.html', current_page='report_overview')

    @app.route('/api/report_overview')
    def api_report_overview():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        user_id    = session['user_id']
        id_company = session['company_id']

        try:
            visible_recon_ids = get_visible_recon_ids(id_company, user_id)
            if not visible_recon_ids:
                return jsonify({
                    'batido': 0, 'divergente': 0, 'orfao': 0,
                    'top_batido': None, 'top_divergente': None, 'top_orfao': None
                })

            recon_query = (
                db.select(Recon.id, Recon.name)
                .filter_by(id_company=id_company)
                .filter(Recon.id.in_(visible_recon_ids))
            )
            recons = db.session.execute(recon_query).all()

            totals = {'Batido': 0, 'Divergente': 0, 'Órfão': 0}
            per_recon = []
            for id_recon, recon_name in recons:
                result = read_result(id_company, id_recon)
                if not result:
                    continue
                recon_totals = {'Batido': 0, 'Divergente': 0, 'Órfão': 0}
                for side_key in ('lado1', 'lado2'):
                    side_counts = _count_by_status(result.get(side_key))
                    for status in totals:
                        recon_totals[status] += side_counts[status]
                        totals[status] += side_counts[status]
                per_recon.append((id_recon, recon_name, recon_totals))
        except Exception as ex:
            return jsonify({'error': f'Erro ao carregar visão geral: {ex}'}), 500

        def top_recon(status_key):
            candidates = [(rid, name, t[status_key]) for rid, name, t in per_recon if t[status_key] > 0]
            if not candidates:
                return None
            rid, name, _ = max(candidates, key=lambda c: c[2])
            return {'id': rid, 'name': name}

        return jsonify({
            'batido': totals['Batido'],
            'divergente': totals['Divergente'],
            'orfao': totals['Órfão'],
            'top_batido': top_recon('Batido'),
            'top_divergente': top_recon('Divergente'),
            'top_orfao': top_recon('Órfão')
        })
