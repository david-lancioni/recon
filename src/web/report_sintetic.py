from flask import render_template, jsonify, session
from src.web.models import db, Recon
from src.core.dblib import DbLib
from src.core.constlib import const
from src.core.baselib import BaseLib

dblib = DbLib()


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

        recons = db.session.execute(
            db.select(Recon.id, Recon.name)
            .filter_by(id_company=id_company, id_user=user_id)
            .order_by(Recon.id)
        ).all()

        rows = []
        cn = dblib.get_connection()
        try:
            for id_recon, recon_name in recons:
                tb1 = BaseLib.get_table_name(id_company, id_recon, 1)
                tb2 = BaseLib.get_table_name(id_company, id_recon, 2)

                log_sql = f"select max(created_at) from tb_log where id_user = {user_id} and id_recon = {id_recon}"
                log_rs = dblib.query(log_sql, cn)
                max_created_at = log_rs[0][0] if log_rs else None
                execution_date = max_created_at.strftime('%d/%m/%Y %H:%M') if max_created_at else ''

                sql = f"""
                select * from
                (
                    select  {const.FIELD_RECON} 'Recon', 'Lado 1' Lado, {const.FIELD_STATUS} 'Status', count({const.FIELD_STATUS}) 'Total' from {tb1} where {const.FIELD_ID_COMPANY} = {id_company} group by {const.FIELD_RECON}, {const.FIELD_STATUS}
                    union all
                    select  {const.FIELD_RECON} 'Recon', 'Lado 2' Lado, {const.FIELD_STATUS} 'Status', count({const.FIELD_STATUS}) 'Total' from {tb2} where {const.FIELD_ID_COMPANY} = {id_company} group by {const.FIELD_RECON}, {const.FIELD_STATUS}
                ) tb
                """
                try:
                    rs = dblib.query(sql, cn)
                except Exception:
                    continue
                for r in rs:
                    rows.append({'id_recon': id_recon, 'recon': recon_name, 'execution_date': execution_date, 'lado': r[1], 'status': r[2], 'total': r[3]})
        finally:
            cn.close()

        return jsonify(rows)
