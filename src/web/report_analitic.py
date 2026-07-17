import datetime
import decimal
from flask import render_template, jsonify, session, abort
from src.web.models import db, Recon
from src.core.dblib import DbLib
from src.core.constlib import const
from src.core.baselib import BaseLib

dblib = DbLib()

_HIDDEN_COLUMNS = {const.FIELD_SIDE, const.FIELD_ID_USER, const.FIELD_ID_STATUS, const.FIELD_DATE}

_COLUMN_LABELS = {
    const.FIELD_ID: 'ID',
    const.FIELD_DATE: 'Data da Execução',
    const.FIELD_RECON: 'Recon',
    const.FIELD_RULE: 'Regra',
    const.FIELD_STATUS: 'Status'
}


def _serialize(value):
    if isinstance(value, datetime.datetime):
        return value.strftime('%d/%m/%Y %H:%M:%S')
    if isinstance(value, datetime.date):
        return value.strftime('%d/%m/%Y')
    if isinstance(value, decimal.Decimal):
        return float(value)
    return value


def _fetch_table(cn, tablename):
    try:
        cursor = cn.cursor()
        cursor.execute(f"select * from {tablename}")
        all_columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
    except Exception:
        return {'columns': [], 'rows': []}
    keep_idx = [i for i, c in enumerate(all_columns) if c not in _HIDDEN_COLUMNS]
    columns = [_COLUMN_LABELS.get(all_columns[i], all_columns[i]) for i in keep_idx]
    return {
        'columns': columns,
        'rows': [[_serialize(row[i]) for i in keep_idx] for row in rows]
    }


def register(app):
    @app.route('/report_analitic')
    def report_analitic():
        return render_template('report_analitic.html', current_page='report_analitic')

    @app.route('/api/report_analitic/<int:id_recon>')
    def api_report_analitic(id_recon):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        user_id = session['user_id']
        recon = db.session.execute(
            db.select(Recon).filter_by(id=id_recon, id_company=session['company_id'], id_user=user_id)
        ).scalar_one_or_none()
        if not recon:
            abort(404)

        cn = dblib.get_connection()
        try:
            lado1 = _fetch_table(cn, BaseLib.get_table_name(user_id, id_recon, 1))
            lado2 = _fetch_table(cn, BaseLib.get_table_name(user_id, id_recon, 2))

            log_sql = f"select max(created_at) from tb_log where id_user = {user_id} and id_recon = {id_recon}"
            log_rs = dblib.query(log_sql, cn)
            max_created_at = log_rs[0][0] if log_rs else None
            execution_date = max_created_at.strftime('%d/%m/%Y %H:%M') if max_created_at else None
        finally:
            cn.close()

        return jsonify({'execution_date': execution_date, 'lado1': lado1, 'lado2': lado2})
