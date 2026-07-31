import datetime
from flask import render_template, jsonify, session, abort
from src.web.models import db, Recon
from src.core.dblib import DbLib
from src.core.constlib import const
from src.web.access import get_visible_recon_ids
from src.core.loglib import read_log
from src.core.resultlib import read_result

dblib = DbLib()

_HIDDEN_COLUMNS = {const.FIELD_SIDE, const.FIELD_ID_USER, const.FIELD_ID_COMPANY, const.FIELD_ID_STATUS, const.FIELD_DATE, const.FIELD_ID_RECON}

_COLUMN_LABELS = {
    const.FIELD_ID: 'ID',
    const.FIELD_DATE: 'Data da Execução',
    const.FIELD_RECON: 'Conciliação',
    const.FIELD_RULE: 'Regra',
    const.FIELD_STATUS: 'Status'
}

_DIFF_SUFFIX = ' (Diferença)'


def _fetch_table(table_dump, field_order):
    if not table_dump:
        return {'columns': [], 'rows': []}
    all_columns = table_dump.get('columns', [])
    rows = table_dump.get('rows', [])
    keep_idx = [i for i, c in enumerate(all_columns) if c not in _HIDDEN_COLUMNS]

    def sort_key(i):
        name = all_columns[i]
        if name.endswith(_DIFF_SUFFIX):
            base = name[:-len(_DIFF_SUFFIX)]
            return (2, field_order.index(base) if base in field_order else len(field_order))
        if name in field_order:
            return (1, field_order.index(name))
        return (0, i)

    keep_idx = sorted(keep_idx, key=sort_key)
    columns = [_COLUMN_LABELS.get(all_columns[i], all_columns[i]) for i in keep_idx]
    return {
        'columns': columns,
        'rows': [[row[i] for i in keep_idx] for row in rows]
    }


def _get_field_order(cn1, id_recon, side):
    sql = f"""
    select f.name
    from tb_field f
    inner join tb_ds d on f.id_ds = d.id
    where d.id_recon = {id_recon} and d.id_side = {side}
    order by f.position
    """
    rows = dblib.query(sql, cn1)
    return [row[0] for row in rows]


def register(app):
    @app.route('/report_analitic')
    def report_analitic():
        return render_template('report_analitic.html', current_page='report_analitic')

    @app.route('/api/report_analitic/<int:id_recon>')
    def api_report_analitic(id_recon):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        user_id    = session['user_id']
        id_company = session['company_id']

        visible_recon_ids = get_visible_recon_ids(id_company, user_id)
        if not visible_recon_ids:
            abort(404)
        recon_query = (
            db.select(Recon)
            .filter_by(id=id_recon, id_company=id_company)
            .filter(Recon.id.in_(visible_recon_ids))
        )
        recon = db.session.execute(recon_query).scalar_one_or_none()
        if not recon:
            abort(404)

        cn1 = dblib.get_connection("DB_NAME")
        try:
            field_order_1 = _get_field_order(cn1, id_recon, 1)
            field_order_2 = _get_field_order(cn1, id_recon, 2)
        finally:
            cn1.close()

        result = read_result(id_company, id_recon)
        lado1 = _fetch_table(result.get('lado1') if result else None, field_order_1)
        lado2 = _fetch_table(result.get('lado2') if result else None, field_order_2)

        log_data = read_log(id_company, id_recon) or {}
        entries = log_data.get('entries', [])
        created_at_values = [e.get('created_at') for e in entries if e.get('created_at')]
        max_created_at = max(created_at_values) if created_at_values else None
        execution_date = datetime.datetime.fromisoformat(max_created_at).strftime('%d/%m/%Y %H:%M') if max_created_at else None
        has_error = any(e.get('level') == 'ERROR' for e in entries)

        return jsonify({'execution_date': execution_date, 'has_error': has_error, 'lado1': lado1, 'lado2': lado2})
