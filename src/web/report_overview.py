from flask import render_template, jsonify, session
from src.web.models import db, Recon
from src.core.dblib import DbLib
from src.core.constlib import const
from src.core.baselib import BaseLib
from src.web.access import get_visible_recon_ids

dblib = DbLib()


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
            cn = dblib.get_connection()
            try:
                for id_recon, recon_name in recons:
                    tb1 = BaseLib.get_table_name(id_company, id_recon, 1)
                    tb2 = BaseLib.get_table_name(id_company, id_recon, 2)

                    sql = f"""
                    select {const.FIELD_STATUS} 'Status', count({const.FIELD_STATUS}) 'Total' from {tb1} where {const.FIELD_ID_COMPANY} = {id_company} group by {const.FIELD_STATUS}
                    union all
                    select {const.FIELD_STATUS} 'Status', count({const.FIELD_STATUS}) 'Total' from {tb2} where {const.FIELD_ID_COMPANY} = {id_company} group by {const.FIELD_STATUS}
                    """
                    try:
                        rs = dblib.query(sql, cn)
                    except Exception:
                        continue
                    recon_totals = {'Batido': 0, 'Divergente': 0, 'Órfão': 0}
                    for status, total in rs:
                        status_key = status.decode() if isinstance(status, (bytes, bytearray)) else status
                        if status_key in totals:
                            totals[status_key] += total
                            recon_totals[status_key] += total
                    per_recon.append((id_recon, recon_name, recon_totals))
            finally:
                cn.close()
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
